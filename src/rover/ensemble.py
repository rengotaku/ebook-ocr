"""ROVER (Recognizer Output Voting Error Reduction) for OCR.

Combines multiple OCR engine outputs using voting and alignment
to produce higher quality results than any single engine.

Strategy:
1. Line-level alignment by y-coordinate
2. Token-level voting within aligned lines
3. Gap detection and filling from secondary engines
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from PIL import Image

from src.rover.engines import EngineResult, TextWithBox, run_all_engines
from src.rover.output import ROVEROutput
from src.rover.alignment import align_texts_character_level, vote_aligned_text


# Engine priority weights for voting (Tesseract excluded from ROVER)
ENGINE_WEIGHTS = {
    "yomitoku": 1.5,    # Best for Japanese
    "paddleocr": 1.2,   # High accuracy
    "easyocr": 1.0,     # Balanced
}


@dataclass
class OCRLine:
    """Single line of OCR result."""
    items: list[TextWithBox]
    engine: str
    y_center: float
    confidence: float = 0.0

    @property
    def text(self) -> str:
        """Concatenated text from all items."""
        return "".join(item.text for item in self.items)

    @property
    def bbox(self) -> tuple[int, int, int, int]:
        """Bounding box covering all items."""
        if not self.items:
            return (0, 0, 0, 0)
        x1 = min(item.bbox[0] for item in self.items)
        y1 = min(item.bbox[1] for item in self.items)
        x2 = max(item.bbox[2] for item in self.items)
        y2 = max(item.bbox[3] for item in self.items)
        return (x1, y1, x2, y2)


@dataclass
class AlignedLine:
    """Aligned line from multiple engines."""
    lines: dict[str, OCRLine | None]  # engine -> line
    y_center: float
    voted_text: str = ""
    source_engines: list[str] = field(default_factory=list)


@dataclass
class ROVERResult:
    """ROVER processing result."""
    text: str
    lines: list[str]
    aligned: list[AlignedLine]
    engine_contributions: dict[str, int]
    gaps_filled: int = 0


def is_garbage(
    text: str,
    confidence: float,
    min_confidence: float = 0.5,
) -> bool:
    """Check if text is garbage output.

    Garbage criteria:
    1. Empty or whitespace-only
    2. confidence < min_confidence
    3. No Japanese chars and len <= 5 (ASCII fragments)
    4. Same character repeated >= 5 times
    5. Punctuation only

    Args:
        text: Text to check.
        confidence: Confidence score (0.0 - 1.0).
        min_confidence: Minimum confidence threshold.

    Returns:
        True if text is garbage, False otherwise.
    """
    # 1. Empty or whitespace-only
    if not text or not text.strip():
        return True

    # 2. Low confidence
    if confidence < min_confidence:
        return True

    # 3. No Japanese chars and len <= 5
    has_japanese = any('\u3040' <= ch <= '\u30ff' or '\u4e00' <= ch <= '\u9fff' for ch in text)
    if not has_japanese and len(text) <= 5:
        return True

    # 4. Same character repeated >= 5 times
    if len(text) >= 5:
        for i in range(len(text) - 4):
            if text[i] == text[i+1] == text[i+2] == text[i+3] == text[i+4]:
                return True

    # 5. Punctuation only
    if all(not ch.isalnum() for ch in text):
        return True

    return False


def normalize_confidence(raw_conf: float, engine: str) -> float:
    """Normalize confidence to [0, 1] scale based on engine-specific range.

    Ranges (from research):
    - yomitoku: (0.4, 1.0)
    - paddleocr: (0.85, 1.0)
    - easyocr: (0.25, 1.0)
    - unknown: (0.0, 1.0)

    Args:
        raw_conf: Raw confidence from engine.
        engine: Engine name.

    Returns:
        Normalized confidence (0.0 - 1.0).
    """
    ranges = {
        "yomitoku": (0.4, 1.0),
        "paddleocr": (0.85, 1.0),
        "easyocr": (0.25, 1.0),
    }
    min_conf, max_conf = ranges.get(engine, (0.0, 1.0))
    normalized = (raw_conf - min_conf) / (max_conf - min_conf)
    return max(0.0, min(1.0, normalized))


def split_multiline_items(
    items: list[TextWithBox],
    y_gap_threshold: int = 15,
) -> list[list[TextWithBox]]:
    """Split items that span multiple physical lines.

    This handles the case where yomitoku returns a single paragraph
    that actually spans multiple physical lines (e.g., y_range=[169-277]).

    Args:
        items: List of text items (may span multiple lines).
        y_gap_threshold: Minimum y-gap to consider a new line.

    Returns:
        List of lists, each inner list is one physical line.
    """
    if not items:
        return []

    # Sort by y_center
    sorted_items = sorted(items, key=lambda x: x.y_center)

    lines: list[list[TextWithBox]] = []
    current_line: list[TextWithBox] = [sorted_items[0]]

    for item in sorted_items[1:]:
        # Check y-gap from previous item
        prev_y = current_line[-1].y_center
        if item.y_center - prev_y > y_gap_threshold:
            # New line
            lines.append(current_line)
            current_line = [item]
        else:
            current_line.append(item)

    if current_line:
        lines.append(current_line)

    return lines


def cluster_lines_by_y(
    items: list[TextWithBox],
    y_tolerance: int = 20,
) -> list[OCRLine]:
    """Cluster text items into lines by y-coordinate.

    Args:
        items: List of text items with bboxes.
        y_tolerance: Maximum vertical distance to consider same line.

    Returns:
        List of OCRLine objects.
    """
    if not items:
        return []

    # Sort by y_center
    sorted_items = sorted(items, key=lambda x: x.y_center)

    lines: list[list[TextWithBox]] = []
    current_line: list[TextWithBox] = [sorted_items[0]]

    for item in sorted_items[1:]:
        # Check if this item belongs to current line
        current_y = sum(i.y_center for i in current_line) / len(current_line)
        if abs(item.y_center - current_y) <= y_tolerance:
            current_line.append(item)
        else:
            lines.append(current_line)
            current_line = [item]

    if current_line:
        lines.append(current_line)

    # Convert to OCRLine objects
    ocr_lines: list[OCRLine] = []
    for line_items in lines:
        # Sort items in line by x-coordinate
        line_items.sort(key=lambda x: x.bbox[0])
        y_center = sum(item.y_center for item in line_items) / len(line_items)
        avg_conf = sum(item.confidence for item in line_items) / len(line_items)
        ocr_lines.append(OCRLine(
            items=line_items,
            engine="",  # Will be set by caller
            y_center=y_center,
            confidence=avg_conf,
        ))

    return ocr_lines


def align_lines_by_y(
    lines_by_engine: dict[str, list[OCRLine]],
    y_tolerance: int = 30,
) -> list[AlignedLine]:
    """Align lines from multiple engines by y-coordinate.

    Args:
        lines_by_engine: Dict mapping engine name to list of OCRLine.
        y_tolerance: Maximum vertical distance to consider same line.

    Returns:
        List of AlignedLine objects.
    """
    # Collect all unique y positions
    all_y_positions: list[tuple[float, str, int]] = []  # (y_center, engine, line_idx)
    for engine, lines in lines_by_engine.items():
        for idx, line in enumerate(lines):
            all_y_positions.append((line.y_center, engine, idx))

    # Sort by y position
    all_y_positions.sort(key=lambda x: x[0])

    # Cluster y positions
    aligned: list[AlignedLine] = []
    used_lines: set[tuple[str, int]] = set()

    i = 0
    while i < len(all_y_positions):
        y_center, engine, idx = all_y_positions[i]

        # Find all lines within tolerance
        lines_dict: dict[str, OCRLine | None] = {}
        y_sum = y_center
        count = 1

        lines_dict[engine] = lines_by_engine[engine][idx]
        used_lines.add((engine, idx))

        # Look ahead for nearby lines
        j = i + 1
        while j < len(all_y_positions):
            next_y, next_engine, next_idx = all_y_positions[j]
            if next_y - y_center <= y_tolerance:
                if next_engine not in lines_dict and (next_engine, next_idx) not in used_lines:
                    lines_dict[next_engine] = lines_by_engine[next_engine][next_idx]
                    used_lines.add((next_engine, next_idx))
                    y_sum += next_y
                    count += 1
                j += 1
            else:
                break

        avg_y = y_sum / count
        aligned.append(AlignedLine(
            lines=lines_dict,
            y_center=avg_y,
        ))

        i = j if j > i + 1 else i + 1

    return aligned


def vote_line_text(
    aligned_line: AlignedLine,
    engine_weights: dict[str, float] | None = None,
    min_agreement: int = 2,
) -> tuple[str, list[str], float]:
    """Vote for best text from aligned lines using character-level voting.

    Args:
        aligned_line: Aligned line with multiple engine results.
        engine_weights: Weight for each engine (higher = more trusted).
        min_agreement: Minimum number of engines that must agree (deprecated).

    Returns:
        Tuple of (voted_text, source_engines, final_confidence).
    """
    if engine_weights is None:
        engine_weights = ENGINE_WEIGHTS

    # Get valid lines (non-None)
    valid_lines = {
        engine: line
        for engine, line in aligned_line.lines.items()
        if line is not None
    }

    if not valid_lines:
        return "", [], 0.0

    # Single engine case
    if len(valid_lines) == 1:
        engine, line = list(valid_lines.items())[0]
        return line.text, [engine], line.confidence

    # Character-level alignment and voting (Phase 3: True ROVER)
    texts = {engine: line.text for engine, line in valid_lines.items()}
    confidences = {engine: normalize_confidence(line.confidence, engine)
                   for engine, line in valid_lines.items()}

    # Align texts at character level
    aligned_positions = align_texts_character_level(texts)

    # Vote across aligned positions
    voted_text, avg_confidence = vote_aligned_text(
        aligned_positions,
        confidences,
        engine_weights,
    )

    # Determine source engines (engines that contributed to the result)
    source_engines = list(valid_lines.keys())

    return voted_text, source_engines, avg_confidence


def rover_merge(
    engine_results: dict[str, EngineResult],
    primary_engine: str = "yomitoku",
    y_tolerance: int = 30,
    min_agreement: int = 2,
) -> ROVERResult:
    """Merge OCR results using ROVER algorithm.

    Args:
        engine_results: Dict mapping engine name to EngineResult.
        primary_engine: Primary engine for baseline.
        y_tolerance: Maximum vertical distance for line alignment.
        min_agreement: Minimum engines that must agree for voting.

    Returns:
        ROVERResult with merged text and metadata.
    """
    # Convert to line-based structure with garbage filtering
    lines_by_engine: dict[str, list[OCRLine]] = {}
    for engine, result in engine_results.items():
        if result.success and result.items:
            # Filter out garbage items
            filtered_items = [
                item for item in result.items
                if not is_garbage(item.text, item.confidence)
            ]
            if filtered_items:
                lines = cluster_lines_by_y(filtered_items)
                for line in lines:
                    line.engine = engine
                lines_by_engine[engine] = lines

    if not lines_by_engine:
        return ROVERResult(
            text="",
            lines=[],
            aligned=[],
            engine_contributions={},
        )

    # Align lines by y-coordinate
    aligned = align_lines_by_y(lines_by_engine, y_tolerance)

    # Vote for each line
    final_lines: list[str] = []
    engine_contributions: dict[str, int] = {engine: 0 for engine in engine_results.keys()}
    gaps_filled = 0

    for aligned_line in aligned:
        voted_text, source_engines, final_confidence = vote_line_text(aligned_line, min_agreement=min_agreement)
        aligned_line.voted_text = voted_text
        aligned_line.source_engines = source_engines
        aligned_line.final_confidence = final_confidence

        if voted_text:
            final_lines.append(voted_text)
            for engine in source_engines:
                engine_contributions[engine] += 1

            # Count gap filling (primary engine missing but others filled)
            if primary_engine not in source_engines and primary_engine in aligned_line.lines:
                if aligned_line.lines[primary_engine] is None:
                    gaps_filled += 1

    # Combine into final text
    final_text = "\n".join(final_lines)

    return ROVERResult(
        text=final_text,
        lines=final_lines,
        aligned=aligned,
        engine_contributions=engine_contributions,
        gaps_filled=gaps_filled,
    )


def run_rover_ocr(
    image: Image.Image | str,
    engines: list[str] | None = None,
    primary_engine: str = "yomitoku",
    device: str = "cpu",
    min_agreement: int = 2,
) -> ROVERResult:
    """Run ROVER OCR on a single image.

    Args:
        image: PIL Image or path to image file.
        engines: List of engine names to use.
        primary_engine: Primary engine (for gap detection).
        device: Device for Yomitoku.
        min_agreement: Minimum engines that must agree.

    Returns:
        ROVERResult with merged text.
    """
    if isinstance(image, str):
        image = Image.open(image)

    # Run all engines
    engine_results = run_all_engines(
        image,
        engines=engines,
        device=device,
    )

    # ROVER merge
    return rover_merge(
        engine_results,
        primary_engine=primary_engine,
        min_agreement=min_agreement,
    )


def run_rover_batch(
    pages_dir: str,
    output_dir: str,
    engines: list[str] | None = None,
    primary_engine: str = "yomitoku",
    device: str = "cpu",
    min_agreement: int = 2,
) -> list[tuple[str, ROVERResult]]:
    """Run ROVER OCR on all pages in a directory.

    Args:
        pages_dir: Directory containing page images.
        output_dir: Directory for output files.
        engines: List of engine names to use.
        primary_engine: Primary engine.
        device: Device for Yomitoku.
        min_agreement: Minimum engines that must agree.

    Returns:
        List of (page_name, ROVERResult) tuples.
    """
    pages_path = Path(pages_dir)
    output = ROVEROutput(output_dir)

    pages = sorted(pages_path.glob("*.png"))
    all_results: list[tuple[str, ROVERResult]] = []

    print(f"Running ROVER OCR on {len(pages)} pages...")
    if engines:
        print(f"Engines: {', '.join(engines)}")

    for page_path in pages:
        page_name = page_path.stem
        print(f"\nProcessing {page_path.name}...")

        with Image.open(page_path) as img:
            # Run all engines
            engine_results = run_all_engines(
                img,
                engines=engines,
                device=device,
            )

            # Save raw outputs and extract headings from yomitoku
            for engine, result in engine_results.items():
                if result.success:
                    output.save_raw(engine, page_name, result.text)
                    print(f"  {engine}: {len(result.items)} items")
                    # Save headings from yomitoku
                    if engine == "yomitoku" and result.headings:
                        output.save_headings(page_name, result.headings)
                        print(f"    headings: {result.headings}")
                else:
                    print(f"  {engine}: FAILED - {result.error}")

            # ROVER merge
            rover_result = rover_merge(
                engine_results,
                primary_engine=primary_engine,
                min_agreement=min_agreement,
            )

            # Save ROVER output
            output.save_rover(page_name, rover_result.text)

            # Report
            contrib_str = ", ".join(
                f"{e}:{c}" for e, c in rover_result.engine_contributions.items()
                if c > 0
            )
            print(f"  ROVER: {len(rover_result.lines)} lines, gaps_filled={rover_result.gaps_filled}")
            print(f"  Contributions: {contrib_str}")

            all_results.append((page_name, rover_result))

    print(f"\n✅ ROVER OCR complete")
    print(f"  Raw outputs: {output.raw_dir}")
    print(f"  ROVER outputs: {output.rover_dir}")

    return all_results


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="ROVER OCR: Multi-engine voting for improved accuracy"
    )
    parser.add_argument("pages_dir", help="Directory containing page images")
    parser.add_argument("-o", "--output", default="ocr_output", help="Output directory")
    parser.add_argument(
        "--engines",
        default="yomitoku,paddleocr,easyocr",
        help="Comma-separated list of engines (Tesseract excluded by default)",
    )
    parser.add_argument(
        "--primary",
        default="yomitoku",
        help="Primary engine for baseline",
    )
    parser.add_argument(
        "--device",
        default="cpu",
        choices=["cpu", "cuda"],
        help="Device for Yomitoku",
    )
    parser.add_argument(
        "--min-agreement",
        type=int,
        default=2,
        help="Minimum engines that must agree",
    )
    args = parser.parse_args()

    engines = [e.strip() for e in args.engines.split(",")]

    run_rover_batch(
        pages_dir=args.pages_dir,
        output_dir=args.output,
        engines=engines,
        primary_engine=args.primary,
        device=args.device,
        min_agreement=args.min_agreement,
    )


if __name__ == "__main__":
    main()
