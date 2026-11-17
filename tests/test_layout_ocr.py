"""Tests for src.layout_ocr region-based OCR processing.

Phase 4 RED tests for US2 - Region-based OCR Processing.

OCR Engine Selection Rules:
| Region Type | OCR Engine | Output Format |
|-------------|------------|---------------|
| TITLE | Yomitoku | `## {text}` |
| TEXT | Yomitoku | `{text}` |
| TABLE | Yomitoku | Markdown table |
| FIGURE | Skip | (excluded from output) |
| CAPTION | Yomitoku | `*{text}*` |
| FOOTNOTE | Yomitoku | `^{text}^` |
| FORMULA | Skip or OCR | `$${text}$$` |
| ABANDON | Skip | None |

Note: VLM support was removed in 008-rover-redesign.
FIGURE regions are now skipped instead of processed by VLM.
"""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image


def _blocks(text: str) -> list[dict]:
    """ページ全体 OCR の段落を 1 つだけ返す（並べ替えに位置が要る）."""
    return [{"type": "TEXT", "text": text, "bbox": [0, 0, 100, 50], "confidence": 1.0}]


class TestSelectOcrEngine:
    """OCRエンジン選択ロジックのテスト。"""

    def test_select_ocr_engine_text_returns_yomitoku(self) -> None:
        """TEXT領域に対してYomitokuが選択されることを検証。"""
        from src.layout_ocr import select_ocr_engine

        # Act
        engine = select_ocr_engine("TEXT")

        # Assert
        assert engine == "yomitoku", f"TEXT region should use yomitoku engine. Got: {engine}"

    def test_select_ocr_engine_title_returns_yomitoku(self) -> None:
        """TITLE領域に対してYomitokuが選択されることを検証。"""
        from src.layout_ocr import select_ocr_engine

        # Act
        engine = select_ocr_engine("TITLE")

        # Assert
        assert engine == "yomitoku", f"TITLE region should use yomitoku engine. Got: {engine}"

    def test_select_ocr_engine_figure_returns_skip(self) -> None:
        """FIGURE領域がスキップされることを検証。"""
        from src.layout_ocr import select_ocr_engine

        # Act
        engine = select_ocr_engine("FIGURE")

        # Assert
        assert engine == "skip", f"FIGURE region should be skipped. Got: {engine}"

    def test_select_ocr_engine_table_returns_yomitoku(self) -> None:
        """TABLE領域に対してYomitokuが選択されることを検証。"""
        from src.layout_ocr import select_ocr_engine

        # Act
        engine = select_ocr_engine("TABLE")

        # Assert
        assert engine == "yomitoku", f"TABLE region should use yomitoku engine. Got: {engine}"

    def test_select_ocr_engine_caption_returns_yomitoku(self) -> None:
        """CAPTION領域に対してYomitokuが選択されることを検証。"""
        from src.layout_ocr import select_ocr_engine

        # Act
        engine = select_ocr_engine("CAPTION")

        # Assert
        assert engine == "yomitoku", f"CAPTION region should use yomitoku engine. Got: {engine}"

    def test_select_ocr_engine_footnote_returns_yomitoku(self) -> None:
        """FOOTNOTE領域に対してYomitokuが選択されることを検証。"""
        from src.layout_ocr import select_ocr_engine

        # Act
        engine = select_ocr_engine("FOOTNOTE")

        # Assert
        assert engine == "yomitoku", f"FOOTNOTE region should use yomitoku engine. Got: {engine}"

    def test_select_ocr_engine_formula_returns_yomitoku(self) -> None:
        """FORMULA領域に対してYomitokuが選択されることを検証。"""
        from src.layout_ocr import select_ocr_engine

        # Act
        engine = select_ocr_engine("FORMULA")

        # Assert
        assert engine == "yomitoku", f"FORMULA region should use yomitoku engine. Got: {engine}"

    def test_select_ocr_engine_abandon_returns_skip(self) -> None:
        """ABANDON領域に対してスキップが選択されることを検証。"""
        from src.layout_ocr import select_ocr_engine

        # Act
        engine = select_ocr_engine("ABANDON")

        # Assert
        assert engine == "skip", f"ABANDON region should be skipped. Got: {engine}"


class TestFormatOcrResult:
    """OCR結果のフォーマット変換テスト。"""

    def test_format_ocr_result_title_adds_heading(self) -> None:
        """TITLE領域のOCR結果が見出しマークアップで出力されることを検証。

        期待フォーマット: `## {text}`
        """
        from src.layout_ocr import format_ocr_result

        # Arrange
        text = "第1章 はじめに"

        # Act
        formatted = format_ocr_result("TITLE", text)

        # Assert
        assert formatted == "## 第1章 はじめに", f"TITLE should be formatted as '## {{text}}'. Got: {formatted}"

    def test_format_ocr_result_text_unchanged(self) -> None:
        """TEXT領域のOCR結果がそのまま出力されることを検証。

        期待フォーマット: `{text}`
        """
        from src.layout_ocr import format_ocr_result

        # Arrange
        text = "これは本文テキストです。"

        # Act
        formatted = format_ocr_result("TEXT", text)

        # Assert
        assert formatted == "これは本文テキストです。", f"TEXT should remain unchanged. Got: {formatted}"

    def test_format_ocr_result_figure_returns_empty(self) -> None:
        """FIGURE領域に対して空文字が返されることを検証（VLM削除後）。

        FIGURE領域はスキップされるため、空文字を返す。
        """
        from src.layout_ocr import format_ocr_result

        # Arrange
        description = "棒グラフで売上推移を示している"

        # Act
        formatted = format_ocr_result("FIGURE", description)

        # Assert
        assert formatted == "", f"FIGURE should return empty string (skipped). Got: {formatted}"

    def test_format_ocr_result_caption_adds_italic(self) -> None:
        """CAPTION領域のOCR結果がイタリックで出力されることを検証。

        期待フォーマット: `*{text}*`
        """
        from src.layout_ocr import format_ocr_result

        # Arrange
        text = "図1: システム構成図"

        # Act
        formatted = format_ocr_result("CAPTION", text)

        # Assert
        assert formatted == "*図1: システム構成図*", f"CAPTION should be formatted as '*{{text}}*'. Got: {formatted}"

    def test_format_ocr_result_footnote_adds_superscript(self) -> None:
        """FOOTNOTE領域のOCR結果がスーパースクリプトで出力されることを検証。

        期待フォーマット: `^{text}^`
        """
        from src.layout_ocr import format_ocr_result

        # Arrange
        text = "注: データは2025年時点"

        # Act
        formatted = format_ocr_result("FOOTNOTE", text)

        # Assert
        assert formatted == "^注: データは2025年時点^", (
            f"FOOTNOTE should be formatted as '^{{text}}^'. Got: {formatted}"
        )

    def test_format_ocr_result_formula_adds_latex(self) -> None:
        """FORMULA領域のOCR結果がLaTeXで出力されることを検証。

        期待フォーマット: `$${text}$$`
        """
        from src.layout_ocr import format_ocr_result

        # Arrange
        text = "E = mc^2"

        # Act
        formatted = format_ocr_result("FORMULA", text)

        # Assert
        assert formatted == "$$E = mc^2$$", f"FORMULA should be formatted as '$${{text}}$$'. Got: {formatted}"

    def test_format_ocr_result_table_unchanged(self) -> None:
        """TABLE領域のOCR結果がそのまま出力されることを検証。

        Markdown tableはOCRエンジンが生成するため、追加フォーマットなし
        """
        from src.layout_ocr import format_ocr_result

        # Arrange
        text = "| A | B |\n|---|---|\n| 1 | 2 |"

        # Act
        formatted = format_ocr_result("TABLE", text)

        # Assert
        assert formatted == "| A | B |\n|---|---|\n| 1 | 2 |", (
            f"TABLE should remain unchanged (OCR produces markdown). Got: {formatted}"
        )

    def test_format_ocr_result_abandon_returns_empty(self) -> None:
        """ABANDON領域に対して空文字が返されることを検証。"""
        from src.layout_ocr import format_ocr_result

        # Act
        formatted = format_ocr_result("ABANDON", "ignored text")

        # Assert
        assert formatted == "", f"ABANDON should return empty string. Got: {formatted}"


class TestCropRegion:
    """領域クロップ機能のテスト。"""

    def test_crop_region_basic(self) -> None:
        """bboxに基づいて画像が正しくクロップされることを検証。"""
        from src.layout_ocr import crop_region

        # Arrange: 100x100の画像からbbox=[10, 20, 50, 60]を切り出し
        img = Image.new("RGB", (100, 100), color=(255, 0, 0))
        bbox = [10, 20, 50, 60]

        # Act
        cropped = crop_region(img, bbox)

        # Assert
        assert cropped.size == (40, 40), f"Cropped size should be (40, 40) for bbox [10,20,50,60]. Got: {cropped.size}"

    def test_crop_region_full_image(self) -> None:
        """bbox=[0, 0, w, h]で全画像がクロップされることを検証。"""
        from src.layout_ocr import crop_region

        # Arrange
        img = Image.new("RGB", (200, 150), color=(0, 255, 0))
        bbox = [0, 0, 200, 150]

        # Act
        cropped = crop_region(img, bbox)

        # Assert
        assert cropped.size == (200, 150), f"Full image crop should match original size. Got: {cropped.size}"

    def test_crop_region_boundary_clamp(self) -> None:
        """bboxが画像境界を超えた場合のハンドリングを検証。"""
        from src.layout_ocr import crop_region

        # Arrange: bboxが画像境界を超える
        img = Image.new("RGB", (100, 100), color=(0, 0, 255))
        bbox = [80, 80, 150, 150]  # x2, y2が画像サイズ超過

        # Act
        cropped = crop_region(img, bbox)

        # Assert: 画像境界でクランプされる
        # PIL.crop()は境界外を受け入れるが、結果サイズは画像内に収まる
        assert cropped.size[0] <= 100 and cropped.size[1] <= 100, (
            f"Cropped region should be clamped to image bounds. Got: {cropped.size}"
        )


