# Quickstart: レイアウト検出に基づく領域別OCR

**Date**: 2026-02-11
**Feature**: 007-layout-region-ocr

## Prerequisites

- Python 3.13+
- Ollama running with `deepseek-ocr` and `gemma3:12b` models
- Virtual environment setup (`make setup`)

## Quick Usage

### 1. Full Pipeline (推奨)

```bash
# 動画からテキスト抽出（領域別OCR有効）
make run VIDEO="path/to/video.mov"
```

### 2. Individual Steps

```bash
# Step 1-2: フレーム抽出 + 重複除去
make extract VIDEO="path/to/video.mov"

# Step 3: レイアウト検出（拡張版）
PYTHONPATH=. python src/detect_figures.py output/<hash>/pages -o output/<hash>

# Step 4: 領域別OCR
PYTHONPATH=. python src/layout_ocr.py output/<hash>/pages -o output/<hash>/book.txt --layout output/<hash>/layout.json

# Step 5: 図の説明（VLM）
PYTHONPATH=. python src/describe_figures.py output/<hash>/book.txt -o output/<hash>/book.md
```

## Configuration

`config.yaml` で設定可能:

```yaml
# レイアウト検出
min_confidence: 0.3          # 検出信頼度しきい値
coverage_threshold: 0.3      # フォールバック判定しきい値（30%未満でフォールバック）
min_region_area: 0.01        # 最小領域面積（ページ面積の1%）

# OCR
ocr_model: deepseek-ocr
ocr_timeout: 60

# VLM
vlm_model: gemma3:12b
vlm_timeout: 120
```

## Output Files

```
output/<hash>/
├── pages/              # 重複除去済みページ画像
├── figures/            # クロップされた図・表画像
├── layout.json         # レイアウト検出結果（拡張版）
├── book.txt            # OCR結果（領域別処理済み）
└── book.md             # 最終出力（図の説明付き）
```

## layout.json Format (New)

```json
{
  "page_001.png": {
    "regions": [
      {"type": "TITLE", "bbox": [100, 50, 500, 100], "confidence": 0.95},
      {"type": "TEXT", "bbox": [100, 120, 800, 600], "confidence": 0.92},
      {"type": "FIGURE", "bbox": [100, 620, 400, 900], "confidence": 0.88, "cropped_path": "figures/page_001_figure1.png"}
    ],
    "page_size": [1920, 1080]
  }
}
```

## Testing

```bash
# 全テスト実行
make test

# 特定モジュールのテスト
pytest tests/test_reading_order.py -v
pytest tests/test_layout_ocr.py -v
```

## Troubleshooting

### 読み順がおかしい

- 2カラムレイアウトで左→右の順序になっているか確認
- `layout.json` の `page_size` が正しいか確認

### フォールバックが多発する

- `min_confidence` を下げる（0.3 → 0.2）
- `coverage_threshold` を下げる（0.3 → 0.2）

### OCRが遅い

- 領域数が多い場合、各領域のOCRに時間がかかる
- `ocr_timeout` を増やす（60 → 120）
