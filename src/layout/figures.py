"""Detect figures, tables, and formulas in page images using DocLayout-YOLO."""

import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

# DocLayout-YOLO class name → output TYPE mapping
LABEL_TYPE_MAP = {
    "title": "TITLE",
    "plain text": "TEXT",
    "abandon": "ABANDON",
    "figure": "FIGURE",
    "figure_caption": "CAPTION",
    "table": "TABLE",
    "table_caption": "CAPTION",
    "table_footnote": "FOOTNOTE",
    "isolated formula": "FORMULA",
    "formula_caption": "CAPTION",
}

# Labels we care about (all 10 classes from DocLayout-YOLO)
TARGET_LABELS = set(LABEL_TYPE_MAP.keys())

# HuggingFace model info
HF_REPO_ID = "juliozhao/DocLayout-YOLO-DocStructBench"
HF_MODEL_FILE = "doclayout_yolo_docstructbench_imgsz1024.pt"

# Colors for visualization (RGB)
TYPE_COLORS = {
    "TITLE": (255, 0, 0),  # Red
    "TEXT": (0, 128, 0),  # Green
    "ABANDON": (128, 128, 128),  # Gray
    "FIGURE": (0, 0, 255),  # Blue
    "CAPTION": (255, 165, 0),  # Orange
    "TABLE": (128, 0, 128),  # Purple
    "FOOTNOTE": (0, 128, 128),  # Teal
    "FORMULA": (255, 0, 255),  # Magenta
}


def draw_layout_boxes(
    img: Image.Image,
    regions: list[dict],
    line_width: int = 3,
) -> Image.Image:
    """Draw bounding boxes with labels on image.

    Args:
        img: Original PIL Image.
        regions: List of region dicts with type, bbox, confidence.
        line_width: Width of bounding box lines.

    Returns:
        New image with boxes drawn.
    """
    result = img.copy().convert("RGB")
    draw = ImageDraw.Draw(result)

    # Try to get a font, fall back to default if not available
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except (OSError, IOError):
        font = ImageFont.load_default()

    for region in regions:
        region_type = region["type"]
        bbox = region["bbox"]
        conf = region.get("confidence", 0)
        color = TYPE_COLORS.get(region_type, (0, 0, 0))

        # Draw rectangle
        x1, y1, x2, y2 = bbox
        draw.rectangle([x1, y1, x2, y2], outline=color, width=line_width)

        # Draw label background
        label = f"{region_type} {conf:.2f}"
        text_bbox = draw.textbbox((x1, y1), label, font=font)
        text_w = text_bbox[2] - text_bbox[0]
        text_h = text_bbox[3] - text_bbox[1]
        draw.rectangle([x1, y1 - text_h - 4, x1 + text_w + 4, y1], fill=color)

        # Draw label text
        draw.text((x1 + 2, y1 - text_h - 2), label, fill=(255, 255, 255), font=font)

    return result


def detect_figures(
    page_dir: str,
    output_dir: str,
    figures_dir: str | None = None,
    layouts_dir: str | None = None,
    min_confidence: float = 0.3,
    min_area: float = 0.01,
) -> dict:
    """Detect figures, tables, and formulas in page images.

    Args:
        page_dir: Directory containing page images (preprocessed or raw).
        output_dir: Directory to save layout.json.
        figures_dir: Directory to save cropped figure images.
            Defaults to output_dir/figures.
        layouts_dir: Directory to save layout visualizations (images with bboxes).
            Defaults to output_dir/layouts.
        min_confidence: Minimum confidence threshold for detection.
        min_area: Minimum area threshold as a fraction of page area (default: 0.01 = 1%).

    Returns:
        Layout dict mapping page filenames to detected elements.
    """
    from doclayout_yolo import YOLOv10
    from huggingface_hub import hf_hub_download

    src = Path(page_dir)
    out = Path(output_dir)
    fig_dir = Path(figures_dir) if figures_dir else out / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)
    lay_dir = Path(layouts_dir) if layouts_dir else out / "layouts"
    lay_dir.mkdir(parents=True, exist_ok=True)

    pages = sorted(src.glob("page_*.png"))
    if not pages:
        print("No page images found")
        return {}

    print("Loading DocLayout-YOLO model...")
    model_path = hf_hub_download(repo_id=HF_REPO_ID, filename=HF_MODEL_FILE)
    model = YOLOv10(model_path)

    layout_data: dict = {}
    total_detected = 0

    for i, page_path in enumerate(pages, 1):
        print(f"Detecting layout: page {i}/{len(pages)} ({page_path.name})")
        results = model.predict(
            str(page_path),
            imgsz=1024,
            conf=min_confidence,
            device="cpu",
            verbose=False,
        )

        page_name = page_path.name
        img = Image.open(page_path)
        page_width, page_height = img.size
        page_area = page_width * page_height
        min_area_px = page_area * min_area

        regions: list[dict] = []
        type_counters: dict[str, int] = {}

        for r in results:
            for box in r.boxes:
                cls_name = r.names[int(box.cls[0])]
                if cls_name not in TARGET_LABELS:
                    continue

                bbox = [int(v) for v in box.xyxy[0].tolist()]
                area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
                if area < min_area_px:
                    continue  # Filter out small regions (noise)

                conf = float(box.conf[0])
                fig_type = LABEL_TYPE_MAP[cls_name]
                type_counters[fig_type] = type_counters.get(fig_type, 0) + 1
                count = type_counters[fig_type]

                type_suffix = fig_type.lower()
                crop_name = f"{page_path.stem}_{type_suffix}{count}.png"
                crop_path = fig_dir / crop_name

                cropped = img.crop(bbox)
                cropped.save(crop_path)

                regions.append(
                    {
                        "type": fig_type,
                        "label": cls_name,
                        "bbox": bbox,
                        "confidence": round(conf, 3),
                        "cropped_path": f"figures/{crop_name}",
                    }
                )

        # Save visualization with bounding boxes
        if regions:
            layout_data[page_name] = {
                "regions": regions,
                "page_size": [page_width, page_height],
            }
            total_detected += len(regions)

            # Draw boxes and save to layouts/
            viz_img = draw_layout_boxes(img, regions)
            viz_path = lay_dir / page_name
            viz_img.save(viz_path)
        else:
            # Save original image without boxes for pages with no detections
            img.save(lay_dir / page_name)

    layout_path = out / "layout.json"
    layout_path.write_text(
        json.dumps(layout_data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    pages_with_figures = len(layout_data)
    print(f"Detection complete: {total_detected} elements in {pages_with_figures} pages")
    print(f"  Layout: {layout_path}")
    print(f"  Figures: {fig_dir}")
    print(f"  Layouts: {lay_dir}")
    return layout_data


def load_layout(output_dir: str) -> dict:
    """Load layout.json from output directory.

    Args:
        output_dir: Directory containing layout.json.

    Returns:
        Layout dict, or empty dict if not found.
    """
    layout_path = Path(output_dir) / "layout.json"
    if not layout_path.exists():
        return {}
    return json.loads(layout_path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Detect figures in page images")
    parser.add_argument("page_dir", help="Directory with page images")
    parser.add_argument("-o", "--output", default="output", help="Output directory for layout.json")
    parser.add_argument("--min-confidence", type=float, default=0.3, help="Min detection confidence")
    args = parser.parse_args()

    detect_figures(args.page_dir, args.output, min_confidence=args.min_confidence)