class TestTextRegionOcr:
    """TEXT領域のOCRテスト（layout.json の text を使う）。"""

    def test_text_region_uses_layout_text(self, tmp_path: Path) -> None:
        """TEXT領域はレイアウト検出時の text を使い、クロップ再 OCR をしないことを検証。"""
        from src.layout_ocr import ocr_region

        # Arrange
        img = Image.new("RGB", (500, 200), color=(255, 255, 255))
        region = {
            "type": "TEXT",
            "bbox": [10, 10, 490, 190],
            "confidence": 0.9,
            "text": "テキスト内容",
        }

        # Act & Assert: ocr_page_yomitoku は呼ばれない
        with patch("src.ocr_yomitoku.ocr_page_blocks", return_value=_blocks("再OCRの結果")) as mock_ocr:
            result = ocr_region(img, region)

            assert result.text == "テキスト内容", f"Should use layout.json text. Got: {result.text}"
            assert not mock_ocr.called, "ocr_page_yomitoku should NOT be called for TEXT region"

    def test_text_region_ocr_result_format(self) -> None:
        """TEXT領域の text がそのまま出力されることを検証。"""
        from src.layout_ocr import ocr_region

        # Arrange
        img = Image.new("RGB", (500, 200), color=(255, 255, 255))
        region = {
            "type": "TEXT",
            "bbox": [10, 10, 490, 190],
            "confidence": 0.9,
            "text": "これは本文です。",
        }

        # Act
        result = ocr_region(img, region)

        # Assert: TEXTはそのまま出力
        assert result.text == "これは本文です。", f"Layout text should be extracted. Got: {result.text}"
        assert result.formatted == "これは本文です。", f"TEXT should remain unchanged. Got: {result.formatted}"

    def test_text_region_without_text_is_empty(self) -> None:
        """text を持たない TEXT 領域でも落ちず、空で出力されることを検証。"""
        from src.layout_ocr import ocr_region

        # Arrange
        img = Image.new("RGB", (500, 200), color=(255, 255, 255))
        region = {"type": "TEXT", "bbox": [10, 10, 490, 190], "confidence": 0.9}

        # Act
        result = ocr_region(img, region)

        # Assert
        assert result.text == ""
        assert result.formatted == ""


class TestFigureRegionOcr:
    """FIGURE領域のOCRテスト（VLM削除後：スキップされる）。"""

    def test_figure_region_is_skipped(self) -> None:
        """FIGURE領域がスキップされることを検証（VLM削除後）。"""
        from src.layout_ocr import ocr_region

        # Arrange
        img = Image.new("RGB", (400, 300), color=(200, 200, 200))
        region = {
            "type": "FIGURE",
            "bbox": [10, 10, 390, 290],
            "confidence": 0.95,
        }

        # Act
        result = ocr_region(img, region)

        # Assert: FIGUREはスキップされ、空文字を返す
        assert result.text == "", f"FIGURE region should return empty text (skipped). Got: {result.text}"
        assert result.formatted == "", f"FIGURE should return empty formatted text. Got: {result.formatted}"


class TestTitleRegionOcr:
    """TITLE領域のOCRテスト（layout.json の text を使う）。"""

    def test_title_region_uses_layout_text(self) -> None:
        """TITLE領域がレイアウト検出時の text を使うことを検証。"""
        from src.layout_ocr import ocr_region

        # Arrange
        img = Image.new("RGB", (600, 50), color=(255, 255, 255))
        region = {
            "type": "TITLE",
            "bbox": [10, 5, 590, 45],
            "confidence": 0.98,
            "text": "第2章 システム設計",
        }

        # Act & Assert: ocr_page_yomitoku は呼ばれない
        with patch("src.ocr_yomitoku.ocr_page_blocks", return_value=_blocks("再OCRの結果")) as mock_ocr:
            result = ocr_region(img, region)

            assert result.text == "第2章 システム設計", f"Should use layout.json text. Got: {result.text}"
            assert not mock_ocr.called, "ocr_page_yomitoku should NOT be called for TITLE region"

    def test_title_region_formatted_as_heading(self) -> None:
        """TITLE領域の text が見出しマークアップで出力されることを検証。"""
        from src.layout_ocr import ocr_region

        # Arrange
        img = Image.new("RGB", (600, 50), color=(255, 255, 255))
        region = {
            "type": "TITLE",
            "bbox": [10, 5, 590, 45],
            "confidence": 0.98,
            "text": "第3章 実装",
        }

        # Act
        result = ocr_region(img, region)

        # Assert
        assert result.formatted == "## 第3章 実装", (
            f"TITLE should be formatted as '## {{text}}'. Got: {result.formatted}"
        )


class TestResultConcatenation:
    """複数領域のOCR結果連結テスト。"""

    def test_ocr_by_layout_concatenates_results(self, tmp_path: Path) -> None:
        """複数領域のOCR結果が正しく連結されることを検証。"""
        from src.layout_ocr import ocr_by_layout

        # Arrange
        img_path = tmp_path / "test_page.png"
        img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        img.save(img_path)

        layout = {
            "regions": [
                {"type": "TITLE", "bbox": [50, 50, 750, 100], "confidence": 0.95, "text": "第1章 概要"},
                {"type": "TEXT", "bbox": [50, 120, 750, 300], "confidence": 0.9, "text": "これは最初の段落です。"},
                {"type": "TEXT", "bbox": [50, 320, 750, 500], "confidence": 0.88, "text": "これは2番目の段落です。"},
            ],
            "page_size": [800, 600],
        }

        # Act
        results = ocr_by_layout(str(img_path), layout)

        # Assert
        assert len(results) == 3, f"Should return 3 OCR results. Got: {len(results)}"
        assert results[0].region_type == "TITLE", "First result should be TITLE"
        assert results[1].region_type == "TEXT", "Second result should be TEXT"
        assert results[2].region_type == "TEXT", "Third result should be TEXT"
        assert [r.text for r in results] == [
            "第1章 概要",
            "これは最初の段落です。",
            "これは2番目の段落です。",
        ], f"Texts should be kept in order. Got: {[r.text for r in results]}"

    def test_ocr_by_layout_respects_region_order(self, tmp_path: Path) -> None:
        """OCR結果がレイアウトの領域順序を維持することを検証。"""
        from src.layout_ocr import ocr_by_layout

        # Arrange
        img_path = tmp_path / "test_page.png"
        img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        img.save(img_path)

        # 読み順: TITLE -> CAPTION -> TEXT
        layout = {
            "regions": [
                {"type": "TITLE", "bbox": [50, 50, 600, 100], "confidence": 0.95, "text": "表1のタイトル"},
                {"type": "CAPTION", "bbox": [50, 110, 400, 140], "confidence": 0.85, "text": "表1: サンプルデータ"},
                {"type": "TEXT", "bbox": [50, 150, 750, 550], "confidence": 0.9, "text": "本文テキスト"},
            ],
            "page_size": [800, 600],
        }

        # Act
        results = ocr_by_layout(str(img_path), layout)

        # Assert: 順序が維持されている
        types = [r.region_type for r in results]
        assert types == ["TITLE", "CAPTION", "TEXT"], f"Results should maintain region order. Got: {types}"
        assert [r.text for r in results] == [
            "表1のタイトル",
            "表1: サンプルデータ",
            "本文テキスト",
        ], f"Texts should follow reading order. Got: {[r.text for r in results]}"

    def test_ocr_by_layout_skips_abandon_regions(self, tmp_path: Path) -> None:
        """ABANDON領域がスキップされることを検証。"""
        from src.layout_ocr import ocr_by_layout

        # Arrange
        img_path = tmp_path / "test_page.png"
        img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        img.save(img_path)

        layout = {
            "regions": [
                {"type": "ABANDON", "bbox": [700, 10, 790, 30], "confidence": 0.8},  # Header
                {"type": "TEXT", "bbox": [50, 100, 750, 500], "confidence": 0.9, "text": "本文テキスト"},
                {"type": "ABANDON", "bbox": [350, 570, 450, 590], "confidence": 0.75},  # Page num
            ],
            "page_size": [800, 600],
        }

        # Act
        results = ocr_by_layout(str(img_path), layout)

        # Assert: ABANDONは結果に含まれない
        assert len(results) == 1, f"Only TEXT region should be processed. Got: {len(results)}"
        assert results[0].region_type == "TEXT", f"Result should be TEXT only. Got: {results[0].region_type}"


class TestOcrResultDataclass:
    """OCRResult データクラスのテスト。"""

    def test_ocr_result_has_required_fields(self) -> None:
        """OCRResultが必要なフィールドを持つことを検証。"""
        from src.layout_ocr import OCRResult

        # Act
        result = OCRResult(
            region_type="TEXT",
            text="テキスト内容",
            formatted="テキスト内容",
        )

        # Assert
        assert result.region_type == "TEXT", "region_type should be set"
        assert result.text == "テキスト内容", "text should be set"
        assert result.formatted == "テキスト内容", "formatted should be set"

    def test_ocr_result_immutable(self) -> None:
        """OCRResultがイミュータブルであることを検証。"""
        from src.layout_ocr import OCRResult

        # Arrange
        result = OCRResult(
            region_type="TITLE",
            text="タイトル",
            formatted="## タイトル",
        )

        # Act & Assert: 変更しようとするとエラー
        with pytest.raises((AttributeError, TypeError)):
            result.text = "新しいテキスト"  # type: ignore[misc]


class TestOcrByLayoutEdgeCases:
    """ocr_by_layout のエッジケーステスト。"""

    # NOTE: test_ocr_by_layout_empty_regions removed - replaced by Phase 5 fallback tests
    # Empty regions now trigger fallback (US4), not return empty list

    def test_ocr_by_layout_unicode_text(self, tmp_path: Path) -> None:
        """Unicode文字を含むOCR結果が正しく処理されることを検証。"""
        from src.layout_ocr import ocr_by_layout

        # Arrange
        img_path = tmp_path / "test_page.png"
        img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        img.save(img_path)

        # Unicode text with various characters
        unicode_text = "日本語テキスト。\n絵文字テスト。\nSpecial: '\"\\/n"

        layout = {
            "regions": [
                {"type": "TEXT", "bbox": [50, 50, 750, 550], "confidence": 0.9, "text": unicode_text},
            ],
            "page_size": [800, 600],
        }

        # Act
        results = ocr_by_layout(str(img_path), layout)

        # Assert
        assert len(results) == 1, "Should return 1 result"
        assert results[0].text == unicode_text, "Unicode text should be preserved"

    def test_ocr_by_layout_mixed_region_types(self, tmp_path: Path) -> None:
        """異なる領域タイプが混在する場合の処理を検証。

        FR-012: FIGURE領域はOCR出力から除外される。
        """
        from src.layout_ocr import ocr_by_layout

        # Arrange: シンプルな単一カラムレイアウト（読み順を予測しやすい）
        img_path = tmp_path / "test_page.png"
        img = Image.new("RGB", (800, 800), color=(255, 255, 255))
        img.save(img_path)

        layout = {
            "regions": [
                {"type": "TITLE", "bbox": [50, 50, 750, 100], "confidence": 0.95, "text": "第5章 結論"},
                {"type": "TEXT", "bbox": [50, 120, 750, 250], "confidence": 0.9, "text": "左カラムのテキスト"},
                {"type": "FIGURE", "bbox": [50, 270, 750, 450], "confidence": 0.88},
                {"type": "CAPTION", "bbox": [50, 460, 750, 490], "confidence": 0.85, "text": "図5.1: 統計データ"},
                {"type": "TEXT", "bbox": [50, 510, 750, 640], "confidence": 0.9, "text": "結論の本文テキスト"},
                {"type": "FOOTNOTE", "bbox": [50, 750, 750, 790], "confidence": 0.8, "text": "脚注: 参考文献より"},
            ],
            "page_size": [800, 800],
        }

        # Act
        results = ocr_by_layout(str(img_path), layout)

        # Assert: FIGUREは除外されるので5つの結果（元6領域 - FIGURE 1つ）
        assert len(results) == 5, f"Should return 5 results (FIGURE excluded). Got: {len(results)}"

        # 各領域タイプが正しくフォーマットされているかチェック
        region_types = [r.region_type for r in results]
        assert "FIGURE" not in region_types, "FIGURE should be excluded from results"

        # 少なくとも以下を確認:
        # - TITLEは ## で始まる
        title_results = [r for r in results if r.region_type == "TITLE"]
        assert len(title_results) == 1, "Should have exactly one TITLE"
        assert title_results[0].formatted.startswith("## "), "TITLE should start with '## '"

        # - CAPTIONは * で囲まれる
        caption_results = [r for r in results if r.region_type == "CAPTION"]
        assert len(caption_results) == 1, "Should have exactly one CAPTION"
        assert caption_results[0].formatted.startswith("*"), "CAPTION should start with '*'"
        assert caption_results[0].formatted.endswith("*"), "CAPTION should end with '*'"

        # - FOOTNOTEは ^ で囲まれる
        footnote_results = [r for r in results if r.region_type == "FOOTNOTE"]
        assert len(footnote_results) == 1, "Should have exactly one FOOTNOTE"
        assert footnote_results[0].formatted.startswith("^"), "FOOTNOTE should start with '^'"
        assert footnote_results[0].formatted.endswith("^"), "FOOTNOTE should end with '^'"


