"""Tests for code block (code fence) parsing and transformation."""

from __future__ import annotations

from pathlib import Path

from src.book_converter.models import CodeBlock, Paragraph
from src.book_converter.parser.page import _collect_code_block, _is_code_fence, parse_pages_with_errors
from src.book_converter.transformer import transform_code_block


class TestIsCodeFence:
    """Test code fence line detection."""

    def test_simple_fence(self):
        is_fence, lang = _is_code_fence("```")
        assert is_fence is True
        assert lang == ""

    def test_fence_with_language(self):
        is_fence, lang = _is_code_fence("```python")
        assert is_fence is True
        assert lang == "python"

    def test_fence_with_language_and_spaces(self):
        is_fence, lang = _is_code_fence("```  java  ")
        assert is_fence is True
        assert lang == "java"

    def test_indented_fence(self):
        is_fence, lang = _is_code_fence("  ```")
        assert is_fence is True
        assert lang == ""

    def test_not_a_fence(self):
        is_fence, _ = _is_code_fence("regular text")
        assert is_fence is False

    def test_empty_line(self):
        is_fence, _ = _is_code_fence("")
        assert is_fence is False


class TestCollectCodeBlock:
    """Test code block collection from lines."""

    def test_simple_code_block(self):
        lines = ["```", "print('hello')", "```"]
        block, next_idx = _collect_code_block(lines, 0)
        assert block is not None
        assert block.text == "print('hello')"
        assert block.language == ""
        assert next_idx == 3

    def test_code_block_with_language(self):
        lines = ["```python", "def foo():", "    return 42", "```"]
        block, next_idx = _collect_code_block(lines, 0)
        assert block is not None
        assert block.text == "def foo():\n    return 42"
        assert block.language == "python"
        assert next_idx == 4

    def test_empty_code_block(self):
        lines = ["```", "```"]
        block, next_idx = _collect_code_block(lines, 0)
        assert block is not None
        assert block.text == ""
        assert next_idx == 2

    def test_multiline_code_block(self):
        lines = ["```", "line1", "line2", "line3", "```", "after"]
        block, next_idx = _collect_code_block(lines, 0)
        assert block is not None
        assert block.text == "line1\nline2\nline3"
        assert next_idx == 5

    def test_unclosed_code_block(self):
        lines = ["```", "line1", "line2"]
        block, next_idx = _collect_code_block(lines, 0)
        assert block is not None
        assert block.text == "line1\nline2"
        assert next_idx == 3

    def test_code_block_not_at_start(self):
        lines = ["before", "```", "code", "```", "after"]
        block, next_idx = _collect_code_block(lines, 1)
        assert block is not None
        assert block.text == "code"
        assert next_idx == 4


class TestTransformCodeBlock:
    """Test CodeBlock to XML transformation."""

    def test_simple_code_block(self):
        block = CodeBlock(text="print('hello')")
        elem = transform_code_block(block)
        assert elem.tag == "code"
        assert elem.text == "print('hello')"
        assert elem.get("readAloud") == "false"

    def test_code_block_with_language(self):
        block = CodeBlock(text="def foo(): pass", language="python")
        elem = transform_code_block(block)
        assert elem.get("language") == "python"
        assert elem.text == "def foo(): pass"

    def test_code_block_without_language(self):
        block = CodeBlock(text="some code")
        elem = transform_code_block(block)
        assert elem.get("language") is None

    def test_code_block_always_read_aloud_false(self):
        block = CodeBlock(text="code")
        elem = transform_code_block(block)
        assert elem.get("readAloud") == "false"


class TestCodeBlockIntegration:
    """Test code block parsing in full page pipeline."""

    def test_page_with_code_block(self, tmp_path: Path):
        md_content = """
--- page_0001 ---

Some text before code.

```
print("hello")
```

Some text after code.
"""
        md_file = tmp_path / "book.md"
        md_file.write_text(md_content)

        pages, errors, _ = parse_pages_with_errors(md_file)
        assert len(pages) == 1

        elements = pages[0].content.elements
        # Should have: Paragraph, CodeBlock, Paragraph
        types = [type(e).__name__ for e in elements]
        assert "CodeBlock" in types

        code_blocks = [e for e in elements if isinstance(e, CodeBlock)]
        assert len(code_blocks) == 1
        assert code_blocks[0].text == 'print("hello")'

    def test_page_with_language_code_block(self, tmp_path: Path):
        md_content = """
--- page_0001 ---

```python
def hello():
    return "world"
```
"""
        md_file = tmp_path / "book.md"
        md_file.write_text(md_content)

        pages, errors, _ = parse_pages_with_errors(md_file)
        elements = pages[0].content.elements
        code_blocks = [e for e in elements if isinstance(e, CodeBlock)]
        assert len(code_blocks) == 1
        assert code_blocks[0].language == "python"
        assert "def hello():" in code_blocks[0].text

    def test_page_with_multiple_code_blocks(self, tmp_path: Path):
        md_content = """
--- page_0001 ---

```
code block 1
```

text between

```
code block 2
```
"""
        md_file = tmp_path / "book.md"
        md_file.write_text(md_content)

        pages, errors, _ = parse_pages_with_errors(md_file)
        elements = pages[0].content.elements
        code_blocks = [e for e in elements if isinstance(e, CodeBlock)]
        assert len(code_blocks) == 2
        assert code_blocks[0].text == "code block 1"
        assert code_blocks[1].text == "code block 2"

    def test_code_block_not_merged_with_paragraph(self, tmp_path: Path):
        md_content = """
--- page_0001 ---

paragraph before
```
code here
```
paragraph after
"""
        md_file = tmp_path / "book.md"
        md_file.write_text(md_content)

        pages, errors, _ = parse_pages_with_errors(md_file)
        elements = pages[0].content.elements

        paragraphs = [e for e in elements if isinstance(e, Paragraph)]
        code_blocks = [e for e in elements if isinstance(e, CodeBlock)]

        assert len(paragraphs) == 2
        assert len(code_blocks) == 1
        assert "paragraph before" in paragraphs[0].text
        assert "paragraph after" in paragraphs[1].text
        assert code_blocks[0].text == "code here"
