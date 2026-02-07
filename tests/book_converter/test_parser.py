"""Parser tests for book markdown to XML conversion.

Tests for Phase 2: User Story 1 - TTS Page Navigation and Audio Announcement
- T009: Page marker parsing (parse_page_marker)
- T010: Page number extraction (normal, missing, edge cases)
- T011: PageAnnouncement test ("N page" format)

Phase 5: Error Handling Tests
- T071: Error handling tests (continue on warning, XML comment mark)
"""

import pytest
from pathlib import Path

from src.book_converter.parser import (
    parse_page_marker,
    create_page_announcement,
    extract_page_number,
)
from src.book_converter.models import PageAnnouncement


class TestParsePageMarker:
    """T009: ページマーカー解析テスト (parse_page_marker)"""

    def test_parse_standard_page_marker(self) -> None:
        """標準的なページマーカーを解析できる"""
        line = "--- Page 1 (page_0001.png) ---"
        result = parse_page_marker(line)

        assert result is not None
        assert result[0] == "1"  # ページ番号
        assert result[1] == "page_0001.png"  # ソースファイル

    def test_parse_page_marker_with_large_number(self) -> None:
        """大きなページ番号を解析できる"""
        line = "--- Page 999 (page_0999.png) ---"
        result = parse_page_marker(line)

        assert result is not None
        assert result[0] == "999"
        assert result[1] == "page_0999.png"

    def test_parse_page_marker_with_different_filename(self) -> None:
        """異なるファイル名形式を解析できる"""
        line = "--- Page 42 (scan_042_final.png) ---"
        result = parse_page_marker(line)

        assert result is not None
        assert result[0] == "42"
        assert result[1] == "scan_042_final.png"

    def test_parse_page_marker_with_jpg(self) -> None:
        """JPG拡張子を解析できる"""
        line = "--- Page 5 (image_005.jpg) ---"
        result = parse_page_marker(line)

        assert result is not None
        assert result[0] == "5"
        assert result[1] == "image_005.jpg"

    def test_non_page_marker_returns_none(self) -> None:
        """ページマーカーでない行はNoneを返す"""
        lines = [
            "# 見出し",
            "本文テキスト",
            "--- 区切り線 ---",
            "--- Page (no_number.png) ---",
            "",
            "   ",
        ]
        for line in lines:
            result = parse_page_marker(line)
            assert result is None, f"Expected None for line: {line!r}"

    def test_page_marker_with_extra_spaces(self) -> None:
        """余分なスペースがあっても解析できる"""
        line = "---  Page  10  (page_0010.png)  ---"
        result = parse_page_marker(line)

        # 余分なスペースがあっても解析可能であるべき
        assert result is not None
        assert result[0] == "10"
        assert result[1] == "page_0010.png"

    def test_page_marker_case_insensitive(self) -> None:
        """大文字小文字を区別しない"""
        line = "--- page 3 (PAGE_0003.PNG) ---"
        result = parse_page_marker(line)

        assert result is not None
        assert result[0] == "3"
        assert result[1] == "PAGE_0003.PNG"


class TestExtractPageNumber:
    """T010: ページ番号抽出テスト (正常系、欠落系、エッジケース)"""

    # 正常系
    def test_extract_page_number_from_marker(self) -> None:
        """ページマーカーからページ番号を抽出"""
        page_number, source_file = extract_page_number(
            "--- Page 42 (page_0042.png) ---"
        )
        assert page_number == "42"
        assert source_file == "page_0042.png"

    def test_extract_single_digit_page_number(self) -> None:
        """1桁のページ番号を抽出"""
        page_number, _ = extract_page_number("--- Page 1 (page_0001.png) ---")
        assert page_number == "1"

    def test_extract_three_digit_page_number(self) -> None:
        """3桁のページ番号を抽出"""
        page_number, _ = extract_page_number("--- Page 123 (page_0123.png) ---")
        assert page_number == "123"

    # 欠落系
    def test_missing_page_number_returns_empty(self) -> None:
        """ページ番号が欠落している場合は空文字列"""
        page_number, source_file = extract_page_number(
            "--- Page (page_0001.png) ---"
        )
        assert page_number == ""
        assert source_file == "page_0001.png"

    def test_invalid_format_returns_empty(self) -> None:
        """無効なフォーマットは空文字列"""
        page_number, source_file = extract_page_number("invalid line")
        assert page_number == ""
        assert source_file == ""

    def test_empty_line_returns_empty(self) -> None:
        """空行は空文字列"""
        page_number, source_file = extract_page_number("")
        assert page_number == ""
        assert source_file == ""

    # エッジケース
    def test_page_number_zero(self) -> None:
        """ページ番号0を抽出"""
        page_number, _ = extract_page_number("--- Page 0 (page_0000.png) ---")
        assert page_number == "0"

    def test_unicode_in_filename(self) -> None:
        """ファイル名にUnicodeが含まれる場合"""
        line = "--- Page 1 (ページ_0001.png) ---"
        page_number, source_file = extract_page_number(line)
        # ファイル名にUnicodeが含まれても抽出可能
        assert page_number == "1"
        assert source_file == "ページ_0001.png"

    def test_very_long_filename(self) -> None:
        """長いファイル名を抽出"""
        long_filename = "a" * 200 + ".png"
        line = f"--- Page 1 ({long_filename}) ---"
        page_number, source_file = extract_page_number(line)
        assert page_number == "1"
        assert source_file == long_filename


