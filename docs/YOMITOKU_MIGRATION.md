# Yomitoku統合アーキテクチャへの移行

**日付**: 2026-02-13
**バージョン**: v4 Pipeline

## 概要

YOLO + yomitoku の2段階処理から、yomitoku単体の統合処理へ移行しました。

## 問題の背景

### 発覚した問題

**タイトル認識失敗:**
```
page_0024.png に「すべての要求に応えてしまう」というタイトルが存在
→ OCR結果: "## " （空）
```

**原因分析:**

| 処理ステップ | 入力 | 結果 |
|-------------|------|------|
| YOLO検出 | 1224x1800 | ✅ TITLE検出（bbox正確） |
| 領域クロップ | bbox [50,132,595,184] | 545x52の扁平画像 |
| yomitoku OCR | 545x52 | ❌ 空文字（認識失敗） |
| フォールバック | なし | ❌ 未実装 |

**根本原因:**
- yomitokuは小さくクロップされた扁平画像（545x52）の認識に失敗
- ページ全体（1224x1800）では正常に認識可能
- YOLOで検出してクロップする方式自体に問題がある

### 追加で発見した問題

1. **重複処理**: yomitokuを2回実行（detect + OCR）
2. **FIGURE未対応**: yomitoku検出のFIGUREがlayout.jsonに含まれない

## 解決策

### アーキテクチャ変更

**旧方式（v3）:**
```
Step 3: YOLO検出 → layout.json
         ↓
Step 4: 領域クロップ → yomitoku OCR → テキスト
```

**新方式（v4）:**
```
Step 3+4: yomitoku（統合）
           ├→ layout.json（paragraphs + figures）
           ├→ layouts/ 可視化（box反映）
           ├→ ocr_texts/ テキスト（role判定）
           └→ yomitoku_cache/ 結果キャッシュ
```

### 主要な変更

#### 1. yomitoku統合処理

**src/ocr_yomitoku.py** - 新規関数:

```python
def detect_layout_yomitoku():
    """Layout検出 + 可視化 + キャッシュ保存"""
    results = analyzer(cv_img)  # 1回だけ実行

    # layout.json生成（paragraphs + figures）
    layout = paragraphs_to_layout(
        results.paragraphs,
        results.figures,
        page_size
    )

    # box可視化（赤=TITLE, 緑=TEXT, 青=FIGURE）
    visualize_layout(paragraphs, figures, output_path)

    # キャッシュ保存（重複実行防止）
    save_yomitoku_results(results)
```

#### 2. role判定によるフォーマット

```python
for p in results.paragraphs:
    if p.role == 'section_headings':
        output = f"## {p.contents}"  # タイトル
    else:
        output = p.contents           # 本文
```

#### 3. FIGURE検出対応

```python
# paragraphs（TEXT/TITLE）
for p in results.paragraphs:
    regions.append({
        'type': 'TITLE' if p.role == 'section_headings' else 'TEXT',
        'bbox': p.box,
    })

# figures
for f in results.figures:
    regions.append({
        'type': 'FIGURE',
        'bbox': f.box,
    })
```

#### 4. キャッシュ機構

**保存（detect_layout_yomitoku）:**
```python
results = analyzer(cv_img)
save_yomitoku_results(output_dir, page_stem, results)
```

**読み込み（run_yomitoku_ocr）:**
```python
results = load_yomitoku_results(output_dir, page_stem)
if results is None:
    # キャッシュミス → analyzer実行
    results = analyzer(cv_img)
else:
    # キャッシュヒット → 即座に使用
    print("→ Loaded from cache")
```

**効果:**
- 1回目: 8.01s（analyzer実行 + キャッシュ保存）
- 2回目: 0.00s（キャッシュから読み込み）
- **高速化: ∞倍**

## 廃止されたもの

### ファイル

- ~~`src/detect_figures.py`~~ - YOLO検出（不要）

### Makefileターゲット

- ~~`detect`~~ - YOLO-based layout detection
- ~~`layout-ocr`~~ - Region-based OCR with cropping
- ~~`OCR_MODEL`変数~~ - DeepSeek-OCR削除済み

## 新規追加

### Makefileターゲット

