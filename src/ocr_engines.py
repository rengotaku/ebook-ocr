"""OCR engine wrappers with bounding box support.

Provides unified interface for multiple OCR engines:
- Yomitoku (Japanese-specialized)
- PaddleOCR (high accuracy)
- EasyOCR (neural network-based)
- Tesseract (legacy, excluded from ROVER by default)

All engines return results with bounding box information.
"""

from __future__ import annotations

from dataclasses import dataclass

from PIL import Image


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

    filtered_items = [
        item for item in result.items
        if not _is_item_inside_figures(item, figure_bboxes)
    ]

    return EngineResult(
        engine=result.engine,
        items=filtered_items,
        success=result.success,
        error=result.error,
        figures=result.figures,
    )


def run_yomitoku_with_boxes(
    image: Image.Image,
    device: str = "cpu",
) -> EngineResult:
    """Run Yomitoku OCR with bounding boxes.

    Uses words instead of paragraphs to get accurate line-by-line output.
    This prevents multi-line paragraphs from being returned as single items.
    Words inside figure regions are excluded from output.

    Args:
        image: PIL Image to process.
        device: Device to use ("cuda" or "cpu").

    Returns:
        EngineResult with text and bboxes (one per physical line).
    """
    try:
        import cv2
        import numpy as np
        analyzer = _get_yomitoku_analyzer(device)

        # Convert PIL to cv2 format (BGR)
        img_array = np.array(image.convert("RGB"))
        cv_img = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

        # Run OCR
        results, _, _ = analyzer(cv_img)

        # Extract figure bboxes
        figure_bboxes: list[tuple[int, int, int, int]] = []
        for fig in results.figures:
            if hasattr(fig, "box") and fig.box:
                figure_bboxes.append((
                    int(fig.box[0]),
                    int(fig.box[1]),
                    int(fig.box[2]),
                    int(fig.box[3]),
                ))

        # Extract section headings
        headings: list[str] = []
        for p in results.paragraphs:
            if getattr(p, "role", None) == "section_headings":
                contents = getattr(p, "contents", "")
                if contents:
                    # Normalize: remove newlines, strip whitespace
                    heading_text = contents.replace("\n", " ").strip()
                    headings.append(heading_text)

        # Filter out words inside figures
        filtered_words = [
            w for w in results.words
            if not _is_word_inside_figures(w, results.figures)
        ]

        # Use words for line-level output (not paragraphs)
        items = _cluster_words_to_lines(filtered_words)

        return EngineResult(
            engine="yomitoku",
            items=items,
            success=True,
            figures=figure_bboxes if figure_bboxes else None,
            headings=headings if headings else None,
        )
    except Exception as e:
        return EngineResult(engine="yomitoku", items=[], success=False, error=str(e))


def _cluster_words_to_lines(
    words: list,
    y_tolerance: int = 15,
) -> list[TextWithBox]:
    """Cluster yomitoku words into lines by y-coordinate.

    Args:
        words: List of yomitoku word objects.
        y_tolerance: Maximum y-distance to consider same line.

    Returns:
        List of TextWithBox, one per line.
    """
    if not words:
        return []

    # Extract word data
    word_data = []
    for word in words:
        if not hasattr(word, "content") or not word.content:
            continue

        # Get y_center from points or box
        y_center = 0.0
        bbox = (0, 0, 0, 0)

        if hasattr(word, "points") and word.points:
            # points: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            pts = word.points
            x_coords = [p[0] for p in pts]
            y_coords = [p[1] for p in pts]
            bbox = (
                int(min(x_coords)),
                int(min(y_coords)),
                int(max(x_coords)),
                int(max(y_coords)),
            )
            y_center = (bbox[1] + bbox[3]) / 2.0
        elif hasattr(word, "box") and word.box:
            box = word.box
            bbox = (int(box[0]), int(box[1]), int(box[2]), int(box[3]))
            y_center = (bbox[1] + bbox[3]) / 2.0
        else:
            continue

        confidence = getattr(word, "rec_score", 1.0)
        word_data.append({
            "text": word.content,
            "bbox": bbox,
            "y_center": y_center,
            "x_left": bbox[0],
            "confidence": confidence,
        })

    if not word_data:
        return []

    # Sort by y_center
    word_data.sort(key=lambda w: w["y_center"])

    # Cluster into lines
    lines: list[list[dict]] = []
    current_line = [word_data[0]]

    for wd in word_data[1:]:
        current_y = sum(w["y_center"] for w in current_line) / len(current_line)
        if abs(wd["y_center"] - current_y) <= y_tolerance:
            current_line.append(wd)
        else:
            lines.append(current_line)
            current_line = [wd]

    if current_line:
        lines.append(current_line)

    # Convert lines to TextWithBox
    items: list[TextWithBox] = []
    for line_words in lines:
        # Sort words by x-coordinate
        line_words.sort(key=lambda w: w["x_left"])

        # Combine text
        text = "".join(w["text"] for w in line_words)

        # Combined bbox
        x1 = min(w["bbox"][0] for w in line_words)
        y1 = min(w["bbox"][1] for w in line_words)
        x2 = max(w["bbox"][2] for w in line_words)
        y2 = max(w["bbox"][3] for w in line_words)

        # Average confidence
        avg_conf = sum(w["confidence"] for w in line_words) / len(line_words)

        items.append(TextWithBox(
            text=text,
            bbox=(x1, y1, x2, y2),
            confidence=avg_conf,
        ))

    return items


