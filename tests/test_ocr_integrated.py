"""Tests for ocr_integrated module."""

from PIL import Image

from src.ocr_ensemble import create_text_mask, is_garbage
from src.ocr_integrated import ENGINE_PRIORITY, select_best_engine


class TestIsGarbage:
    """Tests for is_garbage function."""

    def test_empty_text_is_garbage(self):
        assert is_garbage("") is True

    def test_normal_japanese_text_is_not_garbage(self):
        text = "これは正常な日本語テキストです。OCRの結果として期待される内容です。"
        assert is_garbage(text) is False

    def test_repeated_characters_is_garbage(self):
        # Same character repeated 10+ times
        text = "1111111111111111111111111111111111"
        assert is_garbage(text) is True

    def test_mixed_repeated_is_garbage(self):
        # Long text with repeated pattern and low Japanese ratio
        text = "}^} " + "1 " * 50  # 100+ chars with low Japanese ratio
        assert is_garbage(text) is True

    def test_low_japanese_ratio_is_garbage(self):
        # Long text with very few Japanese characters
        text = "abcdefghijklmnopqrstuvwxyz" * 5  # 130 chars, no Japanese
        assert is_garbage(text) is True

    def test_short_text_not_checked_for_ratio(self):
        # Short text (< 50 chars) should not be flagged for low ratio
        text = "Hello World"
        assert is_garbage(text) is False

    def test_special_characters_is_garbage(self):
        text = "正常なテキスト@#$%^&*()!@#$%^&*()!@#$%テスト"
        # 10+ consecutive special chars
        assert is_garbage(text) is True

    def test_normal_punctuation_is_not_garbage(self):
        text = "これは、正常な日本語です。句読点があります！"
        assert is_garbage(text) is False


class TestCreateTextMask:
    """Tests for create_text_mask function."""

    def test_mask_figure_region(self):
        # Create a simple test image
        img = Image.new("RGB", (100, 100), color="black")
        regions = [
            {"type": "TEXT", "bbox": [0, 0, 50, 50]},
            {"type": "FIGURE", "bbox": [50, 50, 100, 100]},
        ]

        masked = create_text_mask(img, regions)

        # TEXT region should be unchanged (black)
        pixel_text = masked.getpixel((25, 25))
        assert pixel_text == (0, 0, 0), "TEXT region should be unchanged"

        # FIGURE region should be white (masked)
        pixel_figure = masked.getpixel((75, 75))
        assert pixel_figure == (255, 255, 255), "FIGURE region should be white"

        # Area outside all regions should also be white
        pixel_outside = masked.getpixel((75, 25))
        assert pixel_outside == (255, 255, 255), "Outside regions should be white"

    def test_mask_multiple_non_text_regions(self):
        img = Image.new("RGB", (100, 100), color="red")
        regions = [
            {"type": "TEXT", "bbox": [0, 0, 30, 100]},
            {"type": "FIGURE", "bbox": [30, 0, 60, 100]},
            {"type": "ABANDON", "bbox": [60, 0, 100, 100]},
        ]

        masked = create_text_mask(img, regions)

        # TEXT: unchanged (red)
        assert masked.getpixel((15, 50)) == (255, 0, 0)
        # FIGURE: masked (white)
        assert masked.getpixel((45, 50)) == (255, 255, 255)
        # ABANDON: masked (white)
        assert masked.getpixel((80, 50)) == (255, 255, 255)

    def test_custom_text_types(self):
        img = Image.new("RGB", (100, 100), color="blue")
        regions = [
            {"type": "TEXT", "bbox": [0, 0, 50, 50]},
            {"type": "TITLE", "bbox": [50, 0, 100, 50]},
            {"type": "CAPTION", "bbox": [0, 50, 50, 100]},
        ]

        # Only keep TEXT visible
        masked = create_text_mask(img, regions, text_types=["TEXT"])

        # TEXT: unchanged (blue)
        assert masked.getpixel((25, 25)) == (0, 0, 255)
        # TITLE: masked (white)
        assert masked.getpixel((75, 25)) == (255, 255, 255)
        # CAPTION: masked (white)
        assert masked.getpixel((25, 75)) == (255, 255, 255)

    def test_empty_regions(self):
        img = Image.new("RGB", (100, 100), color="green")
        regions = []

        masked = create_text_mask(img, regions)

        # All white (no TEXT regions to keep)
        assert masked.getpixel((50, 50)) == (255, 255, 255)


class TestSelectBestEngine:
    """Tests for select_best_engine function."""

    def test_select_by_priority_text(self):
        results = {
            "yomitoku": "Yomitoku結果",
            "paddleocr": "PaddleOCR結果",
            "tesseract": "Tesseract結果",
        }
        quality = {"yomitoku": True, "paddleocr": True, "tesseract": True}

        text, engine = select_best_engine(results, "TEXT", quality)

        # TEXT priority: yomitoku > paddleocr > tesseract
        assert engine == "yomitoku"

    def test_select_by_priority_figure(self):
        results = {
            "yomitoku": "Yomitoku結果",
            "easyocr": "EasyOCR結果",
            "paddleocr": "PaddleOCR結果",
        }
        quality = {"yomitoku": True, "easyocr": True, "paddleocr": True}

        text, engine = select_best_engine(results, "FIGURE", quality)

        # FIGURE priority: easyocr > paddleocr > tesseract
        assert engine == "easyocr"

    def test_skip_garbage_engine(self):
        results = {
            "yomitoku": "ゴミデータ",
            "paddleocr": "正常な結果",
        }
        quality = {"yomitoku": False, "paddleocr": True}

        text, engine = select_best_engine(results, "TEXT", quality)

        # yomitoku is garbage, should select paddleocr
        assert engine == "paddleocr"
        assert text == "正常な結果"

    def test_all_garbage_returns_longest(self):
        results = {
            "yomitoku": "短い",
            "paddleocr": "少し長めのテキスト",
        }
        # If all are valid, select by priority
        quality = {"yomitoku": True, "paddleocr": True}

        text, engine = select_best_engine(results, "TEXT", quality)
        assert engine == "yomitoku"  # Priority wins

    def test_empty_results(self):
        results = {}

        text, engine = select_best_engine(results, "TEXT")

        assert text == ""
        assert engine == "none"

    def test_fallback_region_type(self):
        results = {
            "paddleocr": "PaddleOCR結果",
            "tesseract": "Tesseract結果",
        }
        quality = {"paddleocr": True, "tesseract": True}

        text, engine = select_best_engine(results, "UNKNOWN_TYPE", quality)

        # DEFAULT priority: yomitoku > paddleocr > tesseract
        assert engine == "paddleocr"


class TestEnginePriority:
    """Tests for ENGINE_PRIORITY configuration."""

    def test_text_priority(self):
        assert ENGINE_PRIORITY["TEXT"] == ["yomitoku", "paddleocr", "tesseract"]

    def test_figure_priority(self):
        assert ENGINE_PRIORITY["FIGURE"] == ["easyocr", "paddleocr", "tesseract"]

    def test_table_priority(self):
        assert ENGINE_PRIORITY["TABLE"] == ["yomitoku", "paddleocr", "tesseract"]

    def test_default_priority(self):
        assert ENGINE_PRIORITY["DEFAULT"] == ["yomitoku", "paddleocr", "tesseract"]
