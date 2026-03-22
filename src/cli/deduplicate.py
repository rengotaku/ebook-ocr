"""CLI wrapper for deduplicate."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from src.logging_config import setup_logging
from src.preprocessing.deduplicate import deduplicate_frames

logger = logging.getLogger(__name__)


def main() -> int:
    """CLI entry point."""
    setup_logging()
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
    parser.add_argument(
        "--limit",
        type=int,
        help="Process only first N files (for testing)",
    )
    args = parser.parse_args()

    # Validate --limit
    if args.limit is not None and args.limit <= 0:
        logger.error("--limit must be a positive integer")
        return 1

    # Validate input
    input_path = Path(args.input_dir)
    if not input_path.exists():
        logger.error("Input not found: %s", args.input_dir)
        return 1

    if not input_path.is_dir():
        logger.error("Input is not a directory: %s", args.input_dir)
        return 1

    # Check if directory is empty
    if not list(input_path.glob("frame_*.png")):
        logger.error("No frames found in: %s", args.input_dir)
        return 1

    # Call existing function
    try:
        deduplicate_frames(args.input_dir, args.output, args.threshold, limit=args.limit)
        return 0
    except Exception as e:
        logger.error("Error: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
