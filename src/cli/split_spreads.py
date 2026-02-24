"""CLI wrapper for split_spreads."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.preprocessing.split_spread import get_spread_mode, renumber_pages, split_spread_pages


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Split spread pages into separate images")
    parser.add_argument("pages_dir", help="Pages directory (in-place update)")
    parser.add_argument(
        "--mode",
        type=str,
        default=None,
        choices=["single", "spread"],
        help="Processing mode: 'single' (no split) or 'spread' (always split). Default: 'single'",
    )
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
    parser.add_argument(
        "--global-trim-top",
        type=float,
        default=0.0,
        help="Percentage to trim from top before splitting (default: 0.0)",
    )
    parser.add_argument(
        "--global-trim-bottom",
        type=float,
        default=0.0,
        help="Percentage to trim from bottom before splitting (default: 0.0)",
    )
    parser.add_argument(
        "--global-trim-left",
        type=float,
        default=0.0,
        help="Percentage to trim from left before splitting (default: 0.0)",
    )
    parser.add_argument(
        "--global-trim-right",
        type=float,
        default=0.0,
        help="Percentage to trim from right before splitting (default: 0.0)",
    )
    args = parser.parse_args()

    # Validate input
    if not Path(args.pages_dir).exists():
        print(f"Error: Input not found: {args.pages_dir}", file=sys.stderr)
        return 1

    # Get mode (CLI argument > env var > default)
    try:
        mode = get_spread_mode(args.mode)
    except ValueError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

    # Build trim config from CLI arguments
    trim_config = None
    if any(
        [
            args.global_trim_top != 0.0,
            args.global_trim_bottom != 0.0,
            args.global_trim_left != 0.0,
            args.global_trim_right != 0.0,
            args.left_trim != 0.0,
            args.right_trim != 0.0,
        ]
    ):
        try:
            trim_config = TrimConfig(
                global_top=args.global_trim_top,
                global_bottom=args.global_trim_bottom,
                global_left=args.global_trim_left,
                global_right=args.global_trim_right,
                left_page_outer=args.left_trim,
                right_page_outer=args.right_trim,
            )
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1

    # Call existing functions
    try:
        split_spread_pages(
            args.pages_dir,
            aspect_ratio_threshold=args.aspect_ratio,
            mode=mode,
            trim_config=trim_config,
        )
        renumber_pages(args.pages_dir)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
