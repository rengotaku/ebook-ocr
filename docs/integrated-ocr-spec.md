# Integrated OCR 仕様書

## 概要

Full-page OCR with layout-based structuring を実現する統合OCRシステム。

### 設計思想

1. **Full Page OCR**: 領域単位ではなくページ全体をOCRする（レイアウト検出の精度限界を考慮）
2. **DeepSeek中心**: DeepSeekをメインエンジンとし、他エンジンで補完
3. **マスキング**: DeepSeekにはTEXT領域のみ表示した画像を渡す（ノイズ除去）
4. **レイアウト活用**: YOLOのTITLE検出をMarkdownの見出しに反映

---

## アーキテクチャ

```
┌─────────────────────────────────────────────────────────────┐
│                    Input: Page Image                        │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    OCR Engines (Parallel)                   │
├─────────────┬─────────────┬─────────────┬─────────────────┤
│  PaddleOCR  │  Tesseract  │   EasyOCR   │    DeepSeek     │
│ (Full Page) │ (Full Page) │ (Full Page) │ (Masked Image)  │
│ + Positions │             │             │                 │
└─────────────┴─────────────┴─────────────┴─────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Quality Check                            │
│  • Garbage detection (反復文字、日本語比率、特殊文字)        │
│  • Engine priority by region type                          │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    TITLE Extraction                         │
│  • PaddleOCR boxes × YOLO TITLE regions                    │
│  • bbox_contains() for matching                            │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Markdown Structuring                     │
│  • TITLE → ## heading                                      │
│  • Clean up extra newlines                                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    Output Files                             │
│  • {page}_paddleocr.txt                                    │
│  • {page}_tesseract.txt                                    │
│  • {page}_easyocr.txt                                      │
│  • {page}_deepseek.txt                                     │
│  • {page}.txt (structured)                                 │
│  • book_integrated.txt (combined)                          │
└─────────────────────────────────────────────────────────────┘
```

---

## OCRエンジン

### 1. PaddleOCR

- **役割**: メインOCR + 位置情報取得（TITLE抽出用）
- **設定**:
  ```python
  PaddleOCR(
      lang="japan",
      use_doc_orientation_classify=False,
      use_doc_unwarping=False,
      use_textline_orientation=False,
      enable_mkldnn=False,  # PaddlePaddle 3.3.0 oneDNN bug回避
  )
  ```
- **出力**: テキスト + バウンディングボックス（rec_texts, rec_polys）

### 2. Tesseract

- **役割**: 補完エンジン（句読点・構造化テキストに強い）
- **設定**: `lang="jpn+eng"`
- **出力**: テキストのみ

### 3. EasyOCR

- **役割**: 補完エンジン（図中テキスト・吹き出しに強い）
- **設定**: `langs=["ja", "en"]`
- **出力**: テキストのみ

### 4. DeepSeek (VLM)

- **役割**: メインエンジン（マスク画像を読み込み）
- **特徴**: 高精度だがガーベジ出力のリスクあり
- **入力**: TEXT領域のみ表示したマスク画像
- **設定**: Ollama API経由、タイムアウト120秒

---

## マスキング処理

### 対象領域タイプ

| タイプ | マスク処理 |
|--------|-----------|
| TEXT | 表示（残す） |
| TITLE | 表示（残す） |
| CAPTION | 表示（残す） |
| FOOTNOTE | 表示（残す） |
| FIGURE | 白塗り |
| TABLE | 白塗り |
| FORMULA | 白塗り |
| ABANDON | 白塗り |

### 実装

```python
def create_text_mask(image, regions):
    # 白キャンバス作成
    masked = Image.new("RGB", image.size, (255, 255, 255))

    # TEXT系領域のみペースト
    for region in regions:
        if region["type"] in ["TEXT", "TITLE", "CAPTION", "FOOTNOTE"]:
            bbox = region["bbox"]
            cropped = image.crop(bbox)
            masked.paste(cropped, (bbox[0], bbox[1]))

    return masked
```

---

## 品質チェック

### is_garbage() 判定基準

