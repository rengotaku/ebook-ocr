"""Tests for page grouping by TOC structure.

Tests for User Story 1 (Basic Page Grouping) and User Story 2 (Section Detection).
"""

from __future__ import annotations

from xml.etree import ElementTree as ET

import pytest

from src.book_converter.page_grouper import (
    SectionNumber,
    TOCEntry,
    extract_section_from_heading,
    extract_section_from_page_metadata,
    group_pages_by_toc,
    is_chapter_title_page,
    parse_section_number,
    parse_toc,
)


# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture
def sample_toc_xml() -> str:
    """Sample TOC XML element for testing."""
    return """<toc begin="7" end="13">
        <entry level="chapter" number="1" title="SREとは" page="14" />
        <entry level="section" number="1.1" title="SREの概要" page="15" />
        <entry level="subsection" number="1.1.1" title="サイトとは何か" page="18" />
        <entry level="section" number="1.2" title="なぜSREが重要なのか" page="20" />
        <entry level="chapter" number="2" title="信頼性を定義して計測する" page="30" />
        <entry level="section" number="2.1" title="SLOを理解するための基礎概念" page="31" />
        <entry level="subsection" number="2.1.1" title="SLA" page="32" />
    </toc>"""


@pytest.fixture
def sample_book_xml() -> str:
    """Sample book XML with flat page structure for testing grouping."""
    return """<?xml version="1.0" encoding="UTF-8"?>
<book>
    <metadata><title>Converted Book</title></metadata>
    <toc begin="7" end="13">
        <entry level="chapter" number="1" title="SREとは" page="14" />
        <entry level="section" number="1.1" title="SREの概要" page="15" />
        <entry level="subsection" number="1.1.1" title="サイトとは何か" page="18" />
    </toc>
    <page number="1" sourceFile="page_0001.png">
        <content readAloud="false">
            <paragraph readAloud="false">表紙</paragraph>
        </content>
    </page>
    <page number="6" sourceFile="page_0006.png">
        <pageMetadata type="chapter-page" readAloud="false"><emphasis>はじめに</emphasis> 1 / 3</pageMetadata>
        <content readAloud="false">
            <paragraph readAloud="false">序文</paragraph>
        </content>
    </page>
    <page number="7" sourceFile="page_0007.png">
        <pageMetadata type="toc-page" readAloud="false">目次 1 / 7</pageMetadata>
        <content readAloud="false">
            <paragraph readAloud="false">目次ページ1</paragraph>
        </content>
    </page>
    <page number="13" sourceFile="page_0013.png">
        <pageMetadata type="toc-page" readAloud="false">目次 7 / 7</pageMetadata>
        <content readAloud="false">
            <paragraph readAloud="false">目次ページ最終</paragraph>
        </content>
    </page>
    <page number="14" sourceFile="page_0014.png">
        <pageMetadata type="chapter-page" readAloud="false">第1章 SREとは — 1 / 1</pageMetadata>
        <content readAloud="false">
            <heading level="1" readAloud="false">第1章 SREとは</heading>
        </content>
    </page>
    <page number="15" sourceFile="page_0015.png">
        <pageMetadata type="section-page" readAloud="false">1.1 SREの概要 ― 1 / 3</pageMetadata>
        <content readAloud="false">
            <heading level="2" readAloud="false">1.1 SREの概要</heading>
            <paragraph readAloud="false">SREはGoogleで生まれた...</paragraph>
        </content>
    </page>
    <page number="16" sourceFile="page_0016.png">
        <pageMetadata type="section-page" readAloud="false">1.1 SREの概要 ― 2 / 3</pageMetadata>
        <content readAloud="false">
            <paragraph readAloud="false">続き...</paragraph>
        </content>
    </page>
    <page number="17" sourceFile="page_0017.png">
        <pageMetadata type="section-page" readAloud="false">1.1 SREの概要 ― 3 / 3</pageMetadata>
        <content readAloud="false">
            <paragraph readAloud="false">終わり</paragraph>
        </content>
    </page>
    <page number="18" sourceFile="page_0018.png">
        <pageMetadata type="subsection-page" readAloud="false">1.1.1 サイトとは何か ― 1 / 2</pageMetadata>
        <content readAloud="false">
            <heading level="3" readAloud="false">1.1.1 サイトとは何か</heading>
            <paragraph readAloud="false">サイトとは...</paragraph>
        </content>
    </page>
</book>"""


# =============================================================================
# US2 Tests: Section Number Extraction
# =============================================================================


class TestExtractSectionFromPageMetadata:
    """Tests for extracting section number from pageMetadata content."""

    def test_extract_section_standard_format(self) -> None:
        """Extract section from standard format '1.1 SREの概要 ― 1 / 3'."""
        metadata = "1.1 SREの概要 ― 1 / 3"
        result = extract_section_from_page_metadata(metadata)
        assert result == "1.1"

    def test_extract_section_chapter_format(self) -> None:
        """Extract section from chapter format '第1章 SREとは — 1 / 1'."""
        metadata = "第1章 SREとは — 1 / 1"
        result = extract_section_from_page_metadata(metadata)
        assert result == "1"

    def test_extract_subsection_format(self) -> None:
        """Extract section from subsection format '2.1.1 SLA ― 2 / 3'."""
        metadata = "2.1.1 SLA ― 2 / 3"
        result = extract_section_from_page_metadata(metadata)
        assert result == "2.1.1"

    def test_extract_section_deep_nesting(self) -> None:
        """Extract section from deeply nested format '1.2.3.4 Title'."""
        metadata = "1.2.3.4 深いネスト ― 1 / 1"
        result = extract_section_from_page_metadata(metadata)
        assert result == "1.2.3.4"

    def test_extract_section_front_matter_returns_none(self) -> None:
        """Return None for front-matter with emphasis like '<emphasis>はじめに</emphasis> 1 / 3'."""
        metadata = "<emphasis>はじめに</emphasis> 1 / 3"
        result = extract_section_from_page_metadata(metadata)
        assert result is None

    def test_extract_section_no_section_info_returns_none(self) -> None:
        """Return None when no section info like '1 / 1'."""
        metadata = "1 / 1"
        result = extract_section_from_page_metadata(metadata)
        assert result is None

    def test_extract_section_empty_string_returns_none(self) -> None:
        """Return None for empty string."""
        metadata = ""
        result = extract_section_from_page_metadata(metadata)
        assert result is None

    def test_extract_section_none_input_returns_none(self) -> None:
        """Return None for None input."""
        result = extract_section_from_page_metadata(None)
        assert result is None

    def test_extract_section_full_width_space(self) -> None:
        """Extract section with full-width space '1.1　概要'."""
        metadata = "1.1　SREの概要 ― 1 / 3"
        result = extract_section_from_page_metadata(metadata)
        assert result == "1.1"


class TestExtractSectionFromHeading:
    """Tests for extracting section number from heading content."""

    def test_extract_section_prefix_format(self) -> None:
        """Extract section from 'Section 1.1 SREの概要'."""
        heading = "Section 1.1 SREの概要"
        result = extract_section_from_heading(heading)
        assert result == "1.1"

    def test_extract_subsection_direct_format(self) -> None:
        """Extract section from '1.1.1 サイトとは何か'."""
        heading = "1.1.1 サイトとは何か"
        result = extract_section_from_heading(heading)
        assert result == "1.1.1"

    def test_extract_chapter_direct_format(self) -> None:
        """Extract section from '第1章 SREとは'."""
        heading = "第1章 SREとは"
        result = extract_section_from_heading(heading)
        assert result == "1"

    def test_extract_section_no_number_returns_none(self) -> None:
        """Return None for heading without number like 'はじめに'."""
        heading = "はじめに"
        result = extract_section_from_heading(heading)
        assert result is None

    def test_extract_section_empty_returns_none(self) -> None:
        """Return None for empty heading."""
        heading = ""
        result = extract_section_from_heading(heading)
        assert result is None

    def test_extract_section_none_returns_none(self) -> None:
        """Return None for None input."""
        result = extract_section_from_heading(None)
        assert result is None


