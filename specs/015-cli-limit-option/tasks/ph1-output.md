# Phase 1: Setup 完了レポート

**日時**: 2026-02-23
**フェーズ**: Setup (既存コード分析)
**ステータス**: ✅ 完了

## 概要

既存コードの構造を分析し、`--limit` オプション追加に必要な変更箇所を特定した。

## 分析結果

### CLI構造 (src/cli/)

| ファイル | 基盤関数 | argparse引数 | ファイル取得パターン |
|----------|----------|--------------|---------------------|
| deduplicate.py | `deduplicate_frames()` | input_dir, -o, -t | CLI側: `input_path.glob("frame_*.png")` |
| detect_layout.py | `detect_layout()` | pages_dir, -o, --device | 基盤側: `pages_path.glob("*.png")` |
| run_ocr.py | `run_rover_batch()` | pages_dir, -o, --layout-dir, --device | 基盤側: `pages_path.glob("*.png")` |
| consolidate.py | `consolidate_rover_output()` | ocr_dir, -o | CLI側: `ocr_output_dir.glob("*.txt")` |

### 基盤関数構造

| ファイル | 関数 | glob実行箇所 | 行番号 |
|----------|------|--------------|--------|
| src/preprocessing/deduplicate.py | `deduplicate_frames()` | 関数内 | L32 |
| src/layout/detector.py | `detect_layout_yomitoku()` | 関数内 | L233 |
| src/rover/ensemble.py | `run_rover_batch()` | 関数内 | L233 |
| src/consolidate.py | `consolidate_rover_output()` | 関数内 | L39 |

### 実装パターン

全ての基盤関数で同じパターンを適用可能:

```python
# 既存
pages = sorted(pages_path.glob("*.png"))

# 変更後
pages = sorted(pages_path.glob("*.png"))
if limit:
    print(f"Processing first {limit} of {len(pages)} files", file=sys.stderr)
    pages = pages[:limit]
```

### テスト構造

- **テストディレクトリ**: `tests/cli/`
- **既存テストファイル**:
  - test_deduplicate.py
  - test_detect_layout.py
  - test_run_ocr.py
  - test_consolidate.py
  - test_error_handling.py
- **テストパターン**: subprocess でCLIを実行し、returncode と出力を検証

### Makefile構造

- **既存ターゲット**: `run` (フルパイプライン)
- **追加予定**: `test-run` (LIMIT変数付きパイプライン)
- **変数展開パターン**: `$(if $(LIMIT),--limit $(LIMIT),)` を使用

## 変更対象ファイル一覧

### CLI (--limit オプション追加)
1. src/cli/deduplicate.py
2. src/cli/detect_layout.py
3. src/cli/run_ocr.py
4. src/cli/consolidate.py

### 基盤関数 (limit パラメータ追加)
1. src/preprocessing/deduplicate.py
2. src/layout/detector.py
3. src/rover/ensemble.py
4. src/consolidate.py

### Makefile
- test-run ターゲット追加

### テスト (新規作成)
1. tests/cli/test_deduplicate_limit.py
2. tests/cli/test_detect_layout_limit.py
3. tests/cli/test_run_ocr_limit.py
4. tests/cli/test_consolidate_limit.py

## 次フェーズへの引き継ぎ

- Phase 2 (US1 TDD) で上記ファイルを変更
- テストは subprocess パターンを使用
- 全CLIで同一の --limit オプションパターンを適用
