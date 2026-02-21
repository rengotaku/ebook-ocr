#!/usr/bin/env python3
"""詳細診断: なぜ矩形が検出されないかを調査"""

from pathlib import Path

import cv2


def diagnose_image(image_path: str) -> None:
    """画像の特性と各段階の結果を出力"""
    print(f"\n{'=' * 60}")
    print(f"Diagnosing: {image_path}")
    print("=" * 60)

    img = cv2.imread(image_path)
    if img is None:
        print("ERROR: Cannot read image")
        return

    h, w = img.shape[:2]
    total_area = h * w
    print(f"Image size: {w}x{h} = {total_area:,} pixels")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Save grayscale
    output_dir = Path("specs/014-code-block-tagging/validation")
    output_dir.mkdir(parents=True, exist_ok=True)
    stem = Path(image_path).stem

    # Try different Canny thresholds
    for canny_low, canny_high in [(30, 100), (50, 150), (100, 200)]:
        print(f"\n--- Canny({canny_low}, {canny_high}) ---")

        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        edges = cv2.Canny(blurred, canny_low, canny_high)

        # Count edge pixels
        edge_count = cv2.countNonZero(edges)
        print(f"Edge pixels: {edge_count:,} ({edge_count / total_area:.1%})")

        # Morphological closing
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

        # Find all contours
        contours, _ = cv2.findContours(closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)
        print(f"Total contours found: {len(contours)}")

        # Analyze contours
        four_sided = 0
        candidates = []
        for i, contour in enumerate(contours):
            area = cv2.contourArea(contour)
            if area < 100:  # Skip tiny contours
                continue

            epsilon = 0.02 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            if len(approx) == 4:
                four_sided += 1
                x, y, w_rect, h_rect = cv2.boundingRect(contour)
                area_ratio = area / total_area

                # Relaxed filtering for diagnosis
                if area_ratio > 0.001:  # At least 0.1% of image
                    candidates.append(
                        {
                            "vertices": len(approx),
                            "bbox": [x, y, x + w_rect, y + h_rect],
                            "area": int(area),
                            "area_ratio": area_ratio,
                        }
                    )

        print(f"4-sided contours: {four_sided}")
        print(f"Candidates (area > 0.1%): {len(candidates)}")

        # Show top candidates
        candidates.sort(key=lambda c: c["area"], reverse=True)
        for j, c in enumerate(candidates[:3]):
            print(f"  #{j + 1}: area={c['area_ratio']:.2%}, bbox={c['bbox']}")

        # Save edge image for best threshold
        if canny_low == 50:
            cv2.imwrite(str(output_dir / f"{stem}_edges.png"), edges)
            cv2.imwrite(str(output_dir / f"{stem}_closed.png"), closed)

            # Draw all candidate contours
            vis = img.copy()
            for c in candidates[:5]:
                x1, y1, x2, y2 = c["bbox"]
                cv2.rectangle(vis, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.imwrite(str(output_dir / f"{stem}_candidates.png"), vis)


def main():
    samples = ["samples/Screenshot_20260220-150521.png", "samples/frame_0037.png"]
    for s in samples:
        diagnose_image(s)


if __name__ == "__main__":
    main()
