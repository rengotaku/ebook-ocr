"""Heading parsing functions."""

from __future__ import annotations

import re

from src.book_converter.models import Heading
from src.book_converter.parser.models import StructureHeading


def parse_structure_heading(line: str) -> StructureHeading | None:
    """Parse a structure heading line.

    Recognizes:
    - # Chapter N Title → level=1, number="N"
    - ## Section N.N Title → level=2, number="N.N"
    - ### Subsection N.N.N Title → level=3, number="N.N.N"

    Args:
        line: A line from the Markdown file.

    Returns:
        StructureHeading if the line matches a structure pattern, None otherwise.

    Example:
        >>> parse_structure_heading("# Chapter 1 Introduction")
        StructureHeading(level=1, number="1", title="Introduction", raw_text="Chapter 1 Introduction")
        >>> parse_structure_heading("## Section 2.3 Details")
        StructureHeading(level=2, number="2.3", title="Details", raw_text="Section 2.3 Details")
    """
    # Pattern: ^(#{1,3})\s*(.*)$
    pattern = r"^(#{1,3})\s*(.*)$"
    match = re.match(pattern, line)

    if not match:
        return None

    markers = match.group(1)
    text = match.group(2).strip()
    md_level = len(markers)

    # Try Chapter pattern: Chapter N Title
    chapter_match = re.match(r"^Chapter\s+(\d+)\s*(.*)?$", text, re.IGNORECASE)
    if chapter_match and md_level == 1:
        number = chapter_match.group(1)
        title = (chapter_match.group(2) or "").strip()
        return StructureHeading(level=1, number=number, title=title, raw_text=text)

    # Try Section pattern: Section N.N Title
    section_match = re.match(r"^Section\s+(\d+\.\d+)\s*(.*)?$", text, re.IGNORECASE)
    if section_match and md_level == 2:
        number = section_match.group(1)
        title = (section_match.group(2) or "").strip()
        return StructureHeading(level=2, number=number, title=title, raw_text=text)

    # Try Subsection pattern: Subsection N.N.N Title
    subsection_match = re.match(r"^Subsection\s+(\d+\.\d+\.\d+)\s*(.*)?$", text, re.IGNORECASE)
    if subsection_match and md_level == 3:
        number = subsection_match.group(1)
        title = (subsection_match.group(2) or "").strip()
        return StructureHeading(level=3, number=number, title=title, raw_text=text)

    return None


def parse_heading(line: str) -> Heading | None:
    """Parse a markdown heading line.

    Args:
        line: A line from the Markdown file.

    Returns:
        Heading object if the line is a heading (# - ###), None otherwise.
        Level 4+ headings are converted to level 3.

    Example:
        >>> parse_heading("# Chapter 1")
        Heading(level=1, text="Chapter 1", read_aloud=True)
        >>> parse_heading("#### Deep heading")
        Heading(level=3, text="Deep heading", read_aloud=True)
    """
    # Pattern: ^(#{1,6})\s*(.*)$
    # Must start at beginning of line (no leading whitespace)
    pattern = r"^(#{1,6})\s*(.*)$"
    match = re.match(pattern, line)

    if not match:
        return None

    markers = match.group(1)
    text = match.group(2)

    # Calculate level (1-6 from markdown, but cap at 3)
    level = len(markers)
    if level > 3:
        level = 3

    return Heading(level=level, text=text, read_aloud=True)


def parse_heading_with_warning(line: str) -> tuple[Heading | None, str | None]:
    """Parse a heading and return warning if level 4+.

    Args:
        line: A line from the Markdown file.

    Returns:
        Tuple of (Heading, warning). Warning is set if level 4+ was detected.
    """
    pattern = r"^(#{1,6})\s*(.*)$"
    match = re.match(pattern, line)

    if not match:
        return (None, None)

    markers = match.group(1)
    original_level = len(markers)

    heading = parse_heading(line)

    if original_level > 3:
        warning = f"見出しlevel {original_level}階層は3階層に統合されました"
        return (heading, warning)

    return (heading, None)
