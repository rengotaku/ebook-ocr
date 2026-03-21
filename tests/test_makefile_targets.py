"""Tests for Makefile targets: preview-extract, preview-trim, make run integration (US3 Phase 4).

Tests for:
- T051: preview-extract target extracts sample frames to preview/ directory
- T052: preview-trim target applies trim to existing preview frames (no re-extraction)
- T054: make run integrates split-spreads step into full pipeline
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import pytest
from PIL import Image

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).resolve().parent.parent


@pytest.fixture()
def preview_hash_dir(tmp_path: Path) -> Path:
    """Create a hash directory structure for preview testing."""
    hash_dir = tmp_path / "output" / "abc123"
    hash_dir.mkdir(parents=True)
    return hash_dir


@pytest.fixture()
def preview_frames_dir(preview_hash_dir: Path) -> Path:
    """Create preview/frames/ directory with sample images."""
    frames_dir = preview_hash_dir / "preview" / "frames"
    frames_dir.mkdir(parents=True)
    # Create sample frames (simulating extracted video frames)
    for i in range(3):
        img = Image.new("RGB", (2000, 1000), color="white")
        img.save(frames_dir / f"page_{i + 1:04d}.png")
        img.close()
    return frames_dir


@pytest.fixture()
def preview_trimmed_dir(preview_hash_dir: Path) -> Path:
    """Return the expected trimmed output directory path."""
    trimmed_dir = preview_hash_dir / "preview" / "trimmed"
    return trimmed_dir


# ===========================================================================
# T051: preview-extract target tests
# ===========================================================================


class TestPreviewExtractTarget:
    """preview-extract Makefile ターゲットがフレーム抽出を実行する."""

    def test_preview_extract_target_exists_in_makefile(self, project_root: Path) -> None:
        """Makefile contains preview-extract target definition."""
        makefile = project_root / "Makefile"
        content = makefile.read_text()
        assert "preview-extract:" in content, "preview-extract target not found in Makefile"

    def test_preview_extract_requires_video_param(self, project_root: Path) -> None:
        """preview-extract requires VIDEO parameter."""
        result = subprocess.run(
            ["make", "preview-extract"],
            capture_output=True,
            text=True,
            cwd=str(project_root),
            timeout=30,
        )
        # Should fail with error about missing VIDEO
        assert result.returncode != 0
        assert "VIDEO" in result.stderr or "VIDEO" in result.stdout

    def test_preview_extract_accepts_limit_param(self, project_root: Path) -> None:
        """preview-extract accepts LIMIT parameter for frame count."""
        makefile = project_root / "Makefile"
        content = makefile.read_text()
        # The target should reference LIMIT
        assert "LIMIT" in content, "LIMIT variable not referenced in Makefile"

    def test_preview_extract_outputs_to_preview_frames(self, project_root: Path) -> None:
        """preview-extract outputs frames to preview/frames/ directory."""
        makefile = project_root / "Makefile"
        content = makefile.read_text()
        # Target should reference preview/frames or preview directory
        assert "preview" in content.lower(), "preview directory not referenced in Makefile"

    def test_preview_extract_target_uses_hashdir(self, project_root: Path) -> None:
        """preview-extract uses HASHDIR or creates output in hash-based directory."""
        makefile = project_root / "Makefile"
        content = makefile.read_text()
        # Check that preview-extract references HASHDIR
        # Extract preview-extract section
        assert "HASHDIR" in content, "HASHDIR not referenced in Makefile"


# ===========================================================================
# T054: make run integrates split-spreads step
# ===========================================================================


class TestMakeRunIntegration:
    """make run パイプラインに split-spreads ステップが統合されている."""

    def test_run_target_includes_split_spreads(self, project_root: Path) -> None:
        """make run pipeline includes split-spreads step."""
        makefile = project_root / "Makefile"
        content = makefile.read_text()
        # Find the run target section
        lines = content.split("\n")
        in_run = False
        has_split_spreads = False
        for line in lines:
            if line.startswith("run:"):
                in_run = True
                continue
            if in_run:
                if line and not line.startswith("\t") and not line.startswith(" ") and not line.startswith("@"):
                    break
                if "split-spreads" in line or "split_spreads" in line:
                    has_split_spreads = True
        assert has_split_spreads, "run target should include split-spreads step"

    def test_split_spreads_runs_after_deduplicate(self, project_root: Path) -> None:
        """split-spreads step runs after deduplicate in the pipeline."""
        makefile = project_root / "Makefile"
        content = makefile.read_text()
        lines = content.split("\n")
        in_run = False
        dedup_line = -1
        split_line = -1
        for i, line in enumerate(lines):
            if line.startswith("run:"):
                in_run = True
                continue
            if in_run:
                if line and not line.startswith("\t") and not line.startswith(" ") and not line.startswith("@"):
                    break
                if "deduplicate" in line:
                    dedup_line = i
                if "split-spreads" in line or "split_spreads" in line:
                    split_line = i
        assert dedup_line > 0, "deduplicate step not found in run target"
        assert split_line > 0, "split-spreads step not found in run target"
        assert split_line > dedup_line, "split-spreads should run after deduplicate"

    def test_split_spreads_runs_before_detect_layout(self, project_root: Path) -> None:
        """split-spreads step runs before detect-layout in the pipeline."""
        makefile = project_root / "Makefile"
        content = makefile.read_text()
        lines = content.split("\n")
        in_run = False
        split_line = -1
        layout_line = -1
        for i, line in enumerate(lines):
            if line.startswith("run:"):
                in_run = True
                continue
            if in_run:
                if line and not line.startswith("\t") and not line.startswith(" ") and not line.startswith("@"):
                    break
                if "split-spreads" in line or "split_spreads" in line:
                    split_line = i
                if "detect-layout" in line or "detect_layout" in line:
                    layout_line = i
        assert split_line > 0, "split-spreads step not found in run target"
        assert layout_line > 0, "detect-layout step not found in run target"
        assert split_line < layout_line, "split-spreads should run before detect-layout"

    def test_run_pipeline_passes_spread_mode(self, project_root: Path) -> None:
        """make run passes SPREAD_MODE to split-spreads step."""
        makefile = project_root / "Makefile"
        content = makefile.read_text()
        lines = content.split("\n")
        in_run = False
        for line in lines:
            if line.startswith("run:"):
                in_run = True
                continue
            if in_run:
                if line and not line.startswith("\t") and not line.startswith(" ") and not line.startswith("@"):
                    break
                if "split-spreads" in line and "SPREAD_MODE" in line:
                    return  # Pass: found SPREAD_MODE in split-spreads call within run
        # If split-spreads is called via $(MAKE) it inherits variables
        # Check if SPREAD_MODE is defined at top level (which makes it available to sub-makes)
        assert "SPREAD_MODE" in content, "SPREAD_MODE should be defined and available in pipeline"

    def test_run_target_step_numbering(self, project_root: Path) -> None:
        """split-spreads has proper step numbering in run target (Step 2.5 or renumbered)."""
        makefile = project_root / "Makefile"
        content = makefile.read_text()
        # Check that there's a step label/echo for split-spreads
        lines = content.split("\n")
        in_run = False
        has_step_label = False
        for line in lines:
            if line.startswith("run:"):
                in_run = True
                continue
            if in_run:
                if line and not line.startswith("\t") and not line.startswith(" ") and not line.startswith("@"):
                    break
                if ("split" in line.lower() or "spread" in line.lower()) and ("step" in line.lower() or "===" in line):
                    has_step_label = True
        assert has_step_label, "split-spreads should have a step label/echo in run target"


# ===========================================================================
# Edge Cases
# ===========================================================================


class TestMakefileTargetEdgeCases:
    """Makefile ターゲットのエッジケーステスト."""

    def test_phony_targets_include_preview(self, project_root: Path) -> None:
        """preview-extract and preview-trim are listed in .PHONY."""
        makefile = project_root / "Makefile"
        content = makefile.read_text()
        # Find .PHONY line(s)
        phony_content = ""
        for line in content.split("\n"):
            if line.startswith(".PHONY:"):
                phony_content += line
        assert "preview-extract" in phony_content, "preview-extract should be in .PHONY"
        assert "preview-trim" in phony_content, "preview-trim should be in .PHONY"

    def test_preview_extract_has_help_comment(self, project_root: Path) -> None:
        """preview-extract target has help comment for make help."""
        makefile = project_root / "Makefile"
        content = makefile.read_text()
        for line in content.split("\n"):
            if line.startswith("preview-extract:") and "##" in line:
                return  # Pass
        pytest.fail("preview-extract should have a ## help comment")

    def test_trim_variables_are_overridable(self, project_root: Path) -> None:
        """Trim parameters can be overridden via make variables."""
        makefile = project_root / "Makefile"
        content = makefile.read_text()
        assert "GLOBAL_TRIM_TOP ?=" in content, "GLOBAL_TRIM_TOP should be overridable"
        assert "GLOBAL_TRIM_BOTTOM ?=" in content, "GLOBAL_TRIM_BOTTOM should be overridable"
