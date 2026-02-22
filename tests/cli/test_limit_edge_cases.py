"""Tests for --limit edge cases.

Phase 3 RED tests (US2): Verify edge case behaviors:
- --limit greater than actual file count should process all files (no error)
- --limit 1 should process exactly 1 file
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


class TestLimitGreaterThanFileCount:
    """When --limit exceeds file count, all files should be processed."""

    def test_deduplicate_limit_greater_than_file_count(self, tmp_path: Path):
        """--limit 100 with only 3 files should process all 3 files without error."""
        input_dir = tmp_path / "frames"
        input_dir.mkdir()
        output_dir = tmp_path / "output"

        for i in range(3):
            frame = input_dir / f"frame_{i:04d}.png"
            _write_distinct_png(frame, color_r=i * 80)

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.deduplicate",
                str(input_dir),
                "-o",
                str(output_dir),
                "--limit",
                "100",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Should not error when limit > file count. stderr: {result.stderr}"

        # All 3 files should be processed (not 100)
        output_files = sorted(output_dir.glob("*.png"))
        assert len(output_files) == 3, f"Expected 3 output files (all available), got {len(output_files)}"

    def test_detect_layout_limit_greater_than_file_count(self, tmp_path: Path):
        """--limit 100 with only 3 files should process all 3 files without error."""
        pages_dir = tmp_path / "pages"
        pages_dir.mkdir()
        output_dir = tmp_path / "output"

        for i in range(3):
            page = pages_dir / f"page_{i:04d}.png"
            _write_distinct_png(page, color_r=i * 80)

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.detect_layout",
                str(pages_dir),
                "-o",
                str(output_dir),
                "--limit",
                "100",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Should not error when limit > file count. stderr: {result.stderr}"

        # All 3 pages should have layout results
        output_files = sorted(output_dir.glob("*.json"))
        assert len(output_files) == 3, f"Expected 3 layout results (all available), got {len(output_files)}"

    def test_run_ocr_limit_greater_than_file_count(self, tmp_path: Path):
        """--limit 100 with only 3 files should process all 3 files without error."""
        pages_dir = tmp_path / "pages"
        pages_dir.mkdir()
        output_dir = tmp_path / "output"

        for i in range(3):
            page = pages_dir / f"page_{i:04d}.png"
            _write_distinct_png(page, color_r=i * 80)

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.run_ocr",
                str(pages_dir),
                "-o",
                str(output_dir),
                "--limit",
                "100",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Should not error when limit > file count. stderr: {result.stderr}"

        # All 3 pages should have OCR results
        rover_dir = output_dir / "rover"
        rover_files = sorted(rover_dir.glob("*.txt"))
        assert len(rover_files) == 3, f"Expected 3 OCR results (all available), got {len(rover_files)}"

    def test_consolidate_limit_greater_than_file_count(self, tmp_path: Path):
        """--limit 100 with only 3 files should process all 3 files without error."""
        project_dir = tmp_path / "project"
        ocr_output = project_dir / "ocr_output" / "rover"
        ocr_output.mkdir(parents=True)
        output_dir = tmp_path / "output"

        for i in range(3):
            txt_file = ocr_output / f"page_{i:04d}.txt"
            txt_file.write_text(f"Page {i} content\n")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.consolidate",
                str(project_dir),
                "-o",
                str(output_dir),
                "--limit",
                "100",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, f"Should not error when limit > file count. stderr: {result.stderr}"

        # book.txt should contain all 3 pages
        book_txt = project_dir / "book.txt"
        assert book_txt.exists(), "book.txt should be created"
        content = book_txt.read_text()
        for i in range(3):
            assert f"Page {i} content" in content, f"book.txt should contain content from page {i}"


class TestLimitOneFile:
    """--limit 1 should process exactly one file (minimum unit)."""

    def test_deduplicate_limit_one_file(self, tmp_path: Path):
        """--limit 1 should process exactly the first frame file."""
        input_dir = tmp_path / "frames"
        input_dir.mkdir()
        output_dir = tmp_path / "output"

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
                "--limit",
                "1",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

        # Exactly 1 output file should exist
        output_files = sorted(output_dir.glob("*.png"))
        assert len(output_files) == 1, f"Expected exactly 1 output file, got {len(output_files)}"

        # stderr should indicate limiting
        assert "1" in result.stderr
        assert "5" in result.stderr

    def test_consolidate_limit_one_file(self, tmp_path: Path):
        """--limit 1 should consolidate exactly the first OCR result file."""
        project_dir = tmp_path / "project"
        ocr_output = project_dir / "ocr_output" / "rover"
        ocr_output.mkdir(parents=True)
        output_dir = tmp_path / "output"

        for i in range(5):
            txt_file = ocr_output / f"page_{i:04d}.txt"
            txt_file.write_text(f"Page {i} unique content\n")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.consolidate",
                str(project_dir),
                "-o",
                str(output_dir),
                "--limit",
                "1",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

        # book.txt should contain only page 0 content
        book_txt = project_dir / "book.txt"
        assert book_txt.exists(), "book.txt should be created"
        content = book_txt.read_text()
        assert "Page 0 unique content" in content, "book.txt should contain page 0 content"
        # Page 1-4 content should NOT be present
        assert "Page 1 unique content" not in content, "book.txt should NOT contain page 1 content when --limit 1"


def _write_distinct_png(path: Path, *, color_r: int = 255) -> None:
    """Write a minimal valid 1x1 PNG file with a distinct color."""
    import struct
    import zlib

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    ihdr = _png_chunk(b"IHDR", ihdr_data)
    raw_data = b"\x00" + bytes([color_r & 0xFF, 0x00, 0xFF])
    compressed = zlib.compress(raw_data)
    idat = _png_chunk(b"IDAT", compressed)
    iend = _png_chunk(b"IEND", b"")
    path.write_bytes(signature + ihdr + idat + iend)


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    """Create a PNG chunk with CRC."""
    import struct
    import zlib

    chunk = chunk_type + data
    return struct.pack(">I", len(data)) + chunk + struct.pack(">I", zlib.crc32(chunk) & 0xFFFFFFFF)
