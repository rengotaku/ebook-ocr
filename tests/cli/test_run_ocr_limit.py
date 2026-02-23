"""Tests for --limit option on run_ocr CLI.

Phase 2 RED tests: --limit option is not yet implemented, so all tests should FAIL.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


class TestRunOcrLimitOption:
    """Test --limit option for run_ocr CLI."""

    def test_help_shows_limit_option(self):
        """Verify --help includes --limit option description."""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.run_ocr", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "--limit" in result.stdout

    def test_limit_processes_only_n_pages(self, tmp_path: Path):
        """--limit 3 should process only the first 3 page files."""
        pages_dir = tmp_path / "pages"
        pages_dir.mkdir()
        output_dir = tmp_path / "output"

        # Create 5 dummy page PNG files
        for i in range(5):
            page = pages_dir / f"page_{i:04d}.png"
            _write_minimal_png(page)

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.run_ocr",
                str(pages_dir),
                "-o",
                str(output_dir),
                "--limit",
                "3",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

        # The stderr should indicate limiting to 3 files
        assert "3" in result.stderr

    def test_no_limit_processes_all_pages(self, tmp_path: Path):
        """Without --limit, all pages should be processed."""
        pages_dir = tmp_path / "pages"
        pages_dir.mkdir()
        output_dir = tmp_path / "output"

        # Create 5 dummy page PNG files
        for i in range(5):
            page = pages_dir / f"page_{i:04d}.png"
            _write_minimal_png(page)

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

        # Without --limit, no limiting message should appear
        assert "Limiting" not in result.stderr


def _write_minimal_png(path: Path) -> None:
    """Write a minimal valid 1x1 white PNG file."""
    import struct
    import zlib

    signature = b"\x89PNG\r\n\x1a\n"
    ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    ihdr = _png_chunk(b"IHDR", ihdr_data)
    raw_data = b"\x00\xff\xff\xff"
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
