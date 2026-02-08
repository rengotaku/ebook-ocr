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
    ConversionError,
    MarkerType,
    TocEntry,
    TableOfContents,
)


def parse_toc_marker(line: str) -> MarkerType | None:
    """Parse a TOC marker line.

    Returns MarkerType.TOC_START or TOC_END if line is a toc marker.
    Case insensitive.

    Args:
        line: A line from the Markdown file.

    Returns:
        MarkerType.TOC_START for <!-- toc -->, MarkerType.TOC_END for <!-- /toc -->,
        None otherwise.

    Example:
        >>> parse_toc_marker("<!-- toc -->")
        MarkerType.TOC_START
        >>> parse_toc_marker("<!-- /toc -->")
        MarkerType.TOC_END
        >>> parse_toc_marker("<!--   TOC   -->")
        MarkerType.TOC_START
    """
    import re

    # Pattern: <!-- [optional /]toc --> (case insensitive, flexible whitespace)
    pattern = r"<!--\s*(/?)\s*[Tt][Oo][Cc]\s*-->"
    match = re.search(pattern, line)

    if match:
        slash = match.group(1)
        return MarkerType.TOC_END if slash else MarkerType.TOC_START

    return None


def parse_content_marker(line: str) -> MarkerType | None:
    """Parse content/skip marker line.

    Returns:
        MarkerType.CONTENT_START for <!-- content -->
        MarkerType.CONTENT_END for <!-- /content -->
        MarkerType.SKIP_START for <!-- skip -->
        MarkerType.SKIP_END for <!-- /skip -->
        None otherwise

    Example:
        >>> parse_content_marker("<!-- content -->")
        MarkerType.CONTENT_START
        >>> parse_content_marker("<!-- /content -->")
        MarkerType.CONTENT_END
        >>> parse_content_marker("<!-- skip -->")
        MarkerType.SKIP_START
        >>> parse_content_marker("<!-- /skip -->")
        MarkerType.SKIP_END
    """
    import re

    # Content marker pattern
    content_pattern = r"<!--\s*(/?)\s*[Cc][Oo][Nn][Tt][Ee][Nn][Tt]\s*-->"
    match = re.search(content_pattern, line)
    if match:
        slash = match.group(1)
        return MarkerType.CONTENT_END if slash else MarkerType.CONTENT_START

    # Skip marker pattern
    skip_pattern = r"<!--\s*(/?)\s*[Ss][Kk][Ii][Pp]\s*-->"
    match = re.search(skip_pattern, line)
    if match:
        slash = match.group(1)
        return MarkerType.SKIP_END if slash else MarkerType.SKIP_START

    return None


def get_read_aloud_from_stack(stack: list[str]) -> bool:
    """Get readAloud value from marker stack.

    Args:
        stack: List of marker types ("content" or "skip")

    Returns:
        True if top of stack is "content", False otherwise

    Example:
        >>> get_read_aloud_from_stack([])
        False
        >>> get_read_aloud_from_stack(["content"])
        True
        >>> get_read_aloud_from_stack(["content", "skip"])
        False
    """
    if not stack:
        return False  # Default: readAloud=false

    top = stack[-1]
    return top == "content"


def parse_toc_entry(line: str) -> TocEntry | None:
    """Parse a TOC entry line.

    Patterns:
    - 第N章 タイトル ... ページ番号
    - N.N タイトル ... ページ番号
    - N.N.N タイトル ... ページ番号
    - その他 (はじめに, おわりに, etc.)

    Args:
        line: A line from the TOC.

    Returns:
        TocEntry if line matches a TOC pattern, None otherwise.

    Example:
        >>> parse_toc_entry("第1章 SREとは ... 15")
        TocEntry(text="SREとは", level="chapter", number="1", page="15")
        >>> parse_toc_entry("2.1 SLOの理解 ─── 30")
        TocEntry(text="SLOの理解", level="section", number="2.1", page="30")
    """
    import re

    if not line.strip():
        return None

    # Extract page number first (before removing it from title)
    page_number = ""

    # Try dot leader pattern: ... N
    dot_match = re.search(r"\.{2,}\s*(\d+)\s*$", line)
    if dot_match:
        page_number = dot_match.group(1)
        line = line[: dot_match.start()]

    # Try dash leader pattern: ─── N or --- N
    if not page_number:
        dash_match = re.search(r"[─\-]{2,}\s*(\d+)\s*$", line)
        if dash_match:
            page_number = dash_match.group(1)
            line = line[: dash_match.start()]

    # Try space leader pattern: (3+ spaces) N
    if not page_number:
        space_match = re.search(r"\s{3,}(\d+)\s*$", line)
        if space_match:
            page_number = space_match.group(1)
            line = line[: space_match.start()]

    # Now parse entry patterns
    line = line.strip()

    # Chapter pattern: 第N章 タイトル
    chapter_pattern = r"^第(\d+)章\s+(.+)$"
    match = re.match(chapter_pattern, line)
    if match:
        return TocEntry(
            text=match.group(2).strip(),
            level="chapter",
            number=match.group(1),
            page=page_number,
        )

    # Subsection pattern (must come before section): N.N.N タイトル
    subsection_pattern = r"^(\d+\.\d+\.\d+)\s+(.+)$"
    match = re.match(subsection_pattern, line)
    if match:
        return TocEntry(
            text=match.group(2).strip(),
            level="subsection",
            number=match.group(1),
            page=page_number,
        )

    # Section pattern: N.N タイトル
    section_pattern = r"^(\d+\.\d+)\s+(.+)$"
    match = re.match(section_pattern, line)
    if match:
        return TocEntry(
            text=match.group(2).strip(),
            level="section",
            number=match.group(1),
            page=page_number,
        )

    # Other pattern (no number prefix)
    if line:
        return TocEntry(
            text=line,
            level="other",
            number="",
            page=page_number,
        )

    return None


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
    # Use parse_pages_with_errors and yield only pages (ignore errors)
    pages, _ = parse_pages_with_errors(input_path)
    yield from pages


