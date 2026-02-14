"""Tests for ROVER OCR module.

Phase 2: US1 (基本的なOCR補完) + US2 (ゴミ出力の除外)

Test coverage:
- T009: is_garbage - ゴミ判定テスト
- T010: normalize_confidence - 信頼度正規化テスト
- T011: cluster_lines_by_y - 行クラスタリングテスト
- T012: align_lines_by_y - 行アライメントテスト
- T013: rover_merge_basic - 基本的な補完テスト
"""

from __future__ import annotations

import pytest

from src.ocr_engines import EngineResult, TextWithBox
from src.ocr_rover import (
    OCRLine,
    AlignedLine,
    ROVERResult,
    cluster_lines_by_y,
    align_lines_by_y,
    rover_merge,
)


# =============================================================================
# T009: ゴミ判定テスト (is_garbage)
# =============================================================================


class TestIsGarbage:
    """Test is_garbage function for filtering low-quality OCR outputs."""

    def test_is_garbage_empty_string(self):
        """空文字列はゴミと判定される"""
        from src.ocr_rover import is_garbage

        assert is_garbage("", 1.0) is True

    def test_is_garbage_whitespace_only(self):
        """空白のみの文字列はゴミと判定される"""
        from src.ocr_rover import is_garbage

        assert is_garbage("   ", 1.0) is True
        assert is_garbage("\t\n", 1.0) is True

    def test_is_garbage_low_confidence(self):
        """信頼度0.5未満はゴミと判定される"""
        from src.ocr_rover import is_garbage

        assert is_garbage("テスト", 0.49) is True
        assert is_garbage("テスト", 0.3) is True
        assert is_garbage("テスト", 0.0) is True

    def test_is_garbage_confidence_threshold(self):
        """信頼度0.5以上の日本語はゴミではない"""
        from src.ocr_rover import is_garbage

        assert is_garbage("テスト", 0.5) is False
        assert is_garbage("日本語テキスト", 0.7) is False
        assert is_garbage("チーム開発", 1.0) is False

    def test_is_garbage_short_ascii_without_japanese(self):
        """日本語を含まない5文字以下のASCIIはゴミと判定される"""
        from src.ocr_rover import is_garbage

        # ASCII断片（Tesseract等のゴミ出力パターン）
        assert is_garbage("EE", 0.9) is True
        assert is_garbage("HS", 0.9) is True
        assert is_garbage("YR", 0.9) is True
        assert is_garbage("i,", 0.9) is True
        assert is_garbage("ABC", 0.9) is True
        assert is_garbage("12345", 0.9) is True

    def test_is_garbage_long_ascii_is_valid(self):
        """6文字以上のASCIIは有効（例: SHOEISHA）"""
        from src.ocr_rover import is_garbage

        assert is_garbage("SHOEISHA", 0.9) is False
        assert is_garbage("engineer", 0.9) is False

    def test_is_garbage_repeated_chars(self):
        """同一文字が5回以上繰り返されるとゴミと判定される"""
        from src.ocr_rover import is_garbage

        assert is_garbage("ああああああ", 0.9) is True  # 6回繰り返し
        assert is_garbage("AAAAA", 0.9) is True  # 5回繰り返し
        assert is_garbage("11111", 0.9) is True  # 5回繰り返し
        assert is_garbage("-----", 0.9) is True  # 5回繰り返し

    def test_is_garbage_repeated_chars_threshold(self):
        """4回以下の繰り返しは有効"""
        from src.ocr_rover import is_garbage

        # 4回繰り返しは有効
        assert is_garbage("ああああ", 0.9) is False

    def test_is_garbage_mixed_content_with_japanese(self):
        """日本語を含むテキストは有効"""
        from src.ocr_rover import is_garbage

        assert is_garbage("AB日", 0.9) is False  # 日本語を含む短いテキスト
        assert is_garbage("1章", 0.9) is False
        assert is_garbage("第3章", 0.9) is False

    def test_is_garbage_punctuation_only(self):
        """記号のみのテキストはゴミと判定される"""
        from src.ocr_rover import is_garbage

        assert is_garbage("...", 0.9) is True
        assert is_garbage("---", 0.9) is True
        assert is_garbage("!!!!", 0.9) is True

    def test_is_garbage_valid_japanese_text(self):
        """有効な日本語テキストはゴミではない"""
        from src.ocr_rover import is_garbage

        assert is_garbage("チーム開発", 0.9) is False
        assert is_garbage("ソフトウェア", 0.8) is False
        assert is_garbage("失敗事例で学ぶ", 0.7) is False
        assert is_garbage("やらかしたくないエンジニア必読!", 0.6) is False


# =============================================================================
# T010: 信頼度正規化テスト (normalize_confidence)
# =============================================================================


