"""Tests for heading normalizer - Phase 2 RED tests.

US1: 見出しパターンの自動抽出
- T007: 番号フォーマット正規化テスト
- T008: スペース正規化テスト
- T009: 特殊マーカー検出テスト
- T010: 見出し抽出・分類テスト
"""

from __future__ import annotations

import pytest

from src.book_converter.parser.heading_normalizer import (
    HeadingCategory,
    HeadingInfo,
    classify_heading_patterns,
    extract_headings,
    is_special_marker,
    normalize_number_format,
    normalize_spaces,
)


def _wrap_content(lines: list[str]) -> list[str]:
    """Wrap lines with content markers for testing."""
    return ["<!-- content -->", *lines, "<!-- /content -->"]


# ============================================================
# T007: 番号フォーマット正規化テスト
# ============================================================


class TestNormalizeNumberFormat:
    """番号フォーマットをドット区切り半角に統一するテスト"""

    # --- ハイフン → ドット ---

    def test_normalize_hyphen_to_dot_simple(self) -> None:
        """ハイフン区切りをドット区切りに変換: 1-1 → 1.1"""
        assert normalize_number_format("1-1") == "1.1"

    def test_normalize_hyphen_to_dot_three_levels(self) -> None:
        """3階層ハイフン区切り: 1-1-1 → 1.1.1"""
        assert normalize_number_format("1-1-1") == "1.1.1"

    def test_normalize_hyphen_to_dot_with_title(self) -> None:
        """タイトル付きハイフン区切り: 1-1-1 サイトとは何か → 1.1.1 サイトとは何か"""
        assert normalize_number_format("1-1-1 サイトとは何か") == "1.1.1 サイトとは何か"

    # --- 全角 → 半角 ---

    def test_normalize_fullwidth_to_halfwidth_numbers(self) -> None:
        """全角数字を半角に変換: １．１ → 1.1"""
        assert normalize_number_format("１．１") == "1.1"

    def test_normalize_fullwidth_to_halfwidth_three_levels(self) -> None:
        """3階層全角: １．１．１ → 1.1.1"""
        assert normalize_number_format("１．１．１") == "1.1.1"

    def test_normalize_fullwidth_numbers_only(self) -> None:
        """全角数字のみ(ドット半角): １.１ → 1.1"""
        assert normalize_number_format("１.１") == "1.1"

    def test_normalize_fullwidth_with_title(self) -> None:
        """全角番号+タイトル: １．１ SREの概要 → 1.1 SREの概要"""
        assert normalize_number_format("１．１ SREの概要") == "1.1 SREの概要"

    # --- 中黒 → ドット ---

    def test_normalize_nakaguro_to_dot(self) -> None:
        """中黒をドットに変換: 1・1 → 1.1"""
        assert normalize_number_format("1・1") == "1.1"

    def test_normalize_nakaguro_to_dot_three_levels(self) -> None:
        """3階層中黒: 1・1・1 → 1.1.1"""
        assert normalize_number_format("1・1・1") == "1.1.1"

    # --- 混合パターン ---

    def test_normalize_mixed_separators(self) -> None:
        """混合区切り: 1-1・1 → 1.1.1"""
        assert normalize_number_format("1-1・1") == "1.1.1"

    # --- 変換不要 ---

    def test_normalize_already_normalized(self) -> None:
        """既にドット区切り半角の場合は変更なし"""
        assert normalize_number_format("1.1.1") == "1.1.1"

    def test_normalize_no_number(self) -> None:
        """番号がない場合は変更なし"""
        assert normalize_number_format("SREの概要") == "SREの概要"

    def test_normalize_single_number(self) -> None:
        """単独数字は変更なし"""
        assert normalize_number_format("1") == "1"

    # --- エッジケース ---

    def test_normalize_empty_string(self) -> None:
        """空文字列"""
        assert normalize_number_format("") == ""

    def test_normalize_fullwidth_zero(self) -> None:
        """全角ゼロ: ０．１ → 0.1"""
        assert normalize_number_format("０．１") == "0.1"

    def test_normalize_large_numbers(self) -> None:
        """大きい番号: 12-34-56 → 12.34.56"""
        assert normalize_number_format("12-34-56") == "12.34.56"

    def test_normalize_preserves_non_number_hyphens(self) -> None:
        """テキスト中のハイフンは保持: SRE-based → SRE-based"""
        assert normalize_number_format("SRE-based") == "SRE-based"


# ============================================================
# T008: スペース正規化テスト
# ============================================================