class TestParseSectionNumber:
    """Tests for parsing section number string into SectionNumber dataclass."""

    def test_parse_chapter_number(self) -> None:
        """Parse chapter number '1' into SectionNumber."""
        result = parse_section_number("1")
        assert result is not None
        assert result.raw == "1"
        assert result.parts == (1,)
        assert result.level == "chapter"

    def test_parse_section_number(self) -> None:
        """Parse section number '2.1' into SectionNumber."""
        result = parse_section_number("2.1")
        assert result is not None
        assert result.raw == "2.1"
        assert result.parts == (2, 1)
        assert result.level == "section"

    def test_parse_subsection_number(self) -> None:
        """Parse subsection number '2.1.1' into SectionNumber."""
        result = parse_section_number("2.1.1")
        assert result is not None
        assert result.raw == "2.1.1"
        assert result.parts == (2, 1, 1)
        assert result.level == "subsection"

    def test_parse_deep_section_number(self) -> None:
        """Parse deep section number '1.2.3.4' into SectionNumber (level=subsection)."""
        result = parse_section_number("1.2.3.4")
        assert result is not None
        assert result.raw == "1.2.3.4"
        assert result.parts == (1, 2, 3, 4)
        assert result.level == "subsection"

    def test_parse_invalid_returns_none(self) -> None:
        """Return None for invalid section number."""
        result = parse_section_number("abc")
        assert result is None

    def test_parse_empty_returns_none(self) -> None:
        """Return None for empty string."""
        result = parse_section_number("")
        assert result is None

    def test_parse_none_returns_none(self) -> None:
        """Return None for None input."""
        result = parse_section_number(None)
        assert result is None

    def test_section_number_chapter_num_property(self) -> None:
        """Test chapter_num property returns first part."""
        result = parse_section_number("2.1.3")
        assert result is not None
        assert result.chapter_num == 2

    def test_section_number_is_chapter(self) -> None:
        """Test is_chapter property."""
        result = parse_section_number("1")
        assert result is not None
        assert result.is_chapter is True
        assert result.is_section is False
        assert result.is_subsection is False

    def test_section_number_is_section(self) -> None:
        """Test is_section property."""
        result = parse_section_number("1.2")
        assert result is not None
        assert result.is_chapter is False
        assert result.is_section is True
        assert result.is_subsection is False

    def test_section_number_is_subsection(self) -> None:
        """Test is_subsection property."""
        result = parse_section_number("1.2.3")
        assert result is not None
        assert result.is_chapter is False
        assert result.is_section is False
        assert result.is_subsection is True


# =============================================================================
# US1 Tests: TOC Parsing & Page Grouping
# =============================================================================


class TestParseToc:
    """Tests for parsing TOC XML into list of TOCEntry objects."""

    def test_parse_toc_basic(self, sample_toc_xml: str) -> None:
        """Parse TOC XML into list of TOCEntry objects."""
        toc_element = ET.fromstring(sample_toc_xml)
        entries = parse_toc(toc_element)

        assert len(entries) == 7
        assert all(isinstance(e, TOCEntry) for e in entries)

    def test_parse_toc_chapter_entry(self, sample_toc_xml: str) -> None:
        """Verify chapter entry attributes."""
        toc_element = ET.fromstring(sample_toc_xml)
        entries = parse_toc(toc_element)

        chapter1 = entries[0]
        assert chapter1.level == "chapter"
        assert chapter1.number == "1"
        assert chapter1.title == "SREとは"

    def test_parse_toc_section_entry(self, sample_toc_xml: str) -> None:
        """Verify section entry attributes."""
        toc_element = ET.fromstring(sample_toc_xml)
        entries = parse_toc(toc_element)

        section1_1 = entries[1]
        assert section1_1.level == "section"
        assert section1_1.number == "1.1"
        assert section1_1.title == "SREの概要"

    def test_parse_toc_subsection_entry(self, sample_toc_xml: str) -> None:
        """Verify subsection entry attributes."""
        toc_element = ET.fromstring(sample_toc_xml)
        entries = parse_toc(toc_element)

        subsection1_1_1 = entries[2]
        assert subsection1_1_1.level == "subsection"
        assert subsection1_1_1.number == "1.1.1"
        assert subsection1_1_1.title == "サイトとは何か"

    def test_parse_toc_empty(self) -> None:
        """Parse empty TOC returns empty list."""
        toc_xml = '<toc begin="1" end="1"></toc>'
        toc_element = ET.fromstring(toc_xml)
        entries = parse_toc(toc_element)
        assert entries == []

    def test_parse_toc_begin_end_attributes(self) -> None:
        """Parse TOC returns begin/end attributes."""
        toc_xml = '<toc begin="7" end="13"><entry level="chapter" number="1" title="Test" /></toc>'
        toc_element = ET.fromstring(toc_xml)
        entries = parse_toc(toc_element)

        # The function should return entries, begin/end are on element
        assert len(entries) == 1
        assert toc_element.get("begin") == "7"
        assert toc_element.get("end") == "13"


class TestGroupFrontMatter:
    """Tests for grouping front-matter pages (before TOC begins)."""

    def test_group_front_matter_basic(self, sample_book_xml: str) -> None:
        """Pages before TOC.end (inclusive) go to front-matter group per FR-002."""
        result = group_pages_by_toc(sample_book_xml)
        root = ET.fromstring(result)

        front_matter = root.find("front-matter")
        assert front_matter is not None

        pages = front_matter.findall("page")
        page_numbers = [p.get("number") for p in pages]

        # Pages 1-6 (before TOC) should be in front-matter
        assert "1" in page_numbers
        assert "6" in page_numbers
        # Chapter pages (14+) should NOT be in front-matter
        assert "14" not in page_numbers
        assert "15" not in page_numbers

    def test_group_front_matter_includes_toc_pages(self, sample_book_xml: str) -> None:
        """TOC pages (7-13) should be in front-matter but after regular front-matter pages."""
        result = group_pages_by_toc(sample_book_xml)
        root = ET.fromstring(result)

        front_matter = root.find("front-matter")
        assert front_matter is not None

        pages = front_matter.findall("page")
        page_numbers = [p.get("number") for p in pages]

        # TOC pages should also be in front-matter section
        assert "7" in page_numbers
        assert "13" in page_numbers

    def test_group_front_matter_preserves_page_content(self, sample_book_xml: str) -> None:
        """Front-matter pages preserve all original attributes and content."""
        result = group_pages_by_toc(sample_book_xml)
        root = ET.fromstring(result)

        front_matter = root.find("front-matter")
        page1 = front_matter.find("page[@number='1']")

        assert page1 is not None
        assert page1.get("sourceFile") == "page_0001.png"
        assert page1.find("content") is not None
        assert page1.find("content/paragraph") is not None


class TestGroupPagesBySection:
    """Tests for grouping pages by section based on extracted section numbers."""

    def test_group_pages_creates_chapter(self, sample_book_xml: str) -> None:
        """Pages are grouped into chapter elements."""
        result = group_pages_by_toc(sample_book_xml)
        root = ET.fromstring(result)

        chapters = root.findall("chapter")
        assert len(chapters) >= 1

        chapter1 = root.find("chapter[@number='1']")
        assert chapter1 is not None
        assert chapter1.get("title") == "SREとは"

    def test_group_pages_creates_section(self, sample_book_xml: str) -> None:
        """Pages are grouped into section elements within chapter."""
        result = group_pages_by_toc(sample_book_xml)
        root = ET.fromstring(result)

        chapter1 = root.find("chapter[@number='1']")
        assert chapter1 is not None

        sections = chapter1.findall("section")
        assert len(sections) >= 1

        section1_1 = chapter1.find("section[@number='1.1']")
        assert section1_1 is not None
        assert section1_1.get("title") == "SREの概要"

    def test_group_pages_creates_subsection(self, sample_book_xml: str) -> None:
        """Pages are grouped into subsection elements within section."""
        result = group_pages_by_toc(sample_book_xml)
        root = ET.fromstring(result)

        chapter1 = root.find("chapter[@number='1']")
        section1_1 = chapter1.find("section[@number='1.1']")

        subsections = section1_1.findall("subsection")
        assert len(subsections) >= 1

        subsection1_1_1 = section1_1.find("subsection[@number='1.1.1']")
        assert subsection1_1_1 is not None
        assert subsection1_1_1.get("title") == "サイトとは何か"

    def test_group_pages_section_contains_pages(self, sample_book_xml: str) -> None:
        """Section contains its pages based on extracted section number."""
        result = group_pages_by_toc(sample_book_xml)
        root = ET.fromstring(result)

        chapter1 = root.find("chapter[@number='1']")
        section1_1 = chapter1.find("section[@number='1.1']")

        # Pages 15, 16, 17 have section number 1.1
        pages = section1_1.findall("page")
        page_numbers = [p.get("number") for p in pages]

        assert "15" in page_numbers
        assert "16" in page_numbers
        assert "17" in page_numbers

    def test_group_pages_subsection_contains_pages(self, sample_book_xml: str) -> None:
        """Subsection contains its pages based on extracted section number."""
        result = group_pages_by_toc(sample_book_xml)
        root = ET.fromstring(result)

        chapter1 = root.find("chapter[@number='1']")
        section1_1 = chapter1.find("section[@number='1.1']")
        subsection1_1_1 = section1_1.find("subsection[@number='1.1.1']")

        # Page 18 has section number 1.1.1
        pages = subsection1_1_1.findall("page")
        page_numbers = [p.get("number") for p in pages]

        assert "18" in page_numbers