def _get_paragraph_confidence(paragraph, words) -> float:
    """Get paragraph confidence from matching words.

    Args:
        paragraph: Yomitoku paragraph object
        words: List of Yomitoku word objects

    Returns:
        Minimum rec_score from matching words, or 1.0 if no match found.
    """
    if not hasattr(paragraph, "contents") or not paragraph.contents:
        return 1.0

    para_text = paragraph.contents
    matching_scores = []

    for word in words:
        if hasattr(word, "content") and hasattr(word, "rec_score"):
            # Check if word is part of this paragraph
            if word.content in para_text:
                matching_scores.append(word.rec_score)

    # Return minimum score (most conservative), or 1.0 if no matches
    return min(matching_scores) if matching_scores else 1.0


def run_paddleocr_with_boxes(
    image: Image.Image,
    lang: str = "japan",
) -> EngineResult:
    """Run PaddleOCR 3.x with bounding boxes.

    Args:
        image: PIL Image to process.
        lang: Language code for PaddleOCR.

    Returns:
        EngineResult with text and bboxes.
    """
    try:
        import numpy as np
        reader = _get_paddleocr_reader(lang)
        img_array = np.array(image)

        result = reader.predict(img_array)

        items: list[TextWithBox] = []
        if result:
            for res in result:
                texts = res.get("rec_texts", [])
                scores = res.get("rec_scores", [])
                polys = res.get("rec_polys", [])

                for i, text in enumerate(texts):
                    # Convert polygon to bbox
                    if i < len(polys):
                        poly = polys[i]
                        x_coords = [p[0] for p in poly]
                        y_coords = [p[1] for p in poly]
                        bbox = (
                            int(min(x_coords)),
                            int(min(y_coords)),
                            int(max(x_coords)),
                            int(max(y_coords)),
                        )
                    else:
                        bbox = (0, 0, 0, 0)

                    confidence = float(scores[i]) if i < len(scores) else 0.0

                    items.append(TextWithBox(
                        text=text,
                        bbox=bbox,
                        confidence=confidence,
                    ))

        return EngineResult(engine="paddleocr", items=items, success=True)
    except Exception as e:
        return EngineResult(engine="paddleocr", items=[], success=False, error=str(e))


