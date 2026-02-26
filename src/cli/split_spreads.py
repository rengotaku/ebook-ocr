"""CLI wrapper for split_spreads."""

from __future__ import annotations

import argparse
import shutil
import sys
import tempfile
from pathlib import Path

from src.preprocessing.split_spread import (
    SpreadMode,
    TrimConfig,
    get_spread_mode,
    renumber_pages,
    split_spread_pages,
)


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


def preview_trim_check(preview_dir: str) -> bool:
    """Check if preview/frames/ exists and contains images.

    Args:
        preview_dir: Path to preview directory (e.g., "output/abc123/preview")

    Returns:
        True if frames exist and directory is not empty

    Raises:
        FileNotFoundError: If frames directory doesn't exist or is empty
        ValueError: If preview structure is invalid
    """
    preview_path = Path(preview_dir)
    frames_dir = preview_path / "frames"

    if not frames_dir.exists():
        msg = (
            f"Error: {frames_dir} does not exist.\n"
            "Please run 'make preview-extract VIDEO=<video> LIMIT=<n>' first to extract frames."
        )
        raise FileNotFoundError(msg)

    # Check if frames directory has any PNG files
    png_files = list(frames_dir.glob("*.png"))
    if not png_files:
        msg = f"Error: {frames_dir} exists but contains no PNG files. Please run preview-extract first."
        raise ValueError(msg)

    return True


def preview_trim(
    preview_dir: str,
    mode: SpreadMode,
    trim_config: TrimConfig | None = None,
) -> None:
    """Apply trim to preview frames and output to preview/trimmed/.

    This function processes frames from preview/frames/ and outputs trimmed images
    to preview/trimmed/. It does NOT extract new frames from video.

    Args:
        preview_dir: Path to preview directory (e.g., "output/abc123/preview")
        mode: Processing mode (SINGLE or SPREAD)
        trim_config: Trim configuration (global + split trim)

    Raises:
        FileNotFoundError: If frames directory doesn't exist
        ValueError: If frames directory is empty
    """
    # Validate frames exist
    preview_trim_check(preview_dir)

    preview_path = Path(preview_dir)
    frames_dir = preview_path / "frames"
    trimmed_dir = preview_path / "trimmed"

    # Create trimmed directory if it doesn't exist
    trimmed_dir.mkdir(parents=True, exist_ok=True)

    # Use temporary directory to avoid modifying original frames
    # split_spread_pages moves input files to originals/, so we copy to temp first
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir) / "pages"
        temp_path.mkdir(parents=True)

        # Copy frames to temp directory, renaming frame_*.png to page_*.png
        # (split_spread_pages expects page_*.png naming)
        for frame in sorted(frames_dir.glob("*.png")):
            # Extract number from frame_NNNN.png or page_NNNN.png
            stem = frame.stem
            if stem.startswith("frame_"):
                new_name = f"page_{stem[6:]}.png"
            else:
                new_name = frame.name
            shutil.copy2(frame, temp_path / new_name)

        # Process from temp directory to trimmed directory
        split_spread_pages(
            str(temp_path),
            mode=mode,
            trim_config=trim_config,
            output_dir=str(trimmed_dir),
        )

    print(f"Preview trim complete. Output: {trimmed_dir}")


if __name__ == "__main__":
    sys.exit(main())
