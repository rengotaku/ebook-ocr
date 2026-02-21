#!/usr/bin/env python3
"""
コードブロック検出の技術検証スクリプト

検証項目:
1. OpenCV枠線検出が正しく矩形を検出するか
2. 検出された領域がコードブロックらしいか（視覚的確認用）
"""

import json
from pathlib import Path

import cv2


def detect_bordered_rectangles(
    image_path: str,
    min_area_ratio: float = 0.005,
    max_area_ratio: float = 0.75,
    canny_low: int = 50,
    canny_high: int = 150,
) -> list[dict]:
    """OpenCVで枠線付き矩形を検出"""
    img = cv2.imread(image_path)
    if img is None:
        raise ValueError(f"Cannot read image: {image_path}")

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    h, w = img.shape[:2]
    total_area = h * w

    # Canny edge detection
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, canny_low, canny_high)

    # Morphological closing to fill gaps
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
    closed = cv2.morphologyEx(edges, cv2.MORPH_CLOSE, kernel)

    # Find contours
    contours, _ = cv2.findContours(closed, cv2.RETR_TREE, cv2.CHAIN_APPROX_SIMPLE)

    rectangles = []
    for contour in contours:
        # Approximate to polygon
        epsilon = 0.02 * cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, epsilon, True)

        # Must be 4-sided
        if len(approx) != 4:
            continue

        x, y, w_rect, h_rect = cv2.boundingRect(contour)
        area = cv2.contourArea(contour)

        # Calculate metrics
        aspect_ratio = float(w_rect) / h_rect if h_rect > 0 else 0

        hull = cv2.convexHull(contour)
        hull_area = cv2.contourArea(hull)
        solidity = float(area) / hull_area if hull_area > 0 else 0

        rect_area = w_rect * h_rect
        extent = float(area) / rect_area if rect_area > 0 else 0

        # Apply filters
        min_area = min_area_ratio * total_area
        max_area = max_area_ratio * total_area

        if not (min_area < area < max_area):
            continue
        if not (0.3 <= aspect_ratio <= 5.0):  # Wide range for code blocks
            continue
        if solidity < 0.7:  # Allow some irregularity
            continue
        if extent < 0.5:
            continue

        rectangles.append(
            {
                "bbox": [x, y, x + w_rect, y + h_rect],
                "area": int(area),
                "area_ratio": round(area / total_area, 4),
                "aspect_ratio": round(aspect_ratio, 2),
                "solidity": round(solidity, 2),
                "extent": round(extent, 2),
            }
        )

    # Sort by area (largest first)
    rectangles.sort(key=lambda r: r["area"], reverse=True)

    return rectangles


def draw_detections(image_path: str, rectangles: list[dict], output_path: str) -> None:
    """検出結果を画像に描画"""
    img = cv2.imread(image_path)

    for i, rect in enumerate(rectangles):
        x1, y1, x2, y2 = rect["bbox"]
        # Different colors for different rectangles
        color = [(0, 255, 0), (255, 0, 0), (0, 0, 255), (255, 255, 0), (255, 0, 255)][i % 5]
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 3)
        cv2.putText(img, f"#{i + 1}", (x1, y1 - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.9, color, 2)

    cv2.imwrite(output_path, img)
    print(f"Saved: {output_path}")


def main():
    samples_dir = Path("samples")
    output_dir = Path("specs/014-code-block-tagging/validation")
    output_dir.mkdir(parents=True, exist_ok=True)

    images = list(samples_dir.glob("*.png"))
    print(f"Found {len(images)} sample images\n")

    results = {}

    for img_path in images:
        print(f"=== {img_path.name} ===")

        try:
            rectangles = detect_bordered_rectangles(str(img_path))
            print(f"Detected {len(rectangles)} candidate rectangles:\n")

            for i, rect in enumerate(rectangles[:5]):  # Show top 5
                print(f"  #{i + 1}: bbox={rect['bbox']}")
                print(f"       area_ratio={rect['area_ratio']:.1%}, aspect={rect['aspect_ratio']}")
                print(f"       solidity={rect['solidity']}, extent={rect['extent']}")
                print()

            # Save visualization
            output_path = output_dir / f"{img_path.stem}_detected.png"
            if rectangles:
                draw_detections(str(img_path), rectangles[:5], str(output_path))

            results[img_path.name] = {
                "total_detected": len(rectangles),
                "top_candidates": rectangles[:5],
            }

        except Exception as e:
            print(f"Error: {e}")
            results[img_path.name] = {"error": str(e)}

        print()

    # Save JSON results
    results_path = output_dir / "detection_results.json"
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Results saved to: {results_path}")


if __name__ == "__main__":
    main()
