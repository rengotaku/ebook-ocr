"""CLI: book.md を章ごとに分割し、LLM 向けに整形して書き出す."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.chapter_splitter import split_file


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
    written = split_file(args.book_md, out_dir, llm=not args.raw)

    print(f"{len(written)} 章を書き出した: {out_dir}")
    for path in written:
        print(f"  {path.name} ({path.stat().st_size} bytes)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
