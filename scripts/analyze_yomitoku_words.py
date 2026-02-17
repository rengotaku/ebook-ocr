#!/usr/bin/env python3
"""Analyze yomitoku words-level confidence (rec_score)."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PIL import Image
import cv2
import numpy as np
from yomitoku import DocumentAnalyzer


def main():
    image_path = "output/157012a97dcbebed/pages/page_0024.png"

    print("Loading image...")
    image = Image.open(image_path)
    img_array = np.array(image.convert("RGB"))
    cv_img = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

    print("Running yomitoku...")
    analyzer = DocumentAnalyzer(visualize=False, device="cuda")
    results, _, _ = analyzer(cv_img)

    print("\n" + "=" * 60)
    print("PARAGRAPHS (current implementation)")
    print("=" * 60)

    for i, para in enumerate(results.paragraphs):
        text = para.contents if hasattr(para, 'contents') else para.text
        print(f"\nParagraph {i}:")
        print(f"  Text: {text[:50]}..." if len(text) > 50 else f"  Text: {text}")
        print(f"  Box: {para.box}")
        # Check if paragraph has confidence
        if hasattr(para, 'confidence'):
            print(f"  Confidence: {para.confidence}")
        if hasattr(para, 'score'):
            print(f"  Score: {para.score}")

    print("\n" + "=" * 60)
    print("WORDS (rec_score available)")
    print("=" * 60)

    words = results.words if hasattr(results, 'words') else []
    print(f"\nTotal words: {len(words)}")

    if words:
        rec_scores = []
        print(f"\n{'rec_score':>10} | {'Text':<30}")
        print("-" * 45)

        for word in words[:30]:  # First 30 words
            text = word.content if hasattr(word, 'content') else str(word)
            score = word.rec_score if hasattr(word, 'rec_score') else None

            if score is not None:
                rec_scores.append(score)
                print(f"{score:10.4f} | {text[:30]}")
            else:
                print(f"{'N/A':>10} | {text[:30]}")

        if rec_scores:
            print(f"\nWords rec_score Statistics:")
            print(f"  Count:  {len(rec_scores)}")
            print(f"  Min:    {min(rec_scores):.4f}")
            print(f"  Max:    {max(rec_scores):.4f}")
            print(f"  Mean:   {np.mean(rec_scores):.4f}")
            print(f"  Std:    {np.std(rec_scores):.4f}")
            print(f"  Median: {np.median(rec_scores):.4f}")

            # Distribution
            print(f"\nDistribution:")
            buckets = [0, 0.3, 0.5, 0.7, 0.9, 1.0]
            for i in range(len(buckets) - 1):
                count = sum(1 for s in rec_scores if buckets[i] <= s < buckets[i+1])
                pct = count / len(rec_scores) * 100
                bar = '█' * int(pct / 2)
                print(f"  [{buckets[i]:.1f}-{buckets[i+1]:.1f}): {count:3d} ({pct:5.1f}%) {bar}")

    # Check other attributes
    print("\n" + "=" * 60)
    print("RESULTS STRUCTURE")
    print("=" * 60)
    print(f"\nAvailable attributes: {dir(results)}")


if __name__ == "__main__":
    main()
