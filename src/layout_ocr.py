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

from dataclasses import dataclass
from pathlib import Path

import requests
from PIL import Image

from src.utils import encode_pil_image


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
    timeout: int = 60,
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


def ocr_by_layout(
    page_path: str,
    layout: dict,
    base_url: str = "http://localhost:11434",
    timeout: int = 60,
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

    # 空のregionsリストの場合は空リストを返す
    if not regions:
        return []

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
