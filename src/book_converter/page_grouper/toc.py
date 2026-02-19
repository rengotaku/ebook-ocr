"""TOC parsing and validation functions."""

from __future__ import annotations

from xml.etree import ElementTree as ET

from src.book_converter.errors import PageValidationError

from .models import TOCEntry


def _normalize_level(level: str) -> int:
    """Normalize level attribute from numeric or string format.

    Args:
        level: Level attribute value ("1", "2", "3" or "chapter", "section", etc.)

    Returns:
        Normalized level as int (1=chapter, 2=section, 3=subsection)
    """
    # Numeric string to int
    if level.isdigit():
        level_int = int(level)
        return min(level_int, 3)  # Cap at 3 for subsection

    # String to int mapping
    string_map = {
        "chapter": 1,
        "section": 2,
        "subsection": 3,
        "other": 1,  # "other" maps to chapter level
    }
    return string_map.get(level, 1)


def parse_toc(toc_element: ET.Element) -> list[TOCEntry]:
    """Parse TOC XML element into list of TOCEntry.

    Args:
        toc_element: XML Element for <toc>

    Returns:
        List of TOCEntry objects
    """
    entries = []
    for entry in toc_element.findall("entry"):
        level_raw = entry.get("level", "")
        level = _normalize_level(level_raw)
        number = entry.get("number", "")
        title = entry.get("title", "")
        entries.append(TOCEntry(level=level, number=number, title=title))
    return entries


def validate_page_count(input_count: int, output_count: int) -> None:
    """Validate output page count against input.

    Args:
        input_count: Number of pages in input
        output_count: Number of pages in output

    Raises:
        PageValidationError: If output_count < 50% of input_count

    Returns:
        None if validation passes
    """
    if input_count == 0:
        return

    loss_ratio = (input_count - output_count) / input_count
    if loss_ratio >= 0.5:
        raise PageValidationError(
            input_count=input_count,
            output_count=output_count,
            message=f"Page validation failed: {output_count} of {input_count} pages preserved "
            f"({(1 - loss_ratio) * 100:.1f}%). At least 50% required.",
        )
