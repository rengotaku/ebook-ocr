"""CLI entry point for heading normalization.

Provides subcommands:
- report: heading pattern analysis report
- normalize: normalize headings (dry-run or apply)
- validate: TOC-body heading validation report
"""

from __future__ import annotations

import argparse
import sys
import unicodedata
from pathlib import Path


def _display_width(text: str) -> int:
    """Calculate display width of text (handles CJK characters)."""
    width = 0
    for char in text:
        ea = unicodedata.east_asian_width(char)
        if ea in ('F', 'W', 'A'):  # Fullwidth, Wide, Ambiguous
            width += 2
        else:
            width += 1
    return width


def _truncate_to_width(text: str, max_width: int) -> str:
    """Truncate text to fit within max display width."""
    if _display_width(text) <= max_width:
        return text

    result = ""
    current_width = 0
    for char in text:
        ea = unicodedata.east_asian_width(char)
        char_width = 2 if ea in ('F', 'W', 'A') else 1
        if current_width + char_width + 2 > max_width:  # +2 for ".."
            return result + ".."
        result += char
        current_width += char_width
    return result


def _pad_to_width(text: str, target_width: int) -> str:
    """Pad text with spaces to reach target display width."""
    current_width = _display_width(text)
    if current_width >= target_width:
        return text
    return text + " " * (target_width - current_width)


def cmd_report(args: argparse.Namespace) -> int:
    """Execute report subcommand."""
    from src.book_converter.parser.heading_normalizer import (
        classify_heading_patterns,
        extract_headings,
    )

    file_path = Path(args.file)

    # File existence check
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    # Read file
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error: Failed to read file: {e}", file=sys.stderr)
        return 1

    # Extract headings
    lines = content.splitlines()
    headings = extract_headings(lines)

    # Classify patterns
    report = classify_heading_patterns(headings)

    # Print report
    print("Heading Pattern Report")
    print("======================")
    print(f"Total headings: {report.total}")
    print()
    print("Pattern Distribution:")
    if report.total > 0:
        numbered_pct = (report.numbered_count / report.total) * 100
        unnumbered_pct = (report.unnumbered_count / report.total) * 100
        special_pct = (report.special_marker_count / report.total) * 100
        print(f"  Numbered (##N.N):       {report.numbered_count} ({numbered_pct:.1f}%)")
        print(f"  Unnumbered:             {report.unnumbered_count} ({unnumbered_pct:.1f}%)")
        print(f"  Special markers:        {report.special_marker_count} ({special_pct:.1f}%)")
    else:
        print("  No headings found.")

    return 0