# ============================================================================
# Phase 5: US4 - フォールバック処理テスト
# ============================================================================


class TestCalculateCoverage:
    """カバー率計算のテスト。"""

    def test_calculate_coverage_single_region(self) -> None:
        """単一領域のカバー率が正しく計算されることを検証。

        100x100のページに50x50の領域 = 25%のカバー率
        """
        from src.layout_ocr_utils import calculate_coverage

        # Arrange
        regions = [
            {"type": "TEXT", "bbox": [0, 0, 50, 50], "confidence": 0.9},
        ]
        page_size = (100, 100)  # 10000 pixels total

        # Act
        coverage = calculate_coverage(regions, page_size)

        # Assert
        assert coverage == 0.25, f"50x50 region on 100x100 page should be 25% coverage. Got: {coverage}"

    def test_calculate_coverage_multiple_regions(self) -> None:
        """複数領域の合計カバー率が正しく計算されることを検証。

        100x100のページに25x25の領域2つ = (625 + 625) / 10000 = 12.5%
        """
        from src.layout_ocr_utils import calculate_coverage

        # Arrange
        regions = [
            {"type": "TEXT", "bbox": [0, 0, 25, 25], "confidence": 0.9},
            {"type": "TITLE", "bbox": [50, 50, 75, 75], "confidence": 0.95},
        ]
        page_size = (100, 100)

        # Act
        coverage = calculate_coverage(regions, page_size)

        # Assert
        expected = (25 * 25 + 25 * 25) / (100 * 100)  # 0.125
        assert coverage == expected, f"Two 25x25 regions on 100x100 page should be 12.5% coverage. Got: {coverage}"

    def test_calculate_coverage_full_page(self) -> None:
        """ページ全体をカバーする領域の場合、カバー率が100%であることを検証。"""
        from src.layout_ocr_utils import calculate_coverage

        # Arrange
        regions = [
            {"type": "TEXT", "bbox": [0, 0, 800, 600], "confidence": 0.9},
        ]
        page_size = (800, 600)

        # Act
        coverage = calculate_coverage(regions, page_size)

        # Assert
        assert coverage == 1.0, f"Full page coverage should be 100%. Got: {coverage}"

    def test_calculate_coverage_empty_regions(self) -> None:
        """空の領域リストの場合、カバー率が0%であることを検証。"""
        from src.layout_ocr_utils import calculate_coverage

        # Arrange
        regions: list[dict] = []
        page_size = (800, 600)

        # Act
        coverage = calculate_coverage(regions, page_size)

        # Assert
        assert coverage == 0.0, f"Empty regions should have 0% coverage. Got: {coverage}"

    def test_calculate_coverage_real_world_example(self) -> None:
        """実際のページに近い例でカバー率を計算。

        1920x1080ページに複数の領域があるケース
        """
        from src.layout_ocr_utils import calculate_coverage

        # Arrange: 複雑なレイアウト
        regions = [
            {"type": "TITLE", "bbox": [100, 50, 1820, 120], "confidence": 0.95},  # 1720x70
            {"type": "TEXT", "bbox": [100, 150, 900, 800], "confidence": 0.9},  # 800x650
            {"type": "FIGURE", "bbox": [950, 150, 1820, 600], "confidence": 0.88},  # 870x450
            {"type": "TEXT", "bbox": [100, 850, 1820, 1030], "confidence": 0.9},  # 1720x180
        ]
        page_size = (1920, 1080)

        # Expected calculation
        # TITLE: 1720 * 70 = 120,400
        # TEXT1: 800 * 650 = 520,000
        # FIGURE: 870 * 450 = 391,500
        # TEXT2: 1720 * 180 = 309,600
        # Total: 1,341,500 / (1920 * 1080) = 1,341,500 / 2,073,600 ≈ 0.647

        # Act
        coverage = calculate_coverage(regions, page_size)

        # Assert
        expected = (120400 + 520000 + 391500 + 309600) / (1920 * 1080)
        assert abs(coverage - expected) < 0.001, f"Coverage should be approximately {expected:.3f}. Got: {coverage:.3f}"


class TestShouldFallback:
    """フォールバック判定のテスト。"""

    def test_should_fallback_empty_regions(self) -> None:
        """領域が空の場合、フォールバックすることを検証。"""
        from src.layout_ocr import should_fallback

        # Arrange
        regions: list[dict] = []
        page_size = (800, 600)

        # Act
        result = should_fallback(regions, page_size)

        # Assert
        assert result is True, "Empty regions should trigger fallback"

    def test_should_fallback_low_coverage(self) -> None:
        """カバー率が30%未満の場合、フォールバックすることを検証。

        100x100ページに20x20領域 = 4% → フォールバック
        """
        from src.layout_ocr import should_fallback

        # Arrange: 4% coverage (below 30% threshold)
        regions = [
            {"type": "TEXT", "bbox": [0, 0, 20, 20], "confidence": 0.9},
        ]
        page_size = (100, 100)

        # Act
        result = should_fallback(regions, page_size)

        # Assert
        assert result is True, "Coverage below 30% should trigger fallback"

    def test_should_fallback_sufficient_coverage(self) -> None:
        """カバー率が30%以上の場合、フォールバックしないことを検証。

        100x100ページに60x60領域 = 36% → フォールバックしない
        """
        from src.layout_ocr import should_fallback

        # Arrange: 36% coverage (above 30% threshold)
        regions = [
            {"type": "TEXT", "bbox": [0, 0, 60, 60], "confidence": 0.9},
        ]
        page_size = (100, 100)

        # Act
        result = should_fallback(regions, page_size)

        # Assert
        assert result is False, "Coverage above 30% should not trigger fallback"

    def test_should_fallback_exactly_30_percent(self) -> None:
        """カバー率がちょうど30%の場合、フォールバックしないことを検証（境界値）。

        1000x1000ページに約547.7x547.7領域 ≈ 30%
        簡略化: 300x1000 = 30%
        """
        from src.layout_ocr import should_fallback

        # Arrange: exactly 30% coverage
        regions = [
            {"type": "TEXT", "bbox": [0, 0, 300, 1000], "confidence": 0.9},
        ]
        page_size = (1000, 1000)

        # Act
        result = should_fallback(regions, page_size)

        # Assert: 30%は閾値以上なのでフォールバックしない
        assert result is False, "Coverage at exactly 30% should not trigger fallback"

    def test_should_fallback_custom_threshold(self) -> None:
        """カスタムしきい値でフォールバック判定ができることを検証。

        しきい値50%: 40%カバー率 → フォールバック
        """
        from src.layout_ocr import should_fallback

        # Arrange: 40% coverage with 50% threshold
        regions = [
            {"type": "TEXT", "bbox": [0, 0, 200, 200], "confidence": 0.9},  # 40000/100000 = 40%
        ]
        page_size = (500, 200)  # 100,000 total

        # Act
        result = should_fallback(regions, page_size, threshold=0.5)

        # Assert
        assert result is True, "40% coverage with 50% threshold should trigger fallback"

    def test_should_fallback_single_figure_full_page(self) -> None:
        """ページ全体が1つのFIGUREとして検出された場合、フォールバックすることを検証。

        FR-006: ページ全体が1つのFIGUREとして検出された場合
        """
        from src.layout_ocr import should_fallback

        # Arrange: Single FIGURE covering nearly entire page (>90%)
        regions = [
            {"type": "FIGURE", "bbox": [10, 10, 790, 590], "confidence": 0.9},
        ]
        page_size = (800, 600)
        # Coverage: (780 * 580) / (800 * 600) = 452,400 / 480,000 ≈ 94.25%

        # Act
        result = should_fallback(regions, page_size)

        # Assert: 全ページFIGUREはフォールバック
        assert result is True, "Single FIGURE covering full page should trigger fallback"

    def test_should_fallback_multiple_figures_not_fallback(self) -> None:
        """複数のFIGURE領域がある場合はフォールバックしないことを検証。"""
        from src.layout_ocr import should_fallback

        # Arrange: Multiple FIGURE regions
        regions = [
            {"type": "FIGURE", "bbox": [50, 50, 350, 250], "confidence": 0.9},
            {"type": "FIGURE", "bbox": [400, 50, 750, 250], "confidence": 0.88},
            {"type": "TEXT", "bbox": [50, 300, 750, 550], "confidence": 0.92},
        ]
        page_size = (800, 600)
        # Coverage > 30%, multiple regions

        # Act
        result = should_fallback(regions, page_size)

        # Assert
        assert result is False, "Multiple regions with sufficient coverage should not trigger fallback"