def run_easyocr_with_boxes(
    image: Image.Image,
    lang_list: list[str] | None = None,
    apply_preprocessing: bool = True,
) -> EngineResult:
    """Run EasyOCR with bounding boxes.

    Args:
        image: PIL Image to process.
        lang_list: Language list for EasyOCR.
        apply_preprocessing: Apply CLAHE preprocessing (default: True).

    Returns:
        EngineResult with text and bboxes.
    """
    try:
        import numpy as np
        reader = _get_easyocr_reader(lang_list)
        img_array = np.array(image)

        # Apply CLAHE preprocessing if enabled
        if apply_preprocessing:
            from ocr_preprocess import apply_clahe
            img_array = apply_clahe(img_array)

        # EasyOCR returns: [(bbox, text, confidence), ...]
        results = reader.readtext(img_array, detail=1)

        items: list[TextWithBox] = []
        for bbox_points, text, confidence in results:
            # bbox_points: [[x1,y1], [x2,y2], [x3,y3], [x4,y4]]
            x_coords = [p[0] for p in bbox_points]
            y_coords = [p[1] for p in bbox_points]
            bbox = (
                int(min(x_coords)),
                int(min(y_coords)),
                int(max(x_coords)),
                int(max(y_coords)),
            )

            items.append(TextWithBox(
                text=text,
                bbox=bbox,
                confidence=float(confidence),
            ))

        return EngineResult(engine="easyocr", items=items, success=True)
    except Exception as e:
        return EngineResult(engine="easyocr", items=[], success=False, error=str(e))


def run_tesseract_with_boxes(
    image: Image.Image,
    lang: str = "jpn+eng",
) -> EngineResult:
    """Run Tesseract OCR with bounding boxes.

    Args:
        image: PIL Image to process.
        lang: Tesseract language code(s).

    Returns:
        EngineResult with text and bboxes.
    """
    try:
        pytesseract = _get_tesseract()

        # Get detailed data with boxes
        data = pytesseract.image_to_data(
            image,
            lang=lang,
            output_type=pytesseract.Output.DICT,
        )

        items: list[TextWithBox] = []
        n_boxes = len(data["text"])

        for i in range(n_boxes):
            text = data["text"][i].strip()
            if not text:
                continue

            confidence = float(data["conf"][i]) / 100.0 if data["conf"][i] != -1 else 0.0
            x, y, w, h = data["left"][i], data["top"][i], data["width"][i], data["height"][i]
            bbox = (x, y, x + w, y + h)

            items.append(TextWithBox(
                text=text,
                bbox=bbox,
                confidence=confidence,
            ))

        return EngineResult(engine="tesseract", items=items, success=True)
    except Exception as e:
        return EngineResult(engine="tesseract", items=[], success=False, error=str(e))


def run_all_engines(
    image: Image.Image,
    engines: list[str] | None = None,
    yomitoku_device: str = "cpu",
    tesseract_lang: str = "jpn+eng",
    easyocr_langs: list[str] | None = None,
    paddleocr_lang: str = "japan",
    easyocr_preprocessing: bool = True,
) -> dict[str, EngineResult]:
    """Run all specified OCR engines.

    Yomitoku is run first to detect figures. Text inside figures is excluded
    from all engine results.

    Args:
        image: PIL Image to process.
        engines: List of engine names. Default: ["yomitoku", "paddleocr", "easyocr"] (Tesseract excluded)
        yomitoku_device: Device for Yomitoku.
        tesseract_lang: Tesseract language code(s).
        easyocr_langs: EasyOCR language list.
        paddleocr_lang: PaddleOCR language code.
        easyocr_preprocessing: Apply CLAHE preprocessing to EasyOCR (default: True).

    Returns:
        Dict mapping engine name to EngineResult.
    """
    if engines is None:
        engines = ["yomitoku", "paddleocr", "easyocr"]  # Tesseract excluded by default

    results: dict[str, EngineResult] = {}

    # Run yomitoku first to get figure regions
    figure_bboxes: list[tuple[int, int, int, int]] = []
    if "yomitoku" in engines:
        results["yomitoku"] = run_yomitoku_with_boxes(image, yomitoku_device)
        if results["yomitoku"].figures:
            figure_bboxes = results["yomitoku"].figures

    # Run other engines and filter by figure regions
    for engine in engines:
        if engine == "yomitoku":
            continue  # Already run
        elif engine == "paddleocr":
            result = run_paddleocr_with_boxes(image, paddleocr_lang)
        elif engine == "easyocr":
            result = run_easyocr_with_boxes(image, easyocr_langs, easyocr_preprocessing)
        elif engine == "tesseract":
            result = run_tesseract_with_boxes(image, tesseract_lang)
        else:
            continue

        # Filter out items inside figures
        if figure_bboxes:
            result = _filter_items_by_figures(result, figure_bboxes)
        results[engine] = result

    return results
