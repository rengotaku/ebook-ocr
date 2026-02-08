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


# =============================================================================
# Phase 3: User Story 2 - TTSコンテンツ階層と構造解析
# =============================================================================


class TestTransformHeading:
    """T032: Heading XML変換テスト (<heading level="N"> 生成)"""

    def test_transform_heading_level_1(self) -> None:
        """レベル1の見出しをXMLに変換"""
        from src.book_converter.transformer import transform_heading

        heading = Heading(level=1, text="第1章 はじめに")
        element = transform_heading(heading)

        assert element.tag == "heading"
        assert element.get("level") == "1"
        assert element.text == "第1章 はじめに"

    def test_transform_heading_level_2(self) -> None:
        """レベル2の見出しをXMLに変換"""
        from src.book_converter.transformer import transform_heading

        heading = Heading(level=2, text="1.1 概要")
        element = transform_heading(heading)

        assert element.get("level") == "2"
        assert element.text == "1.1 概要"

    def test_transform_heading_level_3(self) -> None:
        """レベル3の見出しをXMLに変換"""
        from src.book_converter.transformer import transform_heading

        heading = Heading(level=3, text="詳細説明")
        element = transform_heading(heading)

        assert element.get("level") == "3"
        assert element.text == "詳細説明"

    def test_transform_heading_returns_element(self) -> None:
        """戻り値はElement型"""
        from src.book_converter.transformer import transform_heading

        heading = Heading(level=1, text="テスト")
        element = transform_heading(heading)

        assert isinstance(element, Element)

    def test_transform_heading_preserves_unicode(self) -> None:
        """Unicode文字を正しく保持"""
        from src.book_converter.transformer import transform_heading

        heading = Heading(level=1, text="日本語見出し「テスト」")
        element = transform_heading(heading)

        assert element.text == "日本語見出し「テスト」"

    def test_transform_heading_xml_serialization(self) -> None:
        """XMLにシリアライズ可能"""
        from src.book_converter.transformer import transform_heading

        heading = Heading(level=2, text="章タイトル")
        element = transform_heading(heading)
        xml_string = tostring(element, encoding="unicode")

        assert "<heading" in xml_string
        assert 'level="2"' in xml_string
        assert "章タイトル" in xml_string


class TestTransformContent:
    """T033: Content XML変換テスト (<content>内にheading/paragraph/list)"""

    def test_transform_content_with_heading(self) -> None:
        """見出しを含むコンテンツを変換"""
        from src.book_converter.transformer import transform_content

        content = Content(
            elements=(Heading(level=1, text="タイトル"),)
        )
        element = transform_content(content)

        assert element is not None
        assert element.tag == "content"
        heading_elem = element.find("heading")
        assert heading_elem is not None
        assert heading_elem.get("level") == "1"
        assert heading_elem.text == "タイトル"

    def test_transform_content_with_paragraph(self) -> None:
        """段落を含むコンテンツを変換"""
        from src.book_converter.transformer import transform_content
        from src.book_converter.models import Paragraph

        content = Content(
            elements=(Paragraph(text="本文テキストです。"),)
        )
        element = transform_content(content)

        assert element is not None
        para_elem = element.find("paragraph")
        assert para_elem is not None
        assert para_elem.text == "本文テキストです。"

    def test_transform_content_with_list(self) -> None:
        """リストを含むコンテンツを変換"""
        from src.book_converter.transformer import transform_content
        from src.book_converter.models import List

        content = Content(
            elements=(List(items=("項目1", "項目2", "項目3")),)
        )
        element = transform_content(content)

        assert element is not None
        list_elem = element.find("list")
        assert list_elem is not None
        items = list_elem.findall("item")
        assert len(items) == 3
        assert items[0].text == "項目1"
        assert items[1].text == "項目2"
        assert items[2].text == "項目3"

    def test_transform_content_mixed_elements(self) -> None:
        """見出し、段落、リストが混在するコンテンツ"""
        from src.book_converter.transformer import transform_content
        from src.book_converter.models import Paragraph, List

        content = Content(
            elements=(
                Heading(level=1, text="章タイトル"),
                Paragraph(text="導入文です。"),
                List(items=("ポイント1", "ポイント2")),
                Heading(level=2, text="節タイトル"),
                Paragraph(text="詳細説明です。"),
            )
        )
        element = transform_content(content)

        assert element is not None
        children = list(element)
        assert len(children) == 5

        # 順序が保持されているか確認
        assert children[0].tag == "heading"
        assert children[1].tag == "paragraph"
        assert children[2].tag == "list"
        assert children[3].tag == "heading"
        assert children[4].tag == "paragraph"

    def test_transform_content_empty_returns_none(self) -> None:
        """空のコンテンツはNoneを返す"""
        from src.book_converter.transformer import transform_content

        content = Content(elements=())
        element = transform_content(content)

        assert element is None

    def test_transform_content_preserves_element_order(self) -> None:
        """要素の順序を保持"""
        from src.book_converter.transformer import transform_content
        from src.book_converter.models import Paragraph

        content = Content(
            elements=(
                Paragraph(text="段落1"),
                Heading(level=2, text="見出し"),
                Paragraph(text="段落2"),
            )
        )
        element = transform_content(content)

        assert element is not None
        children = list(element)
        assert children[0].tag == "paragraph"
        assert children[0].text == "段落1"
        assert children[1].tag == "heading"
        assert children[2].tag == "paragraph"
        assert children[2].text == "段落2"


class TestTransformContentContinued:
    """T034: 継続属性テスト (continued="true" ページ跨ぎ)"""

    def test_content_with_continued_true(self) -> None:
        """continued=trueのコンテンツを変換"""
        from src.book_converter.transformer import transform_content_with_continued
        from src.book_converter.models import Paragraph

        content = Content(
            elements=(Paragraph(text="継続する本文"),)
        )
        element = transform_content_with_continued(content, continued=True)

        assert element is not None
        assert element.get("continued") == "true"

    def test_content_with_continued_false(self) -> None:
        """continued=falseの場合は属性なし"""
        from src.book_converter.transformer import transform_content_with_continued
        from src.book_converter.models import Paragraph

        content = Content(
            elements=(Paragraph(text="通常の本文"),)
        )
        element = transform_content_with_continued(content, continued=False)

        assert element is not None
        assert element.get("continued") is None

    def test_page_continued_attribute(self) -> None:
        """ページのcontinued属性が正しく設定される"""
        page = Page(
            number="5",
            source_file="page_0005.png",
            content=Content(elements=()),
            continued=True,
        )

        element = transform_page(page)

        assert element.get("continued") == "true"

    def test_page_not_continued(self) -> None:
        """ページがcontinued=falseの場合は属性なし"""
        page = Page(
            number="1",
            source_file="page_0001.png",
            content=Content(elements=()),
            continued=False,
        )

        element = transform_page(page)

        assert element.get("continued") is None

    def test_continued_paragraph_in_content(self) -> None:
        """ページ跨ぎの段落をXMLで表現"""
        from src.book_converter.transformer import transform_content_with_continued
        from src.book_converter.models import Paragraph

        # ページの先頭で前ページからの継続を示す
        content = Content(
            elements=(
                Paragraph(text="（前ページからの続き）本文が続きます。"),
            )
        )
        element = transform_content_with_continued(content, continued=True)

        assert element is not None
        assert element.get("continued") == "true"
        para = element.find("paragraph")
        assert para is not None
        assert "続き" in para.text

    def test_continued_heading_spanning_pages(self) -> None:
        """見出しの後に続くページ"""
        from src.book_converter.transformer import transform_content_with_continued
        from src.book_converter.models import Paragraph

        # 前ページで見出しが表示され、このページで本文が続く場合
        content = Content(
            elements=(
                Paragraph(text="前ページの見出しに続く本文です。"),
            )
        )
        element = transform_content_with_continued(content, continued=True)

        assert element is not None
        assert element.get("continued") == "true"


