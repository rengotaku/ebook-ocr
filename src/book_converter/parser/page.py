"""Page parsing functions."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path
from typing import Iterator

from src.book_converter.models import (
    Content,
    ConversionError,
    Heading,
    List,
    MarkerType,
    Page,
    PageAnnouncement,
    PageMetadata,
    Paragraph,
    TableOfContents,
    TocEntry,
)
from src.book_converter.parser.figure import parse_figure, parse_figure_comment, parse_list
from src.book_converter.parser.heading import parse_heading, parse_heading_with_warning
from src.book_converter.parser.paragraph import parse_paragraph
from src.book_converter.parser.toc import (
    normalize_toc_line,
    parse_content_marker,
    parse_toc_lines,
    parse_toc_marker,
)
from src.book_converter.parser.utils import get_read_aloud_from_stack, is_list_line

# Optional LLM-based TOC classifier
try:
    from src.book_converter.toc_classifier import (
        classify_toc_batch_with_llm,
        is_llm_classification_enabled,
    )

    TOC_CLASSIFIER_AVAILABLE = True
except ImportError:
    TOC_CLASSIFIER_AVAILABLE = False


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
        >>> parse_page_marker("--- page_0001 ---")
        ("1", "page_0001")
    """
    # Pattern 1: --- Page N (filename) ---
    # Case-insensitive, handles extra spaces
    # Page number is required (at least one digit)
    pattern1 = r"---\s+[Pp]age\s+(\d+)\s+\((.+?)\)\s+---"
    match = re.search(pattern1, line)
    if match:
        page_number = match.group(1)
        source_file = match.group(2)
        return (page_number, source_file)

    # Pattern 2: --- page_XXXX --- (simple format)
    # Extracts page number from page_XXXX identifier
    pattern2 = r"---\s+page_(\d+)\s+---"
    match = re.search(pattern2, line)
    if match:
        page_num_str = match.group(1)
        # Remove leading zeros for page number, keep original for source_file
        page_number = str(int(page_num_str))
        source_file = f"page_{page_num_str}"
        return (page_number, source_file)

    return None


def extract_page_number(line: str, verbose: bool = False) -> tuple[str, str]:
    """Extract page number and source file from a page marker line.

    Args:
        line: A page marker line.
        verbose: If True, print debug info for unrecognized potential markers.

    Returns:
        Tuple of (page_number, source_file). Returns ("", "") if invalid.
    """
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

    # Try pattern: --- Page: filename ---
    pattern_colon = r"---\s+[Pp]age:\s*(.+?)\s*---"
    match = re.search(pattern_colon, line)
    if match:
        source_file = match.group(1).strip()
        # Extract page number from source_file (e.g., page_0001.png -> 1)
        page_num_match = re.search(r"page_(\d+)", source_file)
        if page_num_match:
            page_number = str(int(page_num_match.group(1)))
            return (page_number, source_file)
        return ("", source_file)

    # Debug: check if this looks like a page marker but wasn't recognized
    if verbose and line.strip().startswith("---") and "page" in line.lower():
        print(f"[DEBUG] Unrecognized potential page marker: {line.strip()!r}", file=sys.stderr)

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
    # Use parse_pages_with_errors and yield only pages (ignore errors and toc)
    pages, _, _ = parse_pages_with_errors(input_path)
    yield from pages


