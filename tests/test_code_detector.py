"""Tests for src.layout.code_detector - code block detection.

Phase 2 RED tests for US1 - Gray background code block auto-detection.
Phase 3 RED tests for US2/US3 - Text analysis code detection.
Phase 4 RED tests for US4 - Fragment code block merging.

Detection Rules:
| Condition | Result |
|-----------|--------|
| Gray background (threshold >= 0.7) | TEXT -> CODE |
| White background | TEXT (unchanged) |
| Black background | TEXT (unchanged) |
| Aspect ratio > 8.0 (wide strip) | TEXT (unchanged, even if gray) |
| cv_img=None (backward compat) | TEXT (unchanged) |
| None image / invalid bbox | False (safe fallback) |
| Symbol ratio > 0.08 (code text) | TEXT/FIGURE -> CODE |
| Keyword count >= 2 (code keywords) | TEXT/FIGURE -> CODE |
| OR condition: symbol OR keyword | Either triggers CODE |
| TITLE (section_headings) | Skip text analysis |
| Japanese text (no symbols/keywords) | TEXT (unchanged) |
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


# ============================================================
# Phase 3: US2 + US3 - Text analysis code detection
# ============================================================


def make_figure_mock(
    box: list[int],
    paragraphs: list | None = None,
) -> MagicMock:
    """Create a mock yomitoku figure object with paragraphs.

    Args:
        box: [x1, y1, x2, y2] bounding box
        paragraphs: List of mock paragraph objects within the figure
    """
    f = MagicMock()
    f.box = box
    if paragraphs is not None:
        f.paragraphs = paragraphs
    else:
        # No paragraphs attribute by default
        del f.paragraphs
    return f


# ============================================================
# T032: calc_symbol_ratio() tests
# ============================================================


class TestCalcSymbolRatio:
    """calc_symbol_ratio() should compute the ratio of code symbols in text."""

    def test_code_text_high_ratio(self) -> None:
        """Code text like 'class Foo { }' should return a high symbol ratio."""
        from src.layout.code_detector import calc_symbol_ratio

        result = calc_symbol_ratio("class Foo { }")

        assert result > 0.08, f"Code text should have symbol ratio > 0.08, got {result}"

    def test_curly_braces_and_semicolons(self) -> None:
        """Text with many symbols: 'if (x > 0) { return x; }' should have high ratio."""
        from src.layout.code_detector import calc_symbol_ratio

        result = calc_symbol_ratio("if (x > 0) { return x; }")

        assert result > 0.08, f"Symbol-heavy code should have ratio > 0.08, got {result}"

    def test_japanese_text_zero_ratio(self) -> None:
        """Japanese text should have zero or near-zero symbol ratio."""
        from src.layout.code_detector import calc_symbol_ratio

        result = calc_symbol_ratio("今日は良い天気です。明日も晴れるでしょう。")

        assert result == 0.0, f"Japanese text should have 0.0 symbol ratio, got {result}"

    def test_empty_string_returns_zero(self) -> None:
        """Empty string should return 0.0."""
        from src.layout.code_detector import calc_symbol_ratio

        result = calc_symbol_ratio("")

        assert result == 0.0, "Empty string should return 0.0"

    def test_only_symbols(self) -> None:
        """Text of only symbols should return a high ratio (close to 1.0)."""
        from src.layout.code_detector import calc_symbol_ratio

        result = calc_symbol_ratio("{}();=<>[]")

        assert result > 0.5, f"All-symbol text should have very high ratio, got {result}"

    def test_mixed_code_and_text(self) -> None:
        """Mixed code: 'public void main(String[] args) {' should have moderate ratio."""
        from src.layout.code_detector import calc_symbol_ratio

        result = calc_symbol_ratio("public void main(String[] args) {")

        assert result > 0.0, f"Mixed code should have positive ratio, got {result}"

    def test_returns_float(self) -> None:
        """Return type should be float."""
        from src.layout.code_detector import calc_symbol_ratio

        result = calc_symbol_ratio("hello world")

        assert isinstance(result, float), f"Expected float, got {type(result)}"

    def test_special_chars_unicode(self) -> None:
        """Unicode and emoji text without code symbols should return 0.0."""
        from src.layout.code_detector import calc_symbol_ratio

        result = calc_symbol_ratio("Hello World")

        assert result == 0.0, f"Plain text should have 0.0 ratio, got {result}"

    def test_hash_and_at_symbols(self) -> None:
        """Text with # and @ symbols (used in code) should count."""
        from src.layout.code_detector import calc_symbol_ratio

        result = calc_symbol_ratio("#include <stdio.h>")

        assert result > 0.0, f"Text with # and < > should have positive ratio, got {result}"


# ============================================================
# T033: count_code_keywords() tests
# ============================================================


