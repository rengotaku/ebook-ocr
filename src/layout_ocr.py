"""Region-based OCR processing with layout detection.

This module implements User Story 2: Region-based OCR Processing.
Each detected region is processed with the appropriate OCR engine:
- TEXT/TITLE/CAPTION/FOOTNOTE/FORMULA: use the text recognized during layout detection
  (`layout.json` の `region["text"]`)
- TABLE: crop the region and OCR it again (its structure has to be read from the pixels)
- FIGURE/CODE: Skip (treated as a figure, excluded from text output)
- ABANDON: Skip

Region Text Source:
| Region Type | Text Source | Output Format |
|-------------|-------------|---------------|
| TITLE | layout.json | `## {text}` |
| TEXT | layout.json | `{text}` |
| TABLE | crop re-OCR (fallback: layout.json) | Markdown table |
| FIGURE | Skip | (treated as a figure) |
| CODE | Skip | (treated as a figure) |
| CAPTION | layout.json | `*{text}*` |
| FOOTNOTE | layout.json | `^{text}^` |
| FORMULA | layout.json | `$${text}$$` |
| ABANDON | Skip | None |
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from src.book_meta import write_book_meta
from src.layout.reading_order import remove_overlaps, sort_reading_order
from src.layout.running_head import (
    chapter_title_from_region,
    find_running_heads,
    is_running_head,
    normalize_running_head_text,
    printed_page_number,
    strip_running_head_lines,
)
from src.layout_ocr_utils import (
    FIGURE_LIKE_TYPES,
    crop_region,
    format_ocr_result,
    is_low_quality,
    prefer_layout_text,
    select_ocr_engine,
    should_fallback,
)
from src.utils import list_page_images


@dataclass(frozen=True)
class OCRResult:
    """1領域のOCR出力。"""

    region_type: str  # 元の領域種類
    text: str  # OCR出力テキスト
    formatted: str  # フォーマット済みテキスト（Markdown形式）


# レイアウト検出時に認識済みの text をそのまま使う領域。
# 領域を切り出して OCR をかけ直すと、薄い・小さい領域で空になる（#97）。
# TABLE は検出時に表構造から Markdown を組み立てているので、ここに含める（#101）。
LAYOUT_TEXT_TYPES = ("TEXT", "TITLE", "CAPTION", "FOOTNOTE", "FORMULA", "TABLE")


def ocr_with_fallback(image: Image.Image, device: str = "cpu") -> tuple[str, str]:
    """OCR with fallback chain: Yomitoku → PaddleOCR → Tesseract.

    Returns:
        (text, engine_name) tuple where engine_name is 'yomitoku', 'paddleocr', or 'tesseract'
    """
    from src.ocr_ensemble import ocr_paddleocr, ocr_tesseract
    from src.ocr_yomitoku import ocr_page_yomitoku

    # 1. Yomitoku
    text = ocr_page_yomitoku("", device=device, img=image)
    if text and not is_low_quality(text):
        return text, "yomitoku"

    # 2. PaddleOCR
    result = ocr_paddleocr(image)
    if result.success and result.text and not is_low_quality(result.text):
        return result.text, "paddleocr"

    # 3. Tesseract
    result = ocr_tesseract(image)
    if result.success and result.text:
        return result.text, "tesseract"

    return "", "none"


def ocr_region(
    img: Image.Image,
    region: dict,
    device: str = "cpu",
) -> OCRResult:
    """単一領域のOCR処理。

    本文・見出しはレイアウト検出時の認識結果（``region["text"]``）を使い、
    クロップした画像への再 OCR は構造を取り直す必要がある TABLE だけに残す。

    Args:
        img: ページ全体の PIL Image
        region: {"type": str, "bbox": list[int], "confidence": float, "text": str}
        device: Device for Yomitoku ("cpu" or "cuda")

    Returns:
        OCRResult with text and formatted output
    """
    region_type = region["type"]

    # 1. FIGURE/CODE/ABANDON領域はスキップ
    engine = select_ocr_engine(region_type)
    if engine == "skip":
        return OCRResult(
            region_type=region_type,
            text="",
            formatted="",
        )

    layout_text = region.get("text") or ""

    # 2. 本文・見出しはレイアウト検出時の text を正とする
    if region_type in LAYOUT_TEXT_TYPES:
        return OCRResult(
            region_type=region_type,
            text=layout_text,
            formatted=format_ocr_result(region_type, layout_text),
        )

    # 3. 未知の領域種別はクロップして読み直す（既知の種別は上で text を使っている）
    from src.ocr_yomitoku import ocr_page_yomitoku

    cropped_img = crop_region(img, region["bbox"])
    ocr_text = ocr_page_yomitoku("", device=device, img=cropped_img)

    # 4. 再 OCR が空ならレイアウトの text に戻す（文字があるのに空にしない）
    if not ocr_text.strip():
        ocr_text = layout_text

    return OCRResult(
        region_type=region_type,
        text=ocr_text,
        formatted=format_ocr_result(region_type, ocr_text),
    )


# 段落の並べ替えで「同じ行」とみなす y の幅（px）
BLOCK_Y_TOLERANCE = 10


def order_page_blocks(blocks: list[dict], page_width: int) -> list[dict] | None:
    """ページ全体 OCR の段落を、領域と同じ規則で紙面の順に並べ直す.

    位置が取れない段落が 1 つでもあれば並べ替えずに ``None`` を返す（文字を落とさない）。
    """
    if not blocks or not page_width:
        return None
    if any(block.get("bbox") is None for block in blocks):
        return None
    # 段落の y は数 px ずれる。同じ行の見出しと本文が入れ替わらないよう幅を持たせる。
    return sort_reading_order(blocks, page_width, y_tolerance=BLOCK_Y_TOLERANCE)


def filter_page_blocks(
    blocks: list[dict],
    running_heads: frozenset[str],
    page_heads: frozenset[str],
) -> list[dict]:
    """柱・ノンブルにあたる段落を落とす（並べ替えの前に呼ぶ）.

    柱は左右の段をまたぐので、残したまま段の判定をすると 2 段組みが 1 段組みになる。
    落とすのは 2 種類だけにする。

    - このページで柱と確認された行（``page_heads``。座標で決まる）
    - ページの先頭・末尾の段落で、本全体で繰り返す柱（``running_heads``）にあたるもの

    本全体の柱は本文の途中にも同じ文字が現れる（目次の「プロローグ」など）ので、
    真ん中の段落には当てない。
    """
    kept: list[dict] = []
    for index, block in enumerate(blocks):
        text = block["text"]
        if normalize_running_head_text(text) in page_heads:
            continue
        if index in (0, len(blocks) - 1):
            text = strip_running_head_lines(text, running_heads, frozenset())
            if not text.strip():
                continue
        kept.append({**block, "text": text})
    return kept


def ocr_by_layout(
    page_path: str,
    layout: dict,
    device: str = "cpu",
    running_heads: frozenset[str] = frozenset(),
) -> list[OCRResult]:
    """ページ内の全領域をOCR処理。

    Args:
        page_path: ページ画像のパス
        layout: {"regions": list[dict], "page_size": [w, h]}
        device: Device for Yomitoku ("cpu" or "cuda")
        running_heads: 柱とみなす文字列（``find_running_heads()`` の戻り値）

    Returns:
        各領域のOCRResult リスト（読み順ソート済み）
    """
    regions = layout.get("regions", [])
    page_size = tuple(layout.get("page_size", [0, 0]))

    # ページ全体 OCR に回すかどうかは、柱を落とす前の領域で決める。
    # 柱を落とすとカバー率がわずかに下がり、境界のページがフォールバックに転ぶ。
    fallback = should_fallback(regions, page_size)

    # 柱・ノンブルは本文ではないので落とす（#98）。落とした行は、このページの
    # 柱として覚えておき、ページ全体 OCR に落ちたときにも取り除く。
    page_heads = frozenset(
        normalize_running_head_text(r.get("text") or "")
        for r in regions
        if is_running_head(r, page_size, running_heads)
    )
    page_heads = frozenset(key for key in page_heads if key)
    regions = [r for r in regions if not is_running_head(r, page_size, running_heads)]

    region_results = _ocr_regions(page_path, regions, page_size, device)

    if not fallback:
        return region_results

    # ページ全体 OCR に回す判定になったページでも、領域別の text と文字数がほぼ同じなら
    # 見出しと読取順を優先して領域別を採る（#108）。ページ全体 OCR のほうが長いときは、
    # 図・表として検出された領域の中に本文が入っているので、ページ全体を採る。
    from src.ocr_yomitoku import ocr_page_blocks

    blocks = ocr_page_blocks(page_path, device=device)
    # 柱・ノンブルは段の判定を邪魔する（2 段組みの段間を柱が塞ぐと 1 段組みと判定される）。
    # 並べ替える前に落とす（#121、codex の指摘）。
    blocks = filter_page_blocks(blocks, running_heads, page_heads)
    ordered = order_page_blocks(blocks, page_size[0] if page_size else 0)
    ocr_text = "\n\n".join(block["text"] for block in (ordered if ordered is not None else blocks))

    # 段落に分かれていない柱が残っていれば、ここでも落とす
    ocr_text = strip_running_head_lines(ocr_text, running_heads, page_heads)
    # 見出しだけはレイアウトから差し込む（本文は変えない）
    ocr_text = apply_layout_headings(ocr_text, regions)

    region_text = "\n\n".join(result.formatted for result in region_results if result.formatted.strip())
    if prefer_layout_text(ocr_text, region_text):
        return region_results

    return [
        OCRResult(
            region_type="FALLBACK",
            text=ocr_text,
            formatted=ocr_text,
        )
    ]


# 目次の点線（``………`` ``......``）
_DOT_LEADER_RE = re.compile(r"[…]{2,}|\.{3,}")


def apply_layout_headings(text: str, regions: list[dict]) -> str:
    """ページ全体 OCR の本文に、レイアウトの TITLE を見出しとして差し込む.

    ページ全体 OCR に回ったページは領域ごとの整形を通らないので見出しが付かない（#108）。
    本文はそのまま残し、TITLE の文字が本文に **1 行だけ** そのまま出てくるときだけ
    ``## `` を付ける。2 回以上出てくるものは、どれが見出しか決められないので触らない。
    """
    titles = [r for r in regions if r["type"] == "TITLE" and (r.get("text") or "").strip()]
    if not titles:
        return text

    lines = text.split("\n")
    stripped = [line.strip() for line in lines]
    for region in titles:
        title = region["text"].strip()
        if not format_ocr_result("TITLE", title).startswith("## "):
            # 文末記号で終わるものは本文の行（#90 と同じ規則）
            continue
        if _DOT_LEADER_RE.search(title):
            # 目次の「1. ワークシートの基本操作………」のような点線付きの行は見出しにしない
            continue
        positions = [index for index, value in enumerate(stripped) if value == title]
        if len(positions) != 1:
            continue
        index = positions[0]
        if stripped[index].startswith("#"):
            continue
        lines[index] = f"## {stripped[index]}"
        stripped[index] = lines[index]
    return "\n".join(lines)


def _ocr_regions(
    page_path: str,
    regions: list[dict],
    page_size: tuple[int, ...],
    device: str,
) -> list[OCRResult]:
    """領域ごとに text を取り出し、読み順に並べて返す."""
    if regions and page_size[0] > 0:
        regions = remove_overlaps(regions)
        regions = sort_reading_order(regions, page_size[0])

    img = Image.open(page_path)

    results = []
    for region in regions:
        # ABANDON/FIGURE/CODE領域はスキップ（CODE は図として扱う）
        if region["type"] in (*FIGURE_LIKE_TYPES, "ABANDON"):
            continue
        results.append(ocr_region(img, region, device=device))
    return results


def run_layout_ocr(
    pages_dir: str,
    layout_data: dict,
    output_file: str,
    device: str = "cpu",
    warmup: bool = True,
    *,
    limit: int | None = None,
) -> list[tuple[str, list[OCRResult]]]:
    """Run layout-aware OCR on all pages in a directory.

    This is the main entry point for OCR processing. It handles:
    - Model warmup (Yomitoku initialization)
    - Reading order sorting
    - Per-page OCR processing
    - Individual and combined result output

    Args:
        pages_dir: Directory containing page images.
        layout_data: Layout detection results (from layout.json).
        output_file: Path for combined output text file.
        device: Device for Yomitoku ("cpu" or "cuda").
        warmup: Whether to warm up the model before processing.

    Returns:
        List of (page_name, ocr_results) tuples.
    """
    pages_path = Path(pages_dir)
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Model warmup (initialize Yomitoku)
    if warmup:
        print("  Initializing Yomitoku OCR...")
        from src.ocr_yomitoku import ocr_page_yomitoku

        start = time.time()
        # Warm up by running a dummy OCR
        dummy_img = Image.new("RGB", (100, 100), color=(255, 255, 255))
        ocr_page_yomitoku("", device=device, img=dummy_img)
        elapsed = time.time() - start
        print(f"  Yomitoku ready in {elapsed:.1f}s")

    # Create ocr_texts directory for individual page results
    ocr_texts_dir = output_path.parent / "ocr_texts"
    ocr_texts_dir.mkdir(parents=True, exist_ok=True)

    pages = list_page_images(pages_path)
    if limit is not None:
        pages = pages[:limit]
    all_results: list[tuple[str, list[OCRResult]]] = []
    page_numbers: dict[str, int] = {}
    chapter_title_votes: dict[int, dict[str, int]] = {}
    fallback_pages: list[str] = []

    # 柱・ノンブルは本全体で決まる（同じ行が複数ページに出るか）ので、先に集めておく
    running_heads = find_running_heads(layout_data)
    if running_heads:
        print(f"  Running heads: {len(running_heads)}")

    for page_path in pages:
        page_name = page_path.name
        page_stem = page_path.stem
        print(f"  Processing {page_name}...")

        # Get layout for this page
        page_layout = layout_data.get(page_name, {"regions": [], "page_size": [0, 0]})

        # Run layout-aware OCR
        ocr_results = ocr_by_layout(
            str(page_path),
            page_layout,
            device=device,
            running_heads=running_heads,
        )

        # 柱・ノンブルから紙面のページ番号（ノンブル）と章名を取り出しておく（#99）
        page_size = page_layout.get("page_size") or [0, 0]
        for region in page_layout.get("regions", []):
            if not is_running_head(region, page_size, running_heads):
                continue
            number = printed_page_number(region)
            if number is not None and page_stem not in page_numbers:
                page_numbers[page_stem] = number
            chapter = chapter_title_from_region(region)
            if chapter is not None:
                chapter_number, title = chapter
                chapter_title_votes.setdefault(chapter_number, {}).setdefault(title, 0)
                chapter_title_votes[chapter_number][title] += 1

        # Report status
        if ocr_results and ocr_results[0].region_type == "FALLBACK":
            fallback_pages.append(page_stem)
            print("    → Fallback: page-level OCR (low coverage or detection failure)")
        else:
            print(f"    → Processed {len(ocr_results)} regions")

        # Write individual page result immediately
        page_text_file = ocr_texts_dir / f"{page_stem}.txt"
        with open(page_text_file, "w", encoding="utf-8") as f:
            for result in ocr_results:
                f.write(result.formatted)
                f.write("\n\n")
        print(f"    → Saved: {page_text_file.name}")

        all_results.append((page_name, ocr_results))

    # Write combined results
    with open(output_file, "w", encoding="utf-8") as f:
        for page_name, ocr_results in all_results:
            f.write(f"\n--- Page: {page_name} ---\n\n")
            for result in ocr_results:
                f.write(result.formatted)
                f.write("\n\n")

    # 紙面のページ番号（ノンブル）と章名。本文から柱を除いた分をここに残す（#99）
    chapter_titles = {
        number: max(votes.items(), key=lambda item: item[1])[0] for number, votes in chapter_title_votes.items()
    }
    meta_file = write_book_meta(output_path.parent, page_numbers, chapter_titles, fallback_pages)
    if meta_file is not None:
        print(
            f"  Book meta: {len(page_numbers)} page numbers, {len(chapter_titles)} chapter titles -> {meta_file.name}"
        )

    print(f"  OCR complete. Output saved to: {output_file}")
    return all_results


def main() -> None:
    """CLI interface for layout-aware OCR."""
    import argparse
    import json

    parser = argparse.ArgumentParser(description="Run layout-aware OCR on page images with detected regions.")
    parser.add_argument("pages_dir", help="Directory containing page images")
    parser.add_argument("-o", "--output", required=True, help="Output text file")
    parser.add_argument("--layout", required=True, help="Path to layout.json file")
    parser.add_argument(
        "--device",
        default="cpu",
        choices=["cpu", "cuda"],
        help="Device for Yomitoku OCR (default: cpu)",
    )
    parser.add_argument("--no-warmup", action="store_true", help="Skip model warm-up")
    args = parser.parse_args()

    # Load layout.json
    with open(args.layout) as f:
        layout_data = json.load(f)

    # Run OCR
    run_layout_ocr(
        pages_dir=args.pages_dir,
        layout_data=layout_data,
        output_file=args.output,
        device=args.device,
        warmup=not args.no_warmup,
    )


def run_yomitoku_ocr(
    pages_dir: str,
    output_file: str,
    device: str = "cpu",
) -> list[tuple[str, str]]:
    """Run yomitoku-based OCR on all pages.

    This function uses cached yomitoku results if available (from detect_layout_yomitoku).
    If cache is not found, it will run yomitoku analysis.

    Args:
        pages_dir: Directory containing page images.
        output_file: Path for combined output text file.
        device: Device for yomitoku ("cpu" or "cuda").

    Returns:
        List of (page_name, formatted_text) tuples.
    """
    import cv2

    from src.ocr_yomitoku import get_analyzer, load_yomitoku_results

    pages_path = Path(pages_dir)
    output_path = Path(output_file)
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create ocr_texts directory
    ocr_texts_dir = output_dir / "ocr_texts"
    ocr_texts_dir.mkdir(parents=True, exist_ok=True)

    pages = list_page_images(pages_path)
    all_results: list[tuple[str, str]] = []

    # Check if we need to initialize analyzer (for non-cached pages)
    analyzer = None
    cache_hits = 0
    cache_misses = 0

    for page_path in pages:
        page_name = page_path.name
        page_stem = page_path.stem
        print(f"  Processing {page_name}...")

        # Try to load from cache first
        results = load_yomitoku_results(str(output_dir), page_stem)

        if results is None:
            # Cache miss - run analyzer
            cache_misses += 1
            if analyzer is None:
                print("  Initializing Yomitoku OCR...")
                start = time.time()
                analyzer = get_analyzer(device)
                elapsed = time.time() - start
                print(f"  Yomitoku ready in {elapsed:.1f}s")

            cv_img = cv2.imread(str(page_path))
            if cv_img is None:
                print("    → Failed to load image")
                continue

            results, _, _ = analyzer(cv_img)
            print("    → Analyzed (no cache)")
        else:
            cache_hits += 1
            print("    → Loaded from cache")

        # Format paragraphs based on role
        formatted_parts = []
        for p in results.paragraphs:
            if not hasattr(p, "contents") or not p.contents:
                continue

            text = p.contents.strip()
            if not text:
                continue

            # Apply formatting based on role
            if hasattr(p, "role") and p.role == "section_headings":
                formatted_parts.append(f"## {text}")
            else:
                formatted_parts.append(text)

        formatted_text = "\n\n".join(formatted_parts)
        print(f"    → Processed {len(results.paragraphs)} paragraphs")

        # Write individual page result
        page_text_file = ocr_texts_dir / f"{page_stem}.txt"
        with open(page_text_file, "w", encoding="utf-8") as f:
            f.write(formatted_text)
            f.write("\n\n")
        print(f"    → Saved: {page_text_file.name}")

        all_results.append((page_name, formatted_text))

    # Write combined results
    with open(output_file, "w", encoding="utf-8") as f:
        for page_name, formatted_text in all_results:
            f.write(f"\n--- Page: {page_name} ---\n\n")
            f.write(formatted_text)
            f.write("\n\n")

    print(f"  OCR complete. Output saved to: {output_file}")
    if cache_hits > 0 or cache_misses > 0:
        print(f"  Cache: {cache_hits} hits, {cache_misses} misses")
    return all_results


if __name__ == "__main__":
    main()