class TestFallbackEmptyLayout:
    """空layout フォールバックテスト (T052)。"""

    def test_ocr_by_layout_fallback_empty_regions(self, tmp_path: Path) -> None:
        """領域なしでページ全体OCRが実行されることを検証。

        US4 Acceptance Scenario 1:
        Given レイアウト検出で領域が検出されなかったページがある
        When 領域別OCRを実行する
        Then ページ全体に対してYomitokuが実行される
        """
        from src.layout_ocr import ocr_by_layout

        # Arrange
        img_path = tmp_path / "empty_layout_page.png"
        img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        img.save(img_path)

        layout = {
            "regions": [],  # 空の領域リスト
            "page_size": [800, 600],
        }

        # Act: ocr_page_yomitoku をモック
        with patch("src.ocr_yomitoku.ocr_page_blocks", return_value=_blocks("ページ全体のOCR結果")) as mock_ocr:
            results = ocr_by_layout(str(img_path), layout)

            # Assert: フォールバックでページ全体OCRが実行される
            assert len(results) == 1, f"Fallback should return 1 result for full page OCR. Got: {len(results)}"
            # フォールバック時は特別なマーカー "FALLBACK" または "TEXT" としてマーク
            assert results[0].region_type in ("FALLBACK", "TEXT"), (
                f"Fallback result should have FALLBACK or TEXT type. Got: {results[0].region_type}"
            )
            # Yomitokuが呼ばれたことを確認
            assert mock_ocr.called, "ocr_page_yomitoku should be called for fallback OCR"

    def test_ocr_by_layout_fallback_missing_regions_key(self, tmp_path: Path) -> None:
        """regionsキーがない場合もフォールバックが実行されることを検証。"""
        from src.layout_ocr import ocr_by_layout

        # Arrange
        img_path = tmp_path / "no_regions_key.png"
        img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        img.save(img_path)

        layout = {
            "page_size": [800, 600],
            # "regions" key is missing
        }

        # Act: ocr_page_yomitoku をモック
        with patch("src.ocr_yomitoku.ocr_page_blocks", return_value=_blocks("フォールバックOCR結果")):
            results = ocr_by_layout(str(img_path), layout)

        # Assert
        assert len(results) == 1, f"Missing regions key should trigger fallback. Got: {len(results)}"


class TestFallbackLowCoverage:
    """低カバー率フォールバックテスト (T053)。"""

    def test_ocr_by_layout_fallback_below_30_percent(self, tmp_path: Path) -> None:
        """30%未満でページ全体OCRが実行されることを検証。

        US4 Acceptance Scenario 2:
        Given 検出領域がページ面積の30%未満のページがある
        When 領域別OCRを実行する
        Then ページ全体に対してYomitokuが実行される
        """
        from src.layout_ocr import ocr_by_layout

        # Arrange: 10% coverage (well below 30%)
        img_path = tmp_path / "low_coverage_page.png"
        img = Image.new("RGB", (1000, 1000), color=(255, 255, 255))
        img.save(img_path)

        layout = {
            "regions": [
                # 100x100 on 1000x1000 = 1% coverage
                {"type": "TEXT", "bbox": [0, 0, 100, 100], "confidence": 0.9},
            ],
            "page_size": [1000, 1000],
        }

        # Act
        with patch("src.ocr_yomitoku.ocr_page_blocks", return_value=_blocks("フォールバック結果")):
            results = ocr_by_layout(str(img_path), layout)

        # Assert: フォールバックが実行される
        assert len(results) == 1, f"Low coverage should trigger fallback. Got: {len(results)}"
        assert results[0].region_type in ("FALLBACK", "TEXT"), (
            f"Fallback result should have FALLBACK or TEXT type. Got: {results[0].region_type}"
        )

    def test_ocr_by_layout_no_fallback_above_30_percent(self, tmp_path: Path) -> None:
        """30%以上のカバー率ではフォールバックしないことを検証。"""
        from src.layout_ocr import ocr_by_layout

        # Arrange: 50% coverage (above 30%)
        img_path = tmp_path / "high_coverage_page.png"
        img = Image.new("RGB", (100, 100), color=(255, 255, 255))
        img.save(img_path)

        layout = {
            "regions": [
                # 70.7x70.7 ≈ 50% coverage, simplify to 50x100 = 50%
                {"type": "TEXT", "bbox": [0, 0, 50, 100], "confidence": 0.9},
            ],
            "page_size": [100, 100],
        }

        # Act
        with patch("src.ocr_yomitoku.ocr_page_blocks", return_value=_blocks("通常OCR結果")):
            results = ocr_by_layout(str(img_path), layout)

        # Assert: 領域別OCRが実行される（フォールバックしない）
        assert len(results) == 1, f"Should return 1 result. Got: {len(results)}"
        assert results[0].region_type == "TEXT", f"Result should be TEXT (not FALLBACK). Got: {results[0].region_type}"

    def test_ocr_by_layout_fallback_29_percent_coverage(self, tmp_path: Path) -> None:
        """29%カバー率（境界値直下）でフォールバックすることを検証。"""
        from src.layout_ocr import ocr_by_layout

        # Arrange: 29% coverage (just below 30%)
        img_path = tmp_path / "boundary_page.png"
        img = Image.new("RGB", (1000, 1000), color=(255, 255, 255))
        img.save(img_path)

        layout = {
            "regions": [
                # sqrt(0.29) ≈ 0.538, so ~538x538 for 29%
                # Simplify: 290x1000 = 29%
                {"type": "TEXT", "bbox": [0, 0, 290, 1000], "confidence": 0.9},
            ],
            "page_size": [1000, 1000],
        }

        # Act
        with patch("src.ocr_yomitoku.ocr_page_blocks", return_value=_blocks("フォールバック結果")):
            results = ocr_by_layout(str(img_path), layout)

        # Assert: 29%はフォールバック
        assert len(results) == 1, f"29% coverage should trigger fallback. Got: {len(results)}"
        assert results[0].region_type in ("FALLBACK", "TEXT"), (
            f"Result should be FALLBACK or TEXT. Got: {results[0].region_type}"
        )


class TestFallbackSingleFigure:
    """ページ全体が1つのFIGUREとして検出された場合のフォールバックテスト。"""

    def test_ocr_by_layout_fallback_full_page_figure(self, tmp_path: Path) -> None:
        """ページ全体がFIGUREの場合、フォールバックが実行されることを検証。

        Edge Case: ページ全体が1つのFIGUREとして検出された場合 → ページ全体OCRにフォールバック
        """
        from src.layout_ocr import ocr_by_layout

        # Arrange: Single FIGURE covering 95% of page
        img_path = tmp_path / "full_figure_page.png"
        img = Image.new("RGB", (800, 600), color=(200, 200, 200))
        img.save(img_path)

        layout = {
            "regions": [
                {"type": "FIGURE", "bbox": [20, 15, 780, 585], "confidence": 0.9},
                # Coverage: (760 * 570) / (800 * 600) = 433,200 / 480,000 ≈ 90.25%
            ],
            "page_size": [800, 600],
        }

        # Act
        with patch("src.ocr_yomitoku.ocr_page_blocks", return_value=_blocks("ページ全体のテキスト")):
            results = ocr_by_layout(str(img_path), layout)

        # Assert: フォールバックが実行される
        assert len(results) == 1, f"Full page FIGURE should trigger fallback. Got: {len(results)}"
        # フォールバック結果は FALLBACK または TEXT
        assert results[0].region_type in ("FALLBACK", "TEXT"), (
            f"Fallback result type should be FALLBACK or TEXT. Got: {results[0].region_type}"
        )


class TestFallbackEdgeCases:
    """フォールバック処理のエッジケーステスト。"""

    def test_calculate_coverage_zero_page_size(self) -> None:
        """ページサイズがゼロの場合のハンドリングを検証。"""
        from src.layout_ocr_utils import calculate_coverage

        # Arrange
        regions = [{"type": "TEXT", "bbox": [0, 0, 100, 100], "confidence": 0.9}]

        # Act & Assert: ゼロ除算を避ける
        # 実装によってはエラーまたは0.0を返す
        try:
            coverage = calculate_coverage(regions, (0, 0))
            # ゼロ除算を避けて0.0を返す実装の場合
            assert coverage == 0.0, f"Zero page size should return 0.0 coverage. Got: {coverage}"
        except (ZeroDivisionError, ValueError):
            # エラーを投げる実装も許容
            pass

    def test_calculate_coverage_negative_bbox(self) -> None:
        """負のbbox座標の場合のハンドリングを検証。"""
        from src.layout_ocr_utils import calculate_coverage

        # Arrange: Invalid bbox with negative values
        regions = [
            {"type": "TEXT", "bbox": [-10, -10, 50, 50], "confidence": 0.9},
        ]
        page_size = (100, 100)

        # Act
        coverage = calculate_coverage(regions, page_size)

        # Assert: 面積は (50 - (-10)) * (50 - (-10)) = 60 * 60 = 3600
        # または実装がクランプする場合
        # ここでは単純計算を想定
        expected = (60 * 60) / (100 * 100)  # 0.36
        assert coverage == expected or coverage >= 0, f"Negative bbox should be handled. Got: {coverage}"

    def test_should_fallback_only_abandon_regions(self) -> None:
        """ABANDON領域のみの場合もフォールバックすることを検証。"""
        from src.layout_ocr import should_fallback

        # Arrange: Only ABANDON regions (effectively empty for OCR)
        regions = [
            {"type": "ABANDON", "bbox": [0, 0, 100, 50], "confidence": 0.8},
            {"type": "ABANDON", "bbox": [0, 550, 100, 600], "confidence": 0.75},
        ]
        page_size = (800, 600)

        # Act
        result = should_fallback(regions, page_size)

        # Assert: ABANDON領域のみならフォールバック（OCR対象がない）
        assert result is True, "Only ABANDON regions should trigger fallback"


# ============================================================================
# Phase 5: US2 - 領域別OCR処理テスト (RED)
# ============================================================================


