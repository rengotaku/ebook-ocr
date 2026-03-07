"""CLI entry point for TOC normalization.

Detects and fixes OCR errors in TOC entries within book.md:
- Fullwidth -> halfwidth conversion (／ -> /, ： -> :, fullwidth digits)
- Unnecessary space removal around slashes/symbols
- Middle dot normalization

NOTE: このスクリプトは normalize_headings.py と相互に影響します。
  - TOC正規化でエントリのテキストが変わると、見出し正規化のマッチング結果が変わる
  - 見出し正規化で本文見出しが変わると、TOC正規化の必要性が変わることがある
  推奨実行順序: normalize_toc → normalize_headings → normalize_toc (再確認)
"""

from __future__ import annotations

import argparse
import re
import sys
import unicodedata
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TocFix:
    """A single fix to apply to a TOC line."""

    line_number: int
    original: str
    fixed: str
    reason: str


# Fullwidth to halfwidth mapping
_FULLWIDTH_MAP: dict[str, str] = {
    "\uff0f": "/",  # ／ -> /
    "\uff1a": ":",  # ： -> :
    "\uff08": "(",  # （ -> (
    "\uff09": ")",  # ） -> )
    "\u3000": " ",  # ideographic space -> space
}


def _normalize_fullwidth_digits(text: str) -> str:
    """Convert fullwidth digits to halfwidth."""
    result = []
    for ch in text:
        if "\uff10" <= ch <= "\uff19":
            result.append(chr(ord(ch) - 0xFEE0))
        else:
            result.append(ch)
    return "".join(result)


def _normalize_fullwidth_alpha(text: str) -> str:
    """Convert fullwidth ASCII letters to halfwidth."""
    result = []
    for ch in text:
        cp = ord(ch)
        if 0xFF21 <= cp <= 0xFF3A:  # Ａ-Ｚ
            result.append(chr(cp - 0xFEE0))
        elif 0xFF41 <= cp <= 0xFF5A:  # ａ-ｚ
            result.append(chr(cp - 0xFEE0))
        else:
            result.append(ch)
    return "".join(result)


def _apply_fullwidth_map(text: str) -> str:
    """Apply fullwidth symbol to halfwidth mapping."""
    for fw, hw in _FULLWIDTH_MAP.items():
        text = text.replace(fw, hw)
    return text


def _remove_extra_spaces_around_symbols(text: str) -> str:
    """Remove unnecessary spaces around / and other symbols.

    Examples:
        'CI／ CD' -> 'CI/CD' (after fullwidth conversion: 'CI/ CD' -> 'CI/CD')
        'SLI / SLO' -> 'SLI/SLO'
    """
    # Remove spaces around /
    text = re.sub(r"\s*/\s*", "/", text)
    return text


def _normalize_middle_dots(text: str) -> str:
    """Normalize middle dot variants to standard middle dot (·).

    Normalizes:
    - U+00B7 MIDDLE DOT (·) - keep as-is
    - U+2022 BULLET (•) -> ·
    - U+30FB KATAKANA MIDDLE DOT (・) - keep as-is (standard Japanese)
    """
    text = text.replace("\u2022", "\u00b7")  # • -> ·
    return text


def normalize_toc_line(line: str) -> str:
    """Apply all normalization rules to a TOC line.

    Args:
        line: A single TOC line.

    Returns:
        Normalized line.
    """
    result = line
    result = _apply_fullwidth_map(result)
    result = _normalize_fullwidth_digits(result)
    result = _normalize_fullwidth_alpha(result)
    result = _remove_extra_spaces_around_symbols(result)
    result = _normalize_middle_dots(result)
    return result


def find_toc_fixes(lines: list[str]) -> list[TocFix]:
    """Scan lines for TOC sections and find fixable OCR errors.

    Args:
        lines: All lines from book.md (with newlines stripped).

    Returns:
        List of TocFix objects describing each fix.
    """
    fixes: list[TocFix] = []
    in_toc = False

    for i, line in enumerate(lines):
        stripped = line.strip()

        if re.match(r"<!--\s*toc\s*-->", stripped, re.IGNORECASE):
            in_toc = True
            continue
        if re.match(r"<!--\s*/toc\s*-->", stripped, re.IGNORECASE):
            in_toc = False
            continue

        if not in_toc:
            continue

        if not stripped:
            continue

        normalized = normalize_toc_line(line)
        if normalized != line:
            reasons = _describe_changes(line, normalized)
            fixes.append(
                TocFix(
                    line_number=i + 1,
                    original=line,
                    fixed=normalized,
                    reason=", ".join(reasons),
                )
            )

    return fixes