class TestCreatePageAnnouncement:
    """T011: PageAnnouncementテスト (「Nページ」フォーマット)"""

    def test_create_simple_announcement(self) -> None:
        """シンプルなページアナウンスを生成"""
        announcement = create_page_announcement("1")

        assert announcement is not None
        assert isinstance(announcement, PageAnnouncement)
        assert announcement.text == "1ページ"
        assert announcement.format == "simple"

    def test_create_announcement_for_page_42(self) -> None:
        """42ページのアナウンスを生成"""
        announcement = create_page_announcement("42")

        assert announcement.text == "42ページ"
        assert announcement.format == "simple"

    def test_create_announcement_for_large_page_number(self) -> None:
        """大きなページ番号のアナウンスを生成"""
        announcement = create_page_announcement("999")

        assert announcement.text == "999ページ"
        assert announcement.format == "simple"

    def test_announcement_for_empty_page_number(self) -> None:
        """空のページ番号はNoneを返す"""
        announcement = create_page_announcement("")

        assert announcement is None

    def test_announcement_for_zero_page(self) -> None:
        """0ページのアナウンスを生成"""
        announcement = create_page_announcement("0")

        # 0ページも有効なアナウンスとして生成
        assert announcement is not None
        assert announcement.text == "0ページ"

    def test_announcement_format_is_simple(self) -> None:
        """フォーマットはsimpleであること"""
        announcement = create_page_announcement("10")

        assert announcement.format == "simple"

    def test_announcement_is_immutable(self) -> None:
        """PageAnnouncementはイミュータブル"""
        announcement = create_page_announcement("5")

        with pytest.raises(Exception):  # frozen=True raises FrozenInstanceError
            announcement.text = "changed"  # type: ignore


# =============================================================================
# Phase 3: User Story 2 - TTSコンテンツ階層と構造解析
# =============================================================================


class TestParseHeading:
    """T028: 見出し解析テスト (#, ##, ### パターン、level 1-3)"""

    def test_parse_level_1_heading(self) -> None:
        """# で始まる行をレベル1の見出しとして解析"""
        from src.book_converter.parser import parse_heading

        result = parse_heading("# 第1章 はじめに")

        assert result is not None
        assert result.level == 1
        assert result.text == "第1章 はじめに"

    def test_parse_level_2_heading(self) -> None:
        """## で始まる行をレベル2の見出しとして解析"""
        from src.book_converter.parser import parse_heading

        result = parse_heading("## 1.1 概要")

        assert result is not None
        assert result.level == 2
        assert result.text == "1.1 概要"

    def test_parse_level_3_heading(self) -> None:
        """### で始まる行をレベル3の見出しとして解析"""
        from src.book_converter.parser import parse_heading

        result = parse_heading("### 詳細説明")

        assert result is not None
        assert result.level == 3
        assert result.text == "詳細説明"

    def test_parse_heading_with_extra_spaces(self) -> None:
        """見出しマーカーと本文の間のスペースを許容"""
        from src.book_converter.parser import parse_heading

        result = parse_heading("#   タイトル")

        assert result is not None
        assert result.level == 1
        assert result.text == "タイトル"

    def test_parse_heading_returns_none_for_non_heading(self) -> None:
        """見出し以外の行はNoneを返す"""
        from src.book_converter.parser import parse_heading

        non_headings = [
            "本文テキスト",
            "- リスト項目",
            "  # インデントされた見出し",
            "",
            "   ",
        ]
        for line in non_headings:
            result = parse_heading(line)
            assert result is None, f"Expected None for: {line!r}"

    def test_parse_heading_preserves_unicode(self) -> None:
        """Unicodeテキストを正しく保持"""
        from src.book_converter.parser import parse_heading

        result = parse_heading("## 日本語の見出し「テスト」")

        assert result is not None
        assert result.text == "日本語の見出し「テスト」"

    def test_parse_heading_with_special_characters(self) -> None:
        """特殊文字を含む見出しを解析"""
        from src.book_converter.parser import parse_heading

        result = parse_heading("# Chapter 1: Introduction & Overview")

        assert result is not None
        assert result.text == "Chapter 1: Introduction & Overview"

    def test_parse_heading_empty_text(self) -> None:
        """テキストなしの見出しマーカー"""
        from src.book_converter.parser import parse_heading

        result = parse_heading("#")

        # 見出しマーカーのみでテキストがない場合
        # 空の見出しとして処理するか、Noneを返すか
        # 仕様: 空テキストでもHeadingを生成（警告を出す可能性あり）
        assert result is not None
        assert result.level == 1
        assert result.text == ""

    def test_parse_heading_returns_heading_type(self) -> None:
        """戻り値はHeading型"""
        from src.book_converter.parser import parse_heading
        from src.book_converter.models import Heading

        result = parse_heading("# テスト")

        assert isinstance(result, Heading)


