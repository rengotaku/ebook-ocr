"""Utility functions for transformer module.

Helper functions for heading normalization, duplicate detection, and emphasis.
Extracted from transformer.py to reduce file size.
"""

from __future__ import annotations

import re
from xml.etree.ElementTree import Element, SubElement


def normalize_heading_for_comparison(heading_text: str) -> str:
    """Normalize heading text for comparison with container titles.

    Removes "Chapter N" or "Section N.N" prefix and normalizes whitespace.

    Args:
        heading_text: Original heading text (e.g., "Chapter 1 「企画」で失敗")

    Returns:
        Normalized text (e.g., "1 「企画」で失敗")

    Examples:
        >>> normalize_heading_for_comparison("Chapter 1 「企画」で失敗")
        '1 「企画」で失敗'
        >>> normalize_heading_for_comparison("Section 1.1 なんでもできる")
        '1.1 なんでもできる'
        >>> normalize_heading_for_comparison("すべての要求に応えてしまう")
        'すべての要求に応えてしまう'
    """
    text = heading_text

    # Remove "Chapter N" prefix (case-insensitive)
    text = re.sub(r"^[Cc][Hh][Aa][Pp][Tt][Ee][Rr]\s+(\d+)\s*", r"\1 ", text)

    # Remove "Section N.N" prefix (case-insensitive)
    text = re.sub(r"^[Ss][Ee][Cc][Tt][Ii][Oo][Nn]\s+(\d+\.\d+)\s*", r"\1 ", text)

    # Normalize whitespace (collapse multiple spaces to single space)
    text = " ".join(text.split())

    return text.strip()


def is_duplicate_heading(
    heading_text: str,
    container_number: str | None,
    container_title: str,
) -> bool:
    """Check if heading is a duplicate of the container's title.

    A heading is considered duplicate if its normalized form matches
    "{number} {title}" or just "{title}" (when number is None).

    Args:
        heading_text: The heading text to check
        container_number: The container's number (e.g., "1" or "1.1")
        container_title: The container's title

    Returns:
        True if the heading is a duplicate, False otherwise

    Examples:
        >>> is_duplicate_heading("Chapter 1 「企画」で失敗", "1", "「企画」で失敗")
        True
        >>> is_duplicate_heading("すべての要求に応えてしまう", "1.1", "なんでもできる")
        False
    """
    normalized = normalize_heading_for_comparison(heading_text)

    if container_number:
        expected = f"{container_number} {container_title}"
    else:
        expected = container_title

    return normalized == expected


def apply_emphasis(text: str, parent: Element) -> None:
    """Apply emphasis conversion to text.

    Converts **text** to <em>text</em>.

    Args:
        text: The text to process.
        parent: The parent element to add text and em children to.

    Example:
        >>> elem = Element("paragraph")
        >>> apply_emphasis("before **bold** after", elem)
        >>> elem.text
        'before '
        >>> elem.find("em").text
        'bold'
    """
    if not text:
        return

    pattern = r"\*\*(.+?)\*\*"
    parts = re.split(pattern, text)

    if len(parts) == 1:
        parent.text = text
        return

    parent.text = parts[0] if parts[0] else None

    for i in range(1, len(parts), 2):
        emphasis_text = parts[i]
        normal_text = parts[i + 1] if i + 1 < len(parts) else ""

        em = SubElement(parent, "em")
        em.text = emphasis_text
        em.tail = normal_text if normal_text else None