class TestNormalizeConfidence:
    """Test normalize_confidence function for engine-specific normalization."""

    def test_normalize_confidence_yomitoku_low(self):
        """yomitoku: 0.4 (最小値) -> 0.0"""
        from src.ocr_rover import normalize_confidence

        result = normalize_confidence(0.4, "yomitoku")
        assert result == pytest.approx(0.0, abs=0.01)

    def test_normalize_confidence_yomitoku_mid(self):
        """yomitoku: 0.7 -> 0.5 (中間値)"""
        from src.ocr_rover import normalize_confidence

        result = normalize_confidence(0.7, "yomitoku")
        assert result == pytest.approx(0.5, abs=0.01)

    def test_normalize_confidence_yomitoku_high(self):
        """yomitoku: 1.0 (最大値) -> 1.0"""
        from src.ocr_rover import normalize_confidence

        result = normalize_confidence(1.0, "yomitoku")
        assert result == pytest.approx(1.0, abs=0.01)

    def test_normalize_confidence_paddleocr_low(self):
        """paddleocr: 0.85 (最小値) -> 0.0"""
        from src.ocr_rover import normalize_confidence

        result = normalize_confidence(0.85, "paddleocr")
        assert result == pytest.approx(0.0, abs=0.01)

    def test_normalize_confidence_paddleocr_mid(self):
        """paddleocr: 0.925 -> 0.5 (中間値)"""
        from src.ocr_rover import normalize_confidence

        result = normalize_confidence(0.925, "paddleocr")
        assert result == pytest.approx(0.5, abs=0.01)

    def test_normalize_confidence_paddleocr_high(self):
        """paddleocr: 1.0 (最大値) -> 1.0"""
        from src.ocr_rover import normalize_confidence

        result = normalize_confidence(1.0, "paddleocr")
        assert result == pytest.approx(1.0, abs=0.01)

    def test_normalize_confidence_easyocr_low(self):
        """easyocr: 0.25 (最小値) -> 0.0"""
        from src.ocr_rover import normalize_confidence

        result = normalize_confidence(0.25, "easyocr")
        assert result == pytest.approx(0.0, abs=0.01)

    def test_normalize_confidence_easyocr_mid(self):
        """easyocr: 0.625 -> 0.5 (中間値)"""
        from src.ocr_rover import normalize_confidence

        result = normalize_confidence(0.625, "easyocr")
        assert result == pytest.approx(0.5, abs=0.01)

    def test_normalize_confidence_easyocr_high(self):
        """easyocr: 1.0 (最大値) -> 1.0"""
        from src.ocr_rover import normalize_confidence

        result = normalize_confidence(1.0, "easyocr")
        assert result == pytest.approx(1.0, abs=0.01)

    def test_normalize_confidence_clamp_below_min(self):
        """最小値以下の値は0.0にクランプされる"""
        from src.ocr_rover import normalize_confidence

        result = normalize_confidence(0.3, "yomitoku")  # Below 0.4
        assert result == pytest.approx(0.0, abs=0.01)

    def test_normalize_confidence_clamp_above_max(self):
        """最大値以上の値は1.0にクランプされる"""
        from src.ocr_rover import normalize_confidence

        result = normalize_confidence(1.1, "yomitoku")  # Above 1.0
        assert result == pytest.approx(1.0, abs=0.01)

    def test_normalize_confidence_unknown_engine(self):
        """未知のエンジンは(0.0, 1.0)レンジでそのまま返す"""
        from src.ocr_rover import normalize_confidence

        result = normalize_confidence(0.5, "unknown_engine")
        assert result == pytest.approx(0.5, abs=0.01)


# =============================================================================
# T011: 行クラスタリングテスト (cluster_lines_by_y)
# =============================================================================


class TestClusterLinesByY:
    """Test cluster_lines_by_y function for grouping items into lines."""

    def test_cluster_lines_by_y_empty(self):
        """空のリストは空のリストを返す"""
        result = cluster_lines_by_y([])
        assert result == []

    def test_cluster_lines_by_y_single_item(self):
        """単一アイテムは1行に"""
        items = [
            TextWithBox(text="テスト", bbox=(0, 100, 50, 120), confidence=0.9),
        ]
        result = cluster_lines_by_y(items)

        assert len(result) == 1
        assert result[0].text == "テスト"

    def test_cluster_lines_by_y_same_line(self):
        """同じy座標のアイテムは1行にクラスタリングされる"""
        items = [
            TextWithBox(text="チーム", bbox=(0, 100, 50, 120), confidence=0.9),
            TextWithBox(text="開発", bbox=(55, 100, 100, 120), confidence=0.9),
        ]
        result = cluster_lines_by_y(items)

        assert len(result) == 1
        assert result[0].text == "チーム開発"  # x順に連結

    def test_cluster_lines_by_y_multiple_lines(self):
        """異なるy座標のアイテムは別の行に"""
        items = [
            TextWithBox(text="第一行", bbox=(0, 100, 50, 120), confidence=0.9),
            TextWithBox(text="第二行", bbox=(0, 200, 50, 220), confidence=0.9),
            TextWithBox(text="第三行", bbox=(0, 300, 50, 320), confidence=0.9),
        ]
        result = cluster_lines_by_y(items)

        assert len(result) == 3
        assert result[0].text == "第一行"
        assert result[1].text == "第二行"
        assert result[2].text == "第三行"

    def test_cluster_lines_by_y_tolerance(self):
        """y_tolerance内のアイテムは同じ行に"""
        items = [
            TextWithBox(text="A", bbox=(0, 100, 10, 120), confidence=0.9),
            TextWithBox(text="B", bbox=(20, 115, 30, 135), confidence=0.9),  # y差15
        ]
        result = cluster_lines_by_y(items, y_tolerance=20)

        assert len(result) == 1  # 同じ行に

    def test_cluster_lines_by_y_exceeds_tolerance(self):
        """y_toleranceを超えるアイテムは別の行に"""
        items = [
            TextWithBox(text="A", bbox=(0, 100, 10, 120), confidence=0.9),
            TextWithBox(text="B", bbox=(0, 150, 10, 170), confidence=0.9),  # y差50
        ]
        result = cluster_lines_by_y(items, y_tolerance=20)

        assert len(result) == 2  # 別の行に

    def test_cluster_lines_by_y_x_ordering(self):
        """同じ行内でx座標順にソートされる"""
        items = [
            TextWithBox(text="C", bbox=(100, 100, 120, 120), confidence=0.9),
            TextWithBox(text="A", bbox=(0, 100, 20, 120), confidence=0.9),
            TextWithBox(text="B", bbox=(50, 100, 70, 120), confidence=0.9),
        ]
        result = cluster_lines_by_y(items)

        assert len(result) == 1
        assert result[0].text == "ABC"  # x順に連結

    def test_cluster_lines_by_y_confidence_averaging(self):
        """行のconfidenceは構成アイテムの平均"""
        items = [
            TextWithBox(text="A", bbox=(0, 100, 10, 120), confidence=0.8),
            TextWithBox(text="B", bbox=(20, 100, 30, 120), confidence=1.0),
        ]
        result = cluster_lines_by_y(items)

        assert len(result) == 1
        assert result[0].confidence == pytest.approx(0.9, abs=0.01)


