"""Quick test for ROVER OCR implementation."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from ocr_engines import EngineResult, TextWithBox
from ocr_rover import (
    AlignedLine,
    OCRLine,
    align_lines_by_y,
    cluster_lines_by_y,
    rover_merge,
    vote_line_text,
)


def test_cluster_lines():
    """Test line clustering by y-coordinate."""
    print("Testing line clustering...")

    items = [
        TextWithBox("Hello", (10, 100, 100, 120), 0.9),
        TextWithBox("World", (110, 102, 200, 122), 0.9),
        TextWithBox("Next", (10, 200, 100, 220), 0.8),
        TextWithBox("Line", (110, 198, 200, 218), 0.8),
    ]

    lines = cluster_lines_by_y(items, y_tolerance=20)

    assert len(lines) == 2, f"Expected 2 lines, got {len(lines)}"
    assert len(lines[0].items) == 2, "Expected 2 items in first line"
    assert lines[0].text == "HelloWorld"
    assert lines[1].text == "NextLine"

    print("  ✅ Line clustering works")


def test_align_lines():
    """Test line alignment across engines."""
    print("Testing line alignment...")

    # Create mock lines for two engines
    lines_by_engine = {
        "engine1": [
            OCRLine(
                items=[TextWithBox("Line 1", (10, 100, 100, 120), 0.9)],
                engine="engine1",
                y_center=110.0,
                confidence=0.9,
            ),
            OCRLine(
                items=[TextWithBox("Line 2", (10, 200, 100, 220), 0.8)],
                engine="engine1",
                y_center=210.0,
                confidence=0.8,
            ),
        ],
        "engine2": [
            OCRLine(
                items=[TextWithBox("Line 1", (10, 105, 100, 125), 0.85)],
                engine="engine2",
                y_center=115.0,
                confidence=0.85,
            ),
            OCRLine(
                items=[TextWithBox("Line 2", (10, 202, 100, 222), 0.75)],
                engine="engine2",
                y_center=212.0,
                confidence=0.75,
            ),
        ],
    }

    aligned = align_lines_by_y(lines_by_engine, y_tolerance=30)

    assert len(aligned) == 2, f"Expected 2 aligned lines, got {len(aligned)}"
    assert "engine1" in aligned[0].lines
    assert "engine2" in aligned[0].lines

    print("  ✅ Line alignment works")


def test_vote_line_text():
    """Test voting for best text."""
    print("Testing text voting...")

    # Create aligned line with agreement
    aligned_line = AlignedLine(
        lines={
            "yomitoku": OCRLine(
                items=[TextWithBox("テスト文章", (10, 100, 100, 120), 0.9)],
                engine="yomitoku",
                y_center=110.0,
                confidence=0.9,
            ),
            "paddleocr": OCRLine(
                items=[TextWithBox("テスト文章", (10, 105, 100, 125), 0.85)],
                engine="paddleocr",
                y_center=112.0,
                confidence=0.85,
            ),
            "easyocr": OCRLine(
                items=[TextWithBox("テスト文章", (10, 103, 100, 123), 0.8)],
                engine="easyocr",
                y_center=111.0,
                confidence=0.8,
            ),
        },
        y_center=111.0,
    )

    voted_text, source_engines = vote_line_text(aligned_line, min_agreement=2)

    assert voted_text == "テスト文章"
    assert len(source_engines) >= 2

    print("  ✅ Text voting works")


def test_rover_merge():
    """Test complete ROVER merge."""
    print("Testing ROVER merge...")

    # Create mock engine results
    engine_results = {
        "yomitoku": EngineResult(
            engine="yomitoku",
            items=[
                TextWithBox("第一行", (10, 100, 100, 120), 0.9),
                TextWithBox("第二行", (10, 200, 100, 220), 0.85),
            ],
            success=True,
        ),
        "paddleocr": EngineResult(
            engine="paddleocr",
            items=[
                TextWithBox("第一行", (10, 102, 100, 122), 0.88),
                TextWithBox("第二行", (10, 202, 100, 222), 0.82),
                TextWithBox("第三行", (10, 300, 100, 320), 0.75),  # Extra line
            ],
            success=True,
        ),
    }

    result = rover_merge(engine_results, min_agreement=1)

    assert result.text != ""
    assert len(result.lines) >= 2
    assert result.engine_contributions["yomitoku"] > 0

    print("  ✅ ROVER merge works")
    print(f"    Lines: {len(result.lines)}")
    print(f"    Contributions: {result.engine_contributions}")


def main():
    """Run all tests."""
    print("\n🧪 ROVER OCR Unit Tests\n")

    try:
        test_cluster_lines()
        test_align_lines()
        test_vote_line_text()
        test_rover_merge()

        print("\n✅ All tests passed!\n")
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
