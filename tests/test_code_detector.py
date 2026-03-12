"""Tests for src.layout.code_detector - gray background code block detection.

Phase 2 RED tests for US1 - Gray background code block auto-detection.

Detection Rules:
| Condition | Result |
|-----------|--------|
| Gray background (threshold >= 0.7) | TEXT -> CODE |
| White background | TEXT (unchanged) |
| Black background | TEXT (unchanged) |
| Aspect ratio > 8.0 (wide strip) | TEXT (unchanged, even if gray) |
| cv_img=None (backward compat) | TEXT (unchanged) |
| None image / invalid bbox | False (safe fallback) |
"""

from __future__ import annotations

from unittest.mock import MagicMock

import numpy as np

# ============================================================
# Fixtures: image generation helpers
# ============================================================


def make_solid_image(color: list[int], height: int = 100, width: int = 200) -> np.ndarray:
    """Create a solid-color BGR image as numpy array."""
    return np.full((height, width, 3), color, dtype=np.uint8)


def make_mixed_gray_image(gray_ratio: float, height: int = 100, width: int = 200) -> np.ndarray:
    """Create an image with a mix of gray and white pixels.

    Args:
        gray_ratio: Fraction of pixels that are gray (0.0 to 1.0)
        height: Image height
        width: Image width

    Returns:
        BGR image where top portion is gray, bottom is white
    """
    img = np.full((height, width, 3), [255, 255, 255], dtype=np.uint8)
    gray_rows = int(height * gray_ratio)
    img[:gray_rows, :] = [128, 128, 128]
    return img


def make_paragraph_mock(
    box: list[int],
    role: str = "plain text",
    contents: str = "sample text",
) -> MagicMock:
    """Create a mock yomitoku paragraph object."""
    p = MagicMock()
    p.box = box
    p.role = role
    p.contents = contents
    return p


# ============================================================
# T009: detect_gray_background() basic tests
# ============================================================


class TestDetectGrayBackgroundBasic:
    """Gray/white/black image detection basic tests."""

    def test_gray_image_returns_true(self) -> None:
        """Gray image (RGB 128,128,128) should be detected as gray background."""
        from src.layout.code_detector import detect_gray_background

        gray_img = make_solid_image([128, 128, 128])
        bbox = [0, 0, 200, 100]

        result = detect_gray_background(gray_img, bbox)

        assert result is True, "Solid gray image should be detected as gray background"

    def test_white_image_returns_false(self) -> None:
        """White image (RGB 255,255,255) should NOT be detected as gray background."""
        from src.layout.code_detector import detect_gray_background

        white_img = make_solid_image([255, 255, 255])
        bbox = [0, 0, 200, 100]

        result = detect_gray_background(white_img, bbox)

        assert result is False, "White image should not be detected as gray background"

    def test_black_image_returns_false(self) -> None:
        """Black image (RGB 0,0,0) should NOT be detected as gray background."""
        from src.layout.code_detector import detect_gray_background

        black_img = make_solid_image([0, 0, 0])
        bbox = [0, 0, 200, 100]

        result = detect_gray_background(black_img, bbox)

        assert result is False, "Black image should not be detected as gray background"

    def test_light_gray_image_returns_true(self) -> None:
        """Light gray (RGB 180,180,180) within V range should be detected."""
        from src.layout.code_detector import detect_gray_background

        light_gray_img = make_solid_image([180, 180, 180])
        bbox = [0, 0, 200, 100]

        result = detect_gray_background(light_gray_img, bbox)

        assert result is True, "Light gray image should be detected as gray background"

    def test_dark_gray_image_returns_true(self) -> None:
        """Dark gray (RGB 60,60,60) within V range should be detected."""
        from src.layout.code_detector import detect_gray_background

        dark_gray_img = make_solid_image([60, 60, 60])
        bbox = [0, 0, 200, 100]

        result = detect_gray_background(dark_gray_img, bbox)

        assert result is True, "Dark gray image should be detected as gray background"

    def test_colored_image_returns_false(self) -> None:
        """Colored image (high saturation) should NOT be detected as gray."""
        from src.layout.code_detector import detect_gray_background

        red_img = make_solid_image([0, 0, 255])  # BGR: pure red
        bbox = [0, 0, 200, 100]

        result = detect_gray_background(red_img, bbox)

        assert result is False, "Colored image should not be detected as gray background"


