#!/usr/bin/env python3
"""Analyze PaddleOCR confidence distribution using legacy API."""

import logging
import os
import sys
from pathlib import Path

os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

# Suppress verbose logging
logging.getLogger("ppocr").setLevel(logging.WARNING)

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from difflib import SequenceMatcher  # noqa: E402

import numpy as np  # noqa: E402
from PIL import Image  # noqa: E402


def text_similarity(t1: str, t2: str) -> float:
    if not t1 or not t2:
        return 0.0
    return SequenceMatcher(None, t1, t2).ratio()


def main():
    image_path = "output/157012a97dcbebed/pages/page_0024.png"
    golden_path = "specs/008-rover-redesign/golden/page_0024_golden.txt"

    # Load golden
    with open(golden_path, "r", encoding="utf-8") as f:
        golden_lines = f.readlines()
    golden_text = "".join(line for line in golden_lines if not line.startswith("#")).strip()

    print("Loading image...")
    image = Image.open(image_path)
    np.array(image)

    print("Running PaddleOCR (legacy mode)...")

    # Try using the engine wrapper from src
    try:
        from ocr_engines import run_paddleocr_with_boxes

        result = run_paddleocr_with_boxes(image, lang="japan")

        print("\n" + "=" * 60)
        print("PaddleOCR Results (via ocr_engines)")
        print("=" * 60)

        if result.success:
            all_scores = [item.confidence for item in result.items]
            all_texts = [item.text for item in result.items]

            print(f"\nTotal items: {len(all_texts)}")

            if all_scores:
                print("\nConfidence Statistics:")
                print(f"  Min:    {min(all_scores):.4f}")
                print(f"  Max:    {max(all_scores):.4f}")
                print(f"  Mean:   {np.mean(all_scores):.4f}")
                print(f"  Std:    {np.std(all_scores):.4f}")
                print(f"  Median: {np.median(all_scores):.4f}")

                # Distribution
                print("\nConfidence Distribution:")
                buckets = [0, 0.3, 0.5, 0.7, 0.9, 1.0]
                for i in range(len(buckets) - 1):
                    count = sum(1 for s in all_scores if buckets[i] <= s < buckets[i + 1])
                    pct = count / len(all_scores) * 100
                    bar = "█" * int(pct / 2)
                    print(f"  [{buckets[i]:.1f}-{buckets[i + 1]:.1f}): {count:3d} ({pct:5.1f}%) {bar}")

                # Item-level analysis
                print("\nItem-level analysis (top 20 by confidence):")
                print(f"{'Score':>8} | {'Len':>4} | {'Match':>6} | Text")
                print("-" * 70)

                items = list(zip(all_texts, all_scores))
                items.sort(key=lambda x: -x[1])

                for text, score in items[:20]:
                    # Find best match in golden
                    best_match = 0.0
                    for start in range(len(golden_text)):
                        for end in range(
                            start + max(1, len(text) - 3), min(start + len(text) + 5, len(golden_text) + 1)
                        ):
                            if end > start:
                                sim = text_similarity(text, golden_text[start:end])
                                best_match = max(best_match, sim)

                    marker = "✓" if best_match >= 0.5 else "✗"
                    print(f"{score:8.4f} | {len(text):4d} | {best_match:5.2f}{marker} | {text[:40]}")

                # Summary
                print("\n" + "=" * 60)
                print("COMPARISON WITH OTHER ENGINES")
                print("=" * 60)
                print(f"\n{'Engine':<12} | {'Min':>6} | {'Max':>6} | {'Mean':>6} | {'Recommended Range'}")
                print("-" * 65)
                print(f"{'yomitoku':<12} | {'0.41':>6} | {'1.00':>6} | {'0.96':>6} | (0.4, 1.0)")
                print(
                    f"{'paddleocr':<12} | {min(all_scores):6.2f} | {max(all_scores):6.2f} | "
                    f"{np.mean(all_scores):6.2f} | ({min(all_scores):.2f}, {max(all_scores):.2f})"
                )
                print(f"{'easyocr':<12} | {'0.26':>6} | {'1.00':>6} | {'0.80':>6} | (0.25, 1.0)")
        else:
            print(f"Error: {result.error}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
