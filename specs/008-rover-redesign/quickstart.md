# Quickstart: ROVER OCR再設計

**Date**: 2026-02-14 | **Branch**: `008-rover-redesign`

## 概要

真のROVER（Recognizer Output Voting Error Reduction）アルゴリズムを実装。文字レベルでのアライメントと信頼度重み付き多数決投票を行い、単一エンジンより高精度な結果を得る。

### 例: 「ソフトウェア」vs「ソフトウエア」問題

| エンジン | 出力 | 信頼度 | 重み |
|----------|------|--------|------|
| yomitoku | ソフトウ**ェ**ア | 0.9 | 1.5 × 0.9 = 1.35 |
| paddle | ソフトウ**エ**ア | 0.95 | 1.2 × 0.95 = 1.14 |
| easy | ソフトウ**ェ**ア | 0.7 | 1.0 × 0.7 = 0.70 |

→ 位置4での投票: 「ェ」(1.35 + 0.70 = 2.05) > 「エ」(1.14) → **「ソフトウェア」**採用

## 前提条件

- Python 3.13+
- venv環境構築済み
- 依存パッケージインストール済み

```bash
make setup
```

## 基本的な使い方

### 1. 単一画像のROVER OCR

```python
from PIL import Image
from ocr_rover import run_rover_ocr

# 画像からROVER結果を取得
result = run_rover_ocr("path/to/image.png")

print(result.text)  # 統合済みテキスト
print(f"Gaps filled: {result.gaps_filled}")
print(f"Garbage filtered: {result.garbage_filtered}")
```

### 2. バッチ処理（ページディレクトリ）

```bash
make rover-ocr HASHDIR=output/<hash>
```

または:

```python
from ocr_rover import run_rover_batch

results = run_rover_batch(
    pages_dir="output/<hash>/pages",
    output_dir="output/<hash>/ocr_output",
)

for page_name, result in results:
    print(f"{page_name}: {len(result.lines)} lines")
```

### 3. 出力ファイル構造

```
ocr_output/
├── raw/
│   ├── yomitoku/
│   │   ├── page_0001.txt
│   │   └── ...
│   ├── paddleocr/
│   │   └── ...
│   └── easyocr/
│       └── ...
└── rover/
    ├── page_0001.txt
    └── ...
```

## 参加エンジン

| エンジン | 役割 | 前処理 | 重み |
|----------|------|--------|------|
| yomitoku | 主エンジン | なし | 1.5 |
| PaddleOCR | 補完 | なし | 1.2 |
| EasyOCR | 補完 | CLAHE | 1.0 |

**Tesseractは除外**（日本語精度低、断片化激しい）

## 真のROVERアルゴリズム

### 処理フロー

1. **ゴミフィルタ**: confidence < 0.5 を投票前に除外
2. **行アライメント**: y座標で各エンジンの行をマッチング
3. **文字アライメント**: difflib.SequenceMatcher で文字単位アライメント
4. **重み付き投票**: 各位置で `weight = engine_weight × confidence` による多数決
5. **結果統合**: 投票結果を連結して最終テキスト生成

### 信頼度の役割

- **投票の重み**: `weight = ENGINE_WEIGHTS[engine] × confidence`
- **ゴミフィルタ**: confidence < 0.5 は投票参加前に除外

### ゴミ判定条件

1. `confidence < 0.5`
2. 日本語を含まない5文字以下のASCII
3. 同一文字が5回以上繰り返し

## カスタマイズ

### エンジン指定

```python
result = run_rover_ocr(
    "image.png",
    engines=["yomitoku", "paddleocr"],  # EasyOCR除外
)
```

### 信頼度閾値変更

```python
result = run_rover_ocr(
    "image.png",
    min_confidence=0.6,  # より厳しく
)
```

### GPU使用

```python
result = run_rover_ocr(
    "image.png",
    yomitoku_device="cuda",
)
```

## トラブルシューティング

### エンジンが見つからない

```bash
# 依存パッケージの確認
pip list | grep -E "yomitoku|paddleocr|easyocr"
```

### 処理が遅い

1. `engines`パラメータでエンジン数を減らす
2. `yomitoku_device="cuda"`でGPU使用

### 結果が空

1. 画像パスが正しいか確認
2. `raw/`ディレクトリで各エンジンの出力を確認
3. `min_confidence`を下げてテスト

## テスト実行

```bash
# 全テスト
make test

# ROVERテストのみ
PYTHONPATH=. pytest tests/test_ocr_rover.py -v
```

## 次のステップ

1. `/speckit.tasks` でタスク生成
2. TDDで実装（RED → GREEN → Refactor）
3. 既存テストとの整合性確認
