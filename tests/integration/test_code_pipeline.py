"""Integration tests for code detection pipeline.

Phase 5: User Story 1 - パイプライン統合テスト
T047: layout.json → CODE検出 → Code dataclass → XML出力

テスト対象:
- detect_code_regions() (src/layout/code_detector.py)
- parse_code_region() (src/book_converter/parser/code.py)
- transform_code() (src/book_converter/transformer.py)
"""

from __future__ import annotations

from xml.etree.ElementTree import tostring

# =============================================================================
# T047: パイプライン統合テスト
# =============================================================================


class TestCodeDetectionPipeline:
    """layout.json → CODE検出 → Code dataclass → XML出力の統合テスト"""

    def test_code_detection_pipeline(self) -> None:
        """layout.json → CODE検出 → パース → XML出力の完全パイプライン

        Pythonコードを含むTEXT領域が:
        1. detect_code_regions()でCODEに再分類される
        2. parse_code_region()でCode dataclassに変換される
        3. transform_code()で<code readAloud="false">のXML要素になる
        """
        from src.book_converter.models import Code
        from src.book_converter.parser.code import parse_code_region
        from src.book_converter.transformer import transform_code
        from src.layout.code_detector import detect_code_regions

        # Arrange: TEXT領域にPythonコードを含むlayout
        layout = {
            "regions": [
                {
                    "type": "TEXT",
                    "label": "plain text",
                    "bbox": [100, 200, 500, 400],
                    "confidence": 1.0,
                    "ocr_text": (
                        "def hello_world():\n"
                        '    print("Hello, World!")\n'
                        "    return 42\n"
                        "\n"
                        'if __name__ == "__main__":\n'
                        "    hello_world()"
                    ),
                }
            ],
            "page_size": [800, 600],
        }

        # Step 1: CODE検出
        updated_layout = detect_code_regions(layout)
        code_regions = [r for r in updated_layout["regions"] if r["type"] == "CODE"]
        assert len(code_regions) == 1, "Pythonコード領域が1つCODEとして検出されるべき"
        assert code_regions[0]["type"] == "CODE"
        assert code_regions[0]["label"] == "code"

        # Step 2: Code dataclass生成
        code = parse_code_region(code_regions[0])
        assert isinstance(code, Code), "parse_code_regionはCode dataclassを返すべき"
        assert "def hello_world():" in code.text
        assert code.read_aloud is False, "コードは常にread_aloud=False"

        # Step 3: XML出力
        elem = transform_code(code)
        assert elem.tag == "code", "XML要素タグは'code'であるべき"
        assert elem.get("readAloud") == "false", "readAloud属性は'false'であるべき"
        assert "def hello_world():" in (elem.text or "")

        # XML文字列として検証
        xml_str = tostring(elem, encoding="unicode")
        assert '<code readAloud="false">' in xml_str
        assert "def hello_world():" in xml_str

    def test_code_detection_pipeline_with_java(self) -> None:
        """Javaコードでもパイプラインが正しく動作する"""
        from src.book_converter.models import Code
        from src.book_converter.parser.code import parse_code_region
        from src.book_converter.transformer import transform_code
        from src.layout.code_detector import detect_code_regions

        layout = {
            "regions": [
                {
                    "type": "TEXT",
                    "label": "plain text",
                    "bbox": [50, 100, 600, 500],
                    "confidence": 1.0,
                    "ocr_text": (
                        "public class HelloWorld {\n"
                        "    public static void main(String[] args) {\n"
                        '        System.out.println("Hello");\n'
                        "    }\n"
                        "}"
                    ),
                }
            ],
            "page_size": [800, 600],
        }

        # 完全パイプライン実行
        updated_layout = detect_code_regions(layout)
        code_regions = [r for r in updated_layout["regions"] if r["type"] == "CODE"]
        assert len(code_regions) == 1, "Javaコードが検出されるべき"

        code = parse_code_region(code_regions[0])
        assert isinstance(code, Code)
        assert "public class HelloWorld" in code.text

        elem = transform_code(code)
        assert elem.tag == "code"
        assert elem.get("readAloud") == "false"

    def test_code_detection_pipeline_preserves_indentation(self) -> None:
        """パイプライン全体でインデントが保持される"""
        from src.book_converter.parser.code import parse_code_region
        from src.book_converter.transformer import transform_code
        from src.layout.code_detector import detect_code_regions

        indented_code = "def foo():\n    if True:\n        return 1\n    return 0"

        layout = {
            "regions": [
                {
                    "type": "TEXT",
                    "label": "plain text",
                    "bbox": [0, 0, 100, 100],
                    "confidence": 1.0,
                    "ocr_text": indented_code,
                }
            ],
            "page_size": [800, 600],
        }

        updated_layout = detect_code_regions(layout)
        code_regions = [r for r in updated_layout["regions"] if r["type"] == "CODE"]
        assert len(code_regions) >= 1

        code = parse_code_region(code_regions[0])
        elem = transform_code(code)

        # インデントが保持されていることを確認
        assert "    if True:" in (elem.text or ""), "4スペースインデントが保持されるべき"
        assert "        return 1" in (elem.text or ""), "8スペースインデントが保持されるべき"


