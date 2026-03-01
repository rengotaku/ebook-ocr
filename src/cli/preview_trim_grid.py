"""Preview trim grid visualization CLI.

This tool draws trim guide lines on preview images to help identify optimal trim values.
Grid lines are color-coded by direction:
- Top: Red (#FF0000)
- Bottom: Blue (#0000FF)
- Left: Green (#00FF00)
- Right: Orange (#FFA500)
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    """Parse command-line arguments.

    Args:
        argv: Command-line arguments (default: sys.argv[1:])

    Returns:
        Parsed arguments namespace
    """
    parser = argparse.ArgumentParser(
        description="Draw trim guide lines on preview images",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Grid line colors:
  Top:    Red (#FF0000)
  Bottom: Blue (#0000FF)
  Left:   Green (#00FF00)
  Right:  Orange (#FFA500)

Example:
  python -m src.cli.preview_trim_grid frames/ -o trim-grid/ --step 0.05 --max 0.30
        """,
    )

    parser.add_argument(
        "input_dir",
        type=Path,
        help="Input directory containing PNG images",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        required=True,
        help="Output directory for images with grid lines",
    )

    parser.add_argument(
        "--step",
        type=float,
        default=0.05,
        help="Grid line step size (default: 0.05)",
    )

    parser.add_argument(
        "--max",
        type=float,
        default=0.30,
        help="Maximum trim ratio (default: 0.30)",
    )

    parser.add_argument(
        "--spread-mode",
        choices=["single", "spread"],
        default="single",
        help="Spread mode (default: single)",
    )

    return parser.parse_args(argv)


def validate_args(args: argparse.Namespace) -> None:
    """Validate parsed arguments.

    Args:
        args: Parsed arguments

    Raises:
        SystemExit: If validation fails
    """
    # Validate input directory exists
    if not args.input_dir.exists():
        print(f"Error: Input directory does not exist: {args.input_dir}", file=sys.stderr)
        sys.exit(1)

    # Validate step > 0
    if args.step <= 0:
        print("Error: --step must be greater than 0", file=sys.stderr)
        sys.exit(1)

    # Validate step <= max
    if args.step > args.max:
        print("Error: --step must be less than or equal to --max", file=sys.stderr)
        sys.exit(1)

    # Validate max < 0.5
    if args.max >= 0.5:
        print("Error: --max must be less than 0.5", file=sys.stderr)
        sys.exit(1)


def draw_grid(
    image: Image.Image,
    step: float,
    max_ratio: float,
) -> Image.Image:
    """Draw trim grid lines on image.

    Args:
        image: Input PIL Image
        step: Grid line step size
        max_ratio: Maximum trim ratio

    Returns:
        Image with grid lines drawn
    """
    # Create a copy to avoid modifying the original
    img = image.copy()
    draw = ImageDraw.Draw(img)
    width, height = img.size

    # Try to load a font, fall back to default if not available
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 12)
    except (OSError, ImportError):
        font = ImageFont.load_default()

    # Generate trim ratios
    ratios = []
    ratio = step
    while ratio <= max_ratio:
        ratios.append(ratio)
        ratio += step

    # Draw top lines (red)
    for ratio in ratios:
        y = int(height * ratio)
        draw.line([(0, y), (width, y)], fill=(255, 0, 0), width=1)
        label = f"T:{ratio:.2f}"
        draw.text((5, y + 2), label, fill=(255, 0, 0), font=font)

    # Draw bottom lines (blue)
    for ratio in ratios:
        y = int(height * (1 - ratio))
        draw.line([(0, y), (width, y)], fill=(0, 0, 255), width=1)
        label = f"B:{ratio:.2f}"
        draw.text((5, y - 15), label, fill=(0, 0, 255), font=font)

    # Draw left lines (green)
    for ratio in ratios:
        x = int(width * ratio)
        draw.line([(x, 0), (x, height)], fill=(0, 255, 0), width=1)
        label = f"L:{ratio:.2f}"
        draw.text((x + 2, 5), label, fill=(0, 255, 0), font=font)

    # Draw right lines (orange)
    for ratio in ratios:
        x = int(width * (1 - ratio))
        draw.line([(x, 0), (x, height)], fill=(255, 165, 0), width=1)
        label = f"R:{ratio:.2f}"
        draw.text((x - 50, 5), label, fill=(255, 165, 0), font=font)

    return img


def process_images(
    input_dir: Path,
    output_dir: Path,
    step: float,
    max_ratio: float,
) -> None:
    """Process all PNG images in input directory.

    Args:
        input_dir: Input directory path
        output_dir: Output directory path
        step: Grid line step size
        max_ratio: Maximum trim ratio
    """
    # Create output directory if it doesn't exist
    output_dir.mkdir(parents=True, exist_ok=True)

    # Process all PNG files
    png_files = sorted(input_dir.glob("*.png"))

    for png_file in png_files:
        # Load image
        img = Image.open(png_file)

        # Draw grid
        img_with_grid = draw_grid(img, step, max_ratio)

        # Save output
        output_path = output_dir / png_file.name
        img_with_grid.save(output_path)


def main(argv: list[str] | None = None) -> int:
    """Main entry point.

    Args:
        argv: Command-line arguments (default: sys.argv[1:])

    Returns:
        Exit code (0 for success, 1 for error)
    """
    try:
        args = parse_args(argv)
        validate_args(args)

        process_images(
            input_dir=args.input_dir,
            output_dir=args.output,
            step=args.step,
            max_ratio=args.max,
        )

        return 0

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