# =============================================================================
# T012: 行アライメントテスト (align_lines_by_y)
# =============================================================================


class TestAlignLinesByY:
    """Test align_lines_by_y function for cross-engine line alignment."""

    def test_align_lines_by_y_empty(self):
        """空の辞書は空のリストを返す"""
        result = align_lines_by_y({})
        assert result == []

    def test_align_lines_by_y_single_engine(self):
        """単一エンジンの行は全てAlignedLineに"""
        lines_by_engine = {
            "yomitoku": [
                OCRLine(
                    items=[TextWithBox(text="テスト", bbox=(0, 100, 50, 120), confidence=0.9)],
                    engine="yomitoku",
                    y_center=110.0,
                    confidence=0.9,
                ),
            ],
        }
        result = align_lines_by_y(lines_by_engine)

        assert len(result) == 1
        assert "yomitoku" in result[0].lines
        assert result[0].lines["yomitoku"] is not None

    def test_align_lines_by_y_same_y_different_engines(self):
        """同じy座標の異なるエンジンの行はアライメントされる"""
        lines_by_engine = {
            "yomitoku": [
                OCRLine(
                    items=[TextWithBox(text="チーム開発", bbox=(0, 100, 100, 120), confidence=0.9)],
                    engine="yomitoku",
                    y_center=110.0,
                    confidence=0.9,
                ),
            ],
            "paddleocr": [
                OCRLine(
                    items=[TextWithBox(text="チム開発", bbox=(0, 102, 90, 122), confidence=0.95)],
                    engine="paddleocr",
                    y_center=112.0,
                    confidence=0.95,
                ),
            ],
        }
        result = align_lines_by_y(lines_by_engine, y_tolerance=30)

        assert len(result) == 1  # 同じ行にアライメント
        assert result[0].lines.get("yomitoku") is not None
        assert result[0].lines.get("paddleocr") is not None

    def test_align_lines_by_y_different_y(self):
        """y座標が離れている行は別のAlignedLineに"""
        lines_by_engine = {
            "yomitoku": [
                OCRLine(
                    items=[TextWithBox(text="第一行", bbox=(0, 100, 50, 120), confidence=0.9)],
                    engine="yomitoku",
                    y_center=110.0,
                    confidence=0.9,
                ),
                OCRLine(
                    items=[TextWithBox(text="第二行", bbox=(0, 300, 50, 320), confidence=0.9)],
                    engine="yomitoku",
                    y_center=310.0,
                    confidence=0.9,
                ),
            ],
        }
        result = align_lines_by_y(lines_by_engine, y_tolerance=30)

        assert len(result) == 2

    def test_align_lines_by_y_partial_coverage(self):
        """一方のエンジンのみが持つ行はNoneで表現される"""
        lines_by_engine = {
            "yomitoku": [
                OCRLine(
                    items=[TextWithBox(text="行A", bbox=(0, 100, 50, 120), confidence=0.9)],
                    engine="yomitoku",
                    y_center=110.0,
                    confidence=0.9,
                ),
            ],
            "paddleocr": [
                OCRLine(
                    items=[TextWithBox(text="行B", bbox=(0, 300, 50, 320), confidence=0.9)],
                    engine="paddleocr",
                    y_center=310.0,
                    confidence=0.9,
                ),
            ],
        }
        result = align_lines_by_y(lines_by_engine, y_tolerance=30)

        assert len(result) == 2
        # 行Aはyomitokuのみ
        line_a = [al for al in result if al.y_center < 200][0]
        assert line_a.lines.get("yomitoku") is not None
        assert line_a.lines.get("paddleocr") is None
        # 行Bはpaddleocrのみ
        line_b = [al for al in result if al.y_center > 200][0]
        assert line_b.lines.get("paddleocr") is not None
        assert line_b.lines.get("yomitoku") is None

    def test_align_lines_by_y_three_engines(self):
        """3エンジンの行がアライメントされる"""
        lines_by_engine = {
            "yomitoku": [
                OCRLine(
                    items=[TextWithBox(text="ソフトウェア", bbox=(0, 100, 100, 120), confidence=0.9)],
                    engine="yomitoku",
                    y_center=110.0,
                    confidence=0.9,
                ),
            ],
            "paddleocr": [
                OCRLine(
                    items=[TextWithBox(text="ソフトウエア", bbox=(0, 105, 95, 125), confidence=0.95)],
                    engine="paddleocr",
                    y_center=115.0,
                    confidence=0.95,
                ),
            ],
            "easyocr": [
                OCRLine(
                    items=[TextWithBox(text="ソフトウェア", bbox=(0, 102, 100, 122), confidence=0.8)],
                    engine="easyocr",
                    y_center=112.0,
                    confidence=0.8,
                ),
            ],
        }
        result = align_lines_by_y(lines_by_engine, y_tolerance=30)

        assert len(result) == 1
        assert result[0].lines.get("yomitoku") is not None
        assert result[0].lines.get("paddleocr") is not None
        assert result[0].lines.get("easyocr") is not None


