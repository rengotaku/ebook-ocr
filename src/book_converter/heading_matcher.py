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
    raise NotImplementedError("match_toc_to_body is not yet implemented")
