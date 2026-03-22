"""CLI wrapper for extract_frames."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from src.logging_config import setup_logging
from src.preprocessing.frames import extract_frames

logger = logging.getLogger(__name__)


def main() -> int:
    """CLI entry point."""
    setup_logging()
    parser = argparse.ArgumentParser(description="Extract frames from video")
    parser.add_argument("video", help="Input video file path")
    parser.add_argument("-o", "--output", required=True, help="Output directory")
    parser.add_argument(
        "-i",
        "--interval",
        type=float,
        default=1.5,
        help="Frame extraction interval in seconds (default: 1.5)",
    )
    args = parser.parse_args()

    # Validate input
    if not Path(args.video).exists():
        logger.error("Input not found: %s", args.video)
        return 1

    # Call existing function
    try:
        extract_frames(args.video, args.output, args.interval)
        return 0
    except Exception as e:
        logger.error("Error: %s", e)
        return 1


if __name__ == "__main__":
    sys.exit(main())
