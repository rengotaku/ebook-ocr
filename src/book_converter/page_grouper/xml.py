"""XML serialization and conversion functions."""

from __future__ import annotations

from xml.etree import ElementTree as ET

from src.book_converter.models import (
    Book,
    BookMetadata,
    HeaderLevelConfig,
    Page,
    TableOfContents,
)

from .assignment import _assign_pages_to_sections_new
from .hierarchy import _build_chapters


def _serialize_to_xml(element: ET.Element) -> str:
    """Serialize XML element to string.

    Args:
        element: Root element

    Returns:
        XML string with declaration
    """
    xml_str = ET.tostring(element, encoding="unicode")
    return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_str}'


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
    from src.book_converter.models import Chapter

    if not toc or not toc.entries:
        # No TOC: put all content in a single chapter
        from .hierarchy import _pages_to_section

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


def main() -> int:
    """CLI entry point for standalone page grouping.

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    import argparse
    import sys

    from .assignment import group_pages_by_toc

    parser = argparse.ArgumentParser(description="Group pages by TOC structure")
    parser.add_argument("input", help="Input book.xml file")
    parser.add_argument("-o", "--output", help="Output file (default: stdout)")
    args = parser.parse_args()

    try:
        # Read input file
        with open(args.input, encoding="utf-8") as f:
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
