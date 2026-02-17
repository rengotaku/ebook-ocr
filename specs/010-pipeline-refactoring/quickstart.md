# Quickstart: パイプライン・リファクタリング

**Date**: 2026-02-17
**Feature**: 010-pipeline-refactoring

## 概要

動画から電子書籍テキストを抽出するワークフロー。各ステップは独立したCLIコマンドとして実行可能。

## 前提条件

- Python 3.13+
- 仮想環境がアクティブ: `source venv/bin/activate`
- 依存パッケージインストール済み: `pip install -r requirements.txt`
- pre-commit設定済み: `pre-commit install`

## 基本ワークフロー

### Step 1: フレーム抽出

```bash
python -m src.cli.extract_frames input.mp4 -o output/frames -i 1.5
```

### Step 2: 重複除去

```bash
python -m src.cli.deduplicate output/frames -o output/pages -t 8
```

### Step 2.5: 見開き分割（オプション）

```bash
python -m src.cli.split_spreads output/pages --aspect-ratio 1.2
```

### Step 3: レイアウト検出

```bash
python -m src.cli.detect_layout output/pages -o output/layout --device cpu
```

### Step 4: OCR実行

```bash
python -m src.cli.run_ocr output/pages -o output/ocr --layout-dir output/layout
```

### Step 5: 統合

```bash
python -m src.cli.consolidate output/ocr -o output
```

## 手動ステップ

### Markdownマーカーの追加

OCR結果（`book.md`）を確認し、必要に応じて以下のマーカーを追加:

1. **章・セクションマーカー**: 見出しレベルを調整
2. **図表参照**: `![図N](figures/fig_N.png)` 形式に修正
3. **ページ区切り**: 必要に応じて `---` を挿入

### 品質確認

```bash
# テキストの行数確認
wc -l output/book.txt

# Markdown構文チェック（オプション）
markdownlint output/book.md
```

## トラブルシューティング

### 「Error: Input not found」

入力ファイル/ディレクトリのパスを確認。相対パスより絶対パス推奨。

### OCRが遅い

`--device cuda` オプションでGPUを使用（CUDA環境が必要）。

### 見開き分割が不正確

`--aspect-ratio` 値を調整。デフォルト1.2は横長画像を見開きと判定。

## ディレクトリ構造

処理完了後:
```
output/
├── frames/          # Step 1の出力
├── pages/           # Step 2/2.5の出力
├── layout/          # Step 3の出力
├── ocr/             # Step 4の出力
├── book.txt         # Step 5の出力（プレーンテキスト）
└── book.md          # Step 5の出力（Markdown）
```

## 一括実行スクリプト（参考）

全ステップを連続実行する場合:

```bash
#!/bin/bash
set -e

VIDEO=$1
OUTPUT=${2:-output}

python -m src.cli.extract_frames "$VIDEO" -o "$OUTPUT/frames"
python -m src.cli.deduplicate "$OUTPUT/frames" -o "$OUTPUT/pages"
python -m src.cli.split_spreads "$OUTPUT/pages"
python -m src.cli.detect_layout "$OUTPUT/pages" -o "$OUTPUT/layout"
python -m src.cli.run_ocr "$OUTPUT/pages" -o "$OUTPUT/ocr" --layout-dir "$OUTPUT/layout"
python -m src.cli.consolidate "$OUTPUT/ocr" -o "$OUTPUT"

echo "Done: $OUTPUT/book.md"
```

**注意**: このスクリプトは参考実装。実際の運用では各ステップの出力を確認しながら進めることを推奨。