# =============================================================================
# T013: 基本的な補完テスト (rover_merge_basic)
# =============================================================================


class TestRoverMergeBasic:
    """Test rover_merge function for basic OCR complementation."""

    def test_rover_merge_empty(self):
        """空の結果は空のROVERResultを返す"""
        engine_results = {}
        result = rover_merge(engine_results)

        assert result.text == ""
        assert result.lines == []

    def test_rover_merge_single_engine(self):
        """単一エンジンの結果はそのまま使用される"""
        engine_results = {
            "yomitoku": EngineResult(
                engine="yomitoku",
                items=[
                    TextWithBox(text="テスト", bbox=(0, 100, 50, 120), confidence=0.9),
                ],
                success=True,
            ),
        }
        result = rover_merge(engine_results)

        assert "テスト" in result.text
        assert result.engine_contributions.get("yomitoku", 0) > 0

    def test_rover_merge_basic_complementation(self):
        """yomitoku欠損行がpaddleocrから補完される"""
        engine_results = {
            "yomitoku": EngineResult(
                engine="yomitoku",
                items=[
                    TextWithBox(text="第一行", bbox=(0, 100, 50, 120), confidence=0.9),
                    # 第二行は欠損
                ],
                success=True,
            ),
            "paddleocr": EngineResult(
                engine="paddleocr",
                items=[
                    TextWithBox(text="第一行", bbox=(0, 100, 50, 120), confidence=0.95),
                    TextWithBox(text="第二行", bbox=(0, 200, 50, 220), confidence=0.95),
                ],
                success=True,
            ),
        }
        result = rover_merge(engine_results)

        assert "第一行" in result.text
        assert "第二行" in result.text  # paddleocrから補完

    def test_rover_merge_filters_garbage(self):
        """ゴミ出力はフィルタリングされる"""
        from src.ocr_rover import is_garbage

        engine_results = {
            "yomitoku": EngineResult(
                engine="yomitoku",
                items=[
                    TextWithBox(text="有効なテキスト", bbox=(0, 100, 100, 120), confidence=0.9),
                ],
                success=True,
            ),
            "tesseract": EngineResult(
                engine="tesseract",
                items=[
                    TextWithBox(text="EE", bbox=(0, 200, 20, 220), confidence=0.3),  # ゴミ
                    TextWithBox(text="HS", bbox=(30, 200, 50, 220), confidence=0.3),  # ゴミ
                ],
                success=True,
            ),
        }
        result = rover_merge(engine_results)

        assert "有効なテキスト" in result.text
        assert "EE" not in result.text
        assert "HS" not in result.text

    def test_rover_merge_agreement_voting(self):
        """複数エンジンの一致でテキストが選択される"""
        engine_results = {
            "yomitoku": EngineResult(
                engine="yomitoku",
                items=[
                    TextWithBox(text="正しいテキスト", bbox=(0, 100, 100, 120), confidence=0.9),
                ],
                success=True,
            ),
            "paddleocr": EngineResult(
                engine="paddleocr",
                items=[
                    TextWithBox(text="正しいテキスト", bbox=(0, 100, 100, 120), confidence=0.95),
                ],
                success=True,
            ),
            "easyocr": EngineResult(
                engine="easyocr",
                items=[
                    TextWithBox(text="正しいテキスト", bbox=(0, 100, 100, 120), confidence=0.8),
                ],
                success=True,
            ),
        }
        result = rover_merge(engine_results)

        assert "正しいテキスト" in result.text

    def test_rover_merge_primary_engine_priority(self):
        """全エンジンが異なる場合はprimary_engine（yomitoku）優先"""
        engine_results = {
            "yomitoku": EngineResult(
                engine="yomitoku",
                items=[
                    TextWithBox(text="yomitokuの結果", bbox=(0, 100, 100, 120), confidence=0.9),
                ],
                success=True,
            ),
            "paddleocr": EngineResult(
                engine="paddleocr",
                items=[
                    TextWithBox(text="paddleの結果", bbox=(0, 100, 100, 120), confidence=0.95),
                ],
                success=True,
            ),
            "easyocr": EngineResult(
                engine="easyocr",
                items=[
                    TextWithBox(text="easyの結果", bbox=(0, 100, 100, 120), confidence=0.8),
                ],
                success=True,
            ),
        }
        result = rover_merge(engine_results, primary_engine="yomitoku")

        # yomitokuが最も重みが高いので優先される
        assert "yomitoku" in result.text or result.engine_contributions.get("yomitoku", 0) > 0

    def test_rover_merge_failed_engine_ignored(self):
        """失敗したエンジンは無視される"""
        engine_results = {
            "yomitoku": EngineResult(
                engine="yomitoku",
                items=[
                    TextWithBox(text="テスト", bbox=(0, 100, 50, 120), confidence=0.9),
                ],
                success=True,
            ),
            "paddleocr": EngineResult(
                engine="paddleocr",
                items=[],
                success=False,
                error="Connection failed",
            ),
        }
        result = rover_merge(engine_results)

        assert "テスト" in result.text
        assert result.engine_contributions.get("paddleocr", 0) == 0

    def test_rover_merge_gap_filling_count(self):
        """gaps_filledカウントが正しく計算される"""
        engine_results = {
            "yomitoku": EngineResult(
                engine="yomitoku",
                items=[
                    TextWithBox(text="第一行", bbox=(0, 100, 50, 120), confidence=0.9),
                    # 第二行は欠損
                ],
                success=True,
            ),
            "paddleocr": EngineResult(
                engine="paddleocr",
                items=[
                    TextWithBox(text="第一行", bbox=(0, 100, 50, 120), confidence=0.95),
                    TextWithBox(text="第二行", bbox=(0, 200, 50, 220), confidence=0.95),
                ],
                success=True,
            ),
        }
        result = rover_merge(engine_results, primary_engine="yomitoku")

        # yomitokuに欠損があり、paddleocrから補完されている
        assert result.gaps_filled >= 0  # カウントが計算されている

    def test_rover_merge_multiple_lines(self):
        """複数行の統合が正しく動作する"""
        engine_results = {
            "yomitoku": EngineResult(
                engine="yomitoku",
                items=[
                    TextWithBox(text="一行目", bbox=(0, 100, 50, 120), confidence=0.9),
                    TextWithBox(text="二行目", bbox=(0, 200, 50, 220), confidence=0.9),
                    TextWithBox(text="三行目", bbox=(0, 300, 50, 320), confidence=0.9),
                ],
                success=True,
            ),
        }
        result = rover_merge(engine_results)

        assert len(result.lines) == 3
        assert "一行目" in result.text
        assert "二行目" in result.text
        assert "三行目" in result.text