class TestBuildHierarchicalXml:
    """Tests for building hierarchical XML output."""

    def test_build_preserves_metadata(self, sample_book_xml: str) -> None:
        """Output XML preserves book metadata."""
        result = group_pages_by_toc(sample_book_xml)
        root = ET.fromstring(result)

        metadata = root.find("metadata")
        assert metadata is not None

        title = metadata.find("title")
        assert title is not None
        assert title.text == "Converted Book"

    def test_build_preserves_toc(self, sample_book_xml: str) -> None:
        """Output XML preserves TOC element."""
        result = group_pages_by_toc(sample_book_xml)
        root = ET.fromstring(result)

        toc = root.find("toc")
        assert toc is not None
        assert toc.get("begin") == "7"
        assert toc.get("end") == "13"

        entries = toc.findall("entry")
        assert len(entries) >= 1

    def test_build_structure_order(self, sample_book_xml: str) -> None:
        """Output XML has correct element order: metadata, toc, front-matter, chapters."""
        result = group_pages_by_toc(sample_book_xml)
        root = ET.fromstring(result)

        children = list(root)
        child_tags = [c.tag for c in children]

        # Expected order: metadata, toc, front-matter, chapter(s)
        assert child_tags[0] == "metadata"
        assert child_tags[1] == "toc"
        assert child_tags[2] == "front-matter"
        assert "chapter" in child_tags

    def test_build_well_formed_xml(self, sample_book_xml: str) -> None:
        """Output is well-formed XML."""
        result = group_pages_by_toc(sample_book_xml)

        # Should not raise an exception
        root = ET.fromstring(result)
        assert root.tag == "book"

    def test_build_page_preserves_all_attributes(self, sample_book_xml: str) -> None:
        """Pages preserve all original attributes (number, sourceFile)."""
        result = group_pages_by_toc(sample_book_xml)
        root = ET.fromstring(result)

        # Find page 15 in section 1.1
        chapter1 = root.find("chapter[@number='1']")
        section1_1 = chapter1.find("section[@number='1.1']")
        page15 = section1_1.find("page[@number='15']")

        assert page15 is not None
        assert page15.get("sourceFile") == "page_0015.png"

    def test_build_page_preserves_all_children(self, sample_book_xml: str) -> None:
        """Pages preserve all original child elements (content, pageMetadata)."""
        result = group_pages_by_toc(sample_book_xml)
        root = ET.fromstring(result)

        # Find page 15
        chapter1 = root.find("chapter[@number='1']")
        section1_1 = chapter1.find("section[@number='1.1']")
        page15 = section1_1.find("page[@number='15']")

        assert page15 is not None
        assert page15.find("pageMetadata") is not None
        assert page15.find("content") is not None
        assert page15.find("content/heading") is not None
        assert page15.find("content/paragraph") is not None

    def test_build_no_flat_pages_at_book_level(self, sample_book_xml: str) -> None:
        """After grouping, no pages should remain directly under book element."""
        result = group_pages_by_toc(sample_book_xml)
        root = ET.fromstring(result)

        # Direct page children of book should not exist
        direct_pages = [c for c in root if c.tag == "page"]
        assert len(direct_pages) == 0


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Edge case tests for page grouping."""

    def test_book_without_toc(self) -> None:
        """Book without TOC element returns pages ungrouped or in front-matter."""
        book_xml = """<?xml version="1.0" encoding="UTF-8"?>
<book>
    <metadata><title>No TOC Book</title></metadata>
    <page number="1" sourceFile="page_0001.png">
        <content readAloud="false"><paragraph>Content</paragraph></content>
    </page>
</book>"""
        result = group_pages_by_toc(book_xml)
        root = ET.fromstring(result)

        # All pages should be in front-matter when no TOC exists
        front_matter = root.find("front-matter")
        if front_matter is not None:
            pages = front_matter.findall("page")
            assert len(pages) == 1

    def test_empty_chapter(self) -> None:
        """Chapter with no pages in TOC still creates empty chapter element."""
        book_xml = """<?xml version="1.0" encoding="UTF-8"?>
<book>
    <metadata><title>Test</title></metadata>
    <toc begin="1" end="1">
        <entry level="chapter" number="1" title="Empty Chapter" page="10" />
    </toc>
    <page number="1" sourceFile="page_0001.png">
        <content><paragraph>TOC page</paragraph></content>
    </page>
</book>"""
        result = group_pages_by_toc(book_xml)
        root = ET.fromstring(result)

        # Chapter should exist even without pages
        chapter1 = root.find("chapter[@number='1']")
        assert chapter1 is not None
        assert chapter1.get("title") == "Empty Chapter"

    def test_unicode_in_titles(self) -> None:
        """Handle Unicode characters in titles properly."""
        book_xml = """<?xml version="1.0" encoding="UTF-8"?>
<book>
    <metadata><title>Test</title></metadata>
    <toc begin="1" end="1">
        <entry level="chapter" number="1" title="日本語タイトル" page="2" />
    </toc>
    <page number="1" sourceFile="page_0001.png">
        <content><paragraph>TOC</paragraph></content>
    </page>
    <page number="2" sourceFile="page_0002.png">
        <pageMetadata>第1章 日本語タイトル — 1 / 1</pageMetadata>
        <content><heading level="1">第1章 日本語タイトル</heading></content>
    </page>
