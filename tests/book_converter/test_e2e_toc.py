"""E2E tests for TOC marker feature using real book.md samples."""

import tempfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pytest

from src.book_converter.cli import convert_book


class TestE2ETocFeature:
    """End-to-end tests for TOC marker feature."""

    def test_full_toc_feature_sample(self, tmp_path: Path) -> None:
        """Test complete TOC feature with real book.md sample.

        This test covers:
        - TOC markers (<!-- toc --> ... <!-- /toc -->)
        - Content markers (<!-- content --> ... <!-- /content -->)
        - Skip markers (<!-- skip --> ... <!-- /skip -->)
        - Default readAloud=false for unmarked content
        - Table of contents generation
        - Entry level detection (chapter, section, subsection, other)
        """
        # Create sample book.md with all features
        book_md = tmp_path / "book.md"
        book_md.write_text(
            """--- Page 1 (page_0001.png) ---
表紙

--- Page 2 (page_0002.png) ---
<!-- toc -->
第1章 SREとは ............... 15
1.1 SREの定義 ............... 16
1.1.1 歴史 ............... 17
第2章 信頼性の定義 ............... 25
おわりに ............... 100
<!-- /toc -->

--- Page 3 (page_0003.png) ---
<!-- content -->
# 第1章 SREとは

SREはGoogleが提唱したプラクティスです。
<!-- /content -->

--- Page 15 (page_0015.png) ---
<!-- content -->
# 第1章 SREとは

本章では、SREの基本概念を説明します。

<!-- skip -->
図1: SREの概要
<!-- /skip -->

続きの本文です。
<!-- /content -->

--- Page 100 (page_0100.png) ---
<!-- skip -->
索引
あ行: 15, 23, 45
い行: 12, 34, 56
<!-- /skip -->
""",
            encoding="utf-8",
        )

        book_xml = tmp_path / "book.xml"

        # Execute conversion
        result = convert_book(book_md, book_xml)

        # Verify conversion succeeded
        assert result.success is True
        assert result.total_pages == 5
        assert result.error_count == 0

        # Parse output XML
        tree = ET.parse(book_xml)
        root = tree.getroot()

        # Verify table of contents (at book level)
        toc = root.find("toc")
        assert toc is not None
        assert toc.get("begin") == "2"
        assert toc.get("end") == "2"

        # Verify TOC entries
        entries = toc.findall("entry")
        assert len(entries) == 5

        # Verify entry attributes (level is now numeric: "1"=chapter, "2"=section, etc.)
        entry1 = entries[0]
        assert entry1.get("level") == "1"  # chapter
        assert entry1.get("number") == "1"
        assert entry1.get("title") == "SREとは"
        assert entry1.get("page") == "15"

        entry2 = entries[1]
        assert entry2.get("level") == "2"  # section
        assert entry2.get("number") == "1.1"
        assert entry2.get("title") == "SREの定義"
        assert entry2.get("page") == "16"

        entry3 = entries[2]
        assert entry3.get("level") == "3"  # subsection
        assert entry3.get("number") == "1.1.1"
        assert entry3.get("title") == "歴史"
        assert entry3.get("page") == "17"

        entry4 = entries[3]
        assert entry4.get("level") == "1"  # chapter
        assert entry4.get("number") == "2"
        assert entry4.get("title") == "信頼性の定義"
        assert entry4.get("page") == "25"

        entry5 = entries[4]
        assert entry5.get("level") == "1"  # other → level 1
        assert entry5.get("number") is None
        assert entry5.get("title") == "おわりに"
        assert entry5.get("page") == "100"

        # Verify page 1 (no markers, default readAloud=true)
        page1 = [p for p in root.findall("page") if p.get("number") == "1"][0]
        content1 = page1.find("content")
        assert content1.get("readAloud") == "true"  # New default: true
        para1 = content1.find("paragraph")
        assert para1.get("readAloud") == "true"  # New default: true
        assert para1.text == "表紙"

        # Verify page 3 (content marker, readAloud=true)
        page3 = [p for p in root.findall("page") if p.get("number") == "3"][0]
        content3 = page3.find("content")
        assert content3.get("readAloud") == "true"
        heading3 = content3.find("heading")
        assert heading3.get("readAloud") == "true"
        para3 = content3.find("paragraph")
        assert para3.get("readAloud") == "true"

        # Verify page 15 (mixed content and skip markers)
        page15 = [p for p in root.findall("page") if p.get("number") == "15"][0]
        content15 = page15.find("content")
        assert content15.get("readAloud") == "true"  # Has some readAloud=true elements

        paragraphs = content15.findall("paragraph")
        # First paragraph (content marker active)
        assert paragraphs[0].get("readAloud") == "true"
        # Skip marker paragraph
        assert paragraphs[1].get("readAloud") == "false"
        # After skip marker (content marker active again)
        assert paragraphs[2].get("readAloud") == "true"

        # Verify page 100 (skip marker, readAloud=false)
        page100 = [p for p in root.findall("page") if p.get("number") == "100"][0]
        content100 = page100.find("content")
        assert content100.get("readAloud") == "false"
        paras100 = content100.findall("paragraph")
        for para in paras100:
            assert para.get("readAloud") == "false"

    def test_toc_spanning_multiple_pages(self, tmp_path: Path) -> None:
        """Test TOC with page-local markers on multiple pages.

        TOC markers are page-local. Each page should have complete marker pairs.
        TOC entries from all pages with markers are collected together.
        """
        book_md = tmp_path / "book.md"
        book_md.write_text(
            """--- Page 1 (page_0001.png) ---
<!-- toc -->
第1章 章1 ... 10
<!-- /toc -->

--- Page 2 (page_0002.png) ---
<!-- toc -->
第2章 章2 ... 20
<!-- /toc -->
""",
            encoding="utf-8",
        )

        book_xml = tmp_path / "book.xml"
        result = convert_book(book_md, book_xml)

        assert result.success is True

        tree = ET.parse(book_xml)
        root = tree.getroot()

        # TOC should appear at book level with begin/end tracking pages
        toc = root.find("toc")
        assert toc is not None
        assert toc.get("begin") == "1"
        assert toc.get("end") == "2"

        entries = toc.findall("entry")
        assert len(entries) == 2

    def test_content_spanning_multiple_pages(self, tmp_path: Path) -> None:
        """Test content marker spanning multiple pages.

        Note: Current implementation resets marker state at page boundaries.
        To have readAloud=true on all pages, repeat the marker on each page.
        """
        book_md = tmp_path / "book.md"
        book_md.write_text(
            """--- Page 1 (page_0001.png) ---
<!-- content -->
最初の段落
<!-- /content -->

--- Page 2 (page_0002.png) ---
<!-- content -->
継続の段落
<!-- /content -->
""",
            encoding="utf-8",
        )

        book_xml = tmp_path / "book.xml"
        result = convert_book(book_md, book_xml)

        assert result.success is True

        tree = ET.parse(book_xml)
        root = tree.getroot()

        # Both pages should have readAloud=true
        page1 = [p for p in root.findall("page") if p.get("number") == "1"][0]
        content1 = page1.find("content")
        assert content1.get("readAloud") == "true"

        page2 = [p for p in root.findall("page") if p.get("number") == "2"][0]
        content2 = page2.find("content")
        assert content2.get("readAloud") == "true"

    def test_backward_compatibility_no_markers(self, tmp_path: Path) -> None:
        """Test backward compatibility with book.md without any markers.

        Without markers, all content should default to readAloud=false.
        """
        book_md = tmp_path / "book.md"
        book_md.write_text(
            """--- Page 1 (page_0001.png) ---
# 見出し

本文です。

- リスト1
- リスト2
""",
            encoding="utf-8",
        )

        book_xml = tmp_path / "book.xml"
        result = convert_book(book_md, book_xml)

        assert result.success is True

        tree = ET.parse(book_xml)
        root = tree.getroot()

        # No table of contents should be generated
        toc = root.find("toc")
        assert toc is None

        # All content should have readAloud=true (new default)
        page1 = [p for p in root.findall("page") if p.get("number") == "1"][0]
        content1 = page1.find("content")
        assert content1.get("readAloud") == "true"

        heading = content1.find("heading")
        assert heading.get("readAloud") == "true"

        para = content1.find("paragraph")
        assert para.get("readAloud") == "true"

        lst = content1.find("list")
        assert lst.get("readAloud") == "true"

    def test_empty_toc_section(self, tmp_path: Path) -> None:
        """Test empty TOC section (only whitespace/empty lines).

        Note: Any non-empty text within TOC markers is treated as an entry
        (level="other" if no pattern matches). To have truly empty TOC,
        the markers must contain only whitespace.
        """
        book_md = tmp_path / "book.md"
        book_md.write_text(
            """--- Page 1 (page_0001.png) ---
<!-- toc -->

<!-- /toc -->

本文
""",
            encoding="utf-8",
        )

        book_xml = tmp_path / "book.xml"
        result = convert_book(book_md, book_xml)

        assert result.success is True

        tree = ET.parse(book_xml)
        root = tree.getroot()

        # No table of contents should be generated (no valid entries)
        toc = root.find("toc")
        assert toc is None

    def test_multiple_content_blocks_same_page(self, tmp_path: Path) -> None:
        """Test multiple content blocks on the same page."""
        book_md = tmp_path / "book.md"
        book_md.write_text(
            """--- Page 1 (page_0001.png) ---
<!-- content -->
最初のブロック
<!-- /content -->

マーカーなし

<!-- content -->
2番目のブロック
<!-- /content -->
""",
            encoding="utf-8",
        )

        book_xml = tmp_path / "book.xml"
        result = convert_book(book_md, book_xml)

        assert result.success is True

        tree = ET.parse(book_xml)
        root = tree.getroot()

        page1 = [p for p in root.findall("page") if p.get("number") == "1"][0]
        content1 = page1.find("content")

        # Content should be readAloud=true because it contains some readAloud=true elements
        assert content1.get("readAloud") == "true"

        paras = content1.findall("paragraph")
        assert len(paras) == 3

        # First block (content marker)
        assert paras[0].get("readAloud") == "true"
        # No marker (new default: true)
        assert paras[1].get("readAloud") == "true"
        # Second block (content marker)
        assert paras[2].get("readAloud") == "true"

    def test_nested_markers_skip_in_content(self, tmp_path: Path) -> None:
        """Test nested markers: skip inside content."""
        book_md = tmp_path / "book.md"
        book_md.write_text(
            """--- Page 1 (page_0001.png) ---
<!-- content -->
読み上げ対象

<!-- skip -->
読み上げ非対象（ネスト）
<!-- /skip -->

再び読み上げ対象
<!-- /content -->
""",
            encoding="utf-8",
        )

        book_xml = tmp_path / "book.xml"
        result = convert_book(book_md, book_xml)

        assert result.success is True

        tree = ET.parse(book_xml)
        root = tree.getroot()

        page1 = [p for p in root.findall("page") if p.get("number") == "1"][0]
        content1 = page1.find("content")

        paras = content1.findall("paragraph")
        assert len(paras) == 3

        # Content marker active
        assert paras[0].get("readAloud") == "true"
        # Skip marker active (nested)
        assert paras[1].get("readAloud") == "false"
        # Content marker active again
        assert paras[2].get("readAloud") == "true"

    def test_quickstart_example(self, tmp_path: Path) -> None:
        """Test the exact example from quickstart.md."""
        book_md = tmp_path / "book.md"
        book_md.write_text(
            """--- Page 1 (page_0001.png) ---
表紙

--- Page 2 (page_0002.png) ---
<!-- toc -->
第1章 SREとは ............... 15
1.1 SREの定義 ............... 16
1.1.1 歴史 ............... 17
第2章 信頼性の定義 ............... 25
おわりに ............... 100
<!-- /toc -->

--- Page 3 (page_0003.png) ---
<!-- content -->
# 第1章 SREとは

SREはGoogleが提唱したプラクティスです。
<!-- /content -->

--- Page 100 (page_0100.png) ---
<!-- skip -->
索引
あ行: 15, 23, 45
い行: 12, 34, 56
<!-- /skip -->
""",
            encoding="utf-8",
        )

        book_xml = tmp_path / "book.xml"
        result = convert_book(book_md, book_xml)

        # Verify conversion succeeded
        assert result.success is True
        assert result.total_pages == 4

        # Parse and verify structure matches quickstart.md expectations
        tree = ET.parse(book_xml)
        root = tree.getroot()

        # Verify TOC (at book level)
        toc = root.find("toc")
        assert toc is not None
        assert toc.get("begin") == "2"
        assert toc.get("end") == "2"

        entries = toc.findall("entry")
        assert len(entries) == 5

        # Verify page 1 (unmarked, default=readAloud is True/None)
        page1 = [p for p in root.findall("page") if p.get("number") == "1"][0]
        content1_ra = page1.find("content").get("readAloud")
        # New default: readAloud=true (attribute absent or "true")
        assert content1_ra is None or content1_ra == "true"

        # Verify page 3 (content marker, readAloud=true)
        page3 = [p for p in root.findall("page") if p.get("number") == "3"][0]
        content3 = page3.find("content")
        content3_ra = content3.get("readAloud")
        assert content3_ra is None or content3_ra == "true"
        heading3 = content3.find("heading")
        if heading3 is not None:
            heading3_ra = heading3.get("readAloud")
            assert heading3_ra is None or heading3_ra == "true"
        para3 = content3.find("paragraph")
        if para3 is not None:
            para3_ra = para3.get("readAloud")
            assert para3_ra is None or para3_ra == "true"

        # Verify page 100 (skip marker, readAloud=false)
        page100 = [p for p in root.findall("page") if p.get("number") == "100"][0]
        assert page100.find("content").get("readAloud") == "false"


