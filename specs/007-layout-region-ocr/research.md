# Research: レイアウト検出に基づく領域別OCR

**Date**: 2026-02-11
**Feature**: 007-layout-region-ocr

## 1. DocLayout-YOLO 検出クラス

### 調査結果

[DocLayout-YOLO](https://github.com/opendatalab/DocLayout-YOLO) の DocStructBench モデルは以下の **10カテゴリ** を検出可能:

| # | Class Name | 日本語 | 用途 |
|---|-----------|--------|------|
| 0 | title | タイトル | OCR（見出しマーク付き） |
| 1 | plain text | 本文 | OCR |
| 2 | abandon | 破棄テキスト | スキップ（ヘッダー/フッター等） |
| 3 | figure | 図 | VLM説明 |
| 4 | figure_caption | 図キャプション | OCR |
| 5 | table | 表 | OCR（構造保持） |
| 6 | table_caption | 表キャプション | OCR |
| 7 | table_footnote | 表脚注 | OCR |
| 8 | isolated formula | 数式 | OCR/スキップ |
| 9 | formula_caption | 数式キャプション | OCR |

**Source**: [HuggingFace - DocLayout-YOLO-DocStructBench](https://huggingface.co/juliozhao/DocLayout-YOLO-DocStructBench)

### Decision

**全クラスを検出対象にする**（現在の3クラス→10クラス）

```python
LABEL_TYPE_MAP = {
    "title": "TITLE",
    "plain text": "TEXT",
    "abandon": "ABANDON",       # スキップ用
    "figure": "FIGURE",
    "figure_caption": "CAPTION",
    "table": "TABLE",
    "table_caption": "CAPTION",
    "table_footnote": "FOOTNOTE",
    "isolated formula": "FORMULA",
    "formula_caption": "CAPTION",
}
```

### Rationale

- モデル自体は変更不要（既に全クラス検出可能）
- `TARGET_LABELS` のフィルタを外すだけで拡張可能
- `abandon` クラスはOCR対象外として処理（ヘッダー/フッター/ページ番号等）

### Alternatives Considered

| Option | Description | Rejected Because |
|--------|-------------|------------------|
| 新モデル導入 | より高精度なモデルを探す | 現モデルで十分、変更コスト大 |
| テキスト領域のみ追加 | title, plain text のみ追加 | キャプション等の情報が失われる |

---

## 2. 読み順ソートアルゴリズム

### 調査結果

文書レイアウトの読み順決定には主に以下のアプローチがある:

1. **単純座標ソート**: Y座標優先、同一行内はX座標
2. **カラム検出**: 領域をカラムにグループ化してからソート
3. **XYカット**: 再帰的にページを水平/垂直分割
4. **グラフベース**: 領域間の関係をグラフ化して順序付け

### Decision

**カラム検出 + 座標ソート** の2段階アルゴリズム

```
1. X座標の重複度でカラムをグループ化
2. カラム内はY座標でソート
3. カラム間は左から右（横書きデフォルト）
```

### Rationale

- 2カラムレイアウト（書籍で一般的）に対応
- 実装がシンプル（50行以下）
- 縦書き対応は将来の拡張として分離

### Algorithm Pseudocode

```python
def sort_reading_order(regions: list[dict], page_width: int) -> list[dict]:
    """横書きレイアウトの読み順でソート"""
    if not regions:
        return regions

    # カラム検出: X座標の中央値でグループ化
    threshold = page_width * 0.4  # 40%以上離れていれば別カラム

    # 左カラム/右カラムに分類
    left_col = []
    right_col = []
    mid_x = page_width / 2

    for r in regions:
        center_x = (r["bbox"][0] + r["bbox"][2]) / 2
        if center_x < mid_x:
            left_col.append(r)
        else:
            right_col.append(r)

    # 各カラム内をY座標でソート
    left_col.sort(key=lambda r: r["bbox"][1])
    right_col.sort(key=lambda r: r["bbox"][1])

    # 左→右の順で結合
    return left_col + right_col
```

### Alternatives Considered

| Option | Description | Rejected Because |
|--------|-------------|------------------|
| XYカット | 再帰的分割 | 複雑、マンガパネルに不適 |
| MLベース | 学習済みモデル | 依存追加、オーバーエンジニアリング |
| 単純Y→X | 座標のみ | 2カラムで読み順が崩れる |

---

## 3. layout.json 構造変更

### 現在の構造

```json
{
  "page_001.png": {
    "figures": [
      {"type": "FIGURE", "bbox": [...], "confidence": 0.9, ...}
    ]
  }
}
```

### 新構造

```json
{
  "page_001.png": {
    "regions": [
      {"type": "TITLE", "bbox": [...], "confidence": 0.95},
      {"type": "TEXT", "bbox": [...], "confidence": 0.92},
      {"type": "FIGURE", "bbox": [...], "confidence": 0.88, "cropped_path": "..."}
    ],
    "page_size": [1920, 1080]
  }
}
```

### Decision

- `figures` → `regions` にリネーム
- `page_size` を追加（読み順ソートに使用）
- 後方互換性: `figures` キーも読み取り可能に

### Rationale

- 意味的に正確（figuresだけでなく全領域）
- page_sizeはソートに必要
- 既存出力との互換性維持

---

## 4. フォールバック戦略

### Decision

以下の条件でページ全体OCRにフォールバック:

1. 領域が検出されなかった
2. 検出領域のカバー率が30%未満
3. ページ全体が1つのFIGUREとして検出された

### Rationale

- 検出失敗時も出力を保証
- 30%は経験的しきい値（要調整）
- ページ全体FIGUREは誤検出の可能性高

---

## 5. OCRエンジン選択ルール（更新: 2026-02-13）

### Decision

| Region Type | OCR Engine | Output Format |
|-------------|------------|---------------|
| TITLE | Yomitoku | `## {text}` |
| TEXT | Yomitoku | `{text}` |
| TABLE | Yomitoku | Markdown table |
| FIGURE | VLM (gemma3:12b) | 除外（figures/で管理） |
| CAPTION | Yomitoku | `*{text}*` |
| FOOTNOTE | Yomitoku | `^{text}^` |
| FORMULA | スキップまたはOCR | `$${text}$$` |
| ABANDON | スキップ | なし |

### Rationale

- DeepSeek-OCR → Yomitoku に移行済み（精度向上）
- FIGUREはOCR出力から除外し、figures/ディレクトリで別管理
- ABANDONはヘッダー/フッターなのでスキップ

---

## 6. TITLE判定ロジック（FR-009）

### Decision

**YOLOとYomitokuの併用**によるTITLE判定:

```python
def is_title(region: dict, yomitoku_result: dict) -> bool:
    """TITLEかどうかを判定"""
    # YOLOでTITLEとして検出
    if region.get("type") == "TITLE":
        return True
    # Yomitokuの role が section_headings
    if yomitoku_result.get("role") == "section_headings":
        return True
    return False
```

### Rationale

- YOLOは視覚的特徴（フォントサイズ、位置）でTITLEを検出
- Yomitokuは意味的特徴（章番号、「第X章」パターン）でTITLEを検出
- 両方を併用することで検出精度向上

---

## 7. OCRフォールバック戦略（FR-010）

### Decision

Yomitoku出力が低品質の場合、**PaddleOCR → Tesseract** の順でフォールバック:

```python
def ocr_with_fallback(image: Image) -> str:
    """OCRフォールバック付き"""
    # 1. Yomitoku（メインOCR）
    result = yomitoku_ocr(image)
    if is_good_quality(result):
        return result

    # 2. PaddleOCR（フォールバック1）
    result = paddle_ocr(image)
    if is_good_quality(result):
        return result

    # 3. Tesseract（フォールバック2）
    return tesseract_ocr(image)
```

### 品質判定基準

- 空文字列
- 極端に短い（< 10文字）
- ゴミ文字の割合が高い（非ASCII/非日本語の割合）

### Rationale

- Yomitokuは通常最高精度だが、特定画像で失敗することがある
- PaddleOCRは中国語由来で日本語にも強い
- Tesseractは最も汎用的で安定

---

## 8. FIGUREマスク処理（FR-011）

### Decision

Yomitokuへの入力画像で**FIGURE領域のみを白塗りでマスク**:

```python
def mask_figures(image: Image, regions: list[dict]) -> Image:
    """FIGURE領域を白でマスク"""
    masked = image.copy()
    draw = ImageDraw.Draw(masked)
    for r in regions:
        if r["type"] == "FIGURE":
            draw.rectangle(r["bbox"], fill="white")
    return masked
```

### Rationale

- FIGUREをマスクすることで、Yomitokuが図内の文字を誤認識しない
- ABANDONはマスク不要（スキップされるため）
- TABLEはOCR対象なのでマスク不要

---

## 9. FIGURE出力管理（FR-012）

### Decision

FIGURE領域は**OCR出力から除外**し、**figures/ディレクトリで別管理**:

```
output/<hash>/
├── book.txt      # FIGURE除外のOCRテキスト
├── book.md       # FIGURE説明付きの最終出力
└── figures/      # FIGUREクロップ画像
    ├── page_001_figure1.png
    └── page_001_figure2.png
```

### Rationale

- book.txtはテキストのみ（音声合成等に利用）
- book.mdでFIGURE説明を統合（完全版）
- figures/で元画像を保持（後処理に利用可能）