</book>"""
        result = group_pages_by_toc(book_xml)
        root = ET.fromstring(result)

        chapter1 = root.find("chapter[@number='1']")
        assert chapter1 is not None
        assert chapter1.get("title") == "日本語タイトル"


# =============================================================================
# US3 Tests: Chapter Title Page Identification (Phase 3)
# =============================================================================


class TestIsChapterTitlePage:
    """Tests for is_chapter_title_page function (FR-007)."""

    def test_identify_chapter_title_page_by_metadata(self) -> None:
        """Page with '第N章' in pageMetadata is identified as chapter title page."""
        page_xml = """<page number="14" sourceFile="page_0014.png">
            <pageMetadata type="chapter-page" readAloud="false">第1章 SREとは — 1 / 1</pageMetadata>
            <content readAloud="false">
                <heading level="1" readAloud="false">第1章 SREとは</heading>
            </content>
        </page>"""
        page = ET.fromstring(page_xml)
        result = is_chapter_title_page(page)
        assert result is True

    def test_identify_chapter_title_page_by_heading(self) -> None:
        """Page with '第N章' in heading is identified as chapter title page."""
        page_xml = """<page number="30" sourceFile="page_0030.png">
            <content readAloud="false">
                <heading level="1" readAloud="false">第2章 信頼性を定義する</heading>
                <paragraph>章の内容...</paragraph>
            </content>
        </page>"""
        page = ET.fromstring(page_xml)
        result = is_chapter_title_page(page)
        assert result is True

    def test_section_page_is_not_chapter_title(self) -> None:
        """Page with section number (1.1) is NOT identified as chapter title page."""
        page_xml = """<page number="15" sourceFile="page_0015.png">
            <pageMetadata type="section-page" readAloud="false">1.1 SREの概要 ― 1 / 3</pageMetadata>
            <content readAloud="false">
                <heading level="2" readAloud="false">1.1 SREの概要</heading>
            </content>
        </page>"""
        page = ET.fromstring(page_xml)
        result = is_chapter_title_page(page)
        assert result is False

    def test_subsection_page_is_not_chapter_title(self) -> None:
        """Page with subsection number (1.1.1) is NOT identified as chapter title page."""
        page_xml = """<page number="18" sourceFile="page_0018.png">
            <pageMetadata type="subsection-page" readAloud="false">1.1.1 サイトとは何か ― 1 / 2</pageMetadata>
            <content readAloud="false">
                <heading level="3" readAloud="false">1.1.1 サイトとは何か</heading>
            </content>
        </page>"""
        page = ET.fromstring(page_xml)
        result = is_chapter_title_page(page)
        assert result is False

    def test_front_matter_page_is_not_chapter_title(self) -> None:
        """Front-matter page is NOT identified as chapter title page."""
        page_xml = """<page number="6" sourceFile="page_0006.png">
            <pageMetadata type="chapter-page" readAloud="false"><emphasis>はじめに</emphasis> 1 / 3</pageMetadata>
            <content readAloud="false">
                <paragraph readAloud="false">序文</paragraph>
            </content>
        </page>"""
        page = ET.fromstring(page_xml)
        result = is_chapter_title_page(page)
        assert result is False

    def test_page_without_metadata_not_chapter_title(self) -> None:
        """Page without pageMetadata is NOT identified as chapter title page by default."""
        page_xml = """<page number="1" sourceFile="page_0001.png">
            <content readAloud="false">
                <paragraph readAloud="false">表紙</paragraph>
            </content>
        </page>"""
        page = ET.fromstring(page_xml)
        result = is_chapter_title_page(page)
        assert result is False


class TestChapterTitlePageTypeAttribute:
    """Tests for type='chapter-title' attribute on chapter title pages (FR-007)."""

    def test_chapter_title_page_has_type_attribute(self) -> None:
        """Chapter title page gets type='chapter-title' attribute in output XML."""
        book_xml = """<?xml version="1.0" encoding="UTF-8"?>
<book>
    <metadata><title>Test</title></metadata>
    <toc begin="1" end="1">
        <entry level="chapter" number="1" title="SREとは" page="2" />
        <entry level="section" number="1.1" title="SREの概要" page="3" />
    </toc>
    <page number="1" sourceFile="page_0001.png">
        <content><paragraph>TOC</paragraph></content>
    </page>
    <page number="2" sourceFile="page_0002.png">
        <pageMetadata type="chapter-page" readAloud="false">第1章 SREとは — 1 / 1</pageMetadata>
        <content><heading level="1">第1章 SREとは</heading></content>
    </page>
    <page number="3" sourceFile="page_0003.png">
        <pageMetadata type="section-page" readAloud="false">1.1 SREの概要 ― 1 / 3</pageMetadata>
        <content><heading level="2">1.1 SREの概要</heading></content>
    </page>
</book>"""
        result = group_pages_by_toc(book_xml)
        root = ET.fromstring(result)

        chapter1 = root.find("chapter[@number='1']")
        assert chapter1 is not None

        # Find the chapter title page (page 2)
        chapter_title_page = chapter1.find("page[@number='2']")
        assert chapter_title_page is not None
        assert chapter_title_page.get("type") == "chapter-title"

    def test_chapter_title_page_is_first_in_chapter(self) -> None:
        """The first page in each chapter element (with chapter number) has type='chapter-title'."""
        book_xml = """<?xml version="1.0" encoding="UTF-8"?>
<book>
    <metadata><title>Test</title></metadata>
    <toc begin="1" end="1">
        <entry level="chapter" number="1" title="第一章" page="2" />
        <entry level="chapter" number="2" title="第二章" page="5" />
    </toc>
    <page number="1" sourceFile="page_0001.png">
        <content><paragraph>TOC</paragraph></content>
    </page>
    <page number="2" sourceFile="page_0002.png">
        <pageMetadata>第1章 第一章 — 1 / 1</pageMetadata>
        <content><heading level="1">第1章 第一章</heading></content>
    </page>
    <page number="5" sourceFile="page_0005.png">
        <pageMetadata>第2章 第二章 — 1 / 1</pageMetadata>
        <content><heading level="1">第2章 第二章</heading></content>
    </page>
</book>"""
        result = group_pages_by_toc(book_xml)
        root = ET.fromstring(result)

        # Chapter 1's first page should have type="chapter-title"
        chapter1 = root.find("chapter[@number='1']")
        assert chapter1 is not None
        page2 = chapter1.find("page[@number='2']")
        assert page2 is not None
        assert page2.get("type") == "chapter-title"

        # Chapter 2's first page should have type="chapter-title"
        chapter2 = root.find("chapter[@number='2']")
        assert chapter2 is not None
        page5 = chapter2.find("page[@number='5']")
        assert page5 is not None
        assert page5.get("type") == "chapter-title"

    def test_non_chapter_title_pages_no_type_attribute(self) -> None:
        """Section/subsection pages do NOT have type='chapter-title' attribute."""
        book_xml = """<?xml version="1.0" encoding="UTF-8"?>
<book>
    <metadata><title>Test</title></metadata>
    <toc begin="1" end="1">
        <entry level="chapter" number="1" title="SREとは" page="2" />
        <entry level="section" number="1.1" title="SREの概要" page="3" />
        <entry level="subsection" number="1.1.1" title="サイトとは" page="4" />
    </toc>
    <page number="1" sourceFile="page_0001.png">
        <content><paragraph>TOC</paragraph></content>
    </page>
    <page number="2" sourceFile="page_0002.png">
        <pageMetadata>第1章 SREとは — 1 / 1</pageMetadata>
        <content><heading level="1">第1章 SREとは</heading></content>
    </page>
    <page number="3" sourceFile="page_0003.png">
        <pageMetadata>1.1 SREの概要 ― 1 / 3</pageMetadata>
        <content><heading level="2">1.1 SREの概要</heading></content>
    </page>
    <page number="4" sourceFile="page_0004.png">
        <pageMetadata>1.1.1 サイトとは ― 1 / 2</pageMetadata>
        <content><heading level="3">1.1.1 サイトとは</heading></content>
    </page>
</book>"""
        result = group_pages_by_toc(book_xml)
        root = ET.fromstring(result)

        chapter1 = root.find("chapter[@number='1']")
        assert chapter1 is not None

        # Section page should NOT have type="chapter-title"
        section = chapter1.find("section[@number='1.1']")
        assert section is not None
        page3 = section.find("page[@number='3']")
        assert page3 is not None
        assert page3.get("type") is None

        # Subsection page should NOT have type="chapter-title"
        subsection = section.find("subsection[@number='1.1.1']")
        assert subsection is not None
        page4 = subsection.find("page[@number='4']")
        assert page4 is not None
        assert page4.get("type") is None

    def test_front_matter_pages_no_type_attribute(self) -> None:
        """Front-matter pages do NOT have type='chapter-title' attribute."""
        book_xml = """<?xml version="1.0" encoding="UTF-8"?>
<book>
    <metadata><title>Test</title></metadata>
    <toc begin="1" end="2">
        <entry level="chapter" number="1" title="Test" page="3" />
    </toc>
    <page number="1" sourceFile="page_0001.png">
        <content><paragraph>Cover</paragraph></content>
    </page>
    <page number="2" sourceFile="page_0002.png">
        <pageMetadata>TOC 1 / 1</pageMetadata>
        <content><paragraph>TOC</paragraph></content>
    </page>
    <page number="3" sourceFile="page_0003.png">
        <pageMetadata>第1章 Test — 1 / 1</pageMetadata>
        <content><heading level="1">第1章 Test</heading></content>
    </page>
