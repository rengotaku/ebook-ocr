"""CLI: book.md を章ごとに分割し、LLM 向けに整形して書き出す."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.chapter_splitter import load_page_numbers, split_file, write_page_numbers_csv


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="book.md を章ごとの Markdown に分割する")
    parser.add_argument("book_md", type=Path, help="対象の book.md（ページマーカー入り）")
    parser.add_argument("-o", "--outdir", type=Path, help="出力ディレクトリ（既定: book.md と同じ階層の chapters/）")
    parser.add_argument(
        "--raw",
        action="store_true",
        help="折り返しの復元・柱の除去をせず、ページマーカーだけ外して出す",
    )
    args = parser.parse_args(argv)

    if not args.book_md.exists():
        print(f"book.md が見つからない: {args.book_md}", file=sys.stderr)
        return 1

    out_dir = args.outdir or args.book_md.parent / "chapters"
    page_numbers = load_page_numbers(args.book_md)
    written = split_file(args.book_md, out_dir, llm=not args.raw, page_numbers=page_numbers)

    print(f"{len(written)} 章を書き出した: {out_dir}")
    for path in written:
        print(f"  {path.name} ({path.stat().st_size} bytes)")

    if page_numbers:
        numbers_path = write_page_numbers_csv(out_dir, page_numbers)
        print(f"ページ番号の対応表: {numbers_path} ({len(page_numbers)} ページ)")
    else:
        print("ページ番号の対応表: page_numbers.json が見つからないため未出力")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
