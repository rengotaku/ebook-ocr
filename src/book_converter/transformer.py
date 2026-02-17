"""Transformer module for book markdown to XML conversion.

Provides functions to transform data models into XML elements.
"""

from __future__ import annotations

import re
from xml.etree.ElementTree import Element, SubElement

from src.book_converter.models import (
    Book,
    BookMetadata,
    Chapter,
    Section,
    Paragraph,
    Heading,
    List,
    Figure,
    TocEntry,
    TableOfContents,
)


# ============================================================
# Phase 7: Heading Normalization and Duplicate Detection
# ============================================================


def normalize_heading_for_comparison(heading_text: str) -> str:
    """Normalize heading text for comparison with container titles.

    Removes "Chapter N" or "Section N.N" prefix and normalizes whitespace.

    Args:
        heading_text: Original heading text (e.g., "Chapter 1 「企画」で失敗")

    Returns:
        Normalized text (e.g., "1 「企画」で失敗")

    Examples:
        >>> normalize_heading_for_comparison("Chapter 1 「企画」で失敗")
        '1 「企画」で失敗'
        >>> normalize_heading_for_comparison("Section 1.1 なんでもできる")
        '1.1 なんでもできる'
        >>> normalize_heading_for_comparison("すべての要求に応えてしまう")
        'すべての要求に応えてしまう'
    """
    text = heading_text

    # Remove "Chapter N" prefix (case-insensitive)
    text = re.sub(r'^[Cc][Hh][Aa][Pp][Tt][Ee][Rr]\s+(\d+)\s*', r'\1 ', text)

    # Remove "Section N.N" prefix (case-insensitive)
    text = re.sub(r'^[Ss][Ee][Cc][Tt][Ii][Oo][Nn]\s+(\d+\.\d+)\s*', r'\1 ', text)

    # Normalize whitespace (collapse multiple spaces to single space)
    text = ' '.join(text.split())

    return text.strip()


def is_duplicate_heading(
    heading_text: str,
    container_number: str | None,
    container_title: str,
) -> bool:
    """Check if heading is a duplicate of the container's title.

    A heading is considered duplicate if its normalized form matches
    "{number} {title}" or just "{title}" (when number is None).

    Args:
        heading_text: The heading text to check
        container_number: The container's number (e.g., "1" or "1.1")
        container_title: The container's title

    Returns:
        True if the heading is a duplicate, False otherwise

    Examples:
        >>> is_duplicate_heading("Chapter 1 「企画」で失敗", "1", "「企画」で失敗")
        True
        >>> is_duplicate_heading("すべての要求に応えてしまう", "1.1", "なんでもできる")
        False
    """
    normalized = normalize_heading_for_comparison(heading_text)

    if container_number:
        expected = f"{container_number} {container_title}"
    else:
        expected = container_title

    return normalized == expected


# ============================================================
# New Design: Book → Chapter → Section → Elements
# ============================================================


def transform_book(book: Book) -> Element:
    """Transform Book to XML element.

    Args:
        book: The Book object to transform.

    Returns:
        An XML Element representing the book.

    Example:
        >>> metadata = BookMetadata(title="Test Book")
        >>> book = Book(metadata=metadata)
        >>> elem = transform_book(book)
        >>> elem.tag
        'book'
    """
    elem = Element("book")

    # Metadata
    metadata_elem = transform_book_metadata(book.metadata)
    elem.append(metadata_elem)

    # TOC
    if book.toc:
        toc_elem = transform_table_of_contents(book.toc)
        if toc_elem is not None:
            elem.append(toc_elem)

    # Chapters
    for chapter in book.chapters:
        chapter_elem = transform_chapter(chapter)
        elem.append(chapter_elem)

    return elem


def transform_book_metadata(metadata: BookMetadata) -> Element:
    """Transform BookMetadata to XML element.

    Args:
        metadata: The BookMetadata object to transform.

    Returns:
        An XML Element representing the metadata.
    """
    elem = Element("metadata")

    title_elem = SubElement(elem, "title")
    title_elem.text = metadata.title

    if metadata.isbn:
        isbn_elem = SubElement(elem, "isbn")
        isbn_elem.text = metadata.isbn

    return elem


def transform_chapter(chapter: Chapter) -> Element:
    """Transform Chapter to XML element.

    <chapter number="1" title="Chapter Title">
      <section .../>
    </chapter>

    Args:
        chapter: The Chapter object to transform.

    Returns:
        An XML Element representing the chapter.
    """
    elem = Element("chapter")

    if chapter.number:
        elem.set("number", chapter.number)
    elem.set("title", chapter.title)

    for section in chapter.sections:
        section_elem = transform_section(section)
        elem.append(section_elem)

    return elem