```makefile
yomitoku-detect  # Layout検出 + 可視化 + キャッシュ
yomitoku-ocr     # OCR（キャッシュ優先）
```

**使用例:**
```bash
# フルパイプライン
make run VIDEO=input.mp4

# 個別実行（既存ページ）
make yomitoku-detect HASHDIR=output/157012a97dcbebed
make yomitoku-ocr HASHDIR=output/157012a97dcbebed
```

### ディレクトリ構造

```
output/{hash}/
├── yomitoku_cache/      # ← NEW: yomitoku結果キャッシュ
│   ├── page_0001.pkl
│   └── ...
├── layouts/             # box可視化（赤=TITLE, 緑=TEXT, 青=FIGURE）
├── layout.json          # 領域情報（paragraphs + figures）
├── ocr_texts/           # ページ別OCRテキスト
└── book.txt             # 統合テキスト
```

## 検証結果

### page_0024.png（問題のページ）

**検出結果:**

| 種類 | 数 | 可視化 |
|------|----|----|
| TITLE | 1 | 🔴 赤枠 |
| TEXT | 6 | 🟢 緑枠 |
| FIGURE | 4 | 🔵 青枠 |

**OCR結果:**
```markdown
## すべての要求に応えてしまう  ← ✅ 正常認識

株式会社ロボチェック社は、このたび新しい製品企画...
```

**処理時間:**
- 旧方式: ~16s（YOLO 8s + yomitoku 8s）
- 新方式（1回目）: 8s（yomitoku統合）
- 新方式（2回目）: 0.00s（キャッシュ）

## マイグレーション手順

### 既存プロジェクトの場合

1. **出力ディレクトリをクリーンアップ:**
```bash
rm -rf output/*/layout.json
rm -rf output/*/layouts/
rm -rf output/*/ocr_texts/
```

2. **新パイプライン実行:**
```bash
make run VIDEO=your_video.mp4
```

3. **個別ステップ実行（オプション）:**
```bash
# Layout検出のみ
make yomitoku-detect HASHDIR=output/<hash>

# OCR再実行
make yomitoku-ocr HASHDIR=output/<hash>
```

### 注意事項

- **VLM_MODELは削除しない**: FIGURE説明生成で使用
- **キャッシュディレクトリ**: `yomitoku_cache/`は自動生成
- **互換性**: 旧layout.jsonとは非互換

## パフォーマンス比較

### 処理時間（100ページの場合）

| 処理 | 旧方式 | 新方式 | 改善 |
|------|--------|--------|------|
| Layout検出 | 800s（YOLO） | - | - |
| OCR | 800s（yomitoku） | 800s | - |
| **合計** | **1600s** | **800s** | **2倍高速** |

### 再実行（OCRのみ）

| 処理 | 旧方式 | 新方式（キャッシュ） | 改善 |
|------|--------|---------------------|------|
| OCR再実行 | 800s | 0s | **∞倍高速** |

## トラブルシューティング

### キャッシュが使われない

**症状:**
```
Cache: 0 hits, 1 misses
```

**原因:**
- `yomitoku-detect`を先に実行していない
- `yomitoku_cache/`ディレクトリが削除された

**解決:**
```bash
make yomitoku-detect HASHDIR=output/<hash>
```

### タイトルが認識されない

**症状:**
```
##
```

**原因:**
- 古いパイプライン（v3以前）を使用している

**解決:**
```bash
git pull
make clean-all
make setup
make run VIDEO=your_video.mp4
```

### FIGUREが検出されない

**症状:**
- layout.jsonにFIGUREなし
- 可視化に青枠なし

**原因:**
- 古いコード

**確認:**
```python
# src/ocr_yomitoku.py
def paragraphs_to_layout(paragraphs, figures, page_size):  # ← figuresあるか確認
```

## 参考リンク

- yomitoku: https://github.com/kotaro-kinoshita/yomitoku
- DocLayout-YOLO（廃止）: https://github.com/opendatalab/DocLayout-YOLO

## 変更履歴

- 2026-02-13: v4パイプライン実装（yomitoku統合）
- 2025-XX-XX: v3パイプライン（YOLO + yomitoku）