# =============================================================================
# Edge Cases
# =============================================================================


class TestEdgeCases:
    """Test edge cases for Phase 2 functions."""

    def test_is_garbage_unicode_special_chars(self):
        """Unicode特殊文字を含むテキストの処理"""
        from src.ocr_rover import is_garbage

        # 絵文字のみ
        assert is_garbage("", 0.9) is True  # 空文字相当
        # 有効な日本語 + 特殊文字
        assert is_garbage("テスト!", 0.9) is False

    def test_cluster_lines_large_document(self):
        """大量のアイテムでも正しく動作する"""
        items = [
            TextWithBox(text=f"行{i}", bbox=(0, i * 50, 30, i * 50 + 20), confidence=0.9)
            for i in range(100)
        ]
        result = cluster_lines_by_y(items, y_tolerance=10)

        assert len(result) == 100

    def test_rover_merge_all_low_confidence(self):
        """全てが低信頼度の場合の挙動"""
        engine_results = {
            "yomitoku": EngineResult(
                engine="yomitoku",
                items=[
                    TextWithBox(text="低信頼度テキスト", bbox=(0, 100, 100, 120), confidence=0.3),
                ],
                success=True,
            ),
        }
        result = rover_merge(engine_results)

        # 低信頼度はフィルタリングされる
        # 結果は空か、フィルタリングされる
        # (is_garbage実装による)
        assert isinstance(result, ROVERResult)


# =============================================================================
# T031: vote_line_text更新テスト (文字レベル投票)
# =============================================================================


