#!/usr/bin/env python3
"""New ROVER v3: Paragraph-based merging with yomitoku as reference.

Key insight: yomitoku outputs paragraphs, easyocr outputs lines.
Solution: Map easyocr lines to yomitoku paragraphs by y-range, then vote.
"""

import sys
from pathlib import Path
from dataclasses import dataclass
from difflib import SequenceMatcher

sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from PIL import Image
import numpy as np

from ocr_engines import TextWithBox, EngineResult

ENGINE_WEIGHTS = {
    "yomitoku": 1.5,
    "paddleocr": 1.2,
    "easyocr": 1.0,
}

CONFIDENCE_THRESHOLD = 0.5


def is_garbage(text: str, confidence: float) -> bool:
    """Check if text is garbage."""
    if confidence < CONFIDENCE_THRESHOLD:
        return True
    if len(text) <= 5 and text.isascii():
        return True
    return False


def text_similarity(t1: str, t2: str) -> float:
    """Calculate similarity ratio."""
    if not t1 or not t2:
        return 0.0
    return SequenceMatcher(None, t1, t2).ratio()


def char_level_vote(texts: list[tuple[str, str, float]]) -> str:
    """Character-level voting.

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
        valid = sorted(texts, key=lambda x: ENGINE_WEIGHTS.get(x[0], 0), reverse=True)[:1]

    if len(valid) == 1:
        return valid[0][1]

    # Sort by weight * confidence
    valid.sort(key=lambda x: ENGINE_WEIGHTS.get(x[0], 0) * x[2], reverse=True)
    ref_engine, ref_text, ref_conf = valid[0]

    # Initialize positions
    positions: list[dict[str, float]] = [{c: ENGINE_WEIGHTS[ref_engine] * ref_conf} for c in ref_text]

    # Add votes from other engines
    for engine, text, conf in valid[1:]:
        weight = ENGINE_WEIGHTS.get(engine, 1.0) * conf
        matcher = SequenceMatcher(None, ref_text, text)

        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                for k in range(i2 - i1):
                    pos_idx = i1 + k
                    if pos_idx < len(positions):
                        char = text[j1 + k]
                        positions[pos_idx][char] = positions[pos_idx].get(char, 0) + weight
            elif tag == 'replace':
                for k in range(min(i2 - i1, j2 - j1)):
                    pos_idx = i1 + k
                    if pos_idx < len(positions):
                        char = text[j1 + k]
                        positions[pos_idx][char] = positions[pos_idx].get(char, 0) + weight

    # Vote
    result = []
    for pos_votes in positions:
        if pos_votes:
            best_char = max(pos_votes.items(), key=lambda x: x[1])[0]
            result.append(best_char)

    return ''.join(result)


@dataclass
class Paragraph:
    """A paragraph with y-range."""
    engine: str
    text: str
    confidence: float
    y_min: int
    y_max: int


def extract_paragraphs_yomitoku(result: EngineResult) -> list[Paragraph]:
    """Extract paragraphs from yomitoku result."""
    paragraphs = []
    for item in result.items:
        paragraphs.append(Paragraph(
            engine="yomitoku",
            text=item.text,
            confidence=item.confidence,
            y_min=item.bbox[1],
            y_max=item.bbox[3],
        ))
    return paragraphs


def extract_lines_easyocr(result: EngineResult) -> list[Paragraph]:
    """Extract lines from easyocr result, grouped by y."""
    if not result.items:
        return []

    # Group by y
    sorted_items = sorted(result.items, key=lambda x: x.y_center)
    y_tolerance = 20

    lines: list[list[TextWithBox]] = []
    current: list[TextWithBox] = [sorted_items[0]]

    for item in sorted_items[1:]:
        current_y = sum(i.y_center for i in current) / len(current)
        if abs(item.y_center - current_y) <= y_tolerance:
            current.append(item)
        else:
            lines.append(sorted(current, key=lambda x: x.bbox[0]))
            current = [item]
    if current:
        lines.append(sorted(current, key=lambda x: x.bbox[0]))

    # Convert to Paragraph
    paragraphs = []
    for line_items in lines:
        text = ''.join(item.text for item in line_items)
        conf = sum(item.confidence for item in line_items) / len(line_items)
        y_min = min(item.bbox[1] for item in line_items)
        y_max = max(item.bbox[3] for item in line_items)
        paragraphs.append(Paragraph("easyocr", text, conf, y_min, y_max))

    return paragraphs


def new_rover_v3(engine_results: dict[str, EngineResult]) -> tuple[str, dict[str, int]]:
    """New ROVER v3: Use yomitoku paragraphs as reference structure.

    Strategy:
    1. Use yomitoku paragraphs as the structural base
    2. Find easyocr lines that overlap with each yomitoku paragraph
    3. Concatenate overlapping easyocr lines into single text
    4. Character-level vote between yomitoku paragraph and concatenated easyocr
    """
    yomitoku_result = engine_results.get("yomitoku")
    easyocr_result = engine_results.get("easyocr")

    if not yomitoku_result or not yomitoku_result.success:
        # Fall back to easyocr only
        if easyocr_result and easyocr_result.success:
            return '\n'.join(item.text for item in easyocr_result.items), {"easyocr": len(easyocr_result.items)}
        return "", {}

    # Extract paragraphs
    yomitoku_paras = extract_paragraphs_yomitoku(yomitoku_result)

    # Extract easyocr lines
    easyocr_lines = []
    if easyocr_result and easyocr_result.success:
        easyocr_lines = extract_lines_easyocr(easyocr_result)

    # For each yomitoku paragraph, find overlapping easyocr lines
    final_lines: list[str] = []
    contributions = {"yomitoku": 0, "easyocr": 0}

    for para in yomitoku_paras:
        # Find overlapping easyocr lines (with margin)
        margin = 30
        overlapping = [
            line for line in easyocr_lines
            if (line.y_min <= para.y_max + margin and line.y_max >= para.y_min - margin)
        ]

        if overlapping:
            # Sort by y position and concatenate
            overlapping.sort(key=lambda x: x.y_min)
            easyocr_text = ''.join(line.text for line in overlapping)
            easyocr_conf = sum(line.confidence for line in overlapping) / len(overlapping)

            # Character-level vote
            texts = [
                ("yomitoku", para.text, para.confidence),
                ("easyocr", easyocr_text, easyocr_conf),
            ]
            voted = char_level_vote(texts)

            # Check which engine contributed more
            yomi_sim = text_similarity(voted, para.text)
            easy_sim = text_similarity(voted, easyocr_text)

            if yomi_sim >= easy_sim:
                contributions["yomitoku"] += 1
            else:
                contributions["easyocr"] += 1

            final_lines.append(voted)
        else:
            # No easyocr overlap - use yomitoku as-is
            final_lines.append(para.text)
            contributions["yomitoku"] += 1

    return '\n'.join(final_lines), contributions


def run_easyocr_with_clahe(image: Image.Image) -> EngineResult:
    """Run EasyOCR with CLAHE preprocessing."""
    import cv2
    import easyocr

    img_array = np.array(image.convert('RGB'))
    lab = cv2.cvtColor(img_array, cv2.COLOR_RGB2LAB)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    lab[:, :, 0] = clahe.apply(lab[:, :, 0])
    processed = cv2.cvtColor(lab, cv2.COLOR_LAB2RGB)

    try:
        reader = easyocr.Reader(['ja', 'en'], gpu=False)
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
    print(f"  yomitoku: {len(yomitoku_result.items)} items (paragraphs)")

    print("Running easyocr with CLAHE...")
    easyocr_result = run_easyocr_with_clahe(image)
    print(f"  easyocr: {len(easyocr_result.items)} items (lines)")

    engine_results = {
        "yomitoku": yomitoku_result,
        "easyocr": easyocr_result,
    }

    print("\nRunning NEW ROVER v3 (paragraph-based)...")
    merged_text, contributions = new_rover_v3(engine_results)

    print(f"\nContributions: {contributions}")
    print("\n=== NEW ROVER v3 OUTPUT ===")
    print(merged_text)

    lines = merged_text.split('\n')
    print(f"\n--- Stats ---")
    print(f"Total paragraphs: {len(lines)}")

    # Compare with golden
    golden_path = output_dir / "page_0024_golden.txt"
    if golden_path.exists():
        with open(golden_path, 'r', encoding='utf-8') as f:
            golden_text = f.read()
        # Skip header lines
        golden_content = '\n'.join(line for line in golden_text.split('\n') if not line.startswith('#'))
        similarity = text_similarity(merged_text, golden_content.strip())
        print(f"Similarity to golden: {similarity:.2%}")

    output_file = output_dir / "page_0024_rover_new_v3.txt"
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("# NEW ROVER v3 OCR output for page_0024.png\n")
        f.write("# 新ROVERアルゴリズム（段落ベース + 文字レベル投票）\n")
        f.write("# Strategy: yomitoku paragraphs as base, merge overlapping easyocr lines\n")
        f.write(f"# Engines: yomitoku, easyocr (with CLAHE)\n")
        f.write(f"# Contributions: {contributions}\n")
        f.write(f"# Total paragraphs: {len(lines)}\n\n")
        f.write(merged_text)

    print(f"\nSaved: {output_file}")


if __name__ == "__main__":
    main()