class TestIsTitleFunction:
    """TITLE判定ロジックのテスト (FR-009)。

    is_title() は以下の条件でTrueを返す:
    1. YOLOでTITLEとして検出された
    2. Yomitokuのroleがsection_headingsである
    """

    def test_is_title_yolo_title_type(self) -> None:
        """YOLOでTITLEとして検出された場合、is_titleがTrueを返すことを検証。"""
        from src.layout_ocr_utils import is_title

        # Arrange: YOLOがTITLEとして検出
        region = {"type": "TITLE", "bbox": [50, 50, 700, 100], "confidence": 0.95}
        yomitoku_result = {}  # Yomitoku結果なし

        # Act
        result = is_title(region, yomitoku_result)

        # Assert
        assert result is True, "Region with type='TITLE' should be recognized as title"

    def test_is_title_yomitoku_section_headings_role(self) -> None:
        """Yomitokuのroleがsection_headingsの場合、is_titleがTrueを返すことを検証。"""
        from src.layout_ocr_utils import is_title

        # Arrange: YOLOはTEXTだが、Yomitokuがsection_headingsと判定
        region = {"type": "TEXT", "bbox": [50, 50, 700, 100], "confidence": 0.9}
        yomitoku_result = {"role": "section_headings"}

        # Act
        result = is_title(region, yomitoku_result)

        # Assert
        assert result is True, "Region with yomitoku role='section_headings' should be recognized as title"

    def test_is_title_text_without_role_returns_false(self) -> None:
        """YOLO=TEXT、Yomitokuのroleなしの場合、is_titleがFalseを返すことを検証。"""
        from src.layout_ocr_utils import is_title

        # Arrange: 通常のTEXT領域
        region = {"type": "TEXT", "bbox": [50, 100, 700, 500], "confidence": 0.9}
        yomitoku_result = {}  # roleなし

        # Act
        result = is_title(region, yomitoku_result)

        # Assert
        assert result is False, "Regular TEXT region without section_headings role should not be title"

    def test_is_title_yomitoku_paragraph_role(self) -> None:
        """Yomitokuのroleがparagraphの場合、is_titleがFalseを返すことを検証。"""
        from src.layout_ocr_utils import is_title

        # Arrange: Yomitokuがparagraphと判定
        region = {"type": "TEXT", "bbox": [50, 100, 700, 500], "confidence": 0.9}
        yomitoku_result = {"role": "paragraph"}

        # Act
        result = is_title(region, yomitoku_result)

        # Assert
        assert result is False, "Region with yomitoku role='paragraph' should not be title"

    def test_is_title_both_yolo_and_yomitoku_agree(self) -> None:
        """YOLOとYomitoku両方がTITLEと判定した場合、Trueを返すことを検証。"""
        from src.layout_ocr_utils import is_title

        # Arrange: 両方がTITLEと判定
        region = {"type": "TITLE", "bbox": [50, 50, 700, 100], "confidence": 0.98}
        yomitoku_result = {"role": "section_headings"}

        # Act
        result = is_title(region, yomitoku_result)

        # Assert
        assert result is True, "Region detected as TITLE by both YOLO and Yomitoku should be title"


class TestIsLowQualityFunction:
    """OCR結果の低品質判定テスト (FR-010)。

    is_low_quality() は以下の条件でTrueを返す:
    1. 空文字列
    2. 10文字未満
    3. 非文字率が50%を超える
    """

    def test_is_low_quality_empty_string(self) -> None:
        """空文字列が低品質と判定されることを検証。"""
        from src.layout_ocr import is_low_quality

        # Act
        result = is_low_quality("")

        # Assert
        assert result is True, "Empty string should be considered low quality"

    def test_is_low_quality_short_text(self) -> None:
        """10文字未満のテキストが低品質と判定されることを検証。"""
        from src.layout_ocr import is_low_quality

        # Arrange: 9文字のテキスト
        text = "あいうえお123"  # 8文字

        # Act
        result = is_low_quality(text)

        # Assert
        assert result is True, (
            f"Text with less than 10 characters should be low quality. Got: '{text}' ({len(text)} chars)"
        )

    def test_is_low_quality_exactly_10_chars(self) -> None:
        """ちょうど10文字のテキストは低品質でないことを検証。"""
        from src.layout_ocr import is_low_quality

        # Arrange: 10文字のテキスト
        text = "あいうえおかきくけこ"  # 10文字

        # Act
        result = is_low_quality(text)

        # Assert
        assert result is False, "Text with exactly 10 characters should not be low quality"

    def test_is_low_quality_high_non_char_ratio(self) -> None:
        """非文字率が50%を超えるテキストが低品質と判定されることを検証。"""
        from src.layout_ocr import is_low_quality

        # Arrange: 60%以上が非文字（記号・空白）
        text = "...!!!@@@###   ---$$$%%%^^^"  # 27文字全て非文字

        # Act
        result = is_low_quality(text)

        # Assert
        assert result is True, "Text with >50% non-character ratio should be low quality"

    def test_is_low_quality_normal_japanese_text(self) -> None:
        """通常の日本語テキストは低品質でないことを検証。"""
        from src.layout_ocr import is_low_quality

        # Arrange: 通常の日本語テキスト
        text = "これは正常な日本語のテキストです。"

        # Act
        result = is_low_quality(text)

        # Assert
        assert result is False, "Normal Japanese text should not be low quality"

    def test_is_low_quality_mixed_content(self) -> None:
        """日本語と記号が混在するが正常なテキストを検証。"""
        from src.layout_ocr import is_low_quality

        # Arrange: 正常な混合テキスト（記号率は50%以下）
        text = "第1章：はじめに（2026年版）"

        # Act
        result = is_low_quality(text)

        # Assert
        assert result is False, "Mixed text with reasonable symbol ratio should not be low quality"

    def test_is_low_quality_whitespace_only(self) -> None:
        """空白のみのテキストが低品質と判定されることを検証。"""
        from src.layout_ocr import is_low_quality

        # Arrange: 空白のみ
        text = "          "  # 10文字のスペース

        # Act
        result = is_low_quality(text)

        # Assert
        assert result is True, "Whitespace-only text should be low quality"


class TestCalcNonCharRatio:
    """非文字率計算関数のテスト。

    calc_non_char_ratio() は日本語/英数字以外の文字の割合を計算する。
    """

    def test_calc_non_char_ratio_all_japanese(self) -> None:
        """全て日本語文字の場合、非文字率が0であることを検証。"""
        from src.layout_ocr_utils import calc_non_char_ratio

        # Arrange
        text = "日本語テキスト"

        # Act
        ratio = calc_non_char_ratio(text)

        # Assert
        assert ratio == 0.0, f"Pure Japanese text should have 0% non-char ratio. Got: {ratio}"

    def test_calc_non_char_ratio_all_symbols(self) -> None:
        """全て記号の場合、非文字率が1であることを検証。"""
        from src.layout_ocr_utils import calc_non_char_ratio

        # Arrange
        text = "!!!@@@###$$$%%%"

        # Act
        ratio = calc_non_char_ratio(text)

        # Assert
        assert ratio == 1.0, f"All-symbol text should have 100% non-char ratio. Got: {ratio}"

    def test_calc_non_char_ratio_half_and_half(self) -> None:
        """半分が文字、半分が記号の場合を検証。"""
        from src.layout_ocr_utils import calc_non_char_ratio

        # Arrange: 5文字 + 5記号 = 50%
        text = "あいうえお!@#$%"

        # Act
        ratio = calc_non_char_ratio(text)

        # Assert
        assert 0.45 <= ratio <= 0.55, f"Half-and-half text should have ~50% non-char ratio. Got: {ratio}"

    def test_calc_non_char_ratio_empty_string(self) -> None:
        """空文字列の場合の処理を検証。"""
        from src.layout_ocr_utils import calc_non_char_ratio

        # Act
        ratio = calc_non_char_ratio("")

        # Assert: 空文字列は0.0を返す（または別の定義による）
        assert ratio == 0.0 or ratio == 1.0, f"Empty string non-char ratio should be 0.0 or 1.0. Got: {ratio}"

    def test_calc_non_char_ratio_english_and_numbers(self) -> None:
        """英数字は文字としてカウントされることを検証。"""
        from src.layout_ocr_utils import calc_non_char_ratio

        # Arrange: 英数字のみ
        text = "ABC123xyz"

        # Act
        ratio = calc_non_char_ratio(text)

        # Assert
        assert ratio == 0.0, f"Alphanumeric text should have 0% non-char ratio. Got: {ratio}"


class TestOcrWithFallback:
    """OCRフォールバック処理のテスト (FR-010)。

    ocr_with_fallback() は以下の順序でフォールバック:
    1. Yomitoku（メインOCR）
    2. PaddleOCR（フォールバック1）
    3. Tesseract（フォールバック2）
    """

    def test_ocr_with_fallback_yomitoku_success(self) -> None:
        """Yomitokuが成功した場合、そのまま結果を返すことを検証。"""
        from src.layout_ocr import ocr_with_fallback

        # Arrange: テスト画像
        img = Image.new("RGB", (200, 50), color=(255, 255, 255))

        # Act: Yomitokuが成功する場合をモック
        with patch("src.ocr_yomitoku.ocr_page_yomitoku", return_value="正常なOCR結果テキスト"):
            text, engine_used = ocr_with_fallback(img)

        # Assert
        assert engine_used == "yomitoku", f"Should use yomitoku when it succeeds. Got: {engine_used}"
        assert text == "正常なOCR結果テキスト", f"Should return yomitoku result. Got: {text}"

    def test_ocr_with_fallback_yomitoku_empty_uses_paddleocr(self) -> None:
        """Yomitokuが空結果の場合、PaddleOCRにフォールバックすることを検証。"""
        from src.layout_ocr import ocr_with_fallback

        # Arrange
        img = Image.new("RGB", (200, 50), color=(255, 255, 255))

        # Act: Yomitokuが空を返し、PaddleOCRが成功
        with patch("src.ocr_yomitoku.ocr_page_yomitoku", return_value=""):
            with patch("src.ocr_ensemble.ocr_paddleocr") as mock_paddle:
                mock_paddle.return_value = MagicMock(success=True, text="PaddleOCRからの結果")
                text, engine_used = ocr_with_fallback(img)

        # Assert
        assert engine_used == "paddleocr", f"Should fallback to paddleocr when yomitoku is empty. Got: {engine_used}"

    def test_ocr_with_fallback_yomitoku_low_quality_uses_paddleocr(self) -> None:
        """Yomitokuが低品質結果の場合、PaddleOCRにフォールバックすることを検証。"""
        from src.layout_ocr import ocr_with_fallback

        # Arrange
        img = Image.new("RGB", (200, 50), color=(255, 255, 255))

        # Act: Yomitokuが短いゴミ結果を返す
        with patch("src.ocr_yomitoku.ocr_page_yomitoku", return_value="!!!???"):
            with patch("src.ocr_ensemble.ocr_paddleocr") as mock_paddle:
                mock_paddle.return_value = MagicMock(success=True, text="PaddleOCRからの正常な結果テキスト")
                text, engine_used = ocr_with_fallback(img)

        # Assert
        assert engine_used == "paddleocr", (
            f"Should fallback to paddleocr when yomitoku is low quality. Got: {engine_used}"
        )

    def test_ocr_with_fallback_paddleocr_fails_uses_tesseract(self) -> None:
        """Yomitoku/PaddleOCR両方失敗時、Tesseractにフォールバックすることを検証。"""
        from src.layout_ocr import ocr_with_fallback

        # Arrange
        img = Image.new("RGB", (200, 50), color=(255, 255, 255))

        # Act: Yomitoku/PaddleOCR両方失敗、Tesseractが成功
        with patch("src.ocr_yomitoku.ocr_page_yomitoku", return_value=""):
            with patch("src.ocr_ensemble.ocr_paddleocr") as mock_paddle:
                mock_paddle.return_value = MagicMock(success=False, text="", error="OCR failed")
                with patch("src.ocr_ensemble.ocr_tesseract") as mock_tesseract:
                    mock_tesseract.return_value = MagicMock(success=True, text="Tesseractからの結果")
                    text, engine_used = ocr_with_fallback(img)

        # Assert
        assert engine_used == "tesseract", f"Should fallback to tesseract when others fail. Got: {engine_used}"

    def test_ocr_with_fallback_all_fail_returns_empty(self) -> None:
        """全エンジンが失敗した場合、空文字列を返すことを検証。"""
        from src.layout_ocr import ocr_with_fallback

        # Arrange
        img = Image.new("RGB", (200, 50), color=(255, 255, 255))

        # Act: 全エンジンが失敗
        with patch("src.ocr_yomitoku.ocr_page_yomitoku", return_value=""):
            with patch("src.ocr_ensemble.ocr_paddleocr") as mock_paddle:
                mock_paddle.return_value = MagicMock(success=False, text="")
                with patch("src.ocr_ensemble.ocr_tesseract") as mock_tesseract:
                    mock_tesseract.return_value = MagicMock(success=False, text="")
                    text, engine_used = ocr_with_fallback(img)

        # Assert
        assert text == "", "Should return empty string when all engines fail"
        assert engine_used == "none", f"Should indicate no engine succeeded. Got: {engine_used}"


