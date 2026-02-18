"""Ensemble OCR: Combine multiple OCR engines for improved accuracy.

This module runs multiple OCR engines and merges results using voting
to achieve higher accuracy than any single engine alone.

Supported engines:
- Yomitoku (Japanese-specialized Document AI)
- Tesseract (traditional, system install required)
- EasyOCR (neural network-based, pip install)
- PaddleOCR (neural network-based)

Output files:
- ocr_texts/{page}.txt           - Final merged result
- ocr_texts/{page}_yomitoku.txt  - Yomitoku result
- ocr_texts/{page}_tesseract.txt - Tesseract result
- ocr_texts/{page}_easyocr.txt   - EasyOCR result
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

# Re-export public API
from .engines import (
    ocr_easyocr,
    ocr_paddleocr,
    ocr_paddleocr_with_boxes,
    ocr_tesseract,
    ocr_yomitoku_engine,
)
from .models import EngineResult, EnsembleResult, TextWithBox
from .voting import (
    bbox_contains,
    bbox_iou,
    calculate_similarity,
    calculate_similarity_matrix,
    create_text_mask,
    is_garbage,
    merge_by_voting,
    vote_best_result,
)

__all__ = [
    "EngineResult",
    "EnsembleResult",
    "TextWithBox",
    "ocr_tesseract",
    "ocr_easyocr",
    "ocr_paddleocr",
    "ocr_yomitoku_engine",
    "ocr_paddleocr_with_boxes",
    "is_garbage",
    "bbox_iou",
    "bbox_contains",
    "create_text_mask",
    "calculate_similarity",
    "calculate_similarity_matrix",
    "vote_best_result",
    "merge_by_voting",
    "ocr_ensemble",
    "run_ensemble_ocr",
]


def ocr_ensemble(
    image: Image.Image | str,
    engines: list[str] | None = None,
    tesseract_lang: str = "jpn+eng",
    easyocr_langs: list[str] | None = None,
    paddleocr_lang: str = "japan",
    device: str = "cpu",
    similarity_threshold: float = 0.7,
) -> EnsembleResult:
    """Run ensemble OCR with multiple engines.

    Args:
        image: PIL Image or path to image file.
        engines: List of engines to use. Default: ["yomitoku", "paddleocr", "tesseract"]
        tesseract_lang: Tesseract language code(s).
        easyocr_langs: EasyOCR language list.
        paddleocr_lang: PaddleOCR language code.
        device: Device for Yomitoku ("cpu" or "cuda").
        similarity_threshold: Threshold for voting agreement.

    Returns:
        EnsembleResult with merged and individual results.
    """
    if isinstance(image, str):
        image = Image.open(image)

    if engines is None:
        engines = ["yomitoku", "paddleocr", "tesseract"]

    results: dict[str, str] = {}

    # Run each engine
    for engine in engines:
        if engine == "yomitoku":
            result = ocr_yomitoku_engine(image, device)
        elif engine == "tesseract":
            result = ocr_tesseract(image, tesseract_lang)
        elif engine == "easyocr":
            result = ocr_easyocr(image, easyocr_langs)
        elif engine == "paddleocr":
            result = ocr_paddleocr(image, paddleocr_lang)
        else:
            continue

        if result.success:
            results[engine] = result.text
        else:
            print(f"    {engine} failed: {result.error}")
            results[engine] = ""

    # Merge by voting
    return merge_by_voting(results, similarity_threshold)


def run_ensemble_ocr(
    pages_dir: str,
    output_dir: str,
    engines: list[str] | None = None,
    tesseract_lang: str = "jpn+eng",
    easyocr_langs: list[str] | None = None,
    device: str = "cpu",
) -> list[tuple[str, EnsembleResult]]:
    """Run ensemble OCR on all pages in a directory.

    Args:
        pages_dir: Directory containing page images.
        output_dir: Directory for output text files.
        engines: List of engines to use.
        tesseract_lang: Tesseract language code(s).
        easyocr_langs: EasyOCR language list.
        device: Device for Yomitoku ("cpu" or "cuda").

    Returns:
        List of (page_name, EnsembleResult) tuples.
    """
    if engines is None:
        engines = ["yomitoku", "paddleocr", "tesseract"]

    pages_path = Path(pages_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    pages = sorted(pages_path.glob("*.png"))
    all_results: list[tuple[str, EnsembleResult]] = []

    print(f"Running ensemble OCR ({', '.join(engines)}) on {len(pages)} pages...")

    for page_path in pages:
        page_name = page_path.name
        page_stem = page_path.stem
        print(f"  Processing {page_name}...")

        with Image.open(page_path) as img:
            result = ocr_ensemble(
                img,
                engines=engines,
                tesseract_lang=tesseract_lang,
                easyocr_langs=easyocr_langs,
                device=device,
            )

        # Report
        vote_str = ", ".join(f"{e}:{v}" for e, v in result.votes.items()) if result.votes else "N/A"
        print(f"    Winner: {result.source}, Votes: [{vote_str}]")

        # Write individual engine results
        for engine, text in result.results.items():
            engine_file = output_path / f"{page_stem}_{engine}.txt"
            engine_file.write_text(text, encoding="utf-8")

        # Write merged result
        merged_file = output_path / f"{page_stem}.txt"
        merged_file.write_text(result.merged, encoding="utf-8")

        file_list = ", ".join(f"{page_stem}_{e}.txt" for e in engines)
        print(f"    → Saved: {page_stem}.txt, {file_list}")

        all_results.append((page_name, result))

    # Write combined output
    combined_path = output_path.parent / "book_ensemble.txt"
    with open(combined_path, "w", encoding="utf-8") as f:
        for page_name, result in all_results:
            vote_str = ", ".join(f"{e}:{v}" for e, v in result.votes.items())
            f.write(f"\n--- Page: {page_name} (winner: {result.source}, votes: [{vote_str}]) ---\n\n")
            f.write(result.merged)
            f.write("\n\n")

    print(f"\nEnsemble OCR complete. Output: {combined_path}")
    return all_results


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Ensemble OCR (Yomitoku + PaddleOCR + Tesseract + EasyOCR)")
    parser.add_argument("pages_dir", help="Directory containing page images")
    parser.add_argument("-o", "--output", default="ocr_texts", help="Output directory")
    parser.add_argument(
        "--engines",
        default="yomitoku,paddleocr,tesseract",
        help="Comma-separated list of engines (default: yomitoku,paddleocr,tesseract)",
    )
    parser.add_argument(
        "--device",
        default="cpu",
        choices=["cpu", "cuda"],
        help="Device for Yomitoku OCR (default: cpu)",
    )
    parser.add_argument("--tesseract-lang", default="jpn+eng", help="Tesseract language code(s)")
    parser.add_argument("--easyocr-langs", default="ja,en", help="EasyOCR languages (comma-separated)")
    args = parser.parse_args()

    engines = [e.strip() for e in args.engines.split(",")]
    easyocr_langs = [lang.strip() for lang in args.easyocr_langs.split(",")]

    run_ensemble_ocr(
        pages_dir=args.pages_dir,
        output_dir=args.output,
        engines=engines,
        tesseract_lang=args.tesseract_lang,
        easyocr_langs=easyocr_langs,
        device=args.device,
    )


if __name__ == "__main__":
    main()
