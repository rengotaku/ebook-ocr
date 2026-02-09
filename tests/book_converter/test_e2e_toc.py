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

        # Verify entry attributes
        entry1 = entries[0]
        assert entry1.get("level") == "chapter"
        assert entry1.get("number") == "1"
        assert entry1.get("title") == "SREとは"
        assert entry1.get("page") == "15"

        entry2 = entries[1]
        assert entry2.get("level") == "section"
        assert entry2.get("number") == "1.1"
        assert entry2.get("title") == "SREの定義"
        assert entry2.get("page") == "16"

        entry3 = entries[2]
        assert entry3.get("level") == "subsection"
        assert entry3.get("number") == "1.1.1"
        assert entry3.get("title") == "歴史"
        assert entry3.get("page") == "17"

        entry4 = entries[3]
        assert entry4.get("level") == "chapter"
        assert entry4.get("number") == "2"
        assert entry4.get("title") == "信頼性の定義"
        assert entry4.get("page") == "25"

        entry5 = entries[4]
        assert entry5.get("level") == "other"
        assert entry5.get("number") is None
        assert entry5.get("title") == "おわりに"
        assert entry5.get("page") == "100"

        # Verify page 1 (no markers, default readAloud=false)
        page1 = [p for p in root.findall("page") if p.get("number") == "1"][0]
        content1 = page1.find("content")
        assert content1.get("readAloud") == "false"
        para1 = content1.find("paragraph")
        assert para1.get("readAloud") == "false"
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

        # All content should have readAloud=false (default)
        page1 = [p for p in root.findall("page") if p.get("number") == "1"][0]
        content1 = page1.find("content")
        assert content1.get("readAloud") == "false"

        heading = content1.find("heading")
        assert heading.get("readAloud") == "false"

        para = content1.find("paragraph")
        assert para.get("readAloud") == "false"

        lst = content1.find("list")
        assert lst.get("readAloud") == "false"

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
        # No marker
        assert paras[1].get("readAloud") == "false"
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

        # Verify page 1 (unmarked, readAloud=false)
        page1 = [p for p in root.findall("page") if p.get("number") == "1"][0]
        assert page1.find("content").get("readAloud") == "false"

        # Verify page 3 (content marker, readAloud=true)
        page3 = [p for p in root.findall("page") if p.get("number") == "3"][0]
        content3 = page3.find("content")
        assert content3.get("readAloud") == "true"
        assert content3.find("heading").get("readAloud") == "true"
        assert content3.find("paragraph").get("readAloud") == "true"

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
