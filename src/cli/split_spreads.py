"""CLI wrapper for split_spreads."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.preprocessing.split_spread import renumber_pages, split_spread_pages


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Split spread pages into separate images")
    parser.add_argument("pages_dir", help="Pages directory (in-place update)")
    parser.add_argument(
        "--aspect-ratio",
        type=float,
        default=1.2,
        help="Aspect ratio threshold for spread detection (default: 1.2)",
    )
    parser.add_argument(
        "--left-trim",
        type=float,
        default=0.0,
        help="Percentage to trim from left edge of left page (default: 0.0)",
    )
    parser.add_argument(
        "--right-trim",
        type=float,
        default=0.0,
        help="Percentage to trim from right edge of right page (default: 0.0)",
    )
    args = parser.parse_args()

    # Validate input
    if not Path(args.pages_dir).exists():
        print(f"Error: Input not found: {args.pages_dir}", file=sys.stderr)
        return 1

    # Call existing functions
    try:
        split_spread_pages(
            args.pages_dir,
            aspect_ratio_threshold=args.aspect_ratio,
            left_trim_pct=args.left_trim,
            right_trim_pct=args.right_trim,
        )
        renumber_pages(args.pages_dir)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
