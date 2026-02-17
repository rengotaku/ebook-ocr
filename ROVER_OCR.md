# ROVER OCR - Multi-Engine Voting System

ROVER (Recognizer Output Voting Error Reduction) implementation for OCR補完.

## 概要

yomitokuの欠損を他のOCRエンジン（PaddleOCR, EasyOCR, Tesseract）で補完するシステム。

### アーキテクチャ

```
入力画像
    ↓
┌────────────────────────────────────┐
│ 4つのOCRエンジンを並列実行          │
│ - Yomitoku (primary)               │
│ - PaddleOCR                        │
│ - EasyOCR                          │
│ - Tesseract                        │
└────────────────────────────────────┘
    ↓
┌────────────────────────────────────┐
│ 行レベルアライメント（y座標）       │
│ 各エンジンの結果を位置で対応付け    │
└────────────────────────────────────┘
    ↓
┌────────────────────────────────────┐
│ 投票・補完                          │
│ - 2エンジン以上一致 → 採用          │
│ - yomitoku欠損 → 他から補完         │
│ - 重み付け投票（yomitoku最優先）    │
└────────────────────────────────────┘
    ↓
補完済みテキスト
```

## ディレクトリ構造

```
ocr_output/
├── raw/                    # 処理前（各エンジン原文）
│   ├── yomitoku/
│   │   ├── page_001.txt
│   │   └── ...
│   ├── paddleocr/
│   │   └── ...
│   ├── easyocr/
│   │   └── ...
│   └── tesseract/
│       └── ...
└── rover/                  # 処理後（ROVER補完済み）
    ├── page_001.txt
    └── ...
```

`raw/`と`rover/`を比較することで、どこが補完されたか確認できます。

## 使用方法

### コマンドライン

```bash
python src/ocr_rover.py pages_dir -o ocr_output
```

オプション:
- `--engines`: 使用エンジン（デフォルト: yomitoku,paddleocr,easyocr,tesseract）
- `--primary`: プライマリエンジン（デフォルト: yomitoku）
- `--device`: Yomitokuデバイス（cpu/cuda）
- `--min-agreement`: 最低一致エンジン数（デフォルト: 2）

例:
```bash
# 全エンジン使用
python src/ocr_rover.py pages -o ocr_output

# yomitoku + paddleocr のみ
python src/ocr_rover.py pages -o ocr_output --engines yomitoku,paddleocr

# CUDA使用
python src/ocr_rover.py pages -o ocr_output --device cuda

# 厳格なモード（3エンジン以上一致が必要）
python src/ocr_rover.py pages -o ocr_output --min-agreement 3
```

### Python API

```python
from PIL import Image
from ocr_rover import run_rover_ocr, run_rover_batch

# 単一画像
image = Image.open("page_001.png")
result = run_rover_ocr(image)
print(result.text)
print(f"補完箇所: {result.gaps_filled}")
print(f"貢献度: {result.engine_contributions}")

# バッチ処理
results = run_rover_batch(
    pages_dir="pages",
    output_dir="ocr_output",
    engines=["yomitoku", "paddleocr", "easyocr"],
)
```

## エンジン重み付け

投票時の重み（高いほど優先）:
- yomitoku: 1.5（日本語特化、最高品質）
- paddleocr: 1.2（高精度）
- easyocr: 1.0（バランス型）
- tesseract: 0.8（基本的）

## 投票ルール

1. **完全一致**: 2エンジン以上が同じテキスト → そのまま採用
2. **類似一致**: 類似度80%以上 → 最高重みのテキスト採用
3. **不一致**: 重み付き投票で最高得票を採用
4. **欠損補完**: yomitoku欠損 + 他エンジン結果あり → 補完

## モジュール構成

- `ocr_output.py`: 出力管理（raw/roverディレクトリ）
- `ocr_engines.py`: エンジンラッパー（bbox付き結果取得）
- `ocr_rover.py`: ROVERアルゴリズム実装

## テスト

```bash
python test_rover.py
```

## 依存パッケージ

```
yomitoku
paddlepaddle
paddleocr
easyocr
pytesseract
Pillow
```

Tesseractは別途システムインストールが必要:
```bash
# Ubuntu/Debian
sudo apt install tesseract-ocr tesseract-ocr-jpn

# macOS
brew install tesseract tesseract-lang
```