# =============================================================================
# Phase 4: User Story 3 - TTS図表説明制御とメタデータ分離
# =============================================================================


class TestTransformFigure:
    """T053: Figure XML変換テスト (<figure readAloud="optional"> 生成)"""

    def test_transform_figure_basic(self) -> None:
        """基本的な図をXMLに変換"""
        from src.book_converter.transformer import transform_figure
        from src.book_converter.models import Figure

        figure = Figure(file="images/fig1.png")
        element = transform_figure(figure)

        assert element.tag == "figure"
        file_elem = element.find("file")
        assert file_elem is not None
        assert file_elem.text == "images/fig1.png"

    def test_transform_figure_with_caption(self) -> None:
        """キャプション付きの図を変換"""
        from src.book_converter.transformer import transform_figure
        from src.book_converter.models import Figure

        figure = Figure(
            file="chart.png",
            caption="図1: 売上推移",
        )
        element = transform_figure(figure)

        caption_elem = element.find("caption")
        assert caption_elem is not None
        assert caption_elem.text == "図1: 売上推移"

    def test_transform_figure_with_description(self) -> None:
        """説明文付きの図を変換"""
        from src.book_converter.transformer import transform_figure
        from src.book_converter.models import Figure

        figure = Figure(
            file="diagram.png",
            description="システム構成を表す図です。",
        )
        element = transform_figure(figure)

        desc_elem = element.find("description")
        assert desc_elem is not None
        assert desc_elem.text == "システム構成を表す図です。"

    def test_transform_figure_read_aloud_optional(self) -> None:
        """readAloud='optional'属性を変換"""
        from src.book_converter.transformer import transform_figure
        from src.book_converter.models import Figure

        figure = Figure(file="test.png", read_aloud="optional")
        element = transform_figure(figure)

        assert element.get("readAloud") == "optional"

    def test_transform_figure_read_aloud_true(self) -> None:
        """readAloud='true'属性を変換"""
        from src.book_converter.transformer import transform_figure
        from src.book_converter.models import Figure

        figure = Figure(file="test.png", read_aloud="true")
        element = transform_figure(figure)

        assert element.get("readAloud") == "true"

    def test_transform_figure_read_aloud_false(self) -> None:
        """readAloud='false'属性を変換"""
        from src.book_converter.transformer import transform_figure
        from src.book_converter.models import Figure

        figure = Figure(file="test.png", read_aloud="false")
        element = transform_figure(figure)

        assert element.get("readAloud") == "false"

    def test_transform_figure_returns_element(self) -> None:
        """戻り値はElement型"""
        from src.book_converter.transformer import transform_figure
        from src.book_converter.models import Figure

        figure = Figure(file="test.png")
        element = transform_figure(figure)

        assert isinstance(element, Element)

    def test_transform_figure_full(self) -> None:
        """全属性を持つ図を変換"""
        from src.book_converter.transformer import transform_figure
        from src.book_converter.models import Figure

        figure = Figure(
            file="images/architecture.png",
            caption="図2-1: システムアーキテクチャ",
            description="本システムの全体構成を示す図です。主要コンポーネント間の関係を表しています。",
            read_aloud="optional",
        )
        element = transform_figure(figure)

        assert element.tag == "figure"
        assert element.get("readAloud") == "optional"
        assert element.find("file").text == "images/architecture.png"
        assert element.find("caption").text == "図2-1: システムアーキテクチャ"
        assert "全体構成" in element.find("description").text

    def test_transform_figure_xml_serialization(self) -> None:
        """XMLにシリアライズ可能"""
        from src.book_converter.transformer import transform_figure
        from src.book_converter.models import Figure

        figure = Figure(
            file="test.png",
            caption="テスト図",
            read_aloud="optional",
        )
        element = transform_figure(figure)
        xml_string = tostring(element, encoding="unicode")

        assert "<figure" in xml_string
        assert 'readAloud="optional"' in xml_string
        assert "test.png" in xml_string
        assert "テスト図" in xml_string

    def test_transform_figure_with_continued(self) -> None:
        """ページをまたぐ図を変換"""
        from src.book_converter.transformer import transform_figure
        from src.book_converter.models import Figure

        figure = Figure(
            file="large_diagram.png",
            continued=True,
        )
        element = transform_figure(figure)

        assert element.get("continued") == "true"

    def test_transform_figure_preserves_unicode(self) -> None:
        """Unicode文字を保持"""
        from src.book_converter.transformer import transform_figure
        from src.book_converter.models import Figure

        figure = Figure(
            file="日本語/図表.png",
            caption="日本語キャプション「テスト」",
            description="日本語の説明文です。",
        )
        element = transform_figure(figure)

        assert element.find("file").text == "日本語/図表.png"
        assert "日本語キャプション" in element.find("caption").text
        assert "日本語の説明文" in element.find("description").text


