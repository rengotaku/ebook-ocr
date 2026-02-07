"""Transformer module for book markdown to XML conversion.

Provides functions to transform data models into XML elements.
"""

from __future__ import annotations

import re
from xml.etree.ElementTree import Element, SubElement

from src.book_converter.models import (
    Page,
    PageAnnouncement,
    Content,
    Paragraph,
    Heading,
    List,
    Figure,
    PageMetadata,
)


def apply_emphasis(text: str, parent: Element) -> None:
    """Apply emphasis conversion to text and set on parent element.

    Converts **text** patterns to <emphasis>text</emphasis> elements.

    Args:
        text: The text to process for emphasis patterns.
        parent: The parent element to add text and emphasis children to.

    Example:
        >>> elem = Element("paragraph")
        >>> apply_emphasis("before **bold** after", elem)
        >>> elem.text
        'before '
        >>> elem.find("emphasis").text
        'bold'
        >>> elem.find("emphasis").tail
        ' after'
    """
    if not text:
        return

    pattern = r"\*\*(.+?)\*\*"
    parts = re.split(pattern, text)

    # parts example: ['before', 'emphasis1', 'middle', 'emphasis2', 'after']
    # Even indices: normal text
    # Odd indices: emphasized text

    if len(parts) == 1:
        # No emphasis found
        parent.text = text
        return

    # First text (before any emphasis)
    parent.text = parts[0] if parts[0] else None

    for i in range(1, len(parts), 2):
        emphasis_text = parts[i]
        normal_text = parts[i + 1] if i + 1 < len(parts) else ""

        emphasis = SubElement(parent, "emphasis")
        emphasis.text = emphasis_text
        emphasis.tail = normal_text if normal_text else None


def transform_page(page: Page) -> Element:
    """Transform a Page object into an XML Element.

    Args:
        page: The Page object to transform.

    Returns:
        An XML Element representing the page.
    """
    elem = Element("page")

    # Required attributes
    elem.set("number", page.number)
    elem.set("sourceFile", page.source_file)

    # Optional attributes
    if page.continued:
        elem.set("continued", "true")

    if page.page_type != "normal":
        elem.set("type", page.page_type)

    # Child elements
    if page.announcement is not None:
        announcement_elem = transform_page_announcement(page.announcement)
        if announcement_elem is not None:
            elem.append(announcement_elem)

    # Add content elements
    content_elem = transform_content(page.content)
    if content_elem is not None:
        elem.append(content_elem)

    # Add figures
    for figure in page.figures:
        figure_elem = transform_figure(figure)
        if figure_elem is not None:
            elem.append(figure_elem)

    # Add metadata
    if page.metadata is not None:
        metadata_elem = transform_page_metadata(page.metadata)
        if metadata_elem is not None:
            elem.append(metadata_elem)

    return elem


def transform_content(content: Content) -> Element | None:
    """Transform a Content object into an XML Element.

    Args:
        content: The Content object to transform.

    Returns:
        An XML Element representing the content, or None if no elements.
    """
    if not content.elements:
        return None

    elem = Element("content")

    for element in content.elements:
        if isinstance(element, Paragraph):
            para_elem = Element("paragraph")
            apply_emphasis(element.text, para_elem)
            elem.append(para_elem)
        elif isinstance(element, Heading):
            heading_elem = Element("heading")
            heading_elem.set("level", str(element.level))
            apply_emphasis(element.text, heading_elem)
            elem.append(heading_elem)
        elif isinstance(element, List):
            list_elem = Element("list")
            for item in element.items:
                item_elem = Element("item")
                apply_emphasis(item, item_elem)
                list_elem.append(item_elem)
            elem.append(list_elem)

    return elem


def transform_page_announcement(
    announcement: PageAnnouncement | None,
) -> Element | None:
    """Transform a PageAnnouncement into an XML Element.

    Args:
        announcement: The PageAnnouncement object to transform.

    Returns:
        An XML Element representing the announcement, or None if input is None.
    """
    if announcement is None:
        return None

    elem = Element("pageAnnouncement")
    elem.text = announcement.text
    elem.set("format", announcement.format)

    return elem


def transform_heading(heading: Heading) -> Element:
    """Transform a Heading into an XML Element.

    Args:
        heading: The Heading object to transform.

    Returns:
        An XML Element representing the heading.

    Example:
        >>> heading = Heading(level=1, text="Chapter 1")
        >>> elem = transform_heading(heading)
        >>> elem.tag
        'heading'
        >>> elem.get("level")
        '1'
    """
    elem = Element("heading")
    elem.set("level", str(heading.level))
    elem.text = heading.text

    return elem


def transform_content_with_continued(
    content: Content, continued: bool
) -> Element | None:
    """Transform a Content object with continued attribute.

    Args:
        content: The Content object to transform.
        continued: Whether this content continues from previous page.

    Returns:
        An XML Element with optional continued="true" attribute,
        or None if no elements.

    Example:
        >>> content = Content(elements=(Paragraph(text="Text"),))
        >>> elem = transform_content_with_continued(content, True)
        >>> elem.get("continued")
        'true'
    """
    elem = transform_content(content)

    if elem is None:
        return None

    if continued:
        elem.set("continued", "true")

    return elem


def transform_figure(figure: Figure) -> Element:
    """Transform a Figure object into an XML Element.

    Args:
        figure: The Figure object to transform.

    Returns:
        An XML Element representing the figure.

    Example:
        >>> fig = Figure(file="image.png", caption="Title", description="Desc")
        >>> elem = transform_figure(fig)
        >>> elem.tag
        'figure'
        >>> elem.get("readAloud")
        'optional'
    """
    elem = Element("figure")
    elem.set("readAloud", figure.read_aloud)

    if figure.continued:
        elem.set("continued", "true")

    # file element (always readAloud="false")
    file_elem = Element("file")
    file_elem.text = figure.file
    file_elem.set("readAloud", "false")
    elem.append(file_elem)

    # caption element (readAloud="true" if present)
    if figure.caption:
        caption_elem = Element("caption")
        caption_elem.text = figure.caption
        caption_elem.set("readAloud", "true")
        elem.append(caption_elem)

    # description element (inherits from parent)
    if figure.description:
        desc_elem = Element("description")
        desc_elem.text = figure.description
        elem.append(desc_elem)

    return elem


def transform_page_metadata(metadata: PageMetadata | None) -> Element | None:
    """Transform a PageMetadata object into an XML Element.

    Args:
        metadata: The PageMetadata object to transform.

    Returns:
        An XML Element representing the page metadata, or None if input is None.

    Example:
        >>> meta = PageMetadata(text="3 / 7", meta_type="chapter-page")
        >>> elem = transform_page_metadata(meta)
        >>> elem.tag
        'pageMetadata'
        >>> elem.get("type")
        'chapter-page'
        >>> elem.get("readAloud")
        'false'
    """
    if metadata is None:
        return None

    elem = Element("pageMetadata")
    elem.set("type", metadata.meta_type)
    elem.set("readAloud", "false")  # Always false for metadata
    apply_emphasis(metadata.text, elem)

    return elem
