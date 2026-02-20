"""Utility functions for layout-based OCR processing.

Helper functions extracted from layout_ocr.py to reduce file size.
"""

from __future__ import annotations

import re

from PIL import Image


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

    # 日本語（ひらがな/カタカナ/漢字）、英数字をカウント
    char_pattern = r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\w]"
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
    total_region_area = sum((r["bbox"][2] - r["bbox"][0]) * (r["bbox"][3] - r["bbox"][1]) for r in regions)
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
