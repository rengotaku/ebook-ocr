"""Ensemble OCR: Combine multiple OCR engines for improved accuracy.

This module runs multiple OCR engines and merges results using voting
to achieve higher accuracy than any single engine alone.

Supported engines:
- DeepSeek-OCR (LLM-based, via Ollama)
- Tesseract (traditional, system install required)
- EasyOCR (neural network-based, pip install)

Output files:
- ocr_texts/{page}.txt           - Final merged result
- ocr_texts/{page}_deepseek.txt  - DeepSeek-OCR result
- ocr_texts/{page}_tesseract.txt - Tesseract result
- ocr_texts/{page}_easyocr.txt   - EasyOCR result
"""

from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path
from typing import Callable

import requests
from PIL import Image

from src.utils import encode_pil_image


# Lazy imports for optional dependencies
_tesseract = None
_easyocr_reader = None


def _get_tesseract():
    """Lazy import for pytesseract."""
    global _tesseract
    if _tesseract is None:
        import pytesseract
        _tesseract = pytesseract
    return _tesseract


def _get_easyocr_reader(lang_list: list[str] | None = None):
    """Lazy import and initialization for EasyOCR."""
    global _easyocr_reader
    if _easyocr_reader is None:
        import easyocr
        langs = lang_list or ["ja", "en"]
        _easyocr_reader = easyocr.Reader(langs, gpu=False)
    return _easyocr_reader


@dataclass
class EngineResult:
    """Result from a single OCR engine."""
    engine: str
    text: str
    success: bool
    error: str | None = None


@dataclass
class EnsembleResult:
    """Result from ensemble OCR processing."""
    merged: str  # Final merged text
    results: dict[str, str]  # engine_name -> text
    similarity_matrix: dict[str, dict[str, float]]  # pairwise similarities
    source: str  # Which strategy was used
    votes: dict[str, int] = field(default_factory=dict)  # engine -> vote count


def ocr_tesseract(
    image: Image.Image,
    lang: str = "jpn+eng",
) -> EngineResult:
    """Run Tesseract OCR on an image."""
    try:
        pytesseract = _get_tesseract()
        config = "--psm 6"
        text = pytesseract.image_to_string(image, lang=lang, config=config)
        return EngineResult(engine="tesseract", text=text.strip(), success=True)
    except Exception as e:
        return EngineResult(engine="tesseract", text="", success=False, error=str(e))


def ocr_easyocr(
    image: Image.Image,
    lang_list: list[str] | None = None,
) -> EngineResult:
    """Run EasyOCR on an image."""
    try:
        import numpy as np
        reader = _get_easyocr_reader(lang_list)
        # Convert PIL to numpy array
        img_array = np.array(image)
        results = reader.readtext(img_array, detail=0, paragraph=True)
        text = "\n".join(results)
        return EngineResult(engine="easyocr", text=text.strip(), success=True)
    except Exception as e:
        return EngineResult(engine="easyocr", text="", success=False, error=str(e))


