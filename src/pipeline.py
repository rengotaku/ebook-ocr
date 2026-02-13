"""V3 pipeline: video → frames → dedup → detect → Yomitoku OCR → VLM figure description.

No preprocessing step needed - Yomitoku handles raw page images directly.
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
from src.detect_figures import detect_figures
from src.layout_ocr import run_layout_ocr
from src.describe_figures import describe_figures


def run_pipeline(
    video_path: str,
    output_base: str = "output",
    interval: float = 1.5,
    hash_threshold: int = 8,
    yomitoku_device: str = "cpu",
    vlm_model: str = "gemma3:12b",
    ollama_url: str = "http://localhost:11434",
    ocr_timeout: int = 60,
    vlm_timeout: int = 120,
    skip_ocr: bool = False,
    min_confidence: float = 0.7,
    coverage_threshold: float = 0.3,
    min_region_area: float = 0.01,
    split_spreads: bool = True,
    spread_aspect_ratio: float = 1.2,
    spread_left_trim: float = 0.0,
    spread_right_trim: float = 0.0,
    vlm_options: dict | None = None,
) -> None:
    """Run the full video-to-markdown pipeline (v3 with layout-aware OCR).

    Steps 0-2 are shared with v1/v2. Step 2.5 splits spreads into pages.
    Step 3 detects layout regions.
    Step 4 uses layout-aware OCR (region-based processing with fallback).
    Step 5 uses VLM to describe detected figures.

    Args:
        video_path: Path to input video file.
        output_base: Base output directory.
        interval: Frame extraction interval in seconds.
        hash_threshold: Perceptual hash threshold for dedup.
        yomitoku_device: Device for Yomitoku OCR ("cpu" or "cuda").
        vlm_model: Ollama vision model for figure description.
        ollama_url: Ollama API base URL.
        ocr_timeout: Per-page OCR timeout in seconds.
        vlm_timeout: Per-figure VLM timeout in seconds.
        skip_ocr: If True, stop after frame extraction + dedup.
        min_confidence: Minimum confidence for figure detection.
        coverage_threshold: Fallback threshold for low coverage (default: 0.3).
        min_region_area: Minimum region area ratio (default: 0.01).
        split_spreads: If True, split spread images into left/right pages.
        spread_aspect_ratio: Aspect ratio threshold for spread detection (default: 1.2).
        spread_left_trim: Percentage to trim from left edge of left page (default: 0.0).
        spread_right_trim: Percentage to trim from right edge of right page (default: 0.0).
        vlm_options: Ollama generation options for VLM model.
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

    # Step 3: Detect layout regions (extended - all 10 classes)
    print("\n" + "=" * 60)
    print("Step 3: Detecting layout regions (title, text, figure, table, etc.)")
    print("=" * 60)
    layout = detect_figures(pages_dir, str(out), min_confidence=min_confidence)

    # Step 4: Layout-aware OCR (region-based processing)
    print("\n" + "=" * 60)
    print(f"Step 4: Running layout-aware OCR (Yomitoku, device={yomitoku_device})")
    print("=" * 60)

    run_layout_ocr(
        pages_dir=pages_dir,
        layout_data=layout,
        output_file=text_file,
        base_url=ollama_url,
        timeout=ocr_timeout,
        yomitoku_device=yomitoku_device,
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
        options=vlm_options,
    )

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
        description="Extract text from e-book screen recording (v3 - Yomitoku OCR + VLM figures)",
    )
    parser.add_argument("video", help="Input video file path")
    parser.add_argument("-o", "--output", default=cfg.get("output", "output"), help="Base output directory")
    parser.add_argument("-i", "--interval", type=float, default=cfg.get("interval", 1.5), help="Frame interval in seconds")
    parser.add_argument("-t", "--threshold", type=int, default=cfg.get("threshold", 8), help="Dedup hash threshold")
    parser.add_argument("--device", default=cfg.get("yomitoku_device", "cpu"), choices=["cpu", "cuda"], help="Yomitoku device")
    parser.add_argument("--vlm-model", default=cfg.get("vlm_model", "gemma3:12b"), help="Ollama VLM for figures")
    parser.add_argument("--ollama-url", default=cfg.get("ollama_url", "http://localhost:11434"), help="Ollama API URL")
    parser.add_argument("--ocr-timeout", type=int, default=cfg.get("ocr_timeout", 60), help="Per-page OCR timeout")
    parser.add_argument("--vlm-timeout", type=int, default=cfg.get("vlm_timeout", 120), help="Per-figure VLM timeout")
    parser.add_argument("--skip-ocr", action="store_true", help="Stop after frame extraction (skip OCR)")
    parser.add_argument("--min-confidence", type=float, default=cfg.get("min_confidence", 0.7), help="Figure confidence threshold")
    parser.add_argument("--coverage-threshold", type=float, default=cfg.get("coverage_threshold", 0.3), help="Fallback threshold for low coverage")
    parser.add_argument("--min-region-area", type=float, default=cfg.get("min_region_area", 0.01), help="Minimum region area ratio")
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
        vlm_model=args.vlm_model,
        ollama_url=args.ollama_url,
        ocr_timeout=args.ocr_timeout,
        vlm_timeout=args.vlm_timeout,
        skip_ocr=args.skip_ocr,
        min_confidence=args.min_confidence,
        coverage_threshold=args.coverage_threshold,
        min_region_area=args.min_region_area,
        split_spreads=not args.no_split_spreads,
        spread_aspect_ratio=args.spread_aspect_ratio,
        spread_left_trim=args.spread_left_trim,
        spread_right_trim=args.spread_right_trim,
        vlm_options=cfg.get("vlm_options"),
    )


if __name__ == "__main__":
    main()