class TestParseHeadingLevel4Warning:
    """T029: 4階層以上の見出し警告テスト (#### → level=3 + 警告)"""

    def test_level_4_heading_becomes_level_3(self) -> None:
        """#### はlevel=3に変換される"""
        from src.book_converter.parser import parse_heading

        result = parse_heading("#### 4階層目の見出し")

        assert result is not None
        assert result.level == 3  # level=3 に統合
        assert result.text == "4階層目の見出し"

    def test_level_5_heading_becomes_level_3(self) -> None:
        """##### もlevel=3に変換される"""
        from src.book_converter.parser import parse_heading

        result = parse_heading("##### 5階層目の見出し")

        assert result is not None
        assert result.level == 3

    def test_level_6_heading_becomes_level_3(self) -> None:
        """###### もlevel=3に変換される"""
        from src.book_converter.parser import parse_heading

        result = parse_heading("###### 6階層目の見出し")

        assert result is not None
        assert result.level == 3

    def test_parse_heading_with_warning_returns_warning(self) -> None:
        """4階層以上は警告情報を返す"""
        from src.book_converter.parser import parse_heading_with_warning

        heading, warning = parse_heading_with_warning("#### 深い見出し")

        assert heading is not None
        assert heading.level == 3
        assert warning is not None
        assert "level" in warning.lower() or "階層" in warning

    def test_parse_heading_with_warning_no_warning_for_level_3(self) -> None:
        """level 1-3では警告なし"""
        from src.book_converter.parser import parse_heading_with_warning

        heading, warning = parse_heading_with_warning("### 通常の見出し")

        assert heading is not None
        assert heading.level == 3
        assert warning is None


class TestParseParagraph:
    """T030: 段落解析テスト (空行区切り、ContentElement生成)"""

    def test_parse_single_line_paragraph(self) -> None:
        """1行の段落を解析"""
        from src.book_converter.parser import parse_paragraph

        result = parse_paragraph(["これは段落です。"])

        assert result is not None
        assert result.text == "これは段落です。"

    def test_parse_multiline_paragraph(self) -> None:
        """複数行の段落を結合"""
        from src.book_converter.parser import parse_paragraph

        lines = [
            "これは段落の1行目です。",
            "これは段落の2行目です。",
            "これは段落の3行目です。",
        ]
        result = parse_paragraph(lines)

        assert result is not None
        # 複数行は改行で結合されるか、スペースで結合されるか
        # 仕様: 改行を保持してテキストを結合
        assert "1行目" in result.text
        assert "2行目" in result.text
        assert "3行目" in result.text

    def test_parse_paragraph_returns_paragraph_type(self) -> None:
        """戻り値はParagraph型"""
        from src.book_converter.parser import parse_paragraph
        from src.book_converter.models import Paragraph

        result = parse_paragraph(["テスト"])

        assert isinstance(result, Paragraph)

    def test_parse_paragraph_empty_lines(self) -> None:
        """空行のリストはNoneを返す"""
        from src.book_converter.parser import parse_paragraph

        result = parse_paragraph([])

        assert result is None

    def test_parse_paragraph_whitespace_only(self) -> None:
        """空白のみの行はNoneを返す"""
        from src.book_converter.parser import parse_paragraph

        result = parse_paragraph(["   ", "  "])

        assert result is None

    def test_parse_paragraph_preserves_unicode(self) -> None:
        """Unicode文字を正しく保持"""
        from src.book_converter.parser import parse_paragraph

        lines = ["日本語テキスト。", "絵文字を含む文章。"]
        result = parse_paragraph(lines)

        assert result is not None
        assert "日本語" in result.text

    def test_parse_paragraph_trims_trailing_whitespace(self) -> None:
        """末尾の空白を除去"""
        from src.book_converter.parser import parse_paragraph

        result = parse_paragraph(["テスト   "])

        assert result is not None
        assert result.text == "テスト" or result.text.strip() == "テスト"


