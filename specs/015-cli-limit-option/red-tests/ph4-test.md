# Phase 4: Test Implementation (RED) - バリデーションエラーテスト

**日時**: 2026-02-23
**フェーズ**: Phase 4 - User Story 3 (エラーハンドリング)
**ステータス**: RED (5 FAILED, 7 PASSED)

## サマリ

| 項目 | 値 |
|------|-----|
| フェーズ | Phase 4 (US3) |
| FAILテスト数 | 5 |
| PASSテスト数 | 7 (argparse組込み + 偶発的エラーパス) |
| テストファイル | tests/cli/test_limit_validation.py |

## FAILテスト一覧

| テストファイル | テストメソッド | 期待する動作 |
|---------------|---------------|-------------|
| test_limit_validation.py | test_limit_zero_returns_error[src.cli.detect_layout] | --limit 0 で非ゼロ終了コード |
| test_limit_validation.py | test_limit_zero_returns_error[src.cli.run_ocr] | --limit 0 で非ゼロ終了コード |
| test_limit_validation.py | test_limit_zero_returns_error[src.cli.consolidate] | --limit 0 でエラーメッセージに"0"または"positive"を含む |
| test_limit_validation.py | test_limit_negative_returns_error[src.cli.detect_layout] | --limit -5 で非ゼロ終了コード |
| test_limit_validation.py | test_limit_negative_returns_error[src.cli.run_ocr] | --limit -5 で非ゼロ終了コード |

## PASSテストの理由 (実装不要)

| テストメソッド | PASS理由 |
|---------------|---------|
| test_limit_non_integer_argparse_error (全4 CLI) | argparseの`type=int`が自動で非整数を拒否 |
| test_limit_zero_returns_error[src.cli.deduplicate] | 空ディレクトリの"No frames found"チェックが偶発的にエラーを返す |
| test_limit_negative_returns_error[src.cli.deduplicate] | 同上 |
| test_limit_negative_returns_error[src.cli.consolidate] | "No OCR results found"チェックが偶発的にエラーを返す |

## 実装ヒント

各CLIのmain()関数に、argparse後・処理前にバリデーションを追加:

```python
if args.limit is not None and args.limit <= 0:
    parser.error("--limit must be a positive integer")
```

対象ファイル:
- src/cli/deduplicate.py (明示的バリデーション追加推奨 - 現在は偶発的にエラー)
- src/cli/detect_layout.py (バリデーションなし - FAIL)
- src/cli/run_ocr.py (バリデーションなし - FAIL)
- src/cli/consolidate.py (バリデーションなし - FAIL)

## FAIL出力例

```
FAILED tests/cli/test_limit_validation.py::TestLimitZeroReturnsError::test_limit_zero_returns_error[src.cli.detect_layout]
  AssertionError: [src.cli.detect_layout] --limit 0 should return non-zero exit code, got returncode=0

FAILED tests/cli/test_limit_validation.py::TestLimitZeroReturnsError::test_limit_zero_returns_error[src.cli.run_ocr]
  AssertionError: [src.cli.run_ocr] --limit 0 should return non-zero exit code, got returncode=0

FAILED tests/cli/test_limit_validation.py::TestLimitZeroReturnsError::test_limit_zero_returns_error[src.cli.consolidate]
  AssertionError: [src.cli.consolidate] Error output should mention the invalid value or 'positive'.

FAILED tests/cli/test_limit_validation.py::TestLimitNegativeReturnsError::test_limit_negative_returns_error[src.cli.detect_layout]
  AssertionError: [src.cli.detect_layout] --limit -5 should return non-zero exit code, got returncode=0

FAILED tests/cli/test_limit_validation.py::TestLimitNegativeReturnsError::test_limit_negative_returns_error[src.cli.run_ocr]
  AssertionError: [src.cli.run_ocr] --limit -5 should return non-zero exit code, got returncode=0
```

## make test 全体結果

```
5 failed, 1336 passed, 6 skipped in 121.64s (0:02:01)
```

既存テストへのリグレッションなし (1331 passed は従来通り)。
