"""Tests for SpreadMode explicit mode specification (US1 - Phase 2).

Tests for:
- T008: mode=single copies without splitting
- T009: mode=spread always splits
- T010: default mode is single
- T011: SPREAD_MODE environment variable
- T012: CLI argument priority over env var
- T013: mode display on stdout
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

from src.preprocessing.split_spread import (
    SpreadMode,
    get_spread_mode,
    split_spread_pages,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def spread_image_path(tmp_path: Path) -> Path:
    """Create a spread (wide) image in a pages directory structure."""
    hash_dir = tmp_path / "abc123"
    pages_dir = hash_dir / "pages"
    pages_dir.mkdir(parents=True)
    img = Image.new("RGB", (2000, 1000), color="white")
    path = pages_dir / "page_0001.png"
    img.save(path)
    img.close()
    return pages_dir


@pytest.fixture()
def single_image_path(tmp_path: Path) -> Path:
    """Create a single-page (tall) image in a pages directory structure."""
    hash_dir = tmp_path / "abc123"
    pages_dir = hash_dir / "pages"
    pages_dir.mkdir(parents=True)
    img = Image.new("RGB", (800, 1200), color="white")
    path = pages_dir / "page_0001.png"
    img.save(path)
    img.close()
    return pages_dir


@pytest.fixture()
def mixed_images_path(tmp_path: Path) -> Path:
    """Create a directory with both spread and single images."""
    hash_dir = tmp_path / "abc123"
    pages_dir = hash_dir / "pages"
    pages_dir.mkdir(parents=True)
    spread = Image.new("RGB", (2000, 1000), color="white")
    spread.save(pages_dir / "page_0001.png")
    spread.close()
    single = Image.new("RGB", (800, 1200), color="white")
    single.save(pages_dir / "page_0002.png")
    single.close()
    return pages_dir


# ===========================================================================
# T008: mode=single - copy only, no splitting
# ===========================================================================


class TestModeSingle:
    """mode=single ではどんな画像も分割せずコピーのみ行う."""

    def test_single_mode_does_not_split_wide_image(self, spread_image_path: Path) -> None:
        """Wide image (aspect > 1.2) is NOT split when mode=single."""
        result = split_spread_pages(str(spread_image_path), mode=SpreadMode.SINGLE)
        # Should output 1 file, not 2
        assert len(result) == 1
        assert (spread_image_path / "page_0001.png").exists()
        assert not (spread_image_path / "page_0001_L.png").exists()
        assert not (spread_image_path / "page_0001_R.png").exists()

    def test_single_mode_preserves_tall_image(self, single_image_path: Path) -> None:
        """Tall image is preserved as-is with mode=single."""
        result = split_spread_pages(str(single_image_path), mode=SpreadMode.SINGLE)
        assert len(result) == 1
        assert (single_image_path / "page_0001.png").exists()

    def test_single_mode_preserves_image_dimensions(self, spread_image_path: Path) -> None:
        """Image dimensions are preserved (no cropping) with mode=single."""
        split_spread_pages(str(spread_image_path), mode=SpreadMode.SINGLE)
        output = Image.open(spread_image_path / "page_0001.png")
        # Original was 2000x1000, should remain unchanged
        assert output.size == (2000, 1000)
        output.close()

    def test_single_mode_with_multiple_images(self, mixed_images_path: Path) -> None:
        """All images are copied without splitting when mode=single."""
        result = split_spread_pages(str(mixed_images_path), mode=SpreadMode.SINGLE)
        # 2 images in, 2 images out (no splitting)
        assert len(result) == 2


# ===========================================================================
# T009: mode=spread - always splits
# ===========================================================================


class TestModeSpread:
    """mode=spread では全画像を左右に分割する."""

    def test_spread_mode_splits_wide_image(self, spread_image_path: Path) -> None:
        """Wide image is split into L and R with mode=spread."""
        result = split_spread_pages(str(spread_image_path), mode=SpreadMode.SPREAD)
        assert len(result) == 2
        assert (spread_image_path / "page_0001_L.png").exists()
        assert (spread_image_path / "page_0001_R.png").exists()

    def test_spread_mode_splits_tall_image(self, single_image_path: Path) -> None:
        """Even tall images are split when mode=spread (user's explicit choice)."""
        result = split_spread_pages(str(single_image_path), mode=SpreadMode.SPREAD)
        assert len(result) == 2
        assert (single_image_path / "page_0001_L.png").exists()
        assert (single_image_path / "page_0001_R.png").exists()

    def test_spread_mode_creates_correct_dimensions(self, spread_image_path: Path) -> None:
        """Split pages have approximately half the original width."""
        split_spread_pages(str(spread_image_path), mode=SpreadMode.SPREAD)
        left = Image.open(spread_image_path / "page_0001_L.png")
        right = Image.open(spread_image_path / "page_0001_R.png")
        # Original: 2000x1000 -> each half: ~1000x1000
        assert left.size == (1000, 1000)
        assert right.size == (1000, 1000)
        left.close()
        right.close()

    def test_spread_mode_splits_all_images(self, mixed_images_path: Path) -> None:
        """All images are split with mode=spread, regardless of aspect ratio."""
        result = split_spread_pages(str(mixed_images_path), mode=SpreadMode.SPREAD)
        # 2 images -> 4 output files (each split into L and R)
        assert len(result) == 4
        assert (mixed_images_path / "page_0001_L.png").exists()
        assert (mixed_images_path / "page_0001_R.png").exists()
        assert (mixed_images_path / "page_0002_L.png").exists()
        assert (mixed_images_path / "page_0002_R.png").exists()

    def test_spread_mode_with_trim(self, spread_image_path: Path) -> None:
        """Split-trim is applied when mode=spread."""
        split_spread_pages(
            str(spread_image_path),
            mode=SpreadMode.SPREAD,
            left_trim_pct=0.1,
            right_trim_pct=0.1,
        )
        left = Image.open(spread_image_path / "page_0001_L.png")
        right = Image.open(spread_image_path / "page_0001_R.png")
        # 1000px half, 10% trim = 100px removed from each outer edge
        assert left.size[0] == 900
        assert right.size[0] == 900
        left.close()
        right.close()


# ===========================================================================
# T010: default mode is single
# ===========================================================================


class TestDefaultMode:
    """モード未指定時のデフォルトは single."""

    def test_default_mode_is_single(self) -> None:
        """SpreadMode default value is SINGLE."""
        assert SpreadMode.SINGLE.value == "single"
        assert SpreadMode.SPREAD.value == "spread"

    def test_get_spread_mode_default(self) -> None:
        """get_spread_mode() returns SINGLE when no mode specified."""
        mode = get_spread_mode(cli_mode=None)
        assert mode == SpreadMode.SINGLE

    def test_split_spread_pages_default_mode_no_split(self, spread_image_path: Path) -> None:
        """Without explicit mode, wide images are NOT split (default=single)."""
        # Calling without mode parameter should default to single
        result = split_spread_pages(str(spread_image_path), mode=None)
        # Default is single, so no splitting
        assert len(result) == 1


# ===========================================================================
# T011: SPREAD_MODE environment variable
# ===========================================================================


class TestEnvironmentVariable:
    """環境変数 SPREAD_MODE でモードを設定できる."""

    def test_env_var_spread(self) -> None:
        """SPREAD_MODE=spread sets spread mode."""
        with patch.dict("os.environ", {"SPREAD_MODE": "spread"}):
            mode = get_spread_mode(cli_mode=None)
            assert mode == SpreadMode.SPREAD

    def test_env_var_single(self) -> None:
        """SPREAD_MODE=single sets single mode."""
        with patch.dict("os.environ", {"SPREAD_MODE": "single"}):
            mode = get_spread_mode(cli_mode=None)
            assert mode == SpreadMode.SINGLE

    def test_env_var_not_set_uses_default(self) -> None:
        """No SPREAD_MODE env var falls back to default (single)."""
        with patch.dict("os.environ", {}, clear=True):
            mode = get_spread_mode(cli_mode=None)
            assert mode == SpreadMode.SINGLE

    def test_env_var_invalid_value(self) -> None:
        """Invalid SPREAD_MODE value raises ValueError."""
        with patch.dict("os.environ", {"SPREAD_MODE": "auto"}):
            with pytest.raises(ValueError, match="auto"):
                get_spread_mode(cli_mode=None)

    def test_env_var_case_insensitive(self) -> None:
        """SPREAD_MODE is case-insensitive."""
        with patch.dict("os.environ", {"SPREAD_MODE": "SPREAD"}):
            mode = get_spread_mode(cli_mode=None)
            assert mode == SpreadMode.SPREAD

    def test_env_var_with_whitespace(self) -> None:
        """SPREAD_MODE with whitespace is trimmed."""
        with patch.dict("os.environ", {"SPREAD_MODE": "  spread  "}):
            mode = get_spread_mode(cli_mode=None)
            assert mode == SpreadMode.SPREAD


# ===========================================================================
# T012: CLI argument takes priority over env var
# ===========================================================================


class TestCLIPriority:
    """CLI 引数は環境変数より優先される."""

    def test_cli_overrides_env_var(self) -> None:
        """CLI mode=single overrides SPREAD_MODE=spread."""
        with patch.dict("os.environ", {"SPREAD_MODE": "spread"}):
            mode = get_spread_mode(cli_mode="single")
            assert mode == SpreadMode.SINGLE

    def test_cli_spread_overrides_env_single(self) -> None:
        """CLI mode=spread overrides SPREAD_MODE=single."""
        with patch.dict("os.environ", {"SPREAD_MODE": "single"}):
            mode = get_spread_mode(cli_mode="spread")
            assert mode == SpreadMode.SPREAD

    def test_cli_none_falls_to_env(self) -> None:
        """CLI mode=None falls through to env var."""
        with patch.dict("os.environ", {"SPREAD_MODE": "spread"}):
            mode = get_spread_mode(cli_mode=None)
            assert mode == SpreadMode.SPREAD

    def test_cli_invalid_value_raises(self) -> None:
        """Invalid CLI mode raises ValueError."""
        with pytest.raises(ValueError, match="invalid"):
            get_spread_mode(cli_mode="invalid")


# ===========================================================================
# T013: mode display on stdout
# ===========================================================================


class TestModeDisplay:
    """処理開始時に使用モードが標準出力に表示される."""

    def test_single_mode_displayed(self, spread_image_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """'Mode: single' is printed to stdout."""
        split_spread_pages(str(spread_image_path), mode=SpreadMode.SINGLE)
        captured = capsys.readouterr()
        assert "Mode: single" in captured.out

    def test_spread_mode_displayed(self, spread_image_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """'Mode: spread' is printed to stdout."""
        split_spread_pages(str(spread_image_path), mode=SpreadMode.SPREAD)
        captured = capsys.readouterr()
        assert "Mode: spread" in captured.out

    def test_mode_displayed_before_processing(
        self, spread_image_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Mode is displayed as the first output line."""
        split_spread_pages(str(spread_image_path), mode=SpreadMode.SPREAD)
        captured = capsys.readouterr()
        lines = captured.out.strip().split("\n")
        assert len(lines) > 0
        assert lines[0].startswith("Mode:")


# ===========================================================================
# Edge Cases
# ===========================================================================


class TestSpreadModeEdgeCases:
    """SpreadMode に関するエッジケーステスト."""

    def test_spread_mode_enum_values(self) -> None:
        """SpreadMode has exactly 2 values."""
        assert len(SpreadMode) == 2
        assert SpreadMode.SINGLE.value == "single"
        assert SpreadMode.SPREAD.value == "spread"

    def test_spread_mode_from_string_single(self) -> None:
        """SpreadMode can be created from string 'single'."""
        mode = SpreadMode("single")
        assert mode == SpreadMode.SINGLE

    def test_spread_mode_from_string_spread(self) -> None:
        """SpreadMode can be created from string 'spread'."""
        mode = SpreadMode("spread")
        assert mode == SpreadMode.SPREAD

    def test_spread_mode_invalid_string(self) -> None:
        """SpreadMode raises ValueError for invalid string."""
        with pytest.raises(ValueError):
            SpreadMode("auto")

    def test_empty_directory_with_mode(self, tmp_path: Path) -> None:
        """Empty directory returns empty list regardless of mode."""
        hash_dir = tmp_path / "abc123"
        pages_dir = hash_dir / "pages"
        pages_dir.mkdir(parents=True)
        result = split_spread_pages(str(pages_dir), mode=SpreadMode.SPREAD)
        assert result == []

    def test_mode_none_uses_default(self) -> None:
        """get_spread_mode with None cli_mode and no env returns SINGLE."""
        with patch.dict("os.environ", {}, clear=True):
            mode = get_spread_mode(cli_mode=None)
            assert mode == SpreadMode.SINGLE

    def test_iterative_run_with_mode_change(self, spread_image_path: Path) -> None:
        """Re-running with different mode uses originals directory."""
        # First run: spread mode
        split_spread_pages(str(spread_image_path), mode=SpreadMode.SPREAD)
        assert (spread_image_path / "page_0001_L.png").exists()

        # Second run: single mode (should re-process from originals)
        split_spread_pages(str(spread_image_path), mode=SpreadMode.SINGLE)
        # In single mode, should have 1 output (not split)
        pages = list(spread_image_path.glob("page_*.png"))
        # Should have page_0001.png only (no _L/_R)
        non_lr_pages = [p for p in pages if "_L" not in p.stem and "_R" not in p.stem]
        assert len(non_lr_pages) == 1
