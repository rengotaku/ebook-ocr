#!/usr/bin/env python3
"""yomitoku TEXT領域 + Guesslang判定の検証"""

import json
from pathlib import Path


def check_existing_layout_results():
    """既存のlayout.json結果を確認"""
    # Check for any existing layout results
    layout_dirs = [
        Path("output"),
        Path("results"),
        Path("samples"),
    ]

    for d in layout_dirs:
        if not d.exists():
            continue
        for layout_file in d.glob("**/layout*.json"):
            print(f"\n=== {layout_file} ===")
            try:
                with open(layout_file) as f:
                    data = json.load(f)

                if "regions" in data:
                    regions = data["regions"]
                    print(f"Total regions: {len(regions)}")

                    # Count by type
                    types = {}
                    for r in regions:
                        t = r.get("type", "UNKNOWN")
                        types[t] = types.get(t, 0) + 1

                    for t, count in sorted(types.items()):
                        print(f"  {t}: {count}")

                    # Show TEXT regions (potential code candidates)
                    text_regions = [r for r in regions if r.get("type") == "TEXT"]
                    print(f"\nTEXT regions (code candidates): {len(text_regions)}")
                    for i, r in enumerate(text_regions[:3]):
                        print(f"  #{i + 1}: bbox={r.get('bbox')}")

            except Exception as e:
                print(f"Error: {e}")


def simulate_guesslang_flow():
    """Guesslang判定フローのシミュレーション"""
    print("\n" + "=" * 60)
    print("Guesslang Integration Flow (Simulation)")
    print("=" * 60)

    # Simulated TEXT regions from yomitoku
    text_regions = [
        {
            "type": "TEXT",
            "bbox": [100, 200, 500, 300],
            "text": "Element? getFifthElement(List<Element> elements) {\n  if (elements.size() < 5) {\n    return null;\n  }\n  return elements[4];\n}",
        },
        {
            "type": "TEXT",
            "bbox": [100, 400, 500, 450],
            "text": "null安全をサポートしている前提の擬似コードが登場します。",
        },
    ]

    try:
        from guesslang import Guess

        guess = Guess()

        print("\nGuesslang判定結果:")
        for i, region in enumerate(text_regions):
            text = region["text"]
            language = guess.language_name(text)

            if language:
                scores = guess.scores(text)
                confidence = scores.get(language, 0.0)
                is_code = confidence >= 0.5
            else:
                confidence = 0.0
                is_code = False

            print(f"\n  Region #{i + 1}:")
            print(f"    Text: {text[:50]}...")
            print(f"    Language: {language}")
            print(f"    Confidence: {confidence:.2%}")
            print(f"    Is Code: {is_code}")
            print(f"    → New Type: {'CODE' if is_code else 'TEXT'}")

    except ImportError:
        print("\nGuesslang not installed. Install with: pip install guesslang")
        print("Simulating expected behavior:")
        print("  Region #1 (Java code) → CODE (confidence ~95%)")
        print("  Region #2 (Japanese text) → TEXT (confidence ~0%)")


def main():
    check_existing_layout_results()
    simulate_guesslang_flow()


if __name__ == "__main__":
    main()