def parse_pages_with_errors(
    input_path: Path,
    verbose: bool = False,
) -> tuple[list[Page], list[ConversionError], TableOfContents | None]:
    """Parse a Markdown file into Page objects with error tracking.

    Args:
        input_path: Path to the Markdown file.
        verbose: If True, print debug info during parsing.

    Returns:
        Tuple of (pages, errors, toc). TOC is built from all pages with TOC markers.
    """
    # Enable verbose mode via environment variable
    verbose = verbose or os.environ.get("BOOK_CONVERTER_DEBUG", "").lower() in ("1", "true")

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

    # Track TOC across all pages
    all_toc_entries: list[TocEntry] = []
    toc_begin_page = ""
    toc_end_page = ""

    # Track marker stack across all pages (content/skip markers)
    marker_stack: list[str] = []

    # Debug: show first few lines to help diagnose format issues
    if verbose:
        print(f"[DEBUG] Parsing file: {input_path}", file=sys.stderr)
        print(f"[DEBUG] Total lines: {len(lines)}", file=sys.stderr)
        print("[DEBUG] First 5 lines:", file=sys.stderr)
        for i, line_text in enumerate(lines[:5], start=1):
            print(f"  {i}: {line_text!r}", file=sys.stderr)

    for line_idx, line in enumerate(lines, start=1):
        # Check if this is a page marker (including those with missing numbers)
        page_num, source_file = extract_page_number(line, verbose=verbose)
        if page_num or source_file:
            # This is a page marker
            # Save previous page if any
            if current_source_file:
                # Parse the content of the previous page
                page_obj, page_errors, toc_entries, had_toc = _parse_single_page_content(
                    current_page_number,
                    current_source_file,
                    current_page_lines,
                    page_start_line,
                    marker_stack,
                )
                pages.append(page_obj)
                errors.extend(page_errors)

                # Track TOC page range
                if had_toc and current_page_number:
                    if not toc_begin_page:
                        toc_begin_page = current_page_number
                    toc_end_page = current_page_number
                    all_toc_entries.extend(toc_entries)

                # Check for missing page number on previous page
                if not current_page_number:
                    errors.append(
                        ConversionError(
                            error_type="PAGE_NUMBER_NOT_FOUND",
                            message="ページ番号が見つかりません",
                            page_number="",
                            line_number=last_page_marker_line,
                        )
                    )

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
        page_obj, page_errors, toc_entries, had_toc = _parse_single_page_content(
            current_page_number,
            current_source_file,
            current_page_lines,
            page_start_line,
            marker_stack,
        )
        pages.append(page_obj)
        errors.extend(page_errors)

        # Track TOC page range
        if had_toc and current_page_number:
            if not toc_begin_page:
                toc_begin_page = current_page_number
            toc_end_page = current_page_number
            all_toc_entries.extend(toc_entries)

        # Check for missing page number on final page
        if not current_page_number:
            errors.append(
                ConversionError(
                    error_type="PAGE_NUMBER_NOT_FOUND",
                    message="ページ番号が見つかりません",
                    page_number="",
                    line_number=last_page_marker_line,
                )
            )

    # Build TableOfContents if any entries found
    toc = None
    if all_toc_entries:
        toc = TableOfContents(
            entries=tuple(all_toc_entries),
            begin_page=toc_begin_page,
            end_page=toc_end_page,
        )

    return (pages, errors, toc)