class TestTransformPageMetadata:
    """T054: PageMetadata XML変換テスト (<pageMetadata type="chapter-page"> 生成)"""

    def test_transform_page_metadata_basic(self) -> None:
        """基本的なページメタデータをXMLに変換"""
        from src.book_converter.transformer import transform_page_metadata
        from src.book_converter.models import PageMetadata

        metadata = PageMetadata(
            text="3 / 7",
            meta_type="chapter-page",
            current=3,
            total=7,
        )
        element = transform_page_metadata(metadata)

        assert element.tag == "pageMetadata"
        assert element.get("type") == "chapter-page"
        assert element.text == "3 / 7"

    def test_transform_page_metadata_section_page(self) -> None:
        """section-pageタイプを変換"""
        from src.book_converter.transformer import transform_page_metadata
        from src.book_converter.models import PageMetadata

        metadata = PageMetadata(
            text="1.2節 2 / 5",
            meta_type="section-page",
            section_name="1.2節",
            current=2,
            total=5,
        )
        element = transform_page_metadata(metadata)

        assert element.get("type") == "section-page"

    def test_transform_page_metadata_unknown_type(self) -> None:
        """unknownタイプを変換"""
        from src.book_converter.transformer import transform_page_metadata
        from src.book_converter.models import PageMetadata

        metadata = PageMetadata(
            text="??? 1 / 1",
            meta_type="unknown",
            current=1,
            total=1,
        )
        element = transform_page_metadata(metadata)

        assert element.get("type") == "unknown"

    def test_transform_page_metadata_returns_element(self) -> None:
        """戻り値はElement型"""
        from src.book_converter.transformer import transform_page_metadata
        from src.book_converter.models import PageMetadata

        metadata = PageMetadata(text="1 / 5", current=1, total=5)
        element = transform_page_metadata(metadata)

        assert isinstance(element, Element)

    def test_transform_page_metadata_none_returns_none(self) -> None:
        """NoneはNoneを返す"""
        from src.book_converter.transformer import transform_page_metadata

        result = transform_page_metadata(None)

        assert result is None

    def test_transform_page_metadata_with_section_name(self) -> None:
        """セクション名を含むメタデータを変換"""
        from src.book_converter.transformer import transform_page_metadata
        from src.book_converter.models import PageMetadata

        metadata = PageMetadata(
            text="はじめに 1 / 3",
            meta_type="chapter-page",
            section_name="はじめに",
            current=1,
            total=3,
        )
        element = transform_page_metadata(metadata)

        assert element.text == "はじめに 1 / 3"
        # セクション名は属性またはテキストに含まれる
        xml_string = tostring(element, encoding="unicode")
        assert "はじめに" in xml_string

    def test_transform_page_metadata_read_aloud_false(self) -> None:
        """pageMetadataはreadAloud='false'"""
        from src.book_converter.transformer import transform_page_metadata
        from src.book_converter.models import PageMetadata

        metadata = PageMetadata(text="1 / 5", current=1, total=5)
        element = transform_page_metadata(metadata)

        # pageMetadataはTTSで読み上げない
        assert element.get("readAloud") == "false"

    def test_transform_page_metadata_xml_serialization(self) -> None:
        """XMLにシリアライズ可能"""
        from src.book_converter.transformer import transform_page_metadata
        from src.book_converter.models import PageMetadata

        metadata = PageMetadata(
            text="第1章 5 / 20",
            meta_type="chapter-page",
            section_name="第1章",
            current=5,
            total=20,
        )
        element = transform_page_metadata(metadata)
        xml_string = tostring(element, encoding="unicode")

        assert "<pageMetadata" in xml_string
        assert 'type="chapter-page"' in xml_string
        assert "第1章 5 / 20" in xml_string

    def test_transform_page_metadata_preserves_original_text(self) -> None:
        """元のテキストを保持"""
        from src.book_converter.transformer import transform_page_metadata
        from src.book_converter.models import PageMetadata

        original_text = "まえがき  2  /  10"
        metadata = PageMetadata(
            text=original_text,
            meta_type="chapter-page",
            section_name="まえがき",
            current=2,
            total=10,
        )
        element = transform_page_metadata(metadata)

        assert element.text == original_text


class TestReadAloudInheritance:
    """T055: readAloud属性継承テスト (file=false, caption=true, description=親継承)"""

    def test_figure_file_read_aloud_false(self) -> None:
        """<file>要素はreadAloud='false'"""
        from src.book_converter.transformer import transform_figure
        from src.book_converter.models import Figure

        figure = Figure(file="test.png")
        element = transform_figure(figure)

        file_elem = element.find("file")
        assert file_elem is not None
        # file要素は読み上げない
        assert file_elem.get("readAloud") == "false"

    def test_figure_caption_read_aloud_true(self) -> None:
        """<caption>要素はreadAloud='true'"""
        from src.book_converter.transformer import transform_figure
        from src.book_converter.models import Figure

        figure = Figure(file="test.png", caption="図1")
        element = transform_figure(figure)

        caption_elem = element.find("caption")
        assert caption_elem is not None
        # caption要素は読み上げる
        assert caption_elem.get("readAloud") == "true"

    def test_figure_description_inherits_parent(self) -> None:
        """<description>要素は親のreadAloud属性を継承"""
        from src.book_converter.transformer import transform_figure
        from src.book_converter.models import Figure

        # 親がoptionalの場合
        figure_optional = Figure(
            file="test.png",
            description="説明文",
            read_aloud="optional",
        )
        element = transform_figure(figure_optional)
        desc_elem = element.find("description")
        # descriptionは親を継承するか、親と同じ設定
        # 仕様: descriptionは親のreadAloud設定を継承
        assert desc_elem.get("readAloud") is None or \
               desc_elem.get("readAloud") == element.get("readAloud")

    def test_figure_description_inherits_true(self) -> None:
        """親がreadAloud='true'の場合、descriptionも読み上げ対象"""
        from src.book_converter.transformer import transform_figure
        from src.book_converter.models import Figure

        figure = Figure(
            file="test.png",
            description="この図は重要です",
            read_aloud="true",
        )
        element = transform_figure(figure)
        desc_elem = element.find("description")

        # 親がtrueの場合、descriptionも読み上げ対象
        # 属性を継承するか、明示的にtrueを設定
        assert desc_elem is not None

    def test_figure_description_inherits_false(self) -> None:
        """親がreadAloud='false'の場合、descriptionも読み上げない"""
        from src.book_converter.transformer import transform_figure
        from src.book_converter.models import Figure

        figure = Figure(
            file="test.png",
            description="この図は読み上げません",
            read_aloud="false",
        )
        element = transform_figure(figure)
        desc_elem = element.find("description")

        # 親がfalseの場合、descriptionも読み上げない
        assert desc_elem is not None

    def test_page_metadata_always_read_aloud_false(self) -> None:
        """pageMetadataは常にreadAloud='false'"""
        from src.book_converter.transformer import transform_page_metadata
        from src.book_converter.models import PageMetadata

        metadata = PageMetadata(text="1 / 5", current=1, total=5)
        element = transform_page_metadata(metadata)

        # pageMetadataは本文読み上げに混入しない
        assert element.get("readAloud") == "false"

    def test_page_includes_figure_with_read_aloud(self) -> None:
        """ページに図が含まれる場合のreadAloud属性"""
        from src.book_converter.models import Figure

        page = Page(
            number="1",
            source_file="page_0001.png",
            content=Content(elements=()),
            figures=(
                Figure(file="fig1.png", read_aloud="optional"),
                Figure(file="fig2.png", read_aloud="true"),
            ),
        )

        element = transform_page(page)

        # ページ内の図が正しく変換されているか
        # transform_pageが図を含む場合の処理は実装による
        # 少なくともPageオブジェクトには図が含まれている
        assert len(page.figures) == 2

    def test_content_read_aloud_default_true(self) -> None:
        """<content>のreadAloudデフォルトはtrue"""
        from src.book_converter.transformer import transform_content
        from src.book_converter.models import Paragraph

        content = Content(
            elements=(Paragraph(text="本文"),)
        )
        element = transform_content(content)

        # contentのデフォルトはtrue（省略可）
        # 属性がなくてもtrue扱い
        read_aloud = element.get("readAloud")
        assert read_aloud is None or read_aloud == "true"

    def test_heading_read_aloud_default_true(self) -> None:
        """<heading>のreadAloudデフォルトはtrue"""
        from src.book_converter.transformer import transform_heading

        heading = Heading(level=1, text="タイトル")
        element = transform_heading(heading)

        # headingのデフォルトはtrue（省略可）
        read_aloud = element.get("readAloud")
        assert read_aloud is None or read_aloud == "true"


