"""Reading order sorting for detected regions.

Implements column detection and Y-coordinate sorting for
horizontal layout documents (left-to-right, top-to-bottom).
"""

from __future__ import annotations


# TYPE_PRIORITY for sorting: TITLE comes before TEXT at same Y coordinate
TYPE_PRIORITY = {
    "TITLE": 0,
    "TEXT": 1,
    "CAPTION": 2,
    "FOOTNOTE": 3,
    "FIGURE": 4,
    "TABLE": 5,
    "FORMULA": 6,
    "ABANDON": 7,
}


def sort_reading_order(regions: list[dict], page_width: int) -> list[dict]:
    """Sort regions in reading order for horizontal layout.

    Algorithm:
    1. Column detection: Group by X coordinate center (mid_x = page_width / 2)
    2. Sort each column by Y coordinate
    3. Concatenate left column → right column
    4. Same Y coordinate: TITLE comes before TEXT

    Args:
        regions: List of regions (with type, bbox, confidence)
        page_width: Page width (for column detection)

    Returns:
        New sorted list (input is not modified - immutable)
    """
    if not regions:
        return regions

    # Immutable: don't modify the original list
    regions_copy = [r.copy() for r in regions]

    mid_x = page_width / 2
    left_col = []
    right_col = []

    for r in regions_copy:
        center_x = (r["bbox"][0] + r["bbox"][2]) / 2
        if center_x < mid_x:
            left_col.append(r)
        else:
            right_col.append(r)

    # Sort key: Y coordinate, then TYPE_PRIORITY, then X coordinate
    def sort_key(r: dict) -> tuple[int, int, int]:
        y = r["bbox"][1]
        type_priority = TYPE_PRIORITY.get(r["type"], 99)
        x = r["bbox"][0]
        return (y, type_priority, x)

    left_col.sort(key=sort_key)
    right_col.sort(key=sort_key)

    return left_col + right_col


def iou(r1: dict, r2: dict) -> float:
    """Calculate Intersection over Union (IoU) ratio for two regions.

    IoU is calculated as: intersection_area / smaller_area
    This ensures that if one region is completely inside another,
    the IoU will be 1.0 (100% overlap).

    Args:
        r1: First region
        r2: Second region

    Returns:
        IoU ratio (0.0 to 1.0)
    """
    x1 = max(r1["bbox"][0], r2["bbox"][0])
    y1 = max(r1["bbox"][1], r2["bbox"][1])
    x2 = min(r1["bbox"][2], r2["bbox"][2])
    y2 = min(r1["bbox"][3], r2["bbox"][3])

    if x1 >= x2 or y1 >= y2:
        return 0.0

    intersection = (x2 - x1) * (y2 - y1)
    area1 = (r1["bbox"][2] - r1["bbox"][0]) * (r1["bbox"][3] - r1["bbox"][1])
    area2 = (r2["bbox"][2] - r2["bbox"][0]) * (r2["bbox"][3] - r2["bbox"][1])

    return intersection / min(area1, area2)


def remove_overlaps(regions: list[dict]) -> list[dict]:
    """Detect and remove overlapping regions.

    Algorithm:
    1. Calculate overlap ratio for each region pair
    2. If overlap ratio >= 50%, remove the region with lower confidence
    3. Different types are not removed (intentional overlap)

    Args:
        regions: List of regions

    Returns:
        List of regions with overlaps removed
    """
    if not regions:
        return []

    result = []
    removed = set()

    for i, r1 in enumerate(regions):
        if i in removed:
            continue

        keep = True
        for j, r2 in enumerate(regions):
            if i >= j or j in removed:
                continue

            # Different types are not removed
            if r1["type"] != r2["type"]:
                continue

            overlap = iou(r1, r2)
            if overlap >= 0.5:
                if r1["confidence"] < r2["confidence"]:
                    keep = False
                    removed.add(i)
                    break
                else:
                    removed.add(j)

        if keep:
            result.append(r1)

    return result
