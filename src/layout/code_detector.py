"""Code block detection using gray background analysis and text analysis.

This module provides functionality to detect code blocks in document images
by analyzing the gray background characteristic of code regions, as well as
by analyzing text content for programming symbols and keywords.
"""

from __future__ import annotations

import numpy as np

# Extended keyword list for code detection across 25+ languages
EXTENDED_KEYWORDS: list[str] = [
    # Python
    "def ",
    "import ",
    "from ",
    "self.",
    "async ",
    "await ",
    "lambda ",
    "elif ",
    # Go
    "func ",
    "package ",
    "defer ",
    ":=",
    # Rust
    "fn ",
    "let ",
    "mut ",
    "impl ",
    "pub ",
    "struct ",
    "match ",
    # Ruby / Elixir
    "require ",
    "module ",
    "defmodule ",
    "rescue ",
    # C / C++
    "#include",
    "typedef ",
    "sizeof(",
    "std::",
    # JavaScript / TypeScript
    "const ",
    "function ",
    "=>",
    # IaC / DevOps (Dockerfile, Terraform, Kubernetes, Ansible)
    'resource "',
    "FROM ",
    "WORKDIR ",
    "RUN ",
    "COPY ",
    "CMD [",
    "EXPOSE ",
    "apiVersion:",
    "kind:",
    "spec:",
    "hosts:",
    "tasks:",
    # SQL
    "SELECT ",
    "WHERE ",
    "INSERT ",
    "CREATE ",
    # Shell
    "#!/bin/",
    "echo ",
    "${",
    # General OOP / procedural
    "class ",
    "void ",
    "private ",
    "public ",
    "return ",
    "throw ",
    "new ",
    "static ",
    "interface ",
    "extends ",
    "implements ",
    "var ",
    "val ",
]

# Code symbols used for symbol ratio calculation
_CODE_SYMBOLS: frozenset[str] = frozenset("{}();=<>[]!&|+-*/%#@^~\\")


def calc_symbol_ratio(text: str) -> float:
    """Calculate the ratio of code symbols in text.

    Counts occurrences of programming symbols: { } ( ) ; = < > [ ] ! & | + - * / % # @ ^ ~ \\
    Japanese punctuation (。、「」 etc.) is NOT counted.

    Args:
        text: Input text string

    Returns:
        Ratio of symbol characters to total characters (0.0 to 1.0).
        Returns 0.0 for empty string.
    """
    if not text:
        return 0.0

    total = len(text)
    if total == 0:
        return 0.0

    symbol_count = sum(1 for ch in text if ch in _CODE_SYMBOLS)
    return float(symbol_count) / total


def count_code_keywords(text: str) -> int:
    """Count occurrences of programming keywords in text.

    Uses EXTENDED_KEYWORDS list covering 25+ languages.
    Matching is case-insensitive to handle SQL and other uppercase conventions.

    Args:
        text: Input text string

    Returns:
        Total count of keyword occurrences found in text. Returns 0 for empty string.
    """
    if not text:
        return 0

    lower_text = text.lower()
    count = 0
    for keyword in EXTENDED_KEYWORDS:
        lower_keyword = keyword.lower()
        # Count all non-overlapping occurrences using regex for word boundary safety
        occurrences = lower_text.count(lower_keyword)
        count += occurrences

    return count


def detect_code_by_text(
    text: str | None,
    sym_threshold: float = 0.08,
    kw_threshold: int = 2,
) -> bool:
    """Detect if text content is likely code using symbol ratio OR keyword count.

    Uses OR condition: text is code if EITHER:
    - Symbol ratio > sym_threshold (default 0.08)
    - Keyword count >= kw_threshold (default 2)

    Args:
        text: Input text string, or None
        sym_threshold: Minimum symbol ratio to classify as code (exclusive)
        kw_threshold: Minimum keyword count to classify as code (inclusive)

    Returns:
        True if text is likely code, False otherwise.
        Returns False for None or empty string.
    """
    if text is None or not text:
        return False

    if calc_symbol_ratio(text) > sym_threshold:
        return True

    if count_code_keywords(text) >= kw_threshold:
        return True

    return False


def is_code_fragment(text: str | None) -> bool:
    """Identify short code-like text that is likely a fragmented code block.

    Detects short text fragments that appear as isolated code remnants, such as
    single braces ('}', '{') or OCR misreads of such characters (e.g., '3' for '}').

    Args:
        text: Input text string, or None

    Returns:
        True if text is a short code fragment, False otherwise.
        Returns False for None, empty string, whitespace-only, or text >= 20 chars.
    """
    if text is None:
        return False

    stripped = text.strip()

    if not stripped:
        return False

    if len(stripped) >= 20:
        return False

    # OCR misread patterns: '3' is commonly misread as '}'
    _OCR_MISREADS: frozenset[str] = frozenset({"3"})
    if stripped in _OCR_MISREADS:
        return True

    # High symbol ratio: short text composed mostly of code symbols
    if calc_symbol_ratio(stripped) > 0.5:
        return True

    return False


