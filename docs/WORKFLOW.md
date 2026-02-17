# Video-to-Book ワークフロー完全ガイド

**最終更新**: 2026-02-18
**対象バージョン**: v5 (010-pipeline-refactoring)

## 概要

このドキュメントは、動画コンテンツから電子書籍形式への変換を行う完全なワークフローを説明します。各ステップは独立したCLIコマンドとして実行可能で、柔軟なパイプライン構築が可能です。

## 前提条件

### システム要件

- **Python**: 3.13以上
- **OS**: Linux, macOS, Windows (WSL推奨)
- **メモリ**: 最低8GB、推奨16GB以上
- **GPU**: オプション (CUDA対応GPUで高速化可能)

### 環境セットアップ

```bash
# リポジトリクローン
git clone <repository-url>
cd video-separater

# 仮想環境作成・有効化
python3.13 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 依存パッケージインストール
pip install -r requirements.txt

# pre-commit設定 (開発者向け)
pre-commit install
```

### 入力データ準備

- **動画ファイル**: `.mp4`, `.mov`, `.avi`等のサポート形式
- **保存先**: 十分な空き容量があるディレクトリ（動画1時間あたり約5-10GB）

---

## ステップバイステップ・ワークフロー

### Step 1: フレーム抽出

**目的**: 動画からスライド画像を時系列で抽出

**コマンド**:
```bash
python -m src.cli.extract_frames <VIDEO_PATH> -o <OUTPUT_DIR> [OPTIONS]
```

**実行例**:
```bash
# 基本実行 (1.5秒間隔でフレーム抽出)
python -m src.cli.extract_frames /path/to/lecture.mp4 -o output/frames

# カスタム間隔 (2秒間隔)
python -m src.cli.extract_frames /path/to/lecture.mp4 -o output/frames -i 2.0
```

**オプション**:
| オプション | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `-o, --output` | path | 必須 | フレーム出力ディレクトリ |
| `-i, --interval` | float | 1.5 | フレーム抽出間隔（秒） |

**出力**:
```
output/frames/
├── frame_00000.png
├── frame_00001.png
├── frame_00002.png
...
```

**注意事項**:
- 間隔が短いほど精度は上がりますが、処理時間とディスク容量が増加します
- スライド変化が少ない動画では間隔を長く（2-3秒）設定可能

---

### Step 2: 重複除去

**目的**: 同一スライドの重複フレームを除去し、ページ画像を生成

**コマンド**:
```bash
python -m src.cli.deduplicate <INPUT_DIR> -o <OUTPUT_DIR> [OPTIONS]
```

**実行例**:
```bash
# 基本実行 (ハッシュ閾値8)
python -m src.cli.deduplicate output/frames -o output/pages

# 厳格な重複判定 (閾値5)
python -m src.cli.deduplicate output/frames -o output/pages -t 5

# 緩い重複判定 (閾値12)
python -m src.cli.deduplicate output/frames -o output/pages -t 12
```

**オプション**:
| オプション | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `-o, --output` | path | 必須 | ページ出力ディレクトリ |
| `-t, --threshold` | int | 8 | ハッシュ閾値 (小さいほど厳格) |

**出力**:
```
output/pages/
├── page_000.png
├── page_001.png
├── page_002.png
...
```

**チューニング**:
- **閾値が小さい (3-6)**: 微細な変化も別ページと判定 → ページ数増加
- **閾値が大きい (10-15)**: 大きな変化のみ別ページと判定 → ページ数減少
- **推奨**: まずデフォルト8で実行し、結果を見て調整

---

### Step 2.5: 見開き分割 (オプション)

**目的**: 見開きページを左右に分割し、単ページ化

**コマンド**:
```bash
python -m src.cli.split_spreads <PAGES_DIR> [OPTIONS]
```

**実行例**:
```bash
# 基本実行 (アスペクト比1.2で見開き判定)
python -m src.cli.split_spreads output/pages

# カスタムアスペクト比 (横長が1.5倍以上を見開きと判定)
python -m src.cli.split_spreads output/pages --aspect-ratio 1.5

# トリム付き (左ページ左端5%、右ページ右端5%を切り取り)
python -m src.cli.split_spreads output/pages --left-trim 0.05 --right-trim 0.05
```

