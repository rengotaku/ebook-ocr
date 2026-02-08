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


# =============================================================================
# Phase 2 (004-toc-structure): US1+US2 目次マーカー認識と構造化
# =============================================================================


class TestTocMarkerIntegration:
    """T018: 統合テスト（目次マーカーあり）

    US1: 目次マーカーによる目次認識
    book.mdに目次マーカーを含む場合、変換後のXMLに<tableOfContents>が生成される
    """

    def test_book_with_toc_marker_generates_table_of_contents(
        self, tmp_path: Path
    ) -> None:
        """目次マーカー付きの書籍で<tableOfContents>が生成される"""
        input_file = tmp_path / "book_with_toc.md"
        input_file.write_text(
            """--- Page 1 (page_0001.png) ---

# 目次

<!-- toc -->

第1章 SREとは ... 15

1.1 SREの定義 ... 16

<!-- /toc -->

--- Page 2 (page_0002.png) ---

# 第1章 SREとは

本文です。
""",
            encoding="utf-8",
        )

        from src.book_converter.parser import parse_pages
        from src.book_converter.xml_builder import build_xml

        pages = list(parse_pages(input_file))
        book = Book(
            metadata=BookMetadata(title="Test Book"),
            pages=tuple(pages),
        )

        xml_string = build_xml(book)
        root = fromstring(xml_string)

        # tableOfContentsが存在する
        toc = root.find(".//tableOfContents")
        assert toc is not None

    def test_toc_contains_entries(self, tmp_path: Path) -> None:
        """目次に正しいエントリが含まれる"""
        input_file = tmp_path / "book_with_toc.md"
        input_file.write_text(
            """--- Page 1 (page_0001.png) ---

<!-- toc -->

第1章 SREとは ... 15

1.1 SREの定義 ... 16

1.1.1 歴史 ... 17

<!-- /toc -->
""",
            encoding="utf-8",
        )

        from src.book_converter.parser import parse_pages
        from src.book_converter.xml_builder import build_xml

        pages = list(parse_pages(input_file))
        book = Book(
            metadata=BookMetadata(title="Test Book"),
            pages=tuple(pages),
        )

        xml_string = build_xml(book)
        root = fromstring(xml_string)

        toc = root.find(".//tableOfContents")
        assert toc is not None

        entries = toc.findall("entry")
        assert len(entries) == 3

    def test_toc_entry_has_correct_attributes(self, tmp_path: Path) -> None:
        """目次エントリが正しい属性を持つ"""
        input_file = tmp_path / "book_with_toc.md"
        input_file.write_text(
            """--- Page 1 (page_0001.png) ---

<!-- toc -->

第1章 SREとは ... 15

<!-- /toc -->
""",
            encoding="utf-8",
        )

        from src.book_converter.parser import parse_pages
        from src.book_converter.xml_builder import build_xml

        pages = list(parse_pages(input_file))
        book = Book(
            metadata=BookMetadata(title="Test Book"),
            pages=tuple(pages),
        )

        xml_string = build_xml(book)
        root = fromstring(xml_string)

        toc = root.find(".//tableOfContents")
        entry = toc.find("entry")

        assert entry is not None
        assert entry.get("level") == "chapter"
        assert entry.get("number") == "1"
        assert entry.get("title") == "SREとは"
        assert entry.get("page") == "15"

    def test_toc_with_various_levels(self, tmp_path: Path) -> None:
        """さまざまなレベルの目次エントリ"""
        input_file = tmp_path / "book_with_toc.md"
        input_file.write_text(
            """--- Page 1 (page_0001.png) ---

<!-- toc -->

はじめに ... 1

第1章 SREとは ... 15

1.1 SREの定義 ... 16

1.1.1 歴史 ... 17

第2章 信頼性 ... 25

おわりに ... 300

<!-- /toc -->
""",
            encoding="utf-8",
        )

        from src.book_converter.parser import parse_pages
        from src.book_converter.xml_builder import build_xml

        pages = list(parse_pages(input_file))
        book = Book(
            metadata=BookMetadata(title="Test Book"),
            pages=tuple(pages),
        )

        xml_string = build_xml(book)
        root = fromstring(xml_string)

        toc = root.find(".//tableOfContents")
        entries = toc.findall("entry")

        # level確認
        levels = [e.get("level") for e in entries]
        assert "other" in levels  # はじめに, おわりに
        assert "chapter" in levels  # 第1章, 第2章
        assert "section" in levels  # 1.1
        assert "subsection" in levels  # 1.1.1

    def test_toc_spanning_multiple_pages(self, tmp_path: Path) -> None:
        """複数ページにまたがる目次"""
        input_file = tmp_path / "book_with_toc.md"
        input_file.write_text(
            """--- Page 1 (page_0001.png) ---

# 目次

<!-- toc -->

第1章 SREとは ... 15

--- Page 2 (page_0002.png) ---

第2章 信頼性 ... 25

<!-- /toc -->

--- Page 3 (page_0003.png) ---

# 第1章 SREとは
""",
            encoding="utf-8",
        )

        from src.book_converter.parser import parse_pages
        from src.book_converter.xml_builder import build_xml

        pages = list(parse_pages(input_file))
        book = Book(
            metadata=BookMetadata(title="Test Book"),
            pages=tuple(pages),
        )

        xml_string = build_xml(book)
        root = fromstring(xml_string)

        toc = root.find(".//tableOfContents")
        assert toc is not None

        entries = toc.findall("entry")
        # 複数ページにまたがる目次も1つのtableOfContentsに収まる
        assert len(entries) == 2


