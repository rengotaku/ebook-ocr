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

    # Generate markdown (write to temp file then read)
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as f:
        temp_path = f.name

    try:
        results.to_markdown(temp_path, img=cv_img)
        markdown = Path(temp_path).read_text(encoding="utf-8")
    except Exception:
        markdown = text
    finally:
        Path(temp_path).unlink(missing_ok=True)
        # Clean up figures directory if created
        figures_dir = Path(temp_path).parent / f"{Path(temp_path).stem}_figures"
        if figures_dir.exists():
            import shutil
            shutil.rmtree(figures_dir, ignore_errors=True)

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


def reset_analyzer() -> None:
    """Reset the cached analyzer instance.

    Call this if you need to change device or lite settings.
    """
    global _yomitoku_analyzer
    _yomitoku_analyzer = None


def save_yomitoku_results(output_dir: str, page_stem: str, results) -> None:
    """Save yomitoku analysis results to cache.

    Args:
        output_dir: Output directory
        page_stem: Page filename stem (e.g., "page_0024")
        results: DocumentAnalyzerSchema from yomitoku
    """
    from pathlib import Path
    import pickle

    cache_dir = Path(output_dir) / "yomitoku_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)
    cache_file = cache_dir / f"{page_stem}.pkl"

    with open(cache_file, "wb") as f:
        pickle.dump(results, f)


def load_yomitoku_results(output_dir: str, page_stem: str):
    """Load yomitoku analysis results from cache.

    Args:
        output_dir: Output directory
        page_stem: Page filename stem (e.g., "page_0024")

    Returns:
        DocumentAnalyzerSchema or None if cache not found
    """
    from pathlib import Path
    import pickle

    cache_dir = Path(output_dir) / "yomitoku_cache"
    cache_file = cache_dir / f"{page_stem}.pkl"

    if not cache_file.exists():
        return None

    with open(cache_file, "rb") as f:
        return pickle.load(f)


def paragraphs_to_layout(
    paragraphs: list,
    figures: list,
    page_size: tuple[int, int]
) -> dict:
    """Convert yomitoku paragraphs and figures to layout.json format.

    Args:
        paragraphs: List of yomitoku ParagraphSchema objects
        figures: List of yomitoku FigureSchema objects
        page_size: (width, height) of the page

    Returns:
        Layout dict with regions list
    """
    regions = []

    # Process paragraphs
    for p in paragraphs:
        # Determine region type based on role
        if hasattr(p, 'role') and p.role == 'section_headings':
            region_type = 'TITLE'
        else:
            region_type = 'TEXT'

        # Extract bbox
        if hasattr(p, 'box') and p.box:
            bbox = [int(p.box[0]), int(p.box[1]), int(p.box[2]), int(p.box[3])]
        else:
            continue  # Skip paragraphs without box

        regions.append({
            'type': region_type,
            'label': 'section_headings' if region_type == 'TITLE' else 'plain text',
            'bbox': bbox,
            'confidence': 1.0,  # yomitoku doesn't provide confidence per paragraph
        })

    # Process figures
    for f in figures:
        if hasattr(f, 'box') and f.box:
            bbox = [int(f.box[0]), int(f.box[1]), int(f.box[2]), int(f.box[3])]
            regions.append({
                'type': 'FIGURE',
                'label': 'figure',
                'bbox': bbox,
                'confidence': 1.0,
            })

    return {
        'regions': regions,
        'page_size': list(page_size),
    }


def visualize_layout(
    img_path: str,
    paragraphs: list,
    figures: list,
    output_path: str,
) -> None:
    """Draw bounding boxes on image and save to output_path.

    Args:
        img_path: Path to input image
        paragraphs: List of yomitoku ParagraphSchema objects
        figures: List of yomitoku FigureSchema objects
        output_path: Path to save visualized image
    """
    import cv2

    img = cv2.imread(img_path)
    if img is None:
        return

    # Draw paragraphs
    for p in paragraphs:
        if not hasattr(p, 'box') or not p.box:
            continue

        x1, y1, x2, y2 = [int(v) for v in p.box]

        # Determine color based on role
        if hasattr(p, 'role') and p.role == 'section_headings':
            color = (0, 0, 255)  # Red for titles
            thickness = 3
            label = 'section_headings'
        else:
            color = (0, 255, 0)  # Green for text
            thickness = 2
            label = 'text'

        cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
        cv2.putText(
            img,
            label,
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2,
        )

    # Draw figures
    for f in figures:
        if not hasattr(f, 'box') or not f.box:
            continue

        x1, y1, x2, y2 = [int(v) for v in f.box]
        color = (255, 0, 0)  # Blue for figures
        thickness = 3

        cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
        cv2.putText(
            img,
            'figure',
            (x1, y1 - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            color,
            2,
        )

    cv2.imwrite(output_path, img)


def detect_layout_yomitoku(
    pages_dir: str,
    output_dir: str,
    layouts_dir: str | None = None,
    device: str = "cpu",
) -> dict:
    """Detect layout using yomitoku and generate layout.json + visualizations.

    This replaces detect_figures.py (YOLO-based detection).

    Args:
        pages_dir: Directory containing page images
        output_dir: Directory to save layout.json
        layouts_dir: Directory to save layout visualizations (defaults to output_dir/layouts)
        device: Device for yomitoku ("cpu" or "cuda")

    Returns:
        Layout dict mapping page filenames to regions
    """
    from pathlib import Path
    import json

    pages_path = Path(pages_dir)
    out_path = Path(output_dir)
    lay_dir = Path(layouts_dir) if layouts_dir else out_path / "layouts"
    lay_dir.mkdir(parents=True, exist_ok=True)

    pages = sorted(pages_path.glob("*.png"))
    if not pages:
        print("No page images found")
        return {}

    print("Initializing yomitoku DocumentAnalyzer...")
    analyzer = get_analyzer(device)

    layout_data = {}

    for i, page_path in enumerate(pages, 1):
        page_name = page_path.name
        print(f"Analyzing layout: page {i}/{len(pages)} ({page_name})")

        # Load and analyze
        cv_img = cv2.imread(str(page_path))
        if cv_img is None:
            print(f"  → Failed to load image")
            continue

        results, _, _ = analyzer(cv_img)
        page_height, page_width = cv_img.shape[:2]

        # Save results to cache
        save_yomitoku_results(output_dir, page_path.stem, results)

        # Convert to layout format
        page_layout = paragraphs_to_layout(
            results.paragraphs,
            results.figures,
            (page_width, page_height)
        )
        layout_data[page_name] = page_layout

        print(f"  → Found {len(page_layout['regions'])} regions "
              f"({len(results.paragraphs)} paragraphs, {len(results.figures)} figures)")

        # Visualize (box反映)
        vis_path = lay_dir / page_name
        visualize_layout(str(page_path), results.paragraphs, results.figures, str(vis_path))

    # Save layout.json
    layout_file = out_path / "layout.json"
    with open(layout_file, "w", encoding="utf-8") as f:
        json.dump(layout_data, f, indent=2, ensure_ascii=False)

    print(f"\nLayout detection complete")
    print(f"  Layout: {layout_file}")
    print(f"  Visualizations: {lay_dir}")

    return layout_data


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
