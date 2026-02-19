"""Page grouper module for TOC-based page grouping.

This module provides functions to group pages by TOC structure.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from xml.etree import ElementTree as ET

from src.book_converter.errors import PageValidationError
from src.book_converter.models import (
    Book,
    BookMetadata,
    Chapter,
    HeaderLevelConfig,
    Heading,
    Page,
    Paragraph,
    Section,
    SectionElement,
    TableOfContents,
    TocEntry,
)
from src.book_converter.transformer import is_duplicate_heading


@dataclass
class FlattenStats:
    """Statistics from page flattening operation."""

    pages_flattened: int = 0
    headings_removed: int = 0

    def __iadd__(self, other: "FlattenStats") -> "FlattenStats":
        """Add another stats object to this one."""
        self.pages_flattened += other.pages_flattened
        self.headings_removed += other.headings_removed
        return self


@dataclass(frozen=True)
class SectionNumber:
    """Parsed section number with hierarchy information."""

    raw: str
    parts: tuple[int, ...]
    level: int  # 1=chapter, 2=section, 3=subsection

    @property
    def chapter_num(self) -> int:
        """Return the chapter number (first part)."""
        return self.parts[0]

    @property
    def is_chapter(self) -> bool:
        """Return True if this is a chapter number."""
        return len(self.parts) == 1

    @property
    def is_section(self) -> bool:
        """Return True if this is a section number."""
        return len(self.parts) == 2

    @property
    def is_subsection(self) -> bool:
        """Return True if this is a subsection number."""
        return len(self.parts) >= 3


@dataclass(frozen=True)
class TOCEntry:
    """TOC entry from XML."""

    level: int  # 1=chapter, 2=section, 3=subsection
    number: str  # "1", "1.1", "1.1.1"
    title: str


def parse_section_number(section_str: str | None) -> SectionNumber | None:
    """Parse section number string into SectionNumber.

    Args:
        section_str: Section number string like "1", "2.1", "2.1.1"

    Returns:
        SectionNumber or None if invalid
    """
    if not section_str:
        return None

    # Validate pattern: digits separated by dots
    if not re.match(r"^\d+(?:\.\d+)*$", section_str):
        return None

    parts = tuple(int(x) for x in section_str.split("."))

    # Determine level (1=chapter, 2=section, 3=subsection)
    if len(parts) == 1:
        level = 1
    elif len(parts) == 2:
        level = 2
    else:
        level = 3  # 3+ levels are all subsection

    return SectionNumber(raw=section_str, parts=parts, level=level)


def normalize_for_matching(text: str) -> str:
    """Normalize text for consistent matching.

    Applies normalization to ensure TOC entries and page content
    can be matched reliably:
    1. Compress consecutive whitespace to single space
    2. Strip leading/trailing whitespace

    Args:
        text: Text to normalize

    Returns:
        Normalized text

    Example:
        >>> normalize_for_matching("Text  with   spaces")
        "Text with spaces"
        >>> normalize_for_matching("  Line\\n  breaks  ")
        "Line breaks"
    """
    # Compress consecutive whitespace (including newlines) to single space
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def _extract_number_by_keyword(
    text: str,
    config: HeaderLevelConfig | None,
) -> str | None:
    """Extract section number using keyword-based patterns from config.

    Args:
        text: Text to search in
        config: Header level configuration

    Returns:
        Extracted number string or None
    """
    if not config or not config.has_any_config():
        return None

    # Build pattern for each configured keyword
    for level in range(1, 6):
        keywords = config.get_keywords_for_level(level)
        for keyword in keywords:
            # Pattern: "Keyword N" or "Keyword NN" (e.g., "Chapter 2", "Episode 07")
            pattern = rf"^{re.escape(keyword)}\s*(\d+)"
            match = re.match(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).lstrip("0") or "0"

    return None


def extract_section_from_page_metadata(
    metadata: str | None,
    config: HeaderLevelConfig | None = None,
) -> str | None:
    """Extract section number from pageMetadata content.

    Args:
        metadata: pageMetadata text like "1.1 SREの概要 ― 1 / 3"
        config: Header level configuration for keyword-based extraction

    Returns:
        Section number string like "1.1" or None
    """
    if not metadata:
        return None

    # Normalize whitespace for consistent matching
    metadata = normalize_for_matching(metadata)

    # Skip emphasis tags (front-matter)
    if "<emphasis>" in metadata:
        return None

    # Config-based keyword extraction
    if config and config.has_any_config():
        return _extract_number_by_keyword(metadata, config)

    # Fallback patterns (no config required):

    # 1. Direct section number at start (e.g., "1.1 Title", "2.3.1 Title")
    section_match = re.match(r"^(\d+(?:\.\d+)+)\s+", metadata)
    if section_match:
        return section_match.group(1)

    # 2. Single number at start followed by non-numeric non-slash text (e.g., "1 Chapter Title")
    # Avoid matching "1 / 1" (page number format)
    chapter_match = re.match(r"^(\d+)\s+(?![/\d])", metadata)
    if chapter_match:
        return chapter_match.group(1)

    # 3. Japanese chapter pattern (e.g., "第1章 Title")
    japanese_chapter_match = re.match(r"^第(\d+)章", metadata)
    if japanese_chapter_match:
        return japanese_chapter_match.group(1)

    # 4. Keyword prefix with number (e.g., "Section 1.1 Title")
    keyword_number_match = re.match(r"^(?:Section|Chapter|Episode|Part)\s+(\d+(?:\.\d+)*)", metadata, re.IGNORECASE)
    if keyword_number_match:
        return keyword_number_match.group(1)

    return None


def extract_section_from_heading(
    heading: str | None,
    config: HeaderLevelConfig | None = None,
) -> str | None:
    """Extract section number from heading content.

    Args:
        heading: Heading text like "Section 1.1 SREの概要" or "1.1 SREの概要"
        config: Header level configuration for keyword-based extraction

    Returns:
        Section number string like "1.1" or None
    """
    if not heading:
        return None

    # Normalize whitespace for consistent matching
    heading = normalize_for_matching(heading)

    # Config-based keyword extraction
    if config and config.has_any_config():
        return _extract_number_by_keyword(heading, config)

    # Fallback patterns (no config required):

    # 1. Direct section number at start (e.g., "1.1 Title", "2.3.1 Title")
    section_match = re.match(r"^(\d+(?:\.\d+)+)\s+", heading)
    if section_match:
        return section_match.group(1)

    # 2. Single number at start followed by non-numeric non-slash text (e.g., "1 Chapter Title")
    # Avoid matching "1 / 1" (page number format)
    chapter_match = re.match(r"^(\d+)\s+(?![/\d])", heading)
    if chapter_match:
        return chapter_match.group(1)

    # 3. Japanese chapter pattern (e.g., "第1章 Title")
    japanese_chapter_match = re.match(r"^第(\d+)章", heading)
    if japanese_chapter_match:
        return japanese_chapter_match.group(1)

    # 4. Keyword prefix with number (e.g., "Section 1.1 Title", "Chapter 2 Title")
    keyword_number_match = re.match(r"^(?:Section|Chapter|Episode|Part)\s+(\d+(?:\.\d+)*)", heading, re.IGNORECASE)
    if keyword_number_match:
        return keyword_number_match.group(1)

    return None


def is_chapter_title_page(page: ET.Element) -> bool:
    """Check if a page is a chapter title page.

    A chapter title page is the first page of a chapter, typically containing
    only the chapter number and title (e.g., "第1章 SREとは").

    Args:
        page: Page XML element

    Returns:
        True if the page is a chapter title page, False otherwise
    """
    # Pattern to detect chapter title: "第N章"
    chapter_pattern = re.compile(r"^第\d+章")

    # Check pageMetadata for "第N章"
    page_metadata = page.find("pageMetadata")
    if page_metadata is not None:
        metadata_text = "".join(page_metadata.itertext())

        # Skip emphasis tags (front-matter pages like "はじめに")
        if "<emphasis>" in ET.tostring(page_metadata, encoding="unicode"):
            return False

        # Check for chapter pattern
        if chapter_pattern.search(metadata_text):
            return True

    # Check content/heading for "第N章"
    content = page.find("content")
    if content is not None:
        for heading in content.iter("heading"):
            heading_text = "".join(heading.itertext()) if heading.text or len(heading) > 0 else ""
            if chapter_pattern.search(heading_text):
                return True

    return False


def _normalize_level(level: str) -> int:
    """Normalize level attribute from numeric or string format.

    Args:
        level: Level attribute value ("1", "2", "3" or "chapter", "section", etc.)

    Returns:
        Normalized level as int (1=chapter, 2=section, 3=subsection)
    """
    # Numeric string to int
    if level.isdigit():
        level_int = int(level)
        return min(level_int, 3)  # Cap at 3 for subsection

    # String to int mapping
    string_map = {
        "chapter": 1,
        "section": 2,
        "subsection": 3,
        "other": 1,  # "other" maps to chapter level
    }
    return string_map.get(level, 1)


def parse_toc(toc_element: ET.Element) -> list[TOCEntry]:
    """Parse TOC XML element into list of TOCEntry.

    Args:
        toc_element: XML Element for <toc>

    Returns:
        List of TOCEntry objects
    """
    entries = []
    for entry in toc_element.findall("entry"):
        level_raw = entry.get("level", "")
        level = _normalize_level(level_raw)
        number = entry.get("number", "")
        title = entry.get("title", "")
        entries.append(TOCEntry(level=level, number=number, title=title))
    return entries


def validate_page_count(input_count: int, output_count: int) -> None:
    """Validate output page count against input.

    Args:
        input_count: Number of pages in input
        output_count: Number of pages in output

    Raises:
        PageValidationError: If output_count < 50% of input_count

    Returns:
        None if validation passes
    """
    if input_count == 0:
        return

    loss_ratio = (input_count - output_count) / input_count
    if loss_ratio >= 0.5:
        raise PageValidationError(
            input_count=input_count,
            output_count=output_count,
            message=f"Page validation failed: {output_count} of {input_count} pages preserved "
            f"({(1 - loss_ratio) * 100:.1f}%). At least 50% required.",
        )


def _flatten_pages_in_element(
    element: ET.Element,
    container_number: str | None = None,
    container_title: str | None = None,
) -> FlattenStats:
    """Flatten page tags to page comments and extract content elements.

    Transforms:
    - <page number="N"> -> <!-- page N -->
    - <content><children/></content> -> <children/> (direct)
    - <pageAnnouncement> -> removed
    - Duplicate headings -> removed (if matches container title)

    Args:
        element: The XML element to process (modified in place)
        container_number: The container's number for duplicate heading detection
        container_title: The container's title for duplicate heading detection

    Returns:
        FlattenStats with pages_flattened and headings_removed counts
    """
    stats = FlattenStats()

    # Find all page elements to process
    pages_to_process = list(element.findall("page"))

    for page in pages_to_process:
        page_number = page.get("number", "")

        # Get index of page element
        page_index = list(element).index(page)

        # Remove the page element
        element.remove(page)

        # Insert page comment at the same position
        if page_number:
            comment = ET.Comment(f" page {page_number} ")
            element.insert(page_index, comment)
            page_index += 1

        # Extract content elements (skip pageAnnouncement, pageMetadata)
        for child in page:
            if child.tag in ("pageAnnouncement", "pageMetadata"):
                # Skip page-level metadata (not content)
                continue
            elif child.tag == "content":
                # Extract content's children directly
                for content_child in child:
                    # Check for duplicate heading
                    if content_child.tag == "heading" and container_title:
                        heading_text = "".join(content_child.itertext())
                        if is_duplicate_heading(heading_text, container_number, container_title):
                            # Skip duplicate heading
                            stats.headings_removed += 1
                            continue
                    element.insert(page_index, content_child)
                    page_index += 1
            else:
                # Other elements go directly (shouldn't happen normally)
                element.insert(page_index, child)
                page_index += 1

        stats.pages_flattened += 1

    # Recursively process child elements (chapter, section, subsection, front-matter)
    for child in element:
        if child.tag in ("chapter", "section", "subsection", "front-matter"):
            child_number = child.get("number")
            child_title = child.get("title", "")
            stats += _flatten_pages_in_element(child, child_number, child_title)

    return stats


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


def _find_first_chapter(toc_lookup: dict[str, TOCEntry]) -> str | None:
    """Find the first chapter in TOC.

    Args:
        toc_lookup: Dict mapping section number to TOCEntry

    Returns:
        First chapter number or None if no chapters exist
    """
    # Find all chapter entries (level=1) with valid numeric section numbers
    chapter_numbers = [num for num, entry in toc_lookup.items() if entry.level == 1 and num and num.isdigit()]

    if not chapter_numbers:
        return None

    # Return the numerically smallest chapter number
    return min(chapter_numbers, key=lambda x: int(x))


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


def _build_hierarchical_structure(
    book_elem: ET.Element,
    page_assignments: dict[str, list[ET.Element]],
    toc_lookup: dict[str, TOCEntry],
) -> None:
    """Build hierarchical chapter/section/subsection structure.

    Args:
        book_elem: Book element to append to
        page_assignments: Dict mapping section number to pages
        toc_lookup: Dict mapping section number to TOCEntry
    """
    # Group sections by chapter
    chapters: dict[str, dict[str, list[ET.Element]]] = {}

    for section_num, pages in page_assignments.items():
        section_parts = parse_section_number(section_num)
        if not section_parts:
            continue

        chapter_num = str(section_parts.chapter_num)

        if chapter_num not in chapters:
            chapters[chapter_num] = {}

        chapters[chapter_num][section_num] = pages

    # Build chapter elements
    for chapter_num in sorted(chapters.keys(), key=lambda x: int(x)):
        chapter_entry = toc_lookup.get(chapter_num)
        if not chapter_entry:
            continue

        chapter_elem = ET.Element("chapter")
        chapter_elem.set("number", chapter_num)
        chapter_elem.set("title", chapter_entry.title)

        # Get sections in this chapter
        chapter_sections = chapters[chapter_num]

        # Add pages to chapter
        _add_sections_to_chapter(chapter_elem, chapter_sections, toc_lookup)

        book_elem.append(chapter_elem)

    # Handle chapters from TOC that don't have pages yet
    for entry in toc_lookup.values():
        if entry.level == 1:  # chapter level
            chapter_num = entry.number
            if chapter_num not in chapters:
                # Create empty chapter
                chapter_elem = ET.Element("chapter")
                chapter_elem.set("number", chapter_num)
                chapter_elem.set("title", entry.title)
                book_elem.append(chapter_elem)


def _add_sections_to_chapter(
    chapter_elem: ET.Element,
    sections: dict[str, list[ET.Element]],
    toc_lookup: dict[str, TOCEntry],
) -> None:
    """Add sections and subsections to chapter element.

    Args:
        chapter_elem: Chapter element
        sections: Dict mapping section number to pages
        toc_lookup: Dict mapping section number to TOCEntry
    """
    # Organize by section level
    section_map: dict[str, dict[str, list[ET.Element]]] = {}

    for section_num, pages in sections.items():
        section_parts = parse_section_number(section_num)
        if not section_parts:
            continue

        if section_parts.is_chapter:
            # Chapter title pages go directly to chapter
            for page in pages:
                # Mark chapter title pages with type attribute
                if is_chapter_title_page(page):
                    page.set("type", "chapter-title")
                chapter_elem.append(page)
        elif section_parts.is_section:
            # Section level
            if section_num not in section_map:
                section_map[section_num] = {}
            section_map[section_num]["_pages"] = pages
        elif section_parts.is_subsection:
            # Subsection - find parent section
            parent_section = ".".join(section_num.split(".")[:2])
            if parent_section not in section_map:
                section_map[parent_section] = {}
            section_map[parent_section][section_num] = pages

    # Build section elements
    for section_num in sorted(section_map.keys(), key=_section_sort_key):
        section_entry = toc_lookup.get(section_num)
        if not section_entry:
            continue

        section_elem = ET.Element("section")
        section_elem.set("number", section_num)
        section_elem.set("title", section_entry.title)

        # Add section pages
        if "_pages" in section_map[section_num]:
            for page in section_map[section_num]["_pages"]:
                section_elem.append(page)

        # Add subsections
        for subsection_num, pages in section_map[section_num].items():
            if subsection_num == "_pages":
                continue

            subsection_entry = toc_lookup.get(subsection_num)
            if not subsection_entry:
                continue

            subsection_elem = ET.Element("subsection")
            subsection_elem.set("number", subsection_num)
            subsection_elem.set("title", subsection_entry.title)

            for page in pages:
                subsection_elem.append(page)

            section_elem.append(subsection_elem)

        chapter_elem.append(section_elem)


def _section_sort_key(section_num: str) -> tuple[int, ...]:
    """Sort key for section numbers.

    Args:
        section_num: Section number string like "1.1" or "2.3"

    Returns:
        Tuple of integers for sorting
    """
    return tuple(int(x) for x in section_num.split("."))


def _serialize_to_xml(element: ET.Element) -> str:
    """Serialize XML element to string.

    Args:
        element: Root element

    Returns:
        XML string with declaration
    """
    xml_str = ET.tostring(element, encoding="unicode")
    return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'


# ============================================================
# New Design: Page list → Chapter/Section structure
# ============================================================


def convert_pages_to_book(
    pages: tuple[Page, ...],
    toc: TableOfContents | None,
    metadata: BookMetadata,
    config: HeaderLevelConfig | None = None,
) -> Book:
    """Convert flat page list to hierarchical Book structure.

    Args:
        pages: Tuple of Page objects (legacy format)
        toc: Table of contents
        metadata: Book metadata
        config: Header level configuration

    Returns:
        Book with chapters and sections (new format)
    """
    if not toc or not toc.entries:
        # No TOC: put all content in a single chapter
        section = _pages_to_section("", "Content", pages)
        chapter = Chapter(number="", title="Content", sections=(section,))
        return Book(metadata=metadata, toc=toc, chapters=(chapter,))

    # Build TOC lookup
    toc_lookup = {entry.number: entry for entry in toc.entries if entry.number}

    # Assign pages to sections
    page_assignments = _assign_pages_to_sections_new(pages, toc_lookup, config)

    # Build chapters
    chapters = _build_chapters(page_assignments, toc_lookup)

    return Book(metadata=metadata, toc=toc, chapters=chapters)


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


def _find_first_chapter_entry(toc_lookup: dict[str, TocEntry]) -> str | None:
    """Find the first chapter number in TOC."""
    chapter_numbers = [num for num, entry in toc_lookup.items() if entry.level == 1 and num and num.isdigit()]
    if not chapter_numbers:
        return None
    return min(chapter_numbers, key=lambda x: int(x))


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


def _build_chapters(
    page_assignments: dict[str, list[Page]],
    toc_lookup: dict[str, TocEntry],
) -> tuple[Chapter, ...]:
    """Build chapters from page assignments.

    Args:
        page_assignments: Dict mapping section number to pages
        toc_lookup: Dict mapping section number to TocEntry

    Returns:
        Tuple of Chapter objects
    """
    # Group by chapter number
    chapters_data: dict[str, dict[str, list[Page]]] = {}

    for section_num, pages in page_assignments.items():
        section_parts = parse_section_number(section_num)
        if not section_parts:
            continue

        chapter_num = str(section_parts.chapter_num)
        if chapter_num not in chapters_data:
            chapters_data[chapter_num] = {}
        chapters_data[chapter_num][section_num] = pages

    # Build Chapter objects
    chapters = []
    for chapter_num in sorted(chapters_data.keys(), key=lambda x: int(x) if x.isdigit() else 0):
        chapter_entry = toc_lookup.get(chapter_num)
        if not chapter_entry:
            continue

        sections = _build_sections(chapters_data[chapter_num], toc_lookup, chapter_entry)
        chapter = Chapter(
            number=chapter_num,
            title=chapter_entry.text,
            sections=sections,
        )
        chapters.append(chapter)

    return tuple(chapters)


def _build_sections(
    section_pages: dict[str, list[Page]],
    toc_lookup: dict[str, TocEntry],
    chapter_entry: TocEntry,
) -> tuple[Section, ...]:
    """Build sections for a chapter.

    Args:
        section_pages: Dict mapping section number to pages
        toc_lookup: Dict mapping section number to TocEntry
        chapter_entry: TOC entry for the chapter

    Returns:
        Tuple of Section objects
    """
    sections = []

    # Sort section numbers
    sorted_sections = sorted(section_pages.keys(), key=_section_sort_key)

    for section_num in sorted_sections:
        pages = section_pages[section_num]
        section_parts = parse_section_number(section_num)

        if not section_parts:
            continue

        # Get section entry from TOC
        section_entry = toc_lookup.get(section_num)

        if section_parts.is_chapter:
            # Chapter-level pages: create section with chapter title
            # Skip title elements (they're in chapter.title)
            section = _pages_to_section(
                section_num,
                chapter_entry.text,
                pages,
                skip_title=True,
            )
            if section.elements:  # Only add if has elements
                sections.append(section)
        else:
            # Regular section
            title = section_entry.text if section_entry else ""
            section = _pages_to_section(
                section_num,
                title,
                pages,
                skip_title=True,
            )
            sections.append(section)

    return tuple(sections)


def _pages_to_section(
    number: str,
    title: str,
    pages: list[Page] | tuple[Page, ...],
    skip_title: bool = False,
) -> Section:
    """Convert pages to a Section.

    Args:
        number: Section number
        title: Section title
        pages: List of pages
        skip_title: Whether to skip title elements (heading/paragraph matching title)

    Returns:
        Section object
    """
    elements: list[SectionElement] = []

    # Normalize title for comparison
    normalized_title = normalize_for_matching(title) if title else ""

    for page in pages:
        # Add content elements
        for element in page.content.elements:
            # Skip title duplicates if requested
            if skip_title and normalized_title:
                if isinstance(element, (Heading, Paragraph)):
                    normalized_text = normalize_for_matching(element.text)
                    # Skip if text contains the title
                    if _is_title_duplicate(normalized_text, normalized_title):
                        continue

            elements.append(element)

        # Add figures
        for figure in page.figures:
            elements.append(figure)

    return Section(
        number=number,
        title=title,
        elements=tuple(elements),
    )


def _is_title_duplicate(text: str, title: str) -> bool:
    """Check if text is a title duplicate.

    Args:
        text: Normalized text to check
        title: Normalized title

    Returns:
        True if text is a title duplicate
    """
    # Exact match
    if text == title:
        return True

    # Text starts with "Chapter N" or "Section N.N" followed by title
    chapter_pattern = r"^(?:Chapter|Section|第\d+章)\s*\d*\.?\d*\s*"
    stripped = re.sub(chapter_pattern, "", text, flags=re.IGNORECASE)
    if normalize_for_matching(stripped) == title:
        return True

    # Title is contained in text (for cases like "1.1 Title Here")
    if title and title in text:
        return True

    return False


def main() -> int:
    """CLI entry point for standalone page grouping.

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(description="Group pages by TOC structure")
    parser.add_argument("input", help="Input book.xml file")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    try:
        # Read input file
        with open(args.input, "r", encoding="utf-8") as f:
            input_xml = f.read()

        # Group pages
        result = group_pages_by_toc(input_xml)

        # Write output
        if args.output:
            with open(args.output, "w", encoding="utf-8") as f:
                f.write(result)
        else:
            print(result)

        return 0

    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    import sys

    sys.exit(main())
