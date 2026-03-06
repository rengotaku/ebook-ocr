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
        MissingMarkerError,
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
    try:
        headings = extract_headings(lines)
    except MissingMarkerError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

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
    from src.book_converter.heading_matcher import find_similar_candidate, match_toc_to_body
    from src.book_converter.models import MarkerType, MatchType
    from src.book_converter.normalization_rules import (
        apply_rules,
        generate_rules,
        preview_diff,
    )
    from src.book_converter.parser.heading_normalizer import (
        MissingMarkerError,
        extract_headings,
    )
    from src.book_converter.parser.toc import parse_toc_entry, parse_toc_marker

    def extract_num_and_title(text: str) -> tuple[str, str]:
        """Extract number and title from heading text."""
        import re as _re
        _match = _re.match(r'^(\d+(?:\.\d+)*)\s+(.+)$', text)
        if _match:
            return _match.group(1), _match.group(2)
        return "-", text

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

    # Check required markers exist
    has_toc_start = any(parse_toc_marker(line) == MarkerType.TOC_START for line in lines)
    has_toc_end = any(parse_toc_marker(line) == MarkerType.TOC_END for line in lines)

    if not has_toc_start or not has_toc_end:
        print("Error: Required markers <!-- toc --> and <!-- /toc --> not found", file=sys.stderr)
        return 1

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
    try:
        headings = extract_headings(lines)
    except MissingMarkerError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Convert HeadingInfo to Heading for matcher
    # Strip markdown prefix (## ) from raw_text to get clean text
    import re

    from src.book_converter.models import Heading

    def strip_markdown_prefix(raw: str) -> str:
        """Remove leading markdown heading prefix (e.g., '## ')."""
        return re.sub(r'^#+\s*', '', raw)

    body_headings = [
        Heading(level=h.level, text=strip_markdown_prefix(h.raw_text), read_aloud=True, line_number=h.line_number, page=h.page)
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

    # Build set of matched heading line numbers to exclude from candidate search
    matched_lines = {
        m.body_heading.line_number
        for m in matches
        if m.body_heading is not None and m.body_heading.line_number > 0
    }
    unmatched_headings = [
        h for h in body_headings if h.line_number not in matched_lines
    ]

    # Generate FIX_NUMBER rules for MISSING(NUM) entries
    # Only generate rules for unmatched headings (don't overwrite matched ones)
    from src.book_converter.models import NormalizationAction, NormalizationRule
    from src.book_converter.normalization_rules import _heading_level_from_number

    for match in matches:
        if match.match_type != MatchType.MISSING:
            continue
        toc_num = match.toc_entry.number
        if not toc_num:
            continue
        # Search unmatched headings first (safe to modify)
        candidate = find_similar_candidate(
            match.toc_entry,
            unmatched_headings,
            threshold=threshold * 0.5,
        )
        if not candidate:
            continue
        similar_heading, _similarity = candidate
        body_num, body_title = extract_num_and_title(similar_heading.text)
        if body_num == "-" or body_num == toc_num:
            continue
        # FIX_NUMBER: replace wrong number with TOC number
        if similar_heading.level > 0:
            marker = "#" * similar_heading.level
            original_text = f"{marker} {similar_heading.text}"
        else:
            marker = "#" * _heading_level_from_number(toc_num)
            original_text = similar_heading.text
        normalized_text = f"{marker} {toc_num} {body_title}"
        rules.append(NormalizationRule(
            original=original_text,
            normalized=normalized_text,
            line_number=similar_heading.line_number,
            action=NormalizationAction.FIX_NUMBER,
        ))

    # Generate level fix rules for unmatched headings
    # Headings not matched to TOC: if level != 3 and not h1/h2 number pattern → fix to h3
    rule_lines = {r.line_number for r in rules}
    for h in body_headings:
        if h.line_number in matched_lines or h.line_number in rule_lines:
            continue
        if h.level == 0 or h.level == 3:
            continue  # Already h3 or no marker
        # Check if heading number qualifies for h1/h2
        h_num, _ = extract_num_and_title(h.text)
        expected_level = _heading_level_from_number(h_num) if h_num != "-" else 3
        if h.level == expected_level:
            continue
        # Level mismatch: fix to expected level
        old_marker = "#" * h.level
        new_marker = "#" * expected_level
        original_text = f"{old_marker} {h.text}"
        normalized_text = f"{new_marker} {h.text}"
        rules.append(NormalizationRule(
            original=original_text,
            normalized=normalized_text,
            line_number=h.line_number,
            action=NormalizationAction.FORMAT_ONLY,
        ))

    # Calculate match statistics
    matched_count = sum(1 for m in matches if m.match_type.value not in ('missing', 'excluded'))
    missing_count = sum(1 for m in matches if m.match_type.value == 'missing')

    # Apply or preview
    if apply_changes:
        # Apply rules to content
        modified_content = apply_rules(content, rules)

        # Backup original file
        backup_path = file_path.with_suffix(".md.bk")
        try:
            backup_path.write_text(content, encoding="utf-8")
            print(f"Backup saved to {backup_path}")
        except Exception as e:
            print(f"Error: Failed to create backup: {e}", file=sys.stderr)
            return 1

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
        from src.book_converter.models import NormalizationAction

        # Summary is printed after table_rows are built (need action counts)

        # Build rule lookup
        rule_by_line = {r.line_number: r for r in rules}

        # Action labels
        action_labels = {
            NormalizationAction.ADD_NUMBER: "+NUM",
            NormalizationAction.ADD_MARKER: "+MRK",
            NormalizationAction.FIX_NUMBER: "FIX_NUM",
            NormalizationAction.FORMAT_ONLY: "FMT",
            NormalizationAction.NONE: "-",
        }

        # Build table data first to calculate column widths
        # (no, status, page, line, toc_num, toc_title, body_num, body_title, match_pct, cand_pct, action)
        table_rows: list[tuple[str, str, str, str, str, str, str, str, str, str, str]] = []

        for row_no, match in enumerate(matches, start=1):
            toc_num = match.toc_entry.number if match.toc_entry.number else "-"
            toc_title = match.toc_entry.text

            # Check for NO_NUM first (TOC entry has no number)
            if toc_num == "-":
                status = "NO_NUM"
                # Get page/line from body heading if matched
                if match.body_heading:
                    page_str = match.body_heading.page if match.body_heading.page else "-"
                    line_str = str(match.body_heading.line_number) if match.body_heading.line_number > 0 else "-"
                else:
                    page_str = "-"
                    line_str = "-"
                body_num, body_title = "-", "-"
                match_pct, cand_pct = "-", "-"
                action_str = "-"
            elif match.match_type == MatchType.MISSING:
                # MISSING: no body heading found
                # Find similar candidate to check for number mismatch
                # Use unmatched_headings to avoid false positives from duplicates
                candidate = find_similar_candidate(
                    match.toc_entry,
                    unmatched_headings,
                    threshold=threshold * 0.5,
                )
                if candidate:
                    similar_heading, similarity = candidate
                    body_num, _ = extract_num_and_title(similar_heading.text)
                    # Check if number mismatch caused the MISSING
                    if body_num != "-" and body_num != toc_num:
                        # MISSING(NUM): Show candidate info for FIX_NUM action
                        status = "MISSING(NUM)"
                        action_str = "FIX_NUM"
                        cand_pct = str(int(similarity * 100))
                        _, body_title = extract_num_and_title(similar_heading.text)
                        page_str = "-"
                        line_str = "-"
                    else:
                        # MISSING: Don't show candidate (noise)
                        status = "MISSING"
                        action_str = "MANUAL"
                        page_str, line_str = "-", "-"
                        cand_pct, body_num, body_title = "-", "-", "-"
                else:
                    # No candidate at all
                    status = "MISSING"
                    action_str = "MANUAL"
                    page_str, line_str = "-", "-"
                    cand_pct, body_num, body_title = "-", "-", "-"
                match_pct = "-"  # No match for MISSING
            else:
                # Matched (EXACT or FUZZY)
                heading = match.body_heading
                page_str = heading.page if heading.page else "-"
                line_str = str(heading.line_number) if heading.line_number > 0 else "-"
                cand_pct = "-"  # No candidate search for matched

                # Check if rule exists for this match
                if heading.line_number in rule_by_line:
                    rule = rule_by_line[heading.line_number]
                    if rule.action == NormalizationAction.NONE:
                        status = "OK"
                        # For OK: Body Title, Match%, Action = "-"
                        body_num, body_title = "-", "-"
                        match_pct = "-"
                        action_str = "-"
                    else:
                        status = "MATCH"
                        body_num, body_title = extract_num_and_title(heading.text)
                        match_pct = str(int(match.similarity * 100)) if match.match_type == MatchType.FUZZY else "100"
                        action_str = action_labels.get(rule.action, "?")
                else:
                    status = "OK"
                    body_num, body_title = "-", "-"
                    match_pct = "-"
                    action_str = "-"

            table_rows.append((str(row_no), status, page_str, line_str, toc_num, toc_title, body_num, body_title, match_pct, cand_pct, action_str))

        # Calculate action counts from all rows (before filtering)
        from collections import Counter

        # Matched actions: actions for OK/MATCH rows
        matched_actions = Counter(
            row[10] for row in table_rows
            if row[1] in ("OK", "MATCH") and row[10] != "-"
        )
        # Missing actions: actions for MISSING/MISSING(NUM) rows
        missing_actions = Counter(
            row[10] for row in table_rows
            if row[1] in ("MISSING", "MISSING(NUM)") and row[10] != "-"
        )

        # Print summary
        print("Normalization Preview")
        print("=====================")
        print()
        print(f"TOC Entries:    {len(toc_entries)}")
        print(f"Body Headings:  {len(body_headings)}")
        matched_pct = matched_count * 100 // len(toc_entries) if toc_entries else 0
        matched_line = f"Matched:        {matched_count} ({matched_pct}%)"
        if matched_actions:
            parts = [f"{a}:{c}" for a, c in sorted(matched_actions.items())]
            matched_line += f"  {', '.join(parts)}"
        print(matched_line)
        missing_line = f"Missing:        {missing_count}"
        if missing_actions:
            parts = [f"{a}:{c}" for a, c in sorted(missing_actions.items())]
            missing_line += f"          {', '.join(parts)}"
        print(missing_line)
        print()

        # Filter rows if --hide-ok is set
        hide_ok = getattr(args, 'hide_ok', False)
        if hide_ok:
            table_rows = [row for row in table_rows if row[1] != "OK"]

        # Calculate column widths based on content (no truncation)
        # Note: BodyPage/BodyLine = position of matched body heading in content section
        headers = ("No", "Status", "BodyPage", "BodyLine", "Num", "TOC Title", "BodyNum", "Body Title", "Match%", "Cand%", "Action")
        col_widths = [_display_width(h) for h in headers]

        for row in table_rows:
            for i, cell in enumerate(row):
                col_widths[i] = max(col_widths[i], _display_width(cell))

        # Print header
        header_parts = []
        for i, h in enumerate(headers):
            header_parts.append(_pad_to_width(h, col_widths[i]))
        print("  ".join(header_parts))
        print("-" * (sum(col_widths) + 2 * (len(headers) - 1)))

        # Print rows
        for row in table_rows:
            row_parts = []
            for i, cell in enumerate(row):
                row_parts.append(_pad_to_width(cell, col_widths[i]))
            print("  ".join(row_parts))

        print("-" * (sum(col_widths) + 2 * (len(headers) - 1)))
        print()
        print("Column: BodyPage/BodyLine=本文見出しの位置 (content内), BodyNum/Body Title=候補の情報")
        print("Status: OK=変更不要, MATCH=変更必要, MISSING=候補なし, MISSING(NUM)=番号不一致, NO_NUM=番号なし")
        print("Action: +NUM=番号付与, +MRK=マーカー付与, FMT=フォーマット修正, FIX_NUM=番号修正, MANUAL=手動対応")

        if rules:
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
    from src.book_converter.parser.heading_normalizer import (
        MissingMarkerError,
        extract_headings,
    )
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

    # Check required markers exist
    has_toc_start = any(parse_toc_marker(line) == MarkerType.TOC_START for line in lines)
    has_toc_end = any(parse_toc_marker(line) == MarkerType.TOC_END for line in lines)

    if not has_toc_start or not has_toc_end:
        print("Error: Required markers <!-- toc --> and <!-- /toc --> not found", file=sys.stderr)
        return 1

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
    try:
        headings = extract_headings(lines)
    except MissingMarkerError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Convert HeadingInfo to Heading for matcher
    # Strip markdown prefix (## ) from raw_text to get clean text
    import re

    from src.book_converter.models import Heading

    def strip_markdown_prefix(raw: str) -> str:
        """Remove leading markdown heading prefix (e.g., '## ')."""
        return re.sub(r'^#+\s*', '', raw)

    body_headings = [
        Heading(level=h.level, text=strip_markdown_prefix(h.raw_text), read_aloud=True, line_number=h.line_number, page=h.page)
        for h in headings
    ]

    # Match TOC to body
    matches = match_toc_to_body(
        toc_entries,
        body_headings,
        similarity_threshold=threshold,
    )

    # Find similar candidates for MISSING entries
    # Exclude already-matched headings to avoid false positives from duplicates
    matched_lines = {
        m.body_heading.line_number
        for m in matches
        if m.body_heading is not None and m.body_heading.line_number > 0
    }
    unmatched_headings = [
        h for h in body_headings if h.line_number not in matched_lines
    ]

    similar_candidates = {}
    from src.book_converter.models import MatchType

    for match in matches:
        if match.match_type == MatchType.MISSING:
            candidate = find_similar_candidate(
                match.toc_entry,
                unmatched_headings,
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
    parser_normalize.add_argument(
        "--hide-ok",
        action="store_true",
        help="Hide OK status rows in output",
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
