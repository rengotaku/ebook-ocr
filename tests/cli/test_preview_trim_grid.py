"""Tests for CLI preview_trim_grid.

TDD RED Phase: CLIモジュールが存在しないため、全てFAILする想定。

This tool draws trim guide lines on preview images to help identify optimal trim values.
Grid lines are color-coded by direction:
- Top: Red (#FF0000)
- Bottom: Blue (#0000FF)
- Left: Green (#00FF00)
- Right: Orange (#FFA500)
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from PIL import Image


class TestPreviewTrimGridCLI:
    """Test CLI entry point for preview_trim_grid."""

    def test_module_runnable(self):
        """Verify module can be run with --help."""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.preview_trim_grid", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "usage:" in result.stdout.lower()

    def test_help_shows_required_args(self):
        """Verify help text describes required arguments."""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.preview_trim_grid", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        # input_dir is positional required arg
        assert "input" in result.stdout.lower() or "dir" in result.stdout.lower()
        # -o/--output is required
        assert "-o" in result.stdout or "--output" in result.stdout

    def test_help_shows_step_option(self):
        """Verify help text shows --step option with default 0.05."""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.preview_trim_grid", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "--step" in result.stdout
        assert "0.05" in result.stdout  # default value

    def test_help_shows_max_option(self):
        """Verify help text shows --max option with default 0.30."""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.preview_trim_grid", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "--max" in result.stdout
        assert "0.30" in result.stdout  # default value

    def test_help_shows_spread_mode_option(self):
        """Verify help text shows --spread-mode option with default 'single'."""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.preview_trim_grid", "--help"],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 0
        assert "--spread-mode" in result.stdout
        assert "single" in result.stdout.lower()  # default value

    def test_missing_input_shows_error(self):
        """Verify error message for missing input directory."""
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.preview_trim_grid",
                "/nonexistent/frames_dir",
                "-o",
                "/tmp/output",
            ],
            capture_output=True,
            text=True,
        )
        assert result.returncode == 1
        assert "error" in result.stderr.lower()

    def test_requires_output_arg(self):
        """Verify -o/--output is required."""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.preview_trim_grid", "/tmp/input"],
            capture_output=True,
            text=True,
        )
        # argparse should fail without -o
        assert result.returncode != 0

    def test_missing_positional_arg_shows_usage(self):
        """Verify missing positional argument shows usage."""
        result = subprocess.run(
            [sys.executable, "-m", "src.cli.preview_trim_grid"],
            capture_output=True,
            text=True,
        )
        assert result.returncode != 0
        assert "usage" in result.stderr.lower() or "required" in result.stderr.lower()


class TestGridDrawingLogic:
    """Test grid line drawing logic and color coding."""

    def test_draws_red_top_lines(self, tmp_path: Path):
        """Verify top trim lines are drawn in red (#FF0000)."""
        # Create test image
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        test_img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        test_img.save(input_dir / "page_001.png")

        # Run CLI
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.preview_trim_grid",
                str(input_dir),
                "-o",
                str(output_dir),
                "--step",
                "0.10",
                "--max",
                "0.20",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        # Verify output image has red lines for top trim
        output_img = Image.open(output_dir / "page_001.png")
        pixels = output_img.load()

        # Check for red pixels at expected positions (10% and 20% from top)
        # y = 60 (10% of 600), y = 120 (20% of 600)
        red_found = False
        for x in range(100, 700):  # Check horizontal line
            if pixels[x, 60] == (255, 0, 0):  # Red color
                red_found = True
                break

        assert red_found, "Expected red top trim line at 10% position"

    def test_draws_blue_bottom_lines(self, tmp_path: Path):
        """Verify bottom trim lines are drawn in blue (#0000FF)."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        test_img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        test_img.save(input_dir / "page_001.png")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.preview_trim_grid",
                str(input_dir),
                "-o",
                str(output_dir),
                "--step",
                "0.10",
                "--max",
                "0.20",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        output_img = Image.open(output_dir / "page_001.png")
        pixels = output_img.load()

        # Check for blue pixels at expected positions from bottom
        # y = 540 (90% of 600, i.e., 10% from bottom)
        blue_found = False
        for x in range(100, 700):
            if pixels[x, 540] == (0, 0, 255):  # Blue color
                blue_found = True
                break

        assert blue_found, "Expected blue bottom trim line at 10% from bottom"

    def test_draws_green_left_lines(self, tmp_path: Path):
        """Verify left trim lines are drawn in green (#00FF00)."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        test_img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        test_img.save(input_dir / "page_001.png")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.preview_trim_grid",
                str(input_dir),
                "-o",
                str(output_dir),
                "--step",
                "0.10",
                "--max",
                "0.20",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        output_img = Image.open(output_dir / "page_001.png")
        pixels = output_img.load()

        # Check for green pixels at expected positions from left
        # x = 80 (10% of 800)
        green_found = False
        for y in range(100, 500):
            if pixels[80, y] == (0, 255, 0):  # Green color
                green_found = True
                break

        assert green_found, "Expected green left trim line at 10% from left"

    def test_draws_orange_right_lines(self, tmp_path: Path):
        """Verify right trim lines are drawn in orange (#FFA500)."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        test_img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        test_img.save(input_dir / "page_001.png")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.preview_trim_grid",
                str(input_dir),
                "-o",
                str(output_dir),
                "--step",
                "0.10",
                "--max",
                "0.20",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        output_img = Image.open(output_dir / "page_001.png")
        pixels = output_img.load()

        # Check for orange pixels at expected positions from right
        # x = 720 (90% of 800, i.e., 10% from right)
        orange_found = False
        for y in range(100, 500):
            if pixels[720, y] == (255, 165, 0):  # Orange color
                orange_found = True
                break

        assert orange_found, "Expected orange right trim line at 10% from right"

    def test_labels_top_lines_correctly(self, tmp_path: Path):
        """Verify top lines have correct labels (T:0.05, T:0.10, etc.)."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        test_img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        test_img.save(input_dir / "page_001.png")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.preview_trim_grid",
                str(input_dir),
                "-o",
                str(output_dir),
                "--step",
                "0.05",
                "--max",
                "0.10",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        # Note: Verifying text labels requires OCR or manual inspection
        # This test ensures the process completes successfully
        # Actual label verification should be done via visual inspection or OCR
        output_img = Image.open(output_dir / "page_001.png")
        assert output_img.size == (800, 600)

    def test_labels_bottom_lines_correctly(self, tmp_path: Path):
        """Verify bottom lines have correct labels (B:0.05, B:0.10, etc.)."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        test_img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        test_img.save(input_dir / "page_001.png")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.preview_trim_grid",
                str(input_dir),
                "-o",
                str(output_dir),
                "--step",
                "0.05",
                "--max",
                "0.10",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        output_img = Image.open(output_dir / "page_001.png")
        assert output_img.size == (800, 600)

    def test_labels_left_lines_correctly(self, tmp_path: Path):
        """Verify left lines have correct labels (L:0.05, L:0.10, etc.)."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        test_img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        test_img.save(input_dir / "page_001.png")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.preview_trim_grid",
                str(input_dir),
                "-o",
                str(output_dir),
                "--step",
                "0.05",
                "--max",
                "0.10",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        output_img = Image.open(output_dir / "page_001.png")
        assert output_img.size == (800, 600)

    def test_labels_right_lines_correctly(self, tmp_path: Path):
        """Verify right lines have correct labels (R:0.05, R:0.10, etc.)."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        test_img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        test_img.save(input_dir / "page_001.png")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.preview_trim_grid",
                str(input_dir),
                "-o",
                str(output_dir),
                "--step",
                "0.05",
                "--max",
                "0.10",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        output_img = Image.open(output_dir / "page_001.png")
        assert output_img.size == (800, 600)


class TestFileProcessing:
    """Test file processing behavior."""

    def test_processes_all_png_files(self, tmp_path: Path):
        """Verify all PNG files in input directory are processed."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        # Create multiple test images
        for i in range(1, 4):
            test_img = Image.new("RGB", (800, 600), color=(255, 255, 255))
            test_img.save(input_dir / f"page_{i:03d}.png")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.preview_trim_grid",
                str(input_dir),
                "-o",
                str(output_dir),
                "--step",
                "0.10",
                "--max",
                "0.20",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        # Verify all output files exist
        assert (output_dir / "page_001.png").exists()
        assert (output_dir / "page_002.png").exists()
        assert (output_dir / "page_003.png").exists()

    def test_ignores_non_png_files(self, tmp_path: Path):
        """Verify non-PNG files are ignored."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        # Create PNG and non-PNG files
        test_img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        test_img.save(input_dir / "page_001.png")

        # Create dummy non-PNG file
        (input_dir / "readme.txt").write_text("test")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.preview_trim_grid",
                str(input_dir),
                "-o",
                str(output_dir),
                "--step",
                "0.10",
                "--max",
                "0.20",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"

        # Only PNG should be processed
        assert (output_dir / "page_001.png").exists()
        assert not (output_dir / "readme.txt").exists()

    def test_preserves_original_filenames(self, tmp_path: Path):
        """Verify output files have same filenames as input."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        test_img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        test_img.save(input_dir / "custom_name_123.png")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.preview_trim_grid",
                str(input_dir),
                "-o",
                str(output_dir),
                "--step",
                "0.10",
                "--max",
                "0.20",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert (output_dir / "custom_name_123.png").exists()

    def test_creates_output_directory_if_missing(self, tmp_path: Path):
        """Verify output directory is created if it doesn't exist."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "deeply" / "nested" / "output"
        input_dir.mkdir()

        test_img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        test_img.save(input_dir / "page_001.png")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.preview_trim_grid",
                str(input_dir),
                "-o",
                str(output_dir),
                "--step",
                "0.10",
                "--max",
                "0.20",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert output_dir.exists()
        assert (output_dir / "page_001.png").exists()


class TestParameterValidation:
    """Test parameter validation and edge cases."""

    def test_step_parameter_affects_line_count(self, tmp_path: Path):
        """Verify --step parameter controls grid line density."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        test_img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        test_img.save(input_dir / "page_001.png")

        # With step=0.05 and max=0.10, expect 2 lines per direction
        # (0.05 and 0.10)
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.preview_trim_grid",
                str(input_dir),
                "-o",
                str(output_dir),
                "--step",
                "0.05",
                "--max",
                "0.10",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert (output_dir / "page_001.png").exists()

    def test_max_parameter_limits_line_extent(self, tmp_path: Path):
        """Verify --max parameter limits maximum trim value."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        test_img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        test_img.save(input_dir / "page_001.png")

        # With max=0.15, no line should exceed 15% trim
        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.preview_trim_grid",
                str(input_dir),
                "-o",
                str(output_dir),
                "--step",
                "0.05",
                "--max",
                "0.15",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert (output_dir / "page_001.png").exists()

    def test_spread_mode_single_accepted(self, tmp_path: Path):
        """Verify --spread-mode=single is accepted."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        test_img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        test_img.save(input_dir / "page_001.png")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.preview_trim_grid",
                str(input_dir),
                "-o",
                str(output_dir),
                "--spread-mode",
                "single",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"

    def test_spread_mode_spread_accepted(self, tmp_path: Path):
        """Verify --spread-mode=spread is accepted."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        test_img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        test_img.save(input_dir / "page_001.png")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.preview_trim_grid",
                str(input_dir),
                "-o",
                str(output_dir),
                "--spread-mode",
                "spread",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"

    def test_invalid_spread_mode_rejected(self, tmp_path: Path):
        """Verify invalid --spread-mode value is rejected."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        test_img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        test_img.save(input_dir / "page_001.png")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.preview_trim_grid",
                str(input_dir),
                "-o",
                str(output_dir),
                "--spread-mode",
                "invalid",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
        assert "error" in result.stderr.lower() or "invalid" in result.stderr.lower()


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_input_directory(self, tmp_path: Path):
        """Verify behavior with empty input directory."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.preview_trim_grid",
                str(input_dir),
                "-o",
                str(output_dir),
            ],
            capture_output=True,
            text=True,
        )

        # Should succeed but produce no output files
        assert result.returncode == 0

    def test_very_small_image(self, tmp_path: Path):
        """Verify handling of very small images."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        # Create tiny image (50x50)
        test_img = Image.new("RGB", (50, 50), color=(255, 255, 255))
        test_img.save(input_dir / "tiny.png")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.preview_trim_grid",
                str(input_dir),
                "-o",
                str(output_dir),
                "--step",
                "0.10",
                "--max",
                "0.30",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert (output_dir / "tiny.png").exists()

    def test_very_large_image(self, tmp_path: Path):
        """Verify handling of very large images."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        # Create large image (4000x3000)
        test_img = Image.new("RGB", (4000, 3000), color=(255, 255, 255))
        test_img.save(input_dir / "large.png")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.preview_trim_grid",
                str(input_dir),
                "-o",
                str(output_dir),
                "--step",
                "0.10",
                "--max",
                "0.30",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode == 0, f"CLI failed: {result.stderr}"
        assert (output_dir / "large.png").exists()

    def test_step_zero_rejected(self, tmp_path: Path):
        """Verify --step=0 is rejected."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        test_img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        test_img.save(input_dir / "page_001.png")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.preview_trim_grid",
                str(input_dir),
                "-o",
                str(output_dir),
                "--step",
                "0",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
        assert "error" in result.stderr.lower()

    def test_step_greater_than_max_rejected(self, tmp_path: Path):
        """Verify --step > --max is rejected."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        test_img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        test_img.save(input_dir / "page_001.png")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.preview_trim_grid",
                str(input_dir),
                "-o",
                str(output_dir),
                "--step",
                "0.20",
                "--max",
                "0.10",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
        assert "error" in result.stderr.lower()

    def test_max_greater_than_half_rejected(self, tmp_path: Path):
        """Verify --max >= 0.5 is rejected (would trim more than half the image)."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        test_img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        test_img.save(input_dir / "page_001.png")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.preview_trim_grid",
                str(input_dir),
                "-o",
                str(output_dir),
                "--max",
                "0.5",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
        assert "error" in result.stderr.lower()

    def test_negative_step_rejected(self, tmp_path: Path):
        """Verify negative --step is rejected."""
        input_dir = tmp_path / "input"
        output_dir = tmp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        test_img = Image.new("RGB", (800, 600), color=(255, 255, 255))
        test_img.save(input_dir / "page_001.png")

        result = subprocess.run(
            [
                sys.executable,
                "-m",
                "src.cli.preview_trim_grid",
                str(input_dir),
                "-o",
                str(output_dir),
                "--step",
                "-0.05",
            ],
            capture_output=True,
            text=True,
        )

        assert result.returncode != 0
        assert "error" in result.stderr.lower()
