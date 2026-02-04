"""Tests for src.ocr_deepseek OCR engine functions.

Phase 4 RED tests for ocr_page_deepseek() and _detect_repetition().
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from src.ocr_deepseek import _detect_repetition, ocr_page_deepseek


class TestOcrPageDeepseekMock:
    """Ollama API をモックした ocr_page_deepseek のテスト。"""

    def test_ocr_page_deepseek_mock(self, tmp_path: Path) -> None:
        """モックされた Ollama API から OCR 結果テキストが返ることを検証。"""
        # テスト用画像を作成
        img_path = tmp_path / "test_page.png"
        img = Image.new("RGB", (100, 80), color=(200, 200, 200))
        img.save(img_path)

        # Ollama API レスポンスをモック
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "message": {"content": "OCR結果テキスト"}
        }
        mock_response.raise_for_status = MagicMock()

        with patch("src.ocr_deepseek.requests.post", return_value=mock_response) as mock_post:
            result = ocr_page_deepseek(str(img_path))

        assert result == "OCR結果テキスト", (
            f"Expected 'OCR結果テキスト', got '{result}'"
        )
        mock_post.assert_called_once()

    def test_ocr_page_deepseek_strips_whitespace(self, tmp_path: Path) -> None:
        """レスポンスの前後空白が除去されることを検証。"""
        img_path = tmp_path / "test_page.png"
        img = Image.new("RGB", (100, 80), color=(200, 200, 200))
        img.save(img_path)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "message": {"content": "  テキスト with spaces  \n"}
        }
        mock_response.raise_for_status = MagicMock()

        with patch("src.ocr_deepseek.requests.post", return_value=mock_response):
            result = ocr_page_deepseek(str(img_path))

        assert result == "テキスト with spaces", (
            f"Expected stripped text, got '{result}'"
        )


class TestDetectRepetitionNormal:
    """正常テキストに対する反復検出。"""

    def test_detect_repetition_normal(self) -> None:
        """異なる行が複数ある正常テキストに対して None を返すことを検証。"""
        text = "\n".join([f"Line {i}: This is unique content." for i in range(20)])

        result = _detect_repetition(text)

        assert result is None, (
            f"Normal text should not trigger repetition detection, got: {result}"
        )


class TestDetectRepetitionAnomaly:
    """反復テキストに対する異常検出。"""

    def test_detect_repetition_anomaly(self) -> None:
        """同じ行が20回繰り返されるテキストに対して異常検出文字列を返すことを検証。"""
        repeated_line = "This line is repeated many times."
        text = "\n".join([repeated_line] * 20)

        result = _detect_repetition(text)

        assert result is not None, (
            "Repeated text (20 identical lines) should trigger detection"
        )
        assert "Repetition detected" in result, (
            f"Result should contain 'Repetition detected', got: {result}"
        )

    def test_detect_repetition_boundary(self) -> None:
        """min_count=10 の境界: 10回繰り返しで検出されることを検証。"""
        repeated_line = "boundary test line"
        # 11 repeated + 0 unique = ratio 1.0 > 0.5 and count 11 > 10
        text = "\n".join([repeated_line] * 11)

        result = _detect_repetition(text)

        assert result is not None, (
            "11 repeated lines (ratio=1.0, count=11) should trigger detection"
        )


class TestDetectRepetitionEmpty:
    """空テキストに対する処理。"""

    def test_detect_repetition_empty(self) -> None:
        """空文字列に対して None を返すことを検証。"""
        result = _detect_repetition("")

        assert result is None, (
            f"Empty text should return None, got: {result}"
        )

    def test_detect_repetition_whitespace_only(self) -> None:
        """空白のみのテキストに対して None を返すことを検証。"""
        result = _detect_repetition("   \n  \n   ")

        assert result is None, (
            f"Whitespace-only text should return None, got: {result}"
        )


class TestOcrDeepseekContextManager:
    """リソース管理パターンの検証 (FR-008)。"""

    def test_context_manager_usage(self) -> None:
        """Image.open() がコンテキストマネージャで使われていることを検証。"""
        source = Path("src/ocr_deepseek.py").read_text(encoding="utf-8")
        # ocr_pages_deepseek 内の Image.open が with 文内で使われていること
        assert "with Image.open" in source, (
            "Image.open should use context manager (with statement) "
            "to ensure file handles are properly closed"
        )
