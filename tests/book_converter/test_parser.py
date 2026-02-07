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
