# Implementation Plan: CLIコマンドへの--limitオプション追加

**Branch**: `015-cli-limit-option` | **Date**: 2026-02-22 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/015-cli-limit-option/spec.md`

## Summary

各CLIコマンド（deduplicate, detect_layout, run_ocr, consolidate）に`--limit N`オプションを追加し、処理する画像数を制限できるようにする。また、Makefileに`test-run`ターゲットを追加し、`LIMIT`変数でパイプライン全体の画像数制限をサポートする。

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: argparse（標準ライブラリ）
**Storage**: ファイルシステム（PNG画像、TXTファイル）
**Testing**: pytest
**Target Platform**: Linux/macOS
**Project Type**: single
**Performance Goals**: 25枚処理で5分以内
**Constraints**: 後方互換性維持（--limitなしで既存動作）
**Scale/Scope**: 4 CLIファイル + Makefile + テスト

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Pipeline-First | ✅ PASS | 各CLIステップに独立して適用可能 |
| II. Test-First | ✅ PASS | TDDで実装予定 |
| III. Ollama Integration | N/A | OCR処理自体は変更なし |
| IV. Immutability | ✅ PASS | ファイルリストのスライスは副作用なし |
| V. Simplicity (YAGNI) | ✅ PASS | 最小限の変更（argparse + リストスライス） |

**Technical Constraints**:
- Python 3.13+ ✅
- Makefile ✅
- pytest ✅

## Project Structure

### Documentation (this feature)

```text
specs/015-cli-limit-option/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (by /speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── cli/
│   ├── deduplicate.py       # +--limit option
│   ├── detect_layout.py     # +--limit option
│   ├── run_ocr.py           # +--limit option
│   └── consolidate.py       # +--limit option
├── preprocessing/
│   └── deduplicate.py       # +limit parameter
├── layout/
│   └── detector.py          # +limit parameter
├── rover/
│   └── ensemble.py          # +limit parameter
└── consolidate.py           # +limit parameter

tests/
└── cli/
    ├── test_deduplicate_limit.py    # NEW
    ├── test_detect_layout_limit.py  # NEW
    ├── test_run_ocr_limit.py        # NEW
    └── test_consolidate_limit.py    # NEW

Makefile                     # +test-run target
```

**Structure Decision**: 既存のsingleプロジェクト構造を維持。新規ファイルは最小限（テストのみ）。

## Complexity Tracking

> 違反なし - Simplicityに準拠した最小限の実装

## Implementation Phases

### Phase 1: Setup (テスト環境準備)

- テストディレクトリ構造の確認
- フィクスチャの準備（既存のものを再利用）

### Phase 2: TDD - deduplicate.py

**RED**: `test_deduplicate_limit.py` 作成
- `--limit 5` で最初の5枚のみ処理されることをテスト
- `--limit` なしで全画像処理されることをテスト
- `--limit 0` でエラーをテスト

**GREEN**: 実装
1. `src/cli/deduplicate.py` に `--limit` argparse追加
2. `src/preprocessing/deduplicate.py` に `limit` パラメータ追加
3. ファイルリストをスライス

### Phase 3: TDD - detect_layout.py

**RED**: `test_detect_layout_limit.py` 作成
**GREEN**: 同様の実装パターン

### Phase 4: TDD - run_ocr.py

**RED**: `test_run_ocr_limit.py` 作成
**GREEN**: 同様の実装パターン

### Phase 5: TDD - consolidate.py

**RED**: `test_consolidate_limit.py` 作成
**GREEN**: 同様の実装パターン

### Phase 6: Makefile test-run ターゲット

- `test-run` ターゲット追加
- `LIMIT` 変数サポート
- 統合テスト

### Phase 7: Polish

- ドキュメント更新（ヘルプメッセージ確認）
- エッジケーステスト
- CI確認

## Implementation Pattern

各CLIに対して同じパターンを適用：

**CLI変更（例: deduplicate.py）**:
```python
parser.add_argument(
    "--limit",
    type=int,
    help="Process only first N files (for testing)",
)

# バリデーション
if args.limit is not None and args.limit <= 0:
    print("Error: --limit must be a positive integer", file=sys.stderr)
    return 1

# 関数呼び出し
deduplicate_frames(args.input_dir, args.output, args.threshold, limit=args.limit)
```

**基盤関数変更（例: preprocessing/deduplicate.py）**:
```python
def deduplicate_frames(input_dir, output_dir, threshold=8, *, limit=None):
    frames = sorted(src.glob("frame_*.png"))
    if limit:
        print(f"Limiting to first {limit} files (of {len(frames)})", file=sys.stderr)
        frames = frames[:limit]
    # ... rest of processing
```

## Makefile Integration

```makefile
LIMIT ?=

test-run: setup ## Quick test run with limited images
	@test -n "$(VIDEO)" || { echo "Error: VIDEO required"; exit 1; }
	$(eval HASH := $(shell PYTHONPATH=$(CURDIR) $(PYTHON) -m src.preprocessing.hash "$(VIDEO)" --prefix-only))
	$(eval HASHDIR := output/$(HASH)-test)
	$(eval LIMIT_OPT := $(if $(LIMIT),--limit $(LIMIT),))

	@echo "=== Test Run (LIMIT=$(LIMIT)) ==="
	@$(MAKE) extract-frames VIDEO="$(VIDEO)" HASHDIR="$(HASHDIR)"
	PYTHONPATH=$(CURDIR) $(PYTHON) -m src.cli.deduplicate "$(HASHDIR)/frames" -o "$(HASHDIR)/pages" $(LIMIT_OPT)
	PYTHONPATH=$(CURDIR) $(PYTHON) -m src.cli.detect_layout "$(HASHDIR)/pages" -o "$(HASHDIR)/layout" $(LIMIT_OPT)
	PYTHONPATH=$(CURDIR) $(PYTHON) -m src.cli.run_ocr "$(HASHDIR)/pages" -o "$(HASHDIR)/ocr_output" --layout-dir "$(HASHDIR)/layout" $(LIMIT_OPT)
	PYTHONPATH=$(CURDIR) $(PYTHON) -m src.cli.consolidate "$(HASHDIR)/ocr_output" -o "$(HASHDIR)" $(LIMIT_OPT)
	@echo "=== Test run complete: $(HASHDIR) ==="
```

## Risk Assessment

| Risk | Mitigation |
|------|------------|
| 後方互換性破損 | `limit=None` デフォルトで既存動作維持 |
| テストフィクスチャ不足 | 既存フィクスチャを再利用 |
| OCR処理時間 | モック使用でテスト高速化 |

## Next Steps

`/speckit.tasks` で詳細タスクを生成
