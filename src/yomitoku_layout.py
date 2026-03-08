"""Layout detection utilities using Yomitoku.

Helper functions for layout detection and visualization.
Extracted from ocr_yomitoku.py to reduce file size.
"""

from __future__ import annotations

import json
from pathlib import Path

import cv2

from src.layout.detector import paragraphs_to_layout, visualize_layout


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
        page_layout = paragraphs_to_layout(
            results.paragraphs, results.figures, (page_width, page_height), cv_img=cv_img
        )
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
