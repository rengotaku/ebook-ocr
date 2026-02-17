# Phase 3 テスト実装 (RED) 出力

**日付**: 2026-02-18
**Feature**: 010-pipeline-refactoring
**Phase**: Phase 3 - User Story 2 (命名規則統一)

## Summary

| 項目 | 値 |
|------|-----|
| Phase | 3 |
| FAILテスト数 | 7 |
| PASSテスト数 | 3 |
| テストファイル | tests/test_naming_convention.py |
| 状態 | RED |

## FAILテスト一覧

| テストファイル | テストメソッド | 期待動作 | FAIL理由 |
|----------------|----------------|----------|----------|
| test_naming_convention.py | `TestYomitokuNamingInCLI::test_no_yomitoku_device_in_cli_args` | CLIで`yomitoku_device=`引数を使用しない | `run_ocr.py`で`yomitoku_device=args.device`を使用 |
| test_naming_convention.py | `TestYomitokuNamingInCLI::test_no_yomitoku_in_cli_variable_names` | CLIスクリプト内に`yomitoku_*`変数がない | `run_ocr.py:38`で`yomitoku_device`を使用 |
| test_naming_convention.py | `TestYomitokuFunctionNaming::test_no_detect_layout_yomitoku_import_in_cli` | `detect_layout_yomitoku`関数をインポートしない | `detect_layout.py`で`detect_layout_yomitoku`をインポート |
| test_naming_convention.py | `TestYomitokuFunctionNaming::test_no_yomitoku_function_calls_in_cli` | `yomitoku`を含む関数を呼び出さない | `detect_layout.py:31`で`detect_layout_yomitoku()`を呼び出し |
| test_naming_convention.py | `TestGrepVerification::test_grep_no_yomitoku_device_in_cli` | grepで`yomitoku_device`が0件 | `src/cli/run_ocr.py`で検出 |
| test_naming_convention.py | `TestGrepVerification::test_grep_no_detect_layout_yomitoku_in_cli` | grepで`detect_layout_yomitoku`が0件 | `src/cli/detect_layout.py`で2箇所検出 |
| test_naming_convention.py | `TestGrepVerification::test_grep_no_ocr_yomitoku_import_in_cli` | grepで`from src.ocr_yomitoku`が0件 | `src/cli/detect_layout.py`で検出 |

## PASSテスト一覧

| テストファイル | テストメソッド | 検証内容 |
|----------------|----------------|----------|
| test_naming_convention.py | `TestYomitokuNamingInCLI::test_no_yomitoku_in_argparse_dest` | `--yomitoku`引数がない |
| test_naming_convention.py | `TestRoverOcrNaming::test_no_rover_ocr_in_module_names` | ファイル名に`rover-ocr`/`rover_ocr`がない |
| test_naming_convention.py | `TestRoverOcrNaming::test_no_rover_ocr_in_code_comments` | CLIコメントに`rover-ocr`/`rover_ocr`がない |

## 実装ヒント

### 1. run_ocr.py: yomitoku_device → device

**現在のコード**:
```python
# src/cli/run_ocr.py:38
run_rover_batch(
    args.pages_dir,
    args.output,
    yomitoku_device=args.device,  # NG
)
```

**修正案**:
```python
run_rover_batch(
    args.pages_dir,
    args.output,
    device=args.device,  # OK (関数シグネチャも変更必要)
)
```

**注意**: `run_rover_batch`関数のシグネチャも`yomitoku_device` → `device`に変更する必要がある。

### 2. detect_layout.py: detect_layout_yomitoku → detect_layout

**現在のコード**:
```python
# src/cli/detect_layout.py
from src.ocr_yomitoku import detect_layout_yomitoku

detect_layout_yomitoku(args.pages_dir, args.output, device=args.device)
```

**修正案**:
- `ocr_yomitoku.py`の`detect_layout_yomitoku`関数を`detect_layout`にリネーム
- または、新しいラッパー関数`detect_layout`を作成してエイリアスとして使用

### 3. 関連する変更箇所

