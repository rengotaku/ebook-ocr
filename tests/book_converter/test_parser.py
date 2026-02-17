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
    """T051: 図解析テスト (新形式: path, caption, marker)"""

    def test_parse_figure_basic(self) -> None:
        """図コメントを解析 (path)"""
        from src.book_converter.parser import parse_figure

        lines = [
            "<!-- FIGURE: images/fig1.png -->",
        ]
        result = parse_figure(lines)

        assert result is not None
        assert result.path == "images/fig1.png"

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
        assert result.path == "chart.png"
        # キャプションは ** で囲まれた部分
        assert "売上推移" in result.caption or "図1" in result.caption

    def test_parse_figure_without_caption(self) -> None:
        """キャプションなしの図を解析"""
        from src.book_converter.parser import parse_figure

        lines = [
            "<!-- FIGURE: image.png -->",
        ]
        result = parse_figure(lines)

        assert result is not None
        assert result.path == "image.png"
        assert result.caption == ""

    def test_parse_figure_returns_figure_type(self) -> None:
        """戻り値はFigure型"""
        from src.book_converter.parser import parse_figure
        from src.book_converter.models import Figure

        lines = ["<!-- FIGURE: test.png -->"]
        result = parse_figure(lines)

        assert isinstance(result, Figure)

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

    def test_parse_figure_preserves_unicode_path(self) -> None:
        """Unicodeパスを保持"""
        from src.book_converter.parser import parse_figure

        lines = [
            "<!-- FIGURE: 日本語パス.png -->",
        ]
        result = parse_figure(lines)

        assert result is not None
        assert result.path == "日本語パス.png"


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

        pages, errors, _ = parse_pages_with_errors(input_file)

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

        pages, errors, _ = parse_pages_with_errors(input_file)

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

        pages, errors, _ = parse_pages_with_errors(input_file)

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

        pages, errors, _ = parse_pages_with_errors(input_file)

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

        pages, errors, _ = parse_pages_with_errors(input_file)

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

    def test_returns_tuple_of_pages_errors_and_toc(
        self, tmp_path: Path
    ) -> None:
        """ページリストとエラーリストとTOCのタプルを返す"""
        from src.book_converter.parser import parse_pages_with_errors

        input_file = tmp_path / "test.md"
        input_file.write_text("--- Page 1 (page_0001.png) ---\n\n# Title\n")

        result = parse_pages_with_errors(input_file)

        assert isinstance(result, tuple)
        assert len(result) == 3
        pages, errors, toc = result
        assert isinstance(pages, list)
        assert isinstance(errors, list)
        # toc is None when no TOC markers
        assert toc is None

    def test_pages_are_list(
        self, tmp_path: Path
    ) -> None:
        """ページはリストで返される"""
        from src.book_converter.parser import parse_pages_with_errors

        input_file = tmp_path / "test.md"
        input_file.write_text("--- Page 1 (page_0001.png) ---\n\n# Title\n")

        pages, errors, _ = parse_pages_with_errors(input_file)

        assert isinstance(pages, (list, tuple))

    def test_errors_are_list(
        self, tmp_path: Path
    ) -> None:
        """エラーはリストで返される"""
        from src.book_converter.parser import parse_pages_with_errors

        input_file = tmp_path / "test.md"
        input_file.write_text("--- Page 1 (page_0001.png) ---\n\n# Title\n")

        pages, errors, _ = parse_pages_with_errors(input_file)

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

        pages, errors, _ = parse_pages_with_errors(input_file)

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

        pages, errors, _ = parse_pages_with_errors(input_file)

        # 複数のエラーが記録される
        assert len(errors) >= 2


# =============================================================================
# Phase 2 (004-toc-structure): US1+US2 目次マーカー認識と構造化
# =============================================================================


class TestParseTocMarker:
    """T011: 目次マーカー検出テスト (parse_toc_marker)

    US1: 目次マーカーによる目次認識
    - `<!-- toc -->` マーカーで目次開始を検出
    - `<!-- /toc -->` マーカーで目次終了を検出
    - 大文字小文字を区別しない
    """

    def test_parse_toc_start_marker(self) -> None:
        """目次開始マーカーを検出"""
        from src.book_converter.parser import parse_toc_marker
        from src.book_converter.models import MarkerType

        result = parse_toc_marker("<!-- toc -->")

        assert result is not None
        assert result == MarkerType.TOC_START

    def test_parse_toc_end_marker(self) -> None:
        """目次終了マーカーを検出"""
        from src.book_converter.parser import parse_toc_marker
        from src.book_converter.models import MarkerType

        result = parse_toc_marker("<!-- /toc -->")

        assert result is not None
        assert result == MarkerType.TOC_END

    def test_parse_toc_marker_case_insensitive_lowercase(self) -> None:
        """小文字のtocマーカーを検出"""
        from src.book_converter.parser import parse_toc_marker
        from src.book_converter.models import MarkerType

        result = parse_toc_marker("<!-- toc -->")

        assert result == MarkerType.TOC_START

    def test_parse_toc_marker_case_insensitive_uppercase(self) -> None:
        """大文字のTOCマーカーを検出"""
        from src.book_converter.parser import parse_toc_marker
        from src.book_converter.models import MarkerType

        result = parse_toc_marker("<!-- TOC -->")

        assert result == MarkerType.TOC_START

    def test_parse_toc_marker_case_insensitive_mixed(self) -> None:
        """大文字小文字混在のTocマーカーを検出"""
        from src.book_converter.parser import parse_toc_marker
        from src.book_converter.models import MarkerType

        result = parse_toc_marker("<!-- Toc -->")

        assert result == MarkerType.TOC_START

    def test_parse_toc_marker_with_extra_spaces(self) -> None:
        """余分なスペースがあっても検出"""
        from src.book_converter.parser import parse_toc_marker
        from src.book_converter.models import MarkerType

        result = parse_toc_marker("<!--   toc   -->")

        assert result == MarkerType.TOC_START

    def test_parse_toc_end_marker_uppercase(self) -> None:
        """大文字の終了マーカーを検出"""
        from src.book_converter.parser import parse_toc_marker
        from src.book_converter.models import MarkerType

        result = parse_toc_marker("<!-- /TOC -->")

        assert result == MarkerType.TOC_END

    def test_parse_non_toc_marker_returns_none(self) -> None:
        """目次マーカーでない行はNoneを返す"""
        from src.book_converter.parser import parse_toc_marker

        non_toc_lines = [
            "<!-- content -->",
            "<!-- skip -->",
            "# 見出し",
            "本文テキスト",
            "<!-- FIGURE: image.png -->",
            "",
            "   ",
            "<!-- tox -->",  # typo
        ]
        for line in non_toc_lines:
            result = parse_toc_marker(line)
            assert result is None, f"Expected None for line: {line!r}"

    def test_parse_toc_marker_with_leading_spaces(self) -> None:
        """先頭にスペースがあっても検出"""
        from src.book_converter.parser import parse_toc_marker
        from src.book_converter.models import MarkerType

        result = parse_toc_marker("  <!-- toc -->")

        assert result == MarkerType.TOC_START


