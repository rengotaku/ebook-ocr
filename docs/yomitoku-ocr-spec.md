# yomitoku-ocr 仕様書

## 概要

YomitokuをベースとしたOCRモジュール。YOLO layout検出と連携し、FIGURE領域をマスクした上でOCRを実行。構造化されたMarkdown出力を生成する。

## モジュール

`src/ocr_yomitoku_integrated.py`

## 処理フロー

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 入力: ページ画像 + YOLO layout.json                       │
├─────────────────────────────────────────────────────────────┤
│ 2. YOLO FIGURE領域をマスク（白塗り）                          │
├─────────────────────────────────────────────────────────────┤
│ 3. マスク画像をYomitokuに渡してOCR実行                        │
├─────────────────────────────────────────────────────────────┤
│ 4. Yomitoku出力を構造化:                                     │
│    - paragraphs (role=section_headings) → ## {text}         │
│    - paragraphs (role=None) → {text}                        │
│    - figures → [FIGURE: {order}]                            │
│    - tables → {markdown_table}                              │
├─────────────────────────────────────────────────────────────┤
│ 5. order順にソートしてMarkdown出力                           │
├─────────────────────────────────────────────────────────────┤
│ 6. 品質チェック（is_garbage）→ 失敗時はフォールバック         │
└─────────────────────────────────────────────────────────────┘
```

## 入力

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `image` | `PIL.Image` or `str` | ページ画像またはパス |
| `regions` | `list[dict]` | YOLO検出領域 `[{"type": "FIGURE", "bbox": [x1,y1,x2,y2]}, ...]` |
| `device` | `str` | Yomitokuデバイス (`"cpu"` or `"cuda"`) |

## 出力

### YomitokuOCRResult (dataclass)

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `text` | `str` | 構造化されたMarkdownテキスト |
| `raw_text` | `str` | 生テキスト（フォーマットなし） |
| `paragraphs` | `list[ParagraphItem]` | 段落リスト（box, role, order付き） |
| `figures` | `list[FigureItem]` | 図リスト（box, order付き） |
| `tables` | `list[TableItem]` | 表リスト（box, order, markdown付き） |
| `success` | `bool` | OCR成功フラグ |
| `error` | `str | None` | エラーメッセージ |

### ParagraphItem (dataclass)

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `text` | `str` | テキスト内容 |
| `box` | `list[int]` | `[x1, y1, x2, y2]` |
| `role` | `str | None` | `"section_headings"` or `None` |
| `order` | `int` | 読み順 |

### FigureItem (dataclass)

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `box` | `list[int]` | `[x1, y1, x2, y2]` |
| `order` | `int` | 読み順 |

### TableItem (dataclass)

| フィールド | 型 | 説明 |
|-----------|-----|------|
| `markdown` | `str` | Markdown形式の表 |
| `box` | `list[int]` | `[x1, y1, x2, y2]` |
| `order` | `int` | 読み順 |

## 関数

### `mask_figure_regions(image, regions) -> PIL.Image`

YOLO FIGURE領域を白塗りした画像を返す。

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `image` | `PIL.Image` | 元画像 |
| `regions` | `list[dict]` | YOLO領域（`type="FIGURE"`のみマスク） |

**戻り値**: マスク済み `PIL.Image`

### `run_yomitoku_ocr(image, regions, device) -> YomitokuOCRResult`

メイン関数。マスク→OCR→構造化を実行。

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `image` | `PIL.Image` or `str` | ページ画像 |
| `regions` | `list[dict] | None` | YOLO領域（Noneならマスクなし） |
| `device` | `str` | `"cpu"` or `"cuda"` |

**戻り値**: `YomitokuOCRResult`

### `format_structured_output(result) -> str`

YomitokuOCRResultからMarkdownテキストを生成。

**フォーマットルール**:

| 要素 | フォーマット |
|------|-------------|
| `role=section_headings` | `## {text}` |
| `role=None` (paragraph) | `{text}` |
| figure | `[FIGURE]` |
| table | `{markdown_table}` |

### `run_yomitoku_ocr_batch(pages_dir, layout_file, output_dir, device) -> list`

バッチ処理。全ページをOCR処理。

| パラメータ | 型 | 説明 |
|-----------|-----|------|
| `pages_dir` | `str` | ページ画像ディレクトリ |
| `layout_file` | `str | None` | layout.jsonパス |
| `output_dir` | `str` | 出力ディレクトリ |
| `device` | `str` | `"cpu"` or `"cuda"` |

**出力ファイル**:
- `{output_dir}/{page_stem}.txt` - 構造化Markdown
- `{output_dir}/{page_stem}_raw.txt` - 生テキスト
- `{output_dir}/../book_yomitoku.txt` - 全ページ結合

## CLI

```bash
python -m src.ocr_yomitoku_integrated <pages_dir> \
    -o <output_dir> \
    --layout <layout.json> \
    --device cpu|cuda
```

## Makefile ターゲット

```makefile
yomitoku-ocr: setup ## Run Yomitoku OCR (requires HASHDIR)
	PYTHONPATH=$(CURDIR) $(PYTHON) -m src.ocr_yomitoku_integrated \
		"$(HASHDIR)/pages" \
		-o "$(HASHDIR)/ocr_texts" \
		--layout "$(HASHDIR)/layout.json" \
		--device cpu
```

## フォールバック

品質チェック（`is_garbage()`）で失敗した場合:
1. PaddleOCRで再試行
2. それでも失敗ならTesseractで再試行
3. 全て失敗なら空文字列を返す

## 依存関係

- `yomitoku>=0.10.0`
- `PIL`
- `cv2`
- `numpy`

## 既存モジュールとの関係

| モジュール | 役割 | 状態 |
|-----------|------|------|
| `ocr_yomitoku.py` | 既存のyomitokuラッパー（シンプル版） | 維持 |
| `ocr_yomitoku_integrated.py` | 新規。YOLO連携+構造化出力 | **新規作成** |
| `ocr_integrated.py` | 複数エンジン統合（PaddleOCRベース） | 維持（別用途） |
| `ocr_ensemble.py` | 投票ベースのアンサンブル | 維持（別用途） |