class TestCountCodeKeywords:
    """count_code_keywords() should count programming keyword occurrences."""

    def test_class_extends_detected(self) -> None:
        """'class Foo extends Bar' should detect >= 2 keywords (class, extends)."""
        from src.layout.code_detector import count_code_keywords

        result = count_code_keywords("class Foo extends Bar")

        assert result >= 2, f"'class Foo extends Bar' should have >= 2 keywords, got {result}"

    def test_japanese_text_zero_keywords(self) -> None:
        """Japanese text should have 0 keywords."""
        from src.layout.code_detector import count_code_keywords

        result = count_code_keywords("日本語テキストです")

        assert result == 0, f"Japanese text should have 0 keywords, got {result}"

    def test_python_keywords(self) -> None:
        """Python keywords: def, import should be detected."""
        from src.layout.code_detector import count_code_keywords

        result = count_code_keywords("def hello():\n    import os")

        assert result >= 2, f"Python code should have >= 2 keywords (def, import), got {result}"

    def test_go_keywords(self) -> None:
        """Go keywords: func, package should be detected."""
        from src.layout.code_detector import count_code_keywords

        result = count_code_keywords("package main\nfunc main() {}")

        assert result >= 2, f"Go code should have >= 2 keywords (func, package), got {result}"

    def test_rust_keywords(self) -> None:
        """Rust keywords: fn, impl should be detected."""
        from src.layout.code_detector import count_code_keywords

        result = count_code_keywords("impl MyStruct {\n    fn new() -> Self {}")

        assert result >= 2, f"Rust code should have >= 2 keywords (fn, impl), got {result}"

    def test_sql_case_insensitive(self) -> None:
        """SQL keywords should be case insensitive: SELECT, WHERE."""
        from src.layout.code_detector import count_code_keywords

        result = count_code_keywords("SELECT * FROM users WHERE id = 1")

        assert result >= 2, f"SQL should have >= 2 keywords (SELECT, WHERE), got {result}"

    def test_empty_string_returns_zero(self) -> None:
        """Empty string should return 0."""
        from src.layout.code_detector import count_code_keywords

        result = count_code_keywords("")

        assert result == 0, "Empty string should return 0 keywords"

    def test_returns_int(self) -> None:
        """Return type should be int."""
        from src.layout.code_detector import count_code_keywords

        result = count_code_keywords("some text")

        assert isinstance(result, int), f"Expected int, got {type(result)}"

    def test_javascript_keywords(self) -> None:
        """JavaScript keywords: const, function, => should be detected."""
        from src.layout.code_detector import count_code_keywords

        result = count_code_keywords("const handler = function(event) { return event; }")

        assert result >= 2, f"JS code should have >= 2 keywords, got {result}"

    def test_shell_keywords(self) -> None:
        """Shell keywords: #!/bin/, echo should be detected."""
        from src.layout.code_detector import count_code_keywords

        result = count_code_keywords("#!/bin/bash\necho 'hello'")

        assert result >= 2, f"Shell code should have >= 2 keywords, got {result}"

    def test_cpp_keywords(self) -> None:
        """C/C++ keywords: #include, std:: should be detected."""
        from src.layout.code_detector import count_code_keywords

        result = count_code_keywords('#include <iostream>\nstd::cout << "hello";')

        assert result >= 2, f"C++ code should have >= 2 keywords, got {result}"


# ============================================================
# T034: detect_code_by_text() OR condition tests
# ============================================================


class TestDetectCodeByTextOrCondition:
    """detect_code_by_text() uses OR condition: symbol ratio OR keyword count."""

    def test_symbol_ratio_only_returns_true(self) -> None:
        """High symbol ratio alone (no keywords) should return True."""
        from src.layout.code_detector import detect_code_by_text

        # Lots of symbols but no language keywords
        result = detect_code_by_text("{{{{}}}}()()()()")

        assert result is True, "High symbol ratio alone should trigger CODE"

    def test_keyword_only_returns_true(self) -> None:
        """Enough keywords alone (low symbol ratio) should return True."""
        from src.layout.code_detector import detect_code_by_text

        # Keywords but few code symbols
        result = detect_code_by_text("class Foo extends Bar implements Baz")

        assert result is True, "Keyword count alone should trigger CODE"

    def test_both_false_returns_false(self) -> None:
        """Neither symbol ratio nor keywords met should return False."""
        from src.layout.code_detector import detect_code_by_text

        result = detect_code_by_text("今日は良い天気です")

        assert result is False, "Neither condition met should return False"

    def test_both_true_returns_true(self) -> None:
        """Both conditions met should return True."""
        from src.layout.code_detector import detect_code_by_text

        result = detect_code_by_text("public class Foo { private int bar; }")

        assert result is True, "Both conditions met should return True"

    def test_returns_bool(self) -> None:
        """Return type should be bool."""
        from src.layout.code_detector import detect_code_by_text

        result = detect_code_by_text("some text")

        assert isinstance(result, bool), f"Expected bool, got {type(result)}"

    def test_empty_string_returns_false(self) -> None:
        """Empty string should return False."""
        from src.layout.code_detector import detect_code_by_text

        result = detect_code_by_text("")

        assert result is False, "Empty string should return False"

    def test_custom_thresholds(self) -> None:
        """Custom thresholds should be respected."""
        from src.layout.code_detector import detect_code_by_text

        # Very high thresholds - should return False for normal code
        result = detect_code_by_text(
            "class Foo { }",
            sym_threshold=0.9,
            kw_threshold=10,
        )

        assert result is False, "Very high thresholds should make normal code return False"

    def test_none_input_returns_false(self) -> None:
        """None input should return False without error."""
        from src.layout.code_detector import detect_code_by_text

        # None should be handled gracefully
        result = detect_code_by_text(None)

        assert result is False, "None input should return False"