class TestParseTocEntry:
    """T012-T014: 目次エントリ解析テスト

    US2: 章・節タイトルの構造化
    - 章パターン: `第N章 タイトル`
    - 節パターン: `N.N タイトル`
    - 項パターン: `N.N.N タイトル`
    - ページ番号抽出: ドットリーダー（...）、罫線（───）、空白区切り
    """

    # T012: 章パターン（第N章）抽出テスト

    def test_parse_chapter_pattern_basic(self) -> None:
        """Chapter N パターンを解析"""
        from src.book_converter.parser import parse_toc_entry
        from src.book_converter.models import TocEntry

        result = parse_toc_entry("Chapter 1 SRE Overview")

        assert result is not None
        assert isinstance(result, TocEntry)
        assert result.level == 1  # Phase 2: str → int
        assert result.number == "1"
        assert result.text == "SRE Overview"

    def test_parse_chapter_pattern_with_page_dots(self) -> None:
        """Chapter N パターン + ドットリーダーページ番号"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("Chapter 1 SRE Overview ... 15")

        assert result is not None
        assert result.level == 1  # Phase 2: str → int
        assert result.number == "1"
        assert result.text == "SRE Overview"
        assert result.page == "15"

    def test_parse_chapter_pattern_with_page_line(self) -> None:
        """Chapter N パターン + 罫線ページ番号"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("Chapter 2 Reliability Definition ─── 25")

        assert result is not None
        assert result.level == 1  # Phase 2: str → int
        assert result.number == "2"
        assert result.text == "Reliability Definition"
        assert result.page == "25"

    def test_parse_chapter_pattern_double_digit(self) -> None:
        """2桁の章番号を解析"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("Chapter 10 Summary ... 200")

        assert result is not None
        assert result.level == 1  # Phase 2: str → int
        assert result.number == "10"
        assert result.text == "Summary"
        assert result.page == "200"

    # T013: 節パターン（N.N、N.N.N）抽出テスト

    def test_parse_section_pattern_basic(self) -> None:
        """N.Nパターンを解析"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("2.1 SLOの理解")

        assert result is not None
        assert result.level == 2  # Phase 2: str → int
        assert result.number == "2.1"
        assert result.text == "SLOの理解"

    def test_parse_section_pattern_with_page(self) -> None:
        """N.Nパターン + ページ番号"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("2.1 SLOの理解 ... 30")

        assert result is not None
        assert result.level == 2  # Phase 2: str → int
        assert result.number == "2.1"
        assert result.text == "SLOの理解"
        assert result.page == "30"

    def test_parse_subsection_pattern_basic(self) -> None:
        """N.N.Nパターンを解析"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("2.1.1 SLA")

        assert result is not None
        assert result.level == 3  # Phase 2: str → int
        assert result.number == "2.1.1"
        assert result.text == "SLA"

    def test_parse_subsection_pattern_with_page(self) -> None:
        """N.N.Nパターン + ページ番号"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("2.1.1 SLA ─── 35")

        assert result is not None
        assert result.level == 3  # Phase 2: str → int
        assert result.number == "2.1.1"
        assert result.text == "SLA"
        assert result.page == "35"

    def test_parse_section_double_digit(self) -> None:
        """2桁の節番号を解析"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("10.12 高度な設定 ... 150")

        assert result is not None
        assert result.level == 2  # Phase 2: str → int
        assert result.number == "10.12"
        assert result.text == "高度な設定"
        assert result.page == "150"

    # T014: ページ番号抽出テスト（ドットリーダー、罫線形式）

    def test_parse_page_number_with_dots(self) -> None:
        """ドットリーダー形式のページ番号"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("第1章 タイトル ... 42")

        assert result is not None
        assert result.page == "42"

    def test_parse_page_number_with_multiple_dots(self) -> None:
        """複数のドットを含む形式"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("第1章 タイトル ........ 42")

        assert result is not None
        assert result.page == "42"

    def test_parse_page_number_with_horizontal_line(self) -> None:
        """罫線形式のページ番号"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("第1章 タイトル ─── 42")

        assert result is not None
        assert result.page == "42"

    def test_parse_page_number_with_dashes(self) -> None:
        """ダッシュ形式のページ番号"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("第1章 タイトル --- 42")

        assert result is not None
        assert result.page == "42"

    def test_parse_page_number_with_spaces(self) -> None:
        """空白区切りのページ番号"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("第1章 タイトル   42")

        assert result is not None
        assert result.page == "42"

    def test_parse_entry_without_page_number(self) -> None:
        """ページ番号なしのエントリ"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("第1章 タイトル")

        assert result is not None
        assert result.page == ""

    def test_parse_page_number_three_digits(self) -> None:
        """3桁のページ番号"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("第15章 付録 ... 999")

        assert result is not None
        assert result.page == "999"

    # その他のパターン（other）

    def test_parse_other_pattern_hajimeni(self) -> None:
        """「はじめに」パターン"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("はじめに ... 1")

        assert result is not None
        assert result.level == 1  # Phase 2: str → int (other → 1)
        assert result.number == ""
        assert result.text == "はじめに"
        assert result.page == "1"

    def test_parse_other_pattern_owarini(self) -> None:
        """「おわりに」パターン"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("おわりに ─── 300")

        assert result is not None
        assert result.level == 1  # Phase 2: str → int (other → 1)
        assert result.number == ""
        assert result.text == "おわりに"
        assert result.page == "300"

    def test_parse_other_pattern_index(self) -> None:
        """「索引」パターン"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("索引 ... 320")

        assert result is not None
        assert result.level == 1  # Phase 2: str → int (other → 1)
        assert result.text == "索引"
        assert result.page == "320"

    def test_parse_toc_entry_empty_line(self) -> None:
        """空行はNoneを返す"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("")

        assert result is None

    def test_parse_toc_entry_whitespace_only(self) -> None:
        """空白のみはNoneを返す"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("   ")

        assert result is None

    def test_parse_toc_entry_preserves_unicode(self) -> None:
        """Unicode文字を正しく保持"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("Chapter 3 「Japanese」Test ... 50")

        assert result is not None
        assert result.text == "「Japanese」Test"


class TestTocModels:
    """T015: TocEntry/TableOfContentsモデルテスト

    US1: データモデルが正しく定義されていることを確認
    """

    def test_toc_entry_exists(self) -> None:
        """TocEntryクラスが存在する"""
        from src.book_converter.models import TocEntry

        assert TocEntry is not None

    def test_toc_entry_is_dataclass(self) -> None:
        """TocEntryはdataclass"""
        from dataclasses import is_dataclass
        from src.book_converter.models import TocEntry

        assert is_dataclass(TocEntry)

    def test_toc_entry_is_frozen(self) -> None:
        """TocEntryはイミュータブル"""
        from src.book_converter.models import TocEntry

        entry = TocEntry(text="テスト", level=1, number="1", page="10")  # Phase 2: int level

        with pytest.raises(Exception):
            entry.text = "変更"  # type: ignore

    def test_toc_entry_required_fields(self) -> None:
        """TocEntryの必須フィールド"""
        from src.book_converter.models import TocEntry

        entry = TocEntry(text="SREとは", level=1)  # Phase 2: int level

        assert entry.text == "SREとは"
        assert entry.level == 1  # Phase 2: str → int

    def test_toc_entry_optional_fields_defaults(self) -> None:
        """TocEntryのオプションフィールドのデフォルト値"""
        from src.book_converter.models import TocEntry

        entry = TocEntry(text="テスト", level=1)  # Phase 2: int level

        assert entry.number == ""
        assert entry.page == ""

    def test_toc_entry_level_chapter(self) -> None:
        """level=1のエントリ（旧 'chapter'）"""
        from src.book_converter.models import TocEntry

        entry = TocEntry(text="第1章", level=1, number="1", page="15")  # Phase 2: int level

        assert entry.level == 1  # Phase 2: str → int
        assert entry.number == "1"

    def test_toc_entry_level_section(self) -> None:
        """level=2のエントリ（旧 'section'）"""
        from src.book_converter.models import TocEntry

        entry = TocEntry(text="節タイトル", level=2, number="1.2", page="20")  # Phase 2: int level

        assert entry.level == 2  # Phase 2: str → int
        assert entry.number == "1.2"

    def test_toc_entry_level_subsection(self) -> None:
        """level=3のエントリ（旧 'subsection'）"""
        from src.book_converter.models import TocEntry

        entry = TocEntry(text="項タイトル", level=3, number="1.2.3", page="25")  # Phase 2: int level

        assert entry.level == 3  # Phase 2: str → int
        assert entry.number == "1.2.3"

    def test_toc_entry_level_other(self) -> None:
        """level=1のエントリ（旧 'other'）"""
        from src.book_converter.models import TocEntry

        entry = TocEntry(text="はじめに", level=1, page="1")  # Phase 2: int level

        assert entry.level == 1  # Phase 2: str → int (other → 1)
        assert entry.number == ""

    def test_table_of_contents_exists(self) -> None:
        """TableOfContentsクラスが存在する"""
        from src.book_converter.models import TableOfContents

        assert TableOfContents is not None

    def test_table_of_contents_is_dataclass(self) -> None:
        """TableOfContentsはdataclass"""
        from dataclasses import is_dataclass
        from src.book_converter.models import TableOfContents

        assert is_dataclass(TableOfContents)

    def test_table_of_contents_is_frozen(self) -> None:
        """TableOfContentsはイミュータブル"""
        from src.book_converter.models import TocEntry, TableOfContents

        entry = TocEntry(text="テスト", level="chapter")
        toc = TableOfContents(entries=(entry,))

        with pytest.raises(Exception):
            toc.entries = ()  # type: ignore

    def test_table_of_contents_with_entries(self) -> None:
        """TableOfContentsがエントリを保持"""
        from src.book_converter.models import TocEntry, TableOfContents

        entry1 = TocEntry(text="第1章", level="chapter", number="1", page="15")
        entry2 = TocEntry(text="1.1 節", level="section", number="1.1", page="20")

        toc = TableOfContents(entries=(entry1, entry2))

        assert len(toc.entries) == 2
        assert toc.entries[0].text == "第1章"
        assert toc.entries[1].text == "1.1 節"

    def test_marker_type_exists(self) -> None:
        """MarkerType列挙が存在する"""
        from src.book_converter.models import MarkerType

        assert MarkerType is not None

    def test_marker_type_toc_start(self) -> None:
        """MarkerType.TOC_STARTの値"""
        from src.book_converter.models import MarkerType

        assert MarkerType.TOC_START.value == "toc_start"

    def test_marker_type_toc_end(self) -> None:
        """MarkerType.TOC_ENDの値"""
        from src.book_converter.models import MarkerType

        assert MarkerType.TOC_END.value == "toc_end"

    def test_marker_type_is_enum(self) -> None:
        """MarkerTypeはEnum"""
        from enum import Enum
        from src.book_converter.models import MarkerType

        assert issubclass(MarkerType, Enum)


# =============================================================================
# Phase 4 (004-toc-structure): US4 コンテンツ範囲マーカー
# =============================================================================


class TestParseContentMarker:
    """T050: contentマーカー検出テスト (parse_content_marker)

    US4: コンテンツ範囲マーカーによる読み上げ制御
    - `<!-- content -->` マーカーで読み上げ対象範囲開始を検出
    - `<!-- /content -->` マーカーで読み上げ対象範囲終了を検出
    - 大文字小文字を区別しない
    """

    def test_parse_content_start_marker(self) -> None:
        """content開始マーカーを検出"""
        from src.book_converter.parser import parse_content_marker
        from src.book_converter.models import MarkerType

        result = parse_content_marker("<!-- content -->")

        assert result is not None
        assert result == MarkerType.CONTENT_START

    def test_parse_content_end_marker(self) -> None:
        """content終了マーカーを検出"""
        from src.book_converter.parser import parse_content_marker
        from src.book_converter.models import MarkerType

        result = parse_content_marker("<!-- /content -->")

        assert result is not None
        assert result == MarkerType.CONTENT_END

    def test_parse_content_marker_case_insensitive_lowercase(self) -> None:
        """小文字のcontentマーカーを検出"""
        from src.book_converter.parser import parse_content_marker
        from src.book_converter.models import MarkerType

        result = parse_content_marker("<!-- content -->")

        assert result == MarkerType.CONTENT_START

    def test_parse_content_marker_case_insensitive_uppercase(self) -> None:
        """大文字のCONTENTマーカーを検出"""
        from src.book_converter.parser import parse_content_marker
        from src.book_converter.models import MarkerType

        result = parse_content_marker("<!-- CONTENT -->")

        assert result == MarkerType.CONTENT_START

    def test_parse_content_marker_case_insensitive_mixed(self) -> None:
        """大文字小文字混在のContentマーカーを検出"""
        from src.book_converter.parser import parse_content_marker
        from src.book_converter.models import MarkerType

        result = parse_content_marker("<!-- Content -->")

        assert result == MarkerType.CONTENT_START

    def test_parse_content_marker_with_extra_spaces(self) -> None:
        """余分なスペースがあっても検出"""
        from src.book_converter.parser import parse_content_marker
        from src.book_converter.models import MarkerType

        result = parse_content_marker("<!--   content   -->")

        assert result == MarkerType.CONTENT_START

    def test_parse_content_end_marker_uppercase(self) -> None:
        """大文字の終了マーカーを検出"""
        from src.book_converter.parser import parse_content_marker
        from src.book_converter.models import MarkerType

        result = parse_content_marker("<!-- /CONTENT -->")

        assert result == MarkerType.CONTENT_END

    def test_parse_content_marker_with_leading_spaces(self) -> None:
        """先頭にスペースがあっても検出"""
        from src.book_converter.parser import parse_content_marker
        from src.book_converter.models import MarkerType

        result = parse_content_marker("  <!-- content -->")

        assert result == MarkerType.CONTENT_START

    def test_parse_non_content_marker_returns_none(self) -> None:
        """contentマーカーでない行はNoneを返す"""
        from src.book_converter.parser import parse_content_marker

        non_content_lines = [
            "<!-- toc -->",
            "<!-- /toc -->",
            "# 見出し",
            "本文テキスト",
            "<!-- FIGURE: image.png -->",
            "",
            "   ",
            "<!-- contents -->",  # typo
        ]
        for line in non_content_lines:
            result = parse_content_marker(line)
            assert result is None, f"Expected None for line: {line!r}"


class TestParseSkipMarker:
    """T051: skipマーカー検出テスト

    US4: コンテンツ範囲マーカーによる読み上げ制御
    - `<!-- skip -->` マーカーで読み上げ非対象範囲開始を検出
    - `<!-- /skip -->` マーカーで読み上げ非対象範囲終了を検出
    - 大文字小文字を区別しない
    """

    def test_parse_skip_start_marker(self) -> None:
        """skip開始マーカーを検出"""
        from src.book_converter.parser import parse_content_marker
        from src.book_converter.models import MarkerType

        result = parse_content_marker("<!-- skip -->")

        assert result is not None
        assert result == MarkerType.SKIP_START

    def test_parse_skip_end_marker(self) -> None:
        """skip終了マーカーを検出"""
        from src.book_converter.parser import parse_content_marker
        from src.book_converter.models import MarkerType

        result = parse_content_marker("<!-- /skip -->")

        assert result is not None
        assert result == MarkerType.SKIP_END

    def test_parse_skip_marker_case_insensitive_uppercase(self) -> None:
        """大文字のSKIPマーカーを検出"""
        from src.book_converter.parser import parse_content_marker
        from src.book_converter.models import MarkerType

        result = parse_content_marker("<!-- SKIP -->")

        assert result == MarkerType.SKIP_START

    def test_parse_skip_marker_case_insensitive_mixed(self) -> None:
        """大文字小文字混在のSkipマーカーを検出"""
        from src.book_converter.parser import parse_content_marker
        from src.book_converter.models import MarkerType

        result = parse_content_marker("<!-- Skip -->")

        assert result == MarkerType.SKIP_START

    def test_parse_skip_marker_with_extra_spaces(self) -> None:
        """余分なスペースがあっても検出"""
        from src.book_converter.parser import parse_content_marker
        from src.book_converter.models import MarkerType

        result = parse_content_marker("<!--   skip   -->")

        assert result == MarkerType.SKIP_START

    def test_parse_skip_end_marker_uppercase(self) -> None:
        """大文字の終了マーカーを検出"""
        from src.book_converter.parser import parse_content_marker
        from src.book_converter.models import MarkerType

        result = parse_content_marker("<!-- /SKIP -->")

        assert result == MarkerType.SKIP_END

    def test_parse_skip_marker_with_leading_spaces(self) -> None:
        """先頭にスペースがあっても検出"""
        from src.book_converter.parser import parse_content_marker
        from src.book_converter.models import MarkerType

        result = parse_content_marker("  <!-- skip -->")

        assert result == MarkerType.SKIP_START

    def test_parse_non_skip_marker_returns_none(self) -> None:
        """skipマーカーでない行はNoneを返す"""
        from src.book_converter.parser import parse_content_marker

        non_skip_lines = [
            "<!-- toc -->",
            "<!-- content -->",
            "# 見出し",
            "本文テキスト",
            "<!-- skips -->",  # typo
        ]
        for line in non_skip_lines:
            result = parse_content_marker(line)
            # contentマーカーはCONTENT_STARTを返す、それ以外はNone
            if "content" not in line.lower() or "contents" in line.lower():
                assert result is None, f"Expected None for line: {line!r}"


class TestMarkerStateStack:
    """T052: マーカー状態スタックテスト (ネスト処理)

    US4: マーカーがネストした場合の動作
    - 空スタック → readAloud=true (デフォルトで読む)
    - "content"をpush → readAloud=true
    - "skip"をpush → readAloud=false
    - pop → 前の状態に戻る
    """

    def test_get_read_aloud_from_empty_stack(self) -> None:
        """空スタックからreadAloudを取得 → true (デフォルトで読む)"""
        from src.book_converter.parser import get_read_aloud_from_stack

        stack = []
        result = get_read_aloud_from_stack(stack)

        assert result is True

    def test_get_read_aloud_with_content_on_stack(self) -> None:
        """スタックにcontentがある → true"""
        from src.book_converter.parser import get_read_aloud_from_stack

        stack = ["content"]
        result = get_read_aloud_from_stack(stack)

        assert result is True

    def test_get_read_aloud_with_skip_on_stack(self) -> None:
        """スタックにskipがある → false"""
        from src.book_converter.parser import get_read_aloud_from_stack

        stack = ["skip"]
        result = get_read_aloud_from_stack(stack)

        assert result is False

    def test_get_read_aloud_nested_skip_in_content(self) -> None:
        """content内にskipがネスト → false (内側優先)"""
        from src.book_converter.parser import get_read_aloud_from_stack

        stack = ["content", "skip"]
        result = get_read_aloud_from_stack(stack)

        assert result is False

    def test_get_read_aloud_nested_content_in_skip(self) -> None:
        """skip内にcontentがネスト → true (内側優先)"""
        from src.book_converter.parser import get_read_aloud_from_stack

        stack = ["skip", "content"]
        result = get_read_aloud_from_stack(stack)

        assert result is True

    def test_get_read_aloud_after_pop_skip_from_content(self) -> None:
        """content内でskipをpopした後 → true"""
        from src.book_converter.parser import get_read_aloud_from_stack

        stack = ["content", "skip"]
        stack.pop()  # skipをpop
        result = get_read_aloud_from_stack(stack)

        assert result is True

    def test_get_read_aloud_after_pop_content(self) -> None:
        """contentをpopした後 → true (空スタック=デフォルトで読む)"""
        from src.book_converter.parser import get_read_aloud_from_stack

        stack = ["content"]
        stack.pop()  # contentをpop
        result = get_read_aloud_from_stack(stack)

        assert result is True

    def test_get_read_aloud_deep_nesting(self) -> None:
        """深いネスト: content → skip → content → skip"""
        from src.book_converter.parser import get_read_aloud_from_stack

        # content(true) → skip(false) → content(true) → skip(false)
        stack = ["content", "skip", "content", "skip"]
        result = get_read_aloud_from_stack(stack)

        assert result is False  # 最も内側がskip

    def test_get_read_aloud_deep_nesting_ending_with_content(self) -> None:
        """深いネスト: skip → content → skip → content"""
        from src.book_converter.parser import get_read_aloud_from_stack

        stack = ["skip", "content", "skip", "content"]
        result = get_read_aloud_from_stack(stack)

        assert result is True  # 最も内側がcontent

    def test_stack_manipulation_sequence(self) -> None:
        """スタック操作のシーケンスをテスト"""
        from src.book_converter.parser import get_read_aloud_from_stack

        stack = []

        # 初期状態: 空 → true (デフォルトで読む)
        assert get_read_aloud_from_stack(stack) is True

        # content追加 → true
        stack.append("content")
        assert get_read_aloud_from_stack(stack) is True

        # skip追加 → false
        stack.append("skip")
        assert get_read_aloud_from_stack(stack) is False

        # skip削除 → true
        stack.pop()
        assert get_read_aloud_from_stack(stack) is True

        # content削除 → true (空スタック=デフォルトで読む)
        stack.pop()
        assert get_read_aloud_from_stack(stack) is True


class TestMarkerTypeContentSkip:
    """MarkerType列挙のcontent/skip値テスト"""

    def test_marker_type_content_start(self) -> None:
        """MarkerType.CONTENT_STARTの値"""
        from src.book_converter.models import MarkerType

        assert MarkerType.CONTENT_START.value == "content_start"

    def test_marker_type_content_end(self) -> None:
        """MarkerType.CONTENT_ENDの値"""
        from src.book_converter.models import MarkerType

        assert MarkerType.CONTENT_END.value == "content_end"

    def test_marker_type_skip_start(self) -> None:
        """MarkerType.SKIP_STARTの値"""
        from src.book_converter.models import MarkerType

        assert MarkerType.SKIP_START.value == "skip_start"

    def test_marker_type_skip_end(self) -> None:
        """MarkerType.SKIP_ENDの値"""
        from src.book_converter.models import MarkerType

        assert MarkerType.SKIP_END.value == "skip_end"


# =============================================================================
# Phase 2 (006-fix-toc-line-merge): US1 TOC改行分割エントリの結合
# =============================================================================


class TestMergeTocLinesChapter:
    """T009: merge_toc_linesテスト - Chapter結合

    US1: TOC改行分割エントリの結合
    - 「Chapter」単独行と次の「N タイトル」行を結合
    - FR-001: Chapter単独行 + 次行 → 「Chapter N タイトル」として解析
    """

    def test_merge_chapter_with_number_title(self) -> None:
        """「Chapter」と「1 「企画」で失敗」を結合"""
        from src.book_converter.parser import merge_toc_lines

        lines = [
            "Chapter",
            "1 「企画」で失敗",
        ]
        result = merge_toc_lines(lines)

        assert len(result) == 1
        assert result[0] == "Chapter 1 「企画」で失敗"

    def test_merge_chapter_with_number_title_2(self) -> None:
        """「Chapter」と「2 「仕様」で失敗」を結合"""
        from src.book_converter.parser import merge_toc_lines

        lines = [
            "Chapter",
            "2 「仕様」で失敗",
        ]
        result = merge_toc_lines(lines)

        assert len(result) == 1
        assert result[0] == "Chapter 2 「仕様」で失敗"

    def test_merge_multiple_chapters_in_sequence(self) -> None:
        """複数のChapterエントリを順番に結合"""
        from src.book_converter.parser import merge_toc_lines

        lines = [
            "Chapter",
            "1 「企画」で失敗",
            "Chapter",
            "2 「仕様」で失敗",
            "Chapter",
            "3 「設計」で失敗",
        ]
        result = merge_toc_lines(lines)

        assert len(result) == 3
        assert result[0] == "Chapter 1 「企画」で失敗"
        assert result[1] == "Chapter 2 「仕様」で失敗"
        assert result[2] == "Chapter 3 「設計」で失敗"

    def test_merge_chapter_with_empty_line_between(self) -> None:
        """Chapterと次行の間に空行がある場合も結合"""
        from src.book_converter.parser import merge_toc_lines

        lines = [
            "Chapter",
            "",
            "1 「企画」で失敗",
        ]
        result = merge_toc_lines(lines)

        assert len(result) == 1
        assert result[0] == "Chapter 1 「企画」で失敗"

    def test_chapter_standalone_not_followed_by_valid_line(self) -> None:
        """Chapter単独行の後に有効な行がない場合は結合しない"""
        from src.book_converter.parser import merge_toc_lines

        lines = [
            "Chapter",
            "おわりに ... 300",  # 番号パターンでない
        ]
        result = merge_toc_lines(lines)

        # Chapter単独は保持され、次行も保持される
        assert len(result) == 2
        assert result[0] == "Chapter"
        assert result[1] == "おわりに ... 300"

    def test_merge_chapter_preserves_unicode(self) -> None:
        """Unicode文字を含むタイトルを正しく保持"""
        from src.book_converter.parser import merge_toc_lines

        lines = [
            "Chapter",
            "5 「日本語」テスト",
        ]
        result = merge_toc_lines(lines)

        assert len(result) == 1
        assert result[0] == "Chapter 5 「日本語」テスト"


class TestMergeTocLinesEpisode:
    """T010: merge_toc_linesテスト - Episode結合

    US1: TOC改行分割エントリの結合
    - 「Episode NN」行と次のタイトル行を結合
    - FR-002: Episode NN + 次行 → 「Episode NN タイトル」として解析
    """

    def test_merge_episode_with_title(self) -> None:
        """「Episode 01」と「なんでもできる「全部入りソフトウェア」」を結合"""
        from src.book_converter.parser import merge_toc_lines

        lines = [
            "Episode 01",
            "なんでもできる「全部入りソフトウェア」",
        ]
        result = merge_toc_lines(lines)

        assert len(result) == 1
        assert result[0] == "Episode 01 なんでもできる「全部入りソフトウェア」"

    def test_merge_episode_02_with_title(self) -> None:
        """「Episode 02」と「みんなの願いをかなえたい「八方美人仕様」」を結合"""
        from src.book_converter.parser import merge_toc_lines

        lines = [
            "Episode 02",
            "みんなの願いをかなえたい「八方美人仕様」",
        ]
        result = merge_toc_lines(lines)

        assert len(result) == 1
        assert result[0] == "Episode 02 みんなの願いをかなえたい「八方美人仕様」"

    def test_merge_multiple_episodes_in_sequence(self) -> None:
        """複数のEpisodeエントリを順番に結合"""
        from src.book_converter.parser import merge_toc_lines

        lines = [
            "Episode 01",
            "タイトル1",
            "Episode 02",
            "タイトル2",
            "Episode 03",
            "タイトル3",
        ]
        result = merge_toc_lines(lines)

        assert len(result) == 3
        assert result[0] == "Episode 01 タイトル1"
        assert result[1] == "Episode 02 タイトル2"
        assert result[2] == "Episode 03 タイトル3"

    def test_merge_episode_with_multiword_title(self) -> None:
        """Episodeの後に複数単語のタイトル"""
        from src.book_converter.parser import merge_toc_lines

        lines = [
            "Episode 24",
            "テスト テスト2 テスト3",
        ]
        result = merge_toc_lines(lines)

        assert len(result) == 1
        assert result[0] == "Episode 24 テスト テスト2 テスト3"

    def test_episode_without_number_not_merged(self) -> None:
        """「Episode」単独（番号なし）は結合しない"""
        from src.book_converter.parser import merge_toc_lines

        lines = [
            "Episode",
            "タイトル",
        ]
        result = merge_toc_lines(lines)

        # Episode単独は結合対象外
        assert len(result) == 2
        assert result[0] == "Episode"
        assert result[1] == "タイトル"

    def test_merge_episode_preserves_page_number(self) -> None:
        """ページ番号を含む次行も正しく結合"""
        from src.book_converter.parser import merge_toc_lines

        lines = [
            "Episode 01",
            "なんでもできる「全部入りソフトウェア」 ... 10",
        ]
        result = merge_toc_lines(lines)

        assert len(result) == 1
        assert "Episode 01" in result[0]
        assert "なんでもできる" in result[0]
        assert "10" in result[0]


class TestMergeTocLinesColumn:
    """T011: merge_toc_linesテスト - Column結合

    US1: TOC改行分割エントリの結合
    - 「Column」単独行と次のタイトル行を結合
    - FR-003: Column + 次行 → 「Column タイトル」として解析
    """

    def test_merge_column_with_title(self) -> None:
        """「Column」と「何を、なぜ作るのかが最重要」を結合"""
        from src.book_converter.parser import merge_toc_lines

        lines = [
            "Column",
            "何を、なぜ作るのかが最重要",
        ]
        result = merge_toc_lines(lines)

        assert len(result) == 1
        assert result[0] == "Column 何を、なぜ作るのかが最重要"

    def test_merge_column_with_page_number(self) -> None:
        """Column結合後にページ番号が続く場合"""
        from src.book_converter.parser import merge_toc_lines

        lines = [
            "Column",
            "重要なポイント ... 50",
        ]
        result = merge_toc_lines(lines)

        assert len(result) == 1
        assert result[0] == "Column 重要なポイント ... 50"

    def test_merge_multiple_columns_in_sequence(self) -> None:
        """複数のColumnエントリを順番に結合"""
        from src.book_converter.parser import merge_toc_lines

        lines = [
            "Column",
            "コラム1",
            "Column",
            "コラム2",
        ]
        result = merge_toc_lines(lines)

        assert len(result) == 2
        assert result[0] == "Column コラム1"
        assert result[1] == "Column コラム2"

    def test_merge_column_with_empty_line_between(self) -> None:
        """Columnと次行の間に空行がある場合も結合"""
        from src.book_converter.parser import merge_toc_lines

        lines = [
            "Column",
            "",
            "空行の後のタイトル",
        ]
        result = merge_toc_lines(lines)

        assert len(result) == 1
        assert result[0] == "Column 空行の後のタイトル"

    def test_column_preserves_special_characters(self) -> None:
        """特殊文字を含むタイトルを保持"""
        from src.book_converter.parser import merge_toc_lines

        lines = [
            "Column",
            "Q&A: よくある質問 「回答」",
        ]
        result = merge_toc_lines(lines)

        assert len(result) == 1
        assert result[0] == "Column Q&A: よくある質問 「回答」"


class TestNormalizeTocLineEmphasis:
    """T012: normalize_toc_lineテスト - **強調**除去

    US1: TOC改行分割エントリの結合
    - マークダウン強調記号（**）を除去
    - FR-007: **Episode 24** → Episode 24 として認識
    """

    def test_normalize_removes_emphasis_episode(self) -> None:
        """**Episode 24** → Episode 24"""
        from src.book_converter.parser import normalize_toc_line

        result = normalize_toc_line("**Episode 24**")

        assert result == "Episode 24"

    def test_normalize_removes_emphasis_column(self) -> None:
        """**Column** → Column"""
        from src.book_converter.parser import normalize_toc_line

        result = normalize_toc_line("**Column**")

        assert result == "Column"

    def test_normalize_removes_emphasis_chapter(self) -> None:
        """**Chapter** → Chapter"""
        from src.book_converter.parser import normalize_toc_line

        result = normalize_toc_line("**Chapter**")

        assert result == "Chapter"

    def test_normalize_mixed_emphasis_and_text(self) -> None:
        """**Episode 01** タイトル → Episode 01 タイトル"""
        from src.book_converter.parser import normalize_toc_line

        result = normalize_toc_line("**Episode 01** タイトル")

        assert result == "Episode 01 タイトル"

    def test_normalize_multiple_emphasis_blocks(self) -> None:
        """複数の**ブロック**を除去"""
        from src.book_converter.parser import normalize_toc_line

        result = normalize_toc_line("**前半** 中間 **後半**")

        assert result == "前半 中間 後半"

    def test_normalize_preserves_text_without_emphasis(self) -> None:
        """強調なしのテキストはそのまま"""
        from src.book_converter.parser import normalize_toc_line

        result = normalize_toc_line("通常のテキスト")

        assert result == "通常のテキスト"

    def test_normalize_removes_heading_markers_and_emphasis(self) -> None:
        """### **Episode 24** → Episode 24"""
        from src.book_converter.parser import normalize_toc_line

        result = normalize_toc_line("### **Episode 24**")

        assert result == "Episode 24"

    def test_normalize_single_asterisk_not_removed(self) -> None:
        """単一の*は除去しない（強調は**のみ）"""
        from src.book_converter.parser import normalize_toc_line

        result = normalize_toc_line("*イタリック*テスト")

        # 単一アスタリスク（イタリック）の扱いは実装依存
        # 少なくとも内容は保持される
        assert "イタリック" in result or "*イタリック*" in result


