"""Tests for TOC normalization CLI."""

from __future__ import annotations

from src.cli.normalize_toc import (
    TocFix,
    apply_fixes,
    find_toc_fixes,
    normalize_toc_line,
)


class TestNormalizeTocLine:
    """Tests for normalize_toc_line."""

    def test_fullwidth_slash(self) -> None:
        assert normalize_toc_line("CI／CD") == "CI/CD"

    def test_fullwidth_colon(self) -> None:
        assert normalize_toc_line("現在：SREの統合") == "現在:SREの統合"

    def test_fullwidth_digits(self) -> None:
        assert normalize_toc_line("１.２.３ タイトル") == "1.2.3 タイトル"

    def test_fullwidth_alpha(self) -> None:
        assert normalize_toc_line("ＡＢＣ") == "ABC"

    def test_extra_spaces_around_slash(self) -> None:
        assert normalize_toc_line("SLI / SLO") == "SLI/SLO"

    def test_fullwidth_slash_with_space(self) -> None:
        assert normalize_toc_line("CI／ CD") == "CI/CD"

    def test_bullet_to_middle_dot(self) -> None:
        assert normalize_toc_line("• 項目") == "· 項目"

    def test_no_change(self) -> None:
        line = "1.1.0 SREの概要"
        assert normalize_toc_line(line) == line

    def test_ideographic_space(self) -> None:
        assert normalize_toc_line("テスト\u3000項目") == "テスト 項目"

    def test_fullwidth_parens(self) -> None:
        assert normalize_toc_line("（テスト）") == "(テスト)"


class TestFindTocFixes:
    """Tests for find_toc_fixes."""

    def test_finds_fixes_in_toc_section(self) -> None:
        lines = [
            "--- page_0008 ---",
            "",
            "<!-- toc -->",
            "1.0.0 CI／CD",
            "1.1.0 正常なエントリ",
            "<!-- /toc -->",
        ]
        fixes = find_toc_fixes(lines)
        assert len(fixes) == 1
        assert fixes[0].line_number == 4
        assert fixes[0].original == "1.0.0 CI／CD"
        assert fixes[0].fixed == "1.0.0 CI/CD"

    def test_ignores_non_toc_lines(self) -> None:
        lines = [
            "CI／CD outside TOC",
            "<!-- toc -->",
            "1.0.0 正常",
            "<!-- /toc -->",
            "CI／CD also outside",
        ]
        fixes = find_toc_fixes(lines)
        assert len(fixes) == 0

    def test_multiple_toc_sections(self) -> None:
        lines = [
            "<!-- toc -->",
            "1.0.0 テスト１",
            "<!-- /toc -->",
            "",
            "<!-- toc -->",
            "2.0.0 テスト２",
            "<!-- /toc -->",
        ]
        fixes = find_toc_fixes(lines)
        assert len(fixes) == 2

    def test_empty_toc(self) -> None:
        lines = [
            "<!-- toc -->",
            "",
            "<!-- /toc -->",
        ]
        fixes = find_toc_fixes(lines)
        assert len(fixes) == 0

    def test_no_toc_markers(self) -> None:
        lines = ["CI／CD", "SLI / SLO"]
        fixes = find_toc_fixes(lines)
        assert len(fixes) == 0


class TestApplyFixes:
    """Tests for apply_fixes."""

    def test_apply_single_fix(self) -> None:
        lines = ["line 1", "CI／CD", "line 3"]
        fixes = [TocFix(line_number=2, original="CI／CD", fixed="CI/CD", reason="test")]
        result = apply_fixes(lines, fixes)
        assert result == ["line 1", "CI/CD", "line 3"]

    def test_apply_no_fixes(self) -> None:
        lines = ["line 1", "line 2"]
        result = apply_fixes(lines, [])
        assert result == lines

    def test_does_not_mutate_original(self) -> None:
        lines = ["CI／CD"]
        fixes = [TocFix(line_number=1, original="CI／CD", fixed="CI/CD", reason="test")]
        result = apply_fixes(lines, fixes)
        assert lines == ["CI／CD"]
        assert result == ["CI/CD"]
