"""Yomitoku OCR engine - Japanese-specialized Document AI.

This module provides yomitoku integration as an alternative to DeepSeek-OCR.
Yomitoku is a Japanese-specialized AI document analysis engine with:
- Built-in layout analysis
- Text detection and recognition
- Table structure recognition
- Support for vertical text and handwriting
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

import cv2
import numpy as np
from PIL import Image

if TYPE_CHECKING:
    from yomitoku import DocumentAnalyzer

from src.yomitoku_layout import detect_layout_yomitoku

# Lazy import for yomitoku
_yomitoku_analyzer: "DocumentAnalyzer | None" = None


def get_analyzer(device: str = "cpu") -> "DocumentAnalyzer":
    """Lazy initialization of yomitoku DocumentAnalyzer.

    Args:
        device: Device to use ("cuda" or "cpu").

    Returns:
        DocumentAnalyzer instance.
    """
    global _yomitoku_analyzer
    if _yomitoku_analyzer is None:
        from yomitoku import DocumentAnalyzer

        _yomitoku_analyzer = DocumentAnalyzer(
            visualize=False,
            device=device,
        )
    return _yomitoku_analyzer


@dataclass
class YomitokuResult:
    """Result from yomitoku OCR processing."""

    text: str  # Plain text output
    markdown: str  # Markdown-formatted output
    paragraphs: list[str]  # List of detected paragraphs
    tables: int  # Number of tables detected
    figures: int  # Number of figures detected


def ocr_page_yomitoku(
    page_path: str,
    device: str = "cpu",
    img: Image.Image | None = None,
) -> str:
    """OCR a single page image using yomitoku.

    Args:
        page_path: Path to the page image file.
        device: Device to use ("cuda" or "cpu").
        img: Optional pre-processed PIL Image (e.g. with figures masked).
            If provided, this is used instead of reading from page_path.

    Returns:
        Plain text extracted from the page.
    """
    analyzer = get_analyzer(device)

    # Load image
    if img is not None:
        # Convert PIL Image to cv2 format (BGR)
        img_array = np.array(img.convert("RGB"))
        cv_img = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    else:
        cv_img = cv2.imread(page_path)

    if cv_img is None:
        return ""

    # Run OCR
    results, _, _ = analyzer(cv_img)

    # Extract text from paragraphs
    paragraphs = []
    for p in results.paragraphs:
        if hasattr(p, "contents"):
            paragraphs.append(p.contents)
        elif hasattr(p, "text"):
            paragraphs.append(p.text)
        else:
            paragraphs.append(str(p))

    return "\n\n".join(paragraphs)


def _generate_markdown_from_results(results, cv_img, fallback_text: str) -> str:
    """Generate markdown from yomitoku results.

    Args:
        results: Yomitoku analysis results.
        cv_img: OpenCV image.
        fallback_text: Fallback text if markdown generation fails.

    Returns:
        Markdown string.
    """
    import shutil
    import tempfile

    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        temp_path = f.name

    try:
        results.to_markdown(temp_path, img=cv_img)
        markdown = Path(temp_path).read_text(encoding="utf-8")
    except Exception:
        markdown = fallback_text
    finally:
        Path(temp_path).unlink(missing_ok=True)
        # Clean up figures directory if created
        figures_dir = Path(temp_path).parent / f"{Path(temp_path).stem}_figures"
        if figures_dir.exists():
            shutil.rmtree(figures_dir, ignore_errors=True)

    return markdown


def ocr_page_yomitoku_full(
    page_path: str,
    device: str = "cpu",
    img: Image.Image | None = None,
) -> YomitokuResult:
    """OCR a single page image using yomitoku with full results.

    Args:
        page_path: Path to the page image file.
        device: Device to use ("cuda" or "cpu").
        img: Optional pre-processed PIL Image.

    Returns:
        YomitokuResult with text, markdown, and metadata.
    """
    analyzer = get_analyzer(device)

    # Load image
    if img is not None:
        img_array = np.array(img.convert("RGB"))
        cv_img = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)
    else:
        cv_img = cv2.imread(page_path)

    if cv_img is None:
        return YomitokuResult(
            text="",
            markdown="",
            paragraphs=[],
            tables=0,
            figures=0,
        )

    # Run OCR
    results, _, _ = analyzer(cv_img)

    # Extract paragraphs
    paragraphs = []
    for p in results.paragraphs:
        if hasattr(p, "contents"):
            paragraphs.append(p.contents)
        elif hasattr(p, "text"):
            paragraphs.append(p.text)
        else:
            paragraphs.append(str(p))

    text = "\n\n".join(paragraphs)

    # Generate markdown
    markdown = _generate_markdown_from_results(results, cv_img, text)

    return YomitokuResult(
        text=text,
        markdown=markdown,
        paragraphs=paragraphs,
        tables=len(results.tables),
        figures=len(results.figures),
    )


def ocr_pages_yomitoku(
    pages_dir: str,
    output_file: str,
    device: str = "cpu",
    layout: dict | None = None,
) -> str:
    """Run yomitoku OCR on all page images and combine into a single file.

    Args:
        pages_dir: Directory containing raw page images (pages/).
        output_file: Path to output text file.
        device: Device to use ("cuda" or "cpu").
        layout: Layout dict from figure detection (for compatibility, not used).

    Returns:
        Path to the output text file.
    """
    pages = sorted(Path(pages_dir).glob("page_*.png"))
    if not pages:
        print("No page images found")
        return output_file

    print(f"Using Yomitoku OCR on {len(pages)} pages (device={device})")
    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    # Initialize analyzer (warm up)
    print("  Loading yomitoku models...", end="", flush=True)
    start = time.time()
    get_analyzer(device)
    elapsed = time.time() - start
    print(f" loaded in {elapsed:.1f}s")

    all_text: list[str] = []
    total_start = time.time()

    # Create ocr_texts directory for individual page results
    ocr_texts_dir = out_path.parent / "ocr_texts"
    ocr_texts_dir.mkdir(parents=True, exist_ok=True)

    for i, page_path in enumerate(pages, 1):
        print(f"  [{i}/{len(pages)}] {page_path.name}", end="", flush=True)
        page_start = time.time()

        try:
            page_text = ocr_page_yomitoku(str(page_path), device=device)
            elapsed = time.time() - page_start
            print(f" -> {len(page_text)} chars ({elapsed:.1f}s)")

        except Exception as e:
            elapsed = time.time() - page_start
            print(f" -> ERROR ({elapsed:.1f}s): {e}")
            page_text = f"[OCR ERROR: {e}]"

        header = f"--- Page {i} ({page_path.name}) ---\n"
        all_text.append(f"{header}{page_text}")

        # Write individual page result immediately
        page_text_file = ocr_texts_dir / f"{page_path.stem}.txt"
        page_text_file.write_text(page_text, encoding="utf-8")
        print(f"    → Saved: {page_text_file.name}")

    combined = "\n\n".join(all_text)
    out_path.write_text(combined, encoding="utf-8")

    total_elapsed = time.time() - total_start
    print(f"\nYomitoku OCR complete in {total_elapsed:.1f}s")
    print(f"  Output: {out_path}")
    return output_file


# Alias for cleaner naming convention
detect_layout = detect_layout_yomitoku


def main() -> None:
    """CLI entry point for standalone Yomitoku OCR."""
    import argparse

    parser = argparse.ArgumentParser(description="Yomitoku OCR on page images")
    parser.add_argument("pages_dir", help="Directory containing page images")
    parser.add_argument("-o", "--output", default="book.txt", help="Output file path")
    parser.add_argument(
        "--device",
        default="cpu",
        choices=["cpu", "cuda"],
        help="Device to use (default: cpu)",
    )
    args = parser.parse_args()

    ocr_pages_yomitoku(
        pages_dir=args.pages_dir,
        output_file=args.output,
        device=args.device,
    )


if __name__ == "__main__":
    main()