class TestNormalizeSpaces:
    """番号周辺の余分なスペースを除去するテスト"""

    # --- 章・節周辺のスペース ---

    def test_normalize_chapter_spaces(self) -> None:
        """章周辺のスペース除去: 第 1 章 → 第1章"""
        assert normalize_spaces("第 1 章") == "第1章"

    def test_normalize_section_spaces(self) -> None:
        """節周辺のスペース: 第 2 節 → 第2節"""
        assert normalize_spaces("第 2 節") == "第2節"

    def test_normalize_chapter_with_title(self) -> None:
        """章+タイトル: 第 1 章 SREとは → 第1章 SREとは"""
        assert normalize_spaces("第 1 章 SREとは") == "第1章 SREとは"

    # --- 番号内スペース ---

    def test_normalize_number_spaces_dot(self) -> None:
        """番号内スペース(ドット後): 1. 1 → 1.1"""
        assert normalize_spaces("1. 1") == "1.1"

    def test_normalize_number_spaces_three_levels(self) -> None:
        """3階層番号内スペース: 1. 1. 1 → 1.1.1"""
        assert normalize_spaces("1. 1. 1") == "1.1.1"

    def test_normalize_number_spaces_with_title(self) -> None:
        """番号+タイトル: 1. 1 SREの概要 → 1.1 SREの概要"""
        assert normalize_spaces("1. 1 SREの概要") == "1.1 SREの概要"

    # --- 変換不要 ---

    def test_normalize_spaces_already_clean(self) -> None:
        """既にスペースなしの場合は変更なし"""
        assert normalize_spaces("第1章") == "第1章"

    def test_normalize_spaces_number_clean(self) -> None:
        """既に番号内スペースなし"""
        assert normalize_spaces("1.1") == "1.1"

    def test_normalize_spaces_title_space_preserved(self) -> None:
        """タイトル前のスペースは保持: 1.1 SREの概要"""
        assert normalize_spaces("1.1 SREの概要") == "1.1 SREの概要"

    # --- エッジケース ---

    def test_normalize_spaces_empty_string(self) -> None:
        """空文字列"""
        assert normalize_spaces("") == ""

    def test_normalize_spaces_only_spaces(self) -> None:
        """スペースのみの文字列は空になる可能性"""
        result = normalize_spaces("   ")
        assert isinstance(result, str)

    def test_normalize_spaces_multiple_spaces_in_number(self) -> None:
        """番号内に複数スペース: 1.  1 → 1.1"""
        assert normalize_spaces("1.  1") == "1.1"

    def test_normalize_spaces_chapter_double_digit(self) -> None:
        """2桁章番号: 第 12 章 → 第12章"""
        assert normalize_spaces("第 12 章") == "第12章"


# ============================================================
# T009: 特殊マーカー検出テスト
# ============================================================


class TestIsSpecialMarker:
    """特殊マーカー（■、◆等）の検出テスト"""

    # --- 検出すべきマーカー ---

    def test_is_special_marker_square(self) -> None:
        """黒四角マーカー: ■コードベース → True"""
        assert is_special_marker("■コードベース") is True

    def test_is_special_marker_diamond(self) -> None:
        """菱形マーカー: ◆注意事項 → True"""
        assert is_special_marker("◆注意事項") is True

    def test_is_special_marker_white_square(self) -> None:
        """白四角マーカー: □補足 → True"""
        assert is_special_marker("□補足") is True

    def test_is_special_marker_black_circle(self) -> None:
        """黒丸マーカー: ●概要 → True"""
        assert is_special_marker("●概要") is True

    def test_is_special_marker_white_diamond(self) -> None:
        """白菱形マーカー: ◇参考 → True"""
        assert is_special_marker("◇参考") is True

    def test_is_special_marker_triangle(self) -> None:
        """三角マーカー: ▲警告 → True"""
        assert is_special_marker("▲警告") is True

    # --- 検出すべきでないもの ---

    def test_is_special_marker_normal_text(self) -> None:
        """通常テキスト: SREの概要 → False"""
        assert is_special_marker("SREの概要") is False

    def test_is_special_marker_numbered(self) -> None:
        """番号付きテキスト: 1.1 SREの概要 → False"""
        assert is_special_marker("1.1 SREの概要") is False

    def test_is_special_marker_english(self) -> None:
        """英語テキスト: Introduction → False"""
        assert is_special_marker("Introduction") is False

    def test_is_special_marker_with_markdown(self) -> None:
        """Markdownマーカーなしでテスト: マーカーはテキスト部分のみ判定"""
        assert is_special_marker("■コードの送信") is True

    # --- エッジケース ---

    def test_is_special_marker_empty(self) -> None:
        """空文字列 → False"""
        assert is_special_marker("") is False

    def test_is_special_marker_marker_only(self) -> None:
        """マーカーのみ: ■ → True"""
        assert is_special_marker("■") is True

    def test_is_special_marker_marker_in_middle(self) -> None:
        """マーカーが途中にある場合: SRE■概要 → False (先頭のみ判定)"""
        assert is_special_marker("SRE■概要") is False

    def test_is_special_marker_with_space(self) -> None:
        """マーカー後にスペース: ■ コードベース → True"""
        assert is_special_marker("■ コードベース") is True


