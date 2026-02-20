"""Integrated OCR: Full-page OCR with layout-based structuring.

This module implements the integrated OCR approach:
1. Run multiple OCR engines on full page (Yomitoku, PaddleOCR, Tesseract, EasyOCR)
2. Quality check and engine selection
3. Structure output using layout region information

Strategy:
- Full page OCR for maximum information capture
- Layout info for Markdown structuring (not region-level OCR)
- Yomitoku for TEXT (Japanese-specialized), PaddleOCR/Tesseract as fallback
- EasyOCR for FIGURE regions (better at embedded text)
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

from src.ocr_ensemble import (
    TextWithBox,
    is_garbage,
    ocr_easyocr,
    ocr_paddleocr_with_boxes,
    ocr_tesseract,
    ocr_yomitoku_engine,
)
from src.ocr_integrated_utils import (
    ENGINE_PRIORITY,
    filter_overlapping_regions,
    select_best_engine,
    structure_text_by_paragraphs,
)

# Re-export for backward compatibility
__all__ = [
    "ENGINE_PRIORITY",
    "IntegratedResult",
    "filter_overlapping_regions",
    "run_integrated_ocr",
    "run_integrated_ocr_batch",
    "select_best_engine",
    "structure_text_by_paragraphs",
]


@dataclass
class IntegratedResult:
    """Result from integrated OCR processing."""

    text: str  # Final merged text
    structured: str  # Markdown structured output
    engine_results: dict[str, str]  # engine_name -> text
    selected_engine: str  # Primary engine used
    quality_flags: dict[str, bool] = field(default_factory=dict)  # engine -> is_valid


def run_integrated_ocr(
    image: Image.Image | str,
    regions: list[dict] | None = None,
    tesseract_lang: str = "jpn+eng",
    easyocr_langs: list[str] | None = None,
    paddleocr_lang: str = "japan",
    device: str = "cpu",
) -> IntegratedResult:
    """Run integrated OCR on a single page.

    Process:
    1. Run Yomitoku, PaddleOCR, Tesseract, EasyOCR on full page
    2. Quality check all results
    3. Select best result

    Args:
        image: PIL Image or path to image file.
        regions: Layout regions for structuring output.
        tesseract_lang: Tesseract language code(s).
        easyocr_langs: EasyOCR language list.
        paddleocr_lang: PaddleOCR language code.
        device: Device for Yomitoku ("cpu" or "cuda").

    Returns:
        IntegratedResult with all engine results and selected output.
    """
    if isinstance(image, str):
        image = Image.open(image)

    results: dict[str, str] = {}
    quality_flags: dict[str, bool] = {}
    paddle_items: list[TextWithBox] = []

    # 1. Run full-page OCR engines
    print("    Running Yomitoku...", end="", flush=True)
    yomi_result = ocr_yomitoku_engine(image, device)
    if yomi_result.success:
        results["yomitoku"] = yomi_result.text
        quality_flags["yomitoku"] = not is_garbage(yomi_result.text)
        status = "OK" if quality_flags["yomitoku"] else "GARBAGE"
        print(f" {status} ({len(yomi_result.text)} chars)")
    else:
        print(f" FAIL: {yomi_result.error}")
        results["yomitoku"] = ""
        quality_flags["yomitoku"] = False

    print("    Running PaddleOCR...", end="", flush=True)
    paddle_items, paddle_success, paddle_error = ocr_paddleocr_with_boxes(image, paddleocr_lang)
    if paddle_success:
        paddle_text = "\n".join(item.text for item in paddle_items)
        results["paddleocr"] = paddle_text
        quality_flags["paddleocr"] = not is_garbage(paddle_text)
        print(f" OK ({len(paddle_text)} chars, {len(paddle_items)} boxes)")
    else:
        print(f" FAIL: {paddle_error}")
        results["paddleocr"] = ""
        quality_flags["paddleocr"] = False

    print("    Running Tesseract...", end="", flush=True)
    tess_result = ocr_tesseract(image, tesseract_lang)
    if tess_result.success:
        results["tesseract"] = tess_result.text
        quality_flags["tesseract"] = not is_garbage(tess_result.text)
        print(f" OK ({len(tess_result.text)} chars)")
    else:
        print(f" FAIL: {tess_result.error}")
        results["tesseract"] = ""
        quality_flags["tesseract"] = False

    print("    Running EasyOCR...", end="", flush=True)
    easy_result = ocr_easyocr(image, easyocr_langs)
    if easy_result.success:
        results["easyocr"] = easy_result.text
        quality_flags["easyocr"] = not is_garbage(easy_result.text)
        print(f" OK ({len(easy_result.text)} chars)")
    else:
        print(f" FAIL: {easy_result.error}")
        results["easyocr"] = ""
        quality_flags["easyocr"] = False

    # 2. Determine dominant region type
    dominant_type = "TEXT"
    if regions:
        type_counts: dict[str, int] = {}
        for r in regions:
            t = r.get("type", "TEXT")
            if t != "ABANDON":
                type_counts[t] = type_counts.get(t, 0) + 1
        if type_counts:
            dominant_type = max(type_counts.items(), key=lambda x: x[1])[0]

    # 3. Select best result
    selected_text, selected_engine = select_best_engine(results, dominant_type, quality_flags)

    # 4. Structure output by paragraphs using YOLO regions
    if regions and paddle_items:
        structured = structure_text_by_paragraphs(paddle_items, regions)
        # Count regions used
        filtered = filter_overlapping_regions(regions)
        title_count = sum(1 for r in filtered if r.get("type") == "TITLE")
        text_count = sum(1 for r in filtered if r.get("type") == "TEXT")
        print(f"    → Structured: {title_count} TITLE(s), {text_count} TEXT paragraph(s)")
    else:
        structured = selected_text

    return IntegratedResult(
        text=selected_text,
        structured=structured,
        engine_results=results,
        selected_engine=selected_engine,
        quality_flags=quality_flags,
    )


def run_integrated_ocr_batch(
    pages_dir: str,
    layout_file: str | None,
    output_dir: str,
    tesseract_lang: str = "jpn+eng",
    easyocr_langs: list[str] | None = None,
    paddleocr_lang: str = "japan",
    device: str = "cpu",
) -> list[tuple[str, IntegratedResult]]:
    """Run integrated OCR on all pages in a directory.

    Args:
        pages_dir: Directory containing page images.
        layout_file: Path to layout.json file (optional).
        output_dir: Directory for output files.
        tesseract_lang: Tesseract language code(s).
        easyocr_langs: EasyOCR language list.
        paddleocr_lang: PaddleOCR language code.
        device: Device for Yomitoku ("cpu" or "cuda").

    Returns:
        List of (page_name, IntegratedResult) tuples.
    """
    pages_path = Path(pages_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Load layout data if provided
    layout_data: dict = {}
    if layout_file and Path(layout_file).exists():
        with open(layout_file) as f:
            layout_data = json.load(f)

    pages = sorted(pages_path.glob("*.png"))
    all_results: list[tuple[str, IntegratedResult]] = []

    print(f"Running integrated OCR on {len(pages)} pages...")

    for page_path in pages:
        page_name = page_path.name
        page_stem = page_path.stem
        print(f"\n  Processing {page_name}...")

        # Get regions for this page
        page_layout = layout_data.get(page_name, {})
        regions = page_layout.get("regions", [])

        # Run OCR
        with Image.open(page_path) as img:
            result = run_integrated_ocr(
                img,
                regions=regions,
                tesseract_lang=tesseract_lang,
                easyocr_langs=easyocr_langs,
                paddleocr_lang=paddleocr_lang,
                device=device,
            )

        # Report
        valid_engines = [e for e, v in result.quality_flags.items() if v]
        print(f"    → Selected: {result.selected_engine}")
        print(f"    → Valid engines: {', '.join(valid_engines) or 'none'}")

        # Write individual engine results
        for engine, text in result.engine_results.items():
            engine_file = output_path / f"{page_stem}_{engine}.txt"
            engine_file.write_text(text, encoding="utf-8")

        # Write structured result (with TITLE as Markdown headings)
        merged_file = output_path / f"{page_stem}.txt"
        merged_file.write_text(result.structured, encoding="utf-8")

        all_results.append((page_name, result))

    # Write combined output (structured)
    combined_path = output_path.parent / "book_integrated.txt"
    with open(combined_path, "w", encoding="utf-8") as f:
        for page_name, result in all_results:
            f.write(f"\n--- Page: {page_name} (engine: {result.selected_engine}) ---\n\n")
            f.write(result.structured)
            f.write("\n\n")

    print(f"\nIntegrated OCR complete. Output: {combined_path}")
    return all_results


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Integrated OCR (Yomitoku + PaddleOCR + Tesseract + EasyOCR)")
    parser.add_argument("pages_dir", help="Directory containing page images")
    parser.add_argument("-o", "--output", default="ocr_texts", help="Output directory")
    parser.add_argument("--layout", help="Path to layout.json file (optional)")
    parser.add_argument(
        "--device",
        default="cpu",
        choices=["cpu", "cuda"],
        help="Device for Yomitoku OCR (default: cpu)",
    )
    parser.add_argument("--tesseract-lang", default="jpn+eng", help="Tesseract language code(s)")
    parser.add_argument("--easyocr-langs", default="ja,en", help="EasyOCR languages (comma-separated)")
    parser.add_argument("--paddleocr-lang", default="japan", help="PaddleOCR language code")
    args = parser.parse_args()

    easyocr_langs = [lang.strip() for lang in args.easyocr_langs.split(",")]

    run_integrated_ocr_batch(
        pages_dir=args.pages_dir,
        layout_file=args.layout,
        output_dir=args.output,
        tesseract_lang=args.tesseract_lang,
        easyocr_langs=easyocr_langs,
        paddleocr_lang=args.paddleocr_lang,
        device=args.device,
    )


if __name__ == "__main__":
    main()
