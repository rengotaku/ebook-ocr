"""Tests for code detector module.

Phase 2: User Story 1 - コード検出コア機能
T008: Guesslangコード判定テスト
T009: CodeRegion dataclassテスト
T010: layout.json更新テスト
"""

from __future__ import annotations

import pytest

# =============================================================================
# T008: Guesslangコード判定のテスト
# =============================================================================


class TestIsCode:
    """is_code() 関数のテスト

    Guesslangを使用してテキストがコードかどうかを判定する。
    戻り値: tuple[bool, float] = (コード判定結果, 確信度)
    """

    def test_is_code_with_python_code(self) -> None:
        """Pythonコードがコードと判定される"""
        from src.layout.code_detector import is_code

        python_code = """\
def hello_world():
    print("Hello, World!")
    return 42

if __name__ == "__main__":
    hello_world()
"""
        result, confidence = is_code(python_code)

        assert result is True, "Pythonコードはコードと判定されるべき"
        assert isinstance(confidence, float), "確信度はfloat型であるべき"
        assert 0.0 <= confidence <= 1.0, "確信度は0.0-1.0の範囲であるべき"

    def test_is_code_with_java_code(self) -> None:
        """Javaコードがコードと判定される"""
        from src.layout.code_detector import is_code

        java_code = """\
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
"""
        result, confidence = is_code(java_code)

        assert result is True, "Javaコードはコードと判定されるべき"
        assert isinstance(confidence, float), "確信度はfloat型であるべき"
        assert 0.0 <= confidence <= 1.0, "確信度は0.0-1.0の範囲であるべき"

    def test_is_code_with_japanese_text(self) -> None:
        """日本語テキストが非コードと判定される"""
        from src.layout.code_detector import is_code

        japanese_text = (
            "これは日本語の文章です。プログラミングとは関係ありません。"
            "書籍の本文として記述されている通常のテキストであり、"
            "コードブロックではありません。"
        )

        result, confidence = is_code(japanese_text)

        assert result is False, "日本語テキストは非コードと判定されるべき"
        assert isinstance(confidence, float), "確信度はfloat型であるべき"

    def test_is_code_with_empty_string(self) -> None:
        """空文字列が非コードと判定される"""
        from src.layout.code_detector import is_code

        result, confidence = is_code("")

        assert result is False, "空文字列は非コードと判定されるべき"
        assert confidence == 0.0, "空文字列の確信度は0.0であるべき"


# =============================================================================
# T009: CodeRegion dataclassのテスト
# =============================================================================


class TestCodeRegion:
    """CodeRegion dataclass のテスト

    レイアウト検出結果のコード領域を表すデータクラス。
    bbox, confidence, is_code, ocr_text を保持する。
    """

    def test_code_region_creation(self) -> None:
        """CodeRegionを正しく生成できる"""
        from src.layout.code_detector import CodeRegion

        region = CodeRegion(
            bbox=(100, 200, 500, 400),
            confidence=0.87,
            is_code=True,
            ocr_text="def hello(): pass",
        )

        assert region.bbox == (100, 200, 500, 400)
        assert region.confidence == 0.87
        assert region.is_code is True
        assert region.ocr_text == "def hello(): pass"

    def test_code_region_default_ocr_text(self) -> None:
        """CodeRegionのocr_textはデフォルトで空文字列"""
        from src.layout.code_detector import CodeRegion

        region = CodeRegion(
            bbox=(0, 0, 100, 100),
            confidence=0.5,
            is_code=False,
        )

        assert region.ocr_text == ""

    def test_code_region_immutability(self) -> None:
        """frozen dataclassの不変性"""
        from src.layout.code_detector import CodeRegion

        region = CodeRegion(
            bbox=(100, 200, 500, 400),
            confidence=0.87,
            is_code=True,
            ocr_text="code",
        )

        # frozen=True なので属性変更で FrozenInstanceError が発生する
        with pytest.raises(Exception):  # FrozenInstanceError
            region.confidence = 0.5

    def test_code_region_non_code(self) -> None:
        """is_code=Falseの領域を正しく表現できる"""
        from src.layout.code_detector import CodeRegion

        region = CodeRegion(
            bbox=(10, 20, 300, 150),
            confidence=0.15,
            is_code=False,
            ocr_text="これは日本語テキスト",
        )

        assert region.is_code is False
        assert region.confidence == 0.15


