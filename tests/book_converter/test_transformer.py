"""Transformer tests for book markdown to XML conversion.

Tests for Phase 2: User Story 1 - TTS Page Navigation and Audio Announcement
- T012: Page XML conversion test (<page number="N" sourceFile="...">)
- T013: PageAnnouncement XML conversion test (<pageAnnouncement>)
"""

import pytest
from xml.etree.ElementTree import Element, tostring

from src.book_converter.transformer import (
    transform_page,
    transform_page_announcement,
)
from src.book_converter.models import (
    Page,
    PageAnnouncement,
    Content,
    Heading,
)


class TestTransformPage:
    """T012: ページXML変換テスト (<page number="N" sourceFile="..."> 生成)"""

    def test_transform_page_basic_attributes(self) -> None:
        """基本的なページ属性を変換"""
        page = Page(
            number="1",
            source_file="page_0001.png",
            content=Content(elements=()),
        )

        element = transform_page(page)

        assert element.tag == "page"
        assert element.get("number") == "1"
        assert element.get("sourceFile") == "page_0001.png"

    def test_transform_page_with_large_number(self) -> None:
        """大きなページ番号を変換"""
        page = Page(
            number="999",
            source_file="page_0999.png",
            content=Content(elements=()),
        )

        element = transform_page(page)

        assert element.get("number") == "999"
        assert element.get("sourceFile") == "page_0999.png"

    def test_transform_page_with_empty_number(self) -> None:
        """ページ番号が空の場合も変換"""
        page = Page(
            number="",
            source_file="page_unknown.png",
            content=Content(elements=()),
        )

        element = transform_page(page)

        assert element.get("number") == ""
        assert element.get("sourceFile") == "page_unknown.png"

    def test_transform_page_includes_announcement(self) -> None:
        """ページアナウンスを含む場合"""
        page = Page(
            number="42",
            source_file="page_0042.png",
            content=Content(elements=()),
            announcement=PageAnnouncement(text="42ページ", format="simple"),
        )

        element = transform_page(page)

        announcement_elem = element.find("pageAnnouncement")
        assert announcement_elem is not None
        assert announcement_elem.text == "42ページ"
        assert announcement_elem.get("format") == "simple"

    def test_transform_page_without_announcement(self) -> None:
        """ページアナウンスがない場合"""
        page = Page(
            number="1",
            source_file="page_0001.png",
            content=Content(elements=()),
            announcement=None,
        )

        element = transform_page(page)

        announcement_elem = element.find("pageAnnouncement")
        assert announcement_elem is None

    def test_transform_page_returns_element(self) -> None:
        """戻り値はElement型"""
        page = Page(
            number="1",
            source_file="page_0001.png",
            content=Content(elements=()),
        )

        element = transform_page(page)

        assert isinstance(element, Element)

    def test_transform_page_with_continued_attribute(self) -> None:
        """continuedフラグを変換"""
        page = Page(
            number="5",
            source_file="page_0005.png",
            content=Content(elements=()),
            continued=True,
        )

        element = transform_page(page)

        assert element.get("continued") == "true"

    def test_transform_page_without_continued(self) -> None:
        """continued=Falseの場合は属性なし"""
        page = Page(
            number="1",
            source_file="page_0001.png",
            content=Content(elements=()),
            continued=False,
        )

        element = transform_page(page)

        # continued=Falseの場合は属性を含まない
        assert element.get("continued") is None

    def test_transform_page_with_special_page_type(self) -> None:
        """特殊ページタイプを変換"""
        page = Page(
            number="0",
            source_file="cover.png",
            content=Content(elements=()),
            page_type="cover",
        )

        element = transform_page(page)

        assert element.get("type") == "cover"

    def test_transform_page_normal_type_not_included(self) -> None:
        """normalタイプはtype属性を含まない"""
        page = Page(
            number="1",
            source_file="page_0001.png",
            content=Content(elements=()),
            page_type="normal",
        )

        element = transform_page(page)

        # normalの場合はtype属性を含まない
        assert element.get("type") is None


class TestTransformPageAnnouncement:
    """T013: PageAnnouncementXML変換テスト (<pageAnnouncement> 生成)"""

    def test_transform_simple_announcement(self) -> None:
        """シンプルなアナウンスを変換"""
        announcement = PageAnnouncement(text="1ページ", format="simple")

        element = transform_page_announcement(announcement)

        assert element.tag == "pageAnnouncement"
        assert element.text == "1ページ"
        assert element.get("format") == "simple"

    def test_transform_announcement_with_large_number(self) -> None:
        """大きなページ番号のアナウンス"""
        announcement = PageAnnouncement(text="999ページ", format="simple")

        element = transform_page_announcement(announcement)

        assert element.text == "999ページ"

    def test_transform_announcement_format_attribute(self) -> None:
        """format属性が正しく設定される"""
        announcement = PageAnnouncement(text="10ページ", format="simple")

        element = transform_page_announcement(announcement)

        assert element.get("format") == "simple"

    def test_transform_announcement_returns_element(self) -> None:
        """戻り値はElement型"""
        announcement = PageAnnouncement(text="5ページ", format="simple")

        element = transform_page_announcement(announcement)

        assert isinstance(element, Element)

    def test_transform_announcement_chapter_format(self) -> None:
        """chapterフォーマットを変換"""
        announcement = PageAnnouncement(
            text="第1章 5ページ目", format="chapter"
        )

        element = transform_page_announcement(announcement)

        assert element.text == "第1章 5ページ目"
        assert element.get("format") == "chapter"

    def test_announcement_xml_serialization(self) -> None:
        """XMLにシリアライズ可能"""
        announcement = PageAnnouncement(text="42ページ", format="simple")

        element = transform_page_announcement(announcement)
        xml_string = tostring(element, encoding="unicode")

        assert "pageAnnouncement" in xml_string
        assert "42ページ" in xml_string
        assert 'format="simple"' in xml_string

    def test_transform_none_announcement_returns_none(self) -> None:
        """Noneの場合はNoneを返す"""
        result = transform_page_announcement(None)

        assert result is None


class TestPageXMLStructure:
    """ページXML構造の統合テスト"""

    def test_page_has_correct_child_order(self) -> None:
        """子要素の順序が正しい（announcement → content）"""
        page = Page(
            number="1",
            source_file="page_0001.png",
            content=Content(elements=(Heading(level=1, text="タイトル"),)),
            announcement=PageAnnouncement(text="1ページ", format="simple"),
        )

        element = transform_page(page)
        children = list(element)

        # 最初の子要素はpageAnnouncement
        assert len(children) >= 1
        assert children[0].tag == "pageAnnouncement"

    def test_page_xml_is_well_formed(self) -> None:
        """生成されるXMLは整形式"""
        page = Page(
            number="42",
            source_file="page_0042.png",
            content=Content(elements=()),
            announcement=PageAnnouncement(text="42ページ", format="simple"),
        )

        element = transform_page(page)

        # XMLにシリアライズ可能であること
        xml_string = tostring(element, encoding="unicode")
        assert xml_string.startswith("<page ")
        assert "</page>" in xml_string