# ============================================================
# T035: FIGURE -> CODE reclassification test
# ============================================================


class TestFigureToCodeReclassification:
    """FIGURE with code-like paragraph text should be reclassified to CODE."""

    def test_figure_with_code_paragraphs_becomes_code(self) -> None:
        """FIGURE containing code text in paragraphs should become CODE."""
        from src.layout.detector import paragraphs_to_layout

        # Create a figure with code-like paragraphs
        code_paragraph = make_paragraph_mock(
            box=[20, 20, 180, 80],
            role="plain text",
            contents="public class Foo { private int bar; }",
        )
        figure = make_figure_mock(
            box=[10, 10, 190, 90],
            paragraphs=[code_paragraph],
        )

        result = paragraphs_to_layout(
            [],
            [figure],
            (200, 100),
        )

        regions = result["regions"]
        assert len(regions) == 1
        assert regions[0]["type"] == "CODE", "FIGURE with code-like paragraphs should be reclassified to CODE"

    def test_figure_without_code_stays_figure(self) -> None:
        """FIGURE without code text should remain FIGURE."""
        from src.layout.detector import paragraphs_to_layout

        # Non-code paragraph in figure
        text_paragraph = make_paragraph_mock(
            box=[20, 20, 180, 80],
            role="plain text",
            contents="これはフローチャートの説明です",
        )
        figure = make_figure_mock(
            box=[10, 10, 190, 90],
            paragraphs=[text_paragraph],
        )

        result = paragraphs_to_layout(
            [],
            [figure],
            (200, 100),
        )

        regions = result["regions"]
        assert len(regions) == 1
        assert regions[0]["type"] == "FIGURE", "FIGURE without code text should remain FIGURE"

    def test_figure_without_paragraphs_stays_figure(self) -> None:
        """FIGURE with no paragraphs attribute should remain FIGURE."""
        from src.layout.detector import paragraphs_to_layout

        figure = make_figure_mock(box=[10, 10, 190, 90])

        result = paragraphs_to_layout(
            [],
            [figure],
            (200, 100),
        )

        regions = result["regions"]
        assert len(regions) == 1
        assert regions[0]["type"] == "FIGURE", "FIGURE without paragraphs attribute should remain FIGURE"

    def test_figure_code_region_has_code_label(self) -> None:
        """Reclassified FIGURE->CODE should have label='code'."""
        from src.layout.detector import paragraphs_to_layout

        code_paragraph = make_paragraph_mock(
            box=[20, 20, 180, 80],
            role="plain text",
            contents="import java.util.List;\nclass Foo extends Bar {",
        )
        figure = make_figure_mock(
            box=[10, 10, 190, 90],
            paragraphs=[code_paragraph],
        )

        result = paragraphs_to_layout(
            [],
            [figure],
            (200, 100),
        )

        regions = result["regions"]
        assert regions[0]["label"] == "code", "Reclassified FIGURE->CODE should have label='code'"


# ============================================================
# T036: TEXT -> CODE reclassification test
# ============================================================


class TestTextToCodeReclassification:
    """TEXT with code-like contents should be reclassified to CODE via text analysis."""

    def test_text_with_code_contents_becomes_code(self) -> None:
        """TEXT paragraph with code contents should become CODE."""
        from src.layout.detector import paragraphs_to_layout

        paragraph = make_paragraph_mock(
            box=[10, 10, 190, 90],
            role="plain text",
            contents="public static void main(String[] args) {",
        )

        # No cv_img: gray detection won't trigger, only text analysis
        result = paragraphs_to_layout(
            [paragraph],
            [],
            (200, 100),
        )

        regions = result["regions"]
        assert len(regions) == 1
        assert regions[0]["type"] == "CODE", "TEXT with code contents should be reclassified to CODE via text analysis"

    def test_text_with_normal_japanese_stays_text(self) -> None:
        """Normal Japanese text should remain TEXT."""
        from src.layout.detector import paragraphs_to_layout

        paragraph = make_paragraph_mock(
            box=[10, 10, 190, 90],
            role="plain text",
            contents="プログラミングの基礎を学ぶことは重要です。",
        )

        result = paragraphs_to_layout(
            [paragraph],
            [],
            (200, 100),
        )

        regions = result["regions"]
        assert len(regions) == 1
        assert regions[0]["type"] == "TEXT", "Normal Japanese text should remain TEXT"

    def test_text_code_region_has_code_label(self) -> None:
        """Reclassified TEXT->CODE should have label='code'."""
        from src.layout.detector import paragraphs_to_layout

        paragraph = make_paragraph_mock(
            box=[10, 10, 190, 90],
            role="plain text",
            contents="def calculate(x, y):\n    return x + y",
        )

        result = paragraphs_to_layout(
            [paragraph],
            [],
            (200, 100),
        )

        regions = result["regions"]
        assert regions[0]["label"] == "code", "Reclassified TEXT->CODE should have label='code'"