</book>"""
        result = group_pages_by_toc(book_xml)
        root = ET.fromstring(result)

        front_matter = root.find("front-matter")
        assert front_matter is not None

        # Front-matter pages should NOT have type attribute
        for page in front_matter.findall("page"):
            assert page.get("type") is None


class TestChapterTitlePageEdgeCases:
    """Edge case tests for chapter title page identification."""

    def test_chapter_with_only_title_page(self) -> None:
        """Chapter containing only the title page still gets type='chapter-title'."""
        book_xml = """<?xml version="1.0" encoding="UTF-8"?>
<book>
    <metadata><title>Test</title></metadata>
    <toc begin="1" end="1">
        <entry level="chapter" number="1" title="Empty Chapter" page="2" />
    </toc>
    <page number="1" sourceFile="page_0001.png">
        <content><paragraph>TOC</paragraph></content>
    </page>
    <page number="2" sourceFile="page_0002.png">
        <pageMetadata>第1章 Empty Chapter — 1 / 1</pageMetadata>
        <content><heading level="1">第1章 Empty Chapter</heading></content>
    </page>
</book>"""
        result = group_pages_by_toc(book_xml)
        root = ET.fromstring(result)

        chapter1 = root.find("chapter[@number='1']")
        assert chapter1 is not None
        page2 = chapter1.find("page[@number='2']")
        assert page2 is not None
        assert page2.get("type") == "chapter-title"

    def test_multiple_chapters_all_get_type_attribute(self) -> None:
        """All chapters' title pages get type='chapter-title' attribute."""
        book_xml = """<?xml version="1.0" encoding="UTF-8"?>
<book>
    <metadata><title>Test</title></metadata>
    <toc begin="1" end="1">
        <entry level="chapter" number="1" title="Chapter One" page="2" />
        <entry level="chapter" number="2" title="Chapter Two" page="3" />
        <entry level="chapter" number="3" title="Chapter Three" page="4" />
    </toc>
    <page number="1" sourceFile="page_0001.png">
        <content><paragraph>TOC</paragraph></content>
    </page>
    <page number="2" sourceFile="page_0002.png">
        <pageMetadata>第1章 Chapter One — 1 / 1</pageMetadata>
        <content><heading level="1">第1章 Chapter One</heading></content>
    </page>
    <page number="3" sourceFile="page_0003.png">
        <pageMetadata>第2章 Chapter Two — 1 / 1</pageMetadata>
        <content><heading level="1">第2章 Chapter Two</heading></content>
    </page>
    <page number="4" sourceFile="page_0004.png">
        <pageMetadata>第3章 Chapter Three — 1 / 1</pageMetadata>
        <content><heading level="1">第3章 Chapter Three</heading></content>
    </page>
</book>"""
        result = group_pages_by_toc(book_xml)
        root = ET.fromstring(result)

        # All three chapters should have title pages with type="chapter-title"
        for chapter_num in ["1", "2", "3"]:
            chapter = root.find(f"chapter[@number='{chapter_num}']")
            assert chapter is not None
            # Find direct child page (chapter title page)
            pages = [p for p in chapter.findall("page") if p.get("type") == "chapter-title"]
            assert len(pages) == 1, f"Chapter {chapter_num} should have exactly one chapter-title page"


# =============================================================================
# US4 Tests: Fallback to Previous Section (Phase 4)
# =============================================================================


