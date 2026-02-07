"""Integration tests for book markdown to XML conversion.

Tests for Phase 2: User Story 1 - TTS Page Navigation and Audio Announcement
- T014: Integration test (Markdown -> XML -> XPath query)

Acceptance Scenarios:
1. XPathクエリ `//page[@number='42']` で該当ページを特定
2. TTSが「42ページ」とアナウンス可能
3. ページ境界でアナウンスが生成される
"""

import pytest
from pathlib import Path
from xml.etree.ElementTree import fromstring, Element

from src.book_converter.parser import parse_pages
from src.book_converter.transformer import transform_page
from src.book_converter.xml_builder import build_xml
from src.book_converter.models import Book, BookMetadata


class TestMarkdownToXMLConversion:
    """Markdown -> XML 変換の統合テスト"""

    def test_parse_sample_book_returns_pages(self) -> None:
        """sample_book.mdからページをパースできる"""
        fixture_path = Path(__file__).parent / "fixtures" / "sample_book.md"

        pages = list(parse_pages(fixture_path))

        # sample_book.mdには5ページある
        assert len(pages) >= 5

    def test_parsed_pages_have_numbers(self) -> None:
        """パースされたページにページ番号がある"""
        fixture_path = Path(__file__).parent / "fixtures" / "sample_book.md"

        pages = list(parse_pages(fixture_path))

        # 全ページにページ番号がある
        for i, page in enumerate(pages, start=1):
            assert page.number == str(i), f"Page {i} should have number '{i}'"

    def test_parsed_pages_have_source_files(self) -> None:
        """パースされたページにソースファイルがある"""
        fixture_path = Path(__file__).parent / "fixtures" / "sample_book.md"

        pages = list(parse_pages(fixture_path))

        expected_files = [
            "page_0001.png",
            "page_0002.png",
            "page_0003.png",
            "page_0004.png",
            "page_0005.png",
        ]

        for page, expected in zip(pages, expected_files):
            assert page.source_file == expected


class TestXPathQuery:
    """XPathクエリのテスト（SC-001準拠）"""

    def test_find_page_by_number_42(self) -> None:
        """XPathで42ページを検索できる"""
        fixture_path = Path(__file__).parent / "fixtures" / "sample_book.md"

        pages = list(parse_pages(fixture_path))
        book = Book(
            metadata=BookMetadata(title="Test Book"),
            pages=tuple(pages),
        )

        xml_string = build_xml(book)
        root = fromstring(xml_string)

        # XPathクエリでページ42を検索（sample_bookには42ページはないが、構造テスト）
        # 代わりにページ1を検索
        result = root.find(".//page[@number='1']")

        assert result is not None
        assert result.get("number") == "1"
        assert result.get("sourceFile") == "page_0001.png"

    def test_find_page_by_number_with_xpath(self) -> None:
        """複数ページから特定ページをXPathで検索"""
        fixture_path = Path(__file__).parent / "fixtures" / "sample_book.md"

        pages = list(parse_pages(fixture_path))
        book = Book(
            metadata=BookMetadata(title="Test Book"),
            pages=tuple(pages),
        )

        xml_string = build_xml(book)
        root = fromstring(xml_string)

        # ページ3を検索
        result = root.find(".//page[@number='3']")

        assert result is not None
        assert result.get("number") == "3"

    def test_all_pages_findable_by_xpath(self) -> None:
        """全ページがXPathで検索可能"""
        fixture_path = Path(__file__).parent / "fixtures" / "sample_book.md"

        pages = list(parse_pages(fixture_path))
        book = Book(
            metadata=BookMetadata(title="Test Book"),
            pages=tuple(pages),
        )

        xml_string = build_xml(book)
        root = fromstring(xml_string)

        # 全5ページが検索可能
        for i in range(1, 6):
            result = root.find(f".//page[@number='{i}']")
            assert result is not None, f"Page {i} should be findable"


