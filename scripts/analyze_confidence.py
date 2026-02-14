#!/usr/bin/env python3
"""Analyze OCR confidence distributions and compare with golden text."""

import sys
from pathlib import Path
from difflib import SequenceMatcher

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PIL import Image
import numpy as np

from ocr_engines import run_yomitoku_with_boxes, run_easyocr_with_boxes, TextWithBox


def text_similarity(t1: str, t2: str) -> float:
    """Calculate similarity ratio."""
    if not t1 or not t2:
        return 0.0
    return SequenceMatcher(None, t1, t2).ratio()


def analyze_engine_confidence(items: list[TextWithBox], golden_text: str, engine_name: str):
    """Analyze confidence distribution for an engine."""
    print(f"\n{'='*60}")
    print(f"Engine: {engine_name}")
    print(f"{'='*60}")

    if not items:
        print("No items")
        return {}

    confidences = [item.confidence for item in items]

    print(f"\nConfidence Statistics:")
    print(f"  Count: {len(confidences)}")
    print(f"  Min:   {min(confidences):.4f}")
    print(f"  Max:   {max(confidences):.4f}")
    print(f"  Mean:  {np.mean(confidences):.4f}")
    print(f"  Std:   {np.std(confidences):.4f}")
    print(f"  Median: {np.median(confidences):.4f}")

    # Distribution buckets
    buckets = [0, 0.3, 0.5, 0.7, 0.9, 1.0]
    print(f"\nConfidence Distribution:")
    for i in range(len(buckets) - 1):
        count = sum(1 for c in confidences if buckets[i] <= c < buckets[i+1])
        pct = count / len(confidences) * 100
        bar = '█' * int(pct / 2)
        print(f"  [{buckets[i]:.1f}-{buckets[i+1]:.1f}): {count:3d} ({pct:5.1f}%) {bar}")

    # Compare each item with golden
    print(f"\nItem-level analysis (confidence vs golden match):")
    print(f"{'Conf':>6} | {'Len':>4} | {'Golden Match':>12} | Text (first 40 chars)")
    print("-" * 80)

    correct_high_conf = 0  # High conf (>=0.7) and good match (>=0.5)
    correct_low_conf = 0   # Low conf (<0.7) and good match
    wrong_high_conf = 0    # High conf but bad match
    wrong_low_conf = 0     # Low conf and bad match

    for item in sorted(items, key=lambda x: -x.confidence)[:20]:  # Top 20
        # Find best match in golden
        best_match = 0.0
        text_clean = item.text.replace('\n', ' ')

        # Try to find substring match
        for start in range(len(golden_text)):
            for end in range(start + len(item.text) - 5, min(start + len(item.text) + 10, len(golden_text) + 1)):
                if end > start:
                    substr = golden_text[start:end]
                    sim = text_similarity(item.text, substr)
                    best_match = max(best_match, sim)

        # Categorize
        is_high_conf = item.confidence >= 0.7
        is_good_match = best_match >= 0.5

        if is_high_conf and is_good_match:
            correct_high_conf += 1
        elif not is_high_conf and is_good_match:
            correct_low_conf += 1
        elif is_high_conf and not is_good_match:
            wrong_high_conf += 1
        else:
            wrong_low_conf += 1

        marker = "✓" if is_good_match else "✗"
        print(f"{item.confidence:6.3f} | {len(item.text):4d} | {best_match:5.2f} {marker:>6} | {text_clean[:40]}")

    print(f"\nConfidence Reliability Analysis:")
    print(f"  High conf (>=0.7) + Good match: {correct_high_conf}")
    print(f"  High conf (>=0.7) + Bad match:  {wrong_high_conf} ← False positives")
    print(f"  Low conf (<0.7) + Good match:   {correct_low_conf} ← False negatives")
    print(f"  Low conf (<0.7) + Bad match:    {wrong_low_conf}")

    return {
        "min": min(confidences),
        "max": max(confidences),
        "mean": np.mean(confidences),
        "std": np.std(confidences),
        "correct_high": correct_high_conf,
        "wrong_high": wrong_high_conf,
    }


def main():
    image_path = "output/157012a97dcbebed/pages/page_0024.png"
    golden_path = "specs/008-rover-redesign/golden/page_0024_golden.txt"

    # Load golden
    with open(golden_path, 'r', encoding='utf-8') as f:
        golden_lines = f.readlines()
    golden_text = ''.join(line for line in golden_lines if not line.startswith('#')).strip()

    print("Golden text preview:")
    print(golden_text[:200] + "...")

    # Load image
    image = Image.open(image_path)

    # Run yomitoku
    print("\nRunning yomitoku...")
    yomitoku_result = run_yomitoku_with_boxes(image, device="cuda")
    yomi_stats = analyze_engine_confidence(yomitoku_result.items, golden_text, "yomitoku")

    # Run easyocr
    print("\nRunning easyocr...")
    easyocr_result = run_easyocr_with_boxes(image)
    easy_stats = analyze_engine_confidence(easyocr_result.items, golden_text, "easyocr")

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY: Confidence Scale Comparison")
    print("=" * 60)

    print(f"\n{'Engine':<12} | {'Min':>6} | {'Max':>6} | {'Mean':>6} | {'Std':>6}")
    print("-" * 50)
    print(f"{'yomitoku':<12} | {yomi_stats['min']:6.3f} | {yomi_stats['max']:6.3f} | {yomi_stats['mean']:6.3f} | {yomi_stats['std']:6.3f}")
    print(f"{'easyocr':<12} | {easy_stats['min']:6.3f} | {easy_stats['max']:6.3f} | {easy_stats['mean']:6.3f} | {easy_stats['std']:6.3f}")

    print("\nNormalization Recommendation:")

    # Check if normalization is needed
    yomi_range = yomi_stats['max'] - yomi_stats['min']
    easy_range = easy_stats['max'] - easy_stats['min']

    if yomi_stats['mean'] > 0.9 and yomi_stats['std'] < 0.1:
        print("  yomitoku: Always high confidence (near 1.0) - consider using 1.0 as constant")
    else:
        print(f"  yomitoku: Range [{yomi_stats['min']:.2f}, {yomi_stats['max']:.2f}] - min-max normalize")

    if easy_stats['mean'] < 0.5:
        print("  easyocr: Generally low confidence - may need upscaling")
    else:
        print(f"  easyocr: Range [{easy_stats['min']:.2f}, {easy_stats['max']:.2f}] - min-max normalize")


if __name__ == "__main__":
    main()
