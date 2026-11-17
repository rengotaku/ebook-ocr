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

from src.layout.table import UNSTRUCTURED_NOTE
from src.layout_ocr_utils import FIGURE_LIKE_TYPES

PAGE_MARKER_RE = re.compile(r"^--- (\d+) ---\s*$", re.M)

# 図の種別はこの語彙だけを使わせる。自由に名付けさせると「魚の骨図」「イシノカワ図」
# のような固有名詞で誤ラベルする（#100）。
FIGURE_KINDS = ("表", "グラフ", "模式図", "スクリーンショット", "写真", "その他")

PROMPT = (
    "この画像を説明してください。出力は次の 2 行だけにしてください。\n"
    "種別: " + "／".join(FIGURE_KINDS) + " から 1 つ\n"
    "内容: 画像に写っているものと、画像の中に書かれている文字を 2〜3 文で説明\n"
    "\n"
    "守ること:\n"
    "- 図の種類を名付けるときは「種別」の語だけを使う（「魚の骨図」「イシノカワ図」のような\n"
    "  固有名詞は使わない）\n"
    "- 画像から読み取れないことは書かない。推測で補わない\n"
    "- 数値は、画像にはっきり書かれているものだけ書く\n"
    "- 「〜と思われます」のような推測の言い回しを置かない"
)

# 数値を求めるとモデルが読み取りに時間を使い、生成枠を使い切って content が空になる
# ことがある（#88）。短い指示に切り替えると返ってくる。種別の形式は保つ。
PROMPT_BRIEF = (
    "この画像の種別（" + "／".join(FIGURE_KINDS) + "）と内容を 2 文以内で、"
    "「種別: ...」「内容: ...」の形だけで書いてください。推測は書かないでください。"
)

# 種別と内容の取り出し。形式を守らなかったときは、本文全体を内容として扱う
KIND_RE = re.compile(r"^\s*種別\s*[:：]\s*(\S+)", re.M)
CONTENT_RE = re.compile(r"^\s*内容\s*[:：]\s*(.+)$", re.M | re.S)


def parse_description(text: str) -> tuple[str, str]:
    """VLM の出力から (種別, 内容) を取り出す.

    種別は ``FIGURE_KINDS`` にある語だけを受け付ける（想定外の語は捨てる）。
    """
    kind_match = KIND_RE.search(text)
    kind = kind_match.group(1).strip("。.、, ") if kind_match else ""
    if kind not in FIGURE_KINDS:
        kind = ""

    content_match = CONTENT_RE.search(text)
    if content_match:
        content = content_match.group(1).strip()
    else:
        content = text.strip()
    return kind, "".join(line.strip() for line in content.splitlines() if line.strip())


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
    kind: str = ""
    note: str = ""
    text: str = ""


class OllamaUnavailable(RuntimeError):
    """Ollama に接続できない."""


