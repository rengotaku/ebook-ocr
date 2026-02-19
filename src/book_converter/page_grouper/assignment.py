"""Page assignment to sections based on TOC."""

from __future__ import annotations

import re
from xml.etree import ElementTree as ET

from src.book_converter.models import (
    HeaderLevelConfig,
    Heading,
    Page,
    Paragraph,
    TocEntry,
)

from .models import TOCEntry
from .section import extract_section_from_heading, extract_section_from_page_metadata
from .toc import parse_toc, validate_page_count


def group_pages_by_toc(
    xml_input: str,
    header_level_config: HeaderLevelConfig | None = None,
) -> str:
    """Group pages in book XML by TOC structure.

    Args:
        xml_input: Input book XML string with flat pages
        header_level_config: Header level keyword mapping configuration

    Returns:
        Output book XML string with hierarchical page grouping
    """
    from .hierarchy import _build_hierarchical_structure, _flatten_pages_in_element
    from .xml import _serialize_to_xml

    # Parse input XML
    root = ET.fromstring(xml_input)

    # Extract metadata and TOC
    metadata = root.find("metadata")
    toc_element = root.find("toc")

    # Get TOC begin/end
    toc_begin = None
    toc_end = None
    toc_entries = []
    if toc_element is not None:
        toc_begin = int(toc_element.get("begin", "0"))
        toc_end = int(toc_element.get("end", "0"))
        toc_entries = parse_toc(toc_element)

    # Build TOC lookup: section number -> TOCEntry (skip entries without number)
    toc_lookup = {entry.number: entry for entry in toc_entries if entry.number}

    # Create new book element
    new_book = ET.Element("book")

    # Add metadata
    if metadata is not None:
        new_book.append(metadata)

    # Add TOC
    if toc_element is not None:
        new_book.append(toc_element)

    # Collect all pages and classify them
    pages = root.findall("page")

    # If no TOC entries exist, place all pages in front-matter
    if not toc_entries:
        front_matter_elem = ET.Element("front-matter")
        for page in pages:
            front_matter_elem.append(page)
        new_book.append(front_matter_elem)
    else:
        # Front-matter pages: before toc_begin and TOC pages themselves
        front_matter_pages = []
        content_pages = []

        for page in pages:
            page_num = int(page.get("number", "0"))
            if toc_begin and page_num <= toc_end:
                front_matter_pages.append(page)
            else:
                content_pages.append(page)

        # Create front-matter section
        if front_matter_pages:
            front_matter_elem = ET.Element("front-matter")
            for page in front_matter_pages:
                front_matter_elem.append(page)
            new_book.append(front_matter_elem)

        # Assign content pages to sections
        page_assignments = _assign_pages_to_sections(content_pages, toc_lookup, header_level_config)

        # Build hierarchical structure
        _build_hierarchical_structure(new_book, page_assignments, toc_lookup)

    # Validate page count (before flattening)
    input_count = len(pages)
    output_count = len(new_book.findall(".//page"))
    validate_page_count(input_count, output_count)

    # Count structure elements created
    chapters_count = len(new_book.findall(".//chapter"))
    sections_count = len(new_book.findall(".//section"))
    subsections_count = len(new_book.findall(".//subsection"))

    # Count content elements before flattening
    headings_before = len(new_book.findall(".//heading"))
    paragraphs_count = len(new_book.findall(".//paragraph"))
    lists_count = len(new_book.findall(".//list"))
    figures_count = len(new_book.findall(".//figure"))

    # Flatten pages: convert <page> to <!-- page N --> comments
    # and extract content elements directly
    flatten_stats = _flatten_pages_in_element(new_book)

    # Count headings after flattening
    headings_after = len(new_book.findall(".//heading"))

    # Print statistics
    print("グループ化統計:")
    print(f"  TOCエントリ: {len(toc_entries)}件")
    print(f"  構造タグ: chapter={chapters_count}, section={sections_count}, subsection={subsections_count}")
    print(
        f"  コンテンツタグ: heading={headings_after}, paragraph={paragraphs_count}, "
        f"list={lists_count}, figure={figures_count}"
    )
    print(f"  重複heading削除: {flatten_stats.headings_removed}件 ({headings_before}→{headings_after})")

    # Serialize to string
    return _serialize_to_xml(new_book)


