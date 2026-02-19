"""Tests for CLI extract_frames.

Phase 2 RED tests: CLIモジュールが存在しないため、全てFAILする想定。
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


class TestExtractFramesCLI:
    """Test CLI entry point for extract_frames."""

    def test_module_runnable(self):
        """Verify module can be run with --help."""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.extract_frames", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()

    def test_help_shows_required_args(self):
        """Verify help text describes required arguments."""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.extract_frames", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        # VIDEO_PATH is positional required arg
        assert "video" in result.stdout.lower() or "input" in result.stdout.lower()
        # -o/--output is required
        assert "-o" in result.stdout or "--output" in result.stdout

    def test_help_shows_interval_option(self):
        """Verify help text shows -i/--interval option."""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.extract_frames", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "-i" in result.stdout or "--interval" in result.stdout

    def test_missing_input_shows_error(self, tmp_path: Path):
        """Verify error message for missing input video file."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.extract_frames",
                "/nonexistent/video.mp4",
                "-o",
                str(tmp_path / "output"),
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "error" in result.stderr.lower()

    def test_requires_output_arg(self):
        """Verify -o/--output is required."""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.extract_frames", "input.mp4"],
            capture_output=True,
            text=True,
        )
        # argparse should fail without -o
        assert result.returncode != 0

    def test_missing_positional_arg_shows_usage(self):
        """Verify missing positional argument shows usage."""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.extract_frames"],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        # argparse shows usage on missing required args
        assert "usage" in result.stderr.lower() or "required" in result.stderr.lower()
