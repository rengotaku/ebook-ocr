"""Integrated OCR: Full-page OCR with layout-based structuring.

This module implements the integrated OCR approach:
1. Run multiple OCR engines on full page (Yomitoku, PaddleOCR, Tesseract, EasyOCR)
2. Quality check and engine selection
3. Structure output using layout region information

Strategy:
- Full page OCR for maximum information capture
- Layout info for Markdown structuring (not region-level OCR)
- Yomitoku for TEXT (Japanese-specialized), PaddleOCR/Tesseract as fallback
- EasyOCR for FIGURE regions (better at embedded text)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

from src.ocr_ensemble import (
    EngineResult,
    EnsembleResult,
    TextWithBox,
    bbox_contains,
    calculate_similarity,
    create_text_mask,
    is_garbage,
    ocr_easyocr,
    ocr_paddleocr,
    ocr_paddleocr_with_boxes,
    ocr_tesseract,
    ocr_yomitoku_engine,
)


@dataclass
class IntegratedResult:
    """Result from integrated OCR processing."""

    text: str  # Final merged text
    structured: str  # Markdown structured output
    engine_results: dict[str, str]  # engine_name -> text
    selected_engine: str  # Primary engine used
    quality_flags: dict[str, bool] = field(default_factory=dict)  # engine -> is_valid


# Engine priority by region type (yomitoku is preferred for Japanese text)
ENGINE_PRIORITY = {
    "TEXT": ["yomitoku", "paddleocr", "tesseract"],
    "TITLE": ["yomitoku", "paddleocr", "tesseract"],
    "FIGURE": ["easyocr", "paddleocr", "tesseract"],
    "TABLE": ["yomitoku", "paddleocr", "tesseract"],
    "CAPTION": ["yomitoku", "paddleocr", "easyocr"],
    "FOOTNOTE": ["yomitoku", "paddleocr", "tesseract"],
    "FORMULA": ["yomitoku", "paddleocr", "tesseract"],
    "DEFAULT": ["yomitoku", "paddleocr", "tesseract"],
}


def filter_overlapping_regions(
    regions: list[dict],
    iou_threshold: float = 0.5,
    min_confidence: float = 0.4,
) -> list[dict]:
    """Filter out overlapping and low-confidence regions.

    Args:
        regions: List of YOLO regions.
        iou_threshold: IoU threshold for considering regions as overlapping.
        min_confidence: Minimum confidence threshold.

    Returns:
        Filtered list of regions (higher confidence kept for overlaps).
    """
    from src.ocr_ensemble import bbox_iou

    # Filter by confidence first
    valid = [r for r in regions if r.get("confidence", 0) >= min_confidence]

    # Sort by confidence descending
    valid.sort(key=lambda r: r.get("confidence", 0), reverse=True)

    # Keep non-overlapping regions (greedy)
    kept: list[dict] = []
    for region in valid:
        bbox = region.get("bbox", [])
        if len(bbox) != 4:
            continue

        # Check if this region overlaps significantly with any kept region
        is_overlapping = False
        for kept_region in kept:
            kept_bbox = kept_region.get("bbox", [])
            if bbox_iou(bbox, kept_bbox) > iou_threshold:
                is_overlapping = True
                break

        if not is_overlapping:
            kept.append(region)

    return kept


def group_text_by_regions(
    ocr_items: list[TextWithBox],
    regions: list[dict],
) -> list[tuple[dict, list[TextWithBox]]]:
    """Group OCR text items by YOLO regions.

    Args:
        ocr_items: List of TextWithBox from PaddleOCR.
        regions: Layout regions from YOLO (already filtered).

    Returns:
        List of (region, [items]) tuples, sorted by Y position.
    """
    # Filter and sort regions by Y position (top to bottom)
    text_regions = [
        r for r in regions
        if r.get("type") in ["TEXT", "TITLE", "CAPTION", "FOOTNOTE"]
    ]
    text_regions.sort(key=lambda r: r.get("bbox", [0, 0, 0, 0])[1])

    # Map items to regions (use lower threshold for better coverage)
    region_items: list[tuple[dict, list[TextWithBox]]] = []
    used_items: set[int] = set()

    for region in text_regions:
        bbox = region.get("bbox", [])
        if len(bbox) != 4:
            continue

        items_in_region: list[TextWithBox] = []
        for i, item in enumerate(ocr_items):
            if i in used_items:
                continue
            # Use lower threshold (0.3) for better coverage
            if bbox_contains(bbox, item.bbox, threshold=0.3):
                items_in_region.append(item)
                used_items.add(i)

        if items_in_region:
            # Sort items within region by Y position
            items_in_region.sort(key=lambda it: it.bbox[1])
            region_items.append((region, items_in_region))

    # Handle orphan items (not in any region)
    orphans = [item for i, item in enumerate(ocr_items) if i not in used_items]
    if orphans:
        # Insert orphans at appropriate Y positions among existing groups
        orphans.sort(key=lambda it: it.bbox[1])

        # Build list with Y positions for insertion
        result_with_y: list[tuple[float, dict, list[TextWithBox]]] = []
        for region, items in region_items:
            y_pos = region.get("bbox", [0, 0, 0, 0])[1]
            result_with_y.append((y_pos, region, items))

        # Add orphan groups (cluster by proximity)
        orphan_groups: list[list[TextWithBox]] = []
        current_group: list[TextWithBox] = []
        last_y = -1000

        for item in orphans:
            item_y = item.bbox[1]
            # If gap is large (>100px), start new group
            if current_group and item_y - last_y > 100:
                orphan_groups.append(current_group)
                current_group = []
            current_group.append(item)
            last_y = item.bbox[3]  # bottom of current item

        if current_group:
            orphan_groups.append(current_group)

        # Add orphan groups with pseudo-regions
        for group in orphan_groups:
            y_pos = group[0].bbox[1]
            pseudo_region = {"type": "TEXT", "bbox": [0, y_pos, 0, 0], "confidence": 0}
            result_with_y.append((y_pos, pseudo_region, group))

        # Sort all by Y position
        result_with_y.sort(key=lambda x: x[0])
        region_items = [(r, items) for _, r, items in result_with_y]

    return region_items


def structure_text_by_paragraphs(
    ocr_items: list[TextWithBox],
    regions: list[dict],
) -> str:
    """Structure OCR text into paragraphs using YOLO regions.

    Args:
        ocr_items: List of TextWithBox from PaddleOCR.
        regions: Layout regions from YOLO.

    Returns:
        Structured text with paragraph breaks and Markdown headings.
    """
    # Filter overlapping regions
    filtered_regions = filter_overlapping_regions(regions)

    # Group text by regions
    region_groups = group_text_by_regions(ocr_items, filtered_regions)

    # Build structured output
    paragraphs: list[str] = []

    for region, items in region_groups:
        region_type = region.get("type", "TEXT")
        text_lines = [item.text for item in items]
        combined = "\n".join(text_lines)

        if region_type == "TITLE":
            # Format as Markdown heading
            title_text = " ".join(text_lines)
            paragraphs.append(f"## {title_text}")
        else:
            paragraphs.append(combined)

    # Join with double newlines for paragraph separation
    return "\n\n".join(paragraphs)


def extract_titles_from_regions(
    ocr_items: list[TextWithBox],
    regions: list[dict],
) -> list[tuple[str, list[int]]]:
    """Extract title texts that fall within TITLE regions.

    Args:
        ocr_items: List of TextWithBox from PaddleOCR.
        regions: Layout regions from YOLO.

    Returns:
        List of (title_text, bbox) tuples.
    """
    title_regions = [r for r in regions if r.get("type") == "TITLE"]
    titles: list[tuple[str, list[int]]] = []

    for title_region in title_regions:
        title_bbox = title_region.get("bbox", [])
        if len(title_bbox) != 4:
            continue

        # Find OCR texts within this TITLE region
        title_texts = []
        for item in ocr_items:
            if bbox_contains(title_bbox, item.bbox, threshold=0.5):
                title_texts.append(item.text)

        if title_texts:
            # Combine texts in this title region
            combined = " ".join(title_texts)
            titles.append((combined, title_bbox))

    return titles


def structure_text_with_titles(
    text: str,
    titles: list[tuple[str, list[int]]],
) -> str:
    """Insert Markdown headings for titles into text.

    Strategy:
    - Find title text in the OCR output
    - Replace with ## {title}

    Args:
        text: Raw OCR text.
        titles: List of (title_text, bbox) tuples.

    Returns:
        Markdown structured text.
    """
    structured = text

    for title_text, _ in titles:
        # Find and replace title with Markdown heading
        # Handle partial matches and normalize whitespace
        title_normalized = " ".join(title_text.split())

        # Try exact match first
        if title_text in structured:
            structured = structured.replace(title_text, f"\n## {title_text}\n", 1)
        elif title_normalized in structured:
            structured = structured.replace(title_normalized, f"\n## {title_normalized}\n", 1)
        else:
            # Try finding by first few characters
            title_start = title_text[:20] if len(title_text) > 20 else title_text
            if title_start in structured:
                # Find the line containing this title
                lines = structured.split("\n")
                for i, line in enumerate(lines):
                    if title_start in line:
                        lines[i] = f"## {line}"
                        break
                structured = "\n".join(lines)

    # Clean up extra newlines
    while "\n\n\n" in structured:
        structured = structured.replace("\n\n\n", "\n\n")

    return structured.strip()


def select_best_engine(
    results: dict[str, str],
    region_type: str = "TEXT",
    quality_flags: dict[str, bool] | None = None,
) -> tuple[str, str]:
    """Select best engine result based on region type and quality.

    Args:
        results: Dict of engine_name -> text.
        region_type: Type of region for priority selection.
        quality_flags: Dict of engine_name -> is_valid (True if not garbage).

    Returns:
        Tuple of (selected_text, engine_name).
    """
    if quality_flags is None:
        quality_flags = {k: not is_garbage(v) for k, v in results.items()}

    priority = ENGINE_PRIORITY.get(region_type, ENGINE_PRIORITY["DEFAULT"])

    # Try engines in priority order, preferring valid results
    for engine in priority:
        if engine in results and results[engine] and quality_flags.get(engine, True):
            return results[engine], engine

    # Fallback: return longest valid result
    valid_results = {k: v for k, v in results.items() if v and quality_flags.get(k, True)}
    if valid_results:
        best = max(valid_results.items(), key=lambda x: len(x[1]))
        return best[1], best[0]

    # Last resort: return any non-empty result
    for engine, text in results.items():
        if text:
            return text, engine

    return "", "none"


def run_integrated_ocr(
    image: Image.Image | str,
    regions: list[dict] | None = None,
    tesseract_lang: str = "jpn+eng",
    easyocr_langs: list[str] | None = None,
    paddleocr_lang: str = "japan",
    device: str = "cpu",
) -> IntegratedResult:
    """Run integrated OCR on a single page.

    Process:
    1. Run Yomitoku, PaddleOCR, Tesseract, EasyOCR on full page
    2. Quality check all results
    3. Select best result

    Args:
        image: PIL Image or path to image file.
        regions: Layout regions for structuring output.
        tesseract_lang: Tesseract language code(s).
        easyocr_langs: EasyOCR language list.
        paddleocr_lang: PaddleOCR language code.
        device: Device for Yomitoku ("cpu" or "cuda").

    Returns:
        IntegratedResult with all engine results and selected output.
    """
    if isinstance(image, str):
        image = Image.open(image)

    results: dict[str, str] = {}
    quality_flags: dict[str, bool] = {}
    paddle_items: list[TextWithBox] = []

    # 1. Run full-page OCR engines
    print("    Running Yomitoku...", end="", flush=True)
    yomi_result = ocr_yomitoku_engine(image, device)
    if yomi_result.success:
        results["yomitoku"] = yomi_result.text
        quality_flags["yomitoku"] = not is_garbage(yomi_result.text)
        status = "OK" if quality_flags["yomitoku"] else "GARBAGE"
        print(f" {status} ({len(yomi_result.text)} chars)")
    else:
        print(f" FAIL: {yomi_result.error}")
        results["yomitoku"] = ""
        quality_flags["yomitoku"] = False

    print("    Running PaddleOCR...", end="", flush=True)
    paddle_items, paddle_success, paddle_error = ocr_paddleocr_with_boxes(image, paddleocr_lang)
    if paddle_success:
        paddle_text = "\n".join(item.text for item in paddle_items)
        results["paddleocr"] = paddle_text
        quality_flags["paddleocr"] = not is_garbage(paddle_text)
        print(f" OK ({len(paddle_text)} chars, {len(paddle_items)} boxes)")
    else:
        print(f" FAIL: {paddle_error}")
        results["paddleocr"] = ""
        quality_flags["paddleocr"] = False

    print("    Running Tesseract...", end="", flush=True)
    tess_result = ocr_tesseract(image, tesseract_lang)
    if tess_result.success:
        results["tesseract"] = tess_result.text
        quality_flags["tesseract"] = not is_garbage(tess_result.text)
        print(f" OK ({len(tess_result.text)} chars)")
    else:
        print(f" FAIL: {tess_result.error}")
        results["tesseract"] = ""
        quality_flags["tesseract"] = False

    print("    Running EasyOCR...", end="", flush=True)
    easy_result = ocr_easyocr(image, easyocr_langs)
    if easy_result.success:
        results["easyocr"] = easy_result.text
        quality_flags["easyocr"] = not is_garbage(easy_result.text)
        print(f" OK ({len(easy_result.text)} chars)")
    else:
        print(f" FAIL: {easy_result.error}")
        results["easyocr"] = ""
        quality_flags["easyocr"] = False

    # 2. Determine dominant region type
    dominant_type = "TEXT"
    if regions:
        type_counts: dict[str, int] = {}
        for r in regions:
            t = r.get("type", "TEXT")
            if t != "ABANDON":
                type_counts[t] = type_counts.get(t, 0) + 1
        if type_counts:
            dominant_type = max(type_counts.items(), key=lambda x: x[1])[0]

    # 3. Select best result
    selected_text, selected_engine = select_best_engine(
        results, dominant_type, quality_flags
    )

    # 4. Structure output by paragraphs using YOLO regions
    if regions and paddle_items:
        structured = structure_text_by_paragraphs(paddle_items, regions)
        # Count regions used
        filtered = filter_overlapping_regions(regions)
        title_count = sum(1 for r in filtered if r.get("type") == "TITLE")
        text_count = sum(1 for r in filtered if r.get("type") == "TEXT")
        print(f"    → Structured: {title_count} TITLE(s), {text_count} TEXT paragraph(s)")
    else:
        structured = selected_text

    return IntegratedResult(
        text=selected_text,
        structured=structured,
        engine_results=results,
        selected_engine=selected_engine,
        quality_flags=quality_flags,
    )


def run_integrated_ocr_batch(
    pages_dir: str,
    layout_file: str | None,
    output_dir: str,
    tesseract_lang: str = "jpn+eng",
    easyocr_langs: list[str] | None = None,
    paddleocr_lang: str = "japan",
    device: str = "cpu",
) -> list[tuple[str, IntegratedResult]]:
    """Run integrated OCR on all pages in a directory.

    Args:
        pages_dir: Directory containing page images.
        layout_file: Path to layout.json file (optional).
        output_dir: Directory for output files.
        tesseract_lang: Tesseract language code(s).
        easyocr_langs: EasyOCR language list.
        paddleocr_lang: PaddleOCR language code.
        device: Device for Yomitoku ("cpu" or "cuda").

    Returns:
        List of (page_name, IntegratedResult) tuples.
    """
    pages_path = Path(pages_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load layout data if provided
    layout_data: dict = {}
    if layout_file and Path(layout_file).exists():
        with open(layout_file) as f:
            layout_data = json.load(f)

    pages = sorted(pages_path.glob("*.png"))
    all_results: list[tuple[str, IntegratedResult]] = []

    print(f"Running integrated OCR on {len(pages)} pages...")

    for page_path in pages:
        page_name = page_path.name
        page_stem = page_path.stem
        print(f"\n  Processing {page_name}...")

        # Get regions for this page
        page_layout = layout_data.get(page_name, {})
        regions = page_layout.get("regions", [])

        # Run OCR
        with Image.open(page_path) as img:
            result = run_integrated_ocr(
                img,
                regions=regions,
                tesseract_lang=tesseract_lang,
                easyocr_langs=easyocr_langs,
                paddleocr_lang=paddleocr_lang,
                device=device,
            )

        # Report
        valid_engines = [e for e, v in result.quality_flags.items() if v]
        print(f"    → Selected: {result.selected_engine}")
        print(f"    → Valid engines: {', '.join(valid_engines) or 'none'}")

        # Write individual engine results
        for engine, text in result.engine_results.items():
            engine_file = output_path / f"{page_stem}_{engine}.txt"
            engine_file.write_text(text, encoding="utf-8")

        # Write structured result (with TITLE as Markdown headings)
        merged_file = output_path / f"{page_stem}.txt"
        merged_file.write_text(result.structured, encoding="utf-8")

        all_results.append((page_name, result))

    # Write combined output (structured)
    combined_path = output_path.parent / "book_integrated.txt"
    with open(combined_path, "w", encoding="utf-8") as f:
        for page_name, result in all_results:
            f.write(f"\n--- Page: {page_name} (engine: {result.selected_engine}) ---\n\n")
            f.write(result.structured)
            f.write("\n\n")

    print(f"\nIntegrated OCR complete. Output: {combined_path}")
    return all_results


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Integrated OCR (Yomitoku + PaddleOCR + Tesseract + EasyOCR)"
    )
    parser.add_argument("pages_dir", help="Directory containing page images")
    parser.add_argument("-o", "--output", default="ocr_texts", help="Output directory")
    parser.add_argument("--layout", help="Path to layout.json file (optional)")
    parser.add_argument(
        "--device",
        default="cpu",
        choices=["cpu", "cuda"],
        help="Device for Yomitoku OCR (default: cpu)",
    )
    parser.add_argument(
        "--tesseract-lang", default="jpn+eng", help="Tesseract language code(s)"
    )
    parser.add_argument(
        "--easyocr-langs", default="ja,en", help="EasyOCR languages (comma-separated)"
    )
    parser.add_argument(
        "--paddleocr-lang", default="japan", help="PaddleOCR language code"
    )
    args = parser.parse_args()

    easyocr_langs = [lang.strip() for lang in args.easyocr_langs.split(",")]

    run_integrated_ocr_batch(
        pages_dir=args.pages_dir,
        layout_file=args.layout,
        output_dir=args.output,
        tesseract_lang=args.tesseract_lang,
        easyocr_langs=easyocr_langs,
        paddleocr_lang=args.paddleocr_lang,
        device=args.device,
    )


if __name__ == "__main__":
    main()
