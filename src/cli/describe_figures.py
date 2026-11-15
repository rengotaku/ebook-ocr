"""CLI: book.md に図の説明を差し込む."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from src.describe_figures import (
    DEFAULT_BASE_URL,
    DEFAULT_FALLBACK_MODEL,
    DEFAULT_MODEL,
    describe_book,
    load_layout,
)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="book.md の図に説明を付ける（ローカル VLM）")
    parser.add_argument("book_md", type=Path, help="対象の book.md")
    parser.add_argument("--layout", type=Path, required=True, help="layout.json")
    parser.add_argument("--pages", type=Path, required=True, help="ページ画像のディレクトリ")
    parser.add_argument("--figures-dir", type=Path, help="クロップ画像の保存先（既定: book.md と同じ階層の figures/）")
    parser.add_argument("-o", "--output", type=Path, help="書き出し先（既定: book.md を上書き）")
    parser.add_argument("--vlm-model", default=DEFAULT_MODEL, help=f"Ollama のモデル（既定: {DEFAULT_MODEL}）")
    parser.add_argument("--vlm-base-url", default=DEFAULT_BASE_URL, help=f"Ollama の URL（既定: {DEFAULT_BASE_URL}）")
    parser.add_argument(
        "--vlm-fallback-model",
        default=DEFAULT_FALLBACK_MODEL,
        help=f"1 つ目のモデルが空応答のときに使うモデル。空文字で無効（既定: {DEFAULT_FALLBACK_MODEL}）",
    )
    parser.add_argument("--timeout", type=int, default=300, help="1 枚あたりのタイムアウト秒")
    parser.add_argument("--limit-pages", type=int, help="図があるページを先頭から N ページだけ処理する（試運用）")
    parser.add_argument(
        "--min-area-ratio",
        type=float,
        default=0.02,
        help="図として扱う最小の面積比（ページ面積に対する割合。既定 0.02）",
    )
    parser.add_argument(
        "--max-figure-aspect",
        type=float,
        default=6.0,
        help="図として扱う最大の縦横比（幅÷高さ。既定 6.0。これより横長は本文の行とみなす）",
    )
    args = parser.parse_args(argv)

    if not args.book_md.exists():
        print(f"book.md が見つからない: {args.book_md}", file=sys.stderr)
        return 1
    if not args.layout.exists():
        print(f"layout.json が見つからない: {args.layout}", file=sys.stderr)
        return 1

    figures_dir = args.figures_dir or args.book_md.parent / "figures"
    output = args.output or args.book_md

    layout = load_layout(args.layout)
    text, figures = describe_book(
        args.book_md,
        layout,
        args.pages,
        figures_dir,
        model=args.vlm_model,
        base_url=args.vlm_base_url,
        timeout=args.timeout,
        fallback_model=args.vlm_fallback_model or None,
        max_pages=args.limit_pages,
        min_area_ratio=args.min_area_ratio,
        max_aspect_ratio=args.max_figure_aspect,
    )

    output.write_text(text, encoding="utf-8")
    pages = len({figure.page for figure in figures})
    print(f"{len(figures)} 個の図に説明を付けた（{pages} ページ）")
    print(f"  クロップ: {figures_dir}")
    print(f"  出力: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
