"""VLM-based OCR engine using Ollama vision models.

Processes page images through a Vision Language Model to produce
Markdown-formatted text output. Designed as a drop-in replacement
for the v1 Tesseract/EasyOCR pipeline step.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import time
from pathlib import Path

import requests

SYSTEM_PROMPT = """\
あなたは日本語の電子書籍のページ画像を読み取るOCRアシスタントです。
画像のテキストを正確にMarkdown形式で書き起こしてください。

ルール：
- テキストは原文に忠実に書き起こす（要約・意訳しない）
- 章タイトルは適切なMarkdown見出しレベルで表現
- セクション番号付き見出しはそのまま保持（例: 1.1.3　信頼性を制御するとはどういうことか）
- 太字は**太字**で表現
- 表はMarkdownテーブル（| ヘッダ | ... |）形式で正確に表現
- 図やチャートはテキストで構造的に説明し、コードブロックやASCIIアートで視覚的構造を再現
- 箇条書きは - で表現、ネストはインデントで表現
- 引用は > で表現
- ページ下部のフッター（セクション名 — ページ番号）も記載
- 画像にないテキストは絶対に追加しない
- Markdownのメタ情報（```markdown等）は出力しない。本文のみ出力する\
"""

USER_PROMPT_BASE = "この電子書籍ページの画像からテキストを正確に書き起こしてください。"

USER_PROMPT_WITH_FIGURES = """\
この電子書籍ページの画像からテキストを正確に書き起こしてください。

このページには以下の要素が検出されています：
{figure_info}

検出された図表は、テキストで構造的に説明してください。\
"""


def _encode_image(path: str) -> str:
    """Read an image file and return its base64-encoded string."""
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8")


def _build_figure_context(page_figures: list[dict]) -> str:
    """Build a description string of detected figures for the prompt."""
    if not page_figures:
        return ""
    lines = []
    for fig in page_figures:
        fig_type = fig.get("type", "UNKNOWN")
        confidence = fig.get("confidence", 0)
        lines.append(f"- {fig_type} (confidence: {confidence:.2f})")
    return "\n".join(lines)


def ocr_page_vlm(
    page_path: str,
    model: str,
    page_figures: list[dict] | None = None,
    base_url: str = "http://localhost:11434",
    timeout: int = 120,
) -> str:
    """OCR a single page image using a VLM via Ollama.

    Args:
        page_path: Path to the page image file.
        model: Ollama model name (must support vision).
        page_figures: List of detected figure dicts from layout.json.
        base_url: Ollama API base URL.
        timeout: Request timeout in seconds.

    Returns:
        Markdown-formatted text extracted from the page.
    """
    image_b64 = _encode_image(page_path)

    if page_figures:
        figure_info = _build_figure_context(page_figures)
        user_content = USER_PROMPT_WITH_FIGURES.format(figure_info=figure_info)
    else:
        user_content = USER_PROMPT_BASE

    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": user_content, "images": [image_b64]},
        ],
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 4096,
            "repeat_penalty": 1.3,
            "repeat_last_n": 256,
        },
    }

    response = requests.post(
        f"{base_url}/api/chat",
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()

    result = response.json()
    raw_text = result["message"]["content"].strip()
    return _remove_repetitions(raw_text)


def _remove_repetitions(text: str, max_repeats: int = 2) -> str:
    """Remove consecutive repeated lines/paragraphs from VLM output.

    VLMs sometimes enter a repetition loop. This detects and truncates
    such output, keeping at most max_repeats occurrences of any line.
    """
    lines = text.split("\n")
    result: list[str] = []
    consecutive_count = 0
    prev_line = None

    for line in lines:
        stripped = line.strip()
        if stripped and stripped == prev_line:
            consecutive_count += 1
            if consecutive_count >= max_repeats:
                continue
        else:
            consecutive_count = 0
            prev_line = stripped if stripped else prev_line

        result.append(line)

    return "\n".join(result)


def ocr_pages_vlm(
    page_dir: str,
    output_file: str,
    model: str = "gemma3:12b",
    layout: dict | None = None,
    base_url: str = "http://localhost:11434",
    timeout: int = 120,
) -> str:
    """Run VLM OCR on all page images and combine into a Markdown file.

    Args:
        page_dir: Directory containing page images (pages/, not preprocessed/).
        output_file: Path to output Markdown file.
        model: Ollama vision model name.
        layout: Layout dict from figure detection (layout.json contents).
        base_url: Ollama API base URL.
        timeout: Per-page request timeout in seconds.

    Returns:
        Path to the output file.
    """
    if layout is None:
        layout = {}

    pages = sorted(Path(page_dir).glob("page_*.png"))
    if not pages:
        print("No page images found")
        return output_file

    print(f"VLM OCR: {len(pages)} pages with model '{model}'")
    print(f"  Ollama endpoint: {base_url}")
    if layout:
        print(f"  Layout info: {sum(len(v.get('figures', [])) for v in layout.values())} detected elements")

    out_path = Path(output_file)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    all_text: list[str] = []
    total_start = time.time()

    for i, page_path in enumerate(pages, 1):
        page_name = page_path.name
        page_layout = layout.get(page_name, {})
        page_figures = page_layout.get("figures", [])

        print(f"  [{i}/{len(pages)}] {page_name}", end="", flush=True)
        if page_figures:
            types = ", ".join(f["type"] for f in page_figures)
            print(f" (detected: {types})", end="", flush=True)

        start = time.time()
        try:
            text = ocr_page_vlm(
                str(page_path),
                model=model,
                page_figures=page_figures if page_figures else None,
                base_url=base_url,
                timeout=timeout,
            )
            elapsed = time.time() - start
            print(f" -> {len(text)} chars ({elapsed:.1f}s)")
            all_text.append(text)
        except requests.RequestException as e:
            elapsed = time.time() - start
            print(f" -> ERROR ({elapsed:.1f}s): {e}")
            all_text.append(f"[OCR ERROR: {page_name} - {e}]")

    combined = "\n\n".join(all_text)
    out_path.write_text(combined, encoding="utf-8")

    total_elapsed = time.time() - total_start
    print(f"\nVLM OCR complete in {total_elapsed:.1f}s")
    print(f"  Output: {out_path}")
    return output_file


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run VLM OCR on page images (v2 engine)",
    )
    parser.add_argument("pages_dir", help="Directory containing page_*.png images")
    parser.add_argument("-o", "--output", default="book.md", help="Output file (default: book.md)")
    parser.add_argument("--model", default="gemma3:12b", help="Ollama vision model (default: gemma3:12b)")
    parser.add_argument("--layout", default=None, help="Path to layout.json (optional)")
    parser.add_argument("--vlm-url", default="http://localhost:11434", help="Ollama API URL")
    parser.add_argument("--timeout", type=int, default=120, help="Per-page timeout in seconds (default: 120)")
    args = parser.parse_args()

    layout = {}
    if args.layout:
        layout_path = Path(args.layout)
        if layout_path.exists():
            layout = json.loads(layout_path.read_text(encoding="utf-8"))
            print(f"Loaded layout from {layout_path}")

    ocr_pages_vlm(
        page_dir=args.pages_dir,
        output_file=args.output,
        model=args.model,
        layout=layout,
        base_url=args.vlm_url,
        timeout=args.timeout,
    )


if __name__ == "__main__":
    main()
