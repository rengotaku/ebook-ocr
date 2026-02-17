"""CLI wrapper for deduplicate."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.deduplicate import deduplicate_frames


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Remove duplicate frames")
    parser.add_argument("input_dir", help="Input directory with frames")
    parser.add_argument("-o", "--output", required=True, help="Output directory")
    parser.add_argument(
        "-t",
        "--threshold",
        type=int,
        default=8,
        help="Hash distance threshold (default: 8)",
    )
    args = parser.parse_args()

    # Validate input
    input_path = Path(args.input_dir)
    if not input_path.exists():
        print(f"Error: Input not found: {args.input_dir}", file=sys.stderr)
        return 1

    if not input_path.is_dir():
        print(f"Error: Input is not a directory: {args.input_dir}", file=sys.stderr)
        return 1

    # Check if directory is empty
    if not list(input_path.glob("frame_*.png")):
        print(f"Error: No frames found in: {args.input_dir}", file=sys.stderr)
        return 1

    # Call existing function
    try:
        deduplicate_frames(args.input_dir, args.output, args.threshold)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
