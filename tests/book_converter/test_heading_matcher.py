"""Tests for heading_matcher module - TOC-body heading matching engine.

Phase 3 RED tests for US2: TOC形式への見出し正規化
"""

from __future__ import annotations

import pytest

from src.book_converter.models import (
    Heading,
    MatchResult,
    MatchType,
    NormalizationAction,
    TocEntry,
)


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture()
def toc_entry_numbered() -> TocEntry:
    """番号付き TOC エントリ"""
    return TocEntry(text="SREの概要", level=2, number="1.1", page="015")


@pytest.fixture()
def toc_entry_deep_numbered() -> TocEntry:
    """3階層番号付き TOC エントリ"""
    return TocEntry(text="サイトとは何か", level=3, number="1.1.1", page="018")


@pytest.fixture()
def toc_entry_no_number() -> TocEntry:
    """番号なし TOC エントリ (はじめに等)"""
    return TocEntry(text="はじめに", level=1, number="", page="001")


@pytest.fixture()
def heading_with_number() -> Heading:
    """番号付き本文見出し"""
    return Heading(level=2, text="1.1 SREの概要")


@pytest.fixture()
def heading_without_number() -> Heading:
    """番号なし本文見出し"""
    return Heading(level=2, text="SREの概要")


@pytest.fixture()
def heading_fuzzy() -> Heading:
    """OCR誤認識を含む本文見出し (ファジーマッチ対象)"""
    return Heading(level=2, text="信頼性とは")


@pytest.fixture()
def heading_special_marker() -> Heading:
    """特殊マーカー付き本文見出し"""
    return Heading(level=2, text="■コードベース")


# ============================================================
# T026: MatchResult モデルテスト
# ============================================================


class TestMatchResultModel:
    """MatchResult データクラスの制約テスト"""

    def test_match_result_exact_similarity_is_one(
        self, toc_entry_numbered: TocEntry, heading_with_number: Heading
    ) -> None:
        """EXACT マッチの場合、similarity は 1.0 であること"""
        result = MatchResult(
            toc_entry=toc_entry_numbered,
            body_heading=heading_with_number,
            match_type=MatchType.EXACT,
            similarity=1.0,
            line_number=52,
        )
        assert result.match_type == MatchType.EXACT
        assert result.similarity == 1.0
        assert result.body_heading is not None
        assert result.line_number == 52

    def test_match_result_fuzzy_similarity_range(
        self, toc_entry_numbered: TocEntry, heading_fuzzy: Heading
    ) -> None:
        """FUZZY マッチの場合、0.8 <= similarity < 1.0 であること"""
        result = MatchResult(
            toc_entry=toc_entry_numbered,
            body_heading=heading_fuzzy,
            match_type=MatchType.FUZZY,
            similarity=0.85,
            line_number=85,
        )
        assert result.match_type == MatchType.FUZZY
        assert 0.8 <= result.similarity < 1.0
        assert result.body_heading is not None

    def test_match_result_missing_body_heading_is_none(
        self, toc_entry_numbered: TocEntry
    ) -> None:
        """MISSING の場合、body_heading は None であること"""
        result = MatchResult(
            toc_entry=toc_entry_numbered,
            body_heading=None,
            match_type=MatchType.MISSING,
            similarity=0.0,
            line_number=0,
        )
        assert result.match_type == MatchType.MISSING
        assert result.body_heading is None
        assert result.similarity == 0.0

    def test_match_result_excluded(
        self, toc_entry_numbered: TocEntry, heading_special_marker: Heading
    ) -> None:
        """EXCLUDED の場合、特殊マーカー付き見出しが設定されること"""
        result = MatchResult(
            toc_entry=toc_entry_numbered,
            body_heading=heading_special_marker,
            match_type=MatchType.EXCLUDED,
            similarity=0.0,
            line_number=192,
        )
        assert result.match_type == MatchType.EXCLUDED
        assert result.body_heading is not None
        assert result.body_heading.text == "■コードベース"

    def test_match_result_is_frozen(
        self, toc_entry_numbered: TocEntry, heading_with_number: Heading
    ) -> None:
        """MatchResult は frozen dataclass であること (immutability)"""
        result = MatchResult(
            toc_entry=toc_entry_numbered,
            body_heading=heading_with_number,
            match_type=MatchType.EXACT,
            similarity=1.0,
            line_number=52,
        )
        with pytest.raises(AttributeError):
            result.similarity = 0.5  # type: ignore[misc]


