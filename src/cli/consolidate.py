"""CLI wrapper for consolidate."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.consolidate import consolidate_ocr_output
from src.logging_config import setup_logging


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
        print("Error: --limit must be a positive integer", file=sys.stderr)
        return 1

    # Validate input
    input_path = Path(args.ocr_dir)
    if not input_path.exists():
        print(f"Error: Input not found: {args.ocr_dir}", file=sys.stderr)
        return 1

    # Check if directory has OCR results
    ocr_texts_dir = input_path / "ocr_texts"
    if not ocr_texts_dir.exists() or not list(ocr_texts_dir.glob("*.txt")):
        print(f"Error: No OCR results found in: {args.ocr_dir}", file=sys.stderr)
        return 1

    # Call consolidation function
    try:
        consolidate_ocr_output(args.output, limit=args.limit)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
