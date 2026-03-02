"""Tests for normalization_rules module - rule generation from match results.

Phase 3 RED tests for US2: TOC形式への見出し正規化
"""

from __future__ import annotations

import pytest

from src.book_converter.models import (
    Heading,
    MatchResult,
    MatchType,
    NormalizationAction,
    NormalizationRule,
    TocEntry,
)


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture()
def match_exact_with_number() -> MatchResult:
    """既に番号付きで完全一致のマッチ結果 (変更不要)"""
    return MatchResult(
        toc_entry=TocEntry(text="SREの概要", level=2, number="1.1", page="015"),
        body_heading=Heading(level=2, text="1.1 SREの概要"),
        match_type=MatchType.EXACT,
        similarity=1.0,
        line_number=52,
    )


@pytest.fixture()
def match_exact_without_number() -> MatchResult:
    """番号なし完全一致のマッチ結果 (番号付与が必要)"""
    return MatchResult(
        toc_entry=TocEntry(text="SREの概要", level=2, number="1.1", page="015"),
        body_heading=Heading(level=2, text="SREの概要"),
        match_type=MatchType.EXACT,
        similarity=1.0,
        line_number=52,
    )


@pytest.fixture()
def match_fuzzy() -> MatchResult:
    """ファジーマッチ結果 (番号付与 + 可能ならマーカー付与)"""
    return MatchResult(
        toc_entry=TocEntry(text="信頼性とは何か", level=2, number="1.1.2", page="021"),
        body_heading=Heading(level=2, text="信頼性とは"),
        match_type=MatchType.FUZZY,
        similarity=0.85,
        line_number=85,
    )


@pytest.fixture()
def match_missing() -> MatchResult:
    """MISSING マッチ結果 (ルール生成なし)"""
    return MatchResult(
        toc_entry=TocEntry(text="SREとは", level=2, number="1.1", page="015"),
        body_heading=None,
        match_type=MatchType.MISSING,
        similarity=0.0,
        line_number=0,
    )


@pytest.fixture()
def match_format_only() -> MatchResult:
    """フォーマットのみ正規化が必要なマッチ結果"""
    return MatchResult(
        toc_entry=TocEntry(text="SREの概要", level=2, number="1.1", page="015"),
        body_heading=Heading(level=2, text="1-1 SREの概要"),  # ハイフン区切り
        match_type=MatchType.EXACT,
        similarity=1.0,
        line_number=52,
    )


# ============================================================
# T030: NormalizationRule 生成テスト
# ============================================================


class TestGenerateRules:
    """generate_rules() のテスト"""

    def test_generate_rule_add_number(
        self, match_exact_without_number: MatchResult
    ) -> None:
        """番号なし見出しに番号を付与するルールが生成される"""
        from src.book_converter.normalization_rules import generate_rules

        rules = generate_rules([match_exact_without_number])

        assert len(rules) == 1
        rule = rules[0]
        assert isinstance(rule, NormalizationRule)
        assert rule.action == NormalizationAction.ADD_NUMBER
        assert rule.line_number == 52
        assert rule.original != rule.normalized
        # 正規化後は番号が含まれること
        assert "1.1" in rule.normalized
        assert "SREの概要" in rule.normalized

    def test_generate_rule_add_marker(self) -> None:
        """Markdownマーカーなしの本文にマーカーと番号を付与するルール"""
        from src.book_converter.normalization_rules import generate_rules

        # マーカーなしの本文見出し (level=0 はプレーンテキストを示す)
        match = MatchResult(
            toc_entry=TocEntry(
                text="サイトとは何か", level=3, number="1.1.1", page="018"
            ),
            body_heading=Heading(level=0, text="サイトとは何か"),
            match_type=MatchType.EXACT,
            similarity=1.0,
            line_number=68,
        )
        rules = generate_rules([match])

        assert len(rules) == 1
        rule = rules[0]
        assert rule.action == NormalizationAction.ADD_MARKER
        assert rule.line_number == 68
        # 正規化後は ### マーカーと番号が含まれること
        assert "###" in rule.normalized or "##" in rule.normalized
        assert "1.1.1" in rule.normalized
        assert "サイトとは何か" in rule.normalized

    def test_generate_rule_format_only(
        self, match_format_only: MatchResult
    ) -> None:
        """番号フォーマットのみの正規化ルール (1-1 -> 1.1)"""
        from src.book_converter.normalization_rules import generate_rules

        rules = generate_rules([match_format_only])

        assert len(rules) == 1
        rule = rules[0]
        assert rule.action == NormalizationAction.FORMAT_ONLY
        assert rule.line_number == 52
        # 正規化後はドット区切りになること
        assert "1.1" in rule.normalized
        assert "1-1" not in rule.normalized

    def test_generate_rule_none_already_correct(
        self, match_exact_with_number: MatchResult
    ) -> None:
        """既に正しい形式の場合、NONE ルールまたはルールが生成されない"""
        from src.book_converter.normalization_rules import generate_rules

        rules = generate_rules([match_exact_with_number])

        if len(rules) == 0:
            # ルールが生成されないパターン (変更不要)
            pass
        else:
            # NONE アクションのルールが生成されるパターン
            assert len(rules) == 1
            rule = rules[0]
            assert rule.action == NormalizationAction.NONE
            assert rule.original == rule.normalized

    def test_generate_rule_missing_skipped(
        self, match_missing: MatchResult
    ) -> None:
        """MISSING マッチからはルールが生成されない"""
        from src.book_converter.normalization_rules import generate_rules

        rules = generate_rules([match_missing])

        assert len(rules) == 0

    def test_generate_rules_multiple_matches(
        self,
        match_exact_without_number: MatchResult,
        match_exact_with_number: MatchResult,
        match_missing: MatchResult,
    ) -> None:
        """複数マッチから適切にルールが生成される"""
        from src.book_converter.normalization_rules import generate_rules

        rules = generate_rules([
            match_exact_without_number,
            match_exact_with_number,
            match_missing,
        ])

        # MISSING はスキップされるので、最大2件のルール
        # match_exact_with_number は NONE (変更不要) なので0-1件
        # match_exact_without_number は ADD_NUMBER なので1件
        add_number_rules = [
            r for r in rules if r.action == NormalizationAction.ADD_NUMBER
        ]
        assert len(add_number_rules) == 1


