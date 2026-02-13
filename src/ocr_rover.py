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
from difflib import SequenceMatcher
from pathlib import Path

from PIL import Image

from ocr_engines import EngineResult, TextWithBox, run_all_engines
from ocr_output import ROVEROutput


# Engine priority weights for voting
ENGINE_WEIGHTS = {
    "yomitoku": 1.5,    # Best for Japanese
    "paddleocr": 1.2,   # High accuracy
    "easyocr": 1.0,     # Balanced
    "tesseract": 0.8,   # Basic but useful
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


def calculate_text_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts.

    Args:
        text1: First text.
        text2: Second text.

    Returns:
        Similarity ratio (0.0 - 1.0).
    """
    if not text1 and not text2:
        return 1.0
    if not text1 or not text2:
        return 0.0
    return SequenceMatcher(None, text1, text2).ratio()


def vote_line_text(
    aligned_line: AlignedLine,
    engine_weights: dict[str, float] | None = None,
    min_agreement: int = 2,
) -> tuple[str, list[str]]:
    """Vote for best text from aligned lines.

    Args:
        aligned_line: Aligned line with multiple engine results.
        engine_weights: Weight for each engine (higher = more trusted).
        min_agreement: Minimum number of engines that must agree.

    Returns:
        Tuple of (voted_text, source_engines).
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
        return "", []

    # Single engine case
    if len(valid_lines) == 1:
        engine, line = list(valid_lines.items())[0]
        return line.text, [engine]

    # Calculate weighted votes
    texts = {engine: line.text for engine, line in valid_lines.items()}
    text_votes: dict[str, float] = {}
    text_engines: dict[str, list[str]] = {}

    for engine, text in texts.items():
        # Find similar texts
        similar_count = sum(
            1 for other_text in texts.values()
            if calculate_text_similarity(text, other_text) >= 0.8
        )

        if similar_count >= min_agreement or len(valid_lines) < min_agreement:
            weight = engine_weights.get(engine, 1.0) * (1 + valid_lines[engine].confidence)
            if text in text_votes:
                text_votes[text] += weight
                text_engines[text].append(engine)
            else:
                text_votes[text] = weight
                text_engines[text] = [engine]

    if not text_votes:
        # No agreement - use highest priority engine
        priority = ["yomitoku", "paddleocr", "easyocr", "tesseract"]
        for engine in priority:
            if engine in valid_lines:
                return valid_lines[engine].text, [engine]

    # Return text with highest vote
    best_text = max(text_votes.items(), key=lambda x: x[1])[0]
    return best_text, text_engines[best_text]


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
    # Convert to line-based structure
    lines_by_engine: dict[str, list[OCRLine]] = {}
    for engine, result in engine_results.items():
        if result.success and result.items:
            lines = cluster_lines_by_y(result.items)
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
        voted_text, source_engines = vote_line_text(aligned_line, min_agreement=min_agreement)
        aligned_line.voted_text = voted_text
        aligned_line.source_engines = source_engines

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
    yomitoku_device: str = "cpu",
    min_agreement: int = 2,
) -> ROVERResult:
    """Run ROVER OCR on a single image.

    Args:
        image: PIL Image or path to image file.
        engines: List of engine names to use.
        primary_engine: Primary engine (for gap detection).
        yomitoku_device: Device for Yomitoku.
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
        yomitoku_device=yomitoku_device,
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
    yomitoku_device: str = "cpu",
    min_agreement: int = 2,
) -> list[tuple[str, ROVERResult]]:
    """Run ROVER OCR on all pages in a directory.

    Args:
        pages_dir: Directory containing page images.
        output_dir: Directory for output files.
        engines: List of engine names to use.
        primary_engine: Primary engine.
        yomitoku_device: Device for Yomitoku.
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
                yomitoku_device=yomitoku_device,
            )

            # Save raw outputs
            for engine, result in engine_results.items():
                if result.success:
                    output.save_raw(engine, page_name, result.text)
                    print(f"  {engine}: {len(result.items)} items")
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
        default="yomitoku,paddleocr,easyocr,tesseract",
        help="Comma-separated list of engines",
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
        yomitoku_device=args.device,
        min_agreement=args.min_agreement,
    )


if __name__ == "__main__":
    main()
