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
from src.book_converter.normalization_rules import (
    apply_rules,
    generate_sed_script,
    preview_diff,
)

# ============================================================
# Fixtures
# ============================================================


@pytest.fixture()
def match_exact_with_number() -> MatchResult:
    """既に番号付きで完全一致のマッチ結果 (変更不要)"""
    return MatchResult(
        toc_entry=TocEntry(text="SREの概要", level=2, number="1.1.0", page="015"),
        body_heading=Heading(level=2, text="1.1.0 SREの概要"),
        match_type=MatchType.EXACT,
        similarity=1.0,
        line_number=52,
    )


@pytest.fixture()
def match_exact_without_number() -> MatchResult:
    """番号なし完全一致のマッチ結果 (番号付与が必要)"""
    return MatchResult(
        toc_entry=TocEntry(text="SREの概要", level=2, number="1.1.0", page="015"),
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

    def test_generate_rule_add_number(self, match_exact_without_number: MatchResult) -> None:
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
            toc_entry=TocEntry(text="サイトとは何か", level=3, number="1.1.1", page="018"),
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

    def test_generate_rule_format_only(self, match_format_only: MatchResult) -> None:
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

    def test_generate_rule_none_already_correct(self, match_exact_with_number: MatchResult) -> None:
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

    def test_generate_rule_missing_skipped(self, match_missing: MatchResult) -> None:
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

        rules = generate_rules(
            [
                match_exact_without_number,
                match_exact_with_number,
                match_missing,
            ]
        )

        # MISSING はスキップされるので、最大2件のルール
        # match_exact_with_number は NONE (変更不要) なので0-1件
        # match_exact_without_number は ADD_NUMBER なので1件
        add_number_rules = [r for r in rules if r.action == NormalizationAction.ADD_NUMBER]
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

    def test_generated_rule_is_frozen(self, match_exact_without_number: MatchResult) -> None:
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
            toc_entry=TocEntry(text="C++とRustの比較", level=2, number="3.1", page="045"),
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

    def test_generate_rule_fuzzy_match_add_number(self, match_fuzzy: MatchResult) -> None:
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


# ============================================================
# Phase 4: T044 - sed スクリプト生成テスト (US3)
# ============================================================


class TestGenerateSedScript:
    """generate_sed_script() のテスト"""

    def test_generate_sed_script_single_rule(self) -> None:
        """単一ルールから sed コマンドが1行生成される"""
        rule = NormalizationRule(
            original="## SREの概要",
            normalized="## 1.1 SREの概要",
            line_number=52,
            action=NormalizationAction.ADD_NUMBER,
        )
        result = generate_sed_script([rule])

        assert isinstance(result, str)
        assert len(result.strip()) > 0
        # sed 's/.../.../': s コマンド形式を含むこと
        assert "s/" in result or "s|" in result
        # 元テキストと変換後テキストが含まれること
        assert "SREの概要" in result
        assert "1.1" in result

    def test_generate_sed_script_multiple_rules(self) -> None:
        """複数ルールから複数行の sed コマンドが生成される"""
        rules = [
            NormalizationRule(
                original="## SREの概要",
                normalized="## 1.1 SREの概要",
                line_number=52,
                action=NormalizationAction.ADD_NUMBER,
            ),
            NormalizationRule(
                original="サイトとは何か",
                normalized="### 1.1.1 サイトとは何か",
                line_number=68,
                action=NormalizationAction.ADD_MARKER,
            ),
        ]
        result = generate_sed_script(rules)

        lines = [line for line in result.strip().split("\n") if line.strip()]
        # 各ルールに対して1行のコマンド
        assert len(lines) >= 2
        # 両方のルールの内容が含まれること
        assert "SREの概要" in result
        assert "サイトとは何か" in result

    def test_generate_sed_script_escape_special_chars(self) -> None:
        """sed の特殊文字（/, &, \\）が正しくエスケープされる"""
        rule = NormalizationRule(
            original="## C++/Rustの比較 & 解説",
            normalized="## 3.1 C++/Rustの比較 & 解説",
            line_number=100,
            action=NormalizationAction.ADD_NUMBER,
        )
        result = generate_sed_script([rule])

        assert isinstance(result, str)
        # スラッシュがエスケープされているか、別のデリミタが使われていること
        # 生成されたスクリプトが構文的に正しいこと（未エスケープの / や & がない）
        # エスケープ済み: \/ or \& or 別デリミタ使用
        if "s/" in result:
            # / デリミタの場合、original/normalized 内の / はエスケープ必須
            # 's/^...$/.../' 形式で、パターン内の / が \/ になっていること
            inner = result.split("s/", 1)[1]
            # 正しくエスケープされていれば C++\/Rust のように \/ がある
            assert "\\/" in inner or "|" in result
        # & も sed ではバックリファレンスなのでエスケープが必要
        assert "\\&" in result or "&" not in rule.original

    def test_generate_sed_script_empty_rules(self) -> None:
        """空のルールリストからは空文字列が返される"""
        result = generate_sed_script([])
        assert result == "" or result.strip() == ""

    def test_generate_sed_script_posix_compatible(self) -> None:
        """POSIX 互換の sed コマンドが生成される（GNU 拡張なし）"""
        rule = NormalizationRule(
            original="## テスト見出し",
            normalized="## 1.1 テスト見出し",
            line_number=10,
            action=NormalizationAction.ADD_NUMBER,
        )
        result = generate_sed_script([rule])

        # GNU 拡張の -r や -E オプションが含まれないこと
        assert "-r " not in result
        assert "-E " not in result
        # \d (Perl拡張) ではなく [0-9] を使うこと（パターン内に数字参照がある場合）
        assert "\\d" not in result

    def test_generate_sed_script_anchored_pattern(self) -> None:
        """sed パターンは行頭アンカー (^) を使用する"""
        rule = NormalizationRule(
            original="## SREの概要",
            normalized="## 1.1 SREの概要",
            line_number=52,
            action=NormalizationAction.ADD_NUMBER,
        )
        result = generate_sed_script([rule])

        # 行頭アンカーが使用されていること（部分一致を防ぐため）
        assert "^" in result

    def test_generate_sed_script_format_only_rule(self) -> None:
        """FORMAT_ONLY ルールからも sed コマンドが生成される"""
        rule = NormalizationRule(
            original="## 1-1 SREの概要",
            normalized="## 1.1 SREの概要",
            line_number=52,
            action=NormalizationAction.FORMAT_ONLY,
        )
        result = generate_sed_script([rule])

        assert isinstance(result, str)
        assert len(result.strip()) > 0
        assert "1-1" in result or "1\\-1" in result  # 元パターン
        assert "1.1" in result  # 変換後

    def test_generate_sed_script_unicode_heading(self) -> None:
        """Unicode（日本語、絵文字）を含む見出しの sed スクリプト生成"""
        rule = NormalizationRule(
            original="## データベースの設計",
            normalized="## 2.1 データベースの設計",
            line_number=200,
            action=NormalizationAction.ADD_NUMBER,
        )
        result = generate_sed_script([rule])

        assert "データベースの設計" in result
        assert "2.1" in result


# ============================================================
# Phase 4: T045 - 差分プレビューテスト (US3)
# ============================================================


class TestPreviewDiff:
    """preview_diff() のテスト"""

    def test_preview_diff_changes(self) -> None:
        """変更がある場合、差分プレビューが表示される"""
        content = "# タイトル\n\n## SREの概要\n\nテキスト\n"
        rules = [
            NormalizationRule(
                original="## SREの概要",
                normalized="## 1.1 SREの概要",
                line_number=3,
                action=NormalizationAction.ADD_NUMBER,
            ),
        ]
        result = preview_diff(content, rules)

        assert isinstance(result, str)
        assert len(result.strip()) > 0
        # 行番号が含まれること
        assert "3" in result
        # 元テキストと変換後テキストの両方が含まれること
        assert "SREの概要" in result
        assert "1.1" in result

    def test_preview_diff_no_changes(self) -> None:
        """変更がない場合、空の差分プレビューが返される"""
        content = "# タイトル\n\n## 1.1 SREの概要\n"
        rules: list[NormalizationRule] = []
        result = preview_diff(content, rules)

        assert isinstance(result, str)
        # ルールがないので変更なし
        assert result.strip() == "" or "変更なし" in result or "No changes" in result

    def test_preview_diff_multiple_changes(self) -> None:
        """複数変更の差分プレビュー"""
        content = "# タイトル\n\n## SREの概要\n\nテキスト\n\nサイトとは何か\n\n"
        rules = [
            NormalizationRule(
                original="## SREの概要",
                normalized="## 1.1 SREの概要",
                line_number=3,
                action=NormalizationAction.ADD_NUMBER,
            ),
            NormalizationRule(
                original="サイトとは何か",
                normalized="### 1.1.1 サイトとは何か",
                line_number=7,
                action=NormalizationAction.ADD_MARKER,
            ),
        ]
        result = preview_diff(content, rules)

        # 両方の変更が含まれること
        assert "SREの概要" in result
        assert "サイトとは何か" in result
        assert "3" in result
        assert "7" in result

    def test_preview_diff_shows_arrow_or_separator(self) -> None:
        """差分表示に変換を示す記号（-> や =>）が含まれる"""
        content = "## SREの概要\n"
        rules = [
            NormalizationRule(
                original="## SREの概要",
                normalized="## 1.1 SREの概要",
                line_number=1,
                action=NormalizationAction.ADD_NUMBER,
            ),
        ]
        result = preview_diff(content, rules)

        # 変換を示す記号が含まれること
        has_arrow = "->" in result or "=>" in result or "\u2192" in result
        assert has_arrow, f"Expected arrow/separator in diff output, got: {result}"


# ============================================================
# Phase 4: apply_rules テスト (US3)
# ============================================================


class TestApplyRules:
    """apply_rules() のテスト"""

    def test_apply_rules_single_change(self) -> None:
        """単一ルールの適用で対象行のみが変更される"""
        content = "# タイトル\n\n## SREの概要\n\nテキスト\n"
        rules = [
            NormalizationRule(
                original="## SREの概要",
                normalized="## 1.1 SREの概要",
                line_number=3,
                action=NormalizationAction.ADD_NUMBER,
            ),
        ]
        result = apply_rules(content, rules)

        assert isinstance(result, str)
        lines = result.split("\n")
        # 3行目が変更されていること (0-indexed: index 2)
        assert lines[2] == "## 1.1 SREの概要"
        # 他の行は変更なし
        assert lines[0] == "# タイトル"
        assert lines[4] == "テキスト"

    def test_apply_rules_multiple_changes(self) -> None:
        """複数ルールの適用"""
        content = "# タイトル\n\n## SREの概要\n\nテキスト\n\nサイトとは何か\n"
        rules = [
            NormalizationRule(
                original="## SREの概要",
                normalized="## 1.1 SREの概要",
                line_number=3,
                action=NormalizationAction.ADD_NUMBER,
            ),
            NormalizationRule(
                original="サイトとは何か",
                normalized="### 1.1.1 サイトとは何か",
                line_number=7,
                action=NormalizationAction.ADD_MARKER,
            ),
        ]
        result = apply_rules(content, rules)

        lines = result.split("\n")
        assert lines[2] == "## 1.1 SREの概要"
        assert lines[6] == "### 1.1.1 サイトとは何か"

    def test_apply_rules_no_rules(self) -> None:
        """ルールがない場合はコンテンツがそのまま返される"""
        content = "# タイトル\n\n## SREの概要\n"
        result = apply_rules(content, [])

        assert result == content

    def test_apply_rules_preserves_newlines(self) -> None:
        """ルール適用後も改行構造が保持される"""
        content = "行1\n行2\n行3\n"
        rules = [
            NormalizationRule(
                original="行2",
                normalized="## 1.1 行2",
                line_number=2,
                action=NormalizationAction.ADD_NUMBER,
            ),
        ]
        result = apply_rules(content, rules)

        # 改行の数は変わらないこと
        assert result.count("\n") == content.count("\n")

    def test_apply_rules_returns_new_string(self) -> None:
        """apply_rules は元のコンテンツを変更せず新しい文字列を返す（不変性）"""
        content = "## SREの概要\n"
        original_content = content
        rules = [
            NormalizationRule(
                original="## SREの概要",
                normalized="## 1.1 SREの概要",
                line_number=1,
                action=NormalizationAction.ADD_NUMBER,
            ),
        ]
        result = apply_rules(content, rules)

        # 元の文字列は変更されていないこと
        assert content == original_content
        # 結果は異なること
        assert result != content

    def test_apply_rules_special_chars(self) -> None:
        """特殊文字を含む行のルール適用"""
        content = "## C++/Rustの比較 & 解説\n"
        rules = [
            NormalizationRule(
                original="## C++/Rustの比較 & 解説",
                normalized="## 3.1 C++/Rustの比較 & 解説",
                line_number=1,
                action=NormalizationAction.ADD_NUMBER,
            ),
        ]
        result = apply_rules(content, rules)

        lines = result.split("\n")
        assert lines[0] == "## 3.1 C++/Rustの比較 & 解説"

    def test_apply_rules_empty_content(self) -> None:
        """空コンテンツにルールを適用"""
        content = ""
        rules = [
            NormalizationRule(
                original="## テスト",
                normalized="## 1.1 テスト",
                line_number=1,
                action=NormalizationAction.ADD_NUMBER,
            ),
        ]
        result = apply_rules(content, rules)

        # 空コンテンツは空のまま（対象行が存在しないのでルールは適用されない）
        assert isinstance(result, str)
