# Video-to-Book ワークフロー完全ガイド

**最終更新**: 2026-02-26
**対象バージョン**: v5 (010-pipeline-refactoring)

## 概要

このドキュメントは、動画コンテンツから電子書籍形式への変換を行う完全なワークフローを説明します。

### ワークフロー全体像

```
動画 → フレーム抽出 → 重複除去 → レイアウト検出 → OCR → 統合
                                                           ↓
                                                        book.md (生OCR)
                                                           ↓
                                              【手動作業: マーカー追加】
                                                           ↓
                                                        book.md (構造化)
                                                           ↓
                                                        XML変換
                                                           ↓
                                                        book.xml (TTS対応)
```

### 処理の種類

- **自動処理** (Step 1-5): CLI コマンドで実行
- **手動処理**: book.md へのマーカー追加（ページ区切り、図、見出し）
- **XML変換** (Step 6): 構造化された book.md から book.xml を生成

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

**注意**: この段階の `book.md` は構造化されていない生のOCR結果です。次の「手動ステップ」でページマーカーや図マーカーを追加する必要があります。

---

## 手動ステップ

### book.md フォーマット仕様

OCR結果（`book.txt`）を `book.md` に変換する際、以下の仕様に従ってマーカーを追加します。

#### book.md の完全な例

```markdown
--- Page 1 (page_0001.png) ---

<!-- FIGURE: figures/page_0001_figure1.png -->
図の説明文がここに入る...

# 書籍タイトル

1 / 1

--- Page 2 (page_0002.png) ---

<!-- toc -->
第1章 概要 ............... 3
1.1 背景 ............... 3
1.2 目的 ............... 5
第2章 詳細 ............... 10
<!-- /toc -->

--- Page 3 (page_0003.png) ---

<!-- content -->
## 第1章 概要

本文...

- リスト項目1
- リスト項目2

はじめに 1 / 3
<!-- /content -->

--- Page 4 (page_0004.png) ---

<!-- content -->
### 1.1 背景

詳細な説明...
<!-- /content -->
```

---

### マーカー追加手順

#### 1. ページマーカーの追加（必須）

**目的**: 各ページの境界とファイル名を明示

**フォーマット**:
```markdown
--- Page N (page_XXXX.png) ---
```

**追加方法**:
```markdown
# 修正前（OCR結果のまま）
書籍タイトル

第1章 概要

# 修正後（ページマーカー追加）
--- Page 1 (page_0001.png) ---

書籍タイトル

--- Page 2 (page_0002.png) ---

第1章 概要
```

**注意**:
- `N` はページ番号（1から開始）
- `page_XXXX.png` は実際のファイル名と一致させる
- ページマーカーの前後に空行を入れる

---

#### 2. 図マーカーの追加（図がある場合）

**目的**: 図の位置と説明文を構造化

**フォーマット**:
```markdown
<!-- FIGURE: パス/to/画像.png -->
図の説明文
```

**追加方法**:
```markdown
# 修正前
図1: システムアーキテクチャ
本システムは3層構造になっています。

# 修正後
<!-- FIGURE: figures/page_0005_figure1.png -->
図1: システムアーキテクチャ
本システムは3層構造になっています。
```

**注意**:
- パスは `figures/` ディレクトリからの相対パス
- 図の説明文はマーカーの次の行に記述
- 複数行の説明も可能

---

#### 3. 見出しマーカーの追加

**目的**: 章・節・小節の階層構造を明確化

**フォーマット**:
- `#` : レベル1（章）
- `##` : レベル2（節）
- `###` : レベル3（小節）

**追加方法**:
```markdown
# 修正前
第1章 イントロダクション
1.1 背景
1.1.1 問題の所在

# 修正後
# 第1章 イントロダクション

## 1.1 背景

### 1.1.1 問題の所在
```

**注意**:
- 見出しの前後に空行を入れる
- 最大3階層まで（Constitution準拠）
- `####` 以上は使用しない

---

#### 4. 読み上げ制御マーカーの追加（オプション）

**目的**: 目次、索引、コラムなどの読み上げ制御

**マーカー一覧**:
| マーカー | 用途 | readAloud |
|---------|------|-----------|
| `<!-- toc -->` ... `<!-- /toc -->` | 目次範囲 | false |
| `<!-- content -->` ... `<!-- /content -->` | 読み上げ対象範囲 | true |
| `<!-- skip -->` ... `<!-- /skip -->` | 読み上げ非対象範囲 | false |

**追加方法**:

**目次ページ**:
```markdown
--- Page 2 (page_0002.png) ---

<!-- toc -->
第1章 SREとは ............... 15
1.1 SREの定義 ............... 16
1.1.1 歴史 ............... 17
第2章 信頼性の定義 ............... 25
おわりに ............... 100
<!-- /toc -->
```

**索引ページ**:
```markdown
--- Page 100 (page_0100.png) ---

<!-- skip -->
索引
あ行: 15, 23, 45
い行: 12, 34, 56
<!-- /skip -->
```

**本文ページ（明示的に読み上げ対象にする場合）**:
```markdown
--- Page 3 (page_0003.png) ---

<!-- content -->
# 第1章 SREとは

SREはGoogleが提唱したプラクティスです。
<!-- /content -->
```

**注意**:
- マーカーなしのページはデフォルトで `readAloud="false"`
- 目次は自動的に `<tableOfContents>` 要素に変換される
- 索引などの付録は `<!-- skip -->` で読み上げをスキップ

---