1. **短すぎるテキスト**: 20文字未満
2. **反復文字**: 同一文字が50%以上
3. **日本語比率**: ひらがな・カタカナ・漢字が10%未満
4. **特殊文字過多**: 特殊文字が30%以上

### エンジン優先順位

| 領域タイプ | 優先順位 |
|-----------|---------|
| TEXT | deepseek → paddleocr → tesseract |
| TITLE | deepseek → paddleocr → tesseract |
| FIGURE | easyocr → paddleocr → tesseract |
| TABLE | paddleocr → deepseek → tesseract |
| CAPTION | deepseek → paddleocr → easyocr |
| FOOTNOTE | deepseek → paddleocr → tesseract |
| FORMULA | deepseek → paddleocr → tesseract |
| FALLBACK | paddleocr → tesseract → deepseek |

---

## TITLE抽出とMarkdown構造化

### TITLE抽出ロジック

1. PaddleOCRの結果（テキスト+位置）を取得
2. YOLOのTITLE領域とマッチング（bbox_contains, threshold=0.5）
3. マッチしたテキストをTITLEとして抽出

### Markdown変換

```python
def structure_text_with_titles(text, titles):
    for title_text, bbox in titles:
        # タイトルを ## 見出しに変換
        text = text.replace(title_text, f"\n## {title_text}\n", 1)
    return text
```

---

## 出力ファイル

### ページ単位

| ファイル | 内容 |
|---------|------|
| `{page}_paddleocr.txt` | PaddleOCR生テキスト |
| `{page}_tesseract.txt` | Tesseract生テキスト |
| `{page}_easyocr.txt` | EasyOCR生テキスト |
| `{page}_deepseek.txt` | DeepSeek生テキスト |
| `{page}.txt` | 構造化テキスト（TITLE→##） |

### 結合ファイル

| ファイル | 内容 |
|---------|------|
| `book_integrated.txt` | 全ページ結合（構造化） |

---

## 使用方法

### Makefile

```bash
make integrated-ocr HASHDIR=output/xxxxx
```

### Python直接実行

```bash
python -m src.ocr_integrated "pages_dir" -o "output_dir" --layout "layout.json"
```

### オプション

| オプション | デフォルト | 説明 |
|-----------|-----------|------|
| `--layout` | なし | layout.jsonパス（なしでもOK） |
| `--base-url` | http://localhost:11434 | Ollama APIベースURL |
| `--timeout` | 120 | DeepSeekタイムアウト（秒） |
| `--tesseract-lang` | jpn+eng | Tesseract言語 |
| `--easyocr-langs` | ja,en | EasyOCR言語（カンマ区切り） |
| `--paddleocr-lang` | japan | PaddleOCR言語 |

---

## 依存関係

```
paddlepaddle>=2.5.0
paddleocr>=2.7.0
pytesseract
easyocr
Pillow
requests
```

---

## 既知の問題と回避策

### PaddlePaddle 3.3.0 oneDNN PIR変換バグ

- **症状**: `ConvertPirAttribute2RuntimeAttribute not support attr SortDescendingInt64`
- **原因**: PaddlePaddle 3.3.0のoneDNN実装バグ
- **回避策**: `enable_mkldnn=False`
- **参考**: https://github.com/PaddlePaddle/PaddleOCR/issues/17539

### DeepSeekガーベジ出力

- **症状**: 無意味な文字列を出力
- **原因**: VLMの限界、画像品質、マスク処理の影響
- **回避策**: is_garbage()による品質チェック、フォールバックエンジン

---

## ファイル構成

```
src/
├── ocr_ensemble.py      # 個別OCRエンジン関数、品質チェック、マスキング
├── ocr_integrated.py    # 統合OCR処理、TITLE抽出、バッチ処理
tests/
├── test_ocr_integrated.py  # 統合OCRテスト
```

---

## 今後の拡張案

1. **TABLE構造化**: TABLEをMarkdownテーブルに変換
2. **FIGURE説明**: FIGUREにキャプション付与
3. **FORMULA LaTeX化**: 数式をLaTeX形式に変換
4. **信頼度スコア**: 各エンジンの信頼度を出力
5. **並列処理**: ページ単位の並列OCR処理
