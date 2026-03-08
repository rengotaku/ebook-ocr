"""Tests for src.layout.code_detector gray background detection.

Tests for detect_gray_background function:
- 灰色背景の検出
- 非灰色背景の排除
- エッジケースのバリデーション

Tests for paragraphs_to_layout integration:
- cv_img 提供時の CODE 判定
- cv_img=None 時の後方互換
- TITLE は灰色チェックしない
- アスペクト比フィルタ
"""

from __future__ import annotations

import numpy as np


class TestDetectGrayBackgroundBasic:
    """基本的な灰色背景検出を検証する。"""

    def test_gray_background_returns_true(self) -> None:
        """灰色背景画像 (RGB 180,180,180) → True を検証。"""
        from src.layout.code_detector import detect_gray_background

        # Arrange: 灰色 (RGB 180,180,180) の画像を作成
        # OpenCV は BGR 順
        img = np.full((100, 100, 3), fill_value=180, dtype=np.uint8)
        bbox = [0, 0, 100, 100]

        # Act
        result = detect_gray_background(img, bbox)

        # Assert
        assert result is True, f"Gray background (RGB 180,180,180) should be detected as gray. Got: {result}"

    def test_white_background_returns_false(self) -> None:
        """白背景画像 (RGB 255,255,255) → False を検証 (V=255 > 200 で灰色外)。"""
        from src.layout.code_detector import detect_gray_background

        # Arrange: 白 (BGR 255,255,255) の画像
        img = np.full((100, 100, 3), fill_value=255, dtype=np.uint8)
        bbox = [0, 0, 100, 100]

        # Act
        result = detect_gray_background(img, bbox)

        # Assert: V=255 > value_max=200 なので灰色外
        assert result is False, f"White background (V=255 > 200) should NOT be detected as gray. Got: {result}"

    def test_black_background_returns_false(self) -> None:
        """黒背景画像 (RGB 0,0,0) → False を検証 (V=0 < 50 で灰色外)。"""
        from src.layout.code_detector import detect_gray_background

        # Arrange: 黒 (BGR 0,0,0) の画像
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        bbox = [0, 0, 100, 100]

        # Act
        result = detect_gray_background(img, bbox)

        # Assert: V=0 < value_min=50 なので灰色外
        assert result is False, f"Black background (V=0 < 50) should NOT be detected as gray. Got: {result}"

    def test_color_background_returns_false(self) -> None:
        """カラー背景画像 (RGB 255,0,0) → False を検証 (彩度高い)。"""
        from src.layout.code_detector import detect_gray_background

        # Arrange: 赤 (BGR: B=0, G=0, R=255) の画像
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[:, :, 2] = 255  # R チャンネル
        bbox = [0, 0, 100, 100]

        # Act
        result = detect_gray_background(img, bbox)

        # Assert: 彩度が高いため灰色外
        assert result is False, f"Red background (high saturation) should NOT be detected as gray. Got: {result}"


class TestDetectGrayBackgroundThreshold:
    """閾値に基づく混合背景の判定を検証する。"""

    def test_mixed_gray_70_percent_at_threshold_returns_true(self) -> None:
        """混合背景 (灰色70% + 白30%) で threshold=0.7 → True を検証。"""
        from src.layout.code_detector import detect_gray_background

        # Arrange: 100x100 画像、70画素行は灰色、30画素行は白
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        # 上70行: 灰色 (BGR 180,180,180) → HSV の S≈0, V≈180
        img[:70, :] = 180
        # 下30行: 白 (BGR 255,255,255) → HSV の S=0, V=255
        img[70:, :] = 255
        bbox = [0, 0, 100, 100]

        # Act
        result = detect_gray_background(img, bbox, threshold=0.7)

        # Assert: 灰色比率 = 0.70 >= threshold=0.70 → True
        assert result is True, f"Mixed background (gray=70%, threshold=0.7) should return True. Got: {result}"

    def test_mixed_gray_60_percent_below_threshold_returns_false(self) -> None:
        """混合背景 (灰色60% + 白40%) で threshold=0.7 → False を検証。"""
        from src.layout.code_detector import detect_gray_background

        # Arrange: 100x100 画像、60画素行は灰色、40画素行は白
        img = np.zeros((100, 100, 3), dtype=np.uint8)
        img[:60, :] = 180  # 灰色
        img[60:, :] = 255  # 白
        bbox = [0, 0, 100, 100]

        # Act
        result = detect_gray_background(img, bbox, threshold=0.7)

        # Assert: 灰色比率 = 0.60 < threshold=0.70 → False
        assert result is False, f"Mixed background (gray=60%, threshold=0.7) should return False. Got: {result}"


