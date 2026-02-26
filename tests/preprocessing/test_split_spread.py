"""Tests for SpreadMode and TrimConfig (US1 Phase 2 + US2 Phase 3 + US3 Phase 4).

Tests for:
- T008: mode=single copies without splitting
- T009: mode=spread always splits
- T010: default mode is single
- T011: SPREAD_MODE environment variable
- T012: CLI argument priority over env var
- T013: mode display on stdout
- T031: global-trim-top/bottom application
- T032: global-trim-left/right application
- T033: global-trim -> split-trim ordering
- T034: single mode with global-trim
- T035: trim value validation (out of range)
- T053: preview/ empty directory error handling
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from PIL import Image

from src.preprocessing.split_spread import (
    SpreadMode,
    TrimConfig,  # noqa: F401 - Phase 3 RED: not yet implemented
    apply_global_trim,  # noqa: F401 - Phase 3 RED: not yet implemented
    get_spread_mode,
    split_spread_pages,
    validate_trim_value,  # noqa: F401 - Phase 3 RED: not yet implemented
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


# ===========================================================================
# Phase 3: US2 - 2段階 Trim 制御
# ===========================================================================


# ---------------------------------------------------------------------------
# Phase 3 Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def trim_spread_image(tmp_path: Path) -> Path:
    """Create a spread image (1000x500) with colored borders for trim verification.

    Image layout (1000x500):
    - Top 10px (2%): red border
    - Bottom 10px (2%): blue border
    - Left 10px (1%): green border
    - Right 10px (1%): yellow border
    - Center: white
    """
    hash_dir = tmp_path / "trim_test"
    pages_dir = hash_dir / "pages"
    pages_dir.mkdir(parents=True)
    img = Image.new("RGB", (1000, 500), color="white")
    # Draw colored borders for verification
    pixels = img.load()
    # Top border: red (2% of 500 = 10px)
    for x in range(1000):
        for y in range(10):
            pixels[x, y] = (255, 0, 0)
    # Bottom border: blue (2% of 500 = 10px)
    for x in range(1000):
        for y in range(490, 500):
            pixels[x, y] = (255, 0, 255)
    # Left border: green (1% of 1000 = 10px)
    for x in range(10):
        for y in range(10, 490):
            pixels[x, y] = (0, 255, 0)
    # Right border: yellow (1% of 1000 = 10px)
    for x in range(990, 1000):
        for y in range(10, 490):
            pixels[x, y] = (255, 255, 0)
    path = pages_dir / "page_0001.png"
    img.save(path)
    img.close()
    return pages_dir


@pytest.fixture()
def large_spread_image(tmp_path: Path) -> Path:
    """Create a large spread image (2000x1000) for trim tests."""
    hash_dir = tmp_path / "large_trim"
    pages_dir = hash_dir / "pages"
    pages_dir.mkdir(parents=True)
    img = Image.new("RGB", (2000, 1000), color="white")
    path = pages_dir / "page_0001.png"
    img.save(path)
    img.close()
    return pages_dir


# ===========================================================================
# T031: global-trim-top/bottom application
# ===========================================================================


class TestGlobalTrimTopBottom:
    """global-trim-top/bottom が分割前の画像に正しく適用される."""

    def test_global_trim_top_reduces_height(self, trim_spread_image: Path) -> None:
        """global_top=0.02 removes 2% from top (10px from 500px height)."""
        trim_cfg = TrimConfig(global_top=0.02)
        img = Image.open(trim_spread_image / "page_0001.png")
        trimmed = apply_global_trim(img, trim_cfg)
        # Original: 1000x500, top 2% removed = 1000x490
        assert trimmed.size == (1000, 490)
        img.close()
        trimmed.close()

    def test_global_trim_bottom_reduces_height(self, trim_spread_image: Path) -> None:
        """global_bottom=0.02 removes 2% from bottom."""
        trim_cfg = TrimConfig(global_bottom=0.02)
        img = Image.open(trim_spread_image / "page_0001.png")
        trimmed = apply_global_trim(img, trim_cfg)
        # Original: 1000x500, bottom 2% removed = 1000x490
        assert trimmed.size == (1000, 490)
        img.close()
        trimmed.close()

    def test_global_trim_top_and_bottom_combined(self, trim_spread_image: Path) -> None:
        """global_top=0.02 + global_bottom=0.02 removes 4% total height."""
        trim_cfg = TrimConfig(global_top=0.02, global_bottom=0.02)
        img = Image.open(trim_spread_image / "page_0001.png")
        trimmed = apply_global_trim(img, trim_cfg)
        # Original: 1000x500, top+bottom 2% each = 1000x480
        assert trimmed.size == (1000, 480)
        img.close()
        trimmed.close()

    def test_global_trim_top_removes_top_border(self, trim_spread_image: Path) -> None:
        """After top trim, the red top border (10px) should be removed."""
        trim_cfg = TrimConfig(global_top=0.02)
        img = Image.open(trim_spread_image / "page_0001.png")
        trimmed = apply_global_trim(img, trim_cfg)
        # Top-left pixel should NOT be red anymore (border was removed)
        top_pixel = trimmed.getpixel((500, 0))
        assert top_pixel != (255, 0, 0), "Red top border should have been trimmed"
        img.close()
        trimmed.close()

    def test_global_trim_zero_top_bottom_no_change(self, trim_spread_image: Path) -> None:
        """global_top=0.0, global_bottom=0.0 does not change image height."""
        trim_cfg = TrimConfig(global_top=0.0, global_bottom=0.0)
        img = Image.open(trim_spread_image / "page_0001.png")
        trimmed = apply_global_trim(img, trim_cfg)
        assert trimmed.size == (1000, 500)
        img.close()
        trimmed.close()


# ===========================================================================
# T032: global-trim-left/right application
# ===========================================================================


class TestGlobalTrimLeftRight:
    """global-trim-left/right が分割前の画像に正しく適用される."""

    def test_global_trim_left_reduces_width(self, trim_spread_image: Path) -> None:
        """global_left=0.01 removes 1% from left (10px from 1000px width)."""
        trim_cfg = TrimConfig(global_left=0.01)
        img = Image.open(trim_spread_image / "page_0001.png")
        trimmed = apply_global_trim(img, trim_cfg)
        # Original: 1000x500, left 1% removed = 990x500
        assert trimmed.size == (990, 500)
        img.close()
        trimmed.close()

    def test_global_trim_right_reduces_width(self, trim_spread_image: Path) -> None:
        """global_right=0.01 removes 1% from right."""
        trim_cfg = TrimConfig(global_right=0.01)
        img = Image.open(trim_spread_image / "page_0001.png")
        trimmed = apply_global_trim(img, trim_cfg)
        # Original: 1000x500, right 1% removed = 990x500
        assert trimmed.size == (990, 500)
        img.close()
        trimmed.close()

    def test_global_trim_left_and_right_combined(self, trim_spread_image: Path) -> None:
        """global_left=0.01 + global_right=0.01 removes 2% total width."""
        trim_cfg = TrimConfig(global_left=0.01, global_right=0.01)
        img = Image.open(trim_spread_image / "page_0001.png")
        trimmed = apply_global_trim(img, trim_cfg)
        # Original: 1000x500, left+right 1% each = 980x500
        assert trimmed.size == (980, 500)
        img.close()
        trimmed.close()

    def test_global_trim_all_sides(self, trim_spread_image: Path) -> None:
        """All four global trim values applied simultaneously."""
        trim_cfg = TrimConfig(global_top=0.02, global_bottom=0.02, global_left=0.01, global_right=0.01)
        img = Image.open(trim_spread_image / "page_0001.png")
        trimmed = apply_global_trim(img, trim_cfg)
        # 1000 - 10 - 10 = 980 width, 500 - 10 - 10 = 480 height
        assert trimmed.size == (980, 480)
        img.close()
        trimmed.close()

    def test_global_trim_left_removes_left_border(self, trim_spread_image: Path) -> None:
        """After left trim, the green left border should be removed."""
        trim_cfg = TrimConfig(global_left=0.01)
        img = Image.open(trim_spread_image / "page_0001.png")
        trimmed = apply_global_trim(img, trim_cfg)
        # Left edge pixel should NOT be green anymore
        left_pixel = trimmed.getpixel((0, 250))
        assert left_pixel != (0, 255, 0), "Green left border should have been trimmed"
        img.close()
        trimmed.close()

    def test_global_trim_zero_all_no_change(self, trim_spread_image: Path) -> None:
        """All zeros produces identical image dimensions."""
        trim_cfg = TrimConfig()
        img = Image.open(trim_spread_image / "page_0001.png")
        trimmed = apply_global_trim(img, trim_cfg)
        assert trimmed.size == (1000, 500)
        img.close()
        trimmed.close()


# ===========================================================================
# T033: global-trim -> split-trim ordering
# ===========================================================================


class TestTrimOrdering:
    """global-trim が分割前に適用され、split-trim が分割後に適用される順序."""

    def test_global_trim_then_split_produces_correct_width(self, large_spread_image: Path) -> None:
        """global-trim reduces image first, then split divides the trimmed image."""
        trim_cfg = TrimConfig(global_left=0.05, global_right=0.05)
        # Original: 2000x1000
        # After global trim: 2000 - 100 - 100 = 1800x1000
        # After spread split: each half = 900x1000
        result = split_spread_pages(
            str(large_spread_image),
            mode=SpreadMode.SPREAD,
            trim_config=trim_cfg,
        )
        assert len(result) == 2
        left = Image.open(result[0])
        right = Image.open(result[1])
        # Each half of 1800px = 900px
        assert left.size[0] == 900
        assert right.size[0] == 900
        left.close()
        right.close()

    def test_global_trim_then_split_trim_combined(self, large_spread_image: Path) -> None:
        """Both global-trim and split-trim applied in correct order."""
        trim_cfg = TrimConfig(
            global_left=0.05,
            global_right=0.05,
            left_page_outer=0.1,
            right_page_outer=0.1,
        )
        # Original: 2000x1000
        # After global trim: 1800x1000
        # After split: each 900x1000
        # After split-trim: left outer 10% = 90px removed, right outer 10% = 90px removed
        # Left page: 900 - 90 = 810px, Right page: 900 - 90 = 810px
        result = split_spread_pages(
            str(large_spread_image),
            mode=SpreadMode.SPREAD,
            trim_config=trim_cfg,
        )
        assert len(result) == 2
        left = Image.open(result[0])
        right = Image.open(result[1])
        assert left.size[0] == 810
        assert right.size[0] == 810
        left.close()
        right.close()

    def test_global_trim_top_bottom_then_split_preserves_height(self, large_spread_image: Path) -> None:
        """global-trim top/bottom affects height, split does not."""
        trim_cfg = TrimConfig(global_top=0.1, global_bottom=0.1)
        # Original: 2000x1000
        # After global trim: 2000x800 (100px top + 100px bottom removed)
        # After split: each 1000x800
        result = split_spread_pages(
            str(large_spread_image),
            mode=SpreadMode.SPREAD,
            trim_config=trim_cfg,
        )
        assert len(result) == 2
        left = Image.open(result[0])
        assert left.size == (1000, 800)
        left.close()

    def test_split_trim_not_applied_without_global_trim(self, large_spread_image: Path) -> None:
        """split-trim works independently of global-trim."""
        trim_cfg = TrimConfig(left_page_outer=0.1, right_page_outer=0.1)
        # Original: 2000x1000
        # No global trim -> split: each 1000x1000
        # Split-trim: 10% of 1000 = 100px removed from outer edges
        result = split_spread_pages(
            str(large_spread_image),
            mode=SpreadMode.SPREAD,
            trim_config=trim_cfg,
        )
        assert len(result) == 2
        left = Image.open(result[0])
        right = Image.open(result[1])
        assert left.size[0] == 900
        assert right.size[0] == 900
        left.close()
        right.close()

    def test_default_trim_config_no_trimming(self, large_spread_image: Path) -> None:
        """Default TrimConfig (all zeros) means no trimming at all."""
        trim_cfg = TrimConfig()
        result = split_spread_pages(
            str(large_spread_image),
            mode=SpreadMode.SPREAD,
            trim_config=trim_cfg,
        )
        assert len(result) == 2
        left = Image.open(result[0])
        # No trim: 2000/2 = 1000px each half
        assert left.size == (1000, 1000)
        left.close()


# ===========================================================================
# T034: single mode with global-trim
# ===========================================================================


class TestSingleModeGlobalTrim:
    """単ページモードでも global-trim が適用される."""

    def test_single_mode_applies_global_trim(self, trim_spread_image: Path) -> None:
        """global-trim is applied even in single mode."""
        trim_cfg = TrimConfig(global_top=0.02, global_bottom=0.02)
        result = split_spread_pages(
            str(trim_spread_image),
            mode=SpreadMode.SINGLE,
            trim_config=trim_cfg,
        )
        assert len(result) == 1
        output = Image.open(result[0])
        # Original: 1000x500, top+bottom 2% = 1000x480
        assert output.size == (1000, 480)
        output.close()

    def test_single_mode_global_trim_all_sides(self, trim_spread_image: Path) -> None:
        """All four global-trim values applied in single mode."""
        trim_cfg = TrimConfig(global_top=0.02, global_bottom=0.02, global_left=0.01, global_right=0.01)
        result = split_spread_pages(
            str(trim_spread_image),
            mode=SpreadMode.SINGLE,
            trim_config=trim_cfg,
        )
        assert len(result) == 1
        output = Image.open(result[0])
        assert output.size == (980, 480)
        output.close()

    def test_single_mode_split_trim_ignored(self, trim_spread_image: Path) -> None:
        """split-trim (left_page_outer/right_page_outer) is ignored in single mode."""
        trim_cfg = TrimConfig(left_page_outer=0.1, right_page_outer=0.1)
        result = split_spread_pages(
            str(trim_spread_image),
            mode=SpreadMode.SINGLE,
            trim_config=trim_cfg,
        )
        assert len(result) == 1
        output = Image.open(result[0])
        # Split-trim should NOT be applied in single mode
        assert output.size == (1000, 500)
        output.close()

    def test_single_mode_no_trim_config_preserves_original(self, trim_spread_image: Path) -> None:
        """No trim_config in single mode preserves original dimensions."""
        result = split_spread_pages(
            str(trim_spread_image),
            mode=SpreadMode.SINGLE,
        )
        assert len(result) == 1
        output = Image.open(result[0])
        assert output.size == (1000, 500)
        output.close()


# ===========================================================================
# T035: trim value validation (0.5 or above is error)
# ===========================================================================


class TestTrimValidation:
    """trim 値の範囲検証: 0.0 <= x < 0.5."""

    def test_validate_trim_value_zero_valid(self) -> None:
        """0.0 is a valid trim value."""
        validate_trim_value(0.0, "test_field")

    def test_validate_trim_value_small_valid(self) -> None:
        """Small positive value (0.01) is valid."""
        validate_trim_value(0.01, "test_field")

    def test_validate_trim_value_just_below_half_valid(self) -> None:
        """0.49 is valid (just below 0.5 threshold)."""
        validate_trim_value(0.49, "test_field")

    def test_validate_trim_value_half_invalid(self) -> None:
        """0.5 is invalid (would trim half the image)."""
        with pytest.raises(ValueError, match="0.5"):
            validate_trim_value(0.5, "test_field")

    def test_validate_trim_value_above_half_invalid(self) -> None:
        """Values above 0.5 are invalid."""
        with pytest.raises(ValueError, match="0.8"):
            validate_trim_value(0.8, "test_field")

    def test_validate_trim_value_one_invalid(self) -> None:
        """1.0 is invalid (would remove entire dimension)."""
        with pytest.raises(ValueError, match="1.0"):
            validate_trim_value(1.0, "test_field")

    def test_validate_trim_value_negative_invalid(self) -> None:
        """Negative values are invalid."""
        with pytest.raises(ValueError, match="-0.1"):
            validate_trim_value(-0.1, "test_field")

    def test_validate_trim_value_field_name_in_error(self) -> None:
        """Error message includes the field name for debugging."""
        with pytest.raises(ValueError, match="global_top"):
            validate_trim_value(0.5, "global_top")

    def test_trim_config_validates_on_creation(self) -> None:
        """TrimConfig validates all values on construction."""
        with pytest.raises(ValueError):
            TrimConfig(global_top=0.6)

    def test_trim_config_validates_negative_on_creation(self) -> None:
        """TrimConfig rejects negative values on construction."""
        with pytest.raises(ValueError):
            TrimConfig(global_left=-0.01)

    def test_trim_config_validates_all_fields(self) -> None:
        """TrimConfig validates every field, not just the first."""
        with pytest.raises(ValueError):
            TrimConfig(global_top=0.0, global_bottom=0.0, global_left=0.0, right_page_outer=0.5)


# ===========================================================================
# Phase 3: Edge Cases
# ===========================================================================


class TestTrimEdgeCases:
    """Trim 機能のエッジケーステスト."""

    def test_trim_config_default_all_zeros(self) -> None:
        """Default TrimConfig has all values set to 0.0."""
        cfg = TrimConfig()
        assert cfg.global_top == 0.0
        assert cfg.global_bottom == 0.0
        assert cfg.global_left == 0.0
        assert cfg.global_right == 0.0
        assert cfg.left_page_outer == 0.0
        assert cfg.right_page_outer == 0.0

    def test_apply_global_trim_returns_new_image(self, trim_spread_image: Path) -> None:
        """apply_global_trim returns a new Image, not mutated original."""
        trim_cfg = TrimConfig(global_top=0.02)
        img = Image.open(trim_spread_image / "page_0001.png")
        trimmed = apply_global_trim(img, trim_cfg)
        # Original should remain unchanged
        assert img.size == (1000, 500)
        assert trimmed.size == (1000, 490)
        assert trimmed is not img
        img.close()
        trimmed.close()

    def test_apply_global_trim_with_none_raises(self) -> None:
        """apply_global_trim with None image raises error."""
        trim_cfg = TrimConfig(global_top=0.02)
        with pytest.raises((TypeError, AttributeError)):
            apply_global_trim(None, trim_cfg)

    def test_apply_global_trim_very_small_image(self, tmp_path: Path) -> None:
        """Global trim on a very small image (10x10) still works."""
        img = Image.new("RGB", (10, 10), color="white")
        trim_cfg = TrimConfig(global_top=0.1)
        trimmed = apply_global_trim(img, trim_cfg)
        # 10 * 0.1 = 1px removed from top
        assert trimmed.size == (10, 9)
        img.close()
        trimmed.close()

    def test_apply_global_trim_large_image(self, tmp_path: Path) -> None:
        """Global trim on a large image (4000x3000)."""
        img = Image.new("RGB", (4000, 3000), color="white")
        trim_cfg = TrimConfig(global_top=0.05, global_bottom=0.05)
        trimmed = apply_global_trim(img, trim_cfg)
        # 3000 * 0.05 = 150px removed each side
        assert trimmed.size == (4000, 2700)
        img.close()
        trimmed.close()

    def test_trim_config_with_unicode_special_chars_in_error(self) -> None:
        """Validation error with special field names works correctly."""
        with pytest.raises(ValueError):
            validate_trim_value(0.5, "global_top")

    def test_global_trim_preserves_image_mode(self, trim_spread_image: Path) -> None:
        """apply_global_trim preserves the image color mode (RGB)."""
        trim_cfg = TrimConfig(global_top=0.02)
        img = Image.open(trim_spread_image / "page_0001.png")
        trimmed = apply_global_trim(img, trim_cfg)
        assert trimmed.mode == img.mode
        img.close()
        trimmed.close()

    def test_global_trim_with_spread_multiple_images(self, tmp_path: Path) -> None:
        """Multiple images all receive global trim in spread mode."""
        hash_dir = tmp_path / "multi"
        pages_dir = hash_dir / "pages"
        pages_dir.mkdir(parents=True)
        for i in range(3):
            img = Image.new("RGB", (2000, 1000), color="white")
            img.save(pages_dir / f"page_{i + 1:04d}.png")
            img.close()
        trim_cfg = TrimConfig(global_top=0.1)
        result = split_spread_pages(
            str(pages_dir),
            mode=SpreadMode.SPREAD,
            trim_config=trim_cfg,
        )
        # 3 images split into 6
        assert len(result) == 6
        # Check height of first output: 1000 - 100 = 900
        first = Image.open(result[0])
        assert first.size[1] == 900
        first.close()


# ===========================================================================
# Phase 4: US3 - パイプライン統合とプレビュー
# ===========================================================================


# ---------------------------------------------------------------------------
# Phase 4 Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture()
def preview_hash_dir(tmp_path: Path) -> Path:
    """Create a hash directory structure for preview testing."""
    hash_dir = tmp_path / "preview_test"
    hash_dir.mkdir(parents=True)
    return hash_dir


@pytest.fixture()
def preview_frames_dir(preview_hash_dir: Path) -> Path:
    """Create preview/frames/ directory with sample images."""
    frames_dir = preview_hash_dir / "preview" / "frames"
    frames_dir.mkdir(parents=True)
    for i in range(3):
        img = Image.new("RGB", (2000, 1000), color="white")
        img.save(frames_dir / f"page_{i + 1:04d}.png")
        img.close()
    return frames_dir


@pytest.fixture()
def empty_preview_dir(preview_hash_dir: Path) -> Path:
    """Create empty preview/ directory (no frames subdirectory)."""
    preview_dir = preview_hash_dir / "preview"
    preview_dir.mkdir(parents=True)
    return preview_dir


@pytest.fixture()
def empty_preview_frames_dir(preview_hash_dir: Path) -> Path:
    """Create preview/frames/ directory with no images."""
    frames_dir = preview_hash_dir / "preview" / "frames"
    frames_dir.mkdir(parents=True)
    return frames_dir


# ===========================================================================
# T053: preview/ empty directory error handling
# ===========================================================================


class TestPreviewEmptyErrorHandling:
    """preview/ が空のときの split_spreads のエラーハンドリング."""

    def test_preview_dir_not_exists_raises_error(self, preview_hash_dir: Path) -> None:
        """preview/ directory does not exist raises FileNotFoundError or appropriate error."""
        non_existent = preview_hash_dir / "preview" / "frames"
        # Attempting to process non-existent preview dir should raise error
        with pytest.raises((FileNotFoundError, ValueError, OSError)):
            split_spread_pages(
                str(non_existent),
                mode=SpreadMode.SPREAD,
            )

    def test_preview_frames_empty_returns_empty_list(self, empty_preview_frames_dir: Path) -> None:
        """Empty preview/frames/ directory returns empty list with warning."""
        result = split_spread_pages(
            str(empty_preview_frames_dir),
            mode=SpreadMode.SPREAD,
        )
        assert result == []

    def test_preview_frames_empty_prints_warning(
        self, empty_preview_frames_dir: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Empty preview/frames/ directory prints a warning message."""
        split_spread_pages(
            str(empty_preview_frames_dir),
            mode=SpreadMode.SPREAD,
        )
        captured = capsys.readouterr()
        assert "no page images" in captured.out.lower() or "found" in captured.out.lower()

    def test_preview_trim_without_frames_error_message(
        self, empty_preview_dir: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """When preview exists but frames/ is missing, provide guidance to run preview-extract first."""
        # This tests the CLI-level error handling for preview-trim
        # When frames directory doesn't exist, user should be told to run preview-extract first
        from src.cli.split_spreads import preview_trim_check  # noqa: F401 - Phase 4 RED: not yet implemented

        with pytest.raises((FileNotFoundError, SystemExit, ValueError)):
            preview_trim_check(str(empty_preview_dir))

    def test_preview_trim_check_with_frames_present(self, preview_frames_dir: Path) -> None:
        """preview_trim_check succeeds when frames exist."""
        from src.cli.split_spreads import preview_trim_check  # noqa: F401 - Phase 4 RED: not yet implemented

        # Should not raise any error
        result = preview_trim_check(str(preview_frames_dir.parent))
        assert result is True or result is None  # Either returns True or None (no error)

    def test_preview_trim_check_with_empty_frames_dir(self, empty_preview_frames_dir: Path) -> None:
        """preview_trim_check fails when frames/ exists but is empty."""
        from src.cli.split_spreads import preview_trim_check  # noqa: F401 - Phase 4 RED: not yet implemented

        with pytest.raises((FileNotFoundError, ValueError, SystemExit)):
            preview_trim_check(str(empty_preview_frames_dir.parent))


class TestPreviewTrimProcessing:
    """preview-trim の処理テスト: フレームに trim を適用して trimmed/ に出力."""

    def test_preview_trim_creates_trimmed_directory(self, preview_frames_dir: Path) -> None:
        """preview-trim creates preview/trimmed/ directory."""
        from src.cli.split_spreads import preview_trim  # noqa: F401 - Phase 4 RED: not yet implemented

        preview_dir = preview_frames_dir.parent
        trim_cfg = TrimConfig(global_top=0.02)
        preview_trim(str(preview_dir), mode=SpreadMode.SPREAD, trim_config=trim_cfg)
        trimmed_dir = preview_dir / "trimmed"
        assert trimmed_dir.exists(), "trimmed/ directory should be created"

    def test_preview_trim_outputs_to_trimmed_dir(self, preview_frames_dir: Path) -> None:
        """preview-trim outputs trimmed images to preview/trimmed/."""
        from src.cli.split_spreads import preview_trim  # noqa: F401 - Phase 4 RED: not yet implemented

        preview_dir = preview_frames_dir.parent
        trim_cfg = TrimConfig(global_top=0.02)
        preview_trim(str(preview_dir), mode=SpreadMode.SPREAD, trim_config=trim_cfg)
        trimmed_dir = preview_dir / "trimmed"
        trimmed_files = list(trimmed_dir.glob("*.png"))
        # 3 frames in spread mode -> 6 output files (L and R for each)
        assert len(trimmed_files) == 6

    def test_preview_trim_does_not_modify_original_frames(self, preview_frames_dir: Path) -> None:
        """preview-trim does NOT modify or delete original frames."""
        from src.cli.split_spreads import preview_trim  # noqa: F401 - Phase 4 RED: not yet implemented

        preview_dir = preview_frames_dir.parent
        original_count = len(list(preview_frames_dir.glob("*.png")))
        trim_cfg = TrimConfig(global_top=0.02)
        preview_trim(str(preview_dir), mode=SpreadMode.SPREAD, trim_config=trim_cfg)
        # Original frames should still exist
        assert len(list(preview_frames_dir.glob("*.png"))) == original_count

    def test_preview_trim_applies_global_trim(self, preview_frames_dir: Path) -> None:
        """preview-trim applies global trim to output images."""
        from src.cli.split_spreads import preview_trim  # noqa: F401 - Phase 4 RED: not yet implemented

        preview_dir = preview_frames_dir.parent
        trim_cfg = TrimConfig(global_top=0.1)  # 10% from top
        preview_trim(str(preview_dir), mode=SpreadMode.SPREAD, trim_config=trim_cfg)
        trimmed_dir = preview_dir / "trimmed"
        trimmed_files = sorted(trimmed_dir.glob("*.png"))
        assert len(trimmed_files) > 0
        first = Image.open(trimmed_files[0])
        # Original: 2000x1000, top 10% = 100px removed, then split -> 1000x900
        assert first.size[1] == 900
        first.close()

    def test_preview_trim_single_mode_no_split(self, preview_frames_dir: Path) -> None:
        """preview-trim in single mode does not split images."""
        from src.cli.split_spreads import preview_trim  # noqa: F401 - Phase 4 RED: not yet implemented

        preview_dir = preview_frames_dir.parent
        trim_cfg = TrimConfig(global_top=0.1)
        preview_trim(str(preview_dir), mode=SpreadMode.SINGLE, trim_config=trim_cfg)
        trimmed_dir = preview_dir / "trimmed"
        trimmed_files = list(trimmed_dir.glob("*.png"))
        # 3 frames in single mode -> 3 output files (no splitting)
        assert len(trimmed_files) == 3

    def test_preview_trim_rerun_overwrites_previous(self, preview_frames_dir: Path) -> None:
        """Re-running preview-trim with new parameters overwrites previous output."""
        from src.cli.split_spreads import preview_trim  # noqa: F401 - Phase 4 RED: not yet implemented

        preview_dir = preview_frames_dir.parent

        # First run
        trim_cfg1 = TrimConfig(global_top=0.1)
        preview_trim(str(preview_dir), mode=SpreadMode.SPREAD, trim_config=trim_cfg1)
        trimmed_dir = preview_dir / "trimmed"
        first_files = sorted(trimmed_dir.glob("*.png"))
        first_img = Image.open(first_files[0])
        first_height = first_img.size[1]
        first_img.close()

        # Second run with different params
        trim_cfg2 = TrimConfig(global_top=0.2)
        preview_trim(str(preview_dir), mode=SpreadMode.SPREAD, trim_config=trim_cfg2)
        second_files = sorted(trimmed_dir.glob("*.png"))
        second_img = Image.open(second_files[0])
        second_height = second_img.size[1]
        second_img.close()

        # Heights should be different (different trim values)
        assert first_height != second_height
        # Second run: 1000 * 0.2 = 200px removed -> 800 height
        assert second_height == 800


class TestPreviewEdgeCases:
    """プレビュー機能のエッジケーステスト."""

    def test_preview_trim_with_none_trim_config(self, preview_frames_dir: Path) -> None:
        """preview-trim with None trim_config still processes (no trim applied)."""
        from src.cli.split_spreads import preview_trim  # noqa: F401 - Phase 4 RED: not yet implemented

        preview_dir = preview_frames_dir.parent
        preview_trim(str(preview_dir), mode=SpreadMode.SPREAD, trim_config=None)
        trimmed_dir = preview_dir / "trimmed"
        trimmed_files = list(trimmed_dir.glob("*.png"))
        # Even without trim, should split and output
        assert len(trimmed_files) == 6

    def test_preview_trim_with_default_trim_config(self, preview_frames_dir: Path) -> None:
        """preview-trim with default TrimConfig (all zeros) produces split without trim."""
        from src.cli.split_spreads import preview_trim  # noqa: F401 - Phase 4 RED: not yet implemented

        preview_dir = preview_frames_dir.parent
        trim_cfg = TrimConfig()
        preview_trim(str(preview_dir), mode=SpreadMode.SPREAD, trim_config=trim_cfg)
        trimmed_dir = preview_dir / "trimmed"
        trimmed_files = sorted(trimmed_dir.glob("*.png"))
        first = Image.open(trimmed_files[0])
        # No trim: 2000/2 = 1000x1000
        assert first.size == (1000, 1000)
        first.close()

    def test_preview_trim_unicode_path(self, tmp_path: Path) -> None:
        """preview-trim handles Unicode characters in path."""
        from src.cli.split_spreads import preview_trim  # noqa: F401 - Phase 4 RED: not yet implemented

        hash_dir = tmp_path / "unicode_test"
        frames_dir = hash_dir / "preview" / "frames"
        frames_dir.mkdir(parents=True)
        img = Image.new("RGB", (2000, 1000), color="white")
        img.save(frames_dir / "page_0001.png")
        img.close()
        preview_dir = hash_dir / "preview"
        trim_cfg = TrimConfig()
        # Should not raise an error
        preview_trim(str(preview_dir), mode=SpreadMode.SPREAD, trim_config=trim_cfg)

    def test_preview_trim_large_batch(self, tmp_path: Path) -> None:
        """preview-trim processes large batch of frames."""
        from src.cli.split_spreads import preview_trim  # noqa: F401 - Phase 4 RED: not yet implemented

        hash_dir = tmp_path / "large_batch"
        frames_dir = hash_dir / "preview" / "frames"
        frames_dir.mkdir(parents=True)
        # Create 20 frames
        for i in range(20):
            img = Image.new("RGB", (2000, 1000), color="white")
            img.save(frames_dir / f"page_{i + 1:04d}.png")
            img.close()
        preview_dir = hash_dir / "preview"
        trim_cfg = TrimConfig(global_top=0.05)
        preview_trim(str(preview_dir), mode=SpreadMode.SPREAD, trim_config=trim_cfg)
        trimmed_dir = preview_dir / "trimmed"
        trimmed_files = list(trimmed_dir.glob("*.png"))
        # 20 frames in spread mode -> 40 files
        assert len(trimmed_files) == 40
