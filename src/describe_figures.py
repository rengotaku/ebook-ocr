"""図の領域を切り出し、ローカルの VLM（Ollama）で説明を付ける.

`book.md` のページマーカー（``--- 0085 ---``）ごとに、`layout.json` の FIGURE / CODE
領域をクロップして `figures/` に保存し、説明文をページの末尾に差し込む。

VLM に繋がらないときは図の差し込みだけを飛ばし、`book.md` はそのまま出す。
"""

from __future__ import annotations

import base64
import json
import re
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

from PIL import Image

from src.layout_ocr_utils import FIGURE_LIKE_TYPES

PAGE_MARKER_RE = re.compile(r"^--- (\d+) ---\s*$", re.M)

PROMPT = (
    "この画像の図が何を示しているか、日本語で3文以内で説明してください。"
    "読み取れた数値は書いてください。読み取れない数値は書かないでください。"
)

DEFAULT_MODEL = "qwen3-vl:8b"
DEFAULT_FALLBACK_MODEL = "gemma3:12b"
DEFAULT_BASE_URL = "http://localhost:11434"
# 思考が長引くと content が空のまま終わるので、生成量に上限を置く
DEFAULT_NUM_PREDICT = 1024


@dataclass(frozen=True)
class Figure:
    """1 つの図と、その説明."""

    page: str
    index: int
    path: Path
    description: str


class OllamaUnavailable(RuntimeError):
    """Ollama に接続できない."""


