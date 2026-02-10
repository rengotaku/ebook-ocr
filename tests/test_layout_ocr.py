"""Tests for src.layout_ocr region-based OCR processing.

Phase 4 RED tests for US2 - Region-based OCR Processing.
These tests will FAIL until src/layout_ocr.py is implemented.

OCR Engine Selection Rules (from research.md):
| Region Type | OCR Engine | Output Format |
|-------------|------------|---------------|
| TITLE | DeepSeek-OCR | `## {text}` |
| TEXT | DeepSeek-OCR | `{text}` |
| TABLE | DeepSeek-OCR | Markdown table |
| FIGURE | VLM (gemma3:12b) | `[FIGURE: {description}]` |
| CAPTION | DeepSeek-OCR | `*{text}*` |
| FOOTNOTE | DeepSeek-OCR | `^{text}^` |
| FORMULA | Skip or OCR | `$${text}$$` |
| ABANDON | Skip | None |
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image


class TestSelectOcrEngine:
    """OCRエンジン選択ロジックのテスト。"""

    def test_select_ocr_engine_text_returns_deepseek(self) -> None:
        """TEXT領域に対してDeepSeek-OCRが選択されることを検証。"""
        from src.layout_ocr import select_ocr_engine

        # Act
        engine = select_ocr_engine("TEXT")

        # Assert
        assert engine == "deepseek-ocr", (
            f"TEXT region should use deepseek-ocr engine. Got: {engine}"
        )

    def test_select_ocr_engine_title_returns_deepseek(self) -> None:
        """TITLE領域に対してDeepSeek-OCRが選択されることを検証。"""
        from src.layout_ocr import select_ocr_engine

        # Act
        engine = select_ocr_engine("TITLE")

        # Assert
        assert engine == "deepseek-ocr", (
            f"TITLE region should use deepseek-ocr engine. Got: {engine}"
        )

    def test_select_ocr_engine_figure_returns_vlm(self) -> None:
        """FIGURE領域に対してVLMが選択されることを検証。"""
        from src.layout_ocr import select_ocr_engine

        # Act
        engine = select_ocr_engine("FIGURE")

        # Assert
        assert engine == "vlm", (
            f"FIGURE region should use vlm engine. Got: {engine}"
        )

    def test_select_ocr_engine_table_returns_deepseek(self) -> None:
        """TABLE領域に対してDeepSeek-OCRが選択されることを検証。"""
        from src.layout_ocr import select_ocr_engine

        # Act
        engine = select_ocr_engine("TABLE")

        # Assert
        assert engine == "deepseek-ocr", (
            f"TABLE region should use deepseek-ocr engine. Got: {engine}"
        )

    def test_select_ocr_engine_caption_returns_deepseek(self) -> None:
        """CAPTION領域に対してDeepSeek-OCRが選択されることを検証。"""
        from src.layout_ocr import select_ocr_engine

        # Act
        engine = select_ocr_engine("CAPTION")

        # Assert
        assert engine == "deepseek-ocr", (
            f"CAPTION region should use deepseek-ocr engine. Got: {engine}"
        )

    def test_select_ocr_engine_footnote_returns_deepseek(self) -> None:
        """FOOTNOTE領域に対してDeepSeek-OCRが選択されることを検証。"""
        from src.layout_ocr import select_ocr_engine

        # Act
        engine = select_ocr_engine("FOOTNOTE")

        # Assert
        assert engine == "deepseek-ocr", (
            f"FOOTNOTE region should use deepseek-ocr engine. Got: {engine}"
        )

    def test_select_ocr_engine_formula_returns_deepseek(self) -> None:
        """FORMULA領域に対してDeepSeek-OCRが選択されることを検証。"""
        from src.layout_ocr import select_ocr_engine

        # Act
        engine = select_ocr_engine("FORMULA")

        # Assert
        assert engine == "deepseek-ocr", (
            f"FORMULA region should use deepseek-ocr engine. Got: {engine}"
        )

    def test_select_ocr_engine_abandon_returns_skip(self) -> None:
        """ABANDON領域に対してスキップが選択されることを検証。"""
        from src.layout_ocr import select_ocr_engine

        # Act
        engine = select_ocr_engine("ABANDON")

        # Assert
        assert engine == "skip", (
            f"ABANDON region should be skipped. Got: {engine}"
        )


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
        assert formatted == "## 第1章 はじめに", (
            f"TITLE should be formatted as '## {{text}}'. Got: {formatted}"
        )

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
        assert formatted == "これは本文テキストです。", (
            f"TEXT should remain unchanged. Got: {formatted}"
        )

    def test_format_ocr_result_figure_adds_marker(self) -> None:
        """FIGURE領域のVLM説明が[FIGURE: ...]で出力されることを検証。

        期待フォーマット: `[FIGURE: {description}]`
        """
        from src.layout_ocr import format_ocr_result

        # Arrange
        description = "棒グラフで売上推移を示している"

        # Act
        formatted = format_ocr_result("FIGURE", description)

        # Assert
        assert formatted == "[FIGURE: 棒グラフで売上推移を示している]", (
            f"FIGURE should be formatted as '[FIGURE: {{description}}]'. Got: {formatted}"
        )

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
        assert formatted == "*図1: システム構成図*", (
            f"CAPTION should be formatted as '*{{text}}*'. Got: {formatted}"
        )

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
        assert formatted == "$$E = mc^2$$", (
            f"FORMULA should be formatted as '$${{text}}$$'. Got: {formatted}"
        )

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
        assert formatted == "", (
            f"ABANDON should return empty string. Got: {formatted}"
        )


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
        assert cropped.size == (40, 40), (
            f"Cropped size should be (40, 40) for bbox [10,20,50,60]. Got: {cropped.size}"
        )

    def test_crop_region_full_image(self) -> None:
        """bbox=[0, 0, w, h]で全画像がクロップされることを検証。"""
        from src.layout_ocr import crop_region

        # Arrange
        img = Image.new("RGB", (200, 150), color=(0, 255, 0))
        bbox = [0, 0, 200, 150]

        # Act
        cropped = crop_region(img, bbox)

        # Assert
        assert cropped.size == (200, 150), (
            f"Full image crop should match original size. Got: {cropped.size}"
        )

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
    """TEXT領域のOCRテスト（DeepSeek-OCR使用）。"""

    def test_text_region_uses_deepseek_ocr(self, tmp_path: Path) -> None:
        """TEXT領域がDeepSeek-OCRで処理されることを検証。"""
        from src.layout_ocr import ocr_region

        # Arrange
        img_path = tmp_path / "test_page.png"
        img = Image.new("RGB", (500, 200), color=(255, 255, 255))
        img.save(img_path)

        region = {
            "type": "TEXT",
            "bbox": [10, 10, 490, 190],
            "confidence": 0.9,
        }

        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "テキスト内容"}}
        mock_response.raise_for_status = MagicMock()

        # Act & Assert
        with patch("src.layout_ocr.requests.post", return_value=mock_response) as mock_post:
            result = ocr_region(img, region)

            # DeepSeek-OCRが呼ばれたことを確認
            call_args = mock_post.call_args
            assert call_args is not None, "requests.post should be called"
            payload = call_args.kwargs.get("json") or call_args[1].get("json")
            assert payload["model"] == "deepseek-ocr", (
                f"TEXT region should use deepseek-ocr model. Got: {payload['model']}"
            )

    def test_text_region_ocr_result_format(self, tmp_path: Path) -> None:
        """TEXT領域のOCR結果がフォーマットされることを検証。"""
        from src.layout_ocr import ocr_region

        # Arrange
        img = Image.new("RGB", (500, 200), color=(255, 255, 255))
        region = {
            "type": "TEXT",
            "bbox": [10, 10, 490, 190],
            "confidence": 0.9,
        }

        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "これは本文です。"}}
        mock_response.raise_for_status = MagicMock()

        # Act
        with patch("src.layout_ocr.requests.post", return_value=mock_response):
            result = ocr_region(img, region)

        # Assert: TEXTはそのまま出力
        assert result.text == "これは本文です。", (
            f"OCR text should be extracted. Got: {result.text}"
        )
        assert result.formatted == "これは本文です。", (
            f"TEXT should remain unchanged. Got: {result.formatted}"
        )


class TestFigureRegionOcr:
    """FIGURE領域のOCRテスト（VLM使用）。"""

    def test_figure_region_uses_vlm(self, tmp_path: Path) -> None:
        """FIGURE領域がVLMで処理されることを検証（モック使用）。"""
        from src.layout_ocr import ocr_region

        # Arrange
        img = Image.new("RGB", (400, 300), color=(200, 200, 200))
        region = {
            "type": "FIGURE",
            "bbox": [10, 10, 390, 290],
            "confidence": 0.95,
        }

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "message": {"content": "棒グラフで売上推移を示している図"}
        }
        mock_response.raise_for_status = MagicMock()

        # Act & Assert
        with patch("src.layout_ocr.requests.post", return_value=mock_response) as mock_post:
            result = ocr_region(img, region)

            # VLMが呼ばれたことを確認
            call_args = mock_post.call_args
            assert call_args is not None, "requests.post should be called for VLM"
            payload = call_args.kwargs.get("json") or call_args[1].get("json")
            # VLMモデル（gemma3:12bなど）が使われることを確認
            assert payload["model"] != "deepseek-ocr", (
                f"FIGURE region should NOT use deepseek-ocr. Got: {payload['model']}"
            )

    def test_figure_region_ocr_result_format(self) -> None:
        """FIGURE領域のVLM結果が[FIGURE: ...]でフォーマットされることを検証。"""
        from src.layout_ocr import ocr_region

        # Arrange
        img = Image.new("RGB", (400, 300), color=(200, 200, 200))
        region = {
            "type": "FIGURE",
            "bbox": [10, 10, 390, 290],
            "confidence": 0.95,
        }

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "message": {"content": "円グラフで構成比を示している"}
        }
        mock_response.raise_for_status = MagicMock()

        # Act
        with patch("src.layout_ocr.requests.post", return_value=mock_response):
            result = ocr_region(img, region)

        # Assert
        assert result.text == "円グラフで構成比を示している", (
            f"VLM description should be extracted. Got: {result.text}"
        )
        assert result.formatted == "[FIGURE: 円グラフで構成比を示している]", (
            f"FIGURE should be formatted as '[FIGURE: ...]'. Got: {result.formatted}"
        )


class TestTitleRegionOcr:
    """TITLE領域のOCRテスト。"""

    def test_title_region_uses_deepseek_ocr(self) -> None:
        """TITLE領域がDeepSeek-OCRで処理されることを検証。"""
        from src.layout_ocr import ocr_region

        # Arrange
        img = Image.new("RGB", (600, 50), color=(255, 255, 255))
        region = {
            "type": "TITLE",
            "bbox": [10, 5, 590, 45],
            "confidence": 0.98,
        }

        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "第2章 システム設計"}}
        mock_response.raise_for_status = MagicMock()

        # Act & Assert
        with patch("src.layout_ocr.requests.post", return_value=mock_response) as mock_post:
            result = ocr_region(img, region)

            call_args = mock_post.call_args
            payload = call_args.kwargs.get("json") or call_args[1].get("json")
            assert payload["model"] == "deepseek-ocr", (
                f"TITLE region should use deepseek-ocr. Got: {payload['model']}"
            )

    def test_title_region_formatted_as_heading(self) -> None:
        """TITLE領域のOCR結果が見出しマークアップで出力されることを検証。"""
        from src.layout_ocr import ocr_region

        # Arrange
        img = Image.new("RGB", (600, 50), color=(255, 255, 255))
        region = {
            "type": "TITLE",
            "bbox": [10, 5, 590, 45],
            "confidence": 0.98,
        }

        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "第3章 実装"}}
        mock_response.raise_for_status = MagicMock()

        # Act
        with patch("src.layout_ocr.requests.post", return_value=mock_response):
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
                {"type": "TITLE", "bbox": [50, 50, 750, 100], "confidence": 0.95},
                {"type": "TEXT", "bbox": [50, 120, 750, 300], "confidence": 0.9},
                {"type": "TEXT", "bbox": [50, 320, 750, 500], "confidence": 0.88},
            ],
            "page_size": [800, 600],
        }

        # Mock OCR responses
        mock_responses = [
            {"message": {"content": "第1章 概要"}},
            {"message": {"content": "これは最初の段落です。"}},
            {"message": {"content": "これは2番目の段落です。"}},
        ]
        mock_post = MagicMock()
        mock_post.raise_for_status = MagicMock()
        mock_post.json.side_effect = mock_responses

        # Act
        with patch("src.layout_ocr.requests.post", return_value=mock_post):
            mock_post.json = MagicMock(side_effect=mock_responses)
            results = ocr_by_layout(str(img_path), layout)

        # Assert
        assert len(results) == 3, f"Should return 3 OCR results. Got: {len(results)}"
        assert results[0].region_type == "TITLE", "First result should be TITLE"
        assert results[1].region_type == "TEXT", "Second result should be TEXT"
        assert results[2].region_type == "TEXT", "Third result should be TEXT"

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
                {"type": "TITLE", "bbox": [50, 50, 600, 100], "confidence": 0.95},
                {"type": "CAPTION", "bbox": [50, 110, 400, 140], "confidence": 0.85},
                {"type": "TEXT", "bbox": [50, 150, 750, 550], "confidence": 0.9},
            ],
            "page_size": [800, 600],
        }

        mock_responses = [
            {"message": {"content": "表1のタイトル"}},
            {"message": {"content": "表1: サンプルデータ"}},
            {"message": {"content": "本文テキスト"}},
        ]
        mock_post = MagicMock()
        mock_post.raise_for_status = MagicMock()

        # Act
        with patch("src.layout_ocr.requests.post", return_value=mock_post):
            mock_post.json = MagicMock(side_effect=mock_responses)
            results = ocr_by_layout(str(img_path), layout)

        # Assert: 順序が維持されている
        types = [r.region_type for r in results]
        assert types == ["TITLE", "CAPTION", "TEXT"], (
            f"Results should maintain region order. Got: {types}"
        )

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
                {"type": "TEXT", "bbox": [50, 100, 750, 500], "confidence": 0.9},
                {"type": "ABANDON", "bbox": [350, 570, 450, 590], "confidence": 0.75},  # Page num
            ],
            "page_size": [800, 600],
        }

        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "本文テキスト"}}
        mock_response.raise_for_status = MagicMock()

        # Act
        with patch("src.layout_ocr.requests.post", return_value=mock_response):
            results = ocr_by_layout(str(img_path), layout)

        # Assert: ABANDONは結果に含まれない
        assert len(results) == 1, f"Only TEXT region should be processed. Got: {len(results)}"
        assert results[0].region_type == "TEXT", (
            f"Result should be TEXT only. Got: {results[0].region_type}"
        )


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

    def test_ocr_by_layout_empty_regions(self, tmp_path: Path) -> None:
        """空のregionsリストに対して空リストを返すことを検証。"""
        from src.layout_ocr import ocr_by_layout

        # Arrange
        img_path = tmp_path / "test_page.png"
        img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        img.save(img_path)

        layout = {
            "regions": [],
            "page_size": [800, 600],
        }

        # Act
        results = ocr_by_layout(str(img_path), layout)

        # Assert
        assert results == [], f"Empty regions should return empty list. Got: {results}"

    def test_ocr_by_layout_unicode_text(self, tmp_path: Path) -> None:
        """Unicode文字を含むOCR結果が正しく処理されることを検証。"""
        from src.layout_ocr import ocr_by_layout

        # Arrange
        img_path = tmp_path / "test_page.png"
        img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        img.save(img_path)

        layout = {
            "regions": [
                {"type": "TEXT", "bbox": [50, 50, 750, 550], "confidence": 0.9},
            ],
            "page_size": [800, 600],
        }

        # Unicode text with various characters
        unicode_text = "日本語テキスト。\n絵文字テスト。\nSpecial: '\"\\/n"

        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": unicode_text}}
        mock_response.raise_for_status = MagicMock()

        # Act
        with patch("src.layout_ocr.requests.post", return_value=mock_response):
            results = ocr_by_layout(str(img_path), layout)

        # Assert
        assert len(results) == 1, "Should return 1 result"
        assert "日本語" in results[0].text, "Unicode text should be preserved"

    def test_ocr_by_layout_mixed_region_types(self, tmp_path: Path) -> None:
        """異なる領域タイプが混在する場合の処理を検証。"""
        from src.layout_ocr import ocr_by_layout

        # Arrange
        img_path = tmp_path / "test_page.png"
        img = Image.new("RGB", (800, 800), color=(255, 255, 255))
        img.save(img_path)

        layout = {
            "regions": [
                {"type": "TITLE", "bbox": [50, 50, 750, 100], "confidence": 0.95},
                {"type": "TEXT", "bbox": [50, 120, 400, 350], "confidence": 0.9},
                {"type": "FIGURE", "bbox": [420, 120, 750, 350], "confidence": 0.88},
                {"type": "CAPTION", "bbox": [420, 360, 750, 390], "confidence": 0.85},
                {"type": "TEXT", "bbox": [50, 400, 750, 600], "confidence": 0.9},
                {"type": "FOOTNOTE", "bbox": [50, 750, 750, 790], "confidence": 0.8},
            ],
            "page_size": [800, 800],
        }

        # 各領域タイプに応じたモックレスポンス
        mock_responses = [
            {"message": {"content": "第5章 結論"}},
            {"message": {"content": "左カラムのテキスト"}},
            {"message": {"content": "統計グラフを示す図"}},
            {"message": {"content": "図5.1: 統計データ"}},
            {"message": {"content": "結論の本文テキスト"}},
            {"message": {"content": "脚注: 参考文献より"}},
        ]
        mock_post = MagicMock()
        mock_post.raise_for_status = MagicMock()

        # Act
        with patch("src.layout_ocr.requests.post", return_value=mock_post):
            mock_post.json = MagicMock(side_effect=mock_responses)
            results = ocr_by_layout(str(img_path), layout)

        # Assert: 各領域が正しいフォーマットで出力
        assert len(results) == 6, f"Should return 6 results. Got: {len(results)}"

        # TITLE: ## {text}
        assert results[0].formatted.startswith("## "), (
            f"TITLE should start with '## '. Got: {results[0].formatted}"
        )

        # TEXT: {text}
        assert results[1].formatted == results[1].text, (
            "TEXT should be unchanged"
        )

        # FIGURE: [FIGURE: {desc}]
        assert results[2].formatted.startswith("[FIGURE:"), (
            f"FIGURE should start with '[FIGURE:'. Got: {results[2].formatted}"
        )

        # CAPTION: *{text}*
        assert results[3].formatted.startswith("*") and results[3].formatted.endswith("*"), (
            f"CAPTION should be wrapped in '*'. Got: {results[3].formatted}"
        )

        # FOOTNOTE: ^{text}^
        assert results[5].formatted.startswith("^") and results[5].formatted.endswith("^"), (
            f"FOOTNOTE should be wrapped in '^'. Got: {results[5].formatted}"
        )