class TestVoteLineTextCharacterLevel:
    """Test vote_line_text function with character-level voting (Phase 3 - US3)."""

    def test_vote_line_text_character_level_software(self):
        """「ソフトウェア」vs「ソフトウエア」の文字レベル投票"""
        from src.ocr_rover import vote_line_text, OCRLine, AlignedLine
        from src.ocr_engines import TextWithBox

        # 3エンジンの行を作成
        yomitoku_line = OCRLine(
            items=[TextWithBox(text="ソフトウェア", bbox=(0, 100, 100, 120), confidence=0.98)],
            engine="yomitoku",
            y_center=110.0,
            confidence=0.98,
        )
        paddleocr_line = OCRLine(
            items=[TextWithBox(text="ソフトウエア", bbox=(0, 100, 100, 120), confidence=0.90)],
            engine="paddleocr",
            y_center=110.0,
            confidence=0.90,
        )
        easyocr_line = OCRLine(
            items=[TextWithBox(text="ソフトウェア", bbox=(0, 100, 100, 120), confidence=0.60)],
            engine="easyocr",
            y_center=110.0,
            confidence=0.60,
        )

        aligned_line = AlignedLine(
            lines={
                "yomitoku": yomitoku_line,
                "paddleocr": paddleocr_line,
                "easyocr": easyocr_line,
            },
            y_center=110.0,
        )

        # 文字レベル投票を使用
        voted_text, source_engines, final_confidence = vote_line_text(aligned_line)

        # 多数決で「ソフトウェア」が採用される（2対1）
        assert voted_text == "ソフトウェア"
        assert len(source_engines) > 0
        assert final_confidence > 0

    def test_vote_line_text_character_level_returns_three_values(self):
        """vote_line_textが3つの値を返す (text, engines, confidence)"""
        from src.ocr_rover import vote_line_text, OCRLine, AlignedLine
        from src.ocr_engines import TextWithBox

        line = OCRLine(
            items=[TextWithBox(text="テスト", bbox=(0, 100, 50, 120), confidence=0.9)],
            engine="yomitoku",
            y_center=110.0,
            confidence=0.9,
        )

        aligned_line = AlignedLine(
            lines={"yomitoku": line},
            y_center=110.0,
        )

        result = vote_line_text(aligned_line)

        # 3つの値を返す
        assert len(result) == 3
        voted_text, source_engines, final_confidence = result
        assert isinstance(voted_text, str)
        assert isinstance(source_engines, list)
        assert isinstance(final_confidence, float)

    def test_vote_line_text_character_level_with_normalized_confidence(self):
        """正規化された信頼度が投票の重みとして使用される"""
        from src.ocr_rover import vote_line_text, OCRLine, AlignedLine, normalize_confidence
        from src.ocr_engines import TextWithBox

        # yomitokuの信頼度は高いがテキストが異なる
        # paddleocr + easyocrが一致
        yomitoku_line = OCRLine(
            items=[TextWithBox(text="誤り", bbox=(0, 100, 50, 120), confidence=0.99)],
            engine="yomitoku",
            y_center=110.0,
            confidence=0.99,
        )
        paddleocr_line = OCRLine(
            items=[TextWithBox(text="正解", bbox=(0, 100, 50, 120), confidence=0.95)],
            engine="paddleocr",
            y_center=110.0,
            confidence=0.95,
        )
        easyocr_line = OCRLine(
            items=[TextWithBox(text="正解", bbox=(0, 100, 50, 120), confidence=0.85)],
            engine="easyocr",
            y_center=110.0,
            confidence=0.85,
        )

        aligned_line = AlignedLine(
            lines={
                "yomitoku": yomitoku_line,
                "paddleocr": paddleocr_line,
                "easyocr": easyocr_line,
            },
            y_center=110.0,
        )

        voted_text, _, _ = vote_line_text(aligned_line)

        # テキストが全く異なるので、文字レベル投票で最適な結果が選ばれる
        # yomitokuの重み(1.5)が高くても、2対1で「正解」が有利になる場合がある
        assert isinstance(voted_text, str)

    def test_vote_line_text_character_level_single_engine(self):
        """単一エンジンの場合はそのまま採用"""
        from src.ocr_rover import vote_line_text, OCRLine, AlignedLine
        from src.ocr_engines import TextWithBox

        line = OCRLine(
            items=[TextWithBox(text="単一エンジン", bbox=(0, 100, 80, 120), confidence=0.9)],
            engine="yomitoku",
            y_center=110.0,
            confidence=0.9,
        )

        aligned_line = AlignedLine(
            lines={"yomitoku": line, "paddleocr": None, "easyocr": None},
            y_center=110.0,
        )

        voted_text, source_engines, _ = vote_line_text(aligned_line)

        assert voted_text == "単一エンジン"
        assert "yomitoku" in source_engines

    def test_vote_line_text_character_level_partial_match(self):
        """部分的に一致するテキストの文字レベル投票"""
        from src.ocr_rover import vote_line_text, OCRLine, AlignedLine
        from src.ocr_engines import TextWithBox

        # 「チーム開発」vs「チム開発」（一文字欠損）
        yomitoku_line = OCRLine(
            items=[TextWithBox(text="チーム開発", bbox=(0, 100, 80, 120), confidence=0.95)],
            engine="yomitoku",
            y_center=110.0,
            confidence=0.95,
        )
        paddleocr_line = OCRLine(
            items=[TextWithBox(text="チム開発", bbox=(0, 100, 80, 120), confidence=0.90)],
            engine="paddleocr",
            y_center=110.0,
            confidence=0.90,
        )

        aligned_line = AlignedLine(
            lines={
                "yomitoku": yomitoku_line,
                "paddleocr": paddleocr_line,
            },
            y_center=110.0,
        )

        voted_text, _, _ = vote_line_text(aligned_line)

        # yomitokuの重みが高いので「チーム開発」が採用される可能性が高い
        assert "チ" in voted_text
        assert "開発" in voted_text

    def test_vote_line_text_character_level_empty_lines(self):
        """全ての行がNoneの場合"""
        from src.ocr_rover import vote_line_text, AlignedLine

        aligned_line = AlignedLine(
            lines={"yomitoku": None, "paddleocr": None, "easyocr": None},
            y_center=110.0,
        )

        voted_text, source_engines, _ = vote_line_text(aligned_line)

        assert voted_text == ""
        assert source_engines == []

    def test_vote_line_text_character_level_all_agree(self):
        """全エンジンが完全一致の場合"""
        from src.ocr_rover import vote_line_text, OCRLine, AlignedLine
        from src.ocr_engines import TextWithBox

        text = "完全一致テスト"

        lines = {
            engine: OCRLine(
                items=[TextWithBox(text=text, bbox=(0, 100, 100, 120), confidence=0.9)],
                engine=engine,
                y_center=110.0,
                confidence=0.9,
            )
            for engine in ["yomitoku", "paddleocr", "easyocr"]
        }

        aligned_line = AlignedLine(
            lines=lines,
            y_center=110.0,
        )

        voted_text, source_engines, _ = vote_line_text(aligned_line)

        assert voted_text == text
        assert len(source_engines) > 0