# ============================================================
# T010: detect_gray_background() threshold boundary tests
# ============================================================


class TestDetectGrayBackgroundThreshold:
    """Threshold boundary tests around 0.7."""

    def test_gray_ratio_above_threshold_returns_true(self) -> None:
        """Image with 80% gray pixels should exceed default threshold (0.7)."""
        from src.layout.code_detector import detect_gray_background

        img = make_mixed_gray_image(0.8)
        bbox = [0, 0, 200, 100]

        result = detect_gray_background(img, bbox, threshold=0.7)

        assert result is True, "80% gray ratio should exceed 0.7 threshold"

    def test_gray_ratio_below_threshold_returns_false(self) -> None:
        """Image with 50% gray pixels should NOT exceed default threshold (0.7)."""
        from src.layout.code_detector import detect_gray_background

        img = make_mixed_gray_image(0.5)
        bbox = [0, 0, 200, 100]

        result = detect_gray_background(img, bbox, threshold=0.7)

        assert result is False, "50% gray ratio should not exceed 0.7 threshold"

    def test_gray_ratio_at_threshold_boundary(self) -> None:
        """Image with exactly 70% gray should be at the boundary (threshold=0.7)."""
        from src.layout.code_detector import detect_gray_background

        img = make_mixed_gray_image(0.7)
        bbox = [0, 0, 200, 100]

        # At exactly threshold, result depends on implementation (>= vs >)
        # We just verify it returns a bool without error
        result = detect_gray_background(img, bbox, threshold=0.7)

        assert isinstance(result, bool), "Should return a boolean"

    def test_custom_threshold_low(self) -> None:
        """With low threshold (0.3), 50% gray should be detected."""
        from src.layout.code_detector import detect_gray_background

        img = make_mixed_gray_image(0.5)
        bbox = [0, 0, 200, 100]

        result = detect_gray_background(img, bbox, threshold=0.3)

        assert result is True, "50% gray should exceed 0.3 threshold"

    def test_custom_threshold_high(self) -> None:
        """With high threshold (0.95), 80% gray should NOT be detected."""
        from src.layout.code_detector import detect_gray_background

        img = make_mixed_gray_image(0.8)
        bbox = [0, 0, 200, 100]

        result = detect_gray_background(img, bbox, threshold=0.95)

        assert result is False, "80% gray should not exceed 0.95 threshold"


# ============================================================
# T011: detect_gray_background() input validation tests
# ============================================================


class TestDetectGrayBackgroundValidation:
    """Input validation: None image, out-of-range bbox, zero-size bbox."""

    def test_none_image_returns_false(self) -> None:
        """None image should return False safely."""
        from src.layout.code_detector import detect_gray_background

        result = detect_gray_background(None, [0, 0, 100, 100])

        assert result is False, "None image should return False"

    def test_empty_bbox_returns_false(self) -> None:
        """Empty bbox list should return False safely."""
        from src.layout.code_detector import detect_gray_background

        gray_img = make_solid_image([128, 128, 128])

        result = detect_gray_background(gray_img, [])

        assert result is False, "Empty bbox should return False"

    def test_zero_size_bbox_returns_false(self) -> None:
        """Zero-size bbox (x1==x2 or y1==y2) should return False safely."""
        from src.layout.code_detector import detect_gray_background

        gray_img = make_solid_image([128, 128, 128])

        result = detect_gray_background(gray_img, [50, 50, 50, 50])

        assert result is False, "Zero-size bbox should return False"

    def test_negative_bbox_returns_false(self) -> None:
        """Negative bbox coordinates should return False safely."""
        from src.layout.code_detector import detect_gray_background

        gray_img = make_solid_image([128, 128, 128])

        result = detect_gray_background(gray_img, [-10, -10, -5, -5])

        assert result is False, "Negative bbox should return False"

    def test_bbox_exceeding_image_size_returns_result(self) -> None:
        """Bbox exceeding image dimensions should be clipped and still work."""
        from src.layout.code_detector import detect_gray_background

        gray_img = make_solid_image([128, 128, 128], height=100, width=200)
        # bbox larger than image
        bbox = [0, 0, 500, 500]

        result = detect_gray_background(gray_img, bbox)

        # Should clip to image bounds and detect gray
        assert result is True, "Bbox exceeding image should be clipped and still detect gray"

    def test_inverted_bbox_returns_false(self) -> None:
        """Inverted bbox (x1 > x2) should return False safely."""
        from src.layout.code_detector import detect_gray_background

        gray_img = make_solid_image([128, 128, 128])

        result = detect_gray_background(gray_img, [100, 100, 50, 50])

        assert result is False, "Inverted bbox should return False"


