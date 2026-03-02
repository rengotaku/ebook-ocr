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