**オプション**:
| オプション | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `--aspect-ratio` | float | 1.2 | 見開き判定閾値 (width/height) |
| `--left-trim` | float | 0.0 | 左ページ左端トリム率 (0.0-1.0) |
| `--right-trim` | float | 0.0 | 右ページ右端トリム率 (0.0-1.0) |

**出力** (in-place更新):
```
output/pages/
├── page_000.png      # 元のまま
├── page_001_L.png    # 見開き左ページ
├── page_001_R.png    # 見開き右ページ
├── page_002.png      # 元のまま
...
```

**注意事項**:
- **実行後は自動再採番**: `page_000.png`, `page_001.png`, `page_002.png`...
- **破壊的操作**: 元のファイルは上書きされるため、事前にバックアップ推奨
- **スキップ条件**: 見開きページがない場合、このステップは不要

---

### Step 3: レイアウト検出

**目的**: ページ内のテキスト領域、図表領域を検出

**コマンド**:
```bash
python -m src.cli.detect_layout <PAGES_DIR> -o <OUTPUT_DIR> [OPTIONS]
```

**実行例**:
```bash
# CPU実行 (デフォルト)
python -m src.cli.detect_layout output/pages -o output/layout

# GPU実行 (CUDA環境)
python -m src.cli.detect_layout output/pages -o output/layout --device cuda
```

**オプション**:
| オプション | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `-o, --output` | path | 必須 | レイアウト出力ディレクトリ |
| `--device` | cpu/cuda | cpu | デバイス選択 |

**出力**:
```
output/layout/
├── layout_000.json
├── layout_001.json
├── layout_002.json
...
```

**JSONフォーマット例**:
```json
{
  "page": "page_000.png",
  "regions": [
    {
      "type": "text",
      "bbox": [100, 200, 500, 300],
      "confidence": 0.95
    },
    {
      "type": "figure",
      "bbox": [50, 400, 550, 700],
      "confidence": 0.88
    }
  ]
}
```

**パフォーマンス**:
- **CPU**: 1ページあたり約1-3秒
- **GPU (CUDA)**: 1ページあたり約0.2-0.5秒
- **推奨**: 大量ページ処理時はGPU使用

---

### Step 4: OCR実行

**目的**: 検出された領域からテキストを抽出

**コマンド**:
```bash
python -m src.cli.run_ocr <PAGES_DIR> -o <OUTPUT_DIR> [OPTIONS]
```

**実行例**:
```bash
# レイアウト情報なしで実行 (全ページOCR)
python -m src.cli.run_ocr output/pages -o output/ocr

# レイアウト情報を利用 (推奨)
python -m src.cli.run_ocr output/pages -o output/ocr --layout-dir output/layout

# GPU実行
python -m src.cli.run_ocr output/pages -o output/ocr --layout-dir output/layout --device cuda
```

**オプション**:
| オプション | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `-o, --output` | path | 必須 | OCR結果出力ディレクトリ |
| `--layout-dir` | path | なし | レイアウト情報ディレクトリ |
| `--device` | cpu/cuda | cpu | デバイス選択 |

**出力**:
```
output/ocr/
├── ocr_000.json
├── ocr_001.json
├── ocr_002.json
...
```

**JSONフォーマット例**:
```json
{
  "page": "page_000.png",
  "text_regions": [
    {
      "bbox": [100, 200, 500, 300],
      "text": "第1章 イントロダクション",
      "confidence": 0.92
    }
  ]
}
```

**パフォーマンス**:
- **CPU**: 1ページあたり約5-10秒
- **GPU (CUDA)**: 1ページあたり約1-2秒
- **推奨**: GPUがある場合は必ず使用

---

### Step 5: 統合

**目的**: OCR結果を統合し、プレーンテキストとMarkdown形式で出力

**コマンド**:
```bash
python -m src.cli.consolidate <OCR_DIR> -o <OUTPUT_DIR>
```

**実行例**:
```bash
python -m src.cli.consolidate output/ocr -o output
```

**オプション**:
| オプション | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `-o, --output` | path | 必須 | 最終出力ディレクトリ |

