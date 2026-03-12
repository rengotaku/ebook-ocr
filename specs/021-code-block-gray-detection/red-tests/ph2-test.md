# Phase 2 RED Tests: US1 灰色背景コードブロックの自動検出

**Date**: 2026-03-13
**Status**: RED (FAIL verified)
**User Story**: US1 - 灰色背景コードブロックの自動検出

## Summary

| Item | Value |
|------|-------|
| テスト作成数 | 35 |
| 失敗数 | 31 |
| 成功数 | 4 (後方互換性・既存動作の確認テスト) |
| テストファイル | tests/test_code_detector.py (新規), tests/test_layout_ocr.py (追加) |

## 失敗テスト一覧

| テストファイル | テストメソッド | 期待する動作 | 失敗理由 |
|---------------|--------------|-------------|---------|
| test_code_detector.py | TestDetectGrayBackgroundBasic::test_gray_image_returns_true | 灰色画像 -> True | ModuleNotFoundError: src.layout.code_detector |
| test_code_detector.py | TestDetectGrayBackgroundBasic::test_white_image_returns_false | 白画像 -> False | ModuleNotFoundError |
| test_code_detector.py | TestDetectGrayBackgroundBasic::test_black_image_returns_false | 黒画像 -> False | ModuleNotFoundError |
| test_code_detector.py | TestDetectGrayBackgroundBasic::test_light_gray_image_returns_true | 薄灰色画像 -> True | ModuleNotFoundError |
| test_code_detector.py | TestDetectGrayBackgroundBasic::test_dark_gray_image_returns_true | 暗灰色画像 -> True | ModuleNotFoundError |
| test_code_detector.py | TestDetectGrayBackgroundBasic::test_colored_image_returns_false | 有色画像 -> False | ModuleNotFoundError |
| test_code_detector.py | TestDetectGrayBackgroundThreshold::test_gray_ratio_above_threshold_returns_true | 80%灰色 > 0.7閾値 -> True | ModuleNotFoundError |
| test_code_detector.py | TestDetectGrayBackgroundThreshold::test_gray_ratio_below_threshold_returns_false | 50%灰色 < 0.7閾値 -> False | ModuleNotFoundError |
| test_code_detector.py | TestDetectGrayBackgroundThreshold::test_gray_ratio_at_threshold_boundary | 70%灰色 = 0.7閾値 -> bool | ModuleNotFoundError |
| test_code_detector.py | TestDetectGrayBackgroundThreshold::test_custom_threshold_low | 0.3閾値で50%灰色 -> True | ModuleNotFoundError |
| test_code_detector.py | TestDetectGrayBackgroundThreshold::test_custom_threshold_high | 0.95閾値で80%灰色 -> False | ModuleNotFoundError |
| test_code_detector.py | TestDetectGrayBackgroundValidation::test_none_image_returns_false | None画像 -> False | ModuleNotFoundError |
| test_code_detector.py | TestDetectGrayBackgroundValidation::test_empty_bbox_returns_false | 空bbox -> False | ModuleNotFoundError |
| test_code_detector.py | TestDetectGrayBackgroundValidation::test_zero_size_bbox_returns_false | ゼロサイズbbox -> False | ModuleNotFoundError |
| test_code_detector.py | TestDetectGrayBackgroundValidation::test_negative_bbox_returns_false | 負座標bbox -> False | ModuleNotFoundError |
| test_code_detector.py | TestDetectGrayBackgroundValidation::test_bbox_exceeding_image_size_returns_result | 画像外bbox -> クリップして検出 | ModuleNotFoundError |
| test_code_detector.py | TestDetectGrayBackgroundValidation::test_inverted_bbox_returns_false | 反転bbox -> False | ModuleNotFoundError |
| test_code_detector.py | TestAspectRatioFilter::test_wide_strip_gray_region_stays_text | アスペクト比>8 灰色 -> TEXT維持 | TypeError: cv_img 引数なし |
| test_code_detector.py | TestAspectRatioFilter::test_normal_aspect_ratio_gray_region_becomes_code | 通常アスペクト比 灰色 -> CODE | TypeError: cv_img 引数なし |
| test_code_detector.py | TestParagraphsToLayoutIntegration::test_gray_text_becomes_code_with_cv_img | cv_img付き灰色TEXT -> CODE | TypeError: cv_img 引数なし |
| test_code_detector.py | TestParagraphsToLayoutIntegration::test_white_text_stays_text_with_cv_img | cv_img付き白TEXT -> TEXT維持 | TypeError: cv_img 引数なし |
| test_code_detector.py | TestParagraphsToLayoutIntegration::test_title_not_converted_to_code | TITLE灰色背景 -> TITLE維持 | TypeError: cv_img 引数なし |
| test_code_detector.py | TestParagraphsToLayoutIntegration::test_code_region_has_correct_bbox | CODE bbox座標保持 | TypeError: cv_img 引数なし |
| test_code_detector.py | TestParagraphsToLayoutIntegration::test_multiple_paragraphs_mixed_background | 灰色->CODE, 白->TEXT混在 | TypeError: cv_img 引数なし |
| test_code_detector.py | TestParagraphsToLayoutBackwardCompat::test_cv_img_none_explicit | cv_img=None明示 -> TEXT維持 | TypeError: cv_img 引数なし |
| test_layout_ocr.py | TestFormatOcrResultCode::test_code_region_wrapped_in_code_fence | CODE -> コードフェンス囲み | 現在はテキストそのまま返却 |
| test_layout_ocr.py | TestFormatOcrResultCode::test_code_region_format_structure | CODE -> ```\n{text}\n``` | 現在はテキストそのまま返却 |
| test_layout_ocr.py | TestFormatOcrResultCode::test_code_region_multiline | 複数行コード -> フェンス囲み | 現在はテキストそのまま返却 |
| test_layout_ocr.py | TestFormatOcrResultCode::test_code_region_empty_text | 空テキストCODE -> ```\n\n``` | 現在は空文字返却 |
| test_layout_ocr.py | TestFormatOcrResultCode::test_code_region_special_chars | 特殊文字 -> フェンス内保持 | 現在はテキストそのまま返却 |
| test_layout_ocr.py | TestFormatOcrResultCode::test_code_region_unicode | Unicode -> フェンス内保持 | 現在はテキストそのまま返却 |