def _assign_pages_to_sections(
    pages: list[ET.Element],
    toc_lookup: dict[str, TOCEntry],
    config: HeaderLevelConfig | None = None,
) -> dict[str, list[ET.Element]]:
    """Assign pages to sections based on extracted section numbers.

    Args:
        pages: List of page elements
        toc_lookup: Dict mapping section number to TOCEntry
        config: Header level configuration

    Returns:
        Dict mapping section number to list of pages
    """
    from .hierarchy import _find_first_chapter

    assignments: dict[str, list[ET.Element]] = {}
    current_section = None

    for page in pages:
        # Try to extract section number from page
        section_num = _extract_section_from_page(page, config)

        if section_num and section_num in toc_lookup:
            current_section = section_num
        elif current_section is None:
            # FR-008: First content page without section -> assign to first chapter
            current_section = _find_first_chapter(toc_lookup)
        # If no section found but current_section exists, use previous page's section (US4 fallback)

        if current_section:
            if current_section not in assignments:
                assignments[current_section] = []
            assignments[current_section].append(page)

    return assignments


def _extract_section_from_page(
    page: ET.Element,
    config: HeaderLevelConfig | None = None,
) -> str | None:
    """Extract section number from a page element.

    Recognizes new format:
    - "Chapter N Title" → returns "N"
    - "Section N.N Title" → returns "N.N"
    - "Subsection N.N.N Title" → returns "N.N.N"

    Args:
        page: Page element
        config: Header level configuration

    Returns:
        Section number string or None
    """
    # Try heading first (new format: Chapter N / Section N.N)
    content = page.find("content")
    if content is not None:
        heading = content.find("heading")
        if heading is not None:
            heading_text = "".join(heading.itertext()).strip()

            # New format: "Chapter N Title"
            chapter_match = re.match(r"^Chapter\s+(\d+)", heading_text, re.IGNORECASE)
            if chapter_match:
                return chapter_match.group(1)

            # New format: "Section N.N Title"
            section_match = re.match(r"^Section\s+(\d+\.\d+)", heading_text, re.IGNORECASE)
            if section_match:
                return section_match.group(1)

            # New format: "Subsection N.N.N Title"
            subsection_match = re.match(r"^Subsection\s+(\d+\.\d+\.\d+)", heading_text, re.IGNORECASE)
            if subsection_match:
                return subsection_match.group(1)

            # Fallback: try legacy extraction
            section = extract_section_from_heading(heading_text, config)
            if section:
                return section

    # Try pageMetadata (for legacy support)
    page_metadata = page.find("pageMetadata")
    if page_metadata is not None:
        metadata_text = "".join(page_metadata.itertext())
        section = extract_section_from_page_metadata(metadata_text, config)
        if section:
            return section

    return None


def _assign_pages_to_sections_new(
    pages: tuple[Page, ...],
    toc_lookup: dict[str, TocEntry],
    config: HeaderLevelConfig | None = None,
) -> dict[str, list[Page]]:
    """Assign pages to sections.

    Args:
        pages: Tuple of Page objects
        toc_lookup: Dict mapping section number to TocEntry
        config: Header level configuration

    Returns:
        Dict mapping section number to list of pages
    """
    from .hierarchy import _find_first_chapter_entry

    assignments: dict[str, list[Page]] = {}
    current_section: str | None = None

    for page in pages:
        # Try to extract section number from page content
        section_num = _extract_section_from_page_content(page, config)

        if section_num and section_num in toc_lookup:
            current_section = section_num
        elif current_section is None:
            # First page without section -> assign to first chapter
            first_chapter = _find_first_chapter_entry(toc_lookup)
            if first_chapter:
                current_section = first_chapter

        if current_section:
            if current_section not in assignments:
                assignments[current_section] = []
            assignments[current_section].append(page)

    return assignments


def _extract_section_from_page_content(
    page: Page,
    config: HeaderLevelConfig | None = None,
) -> str | None:
    """Extract section number from page content."""
    for element in page.content.elements:
        if isinstance(element, Heading):
            # Try to extract section number from heading
            section = extract_section_from_heading(element.text, config)
            if section:
                return section
        elif isinstance(element, Paragraph):
            # Try to extract from paragraph (chapter title pages)
            section = extract_section_from_heading(element.text, config)
            if section:
                return section
    return None
