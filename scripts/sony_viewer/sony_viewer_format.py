"""Sony 電子書籍ビューアの配信データを扱う純粋関数群.

ビューア（viewer.ebookstore.sony.jp）はページ画像を次の形で返す.

1. ページ束
   ``[uint32 LE サイズ][データ]`` の繰り返し。末尾に全体サイズ（4 バイト）が付く。

2. ページヘッダ
   ``[uint32 サイズ][meta JSON][uint32 ページサイズ][ページデータ]`` の並びで
   ヘッダ束に格納される。``isCrypted`` のページはページデータの先頭に 20 バイトの
   MAC が付く。

3. ページ画像
   暗号化されている場合はページヘッダから取り出した鍵で復号する。復号後は
   通常の RIFF/WEBP だが、``side`` ピクセル四方のタイルが並べ替えられている。
"""

from __future__ import annotations

import json
import math
import struct
from typing import Iterable

from PIL import Image

MAC_SIZE = 20
DEFAULT_SIDE_LENGTH = 48
COMIC_SIDE_LENGTH = 152

# クライアント側で並べ替え順を作るときの固定数列（ビューアの実装と同じ値）
_PRE_SHARED_NUMBERS = [19, 20, 14, 1, 5, 2, 4, 15, 9, 17, 8, 16, 18, 11, 10, 7, 12, 6, 13, 3]


def split_bundle(data: bytes) -> list[bytes]:
    """ページ束を 1 ページ分ずつのバイト列に分解する.

    末尾の全体サイズ（4 バイト）と、途中で切れている不完全な要素は捨てる。
    """
    pages = []
    offset = 0
    while offset + 4 <= len(data):
        size = struct.unpack_from("<I", data, offset)[0]
        start = offset + 4
        if start + size > len(data):
            break
        pages.append(data[start : start + size])
        offset = start + size
    return pages


def parse_meta(payload: bytes) -> dict:
    """ヘッダ束に入っている 1 ページ分のメタ JSON を読む."""
    return json.loads(payload.decode("utf-8"))


def header_ciphertext(page: bytes) -> bytes:
    """ページデータから、サイズと MAC を除いた暗号文を取り出す.

    ページデータは ``[uint32 ヘッダサイズ][20 バイト MAC][暗号文]``。
    """
    header_size = struct.unpack_from("<I", page, 0)[0]
    return page[4 + MAC_SIZE : header_size + 4]


def unpack_order(blob: bytes) -> tuple[list[int], int]:
    """並べ替え順を展開する.

    先頭 uint16 が順序表のバイト長（要素数の 2 倍）、次の uint16 がタイルの一辺、
    以降が uint16 の並び。
    """
    length = struct.unpack_from("<H", blob, 0)[0] // 2
    side = struct.unpack_from("<H", blob, 2)[0]
    order = list(struct.unpack_from("<%dH" % length, blob, 4))
    return order, side


def build_sample_order(
    iid: str, seed_shift: int, width: int, height: int, side: int = DEFAULT_SIDE_LENGTH
) -> tuple[list[int], int]:
    """暗号化されていないページの並べ替え順を、ビューアと同じ手順で作る.

    ``iid`` の数字と ``seed_shift``（ビューアの URL にある ``v``）で擬似乱数を初期化する。
    """
    seeds = [int(char) for char in str(iid) if char in "123456789"]
    if not seeds:
        raise ValueError("iid に 1〜9 の数字が含まれていない")
    for _ in range(seed_shift % len(seeds)):
        seeds.append(seeds.pop(0))

    def shuffle(indices: list[int]) -> list[int]:
        # ビューアは並べ替えのたびに乱数列を作り直す（続きから使うと順序がずれる）
        shared_iter = _cycle(_PRE_SHARED_NUMBERS)
        seed_iter = _cycle(seeds)
        keyed = sorted((next(shared_iter) + next(seed_iter), index) for index in indices)
        return [index for _, index in keyed]

    columns = math.ceil(width / side)
    rows = math.ceil(height / side)

    main: list[int] = []
    horizontal_tail: list[int] = []
    for row in range(rows - 1):
        line = list(range(row * columns, (row + 1) * columns))
        main.extend(line[:-1])
        horizontal_tail.append(line[-1])
    # 最後のタイルは別に足すので、ここでは含めない（ビューアの実装と同じ）
    vertical_tail = list(range((rows - 1) * columns, rows * columns - 1))

    main = shuffle(main)
    horizontal_tail = shuffle(horizontal_tail)
    vertical_tail = shuffle(vertical_tail)

    order: list[int] = []
    for row in range(rows - 1):
        order.extend(main[: columns - 1])
        main = main[columns - 1 :]
        order.append(horizontal_tail[row])
    order.extend(vertical_tail)
    order.append(columns * rows - 1)
    return order, side


def descramble(image: Image.Image, order: Iterable[int], side: int) -> Image.Image:
    """並べ替えられたタイルを元の位置に戻す.

    ビューアの draw() と同じく、並べ替え後の ``index`` 番目のタイルを
    ``order[index]`` 番目の位置へ移す。
    """
    width, height = image.size
    columns = math.ceil(width / side)
    rows = math.ceil(height / side)
    last_width = width - (columns - 1) * side
    last_height = height - (rows - 1) * side

    source = image.convert("RGBA")
    fixed = Image.new("RGBA", (width, height))
    filled: set[tuple[int, int]] = set()

    for index, target in enumerate(order):
        if index >= columns * rows:
            break
        dst_column, dst_row = target % columns, target // columns
        if (dst_column, dst_row) in filled:
            continue
        src_column, src_row = index % columns, index // columns
        tile_width = last_width if dst_column == columns - 1 else side
        tile_height = last_height if dst_row == rows - 1 else side
        box = (
            src_column * side,
            src_row * side,
            min(src_column * side + tile_width, width),
            min(src_row * side + tile_height, height),
        )
        tile = source.crop(box)
        fixed.paste(tile, (dst_column * side, dst_row * side))
        filled.add((dst_column, dst_row))

    missing = columns * rows - len(filled)
    if missing:
        raise ValueError(f"タイルが {missing} 個埋まっていない（順序表が壊れている）")
    return fixed


def _cycle(values: list[int]) -> Iterable[int]:
    while True:
        for value in values:
            yield value


def side_length_for(book_type: str | None, mimetype: str | None = None) -> int:
    """書籍種別と画像形式からタイルの一辺を決める.

    ビューアの ``retrieveHeader`` は ``image/webp`` のマンガだけ 152 を使い、
    それ以外（JPEG のマンガを含む）は 48 にする。
    """
    if book_type == "comic" and mimetype == "image/webp":
        return COMIC_SIDE_LENGTH
    return DEFAULT_SIDE_LENGTH
