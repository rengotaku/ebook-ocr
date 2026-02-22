"""Tests for --limit validation error handling.

Phase 4 RED tests (US3): Verify that invalid --limit values are rejected:
- --limit 0 should show error and exit with non-zero returncode
- --limit -5 should show error and exit with non-zero returncode
- --limit abc should trigger argparse type error
"""

from __future__ import annotations

import subprocess
import sys

import pytest

# All 4 CLI modules to test
CLI_MODULES = [
    "src.cli.deduplicate",
    "src.cli.detect_layout",
    "src.cli.run_ocr",
    "src.cli.consolidate",
]


class TestLimitZeroReturnsError:
    """--limit 0 should display an error message and exit with non-zero returncode."""

    @pytest.mark.parametrize("module", CLI_MODULES)
    def test_limit_zero_returns_error(self, module: str, tmp_path):
        """--limit 0 should be rejected as invalid for all CLI commands."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_dir = tmp_path / "output"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                module,
                str(input_dir),
                "-o",
                str(output_dir),
                "--limit",
                "0",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0, (
            f"[{module}] --limit 0 should return non-zero exit code, got returncode={result.returncode}"
        )
        # Error message should mention the invalid value
        combined_output = result.stdout + result.stderr
        assert "0" in combined_output or "positive" in combined_output.lower(), (
            f"[{module}] Error output should mention the invalid value or 'positive'. "
            f"stdout: {result.stdout!r}, stderr: {result.stderr!r}"
        )


class TestLimitNegativeReturnsError:
    """--limit with negative values should display an error and exit with non-zero returncode."""

    @pytest.mark.parametrize("module", CLI_MODULES)
    def test_limit_negative_returns_error(self, module: str, tmp_path):
        """--limit -5 should be rejected as invalid for all CLI commands."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_dir = tmp_path / "output"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                module,
                str(input_dir),
                "-o",
                str(output_dir),
                "--limit",
                "-5",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0, (
            f"[{module}] --limit -5 should return non-zero exit code, got returncode={result.returncode}"
        )
        # Error message should indicate the value is invalid
        combined_output = result.stdout + result.stderr
        assert "-5" in combined_output or "positive" in combined_output.lower(), (
            f"[{module}] Error output should mention '-5' or 'positive'. "
            f"stdout: {result.stdout!r}, stderr: {result.stderr!r}"
        )


class TestLimitNonIntegerArgparseError:
    """--limit with non-integer value should trigger argparse type error."""

    @pytest.mark.parametrize("module", CLI_MODULES)
    def test_limit_non_integer_argparse_error(self, module: str, tmp_path):
        """--limit abc should be rejected by argparse with a type error."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        output_dir = tmp_path / "output"

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                module,
                str(input_dir),
                "-o",
                str(output_dir),
                "--limit",
                "abc",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0, (
            f"[{module}] --limit abc should return non-zero exit code, got returncode={result.returncode}"
        )
        # argparse should mention "invalid int value"
        assert "invalid" in result.stderr.lower(), (
            f"[{module}] argparse should report 'invalid int value'. stderr: {result.stderr!r}"
        )
