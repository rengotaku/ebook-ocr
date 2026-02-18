"""Tests for src.ocr_ensemble ensemble OCR module."""


from src.ocr_ensemble import (
    EngineResult,
    EnsembleResult,
    calculate_similarity,
    calculate_similarity_matrix,
    merge_by_voting,
    vote_best_result,
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


class TestCalculateSimilarityMatrix:
    """Tests for calculate_similarity_matrix()."""

    def test_three_engines(self) -> None:
        """Matrix calculation for three engines."""
        results = {
            "yomitoku": "Hello World",
            "tesseract": "Hello World",
            "easyocr": "Hello Wrold",  # typo
        }
        matrix = calculate_similarity_matrix(results)

        # Self-similarity is 1.0
        assert matrix["yomitoku"]["yomitoku"] == 1.0
        assert matrix["tesseract"]["tesseract"] == 1.0

        # yomitoku and tesseract are identical
        assert matrix["yomitoku"]["tesseract"] == 1.0

        # easyocr has typo, lower similarity
        assert matrix["yomitoku"]["easyocr"] < 1.0
        assert matrix["yomitoku"]["easyocr"] > 0.8  # still similar


class TestVoteBestResult:
    """Tests for vote_best_result()."""

    def test_unanimous_agreement(self) -> None:
        """All engines agree - winner has most votes."""
        results = {
            "yomitoku": "Hello World",
            "tesseract": "Hello World",
            "easyocr": "Hello World",
        }
        matrix = calculate_similarity_matrix(results)
        text, winner, votes = vote_best_result(results, matrix, threshold=0.7)

        assert text == "Hello World"
        assert votes["yomitoku"] == 2  # agrees with 2 others
        assert votes["tesseract"] == 2
        assert votes["easyocr"] == 2

    def test_two_agree_one_different(self) -> None:
        """Two engines agree, one different - majority wins."""
        results = {
            "yomitoku": "Hello World",
            "tesseract": "Hello World",
            "easyocr": "Completely Different Text",
        }
        matrix = calculate_similarity_matrix(results)
        text, winner, votes = vote_best_result(results, matrix, threshold=0.7)

        assert text == "Hello World"
        assert winner in ["yomitoku", "tesseract"]
        assert votes["yomitoku"] == 1  # agrees with tesseract
        assert votes["tesseract"] == 1  # agrees with yomitoku
        assert votes["easyocr"] == 0  # agrees with none

    def test_no_agreement_prefers_yomitoku(self) -> None:
        """No agreement - falls back to priority order."""
        results = {
            "yomitoku": "Text A",
            "tesseract": "Text B",
            "easyocr": "Text C",
        }
        matrix = calculate_similarity_matrix(results)
        text, winner, votes = vote_best_result(results, matrix, threshold=0.9)

        # No agreement at 0.9 threshold, should prefer yomitoku
        assert winner == "yomitoku"
        assert text == "Text A"

    def test_single_engine(self) -> None:
        """Single engine returns its result."""
        results = {"yomitoku": "Only Result"}
        matrix = calculate_similarity_matrix(results)
        text, winner, votes = vote_best_result(results, matrix)

        assert text == "Only Result"
        assert winner == "yomitoku"

    def test_empty_results(self) -> None:
        """Empty results returns empty."""
        text, winner, votes = vote_best_result({}, {})
        assert text == ""
        assert winner == "none"


class TestMergeByVoting:
    """Tests for merge_by_voting()."""

    def test_merge_three_engines(self) -> None:
        """Merge with three engines."""
        results = {
            "yomitoku": "Hello World",
            "tesseract": "Hello World",
            "easyocr": "Hello Wrold",
        }
        ensemble = merge_by_voting(results)

        assert ensemble.merged == "Hello World"
        assert ensemble.source in ["yomitoku", "tesseract"]
        assert "yomitoku" in ensemble.results
        assert "tesseract" in ensemble.results
        assert "easyocr" in ensemble.results

    def test_merge_with_empty_result(self) -> None:
        """Merge handles engines with empty results."""
        results = {
            "yomitoku": "Hello World",
            "tesseract": "",
            "easyocr": "Hello World",
        }
        ensemble = merge_by_voting(results)

        assert ensemble.merged == "Hello World"
        # Only yomitoku and easyocr have valid results
        assert ensemble.source in ["yomitoku", "easyocr"]


class TestEnsembleResult:
    """Tests for EnsembleResult dataclass."""

    def test_create_result(self) -> None:
        """Can create EnsembleResult."""
        result = EnsembleResult(
            merged="merged text",
            results={"yomitoku": "d", "tesseract": "t", "easyocr": "e"},
            similarity_matrix={},
            source="yomitoku",
            votes={"yomitoku": 2, "tesseract": 1, "easyocr": 1},
        )
        assert result.merged == "merged text"
        assert result.source == "yomitoku"
        assert result.votes["yomitoku"] == 2


class TestEngineResult:
    """Tests for EngineResult dataclass."""

    def test_successful_result(self) -> None:
        """Successful engine result."""
        result = EngineResult(
            engine="tesseract",
            text="Hello",
            success=True,
        )
        assert result.success
        assert result.error is None

    def test_failed_result(self) -> None:
        """Failed engine result."""
        result = EngineResult(
            engine="tesseract",
            text="",
            success=False,
            error="Timeout",
        )
        assert not result.success
        assert result.error == "Timeout"