class TestFallbackToPreviousSection:
    """Tests for fallback to previous section when page lacks section number (FR-008).

    FR-008: システムはセクション番号を抽出できないページを、
    直前のページと同じセクションに配置しなければならない
    """

    def test_fallback_to_previous_section(self) -> None:
        """Page without section number goes to previous page's section.

        Scenario:
        - Page 3: "1.1 SREの概要 ― 1 / 3" -> section 1.1
        - Page 4: "2 / 3" (no section info) -> fallback to section 1.1
        - Page 5: "3 / 3" (no section info) -> fallback to section 1.1
        """
        book_xml = """<?xml version="1.0" encoding="UTF-8"?>
<book>
    <metadata><title>Test</title></metadata>
    <toc begin="1" end="1">
        <entry level="chapter" number="1" title="SREとは" page="2" />
        <entry level="section" number="1.1" title="SREの概要" page="3" />
    </toc>
    <page number="1" sourceFile="page_0001.png">
        <content><paragraph>TOC</paragraph></content>
    </page>
    <page number="2" sourceFile="page_0002.png">
        <pageMetadata>第1章 SREとは — 1 / 1</pageMetadata>
        <content><heading level="1">第1章 SREとは</heading></content>
    </page>
    <page number="3" sourceFile="page_0003.png">
        <pageMetadata type="section-page" readAloud="false">1.1 SREの概要 ― 1 / 3</pageMetadata>
        <content>
            <heading level="2">1.1 SREの概要</heading>
            <paragraph>SREはGoogleで生まれた...</paragraph>
        </content>
    </page>
    <page number="4" sourceFile="page_0004.png">
        <pageMetadata type="section-page" readAloud="false">2 / 3</pageMetadata>
        <content>
            <paragraph>続きのコンテンツ...</paragraph>
        </content>
    </page>
    <page number="5" sourceFile="page_0005.png">
        <pageMetadata type="section-page" readAloud="false">3 / 3</pageMetadata>
        <content>
            <paragraph>セクションの終わり</paragraph>
        </content>
    </page>
</book>"""
        result = group_pages_by_toc(book_xml)
        root = ET.fromstring(result)

        chapter1 = root.find("chapter[@number='1']")
        assert chapter1 is not None

        section1_1 = chapter1.find("section[@number='1.1']")
        assert section1_1 is not None

        # All three pages (3, 4, 5) should be in section 1.1
        pages = section1_1.findall("page")
        page_numbers = [p.get("number") for p in pages]

        assert "3" in page_numbers, "Page 3 (with section info) should be in section 1.1"
        assert "4" in page_numbers, "Page 4 (no section info) should fallback to section 1.1"
        assert "5" in page_numbers, "Page 5 (no section info) should fallback to section 1.1"

    def test_consecutive_missing_sections(self) -> None:
        """Multiple consecutive pages without section numbers all go to the same section.

        Scenario:
        - Page 3: "1.1 Title" -> section 1.1
        - Page 4: "1 / 5" -> fallback to section 1.1
        - Page 5: "2 / 5" -> fallback to section 1.1
        - Page 6: "3 / 5" -> fallback to section 1.1
        - Page 7: "4 / 5" -> fallback to section 1.1
        - Page 8: "5 / 5" -> fallback to section 1.1
        """
        book_xml = """<?xml version="1.0" encoding="UTF-8"?>
<book>
    <metadata><title>Test</title></metadata>
    <toc begin="1" end="1">
        <entry level="chapter" number="1" title="Chapter One" page="2" />
        <entry level="section" number="1.1" title="Section One" page="3" />
    </toc>
    <page number="1" sourceFile="page_0001.png">
        <content><paragraph>TOC</paragraph></content>
    </page>
    <page number="2" sourceFile="page_0002.png">
        <pageMetadata>第1章 Chapter One — 1 / 1</pageMetadata>
        <content><heading level="1">第1章 Chapter One</heading></content>
    </page>
    <page number="3" sourceFile="page_0003.png">
        <pageMetadata>1.1 Section One ― 1 / 6</pageMetadata>
        <content><heading level="2">1.1 Section One</heading></content>
    </page>
    <page number="4" sourceFile="page_0004.png">
        <pageMetadata>2 / 6</pageMetadata>
        <content><paragraph>Content</paragraph></content>
    </page>
    <page number="5" sourceFile="page_0005.png">
        <pageMetadata>3 / 6</pageMetadata>
        <content><paragraph>Content</paragraph></content>
    </page>
    <page number="6" sourceFile="page_0006.png">
        <pageMetadata>4 / 6</pageMetadata>
        <content><paragraph>Content</paragraph></content>
    </page>
    <page number="7" sourceFile="page_0007.png">
        <pageMetadata>5 / 6</pageMetadata>
        <content><paragraph>Content</paragraph></content>
    </page>
    <page number="8" sourceFile="page_0008.png">
        <pageMetadata>6 / 6</pageMetadata>
        <content><paragraph>Content</paragraph></content>
    </page>
</book>"""
        result = group_pages_by_toc(book_xml)
        root = ET.fromstring(result)

        chapter1 = root.find("chapter[@number='1']")
        assert chapter1 is not None

        section1_1 = chapter1.find("section[@number='1.1']")
        assert section1_1 is not None

        # All six pages (3-8) should be in section 1.1
        pages = section1_1.findall("page")
        page_numbers = [p.get("number") for p in pages]

        assert len(page_numbers) == 6, f"Section 1.1 should contain 6 pages, got {len(page_numbers)}"
        for num in ["3", "4", "5", "6", "7", "8"]:
            assert num in page_numbers, f"Page {num} should be in section 1.1"

    def test_first_chapter_page_without_section_stays_in_chapter(self) -> None:
        """If first page after chapter title has no section, it stays at chapter level.

        Scenario:
        - Page 2: "第1章 Title" -> chapter 1 (chapter-title)
        - Page 3: "1 / 2" (no section info, but belongs to chapter 1) -> stays at chapter level
        - Page 4: "1.1 Section" -> section 1.1
        """
        book_xml = """<?xml version="1.0" encoding="UTF-8"?>
<book>
    <metadata><title>Test</title></metadata>
    <toc begin="1" end="1">
        <entry level="chapter" number="1" title="Chapter One" page="2" />
        <entry level="section" number="1.1" title="Section One" page="4" />
    </toc>
    <page number="1" sourceFile="page_0001.png">
        <content><paragraph>TOC</paragraph></content>
    </page>
    <page number="2" sourceFile="page_0002.png">
        <pageMetadata>第1章 Chapter One — 1 / 2</pageMetadata>
        <content><heading level="1">第1章 Chapter One</heading></content>
    </page>
    <page number="3" sourceFile="page_0003.png">
        <pageMetadata>2 / 2</pageMetadata>
        <content><paragraph>Introduction to chapter...</paragraph></content>
    </page>
    <page number="4" sourceFile="page_0004.png">
        <pageMetadata>1.1 Section One ― 1 / 1</pageMetadata>
        <content><heading level="2">1.1 Section One</heading></content>
    </page>
</book>"""
        result = group_pages_by_toc(book_xml)
        root = ET.fromstring(result)

        chapter1 = root.find("chapter[@number='1']")
        assert chapter1 is not None

        # Page 2 should be at chapter level (chapter-title)
        page2 = chapter1.find("page[@number='2']")
        assert page2 is not None, "Page 2 (chapter title) should be at chapter level"
        assert page2.get("type") == "chapter-title", "Page 2 should have type='chapter-title'"

        # Page 3 should also be at chapter level (fallback from chapter 1, before any section)
        page3 = chapter1.find("page[@number='3']")
        assert page3 is not None, "Page 3 (no section, after chapter title) should be at chapter level"

        # Page 4 should be in section 1.1
        section1_1 = chapter1.find("section[@number='1.1']")
        assert section1_1 is not None
        page4 = section1_1.find("page[@number='4']")
        assert page4 is not None, "Page 4 should be in section 1.1"

    def test_fallback_preserves_page_order(self) -> None:
        """Pages maintain correct order after fallback assignment.

        Scenario:
        - Page 3: "1.1 Title" -> section 1.1 (first)
        - Page 4: "2 / 3" -> fallback to section 1.1 (second)
        - Page 5: "3 / 3" -> fallback to section 1.1 (third)

        Pages should appear in order 3, 4, 5 within section 1.1.
        """
        book_xml = """<?xml version="1.0" encoding="UTF-8"?>
<book>
    <metadata><title>Test</title></metadata>
    <toc begin="1" end="1">
        <entry level="chapter" number="1" title="Chapter One" page="2" />
        <entry level="section" number="1.1" title="Section One" page="3" />
    </toc>
    <page number="1" sourceFile="page_0001.png">
        <content><paragraph>TOC</paragraph></content>
    </page>
    <page number="2" sourceFile="page_0002.png">
        <pageMetadata>第1章 Chapter One — 1 / 1</pageMetadata>
        <content><heading level="1">第1章 Chapter One</heading></content>
    </page>
    <page number="3" sourceFile="page_0003.png">
        <pageMetadata>1.1 Section One ― 1 / 3</pageMetadata>
        <content><heading level="2">1.1 Section One</heading></content>
    </page>
    <page number="4" sourceFile="page_0004.png">
        <pageMetadata>2 / 3</pageMetadata>
        <content><paragraph>Middle content</paragraph></content>
    </page>
    <page number="5" sourceFile="page_0005.png">
        <pageMetadata>3 / 3</pageMetadata>
        <content><paragraph>End content</paragraph></content>
    </page>
</book>"""
        result = group_pages_by_toc(book_xml)
        root = ET.fromstring(result)

        chapter1 = root.find("chapter[@number='1']")
        assert chapter1 is not None

        section1_1 = chapter1.find("section[@number='1.1']")
        assert section1_1 is not None

        # Get pages in order
        pages = section1_1.findall("page")
        page_numbers = [p.get("number") for p in pages]

        # Verify order is preserved: 3, 4, 5
        assert page_numbers == ["3", "4", "5"], f"Pages should be in order [3, 4, 5], got {page_numbers}"

    def test_fallback_when_section_not_in_toc(self) -> None:
        """Page with section number NOT in TOC should fallback to previous section.

        Scenario:
        - Page 3: "1.1 Title" -> section 1.1 (in TOC)
        - Page 4: "1.2 Title" -> section 1.2 NOT in TOC -> fallback to 1.1
        - Page 5: "1 / 1" -> no section -> fallback to 1.1
        """
        book_xml = """<?xml version="1.0" encoding="UTF-8"?>
<book>
    <metadata><title>Test</title></metadata>
    <toc begin="1" end="1">
        <entry level="chapter" number="1" title="Chapter One" page="2" />
        <entry level="section" number="1.1" title="Section One" page="3" />
    </toc>
    <page number="1" sourceFile="page_0001.png">
        <content><paragraph>TOC</paragraph></content>
    </page>
    <page number="2" sourceFile="page_0002.png">
        <pageMetadata>第1章 Chapter One — 1 / 1</pageMetadata>
        <content><heading level="1">第1章 Chapter One</heading></content>
    </page>
    <page number="3" sourceFile="page_0003.png">
        <pageMetadata>1.1 Section One ― 1 / 2</pageMetadata>
        <content><heading level="2">1.1 Section One</heading></content>
    </page>
    <page number="4" sourceFile="page_0004.png">
        <pageMetadata>1.2 Unlisted Section ― 1 / 1</pageMetadata>
        <content><heading level="2">1.2 Unlisted Section</heading></content>
    </page>
    <page number="5" sourceFile="page_0005.png">
        <pageMetadata>1 / 1</pageMetadata>
        <content><paragraph>Some content</paragraph></content>
    </page>
</book>"""
        result = group_pages_by_toc(book_xml)
        root = ET.fromstring(result)

        chapter1 = root.find("chapter[@number='1']")
        assert chapter1 is not None

        section1_1 = chapter1.find("section[@number='1.1']")
        assert section1_1 is not None

        # Page 3 should be in section 1.1
        pages = section1_1.findall("page")
        page_numbers = [p.get("number") for p in pages]

        assert "3" in page_numbers, "Page 3 should be in section 1.1"
        # Page 4 has section 1.2 which is NOT in TOC, so should fallback to 1.1
        assert "4" in page_numbers, "Page 4 (section 1.2 not in TOC) should fallback to section 1.1"
        # Page 5 has no section info, should fallback to 1.1
        assert "5" in page_numbers, "Page 5 (no section) should fallback to section 1.1"

    def test_section_transition_with_missing_info(self) -> None:
        """Page without section info between two sections goes to previous section.

        Scenario:
        - Page 3: "1.1 Title" -> section 1.1
        - Page 4: "1 / 2" -> no section -> fallback to 1.1
        - Page 5: "1.2 Title" -> section 1.2
        """
        book_xml = """<?xml version="1.0" encoding="UTF-8"?>
<book>
    <metadata><title>Test</title></metadata>
    <toc begin="1" end="1">
        <entry level="chapter" number="1" title="Chapter One" page="2" />
        <entry level="section" number="1.1" title="Section One" page="3" />
        <entry level="section" number="1.2" title="Section Two" page="5" />
    </toc>
    <page number="1" sourceFile="page_0001.png">
        <content><paragraph>TOC</paragraph></content>
    </page>
    <page number="2" sourceFile="page_0002.png">
        <pageMetadata>第1章 Chapter One — 1 / 1</pageMetadata>
        <content><heading level="1">第1章 Chapter One</heading></content>
    </page>
    <page number="3" sourceFile="page_0003.png">
        <pageMetadata>1.1 Section One ― 1 / 2</pageMetadata>
        <content><heading level="2">1.1 Section One</heading></content>
    </page>
    <page number="4" sourceFile="page_0004.png">
        <pageMetadata>2 / 2</pageMetadata>
        <content><paragraph>Continuation of section 1.1</paragraph></content>
    </page>
    <page number="5" sourceFile="page_0005.png">
        <pageMetadata>1.2 Section Two ― 1 / 1</pageMetadata>
        <content><heading level="2">1.2 Section Two</heading></content>
    </page>
</book>"""
        result = group_pages_by_toc(book_xml)
        root = ET.fromstring(result)

        chapter1 = root.find("chapter[@number='1']")
        assert chapter1 is not None

        section1_1 = chapter1.find("section[@number='1.1']")
        assert section1_1 is not None

        section1_2 = chapter1.find("section[@number='1.2']")
        assert section1_2 is not None

        # Section 1.1 should contain pages 3 and 4
        pages_1_1 = section1_1.findall("page")
        page_numbers_1_1 = [p.get("number") for p in pages_1_1]
        assert "3" in page_numbers_1_1, "Page 3 should be in section 1.1"
        assert "4" in page_numbers_1_1, "Page 4 (no section) should fallback to section 1.1"

        # Section 1.2 should contain only page 5
        pages_1_2 = section1_2.findall("page")
        page_numbers_1_2 = [p.get("number") for p in pages_1_2]
        assert "5" in page_numbers_1_2, "Page 5 should be in section 1.2"
        assert "4" not in page_numbers_1_2, "Page 4 should NOT be in section 1.2"

    def test_first_content_page_without_section_not_dropped(self) -> None:
        """First content page without section info should NOT be dropped.

        Edge case: When the very first content page (after front-matter) has no
        recognizable section number, it should not be silently dropped.

        Scenario:
        - Page 1: TOC (front-matter)
        - Page 2: "1 / 1" (no section info, no chapter indicator) -> should still appear
        - Page 3: "1.1 Section One" -> section 1.1
        """
        book_xml = """<?xml version="1.0" encoding="UTF-8"?>
<book>
    <metadata><title>Test</title></metadata>
    <toc begin="1" end="1">
        <entry level="chapter" number="1" title="Chapter One" page="2" />
        <entry level="section" number="1.1" title="Section One" page="3" />
    </toc>
    <page number="1" sourceFile="page_0001.png">
        <content><paragraph>TOC</paragraph></content>
    </page>
    <page number="2" sourceFile="page_0002.png">
        <pageMetadata>1 / 1</pageMetadata>
        <content><paragraph>No chapter indicator but belongs to chapter 1</paragraph></content>
    </page>
    <page number="3" sourceFile="page_0003.png">
        <pageMetadata>1.1 Section One ― 1 / 1</pageMetadata>
        <content><heading level="2">1.1 Section One</heading></content>
    </page>
</book>"""
        result = group_pages_by_toc(book_xml)
        root = ET.fromstring(result)

        # Page 2 should NOT be dropped - it should appear somewhere in the output
        # Find all pages in the entire document
        all_pages = root.findall(".//page")
        all_page_numbers = [p.get("number") for p in all_pages]

        assert "2" in all_page_numbers, (
            "Page 2 should NOT be dropped from output. "
            f"Found pages: {all_page_numbers}"
        )

        # Page 2 should be in chapter 1 (at chapter level since no section info)
        chapter1 = root.find("chapter[@number='1']")
        assert chapter1 is not None

        # Page 2 should be directly under chapter (not in a section)
        page2 = chapter1.find("page[@number='2']")
        assert page2 is not None, (
            "Page 2 (first content page without section) should be at chapter level"
        )


