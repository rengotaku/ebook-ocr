"""CLI wrapper for consolidate."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.consolidate import consolidate_rover_output


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Consolidate OCR results")
    parser.add_argument("ocr_dir", help="OCR directory")
    parser.add_argument("-o", "--output", required=True, help="Output directory")
    parser.add_argument(
        "--limit",
        type=int,
        help="Process only first N files (for testing)",
    )
    args = parser.parse_args()

    # Validate input
    input_path = Path(args.ocr_dir)
    if not input_path.exists():
        print(f"Error: Input not found: {args.ocr_dir}", file=sys.stderr)
        return 1

    # Check if directory has OCR results
    ocr_output_dir = input_path / "ocr_output" / "rover"
    if not ocr_output_dir.exists() or not list(ocr_output_dir.glob("*.txt")):
        print(f"Error: No OCR results found in: {args.ocr_dir}", file=sys.stderr)
        return 1

    # Call existing function
    try:
        consolidate_rover_output(args.ocr_dir, limit=args.limit)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
