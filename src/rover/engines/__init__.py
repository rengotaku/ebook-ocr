"""OCR engine wrappers with bounding box support.

Provides unified interface for multiple OCR engines:
- Yomitoku (Japanese-specialized)
- PaddleOCR (high accuracy)
- EasyOCR (neural network-based)
- Tesseract (legacy, excluded from ROVER by default)

All engines return results with bounding box information.
"""

from __future__ import annotations

# Re-export public API
from .core import EngineResult, TextWithBox
from .runners import (
    run_all_engines,
    run_easyocr_with_boxes,
    run_paddleocr_with_boxes,
    run_tesseract_with_boxes,
    run_yomitoku_with_boxes,
)

__all__ = [
    "TextWithBox",
    "EngineResult",
    "run_yomitoku_with_boxes",
    "run_paddleocr_with_boxes",
    "run_easyocr_with_boxes",
    "run_tesseract_with_boxes",
    "run_all_engines",
]
