"""Code region detection module.

Detects code blocks in layout.json by applying Guesslang code detection
to TEXT regions and reclassifying them as CODE when appropriate.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CodeRegion:
    """Represents a code region detected in layout.

    Attributes:
        bbox: Bounding box in (x1, y1, x2, y2) xyxy format
        confidence: Guesslang detection confidence (0.0-1.0)
        is_code: Whether this region is classified as code
        ocr_text: OCR-extracted text used for code detection
    """

    bbox: tuple[int, int, int, int]
    confidence: float
    is_code: bool
    ocr_text: str = ""


@dataclass(frozen=True)
class CodeDetectionResult:
    """Result of code detection for a single image.

    Attributes:
        regions: Detected code regions
        image_path: Input image path
        processing_time_ms: Processing time for performance measurement
    """

    regions: tuple[CodeRegion, ...]
    image_path: str
    processing_time_ms: float = 0.0


def is_code(text: str, threshold: float = 0.5) -> tuple[bool, float]:
    """Detect whether the given text is code using Guesslang.

    NOTE: Python 3.13 Compatibility Issue:
    Guesslang requires TensorFlow 2.5.0 which doesn't support Python 3.13.
    This implementation uses a heuristic fallback for Python 3.13.
    TODO: Replace with Guesslang when Python 3.12 support is available.

    Args:
        text: Text to analyze
        threshold: Confidence threshold for code detection (default: 0.5)

    Returns:
        Tuple of (is_code, confidence) where:
        - is_code: True if confidence >= threshold
        - confidence: Guesslang detection confidence (0.0-1.0)

    Examples:
        >>> is_code("def hello(): pass")
        (True, 0.87)
        >>> is_code("これは日本語です")
        (False, 0.12)
    """
    # Handle empty strings
    if not text or not text.strip():
        return False, 0.0

    # Try to import Guesslang, fall back to heuristics if unavailable
    try:
        from guesslang import Guess

        guess = Guess()
        language = guess.language_name(text)

        # If no language detected, it's not code
        if language is None:
            return False, 0.0

        # Get confidence scores for all languages
        scores = guess.scores(text)
        confidence = scores.get(language, 0.0)

        return confidence >= threshold, confidence

    except (ImportError, ModuleNotFoundError):
        # Fallback to heuristic-based detection for Python 3.13
        return _is_code_heuristic(text, threshold)


def _is_code_heuristic(text: str, threshold: float = 0.5) -> tuple[bool, float]:
    """Heuristic-based code detection fallback for Python 3.13.

    This is a simple pattern-based detector used when Guesslang is unavailable.

    Args:
        text: Text to analyze
        threshold: Confidence threshold

    Returns:
        Tuple of (is_code, confidence)
    """
    import re

    # Code indicators with weights
    indicators = {
        # Common programming keywords
        r"\b(def|class|import|from|function|var|let|const|public|private|static)\b": 0.3,
        # Common operators and symbols
        r"[{}()\[\];]": 0.1,
        # Assignment and comparison operators
        r"(\s*=\s*|\s*==\s*|\s*!=\s*|\s*<=\s*|\s*>=\s*)": 0.15,
        # Method calls
        r"\w+\([^)]*\)": 0.2,
        # Indentation patterns (4+ spaces or tabs)
        r"(^|\n)[ ]{4,}|\t": 0.15,
        # Common code patterns
        r"(->|=>|\.\w+|\:\s*\w+)": 0.1,
    }

    score = 0.0
    for pattern, weight in indicators.items():
        if re.search(pattern, text):
            score += weight

    # Normalize score to 0.0-1.0 range
    confidence = min(score, 1.0)

    # Check if Japanese/non-ASCII characters dominate (likely not code)
    non_ascii_ratio = len([c for c in text if ord(c) > 127]) / len(text)
    if non_ascii_ratio > 0.3:
        confidence *= 0.2  # Reduce confidence significantly

    return confidence >= threshold, confidence


def detect_code_regions(layout: dict[str, Any], threshold: float = 0.5) -> dict[str, Any]:
    """Detect code regions in layout.json and reclassify TEXT regions as CODE.

    Scans all TEXT regions in layout.json, applies Guesslang code detection,
    and reclassifies regions with confidence >= threshold as CODE type.

    Args:
        layout: Layout dictionary with "regions" and "page_size" keys
        threshold: Confidence threshold for code detection (default: 0.5)

    Returns:
        New layout dictionary with TEXT regions reclassified as CODE where appropriate.
        The original layout dictionary is not modified (immutable operation).

    Examples:
        >>> layout = {
        ...     "regions": [
        ...         {
        ...             "type": "TEXT",
        ...             "label": "plain text",
        ...             "bbox": [100, 200, 500, 400],
        ...             "confidence": 1.0,
        ...             "ocr_text": "def hello(): pass"
        ...         }
        ...     ],
        ...     "page_size": [800, 600]
        ... }
        >>> result = detect_code_regions(layout)
        >>> result["regions"][0]["type"]
        'CODE'
    """
    # Create new regions list (immutable operation)
    new_regions = []

    for region in layout.get("regions", []):
        # Only process TEXT regions
        if region.get("type") != "TEXT":
            new_regions.append(region)
            continue

        # Get OCR text for code detection
        ocr_text = region.get("ocr_text", "")

        # Apply code detection
        is_code_result, confidence = is_code(ocr_text, threshold)

        if is_code_result:
            # Reclassify as CODE
            new_region = {**region, "type": "CODE", "label": "code"}
            new_regions.append(new_region)
        else:
            # Keep as TEXT
            new_regions.append(region)

    # Return new layout dict with updated regions
    return {**layout, "regions": new_regions}
