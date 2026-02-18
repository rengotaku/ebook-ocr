#!/usr/bin/env python3
"""New ROVER v2: Character-level voting with paragraph deduplication.

Key improvement: Merge similar lines from different engines to avoid duplication.
"""

import sys
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

import numpy as np
from ocr_engines import EngineResult, TextWithBox
from PIL import Image

ENGINE_WEIGHTS = {
    "yomitoku": 1.5,
    "paddleocr": 1.2,
    "easyocr": 1.0,
}

CONFIDENCE_THRESHOLD = 0.5


@dataclass
class LineCandidate:
    """Line candidate from an engine."""

    engine: str
    text: str
    confidence: float
    y_center: float
    y_range: tuple[int, int]  # (y_min, y_max)


def is_garbage(text: str, confidence: float) -> bool:
    """Check if text is garbage."""
    if confidence < CONFIDENCE_THRESHOLD:
        return True
    if len(text) <= 5 and text.isascii():
        return True
    if len(text) >= 5:
        for i in range(len(text) - 4):
            if len(set(text[i : i + 5])) == 1:
                return True
    return False


def text_similarity(t1: str, t2: str) -> float:
    """Calculate text similarity ratio."""
    if not t1 or not t2:
        return 0.0
    return SequenceMatcher(None, t1, t2).ratio()


def char_level_vote(texts: list[tuple[str, str, float]]) -> str:
    """Vote at character level.

    Args:
        texts: List of (engine, text, confidence)

    Returns:
        Voted text
    """
    if not texts:
        return ""

    # Filter garbage
    valid = [(e, t, c) for e, t, c in texts if not is_garbage(t, c)]
    if not valid:
        # Fall back to highest weight
        valid = sorted(texts, key=lambda x: ENGINE_WEIGHTS.get(x[0], 0), reverse=True)[:1]

    if len(valid) == 1:
        return valid[0][1]

    # Use best engine's text as reference
    valid.sort(key=lambda x: ENGINE_WEIGHTS.get(x[0], 0) * x[2], reverse=True)
    ref_engine, ref_text, ref_conf = valid[0]

    # Character positions with votes
    positions: list[dict[str, float]] = [{c: ENGINE_WEIGHTS[ref_engine] * ref_conf} for c in ref_text]

    # Align others and add votes
    for engine, text, conf in valid[1:]:
        weight = ENGINE_WEIGHTS.get(engine, 1.0) * conf
        matcher = SequenceMatcher(None, ref_text, text)

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                for k in range(i2 - i1):
                    pos_idx = i1 + k
                    char = text[j1 + k]
                    if pos_idx < len(positions):
                        positions[pos_idx][char] = positions[pos_idx].get(char, 0) + weight
            elif tag == "replace":
                for k in range(min(i2 - i1, j2 - j1)):
                    pos_idx = i1 + k
                    char = text[j1 + k]
                    if pos_idx < len(positions):
                        positions[pos_idx][char] = positions[pos_idx].get(char, 0) + weight

    # Vote for best char at each position
    result = []
    for pos_votes in positions:
        if pos_votes:
            best_char = max(pos_votes.items(), key=lambda x: x[1])[0]
            result.append(best_char)

    return "".join(result)


def extract_lines(result: EngineResult, engine: str) -> list[LineCandidate]:
    """Extract lines from engine result."""
    if not result.success or not result.items:
        return []

    # Group by y-coordinate
    sorted_items = sorted(result.items, key=lambda x: x.y_center)

    lines: list[list[TextWithBox]] = []
    current: list[TextWithBox] = [sorted_items[0]]
    y_tolerance = 20

    for item in sorted_items[1:]:
        current_y = sum(i.y_center for i in current) / len(current)
        if abs(item.y_center - current_y) <= y_tolerance:
            current.append(item)
        else:
            lines.append(sorted(current, key=lambda x: x.bbox[0]))
            current = [item]
    if current:
        lines.append(sorted(current, key=lambda x: x.bbox[0]))

    # Convert to LineCandidate
    candidates = []
    for line_items in lines:
        text = "".join(item.text for item in line_items)
        conf = sum(item.confidence for item in line_items) / len(line_items)
        y_center = sum(item.y_center for item in line_items) / len(line_items)
        y_min = min(item.bbox[1] for item in line_items)
        y_max = max(item.bbox[3] for item in line_items)
        candidates.append(LineCandidate(engine, text, conf, y_center, (y_min, y_max)))

    return candidates