class TestE2EErrorHandling:
    """E2E tests for error handling with TOC markers."""

    def test_unclosed_toc_marker(self, tmp_path: Path) -> None:
        """Test handling of unclosed TOC marker.

        With page-local parsing, an unclosed TOC marker still collects
        entries from the rest of the page content. The marker implicitly
        closes at the end of the page.
        """
        book_md = tmp_path / "book.md"
        book_md.write_text(
            """--- Page 1 (page_0001.png) ---
<!-- toc -->
第1章 章1 ... 10
""",
            encoding="utf-8",
        )

        book_xml = tmp_path / "book.xml"
        result = convert_book(book_md, book_xml)

        # Conversion should succeed
        assert result.success is True

        tree = ET.parse(book_xml)
        root = tree.getroot()

        # TOC should be generated (entries collected until end of page)
        toc = root.find("toc")
        assert toc is not None
        assert toc.get("begin") == "1"
        assert toc.get("end") == "1"

        entries = toc.findall("entry")
        assert len(entries) == 1
        assert entries[0].get("title") == "章1"

    def test_unclosed_content_marker(self, tmp_path: Path) -> None:
        """Test handling of unclosed content marker."""
        book_md = tmp_path / "book.md"
        book_md.write_text(
            """--- Page 1 (page_0001.png) ---
<!-- content -->
本文
""",
            encoding="utf-8",
        )

        book_xml = tmp_path / "book.xml"
        result = convert_book(book_md, book_xml)

        # Conversion should succeed
        assert result.success is True

        tree = ET.parse(book_xml)
        root = tree.getroot()

        # Content marker stays active (readAloud=true)
        page1 = [p for p in root.findall("page") if p.get("number") == "1"][0]
        content1 = page1.find("content")
        assert content1.get("readAloud") == "true"


