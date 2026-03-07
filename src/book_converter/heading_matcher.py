"""Heading matcher - TOC entry to body heading matching engine.

Provides functions to match TOC entries with body headings using
exact match, number-removal match, and fuzzy matching strategies.
"""

from __future__ import annotations

from src.book_converter.models import (
    Heading,
    MatchResult,
    MatchType,
    TocEntry,
    ValidationReport,
)


def _extract_heading_number(text: str) -> str | None:
    """見出しテキストから先頭の番号を抽出する.

    Args:
        text: 正規化済み見出しテキスト

    Returns:
        番号文字列 (例: "1.1", "4.4.2") or None
    """
    import re

    match = re.match(r"^(\d+(?:\.\d+)*)\s+", text)
    if match:
        return match.group(1)
    return None


def _numbers_compatible(toc_number: str, heading_number: str | None) -> bool:
    """TOC番号と見出し番号が互換かどうか判定する.

    Rules:
    - 見出しに番号がない → 互換 (番号を付与する想定)
    - 見出しに番号がある → TOC番号と一致する必要あり

    Args:
        toc_number: TOCエントリの番号 (例: "4.4.2")
        heading_number: 見出しの番号 or None

    Returns:
        True if compatible
    """
    if heading_number is None:
        return True  # No number in heading = compatible
    # Both have numbers - must match
    return toc_number == heading_number


def match_toc_to_body(
    toc_entries: list[TocEntry],
    body_headings: list[Heading],
    *,
    similarity_threshold: float = 0.8,
) -> list[MatchResult]:
    """TOC entries and body headings matching.

    2-pass strategy with number verification and sequential constraint:

    Pass 1 (Exact match, sequential order):
    - Exact match: number+title or title-only matches
    - Number verification: if heading has number, must match TOC number
    - Sequential constraint: only search after last matched line

    Pass 2 (Fuzzy match for remaining, sequential order):
    - Fuzzy match: similarity >= threshold
    - Number verification: if heading has number, must match TOC number
    - Sequential constraint: only search after last matched line

    Args:
        toc_entries: list of TOC entries
        body_headings: list of body headings
        similarity_threshold: minimum similarity for fuzzy match (default 0.8)

    Returns:
        list of MatchResult
    """
    import difflib
    import re

    from src.book_converter.parser.heading_normalizer import (
        is_special_marker,
        normalize_number_format,
        normalize_spaces,
    )

    if not toc_entries:
        return []

    # Track which headings have been used
    used_heading_indices: set[int] = set()

    # Track last matched line number for sequential constraint
    last_matched_line: int = 0

    # Pre-process headings: normalize and extract numbers
    heading_info: list[tuple[str, str, str | None]] = []  # (normalized, no_number, number)
    for heading in body_headings:
        normalized = normalize_spaces(normalize_number_format(heading.text))
        no_number = re.sub(r"^\d+(?:\.\d+)*\s+", "", normalized)
        number = _extract_heading_number(normalized)
        heading_info.append((normalized, no_number, number))

    # Results: initially None for each TOC entry
    results: list[MatchResult | None] = [None] * len(toc_entries)

    # === Pass 1: Exact matches (sequential order) ===
    for toc_idx, toc_entry in enumerate(toc_entries):
        toc_number = toc_entry.number
        toc_title = toc_entry.text
        toc_full = f"{toc_number} {toc_title}".strip() if toc_number else toc_title

        toc_full_normalized = normalize_spaces(normalize_number_format(toc_full))
        toc_title_normalized = normalize_spaces(normalize_number_format(toc_title))

        for h_idx, heading in enumerate(body_headings):
            if h_idx in used_heading_indices:
                continue
            if is_special_marker(heading.text):
                continue

            # Sequential constraint: only search after last matched line
            h_line = heading.line_number if heading.line_number > 0 else h_idx + 1
            if h_line <= last_matched_line:
                continue

            h_normalized, h_no_number, h_number = heading_info[h_idx]

            # Number verification: if heading has number, must match TOC
            if not _numbers_compatible(toc_number, h_number):
                continue

            # Exact match check
            is_exact = (
                h_normalized == toc_full_normalized
                or h_normalized == toc_title_normalized
                or h_no_number == toc_title_normalized
            )

            if is_exact:
                results[toc_idx] = MatchResult(
                    toc_entry=toc_entry,
                    body_heading=heading,
                    match_type=MatchType.EXACT,
                    similarity=1.0,
                    line_number=h_line,
                )
                used_heading_indices.add(h_idx)
                last_matched_line = h_line  # Update for next TOC entry
                break

    # === Pass 2: Fuzzy matches for remaining (sequential order) ===
    for toc_idx, toc_entry in enumerate(toc_entries):
        if results[toc_idx] is not None:
            continue  # Already matched in pass 1

        # Get last matched line from previous TOC entries (lower bound)
        prev_matched_line = 0
        for prev_idx in range(toc_idx - 1, -1, -1):
            if results[prev_idx] is not None and results[prev_idx].line_number > 0:
                prev_matched_line = results[prev_idx].line_number
                break

        # Get next matched line from subsequent TOC entries (upper bound)
        # This prevents matching a heading that's too far ahead
        next_matched_line = float("inf")
        for next_idx in range(toc_idx + 1, len(toc_entries)):
            if results[next_idx] is not None and results[next_idx].line_number > 0:
                next_matched_line = results[next_idx].line_number
                break

        toc_number = toc_entry.number
        toc_title = toc_entry.text
        toc_title_normalized = normalize_spaces(normalize_number_format(toc_title))

        best_match: MatchResult | None = None
        best_similarity: float = 0.0
        best_h_idx: int = -1
        best_h_line: int = 0

        for h_idx, heading in enumerate(body_headings):
            if h_idx in used_heading_indices:
                continue
            if is_special_marker(heading.text):
                continue

            # Sequential constraint: search between prev and next matched lines
            h_line = heading.line_number if heading.line_number > 0 else h_idx + 1
            if h_line <= prev_matched_line:
                continue
            if h_line >= next_matched_line:
                continue

            h_normalized, h_no_number, h_number = heading_info[h_idx]

            # Number verification: if heading has number, must match TOC
            if not _numbers_compatible(toc_number, h_number):
                continue

            # Fuzzy match
            similarity = difflib.SequenceMatcher(None, toc_title_normalized, h_no_number).ratio()

            if similarity >= similarity_threshold and similarity > best_similarity:
                best_similarity = similarity
                best_match = MatchResult(
                    toc_entry=toc_entry,
                    body_heading=heading,
                    match_type=MatchType.FUZZY,
                    similarity=similarity,
                    line_number=h_line,
                )
                best_h_idx = h_idx
                best_h_line = h_line

        if best_match is not None:
            results[toc_idx] = best_match
            used_heading_indices.add(best_h_idx)
            last_matched_line = best_h_line  # Update for next TOC entry

    # === Fill MISSING for unmatched ===
    for toc_idx, toc_entry in enumerate(toc_entries):
        if results[toc_idx] is None:
            results[toc_idx] = MatchResult(
                toc_entry=toc_entry,
                body_heading=None,
                match_type=MatchType.MISSING,
                similarity=0.0,
                line_number=0,
            )

    return results  # type: ignore[return-value]