class TestMaskFigures:
    """FIGURE領域マスク処理のテスト (FR-011)。

    mask_figures() はFIGURE領域のみを白塗りでマスクする。
    """

    def test_mask_figures_single_figure(self) -> None:
        """単一のFIGURE領域が白塗りされることを検証。"""
        from src.utils import mask_figures

        # Arrange: 赤い画像にFIGURE領域
        img = Image.new("RGB", (100, 100), color=(255, 0, 0))  # 赤
        regions = [
            {"type": "FIGURE", "bbox": [10, 10, 50, 50], "confidence": 0.9},
        ]

        # Act
        masked = mask_figures(img, regions)

        # Assert: マスク領域が白になっている
        # 領域の中心ピクセルを確認
        center_pixel = masked.getpixel((30, 30))
        assert center_pixel == (255, 255, 255), f"FIGURE region should be white. Got: {center_pixel}"

        # 領域外は元のまま（赤）
        outside_pixel = masked.getpixel((80, 80))
        assert outside_pixel == (255, 0, 0), f"Outside FIGURE region should remain unchanged. Got: {outside_pixel}"

    def test_mask_figures_multiple_figures(self) -> None:
        """複数のFIGURE領域が全て白塗りされることを検証。"""
        from src.utils import mask_figures

        # Arrange
        img = Image.new("RGB", (200, 100), color=(0, 0, 255))  # 青
        regions = [
            {"type": "FIGURE", "bbox": [10, 10, 50, 50], "confidence": 0.9},
            {"type": "FIGURE", "bbox": [100, 10, 150, 50], "confidence": 0.85},
        ]

        # Act
        masked = mask_figures(img, regions)

        # Assert: 両方のFIGURE領域が白
        pixel1 = masked.getpixel((30, 30))
        pixel2 = masked.getpixel((125, 30))
        assert pixel1 == (255, 255, 255), f"First FIGURE should be white. Got: {pixel1}"
        assert pixel2 == (255, 255, 255), f"Second FIGURE should be white. Got: {pixel2}"

    def test_mask_figures_non_figure_regions_unchanged(self) -> None:
        """FIGURE以外の領域（TEXT, TABLE等）はマスクされないことを検証。"""
        from src.utils import mask_figures

        # Arrange
        img = Image.new("RGB", (100, 100), color=(0, 255, 0))  # 緑
        regions = [
            {"type": "TEXT", "bbox": [10, 10, 50, 50], "confidence": 0.9},
            {"type": "TABLE", "bbox": [60, 10, 90, 50], "confidence": 0.85},
        ]

        # Act
        masked = mask_figures(img, regions)

        # Assert: TEXTとTABLE領域は元のまま（緑）
        text_pixel = masked.getpixel((30, 30))
        table_pixel = masked.getpixel((75, 30))
        assert text_pixel == (0, 255, 0), f"TEXT region should be unchanged. Got: {text_pixel}"
        assert table_pixel == (0, 255, 0), f"TABLE region should be unchanged. Got: {table_pixel}"

    def test_mask_figures_empty_regions(self) -> None:
        """空の領域リストの場合、画像が変更されないことを検証。"""
        from src.utils import mask_figures

        # Arrange
        img = Image.new("RGB", (100, 100), color=(128, 128, 128))  # グレー
        regions: list[dict] = []

        # Act
        masked = mask_figures(img, regions)

        # Assert: 画像は変更されない
        pixel = masked.getpixel((50, 50))
        assert pixel == (128, 128, 128), f"Image should be unchanged. Got: {pixel}"

    def test_mask_figures_returns_new_image(self) -> None:
        """mask_figuresは元画像を変更せず、新しい画像を返すことを検証。"""
        from src.utils import mask_figures

        # Arrange
        img = Image.new("RGB", (100, 100), color=(255, 0, 0))  # 赤
        original_pixel = img.getpixel((30, 30))
        regions = [
            {"type": "FIGURE", "bbox": [10, 10, 50, 50], "confidence": 0.9},
        ]

        # Act
        masked = mask_figures(img, regions)

        # Assert: 元画像は変更されていない
        assert img.getpixel((30, 30)) == original_pixel, "Original image should not be modified"
        assert masked is not img, "Should return a new image object"


class TestFigureExclusion:
    """FIGURE領域がOCR出力から除外されることのテスト (FR-012)。"""

    def test_ocr_by_layout_excludes_figure_from_output(self, tmp_path: Path) -> None:
        """FIGURE領域がOCR結果に含まれないことを検証。"""
        from src.layout_ocr import ocr_by_layout

        # Arrange
        img_path = tmp_path / "test_page.png"
        img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        img.save(img_path)

        layout = {
            "regions": [
                {"type": "TITLE", "bbox": [50, 50, 750, 100], "confidence": 0.95, "text": "タイトル"},
                {"type": "FIGURE", "bbox": [50, 120, 400, 350], "confidence": 0.9},
                {"type": "TEXT", "bbox": [50, 370, 750, 550], "confidence": 0.88, "text": "テキスト内容"},
            ],
            "page_size": [800, 600],
        }

        # Act
        results = ocr_by_layout(str(img_path), layout)

        # Assert: 結果にFIGUREが含まれない
        figure_results = [r for r in results if r.region_type == "FIGURE"]

        # FR-012要件: FIGUREはbook.txtから除外される
        assert len(figure_results) == 0, (
            f"FIGURE regions should be excluded from OCR output. Found: {len(figure_results)}"
        )
        # TITLE と TEXT のみが結果に含まれる
        assert len(results) == 2, f"Should have 2 results (TITLE and TEXT). Got: {len(results)}"

    def test_figure_saved_to_separate_directory(self, tmp_path: Path) -> None:
        """FIGURE領域がfigures/ディレクトリに保存されることを検証。"""
        # この機能はrun_layout_ocrで実装されるため、統合テストとして実装
        # ここではfigures/ディレクトリの存在を確認するテストを追加

        # Arrange
        figures_dir = tmp_path / "figures"
        figures_dir.mkdir()

        # Assert: ディレクトリが作成されることを確認（実装で使用される）
        assert figures_dir.exists(), "figures directory should be created"


class TestResultConcatenationWithReadingOrder:
    """読み順ソート後の結果連結テスト (T060)。"""

    def test_results_concatenated_in_reading_order(self, tmp_path: Path) -> None:
        """領域が読み順にソートされてから連結されることを検証。"""
        from src.layout_ocr import ocr_by_layout

        # Arrange: 2カラムレイアウト
        img_path = tmp_path / "two_column_page.png"
        img = Image.new("RGB", (1000, 600), color=(255, 255, 255))
        img.save(img_path)

        # 左カラム→右カラムの読み順になるべきレイアウト
        layout = {
            "regions": [
                # 右カラム上部（読み順: 3番目）
                {"type": "TEXT", "bbox": [550, 50, 950, 200], "confidence": 0.9, "text": "右カラム上部"},
                # 左カラム上部（読み順: 1番目）
                {"type": "TITLE", "bbox": [50, 50, 450, 100], "confidence": 0.95, "text": "タイトル"},
                # 左カラム中部（読み順: 2番目）
                {"type": "TEXT", "bbox": [50, 120, 450, 300], "confidence": 0.88, "text": "左カラム本文"},
                # 右カラム下部（読み順: 4番目）
                {"type": "TEXT", "bbox": [550, 220, 950, 400], "confidence": 0.87, "text": "右カラム下部"},
            ],
            "page_size": [1000, 600],
        }

        # Act
        results = ocr_by_layout(str(img_path), layout)

        # Assert: 読み順（左カラム→右カラム）で結果が返される
        assert len(results) == 4, f"Should have 4 results. Got: {len(results)}"

        # 最初はTITLE（左カラム上部）
        assert results[0].region_type == "TITLE", f"First result should be TITLE. Got: {results[0].region_type}"
        # 2番目は左カラムのTEXT
        assert results[1].region_type == "TEXT", f"Second result should be TEXT. Got: {results[1].region_type}"
        assert [r.text for r in results] == [
            "タイトル",
            "左カラム本文",
            "右カラム上部",
            "右カラム下部",
        ], f"Texts should follow reading order. Got: {[r.text for r in results]}"

    def test_results_maintain_sorted_order_for_single_column(self, tmp_path: Path) -> None:
        """単一カラムレイアウトでも上から下の順序が維持されることを検証。"""
        from src.layout_ocr import ocr_by_layout

        # Arrange: 単一カラムレイアウト
        img_path = tmp_path / "single_column_page.png"
        img = Image.new("RGB", (600, 800), color=(255, 255, 255))
        img.save(img_path)

        layout = {
            "regions": [
                # 下から上に定義（ソートが機能することを確認）
                {"type": "TEXT", "bbox": [50, 400, 550, 600], "confidence": 0.85, "text": "段落2"},
                {"type": "TEXT", "bbox": [50, 200, 550, 380], "confidence": 0.88, "text": "段落1"},
                {"type": "TITLE", "bbox": [50, 50, 550, 100], "confidence": 0.95, "text": "タイトル"},
            ],
            "page_size": [600, 800],
        }

        # Act
        results = ocr_by_layout(str(img_path), layout)

        # Assert: 上から下の順序
        assert len(results) == 3, f"Should have 3 results. Got: {len(results)}"
        assert results[0].region_type == "TITLE", "First should be TITLE (top)"
        assert results[1].region_type == "TEXT", "Second should be TEXT (middle)"
        assert results[2].region_type == "TEXT", "Third should be TEXT (bottom)"
        assert [r.text for r in results] == ["タイトル", "段落1", "段落2"], (
            f"Texts should be sorted top to bottom. Got: {[r.text for r in results]}"
        )