Phase 1分析より、以下のファイルも変更が必要:

| ファイル | 変更内容 |
|----------|----------|
| `src/ocr_rover.py` | `yomitoku_device`引数を`device`にリネーム |
| `src/ocr_integrated.py` | `yomitoku_device`引数を`device`にリネーム |
| `src/layout_ocr.py` | `yomitoku_device`引数を`device`にリネーム |
| `src/ocr_ensemble.py` | `yomitoku_device`引数を`device`にリネーム |
| `src/ocr_engines.py` | `yomitoku_device`引数を`device`にリネーム |
| `src/pipeline.py` | `yomitoku_device`引数を`device`にリネーム |
| `src/ocr_yomitoku.py` | `detect_layout_yomitoku` → `detect_layout`にリネーム（またはエイリアス追加） |

## FAIL出力例

```
$ make test -- tests/test_naming_convention.py -v

FAILED tests/test_naming_convention.py::TestYomitokuNamingInCLI::test_no_yomitoku_device_in_cli_args
  - AssertionError: run_ocr.py: yomitoku_device引数を使用しています。
    deviceにリネームしてください: ['yomitoku_device=']

FAILED tests/test_naming_convention.py::TestYomitokuNamingInCLI::test_no_yomitoku_in_cli_variable_names
  - AssertionError: run_ocr.py: yomitoku_*変数が存在します:
    L38: yomitoku_device=args.device,

FAILED tests/test_naming_convention.py::TestYomitokuFunctionNaming::test_no_detect_layout_yomitoku_import_in_cli
  - AssertionError: detect_layout.py: detect_layout_yomitoku関数を使用しています。
    detect_layout にリネームしてください。

FAILED tests/test_naming_convention.py::TestYomitokuFunctionNaming::test_no_yomitoku_function_calls_in_cli
  - AssertionError: detect_layout.py: yomitoku関数を呼び出しています:
    L31: detect_layout_yomitoku(args.pages_dir, args.output, device=args.device)

FAILED tests/test_naming_convention.py::TestGrepVerification::test_grep_no_yomitoku_device_in_cli
  - AssertionError: CLIにyomitoku_deviceが見つかりました:
    src/cli/run_ocr.py:            yomitoku_device=args.device,

FAILED tests/test_naming_convention.py::TestGrepVerification::test_grep_no_detect_layout_yomitoku_in_cli
  - AssertionError: CLIにdetect_layout_yomitokuが見つかりました:
    src/cli/detect_layout.py:from src.ocr_yomitoku import detect_layout_yomitoku
    src/cli/detect_layout.py:        detect_layout_yomitoku(args.pages_dir, args.output, device=args.device)

FAILED tests/test_naming_convention.py::TestGrepVerification::test_grep_no_ocr_yomitoku_import_in_cli
  - AssertionError: CLIでocr_yomitokuをインポートしています:
    src/cli/detect_layout.py:from src.ocr_yomitoku import detect_layout_yomitoku

========================= 7 failed, 3 passed in 0.06s =========================
```

## 次のステップ

Phase 3 Implementation (GREEN)で以下を実行:

1. **T040**: このREDテスト出力を読み込む
2. **T041**: 変数名`yomitoku_device` → `device`にリネーム (`src/cli/*.py`)
3. **T042**: 関数名の「yomitoku」「rover_ocr」を統一 (`src/`)
4. **T043**: コメント・docstringの名称を更新 (`src/`)
5. **T044**: インポート文を更新 (`src/`)
6. **T045**: `make test` PASSを確認 (GREEN)

## テストファイル

**作成されたテストファイル**: `/data/projects/video-separater/tests/test_naming_convention.py`

**テストクラス構成**:
- `TestYomitokuNamingInCLI`: CLIスクリプト内のyomitoku命名規則違反検出
- `TestYomitokuFunctionNaming`: 関数名のyomitoku命名規則違反検出
- `TestRoverOcrNaming`: rover-ocr/rover_ocr命名規則違反検出
- `TestGrepVerification`: grepによる横断的検証
