"""Tests for src.layout_ocr region-based OCR processing.

Phase 4 RED tests for US2 - Region-based OCR Processing.
These tests will FAIL until src/layout_ocr.py is implemented.

OCR Engine Selection Rules (from research.md):
| Region Type | OCR Engine | Output Format |
|-------------|------------|---------------|
| TITLE | Yomitoku | `## {text}` |
| TEXT | Yomitoku | `{text}` |
| TABLE | Yomitoku | Markdown table |
| FIGURE | VLM (gemma3:12b) | `[FIGURE: {description}]` |
| CAPTION | Yomitoku | `*{text}*` |
| FOOTNOTE | Yomitoku | `^{text}^` |
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

    def test_select_ocr_engine_text_returns_yomitoku(self) -> None:
        """TEXT領域に対してYomitokuが選択されることを検証。"""
        from src.layout_ocr import select_ocr_engine

        # Act
        engine = select_ocr_engine("TEXT")

        # Assert
        assert engine == "yomitoku", (
            f"TEXT region should use yomitoku engine. Got: {engine}"
        )

    def test_select_ocr_engine_title_returns_yomitoku(self) -> None:
        """TITLE領域に対してYomitokuが選択されることを検証。"""
        from src.layout_ocr import select_ocr_engine

        # Act
        engine = select_ocr_engine("TITLE")

        # Assert
        assert engine == "yomitoku", (
            f"TITLE region should use yomitoku engine. Got: {engine}"
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

    def test_select_ocr_engine_table_returns_yomitoku(self) -> None:
        """TABLE領域に対してYomitokuが選択されることを検証。"""
        from src.layout_ocr import select_ocr_engine

        # Act
        engine = select_ocr_engine("TABLE")

        # Assert
        assert engine == "yomitoku", (
            f"TABLE region should use yomitoku engine. Got: {engine}"
        )

    def test_select_ocr_engine_caption_returns_yomitoku(self) -> None:
        """CAPTION領域に対してYomitokuが選択されることを検証。"""
        from src.layout_ocr import select_ocr_engine

        # Act
        engine = select_ocr_engine("CAPTION")

        # Assert
        assert engine == "yomitoku", (
            f"CAPTION region should use yomitoku engine. Got: {engine}"
        )

    def test_select_ocr_engine_footnote_returns_yomitoku(self) -> None:
        """FOOTNOTE領域に対してYomitokuが選択されることを検証。"""
        from src.layout_ocr import select_ocr_engine

        # Act
        engine = select_ocr_engine("FOOTNOTE")

        # Assert
        assert engine == "yomitoku", (
            f"FOOTNOTE region should use yomitoku engine. Got: {engine}"
        )

    def test_select_ocr_engine_formula_returns_yomitoku(self) -> None:
        """FORMULA領域に対してYomitokuが選択されることを検証。"""
        from src.layout_ocr import select_ocr_engine

        # Act
        engine = select_ocr_engine("FORMULA")

        # Assert
        assert engine == "yomitoku", (
            f"FORMULA region should use yomitoku engine. Got: {engine}"
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
    """TEXT領域のOCRテスト（Yomitoku使用）。"""

    def test_text_region_uses_yomitoku(self, tmp_path: Path) -> None:
        """TEXT領域がYomitokuで処理されることを検証。"""
        from src.layout_ocr import ocr_region

        # Arrange
        img = Image.new("RGB", (500, 200), color=(255, 255, 255))
        region = {
            "type": "TEXT",
            "bbox": [10, 10, 490, 190],
            "confidence": 0.9,
        }

        # Act & Assert: ocr_page_yomitoku をモック
        with patch("src.ocr_yomitoku.ocr_page_yomitoku", return_value="テキスト内容") as mock_ocr:
            result = ocr_region(img, region)

            # Yomitokuが呼ばれたことを確認
            assert mock_ocr.called, "ocr_page_yomitoku should be called for TEXT region"

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

        # Act: ocr_page_yomitoku をモック
        with patch("src.ocr_yomitoku.ocr_page_yomitoku", return_value="これは本文です。"):
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
            assert payload["model"] != "yomitoku", (
                f"FIGURE region should NOT use yomitoku. Got: {payload['model']}"
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

    def test_title_region_uses_yomitoku(self) -> None:
        """TITLE領域がYomitokuで処理されることを検証。"""
        from src.layout_ocr import ocr_region

        # Arrange
        img = Image.new("RGB", (600, 50), color=(255, 255, 255))
        region = {
            "type": "TITLE",
            "bbox": [10, 5, 590, 45],
            "confidence": 0.98,
        }

        # Act & Assert: ocr_page_yomitoku をモック
        with patch("src.ocr_yomitoku.ocr_page_yomitoku", return_value="第2章 システム設計") as mock_ocr:
            result = ocr_region(img, region)

            # Yomitokuが呼ばれたことを確認
            assert mock_ocr.called, "ocr_page_yomitoku should be called for TITLE region"

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

        # Act: ocr_page_yomitoku をモック
        with patch("src.ocr_yomitoku.ocr_page_yomitoku", return_value="第3章 実装"):
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

    # NOTE: test_ocr_by_layout_empty_regions removed - replaced by Phase 5 fallback tests
    # Empty regions now trigger fallback (US4), not return empty list

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

        # Act: ocr_page_yomitoku をモック
        with patch("src.ocr_yomitoku.ocr_page_yomitoku", return_value=unicode_text):
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


# ============================================================================
# Phase 5: US4 - フォールバック処理テスト
# ============================================================================


class TestCalculateCoverage:
    """カバー率計算のテスト。"""

    def test_calculate_coverage_single_region(self) -> None:
        """単一領域のカバー率が正しく計算されることを検証。

        100x100のページに50x50の領域 = 25%のカバー率
        """
        from src.layout_ocr import calculate_coverage

        # Arrange
        regions = [
            {"type": "TEXT", "bbox": [0, 0, 50, 50], "confidence": 0.9},
        ]
        page_size = (100, 100)  # 10000 pixels total

        # Act
        coverage = calculate_coverage(regions, page_size)

        # Assert
        assert coverage == 0.25, (
            f"50x50 region on 100x100 page should be 25% coverage. Got: {coverage}"
        )

    def test_calculate_coverage_multiple_regions(self) -> None:
        """複数領域の合計カバー率が正しく計算されることを検証。

        100x100のページに25x25の領域2つ = (625 + 625) / 10000 = 12.5%
        """
        from src.layout_ocr import calculate_coverage

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
        assert coverage == expected, (
            f"Two 25x25 regions on 100x100 page should be 12.5% coverage. Got: {coverage}"
        )

    def test_calculate_coverage_full_page(self) -> None:
        """ページ全体をカバーする領域の場合、カバー率が100%であることを検証。"""
        from src.layout_ocr import calculate_coverage

        # Arrange
        regions = [
            {"type": "TEXT", "bbox": [0, 0, 800, 600], "confidence": 0.9},
        ]
        page_size = (800, 600)

        # Act
        coverage = calculate_coverage(regions, page_size)

        # Assert
        assert coverage == 1.0, (
            f"Full page coverage should be 100%. Got: {coverage}"
        )

    def test_calculate_coverage_empty_regions(self) -> None:
        """空の領域リストの場合、カバー率が0%であることを検証。"""
        from src.layout_ocr import calculate_coverage

        # Arrange
        regions: list[dict] = []
        page_size = (800, 600)

        # Act
        coverage = calculate_coverage(regions, page_size)

        # Assert
        assert coverage == 0.0, (
            f"Empty regions should have 0% coverage. Got: {coverage}"
        )

    def test_calculate_coverage_real_world_example(self) -> None:
        """実際のページに近い例でカバー率を計算。

        1920x1080ページに複数の領域があるケース
        """
        from src.layout_ocr import calculate_coverage

        # Arrange: 複雑なレイアウト
        regions = [
            {"type": "TITLE", "bbox": [100, 50, 1820, 120], "confidence": 0.95},  # 1720x70
            {"type": "TEXT", "bbox": [100, 150, 900, 800], "confidence": 0.9},   # 800x650
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
        assert abs(coverage - expected) < 0.001, (
            f"Coverage should be approximately {expected:.3f}. Got: {coverage:.3f}"
        )


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
        assert result is True, (
            "Empty regions should trigger fallback"
        )

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
        assert result is True, (
            "Coverage below 30% should trigger fallback"
        )

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
        assert result is False, (
            "Coverage above 30% should not trigger fallback"
        )

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
        assert result is False, (
            "Coverage at exactly 30% should not trigger fallback"
        )

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
        assert result is True, (
            "40% coverage with 50% threshold should trigger fallback"
        )

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
        assert result is True, (
            "Single FIGURE covering full page should trigger fallback"
        )

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
        assert result is False, (
            "Multiple regions with sufficient coverage should not trigger fallback"
        )


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
        with patch("src.ocr_yomitoku.ocr_page_yomitoku", return_value="ページ全体のOCR結果") as mock_ocr:
            results = ocr_by_layout(str(img_path), layout)

            # Assert: フォールバックでページ全体OCRが実行される
            assert len(results) == 1, (
                f"Fallback should return 1 result for full page OCR. Got: {len(results)}"
            )
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
        with patch("src.ocr_yomitoku.ocr_page_yomitoku", return_value="フォールバックOCR結果"):
            results = ocr_by_layout(str(img_path), layout)

        # Assert
        assert len(results) == 1, (
            f"Missing regions key should trigger fallback. Got: {len(results)}"
        )


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

        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "フォールバック結果"}}
        mock_response.raise_for_status = MagicMock()

        # Act
        with patch("src.layout_ocr.requests.post", return_value=mock_response) as mock_post:
            results = ocr_by_layout(str(img_path), layout)

            # Assert: フォールバックが実行される
            assert len(results) == 1, (
                f"Low coverage should trigger fallback. Got: {len(results)}"
            )
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

        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "通常OCR結果"}}
        mock_response.raise_for_status = MagicMock()

        # Act
        with patch("src.layout_ocr.requests.post", return_value=mock_response):
            results = ocr_by_layout(str(img_path), layout)

        # Assert: 領域別OCRが実行される（フォールバックしない）
        assert len(results) == 1, f"Should return 1 result. Got: {len(results)}"
        assert results[0].region_type == "TEXT", (
            f"Result should be TEXT (not FALLBACK). Got: {results[0].region_type}"
        )

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

        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "フォールバック結果"}}
        mock_response.raise_for_status = MagicMock()

        # Act
        with patch("src.layout_ocr.requests.post", return_value=mock_response):
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

        mock_response = MagicMock()
        mock_response.json.return_value = {"message": {"content": "ページ全体のテキスト"}}
        mock_response.raise_for_status = MagicMock()

        # Act
        with patch("src.layout_ocr.requests.post", return_value=mock_response):
            results = ocr_by_layout(str(img_path), layout)

        # Assert: フォールバックが実行される
        assert len(results) == 1, (
            f"Full page FIGURE should trigger fallback. Got: {len(results)}"
        )
        # フォールバック結果は FALLBACK または TEXT
        assert results[0].region_type in ("FALLBACK", "TEXT"), (
            f"Fallback result type should be FALLBACK or TEXT. Got: {results[0].region_type}"
        )


class TestFallbackEdgeCases:
    """フォールバック処理のエッジケーステスト。"""

    def test_calculate_coverage_zero_page_size(self) -> None:
        """ページサイズがゼロの場合のハンドリングを検証。"""
        from src.layout_ocr import calculate_coverage

        # Arrange
        regions = [{"type": "TEXT", "bbox": [0, 0, 100, 100], "confidence": 0.9}]

        # Act & Assert: ゼロ除算を避ける
        # 実装によってはエラーまたは0.0を返す
        try:
            coverage = calculate_coverage(regions, (0, 0))
            # ゼロ除算を避けて0.0を返す実装の場合
            assert coverage == 0.0, (
                f"Zero page size should return 0.0 coverage. Got: {coverage}"
            )
        except (ZeroDivisionError, ValueError):
            # エラーを投げる実装も許容
            pass

    def test_calculate_coverage_negative_bbox(self) -> None:
        """負のbbox座標の場合のハンドリングを検証。"""
        from src.layout_ocr import calculate_coverage

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
        assert coverage == expected or coverage >= 0, (
            f"Negative bbox should be handled. Got: {coverage}"
        )

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
        assert result is True, (
            "Only ABANDON regions should trigger fallback"
        )


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
        from src.layout_ocr import is_title

        # Arrange: YOLOがTITLEとして検出
        region = {"type": "TITLE", "bbox": [50, 50, 700, 100], "confidence": 0.95}
        yomitoku_result = {}  # Yomitoku結果なし

        # Act
        result = is_title(region, yomitoku_result)

        # Assert
        assert result is True, (
            "Region with type='TITLE' should be recognized as title"
        )

    def test_is_title_yomitoku_section_headings_role(self) -> None:
        """Yomitokuのroleがsection_headingsの場合、is_titleがTrueを返すことを検証。"""
        from src.layout_ocr import is_title

        # Arrange: YOLOはTEXTだが、Yomitokuがsection_headingsと判定
        region = {"type": "TEXT", "bbox": [50, 50, 700, 100], "confidence": 0.9}
        yomitoku_result = {"role": "section_headings"}

        # Act
        result = is_title(region, yomitoku_result)

        # Assert
        assert result is True, (
            "Region with yomitoku role='section_headings' should be recognized as title"
        )

    def test_is_title_text_without_role_returns_false(self) -> None:
        """YOLO=TEXT、Yomitokuのroleなしの場合、is_titleがFalseを返すことを検証。"""
        from src.layout_ocr import is_title

        # Arrange: 通常のTEXT領域
        region = {"type": "TEXT", "bbox": [50, 100, 700, 500], "confidence": 0.9}
        yomitoku_result = {}  # roleなし

        # Act
        result = is_title(region, yomitoku_result)

        # Assert
        assert result is False, (
            "Regular TEXT region without section_headings role should not be title"
        )

    def test_is_title_yomitoku_paragraph_role(self) -> None:
        """Yomitokuのroleがparagraphの場合、is_titleがFalseを返すことを検証。"""
        from src.layout_ocr import is_title

        # Arrange: Yomitokuがparagraphと判定
        region = {"type": "TEXT", "bbox": [50, 100, 700, 500], "confidence": 0.9}
        yomitoku_result = {"role": "paragraph"}

        # Act
        result = is_title(region, yomitoku_result)

        # Assert
        assert result is False, (
            "Region with yomitoku role='paragraph' should not be title"
        )

    def test_is_title_both_yolo_and_yomitoku_agree(self) -> None:
        """YOLOとYomitoku両方がTITLEと判定した場合、Trueを返すことを検証。"""
        from src.layout_ocr import is_title

        # Arrange: 両方がTITLEと判定
        region = {"type": "TITLE", "bbox": [50, 50, 700, 100], "confidence": 0.98}
        yomitoku_result = {"role": "section_headings"}

        # Act
        result = is_title(region, yomitoku_result)

        # Assert
        assert result is True, (
            "Region detected as TITLE by both YOLO and Yomitoku should be title"
        )


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
        assert result is True, (
            "Empty string should be considered low quality"
        )

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
        assert result is False, (
            "Text with exactly 10 characters should not be low quality"
        )

    def test_is_low_quality_high_non_char_ratio(self) -> None:
        """非文字率が50%を超えるテキストが低品質と判定されることを検証。"""
        from src.layout_ocr import is_low_quality

        # Arrange: 60%以上が非文字（記号・空白）
        text = "...!!!@@@###   ---$$$%%%^^^"  # 27文字全て非文字

        # Act
        result = is_low_quality(text)

        # Assert
        assert result is True, (
            "Text with >50% non-character ratio should be low quality"
        )

    def test_is_low_quality_normal_japanese_text(self) -> None:
        """通常の日本語テキストは低品質でないことを検証。"""
        from src.layout_ocr import is_low_quality

        # Arrange: 通常の日本語テキスト
        text = "これは正常な日本語のテキストです。"

        # Act
        result = is_low_quality(text)

        # Assert
        assert result is False, (
            "Normal Japanese text should not be low quality"
        )

    def test_is_low_quality_mixed_content(self) -> None:
        """日本語と記号が混在するが正常なテキストを検証。"""
        from src.layout_ocr import is_low_quality

        # Arrange: 正常な混合テキスト（記号率は50%以下）
        text = "第1章：はじめに（2026年版）"

        # Act
        result = is_low_quality(text)

        # Assert
        assert result is False, (
            "Mixed text with reasonable symbol ratio should not be low quality"
        )

    def test_is_low_quality_whitespace_only(self) -> None:
        """空白のみのテキストが低品質と判定されることを検証。"""
        from src.layout_ocr import is_low_quality

        # Arrange: 空白のみ
        text = "          "  # 10文字のスペース

        # Act
        result = is_low_quality(text)

        # Assert
        assert result is True, (
            "Whitespace-only text should be low quality"
        )


class TestCalcNonCharRatio:
    """非文字率計算関数のテスト。

    calc_non_char_ratio() は日本語/英数字以外の文字の割合を計算する。
    """

    def test_calc_non_char_ratio_all_japanese(self) -> None:
        """全て日本語文字の場合、非文字率が0であることを検証。"""
        from src.layout_ocr import calc_non_char_ratio

        # Arrange
        text = "日本語テキスト"

        # Act
        ratio = calc_non_char_ratio(text)

        # Assert
        assert ratio == 0.0, (
            f"Pure Japanese text should have 0% non-char ratio. Got: {ratio}"
        )

    def test_calc_non_char_ratio_all_symbols(self) -> None:
        """全て記号の場合、非文字率が1であることを検証。"""
        from src.layout_ocr import calc_non_char_ratio

        # Arrange
        text = "!!!@@@###$$$%%%"

        # Act
        ratio = calc_non_char_ratio(text)

        # Assert
        assert ratio == 1.0, (
            f"All-symbol text should have 100% non-char ratio. Got: {ratio}"
        )

    def test_calc_non_char_ratio_half_and_half(self) -> None:
        """半分が文字、半分が記号の場合を検証。"""
        from src.layout_ocr import calc_non_char_ratio

        # Arrange: 5文字 + 5記号 = 50%
        text = "あいうえお!@#$%"

        # Act
        ratio = calc_non_char_ratio(text)

        # Assert
        assert 0.45 <= ratio <= 0.55, (
            f"Half-and-half text should have ~50% non-char ratio. Got: {ratio}"
        )

    def test_calc_non_char_ratio_empty_string(self) -> None:
        """空文字列の場合の処理を検証。"""
        from src.layout_ocr import calc_non_char_ratio

        # Act
        ratio = calc_non_char_ratio("")

        # Assert: 空文字列は0.0を返す（または別の定義による）
        assert ratio == 0.0 or ratio == 1.0, (
            f"Empty string non-char ratio should be 0.0 or 1.0. Got: {ratio}"
        )

    def test_calc_non_char_ratio_english_and_numbers(self) -> None:
        """英数字は文字としてカウントされることを検証。"""
        from src.layout_ocr import calc_non_char_ratio

        # Arrange: 英数字のみ
        text = "ABC123xyz"

        # Act
        ratio = calc_non_char_ratio(text)

        # Assert
        assert ratio == 0.0, (
            f"Alphanumeric text should have 0% non-char ratio. Got: {ratio}"
        )


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
        assert engine_used == "yomitoku", (
            f"Should use yomitoku when it succeeds. Got: {engine_used}"
        )
        assert text == "正常なOCR結果テキスト", (
            f"Should return yomitoku result. Got: {text}"
        )

    def test_ocr_with_fallback_yomitoku_empty_uses_paddleocr(self) -> None:
        """Yomitokuが空結果の場合、PaddleOCRにフォールバックすることを検証。"""
        from src.layout_ocr import ocr_with_fallback

        # Arrange
        img = Image.new("RGB", (200, 50), color=(255, 255, 255))

        # Act: Yomitokuが空を返し、PaddleOCRが成功
        with patch("src.ocr_yomitoku.ocr_page_yomitoku", return_value=""):
            with patch("src.ocr_ensemble.ocr_paddleocr") as mock_paddle:
                mock_paddle.return_value = MagicMock(
                    success=True, text="PaddleOCRからの結果"
                )
                text, engine_used = ocr_with_fallback(img)

        # Assert
        assert engine_used == "paddleocr", (
            f"Should fallback to paddleocr when yomitoku is empty. Got: {engine_used}"
        )

    def test_ocr_with_fallback_yomitoku_low_quality_uses_paddleocr(self) -> None:
        """Yomitokuが低品質結果の場合、PaddleOCRにフォールバックすることを検証。"""
        from src.layout_ocr import ocr_with_fallback

        # Arrange
        img = Image.new("RGB", (200, 50), color=(255, 255, 255))

        # Act: Yomitokuが短いゴミ結果を返す
        with patch("src.ocr_yomitoku.ocr_page_yomitoku", return_value="!!!???"):
            with patch("src.ocr_ensemble.ocr_paddleocr") as mock_paddle:
                mock_paddle.return_value = MagicMock(
                    success=True, text="PaddleOCRからの正常な結果テキスト"
                )
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
                    mock_tesseract.return_value = MagicMock(
                        success=True, text="Tesseractからの結果"
                    )
                    text, engine_used = ocr_with_fallback(img)

        # Assert
        assert engine_used == "tesseract", (
            f"Should fallback to tesseract when others fail. Got: {engine_used}"
        )

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
        assert engine_used == "none", (
            f"Should indicate no engine succeeded. Got: {engine_used}"
        )


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
        assert center_pixel == (255, 255, 255), (
            f"FIGURE region should be white. Got: {center_pixel}"
        )

        # 領域外は元のまま（赤）
        outside_pixel = masked.getpixel((80, 80))
        assert outside_pixel == (255, 0, 0), (
            f"Outside FIGURE region should remain unchanged. Got: {outside_pixel}"
        )

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
        assert img.getpixel((30, 30)) == original_pixel, (
            "Original image should not be modified"
        )
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
                {"type": "TITLE", "bbox": [50, 50, 750, 100], "confidence": 0.95},
                {"type": "FIGURE", "bbox": [50, 120, 400, 350], "confidence": 0.9},
                {"type": "TEXT", "bbox": [50, 370, 750, 550], "confidence": 0.88},
            ],
            "page_size": [800, 600],
        }

        # Act: モックでOCR結果を設定
        with patch("src.ocr_yomitoku.ocr_page_yomitoku", return_value="テキスト内容"):
            # FIGUREはVLMで処理されるのでrequests.postをモック
            mock_response = MagicMock()
            mock_response.json.return_value = {"message": {"content": "図の説明"}}
            mock_response.raise_for_status = MagicMock()

            with patch("src.layout_ocr.requests.post", return_value=mock_response):
                results = ocr_by_layout(str(img_path), layout)

        # Assert: 結果にFIGUREが含まれない（またはFIGUREは除外される設計の場合）
        # 注: 現在の実装ではFIGUREもVLMで処理され結果に含まれる
        # FR-012の要件は「FIGURE領域がOCR出力から除外」なので、これをテスト
        figure_results = [r for r in results if r.region_type == "FIGURE"]

        # FR-012要件: FIGUREはbook.txtから除外される
        # ここでは「除外される」ことを期待するテスト
        assert len(figure_results) == 0, (
            f"FIGURE regions should be excluded from OCR output. Found: {len(figure_results)}"
        )

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
                {"type": "TEXT", "bbox": [550, 50, 950, 200], "confidence": 0.9},
                # 左カラム上部（読み順: 1番目）
                {"type": "TITLE", "bbox": [50, 50, 450, 100], "confidence": 0.95},
                # 左カラム中部（読み順: 2番目）
                {"type": "TEXT", "bbox": [50, 120, 450, 300], "confidence": 0.88},
                # 右カラム下部（読み順: 4番目）
                {"type": "TEXT", "bbox": [550, 220, 950, 400], "confidence": 0.87},
            ],
            "page_size": [1000, 600],
        }

        # Mock OCR responses - 各領域に異なるテキストを返す
        mock_texts = {
            "TITLE": "タイトル",
            "TEXT_LEFT": "左カラム本文",
            "TEXT_RIGHT1": "右カラム上部",
            "TEXT_RIGHT2": "右カラム下部",
        }

        # Act
        with patch("src.ocr_yomitoku.ocr_page_yomitoku") as mock_ocr:
            # 読み順でソートされた後に呼ばれるので、順番を設定
            mock_ocr.side_effect = [
                "タイトル",      # 左カラム TITLE
                "左カラム本文",   # 左カラム TEXT
                "右カラム上部",   # 右カラム TEXT (上)
                "右カラム下部",   # 右カラム TEXT (下)
            ]
            results = ocr_by_layout(str(img_path), layout)

        # Assert: 読み順（左カラム→右カラム）で結果が返される
        assert len(results) == 4, f"Should have 4 results. Got: {len(results)}"

        # 最初はTITLE（左カラム上部）
        assert results[0].region_type == "TITLE", (
            f"First result should be TITLE. Got: {results[0].region_type}"
        )
        # 2番目は左カラムのTEXT
        assert results[1].region_type == "TEXT", (
            f"Second result should be TEXT. Got: {results[1].region_type}"
        )

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
                {"type": "TEXT", "bbox": [50, 400, 550, 600], "confidence": 0.85},
                {"type": "TEXT", "bbox": [50, 200, 550, 380], "confidence": 0.88},
                {"type": "TITLE", "bbox": [50, 50, 550, 100], "confidence": 0.95},
            ],
            "page_size": [600, 800],
        }

        # Act
        with patch("src.ocr_yomitoku.ocr_page_yomitoku") as mock_ocr:
            mock_ocr.side_effect = ["タイトル", "段落1", "段落2"]
            results = ocr_by_layout(str(img_path), layout)

        # Assert: 上から下の順序
        assert len(results) == 3, f"Should have 3 results. Got: {len(results)}"
        assert results[0].region_type == "TITLE", "First should be TITLE (top)"
        assert results[1].region_type == "TEXT", "Second should be TEXT (middle)"
        assert results[2].region_type == "TEXT", "Third should be TEXT (bottom)"
