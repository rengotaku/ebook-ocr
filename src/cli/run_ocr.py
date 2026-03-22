"""CLI wrapper for run_ocr (layout-aware single-engine OCR)."""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from src.layout_ocr import run_layout_ocr
from src.logging_config import setup_logging

logger = logging.getLogger(__name__)


def main() -> int:
    """CLI entry point."""
    setup_logging()
    parser = argparse.ArgumentParser(description="Run OCR on pages")
    parser.add_argument("pages_dir", help="Pages directory")
    parser.add_argument("-o", "--output", required=True, help="Output directory")
    parser.add_argument(
        "--layout-dir",
        help="Layout directory containing layout.json",
    )
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
    pages_path = Path(args.pages_dir)
    if not pages_path.exists():
        logger.error("Input not found: %s", args.pages_dir)
        return 1

    # Load layout.json
    layout_data: dict = {}
    if args.layout_dir:
        layout_file = Path(args.layout_dir) / "layout.json"
        if layout_file.exists():
            with open(layout_file, encoding="utf-8") as f:
                layout_data = json.load(f)

    # Apply --limit: filter pages before passing to run_layout_ocr
    if args.limit is not None:
        all_pages = sorted(pages_path.glob("*.png"))
        if args.limit < len(all_pages):
            logger.warning(
                "Limiting to first %d of %d files",
                args.limit,
                len(all_pages),
            )
            # Filter layout_data to only include limited pages
            limited_pages = {p.name for p in all_pages[: args.limit]}
            layout_data = {k: v for k, v in layout_data.items() if k in limited_pages}

    # Call layout-aware OCR
    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / "ocr_combined.txt"

    try:
        run_layout_ocr(
            pages_dir=args.pages_dir,
            layout_data=layout_data,
            output_file=str(output_file),
            device=args.device,
            limit=args.limit,
        )
        return 0
    except Exception as e:
        logger.error("Error: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
