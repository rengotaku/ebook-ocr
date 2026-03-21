"""Filter false-positive code blocks back to paragraphs.

Code blocks detected from gray background regions may contain non-code content
such as book references, short OCR artifacts, or Japanese prose. This module
provides filtering to demote such false positives to paragraphs.
"""

from __future__ import annotations

import re

from src.book_converter.models import CodeBlock, Paragraph

# Minimum character count for a code block to be kept as-is
_MIN_CODE_LENGTH = 10

# Symbol ratio threshold for code indicators in filter context.
# Lower than code_detector's 0.08 because we only need a hint of code presence.
_CODE_SYMBOL_RATIO_THRESHOLD = 0.05

# Japanese character pattern (hiragana, katakana, CJK unified ideographs)
_JAPANESE_PATTERN = re.compile(r"[\u3040-\u309f\u30a0-\u30ff\u4e00-\u9fff]")

# Code indicator patterns (symbols and keywords that suggest real code)
# Exclude +, -, / which are common in ISBNs, URLs, book references
_CODE_INDICATOR_SYMBOLS = frozenset("{}();=<>[]&|*%#@^~\\")

_CODE_INDICATOR_KEYWORDS = [
    "def ",
    "func ",
    "fn ",
    "class ",
    "import ",
    "return ",
    "if (",
    "for (",
    "while (",
    "public ",
    "private ",
    "void ",
    "int ",
    "String ",
    "var ",
    "val ",
    "let ",
    "const ",
    "=>",
    ":=",
    "->",
    "::=",
    "std::",
    "#include",
    "#!/",
]


def _has_code_indicators(text: str) -> bool:
    """Check if text contains programming indicators.

    Returns True if text has a meaningful symbol ratio or code keywords.
    """
    if not text:
        return False

    # Check symbol ratio
    symbol_count = sum(1 for ch in text if ch in _CODE_INDICATOR_SYMBOLS)
    ratio = symbol_count / len(text)
    if ratio > _CODE_SYMBOL_RATIO_THRESHOLD:
        return True

    # Check keywords
    lower = text.lower()
    keyword_count = sum(1 for kw in _CODE_INDICATOR_KEYWORDS if kw.lower() in lower)
    if keyword_count >= 1:
        return True

    return False


def _japanese_ratio(text: str) -> float:
    """Calculate the ratio of Japanese characters in text."""
    if not text:
        return 0.0
    jp_count = len(_JAPANESE_PATTERN.findall(text))
    return jp_count / len(text)


def filter_code_block(code_block: CodeBlock) -> CodeBlock | Paragraph | None:
    """Filter a code block, returning the appropriate element type.

    Rules:
    1. Empty code blocks -> None (removed)
    2. Very short text (< _MIN_CODE_LENGTH) without code indicators -> Paragraph
    3. High Japanese ratio (> 0.3) without code indicators -> Paragraph
    4. Otherwise -> keep as CodeBlock

    Args:
        code_block: CodeBlock to evaluate.

    Returns:
        CodeBlock (kept), Paragraph (demoted), or None (removed).
    """
    text = code_block.text.strip()

    # Rule 1: Empty code blocks are removed
    if not text:
        return None

    # Rule 2: Very short text without code indicators
    if len(text) < _MIN_CODE_LENGTH and not _has_code_indicators(text):
        return Paragraph(text=text, read_aloud=True)

    # Rule 3: High Japanese ratio without code indicators
    jp_ratio = _japanese_ratio(text)
    if jp_ratio > 0.3 and not _has_code_indicators(text):
        return Paragraph(text=text, read_aloud=True)

    # Keep as code block
    return code_block
