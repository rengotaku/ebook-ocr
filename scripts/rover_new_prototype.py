#!/usr/bin/env python3
"""New ROVER prototype: Character-level alignment with confidence-weighted voting.

Based on specs/008-rover-redesign/spec.md
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from difflib import SequenceMatcher

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PIL import Image
import numpy as np

from ocr_engines import TextWithBox, EngineResult

# Engine weights
ENGINE_WEIGHTS = {
    "yomitoku": 1.5,
    "paddleocr": 1.2,
    "easyocr": 1.0,
}

# Confidence threshold for garbage filter
CONFIDENCE_THRESHOLD = 0.5


@dataclass
class CharVote:
    """Vote for a single character position."""
    char: str
    weight: float
    engine: str


def is_garbage(text: str, confidence: float) -> bool:
    """Check if text is garbage output.

    Criteria:
    - confidence < 0.5
    - ASCII-only and <= 5 chars without Japanese
    - Same character repeated 5+ times
    """
    if confidence < CONFIDENCE_THRESHOLD:
        return True

    # ASCII-only short text without Japanese
    if len(text) <= 5 and text.isascii():
        return True

    # Repeated character check
    if len(text) >= 5:
        for i in range(len(text) - 4):
            if len(set(text[i:i+5])) == 1:
                return True

    return False


def align_texts_char_level(texts: list[tuple[str, str, float]]) -> list[list[CharVote]]:
    """Align multiple texts at character level using SequenceMatcher.

    Args:
        texts: List of (engine_name, text, confidence) tuples

    Returns:
        List of positions, each containing list of CharVotes
    """
    if not texts:
        return []

    # Filter garbage
    valid_texts = [
        (engine, text, conf)
        for engine, text, conf in texts
        if not is_garbage(text, conf)
    ]

    if not valid_texts:
        # Fall back to highest weight engine if all filtered
        valid_texts = sorted(texts, key=lambda x: ENGINE_WEIGHTS.get(x[0], 0), reverse=True)[:1]

    if len(valid_texts) == 1:
        engine, text, conf = valid_texts[0]
        weight = ENGINE_WEIGHTS.get(engine, 1.0) * conf
        return [[CharVote(c, weight, engine)] for c in text]

    # Use first text as reference for alignment
    ref_engine, ref_text, ref_conf = valid_texts[0]

    # Initialize positions with reference text
    positions: list[list[CharVote]] = []
    for c in ref_text:
        weight = ENGINE_WEIGHTS.get(ref_engine, 1.0) * ref_conf
        positions.append([CharVote(c, weight, ref_engine)])

    # Align other texts to reference
    for engine, text, conf in valid_texts[1:]:
        weight = ENGINE_WEIGHTS.get(engine, 1.0) * conf
        matcher = SequenceMatcher(None, ref_text, text)

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                # Characters match - add votes
                for k, pos_idx in enumerate(range(i1, i2)):
                    if pos_idx < len(positions):
                        positions[pos_idx].append(CharVote(text[j1 + k], weight, engine))
            elif tag == 'replace':
                # Different characters - add as alternative votes
                for k, pos_idx in enumerate(range(i1, i2)):
                    if pos_idx < len(positions) and j1 + k < len(text):
                        positions[pos_idx].append(CharVote(text[j1 + k], weight, engine))
            elif tag == 'insert':
                # Text has extra characters - could insert new positions
                # For now, skip (simplification)
                pass
            elif tag == 'delete':
                # Reference has extra characters - mark as potential deletion
                # Keep reference chars but note they're not in this engine
                pass

    return positions


def vote_characters(positions: list[list[CharVote]]) -> str:
    """Vote for best character at each position.

    Args:
        positions: List of positions with CharVotes

    Returns:
        Voted text string
    """
    result = []
    for pos_votes in positions:
        if not pos_votes:
            continue

        # Aggregate votes by character
        char_weights: dict[str, float] = {}
        for vote in pos_votes:
            char_weights[vote.char] = char_weights.get(vote.char, 0) + vote.weight

        # Pick character with highest total weight
        best_char = max(char_weights.items(), key=lambda x: x[1])[0]
        result.append(best_char)

    return ''.join(result)


def cluster_by_y(items: list[TextWithBox], y_tolerance: int = 20) -> list[list[TextWithBox]]:
    """Cluster items into lines by y-coordinate."""
    if not items:
        return []

    sorted_items = sorted(items, key=lambda x: x.y_center)
    lines: list[list[TextWithBox]] = []
    current_line: list[TextWithBox] = [sorted_items[0]]

    for item in sorted_items[1:]:
        current_y = sum(i.y_center for i in current_line) / len(current_line)
        if abs(item.y_center - current_y) <= y_tolerance:
            current_line.append(item)
        else:
            lines.append(sorted(current_line, key=lambda x: x.bbox[0]))
            current_line = [item]

    if current_line:
        lines.append(sorted(current_line, key=lambda x: x.bbox[0]))

    return lines


def align_lines_by_y(
    lines_by_engine: dict[str, list[list[TextWithBox]]],
    y_tolerance: int = 30,
) -> list[dict[str, list[TextWithBox] | None]]:
    """Align lines from multiple engines by y-coordinate."""
    # Collect all y positions
    all_y: list[tuple[float, str, int]] = []
    for engine, lines in lines_by_engine.items():
        for idx, line in enumerate(lines):
            y_center = sum(item.y_center for item in line) / len(line)
            all_y.append((y_center, engine, idx))

    all_y.sort(key=lambda x: x[0])

    aligned: list[dict[str, list[TextWithBox] | None]] = []
    used: set[tuple[str, int]] = set()

    i = 0
    while i < len(all_y):
        y_center, engine, idx = all_y[i]
        if (engine, idx) in used:
            i += 1
            continue

        line_dict: dict[str, list[TextWithBox] | None] = {}
        line_dict[engine] = lines_by_engine[engine][idx]
        used.add((engine, idx))

        # Find nearby lines from other engines
        j = i + 1
        while j < len(all_y):
            next_y, next_engine, next_idx = all_y[j]
            if next_y - y_center <= y_tolerance:
                if next_engine not in line_dict and (next_engine, next_idx) not in used:
                    line_dict[next_engine] = lines_by_engine[next_engine][next_idx]
                    used.add((next_engine, next_idx))
                j += 1
            else:
                break

        aligned.append(line_dict)
        i += 1

    return aligned


def new_rover_merge(
    engine_results: dict[str, EngineResult],
) -> tuple[str, dict[str, int]]:
    """New ROVER merge with character-level voting.

    Args:
        engine_results: Dict of engine name to EngineResult

    Returns:
        Tuple of (merged_text, engine_contributions)
    """
    # Convert to lines by y-coordinate
    lines_by_engine: dict[str, list[list[TextWithBox]]] = {}
    for engine, result in engine_results.items():
        if result.success and result.items:
            lines = cluster_by_y(result.items)
            lines_by_engine[engine] = lines

    if not lines_by_engine:
        return "", {}

    # Align lines by y-coordinate
    aligned_lines = align_lines_by_y(lines_by_engine)

    # Process each aligned line
    final_lines: list[str] = []
    contributions: dict[str, int] = {engine: 0 for engine in engine_results}

    for line_dict in aligned_lines:
        # Collect texts from each engine for this line
        texts: list[tuple[str, str, float]] = []
        for engine, items in line_dict.items():
            if items:
                # Concatenate items in line
                line_text = ''.join(item.text for item in items)
                avg_conf = sum(item.confidence for item in items) / len(items)
                texts.append((engine, line_text, avg_conf))

        if not texts:
            continue

        # Character-level alignment and voting
        positions = align_texts_char_level(texts)
        voted_text = vote_characters(positions)

        if voted_text:
            final_lines.append(voted_text)

            # Track contributions (simplified: credit engine with most matching chars)
            for engine, text, _ in texts:
                matching = sum(1 for c1, c2 in zip(voted_text, text) if c1 == c2)
                if matching > len(voted_text) * 0.5:
                    contributions[engine] += 1

    return '\n'.join(final_lines), contributions


def run_easyocr_with_clahe(image: Image.Image) -> EngineResult:
    """Run EasyOCR with CLAHE preprocessing."""
    import cv2
    import easyocr

    # Convert to numpy
    img_array = np.array(image.convert('RGB'))

    # Apply CLAHE
    lab = cv2.cvtColor(img_array, cv2.COLOR_RGB2LAB)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    lab[:, :, 0] = clahe.apply(lab[:, :, 0])
    processed = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

    # Run EasyOCR
    try:
        reader = easyocr.Reader(['ja', 'en'], gpu=False)
        results = reader.readtext(processed, detail=1)

        items: list[TextWithBox] = []
        for bbox_points, text, confidence in results:
            x_coords = [p[0] for p in bbox_points]
            y_coords = [p[1] for p in bbox_points]
            bbox = (
                int(min(x_coords)),
                int(min(y_coords)),
                int(max(x_coords)),
                int(max(y_coords)),
            )
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

    # Run engines
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

    # New ROVER merge
    print("\nRunning NEW ROVER (char-level voting)...")
    merged_text, contributions = new_rover_merge(engine_results)

    print(f"\nContributions: {contributions}")
    print("\n=== NEW ROVER OUTPUT ===")
    print(merged_text)

    # Save result
    output_file = output_dir / "page_0024_rover_new.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# NEW ROVER OCR output for page_0024.png\n")
        f.write("# 新ROVERアルゴリズム（文字レベル投票 + 信頼度重み付き）\n")
        f.write(f"# Engines: yomitoku, easyocr (with CLAHE)\n")
        f.write(f"# Contributions: {contributions}\n\n")
        f.write(merged_text)

    print(f"\nSaved: {output_file}")


if __name__ == "__main__":
    main()
