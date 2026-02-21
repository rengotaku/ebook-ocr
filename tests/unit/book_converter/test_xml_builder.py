"""Tests for XML builder / transformer Code element output.

Phase 4: User Story 1 - パーサー統合
T036: XMLビルダーのテスト

Code要素がXML出力に正しく変換されることをテスト。
transform_code関数が未実装のため全テストFAIL (RED) となる。
"""

from __future__ import annotations

from xml.etree.ElementTree import tostring

from src.book_converter.models import Code


class TestTransformCode:
    """Code要素のXML変換テスト"""

    def test_build_xml_with_code(self) -> None:
        """Code要素が<code>タグとして出力される"""
        from src.book_converter.transformer import transform_code

        code = Code(text='def hello():\n    print("Hello")')

        elem = transform_code(code)

        assert elem.tag == "code"
        assert elem.text == 'def hello():\n    print("Hello")'

    def test_code_element_has_read_aloud_false(self) -> None:
        """<code>要素にreadAloud="false"属性が設定される"""
        from src.book_converter.transformer import transform_code

        code = Code(text="x = 1")

        elem = transform_code(code)

        assert elem.get("readAloud") == "false"

    def test_code_element_escapes_special_chars(self) -> None:
        """XML特殊文字が正しくエスケープされる"""
        from src.book_converter.transformer import transform_code

        code = Code(text='if x < 10 && y > 5:\n    s = "a & b"')

        elem = transform_code(code)

        # ElementTreeはシリアライズ時に自動エスケープする
        xml_str = tostring(elem, encoding="unicode")
        assert "&lt;" in xml_str  # < がエスケープ
        assert "&gt;" in xml_str  # > がエスケープ
        assert "&amp;" in xml_str  # & がエスケープ

    def test_code_element_preserves_newlines(self) -> None:
        """改行が保持される"""
        from src.book_converter.transformer import transform_code

        code = Code(text="line1\nline2\nline3")

        elem = transform_code(code)

        assert elem.text is not None
        assert "\n" in elem.text
        lines = elem.text.split("\n")
        assert len(lines) == 3
        assert lines[0] == "line1"
        assert lines[2] == "line3"

    def test_code_element_preserves_indentation(self) -> None:
        """インデントが保持される"""
        from src.book_converter.transformer import transform_code

        code = Code(text="class Foo:\n    def bar(self):\n        pass")

        elem = transform_code(code)

        assert "    def bar(self):" in elem.text
        assert "        pass" in elem.text

    def test_code_element_empty_text(self) -> None:
        """空テキストのCode要素"""
        from src.book_converter.transformer import transform_code

        code = Code(text="")

        elem = transform_code(code)

        assert elem.tag == "code"
        assert elem.get("readAloud") == "false"
        assert elem.text == ""


class TestTransformSectionWithCode:
    """Section内のCode要素変換テスト"""

    def test_section_with_code_element_in_xml(self) -> None:
        """Sectionに含まれるCode要素がXMLに出力される"""
        from src.book_converter.models import Section
        from src.book_converter.transformer import transform_section

        section = Section(
            number="1.1",
            title="Test Section",
            elements=(Code(text="print('hello')"),),
        )

        elem = transform_section(section)

        # section内にcode子要素が存在する
        code_elems = elem.findall("code")
        assert len(code_elems) == 1
        assert code_elems[0].text == "print('hello')"
        assert code_elems[0].get("readAloud") == "false"

    def test_section_with_mixed_elements(self) -> None:
        """Code要素がParagraph等と混在するSection"""
        from src.book_converter.models import Paragraph, Section
        from src.book_converter.transformer import transform_section

        section = Section(
            number="2.1",
            title="Mixed Section",
            elements=(
                Paragraph(text="Before code"),
                Code(text="x = 42"),
                Paragraph(text="After code"),
            ),
        )

        elem = transform_section(section)

        children = list(elem)
        assert len(children) == 3
        assert children[0].tag == "paragraph"
        assert children[1].tag == "code"
        assert children[2].tag == "paragraph"
        assert children[1].text == "x = 42"
        assert children[1].get("readAloud") == "false"
