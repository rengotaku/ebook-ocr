"""Tests for CLI error handling across all commands.

Phase 2 RED tests: CLIモジュールが存在しないため、全てFAILする想定。
T020: 入力不存在時のエラーメッセージテスト
"""

from __future__ import annotations

import subprocess
import sys

import pytest


class TestCLIErrorHandling:
    """Test error handling behavior across all CLI commands."""

    @pytest.mark.parametrize(
        "module,args",
        [
            ("src.cli.extract_frames", ["/nonexistent/video.mp4", "-o", "/tmp/out"]),
            ("src.cli.deduplicate", ["/nonexistent/input", "-o", "/tmp/out"]),
            ("src.cli.split_spreads", ["/nonexistent/pages"]),
            ("src.cli.detect_layout", ["/nonexistent/pages", "-o", "/tmp/out"]),
            ("src.cli.run_ocr", ["/nonexistent/pages", "-o", "/tmp/out"]),
            ("src.cli.consolidate", ["/nonexistent/ocr", "-o", "/tmp/out"]),
        ],
    )
    def test_nonexistent_input_returns_exit_code_1(self, module: str, args: list[str]):
        """Verify all CLIs return exit code 1 for nonexistent input."""
        result = subprocess.run(
            [sys.executable, "-m", module] + args,
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1, (
            f"{module} should return exit code 1 for nonexistent input, "
            f"got {result.returncode}. stderr: {result.stderr}"
        )

    @pytest.mark.parametrize(
        "module,args",
        [
            ("src.cli.extract_frames", ["/nonexistent/video.mp4", "-o", "/tmp/out"]),
            ("src.cli.deduplicate", ["/nonexistent/input", "-o", "/tmp/out"]),
            ("src.cli.split_spreads", ["/nonexistent/pages"]),
            ("src.cli.detect_layout", ["/nonexistent/pages", "-o", "/tmp/out"]),
            ("src.cli.run_ocr", ["/nonexistent/pages", "-o", "/tmp/out"]),
            ("src.cli.consolidate", ["/nonexistent/ocr", "-o", "/tmp/out"]),
        ],
    )
    def test_nonexistent_input_shows_error_message(self, module: str, args: list[str]):
        """Verify all CLIs show error message to stderr for nonexistent input."""
        result = subprocess.run(
            [sys.executable, "-m", module] + args,
            capture_output=True,
            text=True,
        )
        assert "error" in result.stderr.lower(), (
            f"{module} should show 'error' in stderr for nonexistent input. stderr: {result.stderr}"
        )

    @pytest.mark.parametrize(
        "module",
        [
            "src.cli.extract_frames",
            "src.cli.deduplicate",
            "src.cli.split_spreads",
            "src.cli.detect_layout",
            "src.cli.run_ocr",
            "src.cli.consolidate",
        ],
    )
    def test_all_cli_modules_support_help(self, module: str):
        """Verify all CLI modules support --help flag."""
        result = subprocess.run(
            [sys.executable, "-m", module, "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0, (
            f"{module} --help should return 0, got {result.returncode}. stderr: {result.stderr}"
        )
        assert "usage" in result.stdout.lower(), f"{module} --help should show 'usage'. stdout: {result.stdout}"

    @pytest.mark.parametrize(
        "module",
        [
            "src.cli.extract_frames",
            "src.cli.deduplicate",
            "src.cli.split_spreads",
            "src.cli.detect_layout",
            "src.cli.run_ocr",
            "src.cli.consolidate",
        ],
    )
    def test_all_cli_modules_show_error_without_args(self, module: str):
        """Verify all CLI modules show error when called without arguments."""
        result = subprocess.run(
            [sys.executable, "-m", module],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0, f"{module} without args should fail. returncode: {result.returncode}"


class TestCLIExitCodes:
    """Test specific exit codes per CLI contract."""

    def test_extract_frames_exit_code_1_for_missing_input(self):
        """extract_frames: exit code 1 for missing input file."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.extract_frames",
                "/nonexistent/video.mp4",
                "-o",
                "/tmp/out",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1

    def test_deduplicate_exit_code_1_for_missing_input(self):
        """deduplicate: exit code 1 for missing input directory."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.deduplicate",
                "/nonexistent/input",
                "-o",
                "/tmp/out",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1

    def test_split_spreads_exit_code_1_for_missing_input(self):
        """split_spreads: exit code 1 for missing input directory."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.split_spreads",
                "/nonexistent/pages",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1

    def test_detect_layout_exit_code_1_for_missing_input(self):
        """detect_layout: exit code 1 for missing input directory."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.detect_layout",
                "/nonexistent/pages",
                "-o",
                "/tmp/out",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1

    def test_run_ocr_exit_code_1_for_missing_input(self):
        """run_ocr: exit code 1 for missing input directory."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.run_ocr",
                "/nonexistent/pages",
                "-o",
                "/tmp/out",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1

    def test_consolidate_exit_code_1_for_missing_input(self):
        """consolidate: exit code 1 for missing input directory."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.consolidate",
                "/nonexistent/ocr",
                "-o",
                "/tmp/out",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
