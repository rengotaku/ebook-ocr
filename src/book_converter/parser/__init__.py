"""Book parser package - maintains backward compatibility."""

from .figure import parse_figure, parse_figure_comment, parse_figure_placeholder, parse_list
from .heading import parse_heading, parse_heading_with_warning, parse_structure_heading
from .models import StructureHeading
from .page import (
    create_page_announcement,
    extract_page_number,
    parse_page_marker,
    parse_page_metadata,
    parse_pages,
    parse_pages_with_errors,
)
from .paragraph import (
    merge_continuation_paragraphs,
    parse_paragraph,
    parse_paragraph_lines,
    split_paragraphs,
)
from .toc import (
    merge_toc_lines,
    normalize_toc_line,
    normalize_toc_text,
    parse_content_marker,
    parse_toc_entry,
    parse_toc_lines,
    parse_toc_marker,
    split_toc_entries,
)
from .utils import count_markers, get_read_aloud_from_stack, is_list_line

__all__ = [
    # TOC
    "parse_toc_marker",
    "parse_content_marker",
    "normalize_toc_line",
    "merge_toc_lines",
    "normalize_toc_text",
    "split_toc_entries",
    "parse_toc_lines",
    "parse_toc_entry",
    # Page
    "parse_page_marker",
    "extract_page_number",
    "create_page_announcement",
    "parse_page_metadata",
    "parse_pages",
    "parse_pages_with_errors",
    # Heading
    "parse_structure_heading",
    "parse_heading",
    "parse_heading_with_warning",
    # Paragraph
    "parse_paragraph_lines",
    "split_paragraphs",
    "merge_continuation_paragraphs",
    "parse_paragraph",
    # Figure
    "parse_list",
    "parse_figure_comment",
    "parse_figure_placeholder",
    "parse_figure",
    # Utils
    "is_list_line",
    "get_read_aloud_from_stack",
    "count_markers",
    # Models
    "StructureHeading",
]
