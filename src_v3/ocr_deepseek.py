"""DeepSeek-OCR engine using Ollama API with Free OCR prompt.

Sends raw page images to DeepSeek-OCR model via Ollama /api/chat endpoint.
Outputs native Markdown without post-processing.
"""

from __future__ import annotations

import base64
import io
import sys
import time
from pathlib import Path

import requests
from PIL import Image, ImageDraw

from src_v3.ocr import _format_figure_markers


def _encode_image(path: str) -> str:
    """Read an image file and return its base64-encoded string."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _encode_pil_image(img: Image.Image) -> str:
    """Encode a PIL Image to base64 PNG string."""
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def _mask_figure_regions(
    img: Image.Image,
    page_name: str,
    layout: dict,
) -> Image.Image:
    """White-out figure/table/formula regions so OCR only reads text.

    Uses raw page coordinates directly (no crop offset needed).

    Args:
        img: The raw page image.
        page_name: Page filename for layout lookup (e.g. "page_0169.png").
        layout: Full layout dict from layout.json.

    Returns:
        Copy of image with figure regions filled white.
    """
    page_layout = layout.get(page_name, {})
    figures = page_layout.get("figures", [])
    if not figures:
        return img

    masked = img.copy()
    draw = ImageDraw.Draw(masked)
    w, h = masked.size

    for fig in figures:
        x1, y1, x2, y2 = fig["bbox"]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        if x1 < x2 and y1 < y2:
            draw.rectangle([x1, y1, x2, y2], fill="white")

    return masked


def ocr_page_deepseek(
    page_path: str,
    model: str = "deepseek-ocr",
    base_url: str = "http://localhost:11434",
    timeout: int = 60,
    img: Image.Image | None = None,
) -> str:
    """OCR a single page image using DeepSeek-OCR via Ollama.

    Args:
        page_path: Path to the page image file.
        model: Ollama model name.
        base_url: Ollama API base URL.
        timeout: Request timeout in seconds.
        img: Optional pre-processed PIL Image (e.g. with figures masked).
            If provided, this is used instead of reading from page_path.

    Returns:
        Markdown-formatted text extracted from the page.
    """
    image_b64 = _encode_pil_image(img) if img is not None else _encode_image(page_path)

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


def _detect_repetition(
    text: str,
    min_ratio: float = 0.5,
    min_count: int = 10,
) -> str | None:
    """Detect abnormal line repetition in OCR output.

    Args:
        text: OCR output text for a single page.
        min_ratio: Minimum ratio of most-common line to total lines.
        min_count: Minimum count of repeated line to flag.

    Returns:
        Description of the anomaly, or None if normal.
    """
    from collections import Counter

    lines = [line for line in text.strip().split("\n") if line.strip()]
    if not lines:
        return None

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
    return None


def ocr_pages_deepseek(
    pages_dir: str,
    output_file: str,
    layout: dict | None = None,
    model: str = "deepseek-ocr",
    base_url: str = "http://localhost:11434",
    timeout: int = 60,
    min_confidence: float = 0.7,
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

    all_text: list[str] = []
    errors: list[str] = []
    total_start = time.time()

    has_layout = bool(layout)
    if has_layout:
        print("  Figure masking enabled")

    for i, page_path in enumerate(pages, 1):
        print(f"  [{i}/{len(pages)}] {page_path.name}", end="", flush=True)
        page_start = time.time()

        masked_img = None
        if has_layout:
            raw_img = Image.open(page_path)
            masked_img = _mask_figure_regions(raw_img, page_path.name, layout)
            if masked_img is raw_img:
                masked_img = None  # no figures on this page, use file directly

        try:
            page_md = ocr_page_deepseek(
                str(page_path), model, base_url, timeout, img=masked_img,
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

        markers = _format_figure_markers(page_path.name, layout, min_confidence)
        header = f"--- Page {i} ({page_path.name}) ---\n"
        all_text.append(f"{header}{markers}{page_md}")

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
