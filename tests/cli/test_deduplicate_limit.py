"""Tests for --limit option on deduplicate CLI.

Phase 2 RED tests: --limit option is not yet implemented, so all tests should FAIL.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


class TestDeduplicateLimitOption:
    """Test --limit option for deduplicate CLI."""

    def test_help_shows_limit_option(self):
        """Verify --help includes --limit option description."""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.deduplicate", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "--limit" in result.stdout

    def test_limit_processes_only_n_files(self, tmp_path: Path):
        """--limit 3 should process only the first 3 frame files."""
        input_dir = tmp_path / "frames"
        input_dir.mkdir()
        output_dir = tmp_path / "output"

        # Create 5 dummy frame PNG files (1x1 pixel, all different names)
        for i in range(5):
            frame = input_dir / f"frame_{i:04d}.png"
            # Minimal valid PNG (1x1 white pixel)
            _write_minimal_png(frame)

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.deduplicate",
                str(input_dir),
                "-o",
                str(output_dir),
                "--limit",
                "3",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

        # Only 3 files should have been considered for processing
        # The stderr should indicate limiting
        assert "3" in result.stderr

    def test_no_limit_processes_all_files(self, tmp_path: Path):
        """Without --limit, all files should be processed."""
        input_dir = tmp_path / "frames"
        input_dir.mkdir()
        output_dir = tmp_path / "output"

        # Create 5 dummy frame PNG files
        for i in range(5):
            frame = input_dir / f"frame_{i:04d}.png"
            _write_minimal_png(frame)

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

        # Without --limit, no limiting message should appear
        assert "Limiting" not in result.stderr

    def test_limit_stderr_message(self, tmp_path: Path):
        """--limit should display processing count on stderr."""
        input_dir = tmp_path / "frames"
        input_dir.mkdir()
        output_dir = tmp_path / "output"

        for i in range(10):
            frame = input_dir / f"frame_{i:04d}.png"
            _write_minimal_png(frame)

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.deduplicate",
                str(input_dir),
                "-o",
                str(output_dir),
                "--limit",
                "3",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        # Should show message like "Processing first 3 of 10 files"
        assert "3" in result.stderr
        assert "10" in result.stderr


def _write_minimal_png(path: Path) -> None:
    """Write a minimal valid 1x1 white PNG file."""
    import struct
    import zlib

    # PNG signature
    signature = b"\x89PNG\r\n\x1a\n"

    # IHDR chunk: width=1, height=1, bit_depth=8, color_type=2 (RGB)
    ihdr_data = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    ihdr = _png_chunk(b"IHDR", ihdr_data)

    # IDAT chunk: raw image data (filter byte 0 + RGB white pixel)
    raw_data = b"\x00\xff\xff\xff"
    compressed = zlib.compress(raw_data)
    idat = _png_chunk(b"IDAT", compressed)

    # IEND chunk
    iend = _png_chunk(b"IEND", b"")

    path.write_bytes(signature + ihdr + idat + iend)


def _png_chunk(chunk_type: bytes, data: bytes) -> bytes:
    """Create a PNG chunk with CRC."""
    import struct
    import zlib

    chunk = chunk_type + data
    return struct.pack(">I", len(data)) + chunk + struct.pack(">I", zlib.crc32(chunk) & 0xFFFFFFFF)
