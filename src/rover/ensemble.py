"""ROVER (Recognizer Output Voting Error Reduction) for OCR.

Combines multiple OCR engine outputs using voting and alignment
to produce higher quality results than any single engine.

Strategy:
1. Line-level alignment by y-coordinate
2. Token-level voting within aligned lines
3. Gap detection and filling from secondary engines
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from src.rover.alignment import align_texts_character_level, vote_aligned_text
from src.rover.engines import EngineResult, run_all_engines
from src.rover.line_processing import (
    AlignedLine,
    OCRLine,
    align_lines_by_y,
    cluster_lines_by_y,
    is_garbage,
    normalize_confidence,
)
from src.rover.output import ROVEROutput

# Engine priority weights for voting (Tesseract excluded from ROVER)
ENGINE_WEIGHTS = {
    "yomitoku": 1.5,  # Best for Japanese
    "paddleocr": 1.2,  # High accuracy
    "easyocr": 1.0,  # Balanced
}


@dataclass
class ROVERResult:
    """ROVER processing result."""

    text: str
    lines: list[str]
    aligned: list[AlignedLine]
    engine_contributions: dict[str, int]
    gaps_filled: int = 0


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
    valid_lines = {engine: line for engine, line in aligned_line.lines.items() if line is not None}

    if not valid_lines:
        return "", [], 0.0

    # Single engine case
    if len(valid_lines) == 1:
        engine, line = list(valid_lines.items())[0]
        return line.text, [engine], line.confidence

    # Character-level alignment and voting (Phase 3: True ROVER)
    texts = {engine: line.text for engine, line in valid_lines.items()}
    confidences = {engine: normalize_confidence(line.confidence, engine) for engine, line in valid_lines.items()}

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
            filtered_items = [item for item in result.items if not is_garbage(item.text, item.confidence)]
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
            contrib_str = ", ".join(f"{e}:{c}" for e, c in rover_result.engine_contributions.items() if c > 0)
            print(f"  ROVER: {len(rover_result.lines)} lines, gaps_filled={rover_result.gaps_filled}")
            print(f"  Contributions: {contrib_str}")

            all_results.append((page_name, rover_result))

    print("\n✅ ROVER OCR complete")
    print(f"  Raw outputs: {output.raw_dir}")
    print(f"  ROVER outputs: {output.rover_dir}")

    return all_results


def main() -> None:
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="ROVER OCR: Multi-engine voting for improved accuracy")
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