# ============================================================
# Edge Cases
# ============================================================


class TestGenerateRulesEdgeCases:
    """generate_rules() のエッジケーステスト"""

    def test_generate_rules_empty_matches(self) -> None:
        """空のマッチリストからはルールが生成されない"""
        from src.book_converter.normalization_rules import generate_rules

        rules = generate_rules([])
        assert rules == []

    def test_generate_rules_excluded_match(self) -> None:
        """EXCLUDED マッチからはルールが生成されない"""
        from src.book_converter.normalization_rules import generate_rules

        match = MatchResult(
            toc_entry=TocEntry(text="コードベース", level=2, number="", page="050"),
            body_heading=Heading(level=2, text="■コードベース"),
            match_type=MatchType.EXCLUDED,
            similarity=0.0,
            line_number=192,
        )
        rules = generate_rules([match])

        assert len(rules) == 0

    def test_generated_rule_is_frozen(
        self, match_exact_without_number: MatchResult
    ) -> None:
        """生成された NormalizationRule は frozen であること"""
        from src.book_converter.normalization_rules import generate_rules

        rules = generate_rules([match_exact_without_number])
        assert len(rules) >= 1

        rule = rules[0]
        with pytest.raises(AttributeError):
            rule.action = NormalizationAction.NONE  # type: ignore[misc]

    def test_generate_rule_preserves_line_number(self) -> None:
        """ルール生成で行番号が正しく保持される"""
        from src.book_converter.normalization_rules import generate_rules

        match = MatchResult(
            toc_entry=TocEntry(text="テスト", level=2, number="9.9", page="999"),
            body_heading=Heading(level=2, text="テスト"),
            match_type=MatchType.EXACT,
            similarity=1.0,
            line_number=12345,
        )
        rules = generate_rules([match])

        assert len(rules) >= 1
        assert rules[0].line_number == 12345

    def test_generate_rule_with_special_chars(self) -> None:
        """特殊文字を含む見出しからルールが正しく生成される"""
        from src.book_converter.normalization_rules import generate_rules

        match = MatchResult(
            toc_entry=TocEntry(
                text="C++とRustの比較", level=2, number="3.1", page="045"
            ),
            body_heading=Heading(level=2, text="C++とRustの比較"),
            match_type=MatchType.EXACT,
            similarity=1.0,
            line_number=100,
        )
        rules = generate_rules([match])

        # 番号付与が必要
        add_rules = [r for r in rules if r.action == NormalizationAction.ADD_NUMBER]
        assert len(add_rules) == 1
        assert "3.1" in add_rules[0].normalized
        assert "C++とRustの比較" in add_rules[0].normalized

    def test_generate_rule_fuzzy_match_add_number(
        self, match_fuzzy: MatchResult
    ) -> None:
        """ファジーマッチからも番号付与ルールが生成される"""
        from src.book_converter.normalization_rules import generate_rules

        rules = generate_rules([match_fuzzy])

        assert len(rules) >= 1
        rule = rules[0]
        # ファジーマッチでも番号付与
        assert rule.action in (
            NormalizationAction.ADD_NUMBER,
            NormalizationAction.ADD_MARKER,
        )
        assert "1.1.2" in rule.normalized