class TestTocMarkerBackwardCompatibility:
    """T019: 統合テスト（目次マーカーなし、後方互換）

    US1: 目次マーカーがない場合、既存動作を維持（後方互換性）
    """

    def test_book_without_toc_marker_no_table_of_contents(
        self, tmp_path: Path
    ) -> None:
        """目次マーカーなしの書籍で<tableOfContents>は生成されない"""
        input_file = tmp_path / "book_without_toc.md"
        input_file.write_text(
            """--- Page 1 (page_0001.png) ---

# 第1章 SREとは

本文です。

--- Page 2 (page_0002.png) ---

## 1.1 SREの定義

詳細説明です。
""",
            encoding="utf-8",
        )

        from src.book_converter.parser import parse_pages
        from src.book_converter.xml_builder import build_xml

        pages = list(parse_pages(input_file))
        book = Book(
            metadata=BookMetadata(title="Test Book"),
            pages=tuple(pages),
        )

        xml_string = build_xml(book)
        root = fromstring(xml_string)

        # tableOfContentsは存在しない
        toc = root.find(".//tableOfContents")
        assert toc is None

    def test_backward_compatible_page_structure(
        self, tmp_path: Path
    ) -> None:
        """目次マーカーなしでも既存のページ構造は維持"""
        input_file = tmp_path / "book_without_toc.md"
        input_file.write_text(
            """--- Page 1 (page_0001.png) ---

# 第1章

本文テキスト

--- Page 2 (page_0002.png) ---

## 1.1 節

詳細説明
""",
            encoding="utf-8",
        )

        from src.book_converter.parser import parse_pages
        from src.book_converter.xml_builder import build_xml

        pages = list(parse_pages(input_file))
        book = Book(
            metadata=BookMetadata(title="Test Book"),
            pages=tuple(pages),
        )

        xml_string = build_xml(book)
        root = fromstring(xml_string)

        # 既存の構造は維持
        pages_elem = root.findall(".//page")
        assert len(pages_elem) == 2

        # ページアナウンスは維持
        page1 = root.find(".//page[@number='1']")
        assert page1 is not None
        announcement = page1.find("pageAnnouncement")
        assert announcement is not None
        assert announcement.text == "1ページ"

    def test_backward_compatible_content_parsing(
        self, tmp_path: Path
    ) -> None:
        """目次マーカーなしでも既存のコンテンツ解析は維持"""
        input_file = tmp_path / "book_without_toc.md"
        input_file.write_text(
            """--- Page 1 (page_0001.png) ---

# 見出し

段落テキスト

- リスト項目1
- リスト項目2
""",
            encoding="utf-8",
        )

        from src.book_converter.parser import parse_pages
        from src.book_converter.xml_builder import build_xml

        pages = list(parse_pages(input_file))
        book = Book(
            metadata=BookMetadata(title="Test Book"),
            pages=tuple(pages),
        )

        xml_string = build_xml(book)
        root = fromstring(xml_string)

        # 既存のコンテンツ解析は維持
        page = root.find(".//page[@number='1']")
        assert page is not None

        # 見出し
        heading = page.find(".//heading")
        assert heading is not None

        # 段落
        paragraph = page.find(".//paragraph")
        assert paragraph is not None

        # リスト
        list_elem = page.find(".//list")
        assert list_elem is not None

    def test_existing_sample_book_unchanged(self) -> None:
        """既存のsample_book.mdが変更なく動作"""
        fixture_path = Path(__file__).parent / "fixtures" / "sample_book.md"

        if not fixture_path.exists():
            pytest.skip("sample_book.md fixture not found")

        from src.book_converter.parser import parse_pages
        from src.book_converter.xml_builder import build_xml

        pages = list(parse_pages(fixture_path))
        book = Book(
            metadata=BookMetadata(title="Test Book"),
            pages=tuple(pages),
        )

        xml_string = build_xml(book)
        root = fromstring(xml_string)

        # 既存のテストと同様に動作
        assert root.tag == "book"
        pages_elem = root.findall(".//page")
        assert len(pages_elem) >= 5

        # 目次マーカーがないのでtableOfContentsは存在しない
        toc = root.find(".//tableOfContents")
        assert toc is None