def ocr_deepseek(
    image: Image.Image,
    base_url: str = "http://localhost:11434",
    model: str = "deepseek-ocr",
    timeout: int = 120,
) -> EngineResult:
    """Run DeepSeek-OCR on an image."""
    try:
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
        text = result["message"]["content"].strip()
        return EngineResult(engine="deepseek", text=text, success=True)
    except Exception as e:
        return EngineResult(engine="deepseek", text="", success=False, error=str(e))


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity ratio between two texts."""
    if not text1 and not text2:
        return 1.0
    if not text1 or not text2:
        return 0.0
    return SequenceMatcher(None, text1, text2).ratio()


def calculate_similarity_matrix(results: dict[str, str]) -> dict[str, dict[str, float]]:
    """Calculate pairwise similarity between all engine results."""
    engines = list(results.keys())
    matrix: dict[str, dict[str, float]] = {}
    for e1 in engines:
        matrix[e1] = {}
        for e2 in engines:
            matrix[e1][e2] = calculate_similarity(results[e1], results[e2])
    return matrix


def vote_best_result(
    results: dict[str, str],
    similarity_matrix: dict[str, dict[str, float]],
    threshold: float = 0.7,
) -> tuple[str, str, dict[str, int]]:
    """Vote for the best result based on agreement between engines.

    Strategy:
    1. Calculate average similarity of each engine to others
    2. Engine with highest average similarity wins
    3. If all low similarity, prefer DeepSeek (best for Japanese)

    Returns:
        Tuple of (best_text, winning_engine, vote_counts).
    """
    engines = [e for e, t in results.items() if t]  # Only engines with results

    if not engines:
        return "", "none", {}

    if len(engines) == 1:
        return results[engines[0]], engines[0], {engines[0]: 1}

    # Calculate average agreement score for each engine
    scores: dict[str, float] = {}
    for engine in engines:
        other_sims = [
            similarity_matrix[engine][other]
            for other in engines
            if other != engine
        ]
        scores[engine] = sum(other_sims) / len(other_sims) if other_sims else 0

    # Count "votes" - how many engines agree with each
    votes: dict[str, int] = {}
    for engine in engines:
        votes[engine] = sum(
            1 for other in engines
            if other != engine and similarity_matrix[engine][other] >= threshold
        )

    # Find winner
    max_votes = max(votes.values()) if votes else 0

    if max_votes > 0:
        # At least some agreement - pick engine with most votes
        # Tie-break by average similarity score
        winners = [e for e, v in votes.items() if v == max_votes]
        winner = max(winners, key=lambda e: scores.get(e, 0))
        return results[winner], winner, votes
    else:
        # No agreement - prefer by priority: deepseek > easyocr > tesseract
        priority = ["deepseek", "easyocr", "tesseract"]
        for engine in priority:
            if engine in engines and results[engine]:
                return results[engine], engine, votes

        # Fallback to first available
        return results[engines[0]], engines[0], votes


def merge_by_voting(
    results: dict[str, str],
    threshold: float = 0.7,
) -> EnsembleResult:
    """Merge OCR results using voting strategy.

    Args:
        results: Dict of engine_name -> text.
        threshold: Similarity threshold for counting as agreement.

    Returns:
        EnsembleResult with merged text and metadata.
    """
    # Filter to successful results only
    valid_results = {k: v for k, v in results.items() if v}

    if not valid_results:
        return EnsembleResult(
            merged="",
            results=results,
            similarity_matrix={},
            source="none",
        )

    # Calculate similarities
    sim_matrix = calculate_similarity_matrix(valid_results)

    # Vote for best
    merged_text, winner, votes = vote_best_result(valid_results, sim_matrix, threshold)

    return EnsembleResult(
        merged=merged_text,
        results=results,
        similarity_matrix=sim_matrix,
        source=winner,
        votes=votes,
    )


def ocr_ensemble(
    image: Image.Image | str,
    engines: list[str] | None = None,
    base_url: str = "http://localhost:11434",
    model: str = "deepseek-ocr",
    timeout: int = 120,
    tesseract_lang: str = "jpn+eng",
    easyocr_langs: list[str] | None = None,
    similarity_threshold: float = 0.7,
) -> EnsembleResult:
    """Run ensemble OCR with multiple engines.

    Args:
        image: PIL Image or path to image file.
        engines: List of engines to use. Default: ["deepseek", "tesseract", "easyocr"]
        base_url: Ollama API base URL for DeepSeek.
        model: DeepSeek model name.
        timeout: DeepSeek request timeout.
        tesseract_lang: Tesseract language code(s).
        easyocr_langs: EasyOCR language list.
        similarity_threshold: Threshold for voting agreement.

    Returns:
        EnsembleResult with merged and individual results.
    """
    if isinstance(image, str):
        image = Image.open(image)

    if engines is None:
        engines = ["deepseek", "tesseract", "easyocr"]

    results: dict[str, str] = {}

    # Run each engine
    for engine in engines:
        if engine == "deepseek":
            result = ocr_deepseek(image, base_url, model, timeout)
        elif engine == "tesseract":
            result = ocr_tesseract(image, tesseract_lang)
        elif engine == "easyocr":
            result = ocr_easyocr(image, easyocr_langs)
        else:
            continue

        if result.success:
            results[engine] = result.text
        else:
            print(f"    {engine} failed: {result.error}")
            results[engine] = ""

    # Merge by voting
    return merge_by_voting(results, similarity_threshold)


def run_ensemble_ocr(
    pages_dir: str,
    output_dir: str,
    engines: list[str] | None = None,
    base_url: str = "http://localhost:11434",
    model: str = "deepseek-ocr",
    timeout: int = 120,
    tesseract_lang: str = "jpn+eng",
    easyocr_langs: list[str] | None = None,
) -> list[tuple[str, EnsembleResult]]:
    """Run ensemble OCR on all pages in a directory.

    Args:
        pages_dir: Directory containing page images.
        output_dir: Directory for output text files.
        engines: List of engines to use.
        base_url: Ollama API base URL.
        model: DeepSeek model name.
        timeout: DeepSeek request timeout.
        tesseract_lang: Tesseract language code(s).
        easyocr_langs: EasyOCR language list.

    Returns:
        List of (page_name, EnsembleResult) tuples.
    """
    if engines is None:
        engines = ["deepseek", "tesseract", "easyocr"]

    pages_path = Path(pages_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    pages = sorted(pages_path.glob("*.png"))
    all_results: list[tuple[str, EnsembleResult]] = []

    print(f"Running ensemble OCR ({', '.join(engines)}) on {len(pages)} pages...")

    for page_path in pages:
        page_name = page_path.name
        page_stem = page_path.stem
        print(f"  Processing {page_name}...")

        with Image.open(page_path) as img:
            result = ocr_ensemble(
                img,
                engines=engines,
                base_url=base_url,
                model=model,
                timeout=timeout,
                tesseract_lang=tesseract_lang,
                easyocr_langs=easyocr_langs,
            )

        # Report
        vote_str = ", ".join(f"{e}:{v}" for e, v in result.votes.items()) if result.votes else "N/A"
        print(f"    Winner: {result.source}, Votes: [{vote_str}]")

        # Write individual engine results
        for engine, text in result.results.items():
            engine_file = output_path / f"{page_stem}_{engine}.txt"
            engine_file.write_text(text, encoding="utf-8")

        # Write merged result
        merged_file = output_path / f"{page_stem}.txt"
        merged_file.write_text(result.merged, encoding="utf-8")

        file_list = ", ".join(f"{page_stem}_{e}.txt" for e in engines)
        print(f"    → Saved: {page_stem}.txt, {file_list}")

        all_results.append((page_name, result))

    # Write combined output
    combined_path = output_path.parent / "book_ensemble.txt"
    with open(combined_path, "w", encoding="utf-8") as f:
        for page_name, result in all_results:
            vote_str = ", ".join(f"{e}:{v}" for e, v in result.votes.items())
            f.write(f"\n--- Page: {page_name} (winner: {result.source}, votes: [{vote_str}]) ---\n\n")
            f.write(result.merged)
            f.write("\n\n")

    print(f"\nEnsemble OCR complete. Output: {combined_path}")
    return all_results


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Ensemble OCR (DeepSeek + Tesseract + EasyOCR)"
    )
    parser.add_argument("pages_dir", help="Directory containing page images")
    parser.add_argument("-o", "--output", default="ocr_texts", help="Output directory")
    parser.add_argument(
        "--engines",
        default="deepseek,tesseract,easyocr",
        help="Comma-separated list of engines (default: deepseek,tesseract,easyocr)",
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:11434",
        help="Ollama API base URL",
    )
    parser.add_argument(
        "--timeout", type=int, default=120, help="DeepSeek timeout (seconds)"
    )
    parser.add_argument(
        "--tesseract-lang", default="jpn+eng", help="Tesseract language code(s)"
    )
    parser.add_argument(
        "--easyocr-langs", default="ja,en", help="EasyOCR languages (comma-separated)"
    )
    args = parser.parse_args()

    engines = [e.strip() for e in args.engines.split(",")]
    easyocr_langs = [l.strip() for l in args.easyocr_langs.split(",")]

    run_ensemble_ocr(
        pages_dir=args.pages_dir,
        output_dir=args.output,
        engines=engines,
        base_url=args.base_url,
        timeout=args.timeout,
        tesseract_lang=args.tesseract_lang,
        easyocr_langs=easyocr_langs,
    )


if __name__ == "__main__":
    main()