def _describe_changes(original: str, fixed: str) -> list[str]:
    """Describe what changed between original and fixed."""
    reasons: list[str] = []

    for fw, hw in _FULLWIDTH_MAP.items():
        if fw in original:
            name = unicodedata.name(fw, fw)
            reasons.append(f"fullwidth '{fw}' -> '{hw}' ({name})")

    for ch in original:
        if "\uff10" <= ch <= "\uff19":
            reasons.append("fullwidth digits -> halfwidth")
            break

    for ch in original:
        cp = ord(ch)
        if 0xFF21 <= cp <= 0xFF3A or 0xFF41 <= cp <= 0xFF5A:
            reasons.append("fullwidth alpha -> halfwidth")
            break

    if re.search(r"\s+/\s+", original) or re.search(r"\s+/", original) or re.search(r"/\s+", original):
        reasons.append("extra spaces around /")

    if "\u2022" in original:
        reasons.append("bullet • -> middle dot ·")

    if not reasons:
        reasons.append("normalization")

    return reasons


def _display_width(text: str) -> int:
    """Calculate display width of text (handles CJK characters)."""
    width = 0
    for char in text:
        ea = unicodedata.east_asian_width(char)
        if ea in ("F", "W", "A"):
            width += 2
        else:
            width += 1
    return width


def print_preview(fixes: list[TocFix]) -> None:
    """Print a preview of fixes to be applied."""
    if not fixes:
        print("No OCR errors found in TOC entries.")
        return

    print(f"Found {len(fixes)} fix(es):\n")
    for fix in fixes:
        print(f"  L{fix.line_number}: {fix.reason}")
        print(f"    - {fix.original.strip()}")
        print(f"    + {fix.fixed.strip()}")
        print()


def apply_fixes(lines: list[str], fixes: list[TocFix]) -> list[str]:
    """Apply fixes to lines.

    Args:
        lines: Original lines.
        fixes: Fixes to apply.

    Returns:
        New list of lines with fixes applied.
    """
    result = list(lines)
    for fix in fixes:
        idx = fix.line_number - 1
        if result[idx] == fix.original:
            result[idx] = fix.fixed
    return result


def main(argv: list[str] | None = None) -> int:
    """Main entry point.

    Args:
        argv: Command-line arguments.

    Returns:
        Exit code (0 = success, 1 = error).
    """
    parser = argparse.ArgumentParser(
        description="Normalize OCR errors in TOC entries of book.md",
    )
    parser.add_argument(
        "book_md",
        type=Path,
        help="Path to book.md",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        default=False,
        help="Apply fixes (default: dry-run preview only)",
    )

    args = parser.parse_args(argv)
    book_path: Path = args.book_md

    if not book_path.exists():
        print(f"Error: {book_path} not found", file=sys.stderr)
        return 1

    content = book_path.read_text(encoding="utf-8")
    lines = content.splitlines(keepends=True)
    lines_stripped = [line.rstrip("\n") for line in lines]

    fixes = find_toc_fixes(lines_stripped)

    if not fixes:
        print("No OCR errors found in TOC entries.")
        return 0

    print_preview(fixes)

    if not args.apply:
        print(f"Dry-run: {len(fixes)} fix(es) found. Use --apply to apply.")
        return 0

    # Rebuild with original line endings preserved
    fixed_stripped = apply_fixes(lines_stripped, fixes)
    fixed_lines = []
    for orig, fixed in zip(lines, fixed_stripped):
        ending = orig[len(orig.rstrip("\n")) :]
        fixed_lines.append(fixed + ending)

    book_path.write_text("".join(fixed_lines), encoding="utf-8")
    print(f"Applied {len(fixes)} fix(es) to {book_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
