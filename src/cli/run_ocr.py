"""CLI wrapper for run_ocr."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.ocr_rover import run_rover_batch


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="Run OCR on pages")
    parser.add_argument("pages_dir", help="Pages directory")
    parser.add_argument("-o", "--output", required=True, help="Output directory")
    parser.add_argument(
        "--layout-dir",
        help="Layout directory (optional)",
    )
    parser.add_argument(
        "--device",
        choices=["cpu", "cuda"],
        default="cpu",
        help="Device to use (default: cpu)",
    )
    args = parser.parse_args()

    # Validate input
    if not Path(args.pages_dir).exists():
        print(f"Error: Input not found: {args.pages_dir}", file=sys.stderr)
        return 1

    # Call existing function
    try:
        run_rover_batch(
            args.pages_dir,
            args.output,
            device=args.device,
        )
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