# ============================================================
# T010: 見出し抽出・分類テスト
# ============================================================


class TestExtractHeadings:
    """book.md から見出し行を抽出するテスト"""

    def test_extract_headings_basic(self) -> None:
        """Markdown見出し行 (h1-h6) を抽出"""
        lines = _wrap_content(
            [
                "# タイトル",
                "本文テキスト",
                "## 1.1 SREの概要",
                "段落テキスト",
                "## 1.2 信頼性とは",
                "別の段落",
            ]
        )
        result = extract_headings(lines)

        assert len(result) == 3
        assert result[0].raw_text == "# タイトル"
        assert result[0].level == 1
        assert result[1].raw_text == "## 1.1 SREの概要"
        assert result[2].raw_text == "## 1.2 信頼性とは"

    def test_extract_headings_with_h3(self) -> None:
        """### も抽出する"""
        lines = _wrap_content(
            [
                "## 1.1 SREの概要",
                "テキスト",
                "### 1.1.1 サイトとは何か",
            ]
        )
        result = extract_headings(lines)

        assert len(result) == 2
        assert result[0].level == 2
        assert result[1].level == 3

    def test_extract_headings_line_numbers(self) -> None:
        """行番号が正しく記録される (1-indexed, content marker offset +1)"""
        lines = _wrap_content(
            [
                "本文",
                "## 最初の見出し",
                "本文",
                "本文",
                "## 2番目の見出し",
            ]
        )
        result = extract_headings(lines)

        assert len(result) == 2
        # +1 offset for <!-- content --> marker
        assert result[0].line_number == 3
        assert result[1].line_number == 6

    def test_extract_headings_numbered_category(self) -> None:
        """番号付き見出しが NUMBERED に分類される"""
        lines = _wrap_content(["## 1.1 SREの概要"])
        result = extract_headings(lines)

        assert len(result) == 1
        assert result[0].category == HeadingCategory.NUMBERED
        assert result[0].number == "1.1"
        assert result[0].title == "SREの概要"

    def test_extract_headings_unnumbered_category(self) -> None:
        """番号なし見出しが UNNUMBERED に分類される"""
        lines = _wrap_content(["## SREの概要"])
        result = extract_headings(lines)

        assert len(result) == 1
        assert result[0].category == HeadingCategory.UNNUMBERED
        assert result[0].number == ""
        assert result[0].title == "SREの概要"

    def test_extract_headings_special_marker_category(self) -> None:
        """特殊マーカー付き見出しが SPECIAL_MARKER に分類される"""
        lines = _wrap_content(["## ■コードベース"])
        result = extract_headings(lines)

        assert len(result) == 1
        assert result[0].category == HeadingCategory.SPECIAL_MARKER

    def test_extract_headings_empty_lines(self) -> None:
        """マーカーのみで見出しがない場合は空リストを返す"""
        lines = _wrap_content([])
        result = extract_headings(lines)
        assert result == []

    def test_extract_headings_no_headings(self) -> None:
        """見出しがない場合は空リストを返す"""
        lines = _wrap_content(["本文テキスト", "別の本文", "--- Page 1 ---"])
        result = extract_headings(lines)
        assert result == []

    def test_extract_headings_h1_included(self) -> None:
        """# (h1) も抽出対象"""
        lines = _wrap_content(
            [
                "# 書籍タイトル",
                "## 1.1 SREの概要",
            ]
        )
        result = extract_headings(lines)

        assert len(result) == 2
        assert result[0].raw_text == "# 書籍タイトル"
        assert result[0].level == 1
        assert result[1].raw_text == "## 1.1 SREの概要"

    def test_extract_headings_h4_included(self) -> None:
        """#### (h4) も抽出対象"""
        lines = _wrap_content(
            [
                "## 1.1 SREの概要",
                "#### サブサブセクション",
            ]
        )
        result = extract_headings(lines)

        assert len(result) == 2
        assert result[1].raw_text == "#### サブサブセクション"
        assert result[1].level == 4

    def test_extract_headings_preserves_order(self) -> None:
        """抽出結果は元の出現順序を保持"""
        lines = _wrap_content(
            [
                "## C見出し",
                "## A見出し",
                "## B見出し",
            ]
        )
        result = extract_headings(lines)

        assert len(result) == 3
        assert result[0].title == "C見出し"
        assert result[1].title == "A見出し"
        assert result[2].title == "B見出し"

    def test_extract_headings_with_special_chars(self) -> None:
        """Unicode/特殊文字を含む見出し"""
        lines = _wrap_content(["## 1.1 SRE (サイト信頼性エンジニアリング)"])
        result = extract_headings(lines)

        assert len(result) == 1
        assert "SRE" in result[0].title


