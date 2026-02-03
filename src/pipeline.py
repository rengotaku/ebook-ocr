"""Main pipeline: video → hash → frames → deduplicate → preprocess → detect → OCR → text."""

import argparse
import sys
import time
from pathlib import Path

from video_hash import compute_full_hash, write_source_info
from extract_frames import extract_frames
from deduplicate import deduplicate_frames
from preprocess import preprocess_pages
from detect_figures import detect_figures
from ocr import ocr_pages


def run_pipeline(
    video_path: str,
    output_base: str = "output",
    interval: float = 2.0,
    hash_threshold: int = 8,
    engine: str = "tesseract",
    languages: list[str] | None = None,
    gpu: bool = True,
    skip_ocr: bool = False,
) -> None:
    """Run the full video-to-text pipeline.

    Args:
        video_path: Path to input video file.
        output_base: Base output directory. Actual output goes to output_base/<hash>/.
        interval: Frame extraction interval in seconds.
        hash_threshold: Perceptual hash threshold for dedup.
        engine: OCR engine - "tesseract" or "easyocr".
        languages: OCR language codes.
        gpu: Use GPU for OCR.
        skip_ocr: If True, stop after frame extraction + dedup.
    """
    if not Path(video_path).exists():
        print(f"Error: Video file not found: {video_path}", file=sys.stderr)
        sys.exit(1)

    start = time.time()

    # Step 0: Compute hash and determine output directory
    print("=" * 60)
    print("Step 0: Computing video hash")
    print("=" * 60)
    full_hash = compute_full_hash(video_path)
    hash_prefix = full_hash[:16]
    print(f"SHA-256: {full_hash}")
    print(f"Prefix:  {hash_prefix}")

    out = Path(output_base) / hash_prefix
    frames_dir = str(out / "frames")
    pages_dir = str(out / "pages")
    preprocessed_dir = str(out / "preprocessed")
    text_file = str(out / "book.txt")

    write_source_info(str(out), video_path, full_hash)

    # Step 1: Extract frames
    print("\n" + "=" * 60)
    print("Step 1: Extracting frames from video")
    print("=" * 60)
    extract_frames(video_path, frames_dir, interval)

    # Step 2: Deduplicate
    print("\n" + "=" * 60)
    print("Step 2: Removing duplicate/transition frames")
    print("=" * 60)
    unique_pages = deduplicate_frames(frames_dir, pages_dir, hash_threshold)

    if skip_ocr:
        print(f"\nSkipping OCR. {len(unique_pages)} pages saved to {pages_dir}")
        return

    # Step 3: Preprocess
    print("\n" + "=" * 60)
    print("Step 3: Preprocessing pages (crop, contrast, sharpen)")
    print("=" * 60)
    preprocess_pages(pages_dir, preprocessed_dir)

    # Step 4: Detect figures, tables, formulas
    print("\n" + "=" * 60)
    print("Step 4: Detecting figures, tables, and formulas")
    print("=" * 60)
    layout = detect_figures(pages_dir, str(out))

    # Step 5: OCR (with figure markers)
    print("\n" + "=" * 60)
    print(f"Step 5: Running OCR ({engine}) on pages")
    print("=" * 60)
    ocr_pages(preprocessed_dir, text_file, engine, languages, gpu, layout=layout)

    elapsed = time.time() - start
    print(f"\nPipeline complete in {elapsed:.1f}s")
    print(f"  Output: {out}")
    print(f"  Pages:  {pages_dir}")
    print(f"  Text:   {text_file}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract text from e-book screen recording video",
    )
    parser.add_argument("video", help="Input video file path")
    parser.add_argument("-o", "--output", default="output", help="Base output directory (default: output)")
    parser.add_argument("-i", "--interval", type=float, default=2.0, help="Frame interval in seconds (default: 2.0)")
    parser.add_argument("-t", "--threshold", type=int, default=8, help="Dedup hash threshold (default: 8)")
    parser.add_argument("-e", "--engine", choices=["tesseract", "easyocr"], default="tesseract", help="OCR engine (default: tesseract)")
    parser.add_argument("--lang", nargs="+", default=None, help="OCR languages")
    parser.add_argument("--no-gpu", action="store_true", help="Disable GPU for OCR")
    parser.add_argument("--skip-ocr", action="store_true", help="Stop after frame extraction (skip OCR)")
    args = parser.parse_args()

    run_pipeline(
        video_path=args.video,
        output_base=args.output,
        interval=args.interval,
        hash_threshold=args.threshold,
        engine=args.engine,
        languages=args.lang,
        gpu=not args.no_gpu,
        skip_ocr=args.skip_ocr,
    )


if __name__ == "__main__":
    main()