class TestParseList:
    """T031: リスト解析テスト (- / * 項目)"""

    def test_parse_list_with_dash(self) -> None:
        """- で始まる項目をリストとして解析"""
        from src.book_converter.parser import parse_list

        lines = [
            "- 項目1",
            "- 項目2",
            "- 項目3",
        ]
        result = parse_list(lines)

        assert result is not None
        assert len(result.items) == 3
        assert result.items[0] == "項目1"
        assert result.items[1] == "項目2"
        assert result.items[2] == "項目3"

    def test_parse_list_with_asterisk(self) -> None:
        """* で始まる項目をリストとして解析"""
        from src.book_converter.parser import parse_list

        lines = [
            "* First item",
            "* Second item",
        ]
        result = parse_list(lines)

        assert result is not None
        assert len(result.items) == 2
        assert result.items[0] == "First item"
        assert result.items[1] == "Second item"

    def test_parse_list_mixed_markers(self) -> None:
        """- と * が混在したリスト"""
        from src.book_converter.parser import parse_list

        lines = [
            "- 項目A",
            "* 項目B",
            "- 項目C",
        ]
        result = parse_list(lines)

        assert result is not None
        assert len(result.items) == 3

    def test_parse_list_returns_list_type(self) -> None:
        """戻り値はList型"""
        from src.book_converter.parser import parse_list
        from src.book_converter.models import List

        result = parse_list(["- 項目"])

        assert isinstance(result, List)

    def test_parse_list_empty_returns_none(self) -> None:
        """空のリストはNoneを返す"""
        from src.book_converter.parser import parse_list

        result = parse_list([])

        assert result is None

    def test_parse_list_preserves_item_content(self) -> None:
        """リスト項目の内容を保持"""
        from src.book_converter.parser import parse_list

        lines = [
            "- 日本語: テスト",
            "- 記号を含む: @#$%",
        ]
        result = parse_list(lines)

        assert result is not None
        assert "日本語: テスト" in result.items
        assert "記号を含む: @#$%" in result.items

    def test_parse_list_with_leading_spaces(self) -> None:
        """先頭にスペースがある項目"""
        from src.book_converter.parser import parse_list

        lines = [
            "  - インデント項目1",
            "  - インデント項目2",
        ]
        result = parse_list(lines)

        # インデント付きリストも解析可能
        assert result is not None
        assert len(result.items) == 2

    def test_parse_list_items_are_tuple(self) -> None:
        """itemsはイミュータブルなタプル"""
        from src.book_converter.parser import parse_list

        result = parse_list(["- 項目"])

        assert result is not None
        assert isinstance(result.items, tuple)


# =============================================================================
# Phase 4: User Story 3 - TTS図表説明制御とメタデータ分離
# =============================================================================