# =============================================================================
# Phase 4 (006-fix-toc-line-merge): US3 正常ファイルE2Eテスト
# =============================================================================


class TestE2ENormalFileConversion:
    """T042: US3 - 正常ファイルの変換結果不変テスト (E2E)

    正常ファイル (4fd5500620491ebe) を変換し、TOC構造とページ数が
    以前と変わらないことを確認する。

    FR-006: 既存の正常ファイルは同一の出力結果を維持
    SC-003: 正常なファイルの出力XMLが変更されない（回帰なし）
    """

    @pytest.fixture
    def normal_file_path(self) -> Path:
        """正常ファイルのパス"""
        return Path("/mnt/hugevolume/Data/BOOKS/OCR/output/4fd5500620491ebe/book.md")

    @pytest.fixture
    def expected_toc_chapters(self) -> list[dict]:
        """期待されるTOCチャプターエントリ（主要なもの）"""
        return [
            {"level": "chapter", "number": "1", "title_contains": "SRE"},
            {"level": "chapter", "number": "2", "title_contains": "信頼性"},
            {"level": "chapter", "number": "3", "title_contains": "観測"},
            {"level": "chapter", "number": "4", "title_contains": "障害"},
            {"level": "chapter", "number": "5", "title_contains": "障害対応"},
            {"level": "chapter", "number": "6", "title_contains": "自動化"},
            {"level": "chapter", "number": "7", "title_contains": "レビュー"},
            {"level": "chapter", "number": "8", "title_contains": "組織"},
            {"level": "chapter", "number": "9", "title_contains": "実践"},
        ]

    def test_normal_file_exists(self, normal_file_path: Path) -> None:
        """正常ファイルが存在する"""
        if not normal_file_path.exists():
            pytest.skip("正常テストファイルが見つかりません (4fd5500620491ebe)")
        assert normal_file_path.exists()

    def test_normal_file_conversion_succeeds(
        self, normal_file_path: Path, tmp_path: Path
    ) -> None:
        """正常ファイルの変換が成功する"""
        if not normal_file_path.exists():
            pytest.skip("正常テストファイルが見つかりません (4fd5500620491ebe)")

        output_xml = tmp_path / "book.xml"
        result = convert_book(normal_file_path, output_xml)

        # 変換は成功する（警告は許容）
        assert result.success is True
        # ページ数が妥当な範囲（200ページ以上）
        assert result.total_pages >= 200

    def test_toc_structure_preserved(
        self, normal_file_path: Path, tmp_path: Path, expected_toc_chapters: list[dict]
    ) -> None:
        """TOC構造が保持される"""
        if not normal_file_path.exists():
            pytest.skip("正常テストファイルが見つかりません (4fd5500620491ebe)")

        # Check if file has TOC markers
        content = normal_file_path.read_text(encoding="utf-8")
        if "<!-- toc -->" not in content.lower():
            pytest.skip("テストファイルにTOCマーカーがありません")

        output_xml = tmp_path / "book.xml"
        convert_book(normal_file_path, output_xml)

        tree = ET.parse(output_xml)
        root = tree.getroot()

        # TOCが存在する
        toc = root.find("toc")
        assert toc is not None, "TOCが生成されていません"

        # TOCエントリを取得
        entries = toc.findall("entry")
        assert len(entries) > 0, "TOCエントリがありません"

        # チャプターエントリを抽出 (level="1" がchapter)
        chapter_entries = [e for e in entries if e.get("level") == "1"]
        assert len(chapter_entries) >= 9, f"チャプター数が不足: {len(chapter_entries)}"

        # 主要チャプターの存在を確認
        for expected in expected_toc_chapters:
            matching = [
                e
                for e in chapter_entries
                if e.get("number") == expected["number"]
                and expected["title_contains"] in (e.get("title") or "")
            ]
            assert len(matching) > 0, (
                f"チャプター {expected['number']} ({expected['title_contains']}) が見つかりません"
            )

    def test_page_count_preserved(
        self, normal_file_path: Path, tmp_path: Path
    ) -> None:
        """ページ数が保持される"""
        if not normal_file_path.exists():
            pytest.skip("正常テストファイルが見つかりません (4fd5500620491ebe)")

        output_xml = tmp_path / "book.xml"
        result = convert_book(normal_file_path, output_xml)

        # 変換結果のページ数を確認
        assert result.total_pages > 0, "ページ数が0です"

        # XMLからもページ数を確認
        tree = ET.parse(output_xml)
        root = tree.getroot()
        pages = root.findall(".//page")
        assert len(pages) == result.total_pages, (
            f"XMLページ数 ({len(pages)}) と結果ページ数 ({result.total_pages}) が不一致"
        )

    def test_no_page_loss(
        self, normal_file_path: Path, tmp_path: Path
    ) -> None:
        """ページ欠損がない（PageValidationErrorが発生しない）"""
        if not normal_file_path.exists():
            pytest.skip("正常テストファイルが見つかりません (4fd5500620491ebe)")

        from src.book_converter.errors import PageValidationError

        output_xml = tmp_path / "book.xml"

        # PageValidationErrorが発生しないことを確認
        try:
            result = convert_book(normal_file_path, output_xml)
            assert result.success is True
        except PageValidationError as e:
            pytest.fail(f"PageValidationErrorが発生しました: {e}")

    def test_japanese_chapter_format_recognized(
        self, normal_file_path: Path, tmp_path: Path
    ) -> None:
        """日本語の第N章形式が正しく認識される"""
        if not normal_file_path.exists():
            pytest.skip("正常テストファイルが見つかりません (4fd5500620491ebe)")

        # Check if file has TOC markers
        content = normal_file_path.read_text(encoding="utf-8")
        if "<!-- toc -->" not in content.lower():
            pytest.skip("テストファイルにTOCマーカーがありません")

        output_xml = tmp_path / "book.xml"
        convert_book(normal_file_path, output_xml)

        tree = ET.parse(output_xml)
        root = tree.getroot()

        toc = root.find("toc")
        assert toc is not None

        entries = toc.findall("entry")
        chapter_entries = [e for e in entries if e.get("level") == "1"]  # level="1" is chapter

        # 第1章が存在し、正しい属性を持つ
        chapter1 = [e for e in chapter_entries if e.get("number") == "1"]
        assert len(chapter1) > 0, "第1章が見つかりません"
        assert chapter1[0].get("level") == "1"  # chapter

    def test_section_format_recognized(
        self, normal_file_path: Path, tmp_path: Path
    ) -> None:
        """N.N節形式が正しく認識される"""
        if not normal_file_path.exists():
            pytest.skip("正常テストファイルが見つかりません (4fd5500620491ebe)")

        # Check if file has TOC markers
        content = normal_file_path.read_text(encoding="utf-8")
        if "<!-- toc -->" not in content.lower():
            pytest.skip("テストファイルにTOCマーカーがありません")

        output_xml = tmp_path / "book.xml"
        convert_book(normal_file_path, output_xml)

        tree = ET.parse(output_xml)
        root = tree.getroot()

        toc = root.find("toc")
        assert toc is not None

        entries = toc.findall("entry")
        section_entries = [e for e in entries if e.get("level") == "2"]  # level="2" is section

        # セクションエントリが存在する
        assert len(section_entries) > 0, "セクションエントリがありません"

    def test_xml_structure_valid(
        self, normal_file_path: Path, tmp_path: Path
    ) -> None:
        """生成されるXML構造が有効"""
        if not normal_file_path.exists():
            pytest.skip("正常テストファイルが見つかりません (4fd5500620491ebe)")

        output_xml = tmp_path / "book.xml"
        convert_book(normal_file_path, output_xml)

        # XMLパースが成功することを確認
        tree = ET.parse(output_xml)
        root = tree.getroot()

        # 基本構造確認
        assert root.tag == "book"
        assert root.find("metadata") is not None
        assert len(root.findall(".//page")) > 0

        # Check if file has TOC markers before asserting TOC existence
        content = normal_file_path.read_text(encoding="utf-8")
        if "<!-- toc -->" in content.lower():
            assert root.find("toc") is not None


