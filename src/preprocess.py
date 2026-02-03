"""Image preprocessing for OCR quality improvement."""

from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageEnhance, ImageFilter


def _invert_dark_badges(arr: np.ndarray, dark_thresh: int = 80) -> np.ndarray:
    """Detect and invert dark badge regions (white text on dark background).

    Finds small, dense, dark connected components typical of section number
    badges (e.g. "1.1.3" in a dark rounded rectangle) and inverts them
    so OCR can read the white-on-dark text.

    Args:
        arr: Grayscale image as numpy array.
        dark_thresh: Pixel threshold for dark region detection.

    Returns:
        Image array with dark badges inverted.
    """
    _, binary = cv2.threshold(arr, dark_thresh, 255, cv2.THRESH_BINARY_INV)
    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        binary, connectivity=8,
    )

    result = arr.copy()
    for i in range(1, num_labels):
        x, y, bw, bh, area = stats[i]
        if not (40 <= bw <= 400 and 15 <= bh <= 80):
            continue
        fill_ratio = area / (bw * bh)
        if fill_ratio < 0.7:
            continue
        roi = arr[y : y + bh, x : x + bw]
        if roi.mean() > 100:
            continue
        # Dark, dense, badge-sized → invert
        result[y : y + bh, x : x + bw] = 255 - roi

    return result


def preprocess_page(
    img: Image.Image,
    crop_ratio: dict[str, float] | None = None,
    contrast: float = 1.5,
    sharpen: bool = True,
    grayscale: bool = True,
    binarize: bool = True,
    invert_badges: bool = True,
    adaptive_block_size: int = 31,
    adaptive_c: int = 15,
) -> Image.Image:
    """Preprocess a page image for better OCR accuracy.

    Args:
        img: Input PIL Image.
        crop_ratio: Ratio to crop from each side (top, bottom, left, right).
            Values are fractions of image dimension (0.0 to 1.0).
        contrast: Contrast enhancement factor. 1.0 = no change, >1.0 = more contrast.
        sharpen: Whether to apply sharpening filter.
        grayscale: Whether to convert to grayscale.
        binarize: Whether to apply adaptive thresholding.
            Effective for colored highlights, gray backgrounds, etc.
        adaptive_block_size: Block size for adaptive threshold (must be odd).
        adaptive_c: Constant subtracted from the mean in adaptive threshold.

    Returns:
        Preprocessed PIL Image.
    """
    if crop_ratio is None:
        crop_ratio = {
            "top": 0.04,
            "bottom": 0.04,
            "left": 0.06,
            "right": 0.02,
        }

    w, h = img.size
    left = int(w * crop_ratio.get("left", 0))
    top = int(h * crop_ratio.get("top", 0))
    right = int(w * (1 - crop_ratio.get("right", 0)))
    bottom = int(h * (1 - crop_ratio.get("bottom", 0)))
    img = img.crop((left, top, right, bottom))

    if grayscale:
        img = img.convert("L")

    if contrast != 1.0:
        img = ImageEnhance.Contrast(img).enhance(contrast)

    if sharpen:
        img = img.filter(ImageFilter.SHARPEN)

    if invert_badges or binarize:
        arr = np.array(img)
        if arr.ndim == 3:
            arr = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
        if invert_badges:
            arr = _invert_dark_badges(arr)
        if binarize:
            arr = cv2.adaptiveThreshold(
                arr, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY,
                adaptive_block_size, adaptive_c,
            )
        img = Image.fromarray(arr)

    return img


def preprocess_pages(
    page_dir: str,
    output_dir: str,
    **kwargs,
) -> list[Path]:
    """Preprocess all page images in a directory.

    Args:
        page_dir: Directory containing page images.
        output_dir: Directory to save preprocessed images.
        **kwargs: Arguments passed to preprocess_page.

    Returns:
        Sorted list of preprocessed image paths.
    """
    src = Path(page_dir)
    dst = Path(output_dir)
    dst.mkdir(parents=True, exist_ok=True)

    pages = sorted(src.glob("page_*.png"))
    results: list[Path] = []

    for page_path in pages:
        img = Image.open(page_path)
        processed = preprocess_page(img, **kwargs)
        out_path = dst / page_path.name
        processed.save(out_path)
        results.append(out_path)

    print(f"Preprocessed {len(results)} pages to {dst}")
    return results


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Preprocess page images for OCR")
    parser.add_argument("page_dir", help="Directory with page images")
    parser.add_argument("-o", "--output", default="output/preprocessed", help="Output directory")
    parser.add_argument("--contrast", type=float, default=1.5, help="Contrast factor")
    parser.add_argument("--no-sharpen", action="store_true", help="Disable sharpening")
    parser.add_argument("--no-grayscale", action="store_true", help="Keep color")
    args = parser.parse_args()

    preprocess_pages(
        args.page_dir,
        args.output,
        contrast=args.contrast,
        sharpen=not args.no_sharpen,
        grayscale=not args.no_grayscale,
    )