class TestParseFigureComment:
    """T050: 図コメント解析テスト (<!-- FIGURE: path --> パターン)"""

    def test_parse_figure_comment_basic(self) -> None:
        """基本的な図コメントを解析"""
        from src.book_converter.parser import parse_figure_comment

        result = parse_figure_comment("<!-- FIGURE: images/figure1.png -->")

        assert result is not None
        assert result == "images/figure1.png"

    def test_parse_figure_comment_with_spaces(self) -> None:
        """スペースを含む図コメントを解析"""
        from src.book_converter.parser import parse_figure_comment

        result = parse_figure_comment("<!--  FIGURE:  path/to/image.png  -->")

        assert result is not None
        assert result == "path/to/image.png"

    def test_parse_figure_comment_with_japanese_path(self) -> None:
        """日本語パスを含む図コメントを解析"""
        from src.book_converter.parser import parse_figure_comment

        result = parse_figure_comment("<!-- FIGURE: 画像/図1.png -->")

        assert result is not None
        assert result == "画像/図1.png"

    def test_parse_figure_comment_jpg_extension(self) -> None:
        """JPG拡張子を解析"""
        from src.book_converter.parser import parse_figure_comment

        result = parse_figure_comment("<!-- FIGURE: photo.jpg -->")

        assert result is not None
        assert result == "photo.jpg"

    def test_parse_figure_comment_case_insensitive(self) -> None:
        """FIGUREキーワードは大文字小文字を区別しない"""
        from src.book_converter.parser import parse_figure_comment

        result = parse_figure_comment("<!-- figure: test.png -->")

        assert result is not None
        assert result == "test.png"

    def test_parse_non_figure_comment_returns_none(self) -> None:
        """図コメント以外はNoneを返す"""
        from src.book_converter.parser import parse_figure_comment

        non_figure_lines = [
            "<!-- This is a normal comment -->",
            "<!-- ERROR: something -->",
            "本文テキスト",
            "# 見出し",
            "<!-- FIG: invalid.png -->",  # キーワードが違う
            "",
        ]
        for line in non_figure_lines:
            result = parse_figure_comment(line)
            assert result is None, f"Expected None for: {line!r}"

    def test_parse_figure_comment_empty_path(self) -> None:
        """空のパスを含む図コメント"""
        from src.book_converter.parser import parse_figure_comment

        result = parse_figure_comment("<!-- FIGURE: -->")

        # 空パスの場合はNoneか空文字列
        assert result is None or result == ""

    def test_parse_figure_comment_complex_path(self) -> None:
        """複雑なパスを解析"""
        from src.book_converter.parser import parse_figure_comment

        result = parse_figure_comment(
            "<!-- FIGURE: output/chapter_01/fig_2-3_diagram.png -->"
        )

        assert result is not None
        assert result == "output/chapter_01/fig_2-3_diagram.png"


class TestParseFigureDescription:
    """T051: 図説明文解析テスト (図コメント後のテキストをdescriptionに)"""

    def test_parse_figure_with_description(self) -> None:
        """図コメントと説明文を解析"""
        from src.book_converter.parser import parse_figure

        lines = [
            "<!-- FIGURE: images/fig1.png -->",
            "この図は構成図を示しています。",
        ]
        result = parse_figure(lines)

        assert result is not None
        assert result.file == "images/fig1.png"
        assert result.description == "この図は構成図を示しています。"

    def test_parse_figure_with_multiline_description(self) -> None:
        """複数行の説明文を解析"""
        from src.book_converter.parser import parse_figure

        lines = [
            "<!-- FIGURE: diagram.png -->",
            "図1: システム構成図",
            "この図は全体のアーキテクチャを表しています。",
        ]
        result = parse_figure(lines)

        assert result is not None
        assert result.file == "diagram.png"
        # 複数行は結合されるか、最初の行のみか
        assert "図1: システム構成図" in result.description or \
               "アーキテクチャ" in result.description

    def test_parse_figure_without_description(self) -> None:
        """説明文なしの図を解析"""
        from src.book_converter.parser import parse_figure

        lines = [
            "<!-- FIGURE: image.png -->",
        ]
        result = parse_figure(lines)

        assert result is not None
        assert result.file == "image.png"
        assert result.description == ""

    def test_parse_figure_with_caption(self) -> None:
        """キャプション付きの図を解析"""
        from src.book_converter.parser import parse_figure

        lines = [
            "<!-- FIGURE: chart.png -->",
            "**図1: 売上推移**",
            "2020年から2024年までの売上推移を示すグラフです。",
        ]
        result = parse_figure(lines)

        assert result is not None
        assert result.file == "chart.png"
        # キャプションは ** で囲まれた部分
        assert "売上推移" in result.caption or "図1" in result.caption

    def test_parse_figure_returns_figure_type(self) -> None:
        """戻り値はFigure型"""
        from src.book_converter.parser import parse_figure
        from src.book_converter.models import Figure

        lines = ["<!-- FIGURE: test.png -->"]
        result = parse_figure(lines)

        assert isinstance(result, Figure)

    def test_parse_figure_default_read_aloud(self) -> None:
        """デフォルトのreadAloudは'optional'"""
        from src.book_converter.parser import parse_figure

        lines = ["<!-- FIGURE: test.png -->"]
        result = parse_figure(lines)

        assert result is not None
        assert result.read_aloud == "optional"

    def test_parse_figure_empty_lines_returns_none(self) -> None:
        """空のラインリストはNoneを返す"""
        from src.book_converter.parser import parse_figure

        result = parse_figure([])

        assert result is None

    def test_parse_figure_no_comment_returns_none(self) -> None:
        """図コメントなしはNoneを返す"""
        from src.book_converter.parser import parse_figure

        lines = [
            "本文のテキストです。",
            "図コメントがありません。",
        ]
        result = parse_figure(lines)

        assert result is None

    def test_parse_figure_preserves_unicode_description(self) -> None:
        """Unicode説明文を保持"""
        from src.book_converter.parser import parse_figure

        lines = [
            "<!-- FIGURE: 日本語パス.png -->",
            "日本語の説明文「テスト」です。",
        ]
        result = parse_figure(lines)

        assert result is not None
        assert "日本語の説明文" in result.description
        assert "「テスト」" in result.description


