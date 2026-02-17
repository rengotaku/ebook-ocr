# Yomitoku統合アーキテクチャ 技術仕様

**バージョン**: v4 Pipeline
**更新日**: 2026-02-13

## システムアーキテクチャ

### 全体フロー

```
┌──────────────────────────────────────────────────────────┐
│ Step 0-2: 前処理                                          │
│  Video → Frames → Dedup → Split Spreads                 │
└──────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│ Step 3+4: Yomitoku統合処理（本ドキュメントの焦点）        │
│                                                           │
│  ┌─────────────────────────────────────────┐             │
│  │ detect_layout_yomitoku()                │             │
│  │                                         │             │
│  │  1. yomitoku analyzer実行               │             │
│  │     ├→ paragraphs（TEXT/TITLE）         │             │
│  │     └→ figures（FIGURE）                │             │
│  │                                         │             │
│  │  2. layout.json生成                     │             │
│  │     └→ paragraphs + figures → regions  │             │
│  │                                         │             │
│  │  3. 可視化（box描画）                   │             │
│  │     ├→ 赤枠: TITLE                      │             │
│  │     ├→ 緑枠: TEXT                       │             │
│  │     └→ 青枠: FIGURE                     │             │
│  │                                         │             │
│  │  4. キャッシュ保存                      │             │
│  │     └→ yomitoku_cache/{page}.pkl       │             │
│  └─────────────────────────────────────────┘             │
│                         ↓                                 │
│  ┌─────────────────────────────────────────┐             │
│  │ run_yomitoku_ocr()                      │             │
│  │                                         │             │
│  │  1. キャッシュ確認                      │             │
│  │     ├→ HIT: load_yomitoku_results()    │             │
│  │     └→ MISS: analyzer実行              │             │
│  │                                         │             │
│  │  2. role判定によるフォーマット          │             │
│  │     ├→ section_headings → "## {text}"  │             │
│  │     └→ None → "{text}"                 │             │
│  │                                         │             │
│  │  3. 出力生成                            │             │
│  │     ├→ ocr_texts/{page}.txt            │             │
│  │     └→ book.txt                        │             │
│  └─────────────────────────────────────────┘             │
└──────────────────────────────────────────────────────────┘
                         ↓
┌──────────────────────────────────────────────────────────┐
│ Step 5: VLM Figure Description                           │
│  FIGURE領域 → VLM (gemma3:12b) → 図表説明               │
└──────────────────────────────────────────────────────────┘
```

## データフロー

### 入力 → 出力

```
pages/page_0024.png (1224x1800)
    ↓
┌───────────────────────────────────────┐
│ yomitoku DocumentAnalyzer             │
│                                       │
│ results.paragraphs:                   │
│  - Paragraph(role='section_headings', │
│              box=[50,134,589,179],    │
│              contents='すべての...')   │
│  - Paragraph(role=None,               │
│              box=[47,231,1154,573],   │
│              contents='株式会社...')   │
│  - ...                                │
│                                       │
│ results.figures:                      │
│  - Figure(box=[47,622,144,726])       │
│  - Figure(box=[47,971,146,1084])      │
│  - ...                                │
└───────────────────────────────────────┘
    ↓
┌───────────────────────────────────────┐
│ layout.json                           │
│ {                                     │
│   "page_0024.png": {                  │
│     "regions": [                      │
│       {                               │
│         "type": "TITLE",              │
│         "bbox": [50,134,589,179],     │
│         "confidence": 1.0             │
│       },                              │
│       {                               │
│         "type": "TEXT",               │
│         "bbox": [47,231,1154,573],    │
│         "confidence": 1.0             │
│       },                              │
│       {                               │
│         "type": "FIGURE",             │
│         "bbox": [47,622,144,726],     │
│         "confidence": 1.0             │
│       }                               │
│     ],                                │
│     "page_size": [1224, 1800]         │
│   }                                   │
│ }                                     │
└───────────────────────────────────────┘
    ↓
┌───────────────────────────────────────┐
│ ocr_texts/page_0024.txt               │
│                                       │
│ ## すべての要求に応えてしまう          │
│                                       │
│ 株式会社ロボチェック社は...            │
│                                       │
└───────────────────────────────────────┘
```