# ============================================================
# T027: 完全一致マッチングテスト
# ============================================================


class TestExactMatching:
    """完全一致マッチング (match_toc_to_body) のテスト"""

    def test_match_exact_title(self) -> None:
        """TOC タイトルと本文見出しタイトルが完全一致する場合"""
        from src.book_converter.heading_matcher import match_toc_to_body

        toc_entries = [
            TocEntry(text="SREの概要", level=2, number="1.1", page="015"),
        ]
        body_headings = [
            Heading(level=2, text="1.1 SREの概要"),
        ]
        results = match_toc_to_body(toc_entries, body_headings)

        assert len(results) == 1
        assert results[0].match_type == MatchType.EXACT
        assert results[0].similarity == 1.0
        assert results[0].body_heading is not None
        assert results[0].toc_entry.text == "SREの概要"

    def test_match_exact_with_number(self) -> None:
        """TOC 番号付きタイトルと本文見出しが番号含めて一致する場合"""
        from src.book_converter.heading_matcher import match_toc_to_body

        toc_entries = [
            TocEntry(text="SREの概要", level=2, number="1.1", page="015"),
        ]
        body_headings = [
            Heading(level=2, text="1.1 SREの概要"),
        ]
        results = match_toc_to_body(toc_entries, body_headings)

        assert len(results) == 1
        assert results[0].match_type == MatchType.EXACT
        assert results[0].similarity == 1.0

    def test_match_exact_multiple_entries(self) -> None:
        """複数の TOC エントリが全て完全一致する場合"""
        from src.book_converter.heading_matcher import match_toc_to_body

        toc_entries = [
            TocEntry(text="SREの概要", level=2, number="1.1", page="015"),
            TocEntry(text="サイトとは何か", level=3, number="1.1.1", page="018"),
        ]
        body_headings = [
            Heading(level=2, text="1.1 SREの概要"),
            Heading(level=3, text="1.1.1 サイトとは何か"),
        ]
        results = match_toc_to_body(toc_entries, body_headings)

        assert len(results) == 2
        assert all(r.match_type == MatchType.EXACT for r in results)

    def test_match_exact_no_number_entry(self) -> None:
        """番号なしTOCエントリ（はじめに等）と一致する場合"""
        from src.book_converter.heading_matcher import match_toc_to_body

        toc_entries = [
            TocEntry(text="はじめに", level=1, number="", page="001"),
        ]
        body_headings = [
            Heading(level=2, text="はじめに"),
        ]
        results = match_toc_to_body(toc_entries, body_headings)

        assert len(results) == 1
        assert results[0].match_type == MatchType.EXACT
        assert results[0].similarity == 1.0


# ============================================================
# T028: 番号除去マッチングテスト
# ============================================================


class TestNumberRemovalMatching:
    """番号除去後のマッチングテスト"""

    def test_match_after_number_removal(self) -> None:
        """TOCの番号付きタイトルと本文の番号なし見出しが番号除去後に一致"""
        from src.book_converter.heading_matcher import match_toc_to_body

        toc_entries = [
            TocEntry(text="SREの概要", level=2, number="1.1", page="015"),
        ]
        body_headings = [
            Heading(level=2, text="SREの概要"),  # 番号なし
        ]
        results = match_toc_to_body(toc_entries, body_headings)

        assert len(results) == 1
        # 番号除去で一致 → EXACT扱い (番号付与アクションが必要)
        assert results[0].match_type == MatchType.EXACT
        assert results[0].similarity == 1.0
        assert results[0].body_heading is not None
        assert results[0].body_heading.text == "SREの概要"

    def test_match_after_number_removal_three_levels(self) -> None:
        """3階層番号でも番号除去後に一致"""
        from src.book_converter.heading_matcher import match_toc_to_body

        toc_entries = [
            TocEntry(text="サイトとは何か", level=3, number="1.1.1", page="018"),
        ]
        body_headings = [
            Heading(level=3, text="サイトとは何か"),
        ]
        results = match_toc_to_body(toc_entries, body_headings)

        assert len(results) == 1
        assert results[0].match_type == MatchType.EXACT
        assert results[0].similarity == 1.0

    def test_match_number_removal_with_body_having_different_number(self) -> None:
        """本文見出しが異なる番号を持つ場合でも、タイトル部分で一致"""
        from src.book_converter.heading_matcher import match_toc_to_body

        toc_entries = [
            TocEntry(text="SREの概要", level=2, number="1.1", page="015"),
        ]
        body_headings = [
            Heading(level=2, text="2.1 SREの概要"),  # 番号が異なる
        ]
        results = match_toc_to_body(toc_entries, body_headings)

        assert len(results) == 1
        # 番号除去後にタイトルが一致するのでマッチする
        assert results[0].match_type == MatchType.EXACT
        assert results[0].body_heading is not None


