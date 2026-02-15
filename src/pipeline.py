"""V5 pipeline: video → frames → dedup → Yomitoku layout + ROVER multi-engine OCR.

Yomitoku handles layout detection.
ROVER combines multiple OCR engines (Yomitoku, PaddleOCR, EasyOCR) for improved accuracy.
"""

from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

import yaml

from src.video_hash import compute_full_hash, write_source_info
from src.extract_frames import extract_frames
from src.deduplicate import deduplicate_frames
from src.split_spread import split_spread_pages, renumber_pages
from src.ocr_yomitoku import detect_layout_yomitoku
from src.ocr_rover import run_rover_batch
from src.consolidate import consolidate_rover_output


def run_pipeline(
    video_path: str,
    output_base: str = "output",
    interval: float = 1.5,
    hash_threshold: int = 8,
    yomitoku_device: str = "cpu",
    ocr_timeout: int = 60,
    skip_ocr: bool = False,
    split_spreads: bool = True,
    spread_aspect_ratio: float = 1.2,
    spread_left_trim: float = 0.0,
    spread_right_trim: float = 0.0,
) -> None:
    """Run the full video-to-markdown pipeline (v5 with ROVER OCR).

    Steps 0-2 are shared with v1/v2. Step 2.5 splits spreads into pages.
    Step 3 uses Yomitoku for layout detection.
    Step 4 uses ROVER multi-engine OCR (Yomitoku + PaddleOCR + EasyOCR).
    Step 5 consolidates OCR results into book.txt and book.md.

    Args:
        video_path: Path to input video file.
        output_base: Base output directory.
        interval: Frame extraction interval in seconds.
        hash_threshold: Perceptual hash threshold for dedup.
        yomitoku_device: Device for Yomitoku OCR ("cpu" or "cuda").
        ocr_timeout: Per-page OCR timeout in seconds.
        skip_ocr: If True, stop after frame extraction + dedup.
        split_spreads: If True, split spread images into left/right pages.
        spread_aspect_ratio: Aspect ratio threshold for spread detection (default: 1.2).
        spread_left_trim: Percentage to trim from left edge of left page (default: 0.0).
        spread_right_trim: Percentage to trim from right edge of right page (default: 0.0).
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

    # Step 2.5: Split spreads (見開き分割)
    if split_spreads:
        print("\n" + "=" * 60)
        print("Step 2.5: Splitting spread images into separate pages")
        print("=" * 60)
        split_spread_pages(
            pages_dir,
            aspect_ratio_threshold=spread_aspect_ratio,
            left_trim_pct=spread_left_trim,
            right_trim_pct=spread_right_trim,
        )
        renumber_pages(pages_dir)

    # Step 3+4: Layout detection and ROVER multi-engine OCR
    print("\n" + "=" * 60)
    print(f"Step 3+4: Layout detection and ROVER OCR (device={yomitoku_device})")
    print("=" * 60)

    # Detect layout and create visualizations
    detect_layout_yomitoku(
        pages_dir=pages_dir,
        output_dir=str(out),
        device=yomitoku_device,
    )

    # Run ROVER multi-engine OCR
    ocr_output_dir = str(out / "ocr_output")
    run_rover_batch(
        pages_dir=pages_dir,
        output_dir=ocr_output_dir,
        yomitoku_device=yomitoku_device,
    )

    # Step 5: Consolidate OCR results
    print("\n" + "=" * 60)
    print("Step 5: Consolidating OCR results")
    print("=" * 60)
    text_file, md_file = consolidate_rover_output(str(out))

    elapsed = time.time() - start
    print(f"\nPipeline complete in {elapsed:.1f}s")
    print(f"  Output: {out}")
    print(f"  Pages:  {pages_dir}")
    print(f"  OCR:    {text_file}")
    print(f"  Final:  {md_file}")


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file, returning empty dict if not found."""
    path = Path(config_path)
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def main() -> None:
    cfg = load_config()

    parser = argparse.ArgumentParser(
        description="Extract text from e-book screen recording (v5 - ROVER multi-engine OCR)",
    )
    parser.add_argument("video", help="Input video file path")
    parser.add_argument("-o", "--output", default=cfg.get("output", "output"), help="Base output directory")
    parser.add_argument("-i", "--interval", type=float, default=cfg.get("interval", 1.5), help="Frame interval in seconds")
    parser.add_argument("-t", "--threshold", type=int, default=cfg.get("threshold", 8), help="Dedup hash threshold")
    parser.add_argument("--device", default=cfg.get("yomitoku_device", "cpu"), choices=["cpu", "cuda"], help="Yomitoku device")
    parser.add_argument("--ocr-timeout", type=int, default=cfg.get("ocr_timeout", 60), help="Per-page OCR timeout")
    parser.add_argument("--skip-ocr", action="store_true", help="Stop after frame extraction (skip OCR)")
    parser.add_argument("--no-split-spreads", action="store_true", help="Disable spread splitting (見開き分割)")
    parser.add_argument("--spread-aspect-ratio", type=float, default=cfg.get("spread_aspect_ratio", 1.2), help="Aspect ratio threshold for spread detection")
    parser.add_argument("--spread-left-trim", type=float, default=cfg.get("spread_left_trim", 0.0), help="Trim %% from left edge of left page (e.g., 0.03 = 3%%)")
    parser.add_argument("--spread-right-trim", type=float, default=cfg.get("spread_right_trim", 0.0), help="Trim %% from right edge of right page (e.g., 0.03 = 3%%)")
    args = parser.parse_args()

    run_pipeline(
        video_path=args.video,
        output_base=args.output,
        interval=args.interval,
        hash_threshold=args.threshold,
        yomitoku_device=args.device,
        ocr_timeout=args.ocr_timeout,
        skip_ocr=args.skip_ocr,
        split_spreads=not args.no_split_spreads,
        spread_aspect_ratio=args.spread_aspect_ratio,
        spread_left_trim=args.spread_left_trim,
        spread_right_trim=args.spread_right_trim,
    )


if __name__ == "__main__":
    main()