## API仕様

### detect_layout_yomitoku()

**目的**: Layout検出 + 可視化 + キャッシュ保存

**シグネチャ:**
```python
def detect_layout_yomitoku(
    pages_dir: str,
    output_dir: str,
    layouts_dir: str | None = None,
    device: str = "cpu",
) -> dict
```

**パラメータ:**
| 名前 | 型 | 説明 |
|------|-----|------|
| pages_dir | str | ページ画像ディレクトリ |
| output_dir | str | 出力ディレクトリ（layout.json保存先） |
| layouts_dir | str\|None | 可視化画像保存先（デフォルト: output_dir/layouts） |
| device | str | "cpu" or "cuda" |

**戻り値:**
```python
{
    "page_0024.png": {
        "regions": [
            {"type": "TITLE", "bbox": [...], "confidence": 1.0},
            {"type": "TEXT", "bbox": [...], "confidence": 1.0},
            {"type": "FIGURE", "bbox": [...], "confidence": 1.0}
        ],
        "page_size": [1224, 1800]
    }
}
```

**副作用:**
- `{output_dir}/layout.json` 生成
- `{layouts_dir}/{page}.png` 可視化画像生成
- `{output_dir}/yomitoku_cache/{page}.pkl` キャッシュ保存

**実行時間（目安）:**
- 1ページ: ~8秒（CPU）
- 100ページ: ~800秒（CPU）

### run_yomitoku_ocr()

**目的**: OCR処理（キャッシュ優先）

**シグネチャ:**
```python
def run_yomitoku_ocr(
    pages_dir: str,
    output_file: str,
    device: str = "cpu",
) -> list[tuple[str, str]]
```

**パラメータ:**
| 名前 | 型 | 説明 |
|------|-----|------|
| pages_dir | str | ページ画像ディレクトリ |
| output_file | str | 出力ファイルパス（book.txt） |
| device | str | "cpu" or "cuda" |

**戻り値:**
```python
[
    ("page_0024.png", "## すべての要求に応えてしまう\n\n株式会社..."),
    ("page_0025.png", "..."),
]
```

**副作用:**
- `{output_dir}/ocr_texts/{page}.txt` ページ別テキスト
- `{output_file}` 統合テキスト

**キャッシュ動作:**
```python
# キャッシュヒット
if cache_exists:
    results = load_yomitoku_results()  # 0.00s
else:
    results = analyzer(cv_img)         # ~8s
```

**実行時間（目安）:**
- キャッシュHIT: ~0秒
- キャッシュMISS: ~8秒/ページ

### paragraphs_to_layout()

**目的**: yomitoku結果 → layout.json形式変換

**シグネチャ:**
```python
def paragraphs_to_layout(
    paragraphs: list,
    figures: list,
    page_size: tuple[int, int]
) -> dict
```

**ロジック:**
```python
for p in paragraphs:
    if p.role == 'section_headings':
        type = 'TITLE'
    else:
        type = 'TEXT'

    regions.append({
        'type': type,
        'bbox': p.box,
        'confidence': 1.0
    })

for f in figures:
    regions.append({
        'type': 'FIGURE',
        'bbox': f.box,
        'confidence': 1.0
    })
```

### visualize_layout()

**目的**: box可視化（OpenCV描画）

**シグネチャ:**
```python
def visualize_layout(
    img_path: str,
    paragraphs: list,
    figures: list,
    output_path: str,
) -> None
```

**色定義:**
```python
TITLE:  color=(0, 0, 255),   thickness=3  # 赤
TEXT:   color=(0, 255, 0),   thickness=2  # 緑
FIGURE: color=(255, 0, 0),   thickness=3  # 青（BGR）
```

## キャッシュ仕様

### ファイル形式

**形式**: pickle（Python標準ライブラリ）

**パス**: `{output_dir}/yomitoku_cache/{page_stem}.pkl`

**内容**: yomitoku DocumentAnalyzerSchema
```python
{
    'paragraphs': [...],
    'figures': [...],
    'tables': [...],
    'words': [...]
}
```

