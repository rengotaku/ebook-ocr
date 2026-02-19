"""Page parsing functions."""

from __future__ import annotations

import os
import re
import sys

# Import for dataclass extraction
from dataclasses import dataclass
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


@dataclass
class PageAccumulator:
    """Accumulator for parsing multiple pages."""

    pages: list[Page]
    errors: list[ConversionError]
    all_toc_entries: list[TocEntry]
    toc_begin_page: str
    toc_end_page: str
    marker_stack: list[str]

    # Current page state
    current_page_number: str
    current_source_file: str
    current_page_lines: list[str]
    last_page_marker_line: int
    page_start_line: int


def _process_and_save_page(
    accumulator: PageAccumulator,
    check_missing_number: bool = False,
) -> None:
    """Process current page and save to accumulator.

    Args:
        accumulator: Page accumulator (mutated in place).
        check_missing_number: If True, add error for missing page number.
    """
    if not accumulator.current_source_file:
        return

    # Parse the content of the page
    page_obj, page_errors, toc_entries, had_toc = _parse_single_page_content(
        accumulator.current_page_number,
        accumulator.current_source_file,
        accumulator.current_page_lines,
        accumulator.page_start_line,
        accumulator.marker_stack,
    )
    accumulator.pages.append(page_obj)
    accumulator.errors.extend(page_errors)

    # Track TOC page range
    if had_toc and accumulator.current_page_number:
        if not accumulator.toc_begin_page:
            accumulator.toc_begin_page = accumulator.current_page_number
        accumulator.toc_end_page = accumulator.current_page_number
        accumulator.all_toc_entries.extend(toc_entries)

    # Check for missing page number if requested
    if check_missing_number and not accumulator.current_page_number:
        accumulator.errors.append(
            ConversionError(
                error_type="PAGE_NUMBER_NOT_FOUND",
                message="ページ番号が見つかりません",
                page_number="",
                line_number=accumulator.last_page_marker_line,
            )
        )


def _print_debug_info(input_path: Path, lines: list[str]) -> None:
    """Print debug information about the file being parsed.

    Args:
        input_path: Path to the file.
        lines: All lines from the file.
    """
    print(f"[DEBUG] Parsing file: {input_path}", file=sys.stderr)
    print(f"[DEBUG] Total lines: {len(lines)}", file=sys.stderr)
    print("[DEBUG] First 5 lines:", file=sys.stderr)
    for i, line_text in enumerate(lines[:5], start=1):
        print(f"  {i}: {line_text!r}", file=sys.stderr)


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

    # Initialize accumulator
    accumulator = PageAccumulator(
        pages=[],
        errors=[],
        all_toc_entries=[],
        toc_begin_page="",
        toc_end_page="",
        marker_stack=[],
        current_page_number="",
        current_source_file="",
        current_page_lines=[],
        last_page_marker_line=0,
        page_start_line=0,
    )

    # Debug: show first few lines to help diagnose format issues
    if verbose:
        _print_debug_info(input_path, lines)

    for line_idx, line in enumerate(lines, start=1):
        # Check if this is a page marker (including those with missing numbers)
        page_num, source_file = extract_page_number(line, verbose=verbose)
        if page_num or source_file:
            # This is a page marker
            # Save previous page if any
            _process_and_save_page(accumulator, check_missing_number=True)

            # Start new page
            accumulator.current_page_number = page_num
            accumulator.current_source_file = source_file
            accumulator.current_page_lines = []
            accumulator.last_page_marker_line = line_idx
            accumulator.page_start_line = line_idx
        else:
            # Add line to current page content
            accumulator.current_page_lines.append(line)

    # Save final page
    _process_and_save_page(accumulator, check_missing_number=True)

    # Build TableOfContents if any entries found
    toc = None
    if accumulator.all_toc_entries:
        toc = TableOfContents(
            entries=tuple(accumulator.all_toc_entries),
            begin_page=accumulator.toc_begin_page,
            end_page=accumulator.toc_end_page,
        )

    return (accumulator.pages, accumulator.errors, toc)


@dataclass
class PageParseState:
    """State for parsing a single page."""

    content_elements: list
    figures_list: list
    metadata: PageMetadata | None
    toc_entries: list[TocEntry]
    errors: list[ConversionError]
    in_toc: bool
    had_toc_marker: bool
    toc_lines: list[str]


