"""Tests for CLI detect_layout.

Phase 2 RED tests: CLIモジュールが存在しないため、全てFAILする想定。
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


class TestDetectLayoutCLI:
    """Test CLI entry point for detect_layout."""

    def test_module_runnable(self):
        """Verify module can be run with --help."""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.detect_layout", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()

    def test_help_shows_required_args(self):
        """Verify help text describes required arguments."""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.detect_layout", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        # PAGES_DIR is positional required arg
        assert "pages" in result.stdout.lower() or "dir" in result.stdout.lower()
        # -o/--output is required
        assert "-o" in result.stdout or "--output" in result.stdout

    def test_help_shows_device_option(self):
        """Verify help text shows --device option."""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.detect_layout", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "--device" in result.stdout

    def test_missing_input_shows_error(self, tmp_path: Path):
        """Verify error message for missing input directory."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.detect_layout",
                "/nonexistent/pages_dir",
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
            [sys.executable, "-m", "src.cli.detect_layout", "pages_dir"],
            capture_output=True,
            text=True,
        )
        # argparse should fail without -o
        assert result.returncode != 0

    def test_missing_positional_arg_shows_usage(self):
        """Verify missing positional argument shows usage."""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.detect_layout"],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "usage" in result.stderr.lower() or "required" in result.stderr.lower()