# ============================================================
# T029: ファジーマッチングテスト
# ============================================================


class TestFuzzyMatching:
    """ファジーマッチングのテスト"""

    def test_fuzzy_match_above_threshold(self) -> None:
        """類似度 80% 以上でファジーマッチと判定される"""
        from src.book_converter.heading_matcher import match_toc_to_body

        toc_entries = [
            TocEntry(text="信頼性とは何か", level=2, number="1.1.2", page="021"),
        ]
        body_headings = [
            Heading(level=2, text="信頼性とは"),  # OCR誤認識で短縮
        ]
        results = match_toc_to_body(toc_entries, body_headings)

        assert len(results) == 1
        assert results[0].match_type == MatchType.FUZZY
        assert results[0].similarity >= 0.8
        assert results[0].similarity < 1.0
        assert results[0].body_heading is not None

    def test_fuzzy_match_below_threshold(self) -> None:
        """類似度 80% 未満は MISSING と判定される"""
        from src.book_converter.heading_matcher import match_toc_to_body

        toc_entries = [
            TocEntry(text="SREとは何か", level=2, number="1.1", page="015"),
        ]
        body_headings = [
            Heading(level=2, text="完全に別のテキスト"),  # 類似度低い
        ]
        results = match_toc_to_body(toc_entries, body_headings)

        assert len(results) == 1
        assert results[0].match_type == MatchType.MISSING
        assert results[0].body_heading is None

    def test_fuzzy_match_with_ocr_error(self) -> None:
        """OCR誤認識を含む見出しがファジーマッチで検出される"""
        from src.book_converter.heading_matcher import match_toc_to_body

        toc_entries = [
            TocEntry(text="モニタリングの基本", level=2, number="2.1", page="030"),
        ]
        body_headings = [
            Heading(level=2, text="モニタリソグの基本"),  # グ→ソグ OCR誤認識
        ]
        results = match_toc_to_body(toc_entries, body_headings)

        assert len(results) == 1
        assert results[0].match_type == MatchType.FUZZY
        assert results[0].similarity >= 0.8
        assert results[0].body_heading is not None

    def test_fuzzy_match_custom_threshold(self) -> None:
        """カスタム閾値でファジーマッチの感度を調整"""
        from src.book_converter.heading_matcher import match_toc_to_body

        toc_entries = [
            TocEntry(text="信頼性とは何か", level=2, number="1.1.2", page="021"),
        ]
        body_headings = [
            Heading(level=2, text="信頼性とは"),
        ]

        # 高い閾値では MISSING
        results_strict = match_toc_to_body(
            toc_entries, body_headings, similarity_threshold=0.95
        )
        assert len(results_strict) == 1
        assert results_strict[0].match_type == MatchType.MISSING

    def test_fuzzy_match_unicode_special_chars(self) -> None:
        """Unicode特殊文字を含む見出しのファジーマッチ"""
        from src.book_converter.heading_matcher import match_toc_to_body

        toc_entries = [
            TocEntry(text="C++とRustの比較", level=2, number="3.1", page="045"),
        ]
        body_headings = [
            Heading(level=2, text="C++とRustの比較"),
        ]
        results = match_toc_to_body(toc_entries, body_headings)

        assert len(results) == 1
        assert results[0].match_type == MatchType.EXACT
        assert results[0].similarity == 1.0


