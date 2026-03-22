"""CLI wrapper for detect_layout."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from src.layout.detector import detect_layout
from src.logging_config import setup_logging

logger = logging.getLogger(__name__)


def main() -> int:
    """CLI entry point."""
    setup_logging()
    parser = argparse.ArgumentParser(description="Detect page layout")
    parser.add_argument("pages_dir", help="Pages directory")
    parser.add_argument("-o", "--output", required=True, help="Output directory")
    parser.add_argument(
        "--device",
        choices=["cpu", "cuda"],
        default="cpu",
        help="Device to use (default: cpu)",
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
    if not Path(args.pages_dir).exists():
        logger.error("Input not found: %s", args.pages_dir)
        return 1

    # Call existing function
    try:
        detect_layout(args.pages_dir, args.output, device=args.device, limit=args.limit)
        return 0
    except Exception as e:
        logger.error("Error: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