# ============================================================
# T037: TITLE skip test (section_headings skip text analysis)
# ============================================================


class TestTitleSkipsTextAnalysis:
    """TITLE (section_headings) should skip text analysis and stay TITLE."""

    def test_title_with_code_like_text_stays_title(self) -> None:
        """TITLE with code-like text should NOT be reclassified to CODE."""
        from src.layout.detector import paragraphs_to_layout

        # Even if the heading text looks like code, TITLE should be skipped
        paragraph = make_paragraph_mock(
            box=[10, 10, 190, 40],
            role="section_headings",
            contents="class MyClass implements Interface {",
        )

        result = paragraphs_to_layout(
            [paragraph],
            [],
            (200, 100),
        )

        regions = result["regions"]
        assert len(regions) == 1
        assert regions[0]["type"] == "TITLE", "TITLE should not be reclassified to CODE even with code-like text"

    def test_title_label_preserved(self) -> None:
        """TITLE should preserve its label as 'section_headings'."""
        from src.layout.detector import paragraphs_to_layout

        paragraph = make_paragraph_mock(
            box=[10, 10, 190, 40],
            role="section_headings",
            contents="def function_name():",
        )

        result = paragraphs_to_layout(
            [paragraph],
            [],
            (200, 100),
        )

        regions = result["regions"]
        assert regions[0]["label"] == "section_headings", "TITLE label should remain 'section_headings'"


# ============================================================
# T038: Japanese false positive test
# ============================================================


class TestJapaneseFalsePositive:
    """Normal Japanese text should NOT be reclassified to CODE."""

    def test_general_japanese_prose_stays_text(self) -> None:
        """General Japanese prose should remain TEXT."""
        from src.layout.detector import paragraphs_to_layout

        paragraph = make_paragraph_mock(
            box=[10, 10, 190, 90],
            role="plain text",
            contents="この章ではオブジェクト指向プログラミングの概念について説明します。"
            "クラスとインスタンスの関係を理解することが重要です。",
        )

        result = paragraphs_to_layout(
            [paragraph],
            [],
            (200, 100),
        )

        regions = result["regions"]
        assert regions[0]["type"] == "TEXT", "General Japanese prose should remain TEXT, not be reclassified to CODE"

    def test_japanese_with_technical_terms_stays_text(self) -> None:
        """Japanese text with technical terms (not code) should remain TEXT."""
        from src.layout.detector import paragraphs_to_layout

        paragraph = make_paragraph_mock(
            box=[10, 10, 190, 90],
            role="plain text",
            contents="変数の宣言とメソッドの定義について学びます。インターフェースの実装方法も解説します。",
        )

        result = paragraphs_to_layout(
            [paragraph],
            [],
            (200, 100),
        )

        regions = result["regions"]
        assert regions[0]["type"] == "TEXT", "Japanese text with technical terms should remain TEXT"

    def test_japanese_punctuation_not_counted_as_symbols(self) -> None:
        """Japanese punctuation (。、「」) should not trigger symbol detection."""
        from src.layout.code_detector import calc_symbol_ratio

        result = calc_symbol_ratio("「こんにちは」と言いました。「ありがとう」と答えました。")

        assert result == 0.0, f"Japanese punctuation should not count as code symbols, got {result}"

    def test_figure_with_japanese_caption_stays_figure(self) -> None:
        """FIGURE with Japanese caption (not code) should remain FIGURE."""
        from src.layout.detector import paragraphs_to_layout

        caption_paragraph = make_paragraph_mock(
            box=[20, 20, 180, 80],
            role="plain text",
            contents="図2.5 システム構成の概要図",
        )
        figure = make_figure_mock(
            box=[10, 10, 190, 90],
            paragraphs=[caption_paragraph],
        )

        result = paragraphs_to_layout(
            [],
            [figure],
            (200, 100),
        )

        regions = result["regions"]
        assert regions[0]["type"] == "FIGURE", "FIGURE with Japanese caption should remain FIGURE"


# ============================================================
# T039: Multi-language keyword test
# ============================================================


