# Phase 4 RED テスト結果: US2 - 領域別OCR処理

**日付**: 2026-02-11
**Phase**: Phase 4 (US2 - 領域別OCR処理)
**ステータス**: RED - 全テスト FAIL

## サマリ

| 項目 | 値 |
|------|-----|
| Phase | Phase 4 (US2 - 領域別OCR処理) |
| FAIL テスト数 | 33 |
| テストファイル | tests/test_layout_ocr.py |
| 失敗理由 | `src/layout_ocr.py` が存在しない |

---

## FAIL テストリスト

### TestSelectOcrEngine (8テスト)

| テストメソッド | 検証内容 |
|--------------|---------|
| test_select_ocr_engine_text_returns_deepseek | TEXT領域に対してDeepSeek-OCRが選択される |
| test_select_ocr_engine_title_returns_deepseek | TITLE領域に対してDeepSeek-OCRが選択される |
| test_select_ocr_engine_figure_returns_vlm | FIGURE領域に対してVLMが選択される |
| test_select_ocr_engine_table_returns_deepseek | TABLE領域に対してDeepSeek-OCRが選択される |
| test_select_ocr_engine_caption_returns_deepseek | CAPTION領域に対してDeepSeek-OCRが選択される |
| test_select_ocr_engine_footnote_returns_deepseek | FOOTNOTE領域に対してDeepSeek-OCRが選択される |
| test_select_ocr_engine_formula_returns_deepseek | FORMULA領域に対してDeepSeek-OCRが選択される |
| test_select_ocr_engine_abandon_returns_skip | ABANDON領域に対してスキップが選択される |

### TestFormatOcrResult (8テスト)

| テストメソッド | 検証内容 |
|--------------|---------|
| test_format_ocr_result_title_adds_heading | TITLE: `## {text}` 形式 |
| test_format_ocr_result_text_unchanged | TEXT: `{text}` 形式（変更なし） |
| test_format_ocr_result_figure_adds_marker | FIGURE: `[FIGURE: {description}]` 形式 |
| test_format_ocr_result_caption_adds_italic | CAPTION: `*{text}*` 形式 |
| test_format_ocr_result_footnote_adds_superscript | FOOTNOTE: `^{text}^` 形式 |
| test_format_ocr_result_formula_adds_latex | FORMULA: `$${text}$$` 形式 |
| test_format_ocr_result_table_unchanged | TABLE: `{text}` 形式（変更なし） |
| test_format_ocr_result_abandon_returns_empty | ABANDON: 空文字を返す |

### TestCropRegion (3テスト)

| テストメソッド | 検証内容 |
|--------------|---------|
| test_crop_region_basic | bbox に基づく基本クロップ |
| test_crop_region_full_image | 全画像のクロップ |
| test_crop_region_boundary_clamp | 境界外 bbox のクランプ処理 |

### TestTextRegionOcr (2テスト)

| テストメソッド | 検証内容 |
|--------------|---------|
| test_text_region_uses_deepseek_ocr | TEXT領域が DeepSeek-OCR で処理される |
| test_text_region_ocr_result_format | TEXT領域の OCR 結果フォーマット |

### TestFigureRegionOcr (2テスト)

| テストメソッド | 検証内容 |
|--------------|---------|
| test_figure_region_uses_vlm | FIGURE領域が VLM で処理される |
| test_figure_region_ocr_result_format | FIGURE領域の VLM 結果フォーマット |

### TestTitleRegionOcr (2テスト)

| テストメソッド | 検証内容 |
|--------------|---------|
| test_title_region_uses_deepseek_ocr | TITLE領域が DeepSeek-OCR で処理される |
| test_title_region_formatted_as_heading | TITLE領域が見出しマークアップで出力される |

### TestResultConcatenation (3テスト)

| テストメソッド | 検証内容 |
|--------------|---------|
| test_ocr_by_layout_concatenates_results | 複数領域の OCR 結果が連結される |
| test_ocr_by_layout_respects_region_order | 領域順序が維持される |
| test_ocr_by_layout_skips_abandon_regions | ABANDON 領域がスキップされる |

### TestOcrResultDataclass (2テスト)

| テストメソッド | 検証内容 |
|--------------|---------|
| test_ocr_result_has_required_fields | OCRResult に必要なフィールドがある |
| test_ocr_result_immutable | OCRResult がイミュータブル |

### TestOcrByLayoutEdgeCases (3テスト)

