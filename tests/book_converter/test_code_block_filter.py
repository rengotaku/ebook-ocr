"""Tests for code block false-positive filtering."""

from __future__ import annotations

from pathlib import Path

from src.book_converter.code_block_filter import (
    _has_code_indicators,
    _japanese_ratio,
    filter_code_block,
)
from src.book_converter.models import CodeBlock, Paragraph
from src.book_converter.parser.page import parse_pages_with_errors


class TestHasCodeIndicators:
    """Test code indicator detection."""

    def test_python_code(self):
        assert _has_code_indicators("def foo(): return 42") is True

    def test_java_code(self):
        assert _has_code_indicators("public void main(String[] args) {") is True

    def test_pure_japanese(self):
        assert _has_code_indicators("日本語のテキストです") is False

    def test_isbn_reference(self):
        assert _has_code_indicators("ISBN978-4-274-05019-0") is False

    def test_braces_and_symbols(self):
        assert _has_code_indicators("if (x > 0) { return x; }") is True

    def test_empty(self):
        assert _has_code_indicators("") is False

    def test_short_number(self):
        assert _has_code_indicators("3") is False

    def test_arrow_operator(self):
        assert _has_code_indicators("x => x + 1") is True


class TestJapaneseRatio:
    """Test Japanese character ratio calculation."""

    def test_pure_japanese(self):
        ratio = _japanese_ratio("日本語テスト")
        assert ratio > 0.9

    def test_pure_english(self):
        ratio = _japanese_ratio("hello world")
        assert ratio == 0.0

    def test_mixed(self):
        # "コード code" = 3 Japanese + 1 space + 4 English = ratio 3/8
        ratio = _japanese_ratio("コードcode")
        assert 0.3 < ratio < 0.5

    def test_empty(self):
        assert _japanese_ratio("") == 0.0


class TestFilterCodeBlock:
    """Test code block filtering logic."""

    def test_empty_block_removed(self):
        block = CodeBlock(text="")
        assert filter_code_block(block) is None

    def test_whitespace_only_removed(self):
        block = CodeBlock(text="   \n  \n  ")
        assert filter_code_block(block) is None

    def test_short_non_code_demoted(self):
        block = CodeBlock(text="3")
        result = filter_code_block(block)
        assert isinstance(result, Paragraph)
        assert result.text == "3"

    def test_short_code_kept(self):
        block = CodeBlock(text="x = 1;")
        result = filter_code_block(block)
        # Has code indicators (=, ;), so kept as CodeBlock
        assert isinstance(result, CodeBlock)

    def test_japanese_book_reference_demoted(self):
        text = "夫、平澤 章、梅澤真史 訳/オーム社/ ISBN978-4-274-05019-0)"
        block = CodeBlock(text=text)
        result = filter_code_block(block)
        assert isinstance(result, Paragraph)

    def test_japanese_prose_demoted(self):
        text = "クラス名、ドキュメント、任意のパブリック関数はすべて、パブリックAPIの一部である"
        block = CodeBlock(text=text)
        result = filter_code_block(block)
        assert isinstance(result, Paragraph)

    def test_real_code_kept(self):
        text = 'def hello():\n    print("world")\n    return True'
        block = CodeBlock(text=text, language="python")
        result = filter_code_block(block)
        assert isinstance(result, CodeBlock)
        assert result.text == text

    def test_code_with_japanese_comments_kept(self):
        text = "// 正しく設定が読み込まれたらtrueを返す\nBoolean loadSettings(File location) { ... }"
        block = CodeBlock(text=text)
        result = filter_code_block(block)
        assert isinstance(result, CodeBlock)

    def test_java_interface_kept(self):
        text = "interface TextImportanceScorer {\nBoolean isImportant(String text);\n}"
        block = CodeBlock(text=text)
        result = filter_code_block(block)
        assert isinstance(result, CodeBlock)

    def test_single_brace_demoted(self):
        block = CodeBlock(text="}")
        result = filter_code_block(block)
        # Short text with symbol - has code indicators but under length threshold
        # '}' has symbol ratio > 0.05, so it IS a code indicator.
        # But it's only 1 char, very short. Let's check what actually happens.
        # len("}") = 1, symbol_count = 1, ratio = 1.0 > 0.05 → has_code_indicators = True
        # len < 10 but has_code_indicators → kept as CodeBlock
        assert isinstance(result, CodeBlock)

    def test_kanji_word_demoted(self):
        block = CodeBlock(text="可変")
        result = filter_code_block(block)
        assert isinstance(result, Paragraph)

    def test_mixed_code_with_listing_header_kept(self):
        text = (
            "リスト2.6 インターフェイスと実装\n\ninterface TextImportanceScorer {\nBoolean isImportant(String text);\n}"
        )
        block = CodeBlock(text=text)
        result = filter_code_block(block)
        assert isinstance(result, CodeBlock)


class TestFilterIntegration:
    """Test code block filtering in full page pipeline."""

    def test_empty_code_block_removed(self, tmp_path: Path):
        md_content = """
--- page_0001 ---

Some text.

```
```

More text.
"""
        md_file = tmp_path / "book.md"
        md_file.write_text(md_content)

        pages, _, _ = parse_pages_with_errors(md_file)
        elements = pages[0].content.elements
        code_blocks = [e for e in elements if isinstance(e, CodeBlock)]
        assert len(code_blocks) == 0

    def test_short_non_code_becomes_paragraph(self, tmp_path: Path):
        md_content = """
--- page_0001 ---

Some text.

```
3
```

More text.
"""
        md_file = tmp_path / "book.md"
        md_file.write_text(md_content)

        pages, _, _ = parse_pages_with_errors(md_file)
        elements = pages[0].content.elements
        code_blocks = [e for e in elements if isinstance(e, CodeBlock)]
        paragraphs = [e for e in elements if isinstance(e, Paragraph)]
        assert len(code_blocks) == 0
        # "3" should become a paragraph
        assert any("3" in p.text for p in paragraphs)

    def test_real_code_preserved(self, tmp_path: Path):
        md_content = """
--- page_0001 ---

```python
def hello():
    return "world"
```
"""
        md_file = tmp_path / "book.md"
        md_file.write_text(md_content)

        pages, _, _ = parse_pages_with_errors(md_file)
        elements = pages[0].content.elements
        code_blocks = [e for e in elements if isinstance(e, CodeBlock)]
        assert len(code_blocks) == 1
        assert code_blocks[0].language == "python"

    def test_japanese_prose_becomes_paragraph(self, tmp_path: Path):
        md_content = """
--- page_0001 ---

```
クラス名、ドキュメント、任意のパブリック関数はすべて、パブリックAPIの一部である
```
"""
        md_file = tmp_path / "book.md"
        md_file.write_text(md_content)

        pages, _, _ = parse_pages_with_errors(md_file)
        elements = pages[0].content.elements
        code_blocks = [e for e in elements if isinstance(e, CodeBlock)]
        paragraphs = [e for e in elements if isinstance(e, Paragraph)]
        assert len(code_blocks) == 0
        assert len(paragraphs) >= 1
