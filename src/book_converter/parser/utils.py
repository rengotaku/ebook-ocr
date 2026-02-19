"""Utility functions for parser package."""

from __future__ import annotations

import re
from pathlib import Path

from src.book_converter.models import MarkerStats, MarkerType

# ============================================================
# List Detection Constants
# ============================================================

# Unordered list markers (bullet points)
BULLET_MARKERS = (
    "●",
    "○",
    "◎",  # Circle variants
    "•",
    "·",
    "・",  # Dot variants
    "◆",
    "◇",  # Diamond variants
    "■",
    "□",  # Square variants
    "▶",
    "▷",
    "►",  # Triangle variants
    "-",
    "*",  # Standard markdown
)

# Ordered list patterns (compiled regex)
ORDERED_LIST_PATTERN = re.compile(
    r"^\s*("
    r"[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]"  # Circled numbers
    r"|[（(]\d+[)）]"  # (1) (2) etc
    r"|\d+[.．)）]"  # 1. 2. etc
    r")\s*(.*)$"
)


def is_list_line(line: str) -> tuple[bool, str, str]:
    """Check if a line is a list item.

    Args:
        line: The line to check.

    Returns:
        Tuple of (is_list, list_type, content).
        - is_list: True if this is a list item
        - list_type: "unordered" or "ordered"
        - content: The text content after the marker
    """
    stripped = line.strip()
    if not stripped:
        return False, "", ""

    # Check unordered markers
    for marker in BULLET_MARKERS:
        if stripped.startswith(marker):
            # Ensure there's content after marker (with optional space)
            rest = stripped[len(marker) :].lstrip()
            if rest:  # Has content
                return True, "unordered", rest

    # Check ordered markers
    match = ORDERED_LIST_PATTERN.match(stripped)
    if match:
        content = match.group(2).strip()
        if content:  # Has content
            return True, "ordered", content

    return False, "", ""


def get_read_aloud_from_stack(stack: list[str]) -> bool:
    """Get readAloud value from marker stack.

    Args:
        stack: List of marker types ("content" or "skip")

    Returns:
        True by default, False only if top of stack is "skip"

    Example:
        >>> get_read_aloud_from_stack([])
        True
        >>> get_read_aloud_from_stack(["content"])
        True
        >>> get_read_aloud_from_stack(["skip"])
        False
        >>> get_read_aloud_from_stack(["content", "skip"])
        False
        >>> get_read_aloud_from_stack(["skip", "content"])
        True
    """
    if not stack:
        return True  # Default: readAloud=true

    top = stack[-1]
    return top != "skip"


def count_markers(input_path: Path) -> MarkerStats:
    """Count marker occurrences in a Markdown file.

    Args:
        input_path: Path to the Markdown file.

    Returns:
        MarkerStats with counts for toc, content, and skip markers.
    """
    # Import here to avoid circular dependency
    from src.book_converter.parser.toc import parse_content_marker, parse_toc_marker

    with open(input_path, encoding="utf-8") as f:
        content = f.read()

    toc_count = 0
    content_count = 0
    skip_count = 0

    for line in content.split("\n"):
        marker = parse_toc_marker(line)
        if marker == MarkerType.TOC_START:
            toc_count += 1
            continue

        marker = parse_content_marker(line)
        if marker == MarkerType.CONTENT_START:
            content_count += 1
        elif marker == MarkerType.SKIP_START:
            skip_count += 1

    return MarkerStats(toc=toc_count, content=content_count, skip=skip_count)