class TestParseTocEntryChapterFormat:
    """T013: parse_toc_entryテスト - Chapter N形式認識

    US1: TOC改行分割エントリの結合
    - 「Chapter N タイトル」形式を認識
    - FR-004: Chapter N形式をlevel="chapter", number="N"として認識
    """

    def test_parse_chapter_n_format(self) -> None:
        """「Chapter 1 「企画」で失敗」をchapterとして認識"""
        from src.book_converter.parser import parse_toc_entry
        from src.book_converter.models import TocEntry

        result = parse_toc_entry("Chapter 1 「企画」で失敗")

        assert result is not None
        assert isinstance(result, TocEntry)
        assert result.level == 1  # Phase 2: str → int
        assert result.number == "1"
        assert result.text == "「企画」で失敗"

    def test_parse_chapter_10_format(self) -> None:
        """「Chapter 10 まとめ」をchapterとして認識（2桁）"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("Chapter 10 まとめ")

        assert result is not None
        assert result.level == 1  # Phase 2: str → int
        assert result.number == "10"
        assert result.text == "まとめ"

    def test_parse_chapter_with_page_number_dots(self) -> None:
        """「Chapter 1 タイトル ... 15」のページ番号を抽出"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("Chapter 1 タイトル ... 15")

        assert result is not None
        assert result.level == 1  # Phase 2: str → int
        assert result.number == "1"
        assert result.text == "タイトル"
        assert result.page == "15"

    def test_parse_chapter_with_page_number_dashes(self) -> None:
        """「Chapter 2 タイトル --- 25」のページ番号を抽出"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("Chapter 2 タイトル --- 25")

        assert result is not None
        assert result.level == 1  # Phase 2: str → int
        assert result.number == "2"
        assert result.text == "タイトル"
        assert result.page == "25"

    def test_parse_chapter_case_insensitive(self) -> None:
        """「CHAPTER 1 タイトル」も認識（大文字小文字を区別しない）"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("CHAPTER 1 タイトル")

        assert result is not None
        assert result.level == 1  # Phase 2: str → int
        assert result.number == "1"

    def test_parse_chapter_lowercase(self) -> None:
        """「chapter 1 タイトル」も認識（小文字）"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("chapter 1 タイトル")

        assert result is not None
        assert result.level == 1  # Phase 2: str → int
        assert result.number == "1"

    def test_parse_chapter_preserves_unicode_title(self) -> None:
        """Unicodeタイトルを正しく保持"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("Chapter 3 「日本語」タイトル「テスト」")

        assert result is not None
        assert result.level == 1  # Phase 2: str → int
        assert result.number == "3"
        assert result.text == "「日本語」タイトル「テスト」"

    def test_parse_chapter_without_title(self) -> None:
        """「Chapter 1」のみ（タイトルなし）"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("Chapter 1")

        # タイトルなしの場合も認識すべき
        assert result is not None
        assert result.level == 1  # Phase 2: str → int
        assert result.number == "1"
        assert result.text == ""


class TestMergeTocLinesMixed:
    """merge_toc_linesの混合テスト - Chapter, Episode, Column混在"""

    def test_merge_mixed_entries(self) -> None:
        """Chapter、Episode、Columnが混在するTOC"""
        from src.book_converter.parser import merge_toc_lines

        lines = [
            "Chapter",
            "1 はじめに",
            "Episode 01",
            "ソフトウェアの話",
            "Column",
            "重要なポイント",
            "Chapter",
            "2 まとめ",
        ]
        result = merge_toc_lines(lines)

        assert len(result) == 4
        assert result[0] == "Chapter 1 はじめに"
        assert result[1] == "Episode 01 ソフトウェアの話"
        assert result[2] == "Column 重要なポイント"
        assert result[3] == "Chapter 2 まとめ"

    def test_merge_preserves_non_mergeable_lines(self) -> None:
        """結合対象外の行は保持"""
        from src.book_converter.parser import merge_toc_lines

        lines = [
            "はじめに ... 1",
            "Chapter",
            "1 本編",
            "おわりに ... 300",
        ]
        result = merge_toc_lines(lines)

        assert len(result) == 3
        assert result[0] == "はじめに ... 1"
        assert result[1] == "Chapter 1 本編"
        assert result[2] == "おわりに ... 300"

    def test_merge_empty_list(self) -> None:
        """空リストは空リストを返す"""
        from src.book_converter.parser import merge_toc_lines

        result = merge_toc_lines([])

        assert result == []

    def test_merge_single_non_mergeable_line(self) -> None:
        """単一の結合不要行"""
        from src.book_converter.parser import merge_toc_lines

        result = merge_toc_lines(["第1章 SREとは ... 15"])

        assert len(result) == 1
        assert result[0] == "第1章 SREとは ... 15"


# =============================================================================
# Phase 2 (009-converter-redesign): T009 parse_toc_entry level数値化テスト
# =============================================================================


class TestParseTocEntryLevelNumeric:
    """T009: parse_toc_entry level数値化テスト

    User Story 1 - TOC階層構造の正確な反映
    parse_toc_entry が level を int (1-5) で返すことを確認
    """

    def test_parse_toc_entry_level_numeric_chapter(self) -> None:
        """parse_toc_entry が Chapter を level=1 (int) で返す"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("第1章 SREとは ... 15")

        assert result is not None
        assert result.level == 1
        assert isinstance(result.level, int)

    def test_parse_toc_entry_level_numeric_section(self) -> None:
        """parse_toc_entry が Section を level=2 (int) で返す"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("2.1 SLOの理解 ... 30")

        assert result is not None
        assert result.level == 2
        assert isinstance(result.level, int)

    def test_parse_toc_entry_level_numeric_subsection(self) -> None:
        """parse_toc_entry が Subsection を level=3 (int) で返す"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("2.1.1 SLI ... 35")

        assert result is not None
        assert result.level == 3
        assert isinstance(result.level, int)

    def test_parse_toc_entry_level_numeric_episode(self) -> None:
        """parse_toc_entry が Episode を適切な level (int) で返す"""
        from src.book_converter.parser import parse_toc_entry

        # Episode は level 2 相当
        result = parse_toc_entry("Episode 01 ソフトウェアの話 ... 20")

        assert result is not None
        assert isinstance(result.level, int)
        assert result.level >= 1
        assert result.level <= 5

    def test_parse_toc_entry_level_numeric_other(self) -> None:
        """parse_toc_entry が その他 を適切な level (int) で返す"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("はじめに ... 1")

        assert result is not None
        assert isinstance(result.level, int)
        # その他でも 1-5 の範囲
        assert result.level >= 1
        assert result.level <= 5

    def test_parse_toc_entry_level_not_string(self) -> None:
        """parse_toc_entry の level は文字列ではない"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("第1章 テスト ... 10")

        assert result is not None
        # level は "chapter" ではなく int
        assert result.level != "chapter"
        assert isinstance(result.level, int)

    def test_parse_toc_entry_level_1_for_chapter_en(self) -> None:
        """parse_toc_entry が Chapter (英語) を level=1 (int) で返す"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("Chapter 1 Introduction ... 5")

        assert result is not None
        assert result.level == 1
        assert isinstance(result.level, int)

    def test_parse_toc_entry_preserves_text_and_number(self) -> None:
        """parse_toc_entry が text, number, page を正しく保持"""
        from src.book_converter.parser import parse_toc_entry

        result = parse_toc_entry("Chapter 2 Design Patterns ... 50")

        assert result is not None
        assert result.text == "Design Patterns"
        assert result.number == "2"
        assert result.page == "50"
        assert result.level == 1
        assert isinstance(result.level, int)


# =============================================================================
# Phase 2 (009-converter-redesign): T010 TOC階層3レベル以上テスト
# =============================================================================


class TestTocHierarchyMultiLevel:
    """T010: TOC階層3レベル以上テスト

    User Story 1 - TOC階層構造の正確な反映
    複数階層（3レベル以上）のTOCが正しくパースされることを確認
    """

    def test_toc_hierarchy_3_levels(self) -> None:
        """3レベルの階層を持つTOCをパース"""
        from src.book_converter.parser import parse_toc_entry

        # Level 1: Chapter
        level1 = parse_toc_entry("第1章 SREとは ... 15")
        # Level 2: Section
        level2 = parse_toc_entry("1.1 SREの定義 ... 16")
        # Level 3: Subsection
        level3 = parse_toc_entry("1.1.1 歴史的背景 ... 17")

        assert level1 is not None
        assert level2 is not None
        assert level3 is not None

        assert level1.level == 1
        assert level2.level == 2
        assert level3.level == 3

        assert isinstance(level1.level, int)
        assert isinstance(level2.level, int)
        assert isinstance(level3.level, int)

    def test_toc_hierarchy_4_levels(self) -> None:
        """4レベルの階層を持つTOCをパース"""
        from src.book_converter.parser import parse_toc_entry

        level1 = parse_toc_entry("第1章 概要 ... 10")
        level2 = parse_toc_entry("1.1 導入 ... 11")
        level3 = parse_toc_entry("1.1.1 背景 ... 12")
        level4 = parse_toc_entry("1.1.1.1 詳細 ... 13")

        assert level1 is not None
        assert level2 is not None
        assert level3 is not None
        assert level4 is not None

        assert level1.level == 1
        assert level2.level == 2
        assert level3.level == 3
        assert level4.level == 4

    def test_toc_hierarchy_5_levels(self) -> None:
        """5レベルの階層を持つTOCをパース"""
        from src.book_converter.parser import parse_toc_entry

        level1 = parse_toc_entry("第1章 概要 ... 10")
        level2 = parse_toc_entry("1.1 導入 ... 11")
        level3 = parse_toc_entry("1.1.1 背景 ... 12")
        level4 = parse_toc_entry("1.1.1.1 詳細 ... 13")
        level5 = parse_toc_entry("1.1.1.1.1 補足 ... 14")

        assert level1 is not None
        assert level2 is not None
        assert level3 is not None
        assert level4 is not None
        assert level5 is not None

        assert level1.level == 1
        assert level2.level == 2
        assert level3.level == 3
        assert level4.level == 4
        assert level5.level == 5

    def test_toc_hierarchy_mixed_levels_order(self) -> None:
        """混在した階層順序でのパース"""
        from src.book_converter.parser import parse_toc_entry

        # Level 1 -> 2 -> 3 -> 2 -> 1 の順序
        entries = [
            ("第1章 はじめに ... 1", 1),
            ("1.1 概要 ... 2", 2),
            ("1.1.1 詳細 ... 3", 3),
            ("1.2 まとめ ... 10", 2),
            ("第2章 本編 ... 20", 1),
        ]

        for line, expected_level in entries:
            result = parse_toc_entry(line)
            assert result is not None, f"Failed to parse: {line}"
            assert result.level == expected_level, f"Expected level {expected_level} for: {line}"
            assert isinstance(result.level, int)

    def test_toc_hierarchy_level_values_are_integers(self) -> None:
        """全ての階層レベルが整数値である"""
        from src.book_converter.parser import parse_toc_entry

        test_cases = [
            "第1章 テスト ... 10",
            "1.1 テスト ... 11",
            "1.1.1 テスト ... 12",
            "1.1.1.1 テスト ... 13",
            "1.1.1.1.1 テスト ... 14",
        ]

        for line in test_cases:
            result = parse_toc_entry(line)
            if result is not None:
                assert isinstance(result.level, int), f"level should be int for: {line}"
                assert 1 <= result.level <= 5, f"level should be 1-5 for: {line}"

    def test_toc_hierarchy_unicode_titles(self) -> None:
        """Unicode タイトルを含む多階層TOC"""
        from src.book_converter.parser import parse_toc_entry

        entries = [
            ("第1章 日本語タイトル「テスト」 ... 10", 1),
            ("1.1 サブセクション ... 11", 2),
            ("1.1.1 詳細な説明 ... 12", 3),
        ]

        for line, expected_level in entries:
            result = parse_toc_entry(line)
            assert result is not None
            assert result.level == expected_level
            assert isinstance(result.level, int)


# =============================================================================
# Phase 4: User Story 3 - paragraph の論理的分離 (T042-T045)
# =============================================================================


class TestParseParagraphRemoveNewlines:
    """T042: paragraph改行除去テスト (parse_paragraph_lines)

    段落内の改行を除去し、連続テキストとして結合する。
    空白の圧縮も行う。
    """

    def test_parse_paragraph_remove_newlines_basic(self) -> None:
        """複数行が改行なしで結合される"""
        from src.book_converter.parser import parse_paragraph_lines

        lines = ["Line 1", "Line 2", "Line 3"]
        result = parse_paragraph_lines(lines)

        assert result is not None
        # 改行を除去し、スペースで結合
        assert result.text == "Line 1 Line 2 Line 3"
        assert "\n" not in result.text

    def test_parse_paragraph_remove_newlines_japanese(self) -> None:
        """日本語段落の改行除去"""
        from src.book_converter.parser import parse_paragraph_lines

        lines = [
            "これは段落の最初の行です。",
            "これは段落の2行目です。",
            "これは段落の3行目です。",
        ]
        result = parse_paragraph_lines(lines)

        assert result is not None
        # 日本語はスペースなしで直接結合するか、1スペースで結合
        # 仕様: 空白1文字で結合
        expected = "これは段落の最初の行です。 これは段落の2行目です。 これは段落の3行目です。"
        assert result.text == expected
        assert "\n" not in result.text

    def test_parse_paragraph_remove_newlines_single_line(self) -> None:
        """1行の段落は改行なしでそのまま"""
        from src.book_converter.parser import parse_paragraph_lines

        result = parse_paragraph_lines(["Single line paragraph."])

        assert result is not None
        assert result.text == "Single line paragraph."

    def test_parse_paragraph_consecutive_spaces_compression(self) -> None:
        """連続空白を1つに圧縮"""
        from src.book_converter.parser import parse_paragraph_lines

        lines = ["Text with   multiple", "spaces    here"]
        result = parse_paragraph_lines(lines)

        assert result is not None
        # 行末と行頭の空白、および連続空白を圧縮
        assert "   " not in result.text
        assert "    " not in result.text
        # 適切に結合されている
        assert "Text with" in result.text
        assert "spaces" in result.text

    def test_parse_paragraph_empty_list_returns_none(self) -> None:
        """空リストはNoneを返す"""
        from src.book_converter.parser import parse_paragraph_lines

        result = parse_paragraph_lines([])

        assert result is None

    def test_parse_paragraph_whitespace_only_returns_none(self) -> None:
        """空白のみの行リストはNoneを返す"""
        from src.book_converter.parser import parse_paragraph_lines

        result = parse_paragraph_lines(["   ", "  ", "\t"])

        assert result is None

    def test_parse_paragraph_preserves_content(self) -> None:
        """内容は保持される（Unicode含む）"""
        from src.book_converter.parser import parse_paragraph_lines

        lines = ["Unicode: 日本語、「括弧」、絵文字テスト。"]
        result = parse_paragraph_lines(lines)

        assert result is not None
        assert "日本語" in result.text
        assert "「括弧」" in result.text

    def test_parse_paragraph_read_aloud_default_true(self) -> None:
        """デフォルトでread_aloud=True"""
        from src.book_converter.parser import parse_paragraph_lines

        result = parse_paragraph_lines(["Test paragraph."])

        assert result is not None
        assert result.read_aloud is True


class TestParagraphSplitByBlankLines:
    """T043: 空行による段落分離テスト (split_paragraphs)

    空行で区切られたテキストが複数のParagraphになることを確認。
    """

    def test_split_paragraphs_by_blank_lines_basic(self) -> None:
        """空行で区切られた3段落"""
        from src.book_converter.parser import split_paragraphs

        text = "段落1の内容。\n\n段落2の内容。\n\n段落3の内容。"
        result = split_paragraphs(text)

        assert len(result) == 3
        assert result[0].text == "段落1の内容。"
        assert result[1].text == "段落2の内容。"
        assert result[2].text == "段落3の内容。"

    def test_split_paragraphs_multiple_blank_lines(self) -> None:
        """複数の空行も単一の区切りとして扱う"""
        from src.book_converter.parser import split_paragraphs

        text = "段落1。\n\n\n\n段落2。"
        result = split_paragraphs(text)

        assert len(result) == 2
        assert result[0].text == "段落1。"
        assert result[1].text == "段落2。"

    def test_split_paragraphs_single_paragraph(self) -> None:
        """空行がない場合は1つの段落"""
        from src.book_converter.parser import split_paragraphs

        text = "これは1つの段落です。改行はあるけど空行はない。"
        result = split_paragraphs(text)

        assert len(result) == 1
        assert result[0].text == "これは1つの段落です。改行はあるけど空行はない。"

    def test_split_paragraphs_multiline_in_paragraph(self) -> None:
        """段落内の改行は除去される"""
        from src.book_converter.parser import split_paragraphs

        text = "行1\n行2\n行3\n\n段落2行1\n段落2行2"
        result = split_paragraphs(text)

        assert len(result) == 2
        # 段落内の改行は除去（スペースに変換）
        assert result[0].text == "行1 行2 行3"
        assert result[1].text == "段落2行1 段落2行2"

    def test_split_paragraphs_empty_text(self) -> None:
        """空テキストは空リスト"""
        from src.book_converter.parser import split_paragraphs

        result = split_paragraphs("")

        assert len(result) == 0

    def test_split_paragraphs_only_blank_lines(self) -> None:
        """空行のみは空リスト"""
        from src.book_converter.parser import split_paragraphs

        result = split_paragraphs("\n\n\n")

        assert len(result) == 0

    def test_split_paragraphs_returns_paragraph_objects(self) -> None:
        """Paragraphオブジェクトのリストを返す"""
        from src.book_converter.parser import split_paragraphs
        from src.book_converter.models import Paragraph

        result = split_paragraphs("テスト。")

        assert len(result) == 1
        assert isinstance(result[0], Paragraph)

    def test_split_paragraphs_leading_trailing_blank_lines(self) -> None:
        """先頭・末尾の空行は無視"""
        from src.book_converter.parser import split_paragraphs

        text = "\n\n段落1。\n\n段落2。\n\n"
        result = split_paragraphs(text)

        assert len(result) == 2


class TestWhitespaceOnlyLineAsBlank:
    """T044: スペースのみの行を空行として扱うテスト

    スペースやタブのみの行も空行として扱い、段落を区切る。
    """

    def test_space_only_line_as_blank(self) -> None:
        """スペースのみの行は空行として扱う"""
        from src.book_converter.parser import split_paragraphs

        # "   " はスペース3つ
        text = "段落1。\n   \n段落2。"
        result = split_paragraphs(text)

        assert len(result) == 2
        assert result[0].text == "段落1。"
        assert result[1].text == "段落2。"

    def test_tab_only_line_as_blank(self) -> None:
        """タブのみの行は空行として扱う"""
        from src.book_converter.parser import split_paragraphs

        text = "段落1。\n\t\n段落2。"
        result = split_paragraphs(text)

        assert len(result) == 2
        assert result[0].text == "段落1。"
        assert result[1].text == "段落2。"

    def test_mixed_whitespace_line_as_blank(self) -> None:
        """スペースとタブの混在も空行として扱う"""
        from src.book_converter.parser import split_paragraphs

        text = "段落1。\n \t  \t \n段落2。"
        result = split_paragraphs(text)

        assert len(result) == 2
        assert result[0].text == "段落1。"
        assert result[1].text == "段落2。"

    def test_full_width_space_as_blank(self) -> None:
        """全角スペースのみの行も空行として扱う"""
        from src.book_converter.parser import split_paragraphs

        text = "段落1。\n\u3000\n段落2。"  # \u3000 = 全角スペース
        result = split_paragraphs(text)

        assert len(result) == 2
        assert result[0].text == "段落1。"
        assert result[1].text == "段落2。"

    def test_consecutive_whitespace_lines(self) -> None:
        """複数の空白行が連続しても1つの区切り"""
        from src.book_converter.parser import split_paragraphs

        text = "段落1。\n   \n\t\n  \n段落2。"
        result = split_paragraphs(text)

        assert len(result) == 2

    def test_whitespace_line_does_not_create_empty_paragraph(self) -> None:
        """空白行は空の段落を生成しない"""
        from src.book_converter.parser import split_paragraphs

        text = "段落1。\n   \n\n   \n段落2。"
        result = split_paragraphs(text)

        # 2つの段落のみ、空の段落は生成されない
        assert len(result) == 2
        for para in result:
            assert para.text.strip() != ""


class TestParagraphContinuationAcrossPages:
    """T045: ページまたぎ段落結合テスト (merge_continuation_paragraphs)

    句点で終わらない段落は次ページの段落と結合する。
    """

    def test_continuation_basic(self) -> None:
        """句点なしの段落は次と結合"""
        from src.book_converter.parser import merge_continuation_paragraphs
        from src.book_converter.models import Paragraph

        paragraphs = [
            Paragraph(text="継続する文章の途中", read_aloud=True),
            Paragraph(text="続きの文。", read_aloud=True),
        ]
        result = merge_continuation_paragraphs(paragraphs)

        assert len(result) == 1
        assert result[0].text == "継続する文章の途中続きの文。"

    def test_no_continuation_with_period(self) -> None:
        """句点で終わる段落は結合しない"""
        from src.book_converter.parser import merge_continuation_paragraphs
        from src.book_converter.models import Paragraph

        paragraphs = [
            Paragraph(text="完結する文章。", read_aloud=True),
            Paragraph(text="新しい段落。", read_aloud=True),
        ]
        result = merge_continuation_paragraphs(paragraphs)

        assert len(result) == 2
        assert result[0].text == "完結する文章。"
        assert result[1].text == "新しい段落。"

    def test_continuation_multiple_paragraphs(self) -> None:
        """複数の継続段落を結合"""
        from src.book_converter.parser import merge_continuation_paragraphs
        from src.book_converter.models import Paragraph

        paragraphs = [
            Paragraph(text="段落1の途中", read_aloud=True),
            Paragraph(text="段落1の続き", read_aloud=True),
            Paragraph(text="段落1の終わり。", read_aloud=True),
            Paragraph(text="新しい段落2。", read_aloud=True),
        ]
        result = merge_continuation_paragraphs(paragraphs)

        assert len(result) == 2
        assert result[0].text == "段落1の途中段落1の続き段落1の終わり。"
        assert result[1].text == "新しい段落2。"

    def test_continuation_exclamation_mark(self) -> None:
        """感嘆符で終わる段落は結合しない"""
        from src.book_converter.parser import merge_continuation_paragraphs
        from src.book_converter.models import Paragraph

        paragraphs = [
            Paragraph(text="感嘆の文章!", read_aloud=True),
            Paragraph(text="次の段落。", read_aloud=True),
        ]
        result = merge_continuation_paragraphs(paragraphs)

        assert len(result) == 2

    def test_continuation_question_mark(self) -> None:
        """疑問符で終わる段落は結合しない"""
        from src.book_converter.parser import merge_continuation_paragraphs
        from src.book_converter.models import Paragraph

        paragraphs = [
            Paragraph(text="疑問の文章?", read_aloud=True),
            Paragraph(text="次の段落。", read_aloud=True),
        ]
        result = merge_continuation_paragraphs(paragraphs)

        assert len(result) == 2

    def test_continuation_japanese_period(self) -> None:
        """日本語句点（。）で終わる段落は結合しない"""
        from src.book_converter.parser import merge_continuation_paragraphs
        from src.book_converter.models import Paragraph

        paragraphs = [
            Paragraph(text="日本語の文章。", read_aloud=True),
            Paragraph(text="次の文章。", read_aloud=True),
        ]
        result = merge_continuation_paragraphs(paragraphs)

        assert len(result) == 2

    def test_continuation_closing_bracket_period(self) -> None:
        """閉じ括弧+句点で終わる段落は結合しない"""
        from src.book_converter.parser import merge_continuation_paragraphs
        from src.book_converter.models import Paragraph

        paragraphs = [
            Paragraph(text="引用（テスト）。", read_aloud=True),
            Paragraph(text="次の文章。", read_aloud=True),
        ]
        result = merge_continuation_paragraphs(paragraphs)

        assert len(result) == 2

    def test_continuation_empty_list(self) -> None:
        """空リストは空リストを返す"""
        from src.book_converter.parser import merge_continuation_paragraphs

        result = merge_continuation_paragraphs([])

        assert len(result) == 0

    def test_continuation_single_paragraph(self) -> None:
        """1つの段落はそのまま"""
        from src.book_converter.parser import merge_continuation_paragraphs
        from src.book_converter.models import Paragraph

        paragraphs = [Paragraph(text="単独の段落。", read_aloud=True)]
        result = merge_continuation_paragraphs(paragraphs)

        assert len(result) == 1
        assert result[0].text == "単独の段落。"

    def test_continuation_preserves_read_aloud(self) -> None:
        """結合時にread_aloud属性を保持（先頭の値を使用）"""
        from src.book_converter.parser import merge_continuation_paragraphs
        from src.book_converter.models import Paragraph

        paragraphs = [
            Paragraph(text="途中", read_aloud=True),
            Paragraph(text="終わり。", read_aloud=False),
        ]
        result = merge_continuation_paragraphs(paragraphs)

        assert len(result) == 1
        # 先頭の段落のread_aloudを使用
        assert result[0].read_aloud is True

    def test_continuation_trailing_whitespace_period(self) -> None:
        """句点の後に空白がある場合も結合しない"""
        from src.book_converter.parser import merge_continuation_paragraphs
        from src.book_converter.models import Paragraph

        paragraphs = [
            Paragraph(text="文章。   ", read_aloud=True),  # 末尾に空白
            Paragraph(text="次の文。", read_aloud=True),
        ]
        result = merge_continuation_paragraphs(paragraphs)

        # 空白を除去して判定するので結合しない
        assert len(result) == 2


# =============================================================================
# Phase 5 (009-converter-redesign): T060 図プレースホルダー検出テスト
# =============================================================================


class TestParseFigurePlaceholder:
    """T060: 図プレースホルダー検出テスト

    User Story 4 - list/figure要素の出力
    "[図]", "[図1]", "[写真]", "[表]", "[イラスト]" などを検出する
    """

    def test_parse_figure_placeholder_exists(self) -> None:
        """parse_figure_placeholder 関数が存在する"""
        from src.book_converter.parser import parse_figure_placeholder

        assert callable(parse_figure_placeholder)

    def test_detect_simple_figure(self) -> None:
        """[図] を検出"""
        from src.book_converter.parser import parse_figure_placeholder

        result = parse_figure_placeholder("[図]")

        assert result is not None
        assert result["marker"] == "図"

    def test_detect_figure_with_number(self) -> None:
        """[図1] を検出"""
        from src.book_converter.parser import parse_figure_placeholder

        result = parse_figure_placeholder("[図1]")

        assert result is not None
        assert result["marker"] == "図1"

    def test_detect_figure_with_space_number(self) -> None:
        """[図 1] を検出（スペース付き）"""
        from src.book_converter.parser import parse_figure_placeholder

        result = parse_figure_placeholder("[図 1]")

        assert result is not None
        assert result["marker"] == "図 1"

    def test_detect_figure_with_hyphen_number(self) -> None:
        """[図1-1] を検出"""
        from src.book_converter.parser import parse_figure_placeholder

        result = parse_figure_placeholder("[図1-1]")

        assert result is not None
        assert result["marker"] == "図1-1"

    def test_detect_photo(self) -> None:
        """[写真] を検出"""
        from src.book_converter.parser import parse_figure_placeholder

        result = parse_figure_placeholder("[写真]")

        assert result is not None
        assert result["marker"] == "写真"

    def test_detect_photo_with_number(self) -> None:
        """[写真1] を検出"""
        from src.book_converter.parser import parse_figure_placeholder

        result = parse_figure_placeholder("[写真1]")

        assert result is not None
        assert result["marker"] == "写真1"

    def test_detect_table(self) -> None:
        """[表] を検出"""
        from src.book_converter.parser import parse_figure_placeholder

        result = parse_figure_placeholder("[表]")

        assert result is not None
        assert result["marker"] == "表"

    def test_detect_table_with_number(self) -> None:
        """[表1] を検出"""
        from src.book_converter.parser import parse_figure_placeholder

        result = parse_figure_placeholder("[表1]")

        assert result is not None
        assert result["marker"] == "表1"

    def test_detect_illustration(self) -> None:
        """[イラスト] を検出"""
        from src.book_converter.parser import parse_figure_placeholder

        result = parse_figure_placeholder("[イラスト]")

        assert result is not None
        assert result["marker"] == "イラスト"

    def test_detect_graph(self) -> None:
        """[グラフ] を検出"""
        from src.book_converter.parser import parse_figure_placeholder

        result = parse_figure_placeholder("[グラフ]")

        assert result is not None
        assert result["marker"] == "グラフ"

    def test_detect_chart(self) -> None:
        """[チャート] を検出"""
        from src.book_converter.parser import parse_figure_placeholder

        result = parse_figure_placeholder("[チャート]")

        assert result is not None
        assert result["marker"] == "チャート"

    def test_non_figure_returns_none(self) -> None:
        """図プレースホルダーでない行はNoneを返す"""
        from src.book_converter.parser import parse_figure_placeholder

        non_figure_lines = [
            "本文テキスト",
            "# 見出し",
            "- リスト項目",
            "[リンク](url)",
            "[注釈]",  # 図ではない
            "図1",  # 括弧なし
            "(図1)",  # 丸括弧
        ]

        for line in non_figure_lines:
            result = parse_figure_placeholder(line)
            assert result is None, f"Expected None for: {line!r}"

    def test_detect_figure_in_line(self) -> None:
        """行の中に含まれるプレースホルダーを検出"""
        from src.book_converter.parser import parse_figure_placeholder

        result = parse_figure_placeholder("本文の途中に[図1]がある場合")

        assert result is not None
        assert result["marker"] == "図1"

    def test_detect_multiple_figures_returns_first(self) -> None:
        """複数プレースホルダーがある場合は最初のものを返す"""
        from src.book_converter.parser import parse_figure_placeholder

        result = parse_figure_placeholder("[図1]と[図2]")

        assert result is not None
        # 最初のプレースホルダーを返す
        assert result["marker"] == "図1"

    def test_figure_with_label(self) -> None:
        """[図1：キャプション] 形式を検出"""
        from src.book_converter.parser import parse_figure_placeholder

        result = parse_figure_placeholder("[図1：システム構成図]")

        assert result is not None
        # marker部分のみ抽出、またはラベル全体を含む
        assert "図1" in result["marker"]

    def test_empty_line_returns_none(self) -> None:
        """空行はNoneを返す"""
        from src.book_converter.parser import parse_figure_placeholder

        result = parse_figure_placeholder("")

        assert result is None

    def test_whitespace_only_returns_none(self) -> None:
        """空白のみの行はNoneを返す"""
        from src.book_converter.parser import parse_figure_placeholder

        result = parse_figure_placeholder("   ")

        assert result is None


class TestLegacyPatternRemovalInParser:
    """Phase 5 T079: Legacy backward compatibility patterns should be removed.

    These tests verify that the legacy patterns marked for removal in
    specs/010-pipeline-refactoring/plan.md have been removed.

    Category A (Remove):
    - book_converter/parser.py:584 - "Legacy patterns below for backward compatibility"
    - book_converter/parser.py:597 - "Chapter pattern 2: ... - legacy"
    """

    def test_parser_has_no_legacy_patterns_comment(self) -> None:
        """parser.py should not have 'Legacy patterns' comment marker."""
        import inspect
        from src.book_converter import parser

        # Get the parse_toc_line function source
        # Note: We check the module source to find the legacy section
        module_source = inspect.getsource(parser)

        assert "Legacy patterns below for backward compatibility" not in module_source, (
            "parser.py should not contain 'Legacy patterns below for backward compatibility'. "
            "This comment and the associated legacy patterns should be removed."
        )

    def test_parser_has_no_legacy_annotation(self) -> None:
        """parser.py should not have '- legacy' annotations in comments."""
        import inspect
        from src.book_converter import parser

        module_source = inspect.getsource(parser)

        # Check for the specific legacy annotation pattern
        assert "- legacy" not in module_source, (
            "parser.py should not contain '- legacy' annotations. "
            "Remove the redundant legacy Chapter pattern."
        )

    def test_parser_no_character_class_case_insensitive_pattern(self) -> None:
        """parser.py should not use [Cc][Hh]... style case insensitivity.

        The legacy Chapter pattern uses character-by-character case insensitivity:
        [Cc][Hh][Aa][Pp][Tt][Ee][Rr]

        This is redundant because the new pattern uses re.IGNORECASE flag.
        """
        import inspect
        from src.book_converter import parser

        module_source = inspect.getsource(parser)

        # The character-class case-insensitive pattern is a signature of legacy code
        assert "[Cc][Hh][Aa][Pp][Tt][Ee][Rr]" not in module_source, (
            "parser.py should not use character-class case insensitivity. "
            "The new pattern with re.IGNORECASE handles case insensitivity."
        )

    def test_parser_uses_ignorecase_for_chapter(self) -> None:
        """parser.py should use re.IGNORECASE for Chapter pattern."""
        import inspect
        from src.book_converter import parser

        module_source = inspect.getsource(parser)

        # Verify the new pattern exists with IGNORECASE
        # The new format uses: re.match(..., line, re.IGNORECASE)
        assert "re.IGNORECASE" in module_source, (
            "parser.py should use re.IGNORECASE flag for case-insensitive matching. "
            "This is the modern approach instead of character classes."
        )
