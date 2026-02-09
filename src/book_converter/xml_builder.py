"""XML builder module for book markdown to XML conversion.

Provides functions to build and serialize XML from data models.
"""

from __future__ import annotations

from xml.etree.ElementTree import Element, tostring, Comment

from src.book_converter.models import Book, ConversionError
from src.book_converter.transformer import transform_page, transform_table_of_contents


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

    # Add TOC after metadata (if exists)
    toc_elem = transform_table_of_contents(book.toc)
    if toc_elem is not None:
        root.append(toc_elem)

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


def insert_error_comment(element: Element, error: ConversionError) -> None:
    """Insert an error comment into an XML element.

    Args:
        element: The XML element to insert the comment into.
        error: The ConversionError to convert into a comment.

    The comment format is: <!-- ERROR: [type] - [message] -->
    """
    comment_text = f" ERROR: {error.error_type} - {error.message} "
    comment = Comment(comment_text)
    element.append(comment)


def build_xml_with_errors(book: Book, errors: list[ConversionError]) -> str:
    """Build an XML string from a Book object with error comments.

    Args:
        book: The Book object to convert.
        errors: List of ConversionError objects to insert as comments.

    Returns:
        XML string with proper encoding declaration and error comments.
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

    # Add TOC after metadata (if exists)
    toc_elem = transform_table_of_contents(book.toc)
    if toc_elem is not None:
        root.append(toc_elem)

    # Build a mapping of page numbers to errors
    page_errors: dict[str, list[ConversionError]] = {}
    for error in errors:
        page_num = error.page_number or ""
        if page_num not in page_errors:
            page_errors[page_num] = []
        page_errors[page_num].append(error)

    # Add pages with error comments
    for page in book.pages:
        page_elem = transform_page(page)

        # Insert error comments for this page
        if page.number in page_errors:
            for error in page_errors[page.number]:
                insert_error_comment(page_elem, error)

        # Also check for errors with empty page number
        if "" in page_errors and page.number == "":
            for error in page_errors[""]:
                insert_error_comment(page_elem, error)

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