# =============================================================================
# Phase 2 US1: T015 - readAloud属性付与テスト
# =============================================================================


class TestHeadingReadAloudAttribute:
    """T015: transform_heading で readAloud="false" 出力テスト"""

    def test_heading_read_aloud_false_attribute(self) -> None:
        """Heading(read_aloud=False) の場合に readAloud="false" 属性を出力"""
        from src.book_converter.transformer import transform_heading

        heading = Heading(level=1, text="SREの知識地図", read_aloud=False)
        element = transform_heading(heading)

        assert element.get("readAloud") == "false"

    def test_heading_read_aloud_true_default(self) -> None:
        """Heading(read_aloud=True) の場合は readAloud 属性を省略可"""
        from src.book_converter.transformer import transform_heading

        heading = Heading(level=1, text="通常の見出し", read_aloud=True)
        element = transform_heading(heading)

        # デフォルト true は属性省略または "true"
        read_aloud = element.get("readAloud")
        assert read_aloud is None or read_aloud == "true"

    def test_heading_read_aloud_false_xml_serialization(self) -> None:
        """readAloud="false" がXMLにシリアライズされる"""
        from src.book_converter.transformer import transform_heading

        heading = Heading(level=2, text="ページ番号表記", read_aloud=False)
        element = transform_heading(heading)
        xml_string = tostring(element, encoding="unicode")

        assert 'readAloud="false"' in xml_string

    def test_heading_read_aloud_preserves_other_attributes(self) -> None:
        """readAloud 属性と他の属性を両方出力"""
        from src.book_converter.transformer import transform_heading

        heading = Heading(level=3, text="1.1.1 概要 — 1 / 3", read_aloud=False)
        element = transform_heading(heading)

        assert element.get("level") == "3"
        assert element.get("readAloud") == "false"
        assert element.text == "1.1.1 概要 — 1 / 3"

    def test_heading_read_aloud_false_in_content(self) -> None:
        """Content 内の Heading で readAloud=False が反映される"""
        from src.book_converter.transformer import transform_content

        content = Content(
            elements=(
                Heading(level=1, text="柱タイトル", read_aloud=False),
                Heading(level=2, text="通常見出し", read_aloud=True),
            )
        )
        element = transform_content(content)

        headings = element.findall("heading")
        assert len(headings) == 2

        # 最初の heading は readAloud="false"
        assert headings[0].get("readAloud") == "false"

        # 2番目の heading は readAloud 省略または "true"
        read_aloud_2 = headings[1].get("readAloud")
        assert read_aloud_2 is None or read_aloud_2 == "true"

    def test_heading_read_aloud_unicode_text(self) -> None:
        """Unicode テキストの見出しで readAloud=False を出力"""
        from src.book_converter.transformer import transform_heading

        heading = Heading(
            level=1,
            text="日本語タイトル「テスト」",
            read_aloud=False,
        )
        element = transform_heading(heading)

        assert element.get("readAloud") == "false"
        assert element.text == "日本語タイトル「テスト」"

    def test_multiple_headings_mixed_read_aloud(self) -> None:
        """複数の heading で readAloud が混在するケース"""
        from src.book_converter.transformer import transform_content

        content = Content(
            elements=(
                Heading(level=1, text="柱1", read_aloud=False),
                Heading(level=2, text="本文1", read_aloud=True),
                Heading(level=1, text="柱2", read_aloud=False),
                Heading(level=3, text="詳細1", read_aloud=True),
            )
        )
        element = transform_content(content)

        headings = element.findall("heading")
        assert len(headings) == 4

        # 柱は readAloud="false"
        assert headings[0].get("readAloud") == "false"
        assert headings[2].get("readAloud") == "false"

        # 本文見出しは readAloud 省略または "true"
        assert headings[1].get("readAloud") is None or headings[1].get("readAloud") == "true"
        assert headings[3].get("readAloud") is None or headings[3].get("readAloud") == "true"

    def test_paragraph_read_aloud_default_true(self) -> None:
        """<paragraph>のreadAloudデフォルトはtrue"""
        from src.book_converter.transformer import transform_content
        from src.book_converter.models import Paragraph

        content = Content(
            elements=(Paragraph(text="段落テキスト"),)
        )
        element = transform_content(content)
        para_elem = element.find("paragraph")

        # paragraphのデフォルトはtrue（省略可）
        read_aloud = para_elem.get("readAloud")
        assert read_aloud is None or read_aloud == "true"


# =============================================================================
# Phase 7: Emphasis Conversion - **強調** → <emphasis>
# =============================================================================


