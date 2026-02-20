"""Utility functions for integrated OCR processing.

Helper functions extracted from ocr_integrated.py to reduce file size.
"""

from __future__ import annotations

from src.ocr_ensemble import TextWithBox, bbox_contains, bbox_iou, is_garbage

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
    text_regions = [r for r in regions if r.get("type") in ["TEXT", "TITLE", "CAPTION", "FOOTNOTE"]]
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