def find_similar_candidate(
    toc_entry: TocEntry,
    headings: list[Heading],
    *,
    threshold: float = 0.8,
) -> tuple[Heading, float] | None:
    """MISSING TOCエントリに対する類似候補を検索する.

    Args:
        toc_entry: 未マッチのTOCエントリ
        headings: 本文見出しリスト
        threshold: 類似度閾値 (default 0.8)

    Returns:
        (類似見出し, 類似度) or None
    """
    import difflib
    import re

    from src.book_converter.parser.heading_normalizer import (
        normalize_number_format,
        normalize_spaces,
    )

    if not headings:
        return None

    # Normalize TOC entry text (title only, no number)
    toc_text = normalize_spaces(normalize_number_format(toc_entry.text))

    best_heading: Heading | None = None
    best_similarity: float = 0.0

    for heading in headings:
        # Normalize heading text and strip leading number for comparison
        heading_text = normalize_spaces(normalize_number_format(heading.text))
        heading_title = re.sub(r"^\d+(?:\.\d+)*\s+", "", heading_text)

        # Calculate similarity using title-only comparison
        similarity = difflib.SequenceMatcher(None, toc_text, heading_title).ratio()

        if similarity >= threshold and similarity > best_similarity:
            best_similarity = similarity
            best_heading = heading

    if best_heading is None:
        return None

    return (best_heading, best_similarity)


