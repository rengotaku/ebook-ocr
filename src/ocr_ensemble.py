"""Ensemble OCR: Combine multiple OCR engines for improved accuracy.

This module runs multiple OCR engines and merges results using voting
to achieve higher accuracy than any single engine alone.

Supported engines:
- Yomitoku (Japanese-specialized Document AI)
- Tesseract (traditional, system install required)
- EasyOCR (neural network-based, pip install)
- PaddleOCR (neural network-based)

Output files:
- ocr_texts/{page}.txt           - Final merged result
- ocr_texts/{page}_yomitoku.txt  - Yomitoku result
- ocr_texts/{page}_tesseract.txt - Tesseract result
- ocr_texts/{page}_easyocr.txt   - EasyOCR result
"""

from __future__ import annotations

from dataclasses import dataclass, field
from difflib import SequenceMatcher
from pathlib import Path

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


@dataclass
class EngineResult:
    """Result from a single OCR engine."""

    engine: str
    text: str
    success: bool
    error: str | None = None


@dataclass
class EnsembleResult:
    """Result from ensemble OCR processing."""

    merged: str  # Final merged text
    results: dict[str, str]  # engine_name -> text
    similarity_matrix: dict[str, dict[str, float]]  # pairwise similarities
    source: str  # Which strategy was used
    votes: dict[str, int] = field(default_factory=dict)  # engine -> vote count


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


@dataclass
class TextWithBox:
    """Text with bounding box information."""

    text: str
    bbox: list[int]  # [x1, y1, x2, y2]
    confidence: float = 0.0


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