class TestMultiLanguageKeywords:
    """Keywords from multiple programming languages should be detected."""

    def test_python_def_import(self) -> None:
        """Python keywords: def, import should be counted."""
        from src.layout.code_detector import count_code_keywords

        result = count_code_keywords("def process(data):\n    import json")

        assert result >= 2, f"Python def/import should count >= 2, got {result}"

    def test_go_func_package(self) -> None:
        """Go keywords: func, package should be counted."""
        from src.layout.code_detector import count_code_keywords

        result = count_code_keywords("package main\n\nfunc Hello() string {")

        assert result >= 2, f"Go func/package should count >= 2, got {result}"

    def test_rust_fn_impl(self) -> None:
        """Rust keywords: fn, impl should be counted."""
        from src.layout.code_detector import count_code_keywords

        result = count_code_keywords("impl Display for Point {\n    fn fmt(&self)")

        assert result >= 2, f"Rust fn/impl should count >= 2, got {result}"

    def test_java_class_public_void(self) -> None:
        """Java keywords: class, public, void should be counted."""
        from src.layout.code_detector import count_code_keywords

        result = count_code_keywords("public class Main {\n    public void run() {")

        assert result >= 2, f"Java class/public/void should count >= 2, got {result}"

    def test_ruby_require_module(self) -> None:
        """Ruby keywords: require, module should be counted."""
        from src.layout.code_detector import count_code_keywords

        result = count_code_keywords("require 'json'\nmodule MyApp")

        assert result >= 2, f"Ruby require/module should count >= 2, got {result}"

    def test_iac_dockerfile_keywords(self) -> None:
        """IaC/Docker keywords: FROM, WORKDIR, RUN should be counted."""
        from src.layout.code_detector import count_code_keywords

        result = count_code_keywords("FROM ubuntu:22.04\nWORKDIR /app\nRUN apt-get update")

        assert result >= 2, f"Dockerfile FROM/WORKDIR/RUN should count >= 2, got {result}"

    def test_sql_select_where_case_insensitive(self) -> None:
        """SQL keywords should work case-insensitively."""
        from src.layout.code_detector import count_code_keywords

        result = count_code_keywords("select * from users where active = true")

        assert result >= 2, f"SQL select/where (lowercase) should count >= 2, got {result}"

    def test_mixed_language_keywords(self) -> None:
        """Mixed language keywords in one text should all be counted."""
        from src.layout.code_detector import count_code_keywords

        # Mix of Python, Java, generic keywords
        result = count_code_keywords("import sys\npublic class Main {\n    return 0;\n}")

        assert result >= 3, f"Mixed language code should have >= 3 keywords, got {result}"


# ============================================================
# Phase 4 RED Tests: US4 - Fragment code block merging
# ============================================================


# ============================================================
# T055: is_code_fragment() tests
# ============================================================


class TestIsCodeFragment:
    """is_code_fragment() identifies short code-like text fragments."""

    def test_closing_brace_is_fragment(self) -> None:
        """Single '}' should be identified as a code fragment."""
        from src.layout.code_detector import is_code_fragment

        result = is_code_fragment("}")

        assert result is True, "Single '}' should be a code fragment"

    def test_opening_brace_is_fragment(self) -> None:
        """Single '{' should be identified as a code fragment."""
        from src.layout.code_detector import is_code_fragment

        result = is_code_fragment("{")

        assert result is True, "Single '{' should be a code fragment"

    def test_ocr_misread_3_is_fragment(self) -> None:
        """'3' (OCR misread of '}') should be identified as a code fragment."""
        from src.layout.code_detector import is_code_fragment

        result = is_code_fragment("3")

        assert result is True, "'3' (OCR misread of '}') should be a code fragment"

    def test_short_code_like_text_is_fragment(self) -> None:
        """Short text with high symbol ratio (< 20 chars) should be fragment."""
        from src.layout.code_detector import is_code_fragment

        result = is_code_fragment("});")

        assert result is True, "Short code-like text '});' should be a code fragment"

    def test_japanese_text_is_not_fragment(self) -> None:
        """Normal Japanese text should NOT be a fragment."""
        from src.layout.code_detector import is_code_fragment

        result = is_code_fragment("日本語テキスト")

        assert result is False, "Japanese text should not be a code fragment"

    def test_long_text_is_not_fragment(self) -> None:
        """Long text (>= 20 chars) should NOT be a fragment even with symbols."""
        from src.layout.code_detector import is_code_fragment

        result = is_code_fragment("This is a normal sentence that is quite long")

        assert result is False, "Long normal text should not be a code fragment"

    def test_empty_string_is_not_fragment(self) -> None:
        """Empty string should NOT be a fragment."""
        from src.layout.code_detector import is_code_fragment

        result = is_code_fragment("")

        assert result is False, "Empty string should not be a code fragment"

    def test_none_input_is_not_fragment(self) -> None:
        """None input should NOT be a fragment."""
        from src.layout.code_detector import is_code_fragment

        result = is_code_fragment(None)

        assert result is False, "None input should not be a code fragment"

    def test_returns_bool(self) -> None:
        """Return type should be bool."""
        from src.layout.code_detector import is_code_fragment

        result = is_code_fragment("}")

        assert isinstance(result, bool), f"Expected bool, got {type(result)}"

    def test_semicolon_is_fragment(self) -> None:
        """Single ';' should be a code fragment."""
        from src.layout.code_detector import is_code_fragment

        result = is_code_fragment(";")

        assert result is True, "Single ';' should be a code fragment"

    def test_short_symbols_bracket_paren(self) -> None:
        """Short symbol combinations like '])' should be fragments."""
        from src.layout.code_detector import is_code_fragment

        result = is_code_fragment("])")

        assert result is True, "Short symbol text '])' should be a code fragment"

    def test_whitespace_only_is_not_fragment(self) -> None:
        """Whitespace-only text should NOT be a fragment."""
        from src.layout.code_detector import is_code_fragment

        result = is_code_fragment("   ")

        assert result is False, "Whitespace-only text should not be a code fragment"


