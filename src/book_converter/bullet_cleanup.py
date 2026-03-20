"""Bullet marker cleanup for book converter.

Provides two post-processing functions:
1. strip_heading_markers: Remove leading bullet markers from Heading text
2. merge_bullet_paragraphs_to_lists: Convert consecutive bullet-marked Paragraphs to List
"""

from __future__ import annotations

from src.book_converter.models import (
    Heading,
    List,
    Paragraph,
)
from src.book_converter.parser.utils import BULLET_MARKERS

# Markers used for heading/paragraph cleanup
# Exclude "-" and "*" as they are standard markdown markers, not OCR artifacts
_CLEANUP_MARKERS = tuple(m for m in BULLET_MARKERS if m not in ("-", "*"))


def strip_heading_markers(heading: Heading) -> Heading:
    """Remove leading bullet marker from heading text.

    Args:
        heading: The Heading to clean.

    Returns:
        New Heading with marker stripped, or the original if no marker found.
    """
    text = heading.text
    for marker in _CLEANUP_MARKERS:
        if text.startswith(marker):
            cleaned = text[len(marker) :].lstrip()
            if cleaned:
                return Heading(
                    level=heading.level,
                    text=cleaned,
                    read_aloud=heading.read_aloud,
                    line_number=heading.line_number,
                    page=heading.page,
                )
    return heading


def _get_bullet_marker(text: str) -> str | None:
    """Extract the leading bullet marker from text, if any.

    Returns:
        The marker character, or None if no marker found.
    """
    for marker in _CLEANUP_MARKERS:
        if text.startswith(marker):
            rest = text[len(marker) :].lstrip()
            if rest:
                return marker
    return None


def _strip_marker(text: str, marker: str) -> str:
    """Strip a known marker from the start of text."""
    return text[len(marker) :].lstrip()


def merge_bullet_paragraphs_to_lists(
    elements: tuple,
) -> tuple:
    """Convert consecutive same-marker Paragraphs into List elements.

    Rules:
    - Only Paragraph elements with leading bullet markers are candidates
    - 2+ consecutive Paragraphs with the SAME marker become a List
    - Single bullet Paragraphs are left unchanged
    - Non-Paragraph elements break a run

    Args:
        elements: Tuple of content elements (Heading, Paragraph, List, etc.)

    Returns:
        New tuple with bullet runs replaced by List elements.
    """
    if not elements:
        return ()

    result: list = []
    i = 0
    n = len(elements)

    while i < n:
        elem = elements[i]

        # Only process Paragraph elements
        if not isinstance(elem, Paragraph):
            result.append(elem)
            i += 1
            continue

        marker = _get_bullet_marker(elem.text)
        if marker is None:
            result.append(elem)
            i += 1
            continue

        # Start of potential run — collect consecutive same-marker paragraphs
        run_start = i
        run_read_aloud = elem.read_aloud
        i += 1
        while i < n:
            next_elem = elements[i]
            if not isinstance(next_elem, Paragraph):
                break
            next_marker = _get_bullet_marker(next_elem.text)
            if next_marker != marker:
                break
            i += 1

        run_length = i - run_start

        if run_length >= 2:
            # Convert to List
            items = tuple(_strip_marker(elements[j].text, marker) for j in range(run_start, i))
            result.append(
                List(
                    items=items,
                    list_type="unordered",
                    read_aloud=run_read_aloud,
                )
            )
        else:
            # Single bullet paragraph — leave as-is
            result.append(elements[run_start])

    return tuple(result)
