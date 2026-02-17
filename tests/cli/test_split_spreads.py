"""Tests for CLI split_spreads.

Phase 2 RED tests: CLIモジュールが存在しないため、全てFAILする想定。
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest


class TestSplitSpreadsCLI:
    """Test CLI entry point for split_spreads."""

    def test_module_runnable(self):
        """Verify module can be run with --help."""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.split_spreads", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()

    def test_help_shows_required_args(self):
        """Verify help text describes required arguments."""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.split_spreads", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        # PAGES_DIR is positional required arg
        assert "pages" in result.stdout.lower() or "dir" in result.stdout.lower()

    def test_help_shows_aspect_ratio_option(self):
        """Verify help text shows --aspect-ratio option."""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.split_spreads", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "--aspect-ratio" in result.stdout

    def test_help_shows_trim_options(self):
        """Verify help text shows trim options."""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.split_spreads", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "--left-trim" in result.stdout
        assert "--right-trim" in result.stdout

    def test_missing_input_shows_error(self):
        """Verify error message for missing input directory."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.split_spreads",
                "/nonexistent/pages_dir",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "error" in result.stderr.lower()

    def test_missing_positional_arg_shows_usage(self):
        """Verify missing positional argument shows usage."""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.split_spreads"],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "usage" in result.stderr.lower() or "required" in result.stderr.lower()
