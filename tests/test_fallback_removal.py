"""Tests for backward compatibility code removal.

Phase 5: User Story 4 - Fallback Removal Tests

Category A (Remove): Backward compatibility fallback
- ENGINE_PRIORITY["FALLBACK"] -> "DEFAULT"
- Legacy patterns in book_converter/parser.py

Category B (Keep): Error recovery fallbacks - NOT TESTED HERE
"""

import inspect

import pytest


class TestEnginePriorityFallback:
    """ENGINE_PRIORITY["FALLBACK"] should be renamed to "DEFAULT"."""

    def test_no_fallback_key(self) -> None:
        """ENGINE_PRIORITY should not have FALLBACK key."""
        from src.ocr_integrated import ENGINE_PRIORITY

        assert "FALLBACK" not in ENGINE_PRIORITY, (
            "ENGINE_PRIORITY should not have 'FALLBACK' key. "
            "Rename to 'DEFAULT' for clarity."
        )

    def test_has_default_key(self) -> None:
        """ENGINE_PRIORITY should have DEFAULT key."""
        from src.ocr_integrated import ENGINE_PRIORITY

        assert "DEFAULT" in ENGINE_PRIORITY, (
            "ENGINE_PRIORITY should have 'DEFAULT' key instead of 'FALLBACK'."
        )

    def test_default_engines_list(self) -> None:
        """DEFAULT should have the standard engine priority list."""
        from src.ocr_integrated import ENGINE_PRIORITY

        expected = ["yomitoku", "paddleocr", "tesseract"]
        assert ENGINE_PRIORITY.get("DEFAULT") == expected, (
            f"ENGINE_PRIORITY['DEFAULT'] should be {expected}"
        )


class TestLegacyPatternRemoval:
    """Test legacy backward compatibility patterns are removed from parser.py."""

    def test_no_legacy_comment(self) -> None:
        """Parser should not have 'Legacy patterns' comment."""
        from src.book_converter import parser

        source = inspect.getsource(parser)

        # Check for the specific legacy comment
        assert "Legacy patterns below for backward compatibility" not in source, (
            "Remove 'Legacy patterns below for backward compatibility' comment "
            "from parser.py"
        )

    def test_no_legacy_chapter_pattern_comment(self) -> None:
        """Parser should not have 'legacy' annotation in pattern comments."""
        from src.book_converter import parser

        source = inspect.getsource(parser)

        # Check for legacy pattern comments
        assert "- legacy" not in source.lower(), (
            "Remove '- legacy' annotation from pattern comments in parser.py"
        )

    def test_no_redundant_case_insensitive_chapter_pattern(self) -> None:
        """Parser should not have redundant case-insensitive Chapter pattern.

        The legacy pattern uses character-class based case insensitivity
        [Cc][Hh][Aa][Pp][Tt][Ee][Rr] which is redundant with re.IGNORECASE
        used in the new pattern.
        """
        from src.book_converter import parser

        source = inspect.getsource(parser)

        # The old pattern uses character-by-character case insensitivity
        # This is the signature of the legacy pattern
        assert "[Cc][Hh][Aa][Pp][Tt][Ee][Rr]" not in source, (
            "Remove legacy case-insensitive Chapter pattern. "
            "The new pattern with re.IGNORECASE handles this case."
        )

    def test_no_japanese_chapter_legacy_pattern(self) -> None:
        """Parser should not have hardcoded Japanese chapter pattern.

        According to CLAUDE.md, domain-specific values like chapter patterns
        should be configuration-driven, not hardcoded.
        """
        from src.book_converter import parser

        source = inspect.getsource(parser)

        # Check for hardcoded Japanese chapter pattern after "Legacy" comment
        # Note: This checks if the pattern exists in the legacy section
        # The pattern may exist in other legitimate places (e.g., tests)
        legacy_marker = "Legacy patterns"
        if legacy_marker in source:
            legacy_section_start = source.find(legacy_marker)
            legacy_section = source[legacy_section_start:legacy_section_start + 500]

            assert r"^第(\d+)章" not in legacy_section, (
                "Remove hardcoded Japanese chapter pattern from legacy section. "
                "Use configuration-driven patterns instead."
            )
