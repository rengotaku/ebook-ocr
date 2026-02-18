# Phase 2 Test Implementation (RED)

**Date**: 2026-02-18
**Feature**: 010-pipeline-refactoring
**Phase**: Phase 2 - User Story 1 (CLIスクリプト分解)

## Summary

| 項目 | 値 |
|------|-----|
| Phase | 2 |
| FAILテスト数 | 31 |
| PASSテスト数 | 37 |
| 合計テスト数 | 68 |
| RED状態 | 確認済み |

## テストファイル一覧

| ファイル | テスト数 | 状態 |
|----------|----------|------|
| `tests/cli/__init__.py` | - | 作成済み |
| `tests/cli/test_extract_frames.py` | 6 | FAIL |
| `tests/cli/test_deduplicate.py` | 7 | FAIL |
| `tests/cli/test_split_spreads.py` | 6 | FAIL |
| `tests/cli/test_detect_layout.py` | 6 | FAIL |
| `tests/cli/test_run_ocr.py` | 7 | FAIL |
| `tests/cli/test_consolidate.py` | 6 | FAIL |
| `tests/cli/test_error_handling.py` | 30 | 一部FAIL |

## FAILテスト一覧

### test_extract_frames.py

| テストメソッド | 期待動作 |
|----------------|----------|
| `test_module_runnable` | `python -m src.cli.extract_frames --help` が成功 |
| `test_help_shows_required_args` | helpに VIDEO, -o/--output が表示 |
| `test_help_shows_interval_option` | helpに -i/--interval が表示 |
| `test_missing_input_shows_error` | 存在しない入力で exit code 1, stderr に error |
| `test_requires_output_arg` | -o 必須 |
| `test_missing_positional_arg_shows_usage` | 引数なしで usage 表示 |

### test_deduplicate.py

| テストメソッド | 期待動作 |
|----------------|----------|
| `test_module_runnable` | `python -m src.cli.deduplicate --help` が成功 |
| `test_help_shows_required_args` | helpに INPUT, -o/--output が表示 |
| `test_help_shows_threshold_option` | helpに -t/--threshold が表示 |
| `test_missing_input_shows_error` | 存在しないディレクトリで exit code 1 |
| `test_empty_input_dir_shows_error` | 空ディレクトリで exit code 1 |
| `test_requires_output_arg` | -o 必須 |
| `test_missing_positional_arg_shows_usage` | 引数なしで usage 表示 |

### test_split_spreads.py

| テストメソッド | 期待動作 |
|----------------|----------|
| `test_module_runnable` | `python -m src.cli.split_spreads --help` が成功 |
| `test_help_shows_required_args` | helpに PAGES_DIR が表示 |
| `test_help_shows_aspect_ratio_option` | helpに --aspect-ratio が表示 |
| `test_help_shows_trim_options` | helpに --left-trim, --right-trim が表示 |
| `test_missing_input_shows_error` | 存在しないディレクトリで exit code 1 |
| `test_missing_positional_arg_shows_usage` | 引数なしで usage 表示 |

### test_detect_layout.py

| テストメソッド | 期待動作 |
|----------------|----------|
| `test_module_runnable` | `python -m src.cli.detect_layout --help` が成功 |
| `test_help_shows_required_args` | helpに PAGES, -o/--output が表示 |
| `test_help_shows_device_option` | helpに --device が表示 |
| `test_missing_input_shows_error` | 存在しないディレクトリで exit code 1 |
| `test_requires_output_arg` | -o 必須 |
| `test_missing_positional_arg_shows_usage` | 引数なしで usage 表示 |

### test_run_ocr.py

| テストメソッド | 期待動作 |
|----------------|----------|
| `test_module_runnable` | `python -m src.cli.run_ocr --help` が成功 |
| `test_help_shows_required_args` | helpに PAGES, -o/--output が表示 |
| `test_help_shows_layout_dir_option` | helpに --layout-dir が表示 |
| `test_help_shows_device_option` | helpに --device が表示 |
| `test_missing_input_shows_error` | 存在しないディレクトリで exit code 1 |
| `test_requires_output_arg` | -o 必須 |
| `test_missing_positional_arg_shows_usage` | 引数なしで usage 表示 |

### test_consolidate.py

| テストメソッド | 期待動作 |
|----------------|----------|
| `test_module_runnable` | `python -m src.cli.consolidate --help` が成功 |
| `test_help_shows_required_args` | helpに OCR, -o/--output が表示 |
| `test_missing_input_shows_error` | 存在しないディレクトリで exit code 1 |
| `test_empty_input_dir_shows_error` | 空ディレクトリで exit code 1 |
| `test_requires_output_arg` | -o 必須 |
| `test_missing_positional_arg_shows_usage` | 引数なしで usage 表示 |

### test_error_handling.py

| テストメソッド | 期待動作 |
|----------------|----------|
| `test_all_cli_modules_support_help[*]` | 全6 CLIで --help が成功 (6テスト) |
| `test_nonexistent_input_returns_exit_code_1[*]` | 全CLIで存在しない入力時 exit code 1 (6テスト) |
| `test_nonexistent_input_shows_error_message[*]` | 全CLIで error メッセージ出力 (6テスト) |
| `test_all_cli_modules_show_error_without_args[*]` | 引数なしで失敗 (6テスト) |
| `test_*_exit_code_1_for_missing_input` | 各CLIの exit code 1 確認 (6テスト) |

## 実装ヒント

### CLI共通構造

```python
"""CLI command template."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="...")
    parser.add_argument("input", type=Path, help="入力パス")
    parser.add_argument("-o", "--output", type=Path, required=True, help="出力パス")
    # 追加オプション

    args = parser.parse_args()

    if not args.input.exists():
        print(f"Error: Input not found: {args.input}", file=sys.stderr)
        return 1

    # 処理実行
    return 0


if __name__ == "__main__":
    sys.exit(main())
```

### 必要なファイル

```
src/
└── cli/
    ├── __init__.py
    ├── extract_frames.py
    ├── deduplicate.py
    ├── split_spreads.py
    ├── detect_layout.py
    ├── run_ocr.py
    └── consolidate.py
```

## FAIL出力例

```
FAILED tests/cli/test_extract_frames.py::TestExtractFramesCLI::test_module_runnable
    ModuleNotFoundError: No module named 'src.cli'

FAILED tests/cli/test_deduplicate.py::TestDeduplicateCLI::test_module_runnable
    ModuleNotFoundError: No module named 'src.cli'

... (同様のエラーが全31テストで発生)

======================== 31 failed, 37 passed in 1.36s =========================
```

## 次のステップ

1. `src/cli/__init__.py` を作成
2. 各CLIスクリプト (`src/cli/*.py`) を実装
3. `make test` で全テストPASS (GREEN) を確認

## CLI契約参照

詳細は `/specs/010-pipeline-refactoring/contracts/cli-commands.md` を参照。
