"""Tests for src.utils shared utility functions.

Phase 2 RED tests: src/utils.py does not exist yet,
so all tests will fail with ImportError.
"""

from __future__ import annotations

import base64
import io
from pathlib import Path

import pytest
from PIL import Image

from src.utils import (
    encode_image_file,
    encode_pil_image,
    format_figure_markers,
    mask_figure_regions,
)


# ---------- encode_image_file ----------


class TestEncodeImageFile:
    """encode_image_file: file path -> base64 string."""

    def test_encode_image_file(self, sample_image: Path) -> None:
        """正常系: base64エンコード結果をデコードすると元のバイト列と一致する。"""
        original_bytes = sample_image.read_bytes()

        result = encode_image_file(str(sample_image))

        decoded = base64.b64decode(result)
        assert decoded == original_bytes

    def test_encode_image_file_returns_str(self, sample_image: Path) -> None:
        """戻り値が str 型であること。"""
        result = encode_image_file(str(sample_image))
        assert isinstance(result, str)


# ---------- encode_pil_image ----------


class TestEncodePilImage:
    """encode_pil_image: PIL Image -> base64 PNG string."""

    def test_encode_pil_image_roundtrip(self, sample_pil_image: Image.Image) -> None:
        """PIL Image を base64 にエンコードし、デコードして PIL Image に復元できる。"""
        result = encode_pil_image(sample_pil_image)

        decoded_bytes = base64.b64decode(result)
        restored = Image.open(io.BytesIO(decoded_bytes))

        assert restored.size == sample_pil_image.size
        assert restored.mode == sample_pil_image.mode

    def test_encode_pil_image_returns_str(self, sample_pil_image: Image.Image) -> None:
        """戻り値が str 型であること。"""
        result = encode_pil_image(sample_pil_image)
        assert isinstance(result, str)


# ---------- format_figure_markers ----------


class TestFormatFigureMarkers:
    """format_figure_markers: layout dict -> marker string."""

    def test_format_figure_markers(self, sample_layout: dict) -> None:
        """page_0001.png に対して 2 つのマーカーが生成される。"""
        result = format_figure_markers("page_0001.png", sample_layout)

        # sample_layout has 2 figures for page_0001.png (confidence 0.95 and 0.85)
        # Both are above default min_confidence=0.7
        assert result.count("FIGURE") + result.count("TABLE") == 2
        assert "figures/page_0001_fig_0.png" in result
        assert "figures/page_0001_tab_0.png" in result

    def test_format_figure_markers_contains_metadata(self, sample_layout: dict) -> None:
        """出力にはtype, cropped_path, confidenceが含まれる。"""
        result = format_figure_markers("page_0001.png", sample_layout)

        assert "FIGURE" in result
        assert "TABLE" in result
        assert "0.95" in result or "95" in result
        assert "cropped_path" in result or "figures/" in result

    def test_format_figure_markers_empty(self, sample_layout: dict) -> None:
        """存在しないページ名に対して空文字列が返る。"""
        result = format_figure_markers("nonexistent_page.png", sample_layout)

        assert result == ""

    def test_format_figure_markers_low_confidence(self, sample_layout: dict) -> None:
        """min_confidence=0.9 で confidence=0.85 のエントリが除外される。"""
        result = format_figure_markers(
            "page_0001.png", sample_layout, min_confidence=0.9
        )

        # Only the FIGURE entry (confidence=0.95) should remain
        # The TABLE entry (confidence=0.85) should be excluded
        assert "FIGURE" in result
        assert "TABLE" not in result


# ---------- mask_figure_regions ----------


class TestMaskFigureRegions:
    """mask_figure_regions: apply white mask over figure bounding boxes."""

    def test_mask_figure_regions(
        self, sample_pil_image: Image.Image, sample_layout: dict
    ) -> None:
        """100x80 の灰色画像に対して bbox [10,20,50,60] のマスクを適用し、マスク領域が白。"""
        result = mask_figure_regions(
            sample_pil_image, "page_0001.png", sample_layout
        )

        # Check that the masked region [10,20,50,60] is white
        for x in range(10, 50):
            for y in range(20, 60):
                pixel = result.getpixel((x, y))
                assert pixel == (255, 255, 255), (
                    f"Pixel at ({x},{y}) should be white (255,255,255), got {pixel}"
                )

    def test_mask_figure_regions_preserves_outside(
        self, sample_pil_image: Image.Image, sample_layout: dict
    ) -> None:
        """マスク領域外のピクセルは元の灰色のまま。"""
        result = mask_figure_regions(
            sample_pil_image, "page_0001.png", sample_layout
        )

        # Check a pixel outside all bounding boxes remains gray
        # bbox1=[10,20,50,60], bbox2=[60,10,90,70]
        # (0, 0) is outside both
        pixel = result.getpixel((0, 0))
        assert pixel == (200, 200, 200), (
            f"Pixel at (0,0) should remain gray (200,200,200), got {pixel}"
        )

    def test_mask_figure_regions_no_figures(
        self, sample_pil_image: Image.Image, sample_layout: dict
    ) -> None:
        """図のないページに対してマスクを適用し、元画像と同じオブジェクトが返る。"""
        result = mask_figure_regions(
            sample_pil_image, "nonexistent_page.png", sample_layout
        )

        # Should return the exact same object (identity check)
        assert result is sample_pil_image

    def test_mask_figure_regions_clamp(self) -> None:
        """bbox が画像境界を超える [-10,-10,200,200] の場合、クランプされて画像全体が白塗り。"""
        img = Image.new("RGB", (100, 80), color=(128, 128, 128))
        layout = {
            "test_page.png": {
                "figures": [
                    {
                        "type": "FIGURE",
                        "bbox": [-10, -10, 200, 200],
                        "confidence": 0.95,
                        "cropped_path": "figures/test_fig.png",
                    },
                ]
            },
        }

        result = mask_figure_regions(img, "test_page.png", layout)

        # After clamping, the entire image should be white
        for x in range(100):
            for y in range(80):
                pixel = result.getpixel((x, y))
                assert pixel == (255, 255, 255), (
                    f"Pixel at ({x},{y}) should be white after clamp, got {pixel}"
                )