class TestDetectGrayBackgroundValidation:
    """入力バリデーションのエッジケースを検証する。"""

    def test_none_image_returns_false(self) -> None:
        """cv_img が None → False を検証。"""
        from src.layout.code_detector import detect_gray_background

        # Act
        result = detect_gray_background(None, [0, 0, 100, 100])

        # Assert
        assert result is False, f"None image should return False. Got: {result}"

    def test_bbox_out_of_bounds_returns_false(self) -> None:
        """bbox が画像範囲外 → False を検証。"""
        from src.layout.code_detector import detect_gray_background

        # Arrange: 100x100 の画像に対して範囲外の bbox
        img = np.full((100, 100, 3), fill_value=180, dtype=np.uint8)
        bbox = [200, 200, 300, 300]  # 画像の外側

        # Act
        result = detect_gray_background(img, bbox)

        # Assert
        assert result is False, f"Out-of-bounds bbox should return False. Got: {result}"

    def test_bbox_zero_width_returns_false(self) -> None:
        """bbox の幅が 0 → False を検証。"""
        from src.layout.code_detector import detect_gray_background

        # Arrange
        img = np.full((100, 100, 3), fill_value=180, dtype=np.uint8)
        bbox = [50, 10, 50, 90]  # x1 == x2 → 幅 0

        # Act
        result = detect_gray_background(img, bbox)

        # Assert
        assert result is False, f"Zero-width bbox should return False. Got: {result}"

    def test_bbox_zero_height_returns_false(self) -> None:
        """bbox の高さが 0 → False を検証。"""
        from src.layout.code_detector import detect_gray_background

        # Arrange
        img = np.full((100, 100, 3), fill_value=180, dtype=np.uint8)
        bbox = [10, 50, 90, 50]  # y1 == y2 → 高さ 0

        # Act
        result = detect_gray_background(img, bbox)

        # Assert
        assert result is False, f"Zero-height bbox should return False. Got: {result}"


class TestDetectGrayBackgroundBboxCrop:
    """bbox によるクロップが正しく機能することを検証する。"""

    def test_detects_gray_in_specified_bbox_only(self) -> None:
        """指定した bbox 内のみを評価することを検証。

        画像全体は白だが bbox 内は灰色 → True になる。
        """
        from src.layout.code_detector import detect_gray_background

        # Arrange: 全体は白、中央 50x50 部分のみ灰色
        img = np.full((200, 200, 3), fill_value=255, dtype=np.uint8)
        img[50:100, 50:100] = 180  # 中央部分を灰色に
        bbox = [50, 50, 100, 100]  # 灰色部分のみ

        # Act
        result = detect_gray_background(img, bbox)

        # Assert: bbox 内は全て灰色なので True
        assert result is True, f"Should detect gray only within specified bbox. Got: {result}"

    def test_ignores_gray_outside_bbox(self) -> None:
        """bbox 外の灰色は無視されることを検証。

        bbox 外は灰色だが bbox 内は白 → False になる。
        """
        from src.layout.code_detector import detect_gray_background

        # Arrange: bbox 外は灰色、bbox 内は白
        img = np.full((200, 200, 3), fill_value=180, dtype=np.uint8)
        img[50:100, 50:100] = 255  # bbox 内部は白
        bbox = [50, 50, 100, 100]

        # Act
        result = detect_gray_background(img, bbox)

        # Assert: bbox 内は白なので False
        assert result is False, f"Should ignore gray outside bbox. Got: {result}"


class MockParagraph:
    """yomitoku ParagraphSchema の最小モック。"""

    def __init__(self, box, contents="test", role=None):
        self.box = box
        self.contents = contents
        self.role = role


