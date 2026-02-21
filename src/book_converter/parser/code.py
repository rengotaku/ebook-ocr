"""Code parser module for book converter.

Parses CODE regions from layout.json into Code dataclass instances.
"""

from __future__ import annotations

from src.book_converter.models import Code


def parse_code_region(region: dict) -> Code:
    """Parse a CODE region from layout.json into a Code dataclass.

    Args:
        region: Dictionary containing CODE region data with keys:
            - type: Region type (should be "CODE")
            - label: Region label (should be "code")
            - bbox: Bounding box [x1, y1, x2, y2]
            - confidence: Detection confidence (optional, default 1.0)
            - ocr_text: Extracted code text (optional, default "")

    Returns:
        Code dataclass instance with text and confidence.

    Example:
        >>> region = {
        ...     "type": "CODE",
        ...     "label": "code",
        ...     "bbox": [100, 200, 500, 400],
        ...     "confidence": 0.87,
        ...     "ocr_text": 'def hello():\\n    print("Hello, World!")',
        ... }
        >>> code = parse_code_region(region)
        >>> code.text
        'def hello():\\n    print("Hello, World!")'
        >>> code.confidence
        0.87
    """
    text = region.get("ocr_text", "")
    confidence = region.get("confidence", 1.0)
    return Code(text=text, confidence=confidence)
