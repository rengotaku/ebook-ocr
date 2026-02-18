# Phase 2 Output: User Story 1 - CLIスクリプト分解 (GREEN)

**Date**: 2026-02-18
**Feature**: 010-pipeline-refactoring
**Phase**: Phase 2 - User Story 1 (Priority: P1)

## Summary

pipeline.pyを6つの独立したCLIスクリプトに分解し、全68テストがパスした。

| 項目 | 値 |
|------|-----|
| Phase | 2 |
| タスク完了 | 22/22 |
| テスト結果 | 1259 passed, 6 skipped |
| CLI テスト | 68/68 passed |
| 状態 | GREEN |

## 実行タスク

| ID | タスク | ステータス |
|----|--------|-----------|
| T013 | 前フェーズ出力読み込み | ✅ 完了 |
| T014-T020 | REDテスト実装 | ✅ 完了 |
| T021 | make test FAIL 確認 | ✅ 完了 |
| T022 | RED出力生成 | ✅ 完了 |
| T023 | REDテスト読み込み | ✅ 完了 |
| T024 | src/cli/__init__.py 作成 | ✅ 完了 |
| T025 | CLI extract_frames 実装 | ✅ 完了 |
| T026 | CLI deduplicate 実装 | ✅ 完了 |
| T027 | CLI split_spreads 実装 | ✅ 完了 |
| T028 | CLI detect_layout 実装 | ✅ 完了 |
| T029 | CLI run_ocr 実装 | ✅ 完了 |
| T030 | CLI consolidate 実装 | ✅ 完了 |
| T031 | make test PASS 確認 | ✅ 完了 |
| T032 | 全テストパス確認 | ✅ 完了 |
| T033 | 手動実行確認 | ✅ 完了 |
| T034 | フェーズ出力生成 | ✅ 完了 |

## 作成ファイル

### 新規作成

```
src/cli/
├── __init__.py          # CLI パッケージ初期化
├── __main__.py          # CLI コマンド一覧表示
├── extract_frames.py    # 動画フレーム抽出
├── deduplicate.py       # 重複フレーム除去
├── split_spreads.py     # 見開きページ分割
├── detect_layout.py     # レイアウト検出
├── run_ocr.py          # OCR実行
└── consolidate.py      # OCR結果統合
```

## 修正ファイル

### 既存バグ修正

| ファイル | 変更内容 | 理由 |
|----------|----------|------|
| src/ocr_rover.py | importに`src.`プレフィックス追加 | 相対importでモジュールが見つからないエラー修正 |

**詳細**:
```python
# Before (L19-21)
from ocr_engines import EngineResult, TextWithBox, run_all_engines
from ocr_output import ROVEROutput
from ocr_alignment import align_texts_character_level, vote_aligned_text

# After
from src.ocr_engines import EngineResult, TextWithBox, run_all_engines
from src.ocr_output import ROVEROutput
from src.ocr_alignment import align_texts_character_level, vote_aligned_text
```

## CLI仕様

### 1. extract_frames

```bash
python -m src.cli.extract_frames VIDEO -o OUTPUT_DIR [-i INTERVAL]
```

**引数**:
- VIDEO (required): 入力動画ファイルパス
- -o, --output (required): フレーム出力ディレクトリ
- -i, --interval (optional): フレーム抽出間隔（秒、デフォルト: 1.5）

### 2. deduplicate

```bash
python -m src.cli.deduplicate INPUT_DIR -o OUTPUT_DIR [-t THRESHOLD]
```

**引数**:
- INPUT_DIR (required): フレーム入力ディレクトリ
- -o, --output (required): ページ出力ディレクトリ
- -t, --threshold (optional): ハッシュ距離閾値（デフォルト: 8）

### 3. split_spreads

```bash
python -m src.cli.split_spreads PAGES_DIR [--aspect-ratio RATIO] [--left-trim PCT] [--right-trim PCT]
```

**引数**:
- PAGES_DIR (required): ページディレクトリ（in-place更新）
- --aspect-ratio (optional): 見開き判定閾値（デフォルト: 1.2）
- --left-trim (optional): 左ページ左端トリム率（デフォルト: 0.0）
- --right-trim (optional): 右ページ右端トリム率（デフォルト: 0.0）

### 4. detect_layout

```bash
python -m src.cli.detect_layout PAGES_DIR -o OUTPUT_DIR [--device DEVICE]
```

**引数**:
- PAGES_DIR (required): ページ画像ディレクトリ
- -o, --output (required): レイアウト出力ディレクトリ
- --device (optional): cpu または cuda（デフォルト: cpu）

### 5. run_ocr

```bash
python -m src.cli.run_ocr PAGES_DIR -o OUTPUT_DIR [--layout-dir DIR] [--device DEVICE]
```

**引数**:
- PAGES_DIR (required): ページ画像ディレクトリ
- -o, --output (required): OCR結果出力ディレクトリ
- --layout-dir (optional): レイアウト情報ディレクトリ
- --device (optional): cpu または cuda（デフォルト: cpu）

### 6. consolidate

```bash
python -m src.cli.consolidate OCR_DIR -o OUTPUT_DIR
```

**引数**:
- OCR_DIR (required): OCR結果ディレクトリ
- -o, --output (required): 出力ディレクトリ

## テスト結果

### CLI テスト (68 tests)

```
tests/cli/test_consolidate.py ............ 6 passed
tests/cli/test_deduplicate.py ............ 7 passed
tests/cli/test_detect_layout.py ........... 6 passed
tests/cli/test_error_handling.py ........... 30 passed
tests/cli/test_extract_frames.py ........... 6 passed
tests/cli/test_run_ocr.py ........... 7 passed
tests/cli/test_split_spreads.py ........... 6 passed

============================== 68 passed in 5.06s ==============================
```

### 全体テスト

```
============================== 1259 passed, 6 skipped in 7.00s ==============================
```

## 実装の特徴

### エラーハンドリング

全CLIで統一されたエラーハンドリング:

1. **入力検証**: ファイル/ディレクトリ存在確認
2. **エラーメッセージ**: stderr への出力
3. **Exit code**: 成功=0, エラー=1
4. **ヘルプ**: `--help` で usage 表示

### ラップパターン

```python
def main() -> int:
    parser = argparse.ArgumentParser(description="...")
    parser.add_argument("input", ...)
    parser.add_argument("-o", "--output", required=True, ...)
    args = parser.parse_args()

    if not Path(args.input).exists():
        print(f"Error: Input not found: {args.input}", file=sys.stderr)
        return 1

    try:
        existing_function(args.input, args.output, ...)
        return 0
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

## 次フェーズへの引き継ぎ

### Phase 3 (US2) への準備完了

- ✅ 全CLIスクリプトが独立して実行可能
- ✅ 既存機能を維持（既存テスト1259件パス）
- ✅ 新規テスト68件すべてパス

### 注意事項

1. **import バグ修正**: `src/ocr_rover.py` の相対import問題を修正済み
2. **split_spreads の挙動**: renumber_pages() を自動で呼び出す（契約と一致）
3. **consolidate の入力検証**: `ocr_output/rover/` ディレクトリ存在チェック追加

### 残課題

- Phase 3: 命名規則の統一（yomitoku → rover）
- Phase 4: フォルダ構造整理
- Phase 5: 後方互換性コード除去
- Phase 6: ワークフロー手順書作成
- Phase 7: 旧ファイル削除

## Checkpoint達成

✅ **6つのCLIスクリプトが独立して実行可能**

全てのPhase 2目標を達成。Phase 3（命名規則統一）へ進む準備完了。