def _ollama_chat(
    image_path: Path,
    model: str,
    base_url: str,
    timeout: int,
    num_predict: int = DEFAULT_NUM_PREDICT,
    prompt: str = PROMPT,
) -> str:
    """Ollama に画像を送り、説明文を返す."""
    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt,
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

    qwen3-vl は思考が長引くと content が空で返ることがある。空なら
    (1) 同じモデルで retries 回まで引き直し、(2) 短い指示（数値不要）で 1 回、
    (3) fallback_model で 1 回、の順に試す。
    """
    for _ in range(retries + 1):
        text = chat(image_path, model=model, base_url=base_url, timeout=timeout)
        if text:
            return text
    text = chat(image_path, model=model, base_url=base_url, timeout=timeout, prompt=PROMPT_BRIEF)
    if text:
        return text
    if fallback_model:
        return chat(image_path, model=fallback_model, base_url=base_url, timeout=timeout)
    return ""


DEFAULT_MIN_AREA_RATIO = 0.02
# 横長すぎる領域は図ではなく本文の行・見出しのことが多い（対象の本では 12〜16 倍の帯が
# 本文 2 行や節見出しだった）。図は概ね 1〜3 倍に収まる。
DEFAULT_MAX_ASPECT_RATIO = 6.0


def page_figures(
    layout_page: dict,
    min_area_ratio: float = DEFAULT_MIN_AREA_RATIO,
    max_aspect_ratio: float = DEFAULT_MAX_ASPECT_RATIO,
) -> list[dict]:
    """1 ページ分の layout から図として扱う領域を面積の大きい順に返す.

    図ではない領域を落とす基準は 2 つ。

    - ページ面積に対する比率（既定 2%）: ロゴや著者名の行のような小さい領域
    - 縦横比（既定 6.0）: 本文の行や節見出しのような横長の帯
    """
    page_size = layout_page.get("page_size") or [0, 0]
    page_area = int(page_size[0]) * int(page_size[1])
    regions = []
    for region in layout_page.get("regions", []):
        if region.get("type") not in FIGURE_LIKE_TYPES:
            continue
        if page_area and _area(region["bbox"]) / page_area < min_area_ratio:
            continue
        if _aspect_ratio(region["bbox"]) > max_aspect_ratio:
            continue
        regions.append(region)
    return sorted(regions, key=lambda region: _area(region["bbox"]), reverse=True)


def _aspect_ratio(bbox: list[int]) -> float:
    width = max(0, bbox[2] - bbox[0])
    height = max(0, bbox[3] - bbox[1])
    if height == 0:
        return float("inf")
    return width / height


def _area(bbox: list[int]) -> int:
    return max(0, bbox[2] - bbox[0]) * max(0, bbox[3] - bbox[1])


# 図の中の文字は、罫線・点・1 文字の記号が多く出る。1 文字は捨てる。
MIN_FIGURE_TEXT_CHARS = 2
# 数字と記号だけでできた行（目次・索引のページ番号、軸の目盛りの写り込み）。
# 文字として読ませる意味が無いので落とす。
_NUMBERS_ONLY_RE = re.compile(r"^[\d\s.,、。·・:：;；\-–—~〜/()（）\[\]{}]+$")


def _squash(text: str) -> str:
    return re.sub(r"\s+", "", text)


def clean_figure_text(text: str) -> str:
    """OCR の生テキストを、図中の文字として出す形に整える.

    - 1 文字・記号だけの行を落とす（罫線・点・ノイズ）
    - 見出し記号や表の罫線の記号を落とす
    - 同じ行の繰り返しを 1 つにする
    """
    parts: list[str] = []
    seen: set[str] = set()
    for raw in text.splitlines():
        line = raw.strip().strip("#>*`_~| \t")
        line = line.replace("`", "").strip()
        if len(line) < MIN_FIGURE_TEXT_CHARS:
            continue
        if not re.search(r"\w", line):
            continue
        if _NUMBERS_ONLY_RE.match(line):
            continue
        key = _squash(line)
        if not key or key in seen:
            continue
        seen.add(key)
        parts.append(line)
    return " / ".join(parts)


# 本文の行がクロップに写り込んだときの重複を落とす。図の短いラベル（「売上」「利益」など）は
# 本文の文に偶然出てくるので、文ほどの長さの行だけを対象にする。
MIN_BODY_REPEAT_CHARS = 8


def drop_body_repeats(text: str, body: str, min_chars: int = MIN_BODY_REPEAT_CHARS) -> str:
    """ページの本文にそのまま出ている行を落とす.

    図のクロップが本文の領域に重なっていると、本文の行がそのまま返ることがある。
    短いラベルは本文の文に偶然出てくるので、``min_chars`` 以上のものだけを対象にする。
    """
    if not text or not body:
        return text
    squashed_body = _squash(body)
    kept: list[str] = []
    for part in text.split(" / "):
        key = _squash(part)
        if not key:
            continue
        if len(key) >= min_chars and key in squashed_body:
            continue
        kept.append(part)
    return " / ".join(kept)


def _ocr_crop_text(crop_path: Path, device: str) -> str:
    from src.ocr_yomitoku import ocr_page_yomitoku

    with Image.open(crop_path) as image:
        return ocr_page_yomitoku("", device=device, img=image.convert("RGB"))


def figure_text(
    crop_path: Path,
    device: str = "cpu",
    ocr: Callable[[Path, str], str] | None = None,
) -> str:
    """図のクロップから文字を取る.

    図中の文字は本文の補助情報なので、OCR が落ちても図の説明と本文は出す。
    失敗したときは stderr に出して空文字を返す。
    """
    run = ocr or _ocr_crop_text
    try:
        raw = run(crop_path, device)
    except Exception as error:  # pylint: disable=broad-except  # 補助情報なので落とさない
        print(f"[describe_figures] {crop_path.name}: 図中の文字を取れない ({error})", file=sys.stderr)
        return ""
    return clean_figure_text(raw)


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
    """book.md に差し込む Markdown ブロック.

    説明は VLM の自動生成なので、種別と「自動生成」をラベルに出す（#100）。
    図の中の文字は本文に混ぜず、説明の次の行に別枠で置く（#119）。
    """
    caption = figure.description or "（説明なし）"
    label = f"図（{figure.kind}・自動生成）" if figure.kind else "図（自動生成）"
    block = f"![図]({figures_link}/{figure.path.name})\n\n**{label}**: {caption}\n"
    if figure.text:
        block += f"\n**図中の文字**: {figure.text}\n"
    if figure.note:
        block += f"\n*{figure.note}*\n"
    return block


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
    max_aspect_ratio: float = DEFAULT_MAX_ASPECT_RATIO,
    describe: Callable[..., str] = describe_image,
    device: str = "cpu",
    with_figure_text: bool = False,
    ocr: Callable[[Path, str], str] | None = None,
) -> tuple[str, list[Figure]]:
    """book.md の本文に図の説明を差し込んだ文字列を返す.

    ``max_pages`` を指定すると、図があるページを先頭からその数だけ処理する（試運用向け）。

    図の中の文字（``**図中の文字**``）は本文に混ぜず、図の説明の次の行に置く。
    OCR を回すかどうかは ``with_figure_text`` で決める（CLI は既定でオン）。
    テストのように OCR を回したくない呼び出しではオフにする。
    """
    text = book_md.read_text(encoding="utf-8")
    sections = _split_pages(text)

    # 1) 図を切り出し、図の中の文字を先に取る。Ollama が VRAM を掴んだまま
    #    yomitoku を動かすと OOM になるので、VLM より先に OCR を終わらせる。
    crops: list[tuple[str, str, dict, Path, int]] = []
    processed_pages = 0
    for page, body in sections:
        if max_pages is not None and processed_pages >= max_pages:
            break
        page_key = f"{page}.webp"
        page_layout = layout.get(page_key) or layout.get(f"{page}.png") or {}
        regions = page_figures(page_layout, min_area_ratio=min_area_ratio, max_aspect_ratio=max_aspect_ratio)
        if not regions:
            continue
        page_image = _find_page_image(pages_dir, page)
        if page_image is None:
            print(f"[describe_figures] {page}: ページ画像が見つからないためスキップ", file=sys.stderr)
            continue
        processed_pages += 1
        for index, (region, crop_path) in enumerate(crop_figures(page_image, regions, figures_dir), 1):
            crops.append((page, body, region, crop_path, index))

    crop_texts: dict[Path, str] = {}
    if with_figure_text:
        for _page, _body, _region, crop_path, _index in crops:
            crop_texts[crop_path] = figure_text(crop_path, device=device, ocr=ocr)

    # 2) 説明を付ける。Ollama に繋がらなくなったら、そこから先は差し込まない。
    figures: list[Figure] = []
    disabled = False
    for page, body, region, crop_path, index in crops:
        if disabled:
            break
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
        kind, content = parse_description(description)
        note = UNSTRUCTURED_NOTE if region.get("table_note") else ""
        figure_body = drop_body_repeats(crop_texts.get(crop_path, ""), body)
        figures.append(
            Figure(page=page, index=index, path=crop_path, description=content, kind=kind, note=note, text=figure_body)
        )

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