# ============================================================
# T012: Aspect ratio filter test (in paragraphs_to_layout)
# ============================================================


class TestAspectRatioFilter:
    """Wide strip regions (aspect ratio > 8.0) should NOT become CODE."""

    def test_wide_strip_gray_region_stays_text(self) -> None:
        """A very wide gray region (ratio > 8) should remain TEXT, not CODE.

        Note: The aspect ratio filter is in paragraphs_to_layout(), NOT in
        detect_gray_background(). So this tests paragraphs_to_layout() behavior.
        """
        from src.layout.detector import paragraphs_to_layout

        # Create a wide strip region: 800px wide, 30px tall -> ratio = 26.7
        wide_paragraph = make_paragraph_mock(
            box=[0, 0, 800, 30],
            role="plain text",
            contents="list 2.5 summary",
        )

        # Create a gray image where the wide strip area is gray
        gray_img = make_solid_image([128, 128, 128], height=100, width=800)

        result = paragraphs_to_layout(
            [wide_paragraph],
            [],
            (800, 100),
            cv_img=gray_img,
        )

        regions = result["regions"]
        assert len(regions) == 1
        assert regions[0]["type"] == "TEXT", (
            "Wide strip region (aspect ratio > 8) should remain TEXT even with gray background"
        )

    def test_normal_aspect_ratio_gray_region_becomes_code(self) -> None:
        """A normal aspect ratio gray region should become CODE."""
        from src.layout.detector import paragraphs_to_layout

        # Normal aspect ratio: 200px wide, 100px tall -> ratio = 2.0
        normal_paragraph = make_paragraph_mock(
            box=[0, 0, 200, 100],
            role="plain text",
            contents="some code here",
        )

        gray_img = make_solid_image([128, 128, 128], height=100, width=200)

        result = paragraphs_to_layout(
            [normal_paragraph],
            [],
            (200, 100),
            cv_img=gray_img,
        )

        regions = result["regions"]
        assert len(regions) == 1
        assert regions[0]["type"] == "CODE", "Normal aspect ratio gray region should become CODE"


# ============================================================
# T013: paragraphs_to_layout() integration test with cv_img
# ============================================================


