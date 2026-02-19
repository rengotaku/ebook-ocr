"""Layout detection utilities using Yomitoku.

Helper functions for layout detection and visualization.
Extracted from ocr_yomitoku.py to reduce file size.
"""

from __future__ import annotations

import json
from pathlib import Path

import cv2


def paragraphs_to_layout(paragraphs: list, figures: list, page_size: tuple[int, int]) -> dict:
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
        if hasattr(p, "role") and p.role == "section_headings":
            region_type = "TITLE"
        else:
            region_type = "TEXT"

        # Extract bbox
        if hasattr(p, "box") and p.box:
            bbox = [int(p.box[0]), int(p.box[1]), int(p.box[2]), int(p.box[3])]
        else:
            continue  # Skip paragraphs without box

        regions.append(
            {
                "type": region_type,
                "label": "section_headings" if region_type == "TITLE" else "plain text",
                "bbox": bbox,
                "confidence": 1.0,  # yomitoku doesn't provide confidence per paragraph
            }
        )

    # Process figures
    for f in figures:
        if hasattr(f, "box") and f.box:
            bbox = [int(f.box[0]), int(f.box[1]), int(f.box[2]), int(f.box[3])]
            regions.append(
                {
                    "type": "FIGURE",
                    "label": "figure",
                    "bbox": bbox,
                    "confidence": 1.0,
                }
            )

    return {
        "regions": regions,
        "page_size": list(page_size),
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
    img = cv2.imread(img_path)
    if img is None:
        return

    # Draw paragraphs
    for p in paragraphs:
        if not hasattr(p, "box") or not p.box:
            continue

        x1, y1, x2, y2 = [int(v) for v in p.box]

        # Determine color based on role
        if hasattr(p, "role") and p.role == "section_headings":
            color = (0, 0, 255)  # Red for titles
            thickness = 3
            label = "section_headings"
        else:
            color = (0, 255, 0)  # Green for text
            thickness = 2
            label = "text"

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
        if not hasattr(f, "box") or not f.box:
            continue

        x1, y1, x2, y2 = [int(v) for v in f.box]
        color = (255, 0, 0)  # Blue for figures
        thickness = 3

        cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
        cv2.putText(
            img,
            "figure",
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
    from src.ocr_yomitoku import get_analyzer
    from src.yomitoku_io import save_yomitoku_results

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
            print("  → Failed to load image")
            continue

        results, _, _ = analyzer(cv_img)
        page_height, page_width = cv_img.shape[:2]

        # Save results to cache
        save_yomitoku_results(output_dir, page_path.stem, results)

        # Convert to layout format
        page_layout = paragraphs_to_layout(results.paragraphs, results.figures, (page_width, page_height))
        layout_data[page_name] = page_layout

        print(
            f"  → Found {len(page_layout['regions'])} regions "
            f"({len(results.paragraphs)} paragraphs, {len(results.figures)} figures)"
        )

        # Visualize (box反映)
        vis_path = lay_dir / page_name
        visualize_layout(str(page_path), results.paragraphs, results.figures, str(vis_path))

    # Save layout.json
    layout_file = out_path / "layout.json"
    with open(layout_file, "w", encoding="utf-8") as f:
        json.dump(layout_data, f, indent=2, ensure_ascii=False)

    print("\nLayout detection complete")
    print(f"  Layout: {layout_file}")
    print(f"  Visualizations: {lay_dir}")

    return layout_data
