"""Section number extraction and parsing functions."""

from __future__ import annotations

import re
from xml.etree import ElementTree as ET

from src.book_converter.models import HeaderLevelConfig

from .models import SectionNumber


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
