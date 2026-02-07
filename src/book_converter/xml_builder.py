"""XML builder module for book markdown to XML conversion.

Provides functions to build and serialize XML from data models.
"""

from __future__ import annotations

from xml.etree.ElementTree import Element, tostring

from src.book_converter.models import Book
from src.book_converter.transformer import transform_page


def build_xml(book: Book) -> str:
    """Build an XML string from a Book object.

    Args:
        book: The Book object to convert.

    Returns:
        XML string with proper encoding declaration.
    """
    # Create root element
    root = Element("book")

    # Add metadata section
    metadata = Element("metadata")
    title = Element("title")
    title.text = book.metadata.title
    metadata.append(title)

    if book.metadata.isbn:
        isbn = Element("isbn")
        isbn.text = book.metadata.isbn
        metadata.append(isbn)

    root.append(metadata)

    # Add pages
    for page in book.pages:
        page_elem = transform_page(page)
        root.append(page_elem)

    # Serialize to string with XML declaration
    xml_bytes = tostring(root, encoding="UTF-8", xml_declaration=True)
    xml_string = xml_bytes.decode("UTF-8")

    # Fix XML declaration to use double quotes instead of single quotes
    xml_string = xml_string.replace(
        "<?xml version='1.0' encoding='UTF-8'?>",
        '<?xml version="1.0" encoding="UTF-8"?>'
    )

    return xml_string