#### 5. ページメタデータの保持

**目的**: 章内ページ番号などのメタ情報を保存

**対象**:
- `1 / 1` 形式の章内ページ番号
- `はじめに 1 / 3` のような章名付きページ番号

**処理**:
```markdown
# そのまま残す（削除しない）
--- Page 2 (page_0002.png) ---

## 第1章 概要

本文...

はじめに 1 / 3
```

**注意**:
- これらのメタデータは XML 変換時に `<pageMetadata>` 要素になる
- 削除せずそのまま残す

---

#### 6. OCR誤認識の修正

**典型的なOCRエラー**:
- **0/O混同**: `O(log n)` → `0(log n)`
- **1/l混同**: `lst` → `1st`
- **句読点**: `。` → `．` (全角ピリオド)
- **空白**: `第 1章` → `第1章`

**推奨ツール**:
- テキストエディタのFind & Replace機能
- 正規表現での一括置換
- `sed` コマンド（一括処理）

**一括置換例**:
```bash
# 0/O混同修正（アルゴリズム記法）
sed -i 's/0(log n)/O(log n)/g' book.md

# 不要な空白削除
sed -i 's/第 \([0-9]\)章/第\1章/g' book.md
```

---

### Step 6: XML変換（book.md → book.xml）

**目的**: 構造化された book.md を TTS対応の XML 形式に変換

**前提条件**: book.md に以下のマーカーが追加済みであること
- ページマーカー（`--- Page N (file.png) ---`）
- 図マーカー（`<!-- FIGURE: path -->`）
- 見出しマーカー（`#`, `##`, `###`）

**コマンド**:
```bash
python -m src.book_converter.cli <INPUT.md> <OUTPUT.xml> [OPTIONS]
```

**実行例**:
```bash
# 基本実行
python -m src.book_converter.cli output/book.md output/book.xml

# 詳細ログ出力
python -m src.book_converter.cli output/book.md output/book.xml --verbose

# 柱検出閾値調整
python -m src.book_converter.cli output/book.md output/book.xml --running-head-threshold 0.3
```

**オプション**:
| オプション | 型 | デフォルト | 説明 |
|-----------|-----|-----------|------|
| `--verbose` | flag | false | 詳細ログ出力 |
| `--quiet` | flag | false | 警告を抑制 |
| `--running-head-threshold` | float | 0.2 | 柱検出閾値 (0.0-1.0) |

**出力**:
```
output/
└── book.xml    # TTS対応XML形式
```

**book.xml の例**:
```xml
<?xml version="1.0" encoding="UTF-8"?>
<book>
  <metadata>
    <title>書籍タイトル</title>
    <conversionDate>2026-02-26</conversionDate>
  </metadata>

  <page number="1" sourceFile="page_0001.png">
    <pageAnnouncement format="simple">1ページ</pageAnnouncement>

    <figure readAloud="optional">
      <file>figures/page_0001_figure1.png</file>
      <description>図の説明文...</description>
    </figure>

    <content readAloud="true">
      <heading level="1">書籍タイトル</heading>
    </content>

    <pageMetadata type="chapter-page">1 / 1</pageMetadata>
  </page>

  <!-- ... more pages ... -->
</book>
```

**エラーハンドリング**:
- 変換エラーが発生しても処理は継続
- エラー箇所は XML コメントでマーク
- 最後にエラーサマリーを表示

**変換後の用途**:
- TTS（Text-to-Speech）での読み上げ
- SSML形式への二次変換
- EPUB形式への変換

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
- [ ] **ページマーカー**: すべてのページに `--- Page N (page_XXXX.png) ---` があるか
- [ ] **図マーカー**: 図がある場合 `<!-- FIGURE: path -->` が追加されているか
- [ ] **見出し階層**: `#`, `##`, `###` で正しく階層化されているか（最大3階層）
- [ ] **読み上げ制御マーカー**: 目次に `<!-- toc -->`, 索引に `<!-- skip -->`, 本文に `<!-- content -->` が適切に配置されているか
- [ ] **ページメタデータ**: `1 / 1` 形式のメタデータが保持されているか
- [ ] **OCR誤認識**: 数式、アルゴリズム記法、句読点が正しいか
- [ ] **ページ順序**: ページ番号が連番になっているか

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
    ├── book.md              # Step 5: 統合結果 (Markdown、生OCR)
    └── book.xml             # Step 6: XML変換結果 (手動マーキング後)
```

---

## 一括実行スクリプト (参考)

全ステップを連続実行する簡易スクリプトです。

### 基本版（自動処理のみ）

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

echo "=== 自動処理完了 ==="
echo "出力: $OUTPUT/book.md"
echo ""
echo "次のステップ（手動作業）:"
echo "1. book.md にページマーカー、図マーカー、見出しマーカーを追加"
echo "   詳細: docs/WORKFLOW.md の「手動ステップ」セクション参照"
echo "2. XML変換: python -m src.book_converter.cli $OUTPUT/book.md $OUTPUT/book.xml"
```

### GPU対応版（自動処理のみ）

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

echo "=== 自動処理完了 ==="
echo "出力: $OUTPUT/book.md"
echo ""
echo "次のステップ（手動作業）:"
echo "1. book.md にページマーカー、図マーカー、見出しマーカーを追加"
echo "   詳細: docs/WORKFLOW.md の「手動ステップ」セクション参照"
echo "2. XML変換: python -m src.book_converter.cli $OUTPUT/book.md $OUTPUT/book.xml"
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
