# Phase 6 RED Tests: CLI 統合

**Date**: 2026-03-03
**Status**: RED (FAIL verified)
**User Story**: CLI統合 - normalize_headings CLI エントリポイント

## Summary

| Item | Value |
|------|-------|
| Tests Created | 22 |
| Failed Count | 22 |
| Test Files | tests/cli/test_normalize_headings.py |

## Failed Tests

| Test File | Test Method | Expected Behavior |
|-----------|-------------|-------------------|
| tests/cli/test_normalize_headings.py | test_report_command_success | report サブコマンドが見出しパターンレポートを正常出力 |
| tests/cli/test_normalize_headings.py | test_report_command_file_not_found | 存在しないファイルでユーザーフレンドリーなエラー表示 |
| tests/cli/test_normalize_headings.py | test_report_command_empty_file | 空ファイルで正常終了、見出し数0を表示 |
| tests/cli/test_normalize_headings.py | test_report_command_shows_numbered_pattern | 番号付きパターン情報がレポートに含まれる |
| tests/cli/test_normalize_headings.py | test_normalize_command_dryrun | デフォルトで dry-run、ファイル変更なし |
| tests/cli/test_normalize_headings.py | test_normalize_command_apply | --apply でファイルを実際に変更 |
| tests/cli/test_normalize_headings.py | test_normalize_command_with_threshold | --threshold オプションが受付可能 |
| tests/cli/test_normalize_headings.py | test_normalize_command_file_not_found | 存在しないファイルでユーザーフレンドリーなエラー表示 |
| tests/cli/test_normalize_headings.py | test_normalize_command_dryrun_shows_preview | dry-run で変更プレビューを出力 |
| tests/cli/test_normalize_headings.py | test_validate_command_success | validate サブコマンドが検証レポートを出力 |
| tests/cli/test_normalize_headings.py | test_validate_command_warn_exit_code | MISSING があっても exit code 0 |
| tests/cli/test_normalize_headings.py | test_validate_command_file_not_found | 存在しないファイルでユーザーフレンドリーなエラー表示 |
| tests/cli/test_normalize_headings.py | test_validate_command_shows_match_details | マッチ詳細テーブルが含まれる |
| tests/cli/test_normalize_headings.py | test_validate_command_shows_excluded | Excluded セクションに特殊マーカー見出し表示 |
| tests/cli/test_normalize_headings.py | test_validate_command_with_threshold | --threshold オプションが受付可能 |
| tests/cli/test_normalize_headings.py | test_no_subcommand_shows_help | サブコマンドなしで argparse ヘルプ表示 |
| tests/cli/test_normalize_headings.py | test_help_flag | --help で report/normalize/validate 表示 |
| tests/cli/test_normalize_headings.py | test_report_help_flag | report --help でサブコマンドヘルプ表示 |
| tests/cli/test_normalize_headings.py | test_normalize_help_flag | normalize --help で --apply/--threshold 表示 |
| tests/cli/test_normalize_headings.py | test_validate_help_flag | validate --help でサブコマンドヘルプ表示 |
| tests/cli/test_normalize_headings.py | test_invalid_subcommand | 無効サブコマンドで argparse エラー表示 |
| tests/cli/test_normalize_headings.py | test_module_runnable | python -m src.cli.normalize_headings で実行可能 |

## Implementation Hints

- `main()`: argparse でサブコマンド (report, normalize, validate) を定義
  - `report`: extract_headings() + classify_heading_patterns() でレポート出力
  - `normalize`: match_toc_to_body() + generate_rules() + preview_diff()/apply_rules() で正規化
  - `validate`: match_toc_to_body() + generate_validation_report() + format_validation_report() で検証
- `--apply` フラグ: normalize サブコマンドのみ
- `--threshold` オプション: normalize/validate 両方で使用
- ファイル存在チェック: argparse の type か、手動で Path.exists() チェック
- エラーハンドリング: NotImplementedError ではなく、ユーザーフレンドリーなメッセージで sys.exit(1)

### 利用可能な既存 API

- `extract_headings()`, `classify_heading_patterns()`: heading_normalizer.py
- `match_toc_to_body()`, `find_similar_candidate()`, `generate_validation_report()`, `format_validation_report()`: heading_matcher.py
- `generate_rules()`, `preview_diff()`, `apply_rules()`: normalization_rules.py
- `parse_toc_lines()`, `parse_toc_entry()`: parser/toc.py

## make test Output (excerpt)

```
FAILED tests/cli/test_normalize_headings.py::TestReportCommand::test_report_command_success - AssertionError
FAILED tests/cli/test_normalize_headings.py::TestReportCommand::test_report_command_file_not_found - AssertionError
FAILED tests/cli/test_normalize_headings.py::TestReportCommand::test_report_command_empty_file - AssertionError
FAILED tests/cli/test_normalize_headings.py::TestReportCommand::test_report_command_shows_numbered_pattern - AssertionError
FAILED tests/cli/test_normalize_headings.py::TestNormalizeCommand::test_normalize_command_dryrun - AssertionError
FAILED tests/cli/test_normalize_headings.py::TestNormalizeCommand::test_normalize_command_apply - AssertionError
FAILED tests/cli/test_normalize_headings.py::TestNormalizeCommand::test_normalize_command_with_threshold - AssertionError
FAILED tests/cli/test_normalize_headings.py::TestNormalizeCommand::test_normalize_command_file_not_found - AssertionError
FAILED tests/cli/test_normalize_headings.py::TestNormalizeCommand::test_normalize_command_dryrun_shows_preview - AssertionError
FAILED tests/cli/test_normalize_headings.py::TestValidateCommand::test_validate_command_success - AssertionError
FAILED tests/cli/test_normalize_headings.py::TestValidateCommand::test_validate_command_warn_exit_code - AssertionError
FAILED tests/cli/test_normalize_headings.py::TestValidateCommand::test_validate_command_file_not_found - AssertionError
FAILED tests/cli/test_normalize_headings.py::TestValidateCommand::test_validate_command_shows_match_details - AssertionError
FAILED tests/cli/test_normalize_headings.py::TestValidateCommand::test_validate_command_shows_excluded - AssertionError
FAILED tests/cli/test_normalize_headings.py::TestValidateCommand::test_validate_command_with_threshold - AssertionError
FAILED tests/cli/test_normalize_headings.py::TestCLICommon::test_no_subcommand_shows_help - AssertionError
FAILED tests/cli/test_normalize_headings.py::TestCLICommon::test_help_flag - AssertionError
FAILED tests/cli/test_normalize_headings.py::TestCLICommon::test_report_help_flag - AssertionError
FAILED tests/cli/test_normalize_headings.py::TestCLICommon::test_normalize_help_flag - AssertionError
FAILED tests/cli/test_normalize_headings.py::TestCLICommon::test_validate_help_flag - AssertionError
FAILED tests/cli/test_normalize_headings.py::TestCLICommon::test_invalid_subcommand - AssertionError
FAILED tests/cli/test_normalize_headings.py::TestCLICommon::test_module_runnable - AssertionError
22 failed in 3.11s
```

## 既存テストへの影響

既存テスト 1633 passed, 6 skipped -- リグレッションなし。
