# Phase 2 Output: User Story 1 - Spread モード明示指定

**Date**: 2026-02-24
**Status**: Completed
**User Story**: US1 - Spread モード明示指定

## Executed Tasks

- [x] T007 前フェーズの出力を読む: specs/018-spread-mode-trim/tasks/ph1-output.md
- [x] T008 [P] [US1] mode=single でコピーのみのテスト実装: tests/preprocessing/test_split_spread.py
- [x] T009 [P] [US1] mode=spread で常に分割のテスト実装: tests/preprocessing/test_split_spread.py
- [x] T010 [P] [US1] デフォルト mode=single のテスト実装: tests/preprocessing/test_split_spread.py
- [x] T011 [P] [US1] 環境変数 SPREAD_MODE 読み込みのテスト実装: tests/preprocessing/test_split_spread.py
- [x] T012 [P] [US1] CLI引数が環境変数より優先されるテスト実装: tests/preprocessing/test_split_spread.py
- [x] T013 [P] [US1] モード表示（stdout）のテスト実装: tests/preprocessing/test_split_spread.py
- [x] T014 `make test` で FAIL を確認 (RED)
- [x] T015 RED 出力を生成: specs/018-spread-mode-trim/red-tests/ph2-test.md
- [x] T016 RED テストを読む: specs/018-spread-mode-trim/red-tests/ph2-test.md
- [x] T017 [P] [US1] SpreadMode enum を追加: src/preprocessing/split_spread.py
- [x] T018 [P] [US1] split_spread_pages() に mode 引数を追加: src/preprocessing/split_spread.py
- [x] T019 [P] [US1] get_spread_mode() 関数を追加（環境変数/デフォルト）: src/preprocessing/split_spread.py
- [x] T020 [US1] モード表示ロジックを追加: src/preprocessing/split_spread.py
- [x] T021 [P] [US1] CLI に --mode 引数を追加: src/cli/split_spreads.py
- [x] T022 [P] [US1] config.yaml に spread_mode 設定を追加: config.yaml
- [x] T023 [P] [US1] Makefile に SPREAD_MODE 変数を追加: Makefile
- [x] T024 `make test` で PASS を確認 (GREEN)
- [x] T025 `make test` で全テスト通過を確認（リグレッションなし）
- [x] T026 検証用動画でテスト: movies/n3-failers-in-developing-softwear.mov (spread)
- [x] T027 検証用動画でテスト: movies/n5-sre.mov (single)
- [x] T028 Edit: specs/018-spread-mode-trim/tasks/ph2-output.md

## Changed Files

| File | Change Type | Summary |
|------|-------------|---------|
| src/preprocessing/split_spread.py | Modified | SpreadMode enum追加、get_spread_mode()関数追加、split_spread_pages()にmode引数追加、モード表示機能追加 |
| src/cli/split_spreads.py | Modified | --mode CLI引数追加、SpreadMode import追加 |
| config.yaml | Modified | spread_mode設定項目追加（デフォルト: single） |
| Makefile | Modified | SPREAD_MODE変数追加、split-spreadsターゲットに--mode引数追加 |
| tests/preprocessing/test_split_spread.py | New | US1の32テスト実装（mode=single、mode=spread、環境変数、CLI優先度、モード表示、エッジケース） |
| tests/test_split_spread.py | Modified | 既存テストにSpreadMode import追加、3テストにmode=SpreadMode.SPREAD引数追加 |

## Test Results

```
================= 1373 passed, 6 skipped in 124.19s (0:02:04) ==================
```

**全テスト通過**: 1373 passed (32 新規テスト + 既存テスト全て)、リグレッションなし

## Implementation Details

### SpreadMode enum

```python
class SpreadMode(Enum):
    """Processing mode for image splitting."""
    SINGLE = "single"
    SPREAD = "spread"
```

### get_spread_mode() 関数

優先順位: CLI引数 > 環境変数 `SPREAD_MODE` > デフォルト値 (`SINGLE`)

- 大文字小文字を区別しない
- 前後の空白をトリミング
- 無効値の場合は ValueError を発生

### split_spread_pages() の動作

- `mode=SpreadMode.SINGLE`: 全画像を分割せずコピーのみ
- `mode=SpreadMode.SPREAD`: 全画像を左右に分割（アスペクト比に関係なく）
- `mode=None`: `get_spread_mode()` でデフォルト値を取得

### モード表示

処理開始時に標準出力に `Mode: single` または `Mode: spread` を表示

## Discovered Issues

なし

## Handoff to Next Phase

Phase 3 (US2 - 2段階 Trim 制御) で実装するもの:

**新規追加予定**:
- `TrimConfig` dataclass: global-trim と split-trim の設定を統合
- `apply_global_trim()` 関数: 分割前のトリミング処理
- `validate_trim_value()` 関数: 0.0 <= x < 0.5 の範囲検証
- `--global-trim-top`, `--global-trim-bottom`, `--global-trim-left`, `--global-trim-right` CLI引数
- `config.yaml` に `global_trim_*` 設定項目追加

**既存変更予定**:
- `split_spread_pages()`: global-trim 適用ロジック統合

**再利用可能**:
- `SpreadMode` enum: そのまま使用可能
- `get_spread_mode()`: そのまま使用可能
- `split_spread()`: split-trim として継続使用

**Caveats**:
- global-trim は mode=SINGLE でも適用される（分割前のトリミング）
- split-trim は mode=SPREAD でのみ適用される（分割後の外側エッジトリミング）
- trim 値の範囲検証は 0.0 <= x < 0.5（画像の半分以上をトリムすることを防ぐ）