def is_garbage(text: str, min_length: int = 50, ja_ratio_threshold: float = 0.1) -> bool:
    """Check if OCR result is garbage/invalid.

    Detection rules:
    1. Same character repeated 10+ times
    2. Japanese character ratio too low (for Japanese documents)
    3. Too many special characters

    Args:
        text: OCR result text.
        min_length: Minimum text length to check ratio (short texts are not checked).
        ja_ratio_threshold: Minimum Japanese character ratio.

    Returns:
        True if text appears to be garbage.
    """
    import re

    if not text:
        return True

    # Rule 1: Same character repeated 10+ times
    if re.search(r"(.)\1{9,}", text):
        return True

    # Rule 2: Japanese character ratio too low (only for longer texts)
    if len(text) >= min_length:
        ja_chars = len(re.findall(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]", text))
        ja_ratio = ja_chars / len(text)
        if ja_ratio < ja_ratio_threshold:
            return True

    # Rule 3: Too many consecutive special characters
    if re.search(r"[^\w\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF]{10,}", text):
        return True

    return False


def bbox_iou(bbox1: list[int], bbox2: list[int]) -> float:
    """Calculate Intersection over Union (IoU) of two bboxes.

    Args:
        bbox1: [x1, y1, x2, y2]
        bbox2: [x1, y1, x2, y2]

    Returns:
        IoU value (0.0 - 1.0)
    """
    x1 = max(bbox1[0], bbox2[0])
    y1 = max(bbox1[1], bbox2[1])
    x2 = min(bbox1[2], bbox2[2])
    y2 = min(bbox1[3], bbox2[3])

    if x2 <= x1 or y2 <= y1:
        return 0.0

    # Use float to avoid overflow
    intersection = float(x2 - x1) * float(y2 - y1)
    area1 = float(bbox1[2] - bbox1[0]) * float(bbox1[3] - bbox1[1])
    area2 = float(bbox2[2] - bbox2[0]) * float(bbox2[3] - bbox2[1])
    union = area1 + area2 - intersection

    return intersection / union if union > 0 else 0.0


def bbox_contains(outer: list[int], inner: list[int], threshold: float = 0.7) -> bool:
    """Check if outer bbox contains inner bbox.

    Args:
        outer: [x1, y1, x2, y2] - the containing bbox
        inner: [x1, y1, x2, y2] - the bbox to check
        threshold: Minimum overlap ratio of inner bbox

    Returns:
        True if inner is mostly contained in outer
    """
    x1 = max(outer[0], inner[0])
    y1 = max(outer[1], inner[1])
    x2 = min(outer[2], inner[2])
    y2 = min(outer[3], inner[3])

    if x2 <= x1 or y2 <= y1:
        return False

    # Use float to avoid overflow
    intersection = float(x2 - x1) * float(y2 - y1)
    inner_area = float(inner[2] - inner[0]) * float(inner[3] - inner[1])

    return (intersection / inner_area) >= threshold if inner_area > 0 else False


def create_text_mask(
    image: Image.Image,
    regions: list[dict],
    text_types: list[str] | None = None,
    fill_color: str = "white",
) -> Image.Image:
    """Create masked image with only TEXT-like regions visible.

    Strategy: Start with white canvas, paste only TEXT regions from original.
    This ensures everything outside TEXT regions is masked.

    Args:
        image: Original PIL Image.
        regions: List of region dicts with "type" and "bbox" keys.
        text_types: Region types to keep visible. Default: ["TEXT", "TITLE", "CAPTION", "FOOTNOTE"]
        fill_color: Color to fill masked areas.

    Returns:
        Masked PIL Image with only text regions visible.
    """
    if text_types is None:
        text_types = ["TEXT", "TITLE", "CAPTION", "FOOTNOTE"]

    # Start with white canvas
    masked = Image.new("RGB", image.size, color=fill_color)

    # Paste only TEXT regions from original image
    for region in regions:
        region_type = region.get("type", "")
        if region_type in text_types:
            bbox = region.get("bbox", [])
            if len(bbox) == 4:
                x1, y1, x2, y2 = bbox
                # Crop from original and paste to masked
                text_region = image.crop((x1, y1, x2, y2))
                masked.paste(text_region, (x1, y1))

    return masked


def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity ratio between two texts."""
    if not text1 and not text2:
        return 1.0
    if not text1 or not text2:
        return 0.0
    return SequenceMatcher(None, text1, text2).ratio()


def calculate_similarity_matrix(results: dict[str, str]) -> dict[str, dict[str, float]]:
    """Calculate pairwise similarity between all engine results."""
    engines = list(results.keys())
    matrix: dict[str, dict[str, float]] = {}
    for e1 in engines:
        matrix[e1] = {}
        for e2 in engines:
            matrix[e1][e2] = calculate_similarity(results[e1], results[e2])
    return matrix


def vote_best_result(
    results: dict[str, str],
    similarity_matrix: dict[str, dict[str, float]],
    threshold: float = 0.7,
) -> tuple[str, str, dict[str, int]]:
    """Vote for the best result based on agreement between engines.

    Strategy:
    1. Calculate average similarity of each engine to others
    2. Engine with highest average similarity wins
    3. If all low similarity, prefer DeepSeek (best for Japanese)

    Returns:
        Tuple of (best_text, winning_engine, vote_counts).
    """
    engines = [e for e, t in results.items() if t]  # Only engines with results

    if not engines:
        return "", "none", {}

    if len(engines) == 1:
        return results[engines[0]], engines[0], {engines[0]: 1}

    # Calculate average agreement score for each engine
    scores: dict[str, float] = {}
    for engine in engines:
        other_sims = [similarity_matrix[engine][other] for other in engines if other != engine]
        scores[engine] = sum(other_sims) / len(other_sims) if other_sims else 0

    # Count "votes" - how many engines agree with each
    votes: dict[str, int] = {}
    for engine in engines:
        votes[engine] = sum(1 for other in engines if other != engine and similarity_matrix[engine][other] >= threshold)

    # Find winner
    max_votes = max(votes.values()) if votes else 0

    if max_votes > 0:
        # At least some agreement - pick engine with most votes
        # Tie-break by average similarity score
        winners = [e for e, v in votes.items() if v == max_votes]
        winner = max(winners, key=lambda e: scores.get(e, 0))
        return results[winner], winner, votes
    else:
        # No agreement - prefer by priority: yomitoku > paddleocr > easyocr > tesseract
        priority = ["yomitoku", "paddleocr", "easyocr", "tesseract"]
        for engine in priority:
            if engine in engines and results[engine]:
                return results[engine], engine, votes

        # Fallback to first available
        return results[engines[0]], engines[0], votes


def merge_by_voting(
    results: dict[str, str],
    threshold: float = 0.7,
) -> EnsembleResult:
    """Merge OCR results using voting strategy.

    Args:
        results: Dict of engine_name -> text.
        threshold: Similarity threshold for counting as agreement.

    Returns:
        EnsembleResult with merged text and metadata.
    """
    # Filter to successful results only
    valid_results = {k: v for k, v in results.items() if v}

    if not valid_results:
        return EnsembleResult(
            merged="",
            results=results,
            similarity_matrix={},
            source="none",
        )

    # Calculate similarities
    sim_matrix = calculate_similarity_matrix(valid_results)

    # Vote for best
    merged_text, winner, votes = vote_best_result(valid_results, sim_matrix, threshold)

    return EnsembleResult(
        merged=merged_text,
        results=results,
        similarity_matrix=sim_matrix,
        source=winner,
        votes=votes,
    )


def ocr_ensemble(
    image: Image.Image | str,
    engines: list[str] | None = None,
    tesseract_lang: str = "jpn+eng",
    easyocr_langs: list[str] | None = None,
    paddleocr_lang: str = "japan",
    device: str = "cpu",
    similarity_threshold: float = 0.7,
) -> EnsembleResult:
    """Run ensemble OCR with multiple engines.

    Args:
        image: PIL Image or path to image file.
        engines: List of engines to use. Default: ["yomitoku", "paddleocr", "tesseract"]
        tesseract_lang: Tesseract language code(s).
        easyocr_langs: EasyOCR language list.
        paddleocr_lang: PaddleOCR language code.
        device: Device for Yomitoku ("cpu" or "cuda").
        similarity_threshold: Threshold for voting agreement.

    Returns:
        EnsembleResult with merged and individual results.
    """
    if isinstance(image, str):
        image = Image.open(image)

    if engines is None:
        engines = ["yomitoku", "paddleocr", "tesseract"]

    results: dict[str, str] = {}

    # Run each engine
    for engine in engines:
        if engine == "yomitoku":
            result = ocr_yomitoku_engine(image, device)
        elif engine == "tesseract":
            result = ocr_tesseract(image, tesseract_lang)
        elif engine == "easyocr":
            result = ocr_easyocr(image, easyocr_langs)
        elif engine == "paddleocr":
            result = ocr_paddleocr(image, paddleocr_lang)
        else:
            continue

        if result.success:
            results[engine] = result.text
        else:
            print(f"    {engine} failed: {result.error}")
            results[engine] = ""

    # Merge by voting
    return merge_by_voting(results, similarity_threshold)


def run_ensemble_ocr(
    pages_dir: str,
    output_dir: str,
    engines: list[str] | None = None,
    tesseract_lang: str = "jpn+eng",
    easyocr_langs: list[str] | None = None,
    device: str = "cpu",
) -> list[tuple[str, EnsembleResult]]:
    """Run ensemble OCR on all pages in a directory.

    Args:
        pages_dir: Directory containing page images.
        output_dir: Directory for output text files.
        engines: List of engines to use.
        tesseract_lang: Tesseract language code(s).
        easyocr_langs: EasyOCR language list.
        device: Device for Yomitoku ("cpu" or "cuda").

    Returns:
        List of (page_name, EnsembleResult) tuples.
    """
    if engines is None:
        engines = ["yomitoku", "paddleocr", "tesseract"]

    pages_path = Path(pages_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    pages = sorted(pages_path.glob("*.png"))
    all_results: list[tuple[str, EnsembleResult]] = []

    print(f"Running ensemble OCR ({', '.join(engines)}) on {len(pages)} pages...")

    for page_path in pages:
        page_name = page_path.name
        page_stem = page_path.stem
        print(f"  Processing {page_name}...")

        with Image.open(page_path) as img:
            result = ocr_ensemble(
                img,
                engines=engines,
                tesseract_lang=tesseract_lang,
                easyocr_langs=easyocr_langs,
                device=device,
            )

        # Report
        vote_str = ", ".join(f"{e}:{v}" for e, v in result.votes.items()) if result.votes else "N/A"
        print(f"    Winner: {result.source}, Votes: [{vote_str}]")

        # Write individual engine results
        for engine, text in result.results.items():
            engine_file = output_path / f"{page_stem}_{engine}.txt"
            engine_file.write_text(text, encoding="utf-8")

        # Write merged result
        merged_file = output_path / f"{page_stem}.txt"
        merged_file.write_text(result.merged, encoding="utf-8")

        file_list = ", ".join(f"{page_stem}_{e}.txt" for e in engines)
        print(f"    → Saved: {page_stem}.txt, {file_list}")

        all_results.append((page_name, result))

    # Write combined output
    combined_path = output_path.parent / "book_ensemble.txt"
    with open(combined_path, "w", encoding="utf-8") as f:
        for page_name, result in all_results:
            vote_str = ", ".join(f"{e}:{v}" for e, v in result.votes.items())
            f.write(f"\n--- Page: {page_name} (winner: {result.source}, votes: [{vote_str}]) ---\n\n")
            f.write(result.merged)
            f.write("\n\n")

    print(f"\nEnsemble OCR complete. Output: {combined_path}")
    return all_results


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Ensemble OCR (Yomitoku + PaddleOCR + Tesseract + EasyOCR)")
    parser.add_argument("pages_dir", help="Directory containing page images")
    parser.add_argument("-o", "--output", default="ocr_texts", help="Output directory")
    parser.add_argument(
        "--engines",
        default="yomitoku,paddleocr,tesseract",
        help="Comma-separated list of engines (default: yomitoku,paddleocr,tesseract)",
    )
    parser.add_argument(
        "--device",
        default="cpu",
        choices=["cpu", "cuda"],
        help="Device for Yomitoku OCR (default: cpu)",
    )
    parser.add_argument("--tesseract-lang", default="jpn+eng", help="Tesseract language code(s)")
    parser.add_argument("--easyocr-langs", default="ja,en", help="EasyOCR languages (comma-separated)")
    args = parser.parse_args()

    engines = [e.strip() for e in args.engines.split(",")]
    easyocr_langs = [lang.strip() for lang in args.easyocr_langs.split(",")]

    run_ensemble_ocr(
        pages_dir=args.pages_dir,
        output_dir=args.output,
        engines=engines,
        tesseract_lang=args.tesseract_lang,
        easyocr_langs=easyocr_langs,
        device=args.device,
    )


if __name__ == "__main__":
    main()
