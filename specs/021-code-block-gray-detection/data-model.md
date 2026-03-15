# Data Model: コードブロック視覚検出

**Date**: 2026-03-12
**Feature**: 021-code-block-gray-detection

## エンティティ

### Region (既存 + 拡張)

layout.json 内のリージョン。CODE タイプが追加される。

| Field | Type | Description |
|-------|------|-------------|
| type | string | "TEXT" / "TITLE" / "CODE" / "FIGURE" / "ABANDON" |
| label | string | "plain text" / "section_headings" / "code" / "figure" |
| bbox | [int, int, int, int] | [x1, y1, x2, y2] 座標 |
| confidence | float | 検出信頼度（yomitoku は常に 1.0） |

**変更点**: `type` に `"CODE"` を追加、`label` に `"code"` を追加

### CodeDetectionConfig (新規)

config.yaml のコード検出設定セクション。

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| gray_background_threshold | float | 0.7 | 灰色画素比率の閾値 |
| gray_saturation_max | int | 30 | HSV 彩度の上限 |
| gray_value_min | int | 50 | HSV 明度の下限 |
| gray_value_max | int | 200 | HSV 明度の上限 |
| aspect_ratio_max | float | 8.0 | 帯状リージョン除外のアスペクト比上限 |
| symbol_ratio_threshold | float | 0.08 | 記号比率の閾値 |
| keyword_threshold | int | 2 | キーワード出現数の閾値 |
| fragment_gap_threshold | int | 80 | 断片結合の垂直ギャップ閾値（px） |

### CodeDetectionResult (関数戻り値、永続化なし)

コード判定の内部結果。デバッグ用。

| Field | Type | Description |
|-------|------|-------------|
| is_code | bool | CODE と判定されたか |
| gray_ratio | float / None | 灰色画素比率（画像分析時のみ） |
| symbol_ratio | float | 記号比率 |
| keyword_count | int | キーワード出現数 |
| detection_method | string | "gray_background" / "text_analysis" / "none" |

## データフロー

```
yomitoku paragraphs + figures
    ↓
paragraphs_to_layout(paragraphs, figures, page_size, cv_img)
    ├─ paragraph.role == "section_headings" → TITLE（判定スキップ）
    ├─ paragraph → TEXT
    │   ├─ detect_gray_background(cv_img, bbox) → True → CODE
    │   └─ detect_code_by_text(contents) → True → CODE
    ├─ figure → FIGURE
    │   └─ detect_code_by_text(figure.paragraphs text) → True → CODE
    └─ merge_code_fragments(regions) → 隣接 CODE を結合
    ↓
layout.json (regions with CODE type)
    ↓
run_layout_ocr()
    ├─ select_ocr_engine("CODE") → "yomitoku"
    └─ format_ocr_result("CODE", text) → ```\n{text}\n```
```
