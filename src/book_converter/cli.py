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
    Heading,
    HeaderLevelConfig,
    Page,
    Content,
)
from src.book_converter.parser import parse_pages_with_errors, count_markers
from src.book_converter.xml_builder import build_xml_with_errors
from src.book_converter.analyzer import (
    analyze_headings,
    detect_running_head,
    apply_read_aloud_rules,
)


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
        help="Verbose output (show exclusion reasons)"
    )
    group.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Quiet mode"
    )

    # Heading analysis options
    parser.add_argument(
        "--running-head-threshold",
        type=float,
        default=0.5,
        metavar="RATIO",
        help="Running head detection threshold as ratio of total pages (default: 0.5)"
    )

    # Page grouping option
    parser.add_argument(
        "--group-pages",
        action="store_true",
        help="Group pages by TOC structure (front-matter, chapter, section, subsection)"
    )

    # Header level mapping options
    parser.add_argument(
        "--header-level1",
        metavar="KEYWORDS",
        help="Level 1 keywords (pipe-separated, e.g., 'chapter')"
    )
    parser.add_argument(
        "--header-level2",
        metavar="KEYWORDS",
        help="Level 2 keywords (pipe-separated, e.g., 'episode|column')"
    )
    parser.add_argument(
        "--header-level3",
        metavar="KEYWORDS",
        help="Level 3 keywords (pipe-separated)"
    )
    parser.add_argument(
        "--header-level4",
        metavar="KEYWORDS",
        help="Level 4 keywords (pipe-separated)"
    )
    parser.add_argument(
        "--header-level5",
        metavar="KEYWORDS",
        help="Level 5 keywords (pipe-separated)"
    )

    return parser.parse_args(args)


def _extract_headings(pages: list[Page]) -> list[Heading]:
    """Extract all headings from pages.

    Args:
        pages: List of pages to extract headings from.

    Returns:
        List of all headings found in pages.
    """
    all_headings: list[Heading] = []
    for page in pages:
        for element in page.content.elements:
            if isinstance(element, Heading):
                all_headings.append(element)
    return all_headings


def _process_pages_with_headings(
    pages: list[Page],
    heading_map: dict[int, Heading]
) -> list[Page]:
    """Replace headings in pages with processed versions.

    Args:
        pages: Original pages.
        heading_map: Mapping from original heading id to processed heading.

    Returns:
        List of pages with processed headings.
    """
    processed_pages: list[Page] = []
    for page in pages:
        new_elements = []
        for element in page.content.elements:
            if isinstance(element, Heading):
                new_elements.append(heading_map[id(element)])
            else:
                new_elements.append(element)

        new_page = Page(
            number=page.number,
            source_file=page.source_file,
            announcement=page.announcement,
            content=Content(elements=tuple(new_elements), read_aloud=page.content.read_aloud),
            figures=page.figures,
            metadata=page.metadata,
            continued=page.continued,
            page_type=page.page_type,
        )
        processed_pages.append(new_page)

    return processed_pages


def convert_book(
    input_path: Path,
    output_path: Path,
    running_head_threshold: float = 0.5,
    verbose: bool = False,
    group_pages: bool = False,
    header_level_config: HeaderLevelConfig | None = None,
) -> ConversionResult:
    """Convert a Markdown book to XML.

    Args:
        input_path: Path to the input Markdown file.
        output_path: Path to the output XML file.
        running_head_threshold: Ratio threshold for running head detection (default: 0.5).
        verbose: If True, print exclusion reasons to stdout.
        group_pages: If True, group pages by TOC structure.
        header_level_config: Header level keyword mapping configuration.

    Returns:
        ConversionResult with conversion statistics and errors.
    """
    # Parse pages with error tracking
    pages, errors, toc = parse_pages_with_errors(input_path)

    # Extract and analyze headings
    all_headings = _extract_headings(pages)
    analyses = analyze_headings(all_headings)
    analyses = detect_running_head(analyses, len(pages), running_head_threshold)

    # Apply readAloud rules
    processed_headings = apply_read_aloud_rules(all_headings, analyses, verbose)
    heading_map = {id(orig): proc for orig, proc in zip(all_headings, processed_headings)}

    # Replace headings in pages
    processed_pages = _process_pages_with_headings(pages, heading_map)

    # Build and write XML
    book = Book(
        metadata=BookMetadata(title="Converted Book"),
        pages=tuple(processed_pages),
        toc=toc,
    )
    xml_string = build_xml_with_errors(book, errors)

    # Group pages if requested
    if group_pages:
        from src.book_converter.page_grouper import group_pages_by_toc
        xml_string = group_pages_by_toc(xml_string, header_level_config=header_level_config)

    # Write to output file
    output_path.write_text(xml_string, encoding="utf-8")

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

        # Build header level config from CLI args
        header_level_config = HeaderLevelConfig.from_cli_args(
            level1=parsed.header_level1,
            level2=parsed.header_level2,
            level3=parsed.header_level3,
            level4=parsed.header_level4,
            level5=parsed.header_level5,
        )

        # Convert
        if parsed.verbose:
            print(f"変換中: {input_path} -> {output_path}")
            if header_level_config.has_any_config():
                print(f"見出しレベル設定: L1={header_level_config.level1}, L2={header_level_config.level2}, L3={header_level_config.level3}")

        result = convert_book(
            input_path,
            output_path,
            running_head_threshold=parsed.running_head_threshold,
            verbose=parsed.verbose,
            group_pages=parsed.group_pages,
            header_level_config=header_level_config,
        )

        # Count markers
        marker_stats = count_markers(input_path)

        # Output summary (unless quiet mode)
        if not parsed.quiet:
            print(f"変換完了: {result.total_pages}ページ処理")
            # Marker statistics
            print(f"マーカー: toc={marker_stats.toc}, content={marker_stats.content}, skip={marker_stats.skip}")
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
