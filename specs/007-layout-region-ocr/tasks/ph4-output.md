# Phase 4 Output: US2 - 領域別OCR処理

**日付**: 2026-02-11
**Phase**: Phase 4 (US2 - 領域別OCR処理)
**ステータス**: GREEN - 全テスト成功

## 作業サマリ

Phase 4では、User Story 2「領域別OCR処理」を実装しました。検出された各領域の種類に応じて適切なOCRエンジン（DeepSeek-OCR/VLM）を選択し、Markdownフォーマットで結果を出力する機能を追加しました。

### 完了タスク

| タスクID | 説明 | ステータス |
|---------|------|----------|
| T042 | RED テスト結果読み取り | ✅ 完了 |
| T043 | crop_region() 関数実装 | ✅ 完了 |
| T044 | select_ocr_engine() 関数実装 | ✅ 完了 |
| T045 | format_ocr_result() 関数実装 | ✅ 完了 |
| T046 | ocr_by_layout() 関数実装 | ✅ 完了 |
| T047 | `make test` PASS 確認 (GREEN) | ✅ 完了 |
| T048 | リグレッションテスト確認 | ✅ 完了 |
| T049 | Phase 4 出力生成 | ✅ 完了 |

**進捗**: 8/8 タスク完了 (100%)

---

## 変更ファイル一覧

### 実装追加

| ファイル | 変更種別 | 説明 |
|---------|---------|------|
| src/layout_ocr.py | 新規 | 領域別OCR dispatcher、OCRエンジン選択、フォーマット変換 |

### テスト追加

| ファイル | 変更種別 | 説明 |
|---------|---------|------|
| tests/test_layout_ocr.py | 既存 | Phase 4 RED テスト（33テストケース） |

---

## 実装の詳細

### 1. OCRResult データクラス (T043)

**ファイル**: `src/layout_ocr.py`

**実装**:
```python
@dataclass(frozen=True)
class OCRResult:
    """1領域のOCR出力。"""
    region_type: str   # 元の領域種類
    text: str          # OCR出力テキスト
    formatted: str     # フォーマット済みテキスト（Markdown形式）
```

**特徴**:
- `frozen=True` でイミュータブル
- 3つの必須フィールド: region_type, text, formatted

### 2. select_ocr_engine() 関数実装 (T044)

**ファイル**: `src/layout_ocr.py`

**アルゴリズム**:
```python
def select_ocr_engine(region_type: str) -> str:
    """領域種類に応じたOCRエンジンを選択。"""
    if region_type == "FIGURE":
        return "vlm"
    elif region_type == "ABANDON":
        return "skip"
    else:
        return "deepseek-ocr"
```

**OCRエンジン選択ルール**:
| Region Type | Engine | 理由 |
|------------|--------|------|
| FIGURE | vlm | 図の説明を生成 |
| ABANDON | skip | ヘッダー/フッター等は不要 |
| TEXT, TITLE, TABLE, CAPTION, FOOTNOTE, FORMULA | deepseek-ocr | テキスト読み取り |

### 3. format_ocr_result() 関数実装 (T045)

**ファイル**: `src/layout_ocr.py`

**フォーマットルール** (research.md準拠):
| Region Type | Input | Output |
|------------|-------|--------|
| TITLE | "第1章 概要" | "## 第1章 概要" |
| TEXT | "本文テキスト" | "本文テキスト" |
| FIGURE | "棒グラフを示す" | "[FIGURE: 棒グラフを示す]" |
| CAPTION | "図1: データ" | "*図1: データ*" |
| FOOTNOTE | "注: 参考" | "^注: 参考^" |
| FORMULA | "E = mc^2" | "$$E = mc^2$$" |
| TABLE | "&#124; A &#124; B &#124;" | "&#124; A &#124; B &#124;" |
| ABANDON | "ヘッダー" | "" (空文字) |

**実装**:
```python
def format_ocr_result(region_type: str, text: str) -> str:
    """領域種類に応じたMarkdownフォーマットを適用。"""
    if region_type == "TITLE":
        return f"## {text}"
    elif region_type == "FIGURE":
        return f"[FIGURE: {text}]"
    elif region_type == "CAPTION":
        return f"*{text}*"
    elif region_type == "FOOTNOTE":
        return f"^{text}^"
    elif region_type == "FORMULA":
        return f"$${text}$$"
    elif region_type == "ABANDON":
        return ""
    else:
        return text
```

### 4. crop_region() 関数実装 (T043)

**ファイル**: `src/layout_ocr.py`

**実装**:
```python
def crop_region(img: Image.Image, bbox: list[int]) -> Image.Image:
    """画像から bbox 領域をクロップ。"""
    x1, y1, x2, y2 = bbox
    return img.crop((x1, y1, x2, y2))
```

**Note**: 当初は `src/utils.py` への追加を想定していましたが、`src/layout_ocr.py` 内で完結させることでモジュール間の依存を削減しました。

