# Phase 4 Output: User Story 3 - パイプライン統合とプレビュー

**Date**: 2026-02-25
**Status**: Completed
**User Story**: US3 - パイプライン統合とプレビュー

## Executed Tasks

- [x] T049 Setup 分析を読む: specs/018-spread-mode-trim/tasks/ph1-output.md
- [x] T050 前フェーズの出力を読む: specs/018-spread-mode-trim/tasks/ph3-output.md
- [x] T051 [P] [US3] preview-extract ターゲットのテスト実装: tests/test_makefile_targets.py
- [x] T052 [P] [US3] preview-trim ターゲットのテスト実装: tests/test_makefile_targets.py
- [x] T053 [P] [US3] preview/ 空時のエラーハンドリングテスト実装: tests/preprocessing/test_split_spread.py
- [x] T054 [P] [US3] make run に split-spreads 統合のテスト実装: tests/test_makefile_targets.py
- [x] T055 `make test` で FAIL を確認 (RED)
- [x] T056 RED 出力を生成: specs/018-spread-mode-trim/red-tests/ph4-test.md
- [x] T057 RED テストを読む: specs/018-spread-mode-trim/red-tests/ph4-test.md
- [x] T058 [P] [US3] Makefile に preview-extract ターゲットを追加: Makefile
- [x] T059 [P] [US3] Makefile に preview-trim ターゲットを追加: Makefile
- [x] T060 [US3] split_spreads.py に preview/ ディレクトリ確認ロジックを追加: src/cli/split_spreads.py
- [x] T061 [US3] Makefile の run ターゲットに split-spreads ステップを追加: Makefile
- [x] T062 `make test` で PASS を確認 (GREEN)
- [x] T063 `make test` で全テスト通過を確認（US1, US2 含むリグレッションなし）
- [x] T064 `make preview-extract VIDEO=movies/n3-failers-in-developing-softwear.mov LIMIT=3` で動作確認
- [x] T065 `make preview-trim` で trim プレビュー確認
- [x] T066 Edit: specs/018-spread-mode-trim/tasks/ph4-output.md

## Changed Files

| File | Change Type | Summary |
|------|-------------|---------|
| Makefile | Modified | preview-extract ターゲット追加（VIDEO からフレーム抽出）、preview-trim ターゲット追加（frames/ → trimmed/）、run ターゲットに split-spreads ステップ統合、.PHONY に preview-extract/preview-trim 追加、CFG マクロに YAML コメント除去処理追加 |
| src/cli/split_spreads.py | Modified | preview_trim_check() 関数追加（frames/ 存在確認）、preview_trim() 関数追加（trim 適用、frame_*.png → page_*.png リネーム対応）、shutil/tempfile インポート追加 |
| src/preprocessing/split_spread.py | Modified | split_spread_pages() にディレクトリ存在確認追加（FileNotFoundError 発生） |
| tests/test_makefile_targets.py | New | 18 テスト追加（preview-extract ターゲット検証、preview-trim ターゲット検証、make run 統合検証） |
| tests/preprocessing/test_split_spread.py | Modified | 16 テスト追加（preview エラーハンドリング、preview trim 処理、エッジケース） |

## Test Results

```
================= 1448 passed, 6 skipped in 153.75s (0:02:33) ==================
```

**全テスト通過**: 1448 passed (34 新規 Phase 4 テスト + Phase 1-3 テスト + 既存テスト全て)、リグレッションなし

**Coverage**: 80%+ (既存カバレッジ維持)

## Implementation Details

### preview-extract ターゲット

- VIDEO パラメータ必須（ファイル存在確認あり）
- INTERVAL パラメータでフレーム抽出間隔を調整可能（デフォルト: 1.5秒）
- `output/<hash>/preview/frames/` にフレーム抽出
- extract_frames CLI を呼び出し（frame_0001.png, frame_0002.png, ...）

### preview-trim ターゲット

- HASHDIR パラメータ必須（preview/frames/ 存在確認あり）
- SPREAD_MODE, GLOBAL_TRIM_*, LEFT_TRIM, RIGHT_TRIM パラメータを使用
- Python one-liner で preview_trim() 関数を呼び出し
- `preview/frames/` → `preview/trimmed/` に処理結果出力

### preview_trim_check() 関数

- preview/frames/ の存在確認
- PNG ファイルの存在確認
- エラー時に `make preview-extract` 実行を促すメッセージ表示

### preview_trim() 関数

- 一時ディレクトリにフレームをコピー（元ファイル保護）
- frame_*.png を page_*.png にリネーム（split_spread_pages 互換）
- split_spread_pages() で trim 処理実行
- preview/trimmed/ に出力

### make run 統合

- Step 2.5 として split-spreads を deduplicate と detect-layout の間に追加
- SPREAD_MODE および trim パラメータをパイプライン経由で渡す

## Discovered Issues

### Issue 1: extract_frames CLI が --limit をサポートしない

**問題**: `make preview-extract` の LIMIT パラメータが extract_frames に渡せない
**解決**: INTERVAL パラメータで代替（大きな間隔でフレーム数を減らす）

### Issue 2: config.yaml の YAML コメントが Makefile 変数に含まれる

**問題**: `global_trim_left: 0.0      # 左端トリム率` の形式で、`#` 以降がシェルコマンドに含まれてシンタックスエラー
**解決**: CFG マクロに `sed 's/[[:space:]]*#.*//'` を追加してコメント除去

### Issue 3: extract_frames が frame_*.png を出力、split_spread_pages が page_*.png を期待

**問題**: ファイル名パターンの不一致で "No page images found" エラー
**解決**: preview_trim() 内で frame_*.png → page_*.png にリネームしてからコピー

### Issue 4: Makefile 変数が空になる問題

**問題**: GLOBAL_TRIM_LEFT 等が未指定時に空文字列になり Python 構文エラー
**解決**: `$(or $(GLOBAL_TRIM_LEFT),0.0)` でデフォルト値 0.0 を設定

## Handoff to Next Phase

Phase 5 (Polish) で実装するもの:

**廃止予定機能の警告追加**:
- `is_spread_image()` 関数に deprecation warning（互換性のため残す）
- config.yaml の `spread_aspect_ratio` に非推奨コメント

**ドキュメント更新**:
- quickstart.md の検証
- CLAUDE.md に config.yaml 設定項目を追加

**最終検証**:
- `make test` 全テスト通過
- `make lint` エラーなし

**再利用可能な機能**:
- preview_trim_check(): プレビュー構造検証
- preview_trim(): 2段階プレビュー機能
- preview-extract / preview-trim ターゲット: パイプライン独立実行

**Caveats**:
- preview-extract は LIMIT パラメータ非対応（INTERVAL で調整）
- frame_*.png / page_*.png のリネーム処理は preview_trim() 内で実行
- preview-trim は preview/frames/ 必須（preview-extract 事前実行が必要）
