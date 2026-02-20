"""TOC (Table of Contents) parsing functions."""

from __future__ import annotations

import re

from src.book_converter.models import MarkerType, TocEntry

# Optional LLM-based TOC classifier
try:
    from src.book_converter.toc_classifier import (
        classify_toc_entry_with_llm,
        is_llm_classification_enabled,
    )

    TOC_CLASSIFIER_AVAILABLE = True
except ImportError:
    TOC_CLASSIFIER_AVAILABLE = False


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
    # Remove heading markers (###), list markers (-, *) from the beginning
    line = re.sub(r"^[#\-*]+\s*", "", line.strip())
    # Remove ** emphasis markers
    line = re.sub(r"\*\*", "", line)
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
        if re.match(r"^Chapter$", line, re.IGNORECASE):
            needs_merge = True
            merge_pattern = "chapter"

        # Pattern 2: "Episode NN" without title
        elif re.match(r"^Episode\s+\d+$", line, re.IGNORECASE):
            needs_merge = True
            merge_pattern = "episode"

        # Pattern 3: Just "Column" (case insensitive)
        elif re.match(r"^[Cc][Oo][Ll][Uu][Mm][Nn]$", line):
            needs_merge = True
            merge_pattern = "column"

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
                if merge_pattern == "chapter":
                    # For Chapter, next line should start with a digit (N Title format)
                    should_merge = bool(re.match(r"^\d+\s+", next_line))
                elif merge_pattern == "episode":
                    # For Episode, any non-empty line is acceptable as title
                    should_merge = True
                elif merge_pattern == "column":
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
    # Normalize each line and join with space
    normalized = [normalize_toc_line(line) for line in lines]
    text = " ".join(normalized)
    # Compress consecutive whitespace to single space
    return re.sub(r"\s+", " ", text).strip()


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
        r"(?="
        r"(?:Chapter|CHAPTER|chapter)\s+\d+|"
        r"(?:Section|SECTION|section)\s+\d+\.\d+|"
        r"(?:Subsection|SUBSECTION|subsection)\s+\d+\.\d+\.\d+|"
        r"(?:Episode|EPISODE|episode)\s+\d+|"
        r"(?:Column|COLUMN|column)\s+|"
        r"第\d+章|"
        r"\d+\.\d+\.\d+\s|"
        r"\d+\.\d+\s|"
        r"(?:^|\s)\d+\s+(?=[^\d\.])"
        r")"
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
