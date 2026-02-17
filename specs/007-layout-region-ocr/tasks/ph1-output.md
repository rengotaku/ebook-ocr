# Phase 1 Output: Setup（既存コード分析）

**Date**: 2026-02-13
**Status**: Completed

## T001: src/detect_figures.py 分析

### 現在実装
- `LABEL_TYPE_MAP`: 全10クラス対応済み（title, plain text, abandon, figure, figure_caption, table, table_caption, table_footnote, isolated formula, formula_caption）
- `TARGET_LABELS`: LABEL_TYPE_MAP.keys() を使用（全クラス検出対象）
- 出力構造: `{"page_001.png": {"regions": [...], "page_size": [w, h]}}`
- `min_area` パラメータ: 実装済み（デフォルト 0.01 = 1%）

### 変更不要
- 10クラス検出: 実装済み
- regions構造: 実装済み
- page_size: 実装済み
- min_area フィルタリング: 実装済み

## T002: src/ocr_yomitoku.py 分析

### 現在実装
- `YomitokuResult` dataclass: text, markdown, paragraphs, tables, figures
- `ocr_page_yomitoku()`: 単一ページOCR（`img` パラメータでPIL Image対応）
- `ocr_page_yomitoku_full()`: フル結果（markdown含む）
- `_get_analyzer()`: lazy初期化

### roleフィールド
- `results.paragraphs[i]` に `contents` または `text` 属性
- **role フィールドは現在取得していない** → Phase 5 で追加必要

### 変更予定（Phase 5）
- role フィールド取得の追加（TITLE判定用）

## T003: src/ocr_ensemble.py 分析

### 現在実装
- 4エンジン対応: yomitoku, paddleocr, tesseract, easyocr
- `ocr_tesseract()`, `ocr_easyocr()`, `ocr_paddleocr()`, `ocr_yomitoku_engine()`
- `merge_by_voting()`: 投票によるマージ
- `ocr_ensemble()`: 複数エンジン実行

### フォールバック統合ポイント
- `ocr_paddleocr()`: PIL Image → numpy → PaddleOCR
- `ocr_tesseract()`: PIL Image → pytesseract

### 変更予定（Phase 5）
- `ocr_with_fallback()` 関数の追加（layout_ocr.py から呼び出し）

## T004: src/layout_ocr.py 分析

### 現在実装
- `OCRResult` dataclass: region_type, text, formatted
- `select_ocr_engine()`: FIGURE→vlm, ABANDON→skip, その他→yomitoku
- `format_ocr_result()`: Markdownフォーマット
- `crop_region()`: bbox→PIL crop
- `ocr_region()`: 単一領域OCR
- `calculate_coverage()`: カバー率計算
- `should_fallback()`: フォールバック判定
- `ocr_by_layout()`: ページ全体処理
- `run_layout_ocr()`: 全ページ処理

### 既存の領域別OCR構造
- Yomitoku: TEXT/TITLE/TABLE/CAPTION/FOOTNOTE/FORMULA
- VLM (gemma3:12b): FIGURE
- skip: ABANDON

### 変更予定（Phase 5）
- `is_title()`: YOLO + Yomitoku role 併用
- `is_low_quality()`: 品質判定（空/10文字未満/非文字率>50%）
- `calc_non_char_ratio()`: 非文字率計算
- `ocr_with_fallback()`: Yomitoku → PaddleOCR → Tesseract
- `mask_figures()` の呼び出し統合

## T005: src/reading_order.py 分析

### 現在実装
- `TYPE_PRIORITY`: TITLE(0) < TEXT(1) < CAPTION(2) < ...
- `sort_reading_order()`: 2カラム検出 + Y座標ソート
- `iou()`: 重複率計算（intersection / min_area）
- `remove_overlaps()`: 同一タイプ、IoU>=0.5 で除去

### アルゴリズム
1. center_x < mid_x → 左カラム
2. 各カラム内: (Y座標, TYPE_PRIORITY, X座標) でソート
3. 左カラム + 右カラム で結合

### 変更不要
- 基本アルゴリズム実装済み

## T006: src/utils.py 分析

### 現在実装
- `encode_image_file()`: ファイル→base64
- `encode_pil_image()`: PIL→base64
- `format_figure_markers()`: 図マーカーフォーマット
- `mask_figure_regions()`: **figures キー使用**（旧構造）

### 変更予定（Phase 5）
- `mask_figures()`: **regions キー対応**、FIGURE領域のみ白塗り

## T007: tests/ 分析

### 既存テスト
- `test_detect_figures.py`: 10クラス検出、regions構造、page_size、min_area
- `test_layout_ocr.py`: OCRエンジン選択、フォーマット、crop、結果連結、フォールバック
- `test_reading_order.py`: ソート、2カラム、TITLE優先、重複除去

### テストパターン
- pytest + tmp_path fixture
- unittest.mock.patch でYOLO/OCRモック
- MagicMock でAPIレスポンスモック

### 変更予定（Phase 2-5）
- 追加テストは tasks.md に定義済み

## Summary

| ファイル | 状態 | Phase 2 変更 | Phase 3 変更 | Phase 4 変更 | Phase 5 変更 |
|---------|------|-------------|-------------|-------------|-------------|
| detect_figures.py | 完了 | なし | なし | なし | なし |
| ocr_yomitoku.py | 一部対応 | なし | なし | なし | role取得追加 |
| ocr_ensemble.py | 完了 | なし | なし | なし | 統合ポイントのみ |
| layout_ocr.py | 一部対応 | なし | なし | なし | 多数追加 |
| reading_order.py | 完了 | なし | なし | なし | なし |
| utils.py | 旧構造 | なし | なし | なし | mask_figures更新 |

## Conclusion

- **Phase 2 (US1)**: detect_figures.py は既に実装済み。テスト確認のみ。
- **Phase 3 (US3)**: reading_order.py は既に実装済み。テスト確認のみ。
- **Phase 4 (US4)**: layout_ocr.py のフォールバック機能は既に実装済み。テスト確認のみ。
- **Phase 5 (US2)**: 主要な変更が必要。TITLE判定、OCRフォールバック、FIGUREマスク、role取得。