class TestParsePageMetadata:
    """T052: ページメタデータ解析テスト (N / M パターン、type判定)"""

    def test_parse_page_metadata_simple(self) -> None:
        """シンプルなN / M形式を解析"""
        from src.book_converter.parser import parse_page_metadata

        result = parse_page_metadata("3 / 7")

        assert result is not None
        assert result.text == "3 / 7"
        assert result.current == 3
        assert result.total == 7
        assert result.meta_type == "chapter-page"

    def test_parse_page_metadata_with_section_name(self) -> None:
        """セクション名付きのメタデータを解析"""
        from src.book_converter.parser import parse_page_metadata

        result = parse_page_metadata("はじめに 1 / 3")

        assert result is not None
        assert result.text == "はじめに 1 / 3"
        assert result.section_name == "はじめに"
        assert result.current == 1
        assert result.total == 3

    def test_parse_page_metadata_chapter_page_type(self) -> None:
        """chapter-pageタイプを判定"""
        from src.book_converter.parser import parse_page_metadata

        result = parse_page_metadata("第1章 5 / 20")

        assert result is not None
        assert result.meta_type == "chapter-page"
        assert result.section_name == "第1章"

    def test_parse_page_metadata_section_page_type(self) -> None:
        """section-pageタイプを判定"""
        from src.book_converter.parser import parse_page_metadata

        # セクション名が「節」を含む場合はsection-page
        result = parse_page_metadata("1.2節 2 / 5")

        assert result is not None
        # meta_typeは実装に依存するが、section-pageまたはchapter-page
        assert result.meta_type in ("chapter-page", "section-page")

    def test_parse_page_metadata_unknown_type(self) -> None:
        """不明なパターンはunknownタイプ"""
        from src.book_converter.parser import parse_page_metadata

        result = parse_page_metadata("??? 1 / 1")

        assert result is not None
        assert result.meta_type in ("chapter-page", "unknown")

    def test_parse_page_metadata_invalid_format(self) -> None:
        """無効なフォーマットはNoneを返す"""
        from src.book_converter.parser import parse_page_metadata

        invalid_formats = [
            "本文テキスト",
            "ページ42",
            "3 - 7",  # スラッシュでない
            "a / b",  # 数字でない
            "",
            "   ",
        ]
        for text in invalid_formats:
            result = parse_page_metadata(text)
            assert result is None, f"Expected None for: {text!r}"

    def test_parse_page_metadata_returns_type(self) -> None:
        """戻り値はPageMetadata型"""
        from src.book_converter.parser import parse_page_metadata
        from src.book_converter.models import PageMetadata

        result = parse_page_metadata("1 / 5")

        assert isinstance(result, PageMetadata)

    def test_parse_page_metadata_large_numbers(self) -> None:
        """大きなページ番号を解析"""
        from src.book_converter.parser import parse_page_metadata

        result = parse_page_metadata("100 / 500")

        assert result is not None
        assert result.current == 100
        assert result.total == 500

    def test_parse_page_metadata_single_page(self) -> None:
        """単一ページ (1 / 1) を解析"""
        from src.book_converter.parser import parse_page_metadata

        result = parse_page_metadata("1 / 1")

        assert result is not None
        assert result.current == 1
        assert result.total == 1

    def test_parse_page_metadata_with_extra_spaces(self) -> None:
        """余分なスペースがあっても解析"""
        from src.book_converter.parser import parse_page_metadata

        result = parse_page_metadata("  まえがき   2  /  10  ")

        assert result is not None
        assert result.current == 2
        assert result.total == 10
        assert result.section_name.strip() == "まえがき"

    def test_parse_page_metadata_preserves_original_text(self) -> None:
        """元のテキストを保持"""
        from src.book_converter.parser import parse_page_metadata

        original = "第2章 3 / 15"
        result = parse_page_metadata(original)

        assert result is not None
        assert result.text == original


