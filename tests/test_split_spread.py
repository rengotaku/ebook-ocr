"""Tests for src.split_spread spread image splitting."""

from pathlib import Path

from PIL import Image

from src.preprocessing.split_spread import (
    is_spread_image,
    renumber_pages,
    split_spread,
    split_spread_pages,
)


class TestIsSpreadImage:
    """Tests for is_spread_image() detection."""

    def test_wide_image_is_spread(self) -> None:
        """Wide image (aspect ratio > 1.2) is detected as spread."""
        img = Image.new("RGB", (1920, 1080))  # 1.78 aspect ratio
        assert is_spread_image(img) is True

    def test_tall_image_is_not_spread(self) -> None:
        """Tall image (aspect ratio < 1.2) is not a spread."""
        img = Image.new("RGB", (800, 1200))  # 0.67 aspect ratio
        assert is_spread_image(img) is False

    def test_square_image_is_not_spread(self) -> None:
        """Square image is not a spread."""
        img = Image.new("RGB", (1000, 1000))  # 1.0 aspect ratio
        assert is_spread_image(img) is False

    def test_custom_threshold(self) -> None:
        """Custom aspect ratio threshold works."""
        img = Image.new("RGB", (1500, 1000))  # 1.5 aspect ratio

        # With default threshold 1.2: spread
        assert is_spread_image(img, aspect_ratio_threshold=1.2) is True

        # With higher threshold 1.6: not spread
        assert is_spread_image(img, aspect_ratio_threshold=1.6) is False

    def test_exactly_at_threshold(self) -> None:
        """Image exactly at threshold is considered spread."""
        img = Image.new("RGB", (1200, 1000))  # 1.2 aspect ratio
        assert is_spread_image(img, aspect_ratio_threshold=1.2) is True


class TestSplitSpread:
    """Tests for split_spread() image splitting."""

    def test_split_even_width(self) -> None:
        """Spread with even width splits exactly in half."""
        img = Image.new("RGB", (2000, 1000), color="white")
        left, right = split_spread(img)

        assert left.size == (1000, 1000)
        assert right.size == (1000, 1000)

    def test_split_odd_width(self) -> None:
        """Spread with odd width splits correctly."""
        img = Image.new("RGB", (2001, 1000), color="white")
        left, right = split_spread(img)

        # 2001 // 2 = 1000
        assert left.size == (1000, 1000)
        assert right.size == (1001, 1000)

    def test_split_with_overlap(self) -> None:
        """Split with overlap includes center pixels in both pages."""
        img = Image.new("RGB", (2000, 1000), color="white")
        left, right = split_spread(img, overlap_px=50)

        # Left: 0 to 1000+50 = 1050
        assert left.size == (1050, 1000)
        # Right: 1000-50 to 2000 = 1050
        assert right.size == (1050, 1000)

    def test_split_preserves_content(self) -> None:
        """Split preserves pixel content correctly."""
        # Create image with left half red, right half blue
        img = Image.new("RGB", (200, 100))
        for x in range(100):
            for y in range(100):
                img.putpixel((x, y), (255, 0, 0))  # Red
        for x in range(100, 200):
            for y in range(100):
                img.putpixel((x, y), (0, 0, 255))  # Blue

        left, right = split_spread(img)

        # Left page should be red
        assert left.getpixel((50, 50)) == (255, 0, 0)
        # Right page should be blue
        assert right.getpixel((50, 50)) == (0, 0, 255)

    def test_split_with_left_trim(self) -> None:
        """Left trim removes pixels from left edge of left page."""
        img = Image.new("RGB", (2000, 1000), color="white")
        left, right = split_spread(img, left_trim_pct=0.1)  # 10% trim

        # Left page: original width 1000, trim 10% = 100px from left
        # Result: 1000 - 100 = 900px wide
        assert left.size == (900, 1000)
        # Right page unchanged
        assert right.size == (1000, 1000)

    def test_split_with_right_trim(self) -> None:
        """Right trim removes pixels from right edge of right page."""
        img = Image.new("RGB", (2000, 1000), color="white")
        left, right = split_spread(img, right_trim_pct=0.1)  # 10% trim

        # Left page unchanged
        assert left.size == (1000, 1000)
        # Right page: original width 1000, trim 10% = 100px from right
        # Result: 1000 - 100 = 900px wide
        assert right.size == (900, 1000)

    def test_split_with_both_trims(self) -> None:
        """Both left and right trims work together."""
        img = Image.new("RGB", (2000, 1000), color="white")
        left, right = split_spread(img, left_trim_pct=0.03, right_trim_pct=0.03)

        # Each page: 1000px wide, 3% = 30px trimmed
        assert left.size == (970, 1000)
        assert right.size == (970, 1000)


