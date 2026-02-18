"""Tests for src.deduplicate frame deduplication logic.

Phase 4 RED tests for deduplicate_frames().
"""

from __future__ import annotations

from pathlib import Path

from PIL import Image

from src.preprocessing.deduplicate import deduplicate_frames


class TestDeduplicateIdenticalImages:
    """同一画像の重複検出。"""

    def test_deduplicate_identical_images(self, tmp_path: Path) -> None:
        """同一画像を3つ作成し、deduplicate_frames() が1ページのみ返すことを検証。"""
        frame_dir = tmp_path / "frames"
        frame_dir.mkdir()
        output_dir = tmp_path / "output"

        # 同一の灰色画像を3つ作成
        img = Image.new("RGB", (200, 150), color=(128, 128, 128))
        for i in range(1, 4):
            img.save(frame_dir / f"frame_{i:04d}.png")

        result = deduplicate_frames(str(frame_dir), str(output_dir))

        assert len(result) == 1, (
            f"Identical images should deduplicate to 1, got {len(result)}"
        )
        assert all(isinstance(p, Path) for p in result)


class TestDeduplicateDifferentImages:
    """異なる画像の非重複判定。"""

    def test_deduplicate_different_images(self, tmp_path: Path) -> None:
        """十分に異なる画像を3つ作成し、全てが保持されることを検証。"""
        import random

        from PIL import ImageDraw

        frame_dir = tmp_path / "frames"
        frame_dir.mkdir()
        output_dir = tmp_path / "output"

        # ランダムシードを固定して再現性を確保
        random.seed(42)

        # 画像1: ランダムな矩形パターン
        img1 = Image.new("RGB", (200, 150), color=(255, 255, 255))
        draw1 = ImageDraw.Draw(img1)
        for _ in range(10):
            x1, y1 = random.randint(0, 180), random.randint(0, 130)
            x2, y2 = x1 + random.randint(10, 20), y1 + random.randint(10, 20)
            draw1.rectangle([x1, y1, x2, y2], fill=(0, 0, 0))
        img1.save(frame_dir / "frame_0001.png")

        # 画像2: ランダムな円形パターン
        img2 = Image.new("RGB", (200, 150), color=(255, 255, 255))
        draw2 = ImageDraw.Draw(img2)
        for _ in range(8):
            x, y = random.randint(10, 190), random.randint(10, 140)
            r = random.randint(5, 15)
            draw2.ellipse([x-r, y-r, x+r, y+r], fill=(0, 0, 0))
        img2.save(frame_dir / "frame_0002.png")

        # 画像3: ランダムな線パターン
        img3 = Image.new("RGB", (200, 150), color=(255, 255, 255))
        draw3 = ImageDraw.Draw(img3)
        for _ in range(15):
            x1, y1 = random.randint(0, 200), random.randint(0, 150)
            x2, y2 = random.randint(0, 200), random.randint(0, 150)
            draw3.line([x1, y1, x2, y2], fill=(0, 0, 0), width=2)
        img3.save(frame_dir / "frame_0003.png")

        result = deduplicate_frames(str(frame_dir), str(output_dir))

        assert len(result) == 3, (
            f"Different images should all be kept, got {len(result)} instead of 3"
        )


class TestDeduplicateEmptyDir:
    """空ディレクトリに対する処理。"""

    def test_deduplicate_empty_dir(self, tmp_path: Path) -> None:
        """空のディレクトリに対して空リストが返ることを検証。"""
        frame_dir = tmp_path / "frames"
        frame_dir.mkdir()
        output_dir = tmp_path / "output"

        result = deduplicate_frames(str(frame_dir), str(output_dir))

        assert result == [], f"Empty dir should return [], got {result}"


class TestDeduplicateOutputFiles:
    """出力ファイルの命名規則。"""

    def test_output_files_named_page(self, tmp_path: Path) -> None:
        """出力ファイルが page_NNNN.png の命名規則に従うことを検証。"""
        frame_dir = tmp_path / "frames"
        frame_dir.mkdir()
        output_dir = tmp_path / "output"

        img = Image.new("RGB", (200, 150), color=(255, 0, 0))
        img.save(frame_dir / "frame_0001.png")

        result = deduplicate_frames(str(frame_dir), str(output_dir))

        assert len(result) == 1
        assert result[0].name == "page_0001.png"


class TestDeduplicateContextManager:
    """リソース管理パターンの検証 (FR-008)。"""

    def test_context_manager_usage(self) -> None:
        """Image.open() がコンテキストマネージャで使われていることを検証。"""
        source = Path("src/preprocessing/deduplicate.py").read_text(encoding="utf-8")
        assert "with Image.open" in source, (
            "Image.open should use context manager (with statement) "
            "to ensure file handles are properly closed"
        )