def cmd_normalize(args: argparse.Namespace) -> int:
    """Execute normalize subcommand."""
    from src.book_converter.heading_matcher import match_toc_to_body
    from src.book_converter.models import MarkerType
    from src.book_converter.normalization_rules import (
        apply_rules,
        generate_rules,
        preview_diff,
    )
    from src.book_converter.parser.heading_normalizer import extract_headings
    from src.book_converter.parser.toc import parse_toc_entry, parse_toc_marker

    file_path = Path(args.file)
    apply_changes = args.apply
    threshold = args.threshold

    # File existence check
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    # Read file
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error: Failed to read file: {e}", file=sys.stderr)
        return 1

    lines = content.splitlines()

    # Extract TOC entries
    toc_entries = []
    in_toc = False
    toc_lines = []

    for line in lines:
        marker = parse_toc_marker(line)
        if marker == MarkerType.TOC_START:
            in_toc = True
            continue
        elif marker == MarkerType.TOC_END:
            in_toc = False
            continue

        if in_toc:
            toc_lines.append(line)

    # Parse TOC lines
    for line in toc_lines:
        entry = parse_toc_entry(line.strip())
        if entry:
            toc_entries.append(entry)

    # Extract body headings
    headings = extract_headings(lines)

    # Convert HeadingInfo to Heading for matcher
    from src.book_converter.models import Heading

    body_headings = [
        Heading(level=h.level, text=h.raw_text, read_aloud=True, line_number=h.line_number)
        for h in headings
    ]

    # Match TOC to body
    matches = match_toc_to_body(
        toc_entries,
        body_headings,
        similarity_threshold=threshold,
    )

    # Generate rules
    rules = generate_rules(matches)

    # Calculate match statistics
    matched_count = sum(1 for m in matches if m.match_type.value not in ('missing', 'excluded'))
    missing_count = sum(1 for m in matches if m.match_type.value == 'missing')

    # Check if TOC was found
    if not toc_entries:
        print("Normalization Preview")
        print("=====================")
        print("Warning: No TOC found in file.")
        print()
        print("Expected: <!-- toc --> ... <!-- /toc --> markers")
        print(f"Body Headings found: {len(body_headings)}")
        print()
        print("Add TOC markers to the file first, then run this command again.")
        return 0

    # Apply or preview
    if apply_changes:
        # Apply rules to content
        modified_content = apply_rules(content, rules)

        # Write back
        try:
            file_path.write_text(modified_content, encoding="utf-8")
            print(f"Applied {len(rules)} normalization rules to {file_path}")
            print()
            print(f"TOC Entries: {len(toc_entries)}")
            print(f"Matched: {matched_count}, Missing: {missing_count}")
        except Exception as e:
            print(f"Error: Failed to write file: {e}", file=sys.stderr)
            return 1
    else:
        # Preview changes
        print("Normalization Preview")
        print("=====================")
        print()
        print(f"TOC Entries:    {len(toc_entries)}")
        print(f"Body Headings:  {len(body_headings)}")
        print(f"Matched:        {matched_count} ({matched_count * 100 // len(toc_entries) if toc_entries else 0}%)")
        print(f"Missing:        {missing_count}")
        print()

        if not rules:
            print("No changes needed.")
            print("All matched headings are already in the correct format.")
            print()
            print("Run 'make validate-toc' for detailed match information.")
        else:
            from src.book_converter.models import NormalizationAction

            print(f"Changes to apply: {len(rules)}")
            print()

            # Build table data from matches and rules
            # Create a mapping from line_number to rule
            rule_by_line = {r.line_number: r for r in rules}

            # Column widths
            w_line = 5
            w_toc = 24
            w_act = 4
            w_before = 28
            w_after = 28

            # Header
            header = (
                f"{_pad_to_width('Line', w_line)} "
                f"{_pad_to_width('TOC Entry', w_toc)} "
                f"{_pad_to_width('Act', w_act)} "
                f"{_pad_to_width('Before', w_before)} "
                f"After"
            )
            separator = "-" * (w_line + w_toc + w_act + w_before + w_after + 4)
            print(header)
            print(separator)

            # Action labels
            action_labels = {
                NormalizationAction.ADD_NUMBER: "+NUM",
                NormalizationAction.ADD_MARKER: "+MRK",
                NormalizationAction.FORMAT_ONLY: "FMT",
                NormalizationAction.NONE: "NONE",
            }

            # Rows - iterate matches to get TOC entry info
            for match in matches:
                if match.body_heading is None:
                    continue
                line_num = match.body_heading.line_number
                if line_num not in rule_by_line:
                    continue

                rule = rule_by_line[line_num]
                if rule.action == NormalizationAction.NONE:
                    continue  # Skip no-change rules

                # Build TOC entry text
                toc_text = f"{match.toc_entry.number} {match.toc_entry.text}".strip()

                # Format row
                row = (
                    f"{_pad_to_width(str(line_num), w_line)} "
                    f"{_pad_to_width(_truncate_to_width(toc_text, w_toc), w_toc)} "
                    f"{_pad_to_width(action_labels.get(rule.action, '?'), w_act)} "
                    f"{_pad_to_width(_truncate_to_width(rule.original, w_before), w_before)} "
                    f"{_truncate_to_width(rule.normalized, w_after)}"
                )
                print(row)

            print()
            print("Act: +NUM=番号付与, +MRK=マーカー付与, FMT=フォーマット修正")
            print()
            print("Run with APPLY=1 to apply changes.")

    return 0