class TestSplitSpreadPages:
    """Tests for split_spread_pages() directory processing."""

    def test_split_spread_pages_creates_lr_files(self, tmp_path: Path) -> None:
        """Spread images are split into _L and _R files."""
        # Create directory structure: tmp_path/hash/pages/
        hash_dir = tmp_path / "abc123"
        pages_dir = hash_dir / "pages"
        pages_dir.mkdir(parents=True)

        spread = Image.new("RGB", (2000, 1000), color="white")
        spread.save(pages_dir / "page_0001.png")

        split_spread_pages(str(pages_dir))

        # Original should be moved to originals/, L/R created in pages/
        assert not (pages_dir / "page_0001.png").exists()
        assert (pages_dir / "page_0001_L.png").exists()
        assert (pages_dir / "page_0001_R.png").exists()
        # Original preserved in originals/
        assert (hash_dir / "originals" / "page_0001.png").exists()

    def test_non_spread_pages_copied(self, tmp_path: Path) -> None:
        """Non-spread images are copied from originals to pages."""
        hash_dir = tmp_path / "abc123"
        pages_dir = hash_dir / "pages"
        pages_dir.mkdir(parents=True)

        single = Image.new("RGB", (800, 1200), color="white")
        single.save(pages_dir / "page_0001.png")

        split_spread_pages(str(pages_dir))

        # Copy should exist in pages/
        assert (pages_dir / "page_0001.png").exists()
        assert not (pages_dir / "page_0001_L.png").exists()
        # Original preserved in originals/
        assert (hash_dir / "originals" / "page_0001.png").exists()

    def test_mixed_pages(self, tmp_path: Path) -> None:
        """Mix of spread and single pages processed correctly."""
        hash_dir = tmp_path / "abc123"
        pages_dir = hash_dir / "pages"
        pages_dir.mkdir(parents=True)

        spread = Image.new("RGB", (2000, 1000), color="white")
        spread.save(pages_dir / "page_0001.png")

        single = Image.new("RGB", (800, 1200), color="white")
        single.save(pages_dir / "page_0002.png")

        result = split_spread_pages(str(pages_dir))

        # Should have 3 files: 2 from spread + 1 single
        assert len(result) == 3
        assert (pages_dir / "page_0001_L.png").exists()
        assert (pages_dir / "page_0001_R.png").exists()
        assert (pages_dir / "page_0002.png").exists()

    def test_iterative_split_with_new_settings(self, tmp_path: Path) -> None:
        """Re-running split uses originals and applies new settings."""
        hash_dir = tmp_path / "abc123"
        pages_dir = hash_dir / "pages"
        originals_dir = hash_dir / "originals"
        pages_dir.mkdir(parents=True)

        spread = Image.new("RGB", (2000, 1000), color="white")
        spread.save(pages_dir / "page_0001.png")

        # First run
        split_spread_pages(str(pages_dir), left_trim_pct=0.0)
        first_left = Image.open(pages_dir / "page_0001_L.png")
        first_width = first_left.size[0]
        first_left.close()

        # Second run with different settings
        split_spread_pages(str(pages_dir), left_trim_pct=0.1)
        second_left = Image.open(pages_dir / "page_0001_L.png")
        second_width = second_left.size[0]
        second_left.close()

        # Second run should have smaller width due to trim
        assert second_width < first_width
        # Original still preserved
        assert (originals_dir / "page_0001.png").exists()

    def test_empty_directory(self, tmp_path: Path) -> None:
        """Empty directory returns empty list."""
        hash_dir = tmp_path / "abc123"
        pages_dir = hash_dir / "pages"
        pages_dir.mkdir(parents=True)

        result = split_spread_pages(str(pages_dir))
        assert result == []


class TestRenumberPages:
    """Tests for renumber_pages() sequential numbering."""

    def test_renumber_split_pages(self, tmp_path: Path) -> None:
        """Split pages are renumbered sequentially."""
        # Create L/R files
        Image.new("RGB", (100, 100)).save(tmp_path / "page_0001_L.png")
        Image.new("RGB", (100, 100)).save(tmp_path / "page_0001_R.png")
        Image.new("RGB", (100, 100)).save(tmp_path / "page_0002.png")

        result = renumber_pages(str(tmp_path))

        assert len(result) == 3
        assert (tmp_path / "page_0001.png").exists()
        assert (tmp_path / "page_0002.png").exists()
        assert (tmp_path / "page_0003.png").exists()

        # Old names should not exist
        assert not (tmp_path / "page_0001_L.png").exists()
        assert not (tmp_path / "page_0001_R.png").exists()

    def test_renumber_preserves_order(self, tmp_path: Path) -> None:
        """Renumbering preserves alphabetical order."""
        # Create files in specific order
        Image.new("RGB", (100, 100)).save(tmp_path / "page_0001_L.png")
        Image.new("RGB", (100, 100)).save(tmp_path / "page_0001_R.png")
        Image.new("RGB", (100, 100)).save(tmp_path / "page_0002_L.png")
        Image.new("RGB", (100, 100)).save(tmp_path / "page_0002_R.png")

        result = renumber_pages(str(tmp_path))

        # Should be sorted: 0001_L, 0001_R, 0002_L, 0002_R → 0001, 0002, 0003, 0004
        assert len(result) == 4
        assert [p.name for p in result] == [
            "page_0001.png",
            "page_0002.png",
            "page_0003.png",
            "page_0004.png",
        ]

    def test_renumber_empty_directory(self, tmp_path: Path) -> None:
        """Empty directory returns empty list."""
        result = renumber_pages(str(tmp_path))
        assert result == []
