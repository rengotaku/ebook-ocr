"""V3 pipeline: video → frames → dedup → detect → DeepSeek-OCR → VLM figure description.

No preprocessing step needed - DeepSeek-OCR handles raw page images directly.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

from src.video_hash import compute_full_hash, write_source_info
from src.extract_frames import extract_frames
from src.deduplicate import deduplicate_frames
from src.detect_figures import detect_figures
from src.ocr_deepseek import ocr_pages_deepseek
from src.describe_figures import describe_figures


def run_pipeline(
    video_path: str,
    output_base: str = "output",
    interval: float = 2.0,
    hash_threshold: int = 8,
    ocr_model: str = "deepseek-ocr",
    vlm_model: str = "gemma3:12b",
    ollama_url: str = "http://localhost:11434",
    ocr_timeout: int = 60,
    vlm_timeout: int = 120,
    skip_ocr: bool = False,
    min_confidence: float = 0.7,
) -> None:
    """Run the full video-to-markdown pipeline (v3).

    Steps 0-2 are shared with v1/v2. Step 3 detects figures.
    Step 4 uses DeepSeek-OCR (no preprocessing needed).
    Step 5 uses VLM to describe detected figures.

    Args:
        video_path: Path to input video file.
        output_base: Base output directory.
        interval: Frame extraction interval in seconds.
        hash_threshold: Perceptual hash threshold for dedup.
        ocr_model: Ollama model for OCR (default: deepseek-ocr).
        vlm_model: Ollama vision model for figure description.
        ollama_url: Ollama API base URL.
        ocr_timeout: Per-page OCR timeout in seconds.
        vlm_timeout: Per-figure VLM timeout in seconds.
        skip_ocr: If True, stop after frame extraction + dedup.
        min_confidence: Minimum confidence for figure detection.
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
    figures_dir = str(out / "figures")
    text_file = str(out / "book.txt")
    md_file = str(out / "book.md")

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

    # Step 3: Detect figures, tables, formulas
    print("\n" + "=" * 60)
    print("Step 3: Detecting figures, tables, and formulas")
    print("=" * 60)
    layout = detect_figures(pages_dir, str(out))

    # Step 4: DeepSeek-OCR on raw pages (no preprocessing needed)
    print("\n" + "=" * 60)
    print(f"Step 4: Running DeepSeek-OCR ({ocr_model})")
    print("=" * 60)
    ocr_pages_deepseek(
        pages_dir=pages_dir,
        output_file=text_file,
        layout=layout,
        model=ocr_model,
        base_url=ollama_url,
        timeout=ocr_timeout,
        min_confidence=min_confidence,
    )

    # Step 5: Describe figures with VLM
    print("\n" + "=" * 60)
    print(f"Step 5: Describing figures with VLM ({vlm_model})")
    print("=" * 60)
    describe_figures(
        text_file=text_file,
        output_file=md_file,
        figures_dir=figures_dir,
        layout=layout,
        model=vlm_model,
        base_url=ollama_url,
        timeout=vlm_timeout,
        min_confidence=min_confidence,
    )

    elapsed = time.time() - start
    print(f"\nPipeline complete in {elapsed:.1f}s")
    print(f"  Output: {out}")
    print(f"  Pages:  {pages_dir}")
    print(f"  OCR:    {text_file}")
    print(f"  Final:  {md_file}")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Extract text from e-book screen recording (v3 - DeepSeek-OCR + VLM figures)",
    )
    parser.add_argument("video", help="Input video file path")
    parser.add_argument("-o", "--output", default="output", help="Base output directory (default: output)")
    parser.add_argument("-i", "--interval", type=float, default=2.0, help="Frame interval in seconds (default: 2.0)")
    parser.add_argument("-t", "--threshold", type=int, default=8, help="Dedup hash threshold (default: 8)")
    parser.add_argument("--ocr-model", default="deepseek-ocr", help="Ollama OCR model (default: deepseek-ocr)")
    parser.add_argument("--vlm-model", default="gemma3:12b", help="Ollama VLM for figures (default: gemma3:12b)")
    parser.add_argument("--ollama-url", default="http://localhost:11434", help="Ollama API URL")
    parser.add_argument("--ocr-timeout", type=int, default=60, help="Per-page OCR timeout (default: 60)")
    parser.add_argument("--vlm-timeout", type=int, default=120, help="Per-figure VLM timeout (default: 120)")
    parser.add_argument("--skip-ocr", action="store_true", help="Stop after frame extraction (skip OCR)")
    parser.add_argument("--min-confidence", type=float, default=0.7, help="Figure confidence threshold (default: 0.7)")
    args = parser.parse_args()

    run_pipeline(
        video_path=args.video,
        output_base=args.output,
        interval=args.interval,
        hash_threshold=args.threshold,
        ocr_model=args.ocr_model,
        vlm_model=args.vlm_model,
        ollama_url=args.ollama_url,
        ocr_timeout=args.ocr_timeout,
        vlm_timeout=args.vlm_timeout,
        skip_ocr=args.skip_ocr,
        min_confidence=args.min_confidence,
    )


if __name__ == "__main__":
    main()