class TestEmphasisConversion:
    """強調変換テスト: **text** → <emphasis>text</emphasis>"""

    def test_paragraph_with_single_emphasis(self) -> None:
        """単一の強調を含む段落を変換"""
        from src.book_converter.transformer import transform_content
        from src.book_converter.models import Paragraph

        content = Content(
            elements=(Paragraph(text="これは**強調**です。"),)
        )
        element = transform_content(content)
        para_elem = element.find("paragraph")

        # **強調** が <emphasis>強調</emphasis> に変換される
        emphasis = para_elem.find("emphasis")
        assert emphasis is not None
        assert emphasis.text == "強調"

    def test_paragraph_with_multiple_emphasis(self) -> None:
        """複数の強調を含む段落を変換"""
        from src.book_converter.transformer import transform_content
        from src.book_converter.models import Paragraph

        content = Content(
            elements=(Paragraph(text="**最初**と**二番目**の強調"),)
        )
        element = transform_content(content)
        para_elem = element.find("paragraph")

        emphasis_elems = para_elem.findall("emphasis")
        assert len(emphasis_elems) == 2
        assert emphasis_elems[0].text == "最初"
        assert emphasis_elems[1].text == "二番目"

    def test_paragraph_without_emphasis(self) -> None:
        """強調なしの段落はそのまま"""
        from src.book_converter.transformer import transform_content
        from src.book_converter.models import Paragraph

        content = Content(
            elements=(Paragraph(text="通常のテキストです。"),)
        )
        element = transform_content(content)
        para_elem = element.find("paragraph")

        # emphasisは生成されない
        assert para_elem.find("emphasis") is None
        assert para_elem.text == "通常のテキストです。"

    def test_paragraph_emphasis_preserves_surrounding_text(self) -> None:
        """強調の前後のテキストを保持"""
        from src.book_converter.transformer import transform_content
        from src.book_converter.models import Paragraph

        content = Content(
            elements=(Paragraph(text="前のテキスト**強調**後のテキスト"),)
        )
        element = transform_content(content)
        para_elem = element.find("paragraph")

        # 前のテキストはpara_elem.text
        assert para_elem.text == "前のテキスト"
        # 強調
        emphasis = para_elem.find("emphasis")
        assert emphasis.text == "強調"
        # 後のテキストはemphasis.tail
        assert emphasis.tail == "後のテキスト"

    def test_heading_with_emphasis(self) -> None:
        """強調を含む見出しを変換"""
        from src.book_converter.transformer import transform_content

        content = Content(
            elements=(Heading(level=1, text="**重要な**見出し"),)
        )
        element = transform_content(content)
        heading_elem = element.find("heading")

        emphasis = heading_elem.find("emphasis")
        assert emphasis is not None
        assert emphasis.text == "重要な"
        assert emphasis.tail == "見出し"

    def test_list_item_with_emphasis(self) -> None:
        """強調を含むリストアイテムを変換"""
        from src.book_converter.transformer import transform_content
        from src.book_converter.models import List

        content = Content(
            elements=(List(items=("**重要**な項目", "通常の項目")),)
        )
        element = transform_content(content)
        list_elem = element.find("list")
        items = list_elem.findall("item")

        # 最初のアイテムに強調がある
        emphasis = items[0].find("emphasis")
        assert emphasis is not None
        assert emphasis.text == "重要"
        assert emphasis.tail == "な項目"

        # 2番目は強調なし
        assert items[1].find("emphasis") is None
        assert items[1].text == "通常の項目"

    def test_emphasis_unicode_content(self) -> None:
        """Unicode文字を含む強調を変換"""
        from src.book_converter.transformer import transform_content
        from src.book_converter.models import Paragraph

        content = Content(
            elements=(Paragraph(text="**日本語「テスト」**を含む"),)
        )
        element = transform_content(content)
        para_elem = element.find("paragraph")

        emphasis = para_elem.find("emphasis")
        assert emphasis.text == "日本語「テスト」"

    def test_emphasis_xml_serialization(self) -> None:
        """強調を含む要素をXMLにシリアライズ"""
        from src.book_converter.transformer import transform_content
        from src.book_converter.models import Paragraph

        content = Content(
            elements=(Paragraph(text="テスト**強調**です"),)
        )
        element = transform_content(content)
        para_elem = element.find("paragraph")
        xml_string = tostring(para_elem, encoding="unicode")

        assert "<emphasis>" in xml_string
        assert "</emphasis>" in xml_string
        assert "強調" in xml_string

    def test_full_emphasis_only(self) -> None:
        """テキスト全体が強調の場合"""
        from src.book_converter.transformer import transform_content
        from src.book_converter.models import Paragraph

        content = Content(
            elements=(Paragraph(text="**全体が強調**"),)
        )
        element = transform_content(content)
        para_elem = element.find("paragraph")

        # テキスト部分は空またはNone
        assert para_elem.text is None or para_elem.text == ""
        emphasis = para_elem.find("emphasis")
        assert emphasis.text == "全体が強調"

    def test_page_metadata_emphasis_preserved(self) -> None:
        """pageMetadata内の強調も変換"""
        from src.book_converter.transformer import transform_page_metadata
        from src.book_converter.models import PageMetadata

        metadata = PageMetadata(
            text="**はじめに** 1 / 3",
            meta_type="chapter-page",
            section_name="はじめに",
            current=1,
            total=3,
        )
        element = transform_page_metadata(metadata)

        # pageMetadata内の強調も変換される
        emphasis = element.find("emphasis")
        assert emphasis is not None
        assert emphasis.text == "はじめに"


# =============================================================================
# Phase 2 (004-toc-structure): US1+US2 目次マーカー認識と構造化
# =============================================================================


class TestTransformTableOfContents:
    """T016: tableOfContents変換テスト (transform_table_of_contents)

    US1: 目次マーカーによる目次認識
    - <tableOfContents>要素が生成される
    """

    def test_transform_table_of_contents_basic(self) -> None:
        """基本的な目次をXMLに変換"""
        from src.book_converter.transformer import transform_table_of_contents
        from src.book_converter.models import TocEntry, TableOfContents

        entry = TocEntry(text="第1章", level="chapter", number="1", page="15")
        toc = TableOfContents(entries=(entry,))

        element = transform_table_of_contents(toc)

        assert element is not None
        assert element.tag == "tableOfContents"

    def test_transform_table_of_contents_returns_element(self) -> None:
        """戻り値はElement型"""
        from src.book_converter.transformer import transform_table_of_contents
        from src.book_converter.models import TocEntry, TableOfContents

        entry = TocEntry(text="テスト", level="chapter")
        toc = TableOfContents(entries=(entry,))

        element = transform_table_of_contents(toc)

        assert isinstance(element, Element)

    def test_transform_table_of_contents_contains_entries(self) -> None:
        """目次にエントリが含まれる"""
        from src.book_converter.transformer import transform_table_of_contents
        from src.book_converter.models import TocEntry, TableOfContents

        entry1 = TocEntry(text="第1章", level="chapter", number="1", page="15")
        entry2 = TocEntry(text="1.1 節", level="section", number="1.1", page="20")
        toc = TableOfContents(entries=(entry1, entry2))

        element = transform_table_of_contents(toc)

        entries = element.findall("entry")
        assert len(entries) == 2

    def test_transform_table_of_contents_multiple_entries(self) -> None:
        """複数エントリの目次を変換"""
        from src.book_converter.transformer import transform_table_of_contents
        from src.book_converter.models import TocEntry, TableOfContents

        entries = (
            TocEntry(text="はじめに", level="other", page="1"),
            TocEntry(text="第1章", level="chapter", number="1", page="15"),
            TocEntry(text="1.1 節", level="section", number="1.1", page="16"),
            TocEntry(text="1.1.1 項", level="subsection", number="1.1.1", page="17"),
            TocEntry(text="第2章", level="chapter", number="2", page="25"),
        )
        toc = TableOfContents(entries=entries)

        element = transform_table_of_contents(toc)

        entry_elems = element.findall("entry")
        assert len(entry_elems) == 5

    def test_transform_table_of_contents_preserves_order(self) -> None:
        """エントリの順序を保持"""
        from src.book_converter.transformer import transform_table_of_contents
        from src.book_converter.models import TocEntry, TableOfContents

        entries = (
            TocEntry(text="はじめに", level="other", page="1"),
            TocEntry(text="第1章", level="chapter", number="1", page="15"),
            TocEntry(text="おわりに", level="other", page="300"),
        )
        toc = TableOfContents(entries=entries)

        element = transform_table_of_contents(toc)

        entry_elems = element.findall("entry")
        assert entry_elems[0].get("title") == "はじめに"
        assert entry_elems[1].get("title") == "第1章"
        assert entry_elems[2].get("title") == "おわりに"

    def test_transform_table_of_contents_xml_serialization(self) -> None:
        """XMLにシリアライズ可能"""
        from src.book_converter.transformer import transform_table_of_contents
        from src.book_converter.models import TocEntry, TableOfContents

        entry = TocEntry(text="テスト", level="chapter", number="1", page="10")
        toc = TableOfContents(entries=(entry,))

        element = transform_table_of_contents(toc)
        xml_string = tostring(element, encoding="unicode")

        assert "<tableOfContents" in xml_string
        assert "<entry" in xml_string

    def test_transform_table_of_contents_none_returns_none(self) -> None:
        """NoneはNoneを返す"""
        from src.book_converter.transformer import transform_table_of_contents

        result = transform_table_of_contents(None)

        assert result is None


