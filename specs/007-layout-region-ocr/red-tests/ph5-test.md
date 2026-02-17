# Phase 5 テスト実装 (RED) 出力

**Date**: 2026-02-13
**Status**: RED (30 tests FAIL)

## サマリー

| 項目 | 値 |
|------|-----|
| Phase | 5: US2 - 領域別OCR処理 |
| 新規FAILテスト数 | 30 |
| 既存PASSテスト数 | 54 |
| テストファイル | tests/test_layout_ocr.py |

## FAILテスト一覧

### 1. TITLE判定テスト (TestIsTitleFunction)

| テストファイル | テストメソッド | 期待動作 | 失敗理由 |
|----------------|----------------|----------|----------|
| test_layout_ocr.py | test_is_title_yolo_title_type | YOLOでTITLEと検出された場合、Trueを返す | ImportError: is_title未実装 |
| test_layout_ocr.py | test_is_title_yomitoku_section_headings_role | Yomitokuのrole=section_headingsでTrueを返す | ImportError: is_title未実装 |
| test_layout_ocr.py | test_is_title_text_without_role_returns_false | 通常のTEXT領域でFalseを返す | ImportError: is_title未実装 |
| test_layout_ocr.py | test_is_title_yomitoku_paragraph_role | role=paragraphでFalseを返す | ImportError: is_title未実装 |
| test_layout_ocr.py | test_is_title_both_yolo_and_yomitoku_agree | 両方がTITLEと判定した場合、Trueを返す | ImportError: is_title未実装 |

### 2. 低品質判定テスト (TestIsLowQualityFunction)

| テストファイル | テストメソッド | 期待動作 | 失敗理由 |
|----------------|----------------|----------|----------|
| test_layout_ocr.py | test_is_low_quality_empty_string | 空文字列は低品質と判定 | ImportError: is_low_quality未実装 |
| test_layout_ocr.py | test_is_low_quality_short_text | 10文字未満は低品質と判定 | ImportError: is_low_quality未実装 |
| test_layout_ocr.py | test_is_low_quality_exactly_10_chars | 10文字以上は低品質でない | ImportError: is_low_quality未実装 |
| test_layout_ocr.py | test_is_low_quality_high_non_char_ratio | 非文字率>50%は低品質と判定 | ImportError: is_low_quality未実装 |
| test_layout_ocr.py | test_is_low_quality_normal_japanese_text | 通常の日本語テキストは低品質でない | ImportError: is_low_quality未実装 |
| test_layout_ocr.py | test_is_low_quality_mixed_content | 正常な混合テキストは低品質でない | ImportError: is_low_quality未実装 |
| test_layout_ocr.py | test_is_low_quality_whitespace_only | 空白のみは低品質と判定 | ImportError: is_low_quality未実装 |

### 3. 非文字率計算テスト (TestCalcNonCharRatio)

| テストファイル | テストメソッド | 期待動作 | 失敗理由 |
|----------------|----------------|----------|----------|
| test_layout_ocr.py | test_calc_non_char_ratio_all_japanese | 日本語のみ→0.0 | ImportError: calc_non_char_ratio未実装 |
| test_layout_ocr.py | test_calc_non_char_ratio_all_symbols | 記号のみ→1.0 | ImportError: calc_non_char_ratio未実装 |
| test_layout_ocr.py | test_calc_non_char_ratio_half_and_half | 半分ずつ→0.5 | ImportError: calc_non_char_ratio未実装 |
| test_layout_ocr.py | test_calc_non_char_ratio_empty_string | 空文字列の処理 | ImportError: calc_non_char_ratio未実装 |
| test_layout_ocr.py | test_calc_non_char_ratio_english_and_numbers | 英数字は文字として扱う | ImportError: calc_non_char_ratio未実装 |

### 4. OCRフォールバックテスト (TestOcrWithFallback)

| テストファイル | テストメソッド | 期待動作 | 失敗理由 |
|----------------|----------------|----------|----------|
| test_layout_ocr.py | test_ocr_with_fallback_yomitoku_success | Yomitoku成功時はそのまま返す | ImportError: ocr_with_fallback未実装 |
| test_layout_ocr.py | test_ocr_with_fallback_yomitoku_empty_uses_paddleocr | Yomitoku空→PaddleOCRへフォールバック | ImportError: ocr_with_fallback未実装 |
| test_layout_ocr.py | test_ocr_with_fallback_yomitoku_low_quality_uses_paddleocr | 低品質→PaddleOCRへフォールバック | ImportError: ocr_with_fallback未実装 |
| test_layout_ocr.py | test_ocr_with_fallback_paddleocr_fails_uses_tesseract | PaddleOCR失敗→Tesseractへフォールバック | ImportError: ocr_with_fallback未実装 |
| test_layout_ocr.py | test_ocr_with_fallback_all_fail_returns_empty | 全失敗→空文字列 | ImportError: ocr_with_fallback未実装 |

### 5. FIGUREマスクテスト (TestMaskFigures)

| テストファイル | テストメソッド | 期待動作 | 失敗理由 |
|----------------|----------------|----------|----------|
| test_layout_ocr.py | test_mask_figures_single_figure | 単一FIGURE領域が白塗り | ImportError: mask_figures未実装 |
| test_layout_ocr.py | test_mask_figures_multiple_figures | 複数FIGURE領域が全て白塗り | ImportError: mask_figures未実装 |
| test_layout_ocr.py | test_mask_figures_non_figure_regions_unchanged | TEXT/TABLE等はマスクされない | ImportError: mask_figures未実装 |
| test_layout_ocr.py | test_mask_figures_empty_regions | 空のリストで変更なし | ImportError: mask_figures未実装 |
| test_layout_ocr.py | test_mask_figures_returns_new_image | 元画像を変更せず新画像を返す | ImportError: mask_figures未実装 |

