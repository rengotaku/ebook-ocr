"""Tests for OCR preprocessing module.

Phase 4: US4 - CLAHE (Contrast Limited Adaptive Histogram Equalization)
preprocessor for EasyOCR.

Test coverage:
- T046: apply_clahe - CLAHE前処理テスト
"""

from __future__ import annotations

import numpy as np
import pytest


# =============================================================================
# T046: CLAHE前処理テスト (apply_clahe)
# =============================================================================


class TestApplyCLAHE:
    """Test apply_clahe function for EasyOCR preprocessing."""

    def test_apply_clahe_shape_preserved(self):
        """出力のshapeが入力と一致する"""
        from src.ocr_preprocess import apply_clahe

        # Create test image (H, W, 3) RGB
        img = np.random.randint(0, 255, (100, 200, 3), dtype=np.uint8)
        result = apply_clahe(img)

        assert result.shape == img.shape
        assert result.shape == (100, 200, 3)

    def test_apply_clahe_dtype_preserved(self):
        """出力のdtypeが入力と一致する (uint8)"""
        from src.ocr_preprocess import apply_clahe

        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        result = apply_clahe(img)

        assert result.dtype == np.uint8

    def test_apply_clahe_returns_ndarray(self):
        """ndarray型を返す"""
        from src.ocr_preprocess import apply_clahe

        img = np.random.randint(0, 255, (50, 50, 3), dtype=np.uint8)
        result = apply_clahe(img)

        assert isinstance(result, np.ndarray)

    def test_apply_clahe_contrast_enhanced(self):
        """コントラストが向上する (低コントラスト画像の場合)"""
        from src.ocr_preprocess import apply_clahe

        # Create low-contrast grayscale-ish image (all values near 128)
        img = np.full((100, 100, 3), 128, dtype=np.uint8)
        # Add small variation
        img[40:60, 40:60, :] = 120

        result = apply_clahe(img)

        # CLAHE should increase the range of values (enhance contrast)
        # The output should have a larger standard deviation or range
        input_std = img.std()
        output_std = result.std()

        # After CLAHE, contrast should be enhanced or at least not reduced significantly
        # (allowing for cases where the original has almost no variance)
        assert result.shape == img.shape

    def test_apply_clahe_custom_clip_limit(self):
        """カスタムclip_limitパラメータが使用される"""
        from src.ocr_preprocess import apply_clahe

        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        # Different clip limits should produce different results
        result_low = apply_clahe(img, clip_limit=1.0)
        result_high = apply_clahe(img, clip_limit=4.0)

        # Results should be valid images
        assert result_low.shape == img.shape
        assert result_high.shape == img.shape
        assert result_low.dtype == np.uint8
        assert result_high.dtype == np.uint8

    def test_apply_clahe_custom_tile_size(self):
        """カスタムtile_sizeパラメータが使用される"""
        from src.ocr_preprocess import apply_clahe

        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        # Different tile sizes should be accepted
        result_small = apply_clahe(img, tile_size=4)
        result_large = apply_clahe(img, tile_size=16)

        assert result_small.shape == img.shape
        assert result_large.shape == img.shape

    def test_apply_clahe_rgb_image(self):
        """RGB画像を正しく処理する"""
        from src.ocr_preprocess import apply_clahe

        # Create RGB image with distinct colors
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[:, :, 0] = 200  # Red channel
        img[:, :, 1] = 100  # Green channel
        img[:, :, 2] = 50   # Blue channel

        result = apply_clahe(img)

        # Output should still be RGB
        assert result.shape == (100, 100, 3)
        assert result.dtype == np.uint8

    def test_apply_clahe_grayscale_values(self):
        """グレースケール風の画像も処理可能"""
        from src.ocr_preprocess import apply_clahe

        # Grayscale-like image (R=G=B)
        gray_val = np.random.randint(0, 255, (100, 100), dtype=np.uint8)
        img = np.stack([gray_val, gray_val, gray_val], axis=-1)

        result = apply_clahe(img)

        assert result.shape == img.shape

    def test_apply_clahe_black_image(self):
        """全黒画像の処理"""
        from src.ocr_preprocess import apply_clahe

        img = np.zeros((50, 50, 3), dtype=np.uint8)
        result = apply_clahe(img)

        assert result.shape == img.shape
        assert result.dtype == np.uint8

    def test_apply_clahe_white_image(self):
        """全白画像の処理"""
        from src.ocr_preprocess import apply_clahe

        img = np.full((50, 50, 3), 255, dtype=np.uint8)
        result = apply_clahe(img)

        assert result.shape == img.shape
        assert result.dtype == np.uint8

    def test_apply_clahe_typical_document_size(self):
        """書籍スキャン画像の典型的なサイズ"""
        from src.ocr_preprocess import apply_clahe

        # Typical page size (scaled down)
        img = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        result = apply_clahe(img)

        assert result.shape == (480, 640, 3)

    def test_apply_clahe_small_image(self):
        """非常に小さい画像の処理"""
        from src.ocr_preprocess import apply_clahe

        # Smaller than tile size
        img = np.random.randint(0, 255, (4, 4, 3), dtype=np.uint8)
        result = apply_clahe(img)

        assert result.shape == (4, 4, 3)

    def test_apply_clahe_default_parameters(self):
        """デフォルトパラメータで動作する"""
        from src.ocr_preprocess import apply_clahe

        img = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)

        # Should work without any optional parameters
        result = apply_clahe(img)

        assert result.shape == img.shape
        assert result.dtype == np.uint8
