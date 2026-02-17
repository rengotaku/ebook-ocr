"""Region-based OCR processing with layout detection.

This module implements User Story 2: Region-based OCR Processing.
Each detected region is processed with the appropriate OCR engine:
- TEXT/TITLE/TABLE/CAPTION/FOOTNOTE/FORMULA: Yomitoku
- FIGURE: Skip (excluded from text output)
- ABANDON: Skip

OCR Engine Selection Rules:
| Region Type | OCR Engine | Output Format |
|-------------|------------|---------------|
| TITLE | Yomitoku | `## {text}` |
| TEXT | Yomitoku | `{text}` |
| TABLE | Yomitoku | Markdown table |
| FIGURE | Skip | (excluded) |
| CAPTION | Yomitoku | `*{text}*` |
| FOOTNOTE | Yomitoku | `^{text}^` |
| FORMULA | Yomitoku | `$${text}$$` |
| ABANDON | Skip | None |
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from src.reading_order import sort_reading_order, remove_overlaps


@dataclass(frozen=True)
class OCRResult:
    """1領域のOCR出力。"""

    region_type: str  # 元の領域種類
    text: str  # OCR出力テキスト
    formatted: str  # フォーマット済みテキスト（Markdown形式）


def is_title(region: dict, yomitoku_result: dict | None = None) -> bool:
    """Check if region is a title based on YOLO detection or Yomitoku role.

    Args:
        region: Region dict with 'type' key
        yomitoku_result: Optional Yomitoku result with 'role' key

    Returns:
        True if YOLO type is 'TITLE' or yomitoku role is 'section_headings'
    """
    # YOLOでTITLEとして検出
    if region.get("type") == "TITLE":
        return True
    # Yomitokuの role が section_headings
    if yomitoku_result and yomitoku_result.get("role") == "section_headings":
        return True
    return False


def calc_non_char_ratio(text: str) -> float:
    """Calculate the ratio of non-text characters.

    Non-text: Not Japanese (hiragana/katakana/kanji), not alphanumeric, not common punctuation

    Returns:
        Ratio between 0.0 and 1.0
    """
    if not text:
        return 0.0

    import re
    # 日本語（ひらがな/カタカナ/漢字）、英数字をカウント
    char_pattern = r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\w]'
    chars = len(re.findall(char_pattern, text))
    return 1.0 - (chars / len(text))


def is_low_quality(text: str, min_length: int = 10, max_non_char_ratio: float = 0.5) -> bool:
    """Check if OCR result is low quality.

    Low quality criteria:
    - Empty string
    - Less than min_length characters
    - Non-char ratio > max_non_char_ratio
    """
    # 空文字列または空白のみ
    if not text or not text.strip():
        return True
    # 10文字未満
    if len(text.strip()) < min_length:
        return True
    # 非文字率 > 50%
    if calc_non_char_ratio(text) > max_non_char_ratio:
        return True
    return False


def ocr_with_fallback(image: Image.Image, device: str = "cpu") -> tuple[str, str]:
    """OCR with fallback chain: Yomitoku → PaddleOCR → Tesseract.

    Returns:
        (text, engine_name) tuple where engine_name is 'yomitoku', 'paddleocr', or 'tesseract'
    """
    from src.ocr_yomitoku import ocr_page_yomitoku
    from src.ocr_ensemble import ocr_paddleocr, ocr_tesseract

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


def select_ocr_engine(region_type: str) -> str:
    """領域種類に応じたOCRエンジンを選択。

    Args:
        region_type: 領域の種類（TITLE, TEXT, FIGURE, etc.）

    Returns:
        "yomitoku" | "skip"
    """
    if region_type in ("FIGURE", "ABANDON"):
        return "skip"
    else:
        return "yomitoku"


def format_ocr_result(region_type: str, text: str) -> str:
    """領域種類に応じたMarkdownフォーマットを適用。

    フォーマットルール:
    | Type | Format |
    |------|--------|
    | TITLE | `## {text}` |
    | TEXT | `{text}` |
    | TABLE | `{text}` |
    | CAPTION | `*{text}*` |
    | FOOTNOTE | `^{text}^` |
    | FORMULA | `$${text}$$` |
    | FIGURE/ABANDON | `` (empty) |

    Args:
        region_type: 領域の種類
        text: OCR出力テキスト

    Returns:
        フォーマット済みテキスト
    """
    if region_type == "TITLE":
        return f"## {text}"
    elif region_type == "CAPTION":
        return f"*{text}*"
    elif region_type == "FOOTNOTE":
        return f"^{text}^"
    elif region_type == "FORMULA":
        return f"$${text}$$"
    elif region_type in ("FIGURE", "ABANDON"):
        return ""
    else:
        # TEXT, TABLE: そのまま出力
        return text


def crop_region(img: Image.Image, bbox: list[int]) -> Image.Image:
    """画像から bbox 領域をクロップ。

    Args:
        img: PIL Image
        bbox: [x1, y1, x2, y2]

    Returns:
        クロップされた PIL Image
    """
    x1, y1, x2, y2 = bbox
    return img.crop((x1, y1, x2, y2))


def ocr_region(
    img: Image.Image,
    region: dict,
    yomitoku_device: str = "cpu",
) -> OCRResult:
    """単一領域のOCR処理。

    Args:
        img: ページ全体の PIL Image
        region: {"type": str, "bbox": list[int], "confidence": float}
        yomitoku_device: Device for Yomitoku ("cpu" or "cuda")

    Returns:
        OCRResult with text and formatted output
    """
    region_type = region["type"]
    bbox = region["bbox"]

    # 1. 領域をクロップ
    cropped_img = crop_region(img, bbox)

    # 2. OCRエンジン選択
    engine = select_ocr_engine(region_type)

    # 3. FIGURE/ABANDON領域はスキップ
    if engine == "skip":
        return OCRResult(
            region_type=region_type,
            text="",
            formatted="",
        )

    # 4. OCR実行 (Yomitoku)
    from src.ocr_yomitoku import ocr_page_yomitoku
    ocr_text = ocr_page_yomitoku("", device=yomitoku_device, img=cropped_img)

    # 5. フォーマット
    formatted_text = format_ocr_result(region_type, ocr_text)

    return OCRResult(
        region_type=region_type,
        text=ocr_text,
        formatted=formatted_text,
    )


def calculate_coverage(regions: list[dict], page_size: tuple[int, int]) -> float:
    """検出領域がページをカバーする割合を計算。

    Args:
        regions: 領域リスト [{"bbox": [x1, y1, x2, y2], ...}, ...]
        page_size: (width, height)

    Returns:
        カバー率 (0.0 - 1.0)
    """
    if not regions or page_size[0] <= 0 or page_size[1] <= 0:
        return 0.0

    page_area = page_size[0] * page_size[1]
    total_region_area = sum(
        (r["bbox"][2] - r["bbox"][0]) * (r["bbox"][3] - r["bbox"][1])
        for r in regions
    )
    return total_region_area / page_area


def should_fallback(
    regions: list[dict],
    page_size: tuple[int, int],
    threshold: float = 0.3,
) -> bool:
    """フォールバックが必要かどうかを判定。

    フォールバック条件:
    1. 領域が検出されなかった
    2. 検出領域のカバー率が30%未満
    3. ページ全体が1つのFIGUREとして検出された

    Args:
        regions: 領域リスト
        page_size: (width, height)
        threshold: カバー率しきい値 (デフォルト: 0.3)

    Returns:
        True: ページ全体OCRにフォールバック
        False: 領域別OCRを実行
    """
    # 条件1: 領域なし
    if not regions:
        return True

    # OCR対象領域のみをフィルタ（ABANDON/FIGUREを除外）
    ocr_regions = [r for r in regions if r["type"] not in ("ABANDON", "FIGURE")]
    if not ocr_regions:
        return True

    # 条件2: カバー率が閾値未満
    coverage = calculate_coverage(ocr_regions, page_size)
    if coverage < threshold:
        return True

    return False


def ocr_by_layout(
    page_path: str,
    layout: dict,
    yomitoku_device: str = "cpu",
) -> list[OCRResult]:
    """ページ内の全領域をOCR処理。

    Args:
        page_path: ページ画像のパス
        layout: {"regions": list[dict], "page_size": [w, h]}
        yomitoku_device: Device for Yomitoku ("cpu" or "cuda")

    Returns:
        各領域のOCRResult リスト（読み順ソート済み）
    """
    regions = layout.get("regions", [])
    page_size = tuple(layout.get("page_size", [0, 0]))

    # フォールバック判定
    if should_fallback(regions, page_size):
        # ページ全体OCRを実行 (Yomitoku)
        from src.ocr_yomitoku import ocr_page_yomitoku
        ocr_text = ocr_page_yomitoku(page_path, device=yomitoku_device)

        # フォールバック結果を返す
        return [
            OCRResult(
                region_type="FALLBACK",
                text=ocr_text,
                formatted=ocr_text,
            )
        ]

    # 読み順ソート適用
    if regions and page_size[0] > 0:
        regions = remove_overlaps(regions)
        regions = sort_reading_order(regions, page_size[0])

    # 画像を読み込み
    img = Image.open(page_path)

    # 各領域をOCR処理
    results = []
    for region in regions:
        # ABANDON/FIGURE領域はスキップ
        if region["type"] in ("ABANDON", "FIGURE"):
            continue

        result = ocr_region(
            img, region,
            yomitoku_device=yomitoku_device,
        )
        results.append(result)

    return results


def run_layout_ocr(
    pages_dir: str,
    layout_data: dict,
    output_file: str,
    yomitoku_device: str = "cpu",
    warmup: bool = True,
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
        yomitoku_device: Device for Yomitoku ("cpu" or "cuda").
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
        ocr_page_yomitoku("", device=yomitoku_device, img=dummy_img)
        elapsed = time.time() - start
        print(f"  Yomitoku ready in {elapsed:.1f}s")

    # Create ocr_texts directory for individual page results
    ocr_texts_dir = output_path.parent / "ocr_texts"
    ocr_texts_dir.mkdir(parents=True, exist_ok=True)

    pages = sorted(pages_path.glob("*.png"))
    all_results: list[tuple[str, list[OCRResult]]] = []

    for page_path in pages:
        page_name = page_path.name
        page_stem = page_path.stem
        print(f"  Processing {page_name}...")

        # Get layout for this page
        page_layout = layout_data.get(page_name, {"regions": [], "page_size": [0, 0]})
        regions = page_layout.get("regions", [])
        page_size = page_layout.get("page_size", [0, 0])

        # Sort regions in reading order & remove overlaps
        if regions and page_size[0] > 0:
            regions = remove_overlaps(regions)
            regions = sort_reading_order(regions, page_size[0])
            page_layout = {"regions": regions, "page_size": page_size}

        # Run layout-aware OCR
        ocr_results = ocr_by_layout(
            str(page_path),
            page_layout,
            yomitoku_device=yomitoku_device,
        )

        # Report status
        if ocr_results and ocr_results[0].region_type == "FALLBACK":
            print(f"    → Fallback: page-level OCR (low coverage or detection failure)")
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

    print(f"  OCR complete. Output saved to: {output_file}")
    return all_results


def main() -> None:
    """CLI interface for layout-aware OCR."""
    import argparse
    import json

    parser = argparse.ArgumentParser(
        description="Run layout-aware OCR on page images with detected regions."
    )
    parser.add_argument("pages_dir", help="Directory containing page images")
    parser.add_argument("-o", "--output", required=True, help="Output text file")
    parser.add_argument(
        "--layout", required=True, help="Path to layout.json file"
    )
    parser.add_argument(
        "--device",
        default="cpu",
        choices=["cpu", "cuda"],
        help="Device for Yomitoku OCR (default: cpu)",
    )
    parser.add_argument(
        "--no-warmup", action="store_true", help="Skip model warm-up"
    )
    args = parser.parse_args()

    # Load layout.json
    with open(args.layout) as f:
        layout_data = json.load(f)

    # Run OCR
    run_layout_ocr(
        pages_dir=args.pages_dir,
        layout_data=layout_data,
        output_file=args.output,
        yomitoku_device=args.device,
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
    from src.ocr_yomitoku import get_analyzer, load_yomitoku_results
    import cv2

    pages_path = Path(pages_dir)
    output_path = Path(output_file)
    output_dir = output_path.parent
    output_dir.mkdir(parents=True, exist_ok=True)

    # Create ocr_texts directory
    ocr_texts_dir = output_dir / "ocr_texts"
    ocr_texts_dir.mkdir(parents=True, exist_ok=True)

    pages = sorted(pages_path.glob("*.png"))
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
                print(f"    → Failed to load image")
                continue

            results, _, _ = analyzer(cv_img)
            print(f"    → Analyzed (no cache)")
        else:
            cache_hits += 1
            print(f"    → Loaded from cache")

        # Format paragraphs based on role
        formatted_parts = []
        for p in results.paragraphs:
            if not hasattr(p, 'contents') or not p.contents:
                continue

            text = p.contents.strip()
            if not text:
                continue

            # Apply formatting based on role
            if hasattr(p, 'role') and p.role == 'section_headings':
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
