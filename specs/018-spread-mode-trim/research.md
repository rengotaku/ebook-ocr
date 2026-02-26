# Research: Spread モード明示指定と Trim 制御の拡張

**Date**: 2026-02-24
**Feature**: 018-spread-mode-trim

## 1. 既存実装の分析

### 1.1 現在の split_spread.py

**Decision**: 既存の `is_spread_image()` 関数を条件分岐に変更

**Rationale**:
- 現在はアスペクト比のみで判定（`width/height >= 1.2`）
- 誤判定が発生するため、明示的なモード指定が必要
- 関数自体は残し、`mode=auto` 時のみ使用（ただし auto モードは廃止）

**Alternatives Considered**:
- 関数を完全削除 → 後方互換性のため残す（内部使用可能）
- 新規モジュール作成 → 過剰な分離、YAGNI 違反

### 1.2 現在の trim 実装

**Decision**: global-trim を新規追加、既存の left/right-trim は維持

**Rationale**:
- 既存の `split_spread()` は `left_trim_pct`, `right_trim_pct` を受け取る
- これらは分割後の外側エッジトリミングとして機能
- 分割前のトリミング（global-trim）は新規機能として追加

**Current Code Flow**:
```
split_spread(img, overlap_px, left_trim_pct, right_trim_pct)
  → left_page = img.crop((left_trim_px, 0, mid_x + overlap_px, height))
  → right_page = img.crop((mid_x - overlap_px, 0, width - right_trim_px, height))
```

**Proposed Code Flow**:
```
apply_global_trim(img, top, bottom, left, right)  # NEW
  → trimmed_img = img.crop(...)
split_spread(trimmed_img, overlap_px, left_trim_pct, right_trim_pct)  # EXISTING
```

## 2. 設定と環境変数の優先順位

**Decision**: CLI引数 > 環境変数 > config.yaml > デフォルト値

**Rationale**:
- 既存の Makefile パターンに従う（例: `THRESHOLD ?= $(shell $(call CFG,threshold))`）
- ユーザーが一時的にオーバーライドしやすい

**Implementation**:
```python
import os

def get_spread_mode(cli_mode: str | None) -> str:
    if cli_mode:
        return cli_mode
    env_mode = os.environ.get("SPREAD_MODE")
    if env_mode:
        return env_mode
    # config.yaml からの読み込みは CLI ラッパーで行う
    return "single"  # デフォルト
```

## 3. プレビューのディレクトリ構造

**Decision**: `preview/` ディレクトリを HASHDIR 内に作成

**Rationale**:
- 既存の `pages/`, `originals/` パターンに従う
- プロジェクトごとに独立したプレビュー領域

**Structure**:
```
output/<hash>/
├── frames/          # extract-frames の出力
├── pages/           # deduplicate の出力（現在）
├── originals/       # split-spreads のバックアップ（現在）
├── preview/         # preview-extract の出力（NEW）
│   ├── frames/      # サンプルフレーム
│   └── trimmed/     # trim プレビュー結果
└── ...
```

## 4. Makefile ターゲット設計

**Decision**: `preview-extract`, `preview-trim` を独立ターゲットとして追加

**Rationale**:
- 2段階ワークフローの明示化
- 既存の `extract-frames`, `deduplicate` パターンに従う

**Implementation**:
```makefile
preview-extract: setup
	@test -n "$(VIDEO)" || { echo "Error: VIDEO required"; exit 1; }
	PYTHONPATH=$(CURDIR) $(PYTHON) -m src.cli.extract_frames "$(VIDEO)" \
		-o "$(HASHDIR)/preview/frames" -i $(INTERVAL)

preview-trim: setup
	@test -n "$(HASHDIR)" || { echo "Error: HASHDIR required"; exit 1; }
	@test -d "$(HASHDIR)/preview/frames" || { echo "Error: Run preview-extract first"; exit 1; }
	PYTHONPATH=$(CURDIR) $(PYTHON) -m src.cli.split_spreads "$(HASHDIR)/preview/frames" \
		-o "$(HASHDIR)/preview/trimmed" --mode $(SPREAD_MODE) ...
```

## 5. 後方互換性の確保

**Decision**: デフォルト値を現行動作に近づける（ただし auto モードは廃止）

**Breaking Changes**:
- `auto` モード廃止 → モード未指定時は `single` がデフォルト
- これは意図的な破壊的変更（ユーザーの明示的な意図を尊重）

**Non-Breaking**:
- 既存の `--left-trim`, `--right-trim` は維持
- `config.yaml` の既存項目（`spread_left_trim`, `spread_right_trim`）は維持

## 6. テスト戦略

**Decision**: 既存のテストファイルを拡張

**Test Files**:
- `tests/preprocessing/test_split_spread.py` - 新規作成またはファイル名変更
- フィクスチャ: 見開き画像、単ページ画像のサンプル

**Test Cases**:
1. `mode=single` で分割されないこと
2. `mode=spread` で常に分割されること
3. `global-trim` が分割前に適用されること
4. `split-trim` が分割後に適用されること
5. 環境変数からのモード読み込み
6. CLI引数の優先度
