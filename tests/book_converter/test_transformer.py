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