### 6. FIGURE除外テスト (TestFigureExclusion)

| テストファイル | テストメソッド | 期待動作 | 失敗理由 |
|----------------|----------------|----------|----------|
| test_layout_ocr.py | test_ocr_by_layout_excludes_figure_from_output | FIGUREがOCR結果から除外 | AssertionError: 現在FIGUREが含まれる |

### 7. 結果連結テスト (TestResultConcatenationWithReadingOrder)

| テストファイル | テストメソッド | 期待動作 | 失敗理由 |
|----------------|----------------|----------|----------|
| test_layout_ocr.py | test_results_concatenated_in_reading_order | 2カラムで左→右の読み順 | AssertionError: ソート順序が不正 |
| test_layout_ocr.py | test_results_maintain_sorted_order_for_single_column | 上から下の順序維持 | AssertionError: ソート順序が不正 |

## 実装ヒント

### 1. is_title() 関数

```python
def is_title(region: dict, yomitoku_result: dict) -> bool:
    """TITLEかどうかを判定。"""
    # YOLOでTITLEとして検出
    if region.get("type") == "TITLE":
        return True
    # Yomitokuの role が section_headings
    if yomitoku_result.get("role") == "section_headings":
        return True
    return False
```

### 2. calc_non_char_ratio() 関数

```python
import re

def calc_non_char_ratio(text: str) -> float:
    """非文字率（記号・空白）を計算。"""
    if not text:
        return 0.0
    # 日本語、英数字をカウント
    char_pattern = r'[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF\w]'
    chars = len(re.findall(char_pattern, text))
    return 1.0 - (chars / len(text))
```

### 3. is_low_quality() 関数

```python
def is_low_quality(text: str) -> bool:
    """OCR結果が低品質かどうかを判定。"""
    # 空文字列
    if not text or not text.strip():
        return True
    # 10文字未満
    if len(text.strip()) < 10:
        return True
    # 非文字率 > 50%
    if calc_non_char_ratio(text) > 0.5:
        return True
    return False
```

### 4. ocr_with_fallback() 関数

```python
def ocr_with_fallback(image: Image.Image, device: str = "cpu") -> tuple[str, str]:
    """OCRフォールバック付き。Returns (text, engine_used)."""
    from src.ocr_yomitoku import ocr_page_yomitoku
    from src.ocr_ensemble import ocr_paddleocr, ocr_tesseract

    # 1. Yomitoku
    text = ocr_page_yomitoku("", device=device, img=image)
    if text and not is_low_quality(text):
        return text, "yomitoku"

    # 2. PaddleOCR
    result = ocr_paddleocr(image)
    if result.success and result.text and not is_low_quality(result.text):
        return result.text, "paddleocr"

    # 3. Tesseract
    result = ocr_tesseract(image)
    if result.success and result.text:
        return result.text, "tesseract"

    return "", "none"
```

### 5. mask_figures() 関数 (src/utils.py)

```python
def mask_figures(img: Image.Image, regions: list[dict]) -> Image.Image:
    """FIGURE領域のみを白でマスク。"""
    masked = img.copy()
    draw = ImageDraw.Draw(masked)
    for r in regions:
        if r.get("type") == "FIGURE":
            x1, y1, x2, y2 = r["bbox"]
            draw.rectangle([x1, y1, x2, y2], fill="white")
    return masked
```

### 6. FIGURE除外

`ocr_by_layout()` で FIGURE領域をスキップするロジックを追加:

```python
# FIGUREはOCR結果から除外（figures/で別管理）
if region["type"] == "FIGURE":
    continue
```

### 7. 結果連結（読み順）

`ocr_by_layout()` で処理前にソートを適用:

```python
from src.reading_order import sort_reading_order, remove_overlaps

# ソート適用
regions = remove_overlaps(regions)
regions = sort_reading_order(regions, page_size[0])
```

## FAIL出力例

```
FAILED tests/test_layout_ocr.py::TestIsTitleFunction::test_is_title_yolo_title_type
tests/test_layout_ocr.py:1281: in test_is_title_yolo_title_type
    from src.layout_ocr import is_title
E   ImportError: cannot import name 'is_title' from 'src.layout_ocr'

FAILED tests/test_layout_ocr.py::TestFigureExclusion::test_ocr_by_layout_excludes_figure_from_output
tests/test_layout_ocr.py:1809: in test_ocr_by_layout_excludes_figure_from_output
    assert len(figure_results) == 0, (
E   AssertionError: FIGURE regions should be excluded from OCR output. Found: 1
```

## 次のステップ

1. GREEN Phaseで以下を実装:
   - `is_title()` in src/layout_ocr.py
   - `calc_non_char_ratio()` in src/layout_ocr.py
   - `is_low_quality()` in src/layout_ocr.py
   - `ocr_with_fallback()` in src/layout_ocr.py
   - `mask_figures()` in src/utils.py
   - `ocr_by_layout()` にFIGURE除外・読み順ソートを統合

2. `make test` で全テストがPASSすることを確認

## 関連ファイル

- テストファイル: `/data/projects/video-separater/tests/test_layout_ocr.py`
- 実装対象: `/data/projects/video-separater/src/layout_ocr.py`
- 実装対象: `/data/projects/video-separater/src/utils.py`
