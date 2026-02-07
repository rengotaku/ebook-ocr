"""Transformer module for book markdown to XML conversion.

Provides functions to transform data models into XML elements.
"""

from __future__ import annotations

from xml.etree.ElementTree import Element

from src.book_converter.models import (
    Page,
    PageAnnouncement,
    Content,
    Paragraph,
    Heading,
    List,
)


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
            para_elem.text = element.text
            elem.append(para_elem)
        elif isinstance(element, Heading):
            heading_elem = Element("heading")
            heading_elem.set("level", str(element.level))
            heading_elem.text = element.text
            elem.append(heading_elem)
        elif isinstance(element, List):
            list_elem = Element("list")
            for item in element.items:
                item_elem = Element("item")
                item_elem.text = item
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