| テストメソッド | 検証内容 |
|--------------|---------|
| test_ocr_by_layout_empty_regions | 空の regions で空リスト返却 |
| test_ocr_by_layout_unicode_text | Unicode 文字の正しい処理 |
| test_ocr_by_layout_mixed_region_types | 混在する領域タイプの処理 |

---

## 実装ヒント

### 1. OCRResult データクラス

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class OCRResult:
    """1領域のOCR出力。"""
    region_type: str   # 元の領域種類
    text: str          # OCR出力テキスト
    formatted: str     # フォーマット済みテキスト（Markdown形式）
```

### 2. select_ocr_engine() 関数

```python
def select_ocr_engine(region_type: str) -> str:
    """領域種類に応じたOCRエンジンを選択。

    Args:
        region_type: 領域の種類（TITLE, TEXT, FIGURE, etc.）

    Returns:
        "deepseek-ocr" | "vlm" | "skip"
    """
    # FIGURE -> VLM
    # ABANDON -> skip
    # 他 -> DeepSeek-OCR
```

### 3. format_ocr_result() 関数

```python
def format_ocr_result(region_type: str, text: str) -> str:
    """領域種類に応じたMarkdownフォーマットを適用。

    フォーマットルール（research.md準拠）:
    | Type | Format |
    |------|--------|
    | TITLE | `## {text}` |
    | TEXT | `{text}` |
    | TABLE | `{text}` |
    | FIGURE | `[FIGURE: {text}]` |
    | CAPTION | `*{text}*` |
    | FOOTNOTE | `^{text}^` |
    | FORMULA | `$${text}$$` |
    | ABANDON | `` (empty) |
    """
```

### 4. crop_region() 関数

```python
def crop_region(img: Image.Image, bbox: list[int]) -> Image.Image:
    """画像から bbox 領域をクロップ。

    Args:
        img: PIL Image
        bbox: [x1, y1, x2, y2]

    Returns:
        クロップされた PIL Image
    """
    x1, y1, x2, y2 = bbox
    return img.crop((x1, y1, x2, y2))
```

### 5. ocr_region() 関数

```python
def ocr_region(img: Image.Image, region: dict) -> OCRResult:
    """単一領域のOCR処理。

    Args:
        img: ページ全体の PIL Image
        region: {"type": str, "bbox": list[int], "confidence": float}

    Returns:
        OCRResult with text and formatted output
    """
    # 1. crop_region() で領域を切り出し
    # 2. select_ocr_engine() でエンジン選択
    # 3. OCR実行（deepseek-ocr or VLM）
    # 4. format_ocr_result() でフォーマット
    # 5. OCRResult を返す
```

### 6. ocr_by_layout() 関数

```python
def ocr_by_layout(page_path: str, layout: dict) -> list[OCRResult]:
    """ページ内の全領域をOCR処理。

    Args:
        page_path: ページ画像のパス
        layout: {"regions": list[dict], "page_size": [w, h]}

    Returns:
        各領域のOCRResult リスト（領域順序を維持）
    """
    # 1. 画像を読み込み
    # 2. regions をループ
    # 3. ABANDON はスキップ
    # 4. 各領域に ocr_region() を適用
    # 5. 結果リストを返す
```

---

## FAIL 出力例

```
============================= test session starts ==============================
platform linux -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0
...
tests/test_layout_ocr.py::TestSelectOcrEngine::test_select_ocr_engine_text_returns_deepseek FAILED
...

=================================== FAILURES ===================================
_______ TestSelectOcrEngine.test_select_ocr_engine_text_returns_deepseek _______

self = <tests.test_layout_ocr.TestSelectOcrEngine object at 0x...>

    def test_select_ocr_engine_text_returns_deepseek(self) -> None:
        """TEXT領域に対してDeepSeek-OCRが選択されることを検証。"""
>       from src.layout_ocr import select_ocr_engine
E       ModuleNotFoundError: No module named 'src.layout_ocr'

tests/test_layout_ocr.py:33: ModuleNotFoundError
...
============================== 33 failed in 0.20s ==============================
```

---

## 次ステップ

1. **Implementation (GREEN)**: `src/layout_ocr.py` を実装
   - T042: RED テスト結果読み取り
   - T043: crop_region() 関数実装（src/utils.py へ追加も可）
   - T044: select_ocr_engine() 関数実装
   - T045: format_ocr_result() 関数実装
   - T046: ocr_by_layout() 関数実装（統合）
   - T047: `make test` PASS 確認

2. **Verification**: 全テスト通過とリグレッションテスト確認