class TestClassifyHeadingPatterns:
    """見出しをパターン別に分類するテスト"""

    def test_classify_all_numbered(self) -> None:
        """全て番号付き"""
        headings = [
            HeadingInfo(
                line_number=1,
                raw_text="## 1.1 SREの概要",
                level=2,
                title="SREの概要",
                number="1.1",
                category=HeadingCategory.NUMBERED,
            ),
            HeadingInfo(
                line_number=5,
                raw_text="## 1.2 信頼性",
                level=2,
                title="信頼性",
                number="1.2",
                category=HeadingCategory.NUMBERED,
            ),
        ]
        report = classify_heading_patterns(headings)

        assert report.total == 2
        assert report.numbered_count == 2
        assert report.unnumbered_count == 0
        assert report.special_marker_count == 0

    def test_classify_mixed_patterns(self) -> None:
        """番号あり/なし/マーカーの混合"""
        headings = [
            HeadingInfo(
                line_number=1,
                raw_text="## 1.1 SREの概要",
                level=2,
                title="SREの概要",
                number="1.1",
                category=HeadingCategory.NUMBERED,
            ),
            HeadingInfo(
                line_number=5,
                raw_text="## 信頼性とは",
                level=2,
                title="信頼性とは",
                number="",
                category=HeadingCategory.UNNUMBERED,
            ),
            HeadingInfo(
                line_number=10,
                raw_text="## ■コードベース",
                level=2,
                title="■コードベース",
                number="",
                category=HeadingCategory.SPECIAL_MARKER,
            ),
        ]
        report = classify_heading_patterns(headings)

        assert report.total == 3
        assert report.numbered_count == 1
        assert report.unnumbered_count == 1
        assert report.special_marker_count == 1

    def test_classify_empty_list(self) -> None:
        """空リスト"""
        report = classify_heading_patterns([])

        assert report.total == 0
        assert report.numbered_count == 0
        assert report.unnumbered_count == 0
        assert report.special_marker_count == 0

    def test_classify_includes_examples(self) -> None:
        """各カテゴリの代表例が含まれる"""
        headings = [
            HeadingInfo(
                line_number=1,
                raw_text="## 1.1 SREの概要",
                level=2,
                title="SREの概要",
                number="1.1",
                category=HeadingCategory.NUMBERED,
            ),
            HeadingInfo(
                line_number=5,
                raw_text="## 信頼性とは",
                level=2,
                title="信頼性とは",
                number="",
                category=HeadingCategory.UNNUMBERED,
            ),
        ]
        report = classify_heading_patterns(headings)

        assert len(report.numbered_examples) > 0
        assert len(report.unnumbered_examples) > 0
        assert report.special_marker_examples == ()

    def test_classify_report_is_immutable(self) -> None:
        """PatternReport は frozen dataclass"""
        report = classify_heading_patterns([])

        with pytest.raises(AttributeError):
            report.total = 99  # type: ignore[misc]

    def test_classify_large_dataset(self) -> None:
        """大量の見出し (1000件) でも正しく分類"""
        headings = [
            HeadingInfo(
                line_number=i,
                raw_text=f"## {i}.1 見出し{i}",
                level=2,
                title=f"見出し{i}",
                number=f"{i}.1",
                category=HeadingCategory.NUMBERED,
            )
            for i in range(1, 1001)
        ]
        report = classify_heading_patterns(headings)

        assert report.total == 1000
        assert report.numbered_count == 1000
