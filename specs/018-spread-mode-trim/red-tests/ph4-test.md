# Phase 4 RED Tests: パイプライン統合とプレビュー

**Date**: 2026-02-25
**Status**: RED (FAIL verified)
**User Story**: US3 - パイプライン統合とプレビュー

## Summary

| Item | Value |
|------|-------|
| テスト作成数 | 29 |
| FAIL 数 | 29 |
| テストファイル | tests/test_makefile_targets.py (新規), tests/preprocessing/test_split_spread.py (追加) |

## 失敗テスト一覧

### tests/test_makefile_targets.py (T051: preview-extract ターゲット)

| テストメソッド | 期待動作 |
|---------------|----------|
| test_preview_extract_target_exists_in_makefile | Makefile に preview-extract ターゲットが定義されている |
| test_preview_extract_requires_video_param | VIDEO パラメータ未指定時にエラー |
| test_preview_extract_accepts_limit_param | LIMIT パラメータを受け付ける |
| test_preview_extract_outputs_to_preview_frames | preview/ ディレクトリへ出力 |
| test_preview_extract_target_uses_hashdir | HASHDIR を使用する |

### tests/test_makefile_targets.py (T052: preview-trim ターゲット)

| テストメソッド | 期待動作 |
|---------------|----------|
| test_preview_trim_target_exists_in_makefile | Makefile に preview-trim ターゲットが定義されている |
| test_preview_trim_requires_hashdir | HASHDIR パラメータ未指定時にエラー |
| test_preview_trim_uses_spread_mode | SPREAD_MODE を渡す |
| test_preview_trim_uses_global_trim_params | global-trim パラメータを渡す |
| test_preview_trim_outputs_to_preview_trimmed | preview/trimmed/ へ出力 |
| test_preview_trim_does_not_extract_frames | フレーム抽出を呼ばない（独立動作） |

### tests/test_makefile_targets.py (T054: make run 統合)

| テストメソッド | 期待動作 |
|---------------|----------|
| test_run_target_includes_split_spreads | run ターゲットに split-spreads ステップが含まれる |
| test_split_spreads_runs_after_deduplicate | split-spreads は deduplicate の後に実行される |
| test_split_spreads_runs_before_detect_layout | split-spreads は detect-layout の前に実行される |
| test_run_pipeline_passes_spread_mode | SPREAD_MODE がパイプラインで渡される |
| test_run_target_step_numbering | split-spreads にステップラベルがある |

### tests/test_makefile_targets.py (エッジケース)

| テストメソッド | 期待動作 |
|---------------|----------|
| test_phony_targets_include_preview | .PHONY に preview-extract/preview-trim が含まれる |
| test_preview_extract_has_help_comment | preview-extract に help コメントがある |
| test_preview_trim_has_help_comment | preview-trim に help コメントがある |
| test_preview_trim_accepts_trim_override | trim パラメータが上書き可能 |

### tests/preprocessing/test_split_spread.py (T053: preview/ エラーハンドリング)

| テストメソッド | 期待動作 |
|---------------|----------|
| test_preview_dir_not_exists_raises_error | 存在しないディレクトリでエラー |
| test_preview_frames_empty_returns_empty_list | 空の frames/ で空リスト返却 |
| test_preview_frames_empty_prints_warning | 空の frames/ で警告メッセージ表示 |
| test_preview_trim_without_frames_error_message | frames/ 未作成時に preview-extract 実行の案内 |
| test_preview_trim_check_with_frames_present | フレーム存在時に正常動作 |
| test_preview_trim_check_with_empty_frames_dir | 空の frames/ で検証エラー |
| test_preview_trim_creates_trimmed_directory | trimmed/ ディレクトリ作成 |
| test_preview_trim_outputs_to_trimmed_dir | trimmed/ に出力ファイル生成 |
| test_preview_trim_does_not_modify_original_frames | 元フレームを変更しない |
| test_preview_trim_applies_global_trim | global-trim 適用の検証 |
| test_preview_trim_single_mode_no_split | single モードで分割しない |
| test_preview_trim_rerun_overwrites_previous | 再実行時に前回出力を上書き |
| test_preview_trim_with_none_trim_config | None trim_config でも動作 |
| test_preview_trim_with_default_trim_config | デフォルト TrimConfig で動作 |
| test_preview_trim_unicode_path | Unicode パスの処理 |
| test_preview_trim_large_batch | 20枚の大量バッチ処理 |

## 実装ヒント

- `preview-extract` / `preview-trim`: Makefile に新規ターゲット追加が必要
- `preview_trim()` / `preview_trim_check()`: src/cli/split_spreads.py に新規関数追加が必要
- `make run`: split-spreads ステップを deduplicate と detect-layout の間に追加
- `.PHONY`: preview-extract, preview-trim を追加
- preview/frames/ からフレームを読み、preview/trimmed/ に出力する処理フロー

## make test 出力 (抜粋)

```
FAILED tests/test_makefile_targets.py::TestPreviewExtractTarget::test_preview_extract_target_exists_in_makefile - AssertionError: preview-extract target not found in Makefile
FAILED tests/test_makefile_targets.py::TestPreviewTrimTarget::test_preview_trim_target_exists_in_makefile - AssertionError: preview-trim target not found in Makefile
FAILED tests/test_makefile_targets.py::TestMakeRunIntegration::test_run_target_includes_split_spreads - AssertionError: run target should include split-spreads step
FAILED tests/preprocessing/test_split_spread.py::TestPreviewEmptyErrorHandling::test_preview_trim_without_frames_error_message - ImportError: cannot import name 'preview_trim_check'
FAILED tests/preprocessing/test_split_spread.py::TestPreviewTrimProcessing::test_preview_trim_creates_trimmed_directory - ImportError: cannot import name 'preview_trim'
...
29 failed, 78 passed in 2.05s
```
