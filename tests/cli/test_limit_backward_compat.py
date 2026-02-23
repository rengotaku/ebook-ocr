"""Tests for backward compatibility: CLIs work without --limit option.

Phase 3 RED tests (US2): Verify that all CLIs process all files when --limit
is not specified. These tests ensure backward compatibility is maintained.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


class TestDeduplicateBackwardCompat:
    """deduplicate CLI should process all files without --limit."""

    def test_deduplicate_without_limit_processes_all(self, tmp_path: Path):
        """Without --limit, deduplicate should process ALL frame files.

        Verifies FR-007: backward compatibility when --limit is omitted.
        Checks that the number of output pages corresponds to all unique
        input frames (no files silently skipped).
        """
        input_dir = tmp_path / "frames"
        input_dir.mkdir()
        output_dir = tmp_path / "output"

        # Create 5 distinct frame PNGs (different pixel data to avoid dedup)
        for i in range(5):
            frame = input_dir / f"frame_{i:04d}.png"
            _write_distinct_png(frame, color_r=i * 50)

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.deduplicate",
                str(input_dir),
                "-o",
                str(output_dir),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

        # No limiting message should appear in stderr
        assert "Processing first" not in result.stderr

        # All 5 distinct frames should produce output files
        output_files = sorted(output_dir.glob("*.png"))
        assert len(output_files) == 5, f"Expected 5 output files (all frames processed), got {len(output_files)}"


class TestDetectLayoutBackwardCompat:
    """detect_layout CLI should process all files without --limit."""

    def test_detect_layout_without_limit_processes_all(self, tmp_path: Path):
        """Without --limit, detect_layout should process ALL page files.

        Verifies FR-007: backward compatibility when --limit is omitted.
        Checks that no limiting message is printed and all pages are processed.
        """
        import json

        pages_dir = tmp_path / "pages"
        pages_dir.mkdir()
        output_dir = tmp_path / "output"

        # Create 5 page PNG files
        for i in range(5):
            page = pages_dir / f"page_{i:04d}.png"
            _write_distinct_png(page, color_r=i * 50)

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.detect_layout",
                str(pages_dir),
                "-o",
                str(output_dir),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

        # No limiting message should appear
        assert "Processing first" not in result.stderr

        # detect_layout outputs a single layout.json with all pages
        layout_json = output_dir / "layout.json"
        assert layout_json.exists(), "layout.json should be created"

        # Check that all 5 pages are in the layout data
        with open(layout_json) as f:
            layout_data = json.load(f)
        assert len(layout_data) == 5, f"Expected 5 pages in layout.json, got {len(layout_data)}"


class TestRunOcrBackwardCompat:
    """run_ocr CLI should process all files without --limit."""

    def test_run_ocr_without_limit_processes_all(self, tmp_path: Path):
        """Without --limit, run_ocr should process ALL page files.

        Verifies FR-007: backward compatibility when --limit is omitted.
        Checks that no limiting message is printed and all pages are processed.
        """
        pages_dir = tmp_path / "pages"
        pages_dir.mkdir()
        output_dir = tmp_path / "output"

        # Create 5 page PNG files
        for i in range(5):
            page = pages_dir / f"page_{i:04d}.png"
            _write_distinct_png(page, color_r=i * 50)

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.run_ocr",
                str(pages_dir),
                "-o",
                str(output_dir),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

        # No limiting message should appear
        assert "Processing first" not in result.stderr

        # All 5 pages should have OCR results in rover subdir
        rover_dir = output_dir / "rover"
        rover_files = sorted(rover_dir.glob("*.txt"))
        assert len(rover_files) == 5, f"Expected 5 OCR results (all pages processed), got {len(rover_files)}"


class TestConsolidateBackwardCompat:
    """consolidate CLI should process all files without --limit."""

    def test_consolidate_without_limit_processes_all(self, tmp_path: Path):
        """Without --limit, consolidate should process ALL OCR result files.

        Verifies FR-007: backward compatibility when --limit is omitted.
        Checks that no limiting message is printed and all results are consolidated.
        """
        # Structure: hashdir/ocr_output/rover/*.txt
        hashdir = tmp_path / "project"
        ocr_output_dir = hashdir / "ocr_output"
        rover_dir = ocr_output_dir / "rover"
        rover_dir.mkdir(parents=True)

        # Create 5 OCR result text files
        for i in range(5):
            txt_file = rover_dir / f"page_{i:04d}.txt"
            txt_file.write_text(f"Page {i} content line 1\nPage {i} content line 2\n")

        # CLI expects ocr_output_dir as first arg, hashdir as -o
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.consolidate",
                str(ocr_output_dir),
                "-o",
                str(hashdir),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

        # No limiting message should appear
        assert "Processing first" not in result.stderr

        # book.txt should contain all 5 pages (created in hashdir)
        book_txt = hashdir / "book.txt"
        assert book_txt.exists(), "book.txt should be created"
        content = book_txt.read_text()
        for i in range(5):
            assert f"Page {i} content" in content, f"book.txt should contain content from page {i}"


def _write_distinct_png(path: Path, *, color_r: int = 255) -> None:
    """Write a distinct PNG file that won't be detected as duplicate by perceptual hash.

    Creates a larger image with unique patterns to ensure perceptual hash differences.
    """
    from PIL import Image

    # Create a 16x16 image with a unique pattern based on color_r
    # This ensures perceptual hash will detect them as different
    img = Image.new("RGB", (16, 16))
    pixels = img.load()

    # Create a unique pattern for each image
    for y in range(16):
        for x in range(16):
            # Different patterns based on color_r to ensure hash differences
            if (x + y + color_r // 50) % 3 == 0:
                pixels[x, y] = (color_r & 0xFF, 0, 0)
            elif (x + y + color_r // 50) % 3 == 1:
                pixels[x, y] = (0, color_r & 0xFF, 0)
            else:
                pixels[x, y] = (0, 0, color_r & 0xFF)

    img.save(path)
