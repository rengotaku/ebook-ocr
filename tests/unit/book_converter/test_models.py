"""Tests for Code dataclass and SectionElement extension.

Phase 3: User Story 1 - データモデル拡張
T023: Code dataclassのテスト
T024: SectionElement拡張のテスト
"""

from __future__ import annotations

import pytest

# =============================================================================
# T023: Code dataclassのテスト
# =============================================================================


class TestCodeDataclass:
    """Code dataclass のテスト

    コードブロック要素を表現するfrozen dataclass。
    text, confidence, read_aloud を保持する。
    """

    def test_code_creation(self) -> None:
        """Code要素を正しく生成できる"""
        from src.book_converter.models import Code

        code = Code(
            text='def hello():\n    print("Hello")\n    return 42',
        )

        assert code.text == 'def hello():\n    print("Hello")\n    return 42'
        assert isinstance(code.text, str)

    def test_code_default_read_aloud_false(self) -> None:
        """read_aloudのデフォルト値はFalse"""
        from src.book_converter.models import Code

        code = Code(text="x = 1")

        assert code.read_aloud is False, "Code要素のread_aloudはデフォルトでFalseであるべき"

    def test_code_immutability(self) -> None:
        """frozen dataclassの不変性を確認"""
        from src.book_converter.models import Code

        code = Code(text="print('hello')", confidence=0.9, read_aloud=False)

        # frozen=True なので属性変更で FrozenInstanceError が発生する
        with pytest.raises(Exception):  # FrozenInstanceError
            code.text = "modified"

        with pytest.raises(Exception):  # FrozenInstanceError
            code.confidence = 0.5

        with pytest.raises(Exception):  # FrozenInstanceError
            code.read_aloud = True

    def test_code_with_confidence(self) -> None:
        """confidence属性が正しく設定される"""
        from src.book_converter.models import Code

        code = Code(text="import os", confidence=0.87)

        assert code.confidence == 0.87
        assert isinstance(code.confidence, float)

    def test_code_default_confidence(self) -> None:
        """confidenceのデフォルト値は1.0"""
        from src.book_converter.models import Code

        code = Code(text="x = 1")

        assert code.confidence == 1.0

    def test_code_preserves_formatting(self) -> None:
        """改行・インデントが保持される"""
        from src.book_converter.models import Code

        multiline_code = "class Foo:\n    def bar(self):\n        return 42\n"
        code = Code(text=multiline_code)

        assert code.text == multiline_code
        assert "\n" in code.text
        assert "    " in code.text

    def test_code_empty_text(self) -> None:
        """空文字列のコードブロックを生成できる"""
        from src.book_converter.models import Code

        code = Code(text="")

        assert code.text == ""
        assert code.confidence == 1.0
        assert code.read_aloud is False


# =============================================================================
# T024: SectionElement拡張のテスト
# =============================================================================


class TestSectionElementWithCode:
    """SectionElement Union型にCodeが含まれることのテスト

    SectionElement = Union[Heading, Paragraph, List, Figure, Code]
    """

    def test_section_element_includes_code(self) -> None:
        """SectionElement Union型にCodeが含まれる"""
        # Code が SectionElement の構成型に含まれていることを確認
        # Union型の __args__ でチェック
        import typing

        from src.book_converter.models import Code, SectionElement

        args = typing.get_args(SectionElement)
        assert Code in args, "SectionElement Union型にCodeが含まれるべき"

    def test_section_with_code_element(self) -> None:
        """Section.elementsにCode要素を含めることができる"""
        from src.book_converter.models import Code, Paragraph, Section

        code = Code(
            text='print("hello")',
            confidence=0.95,
            read_aloud=False,
        )
        paragraph = Paragraph(text="以下はサンプルコードです。")

        section = Section(
            number="1.1",
            title="サンプル",
            elements=(paragraph, code),
        )

        assert len(section.elements) == 2
        assert isinstance(section.elements[0], Paragraph)
        assert isinstance(section.elements[1], Code)
        assert section.elements[1].text == 'print("hello")'
        assert section.elements[1].read_aloud is False
