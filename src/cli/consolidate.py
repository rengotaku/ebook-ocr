"""CLI wrapper for consolidate."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from src.consolidate import consolidate_ocr_output
from src.logging_config import setup_logging

logger = logging.getLogger(__name__)


def main() -> int:
    """CLI entry point."""
    setup_logging()
    parser = argparse.ArgumentParser(description="Consolidate OCR results")
    parser.add_argument("ocr_dir", help="OCR directory")
    parser.add_argument("-o", "--output", required=True, help="Output directory")
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
    input_path = Path(args.ocr_dir)
    if not input_path.exists():
        logger.error("Input not found: %s", args.ocr_dir)
        return 1

    # Check if directory has OCR results
    ocr_texts_dir = input_path / "ocr_texts"
    if not ocr_texts_dir.exists() or not list(ocr_texts_dir.glob("*.txt")):
        logger.error("No OCR results found in: %s", args.ocr_dir)
        return 1

    # Call consolidation function
    try:
        consolidate_ocr_output(args.output, limit=args.limit)
        return 0
    except Exception as e:
        logger.error("Error: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
