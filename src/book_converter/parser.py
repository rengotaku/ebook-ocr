"""Parser module for book markdown to XML conversion.

Provides functions to parse Markdown content into structured data models.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterator

from src.book_converter.models import (
    Page,
    PageAnnouncement,
    Content,
    Heading,
    Paragraph,
    List,
    Figure,
    PageMetadata,
    ConversionError,
    MarkerType,
    MarkerStats,
    TocEntry,
    TableOfContents,
)

# Optional LLM-based TOC classifier
try:
    from src.book_converter.toc_classifier import (
        classify_toc_entry_with_llm,
        classify_toc_batch_with_llm,
        is_llm_classification_enabled,
    )
    TOC_CLASSIFIER_AVAILABLE = True
except ImportError:
    TOC_CLASSIFIER_AVAILABLE = False


# ============================================================
# List Detection Constants
# ============================================================

# Unordered list markers (bullet points)
BULLET_MARKERS = (
    '●', '○', '◎',  # Circle variants
    '•', '·', '・',  # Dot variants
    '◆', '◇',       # Diamond variants
    '■', '□',       # Square variants
    '▶', '▷', '►',  # Triangle variants
    '-', '*',        # Standard markdown
)

# Ordered list patterns (compiled regex)
import re
ORDERED_LIST_PATTERN = re.compile(
    r'^\s*('
    r'[①②③④⑤⑥⑦⑧⑨⑩⑪⑫⑬⑭⑮⑯⑰⑱⑲⑳]'  # Circled numbers
    r'|[（(]\d+[)）]'                           # (1) (2) etc
    r'|\d+[.．)）]'                              # 1. 2. etc
    r')\s*(.*)$'
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
            rest = stripped[len(marker):].lstrip()
            if rest:  # Has content
                return True, "unordered", rest

    # Check ordered markers
    match = ORDERED_LIST_PATTERN.match(stripped)
    if match:
        content = match.group(2).strip()
        if content:  # Has content
            return True, "ordered", content

    return False, "", ""


def parse_toc_marker(line: str) -> MarkerType | None:
    """Parse a TOC marker line.

    Returns MarkerType.TOC_START or TOC_END if line is a toc marker.
    Case insensitive.

    Args:
        line: A line from the Markdown file.

    Returns:
        MarkerType.TOC_START for <!-- toc -->, MarkerType.TOC_END for <!-- /toc -->,
        None otherwise.

    Example:
        >>> parse_toc_marker("<!-- toc -->")
        MarkerType.TOC_START
        >>> parse_toc_marker("<!-- /toc -->")
        MarkerType.TOC_END
        >>> parse_toc_marker("<!--   TOC   -->")
        MarkerType.TOC_START
    """
    import re

    # Pattern: <!-- [optional /]toc --> (case insensitive, flexible whitespace)
    pattern = r"<!--\s*(/?)\s*[Tt][Oo][Cc]\s*-->"
    match = re.search(pattern, line)

    if match:
        slash = match.group(1)
        return MarkerType.TOC_END if slash else MarkerType.TOC_START

    return None


def parse_content_marker(line: str) -> MarkerType | None:
    """Parse content/skip marker line.

    Returns:
        MarkerType.CONTENT_START for <!-- content -->
        MarkerType.CONTENT_END for <!-- /content -->
        MarkerType.SKIP_START for <!-- skip -->
        MarkerType.SKIP_END for <!-- /skip -->
        None otherwise

    Example:
        >>> parse_content_marker("<!-- content -->")
        MarkerType.CONTENT_START
        >>> parse_content_marker("<!-- /content -->")
        MarkerType.CONTENT_END
        >>> parse_content_marker("<!-- skip -->")
        MarkerType.SKIP_START
        >>> parse_content_marker("<!-- /skip -->")
        MarkerType.SKIP_END
    """
    import re

    # Content marker pattern
    content_pattern = r"<!--\s*(/?)\s*[Cc][Oo][Nn][Tt][Ee][Nn][Tt]\s*-->"
    match = re.search(content_pattern, line)
    if match:
        slash = match.group(1)
        return MarkerType.CONTENT_END if slash else MarkerType.CONTENT_START

    # Skip marker pattern
    skip_pattern = r"<!--\s*(/?)\s*[Ss][Kk][Ii][Pp]\s*-->"
    match = re.search(skip_pattern, line)
    if match:
        slash = match.group(1)
        return MarkerType.SKIP_END if slash else MarkerType.SKIP_START

    return None


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


def normalize_toc_line(line: str) -> str:
    """Normalize TOC line by removing markdown prefixes and emphasis markers.

    Removes heading markers (###), list markers (-, *) from the beginning,
    and ** emphasis markers from anywhere in the line.

    Args:
        line: Raw line from TOC section.

    Returns:
        Normalized line with prefixes and emphasis removed.

    Example:
        >>> normalize_toc_line("#### 2.1.3 SLI")
        "2.1.3 SLI"
        >>> normalize_toc_line("- 2.1.4 エラーバジェット")
        "2.1.4 エラーバジェット"
        >>> normalize_toc_line("**Episode 24**")
        "Episode 24"
        >>> normalize_toc_line("### **Episode 24**")
        "Episode 24"
    """
    import re
    # Remove heading markers (###), list markers (-, *) from the beginning
    line = re.sub(r'^[#\-*]+\s*', '', line.strip())
    # Remove ** emphasis markers
    line = re.sub(r'\*\*', '', line)
    return line


def merge_toc_lines(lines: list[str]) -> list[str]:
    """Merge TOC lines that are split across multiple lines.

    Patterns to merge:
    - "Chapter" + "N Title" → "Chapter N Title"
    - "Episode NN" + "Title" → "Episode NN Title"
    - "Column" + "Title" → "Column Title"
    - "第N章" already complete, no merge needed

    Empty lines between entries do not prevent merging.

    Args:
        lines: List of TOC lines (may be split)

    Returns:
        List of merged TOC lines

    Example:
        >>> merge_toc_lines(["Chapter", "1 Title"])
        ["Chapter 1 Title"]
        >>> merge_toc_lines(["Episode 01", "Title"])
        ["Episode 01 Title"]
        >>> merge_toc_lines(["Column", "", "Title"])
        ["Column Title"]
    """
    import re

    if not lines:
        return []

    result = []
    idx = 0

    while idx < len(lines):
        line = lines[idx].strip()

        # Skip empty lines for now (they'll be handled in context)
        if not line:
            idx += 1
            continue

        # Check if this line is an incomplete pattern that needs merging
        needs_merge = False
        merge_pattern = None

        # Pattern 1: Just "Chapter" (case insensitive)
        if re.match(r'^[Cc][Hh][Aa][Pp][Tt][Ee][Rr]$', line):
            needs_merge = True
            merge_pattern = 'chapter'

        # Pattern 2: "Episode NN" without title
        elif re.match(r'^[Ee][Pp][Ii][Ss][Oo][Dd][Ee]\s+\d+$', line):
            needs_merge = True
            merge_pattern = 'episode'

        # Pattern 3: Just "Column" (case insensitive)
        elif re.match(r'^[Cc][Oo][Ll][Uu][Mm][Nn]$', line):
            needs_merge = True
            merge_pattern = 'column'

        if needs_merge:
            # Find next non-empty line to merge with
            next_idx = idx + 1
            next_line = ""

            while next_idx < len(lines):
                candidate = lines[next_idx].strip()
                if candidate:
                    next_line = candidate
                    break
                next_idx += 1

            # Validate that the next line is appropriate for merging
            should_merge = False
            if next_line:
                if merge_pattern == 'chapter':
                    # For Chapter, next line should start with a digit (N Title format)
                    should_merge = bool(re.match(r'^\d+\s+', next_line))
                elif merge_pattern == 'episode':
                    # For Episode, any non-empty line is acceptable as title
                    should_merge = True
                elif merge_pattern == 'column':
                    # For Column, any non-empty line is acceptable as title
                    should_merge = True

            # Merge if validation passed
            if should_merge and next_line:
                merged = f"{line} {next_line}"
                result.append(merged)
                idx = next_idx + 1
            else:
                # Validation failed or no next line, keep as is
                result.append(line)
                if next_line:
                    # Keep the next line separate too
                    idx += 1
                else:
                    idx += 1
        else:
            # No merge needed, keep line as is
            result.append(line)
            idx += 1

    return result


def normalize_toc_text(lines: list[str]) -> str:
    """Normalize TOC lines into a single text string.

    Processes TOC marker content by:
    1. Normalizing each line with normalize_toc_line
    2. Replacing newlines with spaces
    3. Compressing consecutive whitespace to single space

    This ensures that entries split across multiple lines are properly merged.

    Args:
        lines: List of raw lines from TOC section

    Returns:
        Normalized text with compressed whitespace

    Example:
        >>> normalize_toc_text(["Episode 01", "Title here"])
        "Episode 01 Title here"
        >>> normalize_toc_text(["Chapter", "", "1 Title"])
        "Chapter 1 Title"
        >>> normalize_toc_text(["Line  with   spaces"])
        "Line with spaces"
    """
    import re
    # Normalize each line and join with space
    normalized = [normalize_toc_line(line) for line in lines]
    text = ' '.join(normalized)
    # Compress consecutive whitespace to single space
    return re.sub(r'\s+', ' ', text).strip()


def split_toc_entries(normalized_text: str) -> list[str]:
    """Split normalized TOC text into individual entries.

    Detects entry boundaries by looking for patterns:
    - Chapter N (case insensitive)
    - Section N.N (case insensitive)
    - Subsection N.N.N (case insensitive)
    - Episode NN
    - Column (case insensitive)
    - 第N章

    Args:
        normalized_text: Normalized TOC text (from normalize_toc_text)

    Returns:
        List of individual entry strings

    Example:
        >>> split_toc_entries("Chapter 1 Title Section 1.1 Text")
        ["Chapter 1 Title", "Section 1.1 Text"]
        >>> split_toc_entries("第1章 タイトル 第2章 次")
        ["第1章 タイトル", "第2章 次"]
    """
    import re
    if not normalized_text.strip():
        return []

    # Pattern to match entry start markers
    # Lookahead to split before these patterns:
    # - Chapter N (case insensitive)
    # - Section N.N (case insensitive) - NEW
    # - Subsection N.N.N (case insensitive) - NEW
    # - Episode NN (case insensitive)
    # - Column (case insensitive)
    # - 第N章
    # - N.N.N (subsection)
    # - N.N (section)
    # - N (standalone chapter number at start or after whitespace)
    pattern = (
        r'(?='
        r'(?:Chapter|CHAPTER|chapter)\s+\d+|'
        r'(?:Section|SECTION|section)\s+\d+\.\d+|'
        r'(?:Subsection|SUBSECTION|subsection)\s+\d+\.\d+\.\d+|'
        r'(?:Episode|EPISODE|episode)\s+\d+|'
        r'(?:Column|COLUMN|column)\s+|'
        r'第\d+章|'
        r'\d+\.\d+\.\d+\s|'
        r'\d+\.\d+\s|'
        r'(?:^|\s)\d+\s+(?=[^\d\.])'
        r')'
    )

    entries = re.split(pattern, normalized_text)
    # Filter empty entries and strip whitespace
    return [e.strip() for e in entries if e.strip()]


def parse_toc_lines(lines: list[str]) -> list[TocEntry]:
    """Parse TOC lines into TocEntry objects.

    Processes each line individually as a TOC entry.
    Format: # Chapter N Title / ## Section N.N Title / ### Subsection N.N.N Title

    Args:
        lines: List of TOC lines

    Returns:
        List of TocEntry objects
    """
    entries = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Normalize the line (remove # prefix)
        normalized = normalize_toc_line(stripped)
        entry = parse_toc_entry(normalized)
        if entry is not None:
            entries.append(entry)

    return entries


def parse_toc_entry(line: str) -> TocEntry | None:
    """Parse a TOC entry line.

    Attempts LLM-based classification if enabled (via USE_LLM_TOC_CLASSIFIER env var),
    then falls back to rule-based patterns.

    Patterns:
    - 第N章 タイトル ... ページ番号
    - N.N タイトル ... ページ番号
    - N.N.N タイトル ... ページ番号
    - その他 (はじめに, おわりに, etc.)

    Args:
        line: A line from the TOC.

    Returns:
        TocEntry if line matches a TOC pattern, None otherwise.

    Example:
        >>> parse_toc_entry("第1章 SREとは ... 15")
        TocEntry(text="SREとは", level="chapter", number="1", page="15")
        >>> parse_toc_entry("2.1 SLOの理解 ─── 30")
        TocEntry(text="SLOの理解", level="section", number="2.1", page="30")
    """
    import re

    if not line.strip():
        return None

    # Try LLM classification first if enabled
    if TOC_CLASSIFIER_AVAILABLE and is_llm_classification_enabled():
        # Extract page number before LLM classification
        page_number = ""
        line_without_page = line

        # Extract page number using existing patterns
        dot_match = re.search(r"\.{2,}\s*(\d+)\s*$", line)
        if dot_match:
            page_number = dot_match.group(1)
            line_without_page = line[: dot_match.start()]
        else:
            dash_match = re.search(r"[─\-]{2,}\s*(\d+)\s*$", line)
            if dash_match:
                page_number = dash_match.group(1)
                line_without_page = line[: dash_match.start()]
            else:
                space_match = re.search(r"\s{3,}(\d+)\s*$", line)
                if space_match:
                    page_number = space_match.group(1)
                    line_without_page = line[: space_match.start()]

        # Normalize before LLM
        line_normalized = normalize_toc_line(line_without_page)

        llm_result = classify_toc_entry_with_llm(line_normalized)
        if llm_result:
            # Use LLM classification with extracted page number
            return TocEntry(
                text=llm_result.text,
                level=llm_result.level,
                number=llm_result.number,
                page=page_number,
            )

    # Fallback to rule-based classification

    # Extract page number first (before removing it from title)
    page_number = ""

    # Try dot leader pattern: ... N
    dot_match = re.search(r"\.{2,}\s*(\d+)\s*$", line)
    if dot_match:
        page_number = dot_match.group(1)
        line = line[: dot_match.start()]

    # Try dash leader pattern: ─── N or --- N
    if not page_number:
        dash_match = re.search(r"[─\-]{2,}\s*(\d+)\s*$", line)
        if dash_match:
            page_number = dash_match.group(1)
            line = line[: dash_match.start()]

    # Try space leader pattern: (3+ spaces) N
    if not page_number:
        space_match = re.search(r"\s{3,}(\d+)\s*$", line)
        if space_match:
            page_number = space_match.group(1)
            line = line[: space_match.start()]

    # Normalize: remove markdown prefixes (###, -, *) but preserve structure keywords
    line = normalize_toc_line(line)

    # NEW FORMAT: # Chapter N Title (with markdown prefix stripped)
    # Note: normalize_toc_line removes # prefixes, so we check the original pattern
    chapter_new_pattern = r"^Chapter\s+(\d+)\s*(.*)$"
    match = re.match(chapter_new_pattern, line, re.IGNORECASE)
    if match:
        number = match.group(1)
        title = (match.group(2) or "").strip()
        return TocEntry(
            text=title,
            level=1,
            number=number,
            page=page_number,
        )

    # NEW FORMAT: ## Section N.N Title
    section_new_pattern = r"^Section\s+(\d+\.\d+)\s*(.*)$"
    match = re.match(section_new_pattern, line, re.IGNORECASE)
    if match:
        number = match.group(1)
        title = (match.group(2) or "").strip()
        return TocEntry(
            text=title,
            level=2,
            number=number,
            page=page_number,
        )

    # NEW FORMAT: ### Subsection N.N.N Title
    subsection_new_pattern = r"^Subsection\s+(\d+\.\d+\.\d+)\s*(.*)$"
    match = re.match(subsection_new_pattern, line, re.IGNORECASE)
    if match:
        number = match.group(1)
        title = (match.group(2) or "").strip()
        return TocEntry(
            text=title,
            level=3,
            number=number,
            page=page_number,
        )

    # Legacy patterns below for backward compatibility

    # Chapter pattern 1: 第N章 タイトル
    chapter_pattern = r"^第(\d+)章\s+(.+)$"
    match = re.match(chapter_pattern, line)
    if match:
        return TocEntry(
            text=match.group(2).strip(),
            level=1,
            number=match.group(1),
            page=page_number,
        )

    # Chapter pattern 2: Chapter N タイトル (case insensitive) - legacy
    chapter_en_pattern = r"^[Cc][Hh][Aa][Pp][Tt][Ee][Rr]\s+(\d+)(?:\s+(.+))?$"
    match = re.match(chapter_en_pattern, line)
    if match:
        title = match.group(2).strip() if match.group(2) else ""
        return TocEntry(
            text=title,
            level=1,
            number=match.group(1),
            page=page_number,
        )

    # Level 5 pattern (must come first): N.N.N.N.N タイトル
    level5_pattern = r"^(\d+\.\d+\.\d+\.\d+\.\d+)\s+(.+)$"
    match = re.match(level5_pattern, line)
    if match:
        return TocEntry(
            text=match.group(2).strip(),
            level=5,
            number=match.group(1),
            page=page_number,
        )

    # Level 4 pattern: N.N.N.N タイトル
    level4_pattern = r"^(\d+\.\d+\.\d+\.\d+)\s+(.+)$"
    match = re.match(level4_pattern, line)
    if match:
        return TocEntry(
            text=match.group(2).strip(),
            level=4,
            number=match.group(1),
            page=page_number,
        )

    # Subsection pattern (level 3): N.N.N タイトル
    subsection_pattern = r"^(\d+\.\d+\.\d+)\s+(.+)$"
    match = re.match(subsection_pattern, line)
    if match:
        return TocEntry(
            text=match.group(2).strip(),
            level=3,
            number=match.group(1),
            page=page_number,
        )

    # Section pattern (level 2): N.N タイトル
    section_pattern = r"^(\d+\.\d+)\s+(.+)$"
    match = re.match(section_pattern, line)
    if match:
        return TocEntry(
            text=match.group(2).strip(),
            level=2,
            number=match.group(1),
            page=page_number,
        )

    # Standalone chapter pattern: N タイトル (single digit, no "Chapter" prefix)
    # Example: "4 「進捗管理」で失敗"
    standalone_chapter_pattern = r"^(\d)\s+(.+)$"
    match = re.match(standalone_chapter_pattern, line)
    if match:
        return TocEntry(
            text=match.group(2).strip(),
            level=1,
            number=match.group(1),
            page=page_number,
        )

    # Other pattern (no number prefix)
    # Default to level 1 for entries without clear hierarchy markers
    if line:
        return TocEntry(
            text=line,
            level=1,
            number="",
            page=page_number,
        )

    return None


def parse_page_marker(line: str) -> tuple[str, str] | None:
    """Parse a page marker line.

    Args:
        line: A line from the Markdown file.

    Returns:
        Tuple of (page_number, source_file) if the line is a page marker,
        None otherwise.

    Example:
        >>> parse_page_marker("--- Page 1 (page_0001.png) ---")
        ("1", "page_0001.png")
        >>> parse_page_marker("--- page_0001 ---")
        ("1", "page_0001")
    """
    import re

    # Pattern 1: --- Page N (filename) ---
    # Case-insensitive, handles extra spaces
    # Page number is required (at least one digit)
    pattern1 = r"---\s+[Pp]age\s+(\d+)\s+\((.+?)\)\s+---"
    match = re.search(pattern1, line)
    if match:
        page_number = match.group(1)
        source_file = match.group(2)
        return (page_number, source_file)

    # Pattern 2: --- page_XXXX --- (simple format)
    # Extracts page number from page_XXXX identifier
    pattern2 = r"---\s+page_(\d+)\s+---"
    match = re.search(pattern2, line)
    if match:
        page_num_str = match.group(1)
        # Remove leading zeros for page number, keep original for source_file
        page_number = str(int(page_num_str))
        source_file = f"page_{page_num_str}"
        return (page_number, source_file)

    return None


def extract_page_number(line: str, verbose: bool = False) -> tuple[str, str]:
    """Extract page number and source file from a page marker line.

    Args:
        line: A page marker line.
        verbose: If True, print debug info for unrecognized potential markers.

    Returns:
        Tuple of (page_number, source_file). Returns ("", "") if invalid.
    """
    import re
    import sys

    # First try the standard pattern with page number
    result = parse_page_marker(line)
    if result is not None:
        return result

    # Try pattern without page number (handles missing page numbers)
    pattern = r"---\s+[Pp]age\s+\((.+?)\)\s+---"
    match = re.search(pattern, line)
    if match:
        source_file = match.group(1)
        return ("", source_file)

    # Try pattern: --- Page: filename ---
    pattern_colon = r"---\s+[Pp]age:\s*(.+?)\s*---"
    match = re.search(pattern_colon, line)
    if match:
        source_file = match.group(1).strip()
        # Extract page number from source_file (e.g., page_0001.png -> 1)
        page_num_match = re.search(r"page_(\d+)", source_file)
        if page_num_match:
            page_number = str(int(page_num_match.group(1)))
            return (page_number, source_file)
        return ("", source_file)

    # Debug: check if this looks like a page marker but wasn't recognized
    if verbose and line.strip().startswith("---") and "page" in line.lower():
        print(f"[DEBUG] Unrecognized potential page marker: {line.strip()!r}", file=sys.stderr)

    return ("", "")


def create_page_announcement(page_number: str) -> PageAnnouncement | None:
    """Create a PageAnnouncement for the given page number.

    Args:
        page_number: The page number string.

    Returns:
        PageAnnouncement with format "Nページ", or None if page_number is empty.
    """
    if not page_number:
        return None

    text = f"{page_number}ページ"
    return PageAnnouncement(text=text, format="simple")


@dataclass
class StructureHeading:
    """Parsed structure heading with section info."""

    level: int  # 1=chapter, 2=section, 3=subsection
    number: str  # "1", "1.1", "1.1.1"
    title: str  # Title text after number
    raw_text: str  # Original heading text


def parse_structure_heading(line: str) -> StructureHeading | None:
    """Parse a structure heading line.

    Recognizes:
    - # Chapter N Title → level=1, number="N"
    - ## Section N.N Title → level=2, number="N.N"
    - ### Subsection N.N.N Title → level=3, number="N.N.N"

    Args:
        line: A line from the Markdown file.

    Returns:
        StructureHeading if the line matches a structure pattern, None otherwise.

    Example:
        >>> parse_structure_heading("# Chapter 1 Introduction")
        StructureHeading(level=1, number="1", title="Introduction", raw_text="Chapter 1 Introduction")
        >>> parse_structure_heading("## Section 2.3 Details")
        StructureHeading(level=2, number="2.3", title="Details", raw_text="Section 2.3 Details")
    """
    import re

    # Pattern: ^(#{1,3})\s*(.*)$
    pattern = r"^(#{1,3})\s*(.*)$"
    match = re.match(pattern, line)

    if not match:
        return None

    markers = match.group(1)
    text = match.group(2).strip()
    md_level = len(markers)

    # Try Chapter pattern: Chapter N Title
    chapter_match = re.match(r'^Chapter\s+(\d+)\s*(.*)?$', text, re.IGNORECASE)
    if chapter_match and md_level == 1:
        number = chapter_match.group(1)
        title = (chapter_match.group(2) or "").strip()
        return StructureHeading(level=1, number=number, title=title, raw_text=text)

    # Try Section pattern: Section N.N Title
    section_match = re.match(r'^Section\s+(\d+\.\d+)\s*(.*)?$', text, re.IGNORECASE)
    if section_match and md_level == 2:
        number = section_match.group(1)
        title = (section_match.group(2) or "").strip()
        return StructureHeading(level=2, number=number, title=title, raw_text=text)

    # Try Subsection pattern: Subsection N.N.N Title
    subsection_match = re.match(r'^Subsection\s+(\d+\.\d+\.\d+)\s*(.*)?$', text, re.IGNORECASE)
    if subsection_match and md_level == 3:
        number = subsection_match.group(1)
        title = (subsection_match.group(2) or "").strip()
        return StructureHeading(level=3, number=number, title=title, raw_text=text)

    return None


def parse_heading(line: str) -> Heading | None:
    """Parse a markdown heading line.

    Args:
        line: A line from the Markdown file.

    Returns:
        Heading object if the line is a heading (# - ###), None otherwise.
        Level 4+ headings are converted to level 3.

    Example:
        >>> parse_heading("# Chapter 1")
        Heading(level=1, text="Chapter 1", read_aloud=True)
        >>> parse_heading("#### Deep heading")
        Heading(level=3, text="Deep heading", read_aloud=True)
    """
    import re

    # Pattern: ^(#{1,6})\s*(.*)$
    # Must start at beginning of line (no leading whitespace)
    pattern = r"^(#{1,6})\s*(.*)$"
    match = re.match(pattern, line)

    if not match:
        return None

    markers = match.group(1)
    text = match.group(2)

    # Calculate level (1-6 from markdown, but cap at 3)
    level = len(markers)
    if level > 3:
        level = 3

    from src.book_converter.models import Heading

    return Heading(level=level, text=text, read_aloud=True)


def parse_heading_with_warning(line: str) -> tuple[Heading | None, str | None]:
    """Parse a heading and return warning if level 4+.

    Args:
        line: A line from the Markdown file.

    Returns:
        Tuple of (Heading, warning). Warning is set if level 4+ was detected.
    """
    import re

    pattern = r"^(#{1,6})\s*(.*)$"
    match = re.match(pattern, line)

    if not match:
        return (None, None)

    markers = match.group(1)
    original_level = len(markers)

    heading = parse_heading(line)

    if original_level > 3:
        warning = f"見出しlevel {original_level}階層は3階層に統合されました"
        return (heading, warning)

    return (heading, None)


def parse_paragraph_lines(lines: list[str]) -> Paragraph | None:
    """複数行を改行なしで結合してParagraphを生成

    Args:
        lines: 段落の行リスト

    Returns:
        Paragraph（改行除去済み）、空の場合はNone

    処理:
    1. 各行をstrip
    2. 空白1文字で結合
    3. 連続空白を1つに圧縮

    Example:
        >>> parse_paragraph_lines(["Line 1", "Line 2"])
        Paragraph(text="Line 1 Line 2", read_aloud=True)
        >>> parse_paragraph_lines(["日本語の", "段落です"])
        Paragraph(text="日本語の 段落です", read_aloud=True)
    """
    if not lines:
        return None

    # 各行をstripして空白で結合
    text = " ".join(line.strip() for line in lines)

    # 連続空白を1つに圧縮
    import re
    text = re.sub(r'\s+', ' ', text).strip()

    if not text:
        return None

    from src.book_converter.models import Paragraph

    return Paragraph(text=text, read_aloud=True)


def split_paragraphs(text: str) -> list[Paragraph]:
    """テキストを空行で分割してParagraphリストを生成

    Args:
        text: 複数段落を含むテキスト

    Returns:
        Paragraphのリスト

    処理:
    1. 空行（空白のみの行含む）で分割
    2. 各段落内の改行を除去
    3. 空の段落は除外

    Example:
        >>> split_paragraphs("Para 1\\n\\nPara 2")
        [Paragraph(text="Para 1", read_aloud=True), Paragraph(text="Para 2", read_aloud=True)]
        >>> split_paragraphs("Line 1\\nLine 2\\n\\nLine 3")
        [Paragraph(text="Line 1 Line 2", read_aloud=True), Paragraph(text="Line 3", read_aloud=True)]
    """
    import re
    from src.book_converter.models import Paragraph

    if not text.strip():
        return []

    # 空行（空白のみの行含む）で分割
    # \n\n または 空白のみの行を区切りとする
    # 改良版: 空白のみの行も空行として扱う
    paragraphs = []
    current_lines = []

    for line in text.split('\n'):
        # 空白のみの行（スペース、タブ、全角スペース含む）
        if not line.strip():
            # 現在の段落を保存
            if current_lines:
                para = parse_paragraph_lines(current_lines)
                if para is not None:
                    paragraphs.append(para)
                current_lines = []
        else:
            # 非空行を段落に追加
            current_lines.append(line)

    # 最後の段落を保存
    if current_lines:
        para = parse_paragraph_lines(current_lines)
        if para is not None:
            paragraphs.append(para)

    return paragraphs


def merge_continuation_paragraphs(paragraphs: list[Paragraph]) -> list[Paragraph]:
    """句点で終わらない段落を次の段落と結合

    Args:
        paragraphs: Paragraphのリスト

    Returns:
        結合後のParagraphリスト

    終端文字（結合しない）:
    - 句点: 。.
    - 感嘆符: !！
    - 疑問符: ?？
    - 閉じ括弧+句点: ）。」。

    Example:
        >>> p1 = Paragraph(text="これは継続", read_aloud=True)
        >>> p2 = Paragraph(text="段落です。", read_aloud=True)
        >>> merge_continuation_paragraphs([p1, p2])
        [Paragraph(text="これは継続段落です。", read_aloud=True)]
    """
    from src.book_converter.models import Paragraph

    if not paragraphs:
        return []

    if len(paragraphs) == 1:
        return paragraphs

    # 終端文字のパターン
    terminating_chars = {'。', '.', '!', '！', '?', '？'}

    result = []
    idx = 0

    while idx < len(paragraphs):
        current = paragraphs[idx]
        current_text = current.text.rstrip()

        # 終端文字チェック
        ends_with_terminator = False
        if current_text:
            last_char = current_text[-1]
            if last_char in terminating_chars:
                ends_with_terminator = True
            # 閉じ括弧+句点パターン: ）。 」。
            elif len(current_text) >= 2:
                last_two = current_text[-2:]
                if last_two in {'）。', '」。'}:
                    ends_with_terminator = True

        # 終端文字で終わる場合、または最後の段落の場合は結合しない
        if ends_with_terminator or idx == len(paragraphs) - 1:
            result.append(current)
            idx += 1
        else:
            # 次の段落と結合（空白なし - 日本語テキストのため）
            next_para = paragraphs[idx + 1]
            merged_text = f"{current_text}{next_para.text}".strip()
            merged = Paragraph(text=merged_text, read_aloud=current.read_aloud)
            # 結合した段落を次のイテレーションで処理するため、paragraphsを更新
            paragraphs[idx + 1] = merged
            idx += 1

    return result


def parse_paragraph(lines: list[str]) -> Paragraph | None:
    """Parse paragraph lines into a Paragraph object.

    Args:
        lines: List of paragraph lines.

    Returns:
        Paragraph object with joined text, or None if empty/whitespace only.

    Example:
        >>> parse_paragraph(["Line 1", "Line 2"])
        Paragraph(text="Line 1\\nLine 2", read_aloud=True)
    """
    if not lines:
        return None

    # Join lines and strip whitespace
    text = "\n".join(lines).strip()

    if not text:
        return None

    from src.book_converter.models import Paragraph

    return Paragraph(text=text, read_aloud=True)


def parse_list(lines: list[str]) -> List | None:
    """Parse list lines into a List object.

    Supports various bullet markers (●, •, -, *, etc.) and ordered markers
    (①, 1., (1), etc.).

    Args:
        lines: List of lines containing list items.

    Returns:
        List object with items tuple, or None if empty.

    Example:
        >>> parse_list(["- Item 1", "- Item 2"])
        List(items=("Item 1", "Item 2"), list_type="unordered", read_aloud=True)
        >>> parse_list(["● 項目1", "● 項目2"])
        List(items=("項目1", "項目2"), list_type="unordered", read_aloud=True)
    """
    if not lines:
        return None

    items = []
    list_type = "unordered"  # Default

    for line in lines:
        is_list, detected_type, content = is_list_line(line)
        if is_list:
            # Set list type from first item
            if not items:
                list_type = detected_type
            items.append(content)

    if not items:
        return None

    from src.book_converter.models import List

    return List(items=tuple(items), list_type=list_type, read_aloud=True)


def parse_figure_comment(line: str) -> str | None:
    """Parse a figure comment line to extract the file path.

    Args:
        line: A line from the Markdown file.

    Returns:
        File path if the line is a figure comment, None otherwise.

    Example:
        >>> parse_figure_comment("<!-- FIGURE: path/to/image.png -->")
        "path/to/image.png"
        >>> parse_figure_comment("<!-- figure: image.jpg -->")
        "image.jpg"
    """
    import re

    # Pattern: <!-- FIGURE: path --> (case insensitive)
    pattern = r"<!--\s*[Ff][Ii][Gg][Uu][Rr][Ee]:\s*(.+?)\s*-->"
    match = re.search(pattern, line)

    if match:
        path = match.group(1).strip()
        return path if path else None

    return None


def parse_figure_placeholder(line: str) -> dict | None:
    """図プレースホルダーを検出.

    [図], [図1], [図 1], [写真], [表], [イラスト], [グラフ], [チャート] を検出

    Args:
        line: テキスト行

    Returns:
        {"marker": "図1"} or None

    Example:
        >>> parse_figure_placeholder("[図1]")
        {"marker": "図1"}
        >>> parse_figure_placeholder("テキスト [写真3] テキスト")
        {"marker": "写真3"}
        >>> parse_figure_placeholder("通常のテキスト")
        None
    """
    import re

    # Pattern: [図|写真|表|イラスト|グラフ|チャート][番号・記号] ]
    pattern = r"\[(図|写真|表|イラスト|グラフ|チャート)([^\]]*)\]"
    match = re.search(pattern, line)

    if match:
        # 括弧を除去してマーカーテキストを返す
        marker = f"{match.group(1)}{match.group(2)}"
        return {"marker": marker}

    return None


def parse_figure(lines: list[str]) -> Figure | None:
    """Parse figure comment and description into a Figure object.

    Args:
        lines: List of lines that may contain a figure comment and description.

    Returns:
        Figure object if a figure comment is found, None otherwise.

    Example:
        >>> lines = [
        ...     "<!-- FIGURE: image.png -->",
        ...     "**図のタイトル**",
        ...     "図の説明文です。"
        ... ]
        >>> fig = parse_figure(lines)
        >>> fig.file
        'image.png'
    """
    if not lines:
        return None

    # Find figure comment
    file_path = None
    for line in lines:
        file_path = parse_figure_comment(line)
        if file_path:
            break

    if not file_path:
        return None

    # Extract caption and description from remaining lines
    caption = ""
    description_lines = []

    for line in lines:
        # Skip the figure comment line
        if parse_figure_comment(line):
            continue

        # Empty lines
        if not line.strip():
            continue

        # Check for bold text (caption): **text**
        import re

        bold_pattern = r"\*\*(.+?)\*\*"
        match = re.search(bold_pattern, line)

        if match and not caption:
            # First bold text becomes caption
            caption = match.group(1)
        elif line.strip():
            # Other non-empty lines become description
            description_lines.append(line.strip())

    description = "\n".join(description_lines) if description_lines else ""

    # 新形式: path と caption のみ
    return Figure(
        path=file_path,
        caption=caption,
        marker="",
    )


def parse_page_metadata(text: str) -> PageMetadata | None:
    """Parse page metadata from text.

    Args:
        text: Text that may contain page metadata (e.g., "はじめに 1 / 3").

    Returns:
        PageMetadata object if valid format is found, None otherwise.

    Example:
        >>> parse_page_metadata("はじめに 1 / 3")
        PageMetadata(text='はじめに 1 / 3', meta_type='chapter-page',
                     section_name='はじめに', current=1, total=3)
        >>> parse_page_metadata("第1節 5 / 10")
        PageMetadata(text='第1節 5 / 10', meta_type='section-page', ...)
    """
    import re

    # Pattern: [optional section name] N / M
    # section name is optional, numbers are required
    pattern = r"^(.*?)\s*(\d+)\s*/\s*(\d+)\s*$"
    match = re.match(pattern, text.strip())

    if not match:
        return None

    section_name = match.group(1).strip()
    current = int(match.group(2))
    total = int(match.group(3))

    # Determine meta_type based on section_name
    meta_type = "chapter-page"  # Default
    if "節" in section_name:
        meta_type = "section-page"
    elif not section_name:
        # No section name means unknown type
        meta_type = "chapter-page"

    return PageMetadata(
        text=text,
        meta_type=meta_type,
        section_name=section_name,
        current=current,
        total=total,
    )


def parse_pages(input_path: Path) -> Iterator[Page]:
    """Parse a Markdown file into Page objects.

    Args:
        input_path: Path to the Markdown file.

    Yields:
        Page objects parsed from the Markdown file.
    """
    # Use parse_pages_with_errors and yield only pages (ignore errors and toc)
    pages, _, _ = parse_pages_with_errors(input_path)
    yield from pages


def parse_pages_with_errors(
    input_path: Path,
    verbose: bool = False,
) -> tuple[list[Page], list[ConversionError], TableOfContents | None]:
    """Parse a Markdown file into Page objects with error tracking.

    Args:
        input_path: Path to the Markdown file.
        verbose: If True, print debug info during parsing.

    Returns:
        Tuple of (pages, errors, toc). TOC is built from all pages with TOC markers.
    """
    import os
    import sys

    # Enable verbose mode via environment variable
    verbose = verbose or os.environ.get("BOOK_CONVERTER_DEBUG", "").lower() in ("1", "true")

    with open(input_path, encoding="utf-8") as f:
        content = f.read()

    lines = content.split("\n")
    pages = []
    errors = []

    current_page_number = ""
    current_source_file = ""
    current_page_lines = []
    last_page_marker_line = 0
    page_start_line = 0

    # Track TOC across all pages
    all_toc_entries: list[TocEntry] = []
    toc_begin_page = ""
    toc_end_page = ""

    # Track marker stack across all pages (content/skip markers)
    marker_stack: list[str] = []

    # Debug: show first few lines to help diagnose format issues
    if verbose:
        print(f"[DEBUG] Parsing file: {input_path}", file=sys.stderr)
        print(f"[DEBUG] Total lines: {len(lines)}", file=sys.stderr)
        print(f"[DEBUG] First 5 lines:", file=sys.stderr)
        for i, l in enumerate(lines[:5], start=1):
            print(f"  {i}: {l!r}", file=sys.stderr)

    for line_idx, line in enumerate(lines, start=1):
        # Check if this is a page marker (including those with missing numbers)
        page_num, source_file = extract_page_number(line, verbose=verbose)
        if page_num or source_file:
            # This is a page marker
            # Save previous page if any
            if current_source_file:
                # Parse the content of the previous page
                page_obj, page_errors, toc_entries, had_toc = _parse_single_page_content(
                    current_page_number,
                    current_source_file,
                    current_page_lines,
                    page_start_line,
                    marker_stack,
                )
                pages.append(page_obj)
                errors.extend(page_errors)

                # Track TOC page range
                if had_toc and current_page_number:
                    if not toc_begin_page:
                        toc_begin_page = current_page_number
                    toc_end_page = current_page_number
                    all_toc_entries.extend(toc_entries)

                # Check for missing page number on previous page
                if not current_page_number:
                    errors.append(ConversionError(
                        error_type="PAGE_NUMBER_NOT_FOUND",
                        message="ページ番号が見つかりません",
                        page_number="",
                        line_number=last_page_marker_line,
                    ))

            # Start new page
            current_page_number = page_num
            current_source_file = source_file
            current_page_lines = []
            last_page_marker_line = line_idx
            page_start_line = line_idx
        else:
            # Add line to current page content
            current_page_lines.append(line)

    # Save final page
    if current_source_file:
        # Parse the content of the final page
        page_obj, page_errors, toc_entries, had_toc = _parse_single_page_content(
            current_page_number,
            current_source_file,
            current_page_lines,
            page_start_line,
            marker_stack,
        )
        pages.append(page_obj)
        errors.extend(page_errors)

        # Track TOC page range
        if had_toc and current_page_number:
            if not toc_begin_page:
                toc_begin_page = current_page_number
            toc_end_page = current_page_number
            all_toc_entries.extend(toc_entries)

        # Check for missing page number on final page
        if not current_page_number:
            errors.append(ConversionError(
                error_type="PAGE_NUMBER_NOT_FOUND",
                message="ページ番号が見つかりません",
                page_number="",
                line_number=last_page_marker_line,
            ))

    # Build TableOfContents if any entries found
    toc = None
    if all_toc_entries:
        toc = TableOfContents(
            entries=tuple(all_toc_entries),
            begin_page=toc_begin_page,
            end_page=toc_end_page,
        )

    return (pages, errors, toc)


def _parse_single_page_content(
    page_number: str,
    source_file: str,
    lines: list[str],
    start_line: int,
    marker_stack: list[str],
) -> tuple[Page, list[ConversionError], list[TocEntry], bool]:
    """Parse the content of a single page.

    Args:
        page_number: Page number string.
        source_file: Source file name.
        lines: Lines of content for this page.
        start_line: Starting line number in the original file.
        marker_stack: Marker stack state (mutated in place, persists across pages).

    Returns:
        Tuple of (Page, errors, toc_entries, had_toc_marker).
        had_toc_marker is True if this page contained any TOC markers.
    """
    errors = []
    content_elements = []
    figures_list = []
    metadata = None
    toc_entries = []
    in_toc = False
    had_toc_marker = False  # Track if this page has any TOC markers
    # marker_stack is passed as argument (persists across pages)
    toc_lines: list[str] = []  # Collect TOC lines for merging

    # Parse content line by line
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        line_num = start_line + idx + 1

        # Check for TOC markers
        toc_marker = parse_toc_marker(line)
        if toc_marker == MarkerType.TOC_START:
            in_toc = True
            had_toc_marker = True
            toc_lines = []  # Start collecting TOC lines
            idx += 1
            continue
        elif toc_marker == MarkerType.TOC_END:
            # Process collected TOC lines
            if toc_lines:
                # Try LLM batch processing first if enabled
                if TOC_CLASSIFIER_AVAILABLE and is_llm_classification_enabled():
                    # For LLM, normalize each line but preserve structure with newlines
                    normalized_lines = [normalize_toc_line(line) for line in toc_lines]
                    # Filter out empty lines
                    normalized_lines = [line for line in normalized_lines if line.strip()]
                    raw_text = '\n'.join(normalized_lines)
                    llm_entries = classify_toc_batch_with_llm(raw_text, preserve_newlines=True)
                    if llm_entries:
                        # LLM succeeded - use its results directly
                        toc_entries.extend(llm_entries)
                    else:
                        # LLM failed - fallback to rule-based
                        toc_entries.extend(parse_toc_lines(toc_lines))
                else:
                    # LLM not enabled - use rule-based
                    toc_entries.extend(parse_toc_lines(toc_lines))
            in_toc = False
            toc_lines = []
            idx += 1
            continue

        # Check for content/skip markers
        content_marker = parse_content_marker(line)
        if content_marker == MarkerType.CONTENT_START:
            marker_stack.append("content")
            idx += 1
            continue
        elif content_marker == MarkerType.CONTENT_END:
            if marker_stack and marker_stack[-1] == "content":
                marker_stack.pop()
            idx += 1
            continue
        elif content_marker == MarkerType.SKIP_START:
            marker_stack.append("skip")
            idx += 1
            continue
        elif content_marker == MarkerType.SKIP_END:
            if marker_stack and marker_stack[-1] == "skip":
                marker_stack.pop()
            idx += 1
            continue

        # If inside TOC, collect lines for later merging and parsing
        if in_toc:
            toc_lines.append(line)
            idx += 1
            continue

        # Get current readAloud value from marker stack
        read_aloud = get_read_aloud_from_stack(marker_stack)

        # Check for deep heading warning
        heading, warning = parse_heading_with_warning(line)
        if warning is not None:
            errors.append(ConversionError(
                error_type="DEEP_HEADING",
                message=warning,
                page_number=page_number,
                line_number=line_num,
            ))

        # Check for heading
        if heading is not None:
            # Apply readAloud state
            heading = Heading(level=heading.level, text=heading.text, read_aloud=read_aloud)
            content_elements.append(heading)
            idx += 1
            continue

        # Check for figure comment
        fig_path = parse_figure_comment(line)
        if fig_path is not None:
            # Collect lines for figure parsing
            fig_lines = []
            fig_idx = idx
            while fig_idx < len(lines) and fig_idx < idx + 10:  # Look ahead up to 10 lines
                fig_line = lines[fig_idx]
                if not fig_line.strip():
                    # Empty line ends figure block
                    break
                fig_lines.append(fig_line)
                fig_idx += 1

            fig = parse_figure(fig_lines)
            if fig is not None:
                figures_list.append(fig)
            idx = fig_idx
            continue

        # Check for page metadata (N / M pattern)
        page_meta = parse_page_metadata(line.strip())
        if page_meta is not None:
            metadata = page_meta
            idx += 1
            continue

        # Check for list item (supports ●, •, -, *, ①, 1., etc.)
        is_list, _, _ = is_list_line(line)
        if is_list:
            # Collect consecutive list items (minimum 2 for recognition)
            list_lines = [line]
            list_idx = idx + 1
            while list_idx < len(lines):
                list_line = lines[list_idx]
                if not list_line.strip():
                    # Empty line ends list
                    break
                next_is_list, _, _ = is_list_line(list_line)
                if next_is_list:
                    list_lines.append(list_line)
                    list_idx += 1
                else:
                    # Non-list line ends list
                    break

            # Only treat as list if 2+ consecutive items
            if len(list_lines) >= 2:
                lst = parse_list(list_lines)
                if lst is not None:
                    # Apply readAloud state
                    lst = List(items=lst.items, read_aloud=read_aloud)
                    content_elements.append(lst)
                idx = list_idx
                continue
            # Single item: fall through to paragraph handling

        # Check for paragraph (non-empty, non-special line)
        if line.strip():
            # Collect consecutive non-empty lines for paragraph
            para_lines = []
            para_idx = idx
            while para_idx < len(lines):
                para_line = lines[para_idx]
                # Stop at empty line, heading, list, or figure
                if not para_line.strip():
                    break
                if parse_heading(para_line) is not None:
                    break
                # Stop at list item (check if 2+ consecutive items follow)
                is_list_item, _, _ = is_list_line(para_line)
                if is_list_item:
                    # Look ahead to see if there are 2+ consecutive list items
                    lookahead_idx = para_idx + 1
                    if lookahead_idx < len(lines):
                        next_is_list, _, _ = is_list_line(lines[lookahead_idx])
                        if next_is_list:
                            break  # This starts a real list
                    # Single list marker: treat as part of paragraph
                if parse_figure_comment(para_line) is not None:
                    break
                if parse_page_metadata(para_line.strip()) is not None:
                    break
                # Stop at markers (toc, content, skip)
                if parse_toc_marker(para_line) is not None:
                    break
                if parse_content_marker(para_line) is not None:
                    break
                para_lines.append(para_line)
                para_idx += 1

            para = parse_paragraph(para_lines)
            if para is not None:
                # Apply readAloud state
                para = Paragraph(text=para.text, read_aloud=read_aloud)
                content_elements.append(para)
            idx = para_idx
            continue

        # Empty line, skip
        idx += 1

    # If TOC is still open at end of page, process collected lines
    if in_toc and toc_lines:
        # Try LLM batch processing first if enabled
        if TOC_CLASSIFIER_AVAILABLE and is_llm_classification_enabled():
            # For LLM, normalize each line but preserve structure with newlines
            normalized_lines = [normalize_toc_line(line) for line in toc_lines]
            # Filter out empty lines
            normalized_lines = [line for line in normalized_lines if line.strip()]
            raw_text = '\n'.join(normalized_lines)
            llm_entries = classify_toc_batch_with_llm(raw_text, preserve_newlines=True)
            if llm_entries:
                toc_entries.extend(llm_entries)
            else:
                # LLM failed - fallback to rule-based
                toc_entries.extend(parse_toc_lines(toc_lines))
        else:
            # LLM not enabled - use rule-based
            toc_entries.extend(parse_toc_lines(toc_lines))

    # Create Page object
    # Content readAloud is true if ANY child element has readAloud=true
    content_read_aloud = any(
        elem.read_aloud for elem in content_elements
    ) if content_elements else False
    content = Content(elements=tuple(content_elements), read_aloud=content_read_aloud)
    announcement = create_page_announcement(page_number)

    page = Page(
        number=page_number,
        source_file=source_file,
        content=content,
        announcement=announcement,
        figures=tuple(figures_list),
        metadata=metadata,
    )

    return (page, errors, toc_entries, had_toc_marker)


def count_markers(input_path: Path) -> MarkerStats:
    """Count marker occurrences in a Markdown file.

    Args:
        input_path: Path to the Markdown file.

    Returns:
        MarkerStats with counts for toc, content, and skip markers.
    """
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