def cmd_validate(args: argparse.Namespace) -> int:
    """Execute validate subcommand."""
    from src.book_converter.heading_matcher import (
        find_similar_candidate,
        format_validation_report,
        generate_validation_report,
        match_toc_to_body,
    )
    from src.book_converter.models import MarkerType
    from src.book_converter.parser.heading_normalizer import extract_headings
    from src.book_converter.parser.toc import parse_toc_entry, parse_toc_marker

    file_path = Path(args.file)
    threshold = args.threshold

    # File existence check
    if not file_path.exists():
        print(f"Error: File not found: {file_path}", file=sys.stderr)
        return 1

    # Read file
    try:
        content = file_path.read_text(encoding="utf-8")
    except Exception as e:
        print(f"Error: Failed to read file: {e}", file=sys.stderr)
        return 1

    lines = content.splitlines()

    # Extract TOC entries
    toc_entries = []
    in_toc = False
    toc_lines = []

    for line in lines:
        marker = parse_toc_marker(line)
        if marker == MarkerType.TOC_START:
            in_toc = True
            continue
        elif marker == MarkerType.TOC_END:
            in_toc = False
            continue

        if in_toc:
            toc_lines.append(line)

    # Parse TOC lines
    for line in toc_lines:
        entry = parse_toc_entry(line.strip())
        if entry:
            toc_entries.append(entry)

    # Extract body headings
    headings = extract_headings(lines)

    # Convert HeadingInfo to Heading for matcher
    from src.book_converter.models import Heading

    body_headings = [
        Heading(level=h.level, text=h.raw_text, read_aloud=True, line_number=h.line_number)
        for h in headings
    ]

    # Match TOC to body
    matches = match_toc_to_body(
        toc_entries,
        body_headings,
        similarity_threshold=threshold,
    )

    # Find similar candidates for MISSING entries
    similar_candidates = {}
    from src.book_converter.models import MatchType

    for match in matches:
        if match.match_type == MatchType.MISSING:
            candidate = find_similar_candidate(
                match.toc_entry,
                body_headings,
                threshold=threshold,
            )
            if candidate:
                similar_candidates[match.toc_entry] = candidate

    # Generate report
    report = generate_validation_report(matches, body_headings)

    # Format and print
    formatted = format_validation_report(
        report,
        matches,
        similar_candidates,
    )
    print(formatted)

    # Always exit 0 (even with MISSING)
    return 0


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Normalize book.md headings to match TOC format",
    )

    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # report subcommand
    parser_report = subparsers.add_parser(
        "report",
        help="Generate heading pattern analysis report",
    )
    parser_report.add_argument(
        "file",
        help="Path to book.md file",
    )

    # normalize subcommand
    parser_normalize = subparsers.add_parser(
        "normalize",
        help="Normalize headings (dry-run or apply)",
    )
    parser_normalize.add_argument(
        "file",
        help="Path to book.md file",
    )
    parser_normalize.add_argument(
        "--apply",
        action="store_true",
        help="Apply changes to file (default: dry-run preview)",
    )
    parser_normalize.add_argument(
        "--threshold",
        type=float,
        default=0.8,
        help="Fuzzy matching similarity threshold (default: 0.8)",
    )

    # validate subcommand
    parser_validate = subparsers.add_parser(
        "validate",
        help="Validate TOC-body heading matching",
    )
    parser_validate.add_argument(
        "file",
        help="Path to book.md file",
    )
    parser_validate.add_argument(
        "--threshold",
        type=float,
        default=0.8,
        help="Fuzzy matching similarity threshold (default: 0.8)",
    )

    args = parser.parse_args()

    # Dispatch to subcommand
    if args.command == "report":
        return cmd_report(args)
    elif args.command == "normalize":
        return cmd_normalize(args)
    elif args.command == "validate":
        return cmd_validate(args)
    else:
        parser.print_help()
        return 1


if __name__ == "__main__":
    sys.exit(main())
