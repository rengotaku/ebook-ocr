"""OCR engine initialization and execution functions."""

from __future__ import annotations

from PIL import Image

from .models import EngineResult, TextWithBox

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

        # Suppress PaddleOCR verbose logging
        logging.getLogger("ppocr").setLevel(logging.WARNING)
        from paddleocr import PaddleOCR

        # PaddleOCR 3.x: disable oneDNN to avoid PIR conversion bug
        # See: https://github.com/PaddlePaddle/PaddleOCR/issues/17539
        _paddleocr_reader = PaddleOCR(
            lang=lang,
            use_doc_orientation_classify=False,
            use_doc_unwarping=False,
            use_textline_orientation=False,
            enable_mkldnn=False,  # Workaround for PaddlePaddle 3.3.0 bug
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


def ocr_tesseract(
    image: Image.Image,
    lang: str = "jpn+eng",
) -> EngineResult:
    """Run Tesseract OCR on an image."""
    try:
        pytesseract = _get_tesseract()
        config = "--psm 6"
        text = pytesseract.image_to_string(image, lang=lang, config=config)
        return EngineResult(engine="tesseract", text=text.strip(), success=True)
    except Exception as e:
        return EngineResult(engine="tesseract", text="", success=False, error=str(e))


def ocr_easyocr(
    image: Image.Image,
    lang_list: list[str] | None = None,
) -> EngineResult:
    """Run EasyOCR on an image."""
    try:
        import numpy as np

        reader = _get_easyocr_reader(lang_list)
        # Convert PIL to numpy array
        img_array = np.array(image)
        results = reader.readtext(img_array, detail=0, paragraph=True)
        text = "\n".join(results)
        return EngineResult(engine="easyocr", text=text.strip(), success=True)
    except Exception as e:
        return EngineResult(engine="easyocr", text="", success=False, error=str(e))


def ocr_paddleocr(
    image: Image.Image,
    lang: str = "japan",
) -> EngineResult:
    """Run PaddleOCR 3.x on an image.

    Args:
        image: PIL Image to process.
        lang: Language code for PaddleOCR (japan, en, ch, etc.)

    Returns:
        EngineResult with OCR text.
    """
    try:
        import numpy as np

        reader = _get_paddleocr_reader(lang)
        # Convert PIL to numpy array
        img_array = np.array(image)

        # PaddleOCR 3.x uses predict()
        result = reader.predict(img_array)

        # Extract text from PaddleOCR 3.x result
        # Result is list of OCRResult (dict-like) with 'rec_texts' key
        lines = []
        if result:
            for res in result:
                # PaddleOCR 3.x: dict-like access with 'rec_texts' key
                if "rec_texts" in res:
                    lines.extend(res["rec_texts"])

        text = "\n".join(lines)
        return EngineResult(engine="paddleocr", text=text.strip(), success=True)
    except Exception as e:
        return EngineResult(engine="paddleocr", text="", success=False, error=str(e))


def ocr_yomitoku_engine(
    image: Image.Image,
    device: str = "cpu",
) -> EngineResult:
    """Run Yomitoku OCR on an image.

    Args:
        image: PIL Image to process.
        device: Device to use ("cuda" or "cpu").

    Returns:
        EngineResult with OCR text.
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

        # Extract text from paragraphs
        paragraphs = []
        for p in results.paragraphs:
            if hasattr(p, "contents"):
                paragraphs.append(p.contents)
            elif hasattr(p, "text"):
                paragraphs.append(p.text)
            else:
                paragraphs.append(str(p))

        text = "\n\n".join(paragraphs)
        return EngineResult(engine="yomitoku", text=text.strip(), success=True)
    except Exception as e:
        return EngineResult(engine="yomitoku", text="", success=False, error=str(e))


def ocr_paddleocr_with_boxes(
    image: Image.Image,
    lang: str = "japan",
) -> tuple[list[TextWithBox], bool, str | None]:
    """Run PaddleOCR 3.x and return text with position info.

    Args:
        image: PIL Image to process.
        lang: Language code for PaddleOCR.

    Returns:
        Tuple of (list of TextWithBox, success, error_message)
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
                    # Convert polygon to bbox [x1, y1, x2, y2]
                    if i < len(polys):
                        poly = polys[i]
                        x_coords = [p[0] for p in poly]
                        y_coords = [p[1] for p in poly]
                        bbox = [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]
                    else:
                        bbox = [0, 0, 0, 0]

                    confidence = scores[i] if i < len(scores) else 0.0

                    items.append(
                        TextWithBox(
                            text=text,
                            bbox=bbox,
                            confidence=confidence,
                        )
                    )

        return items, True, None
    except Exception as e:
        return [], False, str(e)
