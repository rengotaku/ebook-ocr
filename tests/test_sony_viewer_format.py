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

    def test_has_one_entry_per_tile(self):
        order, _ = fmt.build_sample_order("12345", 1, 768, 1280)
        assert len(order) == 16 * 27

    def test_requires_digits_in_iid(self):
        with pytest.raises(ValueError):
            fmt.build_sample_order("abcdef", 3, 768, 1280)

    def test_matches_viewer_for_comic_pages(self):
        # ビューアの retrieveHeader（contents.js）をそのまま実行した結果の先頭 20 要素。
        # 並べ替えのたびに乱数列を作り直す実装でないと 20 個目（横の端の列）からずれる。
        order, side = fmt.build_sample_order("BT000038521500100101550001", 2, 960, 1280, 48)
        assert side == 48
        assert order[:20] == [
            5,
            47,
            68,
            110,
            131,
            173,
            194,
            236,
            257,
            300,
            321,
            363,
            384,
            426,
            447,
            489,
            510,
            26,
            89,
            119,
        ]
        assert order[-5:] == [521, 532, 520, 531, 539]


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
    def test_webp_comic_uses_large_tiles(self):
        assert fmt.side_length_for("comic", "image/webp") == 152

    def test_jpeg_comic_uses_default_tiles(self):
        # ビューアは WebP のマンガだけ 152。JPEG のマンガは 48。
        assert fmt.side_length_for("comic", "image/jpeg") == 48

    def test_text_and_unknown(self):
        assert fmt.side_length_for("text", "image/webp") == 48
        assert fmt.side_length_for(None) == 48


class TestDescrambleToDisplaySize:
    """配信画像がメタの表示サイズより大きいときの並べ替え（ビューアと同じ手順）."""

    @staticmethod
    def _tiled_image() -> Image.Image:
        image = Image.new("RGBA", (96, 96))
        colors = [(255, 0, 0, 255), (0, 255, 0, 255), (0, 0, 255, 255), (255, 255, 0, 255)]
        for index, color in enumerate(colors):
            image.paste(color, ((index % 2) * 48, (index // 2) * 48, (index % 2) * 48 + 48, (index // 2) * 48 + 48))
        return image

    @staticmethod
    def _scramble(image: Image.Image, order: list[int], side: int) -> Image.Image:
        scrambled = Image.new("RGBA", image.size)
        for index, target in enumerate(order):
            column, row = index % 2, index // 2
            box = ((target % 2) * side, (target // 2) * side, (target % 2) * side + side, (target // 2) * side + side)
            scrambled.paste(image.crop(box), (column * side, row * side))
        return scrambled

    @staticmethod
    def _widen(scrambled: Image.Image, extra: int) -> Image.Image:
        # ビューアの想定: タイルの間に余り extra を均等に挟んだ画像が配信される。
        widened = Image.new("RGBA", (scrambled.width + extra, scrambled.height + extra))
        step = 48 + extra
        for index in range(4):
            column, row = index % 2, index // 2
            box = (column * 48, row * 48, column * 48 + 48, row * 48 + 48)
            widened.paste(scrambled.crop(box), (column * step, row * step))
        return widened

    def test_restores_original_from_larger_image(self):
        order = [2, 0, 3, 1]
        original = self._tiled_image()
        served = self._widen(self._scramble(original, order, 48), extra=10)
        assert served.size == (106, 106)
        restored = fmt.descramble(served, order, 48, size=(96, 96))
        assert list(restored.getdata()) == list(original.getdata())

    def test_uses_image_size_when_size_is_omitted(self):
        order = [2, 0, 3, 1]
        original = self._tiled_image()
        scrambled = self._scramble(original, order, 48)
        restored = fmt.descramble(scrambled, order, 48)
        assert list(restored.getdata()) == list(original.getdata())


class TestDeduplicate:
    @staticmethod
    def _page(index: int, width: int, content_id: str = "cid"):
        from extract_pages import Page

        return Page(
            content_id=content_id,
            index=index,
            width=width,
            height=width * 4 // 3,
            scrambled=False,
            encrypted=False,
            image=b"",
        )

    def test_keeps_largest_image_for_duplicate_index(self):
        from extract_pages import deduplicate

        pages = [self._page(1, 960), self._page(0, 960), self._page(1, 144)]
        result = deduplicate(pages)
        assert [page.index for page in result] == [0, 1]
        assert result[1].width == 960

    def test_keeps_larger_image_even_when_it_comes_first(self):
        from extract_pages import deduplicate

        pages = [self._page(2, 960), self._page(2, 144)]
        assert deduplicate(pages)[0].width == 960

    def test_does_not_merge_pages_of_different_books(self):
        from extract_pages import deduplicate

        pages = [self._page(0, 960, "book-a"), self._page(0, 960, "book-b")]
        assert len(deduplicate(pages)) == 2
