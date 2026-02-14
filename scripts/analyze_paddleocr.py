#!/usr/bin/env python3
"""Analyze PaddleOCR confidence distribution."""

import sys
from pathlib import Path
import logging

# Suppress PaddleOCR verbose logging
logging.getLogger("ppocr").setLevel(logging.WARNING)

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PIL import Image
import numpy as np
from difflib import SequenceMatcher


def text_similarity(t1: str, t2: str) -> float:
    if not t1 or not t2:
        return 0.0
    return SequenceMatcher(None, t1, t2).ratio()


def main():
    image_path = "output/157012a97dcbebed/pages/page_0024.png"
    golden_path = "specs/008-rover-redesign/golden/page_0024_golden.txt"

    # Load golden
    with open(golden_path, 'r', encoding='utf-8') as f:
        golden_lines = f.readlines()
    golden_text = ''.join(line for line in golden_lines if not line.startswith('#')).strip()

    print("Loading image...")
    image = Image.open(image_path)
    img_array = np.array(image)

    print("Running PaddleOCR...")
    from paddleocr import PaddleOCR

    ocr = PaddleOCR(
        lang="japan",
        use_doc_orientation_classify=False,
        use_doc_unwarping=False,
        use_textline_orientation=False,
    )

    result = ocr.predict(img_array)

    print("\n" + "=" * 60)
    print("PaddleOCR Results")
    print("=" * 60)

    all_texts = []
    all_scores = []

    if result:
        for res in result:
            texts = res.get("rec_texts", [])
            scores = res.get("rec_scores", [])

            for i, text in enumerate(texts):
                score = scores[i] if i < len(scores) else 0.0
                all_texts.append(text)
                all_scores.append(score)

    print(f"\nTotal items: {len(all_texts)}")

    if all_scores:
        print(f"\nConfidence Statistics:")
        print(f"  Min:    {min(all_scores):.4f}")
        print(f"  Max:    {max(all_scores):.4f}")
        print(f"  Mean:   {np.mean(all_scores):.4f}")
        print(f"  Std:    {np.std(all_scores):.4f}")
        print(f"  Median: {np.median(all_scores):.4f}")

        # Distribution
        print(f"\nConfidence Distribution:")
        buckets = [0, 0.3, 0.5, 0.7, 0.9, 1.0]
        for i in range(len(buckets) - 1):
            count = sum(1 for s in all_scores if buckets[i] <= s < buckets[i+1])
            pct = count / len(all_scores) * 100
            bar = '█' * int(pct / 2)
            print(f"  [{buckets[i]:.1f}-{buckets[i+1]:.1f}): {count:3d} ({pct:5.1f}%) {bar}")

        # Item-level analysis
        print(f"\nItem-level analysis (top 20 by confidence):")
        print(f"{'Score':>8} | {'Len':>4} | {'Match':>6} | Text")
        print("-" * 70)

        items = list(zip(all_texts, all_scores))
        items.sort(key=lambda x: -x[1])

        correct_high = 0
        wrong_high = 0

        for text, score in items[:20]:
            # Find best match in golden
            best_match = 0.0
            for start in range(len(golden_text)):
                for end in range(start + len(text) - 3, min(start + len(text) + 5, len(golden_text) + 1)):
                    if end > start:
                        sim = text_similarity(text, golden_text[start:end])
                        best_match = max(best_match, sim)

            is_high = score >= 0.7
            is_good = best_match >= 0.5

            if is_high and is_good:
                correct_high += 1
            elif is_high and not is_good:
                wrong_high += 1

            marker = "✓" if is_good else "✗"
            print(f"{score:8.4f} | {len(text):4d} | {best_match:5.2f}{marker} | {text[:40]}")

        print(f"\nReliability (high conf >=0.7):")
        print(f"  Good match: {correct_high}")
        print(f"  Bad match:  {wrong_high}")

    # Summary comparison
    print("\n" + "=" * 60)
    print("COMPARISON WITH OTHER ENGINES")
    print("=" * 60)
    print(f"\n{'Engine':<12} | {'Min':>6} | {'Max':>6} | {'Mean':>6} | {'Recommended Range'}")
    print("-" * 65)
    print(f"{'yomitoku':<12} | {'0.41':>6} | {'1.00':>6} | {'0.96':>6} | (0.4, 1.0)")
    print(f"{'paddleocr':<12} | {min(all_scores):6.2f} | {max(all_scores):6.2f} | {np.mean(all_scores):6.2f} | ({min(all_scores):.2f}, {max(all_scores):.2f})")
    print(f"{'easyocr':<12} | {'0.26':>6} | {'1.00':>6} | {'0.80':>6} | (0.25, 1.0)")


if __name__ == "__main__":
    main()
