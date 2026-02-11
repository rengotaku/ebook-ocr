"""DeepSeek-OCR engine using Ollama API with Free OCR prompt.

Sends raw page images to DeepSeek-OCR model via Ollama /api/chat endpoint.
Outputs native Markdown without post-processing.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import requests
from PIL import Image

from src.utils import (
    encode_image_file,
    encode_pil_image,
    format_figure_markers,
    mask_figure_regions,
)


def warm_up_model(
    model: str,
    base_url: str = "http://localhost:11434",
    timeout: int = 300,
) -> None:
    """Warm up the model by sending a dummy request to load it into memory.

    Args:
        model: Ollama model name.
        base_url: Ollama API base URL.
        timeout: Request timeout in seconds (longer for initial load).

    Raises:
        requests.RequestException: If the warm-up request fails.
    """
    print(f"  Loading model {model}...", end="", flush=True)
    start = time.time()

    # Create a minimal 1x1 white image
    dummy_img = Image.new("RGB", (1, 1), color="white")
    image_b64 = encode_pil_image(dummy_img)

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": "test",
                "images": [image_b64],
            },
        ],
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_predict": 1,
        },
    }

    response = requests.post(
        f"{base_url}/api/chat",
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()

    elapsed = time.time() - start
    print(f" loaded in {elapsed:.1f}s")


OCR_DEFAULT_OPTIONS = {
    "temperature": 0.1,
    "num_predict": 4096,
    "repeat_penalty": 1.3,
    "repeat_last_n": -1,
}


def ocr_page_deepseek(
    page_path: str,
    model: str = "deepseek-ocr",
    base_url: str = "http://localhost:11434",
    timeout: int = 60,
    img: Image.Image | None = None,
    options: dict | None = None,
) -> str:
    """OCR a single page image using DeepSeek-OCR via Ollama.

    Args:
        page_path: Path to the page image file.
        model: Ollama model name.
        base_url: Ollama API base URL.
        timeout: Request timeout in seconds.
        img: Optional pre-processed PIL Image (e.g. with figures masked).
            If provided, this is used instead of reading from page_path.
        options: Ollama generation options (temperature, repeat_penalty, etc.).

    Returns:
        Markdown-formatted text extracted from the page.
    """
    image_b64 = encode_pil_image(img) if img is not None else encode_image_file(page_path)
    merged_options = {**OCR_DEFAULT_OPTIONS, **(options or {})}

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": "Free OCR.",
                "images": [image_b64],
            },
        ],
        "stream": False,
        "options": merged_options,
    }

    response = requests.post(
        f"{base_url}/api/chat",
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()

    result = response.json()
    return result["message"]["content"].strip()


def _detect_repetition(
    text: str,
    min_ratio: float = 0.5,
    min_count: int = 10,
    min_phrase_len: int = 8,
    min_phrase_repeats: int = 5,
) -> str | None:
    """Detect abnormal repetition in OCR output (line-level and phrase-level).

    Args:
        text: OCR output text for a single page.
        min_ratio: Minimum ratio of most-common line to total lines.
        min_count: Minimum count of repeated line to flag.
        min_phrase_len: Minimum character length of a phrase to check for in-line repetition.
        min_phrase_repeats: Minimum number of phrase repeats within a single line to flag.

    Returns:
        Description of the anomaly, or None if normal.
    """
    import re
    from collections import Counter

    lines = [line for line in text.strip().split("\n") if line.strip()]
    if not lines:
        return None

    # Check 1: Line-level repetition
    counts = Counter(lines)
    most_common_line, count = counts.most_common(1)[0]
    total = len(lines)
    ratio = count / total

    if ratio > min_ratio and count > min_count:
        preview = most_common_line[:50]
        return (
            f"Repetition detected: \"{preview}\" repeated {count}/{total} "
            f"lines ({ratio:.0%})"
        )

    # Check 2: In-line phrase repetition (e.g. same phrase repeated N+ times in one line)
    for line in lines:
        if len(line) < min_phrase_len * min_phrase_repeats:
            continue
        # Find repeated substrings of min_phrase_len+ characters occurring 5+ times
        match = re.search(
            rf"(.{{{min_phrase_len},100}}?)\1{{{min_phrase_repeats - 1},}}",
            line,
        )
        if match:
            phrase = match.group(1)[:50]
            repeat_count = line.count(match.group(1))
            return (
                f"In-line repetition detected: \"{phrase}\" repeated "
                f"{repeat_count} times in one line"
            )

    return None


def ocr_pages_deepseek(
    pages_dir: str,
    output_file: str,
    layout: dict | None = None,
    model: str = "deepseek-ocr",
    base_url: str = "http://localhost:11434",
    timeout: int = 60,
    min_confidence: float = 0.7,
    options: dict | None = None,
) -> str:
    """Run DeepSeek-OCR on all page images and combine into a single file.

    Anomalous pages (e.g. repetitive output) are replaced with a marker
    and logged to errors.txt alongside the output file.

    Args:
        pages_dir: Directory containing raw page images (pages/).
        output_file: Path to output text file.
        layout: Layout dict from figure detection.
        model: Ollama model name.
        base_url: Ollama API base URL.
        timeout: Per-page timeout in seconds.
        min_confidence: Minimum confidence for figure markers.
        options: Ollama generation options (temperature, repeat_penalty, etc.).

    Returns:
        Path to the output text file.
    """
    if layout is None:
        layout = {}

    pages = sorted(Path(pages_dir).glob("page_*.png"))
    if not pages:
        print("No page images found")
        return output_file

    print(f"Using DeepSeek-OCR ({model}) on {len(pages)} pages")
    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Warm up model to avoid timeout on first page
    try:
        warm_up_model(model, base_url, timeout=300)
    except requests.RequestException as e:
        print(f"  Model warm-up failed: {e}")
        print("  Continuing anyway (first page may timeout)...")

    all_text: list[str] = []
    errors: list[str] = []
    total_start = time.time()

    # Create ocr_texts directory for individual page results
    ocr_texts_dir = out_path.parent / "ocr_texts"
    ocr_texts_dir.mkdir(parents=True, exist_ok=True)

    has_layout = bool(layout)
    if has_layout:
        print("  Figure masking enabled")

    for i, page_path in enumerate(pages, 1):
        print(f"  [{i}/{len(pages)}] {page_path.name}", end="", flush=True)
        page_start = time.time()

        masked_img = None
        if has_layout:
            with Image.open(page_path) as raw_img:
                masked_img = mask_figure_regions(raw_img, page_path.name, layout)
                if masked_img is raw_img:
                    masked_img = None  # no figures on this page, use file directly

        try:
            page_md = ocr_page_deepseek(
                str(page_path), model, base_url, timeout, img=masked_img,
                options=options,
            )
            elapsed = time.time() - page_start

            # Post-process: detect repetition anomaly
            anomaly = _detect_repetition(page_md)
            if anomaly is not None:
                print(f" -> ANOMALY ({elapsed:.1f}s): {anomaly}")
                errors.append(f"Page {i} ({page_path.name}): {anomaly}")
                page_md = f"[OCR ANOMALY: {anomaly}]"
            else:
                print(f" -> {len(page_md)} chars ({elapsed:.1f}s)")

        except requests.RequestException as e:
            elapsed = time.time() - page_start
            print(f" -> ERROR ({elapsed:.1f}s): {e}")
            errors.append(f"Page {i} ({page_path.name}): Request error: {e}")
            page_md = f"[OCR ERROR: {e}]"

        markers = format_figure_markers(page_path.name, layout, min_confidence)
        header = f"--- Page {i} ({page_path.name}) ---\n"
        all_text.append(f"{header}{markers}{page_md}")

        # Write individual page result immediately
        page_text_file = ocr_texts_dir / f"{page_path.stem}.txt"
        page_text_file.write_text(f"{markers}{page_md}", encoding="utf-8")
        print(f"    → Saved: {page_text_file.name}")

    combined = "\n\n".join(all_text)
    out_path.write_text(combined, encoding="utf-8")

    # Write errors.txt if any anomalies or errors occurred
    errors_path = out_path.parent / "errors.txt"
    if errors:
        errors_path.write_text("\n".join(errors) + "\n", encoding="utf-8")
        print(f"\n  Errors: {len(errors)} pages flagged -> {errors_path}")
    elif errors_path.exists():
        errors_path.unlink()  # clean up stale errors file

    total_elapsed = time.time() - total_start
    print(f"\nDeepSeek-OCR complete in {total_elapsed:.1f}s")
    print(f"  Output: {out_path}")
    return output_file


def main() -> None:
    """CLI entry point for standalone DeepSeek-OCR."""
    import argparse

    parser = argparse.ArgumentParser(description="DeepSeek-OCR on page images")
    parser.add_argument("pages_dir", help="Directory containing page images")
    parser.add_argument("-o", "--output", default="book.txt", help="Output file path")
    parser.add_argument("--model", default="deepseek-ocr", help="Ollama model name")
    parser.add_argument("--base-url", default="http://localhost:11434", help="Ollama API URL")
    parser.add_argument("--timeout", type=int, default=60, help="Per-page timeout (seconds)")
    args = parser.parse_args()

    ocr_pages_deepseek(
        pages_dir=args.pages_dir,
        output_file=args.output,
        model=args.model,
        base_url=args.base_url,
        timeout=args.timeout,
    )


if __name__ == "__main__":
    main()
