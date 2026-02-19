"""Book converter package.

This package provides tools for converting book.md to book.xml
and grouping pages by TOC structure.
"""

from src.book_converter.page_grouper import (
    SectionNumber,
    TOCEntry,
    extract_section_from_heading,
    extract_section_from_page_metadata,
    group_pages_by_toc,
    parse_section_number,
)

__all__ = [
    "group_pages_by_toc",
    "parse_section_number",
    "extract_section_from_page_metadata",
    "extract_section_from_heading",
    "SectionNumber",
    "TOCEntry",
]
