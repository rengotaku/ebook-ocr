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
