"""Code block detection via gray background analysis."""

from __future__ import annotations

import cv2
import numpy as np


def _clip_bbox(cv_img: np.ndarray, bbox: list[int]) -> tuple[int, int, int, int] | None:
    """bbox を画像サイズにクリップし、有効な座標を返す。

    Args:
        cv_img: OpenCV BGR画像
        bbox: [x1, y1, x2, y2] リージョン境界

    Returns:
        クリップ済み (cx1, cy1, cx2, cy2)、無効なら None
    """
    img_h, img_w = cv_img.shape[:2]
    x1, y1, x2, y2 = bbox[0], bbox[1], bbox[2], bbox[3]

    cx1 = max(0, x1)
    cy1 = max(0, y1)
    cx2 = min(img_w, x2)
    cy2 = min(img_h, y2)

    if cx2 <= cx1 or cy2 <= cy1:
        return None

    return cx1, cy1, cx2, cy2


def _compute_gray_ratio(
    cropped: np.ndarray,
    saturation_max: int,
    value_min: int,
    value_max: int,
) -> float:
    """クロップ領域の灰色画素比率を計算。

    Args:
        cropped: OpenCV BGR クロップ画像
        saturation_max: 灰色と判定する彩度の上限
        value_min: 灰色と判定する明度の下限
        value_max: 灰色と判定する明度の上限

    Returns:
        灰色画素比率 (0.0-1.0)
    """
    hsv = cv2.cvtColor(cropped, cv2.COLOR_BGR2HSV)
    saturation = hsv[:, :, 1]
    value = hsv[:, :, 2]

    gray_mask = (saturation < saturation_max) & (value >= value_min) & (value <= value_max)
    return int(np.count_nonzero(gray_mask)) / gray_mask.size


def detect_gray_background(
    cv_img: np.ndarray | None,
    bbox: list[int],
    threshold: float = 0.7,
    saturation_max: int = 30,
    value_min: int = 50,
    value_max: int = 200,
) -> bool:
    """TEXT リージョンの背景が灰色かどうかを判定。

    Args:
        cv_img: OpenCV BGR画像 (cv2.imread の結果)
        bbox: [x1, y1, x2, y2] リージョン境界
        threshold: 灰色画素比率の閾値 (0.0-1.0)
        saturation_max: 灰色と判定する彩度の上限
        value_min: 灰色と判定する明度の下限
        value_max: 灰色と判定する明度の上限

    Returns:
        True if region has gray background above threshold
    """
    if cv_img is None or len(bbox) < 4:
        return False

    if bbox[2] <= bbox[0] or bbox[3] <= bbox[1]:
        return False

    coords = _clip_bbox(cv_img, bbox)
    if coords is None:
        return False

    cx1, cy1, cx2, cy2 = coords
    cropped = cv_img[cy1:cy2, cx1:cx2]
    if cropped.size == 0:
        return False

    return _compute_gray_ratio(cropped, saturation_max, value_min, value_max) >= threshold
