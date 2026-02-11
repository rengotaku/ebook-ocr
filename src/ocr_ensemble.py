"""Ensemble OCR: Combine DeepSeek-OCR with Tesseract for improved accuracy.

This module runs both OCR engines and merges results using similarity-based
voting to achieve higher accuracy than either engine alone.

Output files:
- ocr_texts/{page}.txt         - Final merged result
- ocr_texts/{page}_deepseek.txt - DeepSeek-OCR result
- ocr_texts/{page}_tesseract.txt - Tesseract result
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

import pytesseract
import requests
from PIL import Image

from src.utils import encode_pil_image


@dataclass
class EnsembleResult:
    """Result from ensemble OCR processing."""

    merged: str  # Final merged text
    deepseek: str  # DeepSeek-OCR result
    tesseract: str  # Tesseract result
    similarity: float  # Similarity score between engines (0.0-1.0)
    source: str  # Which source was primarily used: "deepseek", "tesseract", "merged"


def ocr_tesseract(
    image: Image.Image,
    lang: str = "jpn+eng",
) -> str:
    """Run Tesseract OCR on an image.

    Args:
        image: PIL Image to process.
        lang: Tesseract language code(s).

    Returns:
        Extracted text.
    """
    # Tesseract config for better Japanese recognition
    config = "--psm 6"  # Assume uniform block of text
    text = pytesseract.image_to_string(image, lang=lang, config=config)
    return text.strip()


def ocr_deepseek(
    image: Image.Image,
    base_url: str = "http://localhost:11434",
    model: str = "deepseek-ocr",
    timeout: int = 120,
) -> str:
    """Run DeepSeek-OCR on an image.

    Args:
        image: PIL Image to process.
        base_url: Ollama API base URL.
        model: Model name.
        timeout: Request timeout in seconds.

    Returns:
        Extracted text.
    """
    image_b64 = encode_pil_image(image)

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": "",
                "images": [image_b64],
            },
        ],
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 4096,
        },
    }

    response = requests.post(
        f"{base_url}/api/chat",
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()

    result = response.json()
    return result["message"]["content"].strip()


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity ratio between two texts.

    Args:
        text1: First text.
        text2: Second text.

    Returns:
        Similarity ratio (0.0-1.0).
    """
    if not text1 and not text2:
        return 1.0
    if not text1 or not text2:
        return 0.0
    return SequenceMatcher(None, text1, text2).ratio()


def merge_texts(
    deepseek_text: str,
    tesseract_text: str,
    similarity_threshold: float = 0.8,
) -> tuple[str, str]:
    """Merge OCR results from two engines.

    Strategy:
    - High similarity (>= threshold): Use DeepSeek (better formatting)
    - Low similarity: Line-by-line comparison, prefer longer/more confident

    Args:
        deepseek_text: Text from DeepSeek-OCR.
        tesseract_text: Text from Tesseract.
        similarity_threshold: Threshold for considering results similar.

    Returns:
        Tuple of (merged_text, source_used).
    """
    similarity = calculate_similarity(deepseek_text, tesseract_text)

    if similarity >= similarity_threshold:
        # High similarity - trust DeepSeek (better formatting for Japanese)
        return deepseek_text, "deepseek"

    # Low similarity - need to merge carefully
    deepseek_lines = deepseek_text.split("\n")
    tesseract_lines = tesseract_text.split("\n")

    # If one is significantly longer, it likely captured more text
    if len(deepseek_text) > len(tesseract_text) * 1.5:
        return deepseek_text, "deepseek"
    if len(tesseract_text) > len(deepseek_text) * 1.5:
        return tesseract_text, "tesseract"

    # Line-by-line merge: prefer non-empty, longer lines
    merged_lines = []
    max_lines = max(len(deepseek_lines), len(tesseract_lines))

    for i in range(max_lines):
        d_line = deepseek_lines[i].strip() if i < len(deepseek_lines) else ""
        t_line = tesseract_lines[i].strip() if i < len(tesseract_lines) else ""

        if not d_line and not t_line:
            continue
        elif not d_line:
            merged_lines.append(t_line)
        elif not t_line:
            merged_lines.append(d_line)
        else:
            # Both have content - prefer longer (likely more complete)
            merged_lines.append(d_line if len(d_line) >= len(t_line) else t_line)

    return "\n".join(merged_lines), "merged"


