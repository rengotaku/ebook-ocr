"""Split spread (見開き) images into separate left and right pages.

This module handles book spread images where two pages appear side by side.
It splits them into individual page images for proper OCR processing.
"""

from pathlib import Path

from PIL import Image


def is_spread_image(img: Image.Image, aspect_ratio_threshold: float = 1.2) -> bool:
    """Check if image appears to be a spread (2 pages side by side).

    Args:
        img: PIL Image to check.
        aspect_ratio_threshold: Width/height ratio above which image is
            considered a spread. Default 1.2 (wider than tall).

    Returns:
        True if image appears to be a spread.
    """
    width, height = img.size
    aspect_ratio = width / height
    return aspect_ratio >= aspect_ratio_threshold


def split_spread(
    img: Image.Image,
    overlap_px: int = 0,
    left_trim_pct: float = 0.0,
    right_trim_pct: float = 0.0,
) -> tuple[Image.Image, Image.Image]:
    """Split a spread image into left and right pages.

    Args:
        img: PIL Image of the spread.
        overlap_px: Pixels of overlap to include from center (for gutter text).
            Default 0 (exact split at center).
        left_trim_pct: Percentage to trim from left edge of left page (0.0-1.0).
            E.g., 0.03 = 3% trimmed from outer edge.
        right_trim_pct: Percentage to trim from right edge of right page (0.0-1.0).
            E.g., 0.03 = 3% trimmed from outer edge.

    Returns:
        Tuple of (left_page, right_page) as PIL Images.
    """
    width, height = img.size
    mid_x = width // 2
    half_width = mid_x

    # Calculate trim pixels
    left_trim_px = int(half_width * left_trim_pct)
    right_trim_px = int(half_width * right_trim_pct)

    # Left page: from left_trim to mid_x + overlap
    left_page = img.crop((left_trim_px, 0, mid_x + overlap_px, height))

    # Right page: from mid_x - overlap to width - right_trim
    right_page = img.crop((mid_x - overlap_px, 0, width - right_trim_px, height))

    return left_page, right_page


def split_spread_pages(
    pages_dir: str,
    output_dir: str | None = None,
    aspect_ratio_threshold: float = 1.2,
    overlap_px: int = 0,
    left_trim_pct: float = 0.0,
    right_trim_pct: float = 0.0,
) -> list[Path]:
    """Split all spread images in a directory into separate pages.

    Supports iterative adjustment:
    - First run: moves originals to originals/ subfolder, splits to pages/
    - Subsequent runs: re-splits from originals/ with new settings

    Args:
        pages_dir: Directory containing page images.
        output_dir: Output directory for split pages. Defaults to pages_dir.
        aspect_ratio_threshold: Width/height ratio for spread detection.
        overlap_px: Pixels of overlap from center.
        left_trim_pct: Percentage to trim from left edge of left page (0.0-1.0).
        right_trim_pct: Percentage to trim from right edge of right page (0.0-1.0).

    Returns:
        List of output file paths (includes both split and non-split pages).
    """
    pages_path = Path(pages_dir)
    out = Path(output_dir) if output_dir else pages_path
    originals_dir = pages_path.parent / "originals"

    # Determine source directory
    if originals_dir.exists() and list(originals_dir.glob("page_*.png")):
        # Use existing originals (re-run with new settings)
        src = originals_dir
        print(f"  Using originals from: {originals_dir}")

        # Clear existing split pages
        for existing in pages_path.glob("page_*.png"):
            existing.unlink()
    else:
        # First run: check if pages exist
        pages = sorted(pages_path.glob("page_*.png"))
        if not pages:
            print("No page images found")
            return []

        # Move originals to originals/
        originals_dir.mkdir(parents=True, exist_ok=True)
        print(f"  Moving originals to: {originals_dir}")
        for page_path in pages:
            dest = originals_dir / page_path.name
            page_path.rename(dest)

        src = originals_dir

    if out != pages_path:
        out.mkdir(parents=True, exist_ok=True)

    # Process from source (originals)
    pages = sorted(src.glob("page_*.png"))
    output_files: list[Path] = []
    split_count = 0

    for page_path in pages:
        img = Image.open(page_path)

        if is_spread_image(img, aspect_ratio_threshold):
            # Split into left and right
            left_page, right_page = split_spread(img, overlap_px, left_trim_pct, right_trim_pct)

            # Generate output names: page_0001.png → page_0001_L.png, page_0001_R.png
            stem = page_path.stem
            left_path = out / f"{stem}_L.png"
            right_path = out / f"{stem}_R.png"

            left_page.save(left_path)
            right_page.save(right_path)

            output_files.extend([left_path, right_path])
            split_count += 1
        else:
            # Not a spread, copy as-is
            dest = out / page_path.name
            img.save(dest)
            output_files.append(dest)

        img.close()

    print(f"Split complete: {split_count} spreads → {split_count * 2} pages")
    print(f"Total pages: {len(output_files)}")

    return sorted(output_files)


def renumber_pages(pages_dir: str) -> list[Path]:
    """Renumber page files sequentially after splitting.

    Converts page_0001_L.png, page_0001_R.png, page_0002.png, ...
    to page_0001.png, page_0002.png, page_0003.png, ...

    Args:
        pages_dir: Directory containing page images.

    Returns:
        List of renamed file paths.
    """
    src = Path(pages_dir)
    pages = sorted(src.glob("page_*.png"))

    if not pages:
        return []

    # First pass: rename to temporary names to avoid conflicts
    temp_names = []
    for i, page_path in enumerate(pages):
        temp_path = src / f"_temp_{i:04d}.png"
        page_path.rename(temp_path)
        temp_names.append(temp_path)

    # Second pass: rename to final sequential names
    output_files = []
    for i, temp_path in enumerate(temp_names):
        final_path = src / f"page_{i + 1:04d}.png"
        temp_path.rename(final_path)
        output_files.append(final_path)

    print(f"Renumbered {len(output_files)} pages")
    return output_files


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Split spread images into separate pages")
    parser.add_argument("pages_dir", help="Directory containing page images")
    parser.add_argument("-o", "--output", help="Output directory (default: same as input)")
    parser.add_argument(
        "--aspect-ratio",
        type=float,
        default=1.2,
        help="Aspect ratio threshold for spread detection (default: 1.2)",
    )
    parser.add_argument(
        "--overlap",
        type=int,
        default=0,
        help="Pixels of overlap from center (default: 0)",
    )
    parser.add_argument(
        "--left-trim",
        type=float,
        default=0.0,
        help="Percentage to trim from left edge of left page (default: 0.0, e.g., 0.03 = 3%%)",
    )
    parser.add_argument(
        "--right-trim",
        type=float,
        default=0.0,
        help="Percentage to trim from right edge of right page (default: 0.0, e.g., 0.03 = 3%%)",
    )
    parser.add_argument(
        "--renumber",
        action="store_true",
        help="Renumber pages sequentially after splitting",
    )
    args = parser.parse_args()

    split_spread_pages(
        args.pages_dir,
        args.output,
        aspect_ratio_threshold=args.aspect_ratio,
        overlap_px=args.overlap,
        left_trim_pct=args.left_trim,
        right_trim_pct=args.right_trim,
    )

    if args.renumber:
        output_dir = args.output or args.pages_dir
        renumber_pages(output_dir)