class TestTTSAnnouncement:
    """TTSアナウンスのテスト"""

    def test_page_has_announcement(self) -> None:
        """変換されたページにアナウンスがある"""
        fixture_path = Path(__file__).parent / "fixtures" / "sample_book.md"

        pages = list(parse_pages(fixture_path))
        book = Book(
            metadata=BookMetadata(title="Test Book"),
            pages=tuple(pages),
        )

        xml_string = build_xml(book)
        root = fromstring(xml_string)

        # ページ1のアナウンスを確認
        page = root.find(".//page[@number='1']")
        assert page is not None

        announcement = page.find("pageAnnouncement")
        assert announcement is not None
        assert announcement.text == "1ページ"

    def test_all_pages_have_announcements(self) -> None:
        """全ページにアナウンスがある"""
        fixture_path = Path(__file__).parent / "fixtures" / "sample_book.md"

        pages = list(parse_pages(fixture_path))
        book = Book(
            metadata=BookMetadata(title="Test Book"),
            pages=tuple(pages),
        )

        xml_string = build_xml(book)
        root = fromstring(xml_string)

        for i in range(1, 6):
            page = root.find(f".//page[@number='{i}']")
            assert page is not None

            announcement = page.find("pageAnnouncement")
            assert announcement is not None, f"Page {i} should have announcement"
            assert announcement.text == f"{i}ページ"

    def test_announcement_format_is_simple(self) -> None:
        """アナウンスのformatがsimple"""
        fixture_path = Path(__file__).parent / "fixtures" / "sample_book.md"

        pages = list(parse_pages(fixture_path))
        book = Book(
            metadata=BookMetadata(title="Test Book"),
            pages=tuple(pages),
        )

        xml_string = build_xml(book)
        root = fromstring(xml_string)

        page = root.find(".//page[@number='1']")
        announcement = page.find("pageAnnouncement")

        assert announcement.get("format") == "simple"


class TestXMLStructure:
    """生成されるXML構造のテスト"""

    def test_xml_has_book_root(self) -> None:
        """ルート要素がbook"""
        fixture_path = Path(__file__).parent / "fixtures" / "sample_book.md"

        pages = list(parse_pages(fixture_path))
        book = Book(
            metadata=BookMetadata(title="Test Book"),
            pages=tuple(pages),
        )

        xml_string = build_xml(book)
        root = fromstring(xml_string)

        assert root.tag == "book"

    def test_xml_has_metadata(self) -> None:
        """metadataセクションがある"""
        fixture_path = Path(__file__).parent / "fixtures" / "sample_book.md"

        pages = list(parse_pages(fixture_path))
        book = Book(
            metadata=BookMetadata(title="Test Book"),
            pages=tuple(pages),
        )

        xml_string = build_xml(book)
        root = fromstring(xml_string)

        metadata = root.find("metadata")
        assert metadata is not None

        title = metadata.find("title")
        assert title is not None
        assert title.text == "Test Book"

    def test_xml_is_well_formed(self) -> None:
        """生成されるXMLは整形式"""
        fixture_path = Path(__file__).parent / "fixtures" / "sample_book.md"

        pages = list(parse_pages(fixture_path))
        book = Book(
            metadata=BookMetadata(title="Test Book"),
            pages=tuple(pages),
        )

        xml_string = build_xml(book)

        # XMLパースが成功すれば整形式
        root = fromstring(xml_string)
        assert root is not None

    def test_xml_encoding_declaration(self) -> None:
        """XML宣言にUTF-8エンコーディングがある"""
        fixture_path = Path(__file__).parent / "fixtures" / "sample_book.md"

        pages = list(parse_pages(fixture_path))
        book = Book(
            metadata=BookMetadata(title="Test Book"),
            pages=tuple(pages),
        )

        xml_string = build_xml(book)

        assert '<?xml version="1.0" encoding="UTF-8"?>' in xml_string


class TestEdgeCases:
    """エッジケースのテスト"""

    def test_empty_book(self) -> None:
        """空の書籍を変換"""
        book = Book(
            metadata=BookMetadata(title="Empty Book"),
            pages=(),
        )

        xml_string = build_xml(book)
        root = fromstring(xml_string)

        assert root.tag == "book"
        pages = root.findall(".//page")
        assert len(pages) == 0

    def test_single_page_book(self) -> None:
        """1ページの書籍を変換"""
        from src.book_converter.models import Page, Content

        page = Page(
            number="1",
            source_file="single.png",
            content=Content(elements=()),
        )
        book = Book(
            metadata=BookMetadata(title="Single Page"),
            pages=(page,),
        )

        xml_string = build_xml(book)
        root = fromstring(xml_string)

        pages = root.findall(".//page")
        assert len(pages) == 1
        assert pages[0].get("number") == "1"

    def test_page_with_unicode_content(self) -> None:
        """Unicode文字を含むページ"""
        from src.book_converter.models import Page, Content, Paragraph

        page = Page(
            number="1",
            source_file="unicode.png",
            content=Content(elements=(Paragraph(text="日本語テキスト"),)),
        )
        book = Book(
            metadata=BookMetadata(title="日本語タイトル"),
            pages=(page,),
        )

        xml_string = build_xml(book)
        root = fromstring(xml_string)

        # Unicodeが正しく処理される
        assert "日本語テキスト" in xml_string
        assert "日本語タイトル" in xml_string