class TestCodeDetectionWithMixedContent:
    """コードと日本語テキストが混在するケースのテスト"""

    def test_mixed_code_and_japanese_regions(self) -> None:
        """コード領域と日本語テキスト領域が混在するlayout"""
        from src.layout.code_detector import detect_code_regions

        layout = {
            "regions": [
                {
                    "type": "TEXT",
                    "label": "plain text",
                    "bbox": [50, 50, 400, 150],
                    "confidence": 1.0,
                    "ocr_text": (
                        "この章ではPythonの基本的なデータ構造について説明します。"
                        "リストやタプル、辞書などの使い方を学びましょう。"
                    ),
                },
                {
                    "type": "TEXT",
                    "label": "plain text",
                    "bbox": [50, 200, 400, 400],
                    "confidence": 1.0,
                    "ocr_text": (
                        "def quicksort(arr):\n"
                        "    if len(arr) <= 1:\n"
                        "        return arr\n"
                        "    pivot = arr[0]\n"
                        "    left = [x for x in arr[1:] if x <= pivot]\n"
                        "    right = [x for x in arr[1:] if x > pivot]\n"
                        "    return quicksort(left) + [pivot] + quicksort(right)"
                    ),
                },
                {
                    "type": "TITLE",
                    "label": "section_headings",
                    "bbox": [50, 10, 400, 40],
                    "confidence": 1.0,
                    "ocr_text": "第3章 ソートアルゴリズム",
                },
            ],
            "page_size": [800, 600],
        }

        updated_layout = detect_code_regions(layout)
        regions = updated_layout["regions"]

        # 日本語テキスト領域はTEXTのまま
        assert regions[0]["type"] == "TEXT", "日本語テキストはTEXTのままであるべき"

        # コード領域はCODEに再分類
        assert regions[1]["type"] == "CODE", "Pythonコードの領域はCODEに再分類されるべき"

        # TITLE領域は変更なし
        assert regions[2]["type"] == "TITLE", "TITLE領域はそのままであるべき"

    def test_mixed_content_full_pipeline(self) -> None:
        """混在コンテンツでパイプライン全体が正しく動作する"""
        from src.book_converter.models import Code
        from src.book_converter.parser.code import parse_code_region
        from src.book_converter.transformer import transform_code
        from src.layout.code_detector import detect_code_regions

        layout = {
            "regions": [
                {
                    "type": "TEXT",
                    "label": "plain text",
                    "bbox": [50, 50, 400, 100],
                    "confidence": 1.0,
                    "ocr_text": "関数の定義方法を見ていきましょう。以下のコードは基本的な関数定義の例です。",
                },
                {
                    "type": "TEXT",
                    "label": "plain text",
                    "bbox": [50, 150, 400, 350],
                    "confidence": 1.0,
                    "ocr_text": (
                        "class Calculator:\n"
                        "    def __init__(self):\n"
                        "        self.result = 0\n"
                        "\n"
                        "    def add(self, value):\n"
                        "        self.result += value\n"
                        "        return self\n"
                    ),
                },
            ],
            "page_size": [800, 600],
        }

        updated_layout = detect_code_regions(layout)

        # CODE領域のみをパースしてXML変換
        code_regions = [r for r in updated_layout["regions"] if r["type"] == "CODE"]
        assert len(code_regions) >= 1, "コード領域が検出されるべき"

        for region in code_regions:
            code = parse_code_region(region)
            assert isinstance(code, Code)
            elem = transform_code(code)
            assert elem.tag == "code"
            assert elem.get("readAloud") == "false"

    def test_xml_special_characters_in_code(self) -> None:
        """XML特殊文字を含むコードが正しくエスケープされる"""
        from src.book_converter.models import Code
        from src.book_converter.transformer import transform_code

        # XML特殊文字を含むコード（直接Code dataclassから検証）
        code = Code(
            text='if x < 10 && y > 5:\n    print(f"result: {x & y}")',
            confidence=0.9,
        )

        elem = transform_code(code)
        xml_str = tostring(elem, encoding="unicode")

        # ElementTreeが自動エスケープすることを検証
        assert "&lt;" in xml_str, "< はエスケープされるべき"
        assert "&gt;" in xml_str, "> はエスケープされるべき"
        assert "&amp;" in xml_str, "& はエスケープされるべき"