# ============================================================
# Edge Cases
# ============================================================


class TestMatchingEdgeCases:
    """マッチングのエッジケーステスト"""

    def test_empty_toc_entries(self) -> None:
        """TOC エントリが空の場合"""
        from src.book_converter.heading_matcher import match_toc_to_body

        results = match_toc_to_body([], [Heading(level=2, text="見出し")])
        assert results == []

    def test_empty_body_headings(self) -> None:
        """本文見出しが空の場合、全て MISSING"""
        from src.book_converter.heading_matcher import match_toc_to_body

        toc_entries = [
            TocEntry(text="SREの概要", level=2, number="1.1", page="015"),
        ]
        results = match_toc_to_body(toc_entries, [])

        assert len(results) == 1
        assert results[0].match_type == MatchType.MISSING
        assert results[0].body_heading is None

    def test_both_empty(self) -> None:
        """TOC も本文見出しも空の場合"""
        from src.book_converter.heading_matcher import match_toc_to_body

        results = match_toc_to_body([], [])
        assert results == []

    def test_duplicate_headings_match_by_order(self) -> None:
        """同名の見出しが複数ある場合、出現順序で区別"""
        from src.book_converter.heading_matcher import match_toc_to_body

        toc_entries = [
            TocEntry(text="まとめ", level=2, number="1.5", page="020"),
            TocEntry(text="まとめ", level=2, number="2.5", page="040"),
        ]
        body_headings = [
            Heading(level=2, text="まとめ"),
            Heading(level=2, text="まとめ"),
        ]
        results = match_toc_to_body(toc_entries, body_headings)

        assert len(results) == 2
        # 両方とも EXACT でマッチすること
        assert results[0].match_type == MatchType.EXACT
        assert results[1].match_type == MatchType.EXACT

    def test_special_marker_heading_excluded(self) -> None:
        """特殊マーカー付き見出しはマッチング対象外"""
        from src.book_converter.heading_matcher import match_toc_to_body

        toc_entries = [
            TocEntry(text="SREの概要", level=2, number="1.1", page="015"),
        ]
        body_headings = [
            Heading(level=2, text="■コードベース"),  # 特殊マーカー
            Heading(level=2, text="SREの概要"),
        ]
        results = match_toc_to_body(toc_entries, body_headings)

        # TOCエントリに対するマッチ結果
        assert len(results) >= 1
        exact_results = [r for r in results if r.match_type == MatchType.EXACT]
        assert len(exact_results) == 1

    def test_large_dataset_performance(self) -> None:
        """1000件以上のエントリでもマッチングが機能する"""
        from src.book_converter.heading_matcher import match_toc_to_body

        toc_entries = [
            TocEntry(text=f"セクション{i}", level=2, number=f"1.{i}", page=f"{i:03d}")
            for i in range(1000)
        ]
        body_headings = [
            Heading(level=2, text=f"1.{i} セクション{i}")
            for i in range(1000)
        ]
        results = match_toc_to_body(toc_entries, body_headings)

        assert len(results) == 1000
        exact_count = sum(1 for r in results if r.match_type == MatchType.EXACT)
        assert exact_count == 1000

    def test_emoji_in_heading(self) -> None:
        """絵文字を含む見出しのマッチング"""
        from src.book_converter.heading_matcher import match_toc_to_body

        toc_entries = [
            TocEntry(text="入門ガイド", level=2, number="1.1", page="010"),
        ]
        body_headings = [
            Heading(level=2, text="入門ガイド"),
        ]
        results = match_toc_to_body(toc_entries, body_headings)

        assert len(results) == 1
        assert results[0].match_type == MatchType.EXACT

    def test_sql_special_chars_in_heading(self) -> None:
        """SQL特殊文字を含む見出し"""
        from src.book_converter.heading_matcher import match_toc_to_body

        toc_entries = [
            TocEntry(text="WHERE句とOR'条件", level=2, number="5.1", page="100"),
        ]
        body_headings = [
            Heading(level=2, text="5.1 WHERE句とOR'条件"),
        ]
        results = match_toc_to_body(toc_entries, body_headings)

        assert len(results) == 1
        assert results[0].match_type == MatchType.EXACT
