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


# ページ全体 OCR に回す判定になっても、領域別の text と文字数がほぼ同じなら
# 見出しと読取順を優先して領域別を採る（#108）。この割合を下回る、または差が
# この文字数を超えるときは、図・表として検出された領域に本文が入っているとみなす。
LAYOUT_TEXT_KEEP_RATIO = 0.95
LAYOUT_TEXT_KEEP_SLACK = 20


def char_count(text: str) -> int:
    """見出し記号と空白を除いた文字数."""
    return len("".join(text.replace("#", "").split()))


def prefer_layout_text(page_text: str, region_text: str) -> bool:
    """ページ全体 OCR より領域別の text を採るかどうか.

    領域別のほうが文字数で大きく負けていなければ、見出し（``##``）と読取順が
    効く領域別を採る。負けているときは、図・表として検出された領域に本文が
    入っている（領域別では消える）ので、ページ全体 OCR を採る。
    """
    page_chars = char_count(page_text)
    region_chars = char_count(region_text)
    if page_chars == 0:
        return True
    return region_chars >= page_chars * LAYOUT_TEXT_KEEP_RATIO and page_chars - region_chars <= LAYOUT_TEXT_KEEP_SLACK


# 図として扱う領域。CODE は yomitoku が「コードらしく見える図・表」に付ける型で、
# 実際の書籍では図の中の文字であることが多い。本文には出さず、図として切り出す（#83）。
FIGURE_LIKE_TYPES = ("FIGURE", "CODE")


# 見出しの本文がこれで終わっていたら、見出しではなく本文の行とみなす（#90）
SENTENCE_ENDINGS = ("。", "、", "．", "！", "？")


def _format_title(text: str) -> str:
    """TITLE 領域を Markdown の見出しにする.

    - 空文字なら何も出さない（``## `` だけの行を作らない）
    - 文末記号で終わるなら見出しではなく本文の行なので、そのまま出す
    """
    stripped = text.strip()
    if not stripped:
        return ""
    if stripped.endswith(SENTENCE_ENDINGS):
        return stripped
    return f"## {stripped}"


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
    | FIGURE/CODE/ABANDON | `` (empty) |

    Args:
        region_type: 領域の種類
        text: OCR出力テキスト

    Returns:
        フォーマット済みテキスト
    """
    if region_type == "TITLE":
        return _format_title(text)
    elif region_type in FIGURE_LIKE_TYPES:
        # 図として扱うので本文には出さない（#83）
        return ""
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
    if region_type in (*FIGURE_LIKE_TYPES, "ABANDON"):
        return "skip"
    return "yomitoku"