def ocr_ensemble(
    image: Image.Image | str,
    base_url: str = "http://localhost:11434",
    model: str = "deepseek-ocr",
    timeout: int = 120,
    lang: str = "jpn+eng",
    similarity_threshold: float = 0.8,
) -> EnsembleResult:
    """Run ensemble OCR combining DeepSeek and Tesseract.

    Args:
        image: PIL Image or path to image file.
        base_url: Ollama API base URL.
        model: DeepSeek model name.
        timeout: DeepSeek request timeout.
        lang: Tesseract language code(s).
        similarity_threshold: Threshold for merge strategy.

    Returns:
        EnsembleResult with merged and individual results.
    """
    if isinstance(image, str):
        image = Image.open(image)

    # Run both OCR engines
    deepseek_text = ""
    tesseract_text = ""

    try:
        deepseek_text = ocr_deepseek(image, base_url, model, timeout)
    except Exception as e:
        print(f"    DeepSeek-OCR failed: {e}")

    try:
        tesseract_text = ocr_tesseract(image, lang)
    except Exception as e:
        print(f"    Tesseract failed: {e}")

    # Calculate similarity
    similarity = calculate_similarity(deepseek_text, tesseract_text)

    # Merge results
    if not deepseek_text and not tesseract_text:
        merged_text, source = "", "none"
    elif not deepseek_text:
        merged_text, source = tesseract_text, "tesseract"
    elif not tesseract_text:
        merged_text, source = deepseek_text, "deepseek"
    else:
        merged_text, source = merge_texts(
            deepseek_text, tesseract_text, similarity_threshold
        )

    return EnsembleResult(
        merged=merged_text,
        deepseek=deepseek_text,
        tesseract=tesseract_text,
        similarity=similarity,
        source=source,
    )


def run_ensemble_ocr(
    pages_dir: str,
    output_dir: str,
    base_url: str = "http://localhost:11434",
    model: str = "deepseek-ocr",
    timeout: int = 120,
    lang: str = "jpn+eng",
) -> list[tuple[str, EnsembleResult]]:
    """Run ensemble OCR on all pages in a directory.

    Output files per page:
    - {page}.txt         - Merged result
    - {page}_deepseek.txt - DeepSeek result
    - {page}_tesseract.txt - Tesseract result

    Args:
        pages_dir: Directory containing page images.
        output_dir: Directory for output text files.
        base_url: Ollama API base URL.
        model: DeepSeek model name.
        timeout: DeepSeek request timeout.
        lang: Tesseract language code(s).

    Returns:
        List of (page_name, EnsembleResult) tuples.
    """
    pages_path = Path(pages_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    pages = sorted(pages_path.glob("*.png"))
    results: list[tuple[str, EnsembleResult]] = []

    print(f"Running ensemble OCR on {len(pages)} pages...")

    for page_path in pages:
        page_name = page_path.name
        page_stem = page_path.stem
        print(f"  Processing {page_name}...")

        with Image.open(page_path) as img:
            result = ocr_ensemble(
                img,
                base_url=base_url,
                model=model,
                timeout=timeout,
                lang=lang,
            )

        # Report
        print(f"    Similarity: {result.similarity:.1%}, Source: {result.source}")

        # Write individual engine results
        (output_path / f"{page_stem}_deepseek.txt").write_text(
            result.deepseek, encoding="utf-8"
        )
        (output_path / f"{page_stem}_tesseract.txt").write_text(
            result.tesseract, encoding="utf-8"
        )
        # Write merged result
        (output_path / f"{page_stem}.txt").write_text(
            result.merged, encoding="utf-8"
        )

        print(f"    → Saved: {page_stem}.txt, {page_stem}_deepseek.txt, {page_stem}_tesseract.txt")

        results.append((page_name, result))

    # Write combined output
    combined_path = output_path.parent / "book_ensemble.txt"
    with open(combined_path, "w", encoding="utf-8") as f:
        for page_name, result in results:
            f.write(f"\n--- Page: {page_name} (similarity: {result.similarity:.1%}, source: {result.source}) ---\n\n")
            f.write(result.merged)
            f.write("\n\n")

    print(f"\nEnsemble OCR complete. Output: {combined_path}")
    return results


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Ensemble OCR (DeepSeek + Tesseract)")
    parser.add_argument("pages_dir", help="Directory containing page images")
    parser.add_argument("-o", "--output", default="ocr_texts", help="Output directory")
    parser.add_argument(
        "--base-url",
        default="http://localhost:11434",
        help="Ollama API base URL",
    )
    parser.add_argument(
        "--timeout", type=int, default=120, help="DeepSeek timeout (seconds)"
    )
    parser.add_argument(
        "--lang", default="jpn+eng", help="Tesseract language code(s)"
    )
    args = parser.parse_args()

    run_ensemble_ocr(
        pages_dir=args.pages_dir,
        output_dir=args.output,
        base_url=args.base_url,
        timeout=args.timeout,
        lang=args.lang,
    )


if __name__ == "__main__":
    main()