### 5. ocr_region() 関数実装 (T046)

**ファイル**: `src/layout_ocr.py`

**アルゴリズム**:
1. `crop_region()` で領域を切り出し
2. `select_ocr_engine()` でエンジン選択
3. ABANDON領域は空のOCRResultを返す
4. OCR実行:
   - DeepSeek-OCR: `model="deepseek-ocr"`, prompt=""
   - VLM: `model="gemma3:12b"`, prompt="この画像を説明してください。"
5. `format_ocr_result()` でフォーマット
6. OCRResultを返す

**関数シグネチャ**:
```python
def ocr_region(
    img: Image.Image,
    region: dict,
    base_url: str = "http://localhost:11434",
    timeout: int = 60,
) -> OCRResult:
```

### 6. ocr_by_layout() 関数実装 (T046)

**ファイル**: `src/layout_ocr.py`

**アルゴリズム**:
1. layout から regions を取得
2. 空のregionsリストの場合は空リストを返す
3. ページ画像を読み込み
4. regions をループ:
   - ABANDON領域はスキップ
   - 各領域に `ocr_region()` を適用
   - OCRResultをリストに追加
5. 結果リストを返す

**関数シグネチャ**:
```python
def ocr_by_layout(
    page_path: str,
    layout: dict,
    base_url: str = "http://localhost:11434",
    timeout: int = 60,
) -> list[OCRResult]:
```

**特徴**:
- 領域順序を維持（読み順ソート済みを想定）
- ABANDON領域を自動スキップ
- 各領域を独立してOCR処理
- Ollama API (DeepSeek-OCR / VLM) を使用

---

## テスト結果

### Phase 4 テスト (tests/test_layout_ocr.py)

```
33 passed in 0.12s
```

#### 通過したテスト一覧

| テストクラス | テストメソッド | 検証内容 |
|------------|--------------|---------|
| TestSelectOcrEngine | test_select_ocr_engine_text_returns_deepseek | TEXT → deepseek-ocr |
| TestSelectOcrEngine | test_select_ocr_engine_title_returns_deepseek | TITLE → deepseek-ocr |
| TestSelectOcrEngine | test_select_ocr_engine_figure_returns_vlm | FIGURE → vlm |
| TestSelectOcrEngine | test_select_ocr_engine_table_returns_deepseek | TABLE → deepseek-ocr |
| TestSelectOcrEngine | test_select_ocr_engine_caption_returns_deepseek | CAPTION → deepseek-ocr |
| TestSelectOcrEngine | test_select_ocr_engine_footnote_returns_deepseek | FOOTNOTE → deepseek-ocr |
| TestSelectOcrEngine | test_select_ocr_engine_formula_returns_deepseek | FORMULA → deepseek-ocr |
| TestSelectOcrEngine | test_select_ocr_engine_abandon_returns_skip | ABANDON → skip |
| TestFormatOcrResult | test_format_ocr_result_title_adds_heading | TITLE: "## {text}" |
| TestFormatOcrResult | test_format_ocr_result_text_unchanged | TEXT: "{text}" |
| TestFormatOcrResult | test_format_ocr_result_figure_adds_marker | FIGURE: "[FIGURE: ...]" |
| TestFormatOcrResult | test_format_ocr_result_caption_adds_italic | CAPTION: "*{text}*" |
| TestFormatOcrResult | test_format_ocr_result_footnote_adds_superscript | FOOTNOTE: "^{text}^" |
| TestFormatOcrResult | test_format_ocr_result_formula_adds_latex | FORMULA: "$${text}$$" |
| TestFormatOcrResult | test_format_ocr_result_table_unchanged | TABLE: "{text}" |
| TestFormatOcrResult | test_format_ocr_result_abandon_returns_empty | ABANDON: "" |
| TestCropRegion | test_crop_region_basic | bbox基本クロップ |
| TestCropRegion | test_crop_region_full_image | 全画像クロップ |
| TestCropRegion | test_crop_region_boundary_clamp | 境界外bboxハンドリング |
| TestTextRegionOcr | test_text_region_uses_deepseek_ocr | TEXT領域がDeepSeek-OCRで処理 |
| TestTextRegionOcr | test_text_region_ocr_result_format | TEXT領域の結果フォーマット |
| TestFigureRegionOcr | test_figure_region_uses_vlm | FIGURE領域がVLMで処理 |
| TestFigureRegionOcr | test_figure_region_ocr_result_format | FIGURE領域の結果フォーマット |
| TestTitleRegionOcr | test_title_region_uses_deepseek_ocr | TITLE領域がDeepSeek-OCRで処理 |
| TestTitleRegionOcr | test_title_region_formatted_as_heading | TITLE領域が見出しマークアップ |
| TestResultConcatenation | test_ocr_by_layout_concatenates_results | 複数領域の結果連結 |
| TestResultConcatenation | test_ocr_by_layout_respects_region_order | 領域順序の維持 |
| TestResultConcatenation | test_ocr_by_layout_skips_abandon_regions | ABANDON領域のスキップ |
| TestOcrResultDataclass | test_ocr_result_has_required_fields | OCRResultの必須フィールド |
| TestOcrResultDataclass | test_ocr_result_immutable | OCRResultのイミュータビリティ |
| TestOcrByLayoutEdgeCases | test_ocr_by_layout_empty_regions | 空regions処理 |
| TestOcrByLayoutEdgeCases | test_ocr_by_layout_unicode_text | Unicode文字の処理 |
| TestOcrByLayoutEdgeCases | test_ocr_by_layout_mixed_region_types | 混在領域タイプの処理 |