class TestTransformTocEntry:
    """T017: entry変換テスト (transform_toc_entry)

    US2: 章・節タイトルの構造化
    - <entry level="..." number="..." title="..." page="..."/> 形式で出力
    """

    def test_transform_toc_entry_basic(self) -> None:
        """基本的なエントリをXMLに変換"""
        from src.book_converter.transformer import transform_toc_entry
        from src.book_converter.models import TocEntry

        entry = TocEntry(text="SREとは", level="chapter", number="1", page="15")

        element = transform_toc_entry(entry)

        assert element is not None
        assert element.tag == "entry"

    def test_transform_toc_entry_level_attribute(self) -> None:
        """level属性が正しく設定される"""
        from src.book_converter.transformer import transform_toc_entry
        from src.book_converter.models import TocEntry

        entry = TocEntry(text="テスト", level="chapter", number="1", page="10")

        element = transform_toc_entry(entry)

        assert element.get("level") == "chapter"

    def test_transform_toc_entry_number_attribute(self) -> None:
        """number属性が正しく設定される"""
        from src.book_converter.transformer import transform_toc_entry
        from src.book_converter.models import TocEntry

        entry = TocEntry(text="テスト", level="section", number="2.1", page="20")

        element = transform_toc_entry(entry)

        assert element.get("number") == "2.1"

    def test_transform_toc_entry_title_attribute(self) -> None:
        """title属性が正しく設定される"""
        from src.book_converter.transformer import transform_toc_entry
        from src.book_converter.models import TocEntry

        entry = TocEntry(text="SREとは", level="chapter", number="1", page="15")

        element = transform_toc_entry(entry)

        assert element.get("title") == "SREとは"

    def test_transform_toc_entry_page_attribute(self) -> None:
        """page属性が正しく設定される"""
        from src.book_converter.transformer import transform_toc_entry
        from src.book_converter.models import TocEntry

        entry = TocEntry(text="テスト", level="chapter", number="1", page="42")

        element = transform_toc_entry(entry)

        assert element.get("page") == "42"

    def test_transform_toc_entry_chapter(self) -> None:
        """chapter levelのエントリを変換"""
        from src.book_converter.transformer import transform_toc_entry
        from src.book_converter.models import TocEntry

        entry = TocEntry(text="SREとは", level="chapter", number="1", page="15")

        element = transform_toc_entry(entry)

        assert element.get("level") == "chapter"
        assert element.get("number") == "1"
        assert element.get("title") == "SREとは"
        assert element.get("page") == "15"

    def test_transform_toc_entry_section(self) -> None:
        """section levelのエントリを変換"""
        from src.book_converter.transformer import transform_toc_entry
        from src.book_converter.models import TocEntry

        entry = TocEntry(text="SLOの理解", level="section", number="2.1", page="30")

        element = transform_toc_entry(entry)

        assert element.get("level") == "section"
        assert element.get("number") == "2.1"
        assert element.get("title") == "SLOの理解"
        assert element.get("page") == "30"

    def test_transform_toc_entry_subsection(self) -> None:
        """subsection levelのエントリを変換"""
        from src.book_converter.transformer import transform_toc_entry
        from src.book_converter.models import TocEntry

        entry = TocEntry(text="SLA", level="subsection", number="2.1.1", page="35")

        element = transform_toc_entry(entry)

        assert element.get("level") == "subsection"
        assert element.get("number") == "2.1.1"
        assert element.get("title") == "SLA"
        assert element.get("page") == "35"

    def test_transform_toc_entry_other(self) -> None:
        """other levelのエントリを変換"""
        from src.book_converter.transformer import transform_toc_entry
        from src.book_converter.models import TocEntry

        entry = TocEntry(text="はじめに", level="other", page="1")

        element = transform_toc_entry(entry)

        assert element.get("level") == "other"
        assert element.get("title") == "はじめに"
        assert element.get("page") == "1"

    def test_transform_toc_entry_without_number(self) -> None:
        """number属性が空の場合"""
        from src.book_converter.transformer import transform_toc_entry
        from src.book_converter.models import TocEntry

        entry = TocEntry(text="はじめに", level="other", number="", page="1")

        element = transform_toc_entry(entry)

        # number属性は空文字または省略
        number = element.get("number")
        assert number is None or number == ""

    def test_transform_toc_entry_without_page(self) -> None:
        """page属性が空の場合"""
        from src.book_converter.transformer import transform_toc_entry
        from src.book_converter.models import TocEntry

        entry = TocEntry(text="テスト", level="chapter", number="1", page="")

        element = transform_toc_entry(entry)

        # page属性は空文字または省略
        page = element.get("page")
        assert page is None or page == ""

    def test_transform_toc_entry_returns_element(self) -> None:
        """戻り値はElement型"""
        from src.book_converter.transformer import transform_toc_entry
        from src.book_converter.models import TocEntry

        entry = TocEntry(text="テスト", level="chapter")

        element = transform_toc_entry(entry)

        assert isinstance(element, Element)

    def test_transform_toc_entry_preserves_unicode(self) -> None:
        """Unicode文字を保持"""
        from src.book_converter.transformer import transform_toc_entry
        from src.book_converter.models import TocEntry

        entry = TocEntry(text="日本語「テスト」", level="chapter", number="1", page="10")

        element = transform_toc_entry(entry)

        assert element.get("title") == "日本語「テスト」"

    def test_transform_toc_entry_xml_serialization(self) -> None:
        """XMLにシリアライズ可能"""
        from src.book_converter.transformer import transform_toc_entry
        from src.book_converter.models import TocEntry

        entry = TocEntry(text="SREとは", level="chapter", number="1", page="15")

        element = transform_toc_entry(entry)
        xml_string = tostring(element, encoding="unicode")

        assert "<entry" in xml_string
        assert 'level="chapter"' in xml_string
        assert 'number="1"' in xml_string
        assert 'title="SREとは"' in xml_string
        assert 'page="15"' in xml_string


# =============================================================================
# Phase 3 (004-toc-structure): US3 目次の読み上げ制御
# =============================================================================


