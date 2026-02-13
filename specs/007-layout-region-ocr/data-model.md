# Data Model: レイアウト検出に基づく領域別OCR

**Date**: 2026-02-11
**Feature**: 007-layout-region-ocr

## Entities

### Region（領域）

ページ内で検出された個別の領域。

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| type | string | 領域の種類 | enum: TITLE, TEXT, ABANDON, FIGURE, CAPTION, TABLE, FOOTNOTE, FORMULA |
| label | string | YOLOの検出ラベル | DocLayout-YOLOのクラス名 |
| bbox | list[int] | 境界ボックス [x1, y1, x2, y2] | x1 < x2, y1 < y2 |
| confidence | float | 検出信頼度 | 0.0 - 1.0 |
| cropped_path | string? | クロップ画像パス | FIGURE/TABLEのみ |

### PageLayout（ページレイアウト）

1ページ分の検出結果。

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| regions | list[Region] | 検出された領域リスト | 空の場合あり |
| page_size | tuple[int, int] | ページサイズ (width, height) | 正の整数 |

### Layout（レイアウト全体）

全ページの検出結果を格納する辞書。

```python
Layout = dict[str, PageLayout]  # key: page_001.png
```

### OCRResult（OCR結果）

1領域のOCR出力。

| Field | Type | Description | Constraints |
|-------|------|-------------|-------------|
| region_type | string | 元の領域種類 | Region.type と同じ |
| text | string | OCR出力テキスト | 空文字列可 |
| formatted | string | フォーマット済みテキスト | Markdown形式 |
| ocr_engine | string | 使用したOCRエンジン | yomitoku, paddleocr, tesseract |
| is_title | bool | TITLE判定結果 | YOLO or Yomitoku role |

---

## Data Flow

```
┌─────────────────┐
│   Page Image    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  DocLayout-YOLO │
│   (Detection)   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   PageLayout    │
│   (regions[])   │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  FIGURE Mask    │  ←── FIGURE領域を白塗り (FR-011)
│  (for Yomitoku) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Reading Order  │
│     Sort        │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Region-based   │  ←── Yomitoku → PaddleOCR → Tesseract (FR-010)
│      OCR        │      TITLE判定: YOLO + role (FR-009)
└────────┬────────┘
         │
         ├──────────────────────┐
         ▼                      ▼
┌─────────────────┐    ┌─────────────────┐
│   OCRResult[]   │    │   FIGURE files  │ ←── FR-012: FIGURE除外
│ (FIGURE除外)    │    │   (figures/)    │
└────────┬────────┘    └─────────────────┘
         │
         ▼
┌─────────────────┐
│  Combined Text  │
│   (book.txt)    │
└─────────────────┘
```

---

## layout.json Schema

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "description": "Layout detection results for all pages",
  "additionalProperties": {
    "type": "object",
    "properties": {
      "regions": {
        "type": "array",
        "items": {
          "type": "object",
          "properties": {
            "type": {
              "type": "string",
              "enum": ["TITLE", "TEXT", "ABANDON", "FIGURE", "CAPTION", "TABLE", "FOOTNOTE", "FORMULA"]
            },
            "label": { "type": "string" },
            "bbox": {
              "type": "array",
              "items": { "type": "integer" },
              "minItems": 4,
              "maxItems": 4
            },
            "confidence": {
              "type": "number",
              "minimum": 0,
              "maximum": 1
            },
            "cropped_path": { "type": "string" }
          },
          "required": ["type", "label", "bbox", "confidence"]
        }
      },
      "page_size": {
        "type": "array",
        "items": { "type": "integer" },
        "minItems": 2,
        "maxItems": 2
      }
    },
    "required": ["regions", "page_size"]
  }
}
```

---

## State Transitions

### Region Processing States

```
DETECTED → SORTED → OCR_PROCESSING → OCR_COMPLETE → FORMATTED
```

### Page Processing States

```
                    ┌──────────────┐
                    │   DETECTED   │
                    └──────┬───────┘
                           │
              ┌────────────┴────────────┐
              │                         │
              ▼                         ▼
    ┌─────────────────┐      ┌─────────────────┐
    │  REGION_BASED   │      │    FALLBACK     │
    │  (regions > 0   │      │  (regions = 0   │
    │   && coverage   │      │   || coverage   │
    │      > 30%)     │      │      < 30%)     │
    └────────┬────────┘      └────────┬────────┘
             │                        │
             ▼                        ▼
    ┌─────────────────┐      ┌─────────────────┐
    │  Per-region OCR │      │  Full-page OCR  │
    └────────┬────────┘      └────────┬────────┘
             │                        │
             └────────────┬───────────┘
                          │
                          ▼
                 ┌─────────────────┐
                 │    COMPLETE     │
                 └─────────────────┘
```

---

## Validation Rules

### Region Validation

1. **Minimum Area**: `(x2-x1) * (y2-y1) >= page_area * 0.01` (1%以上)
2. **Confidence Threshold**: `confidence >= 0.3` (検出時)、`>= 0.7` (OCR時)
3. **Bbox Bounds**: `0 <= x1 < x2 <= width`, `0 <= y1 < y2 <= height`

### Coverage Calculation

```python
def calculate_coverage(regions: list[Region], page_size: tuple[int, int]) -> float:
    """検出領域がページをカバーする割合を計算"""
    page_area = page_size[0] * page_size[1]
    total_region_area = sum(
        (r["bbox"][2] - r["bbox"][0]) * (r["bbox"][3] - r["bbox"][1])
        for r in regions
    )
    return total_region_area / page_area
```

### Overlap Detection

```python
def has_overlap(r1: Region, r2: Region) -> bool:
    """2つの領域が重複しているかチェック"""
    return not (
        r1["bbox"][2] < r2["bbox"][0] or  # r1が左
        r1["bbox"][0] > r2["bbox"][2] or  # r1が右
        r1["bbox"][3] < r2["bbox"][1] or  # r1が上
        r1["bbox"][1] > r2["bbox"][3]     # r1が下
    )
```