class TestParagraphsToLayoutIntegration:
    """paragraphs_to_layout と灰色背景判定の統合テスト。"""

    def test_paragraphs_to_layout_code_region_with_gray_bg(self) -> None:
        """cv_img 提供 + TEXT 領域 + 灰色背景 → type='CODE' になること。"""
        import numpy as np

        from src.layout.detector import paragraphs_to_layout

        # Arrange: 全体が灰色 (BGR 180,180,180) の画像
        cv_img = np.full((200, 400, 3), fill_value=180, dtype=np.uint8)
        # TEXT 段落: アスペクト比 = 200/100 = 2.0 <= 8.0
        paragraph = MockParagraph(box=[0, 0, 200, 100])
        figures = []

        # Act
        result = paragraphs_to_layout([paragraph], figures, (400, 200), cv_img=cv_img)

        # Assert
        assert len(result["regions"]) == 1
        region = result["regions"][0]
        assert region["type"] == "CODE", f"Gray background TEXT should become CODE. Got: {region['type']}"
        assert region["label"] == "code", f"CODE label should be 'code'. Got: {region['label']}"

    def test_paragraphs_to_layout_text_with_white_bg(self) -> None:
        """cv_img 提供 + TEXT 領域 + 白背景 → type='TEXT' のまま。"""
        import numpy as np

        from src.layout.detector import paragraphs_to_layout

        # Arrange: 全体が白 (BGR 255,255,255) の画像
        cv_img = np.full((200, 400, 3), fill_value=255, dtype=np.uint8)
        paragraph = MockParagraph(box=[0, 0, 200, 100])
        figures = []

        # Act
        result = paragraphs_to_layout([paragraph], figures, (400, 200), cv_img=cv_img)

        # Assert
        assert len(result["regions"]) == 1
        region = result["regions"][0]
        assert region["type"] == "TEXT", f"White background should remain TEXT. Got: {region['type']}"
        assert region["label"] == "plain text"

    def test_paragraphs_to_layout_no_image(self) -> None:
        """cv_img=None → 従来通り TEXT のまま（後方互換）。"""
        from src.layout.detector import paragraphs_to_layout

        # Arrange: cv_img なし
        paragraph = MockParagraph(box=[0, 0, 200, 100])
        figures = []

        # Act
        result = paragraphs_to_layout([paragraph], figures, (400, 200))

        # Assert: cv_img=None なのでデフォルト TEXT
        assert len(result["regions"]) == 1
        region = result["regions"][0]
        assert region["type"] == "TEXT", f"No image should keep TEXT. Got: {region['type']}"
        assert region["label"] == "plain text"

    def test_paragraphs_to_layout_title_not_checked(self) -> None:
        """section_headings role → TITLE のまま（灰色チェックしない）。"""
        import numpy as np

        from src.layout.detector import paragraphs_to_layout

        # Arrange: 灰色画像でも role=section_headings なら TITLE
        cv_img = np.full((200, 400, 3), fill_value=180, dtype=np.uint8)
        paragraph = MockParagraph(box=[0, 0, 200, 100], role="section_headings")
        figures = []

        # Act
        result = paragraphs_to_layout([paragraph], figures, (400, 200), cv_img=cv_img)

        # Assert
        assert len(result["regions"]) == 1
        region = result["regions"][0]
        assert region["type"] == "TITLE", f"section_headings should remain TITLE. Got: {region['type']}"
        assert region["label"] == "section_headings"

    def test_paragraphs_to_layout_wide_aspect_ratio(self) -> None:
        """aspect_ratio > 8.0 の TEXT → 灰色背景でも CODE にならない。"""
        import numpy as np

        from src.layout.detector import paragraphs_to_layout

        # Arrange: 灰色画像、横長（幅=900, 高さ=100 → aspect_ratio=9.0 > 8.0）
        cv_img = np.full((200, 1000, 3), fill_value=180, dtype=np.uint8)
        paragraph = MockParagraph(box=[0, 0, 900, 100])  # aspect_ratio = 9.0
        figures = []

        # Act
        result = paragraphs_to_layout([paragraph], figures, (1000, 200), cv_img=cv_img)

        # Assert: アスペクト比が高すぎるため CODE にならない
        assert len(result["regions"]) == 1
        region = result["regions"][0]
        assert region["type"] == "TEXT", f"Wide aspect ratio (>8.0) should remain TEXT. Got: {region['type']}"


class TestDetectGrayBackgroundImmutability:
    """immutable パターンを検証する。"""

    def test_input_image_not_modified(self) -> None:
        """入力画像が変更されないことを検証。"""
        from src.layout.code_detector import detect_gray_background

        # Arrange
        img = np.full((100, 100, 3), fill_value=180, dtype=np.uint8)
        original_img = img.copy()
        bbox = [0, 0, 100, 100]

        # Act
        detect_gray_background(img, bbox)

        # Assert: 元の画像は変更されない
        assert np.array_equal(img, original_img), "Input image should not be modified by detect_gray_background"

    def test_input_bbox_not_modified(self) -> None:
        """入力 bbox が変更されないことを検証。"""
        from src.layout.code_detector import detect_gray_background

        # Arrange
        img = np.full((100, 100, 3), fill_value=180, dtype=np.uint8)
        bbox = [10, 20, 80, 90]
        original_bbox = bbox.copy()

        # Act
        detect_gray_background(img, bbox)

        # Assert: 元の bbox は変更されない
        assert bbox == original_bbox, f"Input bbox should not be modified. Expected {original_bbox}, got {bbox}"
