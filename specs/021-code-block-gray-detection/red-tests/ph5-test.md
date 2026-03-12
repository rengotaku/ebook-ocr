# Phase 5 RED Tests: 可視化・出力・設定外部化

**Date**: 2026-03-13
**Status**: RED (FAIL verified)
**User Story**: US5 - CODE リージョンの可視化と出力 + 設定外部化

## サマリ

| 項目 | 値 |
|------|------|
| 作成テスト数 | 21 |
| 失敗数 | 21 |
| テストファイル | tests/test_code_detector.py |

## 失敗テスト一覧

### T073: visualize_layout() CODE 色分けテスト

| テストファイル | テストメソッド | 期待動作 |
|---------------|--------------|---------|
| tests/test_code_detector.py | TestVisualizeLayoutCodeColor::test_code_region_drawn_in_yellow | CODE リージョンが黄色(0,255,255)BGRで描画される |
| tests/test_code_detector.py | TestVisualizeLayoutCodeColor::test_text_region_not_drawn_in_yellow | TEXT リージョンは黄色で描画されない |
| tests/test_code_detector.py | TestVisualizeLayoutCodeColor::test_multiple_region_types_correct_colors | CODE=黄色、TEXT/FIGURE=各デフォルト色 |
| tests/test_code_detector.py | TestVisualizeLayoutCodeColor::test_empty_layout_regions | 空リージョンでエラーなし |
| tests/test_code_detector.py | TestVisualizeLayoutCodeColor::test_no_layout_regions_backward_compat | layout_regions なしで後方互換動作 (PASS) |

### T074: detect_layout_yomitoku() CODE 数サマリ出力テスト

| テストファイル | テストメソッド | 期待動作 |
|---------------|--------------|---------|
| tests/test_code_detector.py | TestCodeCountSummaryOutput::test_code_count_in_summary_output | サマリに [CODE: 3] が含まれる |
| tests/test_code_detector.py | TestCodeCountSummaryOutput::test_zero_code_count_in_summary | CODE がない場合 [CODE: 0] |
| tests/test_code_detector.py | TestCodeCountSummaryOutput::test_single_code_count | CODE 1個で [CODE: 1] |
| tests/test_code_detector.py | TestCodeCountSummaryOutput::test_summary_includes_total_regions | 合計リージョン数も含む |

### T075: 設定読み込みテスト

| テストファイル | テストメソッド | 期待動作 |
|---------------|--------------|---------|
| tests/test_code_detector.py | TestLoadCodeDetectionConfig::test_default_config_keys | 全8キーが存在する |
| tests/test_code_detector.py | TestLoadCodeDetectionConfig::test_default_gray_background_threshold | デフォルト値 0.7 |
| tests/test_code_detector.py | TestLoadCodeDetectionConfig::test_default_symbol_ratio_threshold | デフォルト値 0.08 |
| tests/test_code_detector.py | TestLoadCodeDetectionConfig::test_default_keyword_threshold | デフォルト値 2 |
| tests/test_code_detector.py | TestLoadCodeDetectionConfig::test_default_fragment_gap_threshold | デフォルト値 80 |
| tests/test_code_detector.py | TestLoadCodeDetectionConfig::test_default_aspect_ratio_max | デフォルト値 8.0 |
| tests/test_code_detector.py | TestLoadCodeDetectionConfig::test_default_gray_saturation_max | デフォルト値 30 |
| tests/test_code_detector.py | TestLoadCodeDetectionConfig::test_default_gray_value_range | デフォルト値 min=50, max=200 |
| tests/test_code_detector.py | TestLoadCodeDetectionConfig::test_custom_config_from_file | カスタム設定ファイルから読み込み |
| tests/test_code_detector.py | TestLoadCodeDetectionConfig::test_missing_config_section_returns_defaults | code_detection セクションなしでデフォルト返却 |
| tests/test_code_detector.py | TestLoadCodeDetectionConfig::test_partial_config_fills_missing_with_defaults | 部分設定で未指定キーはデフォルト |
| tests/test_code_detector.py | TestLoadCodeDetectionConfig::test_nonexistent_config_file_returns_defaults | 存在しないファイルでデフォルト返却 |
| tests/test_code_detector.py | TestLoadCodeDetectionConfig::test_config_values_are_correct_types | 型の正確性（float/int） |

## 実装ヒント

- `visualize_layout()`: `layout_regions=None` キーワード引数を追加。CODE リージョンは cv2.rectangle で黄色 (0, 255, 255) BGR で描画。既存の paragraphs/figures 描画はそのまま維持
- `_format_region_summary()`: 新規ヘルパー関数として `src/layout/detector.py` に追加。regions リストから CODE 数をカウントし `[CODE: N]` を含む文字列を返す
- `load_code_detection_config()`: `src/layout/code_detector.py` に追加。config.yaml の `code_detection` セクションを読み、未指定キーにはデフォルト値を適用。ファイルパス引数（オプション）でカスタム設定も対応
- エッジケース: 存在しないファイル、code_detection セクションなし、部分的な設定