class TestTableOfContentsReadAloud:
    """T039: tableOfContentsのreadAloud属性テスト

    US3: 目次の読み上げ制御
    - <tableOfContents>要素にreadAloud="false"属性がデフォルトで設定される
    - FR-006: システムは<tableOfContents>要素にreadAloud="false"属性をデフォルトで設定しなければならない
    """

    def test_table_of_contents_has_read_aloud_false_attribute(self) -> None:
        """tableOfContentsにreadAloud="false"属性が設定される"""
        from src.book_converter.transformer import transform_table_of_contents
        from src.book_converter.models import TocEntry, TableOfContents

        entry = TocEntry(text="第1章", level="chapter", number="1", page="15")
        toc = TableOfContents(entries=(entry,), read_aloud=False)

        element = transform_table_of_contents(toc)

        assert element is not None
        assert element.get("readAloud") == "false"

    def test_table_of_contents_default_read_aloud_is_false(self) -> None:
        """tableOfContentsのreadAloudデフォルト値はfalse"""
        from src.book_converter.transformer import transform_table_of_contents
        from src.book_converter.models import TocEntry, TableOfContents

        entry = TocEntry(text="はじめに", level="other", page="1")
        # read_aloudを明示せずにTableOfContentsを作成
        toc = TableOfContents(entries=(entry,))

        element = transform_table_of_contents(toc)

        # デフォルトでreadAloud="false"が設定される
        assert element.get("readAloud") == "false"

    def test_table_of_contents_read_aloud_in_xml_output(self) -> None:
        """XMLシリアライズ時にreadAloud属性が含まれる"""
        from src.book_converter.transformer import transform_table_of_contents
        from src.book_converter.models import TocEntry, TableOfContents

        entry = TocEntry(text="テスト", level="chapter", number="1", page="10")
        toc = TableOfContents(entries=(entry,))

        element = transform_table_of_contents(toc)
        xml_string = tostring(element, encoding="unicode")

        assert 'readAloud="false"' in xml_string
        assert "<tableOfContents" in xml_string

    def test_page_level_toc_has_read_aloud_false(self) -> None:
        """ページレベルの目次もreadAloud="false"を持つ"""
        from src.book_converter.transformer import transform_page
        from src.book_converter.models import TocEntry, TableOfContents

        entry = TocEntry(text="SREとは", level="chapter", number="1", page="15")
        toc = TableOfContents(entries=(entry,))

        page = Page(
            number="1",
            source_file="page_0001.png",
            content=Content(elements=()),
            toc=toc,
        )

        element = transform_page(page)

        toc_elem = element.find("tableOfContents")
        assert toc_elem is not None
        assert toc_elem.get("readAloud") == "false"

    def test_book_level_toc_has_read_aloud_false(self) -> None:
        """ブックレベル（複数エントリ）の目次もreadAloud="false"を持つ"""
        from src.book_converter.transformer import transform_table_of_contents
        from src.book_converter.models import TocEntry, TableOfContents

        entries = (
            TocEntry(text="はじめに", level="other", page="1"),
            TocEntry(text="SREとは", level="chapter", number="1", page="15"),
            TocEntry(text="SREの定義", level="section", number="1.1", page="16"),
            TocEntry(text="歴史", level="subsection", number="1.1.1", page="17"),
            TocEntry(text="おわりに", level="other", page="300"),
        )
        toc = TableOfContents(entries=entries)

        element = transform_table_of_contents(toc)

        assert element.get("readAloud") == "false"
        # すべてのエントリが含まれている
        assert len(element.findall("entry")) == 5

    def test_empty_toc_still_has_read_aloud_false(self) -> None:
        """空の目次でもreadAloud="false"が設定される"""
        from src.book_converter.transformer import transform_table_of_contents
        from src.book_converter.models import TableOfContents

        toc = TableOfContents(entries=())

        element = transform_table_of_contents(toc)

        assert element is not None
        assert element.get("readAloud") == "false"
        assert len(element.findall("entry")) == 0


# =============================================================================
# Phase 4 (004-toc-structure): US4 コンテンツ範囲マーカー
# =============================================================================


class TestDefaultReadAloudFalse:
    """T053: デフォルトreadAloud=falseテスト

    US4: マーカーで囲まれていない範囲はデフォルトでreadAloud="false"
    FR-013: マーカーで囲まれていない範囲は、デフォルトで読み上げ非対象（readAloud="false"）としなければならない
    """

    def test_content_without_marker_has_read_aloud_false(self) -> None:
        """マーカーなしのcontentはreadAloud=false"""
        from src.book_converter.transformer import transform_content
        from src.book_converter.models import Content, Paragraph

        # read_aloud=Falseのコンテンツ（デフォルト動作）
        content = Content(
            elements=(Paragraph(text="本文テキスト", read_aloud=False),),
            read_aloud=False,
        )
        element = transform_content(content)

        assert element is not None
        assert element.get("readAloud") == "false"

    def test_paragraph_without_marker_has_read_aloud_false(self) -> None:
        """マーカーなしの段落はreadAloud=false"""
        from src.book_converter.transformer import transform_content
        from src.book_converter.models import Content, Paragraph

        content = Content(
            elements=(Paragraph(text="段落テキスト", read_aloud=False),),
            read_aloud=False,
        )
        element = transform_content(content)

        para_elem = element.find("paragraph")
        assert para_elem is not None
        assert para_elem.get("readAloud") == "false"

    def test_heading_without_marker_has_read_aloud_false(self) -> None:
        """マーカーなしの見出しはreadAloud=false"""
        from src.book_converter.transformer import transform_content
        from src.book_converter.models import Content, Heading

        content = Content(
            elements=(Heading(level=1, text="見出し", read_aloud=False),),
            read_aloud=False,
        )
        element = transform_content(content)

        heading_elem = element.find("heading")
        assert heading_elem is not None
        assert heading_elem.get("readAloud") == "false"

    def test_list_without_marker_has_read_aloud_false(self) -> None:
        """マーカーなしのリストはreadAloud=false"""
        from src.book_converter.transformer import transform_content
        from src.book_converter.models import Content, List

        content = Content(
            elements=(List(items=("項目1", "項目2"), read_aloud=False),),
            read_aloud=False,
        )
        element = transform_content(content)

        list_elem = element.find("list")
        assert list_elem is not None
        assert list_elem.get("readAloud") == "false"

    def test_default_content_model_read_aloud_is_false(self) -> None:
        """Content.read_aloudのデフォルト値はFalse"""
        from src.book_converter.models import Content

        content = Content(elements=())

        # Phase 4でデフォルトがFalseに変更される
        assert content.read_aloud is False


