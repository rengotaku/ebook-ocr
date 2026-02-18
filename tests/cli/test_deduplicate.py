"""Tests for CLI deduplicate.

Phase 2 RED tests: CLIモジュールが存在しないため、全てFAILする想定。
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


class TestDeduplicateCLI:
    """Test CLI entry point for deduplicate."""

    def test_module_runnable(self):
        """Verify module can be run with --help."""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.deduplicate", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()

    def test_help_shows_required_args(self):
        """Verify help text describes required arguments."""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.deduplicate", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        # INPUT_DIR is positional required arg
        assert "input" in result.stdout.lower() or "dir" in result.stdout.lower()
        # -o/--output is required
        assert "-o" in result.stdout or "--output" in result.stdout

    def test_help_shows_threshold_option(self):
        """Verify help text shows -t/--threshold option."""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.deduplicate", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "-t" in result.stdout or "--threshold" in result.stdout

    def test_missing_input_shows_error(self, tmp_path: Path):
        """Verify error message for missing input directory."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.deduplicate",
                "/nonexistent/input_dir",
                "-o",
                str(tmp_path / "output"),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "error" in result.stderr.lower()

    def test_empty_input_dir_shows_error(self, tmp_path: Path):
        """Verify error message for empty input directory."""
        empty_dir = tmp_path / "empty_input"
        empty_dir.mkdir()
        output_dir = tmp_path / "output"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.deduplicate",
                str(empty_dir),
                "-o",
                str(output_dir),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "error" in result.stderr.lower()

    def test_requires_output_arg(self):
        """Verify -o/--output is required."""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.deduplicate", "input_dir"],
            capture_output=True,
            text=True,
        )
        # argparse should fail without -o
        assert result.returncode != 0

    def test_missing_positional_arg_shows_usage(self):
        """Verify missing positional argument shows usage."""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.deduplicate"],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "usage" in result.stderr.lower() or "required" in result.stderr.lower()