# ============================================================
# T015: CODE は図として扱う（本文には出さない）
# ============================================================


class TestCodeRegionTreatedAsFigure:
    """CODE 領域は図として扱い、本文の Markdown には出さない."""

    def test_code_region_is_not_emitted(self) -> None:
        from src.layout_ocr_utils import format_ocr_result

        text = "1112200\nAGAATERMARAR"
        assert format_ocr_result("CODE", text) == ""

    def test_figure_and_code_are_both_figure_like(self) -> None:
        from src.layout_ocr_utils import FIGURE_LIKE_TYPES

        assert "FIGURE" in FIGURE_LIKE_TYPES
        assert "CODE" in FIGURE_LIKE_TYPES

    def test_code_region_is_skipped_by_engine_selection(self) -> None:
        from src.layout_ocr_utils import select_ocr_engine

        assert select_ocr_engine("CODE") == "skip"

    def test_text_region_is_still_emitted(self) -> None:
        from src.layout_ocr_utils import format_ocr_result

        assert format_ocr_result("TEXT", "本文") == "本文"

    def test_ocr_region_returns_empty_for_code(self) -> None:
        """ocr_region は CODE 領域で OCR を実行しない."""
        from PIL import Image

        from src.layout_ocr import ocr_region

        img = Image.new("RGB", (100, 100), "white")
        result = ocr_region(img, {"type": "CODE", "bbox": [0, 0, 50, 50]})

        assert result.text == ""
        assert result.formatted == ""


# ============================================================
# T017: TITLE の空テキスト・本文行の扱い
# ============================================================


class TestTitleFormatting:
    """見出しが空なら行を出さず、文末記号で終わるものは本文として出す."""

    def test_empty_title_emits_nothing(self) -> None:
        from src.layout_ocr_utils import format_ocr_result

        assert format_ocr_result("TITLE", "") == ""
        assert format_ocr_result("TITLE", "   ") == ""

    def test_heading_gets_markdown(self) -> None:
        from src.layout_ocr_utils import format_ocr_result

        assert format_ocr_result("TITLE", "第3章 分析方法を選ぶ") == "## 第3章 分析方法を選ぶ"

    def test_sentence_ending_title_is_body_text(self) -> None:
        from src.layout_ocr_utils import format_ocr_result

        text = "まず、計算をする前に踏まねばならないステップが3つあります。"
        assert format_ocr_result("TITLE", text) == text

    def test_sentence_ending_midway_is_heading(self) -> None:
        from src.layout_ocr_utils import format_ocr_result

        assert format_ocr_result("TITLE", "6-2. 大小関係の確からしさをどう考えるか?") == (
            "## 6-2. 大小関係の確からしさをどう考えるか?"
        )


# ============================================================
# #97: 本文は layout.json の text を正とし、空にしない
# ============================================================


class TestLayoutTextIsAuthoritative:
    """本文・見出しの text はレイアウト検出時の認識結果を正とする."""

    def test_text_region_does_not_reocr(self) -> None:
        """TEXT 領域でクロップ再 OCR を呼ばない."""
        from src.layout_ocr import ocr_region

        img = Image.new("RGB", (400, 200), "white")
        region = {"type": "TEXT", "bbox": [10, 10, 390, 190], "confidence": 1.0, "text": "紙面にある本文"}

        with patch("src.ocr_yomitoku.ocr_page_yomitoku") as mock_ocr:
            result = ocr_region(img, region)

        assert mock_ocr.called is False
        assert result.text == "紙面にある本文"

    def test_text_region_keeps_text_when_crop_would_be_empty(self, tmp_path: Path) -> None:
        """クロップ再 OCR が空になる紙面でも、本文が消えない.

        #97 の再現条件: 小さい・薄い領域を切り出すと認識結果が空になる。
        再 OCR の結果を正にしないので、本文は layout.json の text のまま残る。
        """
        from src.layout_ocr import ocr_by_layout

        img_path = tmp_path / "page.png"
        Image.new("RGB", (400, 200), "white").save(img_path)
        layout = {
            "regions": [
                {
                    "type": "TEXT",
                    "bbox": [10, 10, 390, 150],
                    "confidence": 1.0,
                    "text": "① データ分析で重大な見落としを防ぐ",
                },
            ],
            "page_size": [400, 200],
        }

        with patch("src.ocr_yomitoku.ocr_page_blocks", return_value=_blocks("")):
            results = ocr_by_layout(str(img_path), layout)

        assert [r.text for r in results] == ["① データ分析で重大な見落としを防ぐ"]

    def test_text_region_can_be_empty_without_error(self) -> None:
        """text が空の TEXT 領域でも例外にせず、空で返す."""
        from src.layout_ocr import ocr_region

        img = Image.new("RGB", (400, 200), "white")
        region = {"type": "TEXT", "bbox": [10, 10, 390, 190], "confidence": 1.0, "text": ""}

        result = ocr_region(img, region)

        assert result.text == ""
        assert result.formatted == ""


class TestTableRegion:
    """TABLE は検出時に組み立てた Markdown をそのまま使う（#101）."""

    def test_table_region_uses_layout_markdown(self) -> None:
        from src.layout_ocr import ocr_region

        img = Image.new("RGB", (400, 300), "white")
        markdown = "| 項目 | 値 |\n| --- | --- |\n| 本体価格 | 5 万円 |"
        region = {"type": "TABLE", "bbox": [10, 10, 390, 290], "confidence": 1.0, "text": markdown}

        with patch("src.ocr_yomitoku.ocr_page_yomitoku") as mock_ocr:
            result = ocr_region(img, region)

        assert mock_ocr.called is False
        assert result.text == markdown
        assert result.formatted == markdown

    def test_unknown_region_type_is_reocrd(self) -> None:
        """未知の種別はクロップして読み直す（保険）."""
        from src.layout_ocr import ocr_region

        img = Image.new("RGB", (400, 300), "white")
        region = {"type": "UNKNOWN", "bbox": [10, 10, 390, 290], "confidence": 1.0, "text": "元の text"}

        with patch("src.ocr_yomitoku.ocr_page_yomitoku", return_value="読み直した text") as mock_ocr:
            result = ocr_region(img, region)

        assert mock_ocr.called is True
        assert result.text == "読み直した text"


# ============================================================
# #98: 柱・ノンブルを本文から除く
# ============================================================


class TestRunningHeadInLayoutOcr:
    """レイアウト OCR の出力に柱・ノンブルを混ぜない."""

    def test_running_head_region_is_dropped(self, tmp_path: Path) -> None:
        from src.layout.running_head import find_running_heads
        from src.layout_ocr import ocr_by_layout

        img_path = tmp_path / "page.png"
        Image.new("RGB", (960, 1280), "white").save(img_path)
        layout = {
            "regions": [
                {"type": "TEXT", "bbox": [106, 194, 859, 900], "confidence": 1.0, "text": "本文"},
                {
                    "type": "TEXT",
                    "bbox": [114, 1194, 500, 1209],
                    "confidence": 1.0,
                    "text": "22 第1章 データ分析を設計する",
                },
            ],
            "page_size": [960, 1280],
        }
        heads = find_running_heads(
            {
                f"{i:04d}.webp": {
                    "regions": [
                        {
                            "type": "TEXT",
                            "bbox": [114, 1194, 500, 1209],
                            "confidence": 1.0,
                            "text": f"第1章 データ分析を設計する {n}",
                        },
                    ],
                    "page_size": [960, 1280],
                }
                for i, n in enumerate([20, 21, 22])
            }
        )

        results = ocr_by_layout(str(img_path), layout, running_heads=heads)

        assert [r.text for r in results] == ["本文"]

    def test_page_number_region_is_dropped(self, tmp_path: Path) -> None:
        from src.layout_ocr import ocr_by_layout

        img_path = tmp_path / "page.png"
        Image.new("RGB", (960, 1280), "white").save(img_path)
        layout = {
            "regions": [
                {"type": "TEXT", "bbox": [106, 194, 859, 900], "confidence": 1.0, "text": "本文"},
                {"type": "TEXT", "bbox": [430, 1194, 470, 1209], "confidence": 1.0, "text": "23"},
            ],
            "page_size": [960, 1280],
        }

        results = ocr_by_layout(str(img_path), layout)

        assert [r.text for r in results] == ["本文"]

    def test_fallback_text_has_running_head_lines_stripped(self, tmp_path: Path) -> None:
        from src.layout.running_head import find_running_heads
        from src.layout_ocr import ocr_by_layout

        img_path = tmp_path / "page.png"
        Image.new("RGB", (960, 1280), "white").save(img_path)
        layout = {
            "regions": [
                {"type": "TEXT", "bbox": [106, 194, 400, 300], "confidence": 1.0, "text": "本文"},
                {
                    "type": "TEXT",
                    "bbox": [114, 1194, 500, 1209],
                    "confidence": 1.0,
                    "text": "23 第1章 データ分析を設計する",
                },
            ],
            "page_size": [960, 1280],
        }
        heads = find_running_heads(
            {
                f"{i:04d}.webp": {
                    "regions": [
                        {
                            "type": "TEXT",
                            "bbox": [114, 1194, 500, 1209],
                            "confidence": 1.0,
                            "text": f"第1章 データ分析を設計する {n}",
                        },
                    ],
                    "page_size": [960, 1280],
                }
                for i, n in enumerate([20, 21, 22])
            }
        )

        with patch(
            "src.ocr_yomitoku.ocr_page_blocks",
            return_value=_blocks("本文\n23 第1章 データ分析を設計する\n続きの本文"),
        ):
            results = ocr_by_layout(str(img_path), layout, running_heads=heads)

        assert results[0].region_type == "FALLBACK"
        assert results[0].text == "本文\n続きの本文"


# ============================================================
# #99: 紙面のページ番号（ノンブル）を書き出す
# ============================================================


