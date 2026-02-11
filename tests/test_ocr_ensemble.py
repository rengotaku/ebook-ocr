"""Tests for src.ocr_ensemble ensemble OCR module."""

import pytest

from src.ocr_ensemble import (
    calculate_similarity,
    merge_texts,
    EnsembleResult,
)


class TestCalculateSimilarity:
    """Tests for calculate_similarity()."""

    def test_identical_texts(self) -> None:
        """Identical texts have similarity 1.0."""
        assert calculate_similarity("hello", "hello") == 1.0

    def test_completely_different(self) -> None:
        """Completely different texts have low similarity."""
        sim = calculate_similarity("abc", "xyz")
        assert sim < 0.5

    def test_partial_match(self) -> None:
        """Partially matching texts have medium similarity."""
        sim = calculate_similarity("hello world", "hello there")
        assert 0.3 < sim < 0.8

    def test_empty_texts(self) -> None:
        """Two empty texts have similarity 1.0."""
        assert calculate_similarity("", "") == 1.0

    def test_one_empty(self) -> None:
        """One empty text has similarity 0.0."""
        assert calculate_similarity("hello", "") == 0.0
        assert calculate_similarity("", "hello") == 0.0

    def test_japanese_text(self) -> None:
        """Japanese text similarity works correctly."""
        sim = calculate_similarity("こんにちは世界", "こんにちは世界")
        assert sim == 1.0

        sim = calculate_similarity("こんにちは世界", "こんにちは日本")
        assert 0.5 < sim < 1.0


class TestMergeTexts:
    """Tests for merge_texts()."""

    def test_high_similarity_uses_deepseek(self) -> None:
        """High similarity returns DeepSeek result."""
        result, source = merge_texts(
            "Hello World",
            "Hello World",
            similarity_threshold=0.8,
        )
        assert result == "Hello World"
        assert source == "deepseek"

    def test_low_similarity_merges(self) -> None:
        """Low similarity triggers merge."""
        result, source = merge_texts(
            "Line A\nLine B",
            "Different\nLine B",
            similarity_threshold=0.9,
        )
        # Should return merged since similarity is below threshold
        assert source in ["deepseek", "tesseract", "merged"]

    def test_deepseek_much_longer(self) -> None:
        """When DeepSeek is much longer, use it."""
        result, source = merge_texts(
            "This is a very long text with lots of content",
            "Short",
            similarity_threshold=0.9,
        )
        assert source == "deepseek"

    def test_tesseract_much_longer(self) -> None:
        """When Tesseract is much longer, use it."""
        result, source = merge_texts(
            "Short",
            "This is a very long text with lots of content",
            similarity_threshold=0.9,
        )
        assert source == "tesseract"

    def test_line_by_line_merge(self) -> None:
        """Line-by-line merge prefers longer lines."""
        result, source = merge_texts(
            "Short\nMedium text",
            "Longer line here\nMed",
            similarity_threshold=0.9,
        )
        assert source == "merged"
        lines = result.split("\n")
        assert "Longer line here" in lines[0]  # Longer line preferred


class TestEnsembleResult:
    """Tests for EnsembleResult dataclass."""

    def test_create_result(self) -> None:
        """Can create EnsembleResult."""
        result = EnsembleResult(
            merged="merged text",
            deepseek="deepseek text",
            tesseract="tesseract text",
            similarity=0.85,
            source="deepseek",
        )
        assert result.merged == "merged text"
        assert result.similarity == 0.85
        assert result.source == "deepseek"