# =============================================================================
# Phase 5: Error Handling Tests
# =============================================================================


class TestErrorHandlingContinueOnWarning:
    """T071: エラーハンドリングテスト - 警告継続"""

    def test_parse_pages_continues_on_missing_page_number(
        self, tmp_path: Path
    ) -> None:
        """ページ番号が欠落しても解析を継続"""
        from src.book_converter.parser import parse_pages_with_errors

        input_file = tmp_path / "test.md"
        input_file.write_text(
            "--- Page 1 (page_0001.png) ---\n\n# Title\n\n"
            "--- Page (page_0002.png) ---\n\n## Chapter 1\n\n"  # Missing number
            "--- Page 3 (page_0003.png) ---\n\n## Chapter 2\n"
        )

        pages, errors = parse_pages_with_errors(input_file)

        # 3ページすべて解析される
        assert len(pages) == 3
        # エラーが記録される
        assert len(errors) >= 1

    def test_parse_pages_continues_on_invalid_heading(
        self, tmp_path: Path
    ) -> None:
        """不正な見出しがあっても解析を継続"""
        from src.book_converter.parser import parse_pages_with_errors

        input_file = tmp_path / "test.md"
        input_file.write_text(
            "--- Page 1 (page_0001.png) ---\n\n"
            "####### Invalid 7-level heading\n\n"  # Invalid: 7 levels
            "## Valid heading\n"
        )

        pages, errors = parse_pages_with_errors(input_file)

        # ページは解析される
        assert len(pages) == 1

    def test_parse_pages_records_error_for_missing_number(
        self, tmp_path: Path
    ) -> None:
        """欠落したページ番号のエラーを記録"""
        from src.book_converter.parser import parse_pages_with_errors
        from src.book_converter.models import ConversionError

        input_file = tmp_path / "test.md"
        input_file.write_text(
            "--- Page (page_0001.png) ---\n\n# Title\n"  # Missing number
        )

        pages, errors = parse_pages_with_errors(input_file)

        assert len(errors) >= 1
        assert isinstance(errors[0], ConversionError)
        assert "PAGE_NUMBER" in errors[0].error_type or "NUMBER" in errors[0].error_type

    def test_parse_pages_records_error_for_deep_heading(
        self, tmp_path: Path
    ) -> None:
        """4階層以上の見出しのエラーを記録"""
        from src.book_converter.parser import parse_pages_with_errors

        input_file = tmp_path / "test.md"
        input_file.write_text(
            "--- Page 1 (page_0001.png) ---\n\n"
            "#### Deep heading\n\n"  # Level 4
            "Content\n"
        )

        pages, errors = parse_pages_with_errors(input_file)

        # 警告/エラーが記録される
        has_heading_warning = any(
            "HEADING" in e.error_type or "LEVEL" in e.error_type or "階層" in e.message
            for e in errors
        )
        assert has_heading_warning

    def test_error_contains_line_number(
        self, tmp_path: Path
    ) -> None:
        """エラーに行番号が含まれる"""
        from src.book_converter.parser import parse_pages_with_errors

        input_file = tmp_path / "test.md"
        input_file.write_text(
            "--- Page (page_0001.png) ---\n"  # Line 1: Missing number
            "\n"
            "# Title\n"
        )

        pages, errors = parse_pages_with_errors(input_file)

        assert len(errors) >= 1
        # line_number属性がある
        assert hasattr(errors[0], "line_number")
        assert errors[0].line_number > 0