# ============================================================
# T056: merge_code_fragments() adjacent merge test
# ============================================================


def _make_region(
    region_type: str,
    label: str,
    bbox: list[int],
    text: str = "",
    confidence: float = 1.0,
) -> dict:
    """Helper to create a region dict for merge tests."""
    return {
        "type": region_type,
        "label": label,
        "bbox": bbox,
        "confidence": confidence,
        "text": text,
    }


class TestMergeCodeFragmentsAdjacentMerge:
    """Adjacent CODE regions with gap < threshold should be merged."""

    def test_two_adjacent_codes_merged(self) -> None:
        """Two CODE regions with gap < 80px should merge into one CODE."""
        from src.layout.code_detector import merge_code_fragments

        regions = [
            _make_region("CODE", "code", [100, 100, 500, 200], text="line1"),
            _make_region("CODE", "code", [100, 250, 500, 350], text="line2"),
        ]
        # gap = 250 - 200 = 50px < 80px threshold

        result = merge_code_fragments(regions)

        assert len(result) == 1, f"Two adjacent CODEs should merge to 1, got {len(result)}"
        assert result[0]["type"] == "CODE"

    def test_merged_bbox_is_bounding_rect(self) -> None:
        """Merged region bbox should be the bounding rectangle of both."""
        from src.layout.code_detector import merge_code_fragments

        regions = [
            _make_region("CODE", "code", [100, 100, 500, 200]),
            _make_region("CODE", "code", [80, 250, 520, 350]),
        ]

        result = merge_code_fragments(regions)

        assert len(result) == 1
        # Bounding rect: [min(100,80), min(100,250), max(500,520), max(200,350)]
        assert result[0]["bbox"] == [80, 100, 520, 350], (
            f"Merged bbox should be bounding rect [80, 100, 520, 350], got {result[0]['bbox']}"
        )

    def test_three_adjacent_codes_merged(self) -> None:
        """Three adjacent CODE regions should all merge into one."""
        from src.layout.code_detector import merge_code_fragments

        regions = [
            _make_region("CODE", "code", [100, 100, 500, 200]),
            _make_region("CODE", "code", [100, 250, 500, 350]),  # gap 50
            _make_region("CODE", "code", [100, 400, 500, 500]),  # gap 50
        ]

        result = merge_code_fragments(regions)

        assert len(result) == 1, f"Three adjacent CODEs should merge to 1, got {len(result)}"
        assert result[0]["bbox"] == [100, 100, 500, 500]

    def test_single_code_returned_as_is(self) -> None:
        """Single CODE region should be returned unchanged."""
        from src.layout.code_detector import merge_code_fragments

        regions = [
            _make_region("CODE", "code", [100, 100, 500, 200]),
        ]

        result = merge_code_fragments(regions)

        assert len(result) == 1
        assert result[0]["type"] == "CODE"
        assert result[0]["bbox"] == [100, 100, 500, 200]

    def test_empty_list_returns_empty(self) -> None:
        """Empty region list should return empty list."""
        from src.layout.code_detector import merge_code_fragments

        result = merge_code_fragments([])

        assert result == [], f"Empty input should return empty list, got {result}"

    def test_returns_list(self) -> None:
        """Return type should be list."""
        from src.layout.code_detector import merge_code_fragments

        result = merge_code_fragments([])

        assert isinstance(result, list), f"Expected list, got {type(result)}"


# ============================================================
# T057: merge_code_fragments() merge break test (non-CODE in between)
# ============================================================