## make test 出力（抜粋）

```
FAILED tests/test_code_detector.py::TestVisualizeLayoutCodeColor::test_code_region_drawn_in_yellow - TypeError: visualize_layout() got an unexpected keyword argument 'layout_regions'
FAILED tests/test_code_detector.py::TestVisualizeLayoutCodeColor::test_text_region_not_drawn_in_yellow - TypeError: visualize_layout() got an unexpected keyword argument 'layout_regions'
FAILED tests/test_code_detector.py::TestVisualizeLayoutCodeColor::test_multiple_region_types_correct_colors - TypeError: visualize_layout() got an unexpected keyword argument 'layout_regions'
FAILED tests/test_code_detector.py::TestVisualizeLayoutCodeColor::test_empty_layout_regions - TypeError: visualize_layout() got an unexpected keyword argument 'layout_regions'
FAILED tests/test_code_detector.py::TestCodeCountSummaryOutput::test_code_count_in_summary_output - ImportError: cannot import name '_format_region_summary' from 'src.layout.detector'
FAILED tests/test_code_detector.py::TestCodeCountSummaryOutput::test_zero_code_count_in_summary - ImportError: cannot import name '_format_region_summary' from 'src.layout.detector'
FAILED tests/test_code_detector.py::TestCodeCountSummaryOutput::test_single_code_count - ImportError: cannot import name '_format_region_summary' from 'src.layout.detector'
FAILED tests/test_code_detector.py::TestCodeCountSummaryOutput::test_summary_includes_total_regions - ImportError: cannot import name '_format_region_summary' from 'src.layout.detector'
FAILED tests/test_code_detector.py::TestLoadCodeDetectionConfig::test_default_config_keys - ImportError: cannot import name 'load_code_detection_config' from 'src.layout.code_detector'
FAILED tests/test_code_detector.py::TestLoadCodeDetectionConfig::test_default_gray_background_threshold - ImportError: cannot import name 'load_code_detection_config' from 'src.layout.code_detector'
FAILED tests/test_code_detector.py::TestLoadCodeDetectionConfig::test_default_symbol_ratio_threshold - ImportError: cannot import name 'load_code_detection_config' from 'src.layout.code_detector'
FAILED tests/test_code_detector.py::TestLoadCodeDetectionConfig::test_default_keyword_threshold - ImportError: cannot import name 'load_code_detection_config' from 'src.layout.code_detector'
FAILED tests/test_code_detector.py::TestLoadCodeDetectionConfig::test_default_fragment_gap_threshold - ImportError: cannot import name 'load_code_detection_config' from 'src.layout.code_detector'
FAILED tests/test_code_detector.py::TestLoadCodeDetectionConfig::test_default_aspect_ratio_max - ImportError: cannot import name 'load_code_detection_config' from 'src.layout.code_detector'
FAILED tests/test_code_detector.py::TestLoadCodeDetectionConfig::test_default_gray_saturation_max - ImportError: cannot import name 'load_code_detection_config' from 'src.layout.code_detector'
FAILED tests/test_code_detector.py::TestLoadCodeDetectionConfig::test_default_gray_value_range - ImportError: cannot import name 'load_code_detection_config' from 'src.layout.code_detector'
FAILED tests/test_code_detector.py::TestLoadCodeDetectionConfig::test_custom_config_from_file - ImportError: cannot import name 'load_code_detection_config' from 'src.layout.code_detector'
FAILED tests/test_code_detector.py::TestLoadCodeDetectionConfig::test_missing_config_section_returns_defaults - ImportError: cannot import name 'load_code_detection_config' from 'src.layout.code_detector'
FAILED tests/test_code_detector.py::TestLoadCodeDetectionConfig::test_partial_config_fills_missing_with_defaults - ImportError: cannot import name 'load_code_detection_config' from 'src.layout.code_detector'
FAILED tests/test_code_detector.py::TestLoadCodeDetectionConfig::test_nonexistent_config_file_returns_defaults - ImportError: cannot import name 'load_code_detection_config' from 'src.layout.code_detector'
FAILED tests/test_code_detector.py::TestLoadCodeDetectionConfig::test_config_values_are_correct_types - ImportError: cannot import name 'load_code_detection_config' from 'src.layout.code_detector'
21 failed, 1677 passed, 2 skipped, 131 deselected, 6 warnings in 35.66s
```
