"""Detect figures, tables, and formulas in page images using DocLayout-YOLO."""

import json
from pathlib import Path

from PIL import Image

# DocLayout-YOLO class name → output TYPE mapping
LABEL_TYPE_MAP = {
    "table": "TABLE",
    "figure": "FIGURE",
    "isolated formula": "FORMULA",
}

# Labels we care about (skip plain text, title, abandon, captions, etc.)
TARGET_LABELS = set(LABEL_TYPE_MAP.keys())

# HuggingFace model info
HF_REPO_ID = "juliozhao/DocLayout-YOLO-DocStructBench"
HF_MODEL_FILE = "doclayout_yolo_docstructbench_imgsz1024.pt"


def detect_figures(
    page_dir: str,
    output_dir: str,
    figures_dir: str | None = None,
    min_confidence: float = 0.3,
) -> dict:
    """Detect figures, tables, and formulas in page images.

    Args:
        page_dir: Directory containing page images (preprocessed or raw).
        output_dir: Directory to save layout.json.
        figures_dir: Directory to save cropped figure images.
            Defaults to output_dir/figures.
        min_confidence: Minimum confidence threshold for detection.

    Returns:
        Layout dict mapping page filenames to detected elements.
    """
    from doclayout_yolo import YOLOv10
    from huggingface_hub import hf_hub_download

    src = Path(page_dir)
    out = Path(output_dir)
    fig_dir = Path(figures_dir) if figures_dir else out / "figures"
    fig_dir.mkdir(parents=True, exist_ok=True)

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
            str(page_path), imgsz=1024, conf=min_confidence, device="cpu", verbose=False,
        )

        page_name = page_path.name
        img = Image.open(page_path)
        figures: list[dict] = []
        type_counters: dict[str, int] = {}

        for r in results:
            for box in r.boxes:
                cls_name = r.names[int(box.cls[0])]
                if cls_name not in TARGET_LABELS:
                    continue

                conf = float(box.conf[0])
                fig_type = LABEL_TYPE_MAP[cls_name]
                type_counters[fig_type] = type_counters.get(fig_type, 0) + 1
                count = type_counters[fig_type]

                bbox = [int(v) for v in box.xyxy[0].tolist()]
                type_suffix = fig_type.lower()
                crop_name = f"{page_path.stem}_{type_suffix}{count}.png"
                crop_path = fig_dir / crop_name

                cropped = img.crop(bbox)
                cropped.save(crop_path)

                figures.append({
                    "type": fig_type,
                    "label": cls_name,
                    "bbox": bbox,
                    "confidence": round(conf, 3),
                    "cropped_path": f"figures/{crop_name}",
                })

        if figures:
            layout_data[page_name] = {"figures": figures}
            total_detected += len(figures)

    layout_path = out / "layout.json"
    layout_path.write_text(
        json.dumps(layout_data, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    pages_with_figures = len(layout_data)
    print(f"Detection complete: {total_detected} elements in {pages_with_figures} pages")
    print(f"  Layout: {layout_path}")
    print(f"  Figures: {fig_dir}")
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
