"""Hierarchical structure building functions."""

from __future__ import annotations

import re
from xml.etree import ElementTree as ET

from src.book_converter.models import (
    Heading,
    Page,
    Paragraph,
    Section,
    SectionElement,
    TocEntry,
)
from src.book_converter.transformer_utils import is_duplicate_heading

from .models import FlattenStats, TOCEntry
from .section import is_chapter_title_page, normalize_for_matching, parse_section_number


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


def _find_first_chapter_entry(toc_lookup: dict[str, TocEntry]) -> str | None:
    """Find the first chapter number in TOC."""
    chapter_numbers = [num for num, entry in toc_lookup.items() if entry.level == 1 and num and num.isdigit()]
    if not chapter_numbers:
        return None
    return min(chapter_numbers, key=lambda x: int(x))


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


def _build_chapters(
    page_assignments: dict[str, list[Page]],
    toc_lookup: dict[str, TocEntry],
) -> tuple:
    """Build chapters from page assignments.

    Args:
        page_assignments: Dict mapping section number to pages
        toc_lookup: Dict mapping section number to TocEntry

    Returns:
        Tuple of Chapter objects
    """
    from src.book_converter.models import Chapter

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
) -> tuple:
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
