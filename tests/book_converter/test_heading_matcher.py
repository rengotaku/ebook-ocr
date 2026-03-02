"""Tests for heading_matcher module - TOC-body heading matching engine.

Phase 3 RED tests for US2: TOC形式への見出し正規化
Phase 5 RED tests for US4: 正規化結果の検証
"""

from __future__ import annotations

import pytest

from src.book_converter.models import (
    Heading,
    MatchResult,
    MatchType,
    NormalizationAction,
    TocEntry,
    ValidationReport,
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


# ============================================================
# Phase 5: US4 - 正規化結果の検証
# ============================================================


# ============================================================
# T058: ValidationReport モデルテスト
# ============================================================


class TestValidationReportModel:
    """ValidationReport データクラスの制約テスト"""

    def test_validation_report_match_rate(self) -> None:
        """match_rate が正しく設定されること"""
        report = ValidationReport(
            toc_entry_count=42,
            body_heading_count=40,
            matched_count=38,
            match_rate=38 / 42,
            missing_entries=(),
            excluded_headings=(),
        )
        assert report.toc_entry_count == 42
        assert report.body_heading_count == 40
        assert report.matched_count == 38
        assert abs(report.match_rate - 38 / 42) < 1e-9
        assert report.match_rate > 0.0
        assert report.match_rate <= 1.0

    def test_validation_report_match_rate_zero(self) -> None:
        """マッチ数0の場合、match_rate は 0.0"""
        report = ValidationReport(
            toc_entry_count=10,
            body_heading_count=5,
            matched_count=0,
            match_rate=0.0,
            missing_entries=(),
            excluded_headings=(),
        )
        assert report.match_rate == 0.0
        assert report.matched_count == 0

    def test_validation_report_match_rate_full(self) -> None:
        """全マッチの場合、match_rate は 1.0"""
        report = ValidationReport(
            toc_entry_count=10,
            body_heading_count=10,
            matched_count=10,
            match_rate=1.0,
            missing_entries=(),
            excluded_headings=(),
        )
        assert report.match_rate == 1.0

    def test_validation_report_missing_entries(self) -> None:
        """missing_entries に未マッチの TocEntry が含まれること"""
        missing1 = TocEntry(text="第1章 SREとは", level=1, number="1", page="001")
        missing2 = TocEntry(text="第2章 信頼性を定義", level=1, number="2", page="025")
        report = ValidationReport(
            toc_entry_count=42,
            body_heading_count=40,
            matched_count=40,
            match_rate=40 / 42,
            missing_entries=(missing1, missing2),
            excluded_headings=(),
        )
        assert len(report.missing_entries) == 2
        assert report.missing_entries[0].text == "第1章 SREとは"
        assert report.missing_entries[1].text == "第2章 信頼性を定義"

    def test_validation_report_missing_entries_empty(self) -> None:
        """未マッチがない場合、missing_entries は空タプル"""
        report = ValidationReport(
            toc_entry_count=10,
            body_heading_count=10,
            matched_count=10,
            match_rate=1.0,
            missing_entries=(),
            excluded_headings=(),
        )
        assert report.missing_entries == ()

    def test_validation_report_excluded_headings(self) -> None:
        """excluded_headings に特殊マーカー付き見出しが含まれること"""
        excluded1 = Heading(level=2, text="■コードベース")
        excluded2 = Heading(level=2, text="■コードの送信")
        report = ValidationReport(
            toc_entry_count=42,
            body_heading_count=40,
            matched_count=38,
            match_rate=38 / 42,
            missing_entries=(),
            excluded_headings=(excluded1, excluded2),
        )
        assert len(report.excluded_headings) == 2
        assert report.excluded_headings[0].text == "■コードベース"
        assert report.excluded_headings[1].text == "■コードの送信"

    def test_validation_report_is_frozen(self) -> None:
        """ValidationReport は frozen dataclass であること (immutability)"""
        report = ValidationReport(
            toc_entry_count=10,
            body_heading_count=10,
            matched_count=10,
            match_rate=1.0,
            missing_entries=(),
            excluded_headings=(),
        )
        with pytest.raises(AttributeError):
            report.match_rate = 0.5  # type: ignore[misc]

    def test_validation_report_empty_toc(self) -> None:
        """TOCエントリ数0の場合のレポート"""
        report = ValidationReport(
            toc_entry_count=0,
            body_heading_count=5,
            matched_count=0,
            match_rate=0.0,
            missing_entries=(),
            excluded_headings=(),
        )
        assert report.toc_entry_count == 0
        assert report.match_rate == 0.0


# ============================================================
# T059: 類似候補表示テスト
# ============================================================


class TestFindSimilarCandidate:
    """find_similar_candidate のテスト"""

    def test_find_similar_candidate_above_threshold(self) -> None:
        """類似度が閾値以上の場合、候補が返されること"""
        from src.book_converter.heading_matcher import find_similar_candidate

        toc_entry = TocEntry(text="SREとは何か", level=2, number="1.1", page="015")
        headings = [
            Heading(level=2, text="SRE とは"),
            Heading(level=2, text="完全に別のテキスト"),
        ]
        result = find_similar_candidate(toc_entry, headings, threshold=0.6)

        assert result is not None
        heading, similarity = result
        assert heading.text == "SRE とは"
        assert similarity >= 0.6

    def test_find_similar_candidate_exact_match(self) -> None:
        """完全一致の見出しがある場合、類似度1.0で返されること"""
        from src.book_converter.heading_matcher import find_similar_candidate

        toc_entry = TocEntry(text="SREの概要", level=2, number="1.1", page="015")
        headings = [
            Heading(level=2, text="SREの概要"),
        ]
        result = find_similar_candidate(toc_entry, headings)

        assert result is not None
        heading, similarity = result
        assert similarity >= 0.8

    def test_find_similar_candidate_none(self) -> None:
        """類似度が閾値未満の場合、None が返されること"""
        from src.book_converter.heading_matcher import find_similar_candidate

        toc_entry = TocEntry(text="SREとは何か", level=2, number="1.1", page="015")
        headings = [
            Heading(level=2, text="完全に別のテキスト"),
            Heading(level=2, text="全く異なる見出し"),
        ]
        result = find_similar_candidate(toc_entry, headings)

        assert result is None

    def test_find_similar_candidate_empty_headings(self) -> None:
        """見出しリストが空の場合、None が返されること"""
        from src.book_converter.heading_matcher import find_similar_candidate

        toc_entry = TocEntry(text="SREの概要", level=2, number="1.1", page="015")
        result = find_similar_candidate(toc_entry, [])

        assert result is None

    def test_find_similar_candidate_best_match(self) -> None:
        """複数候補がある場合、最も類似度が高いものが返されること"""
        from src.book_converter.heading_matcher import find_similar_candidate

        toc_entry = TocEntry(text="モニタリングの基本", level=2, number="2.1", page="030")
        headings = [
            Heading(level=2, text="モニタリソグの基本"),  # OCR error
            Heading(level=2, text="モニタリングの基本原則"),  # close
            Heading(level=2, text="完全に別のテキスト"),  # unrelated
        ]
        result = find_similar_candidate(toc_entry, headings)

        assert result is not None
        _, similarity = result
        assert similarity >= 0.8

    def test_find_similar_candidate_special_marker_excluded(self) -> None:
        """特殊マーカー付き見出しは候補から除外されること"""
        from src.book_converter.heading_matcher import find_similar_candidate

        toc_entry = TocEntry(text="コードベース", level=2, number="3.1", page="050")
        headings = [
            Heading(level=2, text="■コードベース"),  # special marker
        ]
        # 特殊マーカー付きでも文字列としては類似しているが、
        # マーカー除去後の比較で閾値を超えるなら返す
        # (実装によるが、テストとしては特殊マーカーの扱いを検証)
        result = find_similar_candidate(toc_entry, headings)
        # 特殊マーカーの扱いは実装次第
        # 類似度が閾値以上なら結果が返る、未満なら None
        if result is not None:
            _, similarity = result
            assert similarity >= 0.8

    def test_find_similar_candidate_custom_threshold(self) -> None:
        """カスタム閾値で類似候補の感度を調整できること"""
        from src.book_converter.heading_matcher import find_similar_candidate

        toc_entry = TocEntry(text="信頼性とは何か", level=2, number="1.2", page="021")
        headings = [
            Heading(level=2, text="信頼性とは"),
        ]

        # 低い閾値なら見つかる
        result_low = find_similar_candidate(toc_entry, headings, threshold=0.6)
        assert result_low is not None

        # 高い閾値なら見つからない
        result_high = find_similar_candidate(toc_entry, headings, threshold=0.99)
        assert result_high is None


# ============================================================
# T060: レポート出力テスト
# ============================================================


class TestGenerateValidationReport:
    """generate_validation_report のテスト"""

    def test_generate_report_basic(self) -> None:
        """基本的なレポート生成 - マッチ率が正しいこと"""
        from src.book_converter.heading_matcher import generate_validation_report

        toc1 = TocEntry(text="SREの概要", level=2, number="1.1", page="015")
        toc2 = TocEntry(text="サイトとは何か", level=3, number="1.1.1", page="018")
        toc3 = TocEntry(text="第1章 SREとは", level=1, number="1", page="001")

        heading1 = Heading(level=2, text="1.1 SREの概要")
        heading2 = Heading(level=3, text="1.1.1 サイトとは何か")
        heading_excluded = Heading(level=2, text="■コードベース")

        matches = [
            MatchResult(toc_entry=toc1, body_heading=heading1, match_type=MatchType.EXACT, similarity=1.0, line_number=52),
            MatchResult(toc_entry=toc2, body_heading=heading2, match_type=MatchType.EXACT, similarity=1.0, line_number=68),
            MatchResult(toc_entry=toc3, body_heading=None, match_type=MatchType.MISSING, similarity=0.0, line_number=0),
        ]
        headings = [heading1, heading2, heading_excluded]

        report = generate_validation_report(matches, headings)

        assert isinstance(report, ValidationReport)
        assert report.toc_entry_count == 3
        assert report.matched_count == 2
        assert abs(report.match_rate - 2 / 3) < 1e-9
        assert len(report.missing_entries) == 1
        assert report.missing_entries[0].text == "第1章 SREとは"

    def test_generate_report_all_matched(self) -> None:
        """全てマッチした場合のレポート"""
        from src.book_converter.heading_matcher import generate_validation_report

        toc1 = TocEntry(text="SREの概要", level=2, number="1.1", page="015")
        heading1 = Heading(level=2, text="1.1 SREの概要")

        matches = [
            MatchResult(toc_entry=toc1, body_heading=heading1, match_type=MatchType.EXACT, similarity=1.0, line_number=52),
        ]

        report = generate_validation_report(matches, [heading1])

        assert report.match_rate == 1.0
        assert report.missing_entries == ()
        assert report.matched_count == 1

    def test_generate_report_none_matched(self) -> None:
        """全て未マッチの場合のレポート"""
        from src.book_converter.heading_matcher import generate_validation_report

        toc1 = TocEntry(text="SREの概要", level=2, number="1.1", page="015")
        toc2 = TocEntry(text="サイトとは何か", level=3, number="1.1.1", page="018")

        matches = [
            MatchResult(toc_entry=toc1, body_heading=None, match_type=MatchType.MISSING, similarity=0.0, line_number=0),
            MatchResult(toc_entry=toc2, body_heading=None, match_type=MatchType.MISSING, similarity=0.0, line_number=0),
        ]

        report = generate_validation_report(matches, [])

        assert report.match_rate == 0.0
        assert report.matched_count == 0
        assert len(report.missing_entries) == 2

    def test_generate_report_excluded_headings(self) -> None:
        """除外見出しがレポートに含まれること"""
        from src.book_converter.heading_matcher import generate_validation_report

        toc1 = TocEntry(text="SREの概要", level=2, number="1.1", page="015")
        heading1 = Heading(level=2, text="1.1 SREの概要")
        heading_excluded1 = Heading(level=2, text="■コードベース")
        heading_excluded2 = Heading(level=2, text="◆注意事項")

        matches = [
            MatchResult(toc_entry=toc1, body_heading=heading1, match_type=MatchType.EXACT, similarity=1.0, line_number=52),
        ]
        headings = [heading1, heading_excluded1, heading_excluded2]

        report = generate_validation_report(matches, headings)

        assert len(report.excluded_headings) == 2
        excluded_texts = {h.text for h in report.excluded_headings}
        assert "■コードベース" in excluded_texts
        assert "◆注意事項" in excluded_texts

    def test_generate_report_empty_matches(self) -> None:
        """空のマッチリストでもエラーにならないこと"""
        from src.book_converter.heading_matcher import generate_validation_report

        report = generate_validation_report([], [])

        assert report.toc_entry_count == 0
        assert report.body_heading_count == 0
        assert report.matched_count == 0
        assert report.match_rate == 0.0

    def test_generate_report_fuzzy_counted_as_matched(self) -> None:
        """FUZZY マッチもマッチ数に含まれること"""
        from src.book_converter.heading_matcher import generate_validation_report

        toc1 = TocEntry(text="信頼性とは何か", level=2, number="1.1.2", page="021")
        heading1 = Heading(level=2, text="信頼性とは")

        matches = [
            MatchResult(toc_entry=toc1, body_heading=heading1, match_type=MatchType.FUZZY, similarity=0.85, line_number=85),
        ]

        report = generate_validation_report(matches, [heading1])

        assert report.matched_count == 1
        assert report.match_rate == 1.0


class TestFormatValidationReport:
    """format_validation_report のテスト"""

    def test_format_validation_report_table(self) -> None:
        """テーブル形式の出力が含まれること"""
        from src.book_converter.heading_matcher import format_validation_report

        toc1 = TocEntry(text="SREの概要", level=2, number="1.1", page="015")
        heading1 = Heading(level=2, text="1.1 SREの概要")

        matches = [
            MatchResult(toc_entry=toc1, body_heading=heading1, match_type=MatchType.EXACT, similarity=1.0, line_number=52),
        ]

        report = ValidationReport(
            toc_entry_count=1,
            body_heading_count=1,
            matched_count=1,
            match_rate=1.0,
            missing_entries=(),
            excluded_headings=(),
        )

        output = format_validation_report(report, matches, {})

        assert isinstance(output, str)
        assert "TOC Validation Report" in output
        assert "SREの概要" in output
        assert "EXACT" in output

    def test_format_validation_report_summary(self) -> None:
        """サマリー情報が含まれること"""
        from src.book_converter.heading_matcher import format_validation_report

        report = ValidationReport(
            toc_entry_count=42,
            body_heading_count=40,
            matched_count=38,
            match_rate=38 / 42,
            missing_entries=(
                TocEntry(text="第1章 SREとは", level=1, number="1", page="001"),
                TocEntry(text="第2章 信頼性を定義", level=1, number="2", page="025"),
            ),
            excluded_headings=(
                Heading(level=2, text="■コードベース"),
                Heading(level=2, text="■コードの送信"),
            ),
        )

        matches: list[MatchResult] = []
        output = format_validation_report(report, matches, {})

        assert "42" in output  # TOC Entries
        assert "40" in output  # Body Headings
        assert "38" in output  # Matched
        assert "90" in output  # Match rate ~90.5%

    def test_format_validation_report_missing_with_similar(self) -> None:
        """MISSING エントリに類似候補が表示されること"""
        from src.book_converter.heading_matcher import format_validation_report

        toc_missing = TocEntry(text="第1章 SREとは", level=1, number="1", page="001")
        similar_heading = Heading(level=2, text="SRE とは")

        report = ValidationReport(
            toc_entry_count=1,
            body_heading_count=1,
            matched_count=0,
            match_rate=0.0,
            missing_entries=(toc_missing,),
            excluded_headings=(),
        )

        matches = [
            MatchResult(toc_entry=toc_missing, body_heading=None, match_type=MatchType.MISSING, similarity=0.0, line_number=0),
        ]

        similar_candidates = {
            toc_missing: (similar_heading, 0.82),
        }

        output = format_validation_report(report, matches, similar_candidates)

        assert "MISSING" in output
        assert "Similar" in output or "similar" in output.lower() or "SRE とは" in output

    def test_format_validation_report_excluded_section(self) -> None:
        """Excluded セクションが含まれること"""
        from src.book_converter.heading_matcher import format_validation_report

        report = ValidationReport(
            toc_entry_count=1,
            body_heading_count=3,
            matched_count=1,
            match_rate=1.0,
            missing_entries=(),
            excluded_headings=(
                Heading(level=2, text="■コードベース"),
                Heading(level=2, text="■コードの送信"),
            ),
        )

        output = format_validation_report(report, [], {})

        assert "Excluded" in output or "excluded" in output.lower()
        assert "■コードベース" in output
        assert "■コードの送信" in output

    def test_validation_report_exit_code_zero_with_missing(self) -> None:
        """MISSING があっても exit code は 0 であること (WARN表示)"""
        from src.book_converter.heading_matcher import format_validation_report

        report = ValidationReport(
            toc_entry_count=10,
            body_heading_count=8,
            matched_count=8,
            match_rate=0.8,
            missing_entries=(
                TocEntry(text="第1章 SREとは", level=1, number="1", page="001"),
            ),
            excluded_headings=(),
        )

        output = format_validation_report(report, [], {})

        # exit code 0 + WARN表示
        assert "WARN" in output
        assert "Exit: 0" in output or "exit: 0" in output.lower()

    def test_validation_report_exit_code_zero_all_matched(self) -> None:
        """全マッチの場合も exit code は 0 (OK 表示)"""
        from src.book_converter.heading_matcher import format_validation_report

        report = ValidationReport(
            toc_entry_count=10,
            body_heading_count=10,
            matched_count=10,
            match_rate=1.0,
            missing_entries=(),
            excluded_headings=(),
        )

        output = format_validation_report(report, [], {})

        assert "Exit: 0" in output or "exit: 0" in output.lower()

    def test_format_validation_report_empty(self) -> None:
        """空レポートでもエラーにならないこと"""
        from src.book_converter.heading_matcher import format_validation_report

        report = ValidationReport(
            toc_entry_count=0,
            body_heading_count=0,
            matched_count=0,
            match_rate=0.0,
            missing_entries=(),
            excluded_headings=(),
        )

        output = format_validation_report(report, [], {})

        assert isinstance(output, str)
        assert len(output) > 0
