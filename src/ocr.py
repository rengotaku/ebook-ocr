"""OCR processing with EasyOCR or Tesseract for Japanese + English text extraction."""

from pathlib import Path

import pytesseract
from PIL import Image, ImageDraw


def _mask_figure_regions(
    img: Image.Image,
    page_name: str,
    layout: dict,
    crop_offset: tuple[int, int] = (0, 0),
) -> Image.Image:
    """White-out figure/table/formula regions so OCR only reads text.

    Args:
        img: The image to mask (preprocessed page).
        page_name: Page filename for layout lookup (e.g. "page_0022.png").
        layout: Full layout dict from layout.json.
        crop_offset: (left, top) pixel offset from preprocessing crop.

    Returns:
        Copy of image with figure regions filled white.
    """
    page_layout = layout.get(page_name, {})
    figures = page_layout.get("figures", [])
    if not figures:
        return img

    masked = img.copy()
    draw = ImageDraw.Draw(masked)
    ox, oy = crop_offset
    w, h = masked.size

    for fig in figures:
        x1, y1, x2, y2 = fig["bbox"]
        # Adjust for preprocessing crop offset
        x1, y1, x2, y2 = x1 - ox, y1 - oy, x2 - ox, y2 - oy
        # Clamp to image bounds
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        if x1 < x2 and y1 < y2:
            draw.rectangle([x1, y1, x2, y2], fill="white")

    return masked


def ocr_page_tesseract(
    image_path: str,
    languages: str = "jpn+eng",
    psm: int = 6,
    img: Image.Image | None = None,
) -> str:
    """Run Tesseract OCR on a single image.

    Args:
        image_path: Path to the image file.
        languages: Tesseract language codes joined by '+'.
        psm: Page segmentation mode. 6 = uniform block of text.
        img: Pre-loaded image. If provided, image_path is ignored.

    Returns:
        Extracted text.
    """
    if img is None:
        img = Image.open(image_path)
    config = f"--psm {psm}"
    return pytesseract.image_to_string(img, lang=languages, config=config)


def ocr_page_easyocr(
    image_path: str,
    reader,
    img: Image.Image | None = None,
) -> str:
    """Run EasyOCR on a single image.

    Args:
        image_path: Path to the image file.
        reader: Initialized EasyOCR Reader instance.
        img: Pre-loaded image. If provided, uses this instead of image_path.

    Returns:
        Extracted text.
    """
    import numpy as np

    if img is not None:
        results = reader.readtext(np.array(img), detail=0, paragraph=True)
    else:
        results = reader.readtext(str(image_path), detail=0, paragraph=True)
    return "\n".join(results)


def _format_figure_markers(page_name: str, layout: dict, min_confidence: float = 0.7) -> str:
    """Format figure detection markers for a page.

    Args:
        page_name: Page filename (e.g. "page_0030.png").
        layout: Full layout dict from layout.json.
        min_confidence: Minimum confidence threshold for including figures.

    Returns:
        Formatted marker string, or empty string if no figures.
    """
    page_layout = layout.get(page_name, {})
    figures = page_layout.get("figures", [])
    if not figures:
        return ""

    markers = []
    for fig in figures:
        conf = fig.get("confidence", 0)
        if conf < min_confidence:
            continue
        conf_str = f" (confidence: {conf})" if conf is not None else ""
        markers.append(f"[{fig['type']}: {fig['cropped_path']}{conf_str}]")
    return "\n".join(markers) + "\n" if markers else ""


def ocr_pages(
    page_dir: str,
    output_file: str,
    engine: str = "tesseract",
    languages: list[str] | None = None,
    gpu: bool = True,
    layout: dict | None = None,
) -> str:
    """Run OCR on all page images and combine into a single text file.

    Args:
        page_dir: Directory containing page images.
        output_file: Path to output text file.
        engine: OCR engine - "tesseract" or "easyocr".
        languages: Language codes. Defaults depend on engine.
        gpu: Whether to use GPU (EasyOCR only).
        layout: Layout dict from figure detection. If provided, figure
            markers are inserted into the output.

    Returns:
        Path to the output text file.
    """
    if layout is None:
        layout = {}

    pages = sorted(Path(page_dir).glob("page_*.png"))
    if not pages:
        print("No page images found")
        return output_file

    reader = None
    tess_lang = "jpn+eng"

    if engine == "easyocr":
        import easyocr

        if languages is None:
            languages = ["ja", "en"]
        print(f"Initializing EasyOCR with languages: {languages}")
        reader = easyocr.Reader(languages, gpu=gpu)
    else:
        if languages is not None:
            tess_lang = "+".join(languages)
        print(f"Using Tesseract with languages: {tess_lang}")

    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    all_text: list[str] = []

    # Preprocessing crop offset for bbox coordinate adjustment
    # Must match the crop ratios in preprocess.py
    crop_left_ratio = 0.06
    crop_top_ratio = 0.04
    sample_img = Image.open(pages[0])
    raw_w, raw_h = sample_img.size
    # Estimate original (pre-crop) size from preprocessed size
    orig_w = int(raw_w / (1.0 - crop_left_ratio - 0.02))
    orig_h = int(raw_h / (1.0 - crop_top_ratio - crop_top_ratio))
    crop_offset = (int(orig_w * crop_left_ratio), int(orig_h * crop_top_ratio))
    has_layout = bool(layout)
    if has_layout:
        print(f"  Figure masking enabled (crop offset: {crop_offset})")

    for i, page_path in enumerate(pages, 1):
        print(f"OCR processing page {i}/{len(pages)}: {page_path.name}")

        img = Image.open(page_path)
        if has_layout:
            img = _mask_figure_regions(img, page_path.name, layout, crop_offset)

        if engine == "easyocr":
            page_text = ocr_page_easyocr(str(page_path), reader, img=img if has_layout else None)
        else:
            page_text = ocr_page_tesseract(str(page_path), tess_lang, img=img if has_layout else None)

        markers = _format_figure_markers(page_path.name, layout)
        header = f"--- Page {i} ({page_path.name}) ---\n"
        all_text.append(f"{header}{markers}{page_text}")

    combined = "\n\n".join(all_text)
    out_path.write_text(combined, encoding="utf-8")
    print(f"OCR complete. Output saved to {out_path}")
    return output_file


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="OCR page images")
    parser.add_argument("page_dir", help="Directory with page images")
    parser.add_argument("-o", "--output", default="output/book.txt", help="Output text file")
    parser.add_argument("-e", "--engine", choices=["tesseract", "easyocr"], default="tesseract", help="OCR engine")
    parser.add_argument("--no-gpu", action="store_true", help="Disable GPU (EasyOCR)")
    parser.add_argument("--lang", nargs="+", default=None, help="Languages")
    args = parser.parse_args()

    ocr_pages(args.page_dir, args.output, args.engine, args.lang, gpu=not args.no_gpu)