class TestMergeCodeFragmentsMergeBreak:
    """Non-CODE region between CODEs should break the merge chain."""

    def test_code_text_code_produces_two_codes(self) -> None:
        """CODE + TEXT + CODE should remain as 2 separate CODEs."""
        from src.layout.code_detector import merge_code_fragments

        regions = [
            _make_region("CODE", "code", [100, 100, 500, 200], text="code1"),
            _make_region("TEXT", "plain text", [100, 250, 500, 350], text="Normal text here"),
            _make_region("CODE", "code", [100, 400, 500, 500], text="code2"),
        ]

        result = merge_code_fragments(regions)

        code_regions = [r for r in result if r["type"] == "CODE"]
        assert len(code_regions) == 2, f"CODE+TEXT+CODE should produce 2 separate CODEs, got {len(code_regions)}"

    def test_text_region_preserved(self) -> None:
        """TEXT region between CODEs should be preserved in output."""
        from src.layout.code_detector import merge_code_fragments

        regions = [
            _make_region("CODE", "code", [100, 100, 500, 200]),
            _make_region("TEXT", "plain text", [100, 250, 500, 350], text="Normal text"),
            _make_region("CODE", "code", [100, 400, 500, 500]),
        ]

        result = merge_code_fragments(regions)

        types = [r["type"] for r in result]
        assert "TEXT" in types, "TEXT region should be preserved in output"
        assert len(result) == 3, f"Should have 3 regions (CODE, TEXT, CODE), got {len(result)}"

    def test_code_title_code_not_merged(self) -> None:
        """CODE + TITLE + CODE should not merge through TITLE."""
        from src.layout.code_detector import merge_code_fragments

        regions = [
            _make_region("CODE", "code", [100, 100, 500, 200]),
            _make_region("TITLE", "section_headings", [100, 250, 500, 300], text="Chapter 1"),
            _make_region("CODE", "code", [100, 350, 500, 450]),
        ]

        result = merge_code_fragments(regions)

        code_regions = [r for r in result if r["type"] == "CODE"]
        assert len(code_regions) == 2, "CODE+TITLE+CODE should produce 2 separate CODEs"


# ============================================================
# T058: merge_code_fragments() FRAG merge test
# ============================================================


class TestMergeCodeFragmentsFragMerge:
    """CODE + fragment-like TEXT + CODE should merge into one CODE."""

    def test_code_frag_code_merged(self) -> None:
        """CODE + TEXT(fragment '}') + CODE should merge into 1 CODE."""
        from src.layout.code_detector import merge_code_fragments

        regions = [
            _make_region("CODE", "code", [100, 100, 500, 200], text="if (x > 0) {"),
            _make_region("TEXT", "plain text", [100, 250, 500, 280], text="}"),
            _make_region("CODE", "code", [100, 330, 500, 430], text="return result;"),
        ]

        result = merge_code_fragments(regions)

        code_regions = [r for r in result if r["type"] == "CODE"]
        assert len(code_regions) == 1, f"CODE+FRAG('}}')+ CODE should merge to 1 CODE, got {len(code_regions)}"

    def test_code_frag_ocr_misread_code_merged(self) -> None:
        """CODE + TEXT(fragment '3' OCR misread) + CODE should merge into 1 CODE."""
        from src.layout.code_detector import merge_code_fragments

        regions = [
            _make_region("CODE", "code", [100, 100, 500, 200], text="for (int i = 0;"),
            _make_region("TEXT", "plain text", [100, 250, 500, 280], text="3"),
            _make_region("CODE", "code", [100, 330, 500, 430], text="i++; }"),
        ]

        result = merge_code_fragments(regions)

        code_regions = [r for r in result if r["type"] == "CODE"]
        assert len(code_regions) == 1, f"CODE+FRAG('3')+CODE should merge to 1 CODE, got {len(code_regions)}"

    def test_frag_merged_bbox_covers_all(self) -> None:
        """Merged CODE (with FRAG) bbox should cover all three regions."""
        from src.layout.code_detector import merge_code_fragments

        regions = [
            _make_region("CODE", "code", [100, 100, 500, 200], text="code1"),
            _make_region("TEXT", "plain text", [120, 250, 480, 280], text="}"),
            _make_region("CODE", "code", [90, 330, 510, 430], text="code2"),
        ]

        result = merge_code_fragments(regions)

        code_regions = [r for r in result if r["type"] == "CODE"]
        assert len(code_regions) == 1
        # Bounding rect: [min(100,120,90), min(100,250,330), max(500,480,510), max(200,280,430)]
        assert code_regions[0]["bbox"] == [90, 100, 510, 430], (
            f"Merged bbox should cover all 3 regions, got {code_regions[0]['bbox']}"
        )

    def test_code_frag_brace_opening_code_merged(self) -> None:
        """CODE + TEXT(fragment '{') + CODE should merge."""
        from src.layout.code_detector import merge_code_fragments

        regions = [
            _make_region("CODE", "code", [100, 100, 500, 200], text="class Foo"),
            _make_region("TEXT", "plain text", [100, 250, 500, 280], text="{"),
            _make_region("CODE", "code", [100, 330, 500, 430], text="int x = 1;"),
        ]

        result = merge_code_fragments(regions)

        code_regions = [r for r in result if r["type"] == "CODE"]
        assert len(code_regions) == 1, "CODE+FRAG('{')+CODE should merge to 1 CODE"

    def test_non_fragment_text_breaks_merge(self) -> None:
        """CODE + TEXT(long Japanese, not fragment) + CODE should NOT merge."""
        from src.layout.code_detector import merge_code_fragments

        regions = [
            _make_region("CODE", "code", [100, 100, 500, 200], text="code1"),
            _make_region(
                "TEXT",
                "plain text",
                [100, 250, 500, 350],
                text="これはコードではない通常のテキストです。長い日本語の文章が続きます。",
            ),
            _make_region("CODE", "code", [100, 400, 500, 500], text="code2"),
        ]

        result = merge_code_fragments(regions)

        code_regions = [r for r in result if r["type"] == "CODE"]
        assert len(code_regions) == 2, "CODE + long TEXT (not fragment) + CODE should produce 2 separate CODEs"


