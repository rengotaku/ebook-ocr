"""Core engine initialization, data classes, and filtering functions."""

from __future__ import annotations

from dataclasses import dataclass

# Lazy imports for optional dependencies
_tesseract = None
_easyocr_reader = None
_paddleocr_reader = None
_yomitoku_analyzer = None


def _get_tesseract():
    """Lazy import for pytesseract."""
    global _tesseract
    if _tesseract is None:
        import pytesseract

        _tesseract = pytesseract
    return _tesseract


def _get_easyocr_reader(lang_list: list[str] | None = None):
    """Lazy import and initialization for EasyOCR."""
    global _easyocr_reader
    if _easyocr_reader is None:
        import easyocr

        langs = lang_list or ["ja", "en"]
        _easyocr_reader = easyocr.Reader(langs, gpu=False)
    return _easyocr_reader


def _get_paddleocr_reader(lang: str = "japan"):
    """Lazy import and initialization for PaddleOCR 3.x."""
    global _paddleocr_reader
    if _paddleocr_reader is None:
        import logging

        logging.getLogger("ppocr").setLevel(logging.WARNING)
        from paddleocr import PaddleOCR

        _paddleocr_reader = PaddleOCR(
            lang=lang,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            enable_mkldnn=False,
        )
    return _paddleocr_reader


def _get_yomitoku_analyzer(device: str = "cpu"):
    """Lazy import and initialization for Yomitoku."""
    global _yomitoku_analyzer
    if _yomitoku_analyzer is None:
        from yomitoku import DocumentAnalyzer

        _yomitoku_analyzer = DocumentAnalyzer(
            visualize=False,
            device=device,
        )
    return _yomitoku_analyzer


@dataclass
class TextWithBox:
    """Text with bounding box and confidence."""

    text: str
    bbox: tuple[int, int, int, int]  # (x1, y1, x2, y2)
    confidence: float

    @property
    def y_center(self) -> float:
        """Vertical center position for line alignment."""
        return (self.bbox[1] + self.bbox[3]) / 2.0


@dataclass
class EngineResult:
    """Result from a single OCR engine."""

    engine: str
    items: list[TextWithBox]
    success: bool
    error: str | None = None
    figures: list[tuple[int, int, int, int]] | None = None  # Figure bboxes (x1, y1, x2, y2)
    headings: list[str] | None = None  # Section heading texts

    @property
    def text(self) -> str:
        """Concatenated text from all items."""
        return "\n".join(item.text for item in self.items)


def _is_word_inside_figures(
    word,
    figures: list,
    overlap_threshold: float = 0.5,
) -> bool:
    """Check if a word is inside any figure region.

    Args:
        word: Yomitoku word object with points or box attribute.
        figures: List of yomitoku figure objects.
        overlap_threshold: Minimum overlap ratio to consider word inside figure.

    Returns:
        True if word center is inside any figure bbox.
    """
    if not figures:
        return False

    # Get word bbox
    if hasattr(word, "points") and word.points:
        pts = word.points
        w_x1 = min(p[0] for p in pts)
        w_y1 = min(p[1] for p in pts)
        w_x2 = max(p[0] for p in pts)
        w_y2 = max(p[1] for p in pts)
    elif hasattr(word, "box") and word.box:
        w_x1, w_y1, w_x2, w_y2 = word.box
    else:
        return False

    w_cx = (w_x1 + w_x2) / 2
    w_cy = (w_y1 + w_y2) / 2

    # Check against each figure
    for fig in figures:
        if not hasattr(fig, "box") or not fig.box:
            continue
        f_x1, f_y1, f_x2, f_y2 = fig.box

        # Check if word center is inside figure bbox
        if f_x1 <= w_cx <= f_x2 and f_y1 <= w_cy <= f_y2:
            return True

    return False


def _is_item_inside_figures(
    item: TextWithBox,
    figure_bboxes: list[tuple[int, int, int, int]],
) -> bool:
    """Check if a TextWithBox item's center is inside any figure region.

    Args:
        item: TextWithBox with bbox.
        figure_bboxes: List of figure bboxes (x1, y1, x2, y2).

    Returns:
        True if item center is inside any figure bbox.
    """
    if not figure_bboxes:
        return False

    # Get item center
    i_cx = (item.bbox[0] + item.bbox[2]) / 2
    i_cy = (item.bbox[1] + item.bbox[3]) / 2

    # Check against each figure
    for f_x1, f_y1, f_x2, f_y2 in figure_bboxes:
        if f_x1 <= i_cx <= f_x2 and f_y1 <= i_cy <= f_y2:
            return True

    return False


def _filter_items_by_figures(
    result: EngineResult,
    figure_bboxes: list[tuple[int, int, int, int]],
) -> EngineResult:
    """Filter out items that are inside figure regions.

    Args:
        result: EngineResult to filter.
        figure_bboxes: List of figure bboxes to exclude.

    Returns:
        New EngineResult with items outside figures.
    """
    if not figure_bboxes or not result.items:
        return result

    filtered_items = [item for item in result.items if not _is_item_inside_figures(item, figure_bboxes)]

    return EngineResult(
        engine=result.engine,
        items=filtered_items,
        success=result.success,
        error=result.error,
        figures=result.figures,
    )