### 保存/読み込み

**保存:**
```python
import pickle

def save_yomitoku_results(output_dir, page_stem, results):
    cache_file = f"{output_dir}/yomitoku_cache/{page_stem}.pkl"
    with open(cache_file, "wb") as f:
        pickle.dump(results, f)
```

**読み込み:**
```python
def load_yomitoku_results(output_dir, page_stem):
    cache_file = f"{output_dir}/yomitoku_cache/{page_stem}.pkl"
    if not cache_file.exists():
        return None

    with open(cache_file, "rb") as f:
        return pickle.load(f)
```

### キャッシュ無効化

**手動削除:**
```bash
rm -rf output/*/yomitoku_cache/
```

**再生成:**
```bash
make yomitoku-detect HASHDIR=output/<hash>
```

## yomitoku役割分類

### role属性

yomitokuは各paragraphに`role`属性を付与:

| role | 意味 | 出力フォーマット |
|------|------|-----------------|
| `section_headings` | タイトル・見出し | `## {text}` |
| `None` | 本文 | `{text}` |

### 検出ロジック

yomitoku内部でレイアウト解析により自動判定:
- フォントサイズ
- 位置（ページ上部等）
- 周辺テキストとの関係

## パフォーマンス最適化

### 並列処理（将来対応）

現在は逐次処理だが、並列化可能:

```python
from multiprocessing import Pool

def process_page(page_path):
    results = analyzer(cv_img)
    # ...

with Pool(processes=4) as pool:
    pool.map(process_page, pages)
```

**注意**: yomitokuのanalyzerはGPU使用時にメモリ競合の可能性

### GPU使用

```bash
make run VIDEO=input.mp4 DEVICE=cuda
```

**メモリ要件:**
- CPU: ~2GB/プロセス
- GPU: ~4GB VRAM

## エラーハンドリング

### 画像読み込み失敗

```python
cv_img = cv2.imread(str(page_path))
if cv_img is None:
    print(f"  → Failed to load image")
    continue
```

### yomitoku実行失敗

現在は未対応。将来的にフォールバック追加予定:

```python
try:
    results, _, _ = analyzer(cv_img)
except Exception as e:
    # Fallback to Tesseract
    text = ocr_tesseract(image)
```

## テスト

### 単体テスト

```bash
pytest tests/test_ocr_yomitoku.py -v
```

### 統合テスト

```bash
# 小規模テスト（1ページ）
python /tmp/video-separater/test_yomitoku_pipeline.py

# フルパイプライン
make run VIDEO=tests/fixtures/sample.mp4
```

### 性能テスト

```bash
# キャッシュ性能
python /tmp/video-separater/test_cache.py
```

## デバッグ

### ログレベル設定

yomitokuのログを抑制:
```bash
export YOMITOKU_LOG_LEVEL=ERROR
make run VIDEO=input.mp4
```

### 可視化確認

```bash
# Layout検出のみ実行
make yomitoku-detect HASHDIR=output/<hash>

# 可視化画像確認
open output/<hash>/layouts/page_0024.png
```

### キャッシュ状態確認

```bash
ls -lh output/*/yomitoku_cache/
```

## 依存関係

### Python パッケージ

```
yomitoku >= 0.2.0
opencv-python >= 4.8.0
numpy >= 1.24.0
Pillow >= 10.0.0
```

### システム要件

- Python 3.13+
- 2GB RAM（CPU）/ 4GB VRAM（GPU）
- 500MB ディスク（モデルキャッシュ）

## 今後の改善案

1. **並列処理**: multiprocessingでページ並列処理
2. **エラーハンドリング**: フォールバック機構
3. **キャッシュ管理**: 有効期限・自動削除
4. **進捗表示**: tqdmでプログレスバー
5. **TABLE対応**: results.tablesの処理追加

## 関連ドキュメント

- [YOMITOKU_MIGRATION.md](./YOMITOKU_MIGRATION.md) - マイグレーションガイド
- [specs/007-layout-region-ocr/](../specs/007-layout-region-ocr/) - 元の仕様書
- [research.md](../research.md) - 調査・検証結果