**出力**:
```
output/
├── book.txt    # プレーンテキスト
└── book.md     # Markdown形式
```

**book.md の例**:
```markdown
# 第1章 イントロダクション

この章では、プロジェクトの背景と目的について説明します。

## 1.1 背景

...
```

---

## 手動ステップ

### Markdownマーカーの追加

OCR結果（`book.md`）を確認し、必要に応じて以下のマーカーを手動で追加します。

#### 1. 章・セクションマーカー

**目的**: 見出しレベルを適切に設定し、構造を明確化

**修正前**:
```markdown
第1章 イントロダクション
1.1 背景
1.2 目的
```

**修正後**:
```markdown
# 第1章 イントロダクション

## 1.1 背景

## 1.2 目的
```

#### 2. 図表参照の修正

**目的**: 図表への参照を適切なMarkdown構文に修正

**修正前**:
```markdown
図1を参照してください。
```

**修正後**:
```markdown
![図1: システムアーキテクチャ](figures/fig_1.png)

図1を参照してください。
```

#### 3. ページ区切りの挿入

**目的**: 章の境目などで明示的な区切りを追加

**修正前**:
```markdown
## まとめ
...

第2章 詳細設計
```

**修正後**:
```markdown
## まとめ
...

---

# 第2章 詳細設計
```

#### 4. OCR誤認識の修正

OCRエラーの典型例:
- **0/O混同**: `O(log n)` → `0(log n)`
- **1/l混同**: `lst` → `1st`
- **句読点**: `。` → `．` (全角ピリオド)

**推奨ツール**:
- テキストエディタのFind & Replace機能
- 正規表現での一括置換

---

### 品質確認

#### テキスト量の確認

```bash
# 総行数確認
wc -l output/book.txt

# 文字数確認
wc -m output/book.txt

# ページ数確認
ls output/pages/*.png | wc -l
```

#### Markdown構文チェック (オプション)

```bash
# markdownlintインストール (Node.js必要)
npm install -g markdownlint-cli

# 構文チェック
markdownlint output/book.md
```

#### 視覚的確認

```bash
# Markdownプレビュー (VS Code, Typora等)
code output/book.md
```

**チェックポイント**:
- [ ] 章・セクション構造が正しく認識されているか
- [ ] 図表参照が適切に配置されているか
- [ ] OCR誤認識が許容範囲内か
- [ ] ページ順序が正しいか

---

## トラブルシューティング

### 一般的な問題

#### 問題: 入力ファイルが見つからない

**症状**:
```
Error: Input not found
```

**原因**:
- ファイルパスが間違っている
- 相対パスの基準ディレクトリが異なる

**解決策**:
```bash
# 絶対パスを使用
python -m src.cli.extract_frames /absolute/path/to/video.mp4 -o /absolute/path/to/output

# 現在のディレクトリを確認
pwd

# ファイル存在確認
ls -la /path/to/file
```

---

#### 問題: OCRが非常に遅い

**症状**: 1ページの処理に10秒以上かかる

**原因**:
- CPUモードで実行している
- メモリ不足

**解決策**:

**GPU使用 (推奨)**:
```bash
# CUDA環境確認
nvidia-smi

# GPU実行
python -m src.cli.run_ocr output/pages -o output/ocr --device cuda
```

**メモリ不足対策**:
```bash
# メモリ使用量確認
free -h

# スワップ領域追加 (Linux)
sudo fallocate -l 8G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

**バッチ処理**:
```bash
# ページを分割して処理
python -m src.cli.run_ocr output/pages/page_{000..100}.png -o output/ocr/batch1
python -m src.cli.run_ocr output/pages/page_{101..200}.png -o output/ocr/batch2
```

---

#### 問題: 見開き分割が不正確

**症状**: 単ページが分割される、または見開きが分割されない

**原因**:
- アスペクト比閾値が適切でない

**解決策**:

**閾値調整**:
```bash
# 見開き判定を厳しく (より横長のみ分割)
python -m src.cli.split_spreads output/pages --aspect-ratio 1.5

