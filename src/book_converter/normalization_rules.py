"""Normalization rules - generate transformation rules from match results.

Provides functions to generate NormalizationRule from MatchResult,
and to output sed scripts for batch application.
"""

from __future__ import annotations

from src.book_converter.models import (
    MatchResult,
    NormalizationRule,
)


def generate_rules(matches: list[MatchResult]) -> list[NormalizationRule]:
    """Generate normalization rules from match results.

    For each MatchResult, determine the appropriate NormalizationAction:
    - EXACT with number already present -> NONE or FORMAT_ONLY
    - EXACT/FUZZY without number -> ADD_NUMBER
    - Body heading without markdown marker -> ADD_MARKER
    - MISSING -> skip (no rule generated)

    Args:
        matches: list of MatchResult from heading matcher

    Returns:
        list of NormalizationRule
    """
    raise NotImplementedError("generate_rules is not yet implemented")