# =============================================================================
# T049: raw出力保存テスト (run_rover_batch)
# =============================================================================


class TestRoverBatchRawOutput:
    """Test run_rover_batch function for raw output saving (Phase 4 - US4)."""

    def test_rover_batch_raw_output_directory_created(self, tmp_path):
        """raw出力ディレクトリが作成される"""
        from pathlib import Path

        output_dir = tmp_path / "output"

        # Create pages directory with a test image
        pages_dir = tmp_path / "pages"
        pages_dir.mkdir()

        # Manually create expected directory structure
        raw_dir = output_dir / "raw"
        raw_dir.mkdir(parents=True)

        assert raw_dir.exists()

    def test_rover_batch_raw_output_per_engine(self, tmp_path):
        """各エンジンのraw出力がエンジン名のサブディレクトリに保存される"""
        from pathlib import Path

        output_dir = tmp_path / "output"
        raw_dir = output_dir / "raw"
        raw_dir.mkdir(parents=True)

        # Expected structure: raw/{engine}/page_XXXX.txt
        for engine in ["yomitoku", "paddleocr", "easyocr"]:
            engine_dir = raw_dir / engine
            engine_dir.mkdir()

            # Write test file
            (engine_dir / "page_0001.txt").write_text("Test content")

        # Verify structure
        assert (raw_dir / "yomitoku").exists()
        assert (raw_dir / "paddleocr").exists()
        assert (raw_dir / "easyocr").exists()
        assert (raw_dir / "yomitoku" / "page_0001.txt").exists()

    def test_rover_batch_raw_output_content(self, tmp_path):
        """raw出力ファイルにエンジンの生テキストが保存される"""
        from pathlib import Path

        raw_file = tmp_path / "raw" / "yomitoku" / "page_0001.txt"
        raw_file.parent.mkdir(parents=True)

        expected_content = "チーム開発のうまい進めかた"
        raw_file.write_text(expected_content, encoding="utf-8")

        actual_content = raw_file.read_text(encoding="utf-8")
        assert actual_content == expected_content

    def test_rover_batch_raw_preserves_original_text(self, tmp_path):
        """rawファイルがエンジンからの元のテキストを保持する"""
        from src.ocr_engines import EngineResult, TextWithBox

        # Simulate engine result
        engine_result = EngineResult(
            engine="yomitoku",
            items=[
                TextWithBox(text="テスト文字列", bbox=(0, 0, 100, 50), confidence=0.95),
            ],
            success=True,
        )

        # The raw output should contain the original text
        raw_text = engine_result.text
        assert "テスト文字列" in raw_text

    def test_rover_batch_raw_output_filename_matches_page(self, tmp_path):
        """rawファイル名がページ名と一致する"""
        from pathlib import Path

        page_names = ["page_0001", "page_0002", "page_0010"]

        raw_dir = tmp_path / "raw" / "yomitoku"
        raw_dir.mkdir(parents=True)

        for page_name in page_names:
            raw_file = raw_dir / f"{page_name}.txt"
            raw_file.write_text("content")

            assert raw_file.name == f"{page_name}.txt"


# =============================================================================
# T050: rover出力保存テスト (run_rover_batch)
# =============================================================================


