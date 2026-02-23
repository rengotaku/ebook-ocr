# Phase 2: テスト実装 (RED) 結果

**日時**: 2026-02-23
**フェーズ**: Phase 2 - User Story 1 (パイプライン全体の短時間検証)
**ステータス**: RED確認完了

## 概要

| 項目 | 値 |
|------|-----|
| フェーズ | Phase 2 (US1) |
| 作成テスト数 | 13テスト (4ファイル) |
| FAILテスト数 | 9 |
| PASSテスト数 | 4 (既存動作の後方互換性テスト) |
| 既存テストへの影響 | なし (1310 passed, 6 skipped) |

## テストファイル一覧

| ファイル | テスト数 | FAIL | PASS |
|----------|---------|------|------|
| tests/cli/test_deduplicate_limit.py | 4 | 3 | 1 |
| tests/cli/test_detect_layout_limit.py | 3 | 2 | 1 |
| tests/cli/test_run_ocr_limit.py | 3 | 2 | 1 |
| tests/cli/test_consolidate_limit.py | 3 | 2 | 1 |

## FAILテスト一覧

| テストファイル | テストメソッド | 期待する動作 |
|----------------|---------------|-------------|
| test_deduplicate_limit.py | test_help_shows_limit_option | --helpに--limitオプションが表示される |
| test_deduplicate_limit.py | test_limit_processes_only_n_files | --limit 3で最初の3ファイルのみ処理 |
| test_deduplicate_limit.py | test_limit_stderr_message | --limit指定時にstderrに処理数を表示 |
| test_detect_layout_limit.py | test_help_shows_limit_option | --helpに--limitオプションが表示される |
| test_detect_layout_limit.py | test_limit_processes_only_n_pages | --limit 3で最初の3ページのみ処理 |
| test_run_ocr_limit.py | test_help_shows_limit_option | --helpに--limitオプションが表示される |
| test_run_ocr_limit.py | test_limit_processes_only_n_pages | --limit 3で最初の3ページのみ処理 |
| test_consolidate_limit.py | test_help_shows_limit_option | --helpに--limitオプションが表示される |
| test_consolidate_limit.py | test_limit_processes_only_n_files | --limit 3で最初の3ファイルのみ処理 |

## PASSテスト一覧 (後方互換性確認)

| テストファイル | テストメソッド | 確認内容 |
|----------------|---------------|---------|
| test_deduplicate_limit.py | test_no_limit_processes_all_files | --limitなしで全ファイル処理 |
| test_detect_layout_limit.py | test_no_limit_processes_all_pages | --limitなしで全ページ処理 |
| test_run_ocr_limit.py | test_no_limit_processes_all_pages | --limitなしで全ページ処理 |
| test_consolidate_limit.py | test_no_limit_processes_all_files | --limitなしで全ファイル処理 |

## 実装ヒント

全CLIで同じパターンを適用:

1. **argparseに--limitオプションを追加**: `parser.add_argument("--limit", type=int, help="Process only first N files")`
2. **基盤関数にlimitパラメータを追加**: `def func(..., *, limit=None)`
3. **ファイルリストをスライス**: `if limit: files = files[:limit]`
4. **stderrにメッセージ出力**: `print(f"Processing first {limit} of {len(files)} files", file=sys.stderr)`

## FAIL出力例

```
FAILED tests/cli/test_deduplicate_limit.py::TestDeduplicateLimitOption::test_help_shows_limit_option
  AssertionError: assert '--limit' in 'usage: deduplicate.py [-h] -o OUTPUT [-t THRESHOLD] input_dir...'

FAILED tests/cli/test_deduplicate_limit.py::TestDeduplicateLimitOption::test_limit_processes_only_n_files
  AssertionError: assert 2 == 0 (returncode)
  stderr: 'deduplicate.py: error: unrecognized arguments: --limit 3'

FAILED tests/cli/test_run_ocr_limit.py::TestRunOcrLimitOption::test_help_shows_limit_option
  AssertionError: assert '--limit' in 'usage: run_ocr.py [-h] -o OUTPUT [--layout-dir LAYOUT_DIR]...'
```

全FAILの原因: 各CLIにまだ`--limit`オプションが実装されていないため、argparseが`unrecognized arguments`エラーを返す。
