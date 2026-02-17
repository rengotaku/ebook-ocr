"""Layout detection - Clean naming interface.

This module provides a clean import interface for layout detection functionality.
In Phase 4, this will be reorganized into src/layout/detector.py.
"""

from __future__ import annotations

from src.ocr_yomitoku import detect_layout_yomitoku

# Export with clean name
detect_layout = detect_layout_yomitoku

__all__ = ["detect_layout"]