def _parse_single_page_content(
    page_number: str,
    source_file: str,
    lines: list[str],
    start_line: int,
    marker_stack: list[str],
) -> tuple[Page, list[ConversionError], list[TocEntry], bool]:
    """Parse the content of a single page.

    Args:
        page_number: Page number string.
        source_file: Source file name.
        lines: Lines of content for this page.
        start_line: Starting line number in the original file.
        marker_stack: Marker stack state (mutated in place, persists across pages).

    Returns:
        Tuple of (Page, errors, toc_entries, had_toc_marker).
        had_toc_marker is True if this page contained any TOC markers.
    """
    errors = []
    content_elements = []
    figures_list = []
    metadata = None
    toc_entries = []
    in_toc = False
    had_toc_marker = False  # Track if this page has any TOC markers
    # marker_stack is passed as argument (persists across pages)
    toc_lines: list[str] = []  # Collect TOC lines for merging

    # Parse content line by line
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        line_num = start_line + idx + 1

        # Check for TOC markers
        toc_marker = parse_toc_marker(line)
        if toc_marker == MarkerType.TOC_START:
            in_toc = True
            had_toc_marker = True
            toc_lines = []  # Start collecting TOC lines
            idx += 1
            continue
        elif toc_marker == MarkerType.TOC_END:
            # Process collected TOC lines
            if toc_lines:
                # Try LLM batch processing first if enabled
                if TOC_CLASSIFIER_AVAILABLE and is_llm_classification_enabled():
                    # For LLM, normalize each line but preserve structure with newlines
                    normalized_lines = [normalize_toc_line(line) for line in toc_lines]
                    # Filter out empty lines
                    normalized_lines = [line for line in normalized_lines if line.strip()]
                    raw_text = "\n".join(normalized_lines)
                    llm_entries = classify_toc_batch_with_llm(raw_text, preserve_newlines=True)
                    if llm_entries:
                        # LLM succeeded - use its results directly
                        toc_entries.extend(llm_entries)
                    else:
                        # LLM failed - fallback to rule-based
                        toc_entries.extend(parse_toc_lines(toc_lines))
                else:
                    # LLM not enabled - use rule-based
                    toc_entries.extend(parse_toc_lines(toc_lines))
            in_toc = False
            toc_lines = []
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

        # If inside TOC, collect lines for later merging and parsing
        if in_toc:
            toc_lines.append(line)
            idx += 1
            continue

        # Get current readAloud value from marker stack
        read_aloud = get_read_aloud_from_stack(marker_stack)

        # Check for deep heading warning
        heading, warning = parse_heading_with_warning(line)
        if warning is not None:
            errors.append(
                ConversionError(
                    error_type="DEEP_HEADING",
                    message=warning,
                    page_number=page_number,
                    line_number=line_num,
                )
            )

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

        # Check for list item (supports ●, •, -, *, ①, 1., etc.)
        is_list, _, _ = is_list_line(line)
        if is_list:
            # Collect consecutive list items (minimum 2 for recognition)
            list_lines = [line]
            list_idx = idx + 1
            while list_idx < len(lines):
                list_line = lines[list_idx]
                if not list_line.strip():
                    # Empty line ends list
                    break
                next_is_list, _, _ = is_list_line(list_line)
                if next_is_list:
                    list_lines.append(list_line)
                    list_idx += 1
                else:
                    # Non-list line ends list
                    break

            # Only treat as list if 2+ consecutive items
            if len(list_lines) >= 2:
                lst = parse_list(list_lines)
                if lst is not None:
                    # Apply readAloud state
                    lst = List(items=lst.items, list_type=lst.list_type, read_aloud=read_aloud)
                    content_elements.append(lst)
                idx = list_idx
                continue
            # Single item: fall through to paragraph handling

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
                # Stop at list item (check if 2+ consecutive items follow)
                is_list_item, _, _ = is_list_line(para_line)
                if is_list_item:
                    # Look ahead to see if there are 2+ consecutive list items
                    lookahead_idx = para_idx + 1
                    if lookahead_idx < len(lines):
                        next_is_list, _, _ = is_list_line(lines[lookahead_idx])
                        if next_is_list:
                            break  # This starts a real list
                    # Single list marker: treat as part of paragraph
                if parse_figure_comment(para_line) is not None:
                    break
                if parse_page_metadata(para_line.strip()) is not None:
                    break
                # Stop at markers (toc, content, skip)
                if parse_toc_marker(para_line) is not None:
                    break
                if parse_content_marker(para_line) is not None:
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

    # If TOC is still open at end of page, process collected lines
    if in_toc and toc_lines:
        # Try LLM batch processing first if enabled
        if TOC_CLASSIFIER_AVAILABLE and is_llm_classification_enabled():
            # For LLM, normalize each line but preserve structure with newlines
            normalized_lines = [normalize_toc_line(line) for line in toc_lines]
            # Filter out empty lines
            normalized_lines = [line for line in normalized_lines if line.strip()]
            raw_text = "\n".join(normalized_lines)
            llm_entries = classify_toc_batch_with_llm(raw_text, preserve_newlines=True)
            if llm_entries:
                toc_entries.extend(llm_entries)
            else:
                # LLM failed - fallback to rule-based
                toc_entries.extend(parse_toc_lines(toc_lines))
        else:
            # LLM not enabled - use rule-based
            toc_entries.extend(parse_toc_lines(toc_lines))

    # Create Page object
    # Content readAloud is true if ANY child element has readAloud=true
    content_read_aloud = any(elem.read_aloud for elem in content_elements) if content_elements else False
    content = Content(elements=tuple(content_elements), read_aloud=content_read_aloud)
    announcement = create_page_announcement(page_number)

    page = Page(
        number=page_number,
        source_file=source_file,
        content=content,
        announcement=announcement,
        figures=tuple(figures_list),
        metadata=metadata,
    )

    return (page, errors, toc_entries, had_toc_marker)