# =============================================================================
# Phase 3 Tests: US2 - Page Loss Prevention (ページ欠損の防止)
# =============================================================================


class TestValidatePageCountNormal:
    """Tests for validate_page_count function - normal cases (T026).

    FR-005: All input pages must appear in output XML, even if TOC is incomplete.
    """

    def test_validate_all_pages_present(self) -> None:
        """10 input pages, 10 output pages -> no error."""
        from src.book_converter.page_grouper import validate_page_count

        # Should not raise any exception
        validate_page_count(input_count=10, output_count=10)

    def test_validate_with_toc_pages(self) -> None:
        """Total pages (front-matter + chapters) equal to input -> no error."""
        from src.book_converter.page_grouper import validate_page_count

        # Scenario: 5 front-matter + 15 chapter pages = 20 total
        # Input: 20 pages, Output: 20 pages
        validate_page_count(input_count=20, output_count=20)

    def test_validate_exact_match(self) -> None:
        """Input count == output count is valid."""
        from src.book_converter.page_grouper import validate_page_count

        # Test with various counts
        validate_page_count(input_count=1, output_count=1)
        validate_page_count(input_count=100, output_count=100)
        validate_page_count(input_count=181, output_count=181)

    def test_validate_minor_loss_no_error(self) -> None:
        """Minor page loss (less than 50%) should not raise error."""
        from src.book_converter.page_grouper import validate_page_count

        # 10% loss: OK
        validate_page_count(input_count=100, output_count=90)
        # 30% loss: OK
        validate_page_count(input_count=100, output_count=70)
        # 49% loss: OK (boundary)
        validate_page_count(input_count=100, output_count=51)


class TestValidatePageCountError:
    """Tests for validate_page_count function - error cases (T027).

    FR-008: When 50%+ pages are missing, report as error.
    """

    def test_validate_50_percent_loss_raises_error(self) -> None:
        """10 input, 5 output (50% loss) -> PageValidationError."""
        from src.book_converter.errors import PageValidationError
        from src.book_converter.page_grouper import validate_page_count

        with pytest.raises(PageValidationError):
            validate_page_count(input_count=10, output_count=5)

    def test_validate_over_50_percent_loss(self) -> None:
        """10 input, 4 output (60% loss) -> error."""
        from src.book_converter.errors import PageValidationError
        from src.book_converter.page_grouper import validate_page_count

        with pytest.raises(PageValidationError):
            validate_page_count(input_count=10, output_count=4)

    def test_validate_49_percent_loss_no_error(self) -> None:
        """10 input, 6 output (40% loss) -> warning but no error."""
        from src.book_converter.page_grouper import validate_page_count

        # 40% loss is under threshold, should not raise
        validate_page_count(input_count=10, output_count=6)

    def test_error_message_contains_counts(self) -> None:
        """Error message shows expected vs actual counts."""
        from src.book_converter.errors import PageValidationError
        from src.book_converter.page_grouper import validate_page_count

        with pytest.raises(PageValidationError) as exc_info:
            validate_page_count(input_count=100, output_count=40)

        error = exc_info.value
        # Check that error contains the counts
        assert error.input_count == 100
        assert error.output_count == 40
        # Check that message contains counts
        assert "100" in str(error)
        assert "40" in str(error)

    def test_validate_extreme_loss(self) -> None:
        """181 input, 10 output (94.5% loss) -> error (real bug scenario)."""
        from src.book_converter.errors import PageValidationError
        from src.book_converter.page_grouper import validate_page_count

        with pytest.raises(PageValidationError):
            validate_page_count(input_count=181, output_count=10)

    def test_validate_zero_output_raises_error(self) -> None:
        """Zero output pages always raises error."""
        from src.book_converter.errors import PageValidationError
        from src.book_converter.page_grouper import validate_page_count

        with pytest.raises(PageValidationError):
            validate_page_count(input_count=10, output_count=0)