def merge_code_fragments(
    regions: list[dict],
    gap_threshold: int = 80,
) -> list[dict]:
    """Merge adjacent CODE and code-fragment regions into single CODE regions.

    Iterates through regions sorted by y-coordinate and merges consecutive
    mergeable regions (CODE type or short code fragments) when their vertical
    gap is less than gap_threshold.

    A region is "mergeable" if:
    - Its type is "CODE", OR
    - It is a TEXT/FIGURE region whose text is identified as a code fragment
      by is_code_fragment()

    A non-mergeable region breaks the merge chain.
    Merged bbox is the bounding rectangle of all merged regions.

    Args:
        regions: List of region dicts with keys: type, label, bbox, confidence, text
        gap_threshold: Maximum vertical gap (px) between adjacent mergeable regions
                       to allow merging. Default: 80. Uses strict less-than (<).

    Returns:
        New list of region dicts. Input list and input dicts are not modified.
    """
    if not regions:
        return []

    # Sort by y-coordinate (top of bbox)
    sorted_regions = sorted(regions, key=lambda r: r["bbox"][1])

    def _is_mergeable(region: dict) -> bool:
        """Check if a region is CODE or a code fragment."""
        if region["type"] == "CODE":
            return True
        return is_code_fragment(region.get("text", ""))

    def _merge_group(group: list[dict]) -> dict:
        """Merge a group of regions into a single CODE region (bounding rect)."""
        x1 = min(r["bbox"][0] for r in group)
        y1 = min(r["bbox"][1] for r in group)
        x2 = max(r["bbox"][2] for r in group)
        y2 = max(r["bbox"][3] for r in group)
        return {
            "type": "CODE",
            "label": "code",
            "bbox": [x1, y1, x2, y2],
            "confidence": group[0]["confidence"],
        }

    result: list[dict] = []
    i = 0

    while i < len(sorted_regions):
        current = sorted_regions[i]

        if not _is_mergeable(current):
            # Non-mergeable: pass through as new dict (immutable)
            result.append(dict(current))
            i += 1
            continue

        # Start accumulating a merge group
        merge_group: list[dict] = [current]
        j = i + 1

        while j < len(sorted_regions):
            candidate = sorted_regions[j]

            if not _is_mergeable(candidate):
                break

            # Check vertical gap between last region in group and candidate
            last = merge_group[-1]
            gap = candidate["bbox"][1] - last["bbox"][3]
            if gap >= gap_threshold:
                break

            merge_group.append(candidate)
            j += 1

        # Emit merged region (or single region as new dict)
        result.append(_merge_group(merge_group))
        i = j

    return result


def _clip_bbox(cv_img: np.ndarray, bbox: list[int]) -> list[int]:
    """Clip bbox coordinates to image boundaries.

    Args:
        cv_img: BGR image as numpy array
        bbox: [x1, y1, x2, y2] bounding box coordinates

    Returns:
        Clipped bbox [x1, y1, x2, y2]
    """
    h, w = cv_img.shape[:2]
    x1, y1, x2, y2 = bbox
    x1 = max(0, min(x1, w))
    y1 = max(0, min(y1, h))
    x2 = max(0, min(x2, w))
    y2 = max(0, min(y2, h))
    return [x1, y1, x2, y2]


def _compute_gray_ratio(
    cropped: np.ndarray,
    saturation_max: int = 30,
    value_min: int = 50,
    value_max: int = 200,
) -> float:
    """Compute the ratio of gray pixels in a BGR image region.

    Gray pixels are defined as: saturation < saturation_max AND value_min <= value <= value_max
    in HSV color space.

    Args:
        cropped: BGR image region as numpy array
        saturation_max: Maximum saturation value for gray (exclusive)
        value_min: Minimum brightness value for gray (inclusive)
        value_max: Maximum brightness value for gray (inclusive)

    Returns:
        Ratio of gray pixels (0.0 to 1.0)
    """
    import cv2

    hsv = cv2.cvtColor(cropped, cv2.COLOR_BGR2HSV)
    saturation = hsv[:, :, 1]
    value = hsv[:, :, 2]

    gray_mask = (saturation < saturation_max) & (value >= value_min) & (value <= value_max)
    total_pixels = gray_mask.size
    if total_pixels == 0:
        return 0.0

    return float(np.sum(gray_mask)) / total_pixels


def detect_gray_background(
    cv_img: np.ndarray | None,
    bbox: list[int],
    threshold: float = 0.7,
    saturation_max: int = 30,
    value_min: int = 50,
    value_max: int = 200,
) -> bool:
    """Detect if image region has a gray background (typical of code blocks).

    Args:
        cv_img: BGR image as numpy array, or None
        bbox: [x1, y1, x2, y2] bounding box coordinates
        threshold: Minimum ratio of gray pixels to return True (default: 0.7)
        saturation_max: Maximum HSV saturation for gray pixels (default: 30)
        value_min: Minimum HSV value (brightness) for gray pixels (default: 50)
        value_max: Maximum HSV value (brightness) for gray pixels (default: 200)

    Returns:
        True if gray pixel ratio >= threshold, False otherwise
    """
    # Guard: None image
    if cv_img is None:
        return False

    # Guard: empty or invalid bbox
    if not bbox or len(bbox) < 4:
        return False

    x1, y1, x2, y2 = bbox

    # Guard: inverted or zero-size bbox
    if x1 >= x2 or y1 >= y2:
        return False

    # Guard: entirely negative bbox (would clip to zero-size)
    h, w = cv_img.shape[:2]
    if x2 <= 0 or y2 <= 0 or x1 >= w or y1 >= h:
        return False

    # Clip bbox to image bounds
    clipped = _clip_bbox(cv_img, bbox)
    cx1, cy1, cx2, cy2 = clipped

    # After clipping, verify size is still valid
    if cx1 >= cx2 or cy1 >= cy2:
        return False

    # Crop the region
    cropped = cv_img[cy1:cy2, cx1:cx2]

    if cropped.size == 0:
        return False

    # Compute gray ratio and compare to threshold
    gray_ratio = _compute_gray_ratio(cropped, saturation_max, value_min, value_max)
    return gray_ratio >= threshold