class TestCodeDetectionFalsePositive:
    """誤検出（false positive）のテスト - コラム等がコードと誤判定されないことを確認"""

    def test_column_text_not_detected_as_code(self) -> None:
        """コラム文章がコードと誤判定されない"""
        from src.layout.code_detector import detect_code_regions

        layout = {
            "regions": [
                {
                    "type": "TEXT",
                    "label": "plain text",
                    "bbox": [50, 50, 400, 300],
                    "confidence": 1.0,
                    "ocr_text": (
                        "コラム: プログラミング言語の歴史\n"
                        "プログラミング言語は1950年代から発展してきました。\n"
                        "最初の高級言語であるFORTRANは、科学技術計算のために\n"
                        "開発されました。その後、COBOLがビジネス用途で登場し、\n"
                        "LISPが人工知能研究で使われるようになりました。\n"
                        "現代では数百のプログラミング言語が存在しています。"
                    ),
                }
            ],
            "page_size": [800, 600],
        }

        updated_layout = detect_code_regions(layout)

        # 日本語コラムはCODEに再分類されるべきでない
        assert updated_layout["regions"][0]["type"] == "TEXT", "日本語コラムはTEXTのままであるべき（誤検出なし）"

    def test_table_like_text_not_detected_as_code(self) -> None:
        """表形式テキストがコードと誤判定されない"""
        from src.layout.code_detector import detect_code_regions

        layout = {
            "regions": [
                {
                    "type": "TEXT",
                    "label": "plain text",
                    "bbox": [50, 50, 400, 200],
                    "confidence": 1.0,
                    "ocr_text": (
                        "名前　　　年齢　　　職業\n"
                        "田中太郎　30歳　　　エンジニア\n"
                        "佐藤花子　25歳　　　デザイナー\n"
                        "鈴木一郎　45歳　　　マネージャー"
                    ),
                }
            ],
            "page_size": [800, 600],
        }

        updated_layout = detect_code_regions(layout)

        assert updated_layout["regions"][0]["type"] == "TEXT", "表形式テキストはTEXTのままであるべき（誤検出なし）"

    def test_numbered_list_not_detected_as_code(self) -> None:
        """番号付きリストがコードと誤判定されない"""
        from src.layout.code_detector import detect_code_regions

        layout = {
            "regions": [
                {
                    "type": "TEXT",
                    "label": "plain text",
                    "bbox": [50, 50, 400, 200],
                    "confidence": 1.0,
                    "ocr_text": (
                        "手順:\n"
                        "1. まずファイルを開きます\n"
                        "2. 次に内容を確認します\n"
                        "3. 必要に応じて修正を加えます\n"
                        "4. 最後にファイルを保存します"
                    ),
                }
            ],
            "page_size": [800, 600],
        }

        updated_layout = detect_code_regions(layout)

        assert updated_layout["regions"][0]["type"] == "TEXT", "番号付きリストはTEXTのままであるべき（誤検出なし）"

    def test_figure_and_title_regions_unchanged(self) -> None:
        """FIGURE, TITLE領域はコード検出の対象外"""
        from src.layout.code_detector import detect_code_regions

        layout = {
            "regions": [
                {
                    "type": "FIGURE",
                    "label": "figure",
                    "bbox": [100, 100, 500, 400],
                    "confidence": 1.0,
                },
                {
                    "type": "TITLE",
                    "label": "section_headings",
                    "bbox": [50, 10, 400, 50],
                    "confidence": 1.0,
                    "ocr_text": "def main():",
                },
            ],
            "page_size": [800, 600],
        }

        updated_layout = detect_code_regions(layout)

        # FIGURE, TITLEは変更されない（TEXTのみが検出対象）
        assert updated_layout["regions"][0]["type"] == "FIGURE"
        assert updated_layout["regions"][1]["type"] == "TITLE"

    def test_empty_text_region_not_detected_as_code(self) -> None:
        """空テキスト領域がコードと判定されない"""
        from src.layout.code_detector import detect_code_regions

        layout = {
            "regions": [
                {
                    "type": "TEXT",
                    "label": "plain text",
                    "bbox": [50, 50, 400, 100],
                    "confidence": 1.0,
                    "ocr_text": "",
                },
                {
                    "type": "TEXT",
                    "label": "plain text",
                    "bbox": [50, 150, 400, 200],
                    "confidence": 1.0,
                },
            ],
            "page_size": [800, 600],
        }

        updated_layout = detect_code_regions(layout)

        # 空テキストはCODEに再分類されない
        assert updated_layout["regions"][0]["type"] == "TEXT"
        assert updated_layout["regions"][1]["type"] == "TEXT"

    def test_original_layout_not_modified(self) -> None:
        """元のlayout dictが変更されないことを確認（イミュータビリティ）"""
        from src.layout.code_detector import detect_code_regions

        layout = {
            "regions": [
                {
                    "type": "TEXT",
                    "label": "plain text",
                    "bbox": [0, 0, 100, 100],
                    "confidence": 1.0,
                    "ocr_text": "def foo():\n    return 42",
                }
            ],
            "page_size": [800, 600],
        }

        # 元のデータをコピーして保存
        original_type = layout["regions"][0]["type"]

        _ = detect_code_regions(layout)

        # 元のlayoutは変更されていないことを確認
        assert layout["regions"][0]["type"] == original_type, "元のlayout dictは変更されるべきでない"
