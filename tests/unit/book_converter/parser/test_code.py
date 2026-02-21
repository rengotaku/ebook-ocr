"""Tests for code parser module.

Phase 4: User Story 1 - パーサー統合
T035: コードパーサーのテスト

CODE領域からCode dataclassを生成するパーサーをテスト。
実装が存在しないため全テストFAIL (RED) となる。
"""

from __future__ import annotations


class TestParseCodeRegion:
    """CODE領域からCode要素を生成するテスト"""

    def test_parse_code_region(self) -> None:
        """CODE領域のdictからCode dataclassを生成できる"""
        from src.book_converter.parser.code import parse_code_region

        region = {
            "type": "CODE",
            "label": "code",
            "bbox": [100, 200, 500, 400],
            "confidence": 0.87,
            "ocr_text": 'def hello():\n    print("Hello, World!")',
        }

        result = parse_code_region(region)

        assert result is not None
        assert result.text == 'def hello():\n    print("Hello, World!")'
        assert result.confidence == 0.87
        assert result.read_aloud is False

    def test_parse_code_region_default_confidence(self) -> None:
        """confidence未指定の場合はデフォルト1.0"""
        from src.book_converter.parser.code import parse_code_region

        region = {
            "type": "CODE",
            "label": "code",
            "bbox": [0, 0, 100, 100],
            "ocr_text": "x = 1",
        }

        result = parse_code_region(region)

        assert result is not None
        assert result.confidence == 1.0

    def test_parse_code_preserves_formatting(self) -> None:
        """改行・インデントが保持される"""
        from src.book_converter.parser.code import parse_code_region

        code_text = 'class Foo:\n    def bar(self):\n        return 42\n\n    def baz(self):\n        print("hello")\n'

        region = {
            "type": "CODE",
            "label": "code",
            "bbox": [50, 50, 600, 300],
            "confidence": 0.95,
            "ocr_text": code_text,
        }

        result = parse_code_region(region)

        assert result is not None
        assert result.text == code_text
        # インデントが保持されていること
        assert "    def bar(self):" in result.text
        assert "        return 42" in result.text
        # 空行が保持されていること
        assert "\n\n" in result.text

    def test_parse_code_with_special_chars(self) -> None:
        """特殊文字（<, >, &, 引用符）が正しく処理される"""
        from src.book_converter.parser.code import parse_code_region

        code_text = 'if x < 10 && y > 5:\n    print("a & b")\n    html = "<div>"'

        region = {
            "type": "CODE",
            "label": "code",
            "bbox": [100, 100, 500, 300],
            "confidence": 0.9,
            "ocr_text": code_text,
        }

        result = parse_code_region(region)

        assert result is not None
        assert "<" in result.text
        assert ">" in result.text
        assert "&" in result.text
        assert '"' in result.text

    def test_parse_code_with_empty_text(self) -> None:
        """空のコードブロック"""
        from src.book_converter.parser.code import parse_code_region

        region = {
            "type": "CODE",
            "label": "code",
            "bbox": [0, 0, 100, 100],
            "confidence": 0.5,
            "ocr_text": "",
        }

        result = parse_code_region(region)

        assert result is not None
        assert result.text == ""
        assert result.confidence == 0.5

    def test_parse_code_with_unicode(self) -> None:
        """Unicode文字を含むコード"""
        from src.book_converter.parser.code import parse_code_region

        code_text = '# コメント：日本語\nprint("こんにちは世界")'

        region = {
            "type": "CODE",
            "label": "code",
            "bbox": [0, 0, 400, 200],
            "confidence": 0.8,
            "ocr_text": code_text,
        }

        result = parse_code_region(region)

        assert result is not None
        assert "日本語" in result.text
        assert "こんにちは世界" in result.text
