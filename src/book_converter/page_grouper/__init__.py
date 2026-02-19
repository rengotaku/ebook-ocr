"""Page grouper package - maintains backward compatibility."""

from .assignment import (
    _assign_pages_to_sections_new,
    group_pages_by_toc,
)
from .hierarchy import (
    _add_sections_to_chapter,
    _build_chapters,
    _build_hierarchical_structure,
    _build_sections,
    _find_first_chapter,
    _pages_to_section,
)
from .models import FlattenStats, SectionNumber, TOCEntry
from .section import (
    extract_section_from_heading,
    extract_section_from_page_metadata,
    is_chapter_title_page,
    normalize_for_matching,
    parse_section_number,
)
from .toc import parse_toc, validate_page_count
from .xml import _serialize_to_xml, convert_pages_to_book

__all__ = [
    # Section
    "parse_section_number",
    "normalize_for_matching",
    "extract_section_from_page_metadata",
    "extract_section_from_heading",
    "is_chapter_title_page",
    # TOC
    "parse_toc",
    "validate_page_count",
    # Assignment
    "group_pages_by_toc",
    "_assign_pages_to_sections_new",
    # Hierarchy
    "_find_first_chapter",
    "_build_hierarchical_structure",
    "_add_sections_to_chapter",
    "_build_chapters",
    "_build_sections",
    "_pages_to_section",
    # XML
    "_serialize_to_xml",
    "convert_pages_to_book",
    # Models
    "FlattenStats",
    "SectionNumber",
    "TOCEntry",
]
