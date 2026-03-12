"""Code block detection using gray background analysis.

This module provides functionality to detect code blocks in document images
by analyzing the gray background characteristic of code regions.
"""

from __future__ import annotations

import numpy as np


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