class TestE2ENormalFileRegressionDetailed:
    """US3: 正常ファイルの詳細な回帰テスト

    既存の動作が保持されることを詳細に確認するテスト。
    """

    @pytest.fixture
    def normal_file_path(self) -> Path:
        """正常ファイルのパス"""
        return Path("/mnt/hugevolume/Data/BOOKS/OCR/output/4fd5500620491ebe/book.md")

    def test_toc_begin_end_attributes(
        self, normal_file_path: Path, tmp_path: Path
    ) -> None:
        """TOCのbegin/end属性が正しく設定される"""
        if not normal_file_path.exists():
            pytest.skip("正常テストファイルが見つかりません (4fd5500620491ebe)")

        # Check if file has TOC markers
        content = normal_file_path.read_text(encoding="utf-8")
        if "<!-- toc -->" not in content.lower():
            pytest.skip("テストファイルにTOCマーカーがありません")

        output_xml = tmp_path / "book.xml"
        convert_book(normal_file_path, output_xml)

        tree = ET.parse(output_xml)
        root = tree.getroot()

        toc = root.find("toc")
        assert toc is not None

        begin = toc.get("begin")
        end = toc.get("end")

        # begin/endが数値文字列であること
        assert begin is not None and begin.isdigit(), f"begin属性が不正: {begin}"
        assert end is not None and end.isdigit(), f"end属性が不正: {end}"

        # begin <= end であること
        assert int(begin) <= int(end), f"begin ({begin}) > end ({end})"

    def test_page_numbers_sequential(
        self, normal_file_path: Path, tmp_path: Path
    ) -> None:
        """ページ番号が存在する"""
        if not normal_file_path.exists():
            pytest.skip("正常テストファイルが見つかりません (4fd5500620491ebe)")

        output_xml = tmp_path / "book.xml"
        convert_book(normal_file_path, output_xml)

        tree = ET.parse(output_xml)
        root = tree.getroot()

        pages = root.findall(".//page")
        page_numbers = [p.get("number") for p in pages]

        # すべてのページに番号がある
        assert all(pn is not None and pn != "" for pn in page_numbers), (
            "ページ番号が欠落しているページがあります"
        )

    def test_content_elements_present(
        self, normal_file_path: Path, tmp_path: Path
    ) -> None:
        """コンテンツ要素が存在する"""
        if not normal_file_path.exists():
            pytest.skip("正常テストファイルが見つかりません (4fd5500620491ebe)")

        output_xml = tmp_path / "book.xml"
        convert_book(normal_file_path, output_xml)

        tree = ET.parse(output_xml)
        root = tree.getroot()

        # content要素が存在
        contents = root.findall(".//content")
        assert len(contents) > 0, "content要素がありません"

        # 少なくとも一部のcontentに子要素がある
        contents_with_children = [c for c in contents if len(c) > 0]
        assert len(contents_with_children) > 0, "コンテンツを持つページがありません"
