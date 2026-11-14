"""Sony ビューアの配信データを扱う関数のテスト."""

from __future__ import annotations

import struct
import sys
from pathlib import Path

import pytest
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "sony_viewer"))

import sony_viewer_format as fmt  # noqa: E402


def pack_bundle(items: list[bytes]) -> bytes:
    body = b"".join(struct.pack("<I", len(item)) + item for item in items)
    return body + struct.pack("<I", len(body))


class TestSplitBundle:
    def test_splits_items_and_drops_trailer(self):
        data = pack_bundle([b"aa", b"bbb"])
        assert fmt.split_bundle(data) == [b"aa", b"bbb"]

    def test_ignores_truncated_tail(self):
        data = struct.pack("<I", 10) + b"short"
        assert fmt.split_bundle(data) == []

    def test_empty_body(self):
        assert fmt.split_bundle(b"") == []


class TestHeaderCiphertext:
    def test_drops_size_and_mac(self):
        cipher = b"0123456789abcdef"
        page = struct.pack("<I", 20 + len(cipher)) + bytes(20) + cipher
        assert fmt.header_ciphertext(page) == cipher

    def test_respects_declared_size(self):
        cipher = b"0123456789abcdef"
        page = struct.pack("<I", 20 + len(cipher)) + bytes(20) + cipher + b"trailing"
        assert fmt.header_ciphertext(page) == cipher


class TestUnpackOrder:
    def test_reads_side_and_order(self):
        order = [3, 0, 2, 1]
        blob = struct.pack("<HH", len(order) * 2, 48) + struct.pack("<4H", *order)
        assert fmt.unpack_order(blob) == (order, 48)


class TestBuildSampleOrder:
    def test_returns_full_permutation(self):
        order, side = fmt.build_sample_order("LT000227628003515577550001", 3, 768, 1280)
        assert side == 48
        assert set(order) == set(range(16 * 27))

    def test_last_tile_appears_twice(self):
        order, _ = fmt.build_sample_order("12345", 1, 768, 1280)
        assert len(order) == 16 * 27 + 1

    def test_requires_digits_in_iid(self):
        with pytest.raises(ValueError):
            fmt.build_sample_order("abcdef", 3, 768, 1280)


class TestDescramble:
    @staticmethod
    def _tiled_image() -> Image.Image:
        image = Image.new("RGBA", (96, 96))
        for index, color in enumerate([(255, 0, 0, 255), (0, 255, 0, 255), (0, 0, 255, 255), (255, 255, 0, 255)]):
            column, row = index % 2, index // 2
            image.paste(color, (column * 48, row * 48, column * 48 + 48, row * 48 + 48))
        return image

    @staticmethod
    def _scramble(image: Image.Image, order: list[int], side: int) -> Image.Image:
        columns = image.width // side
        scrambled = Image.new("RGBA", image.size)
        for index, target in enumerate(order):
            column, row = index % columns, index // columns
            src_column, src_row = target % columns, target // columns
            box = (src_column * side, src_row * side, src_column * side + side, src_row * side + side)
            scrambled.paste(image.crop(box), (column * side, row * side))
        return scrambled

    def test_restores_original(self):
        order = [2, 0, 3, 1]
        original = self._tiled_image()
        scrambled = self._scramble(original, order, 48)
        restored = fmt.descramble(scrambled, order, 48)
        assert list(restored.getdata()) == list(original.getdata())

    def test_raises_when_tiles_are_missing(self):
        with pytest.raises(ValueError):
            fmt.descramble(self._tiled_image(), [0, 1], 48)


class TestDefaultOutput:
    def test_sits_next_to_the_har(self):
        from extract_pages import default_output

        assert default_output(Path("/tmp/book.har")) == Path("/tmp/book.har_webp")


class TestSideLength:
    def test_text_and_comic(self):
        assert fmt.side_length_for("text") == 48
        assert fmt.side_length_for("comic") == 152
        assert fmt.side_length_for(None) == 48
