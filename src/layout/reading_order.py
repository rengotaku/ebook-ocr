"""Reading order sorting for detected regions.

Implements column detection and Y-coordinate sorting for
horizontal layout documents (left-to-right, top-to-bottom).
"""

from __future__ import annotations

import re

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

# 段の間（ガター）を「2 段組みの境界」とみなす条件。
# ページ幅に対する最小のすき間幅と、すき間の中心がページのどこにあるか。
COLUMN_GUTTER_MIN_RATIO = 0.04
COLUMN_GUTTER_CENTER_RANGE = (0.35, 0.65)

# ページ番号だけの行（アラビア数字・ローマ数字）。数字だけの列は段ではなくページ番号の列。
PAGE_NUMBER_ONLY_RE = re.compile(r"^[\d０-９Ⅰ-ⅿivxlcIVXLC]{1,5}$")


def _sort_key(region: dict) -> tuple[int, int, int]:
    """上から下、同じ高さなら TITLE 優先、次に左から右."""
    return (
        region["bbox"][1],
        TYPE_PRIORITY.get(region["type"], 99),
        region["bbox"][0],
    )


def _find_gutter(regions: list[dict], page_width: int) -> tuple[int, int] | None:
    """本文が左右に分かれている「段の間」を探す。

    検出領域が 1 つも横切っていない x の区間のうち、最も広いものを返す。
    ページ幅の 4% 未満のすき間と、ページ中央から離れたすき間は段の間とみなさない
    （右端に寄ったすき間は、ページ番号の列との境目であることが多い）。

    Returns:
        (すき間の開始 x, 終了 x)。見つからなければ None。
    """
    width = int(page_width)
    if width <= 0 or not regions:
        return None

    covered = bytearray(width + 1)
    min_x = width
    max_x = 0
    for region in regions:
        x1, _, x2, _ = region["bbox"]
        min_x = min(min_x, int(x1))
        max_x = max(max_x, int(x2))
        for x in range(max(0, int(x1)), min(width, int(x2)) + 1):
            covered[x] = 1

    widest = (0, 0)
    run_start: int | None = None
    for x in range(max(0, min_x), min(width, max_x) + 1):
        if covered[x]:
            if run_start is not None:
                if x - run_start > widest[1] - widest[0]:
                    widest = (run_start, x)
                run_start = None
        elif run_start is None:
            run_start = x
    if run_start is not None and max_x - run_start > widest[1] - widest[0]:
        widest = (run_start, max_x)

    if widest[1] - widest[0] < page_width * COLUMN_GUTTER_MIN_RATIO:
        return None

    gutter_center = (widest[0] + widest[1]) / 2 / page_width
    low, high = COLUMN_GUTTER_CENTER_RANGE
    if not low <= gutter_center <= high:
        return None
    return widest


def _split_columns(regions: list[dict], page_width: int) -> tuple[list[dict], list[dict]] | None:
    """2 段組みと判定できたら (左段, 右段) を返す。

    次のいずれかに当てはまる場合は段組みではない（1 段組みとして扱う）:

    - 段の間が見つからない
    - 段の間をまたぐ領域がある（全幅の見出し・図など）
    - どちらか一方に領域がない
    - 片側がページ番号だけの列
    - 左右の高さが重なっていない（左右に並んでいない）
    """
    gutter = _find_gutter(regions, page_width)
    if gutter is None:
        return None

    gutter_start, gutter_end = gutter
    left = [r for r in regions if r["bbox"][2] <= gutter_start]
    right = [r for r in regions if r["bbox"][0] >= gutter_end]

    if len(left) + len(right) != len(regions):
        return None
    if not left or not right:
        return None
    if all(PAGE_NUMBER_ONLY_RE.match((r.get("text") or "").strip()) for r in right):
        return None
    if all(PAGE_NUMBER_ONLY_RE.match((r.get("text") or "").strip()) for r in left):
        return None

    left_top = min(r["bbox"][1] for r in left)
    left_bottom = max(r["bbox"][3] for r in left)
    right_top = min(r["bbox"][1] for r in right)
    right_bottom = max(r["bbox"][3] for r in right)
    if min(left_bottom, right_bottom) - max(left_top, right_top) <= 0:
        return None

    return left, right


def sort_reading_order(regions: list[dict], page_width: int) -> list[dict]:
    """Sort regions in reading order for horizontal layout.

    Algorithm:
    1. 段の間（ガター）がページ中央付近にあり、左右に本文が分かれて縦に重なるときだけ
       2 段組みとみなす
    2. 2 段組みなら 左段（上から下）→ 右段（上から下）
    3. 1 段組みなら上から下。同じ高さなら TITLE → TEXT の順、次に左から右

    以前は領域の中心 x で機械的に左右へ分けていたため、1 段組みのページでも
    下にある要素が上へ飛んでいた（#98）。

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

    columns = _split_columns(regions_copy, page_width)
    if columns is not None:
        left, right = columns
        return sorted(left, key=_sort_key) + sorted(right, key=_sort_key)

    return sorted(regions_copy, key=_sort_key)


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