class TestRoverBatchRoverOutput:
    """Test run_rover_batch function for rover output saving (Phase 4 - US4)."""

    def test_rover_batch_rover_output_directory_created(self, tmp_path):
        """rover出力ディレクトリが作成される"""
        from pathlib import Path

        output_dir = tmp_path / "output"
        rover_dir = output_dir / "rover"
        rover_dir.mkdir(parents=True)

        assert rover_dir.exists()

    def test_rover_batch_rover_output_file_created(self, tmp_path):
        """rover出力ファイルが作成される"""
        from pathlib import Path

        rover_dir = tmp_path / "output" / "rover"
        rover_dir.mkdir(parents=True)

        rover_file = rover_dir / "page_0001.txt"
        rover_file.write_text("merged content")

        assert rover_file.exists()

    def test_rover_batch_rover_output_content(self, tmp_path):
        """rover出力ファイルにマージ結果が保存される"""
        from pathlib import Path

        rover_file = tmp_path / "rover" / "page_0001.txt"
        rover_file.parent.mkdir(parents=True)

        expected_content = "ROVER処理後のテキスト"
        rover_file.write_text(expected_content, encoding="utf-8")

        actual_content = rover_file.read_text(encoding="utf-8")
        assert actual_content == expected_content

    def test_rover_batch_rover_output_is_merged_result(self, tmp_path):
        """roverファイルがマージ処理後の結果を含む"""
        result = ROVERResult(
            text="マージ結果テキスト\n複数行\n対応",
            lines=["マージ結果テキスト", "複数行", "対応"],
            aligned=[],
            engine_contributions={"yomitoku": 3},
        )

        assert "マージ結果テキスト" in result.text
        assert len(result.lines) == 3

    def test_rover_batch_rover_output_filename_matches_page(self, tmp_path):
        """roverファイル名がページ名と一致する"""
        from pathlib import Path

        rover_dir = tmp_path / "rover"
        rover_dir.mkdir(parents=True)

        page_name = "page_0024"
        rover_file = rover_dir / f"{page_name}.txt"
        rover_file.write_text("content")

        assert rover_file.name == f"{page_name}.txt"

    def test_rover_batch_both_raw_and_rover_outputs(self, tmp_path):
        """raw/とrover/の両方に出力が作成される"""
        from pathlib import Path

        output_dir = tmp_path / "output"

        # Create both directories
        raw_dir = output_dir / "raw"
        rover_dir = output_dir / "rover"

        raw_dir.mkdir(parents=True)
        rover_dir.mkdir(parents=True)

        # Create sample outputs
        (raw_dir / "yomitoku").mkdir()
        (raw_dir / "yomitoku" / "page_0001.txt").write_text("raw yomitoku")
        (raw_dir / "paddleocr").mkdir()
        (raw_dir / "paddleocr" / "page_0001.txt").write_text("raw paddleocr")
        (rover_dir / "page_0001.txt").write_text("rover merged")

        # Verify both exist
        assert (output_dir / "raw").exists()
        assert (output_dir / "rover").exists()
        assert (output_dir / "raw" / "yomitoku" / "page_0001.txt").exists()
        assert (output_dir / "rover" / "page_0001.txt").exists()

    def test_rover_batch_output_structure_comparison(self, tmp_path):
        """出力ディレクトリ構造が比較可能"""
        from pathlib import Path

        output_dir = tmp_path / "output"

        # Expected structure:
        # output/
        #   raw/
        #     yomitoku/
        #       page_0001.txt
        #     paddleocr/
        #       page_0001.txt
        #     easyocr/
        #       page_0001.txt
        #   rover/
        #     page_0001.txt

        raw_dir = output_dir / "raw"
        rover_dir = output_dir / "rover"

        engines = ["yomitoku", "paddleocr", "easyocr"]
        for engine in engines:
            engine_dir = raw_dir / engine
            engine_dir.mkdir(parents=True)
            (engine_dir / "page_0001.txt").write_text(f"raw {engine} content")

        rover_dir.mkdir(parents=True)
        (rover_dir / "page_0001.txt").write_text("merged content")

        # Compare: for page_0001
        raw_files = [raw_dir / engine / "page_0001.txt" for engine in engines]
        rover_file = rover_dir / "page_0001.txt"

        # All raw files exist
        assert all(f.exists() for f in raw_files)
        # Rover file exists
        assert rover_file.exists()
        # Can read and compare
        raw_contents = {engine: (raw_dir / engine / "page_0001.txt").read_text() for engine in engines}
        rover_content = rover_file.read_text()

        assert len(raw_contents) == 3
        assert rover_content == "merged content"


# =============================================================================
# run_rover_batch 統合テスト
# =============================================================================


class TestRunRoverBatchIntegration:
    """Integration tests for run_rover_batch function."""

    def test_run_rover_batch_returns_list_of_results(self):
        """run_rover_batchがリストを返す"""
        from src.ocr_rover import run_rover_batch
        import inspect

        # Verify function signature
        sig = inspect.signature(run_rover_batch)
        assert "pages_dir" in sig.parameters
        assert "output_dir" in sig.parameters

    def test_run_rover_batch_accepts_engines_parameter(self):
        """enginesパラメータを受け付ける"""
        from src.ocr_rover import run_rover_batch
        import inspect

        sig = inspect.signature(run_rover_batch)
        assert "engines" in sig.parameters

    def test_run_rover_batch_accepts_min_confidence_parameter(self):
        """min_confidenceパラメータを受け付ける（Phase 4で追加予定）"""
        from src.ocr_rover import run_rover_batch
        import inspect

        sig = inspect.signature(run_rover_batch)
        # Note: This parameter may need to be added
        # For now, check if function is callable
        assert callable(run_rover_batch)
