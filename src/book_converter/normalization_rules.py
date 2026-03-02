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


def generate_sed_script(rules: list[NormalizationRule]) -> str:
    """Generate POSIX-compatible sed script from normalization rules.

    Each rule becomes one sed substitution command.
    Special characters (/, &, \\) are properly escaped.

    Args:
        rules: list of NormalizationRule to convert

    Returns:
        String containing sed commands (one per line)
    """
    import re

    from src.book_converter.models import NormalizationAction

    if not rules:
        return ""

    commands: list[str] = []
    for rule in rules:
        # Skip NONE action rules (no change needed)
        if rule.action == NormalizationAction.NONE:
            continue

        # Escape special sed characters in original and normalized
        # Escape order matters: \ first, then /, then &
        original_escaped = rule.original
        original_escaped = original_escaped.replace("\\", "\\\\")
        original_escaped = original_escaped.replace("/", "\\/")
        original_escaped = original_escaped.replace("&", "\\&")

        normalized_escaped = rule.normalized
        normalized_escaped = normalized_escaped.replace("\\", "\\\\")
        normalized_escaped = normalized_escaped.replace("/", "\\/")
        normalized_escaped = normalized_escaped.replace("&", "\\&")

        # Generate sed command with line anchors (^ and $) to match entire line
        sed_cmd = f"sed -i 's/^{original_escaped}$/{normalized_escaped}/' book.md"
        commands.append(sed_cmd)

    return "\n".join(commands)


def preview_diff(content: str, rules: list[NormalizationRule]) -> str:
    """Generate a human-readable diff preview of rule application.

    Shows before/after for each rule that would change a line.
    Format: - Line N: "original" -> "normalized"

    Args:
        content: Original file content (multiline string)
        rules: list of NormalizationRule to preview

    Returns:
        String containing diff preview lines
    """
    if not rules:
        return ""

    lines = content.split("\n")
    diff_lines: list[str] = []

    for rule in rules:
        # Check if line exists and matches
        line_idx = rule.line_number - 1  # 1-indexed to 0-indexed
        if 0 <= line_idx < len(lines):
            current_line = lines[line_idx]
            if current_line == rule.original:
                diff_line = (
                    f"- Line {rule.line_number}: "
                    f'"{rule.original}" -> "{rule.normalized}"'
                )
                diff_lines.append(diff_line)

    return "\n".join(diff_lines)


def apply_rules(content: str, rules: list[NormalizationRule]) -> str:
    """Apply normalization rules to content and return modified content.

    Each rule replaces one specific line (identified by line_number).

    Args:
        content: Original file content (multiline string)
        rules: list of NormalizationRule to apply

    Returns:
        Modified content with rules applied
    """
    if not rules:
        return content

    lines = content.split("\n")

    # Apply each rule
    for rule in rules:
        line_idx = rule.line_number - 1  # 1-indexed to 0-indexed
        if 0 <= line_idx < len(lines):
            # Only replace if current line matches original
            if lines[line_idx] == rule.original:
                lines[line_idx] = rule.normalized

    return "\n".join(lines)
