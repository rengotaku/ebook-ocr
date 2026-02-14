#!/usr/bin/env python3
"""Run ROVER OCR on a single image and save results."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PIL import Image

from ocr_engines import run_all_engines
from ocr_rover import rover_merge

def main():
    image_path = sys.argv[1] if len(sys.argv) > 1 else "output/157012a97dcbebed/pages/page_0024.png"
    output_dir = Path(sys.argv[2] if len(sys.argv) > 2 else "specs/008-rover-redesign/golden")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading image: {image_path}")
    image = Image.open(image_path)

    # Run all engines (excluding tesseract as per spec)
    engines = ["yomitoku", "paddleocr", "easyocr"]
    print(f"Running engines: {engines}")

    engine_results = run_all_engines(
        image,
        engines=engines,
        yomitoku_device="cuda",
    )

    # Save individual engine outputs
    for engine, result in engine_results.items():
        output_file = output_dir / f"page_0024_{engine}.txt"
        print(f"\n=== {engine.upper()} ===")
        if result.success:
            print(f"Items: {len(result.items)}")
            print("---")
            print(result.text)
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"# {engine} OCR output for page_0024.png\n")
                f.write(f"# Items: {len(result.items)}\n\n")
                f.write(result.text)
            print(f"\nSaved: {output_file}")
        else:
            print(f"FAILED: {result.error}")
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(f"# {engine} OCR output for page_0024.png\n")
                f.write(f"# FAILED: {result.error}\n")

    # Run ROVER
    print("\n=== ROVER (merged) ===")
    rover_result = rover_merge(
        engine_results,
        primary_engine="yomitoku",
        min_agreement=2,
    )

    print(f"Lines: {len(rover_result.lines)}")
    print(f"Gaps filled: {rover_result.gaps_filled}")
    print(f"Contributions: {rover_result.engine_contributions}")
    print("---")
    print(rover_result.text)

    # Save ROVER output
    rover_file = output_dir / "page_0024_rover_current.txt"
    with open(rover_file, "w", encoding="utf-8") as f:
        f.write("# ROVER OCR output for page_0024.png\n")
        f.write("# 現行ROVERアルゴリズム（ライン単位投票）の結果\n")
        f.write(f"# Engines: {', '.join(engines)}\n")
        f.write(f"# Lines: {len(rover_result.lines)}\n")
        f.write(f"# Gaps filled: {rover_result.gaps_filled}\n")
        f.write(f"# Contributions: {rover_result.engine_contributions}\n\n")
        f.write(rover_result.text)

    print(f"\nSaved: {rover_file}")
    print("\n✅ Done!")

if __name__ == "__main__":
    main()
