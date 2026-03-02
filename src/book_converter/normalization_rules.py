"""Normalization rules - generate transformation rules from match results.

Provides functions to generate NormalizationRule from MatchResult,
and to output sed scripts for batch application.
"""

from __future__ import annotations

from src.book_converter.models import (
    MatchResult,
    MatchType,
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
    import re

    from src.book_converter.models import NormalizationAction
    from src.book_converter.parser.heading_normalizer import (
        normalize_number_format,
        normalize_spaces,
    )

    rules: list[NormalizationRule] = []

    for match in matches:
        # Skip MISSING and EXCLUDED
        if match.match_type in (MatchType.MISSING, MatchType.EXCLUDED):
            continue

        # Skip if no body_heading
        if match.body_heading is None:
            continue

        body_text = match.body_heading.text
        body_level = match.body_heading.level
        toc_number = match.toc_entry.number
        toc_title = match.toc_entry.text
        toc_level = match.toc_entry.level

        # Normalize body text
        body_normalized = normalize_spaces(normalize_number_format(body_text))

        # Check if body already has number
        has_number = re.match(r'^\d+(?:\.\d+)*\s+', body_normalized) is not None

        # Build expected text (without markdown marker)
        if toc_number:
            expected_text = f"{toc_number} {toc_title}"
        else:
            expected_text = toc_title

        # Normalize expected text
        expected_normalized = normalize_spaces(normalize_number_format(expected_text))

        # Determine action
        action: NormalizationAction
        normalized_text: str

        if body_level == 0:
            # No markdown marker (level=0 means plain text) -> ADD_MARKER
            # Determine marker based on TOC level
            if toc_level == 1:
                marker = "#"
            elif toc_level == 2:
                marker = "##"
            elif toc_level == 3:
                marker = "###"
            else:
                marker = "##"  # Default to h2

            normalized_text = f"{marker} {expected_text}"
            action = NormalizationAction.ADD_MARKER

        elif not has_number and toc_number:
            # Has marker but no number -> ADD_NUMBER
            # Build markdown marker based on body_level
            marker = "#" * body_level
            normalized_text = f"{marker} {expected_text}"
            action = NormalizationAction.ADD_NUMBER

        else:
            # Has marker and number (or no number needed), check if format needs normalization
            marker = "#" * body_level
            expected_full = f"{marker} {expected_text}"

            # Build current full text (with marker)
            current_full = f"{marker} {body_text}"

            if current_full == expected_full:
                # Already correct
                continue  # No rule needed
            else:
                # Format normalization needed
                normalized_text = expected_full
                # Check if only format changed (number format like 1-1 -> 1.1)
                body_no_number = re.sub(r'^\d+(?:[.\-・]\d+)*\s+', '', body_normalized)
                if body_no_number == toc_title and has_number:
                    action = NormalizationAction.FORMAT_ONLY
                else:
                    # Should not reach here, but use NONE as fallback
                    action = NormalizationAction.NONE

        rule = NormalizationRule(
            original=f"{'#' * body_level} {body_text}" if body_level > 0 else body_text,
            normalized=normalized_text,
            line_number=match.line_number,
            action=action,
        )
        rules.append(rule)

    return rules