## 成功テスト (後方互換性確認)

| テストファイル | テストメソッド | 説明 |
|---------------|--------------|------|
| test_code_detector.py | TestParagraphsToLayoutBackwardCompat::test_no_cv_img_text_stays_text | 既存3引数シグネチャが動作 |
| test_code_detector.py | TestParagraphsToLayoutBackwardCompat::test_existing_signature_still_works | TITLEが正しく検出 |
| test_layout_ocr.py | TestSelectOcrEngineCode::test_code_region_uses_yomitoku | 既存else分岐で"yomitoku"返却 |
| test_layout_ocr.py | TestSelectOcrEngineCode::test_code_engine_not_skip | 既存else分岐で"skip"でない |

## 実装ヒント

- `src/layout/code_detector.py` (新規ファイル):
  - `detect_gray_background(cv_img, bbox, threshold=0.7)`: HSV色空間で灰色画素比率を計算。彩度(S)<30、明度(V)50-200の条件。bbox クリップ + ゼロサイズチェック + None/空入力ガード
  - feat/022 ブランチの実装を設計参考として使用

- `src/layout/detector.py` (既存ファイル変更):
  - `paragraphs_to_layout()`: `cv_img=None` キーワード引数追加。TEXT リージョンで灰色チェック。アスペクト比 > 8.0 フィルタ。CODE判定時に `type="CODE"`, `label="code"` 設定

- `src/layout_ocr_utils.py` (既存ファイル変更):
  - `format_ocr_result()`: `"CODE"` 分岐追加 -> `` ```\n{text}\n``` ``
  - `select_ocr_engine()`: `"CODE"` 分岐の明示的追加（現在はelse分岐で動作するが明示化推奨）

- エッジケース:
  - None画像、空/ゼロサイズ/負/反転/画像外bbox -> False返却
  - アスペクト比 > 8.0 の帯状リージョン -> CODE判定しない
  - TITLE (section_headings) -> CODE判定スキップ

## make test 出力 (抜粋)

```
FAILED tests/test_code_detector.py::TestDetectGrayBackgroundBasic::test_gray_image_returns_true - ModuleNotFoundError: No module named 'src.layout.code_detector'
FAILED tests/test_code_detector.py::TestAspectRatioFilter::test_wide_strip_gray_region_stays_text - TypeError: paragraphs_to_layout() got an unexpected keyword argument 'cv_img'
FAILED tests/test_code_detector.py::TestParagraphsToLayoutIntegration::test_gray_text_becomes_code_with_cv_img - TypeError: paragraphs_to_layout() got an unexpected keyword argument 'cv_img'
FAILED tests/test_layout_ocr.py::TestFormatOcrResultCode::test_code_region_format_structure - AssertionError: Expected '```\nprint('hello')\n```', got 'print('hello')'
FAILED tests/test_layout_ocr.py::TestFormatOcrResultCode::test_code_region_empty_text - AssertionError: assert '' == '```\n\n```'
=== 31 failed, 1563 passed, 2 skipped, 131 deselected, 6 warnings in 28.46s ===
```