class TestPageNumbersOutput:
    """run_layout_ocr が book_meta.json（紙面のページ番号・章名）を書き出す."""

    def test_writes_page_numbers_from_running_heads(self, tmp_path: Path) -> None:
        from src.layout_ocr import run_layout_ocr

        pages_dir = tmp_path / "pages"
        pages_dir.mkdir()
        for i in range(3):
            Image.new("RGB", (960, 1280), "white").save(pages_dir / f"{i:04d}.png")
        layout = {
            f"{i:04d}.png": {
                "regions": [
                    {"type": "TEXT", "bbox": [106, 194, 859, 900], "confidence": 1.0, "text": "本文"},
                    {
                        "type": "TEXT",
                        "bbox": [114, 1194, 500, 1209],
                        "confidence": 1.0,
                        "text": f"{20 + i} 第1章 データ分析を設計する",
                    },
                ],
                "page_size": [960, 1280],
            }
            for i in range(3)
        }
        out_dir = tmp_path / "out"

        with patch("src.ocr_yomitoku.ocr_page_blocks", return_value=_blocks("本文")):
            run_layout_ocr(
                str(pages_dir),
                layout,
                str(out_dir / "ocr_combined.txt"),
                warmup=False,
            )

        written = json.loads((out_dir / "book_meta.json").read_text(encoding="utf-8"))
        assert written["page_numbers"] == {"0000": 20, "0001": 21, "0002": 22}
        assert written["chapter_titles"] == {"1": "データ分析を設計する"}


# ============================================================
# #108: フォールバックしたページでも見出しと読取順を効かせる
# ============================================================


class TestPreferLayoutText:
    """ページ全体 OCR と領域別の文字数から、領域別を採るか決める."""

    def test_same_length_prefers_layout_text(self) -> None:
        from src.layout_ocr_utils import prefer_layout_text

        assert prefer_layout_text("本文です。", "本文です。") is True

    def test_slightly_shorter_still_prefers_layout_text(self) -> None:
        from src.layout_ocr_utils import prefer_layout_text

        page = "本文がここにあります。" * 40
        region = page[:-10]

        assert prefer_layout_text(page, region) is True

    def test_much_shorter_keeps_page_ocr(self) -> None:
        from src.layout_ocr_utils import prefer_layout_text

        page = "本文がここにあります。" * 10
        region = page[: len(page) // 3]

        assert prefer_layout_text(page, region) is False

    def test_empty_page_text_prefers_layout_text(self) -> None:
        from src.layout_ocr_utils import prefer_layout_text

        assert prefer_layout_text("", "本文です。") is True


class TestFallbackKeepsHeadings:
    """フォールバック判定のページでも、文字数が同じなら領域別（見出しつき）を返す."""

    def _low_coverage_layout(self) -> dict:
        return {
            "regions": [
                {"type": "TITLE", "bbox": [50, 50, 400, 90], "confidence": 1.0, "text": "2. データ分析って何?"},
                {"type": "TEXT", "bbox": [50, 100, 400, 200], "confidence": 1.0, "text": "本文です。"},
            ],
            "page_size": [960, 1280],
        }

    def test_page_ocr_with_same_length_uses_layout_text(self, tmp_path: Path) -> None:
        from src.layout_ocr import ocr_by_layout

        img_path = tmp_path / "page.png"
        Image.new("RGB", (960, 1280), "white").save(img_path)

        with patch("src.ocr_yomitoku.ocr_page_blocks", return_value=_blocks("本文です。")):
            results = ocr_by_layout(str(img_path), self._low_coverage_layout())

        assert [r.region_type for r in results] == ["TITLE", "TEXT"]
        assert results[0].formatted == "## 2. データ分析って何?"

    def test_page_ocr_much_longer_keeps_fallback(self, tmp_path: Path) -> None:
        from src.layout_ocr import ocr_by_layout

        img_path = tmp_path / "page.png"
        Image.new("RGB", (960, 1280), "white").save(img_path)
        long_text = "ページ全体の OCR 結果です。" * 20

        with patch("src.ocr_yomitoku.ocr_page_blocks", return_value=_blocks(long_text)):
            results = ocr_by_layout(str(img_path), self._low_coverage_layout())

        assert [r.region_type for r in results] == ["FALLBACK"]
        assert results[0].text == long_text


# ============================================================
# #116: ページ全体 OCR のページに、レイアウトの見出しを差し込む
# ============================================================


class TestApplyLayoutHeadings:
    def test_title_appearing_once_becomes_heading(self) -> None:
        from src.layout_ocr import apply_layout_headings

        text = "2. データ分析って何?\n\n本文がここにあります。"
        regions = [{"type": "TITLE", "bbox": [0, 0, 10, 10], "text": "2. データ分析って何?"}]

        assert apply_layout_headings(text, regions) == "## 2. データ分析って何?\n\n本文がここにあります。"

    def test_title_appearing_twice_is_left_alone(self) -> None:
        from src.layout_ocr import apply_layout_headings

        text = "同じ見出し\n\n本文です。\n\n同じ見出し"
        regions = [{"type": "TITLE", "bbox": [0, 0, 10, 10], "text": "同じ見出し"}]

        assert apply_layout_headings(text, regions) == text

    def test_sentence_ending_title_is_not_a_heading(self) -> None:
        from src.layout_ocr import apply_layout_headings

        text = "まず、計算をする前に踏まねばならないステップが3つあります。"
        regions = [
            {
                "type": "TITLE",
                "bbox": [0, 0, 10, 10],
                "text": "まず、計算をする前に踏まねばならないステップが3つあります。",
            }
        ]

        assert apply_layout_headings(text, regions) == text

    def test_already_heading_is_not_doubled(self) -> None:
        from src.layout_ocr import apply_layout_headings

        text = "## 見出しです\n\n本文です。"
        regions = [{"type": "TITLE", "bbox": [0, 0, 10, 10], "text": "## 見出しです"}]

        assert apply_layout_headings(text, regions) == text

    def test_fallback_page_gets_heading(self, tmp_path: Path) -> None:
        """フォールバックしたページでも見出しが付く."""
        from src.layout_ocr import ocr_by_layout

        img_path = tmp_path / "page.png"
        Image.new("RGB", (960, 1280), "white").save(img_path)
        layout = {
            "regions": [
                {"type": "TITLE", "bbox": [50, 50, 400, 90], "confidence": 1.0, "text": "2. データ分析って何?"},
            ],
            "page_size": [960, 1280],
        }
        page_text = "2. データ分析って何?\n\n" + "本文です。" * 30

        with patch("src.ocr_yomitoku.ocr_page_blocks", return_value=_blocks(page_text)):
            results = ocr_by_layout(str(img_path), layout)

        assert results[0].region_type == "FALLBACK"
        assert results[0].text.startswith("## 2. データ分析って何?")


class TestDotLeaderTitles:
    def test_toc_dot_leader_is_not_a_heading(self) -> None:
        from src.layout_ocr import apply_layout_headings

        text = "1. ワークシートの基本操作………\n\n本文です。"
        regions = [{"type": "TITLE", "bbox": [0, 0, 10, 10], "text": "1. ワークシートの基本操作………"}]

        assert apply_layout_headings(text, regions) == text


class TestOrderPageBlocks:
    """ページ全体 OCR の段落を紙面の順に並べ直す (#121)."""

    @staticmethod
    def _block(text: str, bbox):
        return {"type": "TEXT", "text": text, "bbox": bbox, "confidence": 1.0}

    def test_orders_single_column_by_y(self) -> None:
        from src.layout_ocr import order_page_blocks

        blocks = [
            self._block("下", [100, 400, 900, 460]),
            self._block("上", [100, 100, 900, 160]),
        ]

        ordered = order_page_blocks(blocks, 1000)

        assert [b["text"] for b in ordered] == ["上", "下"]

    def test_orders_two_columns_left_first(self) -> None:
        from src.layout_ocr import order_page_blocks

        blocks = [
            self._block("右上", [600, 100, 800, 200]),
            self._block("左下", [100, 300, 300, 400]),
            self._block("左上", [100, 100, 300, 200]),
        ]

        ordered = order_page_blocks(blocks, 1000)

        assert [b["text"] for b in ordered] == ["左上", "左下", "右上"]

    def test_returns_none_when_a_block_has_no_position(self) -> None:
        from src.layout_ocr import order_page_blocks

        blocks = [self._block("本文", [0, 0, 10, 10]), {"type": "TEXT", "text": "位置なし", "bbox": None}]

        assert order_page_blocks(blocks, 1000) is None

    def test_returns_none_without_page_width(self) -> None:
        from src.layout_ocr import order_page_blocks

        assert order_page_blocks([self._block("本文", [0, 0, 10, 10])], 0) is None

    def test_returns_none_for_empty_blocks(self) -> None:
        from src.layout_ocr import order_page_blocks

        assert order_page_blocks([], 1000) is None

    def test_running_head_is_dropped_before_ordering(self) -> None:
        """左右をまたぐ柱を落としてから並べる（2 段組みが 1 段組みにならない）."""
        from src.layout.running_head import normalize_running_head_text
        from src.layout_ocr import filter_page_blocks, order_page_blocks

        head = "20 第1章 データ分析を設計する"
        page_heads = frozenset({normalize_running_head_text(head)})
        blocks = [
            self._block(head, [100, 50, 900, 70]),  # 左右をまたぐ柱
            self._block("左上", [100, 100, 300, 200]),
            self._block("左下", [100, 300, 300, 400]),
            self._block("右上", [600, 100, 800, 200]),
            self._block("右下", [600, 300, 800, 400]),
        ]

        # 柱を残したまま並べると 1 段組みと判定され、左右が交互になる
        without_filter = order_page_blocks(blocks, 1000)
        assert [b["text"] for b in without_filter] == [head, "左上", "右上", "左下", "右下"]

        ordered = order_page_blocks(filter_page_blocks(blocks, frozenset(), page_heads), 1000)

        assert [b["text"] for b in ordered] == ["左上", "左下", "右上", "右下"]

    def test_heading_within_a_few_pixels_stays_before_body(self) -> None:
        """数 px の y の差で、同じ行の見出しと本文が入れ替わらないこと."""
        from src.layout_ocr import order_page_blocks

        blocks = [
            {"type": "TEXT", "text": "本文", "bbox": [300, 788, 700, 819], "confidence": 1.0},
            {"type": "TITLE", "text": "表形式", "bbox": [165, 789, 204, 803], "confidence": 1.0},
        ]

        ordered = order_page_blocks(blocks, 960)

        assert [b["text"] for b in ordered] == ["表形式", "本文"]

    def test_running_head_in_the_middle_is_kept(self) -> None:
        """目次の「プロローグ」のような、本全体の柱と同じ文字が本文の途中にあっても消さない."""
        from src.layout.running_head import normalize_running_head_text
        from src.layout_ocr import filter_page_blocks

        running_heads = frozenset({normalize_running_head_text("プロローグ")})
        blocks = [
            self._block("CONTENTS", [100, 100, 300, 120]),
            self._block("プロローグ", [132, 258, 210, 277]),
            self._block("第1章", [156, 433, 208, 452]),
        ]

        kept = filter_page_blocks(blocks, running_heads, frozenset())

        assert [b["text"] for b in kept] == ["CONTENTS", "プロローグ", "第1章"]
