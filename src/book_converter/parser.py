"""Parser module for book markdown to XML conversion.

Provides functions to parse Markdown content into structured data models.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from src.book_converter.models import Page, PageAnnouncement, Content


def parse_page_marker(line: str) -> tuple[str, str] | None:
    """Parse a page marker line.

    Args:
        line: A line from the Markdown file.

    Returns:
        Tuple of (page_number, source_file) if the line is a page marker,
        None otherwise.

    Example:
        >>> parse_page_marker("--- Page 1 (page_0001.png) ---")
        ("1", "page_0001.png")
    """
    import re

    # Pattern: --- Page N (filename) ---
    # Case-insensitive, handles extra spaces
    # Page number is required (at least one digit)
    pattern = r"---\s+[Pp]age\s+(\d+)\s+\((.+?)\)\s+---"
    match = re.search(pattern, line)

    if match:
        page_number = match.group(1)
        source_file = match.group(2)
        return (page_number, source_file)

    return None


def extract_page_number(line: str) -> tuple[str, str]:
    """Extract page number and source file from a page marker line.

    Args:
        line: A page marker line.

    Returns:
        Tuple of (page_number, source_file). Returns ("", "") if invalid.
    """
    import re

    # First try the standard pattern with page number
    result = parse_page_marker(line)
    if result is not None:
        return result

    # Try pattern without page number (handles missing page numbers)
    pattern = r"---\s+[Pp]age\s+\((.+?)\)\s+---"
    match = re.search(pattern, line)
    if match:
        source_file = match.group(1)
        return ("", source_file)

    return ("", "")


def create_page_announcement(page_number: str) -> PageAnnouncement | None:
    """Create a PageAnnouncement for the given page number.

    Args:
        page_number: The page number string.

    Returns:
        PageAnnouncement with format "Nページ", or None if page_number is empty.
    """
    if not page_number:
        return None

    text = f"{page_number}ページ"
    return PageAnnouncement(text=text, format="simple")


def parse_pages(input_path: Path) -> Iterator[Page]:
    """Parse a Markdown file into Page objects.

    Args:
        input_path: Path to the Markdown file.

    Yields:
        Page objects parsed from the Markdown file.
    """
    with open(input_path, encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    current_page_number = ""
    current_source_file = ""

    for line in lines:
        # Check if this is a page marker
        marker_result = parse_page_marker(line)
        if marker_result is not None:
            # Yield previous page if any
            if current_page_number or current_source_file:
                announcement = create_page_announcement(current_page_number)
                yield Page(
                    number=current_page_number,
                    source_file=current_source_file,
                    content=Content(elements=()),
                    announcement=announcement,
                )

            # Start new page
            current_page_number, current_source_file = marker_result

    # Yield final page
    if current_page_number or current_source_file:
        announcement = create_page_announcement(current_page_number)
        yield Page(
            number=current_page_number,
            source_file=current_source_file,
            content=Content(elements=()),
            announcement=announcement,
        )