class TestGroupPagesPreservation:
    """Tests for group_pages_by_toc preserving all pages (T028).

    FR-005: All input pages must appear in output XML.
    """

    def test_all_pages_in_output(self) -> None:
        """Parse XML, count pages, compare to input."""
        book_xml = """<?xml version="1.0" encoding="UTF-8"?>
<book>
    <metadata><title>Test</title></metadata>
    <toc begin="1" end="2">
        <entry level="chapter" number="1" title="Chapter One" page="3" />
    </toc>
    <page number="1" sourceFile="page_0001.png">
        <content><paragraph>Cover</paragraph></content>
    </page>
    <page number="2" sourceFile="page_0002.png">
        <content><paragraph>TOC</paragraph></content>
    </page>
    <page number="3" sourceFile="page_0003.png">
        <pageMetadata>Chapter 1 Title</pageMetadata>
        <content><heading level="1">Chapter 1</heading></content>
    </page>
    <page number="4" sourceFile="page_0004.png">
        <content><paragraph>Chapter 1 content</paragraph></content>
    </page>
    <page number="5" sourceFile="page_0005.png">
        <content><paragraph>More content</paragraph></content>
    </page>
</book>"""
        result = group_pages_by_toc(book_xml)
        root = ET.fromstring(result)

        # Count all pages in output
        all_pages = root.findall(".//page")
        assert len(all_pages) == 5, f"Expected 5 pages, found {len(all_pages)}"

    def test_pages_not_duplicated(self) -> None:
        """Each page appears exactly once."""
        book_xml = """<?xml version="1.0" encoding="UTF-8"?>
<book>
    <metadata><title>Test</title></metadata>
    <toc begin="1" end="1">
        <entry level="chapter" number="1" title="Chapter One" page="2" />
        <entry level="section" number="1.1" title="Section 1.1" page="3" />
    </toc>
    <page number="1" sourceFile="page_0001.png">
        <content><paragraph>TOC</paragraph></content>
    </page>
    <page number="2" sourceFile="page_0002.png">
        <pageMetadata>Chapter 1 Title</pageMetadata>
        <content><heading level="1">Chapter 1</heading></content>
    </page>
    <page number="3" sourceFile="page_0003.png">
        <pageMetadata>1.1 Section 1.1 - 1/1</pageMetadata>
        <content><heading level="2">1.1 Section 1.1</heading></content>
    </page>
</book>"""
        result = group_pages_by_toc(book_xml)
        root = ET.fromstring(result)

        # Get all page numbers
        all_pages = root.findall(".//page")
        page_numbers = [p.get("number") for p in all_pages]

        # Check no duplicates
        assert len(page_numbers) == len(set(page_numbers)), (
            f"Duplicate pages found: {page_numbers}"
        )

    def test_page_content_preserved(self) -> None:
        """Page content is not lost during grouping."""
        book_xml = """<?xml version="1.0" encoding="UTF-8"?>
<book>
    <metadata><title>Test</title></metadata>
    <toc begin="1" end="1">
        <entry level="chapter" number="1" title="Chapter" page="2" />
    </toc>
    <page number="1" sourceFile="page_0001.png">
        <content><paragraph>TOC content here</paragraph></content>
    </page>
    <page number="2" sourceFile="page_0002.png">
        <pageMetadata>Chapter Metadata</pageMetadata>
        <content>
            <heading level="1">Chapter Title</heading>
            <paragraph>Important paragraph</paragraph>
        </content>
    </page>
</book>"""
        result = group_pages_by_toc(book_xml)
        root = ET.fromstring(result)

        # Find page 2 and verify content is preserved
        page2 = root.find(".//page[@number='2']")
        assert page2 is not None

        # Check metadata preserved
        metadata = page2.find("pageMetadata")
        assert metadata is not None
        assert "Chapter Metadata" in metadata.text or "Chapter Metadata" in ET.tostring(metadata, encoding='unicode')

        # Check content preserved
        content = page2.find("content")
        assert content is not None
        heading = content.find("heading")
        assert heading is not None

    def test_181_pages_input_181_output(self) -> None:
        """Specific case from problem file: 181 pages input -> 181 pages output."""
        # Generate 181 pages
        pages_xml = []
        for i in range(1, 182):
            pages_xml.append(
                f'<page number="{i}" sourceFile="page_{i:04d}.png">'
                f'<content><paragraph>Page {i}</paragraph></content>'
                f'</page>'
            )

        book_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<book>
    <metadata><title>181 Page Book</title></metadata>
    <toc begin="1" end="5">
        <entry level="chapter" number="1" title="Chapter One" page="6" />
        <entry level="chapter" number="2" title="Chapter Two" page="100" />
    </toc>
    {''.join(pages_xml)}
</book>"""
        result = group_pages_by_toc(book_xml)
        root = ET.fromstring(result)

        # Count all pages in output
        all_pages = root.findall(".//page")
        assert len(all_pages) == 181, (
            f"Expected 181 pages, found {len(all_pages)}. "
            f"Page loss: {181 - len(all_pages)} pages"
        )


class TestGroupPagesEmptyToc:
    """Tests for group_pages_by_toc when TOC is empty (T029).

    FR-005: When TOC is empty, all pages should go to front-matter.
    """

    def test_empty_toc_all_to_front_matter(self) -> None:
        """When no TOC entries, all pages go to front-matter."""
        book_xml = """<?xml version="1.0" encoding="UTF-8"?>
<book>
    <metadata><title>No TOC Entries Book</title></metadata>
    <toc begin="1" end="1">
    </toc>
    <page number="1" sourceFile="page_0001.png">
        <content><paragraph>Page 1</paragraph></content>
    </page>
    <page number="2" sourceFile="page_0002.png">
        <content><paragraph>Page 2</paragraph></content>
    </page>
    <page number="3" sourceFile="page_0003.png">
        <content><paragraph>Page 3</paragraph></content>
    </page>
</book>"""
        result = group_pages_by_toc(book_xml)
        root = ET.fromstring(result)

        # All pages should be in front-matter
        front_matter = root.find("front-matter")
        assert front_matter is not None, "Front-matter should exist"

        pages = front_matter.findall("page")
        assert len(pages) == 3, f"All 3 pages should be in front-matter, found {len(pages)}"

        # Verify no chapters were created
        chapters = root.findall("chapter")
        assert len(chapters) == 0, "No chapters should be created when TOC is empty"

    def test_no_toc_element_all_to_front_matter(self) -> None:
        """When <toc> element is missing, all pages go to front-matter."""
        book_xml = """<?xml version="1.0" encoding="UTF-8"?>
<book>
    <metadata><title>No TOC Element Book</title></metadata>
    <page number="1" sourceFile="page_0001.png">
        <content><paragraph>Page 1</paragraph></content>
    </page>
    <page number="2" sourceFile="page_0002.png">
        <content><paragraph>Page 2</paragraph></content>
    </page>
</book>"""
        result = group_pages_by_toc(book_xml)
        root = ET.fromstring(result)

        # All pages should be somewhere (not dropped)
        all_pages = root.findall(".//page")
        assert len(all_pages) == 2, f"All 2 pages should be preserved, found {len(all_pages)}"

    def test_front_matter_preserves_order(self) -> None:
        """Pages maintain original order in front-matter."""
        book_xml = """<?xml version="1.0" encoding="UTF-8"?>
<book>
    <metadata><title>Test</title></metadata>
    <toc begin="1" end="1">
    </toc>
    <page number="1" sourceFile="page_0001.png">
        <content><paragraph>First</paragraph></content>
    </page>
    <page number="2" sourceFile="page_0002.png">
        <content><paragraph>Second</paragraph></content>
    </page>
    <page number="3" sourceFile="page_0003.png">
        <content><paragraph>Third</paragraph></content>
    </page>
</book>"""
        result = group_pages_by_toc(book_xml)
        root = ET.fromstring(result)

        front_matter = root.find("front-matter")
        assert front_matter is not None

        pages = front_matter.findall("page")
        page_numbers = [p.get("number") for p in pages]

        # Order should be preserved: 1, 2, 3
        assert page_numbers == ["1", "2", "3"], (
            f"Page order not preserved. Expected ['1', '2', '3'], got {page_numbers}"
        )