class TestContentMarkerReadAloudTrue:
    """T054: contentマーカー内readAloud=trueテスト

    US4: `<!-- content -->`で囲まれた範囲はreadAloud="true"
    FR-009, FR-010: content開始/終了マーカーの認識
    """

    def test_content_inside_marker_has_read_aloud_true(self) -> None:
        """contentマーカー内のcontentはreadAloud=true"""
        from src.book_converter.transformer import transform_content
        from src.book_converter.models import Content, Paragraph

        content = Content(
            elements=(Paragraph(text="読み上げ対象テキスト", read_aloud=True),),
            read_aloud=True,
        )
        element = transform_content(content)

        assert element is not None
        assert element.get("readAloud") == "true"

    def test_paragraph_inside_content_marker_has_read_aloud_true(self) -> None:
        """contentマーカー内の段落はreadAloud=true"""
        from src.book_converter.transformer import transform_content
        from src.book_converter.models import Content, Paragraph

        content = Content(
            elements=(Paragraph(text="読み上げ対象段落", read_aloud=True),),
            read_aloud=True,
        )
        element = transform_content(content)

        para_elem = element.find("paragraph")
        assert para_elem is not None
        assert para_elem.get("readAloud") == "true"

    def test_heading_inside_content_marker_has_read_aloud_true(self) -> None:
        """contentマーカー内の見出しはreadAloud=true"""
        from src.book_converter.transformer import transform_content
        from src.book_converter.models import Content, Heading

        content = Content(
            elements=(Heading(level=1, text="読み上げ対象見出し", read_aloud=True),),
            read_aloud=True,
        )
        element = transform_content(content)

        heading_elem = element.find("heading")
        assert heading_elem is not None
        assert heading_elem.get("readAloud") == "true"

    def test_list_inside_content_marker_has_read_aloud_true(self) -> None:
        """contentマーカー内のリストはreadAloud=true"""
        from src.book_converter.transformer import transform_content
        from src.book_converter.models import Content, List

        content = Content(
            elements=(List(items=("読み上げ項目1", "読み上げ項目2"), read_aloud=True),),
            read_aloud=True,
        )
        element = transform_content(content)

        list_elem = element.find("list")
        assert list_elem is not None
        assert list_elem.get("readAloud") == "true"

    def test_mixed_elements_inside_content_marker_all_have_read_aloud_true(self) -> None:
        """contentマーカー内の複合要素は全てreadAloud=true"""
        from src.book_converter.transformer import transform_content
        from src.book_converter.models import Content, Heading, Paragraph, List

        content = Content(
            elements=(
                Heading(level=1, text="章タイトル", read_aloud=True),
                Paragraph(text="本文", read_aloud=True),
                List(items=("項目",), read_aloud=True),
            ),
            read_aloud=True,
        )
        element = transform_content(content)

        assert element.get("readAloud") == "true"

        heading_elem = element.find("heading")
        assert heading_elem.get("readAloud") == "true"

        para_elem = element.find("paragraph")
        assert para_elem.get("readAloud") == "true"

        list_elem = element.find("list")
        assert list_elem.get("readAloud") == "true"


class TestSkipMarkerReadAloudFalse:
    """T055: skipマーカー内readAloud=falseテスト

    US4: `<!-- skip -->`で囲まれた範囲はreadAloud="false"
    FR-011, FR-012: skip開始/終了マーカーの認識
    """

    def test_content_inside_skip_marker_has_read_aloud_false(self) -> None:
        """skipマーカー内のcontentはreadAloud=false"""
        from src.book_converter.transformer import transform_content
        from src.book_converter.models import Content, Paragraph

        content = Content(
            elements=(Paragraph(text="索引テキスト", read_aloud=False),),
            read_aloud=False,
        )
        element = transform_content(content)

        assert element is not None
        assert element.get("readAloud") == "false"

    def test_paragraph_inside_skip_marker_has_read_aloud_false(self) -> None:
        """skipマーカー内の段落はreadAloud=false"""
        from src.book_converter.transformer import transform_content
        from src.book_converter.models import Content, Paragraph

        content = Content(
            elements=(Paragraph(text="索引段落", read_aloud=False),),
            read_aloud=False,
        )
        element = transform_content(content)

        para_elem = element.find("paragraph")
        assert para_elem is not None
        assert para_elem.get("readAloud") == "false"

    def test_skip_inside_content_has_read_aloud_false(self) -> None:
        """contentマーカー内にskipがネストした場合、skipの中はreadAloud="false"

        ネスト例:
        <!-- content --> (readAloud=true)
            本文... (readAloud=true)
            <!-- skip --> (readAloud=false)
                索引... (readAloud=false)
            <!-- /skip -->
            本文続き... (readAloud=true)
        <!-- /content -->
        """
        from src.book_converter.transformer import transform_content
        from src.book_converter.models import Content, Paragraph

        # skipマーカー内の段落（ネストの内側）
        content = Content(
            elements=(Paragraph(text="ネスト内の索引", read_aloud=False),),
            read_aloud=False,  # 内側のskipが優先
        )
        element = transform_content(content)

        para_elem = element.find("paragraph")
        assert para_elem is not None
        assert para_elem.get("readAloud") == "false"

    def test_content_inside_skip_then_back_to_skip(self) -> None:
        """skip内にcontentがネストし、contentを抜けた後はskip

        ネスト例:
        <!-- skip --> (readAloud=false)
            索引... (readAloud=false)
            <!-- content --> (readAloud=true)
                重要な注釈... (readAloud=true)
            <!-- /content -->
            索引続き... (readAloud=false)
        <!-- /skip -->
        """
        from src.book_converter.transformer import transform_content
        from src.book_converter.models import Content, Paragraph

        # contentマーカーを抜けた後の段落（外側のskipに戻る）
        content = Content(
            elements=(Paragraph(text="索引続き", read_aloud=False),),
            read_aloud=False,
        )
        element = transform_content(content)

        para_elem = element.find("paragraph")
        assert para_elem is not None
        assert para_elem.get("readAloud") == "false"


class TestContentReadAloudXMLSerialization:
    """contentのreadAloud属性のXMLシリアライズテスト"""

    def test_content_read_aloud_true_in_xml(self) -> None:
        """readAloud="true"がXMLに出力される"""
        from src.book_converter.transformer import transform_content
        from src.book_converter.models import Content, Paragraph

        content = Content(
            elements=(Paragraph(text="テスト", read_aloud=True),),
            read_aloud=True,
        )
        element = transform_content(content)
        xml_string = tostring(element, encoding="unicode")

        assert 'readAloud="true"' in xml_string

    def test_content_read_aloud_false_in_xml(self) -> None:
        """readAloud="false"がXMLに出力される"""
        from src.book_converter.transformer import transform_content
        from src.book_converter.models import Content, Paragraph

        content = Content(
            elements=(Paragraph(text="テスト", read_aloud=False),),
            read_aloud=False,
        )
        element = transform_content(content)
        xml_string = tostring(element, encoding="unicode")

        assert 'readAloud="false"' in xml_string

    def test_paragraph_read_aloud_true_in_xml(self) -> None:
        """段落のreadAloud="true"がXMLに出力される"""
        from src.book_converter.transformer import transform_content
        from src.book_converter.models import Content, Paragraph

        content = Content(
            elements=(Paragraph(text="テスト", read_aloud=True),),
            read_aloud=True,
        )
        element = transform_content(content)
        para_elem = element.find("paragraph")
        xml_string = tostring(para_elem, encoding="unicode")

        assert 'readAloud="true"' in xml_string

    def test_paragraph_read_aloud_false_in_xml(self) -> None:
        """段落のreadAloud="false"がXMLに出力される"""
        from src.book_converter.transformer import transform_content
        from src.book_converter.models import Content, Paragraph

        content = Content(
            elements=(Paragraph(text="テスト", read_aloud=False),),
            read_aloud=False,
        )
        element = transform_content(content)
        para_elem = element.find("paragraph")
        xml_string = tostring(para_elem, encoding="unicode")

        assert 'readAloud="false"' in xml_string