# 見開き判定を緩く (やや横長でも分割)
python -m src.cli.split_spreads output/pages --aspect-ratio 1.1
```

**手動確認**:
```bash
# ページアスペクト比を確認
identify -format "%f: %[fx:w/h]\n" output/pages/*.png | head -20
```

**推奨値**:
- **通常の書籍**: 1.2-1.3
- **スライド (16:9)**: 1.7-1.8
- **横長資料**: 1.4-1.5

---

#### 問題: OCR結果が文字化けする

**症状**: 日本語が正しく認識されない

**原因**:
- OCRエンジンの言語設定
- 画像品質が低い

**解決策**:

**画像品質向上**:
```bash
# フレーム抽出時の品質確認
python -m src.cli.extract_frames video.mp4 -o frames

# 元動画の解像度確認
ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0 video.mp4
```

**推奨入力品質**:
- **最低解像度**: 1280x720 (HD)
- **推奨解像度**: 1920x1080 (Full HD)
- **ビットレート**: 3 Mbps以上

---

#### 問題: 重複除去が過剰

**症状**: 異なるスライドが同一と判定される

**原因**:
- ハッシュ閾値が大きすぎる

**解決策**:
```bash
# 閾値を小さく (厳格に判定)
python -m src.cli.deduplicate output/frames -o output/pages -t 5

# 閾値別に実行して比較
python -m src.cli.deduplicate output/frames -o output/pages_t5 -t 5
python -m src.cli.deduplicate output/frames -o output/pages_t8 -t 8
python -m src.cli.deduplicate output/frames -o output/pages_t12 -t 12

# ページ数比較
ls output/pages_t5/*.png | wc -l
ls output/pages_t8/*.png | wc -l
ls output/pages_t12/*.png | wc -l
```

---

#### 問題: レイアウト検出モデルのロードに失敗

**症状**:
```
Error: Model load failed
```

**原因**:
- モデルファイルが未ダウンロード
- ネットワーク接続エラー

**解決策**:
```bash
# 手動ダウンロード
python -c "from doclayout_yolo import YOLOv10; YOLOv10('path/to/model')"

# ネットワーク確認
ping -c 3 huggingface.co

# プロキシ設定 (必要な場合)
export HTTP_PROXY=http://proxy.example.com:8080
export HTTPS_PROXY=http://proxy.example.com:8080
```

---

### デバッグ手法

#### ログ出力の有効化

現在のバージョンでは `--verbose` オプションは未実装ですが、将来的に追加予定です。

#### 中間ファイルの確認

各ステップの出力を確認することで、問題箇所を特定できます:

```bash
# Step 1出力確認
ls -lh output/frames/ | head -10

# Step 2出力確認
ls -lh output/pages/ | head -10

# Step 3出力確認 (JSON内容確認)
cat output/layout/layout_000.json | jq .

# Step 4出力確認 (JSON内容確認)
cat output/ocr/ocr_000.json | jq .
```

---

## ディレクトリ構造

### 処理完了後の標準構造

```
project_root/
├── input.mp4                # 入力動画
└── output/
    ├── frames/              # Step 1: フレーム抽出
    │   ├── frame_00000.png
    │   ├── frame_00001.png
    │   └── ...
    ├── pages/               # Step 2/2.5: 重複除去・見開き分割
    │   ├── page_000.png
    │   ├── page_001.png
    │   └── ...
    ├── layout/              # Step 3: レイアウト検出
    │   ├── layout_000.json
    │   ├── layout_001.json
    │   └── ...
    ├── ocr/                 # Step 4: OCR実行
    │   ├── ocr_000.json
    │   ├── ocr_001.json
    │   └── ...
    ├── book.txt             # Step 5: 統合結果 (プレーンテキスト)
    └── book.md              # Step 5: 統合結果 (Markdown)
```

---

## 一括実行スクリプト (参考)

全ステップを連続実行する簡易スクリプトです。

### 基本版

```bash
#!/bin/bash
set -e

VIDEO=$1
OUTPUT=${2:-output}

echo "=== Step 1: フレーム抽出 ==="
python -m src.cli.extract_frames "$VIDEO" -o "$OUTPUT/frames"

echo "=== Step 2: 重複除去 ==="
python -m src.cli.deduplicate "$OUTPUT/frames" -o "$OUTPUT/pages"

echo "=== Step 2.5: 見開き分割 (オプション) ==="
# 必要に応じてコメント解除
# python -m src.cli.split_spreads "$OUTPUT/pages"

echo "=== Step 3: レイアウト検出 ==="
python -m src.cli.detect_layout "$OUTPUT/pages" -o "$OUTPUT/layout"

echo "=== Step 4: OCR実行 ==="
python -m src.cli.run_ocr "$OUTPUT/pages" -o "$OUTPUT/ocr" --layout-dir "$OUTPUT/layout"

echo "=== Step 5: 統合 ==="
python -m src.cli.consolidate "$OUTPUT/ocr" -o "$OUTPUT"

echo "=== 完了 ==="
echo "出力: $OUTPUT/book.md"
```

### GPU対応版

```bash
#!/bin/bash
set -e

VIDEO=$1
OUTPUT=${2:-output}
DEVICE=${3:-cuda}  # デフォルトGPU使用

echo "=== Step 1: フレーム抽出 ==="
python -m src.cli.extract_frames "$VIDEO" -o "$OUTPUT/frames"

echo "=== Step 2: 重複除去 ==="
python -m src.cli.deduplicate "$OUTPUT/frames" -o "$OUTPUT/pages"

echo "=== Step 3: レイアウト検出 (GPU) ==="
python -m src.cli.detect_layout "$OUTPUT/pages" -o "$OUTPUT/layout" --device "$DEVICE"

echo "=== Step 4: OCR実行 (GPU) ==="
python -m src.cli.run_ocr "$OUTPUT/pages" -o "$OUTPUT/ocr" --layout-dir "$OUTPUT/layout" --device "$DEVICE"

echo "=== Step 5: 統合 ==="
python -m src.cli.consolidate "$OUTPUT/ocr" -o "$OUTPUT"

echo "=== 完了 ==="
echo "出力: $OUTPUT/book.md"
```

### 実行方法

```bash
# スクリプトに実行権限付与
chmod +x run_pipeline.sh

# 基本実行
./run_pipeline.sh /path/to/video.mp4 output

# GPU指定
./run_pipeline.sh /path/to/video.mp4 output cuda
```

**注意**: このスクリプトは参考実装です。実際の運用では各ステップの出力を確認しながら進めることを推奨します。

---

## Tips & ベストプラクティス

### パフォーマンス最適化

#### GPU使用

```bash
# GPUメモリ確認
nvidia-smi

# GPU使用時の推奨設定
python -m src.cli.detect_layout output/pages -o output/layout --device cuda
python -m src.cli.run_ocr output/pages -o output/ocr --device cuda
```

#### 並列処理

複数動画を処理する場合:

```bash
# GNU Parallelを使用
parallel -j 2 ./run_pipeline.sh {} output/{/.} ::: videos/*.mp4
```

---

### ディスク容量管理

```bash
# 各ステップ完了後、不要な中間ファイルを削除

# フレーム削除 (pagesがあれば不要)
rm -rf output/frames/

# レイアウトJSON削除 (OCR完了後)
rm -rf output/layout/

# OCR JSON削除 (book.md生成後)
rm -rf output/ocr/
```

---

### バッチ処理

大量の動画を処理する場合:

```bash
#!/bin/bash
for video in videos/*.mp4; do
    name=$(basename "$video" .mp4)
    ./run_pipeline.sh "$video" "output/$name"
done
```

---

### バックアップ

```bash
# 重要な中間ファイルをバックアップ
cp -r output/pages output/pages_backup

# 見開き分割前にバックアップ
cp -r output/pages output/pages_before_split
```

---

## 関連ドキュメント

- **[README.md](./README.md)**: プロジェクト概要
- **[YOMITOKU_ARCHITECTURE.md](./YOMITOKU_ARCHITECTURE.md)**: アーキテクチャ詳細
- **[YOMITOKU_MIGRATION.md](./YOMITOKU_MIGRATION.md)**: マイグレーションガイド
- **[quickstart.md](../specs/010-pipeline-refactoring/quickstart.md)**: クイックスタート
- **[cli-commands.md](../specs/010-pipeline-refactoring/contracts/cli-commands.md)**: CLI仕様

---

## フィードバック

このワークフローに関する改善提案やバグ報告は、GitHubのIssueでお願いします。