class TestErrorHandlingXMLComment:
    """T071: エラーハンドリングテスト - XMLコメントマーク"""

    def test_xml_contains_error_comment_for_missing_number(
        self, tmp_path: Path
    ) -> None:
        """ページ番号欠落時にXMLコメントを挿入"""
        from src.book_converter.cli import convert_book

        input_file = tmp_path / "test.md"
        input_file.write_text(
            "--- Page (page_0001.png) ---\n\n# Title\n"  # Missing number
        )

        output_file = tmp_path / "output.xml"
        convert_book(input_file, output_file)

        content = output_file.read_text(encoding="utf-8")
        # エラーコメントが含まれる
        assert "<!-- ERROR:" in content or "<!--" in content

    def test_xml_contains_error_type(
        self, tmp_path: Path
    ) -> None:
        """XMLコメントにエラータイプが含まれる"""
        from src.book_converter.cli import convert_book

        input_file = tmp_path / "test.md"
        input_file.write_text(
            "--- Page (page_0001.png) ---\n\n# Title\n"
        )

        output_file = tmp_path / "output.xml"
        convert_book(input_file, output_file)

        content = output_file.read_text(encoding="utf-8")
        # エラータイプが含まれる
        assert "ERROR" in content or "PAGE" in content

    def test_xml_comment_format(
        self, tmp_path: Path
    ) -> None:
        """XMLコメントが正しい形式 <!-- ERROR: [type] - [message] -->"""
        from src.book_converter.cli import convert_book

        input_file = tmp_path / "test.md"
        input_file.write_text(
            "--- Page (page_0001.png) ---\n\n# Title\n"
        )

        output_file = tmp_path / "output.xml"
        convert_book(input_file, output_file)

        content = output_file.read_text(encoding="utf-8")
        import re
        # XMLコメント形式: <!-- ERROR: TYPE - message -->
        pattern = r"<!--\s*ERROR:\s*\w+.*-->"
        assert re.search(pattern, content) is not None

    def test_xml_contains_error_comment_for_deep_heading(
        self, tmp_path: Path
    ) -> None:
        """4階層見出し時にXMLコメントを挿入"""
        from src.book_converter.cli import convert_book

        input_file = tmp_path / "test.md"
        input_file.write_text(
            "--- Page 1 (page_0001.png) ---\n\n"
            "#### Deep heading\n\n"  # Level 4
            "Content\n"
        )

        output_file = tmp_path / "output.xml"
        convert_book(input_file, output_file)

        content = output_file.read_text(encoding="utf-8")
        # エラー/警告コメントが含まれる
        assert "ERROR" in content or "WARNING" in content or "<!-- " in content


class TestErrorHandlingParseWithErrors:
    """parse_pages_with_errors関数テスト"""

    def test_function_exists(self) -> None:
        """parse_pages_with_errors関数が存在する"""
        from src.book_converter.parser import parse_pages_with_errors

        assert callable(parse_pages_with_errors)

    def test_returns_tuple_of_pages_and_errors(
        self, tmp_path: Path
    ) -> None:
        """ページリストとエラーリストのタプルを返す"""
        from src.book_converter.parser import parse_pages_with_errors

        input_file = tmp_path / "test.md"
        input_file.write_text("--- Page 1 (page_0001.png) ---\n\n# Title\n")

        result = parse_pages_with_errors(input_file)

        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_pages_are_list(
        self, tmp_path: Path
    ) -> None:
        """ページはリストで返される"""
        from src.book_converter.parser import parse_pages_with_errors

        input_file = tmp_path / "test.md"
        input_file.write_text("--- Page 1 (page_0001.png) ---\n\n# Title\n")

        pages, errors = parse_pages_with_errors(input_file)

        assert isinstance(pages, (list, tuple))

    def test_errors_are_list(
        self, tmp_path: Path
    ) -> None:
        """エラーはリストで返される"""
        from src.book_converter.parser import parse_pages_with_errors

        input_file = tmp_path / "test.md"
        input_file.write_text("--- Page 1 (page_0001.png) ---\n\n# Title\n")

        pages, errors = parse_pages_with_errors(input_file)

        assert isinstance(errors, (list, tuple))

    def test_no_errors_for_valid_input(
        self, tmp_path: Path
    ) -> None:
        """有効な入力ではエラーなし"""
        from src.book_converter.parser import parse_pages_with_errors

        input_file = tmp_path / "test.md"
        input_file.write_text(
            "--- Page 1 (page_0001.png) ---\n\n"
            "# Title\n\n"
            "Content here.\n"
        )

        pages, errors = parse_pages_with_errors(input_file)

        assert len(errors) == 0

    def test_multiple_errors_collected(
        self, tmp_path: Path
    ) -> None:
        """複数のエラーを収集"""
        from src.book_converter.parser import parse_pages_with_errors

        input_file = tmp_path / "test.md"
        input_file.write_text(
            "--- Page (page_0001.png) ---\n\n"  # Error 1: missing number
            "#### Deep heading\n\n"  # Error 2: deep heading
            "--- Page (page_0002.png) ---\n\n"  # Error 3: missing number
            "# Title\n"
        )

        pages, errors = parse_pages_with_errors(input_file)

        # 複数のエラーが記録される
        assert len(errors) >= 2