def parse_pages_with_errors(
    input_path: Path
) -> tuple[list[Page], list[ConversionError]]:
    """Parse a Markdown file into Page objects with error tracking.

    Args:
        input_path: Path to the Markdown file.

    Returns:
        Tuple of (pages, errors). Errors are collected but parsing continues.
    """
    with open(input_path, encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    pages = []
    errors = []

    current_page_number = ""
    current_source_file = ""
    current_page_lines = []
    last_page_marker_line = 0
    page_start_line = 0

    # Track TOC state across pages
    in_toc = False
    toc_entries_accumulated = []

    for line_idx, line in enumerate(lines, start=1):
        # Check if this is a page marker (including those with missing numbers)
        page_num, source_file = extract_page_number(line)
        if page_num or source_file:
            # This is a page marker
            # Save previous page if any
            if current_source_file:
                # Parse the content of the previous page
                page_obj, page_errors, in_toc, new_entries = _parse_single_page_content(
                    current_page_number,
                    current_source_file,
                    current_page_lines,
                    page_start_line,
                    in_toc,
                    toc_entries_accumulated,
                )
                pages.append(page_obj)
                errors.extend(page_errors)
                toc_entries_accumulated.extend(new_entries)

                # Check for missing page number on previous page
                if not current_page_number:
                    errors.append(ConversionError(
                        error_type="PAGE_NUMBER_NOT_FOUND",
                        message="ページ番号が見つかりません",
                        page_number="",
                        line_number=last_page_marker_line,
                    ))

            # Start new page
            current_page_number = page_num
            current_source_file = source_file
            current_page_lines = []
            last_page_marker_line = line_idx
            page_start_line = line_idx
        else:
            # Add line to current page content
            current_page_lines.append(line)

    # Save final page
    if current_source_file:
        # Parse the content of the final page
        page_obj, page_errors, in_toc, new_entries = _parse_single_page_content(
            current_page_number,
            current_source_file,
            current_page_lines,
            page_start_line,
            in_toc,
            toc_entries_accumulated,
        )
        pages.append(page_obj)
        errors.extend(page_errors)
        toc_entries_accumulated.extend(new_entries)

        # Check for missing page number on final page
        if not current_page_number:
            errors.append(ConversionError(
                error_type="PAGE_NUMBER_NOT_FOUND",
                message="ページ番号が見つかりません",
                page_number="",
                line_number=last_page_marker_line,
            ))

    return (pages, errors)


def _parse_single_page_content(
    page_number: str,
    source_file: str,
    lines: list[str],
    start_line: int,
    in_toc_initial: bool = False,
    toc_entries_accumulated: list[TocEntry] | None = None,
) -> tuple[Page, list[ConversionError], bool, list[TocEntry]]:
    """Parse the content of a single page.

    Args:
        page_number: Page number string.
        source_file: Source file name.
        lines: Lines of content for this page.
        start_line: Starting line number in the original file.
        in_toc_initial: Whether we're continuing TOC from previous page.
        toc_entries_accumulated: TOC entries from previous pages (if continuing).

    Returns:
        Tuple of (Page, list of ConversionErrors, in_toc_final, new_toc_entries).
    """
    errors = []
    content_elements = []
    figures_list = []
    metadata = None
    toc_entries = []
    in_toc = in_toc_initial
    marker_stack: list[str] = []  # Track content/skip marker state

    # Parse content line by line
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        line_num = start_line + idx + 1

        # Check for TOC markers
        toc_marker = parse_toc_marker(line)
        if toc_marker == MarkerType.TOC_START:
            in_toc = True
            idx += 1
            continue
        elif toc_marker == MarkerType.TOC_END:
            in_toc = False
            idx += 1
            continue

        # Check for content/skip markers
        content_marker = parse_content_marker(line)
        if content_marker == MarkerType.CONTENT_START:
            marker_stack.append("content")
            idx += 1
            continue
        elif content_marker == MarkerType.CONTENT_END:
            if marker_stack and marker_stack[-1] == "content":
                marker_stack.pop()
            idx += 1
            continue
        elif content_marker == MarkerType.SKIP_START:
            marker_stack.append("skip")
            idx += 1
            continue
        elif content_marker == MarkerType.SKIP_END:
            if marker_stack and marker_stack[-1] == "skip":
                marker_stack.pop()
            idx += 1
            continue

        # If inside TOC, try to parse as TOC entry
        if in_toc:
            toc_entry = parse_toc_entry(line)
            if toc_entry is not None:
                toc_entries.append(toc_entry)
            idx += 1
            continue

        # Get current readAloud value from marker stack
        read_aloud = get_read_aloud_from_stack(marker_stack)

        # Check for deep heading warning
        heading, warning = parse_heading_with_warning(line)
        if warning is not None:
            errors.append(ConversionError(
                error_type="DEEP_HEADING",
                message=warning,
                page_number=page_number,
                line_number=line_num,
            ))

        # Check for heading
        if heading is not None:
            # Apply readAloud state
            heading = Heading(level=heading.level, text=heading.text, read_aloud=read_aloud)
            content_elements.append(heading)
            idx += 1
            continue

        # Check for figure comment
        fig_path = parse_figure_comment(line)
        if fig_path is not None:
            # Collect lines for figure parsing
            fig_lines = []
            fig_idx = idx
            while fig_idx < len(lines) and fig_idx < idx + 10:  # Look ahead up to 10 lines
                fig_line = lines[fig_idx]
                if not fig_line.strip():
                    # Empty line ends figure block
                    break
                fig_lines.append(fig_line)
                fig_idx += 1

            fig = parse_figure(fig_lines)
            if fig is not None:
                figures_list.append(fig)
            idx = fig_idx
            continue

        # Check for page metadata (N / M pattern)
        page_meta = parse_page_metadata(line.strip())
        if page_meta is not None:
            metadata = page_meta
            idx += 1
            continue

        # Check for list item
        if line.strip().startswith(('-', '*')) and line.strip()[1:2] in (' ', ''):
            # Collect consecutive list items
            list_lines = []
            list_idx = idx
            while list_idx < len(lines):
                list_line = lines[list_idx]
                if list_line.strip().startswith(('-', '*')) and list_line.strip()[1:2] in (' ', ''):
                    list_lines.append(list_line)
                    list_idx += 1
                elif not list_line.strip():
                    # Empty line ends list
                    break
                else:
                    # Non-list line ends list
                    break

            lst = parse_list(list_lines)
            if lst is not None:
                # Apply readAloud state
                lst = List(items=lst.items, read_aloud=read_aloud)
                content_elements.append(lst)
            idx = list_idx
            continue

        # Check for paragraph (non-empty, non-special line)
        if line.strip():
            # Collect consecutive non-empty lines for paragraph
            para_lines = []
            para_idx = idx
            while para_idx < len(lines):
                para_line = lines[para_idx]
                # Stop at empty line, heading, list, or figure
                if not para_line.strip():
                    break
                if parse_heading(para_line) is not None:
                    break
                if para_line.strip().startswith(('-', '*')) and para_line.strip()[1:2] in (' ', ''):
                    break
                if parse_figure_comment(para_line) is not None:
                    break
                if parse_page_metadata(para_line.strip()) is not None:
                    break
                para_lines.append(para_line)
                para_idx += 1

            para = parse_paragraph(para_lines)
            if para is not None:
                # Apply readAloud state
                para = Paragraph(text=para.text, read_aloud=read_aloud)
                content_elements.append(para)
            idx = para_idx
            continue

        # Empty line, skip
        idx += 1

    # Create Page object
    # Content readAloud is true if ANY child element has readAloud=true
    content_read_aloud = any(
        elem.read_aloud for elem in content_elements
    ) if content_elements else False
    content = Content(elements=tuple(content_elements), read_aloud=content_read_aloud)
    announcement = create_page_announcement(page_number)

    # Create TableOfContents only on the page where TOC ends
    # If we're still in TOC mode, don't create the element yet
    toc = None
    if not in_toc and toc_entries:
        # TOC has ended on this page, include all accumulated entries
        all_entries = []
        if toc_entries_accumulated:
            all_entries.extend(toc_entries_accumulated)
        all_entries.extend(toc_entries)
        toc = TableOfContents(entries=tuple(all_entries), read_aloud=False)

    page = Page(
        number=page_number,
        source_file=source_file,
        content=content,
        announcement=announcement,
        figures=tuple(figures_list),
        metadata=metadata,
        toc=toc,
    )

    return (page, errors, in_toc, toc_entries)
