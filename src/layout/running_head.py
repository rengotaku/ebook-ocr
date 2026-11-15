"""柱・ノンブル（ページ上部・下部に繰り返し出る行）を本文から除く.

ページの上端・下端に出る行だけを対象にする。同じ文字列が本文の途中に出てきても消さない。
どの行を柱とみなすかは 2 通りで決める:

- ページ番号だけの行（``22`` ``ⅲ`` など）
- 同じ行が複数ページの上端・下端に繰り返し出るもの（``22 第1章 データ分析を設計する`` など）

ページ全体 OCR にフォールバックしたページは領域の座標が無いので、先頭・末尾の行だけを見て落とす。
"""

from __future__ import annotations

import re

# ページ上端からこの割合までを「上部」、この割合より下を「下部」とみなす
TOP_BAND_RATIO = 0.08
BOTTOM_BAND_RATIO = 0.90

# 同じ行がこのページ数以上に出たら柱とみなす
MIN_PAGES = 3

# ページ番号だけの行（アラビア数字・ローマ数字）
PAGE_NUMBER_ONLY_RE = re.compile(r"^[\d０-９Ⅰ-ⅿivxlcIVXLC]{1,5}$")

# 柱の繰り返しを同じ文字列に寄せるために落とす文字（数字・空白・約物）
_NORMALIZE_RE = re.compile(r"[\d０-９Ⅰ-ⅿ\s　・、。,.．:：;；/／|｜\-—–ー〜()（）\[\]「」『』]+")


def normalize_running_head_text(text: str) -> str:
    """柱を見比べるための正規化（数字・空白・約物を落とす）.

    ``22 第1章 データ分析を設計する`` と ``第1章 データ分析を設計する 23`` が
    同じ文字列になる。
    """
    return _NORMALIZE_RE.sub("", text)


def in_margin_band(region: dict, page_height: int) -> bool:
    """領域がページの上端・下端の帯に入っているか."""
    if page_height <= 0:
        return False
    _, y1, _, y2 = region["bbox"]
    return y2 <= page_height * TOP_BAND_RATIO or y1 >= page_height * BOTTOM_BAND_RATIO


def find_running_heads(layout_data: dict) -> frozenset[str]:
    """複数ページの上端・下端に繰り返し出る行を集める.

    Args:
        layout_data: ``{page_name: {"regions": [...], "page_size": [w, h]}}``

    Returns:
        正規化した文字列の集合。``is_running_head()`` に渡す。
    """
    counts: dict[str, int] = {}
    for page in layout_data.values():
        page_size = page.get("page_size") or [0, 0]
        height = page_size[1] if len(page_size) > 1 else 0
        keys_on_page = set()
        for region in page.get("regions", []):
            if region.get("type") in ("FIGURE", "CODE", "ABANDON"):
                continue
            text = (region.get("text") or "").strip()
            if not text or not in_margin_band(region, height):
                continue
            key = normalize_running_head_text(text)
            if key:
                keys_on_page.add(key)
        for key in keys_on_page:
            counts[key] = counts.get(key, 0) + 1

    return frozenset(key for key, count in counts.items() if count >= MIN_PAGES)


def is_running_head(region: dict, page_size: tuple[int, int] | list[int], running_heads: frozenset[str]) -> bool:
    """領域が柱・ノンブルかどうか.

    ページの上端・下端の帯にある行だけを対象にする。帯の外にある同じ文字列は本文として残す。
    """
    height = page_size[1] if len(page_size) > 1 else 0
    if not in_margin_band(region, height):
        return False

    text = (region.get("text") or "").strip()
    if not text:
        return False
    if PAGE_NUMBER_ONLY_RE.match(text):
        return True
    return normalize_running_head_text(text) in running_heads


# 柱から紙面のページ番号（ノンブル）を取り出すための形。
# ``22 第1章 データ分析を設計する`` の先頭、``第1章 データ分析を設計する 23`` の末尾。
_PRINTED_NUMBER_LEADING_RE = re.compile(r"^(\d{1,4})\s+\S")
_PRINTED_NUMBER_TRAILING_RE = re.compile(r"\S\s+(\d{1,4})$")


def printed_page_number(region: dict) -> int | None:
    """柱・ノンブルから紙面のページ番号を取り出す.

    アラビア数字のときだけ返す。ローマ数字（前付の ``ⅲ`` など）や、
    番号が読み取れなかったものは None（推測で埋めない）。
    """
    text = (region.get("text") or "").strip()
    if not text:
        return None
    if text.isdigit() and len(text) <= 4:
        return int(text)
    for pattern in (_PRINTED_NUMBER_LEADING_RE, _PRINTED_NUMBER_TRAILING_RE):
        match = pattern.search(text)
        if match:
            return int(match.group(1))
    return None


# 柱から章番号と章名を取り出すための形（``22 第1章 データ分析を設計する``）
_CHAPTER_HEAD_RE = re.compile(r"^\d{0,3}\s*第\s*(\d+)\s*章\s+(\S.*?)(?:\s+\d{1,3})?\s*$")


def chapter_title_from_region(region: dict) -> tuple[int, str] | None:
    """柱から章番号と章名を取り出す。章の柱でなければ None."""
    text = (region.get("text") or "").strip()
    match = _CHAPTER_HEAD_RE.match(text)
    if not match:
        return None
    return int(match.group(1)), match.group(2).strip()


def _is_running_head_line(line: str, running_heads: frozenset[str]) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    if PAGE_NUMBER_ONLY_RE.match(stripped):
        return True
    return normalize_running_head_text(stripped) in running_heads


def strip_running_head_lines(
    text: str,
    running_heads: frozenset[str],
    page_heads: frozenset[str] = frozenset(),
) -> str:
    """ページ全体 OCR の結果から、柱・ノンブル行を落とす。

    ``page_heads`` はレイアウト側で座標から柱と判定した行（そのページの実物）。
    ページ全体 OCR では柱が途中の行に来ることがあるので、これは位置を問わず落とす。
    ``running_heads`` は本全体で繰り返す行だが、こちらは座標が無いので
    先頭・末尾の行にだけ適用する（本文の途中の同じ文字列は残す）。
    """
    lines = [
        line for line in text.split("\n") if not (line.strip() and normalize_running_head_text(line) in page_heads)
    ]

    start = 0
    end = len(lines)
    while start < end and (not lines[start].strip() or _is_running_head_line(lines[start], running_heads)):
        start += 1
    while end > start and (not lines[end - 1].strip() or _is_running_head_line(lines[end - 1], running_heads)):
        end -= 1
    return "\n".join(lines[start:end])
