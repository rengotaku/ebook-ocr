"""Parser tests for book markdown to XML conversion.

Tests for Phase 2: User Story 1 - TTS Page Navigation and Audio Announcement
- T009: Page marker parsing (parse_page_marker)
- T010: Page number extraction (normal, missing, edge cases)
- T011: PageAnnouncement test ("N page" format)
"""

import pytest

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