def transform_section(section: Section) -> Element:
    """Transform Section to XML element.

    <section number="1.1" title="Section Title">
      <paragraph>...</paragraph>
      <heading level="3">...</heading>
      <list>...</list>
      <figure .../>
    </section>

    Args:
        section: The Section object to transform.

    Returns:
        An XML Element representing the section.
    """
    elem = Element("section")

    if section.number:
        elem.set("number", section.number)
    elem.set("title", section.title)

    for child in section.elements:
        if isinstance(child, Paragraph):
            child_elem = transform_paragraph(child)
            elem.append(child_elem)
        elif isinstance(child, Heading):
            child_elem = transform_heading(child)
            elem.append(child_elem)
        elif isinstance(child, List):
            child_elem = transform_list(child)
            elem.append(child_elem)
        elif isinstance(child, Figure):
            child_elem = transform_figure(child)
            elem.append(child_elem)

    return elem


def transform_paragraph(para: Paragraph) -> Element:
    """Transform Paragraph to XML element.

    readAloud="false" only when read_aloud=False (skip区間).

    Args:
        para: The Paragraph object to transform.

    Returns:
        An XML Element representing the paragraph.
    """
    elem = Element("paragraph")

    # Only output readAloud="false" when skipping
    if not para.read_aloud:
        elem.set("readAloud", "false")

    apply_emphasis(para.text, elem)
    return elem


def transform_heading(heading: Heading) -> Element:
    """Transform Heading to XML element.

    readAloud="false" only when read_aloud=False (skip区間).

    Args:
        heading: The Heading object to transform.

    Returns:
        An XML Element representing the heading.
    """
    elem = Element("heading")
    elem.set("level", str(heading.level))

    # Only output readAloud="false" when skipping
    if not heading.read_aloud:
        elem.set("readAloud", "false")

    apply_emphasis(heading.text, elem)
    return elem


def transform_list(lst: List) -> Element:
    """Transform List to XML element.

    readAloud="false" only when read_aloud=False (skip区間).

    Args:
        lst: The List object to transform.

    Returns:
        An XML Element representing the list.
    """
    elem = Element("list")

    # Only output readAloud="false" when skipping
    if not lst.read_aloud:
        elem.set("readAloud", "false")

    for item_text in lst.items:
        item_elem = SubElement(elem, "item")
        apply_emphasis(item_text, item_elem)

    return elem


def transform_figure(figure: Figure) -> Element:
    """Transform Figure to XML element.

    <figure path="figures/fig001.png" caption="図1: 説明"/>

    Figure は常に読まないので readAloud 属性は出力しない。

    Args:
        figure: The Figure object to transform.

    Returns:
        An XML Element representing the figure.
    """
    elem = Element("figure")
    elem.set("path", figure.path)

    if figure.caption:
        elem.set("caption", figure.caption)

    if figure.marker:
        elem.set("marker", figure.marker)

    return elem


def transform_toc_entry(entry: TocEntry) -> Element:
    """Transform TocEntry to XML element.

    <entry level="1" number="1" title="SREとは" page="15"/>

    Args:
        entry: The TocEntry object to transform.

    Returns:
        An XML Element representing the TOC entry.
    """
    elem = Element("entry")
    elem.set("level", str(entry.level))
    if entry.number:
        elem.set("number", entry.number)
    elem.set("title", entry.text)
    if entry.page:
        elem.set("page", entry.page)
    return elem


def transform_table_of_contents(toc: TableOfContents | None) -> Element | None:
    """Transform TableOfContents to XML element.

    <toc begin="13" end="15">
      <entry .../>
    </toc>

    TOC は常に読まないので readAloud 属性は出力しない。

    Args:
        toc: The TableOfContents object to transform.

    Returns:
        An XML Element, or None if toc is None or empty.
    """
    if toc is None or not toc.entries:
        return None

    elem = Element("toc")
    if toc.begin_page:
        elem.set("begin", toc.begin_page)
    if toc.end_page:
        elem.set("end", toc.end_page)

    for entry in toc.entries:
        entry_elem = transform_toc_entry(entry)
        elem.append(entry_elem)

    return elem


def apply_emphasis(text: str, parent: Element) -> None:
    """Apply emphasis conversion to text.

    Converts **text** to <em>text</em>.

    Args:
        text: The text to process.
        parent: The parent element to add text and em children to.

    Example:
        >>> elem = Element("paragraph")
        >>> apply_emphasis("before **bold** after", elem)
        >>> elem.text
        'before '
        >>> elem.find("em").text
        'bold'
    """
    if not text:
        return

    pattern = r"\*\*(.+?)\*\*"
    parts = re.split(pattern, text)

    if len(parts) == 1:
        parent.text = text
        return

    parent.text = parts[0] if parts[0] else None

    for i in range(1, len(parts), 2):
        emphasis_text = parts[i]
        normal_text = parts[i + 1] if i + 1 < len(parts) else ""

        em = SubElement(parent, "em")
        em.text = emphasis_text
        em.tail = normal_text if normal_text else None