def _process_toc_lines_with_llm_fallback(toc_lines: list[str]) -> list[TocEntry]:
    """Process TOC lines with LLM classification, fallback to rule-based.

    Args:
        toc_lines: Lines to process as TOC.

    Returns:
        List of parsed TOC entries.
    """
    if TOC_CLASSIFIER_AVAILABLE and is_llm_classification_enabled():
        # For LLM, normalize each line but preserve structure with newlines
        normalized_lines = [normalize_toc_line(line) for line in toc_lines]
        # Filter out empty lines
        normalized_lines = [line for line in normalized_lines if line.strip()]
        raw_text = "\n".join(normalized_lines)
        llm_entries = classify_toc_batch_with_llm(raw_text, preserve_newlines=True)
        if llm_entries:
            # LLM succeeded - use its results directly
            return llm_entries
        # LLM failed - fallback to rule-based
        return parse_toc_lines(toc_lines)
    # LLM not enabled - use rule-based
    return parse_toc_lines(toc_lines)


def _handle_toc_end(state: PageParseState) -> None:
    """Handle TOC end marker.

    Args:
        state: Current page parse state (mutated in place).
    """
    if state.toc_lines:
        state.toc_entries.extend(_process_toc_lines_with_llm_fallback(state.toc_lines))
    state.in_toc = False
    state.toc_lines = []


def _handle_heading(
    line: str,
    line_num: int,
    page_number: str,
    read_aloud: bool,
    state: PageParseState,
) -> Heading | None:
    """Parse and handle heading line.

    Args:
        line: Line to parse.
        line_num: Line number for error reporting.
        page_number: Page number for error reporting.
        read_aloud: Current readAloud state.
        state: Current page parse state (mutated for errors).

    Returns:
        Parsed Heading object if successful, None otherwise.
    """
    heading, warning = parse_heading_with_warning(line)
    if warning is not None:
        state.errors.append(
            ConversionError(
                error_type="DEEP_HEADING",
                message=warning,
                page_number=page_number,
                line_number=line_num,
            )
        )
    if heading is not None:
        # Apply readAloud state
        return Heading(level=heading.level, text=heading.text, read_aloud=read_aloud)
    return None


def _collect_figure_lines(lines: list[str], start_idx: int) -> list[str]:
    """Collect lines for figure parsing.

    Args:
        lines: All lines.
        start_idx: Index to start from.

    Returns:
        List of lines belonging to the figure.
    """
    fig_lines = []
    fig_idx = start_idx
    while fig_idx < len(lines) and fig_idx < start_idx + 10:  # Look ahead up to 10 lines
        fig_line = lines[fig_idx]
        if not fig_line.strip():
            # Empty line ends figure block
            break
        fig_lines.append(fig_line)
        fig_idx += 1
    return fig_lines


def _collect_list_lines(lines: list[str], start_idx: int) -> tuple[list[str], int]:
    """Collect consecutive list items.

    Args:
        lines: All lines.
        start_idx: Index to start from.

    Returns:
        Tuple of (list_lines, next_index).
    """
    list_lines = [lines[start_idx]]
    list_idx = start_idx + 1
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
    return list_lines, list_idx


def _should_stop_paragraph(para_line: str, lines: list[str], para_idx: int) -> bool:
    """Check if paragraph collection should stop.

    Args:
        para_line: Current line being checked.
        lines: All lines.
        para_idx: Current index.

    Returns:
        True if should stop, False otherwise.
    """
    # Stop at empty line
    if not para_line.strip():
        return True
    # Stop at heading
    if parse_heading(para_line) is not None:
        return True
    # Stop at list item (check if 2+ consecutive items follow)
    is_list_item, _, _ = is_list_line(para_line)
    if is_list_item:
        # Look ahead to see if there are 2+ consecutive list items
        lookahead_idx = para_idx + 1
        if lookahead_idx < len(lines):
            next_is_list, _, _ = is_list_line(lines[lookahead_idx])
            if next_is_list:
                return True  # This starts a real list
        # Single list marker: treat as part of paragraph
    # Stop at figure comment
    if parse_figure_comment(para_line) is not None:
        return True
    # Stop at page metadata
    if parse_page_metadata(para_line.strip()) is not None:
        return True
    # Stop at markers (toc, content, skip)
    if parse_toc_marker(para_line) is not None:
        return True
    if parse_content_marker(para_line) is not None:
        return True
    return False


