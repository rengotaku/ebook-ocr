"""Transformer tests for book markdown to XML conversion.

Tests for Phase 2: User Story 1 - TTS Page Navigation and Audio Announcement
- T012: Page XML conversion test (<page number="N" sourceFile="...">)
- T013: PageAnnouncement XML conversion test (<pageAnnouncement>)
"""

from xml.etree.ElementTree import Element, tostring

from src.book_converter.models import (
    Content,
    Heading,
    Page,
    PageAnnouncement,
)
from src.book_converter.transformer import (
    transform_page,
    transform_page_announcement,
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
        announcement = PageAnnouncement(text="第1章 5ページ目", format="chapter")

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

        content = Content(elements=(Heading(level=1, text="タイトル"),))
        element = transform_content(content)

        assert element is not None
        assert element.tag == "content"
        heading_elem = element.find("heading")
        assert heading_elem is not None
        assert heading_elem.get("level") == "1"
        assert heading_elem.text == "タイトル"

    def test_transform_content_with_paragraph(self) -> None:
        """段落を含むコンテンツを変換"""
        from src.book_converter.models import Paragraph
        from src.book_converter.transformer import transform_content

        content = Content(elements=(Paragraph(text="本文テキストです。"),))
        element = transform_content(content)

        assert element is not None
        para_elem = element.find("paragraph")
        assert para_elem is not None
        assert para_elem.text == "本文テキストです。"

    def test_transform_content_with_list(self) -> None:
        """リストを含むコンテンツを変換"""
        from src.book_converter.models import List
        from src.book_converter.transformer import transform_content

        content = Content(elements=(List(items=("項目1", "項目2", "項目3")),))
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
        from src.book_converter.models import List, Paragraph
        from src.book_converter.transformer import transform_content

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
        from src.book_converter.models import Paragraph
        from src.book_converter.transformer import transform_content

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
        from src.book_converter.models import Paragraph
        from src.book_converter.transformer import transform_content_with_continued

        content = Content(elements=(Paragraph(text="継続する本文"),))
        element = transform_content_with_continued(content, continued=True)

        assert element is not None
        assert element.get("continued") == "true"

    def test_content_with_continued_false(self) -> None:
        """continued=falseの場合は属性なし"""
        from src.book_converter.models import Paragraph
        from src.book_converter.transformer import transform_content_with_continued

        content = Content(elements=(Paragraph(text="通常の本文"),))
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
        from src.book_converter.models import Paragraph
        from src.book_converter.transformer import transform_content_with_continued

        # ページの先頭で前ページからの継続を示す
        content = Content(elements=(Paragraph(text="（前ページからの続き）本文が続きます。"),))
        element = transform_content_with_continued(content, continued=True)

        assert element is not None
        assert element.get("continued") == "true"
        para = element.find("paragraph")
        assert para is not None
        assert "続き" in para.text

    def test_continued_heading_spanning_pages(self) -> None:
        """見出しの後に続くページ"""
        from src.book_converter.models import Paragraph
        from src.book_converter.transformer import transform_content_with_continued

        # 前ページで見出しが表示され、このページで本文が続く場合
        content = Content(elements=(Paragraph(text="前ページの見出しに続く本文です。"),))
        element = transform_content_with_continued(content, continued=True)

        assert element is not None
        assert element.get("continued") == "true"


# =============================================================================
# Phase 4: User Story 3 - TTS図表説明制御とメタデータ分離
# =============================================================================


class TestTransformFigure:
    """T053: Figure XML変換テスト (新形式: <figure path="..." caption="..." marker="..."/>)"""

    def test_transform_figure_basic(self) -> None:
        """基本的な図をXMLに変換"""
        from src.book_converter.models import Figure
        from src.book_converter.transformer import transform_figure

        figure = Figure(path="images/fig1.png")
        element = transform_figure(figure)

        assert element.tag == "figure"
        assert element.get("path") == "images/fig1.png"

    def test_transform_figure_with_caption(self) -> None:
        """キャプション付きの図を変換"""
        from src.book_converter.models import Figure
        from src.book_converter.transformer import transform_figure

        figure = Figure(
            path="chart.png",
            caption="図1: 売上推移",
        )
        element = transform_figure(figure)

        assert element.get("caption") == "図1: 売上推移"

    def test_transform_figure_with_marker(self) -> None:
        """マーカー付きの図を変換"""
        from src.book_converter.models import Figure
        from src.book_converter.transformer import transform_figure

        figure = Figure(
            path="diagram.png",
            marker="図1",
        )
        element = transform_figure(figure)

        assert element.get("marker") == "図1"

    def test_transform_figure_no_read_aloud_attribute(self) -> None:
        """図にreadAloud属性は出力されない"""
        from src.book_converter.models import Figure
        from src.book_converter.transformer import transform_figure

        figure = Figure(path="test.png")
        element = transform_figure(figure)

        # 図は常に読まないのでreadAloud属性は出力しない
        assert element.get("readAloud") is None

    def test_transform_figure_returns_element(self) -> None:
        """戻り値はElement型"""
        from src.book_converter.models import Figure
        from src.book_converter.transformer import transform_figure

        figure = Figure(path="test.png")
        element = transform_figure(figure)

        assert isinstance(element, Element)

    def test_transform_figure_full(self) -> None:
        """全属性を持つ図を変換"""
        from src.book_converter.models import Figure
        from src.book_converter.transformer import transform_figure

        figure = Figure(
            path="images/architecture.png",
            caption="図2-1: システムアーキテクチャ",
            marker="図2-1",
        )
        element = transform_figure(figure)

        assert element.tag == "figure"
        assert element.get("path") == "images/architecture.png"
        assert element.get("caption") == "図2-1: システムアーキテクチャ"
        assert element.get("marker") == "図2-1"

    def test_transform_figure_xml_serialization(self) -> None:
        """XMLにシリアライズ可能"""
        from src.book_converter.models import Figure
        from src.book_converter.transformer import transform_figure

        figure = Figure(
            path="test.png",
            caption="テスト図",
        )
        element = transform_figure(figure)
        xml_string = tostring(element, encoding="unicode")

        assert "<figure" in xml_string
        assert 'path="test.png"' in xml_string
        assert 'caption="テスト図"' in xml_string

    def test_transform_figure_self_closing(self) -> None:
        """図要素は子要素を持たない（自己終了タグ）"""
        from src.book_converter.models import Figure
        from src.book_converter.transformer import transform_figure

        figure = Figure(path="large_diagram.png")
        element = transform_figure(figure)

        # 子要素がないことを確認
        assert len(list(element)) == 0

    def test_transform_figure_preserves_unicode(self) -> None:
        """Unicode文字を保持"""
        from src.book_converter.models import Figure
        from src.book_converter.transformer import transform_figure

        figure = Figure(
            path="日本語/図表.png",
            caption="日本語キャプション「テスト」",
            marker="図1",
        )
        element = transform_figure(figure)

        assert element.get("path") == "日本語/図表.png"
        assert "日本語キャプション" in element.get("caption")


class TestTransformPageMetadata:
    """T054: PageMetadata XML変換テスト (<pageMetadata type="chapter-page"> 生成)"""

    def test_transform_page_metadata_basic(self) -> None:
        """基本的なページメタデータをXMLに変換"""
        from src.book_converter.models import PageMetadata
        from src.book_converter.transformer import transform_page_metadata

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
        from src.book_converter.models import PageMetadata
        from src.book_converter.transformer import transform_page_metadata

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
        from src.book_converter.models import PageMetadata
        from src.book_converter.transformer import transform_page_metadata

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
        from src.book_converter.models import PageMetadata
        from src.book_converter.transformer import transform_page_metadata

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
        from src.book_converter.models import PageMetadata
        from src.book_converter.transformer import transform_page_metadata

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
        from src.book_converter.models import PageMetadata
        from src.book_converter.transformer import transform_page_metadata

        metadata = PageMetadata(text="1 / 5", current=1, total=5)
        element = transform_page_metadata(metadata)

        # pageMetadataはTTSで読み上げない
        assert element.get("readAloud") == "false"

    def test_transform_page_metadata_xml_serialization(self) -> None:
        """XMLにシリアライズ可能"""
        from src.book_converter.models import PageMetadata
        from src.book_converter.transformer import transform_page_metadata

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
        from src.book_converter.models import PageMetadata
        from src.book_converter.transformer import transform_page_metadata

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
    """T055: readAloud属性テスト (新形式)"""

    def test_figure_no_read_aloud(self) -> None:
        """figure要素はreadAloud属性を持たない（常に読まない）"""
        from src.book_converter.models import Figure
        from src.book_converter.transformer import transform_figure

        figure = Figure(path="test.png", caption="図1")
        element = transform_figure(figure)

        # 図は常に読まないのでreadAloud属性は出力しない
        assert element.get("readAloud") is None

    def test_page_metadata_always_read_aloud_false(self) -> None:
        """pageMetadataは常にreadAloud='false'"""
        from src.book_converter.models import PageMetadata
        from src.book_converter.transformer import transform_page_metadata

        metadata = PageMetadata(text="1 / 5", current=1, total=5)
        element = transform_page_metadata(metadata)

        # pageMetadataは本文読み上げに混入しない
        assert element.get("readAloud") == "false"

    def test_heading_read_aloud_default_true(self) -> None:
        """<heading>のreadAloudデフォルトはtrue（属性省略）"""
        from src.book_converter.transformer import transform_heading

        heading = Heading(level=1, text="タイトル")
        element = transform_heading(heading)

        # headingのデフォルトはtrue（属性省略）
        read_aloud = element.get("readAloud")
        assert read_aloud is None or read_aloud == "true"

    def test_heading_read_aloud_false_when_skipped(self) -> None:
        """skip区間内のheadingはreadAloud='false'"""
        from src.book_converter.transformer import transform_heading

        heading = Heading(level=1, text="スキップ対象", read_aloud=False)
        element = transform_heading(heading)

        # skip区間内ではreadAloud="false"を出力
        assert element.get("readAloud") == "false"


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
        from src.book_converter.models import Paragraph
        from src.book_converter.transformer import transform_content

        content = Content(elements=(Paragraph(text="段落テキスト"),))
        element = transform_content(content)
        para_elem = element.find("paragraph")

        # paragraphのデフォルトはtrue（省略可）
        read_aloud = para_elem.get("readAloud")
        assert read_aloud is None or read_aloud == "true"


# =============================================================================
# Phase 7: Emphasis Conversion - **強調** → <em>
# =============================================================================


class TestEmphasisConversion:
    """強調変換テスト: **text** → <em>text</em>"""

    def test_paragraph_with_single_emphasis(self) -> None:
        """単一の強調を含む段落を変換"""
        from src.book_converter.models import Paragraph
        from src.book_converter.transformer import transform_paragraph

        para = Paragraph(text="これは**強調**です。")
        element = transform_paragraph(para)

        # **強調** が <em>強調</em> に変換される
        em = element.find("em")
        assert em is not None
        assert em.text == "強調"

    def test_paragraph_with_multiple_emphasis(self) -> None:
        """複数の強調を含む段落を変換"""
        from src.book_converter.models import Paragraph
        from src.book_converter.transformer import transform_paragraph

        para = Paragraph(text="**最初**と**二番目**の強調")
        element = transform_paragraph(para)

        em_elems = element.findall("em")
        assert len(em_elems) == 2
        assert em_elems[0].text == "最初"
        assert em_elems[1].text == "二番目"

    def test_paragraph_without_emphasis(self) -> None:
        """強調なしの段落はそのまま"""
        from src.book_converter.models import Paragraph
        from src.book_converter.transformer import transform_paragraph

        para = Paragraph(text="通常のテキストです。")
        element = transform_paragraph(para)

        # emは生成されない
        assert element.find("em") is None
        assert element.text == "通常のテキストです。"

    def test_paragraph_emphasis_preserves_surrounding_text(self) -> None:
        """強調の前後のテキストを保持"""
        from src.book_converter.models import Paragraph
        from src.book_converter.transformer import transform_paragraph

        para = Paragraph(text="前のテキスト**強調**後のテキスト")
        element = transform_paragraph(para)

        # 前のテキストはelement.text
        assert element.text == "前のテキスト"
        # 強調
        em = element.find("em")
        assert em.text == "強調"
        # 後のテキストはem.tail
        assert em.tail == "後のテキスト"

    def test_heading_with_emphasis(self) -> None:
        """強調を含む見出しを変換"""
        from src.book_converter.transformer import transform_heading

        heading = Heading(level=1, text="**重要な**見出し")
        element = transform_heading(heading)

        em = element.find("em")
        assert em is not None
        assert em.text == "重要な"
        assert em.tail == "見出し"

    def test_list_item_with_emphasis(self) -> None:
        """強調を含むリストアイテムを変換"""
        from src.book_converter.models import List
        from src.book_converter.transformer import transform_list

        lst = List(items=("**重要**な項目", "通常の項目"))
        element = transform_list(lst)
        items = element.findall("item")

        # 最初のアイテムに強調がある
        em = items[0].find("em")
        assert em is not None
        assert em.text == "重要"
        assert em.tail == "な項目"

        # 2番目は強調なし
        assert items[1].find("em") is None
        assert items[1].text == "通常の項目"

    def test_emphasis_unicode_content(self) -> None:
        """Unicode文字を含む強調を変換"""
        from src.book_converter.models import Paragraph
        from src.book_converter.transformer import transform_paragraph

        para = Paragraph(text="**日本語「テスト」**を含む")
        element = transform_paragraph(para)

        em = element.find("em")
        assert em.text == "日本語「テスト」"

    def test_emphasis_xml_serialization(self) -> None:
        """強調を含む要素をXMLにシリアライズ"""
        from src.book_converter.models import Paragraph
        from src.book_converter.transformer import transform_paragraph

        para = Paragraph(text="テスト**強調**です")
        element = transform_paragraph(para)
        xml_string = tostring(element, encoding="unicode")

        assert "<em>" in xml_string
        assert "</em>" in xml_string
        assert "強調" in xml_string

    def test_full_emphasis_only(self) -> None:
        """テキスト全体が強調の場合"""
        from src.book_converter.models import Paragraph
        from src.book_converter.transformer import transform_paragraph

        para = Paragraph(text="**全体が強調**")
        element = transform_paragraph(para)

        # テキスト部分は空またはNone
        assert element.text is None or element.text == ""
        em = element.find("em")
        assert em.text == "全体が強調"

    def test_page_metadata_emphasis_preserved(self) -> None:
        """pageMetadata内の強調も変換"""
        from src.book_converter.models import PageMetadata
        from src.book_converter.transformer import transform_page_metadata

        metadata = PageMetadata(
            text="**はじめに** 1 / 3",
            meta_type="chapter-page",
            section_name="はじめに",
            current=1,
            total=3,
        )
        element = transform_page_metadata(metadata)

        # pageMetadata内の強調も変換される
        em = element.find("em")
        assert em is not None
        assert em.text == "はじめに"


# =============================================================================
# Phase 2 (004-toc-structure): US1+US2 目次マーカー認識と構造化
# =============================================================================


class TestTransformTableOfContents:
    """T016: toc変換テスト (transform_table_of_contents)

    US1: 目次マーカーによる目次認識
    - <toc>要素が生成される
    """

    def test_transform_table_of_contents_basic(self) -> None:
        """基本的な目次をXMLに変換"""
        from src.book_converter.models import TableOfContents, TocEntry
        from src.book_converter.transformer import transform_table_of_contents

        entry = TocEntry(text="第1章", level="chapter", number="1", page="15")
        toc = TableOfContents(entries=(entry,), begin_page="1", end_page="1")

        element = transform_table_of_contents(toc)

        assert element is not None
        assert element.tag == "toc"
        assert element.get("begin") == "1"
        assert element.get("end") == "1"

    def test_transform_table_of_contents_returns_element(self) -> None:
        """戻り値はElement型"""
        from src.book_converter.models import TableOfContents, TocEntry
        from src.book_converter.transformer import transform_table_of_contents

        entry = TocEntry(text="テスト", level="chapter")
        toc = TableOfContents(entries=(entry,))

        element = transform_table_of_contents(toc)

        assert isinstance(element, Element)

    def test_transform_table_of_contents_contains_entries(self) -> None:
        """目次にエントリが含まれる"""
        from src.book_converter.models import TableOfContents, TocEntry
        from src.book_converter.transformer import transform_table_of_contents

        entry1 = TocEntry(text="第1章", level="chapter", number="1", page="15")
        entry2 = TocEntry(text="1.1 節", level="section", number="1.1", page="20")
        toc = TableOfContents(entries=(entry1, entry2))

        element = transform_table_of_contents(toc)

        entries = element.findall("entry")
        assert len(entries) == 2

    def test_transform_table_of_contents_multiple_entries(self) -> None:
        """複数エントリの目次を変換"""
        from src.book_converter.models import TableOfContents, TocEntry
        from src.book_converter.transformer import transform_table_of_contents

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
        from src.book_converter.models import TableOfContents, TocEntry
        from src.book_converter.transformer import transform_table_of_contents

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
        from src.book_converter.models import TableOfContents, TocEntry
        from src.book_converter.transformer import transform_table_of_contents

        entry = TocEntry(text="テスト", level="chapter", number="1", page="10")
        toc = TableOfContents(entries=(entry,), begin_page="5", end_page="7")

        element = transform_table_of_contents(toc)
        xml_string = tostring(element, encoding="unicode")

        assert "<toc " in xml_string
        assert 'begin="5"' in xml_string
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
        from src.book_converter.models import TocEntry
        from src.book_converter.transformer import transform_toc_entry

        entry = TocEntry(text="SREとは", level="chapter", number="1", page="15")

        element = transform_toc_entry(entry)

        assert element is not None
        assert element.tag == "entry"

    def test_transform_toc_entry_level_attribute(self) -> None:
        """level属性が正しく設定される"""
        from src.book_converter.models import TocEntry
        from src.book_converter.transformer import transform_toc_entry

        entry = TocEntry(text="テスト", level="chapter", number="1", page="10")

        element = transform_toc_entry(entry)

        assert element.get("level") == "chapter"

    def test_transform_toc_entry_number_attribute(self) -> None:
        """number属性が正しく設定される"""
        from src.book_converter.models import TocEntry
        from src.book_converter.transformer import transform_toc_entry

        entry = TocEntry(text="テスト", level="section", number="2.1", page="20")

        element = transform_toc_entry(entry)

        assert element.get("number") == "2.1"

    def test_transform_toc_entry_title_attribute(self) -> None:
        """title属性が正しく設定される"""
        from src.book_converter.models import TocEntry
        from src.book_converter.transformer import transform_toc_entry

        entry = TocEntry(text="SREとは", level="chapter", number="1", page="15")

        element = transform_toc_entry(entry)

        assert element.get("title") == "SREとは"

    def test_transform_toc_entry_page_attribute(self) -> None:
        """page属性が正しく設定される"""
        from src.book_converter.models import TocEntry
        from src.book_converter.transformer import transform_toc_entry

        entry = TocEntry(text="テスト", level="chapter", number="1", page="42")

        element = transform_toc_entry(entry)

        assert element.get("page") == "42"

    def test_transform_toc_entry_chapter(self) -> None:
        """chapter levelのエントリを変換"""
        from src.book_converter.models import TocEntry
        from src.book_converter.transformer import transform_toc_entry

        entry = TocEntry(text="SREとは", level="chapter", number="1", page="15")

        element = transform_toc_entry(entry)

        assert element.get("level") == "chapter"
        assert element.get("number") == "1"
        assert element.get("title") == "SREとは"
        assert element.get("page") == "15"

    def test_transform_toc_entry_section(self) -> None:
        """section levelのエントリを変換"""
        from src.book_converter.models import TocEntry
        from src.book_converter.transformer import transform_toc_entry

        entry = TocEntry(text="SLOの理解", level="section", number="2.1", page="30")

        element = transform_toc_entry(entry)

        assert element.get("level") == "section"
        assert element.get("number") == "2.1"
        assert element.get("title") == "SLOの理解"
        assert element.get("page") == "30"

    def test_transform_toc_entry_subsection(self) -> None:
        """subsection levelのエントリを変換"""
        from src.book_converter.models import TocEntry
        from src.book_converter.transformer import transform_toc_entry

        entry = TocEntry(text="SLA", level="subsection", number="2.1.1", page="35")

        element = transform_toc_entry(entry)

        assert element.get("level") == "subsection"
        assert element.get("number") == "2.1.1"
        assert element.get("title") == "SLA"
        assert element.get("page") == "35"

    def test_transform_toc_entry_other(self) -> None:
        """other levelのエントリを変換"""
        from src.book_converter.models import TocEntry
        from src.book_converter.transformer import transform_toc_entry

        entry = TocEntry(text="はじめに", level="other", page="1")

        element = transform_toc_entry(entry)

        assert element.get("level") == "other"
        assert element.get("title") == "はじめに"
        assert element.get("page") == "1"

    def test_transform_toc_entry_without_number(self) -> None:
        """number属性が空の場合"""
        from src.book_converter.models import TocEntry
        from src.book_converter.transformer import transform_toc_entry

        entry = TocEntry(text="はじめに", level="other", number="", page="1")

        element = transform_toc_entry(entry)

        # number属性は空文字または省略
        number = element.get("number")
        assert number is None or number == ""

    def test_transform_toc_entry_without_page(self) -> None:
        """page属性が空の場合"""
        from src.book_converter.models import TocEntry
        from src.book_converter.transformer import transform_toc_entry

        entry = TocEntry(text="テスト", level="chapter", number="1", page="")

        element = transform_toc_entry(entry)

        # page属性は空文字または省略
        page = element.get("page")
        assert page is None or page == ""

    def test_transform_toc_entry_returns_element(self) -> None:
        """戻り値はElement型"""
        from src.book_converter.models import TocEntry
        from src.book_converter.transformer import transform_toc_entry

        entry = TocEntry(text="テスト", level="chapter")

        element = transform_toc_entry(entry)

        assert isinstance(element, Element)

    def test_transform_toc_entry_preserves_unicode(self) -> None:
        """Unicode文字を保持"""
        from src.book_converter.models import TocEntry
        from src.book_converter.transformer import transform_toc_entry

        entry = TocEntry(text="日本語「テスト」", level="chapter", number="1", page="10")

        element = transform_toc_entry(entry)

        assert element.get("title") == "日本語「テスト」"

    def test_transform_toc_entry_xml_serialization(self) -> None:
        """XMLにシリアライズ可能"""
        from src.book_converter.models import TocEntry
        from src.book_converter.transformer import transform_toc_entry

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


class TestTableOfContentsPageRange:
    """T039: tocのbegin/end属性テスト

    US3: 目次の読み上げ制御
    - <toc>要素はbook直下に配置され、begin/end属性でページ範囲を示す
    - TOCはbook直下の2番目の子要素（metadata後）
    """

    def test_toc_has_begin_and_end_attributes(self) -> None:
        """tocにbegin/end属性が設定される"""
        from src.book_converter.models import TableOfContents, TocEntry
        from src.book_converter.transformer import transform_table_of_contents

        entry = TocEntry(text="第1章", level="chapter", number="1", page="15")
        toc = TableOfContents(entries=(entry,), begin_page="5", end_page="7")

        element = transform_table_of_contents(toc)

        assert element is not None
        assert element.tag == "toc"
        assert element.get("begin") == "5"
        assert element.get("end") == "7"

    def test_toc_without_page_range(self) -> None:
        """ページ範囲なしのTOC"""
        from src.book_converter.models import TableOfContents, TocEntry
        from src.book_converter.transformer import transform_table_of_contents

        entry = TocEntry(text="はじめに", level="other", page="1")
        toc = TableOfContents(entries=(entry,))

        element = transform_table_of_contents(toc)

        assert element is not None
        assert element.tag == "toc"
        # 空文字の場合は属性が設定されない
        assert element.get("begin") is None or element.get("begin") == ""
        assert element.get("end") is None or element.get("end") == ""

    def test_toc_xml_output_with_page_range(self) -> None:
        """XMLシリアライズ時にbegin/end属性が含まれる"""
        from src.book_converter.models import TableOfContents, TocEntry
        from src.book_converter.transformer import transform_table_of_contents

        entry = TocEntry(text="テスト", level="chapter", number="1", page="10")
        toc = TableOfContents(entries=(entry,), begin_page="3", end_page="5")

        element = transform_table_of_contents(toc)
        xml_string = tostring(element, encoding="unicode")

        assert 'begin="3"' in xml_string
        assert 'end="5"' in xml_string
        assert "<toc " in xml_string

    def test_toc_with_multiple_entries(self) -> None:
        """複数エントリのTOC"""
        from src.book_converter.models import TableOfContents, TocEntry
        from src.book_converter.transformer import transform_table_of_contents

        entries = (
            TocEntry(text="はじめに", level="other", page="1"),
            TocEntry(text="SREとは", level="chapter", number="1", page="15"),
            TocEntry(text="SREの定義", level="section", number="1.1", page="16"),
            TocEntry(text="歴史", level="subsection", number="1.1.1", page="17"),
            TocEntry(text="おわりに", level="other", page="300"),
        )
        toc = TableOfContents(entries=entries, begin_page="2", end_page="4")

        element = transform_table_of_contents(toc)

        assert element.tag == "toc"
        assert element.get("begin") == "2"
        assert element.get("end") == "4"
        # すべてのエントリが含まれている
        assert len(element.findall("entry")) == 5

    def test_empty_toc_returns_none(self) -> None:
        """空の目次はNoneを返す"""
        from src.book_converter.models import TableOfContents
        from src.book_converter.transformer import transform_table_of_contents

        toc = TableOfContents(entries=())

        element = transform_table_of_contents(toc)

        # 空のTOCはNoneを返す（エントリがない場合はTOCを出力しない）
        assert element is None


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
        from src.book_converter.models import Content, Paragraph
        from src.book_converter.transformer import transform_content

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
        from src.book_converter.models import Content, Paragraph
        from src.book_converter.transformer import transform_content

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
        from src.book_converter.models import Content, Heading
        from src.book_converter.transformer import transform_content

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
        from src.book_converter.models import Content, List
        from src.book_converter.transformer import transform_content

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
        from src.book_converter.models import Content, Paragraph
        from src.book_converter.transformer import transform_content

        content = Content(
            elements=(Paragraph(text="読み上げ対象テキスト", read_aloud=True),),
            read_aloud=True,
        )
        element = transform_content(content)

        assert element is not None
        assert element.get("readAloud") == "true"

    def test_paragraph_inside_content_marker_has_read_aloud_true(self) -> None:
        """contentマーカー内の段落はreadAloud=true"""
        from src.book_converter.models import Content, Paragraph
        from src.book_converter.transformer import transform_content

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
        from src.book_converter.models import Content, Heading
        from src.book_converter.transformer import transform_content

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
        from src.book_converter.models import Content, List
        from src.book_converter.transformer import transform_content

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
        from src.book_converter.models import Content, Heading, List, Paragraph
        from src.book_converter.transformer import transform_content

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
        from src.book_converter.models import Content, Paragraph
        from src.book_converter.transformer import transform_content

        content = Content(
            elements=(Paragraph(text="索引テキスト", read_aloud=False),),
            read_aloud=False,
        )
        element = transform_content(content)

        assert element is not None
        assert element.get("readAloud") == "false"

    def test_paragraph_inside_skip_marker_has_read_aloud_false(self) -> None:
        """skipマーカー内の段落はreadAloud=false"""
        from src.book_converter.models import Content, Paragraph
        from src.book_converter.transformer import transform_content

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
        from src.book_converter.models import Content, Paragraph
        from src.book_converter.transformer import transform_content

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
        from src.book_converter.models import Content, Paragraph
        from src.book_converter.transformer import transform_content

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
        from src.book_converter.models import Content, Paragraph
        from src.book_converter.transformer import transform_content

        content = Content(
            elements=(Paragraph(text="テスト", read_aloud=True),),
            read_aloud=True,
        )
        element = transform_content(content)
        xml_string = tostring(element, encoding="unicode")

        assert 'readAloud="true"' in xml_string

    def test_content_read_aloud_false_in_xml(self) -> None:
        """readAloud="false"がXMLに出力される"""
        from src.book_converter.models import Content, Paragraph
        from src.book_converter.transformer import transform_content

        content = Content(
            elements=(Paragraph(text="テスト", read_aloud=False),),
            read_aloud=False,
        )
        element = transform_content(content)
        xml_string = tostring(element, encoding="unicode")

        assert 'readAloud="false"' in xml_string

    def test_paragraph_read_aloud_true_in_xml(self) -> None:
        """段落のreadAloud="true"がXMLに出力される"""
        from src.book_converter.models import Content, Paragraph
        from src.book_converter.transformer import transform_content

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
        from src.book_converter.models import Content, Paragraph
        from src.book_converter.transformer import transform_content

        content = Content(
            elements=(Paragraph(text="テスト", read_aloud=False),),
            read_aloud=False,
        )
        element = transform_content(content)
        para_elem = element.find("paragraph")
        xml_string = tostring(para_elem, encoding="unicode")

        assert 'readAloud="false"' in xml_string


# =============================================================================
# Phase 2 (009-converter-redesign): T011 TOC XML出力テスト
# =============================================================================


class TestTransformTocEntryLevelNumeric:
    """T011: TOC XML出力テスト (transform_toc_entry level数値文字列)

    User Story 1 - TOC階層構造の正確な反映
    transform_toc_entry が level="1" 等の数値文字列を出力することを確認
    """

    def test_transform_toc_entry_level_numeric_1(self) -> None:
        """transform_toc_entry が level="1" を出力する"""
        from src.book_converter.models import TocEntry
        from src.book_converter.transformer import transform_toc_entry

        entry = TocEntry(
            text="Chapter 1 タイトル",
            level=1,
            number="1",
            page="15",
        )

        element = transform_toc_entry(entry)

        assert element is not None
        assert element.get("level") == "1"

    def test_transform_toc_entry_level_numeric_2(self) -> None:
        """transform_toc_entry が level="2" を出力する"""
        from src.book_converter.models import TocEntry
        from src.book_converter.transformer import transform_toc_entry

        entry = TocEntry(
            text="Section タイトル",
            level=2,
            number="1.1",
            page="20",
        )

        element = transform_toc_entry(entry)

        assert element is not None
        assert element.get("level") == "2"

    def test_transform_toc_entry_level_numeric_3(self) -> None:
        """transform_toc_entry が level="3" を出力する"""
        from src.book_converter.models import TocEntry
        from src.book_converter.transformer import transform_toc_entry

        entry = TocEntry(
            text="Subsection タイトル",
            level=3,
            number="1.1.1",
            page="25",
        )

        element = transform_toc_entry(entry)

        assert element is not None
        assert element.get("level") == "3"

    def test_transform_toc_entry_level_numeric_4(self) -> None:
        """transform_toc_entry が level="4" を出力する"""
        from src.book_converter.models import TocEntry
        from src.book_converter.transformer import transform_toc_entry

        entry = TocEntry(
            text="深い階層の見出し",
            level=4,
            number="1.1.1.1",
            page="30",
        )

        element = transform_toc_entry(entry)

        assert element is not None
        assert element.get("level") == "4"

    def test_transform_toc_entry_level_numeric_5(self) -> None:
        """transform_toc_entry が level="5" を出力する"""
        from src.book_converter.models import TocEntry
        from src.book_converter.transformer import transform_toc_entry

        entry = TocEntry(
            text="最深階層の見出し",
            level=5,
            number="1.1.1.1.1",
            page="35",
        )

        element = transform_toc_entry(entry)

        assert element is not None
        assert element.get("level") == "5"

    def test_transform_toc_entry_level_not_chapter_string(self) -> None:
        """transform_toc_entry が level="chapter" ではなく数値文字列を出力する"""
        from src.book_converter.models import TocEntry
        from src.book_converter.transformer import transform_toc_entry

        entry = TocEntry(
            text="テスト",
            level=1,
            number="1",
            page="10",
        )

        element = transform_toc_entry(entry)

        assert element is not None
        # "chapter" ではなく "1" を出力
        assert element.get("level") != "chapter"
        assert element.get("level") == "1"

    def test_transform_toc_entry_level_not_section_string(self) -> None:
        """transform_toc_entry が level="section" ではなく数値文字列を出力する"""
        from src.book_converter.models import TocEntry
        from src.book_converter.transformer import transform_toc_entry

        entry = TocEntry(
            text="テスト",
            level=2,
            number="1.1",
            page="10",
        )

        element = transform_toc_entry(entry)

        assert element is not None
        # "section" ではなく "2" を出力
        assert element.get("level") != "section"
        assert element.get("level") == "2"

    def test_transform_toc_entry_level_numeric_xml_serialization(self) -> None:
        """数値レベルがXMLにシリアライズされる"""
        from src.book_converter.models import TocEntry
        from src.book_converter.transformer import transform_toc_entry

        entry = TocEntry(
            text="SREとは",
            level=1,
            number="1",
            page="15",
        )

        element = transform_toc_entry(entry)
        xml_string = tostring(element, encoding="unicode")

        # level="1" がXMLに含まれる
        assert 'level="1"' in xml_string
        # level="chapter" は含まれない
        assert 'level="chapter"' not in xml_string

    def test_transform_toc_entry_all_levels_xml_serialization(self) -> None:
        """全レベル（1-5）がXMLにシリアライズされる"""
        from src.book_converter.models import TocEntry
        from src.book_converter.transformer import transform_toc_entry

        for level in range(1, 6):
            entry = TocEntry(
                text=f"Level {level} 見出し",
                level=level,
                number=str(level),
                page=str(level * 10),
            )

            element = transform_toc_entry(entry)
            xml_string = tostring(element, encoding="unicode")

            assert f'level="{level}"' in xml_string

    def test_transform_toc_entry_preserves_other_attributes(self) -> None:
        """数値レベル出力時に他の属性も保持される"""
        from src.book_converter.models import TocEntry
        from src.book_converter.transformer import transform_toc_entry

        entry = TocEntry(
            text="日本語タイトル",
            level=2,
            number="1.1",
            page="25",
        )

        element = transform_toc_entry(entry)

        assert element.get("level") == "2"
        assert element.get("title") == "日本語タイトル"
        assert element.get("number") == "1.1"
        assert element.get("page") == "25"

    def test_transform_table_of_contents_with_numeric_levels(self) -> None:
        """transform_table_of_contents が数値レベルを持つエントリを変換する"""
        from src.book_converter.models import TableOfContents, TocEntry
        from src.book_converter.transformer import transform_table_of_contents

        entries = (
            TocEntry(text="Chapter 1", level=1, number="1", page="10"),
            TocEntry(text="Section 1.1", level=2, number="1.1", page="11"),
            TocEntry(text="Subsection 1.1.1", level=3, number="1.1.1", page="12"),
        )
        toc = TableOfContents(entries=entries)

        element = transform_table_of_contents(toc)

        assert element is not None
        entry_elems = element.findall("entry")
        assert len(entry_elems) == 3

        assert entry_elems[0].get("level") == "1"
        assert entry_elems[1].get("level") == "2"
        assert entry_elems[2].get("level") == "3"


# =============================================================================
# Phase 3 (009-converter-redesign): T025 構造コンテナ変換テスト
# =============================================================================


class TestTransformStructureContainer:
    """T025: 構造コンテナ変換テスト (transform_structure_container)

    User Story 2 - chapter/heading タグの役割明確化
    StructureContainer を chapter/section/subsection XML要素に変換
    """

    def test_transform_structure_container_exists(self) -> None:
        """transform_structure_container 関数が存在する"""
        from src.book_converter.transformer import transform_structure_container

        assert transform_structure_container is not None

    def test_transform_structure_container_chapter_basic(self) -> None:
        """chapter コンテナを <chapter> 要素に変換"""
        from src.book_converter.models import StructureContainer
        from src.book_converter.transformer import transform_structure_container

        container = StructureContainer(
            container_type="chapter",
            level=1,
            number="1",
            title="Chapter Title",
            children=(),
        )

        element = transform_structure_container(container)

        assert element is not None
        assert element.tag == "chapter"

    def test_transform_structure_container_chapter_number_attribute(self) -> None:
        """chapter 要素に number 属性が設定される"""
        from src.book_converter.models import StructureContainer
        from src.book_converter.transformer import transform_structure_container

        container = StructureContainer(
            container_type="chapter",
            level=1,
            number="2",
            title="Second Chapter",
            children=(),
        )

        element = transform_structure_container(container)

        assert element.get("number") == "2"

    def test_transform_structure_container_chapter_title_attribute(self) -> None:
        """chapter 要素に title 属性が設定される"""
        from src.book_converter.models import StructureContainer
        from src.book_converter.transformer import transform_structure_container

        container = StructureContainer(
            container_type="chapter",
            level=1,
            number="1",
            title="Introduction to SRE",
            children=(),
        )

        element = transform_structure_container(container)

        assert element.get("title") == "Introduction to SRE"

    def test_transform_structure_container_section(self) -> None:
        """section コンテナを <section> 要素に変換"""
        from src.book_converter.models import StructureContainer
        from src.book_converter.transformer import transform_structure_container

        container = StructureContainer(
            container_type="section",
            level=2,
            number="1",
            title="Episode Title",
            children=(),
        )

        element = transform_structure_container(container)

        assert element is not None
        assert element.tag == "section"
        assert element.get("number") == "1"
        assert element.get("title") == "Episode Title"

    def test_transform_structure_container_subsection_level_3(self) -> None:
        """subsection (level 3) コンテナを <subsection> 要素に変換"""
        from src.book_converter.models import StructureContainer
        from src.book_converter.transformer import transform_structure_container

        container = StructureContainer(
            container_type="subsection",
            level=3,
            number="1.1",
            title="Subsection Title",
            children=(),
        )

        element = transform_structure_container(container)

        assert element is not None
        assert element.tag == "subsection"
        assert element.get("level") == "3"

    def test_transform_structure_container_subsection_level_4(self) -> None:
        """subsection (level 4) コンテナに level 属性が設定される"""
        from src.book_converter.models import StructureContainer
        from src.book_converter.transformer import transform_structure_container

        container = StructureContainer(
            container_type="subsection",
            level=4,
            number="1.1.1",
            title="Deep Subsection",
            children=(),
        )

        element = transform_structure_container(container)

        assert element is not None
        assert element.tag == "subsection"
        assert element.get("level") == "4"

    def test_transform_structure_container_subsection_level_5(self) -> None:
        """subsection (level 5) コンテナに level 属性が設定される"""
        from src.book_converter.models import StructureContainer
        from src.book_converter.transformer import transform_structure_container

        container = StructureContainer(
            container_type="subsection",
            level=5,
            number="1.1.1.1",
            title="Deepest Subsection",
            children=(),
        )

        element = transform_structure_container(container)

        assert element is not None
        assert element.tag == "subsection"
        assert element.get("level") == "5"

    def test_transform_structure_container_with_paragraph_child(self) -> None:
        """コンテナに段落を子要素として含める"""
        from src.book_converter.models import Paragraph, StructureContainer
        from src.book_converter.transformer import transform_structure_container

        paragraph = Paragraph(text="This is paragraph text.")

        container = StructureContainer(
            container_type="chapter",
            level=1,
            number="1",
            title="Chapter with Paragraph",
            children=(paragraph,),
        )

        element = transform_structure_container(container)

        para_elem = element.find("paragraph")
        assert para_elem is not None
        assert para_elem.text == "This is paragraph text."

    def test_transform_structure_container_with_heading_child(self) -> None:
        """コンテナに見出しを子要素として含める"""
        from src.book_converter.models import Heading, StructureContainer
        from src.book_converter.transformer import transform_structure_container

        heading = Heading(level=1, text="Chapter 1 Title", read_aloud=True)

        container = StructureContainer(
            container_type="chapter",
            level=1,
            number="1",
            title="Chapter Title",
            children=(heading,),
        )

        element = transform_structure_container(container)

        heading_elem = element.find("heading")
        assert heading_elem is not None
        assert heading_elem.text == "Chapter 1 Title"

    def test_transform_structure_container_nested_structure(self) -> None:
        """入れ子構造: chapter > section"""
        from src.book_converter.models import StructureContainer
        from src.book_converter.transformer import transform_structure_container

        section = StructureContainer(
            container_type="section",
            level=2,
            number="1",
            title="Section Title",
            children=(),
        )

        chapter = StructureContainer(
            container_type="chapter",
            level=1,
            number="1",
            title="Chapter Title",
            children=(section,),
        )

        element = transform_structure_container(chapter)

        assert element.tag == "chapter"
        section_elem = element.find("section")
        assert section_elem is not None
        assert section_elem.get("number") == "1"
        assert section_elem.get("title") == "Section Title"

    def test_transform_structure_container_deep_nesting(self) -> None:
        """深い入れ子構造: chapter > section > subsection"""
        from src.book_converter.models import StructureContainer
        from src.book_converter.transformer import transform_structure_container

        subsection = StructureContainer(
            container_type="subsection",
            level=3,
            number="1",
            title="Subsection Title",
            children=(),
        )

        section = StructureContainer(
            container_type="section",
            level=2,
            number="1",
            title="Section Title",
            children=(subsection,),
        )

        chapter = StructureContainer(
            container_type="chapter",
            level=1,
            number="1",
            title="Chapter Title",
            children=(section,),
        )

        element = transform_structure_container(chapter)

        assert element.tag == "chapter"
        section_elem = element.find("section")
        assert section_elem is not None
        subsection_elem = section_elem.find("subsection")
        assert subsection_elem is not None
        assert subsection_elem.get("level") == "3"

    def test_transform_structure_container_unicode_title(self) -> None:
        """Unicode タイトルが正しく変換される"""
        from src.book_converter.models import StructureContainer
        from src.book_converter.transformer import transform_structure_container

        container = StructureContainer(
            container_type="chapter",
            level=1,
            number="1",
            title="日本語タイトル「テスト」",
            children=(),
        )

        element = transform_structure_container(container)

        assert element.get("title") == "日本語タイトル「テスト」"

    def test_transform_structure_container_empty_number(self) -> None:
        """空の number は属性を出力しないまたは空文字列"""
        from src.book_converter.models import StructureContainer
        from src.book_converter.transformer import transform_structure_container

        container = StructureContainer(
            container_type="chapter",
            level=1,
            number="",
            title="Preface",
            children=(),
        )

        element = transform_structure_container(container)

        # number が空の場合は属性なしまたは空文字列
        number = element.get("number")
        assert number is None or number == ""

    def test_transform_structure_container_returns_element(self) -> None:
        """戻り値は Element 型"""
        from src.book_converter.models import StructureContainer
        from src.book_converter.transformer import transform_structure_container

        container = StructureContainer(
            container_type="chapter",
            level=1,
            number="1",
            title="Test",
            children=(),
        )

        element = transform_structure_container(container)

        assert isinstance(element, Element)

    def test_transform_structure_container_xml_serialization(self) -> None:
        """XML にシリアライズ可能"""
        from src.book_converter.models import StructureContainer
        from src.book_converter.transformer import transform_structure_container

        container = StructureContainer(
            container_type="chapter",
            level=1,
            number="1",
            title="Chapter Title",
            children=(),
        )

        element = transform_structure_container(container)
        xml_string = tostring(element, encoding="unicode")

        assert "<chapter " in xml_string
        assert 'number="1"' in xml_string
        assert 'title="Chapter Title"' in xml_string

    def test_transform_structure_container_complete_example(self) -> None:
        """完全な例: chapter > heading + section > heading + paragraph"""
        from src.book_converter.models import Heading, Paragraph, StructureContainer
        from src.book_converter.transformer import transform_structure_container

        section = StructureContainer(
            container_type="section",
            level=2,
            number="1",
            title="Episode Title",
            children=(
                Heading(level=2, text="Episode 01 Episode Title", read_aloud=True),
                Paragraph(text="Section content."),
            ),
        )

        chapter = StructureContainer(
            container_type="chapter",
            level=1,
            number="1",
            title="Chapter Title",
            children=(
                Heading(level=1, text="Chapter 1 Chapter Title", read_aloud=True),
                section,
            ),
        )

        element = transform_structure_container(chapter)

        # chapter 構造
        assert element.tag == "chapter"
        assert element.get("number") == "1"
        assert element.get("title") == "Chapter Title"

        # chapter 直下の heading
        chapter_heading = element.find("heading")
        assert chapter_heading is not None
        assert chapter_heading.text == "Chapter 1 Chapter Title"

        # section 構造
        section_elem = element.find("section")
        assert section_elem is not None
        assert section_elem.get("number") == "1"

        # section 内の heading
        section_heading = section_elem.find("heading")
        assert section_heading is not None
        assert section_heading.text == "Episode 01 Episode Title"

        # section 内の paragraph
        para = section_elem.find("paragraph")
        assert para is not None


# =============================================================================
# Phase 3 (009-converter-redesign): T027 heading readAloud属性テスト
# =============================================================================


class TestHeadingReadAloudInStructureContainer:
    """T027: heading readAloud属性テスト

    User Story 2 - chapter/heading タグの役割明確化
    構造コンテナ内の heading 要素は readAloud="true" を出力する
    """

    def test_heading_in_structure_container_has_read_aloud_true(self) -> None:
        """構造コンテナ内の heading は readAloud="true" を出力"""
        from src.book_converter.models import Heading, StructureContainer
        from src.book_converter.transformer import transform_structure_container

        container = StructureContainer(
            container_type="chapter",
            level=1,
            number="1",
            title="Chapter Title",
            children=(Heading(level=1, text="Chapter 1 Title", read_aloud=True),),
        )

        element = transform_structure_container(container)

        heading_elem = element.find("heading")
        assert heading_elem is not None
        assert heading_elem.get("readAloud") == "true"

    def test_heading_read_aloud_true_attribute_value(self) -> None:
        """readAloud 属性の値は "true" 文字列"""
        from src.book_converter.models import Heading, StructureContainer
        from src.book_converter.transformer import transform_structure_container

        container = StructureContainer(
            container_type="section",
            level=2,
            number="1",
            title="Section Title",
            children=(Heading(level=2, text="Section 1 Title", read_aloud=True),),
        )

        element = transform_structure_container(container)

        heading_elem = element.find("heading")
        assert heading_elem is not None
        # 属性値は文字列 "true"
        assert heading_elem.get("readAloud") == "true"

    def test_heading_in_nested_structure_has_read_aloud_true(self) -> None:
        """入れ子構造内の heading も readAloud='true'"""
        from src.book_converter.models import Heading, StructureContainer
        from src.book_converter.transformer import transform_structure_container

        section = StructureContainer(
            container_type="section",
            level=2,
            number="1",
            title="Section Title",
            children=(Heading(level=2, text="Episode 01 Title", read_aloud=True),),
        )

        chapter = StructureContainer(
            container_type="chapter",
            level=1,
            number="1",
            title="Chapter Title",
            children=(
                Heading(level=1, text="Chapter 1 Title", read_aloud=True),
                section,
            ),
        )

        element = transform_structure_container(chapter)

        # chapter 直下の heading
        chapter_heading = element.find("heading")
        assert chapter_heading is not None
        assert chapter_heading.get("readAloud") == "true"

        # section 内の heading
        section_elem = element.find("section")
        section_heading = section_elem.find("heading")
        assert section_heading is not None
        assert section_heading.get("readAloud") == "true"

    def test_heading_read_aloud_xml_serialization(self) -> None:
        """readAloud 属性が XML にシリアライズされる"""
        from src.book_converter.models import Heading, StructureContainer
        from src.book_converter.transformer import transform_structure_container

        container = StructureContainer(
            container_type="chapter",
            level=1,
            number="1",
            title="Chapter Title",
            children=(Heading(level=1, text="Chapter 1 Title", read_aloud=True),),
        )

        element = transform_structure_container(container)
        xml_string = tostring(element, encoding="unicode")

        assert 'readAloud="true"' in xml_string

    def test_heading_text_preserved_in_structure_container(self) -> None:
        """heading テキストが構造コンテナ内で保持される"""
        from src.book_converter.models import Heading, StructureContainer
        from src.book_converter.transformer import transform_structure_container

        container = StructureContainer(
            container_type="chapter",
            level=1,
            number="1",
            title="Chapter Title",
            children=(Heading(level=1, text="Chapter 1 Introduction to Python", read_aloud=True),),
        )

        element = transform_structure_container(container)

        heading_elem = element.find("heading")
        assert heading_elem is not None
        assert heading_elem.text == "Chapter 1 Introduction to Python"

    def test_heading_unicode_text_with_read_aloud(self) -> None:
        """Unicode テキストの heading に readAloud 属性"""
        from src.book_converter.models import Heading, StructureContainer
        from src.book_converter.transformer import transform_structure_container

        container = StructureContainer(
            container_type="chapter",
            level=1,
            number="1",
            title="日本語タイトル",
            children=(Heading(level=1, text="第1章 日本語タイトル「テスト」", read_aloud=True),),
        )

        element = transform_structure_container(container)

        heading_elem = element.find("heading")
        assert heading_elem is not None
        assert heading_elem.text == "第1章 日本語タイトル「テスト」"
        assert heading_elem.get("readAloud") == "true"

    def test_multiple_headings_in_structure_container(self) -> None:
        """複数の heading が全て readAloud="true" を持つ"""
        from src.book_converter.models import Heading, Paragraph, StructureContainer
        from src.book_converter.transformer import transform_structure_container

        container = StructureContainer(
            container_type="chapter",
            level=1,
            number="1",
            title="Chapter Title",
            children=(
                Heading(level=1, text="Main Heading", read_aloud=True),
                Paragraph(text="Some text."),
                Heading(level=2, text="Subheading", read_aloud=True),
            ),
        )

        element = transform_structure_container(container)

        headings = element.findall("heading")
        assert len(headings) == 2

        for h in headings:
            assert h.get("readAloud") == "true"

    def test_heading_without_read_aloud_gets_false(self) -> None:
        """read_aloud=False の heading は readAloud="false" を出力"""
        from src.book_converter.models import Heading, StructureContainer
        from src.book_converter.transformer import transform_structure_container

        container = StructureContainer(
            container_type="chapter",
            level=1,
            number="1",
            title="Chapter Title",
            children=(Heading(level=1, text="Non-readable heading", read_aloud=False),),
        )

        element = transform_structure_container(container)

        heading_elem = element.find("heading")
        assert heading_elem is not None
        assert heading_elem.get("readAloud") == "false"

    def test_heading_read_aloud_mixed_values(self) -> None:
        """read_aloud が混在する場合、各 heading が正しい値を持つ"""
        from src.book_converter.models import Heading, StructureContainer
        from src.book_converter.transformer import transform_structure_container

        container = StructureContainer(
            container_type="chapter",
            level=1,
            number="1",
            title="Chapter Title",
            children=(
                Heading(level=1, text="Readable heading", read_aloud=True),
                Heading(level=2, text="Non-readable heading", read_aloud=False),
            ),
        )

        element = transform_structure_container(container)

        headings = element.findall("heading")
        assert len(headings) == 2
        assert headings[0].get("readAloud") == "true"
        assert headings[1].get("readAloud") == "false"


# =============================================================================
# Phase 5 (009-converter-redesign): T058 リスト変換テスト
# =============================================================================


class TestTransformListType:
    """T058: リスト変換テスト

    User Story 4 - list要素の出力
    transform_list が <list><item>...</item></list> を出力
    """

    def test_transform_list_exists(self) -> None:
        """transform_list 関数が存在する"""
        from src.book_converter.transformer import transform_list

        assert callable(transform_list)

    def test_transform_list_basic(self) -> None:
        """基本的なリストを変換"""
        from src.book_converter.models import List
        from src.book_converter.transformer import transform_list

        lst = List(items=("項目1", "項目2"))
        element = transform_list(lst)

        assert element.tag == "list"

    def test_transform_list_read_aloud_default(self) -> None:
        """リストのreadAloudデフォルト（属性省略=true）"""
        from src.book_converter.models import List
        from src.book_converter.transformer import transform_list

        lst = List(items=("手順1", "手順2"))
        element = transform_list(lst)

        # デフォルトは読む（readAloud属性は出力しない）
        assert element.get("readAloud") is None

    def test_transform_list_has_item_children(self) -> None:
        """リスト要素は <item> 子要素を持つ"""
        from src.book_converter.models import List
        from src.book_converter.transformer import transform_list

        lst = List(items=("item1", "item2", "item3"), list_type="unordered")
        element = transform_list(lst)

        items = element.findall("item")
        assert len(items) == 3
        assert items[0].text == "item1"
        assert items[1].text == "item2"
        assert items[2].text == "item3"

    def test_transform_list_xml_format(self) -> None:
        """XML出力形式が正しい"""
        from xml.etree.ElementTree import tostring

        from src.book_converter.models import List
        from src.book_converter.transformer import transform_list

        lst = List(items=("項目A", "項目B"))
        element = transform_list(lst)
        xml_string = tostring(element, encoding="unicode")

        assert "<list>" in xml_string
        assert "<item>項目A</item>" in xml_string
        assert "<item>項目B</item>" in xml_string
        assert "</list>" in xml_string

    def test_transform_list_read_aloud_false(self) -> None:
        """skip区間内のリストはreadAloud='false'"""
        from xml.etree.ElementTree import tostring

        from src.book_converter.models import List
        from src.book_converter.transformer import transform_list

        lst = List(items=("手順1", "手順2"), read_aloud=False)
        element = transform_list(lst)
        xml_string = tostring(element, encoding="unicode")

        assert 'readAloud="false"' in xml_string

    def test_transform_list_empty_items(self) -> None:
        """空のリストを変換"""
        from src.book_converter.models import List
        from src.book_converter.transformer import transform_list

        lst = List(items=())
        element = transform_list(lst)

        assert element.tag == "list"
        items = element.findall("item")
        assert len(items) == 0

    def test_transform_list_unicode_items(self) -> None:
        """Unicode 項目を含むリストを変換"""
        from src.book_converter.models import List
        from src.book_converter.transformer import transform_list

        lst = List(
            items=("日本語項目", "特殊文字<>&\"'"),
        )
        element = transform_list(lst)

        items = element.findall("item")
        assert len(items) == 2
        assert items[0].text == "日本語項目"

    def test_transform_list_single_item(self) -> None:
        """単一項目のリストを変換"""
        from src.book_converter.models import List
        from src.book_converter.transformer import transform_list

        lst = List(items=("単一項目",), list_type="ordered")
        element = transform_list(lst)

        items = element.findall("item")
        assert len(items) == 1
        assert items[0].text == "単一項目"

    def test_transform_list_returns_element(self) -> None:
        """戻り値は Element 型"""
        from xml.etree.ElementTree import Element

        from src.book_converter.models import List
        from src.book_converter.transformer import transform_list

        lst = List(items=("item",), list_type="unordered")
        element = transform_list(lst)

        assert isinstance(element, Element)


# =============================================================================
# Phase 5 (009-converter-redesign): T061 figure XML出力テスト
# =============================================================================


class TestTransformFigureNewFormat:
    """T061: figure XML出力テスト（新形式）

    User Story 4 - list/figure要素の出力
    <figure path="..." marker="..." caption="..." /> 形式
    """

    def test_transform_figure_new_format_path_attribute(self) -> None:
        """figure 要素は path 属性を持つ"""
        from src.book_converter.models import Figure
        from src.book_converter.transformer import transform_figure

        fig = Figure(path="figures/fig001.png")
        element = transform_figure(fig)

        assert element.tag == "figure"
        assert element.get("path") == "figures/fig001.png"

    def test_transform_figure_new_format_marker_attribute(self) -> None:
        """figure 要素は marker 属性を持つ"""
        from src.book_converter.models import Figure
        from src.book_converter.transformer import transform_figure

        fig = Figure(path="figures/fig001.png", marker="図1")
        element = transform_figure(fig)

        assert element.get("marker") == "図1"

    def test_transform_figure_no_read_aloud_attribute(self) -> None:
        """figure 要素は readAloud 属性を持たない（常に読まない）"""
        from src.book_converter.models import Figure
        from src.book_converter.transformer import transform_figure

        fig = Figure(path="figures/fig001.png")
        element = transform_figure(fig)

        # 図は常に読まないので readAloud 属性は出力しない
        assert element.get("readAloud") is None

    def test_transform_figure_new_format_xml(self) -> None:
        """XML出力形式が正しい"""
        from xml.etree.ElementTree import tostring

        from src.book_converter.models import Figure
        from src.book_converter.transformer import transform_figure

        fig = Figure(path="figures/fig001.png", marker="図1")
        element = transform_figure(fig)
        xml_string = tostring(element, encoding="unicode")

        # 新形式の属性ベース出力（readAloudなし）
        assert 'path="figures/fig001.png"' in xml_string
        assert 'marker="図1"' in xml_string

    def test_transform_figure_without_marker(self) -> None:
        """marker なしの figure を変換"""
        from xml.etree.ElementTree import tostring

        from src.book_converter.models import Figure
        from src.book_converter.transformer import transform_figure

        fig = Figure(path="figures/fig001.png")
        element = transform_figure(fig)
        xml_string = tostring(element, encoding="unicode")

        # path 属性は必須
        assert 'path="figures/fig001.png"' in xml_string
        # marker は空文字列またはなし
        # marker="" または marker 属性なし

    def test_transform_figure_path_required(self) -> None:
        """path 属性は必須"""
        from src.book_converter.models import Figure
        from src.book_converter.transformer import transform_figure

        fig = Figure(path="figures/image.png")
        element = transform_figure(fig)

        assert element.get("path") is not None
        assert element.get("path") == "figures/image.png"

    def test_transform_figure_self_closing_element(self) -> None:
        """figure 要素は自己終了タグ（子要素なし）"""
        from src.book_converter.models import Figure
        from src.book_converter.transformer import transform_figure

        fig = Figure(path="figures/fig001.png", marker="図1")
        element = transform_figure(fig)

        # 子要素がないことを確認
        children = list(element)
        assert len(children) == 0

    def test_transform_figure_unicode_marker(self) -> None:
        """Unicode マーカーを含む figure を変換"""
        from src.book_converter.models import Figure
        from src.book_converter.transformer import transform_figure

        fig = Figure(path="figures/fig001.png", marker="図1：システム構成図")
        element = transform_figure(fig)

        assert element.get("marker") == "図1：システム構成図"

    def test_transform_figure_various_paths(self) -> None:
        """様々なファイルパスを変換"""
        from src.book_converter.models import Figure
        from src.book_converter.transformer import transform_figure

        test_paths = [
            "figures/fig001.png",
            "images/photo.jpg",
            "assets/diagram.svg",
            "../relative/path.png",
            "/absolute/path.png",
        ]

        for path in test_paths:
            fig = Figure(path=path)
            element = transform_figure(fig)
            assert element.get("path") == path, f"Failed for path: {path}"

    def test_transform_figure_returns_element(self) -> None:
        """戻り値は Element 型"""
        from xml.etree.ElementTree import Element

        from src.book_converter.models import Figure
        from src.book_converter.transformer import transform_figure

        fig = Figure(path="figures/fig001.png")
        element = transform_figure(fig)

        assert isinstance(element, Element)


# ============================================================================
# Phase 7: 出力フォーマット簡素化テスト (US5)
# ============================================================================


class TestNormalizeHeadingForComparison:
    """heading テキストの正規化テスト."""

    def test_normalize_heading_chapter(self) -> None:
        """Chapter N Title → N Title に正規化"""
        from src.book_converter.transformer_utils import normalize_heading_for_comparison

        result = normalize_heading_for_comparison("Chapter 1 「企画」で失敗")
        assert result == "1 「企画」で失敗"

    def test_normalize_heading_chapter_case_insensitive(self) -> None:
        """CHAPTER, chapter 等も正規化"""
        from src.book_converter.transformer_utils import normalize_heading_for_comparison

        assert normalize_heading_for_comparison("CHAPTER 2 Title") == "2 Title"
        assert normalize_heading_for_comparison("chapter 3 Title") == "3 Title"

    def test_normalize_heading_section(self) -> None:
        """Section N.N Title → N.N Title に正規化"""
        from src.book_converter.transformer_utils import normalize_heading_for_comparison

        result = normalize_heading_for_comparison("Section 1.1 なんでもできる")
        assert result == "1.1 なんでもできる"

    def test_normalize_heading_section_case_insensitive(self) -> None:
        """SECTION, section 等も正規化"""
        from src.book_converter.transformer_utils import normalize_heading_for_comparison

        assert normalize_heading_for_comparison("SECTION 2.3 Title") == "2.3 Title"
        assert normalize_heading_for_comparison("section 4.5 Title") == "4.5 Title"

    def test_normalize_heading_no_keyword(self) -> None:
        """キーワードなしの場合はそのまま（空白正規化のみ）"""
        from src.book_converter.transformer_utils import normalize_heading_for_comparison

        result = normalize_heading_for_comparison("すべての要求に応えてしまう")
        assert result == "すべての要求に応えてしまう"

    def test_normalize_heading_whitespace_normalization(self) -> None:
        """連続空白を単一空白に正規化"""
        from src.book_converter.transformer_utils import normalize_heading_for_comparison

        result = normalize_heading_for_comparison("Chapter  1   Title")
        assert result == "1 Title"


class TestIsDuplicateHeading:
    """heading 重複判定テスト."""

    def test_is_duplicate_heading_chapter_match(self) -> None:
        """chapter title と一致する heading は重複"""
        from src.book_converter.transformer_utils import is_duplicate_heading

        result = is_duplicate_heading(
            heading_text="Chapter 1 「企画」で失敗",
            container_number="1",
            container_title="「企画」で失敗",
        )
        assert result is True

    def test_is_duplicate_heading_section_match(self) -> None:
        """section title と一致する heading は重複"""
        from src.book_converter.transformer_utils import is_duplicate_heading

        result = is_duplicate_heading(
            heading_text="Section 1.1 なんでもできる「全部入りソフトウェア」",
            container_number="1.1",
            container_title="なんでもできる「全部入りソフトウェア」",
        )
        assert result is True

    def test_is_duplicate_heading_not_match(self) -> None:
        """chapter/section title と一致しない heading は重複ではない"""
        from src.book_converter.transformer_utils import is_duplicate_heading

        result = is_duplicate_heading(
            heading_text="すべての要求に応えてしまう",
            container_number="1.1",
            container_title="なんでもできる「全部入りソフトウェア」",
        )
        assert result is False

    def test_is_duplicate_heading_no_number(self) -> None:
        """number が None の場合は title のみで比較"""
        from src.book_converter.transformer_utils import is_duplicate_heading

        result = is_duplicate_heading(
            heading_text="はじめに",
            container_number=None,
            container_title="はじめに",
        )
        assert result is True

    def test_is_duplicate_heading_partial_match_is_false(self) -> None:
        """部分一致は重複ではない"""
        from src.book_converter.transformer_utils import is_duplicate_heading

        result = is_duplicate_heading(
            heading_text="Chapter 1 「企画」で失敗する",  # extra text
            container_number="1",
            container_title="「企画」で失敗",
        )
        assert result is False


class TestNonStructuralHeadingPreserved:
    """構造と無関係な heading 保持テスト."""

    def test_non_structural_heading_preserved(self) -> None:
        """構造と無関係な heading は保持される"""
        from src.book_converter.transformer_utils import is_duplicate_heading

        # These should NOT be duplicates (preserved)
        non_structural_headings = [
            "すべての要求に応えてしまう",
            "◎ソフトウェア開発は難しい",
            "●ご質問される前に",
            "あいまいな顧客像",
        ]

        for heading in non_structural_headings:
            result = is_duplicate_heading(
                heading_text=heading,
                container_number="1.1",
                container_title="なんでもできる",
            )
            assert result is False, f"'{heading}' should be preserved"