class TestParagraphsToLayoutIntegration:
    """Integration test: cv_img provided, gray TEXT becomes CODE."""

    def test_gray_text_becomes_code_with_cv_img(self) -> None:
        """When cv_img is provided and TEXT has gray background, it should become CODE."""
        from src.layout.detector import paragraphs_to_layout

        paragraph = make_paragraph_mock(
            box=[10, 10, 190, 90],
            role="plain text",
            contents="def hello():",
        )

        gray_img = make_solid_image([128, 128, 128], height=100, width=200)

        result = paragraphs_to_layout(
            [paragraph],
            [],
            (200, 100),
            cv_img=gray_img,
        )

        regions = result["regions"]
        assert len(regions) == 1
        assert regions[0]["type"] == "CODE"
        assert regions[0]["label"] == "code"

    def test_white_text_stays_text_with_cv_img(self) -> None:
        """When cv_img is provided but TEXT has white background, it stays TEXT."""
        from src.layout.detector import paragraphs_to_layout

        paragraph = make_paragraph_mock(
            box=[10, 10, 190, 90],
            role="plain text",
            contents="normal text",
        )

        white_img = make_solid_image([255, 255, 255], height=100, width=200)

        result = paragraphs_to_layout(
            [paragraph],
            [],
            (200, 100),
            cv_img=white_img,
        )

        regions = result["regions"]
        assert len(regions) == 1
        assert regions[0]["type"] == "TEXT"
        assert regions[0]["label"] == "plain text"

    def test_title_not_converted_to_code(self) -> None:
        """TITLE (section_headings) should NOT be converted to CODE even on gray background."""
        from src.layout.detector import paragraphs_to_layout

        title_paragraph = make_paragraph_mock(
            box=[10, 10, 190, 40],
            role="section_headings",
            contents="Chapter 1",
        )

        gray_img = make_solid_image([128, 128, 128], height=100, width=200)

        result = paragraphs_to_layout(
            [title_paragraph],
            [],
            (200, 100),
            cv_img=gray_img,
        )

        regions = result["regions"]
        assert len(regions) == 1
        assert regions[0]["type"] == "TITLE", "TITLE should not be converted to CODE"

    def test_code_region_has_correct_bbox(self) -> None:
        """CODE region should preserve original bbox coordinates."""
        from src.layout.detector import paragraphs_to_layout

        paragraph = make_paragraph_mock(
            box=[50, 100, 300, 400],
            role="plain text",
            contents="code block",
        )

        gray_img = make_solid_image([128, 128, 128], height=500, width=400)

        result = paragraphs_to_layout(
            [paragraph],
            [],
            (400, 500),
            cv_img=gray_img,
        )

        regions = result["regions"]
        assert regions[0]["bbox"] == [50, 100, 300, 400]

    def test_multiple_paragraphs_mixed_background(self) -> None:
        """Multiple paragraphs: gray ones become CODE, white ones stay TEXT."""
        from src.layout.detector import paragraphs_to_layout

        # Create an image with top half gray, bottom half white
        img = np.full((200, 300, 3), [255, 255, 255], dtype=np.uint8)
        img[:100, :] = [128, 128, 128]

        p_gray = make_paragraph_mock(
            box=[10, 10, 290, 90],
            role="plain text",
            contents="gray code",
        )
        p_white = make_paragraph_mock(
            box=[10, 110, 290, 190],
            role="plain text",
            contents="white text",
        )

        result = paragraphs_to_layout(
            [p_gray, p_white],
            [],
            (300, 200),
            cv_img=img,
        )

        regions = result["regions"]
        assert len(regions) == 2
        assert regions[0]["type"] == "CODE", "Gray region should become CODE"
        assert regions[1]["type"] == "TEXT", "White region should stay TEXT"


# ============================================================
# T014: paragraphs_to_layout() backward compatibility test
# ============================================================


class TestParagraphsToLayoutBackwardCompat:
    """Backward compatibility: cv_img=None means TEXT stays TEXT."""

    def test_no_cv_img_text_stays_text(self) -> None:
        """Without cv_img, TEXT should remain TEXT (no gray detection)."""
        from src.layout.detector import paragraphs_to_layout

        paragraph = make_paragraph_mock(
            box=[10, 10, 190, 90],
            role="plain text",
            contents="some text",
        )

        # Call without cv_img (backward compatible)
        result = paragraphs_to_layout(
            [paragraph],
            [],
            (200, 100),
        )

        regions = result["regions"]
        assert len(regions) == 1
        assert regions[0]["type"] == "TEXT", "Without cv_img, TEXT should remain TEXT"

    def test_existing_signature_still_works(self) -> None:
        """Original 3-arg signature should still work without error."""
        from src.layout.detector import paragraphs_to_layout

        paragraph = make_paragraph_mock(
            box=[10, 10, 190, 90],
            role="section_headings",
            contents="Title",
        )

        # Original signature: paragraphs_to_layout(paragraphs, figures, page_size)
        result = paragraphs_to_layout(
            [paragraph],
            [],
            (200, 100),
        )

        regions = result["regions"]
        assert len(regions) == 1
        assert regions[0]["type"] == "TITLE"

    def test_cv_img_none_explicit(self) -> None:
        """Explicitly passing cv_img=None should behave same as omitting it."""
        from src.layout.detector import paragraphs_to_layout

        paragraph = make_paragraph_mock(
            box=[10, 10, 190, 90],
            role="plain text",
            contents="text content",
        )

        result = paragraphs_to_layout(
            [paragraph],
            [],
            (200, 100),
            cv_img=None,
        )

        regions = result["regions"]
        assert len(regions) == 1
        assert regions[0]["type"] == "TEXT"
