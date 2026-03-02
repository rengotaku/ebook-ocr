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


def match_toc_to_body(
    toc_entries: list[TocEntry],
    body_headings: list[Heading],
    *,
    similarity_threshold: float = 0.8,
) -> list[MatchResult]:
    """TOC entries and body headings matching.

    Strategy (priority order):
    1. Exact match: title strings match exactly
    2. Number-removal match: match after removing numbers from both sides
    3. Fuzzy match: similarity >= threshold
    4. Missing: no match found

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

    results: list[MatchResult] = []
    used_headings: set[int] = set()  # Track used heading indices

    for toc_entry in toc_entries:
        # Build full TOC title with number
        toc_full = f"{toc_entry.number} {toc_entry.text}".strip() if toc_entry.number else toc_entry.text
        toc_title = toc_entry.text

        # Normalize TOC strings
        toc_full_normalized = normalize_spaces(normalize_number_format(toc_full))
        toc_title_normalized = normalize_spaces(normalize_number_format(toc_title))

        best_match: MatchResult | None = None
        best_similarity: float = 0.0

        for idx, heading in enumerate(body_headings):
            if idx in used_headings:
                continue

            # Skip special markers
            if is_special_marker(heading.text):
                continue

            heading_normalized = normalize_spaces(normalize_number_format(heading.text))

            # 1. Exact match (with or without number)
            if heading_normalized == toc_full_normalized or heading_normalized == toc_title_normalized:
                best_match = MatchResult(
                    toc_entry=toc_entry,
                    body_heading=heading,
                    match_type=MatchType.EXACT,
                    similarity=1.0,
                    line_number=idx + 1,
                )
                best_similarity = 1.0
                used_headings.add(idx)
                break

            # 2. Number-removal match
            # Remove leading number pattern from heading
            heading_no_number = re.sub(r'^\d+(?:\.\d+)*\s+', '', heading_normalized)

            if heading_no_number == toc_title_normalized:
                best_match = MatchResult(
                    toc_entry=toc_entry,
                    body_heading=heading,
                    match_type=MatchType.EXACT,
                    similarity=1.0,
                    line_number=idx + 1,
                )
                best_similarity = 1.0
                used_headings.add(idx)
                break

            # 3. Fuzzy match
            # Compare against title (without number)
            similarity = difflib.SequenceMatcher(None, toc_title_normalized, heading_no_number).ratio()

            if similarity >= similarity_threshold and similarity > best_similarity:
                best_similarity = similarity
                best_match = MatchResult(
                    toc_entry=toc_entry,
                    body_heading=heading,
                    match_type=MatchType.FUZZY,
                    similarity=similarity,
                    line_number=idx + 1,
                )

        # If fuzzy match found, mark as used
        if best_match and best_match.match_type == MatchType.FUZZY:
            # Find the index of the matched heading
            for idx, heading in enumerate(body_headings):
                if idx not in used_headings and heading == best_match.body_heading:
                    used_headings.add(idx)
                    break

        # If no match found, mark as MISSING
        if best_match is None:
            best_match = MatchResult(
                toc_entry=toc_entry,
                body_heading=None,
                match_type=MatchType.MISSING,
                similarity=0.0,
                line_number=0,
            )

        results.append(best_match)

    return results


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

    from src.book_converter.parser.heading_normalizer import (
        normalize_number_format,
        normalize_spaces,
    )

    if not headings:
        return None

    # Normalize TOC entry text
    toc_text = normalize_spaces(normalize_number_format(toc_entry.text))

    best_heading: Heading | None = None
    best_similarity: float = 0.0

    for heading in headings:
        # Normalize heading text
        heading_text = normalize_spaces(normalize_number_format(heading.text))

        # Calculate similarity
        similarity = difflib.SequenceMatcher(None, toc_text, heading_text).ratio()

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
    matched_count = sum(
        1 for m in matches if m.match_type in (MatchType.EXACT, MatchType.FUZZY)
    )

    # Calculate match rate (avoid division by zero)
    match_rate = matched_count / toc_entry_count if toc_entry_count > 0 else 0.0

    # Collect missing entries (MISSING type)
    missing_entries = tuple(
        m.toc_entry for m in matches if m.match_type == MatchType.MISSING
    )

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
                lines.append(
                    f"|    |                           | -> Similar: {similar_text[:18]:<18} |        | {similar_pct:4d} |       |      |"
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
