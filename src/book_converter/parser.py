"""Parser module for book markdown to XML conversion.

Provides functions to parse Markdown content into structured data models.
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from src.book_converter.models import (
    Page,
    PageAnnouncement,
    Content,
    Heading,
    Paragraph,
    List,
    Figure,
    PageMetadata,
)


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


def parse_heading(line: str) -> Heading | None:
    """Parse a markdown heading line.

    Args:
        line: A line from the Markdown file.

    Returns:
        Heading object if the line is a heading (# - ###), None otherwise.
        Level 4+ headings are converted to level 3.

    Example:
        >>> parse_heading("# Chapter 1")
        Heading(level=1, text="Chapter 1", read_aloud=True)
        >>> parse_heading("#### Deep heading")
        Heading(level=3, text="Deep heading", read_aloud=True)
    """
    import re

    # Pattern: ^(#{1,6})\s*(.*)$
    # Must start at beginning of line (no leading whitespace)
    pattern = r"^(#{1,6})\s*(.*)$"
    match = re.match(pattern, line)

    if not match:
        return None

    markers = match.group(1)
    text = match.group(2)

    # Calculate level (1-6 from markdown, but cap at 3)
    level = len(markers)
    if level > 3:
        level = 3

    from src.book_converter.models import Heading

    return Heading(level=level, text=text, read_aloud=True)


def parse_heading_with_warning(line: str) -> tuple[Heading | None, str | None]:
    """Parse a heading and return warning if level 4+.

    Args:
        line: A line from the Markdown file.

    Returns:
        Tuple of (Heading, warning). Warning is set if level 4+ was detected.
    """
    import re

    pattern = r"^(#{1,6})\s*(.*)$"
    match = re.match(pattern, line)

    if not match:
        return (None, None)

    markers = match.group(1)
    original_level = len(markers)

    heading = parse_heading(line)

    if original_level > 3:
        warning = f"見出しlevel {original_level}階層は3階層に統合されました"
        return (heading, warning)

    return (heading, None)


def parse_paragraph(lines: list[str]) -> Paragraph | None:
    """Parse paragraph lines into a Paragraph object.

    Args:
        lines: List of paragraph lines.

    Returns:
        Paragraph object with joined text, or None if empty/whitespace only.

    Example:
        >>> parse_paragraph(["Line 1", "Line 2"])
        Paragraph(text="Line 1\\nLine 2", read_aloud=True)
    """
    if not lines:
        return None

    # Join lines and strip whitespace
    text = "\n".join(lines).strip()

    if not text:
        return None

    from src.book_converter.models import Paragraph

    return Paragraph(text=text, read_aloud=True)


def parse_list(lines: list[str]) -> List | None:
    """Parse list lines into a List object.

    Args:
        lines: List of lines containing list items (- or * markers).

    Returns:
        List object with items tuple, or None if empty.

    Example:
        >>> parse_list(["- Item 1", "- Item 2"])
        List(items=("Item 1", "Item 2"), read_aloud=True)
    """
    import re

    if not lines:
        return None

    items = []
    # Pattern: optional leading spaces, then - or *, then space, then content
    pattern = r"^\s*[-*]\s+(.*)$"

    for line in lines:
        match = re.match(pattern, line)
        if match:
            item_text = match.group(1)
            items.append(item_text)

    if not items:
        return None

    from src.book_converter.models import List

    return List(items=tuple(items), read_aloud=True)


def parse_figure_comment(line: str) -> str | None:
    """Parse a figure comment line to extract the file path.

    Args:
        line: A line from the Markdown file.

    Returns:
        File path if the line is a figure comment, None otherwise.

    Example:
        >>> parse_figure_comment("<!-- FIGURE: path/to/image.png -->")
        "path/to/image.png"
        >>> parse_figure_comment("<!-- figure: image.jpg -->")
        "image.jpg"
    """
    import re

    # Pattern: <!-- FIGURE: path --> (case insensitive)
    pattern = r"<!--\s*[Ff][Ii][Gg][Uu][Rr][Ee]:\s*(.+?)\s*-->"
    match = re.search(pattern, line)

    if match:
        path = match.group(1).strip()
        return path if path else None

    return None


def parse_figure(lines: list[str]) -> Figure | None:
    """Parse figure comment and description into a Figure object.

    Args:
        lines: List of lines that may contain a figure comment and description.

    Returns:
        Figure object if a figure comment is found, None otherwise.

    Example:
        >>> lines = [
        ...     "<!-- FIGURE: image.png -->",
        ...     "**図のタイトル**",
        ...     "図の説明文です。"
        ... ]
        >>> fig = parse_figure(lines)
        >>> fig.file
        'image.png'
    """
    if not lines:
        return None

    # Find figure comment
    file_path = None
    for line in lines:
        file_path = parse_figure_comment(line)
        if file_path:
            break

    if not file_path:
        return None

    # Extract caption and description from remaining lines
    caption = ""
    description_lines = []

    for line in lines:
        # Skip the figure comment line
        if parse_figure_comment(line):
            continue

        # Empty lines
        if not line.strip():
            continue

        # Check for bold text (caption): **text**
        import re

        bold_pattern = r"\*\*(.+?)\*\*"
        match = re.search(bold_pattern, line)

        if match and not caption:
            # First bold text becomes caption
            caption = match.group(1)
        elif line.strip():
            # Other non-empty lines become description
            description_lines.append(line.strip())

    description = "\n".join(description_lines) if description_lines else ""

    return Figure(
        file=file_path,
        caption=caption,
        description=description,
        read_aloud="optional",
    )


def parse_page_metadata(text: str) -> PageMetadata | None:
    """Parse page metadata from text.

    Args:
        text: Text that may contain page metadata (e.g., "はじめに 1 / 3").

    Returns:
        PageMetadata object if valid format is found, None otherwise.

    Example:
        >>> parse_page_metadata("はじめに 1 / 3")
        PageMetadata(text='はじめに 1 / 3', meta_type='chapter-page',
                     section_name='はじめに', current=1, total=3)
        >>> parse_page_metadata("第1節 5 / 10")
        PageMetadata(text='第1節 5 / 10', meta_type='section-page', ...)
    """
    import re

    # Pattern: [optional section name] N / M
    # section name is optional, numbers are required
    pattern = r"^(.*?)\s*(\d+)\s*/\s*(\d+)\s*$"
    match = re.match(pattern, text.strip())

    if not match:
        return None

    section_name = match.group(1).strip()
    current = int(match.group(2))
    total = int(match.group(3))

    # Determine meta_type based on section_name
    meta_type = "chapter-page"  # Default
    if "節" in section_name:
        meta_type = "section-page"
    elif not section_name:
        # No section name means unknown type
        meta_type = "chapter-page"

    return PageMetadata(
        text=text,
        meta_type=meta_type,
        section_name=section_name,
        current=current,
        total=total,
    )


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