# =============================================================================
# T010: layout.json更新のテスト
# =============================================================================


class TestDetectCodeInLayout:
    """detect_code_regions() 関数のテスト

    layout.jsonのTEXT領域を走査し、コード判定を適用する。
    CODE判定された場合はtypeを"CODE"に変更する。
    """

    def test_detect_code_in_layout(self) -> None:
        """TEXT領域がCODEに再分類される"""
        from src.layout.code_detector import detect_code_regions

        layout = {
            "regions": [
                {
                    "type": "TEXT",
                    "label": "plain text",
                    "bbox": [100, 200, 500, 400],
                    "confidence": 1.0,
                    "ocr_text": "def hello():\n    print('Hello')\n    return 42",
                },
            ],
            "page_size": [800, 600],
        }

        result = detect_code_regions(layout)

        # TEXT領域がCODEに再分類されていること
        code_regions = [r for r in result["regions"] if r["type"] == "CODE"]
        assert len(code_regions) >= 1, "コードテキストを含むTEXT領域はCODEに再分類されるべき"
        assert code_regions[0]["label"] == "code"

    def test_detect_code_preserves_non_text_regions(self) -> None:
        """FIGURE等の非TEXT領域は変更されない"""
        from src.layout.code_detector import detect_code_regions

        layout = {
            "regions": [
                {
                    "type": "FIGURE",
                    "label": "figure",
                    "bbox": [50, 50, 200, 200],
                    "confidence": 1.0,
                },
                {
                    "type": "TITLE",
                    "label": "section_headings",
                    "bbox": [100, 10, 700, 50],
                    "confidence": 1.0,
                },
                {
                    "type": "TEXT",
                    "label": "plain text",
                    "bbox": [100, 300, 700, 500],
                    "confidence": 1.0,
                    "ocr_text": "これは日本語の通常テキストです。",
                },
            ],
            "page_size": [800, 600],
        }

        result = detect_code_regions(layout)

        # FIGURE, TITLE領域はそのまま維持されること
        figure_regions = [r for r in result["regions"] if r["type"] == "FIGURE"]
        title_regions = [r for r in result["regions"] if r["type"] == "TITLE"]
        assert len(figure_regions) == 1, "FIGURE領域は維持されるべき"
        assert len(title_regions) == 1, "TITLE領域は維持されるべき"
        assert figure_regions[0]["bbox"] == [50, 50, 200, 200]
        assert title_regions[0]["bbox"] == [100, 10, 700, 50]

    def test_detect_code_with_threshold(self) -> None:
        """閾値による判定制御"""
        from src.layout.code_detector import detect_code_regions

        layout = {
            "regions": [
                {
                    "type": "TEXT",
                    "label": "plain text",
                    "bbox": [100, 200, 500, 400],
                    "confidence": 1.0,
                    "ocr_text": "def hello():\n    print('Hello')\n    return 42",
                },
            ],
            "page_size": [800, 600],
        }

        # 高い閾値（0.99）では再分類されにくい
        result_high = detect_code_regions(layout, threshold=0.99)
        # 低い閾値（0.01）では再分類されやすい
        result_low = detect_code_regions(layout, threshold=0.01)

        code_regions_low = [r for r in result_low["regions"] if r["type"] == "CODE"]
        assert len(code_regions_low) >= 1, "低い閾値ではコード判定されやすいはず"

    def test_detect_code_returns_new_layout(self) -> None:
        """元のlayout辞書を変更せず、新しい辞書を返す"""
        from src.layout.code_detector import detect_code_regions

        layout = {
            "regions": [
                {
                    "type": "TEXT",
                    "label": "plain text",
                    "bbox": [100, 200, 500, 400],
                    "confidence": 1.0,
                    "ocr_text": "x = 1",
                },
            ],
            "page_size": [800, 600],
        }

        original_type = layout["regions"][0]["type"]
        result = detect_code_regions(layout)

        # 元のデータは変更されていないこと（不変性）
        assert layout["regions"][0]["type"] == original_type
        assert result is not layout, "新しい辞書が返されるべき"

    def test_detect_code_empty_regions(self) -> None:
        """空のregionsリストを処理できる"""
        from src.layout.code_detector import detect_code_regions

        layout = {
            "regions": [],
            "page_size": [800, 600],
        }

        result = detect_code_regions(layout)

        assert result["regions"] == []
        assert result["page_size"] == [800, 600]