def merge_similar_lines(all_lines: list[LineCandidate], similarity_threshold: float = 0.6) -> list[list[LineCandidate]]:
    """Merge lines that are similar (same content from different engines).

    Uses both y-position overlap AND text similarity.
    """
    if not all_lines:
        return []

    # Sort by y_center
    sorted_lines = sorted(all_lines, key=lambda x: x.y_center)

    groups: list[list[LineCandidate]] = []
    used: set[int] = set()

    for i, line in enumerate(sorted_lines):
        if i in used:
            continue

        group = [line]
        used.add(i)

        # Find similar lines (overlapping y-range or similar text)
        for j, other in enumerate(sorted_lines):
            if j in used:
                continue

            # Check y-range overlap
            y_overlap = line.y_range[0] <= other.y_range[1] and other.y_range[0] <= line.y_range[1]

            # Check text similarity
            sim = text_similarity(line.text, other.text)

            # Merge if y-overlap AND similar text, OR very similar text (regardless of y)
            if (y_overlap and sim >= similarity_threshold) or sim >= 0.8:
                group.append(other)
                used.add(j)

        groups.append(group)

    return groups


def new_rover_v2(engine_results: dict[str, EngineResult]) -> tuple[str, dict[str, int]]:
    """New ROVER v2 with deduplication.

    1. Extract lines from all engines
    2. Group similar lines (deduplication)
    3. Character-level vote within each group
    """
    # Extract all lines
    all_lines: list[LineCandidate] = []
    for engine, result in engine_results.items():
        lines = extract_lines(result, engine)
        all_lines.extend(lines)

    if not all_lines:
        return "", {}

    # Merge similar lines
    groups = merge_similar_lines(all_lines)

    # Sort groups by y position
    groups.sort(key=lambda g: min(line.y_center for line in g))

    # Vote within each group
    final_lines: list[str] = []
    contributions: dict[str, int] = {engine: 0 for engine in engine_results}

    for group in groups:
        texts = [(line.engine, line.text, line.confidence) for line in group]
        voted = char_level_vote(texts)

        if voted:
            final_lines.append(voted)

            # Credit contribution
            for line in group:
                sim = text_similarity(voted, line.text)
                if sim >= 0.7:
                    contributions[line.engine] += 1

    return "\n".join(final_lines), contributions


def run_easyocr_with_clahe(image: Image.Image) -> EngineResult:
    """Run EasyOCR with CLAHE preprocessing."""
    import cv2
    import easyocr

    img_array = np.array(image.convert("RGB"))
    lab = cv2.cvtColor(img_array, cv2.COLOR_RGB2LAB)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    lab[:, :, 0] = clahe.apply(lab[:, :, 0])
    processed = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

    try:
        reader = easyocr.Reader(["ja", "en"], gpu=False)
        results = reader.readtext(processed, detail=1)

        items: list[TextWithBox] = []
        for bbox_points, text, confidence in results:
            x_coords = [p[0] for p in bbox_points]
            y_coords = [p[1] for p in bbox_points]
            bbox = (int(min(x_coords)), int(min(y_coords)), int(max(x_coords)), int(max(y_coords)))
            items.append(TextWithBox(text=text, bbox=bbox, confidence=float(confidence)))

        return EngineResult(engine="easyocr", items=items, success=True)
    except Exception as e:
        return EngineResult(engine="easyocr", items=[], success=False, error=str(e))


def main():
    from ocr_engines import run_yomitoku_with_boxes

    image_path = sys.argv[1] if len(sys.argv) > 1 else "output/157012a97dcbebed/pages/page_0024.png"
    output_dir = Path("specs/008-rover-redesign/golden")
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"Loading image: {image_path}")
    image = Image.open(image_path)

    print("Running yomitoku...")
    yomitoku_result = run_yomitoku_with_boxes(image, device="cuda")
    print(f"  yomitoku: {len(yomitoku_result.items)} items")

    print("Running easyocr with CLAHE...")
    easyocr_result = run_easyocr_with_clahe(image)
    print(f"  easyocr: {len(easyocr_result.items)} items")

    engine_results = {
        "yomitoku": yomitoku_result,
        "easyocr": easyocr_result,
    }

    print("\nRunning NEW ROVER v2 (char-level + dedup)...")
    merged_text, contributions = new_rover_v2(engine_results)

    print(f"\nContributions: {contributions}")
    print("\n=== NEW ROVER v2 OUTPUT ===")
    print(merged_text)

    # Count lines
    lines = merged_text.split("\n")
    print("\n--- Stats ---")
    print(f"Total lines: {len(lines)}")

    output_file = output_dir / "page_0024_rover_new_v2.txt"
    with open(output_file, "w", encoding="utf-8") as f:
        f.write("# NEW ROVER v2 OCR output for page_0024.png\n")
        f.write("# 新ROVERアルゴリズム（文字レベル投票 + 重複排除）\n")
        f.write("# Engines: yomitoku, easyocr (with CLAHE)\n")
        f.write(f"# Contributions: {contributions}\n")
        f.write(f"# Total lines: {len(lines)}\n\n")
        f.write(merged_text)

    print(f"\nSaved: {output_file}")


if __name__ == "__main__":
    main()
