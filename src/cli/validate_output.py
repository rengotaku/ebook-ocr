"""CLI: 出力（book.md / 章ファイル）の異常を検出する.

見つけるだけで、直さない。終了コードは 0（警告として使う）。
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from src.book_meta import load_book_meta
from src.output_checks import check_all, split_pages, summarize

# 表示する順番
KIND_ORDER = (
    "empty_page",
    "missing_region",
    "broken_paragraph",
    "page_end_cut",
    "running_head",
    "duplicate_line",
    "broken_heading",
)

KIND_LABELS = {
    "empty_page": "ページがまるごと空",
    "missing_region": "layout.json にある本文が出力に無い",
    "broken_paragraph": "文の途中で切れた段落",
    "page_end_cut": "ページ末尾で切れた段落（紙面どおりのことがある）",
    "running_head": "柱・ノンブルの混入",
    "duplicate_line": "同じ行の重複",
    "broken_heading": "見出しの異常",
}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="book.md の異常を検出する（直さない）")
    parser.add_argument("book_md", type=Path, help="検証する Markdown（ページマーカー入り）")
    parser.add_argument("--layout", type=Path, help="layout.json（本文の欠落を見るとき）")
    parser.add_argument("--json", type=Path, help="検出結果の JSON を書き出す先")
    parser.add_argument("--max-show", type=int, default=10, help="種類ごとに表示する件数（既定: 10）")
    args = parser.parse_args(argv)

    if not args.book_md.exists():
        print(f"book.md が見つからない: {args.book_md}", file=sys.stderr)
        return 1

    pages = split_pages(args.book_md.read_text(encoding="utf-8"))
    if not pages:
        print("ページマーカー（--- 0085 ---）が無い", file=sys.stderr)
        return 1

    layout = None
    if args.layout and args.layout.exists():
        layout = json.loads(args.layout.read_text(encoding="utf-8"))

    book_meta = load_book_meta(args.book_md)
    issues = check_all(pages, layout, book_meta)
    counts = summarize(issues)

    print(f"検証: {args.book_md}（{len(pages)} ページ）")
    if layout is None:
        print("  layout.json が無いので、本文の欠落は見ていない")
    fallback_pages = book_meta.get("fallback_pages") or []
    if fallback_pages:
        print(f"  ページ全体 OCR のページ {len(fallback_pages)} 件は本文の欠落の判定から除いた")
    for kind in KIND_ORDER:
        print(f"  {KIND_LABELS[kind]:32} {counts.get(kind, 0):5}")
    print(f"  {'合計':32} {len(issues):5}")

    for kind in KIND_ORDER:
        rows = [issue for issue in issues if issue.kind == kind]
        if not rows:
            continue
        print(f"\n[{KIND_LABELS[kind]}]")
        for issue in rows[: max(args.max_show, 0)]:
            print(f"  p.{issue.page}  {issue.detail}")
        if len(rows) > args.max_show:
            print(f"  ... ほか {len(rows) - args.max_show} 件")

    if args.json:
        payload = {
            "book": str(args.book_md),
            "pages": len(pages),
            "counts": counts,
            "issues": [issue.as_dict() for issue in issues],
        }
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        print(f"\nJSON: {args.json}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
