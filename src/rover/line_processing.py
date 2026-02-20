"""Line processing utilities for ROVER OCR.

Helper functions extracted from rover/ensemble.py to reduce file size.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from src.rover.engines import TextWithBox


@dataclass
class OCRLine:
    """Single line of OCR result."""

    items: list[TextWithBox]
    engine: str
    y_center: float
    confidence: float = 0.0

    @property
    def text(self) -> str:
        """Concatenated text from all items."""
        return "".join(item.text for item in self.items)

    @property
    def bbox(self) -> tuple[int, int, int, int]:
        """Bounding box covering all items."""
        if not self.items:
            return (0, 0, 0, 0)
        x1 = min(item.bbox[0] for item in self.items)
        y1 = min(item.bbox[1] for item in self.items)
        x2 = max(item.bbox[2] for item in self.items)
        y2 = max(item.bbox[3] for item in self.items)
        return (x1, y1, x2, y2)


@dataclass
class AlignedLine:
    """Aligned line from multiple engines."""

    lines: dict[str, OCRLine | None]  # engine -> line
    y_center: float
    voted_text: str = ""
    source_engines: list[str] = field(default_factory=list)


def is_garbage(
    text: str,
    confidence: float,
    min_confidence: float = 0.5,
) -> bool:
    """Check if text is garbage output.

    Garbage criteria:
    1. Empty or whitespace-only
    2. confidence < min_confidence
    3. No Japanese chars and len <= 5 (ASCII fragments)
    4. Same character repeated >= 5 times
    5. Punctuation only

    Args:
        text: Text to check.
        confidence: Confidence score (0.0 - 1.0).
        min_confidence: Minimum confidence threshold.

    Returns:
        True if text is garbage, False otherwise.
    """
    # 1. Empty or whitespace-only
    if not text or not text.strip():
        return True

    # 2. Low confidence
    if confidence < min_confidence:
        return True

    # 3. No Japanese chars and len <= 5
    has_japanese = any("\u3040" <= ch <= "\u30ff" or "\u4e00" <= ch <= "\u9fff" for ch in text)
    if not has_japanese and len(text) <= 5:
        return True

    # 4. Same character repeated >= 5 times
    if len(text) >= 5:
        for i in range(len(text) - 4):
            if text[i] == text[i + 1] == text[i + 2] == text[i + 3] == text[i + 4]:
                return True

    # 5. Punctuation only
    if all(not ch.isalnum() for ch in text):
        return True

    return False


def normalize_confidence(raw_conf: float, engine: str) -> float:
    """Normalize confidence to [0, 1] scale based on engine-specific range.

    Ranges (from research):
    - yomitoku: (0.4, 1.0)
    - paddleocr: (0.85, 1.0)
    - easyocr: (0.25, 1.0)
    - unknown: (0.0, 1.0)

    Args:
        raw_conf: Raw confidence from engine.
        engine: Engine name.

    Returns:
        Normalized confidence (0.0 - 1.0).
    """
    ranges = {
        "yomitoku": (0.4, 1.0),
        "paddleocr": (0.85, 1.0),
        "easyocr": (0.25, 1.0),
    }
    min_conf, max_conf = ranges.get(engine, (0.0, 1.0))
    normalized = (raw_conf - min_conf) / (max_conf - min_conf)
    return max(0.0, min(1.0, normalized))


def split_multiline_items(
    items: list[TextWithBox],
    y_gap_threshold: int = 15,
) -> list[list[TextWithBox]]:
    """Split items that span multiple physical lines.

    This handles the case where yomitoku returns a single paragraph
    that actually spans multiple physical lines (e.g., y_range=[169-277]).

    Args:
        items: List of text items (may span multiple lines).
        y_gap_threshold: Minimum y-gap to consider a new line.

    Returns:
        List of lists, each inner list is one physical line.
    """
    if not items:
        return []

    # Sort by y_center
    sorted_items = sorted(items, key=lambda x: x.y_center)

    lines: list[list[TextWithBox]] = []
    current_line: list[TextWithBox] = [sorted_items[0]]

    for item in sorted_items[1:]:
        # Check y-gap from previous item
        prev_y = current_line[-1].y_center
        if item.y_center - prev_y > y_gap_threshold:
            # New line
            lines.append(current_line)
            current_line = [item]
        else:
            current_line.append(item)

    if current_line:
        lines.append(current_line)

    return lines


def cluster_lines_by_y(
    items: list[TextWithBox],
    y_tolerance: int = 20,
) -> list[OCRLine]:
    """Cluster text items into lines by y-coordinate.

    Args:
        items: List of text items with bboxes.
        y_tolerance: Maximum vertical distance to consider same line.

    Returns:
        List of OCRLine objects.
    """
    if not items:
        return []

    # Sort by y_center
    sorted_items = sorted(items, key=lambda x: x.y_center)

    lines: list[list[TextWithBox]] = []
    current_line: list[TextWithBox] = [sorted_items[0]]

    for item in sorted_items[1:]:
        # Check if this item belongs to current line
        current_y = sum(i.y_center for i in current_line) / len(current_line)
        if abs(item.y_center - current_y) <= y_tolerance:
            current_line.append(item)
        else:
            lines.append(current_line)
            current_line = [item]

    if current_line:
        lines.append(current_line)

    # Convert to OCRLine objects
    ocr_lines: list[OCRLine] = []
    for line_items in lines:
        # Sort items in line by x-coordinate
        line_items.sort(key=lambda x: x.bbox[0])
        y_center = sum(item.y_center for item in line_items) / len(line_items)
        avg_conf = sum(item.confidence for item in line_items) / len(line_items)
        ocr_lines.append(
            OCRLine(
                items=line_items,
                engine="",  # Will be set by caller
                y_center=y_center,
                confidence=avg_conf,
            )
        )

    return ocr_lines


def align_lines_by_y(
    lines_by_engine: dict[str, list[OCRLine]],
    y_tolerance: int = 30,
) -> list[AlignedLine]:
    """Align lines from multiple engines by y-coordinate.

    Args:
        lines_by_engine: Dict mapping engine name to list of OCRLine.
        y_tolerance: Maximum vertical distance to consider same line.

    Returns:
        List of AlignedLine objects.
    """
    # Collect all unique y positions
    all_y_positions: list[tuple[float, str, int]] = []  # (y_center, engine, line_idx)
    for engine, lines in lines_by_engine.items():
        for idx, line in enumerate(lines):
            all_y_positions.append((line.y_center, engine, idx))

    # Sort by y position
    all_y_positions.sort(key=lambda x: x[0])

    # Cluster y positions
    aligned: list[AlignedLine] = []
    used_lines: set[tuple[str, int]] = set()

    i = 0
    while i < len(all_y_positions):
        y_center, engine, idx = all_y_positions[i]

        # Find all lines within tolerance
        lines_dict: dict[str, OCRLine | None] = {}
        y_sum = y_center
        count = 1

        lines_dict[engine] = lines_by_engine[engine][idx]
        used_lines.add((engine, idx))

        # Look ahead for nearby lines
        j = i + 1
        while j < len(all_y_positions):
            next_y, next_engine, next_idx = all_y_positions[j]
            if next_y - y_center <= y_tolerance:
                if next_engine not in lines_dict and (next_engine, next_idx) not in used_lines:
                    lines_dict[next_engine] = lines_by_engine[next_engine][next_idx]
                    used_lines.add((next_engine, next_idx))
                    y_sum += next_y
                    count += 1
                j += 1
            else:
                break

        avg_y = y_sum / count
        aligned.append(
            AlignedLine(
                lines=lines_dict,
                y_center=avg_y,
            )
        )

        i = j if j > i + 1 else i + 1

    return aligned
