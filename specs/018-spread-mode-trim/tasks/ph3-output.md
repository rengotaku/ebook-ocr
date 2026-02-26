# Phase 3 Output: User Story 2 - 2段階 Trim 制御

**Date**: 2026-02-24
**Status**: Completed
**User Story**: US2 - 2段階 Trim 制御

## Executed Tasks

- [x] T029 Setup 分析を読む: specs/018-spread-mode-trim/tasks/ph1-output.md
- [x] T030 前フェーズの出力を読む: specs/018-spread-mode-trim/tasks/ph2-output.md
- [x] T031 [P] [US2] global-trim-top/bottom 適用のテスト実装: tests/preprocessing/test_split_spread.py
- [x] T032 [P] [US2] global-trim-left/right 適用のテスト実装: tests/preprocessing/test_split_spread.py
- [x] T033 [P] [US2] global-trim → split-trim の順序テスト実装: tests/preprocessing/test_split_spread.py
- [x] T034 [P] [US2] 単ページモードでの global-trim テスト実装: tests/preprocessing/test_split_spread.py
- [x] T035 [P] [US2] trim 値範囲外（0.5以上）エラーテスト実装: tests/preprocessing/test_split_spread.py
- [x] T036 `make test` で FAIL を確認 (RED)
- [x] T037 RED 出力を生成: specs/018-spread-mode-trim/red-tests/ph3-test.md
- [x] T038 RED テストを読む: specs/018-spread-mode-trim/red-tests/ph3-test.md
- [x] T039 [P] [US2] TrimConfig dataclass を追加: src/preprocessing/split_spread.py
- [x] T040 [P] [US2] apply_global_trim() 関数を追加: src/preprocessing/split_spread.py
- [x] T041 [P] [US2] validate_trim_value() 関数を追加: src/preprocessing/split_spread.py
- [x] T042 [US2] split_spread_pages() に global-trim 統合: src/preprocessing/split_spread.py
- [x] T043 [P] [US2] CLI に --global-trim-* 引数を追加: src/cli/split_spreads.py
- [x] T044 [P] [US2] config.yaml に global_trim_* 設定を追加: config.yaml
- [x] T045 [P] [US2] Makefile に GLOBAL_TRIM_* 変数を追加: Makefile
- [x] T046 `make test` で PASS を確認 (GREEN)
- [x] T047 `make test` で全テスト通過を確認（US1 含むリグレッションなし）
- [x] T048 Edit: specs/018-spread-mode-trim/tasks/ph3-output.md

## Changed Files

| File | Change Type | Summary |
|------|-------------|---------|
| src/preprocessing/split_spread.py | Modified | TrimConfig dataclass 追加、validate_trim_value() 関数追加、apply_global_trim() 関数追加、split_spread_pages() に trim_config 引数追加、global-trim → split-trim の順序実装 |
| src/cli/split_spreads.py | Modified | --global-trim-top/bottom/left/right CLI引数追加、TrimConfig インポート追加、CLI引数から TrimConfig を生成 |
| config.yaml | Modified | global_trim_top/bottom/left/right 設定項目追加（全デフォルト: 0.0） |
| Makefile | Modified | GLOBAL_TRIM_TOP/BOTTOM/LEFT/RIGHT 変数追加、split-spreads ターゲットに --global-trim-* 引数追加 |
| tests/preprocessing/test_split_spread.py | Modified | US2 の 39 テスト追加（global-trim-top/bottom、global-trim-left/right、trim順序、単ページモードでの global-trim、trim 値検証、エッジケース） |

## Test Results

```
================= 1412 passed, 6 skipped in 140.39s (0:02:20) ==================
```

**全テスト通過**: 1412 passed (39 新規 Phase 3 テスト + 32 Phase 2 テスト + 既存テスト全て)、リグレッションなし

## Implementation Details

### TrimConfig dataclass

```python
@dataclass
class TrimConfig:
    # Global trim (分割前に適用)
    global_top: float = 0.0
    global_bottom: float = 0.0
    global_left: float = 0.0
    global_right: float = 0.0

    # Split trim (分割後に適用、spread モードのみ)
    left_page_outer: float = 0.0
    right_page_outer: float = 0.0

    def __post_init__(self) -> None:
        # すべてのフィールドを検証 (0.0 <= x < 0.5)
```

### validate_trim_value() 関数

- 0.0 <= value < 0.5 の範囲を検証
- 範囲外の値で ValueError を発生
- エラーメッセージにフィールド名を含む

### apply_global_trim() 関数

- 新しい Image オブジェクトを返す（元画像は変更しない）
- img.crop() を使用して4辺をトリミング
- global_top/bottom/left/right の値に基づいて crop_box を計算

### split_spread_pages() の動作

1. **Global trim 適用**: trim_config が指定されている場合、分割前に apply_global_trim() を適用
2. **モード判定**: mode=SPREAD なら分割、mode=SINGLE なら分割しない
3. **Split trim 適用**: mode=SPREAD のときのみ、trim_config の left_page_outer/right_page_outer を使用して外側エッジをトリミング

### CLI 引数

- `--global-trim-top`, `--global-trim-bottom`, `--global-trim-left`, `--global-trim-right`: 分割前のトリミング
- 既存の `--left-trim`, `--right-trim`: 分割後の外側エッジトリミング（TrimConfig の left_page_outer/right_page_outer として扱われる）

### 設定ファイル

config.yaml に以下の項目を追加:
- `global_trim_top: 0.0`
- `global_trim_bottom: 0.0`
- `global_trim_left: 0.0`
- `global_trim_right: 0.0`

### Makefile 変数

- `GLOBAL_TRIM_TOP`, `GLOBAL_TRIM_BOTTOM`, `GLOBAL_TRIM_LEFT`, `GLOBAL_TRIM_RIGHT`: config.yaml から読み込み
- split-spreads ターゲットに --global-trim-* 引数を追加

## Discovered Issues

なし

## Handoff to Next Phase

Phase 4 (US3 - パイプライン統合とプレビュー) で実装するもの:

**新規追加予定**:
- `make preview-extract` ターゲット: フレーム抽出のみ（trim なし）
- `make preview-trim` ターゲット: preview/ ディレクトリから trim プレビュー
- `make run` への split-spreads ステップ統合
- preview/ ディレクトリ構造: preview/frames/, preview/trimmed/

**既存利用可能**:
- TrimConfig: そのまま使用可能
- apply_global_trim(): プレビューでも使用可能
- split_spread_pages(): trim_config 引数で動作

**Caveats**:
- preview-trim は preview/frames/ が存在することを前提とする
- preview-extract を実行せずに preview-trim を実行した場合のエラーハンドリングが必要
- make run への統合は既存パイプラインステップとの依存関係を考慮すること
