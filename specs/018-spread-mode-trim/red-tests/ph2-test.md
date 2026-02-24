# Phase 2 RED Tests: Spread モード明示指定

**Date**: 2026-02-24
**Status**: RED (FAIL verified)
**User Story**: US1 - Spread モードの明示指定

## サマリ

| 項目 | 値 |
|------|-----|
| 作成テスト数 | 32 |
| FAIL 数 | 32 (ImportError によりコレクション段階で全て失敗) |
| テストファイル | tests/preprocessing/test_split_spread.py |

## テストクラス構成

| クラス | テスト数 | 対象タスク | 概要 |
|--------|----------|------------|------|
| TestModeSingle | 4 | T008 | mode=single でコピーのみ、分割なし |
| TestModeSpread | 5 | T009 | mode=spread で全画像を常に分割 |
| TestDefaultMode | 3 | T010 | デフォルトモードが single であること |
| TestEnvironmentVariable | 6 | T011 | 環境変数 SPREAD_MODE の読み込み |
| TestCLIPriority | 4 | T012 | CLI 引数が環境変数より優先 |
| TestModeDisplay | 3 | T013 | stdout にモード表示 |
| TestSpreadModeEdgeCases | 7 | - | エッジケース (enum 値、無効値、空ディレクトリ、モード変更) |

## 失敗テスト一覧

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|----------|
| test_split_spread.py | TestModeSingle::test_single_mode_does_not_split_wide_image | mode=single で横長画像を分割しない |
| test_split_spread.py | TestModeSingle::test_single_mode_preserves_tall_image | mode=single で縦長画像をそのまま保持 |
| test_split_spread.py | TestModeSingle::test_single_mode_preserves_image_dimensions | mode=single で画像サイズ不変 |
| test_split_spread.py | TestModeSingle::test_single_mode_with_multiple_images | mode=single で複数画像全てコピーのみ |
| test_split_spread.py | TestModeSpread::test_spread_mode_splits_wide_image | mode=spread で L/R ファイル生成 |
| test_split_spread.py | TestModeSpread::test_spread_mode_splits_tall_image | mode=spread で縦長画像も分割 |
| test_split_spread.py | TestModeSpread::test_spread_mode_creates_correct_dimensions | 分割後のサイズが元の半分 |
| test_split_spread.py | TestModeSpread::test_spread_mode_splits_all_images | mode=spread で全画像分割 (2->4) |
| test_split_spread.py | TestModeSpread::test_spread_mode_with_trim | mode=spread + trim 適用 |
| test_split_spread.py | TestDefaultMode::test_default_mode_is_single | SpreadMode enum 値の確認 |
| test_split_spread.py | TestDefaultMode::test_get_spread_mode_default | get_spread_mode(None) -> SINGLE |
| test_split_spread.py | TestDefaultMode::test_split_spread_pages_default_mode_no_split | mode 未指定で分割なし |
| test_split_spread.py | TestEnvironmentVariable::test_env_var_spread | SPREAD_MODE=spread の読み込み |
| test_split_spread.py | TestEnvironmentVariable::test_env_var_single | SPREAD_MODE=single の読み込み |
| test_split_spread.py | TestEnvironmentVariable::test_env_var_not_set_uses_default | 環境変数なしでデフォルト |
| test_split_spread.py | TestEnvironmentVariable::test_env_var_invalid_value | 無効値で ValueError |
| test_split_spread.py | TestEnvironmentVariable::test_env_var_case_insensitive | 大文字小文字の区別なし |
| test_split_spread.py | TestEnvironmentVariable::test_env_var_with_whitespace | 前後空白のトリミング |
| test_split_spread.py | TestCLIPriority::test_cli_overrides_env_var | CLI single > ENV spread |
| test_split_spread.py | TestCLIPriority::test_cli_spread_overrides_env_single | CLI spread > ENV single |
| test_split_spread.py | TestCLIPriority::test_cli_none_falls_to_env | CLI None -> ENV 参照 |
| test_split_spread.py | TestCLIPriority::test_cli_invalid_value_raises | 無効 CLI 値で ValueError |
| test_split_spread.py | TestModeDisplay::test_single_mode_displayed | "Mode: single" 表示 |
| test_split_spread.py | TestModeDisplay::test_spread_mode_displayed | "Mode: spread" 表示 |
| test_split_spread.py | TestModeDisplay::test_mode_displayed_before_processing | モード表示が最初の行 |
| test_split_spread.py | TestSpreadModeEdgeCases::test_spread_mode_enum_values | enum 値が 2 つ |
| test_split_spread.py | TestSpreadModeEdgeCases::test_spread_mode_from_string_single | 文字列から enum 生成 |
| test_split_spread.py | TestSpreadModeEdgeCases::test_spread_mode_from_string_spread | 文字列から enum 生成 |
| test_split_spread.py | TestSpreadModeEdgeCases::test_spread_mode_invalid_string | 無効文字列で ValueError |
| test_split_spread.py | TestSpreadModeEdgeCases::test_empty_directory_with_mode | 空ディレクトリで空リスト |
| test_split_spread.py | TestSpreadModeEdgeCases::test_mode_none_uses_default | None -> SINGLE |
| test_split_spread.py | TestSpreadModeEdgeCases::test_iterative_run_with_mode_change | モード変更の繰り返し実行 |

## 実装ヒント

- `SpreadMode`: `enum.Enum` で `SINGLE = "single"`, `SPREAD = "spread"` の 2 値を定義
- `get_spread_mode(cli_mode: str | None) -> SpreadMode`: CLI 引数 > 環境変数 `SPREAD_MODE` > デフォルト `SINGLE` の優先順位
- `split_spread_pages()`: `mode` 引数を追加。`mode=SINGLE` 時は `is_spread_image()` を呼ばず常にコピー、`mode=SPREAD` 時は常に `split_spread()` を呼ぶ
- `mode=None` 時は `get_spread_mode()` でデフォルト値を取得
- 処理開始時に `print(f"Mode: {mode.value}")` で標準出力に表示
- エッジケース: 環境変数の大文字小文字、前後空白、無効値のハンドリング

## make test 出力 (抜粋)

```
ERRORS
__________ ERROR collecting tests/preprocessing/test_split_spread.py ___________
ImportError while importing test module 'tests/preprocessing/test_split_spread.py'.
tests/preprocessing/test_split_spread.py:18: in <module>
    from src.preprocessing.split_spread import (
E   ImportError: cannot import name 'SpreadMode' from 'src.preprocessing.split_spread'
=========================== short test summary info ============================
ERROR tests/preprocessing/test_split_spread.py
1 error in 0.36s
```

## 既存テストへの影響

- 既存テスト (`tests/test_split_spread.py`): 20 テスト全て PASS (影響なし)
- 新規テストは別ディレクトリ (`tests/preprocessing/`) に配置