def _ollama_chat(
    image_path: Path, model: str, base_url: str, timeout: int, num_predict: int = DEFAULT_NUM_PREDICT
) -> str:
    """Ollama に画像を送り、説明文を返す."""
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": PROMPT,
                "images": [base64.b64encode(image_path.read_bytes()).decode()],
            }
        ],
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": num_predict},
    }
    request = urllib.request.Request(
        f"{base_url.rstrip('/')}/api/chat",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = json.load(response)
    except urllib.error.URLError as error:
        raise OllamaUnavailable(f"Ollama に接続できない ({base_url}): {error}") from error
    return str(body.get("message", {}).get("content", "")).strip()


def describe_image(
    image_path: Path,
    model: str = DEFAULT_MODEL,
    base_url: str = DEFAULT_BASE_URL,
    timeout: int = 300,
    retries: int = 1,
    fallback_model: str | None = DEFAULT_FALLBACK_MODEL,
    chat: Callable[..., str] = _ollama_chat,
) -> str:
    """画像の説明を取る.

    qwen3-vl は思考が長引くと content が空で返ることがある。空なら同じモデルで
    retries 回まで引き直し、それでも空なら fallback_model を 1 回だけ試す。
    """
    for _ in range(retries + 1):
        text = chat(image_path, model=model, base_url=base_url, timeout=timeout)
        if text:
            return text
    if fallback_model:
        return chat(image_path, model=fallback_model, base_url=base_url, timeout=timeout)
    return ""


DEFAULT_MIN_AREA_RATIO = 0.02


def page_figures(layout_page: dict, min_area_ratio: float = DEFAULT_MIN_AREA_RATIO) -> list[dict]:
    """1 ページ分の layout から図として扱う領域を面積の大きい順に返す.

    ロゴや著者名の行のような小さい領域まで図として説明すると、本文に対してノイズになる。
    ページ面積に対する比率で足切りする（既定 2%）。
    """
    page_size = layout_page.get("page_size") or [0, 0]
    page_area = int(page_size[0]) * int(page_size[1])
    regions = []
    for region in layout_page.get("regions", []):
        if region.get("type") not in FIGURE_LIKE_TYPES:
            continue
        if page_area and _area(region["bbox"]) / page_area < min_area_ratio:
            continue
        regions.append(region)
    return sorted(regions, key=lambda region: _area(region["bbox"]), reverse=True)


def _area(bbox: list[int]) -> int:
    return max(0, bbox[2] - bbox[0]) * max(0, bbox[3] - bbox[1])


def crop_figures(
    page_image: Path,
    regions: list[dict],
    figures_dir: Path,
) -> list[tuple[dict, Path]]:
    """図の領域をクロップして保存し、(領域, 保存先) を返す."""
    if not regions:
        return []
    figures_dir.mkdir(parents=True, exist_ok=True)
    cropped: list[tuple[dict, Path]] = []
    with Image.open(page_image) as image:
        width, height = image.size
        rgb = image.convert("RGB")
        for index, region in enumerate(regions, 1):
            x1, y1, x2, y2 = region["bbox"]
            box = (max(0, x1), max(0, y1), min(width, x2), min(height, y2))
            if box[2] <= box[0] or box[3] <= box[1]:
                continue
            target = figures_dir / f"{page_image.stem}_fig{index}.png"
            rgb.crop(box).save(target)
            cropped.append((region, target))
    return cropped


def figure_block(figure: Figure, figures_link: str) -> str:
    """book.md に差し込む Markdown ブロック."""
    caption = figure.description or "（説明なし）"
    return f"![図]({figures_link}/{figure.path.name})\n\n**図**: {caption}\n"


def describe_book(
    book_md: Path,
    layout: dict,
    pages_dir: Path,
    figures_dir: Path,
    model: str = DEFAULT_MODEL,
    base_url: str = DEFAULT_BASE_URL,
    timeout: int = 300,
    fallback_model: str | None = DEFAULT_FALLBACK_MODEL,
    max_pages: int | None = None,
    min_area_ratio: float = DEFAULT_MIN_AREA_RATIO,
    describe: Callable[..., str] = describe_image,
) -> tuple[str, list[Figure]]:
    """book.md の本文に図の説明を差し込んだ文字列を返す.

    ``max_pages`` を指定すると、図があるページを先頭からその数だけ処理する（試運用向け）。
    """
    text = book_md.read_text(encoding="utf-8")
    sections = _split_pages(text)
    figures: list[Figure] = []
    disabled = False
    processed_pages = 0

    for page, body in sections:
        if disabled:
            break
        if max_pages is not None and processed_pages >= max_pages:
            break
        page_key = f"{page}.webp"
        page_layout = layout.get(page_key) or layout.get(f"{page}.png") or {}
        regions = page_figures(page_layout, min_area_ratio=min_area_ratio)
        if not regions:
            continue
        page_image = _find_page_image(pages_dir, page)
        if page_image is None:
            print(f"[describe_figures] {page}: ページ画像が見つからないためスキップ", file=sys.stderr)
            continue
        processed_pages += 1
        cropped = crop_figures(page_image, regions, figures_dir)
        for index, (_, crop_path) in enumerate(cropped, 1):
            try:
                description = describe(
                    crop_path,
                    model=model,
                    base_url=base_url,
                    timeout=timeout,
                    fallback_model=fallback_model,
                )
            except OllamaUnavailable as error:
                print(f"[describe_figures] {error} — 図の説明を飛ばす", file=sys.stderr)
                disabled = True
                break
            figures.append(Figure(page=page, index=index, path=crop_path, description=description))

    return _insert_figures(text, figures, figures_dir), figures


def _find_page_image(pages_dir: Path, page: str) -> Path | None:
    for suffix in (".webp", ".png", ".jpg", ".jpeg"):
        candidate = pages_dir / f"{page}{suffix}"
        if candidate.exists():
            return candidate
    return None


def _split_pages(text: str) -> list[tuple[str, str]]:
    """``--- 0085 ---`` ごとに (ページ番号, 本文) に分ける."""
    sections: list[tuple[str, str]] = []
    matches = list(PAGE_MARKER_RE.finditer(text))
    for position, match in enumerate(matches):
        start = match.end()
        end = matches[position + 1].start() if position + 1 < len(matches) else len(text)
        sections.append((match.group(1), text[start:end]))
    return sections


def _insert_figures(text: str, figures: list[Figure], figures_dir: Path) -> str:
    """ページの末尾に図のブロックを差し込む."""
    if not figures:
        return text
    by_page: dict[str, list[Figure]] = {}
    for figure in figures:
        by_page.setdefault(figure.page, []).append(figure)

    figures_link = figures_dir.name
    matches = list(PAGE_MARKER_RE.finditer(text))
    if not matches:
        return text

    out: list[str] = [text[: matches[0].start()]]
    for position, match in enumerate(matches):
        start = match.start()
        end = matches[position + 1].start() if position + 1 < len(matches) else len(text)
        section = text[start:end]
        page = match.group(1)
        page_figures_list = by_page.get(page)
        if page_figures_list:
            blocks = "\n".join(figure_block(figure, figures_link) for figure in page_figures_list)
            section = f"{section.rstrip()}\n\n{blocks}\n"
        out.append(section)
    return "".join(out)


def load_layout(layout_path: Path) -> dict:
    return json.loads(layout_path.read_text(encoding="utf-8"))
