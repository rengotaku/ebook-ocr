"""CLI module for book markdown to XML conversion.

Provides command-line interface for converting book.md to book.xml.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.book_converter.models import (
    Book,
    BookMetadata,
    ConversionResult,
    ConversionError,
)
from src.book_converter.parser import parse_pages_with_errors
from src.book_converter.xml_builder import build_xml_with_errors


def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """Parse CLI arguments.

    Args:
        args: List of command-line arguments. If None, uses sys.argv.

    Returns:
        Parsed arguments namespace.
    """
    parser = argparse.ArgumentParser(
        description="Convert book.md to book.xml"
    )
    parser.add_argument("input", help="Input markdown file")
    parser.add_argument("output", help="Output XML file")

    # Mutually exclusive group for verbose and quiet
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Verbose output"
    )
    group.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Quiet mode"
    )

    return parser.parse_args(args)


def convert_book(input_path: Path, output_path: Path) -> ConversionResult:
    """Convert a Markdown book to XML.

    Args:
        input_path: Path to the input Markdown file.
        output_path: Path to the output XML file.

    Returns:
        ConversionResult with conversion statistics and errors.
    """
    # Parse pages with error tracking
    pages, errors = parse_pages_with_errors(input_path)

    # Create Book object
    book = Book(
        metadata=BookMetadata(title="Converted Book"),
        pages=tuple(pages),
    )

    # Build XML with error comments
    xml_string = build_xml_with_errors(book, errors)

    # Write to output file
    output_path.write_text(xml_string, encoding="utf-8")

    # Return result
    return ConversionResult(
        success=True,
        total_pages=len(pages),
        error_count=len(errors),
        errors=tuple(errors),
        output_path=str(output_path),
    )


def main(args: list[str] | None = None) -> int:
    """CLI entry point.

    Args:
        args: List of command-line arguments. If None, uses sys.argv.

    Returns:
        Exit code (0 for success, non-zero for error).
    """
    try:
        parsed = parse_args(args)

        input_path = Path(parsed.input)
        output_path = Path(parsed.output)

        # Check if input file exists
        if not input_path.exists():
            print(f"エラー: 入力ファイルが見つかりません: {input_path}", file=sys.stderr)
            return 1

        # Convert
        if parsed.verbose:
            print(f"変換中: {input_path} -> {output_path}")

        result = convert_book(input_path, output_path)

        # Output summary (unless quiet mode)
        if not parsed.quiet:
            print(f"変換完了: {result.total_pages}ページ処理")
            if result.error_count > 0:
                print(f"警告: {result.error_count}個のエラーが発生しました")

        # Error summary at the end
        if result.error_count > 0 and not parsed.quiet:
            print("\n=== エラーサマリー ===", file=sys.stderr)
            for error in result.errors:
                location = ""
                if error.line_number > 0:
                    location = f" (行 {error.line_number})"
                if error.page_number:
                    location += f" (ページ {error.page_number})"
                print(f"  [{error.error_type}] {error.message}{location}", file=sys.stderr)

        # Check error rate (10% threshold)
        if result.total_pages > 0:
            error_rate = result.error_count / result.total_pages
            if error_rate > 0.10:
                print(f"\n警告: エラー率が10%を超えています ({error_rate:.1%})", file=sys.stderr)

        return 0

    except Exception as e:
        print(f"エラー: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