def generate_validation_report(
    matches: list[MatchResult],
    headings: list[Heading],
) -> ValidationReport:
    """マッチング結果から検証レポートを生成する.

    Args:
        matches: MatchResult のリスト
        headings: 本文見出しリスト

    Returns:
        ValidationReport
    """
    from src.book_converter.parser.heading_normalizer import is_special_marker

    # Count TOC entries
    toc_entry_count = len(matches)

    # Count body headings
    body_heading_count = len(headings)

    # Count matched entries (EXACT or FUZZY)
    matched_count = sum(1 for m in matches if m.match_type in (MatchType.EXACT, MatchType.FUZZY))

    # Calculate match rate (avoid division by zero)
    match_rate = matched_count / toc_entry_count if toc_entry_count > 0 else 0.0

    # Collect missing entries (MISSING type)
    missing_entries = tuple(m.toc_entry for m in matches if m.match_type == MatchType.MISSING)

    # Collect excluded headings (special marker headings)
    excluded_headings = tuple(h for h in headings if is_special_marker(h.text))

    return ValidationReport(
        toc_entry_count=toc_entry_count,
        body_heading_count=body_heading_count,
        matched_count=matched_count,
        match_rate=match_rate,
        missing_entries=missing_entries,
        excluded_headings=excluded_headings,
    )


def format_validation_report(
    report: ValidationReport,
    matches: list[MatchResult],
    similar_candidates: dict[TocEntry, tuple[Heading, float]],
) -> str:
    """検証レポートをテーブル形式でフォーマットする.

    Args:
        report: ValidationReport
        matches: MatchResult のリスト
        similar_candidates: MISSINGエントリの類似候補 dict

    Returns:
        フォーマット済みレポート文字列
    """
    lines: list[str] = []

    # Header
    lines.append("=== TOC Validation Report ===")
    lines.append("")

    # Summary
    lines.append("Summary:")
    lines.append(f"  TOC Entries:      {report.toc_entry_count}")
    lines.append(f"  Body Headings:    {report.body_heading_count}")
    match_rate_pct = int(report.match_rate * 100)
    lines.append(f"  Matched:          {report.matched_count} ({match_rate_pct}%)")
    lines.append(f"  Missing:          {len(report.missing_entries)}")
    lines.append(f"  Excluded:         {len(report.excluded_headings)}")
    lines.append("")

    # Match Details table
    if matches:
        lines.append("Match Details:")
        lines.append("+----+---------------------------+---------------------------+--------+------+-------+------+")
        lines.append("| #  | TOC Entry                 | Body Heading              | Type   | Sim% | Line# | Page |")
        lines.append("+----+---------------------------+---------------------------+--------+------+-------+------+")

        for idx, match in enumerate(matches, start=1):
            # TOC Entry column
            toc_text = match.toc_entry.text[:25].ljust(25)

            # Body Heading column
            if match.body_heading is not None:
                body_text = match.body_heading.text[:25].ljust(25)
            else:
                body_text = "(none)".ljust(25)

            # Type column
            match_type_str = match.match_type.value.upper()[:7].ljust(7)

            # Similarity column
            if match.match_type == MatchType.MISSING:
                sim_str = "-".rjust(4)
            else:
                sim_pct = int(match.similarity * 100)
                sim_str = str(sim_pct).rjust(4)

            # Line# column
            if match.line_number > 0:
                line_str = str(match.line_number).rjust(5)
            else:
                line_str = "-".rjust(5)

            # Page column
            page_str = match.toc_entry.page[:4].rjust(4)

            lines.append(
                f"| {idx:2d} | {toc_text} | {body_text} | {match_type_str} | {sim_str} | {line_str} | {page_str} |"
            )

            # Similar candidate for MISSING entries
            if match.match_type == MatchType.MISSING and match.toc_entry in similar_candidates:
                similar_heading, similar_sim = similar_candidates[match.toc_entry]
                similar_text = similar_heading.text[:25].ljust(25)
                similar_pct = int(similar_sim * 100)
                similar_col = f"-> Similar: {similar_text[:18]:<18}"
                lines.append(
                    f"|    |                           | {similar_col} |        | {similar_pct:4d} |       |      |"
                )

        lines.append("+----+---------------------------+---------------------------+--------+------+-------+------+")
        lines.append("")

    # Excluded section
    if report.excluded_headings:
        lines.append("Excluded (special markers):")
        for heading in report.excluded_headings:
            lines.append(f"  [-] {heading.text}")
        lines.append("")

    # Status
    if len(report.missing_entries) > 0:
        lines.append(f"Status: WARN ({len(report.missing_entries)} missing entries require manual review)")
    else:
        lines.append("Status: OK")

    lines.append("Exit: 0")

    return "\n".join(lines)
