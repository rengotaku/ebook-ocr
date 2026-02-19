"""Preprocessing module for OCR engines.

Provides image preprocessing functions to improve OCR accuracy,
particularly CLAHE (Contrast Limited Adaptive Histogram Equalization)
for EasyOCR input.
"""

from __future__ import annotations

import numpy as np


def apply_clahe(
    image: np.ndarray,
    clip_limit: float = 2.0,
    tile_size: int = 8,
) -> np.ndarray:
    """Apply CLAHE preprocessing for EasyOCR.

    Args:
        image: RGB image array (H, W, 3), dtype=uint8
        clip_limit: Threshold for contrast limiting (default: 2.0)
        tile_size: Grid size for histogram equalization (default: 8)

    Returns:
        Preprocessed RGB image array (H, W, 3), dtype=uint8

    Example:
        >>> import numpy as np
        >>> img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        >>> result = apply_clahe(img)
        >>> assert result.shape == img.shape
    """
    import cv2

    # 1. RGB -> LAB変換
    lab = cv2.cvtColor(image, cv2.COLOR_RGB2LAB)

    # 2. CLAHE作成
    clahe = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(tile_size, tile_size))

    # 3. Lチャンネルに適用
    lab[:, :, 0] = clahe.apply(lab[:, :, 0])

    # 4. LAB -> RGB変換
    return cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)