def _collect_paragraph_lines(lines: list[str], start_idx: int) -> tuple[list[str], int]:
    """Collect consecutive non-empty lines for paragraph.

    Args:
        lines: All lines.
        start_idx: Index to start from.

    Returns:
        Tuple of (para_lines, next_index).
    """
    para_lines = []
    para_idx = start_idx
    while para_idx < len(lines):
        para_line = lines[para_idx]
        if _should_stop_paragraph(para_line, lines, para_idx):
            break
        para_lines.append(para_line)
        para_idx += 1
    return para_lines, para_idx


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
    # Initialize parsing state
    state = PageParseState(
        content_elements=[],
        figures_list=[],
        metadata=None,
        toc_entries=[],
        errors=[],
        in_toc=False,
        had_toc_marker=False,
        toc_lines=[],
    )

    # Parse content line by line
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        line_num = start_line + idx + 1

        # Check for TOC markers
        toc_marker = parse_toc_marker(line)
        if toc_marker == MarkerType.TOC_START:
            state.in_toc = True
            state.had_toc_marker = True
            state.toc_lines = []  # Start collecting TOC lines
            idx += 1
            continue
        if toc_marker == MarkerType.TOC_END:
            _handle_toc_end(state)
            idx += 1
            continue

        # Check for content/skip markers
        content_marker = parse_content_marker(line)
        if content_marker == MarkerType.CONTENT_START:
            marker_stack.append("content")
            idx += 1
            continue
        if content_marker == MarkerType.CONTENT_END:
            if marker_stack and marker_stack[-1] == "content":
                marker_stack.pop()
            idx += 1
            continue
        if content_marker == MarkerType.SKIP_START:
            marker_stack.append("skip")
            idx += 1
            continue
        if content_marker == MarkerType.SKIP_END:
            if marker_stack and marker_stack[-1] == "skip":
                marker_stack.pop()
            idx += 1
            continue

        # If inside TOC, collect lines for later merging and parsing
        if state.in_toc:
            state.toc_lines.append(line)
            idx += 1
            continue

        # Get current readAloud value from marker stack
        read_aloud = get_read_aloud_from_stack(marker_stack)

        # Check for heading
        heading = _handle_heading(line, line_num, page_number, read_aloud, state)
        if heading is not None:
            state.content_elements.append(heading)
            idx += 1
            continue

        # Check for figure comment
        fig_path = parse_figure_comment(line)
        if fig_path is not None:
            fig_lines = _collect_figure_lines(lines, idx)
            fig = parse_figure(fig_lines)
            if fig is not None:
                state.figures_list.append(fig)
            idx += len(fig_lines)
            continue

        # Check for page metadata (N / M pattern)
        page_meta = parse_page_metadata(line.strip())
        if page_meta is not None:
            state.metadata = page_meta
            idx += 1
            continue

        # Check for list item (supports ●, •, -, *, ①, 1., etc.)
        is_list, _, _ = is_list_line(line)
        if is_list:
            list_lines, list_idx = _collect_list_lines(lines, idx)
            # Only treat as list if 2+ consecutive items
            if len(list_lines) >= 2:
                lst = parse_list(list_lines)
                if lst is not None:
                    # Apply readAloud state
                    lst = List(items=lst.items, list_type=lst.list_type, read_aloud=read_aloud)
                    state.content_elements.append(lst)
                idx = list_idx
                continue
            # Single item: fall through to paragraph handling

        # Check for paragraph (non-empty, non-special line)
        if line.strip():
            para_lines, para_idx = _collect_paragraph_lines(lines, idx)
            para = parse_paragraph(para_lines)
            if para is not None:
                # Apply readAloud state
                para = Paragraph(text=para.text, read_aloud=read_aloud)
                state.content_elements.append(para)
            idx = para_idx
            continue

        # Empty line, skip
        idx += 1

    # If TOC is still open at end of page, process collected lines
    if state.in_toc and state.toc_lines:
        state.toc_entries.extend(_process_toc_lines_with_llm_fallback(state.toc_lines))

    # Create Page object
    # Content readAloud is true if ANY child element has readAloud=true
    content_read_aloud = any(elem.read_aloud for elem in state.content_elements) if state.content_elements else False
    content = Content(elements=tuple(state.content_elements), read_aloud=content_read_aloud)
    announcement = create_page_announcement(page_number)

    page = Page(
        number=page_number,
        source_file=source_file,
        content=content,
        announcement=announcement,
        figures=tuple(state.figures_list),
        metadata=state.metadata,
    )

    return (page, state.errors, state.toc_entries, state.had_toc_marker)