# ============================================================
# Legacy functions (parser.py との互換性用)
# ============================================================

from src.book_converter.models import (
    Page,
    PageAnnouncement,
    Content,
    PageMetadata,
    StructureContainer,
)


def transform_page(page: Page) -> Element:
    """Transform a Page object into an XML Element (Legacy)."""
    elem = Element("page")
    elem.set("number", page.number)
    elem.set("sourceFile", page.source_file)

    if page.continued:
        elem.set("continued", "true")

    if page.page_type != "normal":
        elem.set("type", page.page_type)

    if page.announcement is not None:
        announcement_elem = transform_page_announcement(page.announcement)
        if announcement_elem is not None:
            elem.append(announcement_elem)

    content_elem = transform_content(page.content)
    if content_elem is not None:
        elem.append(content_elem)

    for figure in page.figures:
        figure_elem = transform_figure_legacy(figure)
        if figure_elem is not None:
            elem.append(figure_elem)

    if page.metadata is not None:
        metadata_elem = transform_page_metadata(page.metadata)
        if metadata_elem is not None:
            elem.append(metadata_elem)

    return elem


def transform_content(content: Content) -> Element | None:
    """Transform a Content object into an XML Element (Legacy)."""
    if not content.elements:
        return None

    elem = Element("content")
    elem.set("readAloud", "true" if content.read_aloud else "false")

    for element in content.elements:
        if isinstance(element, Paragraph):
            para_elem = Element("paragraph")
            para_elem.set("readAloud", "true" if element.read_aloud else "false")
            apply_emphasis(element.text, para_elem)
            elem.append(para_elem)
        elif isinstance(element, Heading):
            heading_elem = Element("heading")
            heading_elem.set("level", str(element.level))
            heading_elem.set("readAloud", "true" if element.read_aloud else "false")
            apply_emphasis(element.text, heading_elem)
            elem.append(heading_elem)
        elif isinstance(element, List):
            list_elem = Element("list")
            list_elem.set("readAloud", "true" if element.read_aloud else "false")
            for item in element.items:
                item_elem = Element("item")
                apply_emphasis(item, item_elem)
                list_elem.append(item_elem)
            elem.append(list_elem)

    return elem


def transform_page_announcement(announcement: PageAnnouncement | None) -> Element | None:
    """Transform a PageAnnouncement (Legacy)."""
    if announcement is None:
        return None

    elem = Element("pageAnnouncement")
    elem.text = announcement.text
    elem.set("format", announcement.format)
    elem.set("readAloud", "false")
    return elem


def transform_figure_legacy(figure: Figure) -> Element:
    """Transform a Figure object (Legacy format)."""
    elem = Element("figure")
    elem.set("readAloud", "false")

    if figure.path:
        elem.set("path", figure.path)
        if figure.marker:
            elem.set("marker", figure.marker)

    return elem


def transform_page_metadata(metadata: PageMetadata | None) -> Element | None:
    """Transform a PageMetadata (Legacy)."""
    if metadata is None:
        return None

    elem = Element("pageMetadata")
    elem.set("type", metadata.meta_type)
    elem.set("readAloud", "false")
    apply_emphasis(metadata.text, elem)
    return elem


def transform_structure_container(container: StructureContainer) -> Element:
    """Transform StructureContainer to XML element (Legacy)."""
    elem = Element(container.container_type)

    if container.container_type in ("chapter", "section"):
        if container.number:
            elem.set("number", container.number)
        elem.set("title", container.title)
    elif container.container_type == "subsection":
        elem.set("level", str(container.level))
        if container.number:
            elem.set("number", container.number)
        elem.set("title", container.title)

    for child in container.children:
        if isinstance(child, StructureContainer):
            child_elem = transform_structure_container(child)
            elem.append(child_elem)
        elif isinstance(child, Heading):
            heading_elem = Element("heading")
            heading_elem.set("readAloud", "true" if child.read_aloud else "false")
            apply_emphasis(child.text, heading_elem)
            elem.append(heading_elem)
        elif isinstance(child, Paragraph):
            para_elem = Element("paragraph")
            apply_emphasis(child.text, para_elem)
            elem.append(para_elem)
        elif isinstance(child, List):
            list_elem = Element("list")
            for item in child.items:
                item_elem = Element("item")
                apply_emphasis(item, item_elem)
                list_elem.append(item_elem)
            elem.append(list_elem)

    return elem


def transform_content_with_continued(content: Content, continued: bool) -> Element | None:
    """Transform a Content object with continued attribute (Legacy)."""
    elem = transform_content(content)

    if elem is None:
        return None

    if continued:
        elem.set("continued", "true")

    return elem
