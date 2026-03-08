"""Layout analysis package for document structure detection.

Modules:
- code_detector: Code block detection via gray background analysis
- detector: Layout detection using yomitoku
- figures: Figure detection using DocLayout-YOLO
- reading_order: Reading order sorting
"""

from src.layout import code_detector, detector, figures, reading_order

__all__ = ["code_detector", "detector", "figures", "reading_order"]
