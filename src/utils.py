"""Shared utility functions for image encoding and layout processing.

This module contains shared utility functions for image processing and OCR.
"""

from __future__ import annotations

import base64
import io

from PIL import Image, ImageDraw


def encode_image_file(path: str) -> str:
    """Read an image file and return its base64-encoded string.

    Args:
        path: File path to the image.

    Returns:
        Base64-encoded string of the image file contents.
    """
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def encode_pil_image(img: Image.Image) -> str:
    """Encode a PIL Image to base64 PNG string.

    Args:
        img: PIL Image object.

    Returns:
        Base64-encoded string of the image as PNG format.
    """
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def format_figure_markers(
    page_name: str,
    layout: dict,
    min_confidence: float = 0.7,
) -> str:
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


def mask_figure_regions(
    img: Image.Image,
    page_name: str,
    layout: dict,
) -> Image.Image:
    """White-out figure/table/formula regions so OCR only reads text.

    Uses raw page coordinates directly (no crop offset needed).

    Args:
        img: The raw page image.
        page_name: Page filename for layout lookup (e.g. "page_0169.png").
        layout: Full layout dict from layout.json.

    Returns:
        Copy of image with figure regions filled white, or original image
        if no figures are present for this page.
    """
    page_layout = layout.get(page_name, {})
    figures = page_layout.get("figures", [])
    if not figures:
        return img

    masked = img.copy()
    draw = ImageDraw.Draw(masked)
    w, h = masked.size

    for fig in figures:
        x1, y1, x2, y2 = fig["bbox"]
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(w, x2), min(h, y2)
        if x1 < x2 and y1 < y2:
            draw.rectangle([x1, y1, x2, y2], fill="white")

    return masked
