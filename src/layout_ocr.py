"""Region-based OCR processing with layout detection.

This module implements User Story 2: Region-based OCR Processing.
Each detected region is processed with the appropriate OCR engine:
- TEXT/TITLE/TABLE/CAPTION/FOOTNOTE/FORMULA: DeepSeek-OCR
- FIGURE: VLM (gemma3:12b)
- ABANDON: Skip

OCR Engine Selection Rules (from research.md):
| Region Type | OCR Engine | Output Format |
|-------------|------------|---------------|
| TITLE | DeepSeek-OCR | `## {text}` |
| TEXT | DeepSeek-OCR | `{text}` |
| TABLE | DeepSeek-OCR | Markdown table |
| FIGURE | VLM (gemma3:12b) | `[FIGURE: {description}]` |
| CAPTION | DeepSeek-OCR | `*{text}*` |
| FOOTNOTE | DeepSeek-OCR | `^{text}^` |
| FORMULA | DeepSeek-OCR | `$${text}$$` |
| ABANDON | Skip | None |
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path

import requests
from PIL import Image

from src.utils import encode_pil_image
from src.reading_order import sort_reading_order, remove_overlaps


def warm_up_model(
    model: str,
    base_url: str = "http://localhost:11434",
    timeout: int = 300,
) -> None:
    """Warm up the model by sending a dummy request to load it into memory.

    Args:
        model: Ollama model name.
        base_url: Ollama API base URL.
        timeout: Request timeout in seconds (longer for initial load).
    """
    print(f"  Loading model {model}...", end="", flush=True)
    start = time.time()

    # Create a minimal 1x1 white image
    dummy_img = Image.new("RGB", (1, 1), color="white")
    image_b64 = encode_pil_image(dummy_img)

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": "test",
                "images": [image_b64],
            },
        ],
        "stream": False,
        "options": {
            "temperature": 0.0,
            "num_predict": 1,
        },
    }

    try:
        response = requests.post(
            f"{base_url}/api/chat",
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()
        elapsed = time.time() - start
        print(f" loaded in {elapsed:.1f}s")
    except requests.RequestException as e:
        print(f" failed: {e}")
        print("  Continuing anyway (first request may timeout)...")


@dataclass(frozen=True)
class OCRResult:
    """1領域のOCR出力。"""

    region_type: str  # 元の領域種類
    text: str  # OCR出力テキスト
    formatted: str  # フォーマット済みテキスト（Markdown形式）


def select_ocr_engine(region_type: str) -> str:
    """領域種類に応じたOCRエンジンを選択。

    Args:
        region_type: 領域の種類（TITLE, TEXT, FIGURE, etc.）

    Returns:
        "deepseek-ocr" | "vlm" | "skip"
    """
    if region_type == "FIGURE":
        return "vlm"
    elif region_type == "ABANDON":
        return "skip"
    else:
        return "deepseek-ocr"


def format_ocr_result(region_type: str, text: str) -> str:
    """領域種類に応じたMarkdownフォーマットを適用。

    フォーマットルール（research.md準拠）:
    | Type | Format |
    |------|--------|
    | TITLE | `## {text}` |
    | TEXT | `{text}` |
    | TABLE | `{text}` |
    | FIGURE | `[FIGURE: {text}]` |
    | CAPTION | `*{text}*` |
    | FOOTNOTE | `^{text}^` |
    | FORMULA | `$${text}$$` |
    | ABANDON | `` (empty) |

    Args:
        region_type: 領域の種類
        text: OCR出力テキスト

    Returns:
        フォーマット済みテキスト
    """
    if region_type == "TITLE":
        return f"## {text}"
    elif region_type == "FIGURE":
        return f"[FIGURE: {text}]"
    elif region_type == "CAPTION":
        return f"*{text}*"
    elif region_type == "FOOTNOTE":
        return f"^{text}^"
    elif region_type == "FORMULA":
        return f"$${text}$$"
    elif region_type == "ABANDON":
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
    base_url: str = "http://localhost:11434",
    timeout: int = 120,
) -> OCRResult:
    """単一領域のOCR処理。

    Args:
        img: ページ全体の PIL Image
        region: {"type": str, "bbox": list[int], "confidence": float}
        base_url: Ollama API base URL
        timeout: Request timeout in seconds

    Returns:
        OCRResult with text and formatted output
    """
    region_type = region["type"]
    bbox = region["bbox"]

    # 1. 領域をクロップ
    cropped_img = crop_region(img, bbox)

    # 2. OCRエンジン選択
    engine = select_ocr_engine(region_type)

    # 3. ABANDON領域はスキップ
    if engine == "skip":
        return OCRResult(
            region_type=region_type,
            text="",
            formatted="",
        )

    # 4. OCR実行
    image_b64 = encode_pil_image(cropped_img)

    if engine == "vlm":
        # VLM (gemma3:12b) for FIGURE regions
        model = "gemma3:12b"
        prompt = "この画像を説明してください。"
    else:
        # DeepSeek-OCR for TEXT/TITLE/TABLE/etc.
        model = "deepseek-ocr"
        prompt = ""

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": prompt,
                "images": [image_b64],
            },
        ],
        "stream": False,
        "options": {
            "temperature": 0.1,
            "num_predict": 4096,
        },
    }

    response = requests.post(
        f"{base_url}/api/chat",
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()

    result_json = response.json()
    ocr_text = result_json["message"]["content"]

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

    フォールバック条件 (research.md):
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

    # OCR対象領域のみをフィルタ（ABANDONを除外）
    ocr_regions = [r for r in regions if r["type"] != "ABANDON"]
    if not ocr_regions:
        return True

    # 条件2: カバー率が閾値未満
    coverage = calculate_coverage(ocr_regions, page_size)
    if coverage < threshold:
        return True

    # 条件3: 単一FIGUREがページの90%以上をカバー
    if len(ocr_regions) == 1 and ocr_regions[0]["type"] == "FIGURE":
        if coverage >= 0.9:
            return True

    return False


def ocr_by_layout(
    page_path: str,
    layout: dict,
    base_url: str = "http://localhost:11434",
    timeout: int = 120,
) -> list[OCRResult]:
    """ページ内の全領域をOCR処理。

    Args:
        page_path: ページ画像のパス
        layout: {"regions": list[dict], "page_size": [w, h]}
        base_url: Ollama API base URL
        timeout: Request timeout in seconds

    Returns:
        各領域のOCRResult リスト（領域順序を維持）
    """
    regions = layout.get("regions", [])
    page_size = tuple(layout.get("page_size", [0, 0]))

    # フォールバック判定
    if should_fallback(regions, page_size):
        # ページ全体OCRを実行
        img = Image.open(page_path)
        image_b64 = encode_pil_image(img)

        payload = {
            "model": "deepseek-ocr",
            "messages": [
                {
                    "role": "user",
                    "content": "",
                    "images": [image_b64],
                },
            ],
            "stream": False,
            "options": {
                "temperature": 0.1,
                "num_predict": 4096,
            },
        }

        response = requests.post(
            f"{base_url}/api/chat",
            json=payload,
            timeout=timeout,
        )
        response.raise_for_status()

        result_json = response.json()
        ocr_text = result_json["message"]["content"]

        # フォールバック結果を返す
        return [
            OCRResult(
                region_type="FALLBACK",
                text=ocr_text,
                formatted=ocr_text,
            )
        ]

    # 画像を読み込み
    img = Image.open(page_path)

    # 各領域をOCR処理
    results = []
    for region in regions:
        # ABANDON領域はスキップ
        if region["type"] == "ABANDON":
            continue

        result = ocr_region(img, region, base_url=base_url, timeout=timeout)
        results.append(result)

    return results


def run_layout_ocr(
    pages_dir: str,
    layout_data: dict,
    output_file: str,
    base_url: str = "http://localhost:11434",
    timeout: int = 120,
    model: str = "deepseek-ocr",
    warmup: bool = True,
    warmup_timeout: int = 300,
) -> list[tuple[str, list[OCRResult]]]:
    """Run layout-aware OCR on all pages in a directory.

    This is the main entry point for OCR processing. It handles:
    - Model warmup
    - Reading order sorting
    - Per-page OCR processing
    - Individual and combined result output

    Args:
        pages_dir: Directory containing page images.
        layout_data: Layout detection results (from layout.json).
        output_file: Path for combined output text file.
        base_url: Ollama API base URL.
        timeout: Per-region OCR timeout in seconds.
        model: OCR model name for warmup.
        warmup: Whether to warm up the model before processing.
        warmup_timeout: Warmup timeout in seconds.

    Returns:
        List of (page_name, ocr_results) tuples.
    """
    pages_path = Path(pages_dir)
    output_path = Path(output_file)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Model warmup
    if warmup:
        print("  Warming up OCR model...")
        warm_up_model(model, base_url, timeout=warmup_timeout)
        print("  Model ready.")

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
            base_url=base_url,
            timeout=timeout,
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
        "--base-url",
        default="http://localhost:11434",
        help="Ollama API base URL",
    )
    parser.add_argument(
        "--timeout", type=int, default=120, help="Per-region OCR timeout (seconds)"
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
        base_url=args.base_url,
        timeout=args.timeout,
        warmup=not args.no_warmup,
    )


if __name__ == "__main__":
    main()