# ============================================================
# T059: merge_code_fragments() gap exceeded test
# ============================================================


class TestMergeCodeFragmentsGapExceeded:
    """CODE regions with gap > threshold should NOT be merged."""

    def test_large_gap_not_merged(self) -> None:
        """CODE + CODE with gap > 80px should remain as 2 separate CODEs."""
        from src.layout.code_detector import merge_code_fragments

        regions = [
            _make_region("CODE", "code", [100, 100, 500, 200], text="code1"),
            _make_region("CODE", "code", [100, 350, 500, 450], text="code2"),
        ]
        # gap = 350 - 200 = 150px > 80px threshold

        result = merge_code_fragments(regions)

        code_regions = [r for r in result if r["type"] == "CODE"]
        assert len(code_regions) == 2, f"CODE+CODE with gap 150px > 80px should remain 2 CODEs, got {len(code_regions)}"

    def test_custom_gap_threshold(self) -> None:
        """Custom gap_threshold should be respected."""
        from src.layout.code_detector import merge_code_fragments

        regions = [
            _make_region("CODE", "code", [100, 100, 500, 200]),
            _make_region("CODE", "code", [100, 250, 500, 350]),
        ]
        # gap = 50px. With threshold=30, should NOT merge

        result = merge_code_fragments(regions, gap_threshold=30)

        code_regions = [r for r in result if r["type"] == "CODE"]
        assert len(code_regions) == 2, "CODE+CODE with gap 50px > custom threshold 30px should remain 2 CODEs"

    def test_exact_threshold_boundary(self) -> None:
        """Gap exactly at threshold should be handled consistently."""
        from src.layout.code_detector import merge_code_fragments

        regions = [
            _make_region("CODE", "code", [100, 100, 500, 200]),
            _make_region("CODE", "code", [100, 280, 500, 380]),
        ]
        # gap = 280 - 200 = 80px == threshold

        result = merge_code_fragments(regions, gap_threshold=80)

        # At exact boundary, either merge or not is acceptable,
        # but the function must return a valid result
        assert isinstance(result, list), "Should return a list"
        code_regions = [r for r in result if r["type"] == "CODE"]
        assert 1 <= len(code_regions) <= 2, (
            f"At exact threshold boundary, should have 1 or 2 CODEs, got {len(code_regions)}"
        )


# ============================================================
# T060: merge_code_fragments() immutability test
# ============================================================


class TestMergeCodeFragmentsImmutability:
    """merge_code_fragments() must NOT mutate the input list."""

    def test_input_list_not_mutated(self) -> None:
        """Original input list should not be modified."""
        from src.layout.code_detector import merge_code_fragments

        regions = [
            _make_region("CODE", "code", [100, 100, 500, 200]),
            _make_region("CODE", "code", [100, 250, 500, 350]),
        ]
        original_len = len(regions)
        original_regions = [dict(r) for r in regions]

        merge_code_fragments(regions)

        assert len(regions) == original_len, f"Input list length changed from {original_len} to {len(regions)}"
        for i, region in enumerate(regions):
            assert region == original_regions[i], (
                f"Input region at index {i} was mutated: {region} != {original_regions[i]}"
            )

    def test_input_region_dicts_not_mutated(self) -> None:
        """Individual region dicts in input should not be modified."""
        import copy

        from src.layout.code_detector import merge_code_fragments

        regions = [
            _make_region("CODE", "code", [100, 100, 500, 200]),
            _make_region("TEXT", "plain text", [100, 250, 500, 300], text="}"),
            _make_region("CODE", "code", [100, 350, 500, 450]),
        ]
        deep_copy = copy.deepcopy(regions)

        merge_code_fragments(regions)

        for i, region in enumerate(regions):
            assert region == deep_copy[i], f"Input region dict at index {i} was mutated"

    def test_input_bbox_lists_not_mutated(self) -> None:
        """bbox lists inside input regions should not be modified."""
        from src.layout.code_detector import merge_code_fragments

        bbox1 = [100, 100, 500, 200]
        bbox2 = [100, 250, 500, 350]
        original_bbox1 = list(bbox1)
        original_bbox2 = list(bbox2)

        regions = [
            _make_region("CODE", "code", bbox1),
            _make_region("CODE", "code", bbox2),
        ]

        merge_code_fragments(regions)

        assert bbox1 == original_bbox1, f"bbox1 was mutated: {bbox1} != {original_bbox1}"
        assert bbox2 == original_bbox2, f"bbox2 was mutated: {bbox2} != {original_bbox2}"

    def test_result_is_new_list(self) -> None:
        """Result should be a new list, not the same object as input."""
        from src.layout.code_detector import merge_code_fragments

        regions = [
            _make_region("CODE", "code", [100, 100, 500, 200]),
        ]

        result = merge_code_fragments(regions)

        assert result is not regions, "Result should be a new list, not the same object as input"
