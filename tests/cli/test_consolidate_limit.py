"""Tests for --limit option on consolidate CLI.

Phase 2 RED tests: --limit option is not yet implemented, so all tests should FAIL.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


class TestConsolidateLimitOption:
    """Test --limit option for consolidate CLI."""

    def test_help_shows_limit_option(self):
        """Verify --help includes --limit option description."""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.consolidate", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "--limit" in result.stdout

    def test_limit_processes_only_n_files(self, tmp_path: Path):
        """--limit 3 should process only the first 3 OCR result files."""
        ocr_dir = tmp_path / "project"
        ocr_output = ocr_dir / "ocr_output" / "rover"
        ocr_output.mkdir(parents=True)
        output_dir = tmp_path / "output"

        # Create 5 dummy OCR result text files
        for i in range(5):
            txt_file = ocr_output / f"page_{i:04d}.txt"
            txt_file.write_text(f"OCR result for page {i}")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.consolidate",
                str(ocr_dir),
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

    def test_no_limit_processes_all_files(self, tmp_path: Path):
        """Without --limit, all OCR result files should be processed."""
        ocr_dir = tmp_path / "project"
        ocr_output = ocr_dir / "ocr_output" / "rover"
        ocr_output.mkdir(parents=True)
        output_dir = tmp_path / "output"

        # Create 5 dummy OCR result text files
        for i in range(5):
            txt_file = ocr_output / f"page_{i:04d}.txt"
            txt_file.write_text(f"OCR result for page {i}")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.consolidate",
                str(ocr_dir),
                "-o",
                str(output_dir),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0

        # Without --limit, no limiting message should appear
        assert "Limiting" not in result.stderr
