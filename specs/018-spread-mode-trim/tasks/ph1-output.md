# Phase 1 Output: Setup

**Date**: 2026-02-24
**Status**: Completed

## Executed Tasks

- [x] T001 既存実装を確認: src/preprocessing/split_spread.py
- [x] T002 [P] 既存CLIを確認: src/cli/split_spreads.py
- [x] T003 [P] 既存設定を確認: config.yaml
- [x] T004 [P] 既存Makefileを確認: Makefile（split-spreads ターゲット）
- [x] T005 [P] 既存テストを確認: tests/preprocessing/（存在しない）
- [x] T006 Edit: specs/018-spread-mode-trim/tasks/ph1-output.md

## Existing Code Analysis

### src/preprocessing/split_spread.py

**Structure**:
- `is_spread_image(img, aspect_ratio_threshold)`: アスペクト比で見開き判定（width/height >= threshold）
- `split_spread(img, overlap_px, left_trim_pct, right_trim_pct)`: 画像を左右に分割
- `split_spread_pages(pages_dir, output_dir, ...)`: ディレクトリ内の画像を一括処理
- `renumber_pages(pages_dir)`: 分割後のページ番号を振り直し

**Required Updates**:
1. `SpreadMode` enum を追加: `single`, `spread` の2値
2. `split_spread_pages()` に `mode` 引数を追加: 現在の auto 判定を明示的モード指定に変更
3. `get_spread_mode()` 関数を新規追加: CLI引数 > 環境変数 > デフォルト値の優先順位
4. `TrimConfig` dataclass を追加: global-trim と split-trim の設定を統合
5. `apply_global_trim()` 関数を新規追加: 分割前のトリミング処理
6. `validate_trim_value()` 関数を新規追加: 0.0 <= x < 0.5 の範囲検証

**Current Flow**:
```
split_spread_pages()
  → is_spread_image() で自動判定
  → split_spread() で分割 + split-trim 適用
```

**Target Flow**:
```
split_spread_pages(mode=...)
  → mode == spread なら分割
  → apply_global_trim() で分割前トリミング
  → split_spread() で分割 + split-trim 適用
```

### src/cli/split_spreads.py

**Structure**:
- `main()`: CLI エントリポイント
- 引数: `pages_dir`, `--aspect-ratio`, `--left-trim`, `--right-trim`

**Required Updates**:
1. `--mode` 引数を追加: `single` | `spread` (default: `single`)
2. `--global-trim-top`, `--global-trim-bottom`, `--global-trim-left`, `--global-trim-right` 引数を追加
3. 環境変数 `SPREAD_MODE` の読み込み対応
4. モード表示ロジック追加（stdout に "Mode: spread" など）
5. `--aspect-ratio` を非推奨化（mode=spread では不要）

### config.yaml

**Existing Settings**:
```yaml
split_spreads: true
spread_aspect_ratio: 1.2
spread_left_trim: 0.15
spread_right_trim: 0.15
```

**Required Updates**:
1. `spread_mode: single` を追加（デフォルト値）
2. `global_trim_top: 0.0` を追加
3. `global_trim_bottom: 0.0` を追加
4. `global_trim_left: 0.0` を追加
5. `global_trim_right: 0.0` を追加
6. `spread_aspect_ratio` にコメント追加（非推奨）

### Makefile

**Existing Variables**:
```makefile
LEFT_TRIM ?= $(shell $(call CFG,spread_left_trim))
RIGHT_TRIM ?= $(shell $(call CFG,spread_right_trim))
ASPECT_RATIO ?= $(shell $(call CFG,spread_aspect_ratio))
```

**Existing Target**:
```makefile
split-spreads: setup
    PYTHONPATH=$(CURDIR) $(PYTHON) -m src.cli.split_spreads "$(HASHDIR)/pages" \
        --left-trim $(LEFT_TRIM) --right-trim $(RIGHT_TRIM) --aspect-ratio $(ASPECT_RATIO)
```

**Required Updates**:
1. `SPREAD_MODE ?= $(shell $(call CFG,spread_mode))` を追加
2. `GLOBAL_TRIM_TOP ?= ...` 等を追加
3. `split-spreads` ターゲットに `--mode $(SPREAD_MODE)` を追加
4. `preview-extract` ターゲットを新規追加（Phase 4）
5. `preview-trim` ターゲットを新規追加（Phase 4）
6. `run` ターゲットに `split-spreads` ステップを追加（Phase 4）

## Existing Test Analysis

- **存在しない**: tests/preprocessing/ ディレクトリ自体が存在しない
- 新規作成必要: `tests/preprocessing/test_split_spread.py`
- 新規作成必要: `tests/test_makefile_targets.py` （Phase 4 用）

**Required Fixtures**:
- `sample_spread_image`: 見開き画像（例: 1600x1000）
- `sample_single_image`: 単ページ画像（例: 800x1000）
- `temp_pages_dir`: 一時ディレクトリ（pytest `tmp_path` 使用）

## Technical Decisions

1. **デフォルトモード = single**: 明示的な指定がない場合は分割しない（安全側に倒す）
2. **auto モード廃止**: `is_spread_image()` は内部的に残すが、CLI からは使用しない
3. **global-trim は分割前**: 画像全体に適用後、モード判定・分割を実行
4. **split-trim は spread モードのみ**: single モードでは適用されない
5. **環境変数名**: `SPREAD_MODE`, `GLOBAL_TRIM_TOP`, `GLOBAL_TRIM_BOTTOM`, `GLOBAL_TRIM_LEFT`, `GLOBAL_TRIM_RIGHT`

## Handoff to Next Phase

Phase 2 (US1 - Spread モード明示指定) で実装するもの:

**新規追加**:
- `SpreadMode` enum: `SINGLE`, `SPREAD` の2値
- `get_spread_mode(cli_mode: str | None)`: モード取得（優先順位処理）
- `--mode` CLI 引数と環境変数対応

**既存変更**:
- `split_spread_pages()`: `mode` 引数追加、`is_spread_image()` 呼び出しを条件分岐に変更

**再利用可能**:
- `split_spread()`: そのまま使用可能
- `renumber_pages()`: そのまま使用可能
- Makefile の変数パターン: `CFG` マクロ

**注意事項**:
- `is_spread_image()` は削除せず残す（後方互換性）
- テストは `tests/preprocessing/` ディレクトリから新規作成