### リグレッションテスト

関連テストファイル全て通過:
- `tests/test_layout_ocr.py`: 33/33 PASS (Phase 4)
- `tests/test_reading_order.py`: 20/20 PASS (Phase 3)
- `tests/test_ocr_deepseek.py`: 8/8 PASS
- `tests/test_utils.py`: 12/12 PASS

**合計**: 73/73 テスト成功

**Note**: `tests/test_detect_figures.py` の3件のテストは Phase 4 実装前から失敗しており（`doclayout_yolo` モジュール不足）、Phase 4 の変更とは無関係です。Phase 3 output でも同様の状況が記載されています。

---

## 次フェーズへの引き継ぎ

### 実装完了項目

1. ✅ **OCRResult データクラス**: イミュータブルなOCR結果格納
2. ✅ **select_ocr_engine()**: 領域種類に応じたエンジン選択
3. ✅ **format_ocr_result()**: Markdownフォーマット変換
4. ✅ **crop_region()**: 画像から領域クロップ
5. ✅ **ocr_region()**: 単一領域のOCR処理
6. ✅ **ocr_by_layout()**: ページ内全領域のOCR処理

### 後続フェーズでの利用可能な機能

- `ocr_by_layout(page_path, layout)`: ページ内の全領域をOCR処理
  - layout: `{"regions": [...], "page_size": [w, h]}`
  - 返り値: `list[OCRResult]`
  - 各領域を適切なエンジン（DeepSeek-OCR/VLM）で処理
  - ABANDON領域を自動スキップ
  - 領域順序を維持

- `OCRResult`: OCR結果の格納
  - `region_type`: 領域種類
  - `text`: OCR生テキスト
  - `formatted`: Markdownフォーマット済みテキスト

### Phase 5 で実装予定の機能

**User Story 4: フォールバック処理**
- レイアウト検出失敗時やカバー率低下時にページ全体OCRにフォールバック
- `calculate_coverage()`: 検出領域のカバー率計算
- `should_fallback()`: フォールバック判定ロジック
- カバー率しきい値: 30%（デフォルト）

**依存関係**:
- Phase 5は、Phase 4 で実装した `ocr_by_layout()` を拡張し、フォールバック処理を追加

---

## 発見した問題点

### なし

すべてのテストが成功し、既存機能への影響もありません。

---

## 備考

### OCRエンジン統合

**DeepSeek-OCR統合**:
- 既存の `src/ocr_deepseek.py` を参考に実装
- Ollama API `/api/chat` エンドポイントを使用
- `model="deepseek-ocr"`, prompt=""

**VLM統合**:
- モデル: `gemma3:12b`
- プロンプト: "この画像を説明してください。"
- FIGURE領域のみ使用

### モジュール構成の決定

当初は `crop_region()` を `src/utils.py` に追加する予定でしたが、以下の理由で `src/layout_ocr.py` 内に実装:

**利点**:
1. モジュール間の依存削減
2. layout_ocr 関連機能の凝集性向上
3. utils モジュールの肥大化防止

**トレードオフ**:
- `crop_region()` が他のモジュールで再利用される場合は utils への移動を検討

### Markdownフォーマット

各領域種類に応じたフォーマットは `research.md` の仕様に準拠:
- TITLE: 見出しマークアップ (`## `)
- FIGURE: 記述子マークアップ (`[FIGURE: ]`)
- CAPTION: イタリック (`*...*`)
- FOOTNOTE: スーパースクリプト (`^...^`)
- FORMULA: LaTeX (`$$...$$`)
- TEXT/TABLE: そのまま出力

### テストカバレッジ

Phase 4 では以下の観点をカバー:
- OCRエンジン選択ロジック (8テスト)
- フォーマット変換ロジック (8テスト)
- 領域クロップ機能 (3テスト)
- 各領域タイプのOCR処理 (6テスト)
- 複数領域の結果連結 (3テスト)
- データクラスの動作 (2テスト)
- エッジケース (3テスト)

---

**ステータス**: ✅ Phase 4 完了 - 次は Phase 5 (US4 - フォールバック処理) へ
