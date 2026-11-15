"""OCR の実行時に決まる本のメタ情報（紙面のページ番号・章名）.

柱・ノンブルは本文から除くが、そこにしか無い情報（紙面のページ番号、章名）は
ここに残して、章分割や後段のツールが使えるようにする（#99）。

``book_meta.json``:
    {
      "page_numbers": {"0021": 22, ...},   # 原ページ → 紙面のページ番号
      "chapter_titles": {"1": "データ分析を設計する", ...},
      "fallback_pages": ["0014", ...]      # ページ全体 OCR にフォールバックしたページ
    }
"""

from __future__ import annotations

import json
from pathlib import Path

FILE_NAME = "book_meta.json"


def write_book_meta(
    output_dir: Path,
    page_numbers: dict[str, int],
    chapter_titles: dict[int, str],
    fallback_pages: list[str] | None = None,
) -> Path | None:
    """``book_meta.json`` を書き出す。書くものが無ければ何もしない."""
    if not page_numbers and not chapter_titles and not fallback_pages:
        return None
    target = output_dir / FILE_NAME
    payload = {
        "page_numbers": dict(sorted(page_numbers.items())),
        "chapter_titles": {str(number): chapter_titles[number] for number in sorted(chapter_titles)},
        "fallback_pages": sorted(fallback_pages or []),
    }
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return target


def load_book_meta(book_md: Path) -> dict:
    """``book_meta.json`` を読む。book.md の隣か、その 1 つ下の ``ocr_output/`` を探す.

    Returns:
        ``{"page_numbers": {...}, "chapter_titles": {...}}``。無ければ空の辞書を返す。
    """
    empty: dict = {"page_numbers": {}, "chapter_titles": {}, "fallback_pages": []}
    for candidate in (book_md.parent / FILE_NAME, book_md.parent / "ocr_output" / FILE_NAME):
        if not candidate.exists():
            continue
        data = json.loads(candidate.read_text(encoding="utf-8"))
        page_numbers = {
            str(page): int(number) for page, number in (data.get("page_numbers") or {}).items() if str(number).isdigit()
        }
        chapter_titles = {
            int(number): str(title)
            for number, title in (data.get("chapter_titles") or {}).items()
            if str(number).isdigit()
        }
        return {
            "page_numbers": page_numbers,
            "chapter_titles": chapter_titles,
            "fallback_pages": [str(page) for page in (data.get("fallback_pages") or [])],
        }
    return empty
