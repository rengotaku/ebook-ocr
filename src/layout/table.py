"""yomitoku の表構造から Markdown の表を組み立てる.

yomitoku の ``TableStructureRecognizer`` は、行・列・セル（``row`` ``col``
``col_span`` ``row_span`` ``contents``）を返す。セルは位置を持っているので、
空のセルがあっても列を詰めずにそのまま並べる（詰めると別の列に値が入る）。
"""

from __future__ import annotations

# これ未満は表として扱わない（1 行・1 列はただのテキスト）
MIN_ROWS = 2
MIN_COLS = 2

# 表として組み立てられなかったときに付ける注記
UNSTRUCTURED_NOTE = "表として組み立てられなかったため、図として残しています"

# Markdown の表として出す条件。崩れた表（Excel のスクリーンショットなど）は
# 本文より読みにくくなるので、図のまま残す（#101）。
MIN_FILL_RATIO = 0.6
MAX_EMPTY_ROW_RATIO = 0.2
MAX_COLS = 10


def table_grid(table) -> list[list[str]]:
    """セルを行列に並べる.

    結合セル（``row_span`` ``col_span``）は左上のマスにだけ文字を置き、
    残りのマスは空にする。空のマスを詰めないので、列の対応が崩れない。
    """
    rows = int(getattr(table, "n_row", 0) or 0)
    cols = int(getattr(table, "n_col", 0) or 0)
    if rows <= 0 or cols <= 0:
        return []

    grid = [["" for _ in range(cols)] for _ in range(rows)]
    for cell in getattr(table, "cells", None) or []:
        row = int(getattr(cell, "row", 0) or 0) - 1
        col = int(getattr(cell, "col", 0) or 0) - 1
        if not (0 <= row < rows and 0 <= col < cols):
            continue
        grid[row][col] = (getattr(cell, "contents", "") or "").strip()
    return _trim_empty_edges(grid)


def _trim_empty_edges(grid: list[list[str]]) -> list[list[str]]:
    """先頭・末尾の空行を落とす（表の余白で崩れ判定しないように）."""
    while grid and not any(grid[0]):
        grid = grid[1:]
    while grid and not any(grid[-1]):
        grid = grid[:-1]
    return grid


def _cell_text(text: str) -> str:
    """Markdown のセルに入れられる形にする."""
    return text.replace("|", "\\|").replace("\n", "<br>").strip()


def table_to_markdown(table) -> str:
    """表を Markdown にする。表として組み立てられないときは空文字.

    先頭の行を見出し行として扱う（Markdown の表は見出し行が必須）。
    """
    grid = table_grid(table)
    if len(grid) < MIN_ROWS:
        return ""
    width = max((len(row) for row in grid), default=0)
    if width < MIN_COLS:
        return ""
    rows = [row + [""] * (width - len(row)) for row in grid]

    lines = ["| " + " | ".join(_cell_text(text) for text in rows[0]) + " |"]
    lines.append("|" + "|".join(" --- " for _ in range(width)) + "|")
    for row in rows[1:]:
        lines.append("| " + " | ".join(_cell_text(text) for text in row) + " |")
    return "\n".join(lines)


def is_markdown_ready(grid: list[list[str]]) -> bool:
    """崩れていない表かどうか.

    - 空のセルが多すぎる（半分近く空）
    - 空の行が多すぎる
    - 列が多すぎる（Excel のスクリーンショットは 10 列を超える）
    """
    if not grid:
        return False
    cells = [cell for row in grid for cell in row]
    filled = sum(1 for cell in cells if cell)
    if not cells or filled / len(cells) < MIN_FILL_RATIO:
        return False
    empty_rows = sum(1 for row in grid if not any(row))
    if empty_rows / len(grid) > MAX_EMPTY_ROW_RATIO:
        return False
    return max(len(row) for row in grid) <= MAX_COLS


def unstable_table_boxes(tables: list) -> list[list[int]]:
    """表として組み立てられなかった表の bbox を返す（図として残す対象）."""
    boxes = []
    for table in tables or []:
        box = getattr(table, "box", None)
        if not box:
            continue
        if not is_stable_table(table):
            boxes.append([int(value) for value in box])
    return boxes


def is_stable_table(table) -> bool:
    """Markdown の表として出せる表かどうか."""
    return bool(table_to_markdown(table)) and is_markdown_ready(table_grid(table))


def table_regions(tables: list) -> list[dict]:
    """yomitoku の表から TABLE 領域を作る。崩れている表は捨てる（図として残す）."""
    regions: list[dict] = []
    for table in tables or []:
        if not is_stable_table(table):
            continue
        markdown = table_to_markdown(table)
        if not markdown:
            continue
        box = getattr(table, "box", None)
        if not box:
            continue
        regions.append(
            {
                "type": "TABLE",
                "label": "table",
                "bbox": [int(value) for value in box],
                "confidence": 1.0,
                "text": markdown,
            }
        )
    return regions
