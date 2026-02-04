"""Tests for src.describe_figures VLM figure description functions.

Phase 4 RED tests for FIGURE_MARKER_RE and _describe_single().
"""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from src.describe_figures import FIGURE_MARKER_RE, _describe_single


class TestFigureMarkerRegex:
    """FIGURE_MARKER_RE 正規表現のマッチテスト。"""

    def test_figure_marker_with_confidence(self) -> None:
        """confidence 付き FIGURE マーカーにマッチし、グループが正しいことを検証。"""
        text = "[FIGURE: figures/page_0001_fig_0.png (confidence: 0.95)]"
        match = FIGURE_MARKER_RE.search(text)

        assert match is not None, f"Should match FIGURE marker: {text}"
        assert match.group(1) == "FIGURE"
        assert match.group(2) == "figures/page_0001_fig_0.png"

    def test_table_marker_without_confidence(self) -> None:
        """confidence なし TABLE マーカーにマッチすることを検証。"""
        text = "[TABLE: figures/page_0001_tab_0.png]"
        match = FIGURE_MARKER_RE.search(text)

        assert match is not None, f"Should match TABLE marker: {text}"
        assert match.group(1) == "TABLE"
        assert match.group(2) == "figures/page_0001_tab_0.png"

    def test_plain_text_no_match(self) -> None:
        """普通のテキストにはマッチしないことを検証。"""
        text = "普通のテキスト"
        match = FIGURE_MARKER_RE.search(text)

        assert match is None, f"Should not match plain text: {text}"

    def test_figure_marker_in_multiline(self) -> None:
        """複数行テキスト内でマーカーを検出できることを検証。"""
        text = (
            "Some text before.\n"
            "[FIGURE: figures/page_0010_fig_0.png (confidence: 0.88)]\n"
            "Some text after."
        )
        match = FIGURE_MARKER_RE.search(text)

        assert match is not None
        assert match.group(1) == "FIGURE"
        assert match.group(2) == "figures/page_0010_fig_0.png"

    def test_marker_findall_multiple(self) -> None:
        """複数マーカーを finditer で全て検出できることを検証。"""
        text = (
            "[FIGURE: figures/fig_0.png (confidence: 0.9)]\n"
            "text\n"
            "[TABLE: figures/tab_0.png]\n"
        )
        matches = list(FIGURE_MARKER_RE.finditer(text))

        assert len(matches) == 2, f"Expected 2 matches, got {len(matches)}"


class TestDescribeSingleMock:
    """Ollama VLM API をモックした _describe_single のテスト。"""

    def test_describe_single_mock(self, tmp_path: Path) -> None:
        """モックされた VLM API から図の説明文が返ることを検証。"""
        # テスト用画像を作成
        img_path = tmp_path / "test_figure.png"
        img = Image.new("RGB", (200, 150), color=(100, 100, 100))
        img.save(img_path)

        # Ollama API レスポンスをモック
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "message": {"content": "図の説明文"}
        }
        mock_response.raise_for_status = MagicMock()

        with patch("src.describe_figures.requests.post", return_value=mock_response) as mock_post:
            result = _describe_single(
                str(img_path),
                fig_type="FIGURE",
                model="gemma3:12b",
                base_url="http://localhost:11434",
                timeout=120,
            )

        assert result == "図の説明文", f"Expected '図の説明文', got '{result}'"
        mock_post.assert_called_once()

    def test_describe_single_strips_whitespace(self, tmp_path: Path) -> None:
        """レスポンスの前後空白が除去されることを検証。"""
        img_path = tmp_path / "test_figure.png"
        img = Image.new("RGB", (200, 150), color=(100, 100, 100))
        img.save(img_path)

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "message": {"content": "  説明文  \n"}
        }
        mock_response.raise_for_status = MagicMock()

        with patch("src.describe_figures.requests.post", return_value=mock_response):
            result = _describe_single(
                str(img_path),
                fig_type="TABLE",
                model="gemma3:12b",
                base_url="http://localhost:11434",
                timeout=120,
            )

        assert result == "説明文", f"Expected '説明文', got '{result}'"
