"""Page grouper module for TOC-based page grouping.

This module provides functions to group pages by TOC structure.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from xml.etree import ElementTree as ET


@dataclass(frozen=True)
class SectionNumber:
    """Parsed section number with hierarchy information."""

    raw: str
    parts: tuple[int, ...]
    level: str  # "chapter", "section", "subsection"

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

    level: str  # "chapter", "section", "subsection"
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
    if not re.match(r'^\d+(?:\.\d+)*$', section_str):
        return None

    parts = tuple(int(x) for x in section_str.split('.'))

    # Determine level
    if len(parts) == 1:
        level = "chapter"
    elif len(parts) == 2:
        level = "section"
    else:
        level = "subsection"

    return SectionNumber(raw=section_str, parts=parts, level=level)


def extract_section_from_page_metadata(metadata: str | None) -> str | None:
    """Extract section number from pageMetadata content.

    Args:
        metadata: pageMetadata text like "1.1 SREの概要 ― 1 / 3"

    Returns:
        Section number string like "1.1" or None
    """
    if not metadata:
        return None

    # Skip emphasis tags (front-matter)
    if '<emphasis>' in metadata:
        return None

    # Try chapter pattern first: "第1章 SREとは — 1 / 1"
    chapter_match = re.match(r'^第(\d+)章', metadata)
    if chapter_match:
        return chapter_match.group(1)

    # Try standard section pattern: "1.1 SREの概要 ― 1 / 3"
    # Support both half-width and full-width spaces
    # Must have a section number followed by space, but NOT followed by "/" or digit
    # (to avoid matching "1 / 1" which is just page count)
    section_match = re.match(r'^(\d+(?:\.\d+)*)[\s　]+(?![/\d])', metadata)
    if section_match:
        return section_match.group(1)

    return None


def extract_section_from_heading(heading: str | None) -> str | None:
    """Extract section number from heading content.

    Args:
        heading: Heading text like "Section 1.1 SREの概要"

    Returns:
        Section number string like "1.1" or None
    """
    if not heading:
        return None

    # Try chapter pattern: "第1章 SREとは"
    chapter_match = re.match(r'^第(\d+)章', heading)
    if chapter_match:
        return chapter_match.group(1)

    # Try "Section X.Y" prefix pattern
    section_prefix_match = re.match(r'^Section\s+(\d+(?:\.\d+)*)', heading)
    if section_prefix_match:
        return section_prefix_match.group(1)

    # Try direct section number pattern: "1.1.1 サイトとは何か"
    direct_match = re.match(r'^(\d+(?:\.\d+)*)\s', heading)
    if direct_match:
        return direct_match.group(1)

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
    chapter_pattern = re.compile(r'^第\d+章')

    # Check pageMetadata for "第N章"
    page_metadata = page.find('pageMetadata')
    if page_metadata is not None:
        metadata_text = ''.join(page_metadata.itertext())

        # Skip emphasis tags (front-matter pages like "はじめに")
        if '<emphasis>' in ET.tostring(page_metadata, encoding='unicode'):
            return False

        # Check for chapter pattern
        if chapter_pattern.search(metadata_text):
            return True

    # Check content/heading for "第N章"
    content = page.find('content')
    if content is not None:
        for heading in content.iter('heading'):
            heading_text = ''.join(heading.itertext()) if heading.text or len(heading) > 0 else ''
            if chapter_pattern.search(heading_text):
                return True

    return False


def parse_toc(toc_element: ET.Element) -> list[TOCEntry]:
    """Parse TOC XML element into list of TOCEntry.

    Args:
        toc_element: XML Element for <toc>

    Returns:
        List of TOCEntry objects
    """
    entries = []
    for entry in toc_element.findall('entry'):
        level = entry.get('level', '')
        number = entry.get('number', '')
        title = entry.get('title', '')
        entries.append(TOCEntry(level=level, number=number, title=title))
    return entries


def group_pages_by_toc(xml_input: str) -> str:
    """Group pages in book XML by TOC structure.

    Args:
        xml_input: Input book XML string with flat pages

    Returns:
        Output book XML string with hierarchical page grouping
    """
    # Parse input XML
    root = ET.fromstring(xml_input)

    # Extract metadata and TOC
    metadata = root.find('metadata')
    toc_element = root.find('toc')

    # Get TOC begin/end
    toc_begin = None
    toc_end = None
    toc_entries = []
    if toc_element is not None:
        toc_begin = int(toc_element.get('begin', '0'))
        toc_end = int(toc_element.get('end', '0'))
        toc_entries = parse_toc(toc_element)

    # Build TOC lookup: section number -> TOCEntry
    toc_lookup = {entry.number: entry for entry in toc_entries}

    # Create new book element
    new_book = ET.Element('book')

    # Add metadata
    if metadata is not None:
        new_book.append(metadata)

    # Add TOC
    if toc_element is not None:
        new_book.append(toc_element)

    # Collect all pages and classify them
    pages = root.findall('page')

    # Front-matter pages: before toc_begin and TOC pages themselves
    front_matter_pages = []
    content_pages = []

    for page in pages:
        page_num = int(page.get('number', '0'))
        if toc_begin and page_num <= toc_end:
            front_matter_pages.append(page)
        else:
            content_pages.append(page)

    # Create front-matter section
    if front_matter_pages:
        front_matter_elem = ET.Element('front-matter')
        for page in front_matter_pages:
            front_matter_elem.append(page)
        new_book.append(front_matter_elem)

    # Assign content pages to sections
    page_assignments = _assign_pages_to_sections(content_pages, toc_lookup)

    # Build hierarchical structure
    _build_hierarchical_structure(new_book, page_assignments, toc_lookup)

    # Serialize to string
    return _serialize_to_xml(new_book)


def _assign_pages_to_sections(
    pages: list[ET.Element], toc_lookup: dict[str, TOCEntry]
) -> dict[str, list[ET.Element]]:
    """Assign pages to sections based on extracted section numbers.

    Args:
        pages: List of page elements
        toc_lookup: Dict mapping section number to TOCEntry

    Returns:
        Dict mapping section number to list of pages
    """
    assignments: dict[str, list[ET.Element]] = {}
    current_section = None

    for page in pages:
        # Try to extract section number from page
        section_num = _extract_section_from_page(page)

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
    # Find all chapter entries (single digit section numbers)
    chapter_numbers = [num for num, entry in toc_lookup.items() if entry.level == 'chapter']

    if not chapter_numbers:
        return None

    # Return the numerically smallest chapter number
    return min(chapter_numbers, key=lambda x: int(x))


def _extract_section_from_page(page: ET.Element) -> str | None:
    """Extract section number from a page element.

    Args:
        page: Page element

    Returns:
        Section number string or None
    """
    # Try pageMetadata first
    page_metadata = page.find('pageMetadata')
    if page_metadata is not None:
        metadata_text = ''.join(page_metadata.itertext())
        section = extract_section_from_page_metadata(metadata_text)
        if section:
            return section

    # Try heading
    content = page.find('content')
    if content is not None:
        heading = content.find('heading')
        if heading is not None:
            heading_text = ''.join(heading.itertext())
            section = extract_section_from_heading(heading_text)
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

        chapter_elem = ET.Element('chapter')
        chapter_elem.set('number', chapter_num)
        chapter_elem.set('title', chapter_entry.title)

        # Get sections in this chapter
        chapter_sections = chapters[chapter_num]

        # Add pages to chapter
        _add_sections_to_chapter(chapter_elem, chapter_sections, toc_lookup)

        book_elem.append(chapter_elem)

    # Handle chapters from TOC that don't have pages yet
    for entry in toc_lookup.values():
        if entry.level == 'chapter':
            chapter_num = entry.number
            if chapter_num not in chapters:
                # Create empty chapter
                chapter_elem = ET.Element('chapter')
                chapter_elem.set('number', chapter_num)
                chapter_elem.set('title', entry.title)
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
                    page.set('type', 'chapter-title')
                chapter_elem.append(page)
        elif section_parts.is_section:
            # Section level
            if section_num not in section_map:
                section_map[section_num] = {}
            section_map[section_num]['_pages'] = pages
        elif section_parts.is_subsection:
            # Subsection - find parent section
            parent_section = '.'.join(section_num.split('.')[:2])
            if parent_section not in section_map:
                section_map[parent_section] = {}
            section_map[parent_section][section_num] = pages

    # Build section elements
    for section_num in sorted(section_map.keys(), key=_section_sort_key):
        section_entry = toc_lookup.get(section_num)
        if not section_entry:
            continue

        section_elem = ET.Element('section')
        section_elem.set('number', section_num)
        section_elem.set('title', section_entry.title)

        # Add section pages
        if '_pages' in section_map[section_num]:
            for page in section_map[section_num]['_pages']:
                section_elem.append(page)

        # Add subsections
        for subsection_num, pages in section_map[section_num].items():
            if subsection_num == '_pages':
                continue

            subsection_entry = toc_lookup.get(subsection_num)
            if not subsection_entry:
                continue

            subsection_elem = ET.Element('subsection')
            subsection_elem.set('number', subsection_num)
            subsection_elem.set('title', subsection_entry.title)

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
    return tuple(int(x) for x in section_num.split('.'))


def _serialize_to_xml(element: ET.Element) -> str:
    """Serialize XML element to string.

    Args:
        element: Root element

    Returns:
        XML string with declaration
    """
    xml_str = ET.tostring(element, encoding='unicode')
    return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'


def main() -> int:
    """CLI entry point for standalone page grouping.

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    import argparse
    import sys

    parser = argparse.ArgumentParser(
        description='Group pages by TOC structure'
    )
    parser.add_argument('input', help='Input book.xml file')
    parser.add_argument(
        '-o', '--output', help='Output file (default: stdout)'
    )
    args = parser.parse_args()

    try:
        # Read input file
        with open(args.input, 'r', encoding='utf-8') as f:
            input_xml = f.read()

        # Group pages
        result = group_pages_by_toc(input_xml)

        # Write output
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(result)
        else:
            print(result)

        return 0

    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    import sys
    sys.exit(main())
