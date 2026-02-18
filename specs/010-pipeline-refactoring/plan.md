# Implementation Plan: パイプライン・リファクタリング

**Branch**: `010-pipeline-refactoring` | **Date**: 2026-02-17 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/010-pipeline-refactoring/spec.md`

## Summary

`pipeline.py`を個別の独立実行可能なCLIスクリプトに分解し、命名規則を「rover」に統一、フォルダ構造を機能別に整理する。後方互換性コードを除去する。

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: argparse (CLI), PyYAML (config)
**Storage**: ファイルベース（画像、JSON、Markdown、XML）
**Testing**: pytest
**Target Platform**: Linux/macOS CLI
**Project Type**: single
**Performance Goals**: N/A（バッチ処理、リファクタリングのため性能目標なし）
**Constraints**: TDD必須
**Scale/Scope**: src/内18ファイル、約5300行のリファクタリング

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Pipeline-First | ✅ PASS | 既存パイプラインを分解、各ステップ独立実行可能に |
| II. Test-First (NON-NEGOTIABLE) | ✅ PASS | TDDでリファクタリング、既存テストを維持 |
| III. Ollama Integration | ✅ N/A | OCR機能の変更なし |
| IV. Immutability & Side-Effect Isolation | ✅ PASS | 既存の純粋関数構造を維持 |
| V. Simplicity (YAGNI) | ✅ PASS | 必要最小限の変更、過剰な抽象化なし |

**Technical Constraints Check**:
- Python 3.13+ ✅
- 依存管理: requirements.txt + venv ✅
- ビルド/テスト: Makefile ✅

## Project Structure

### Documentation (this feature)

```text
specs/010-pipeline-refactoring/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (CLIコマンド仕様)
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code - Current Structure

```text
src/
├── pipeline.py           # 186行 - 分解対象
├── ocr_ensemble.py       # 699行
├── ocr_engines.py        # 613行
├── ocr_rover.py          # 600行
├── layout_ocr.py         # 598行
├── ocr_integrated.py     # 595行
├── ocr_yomitoku.py       # 530行 (リネーム対象)
├── split_spread.py       # 244行
├── detect_figures.py     # 234行
├── ocr_alignment.py      # 211行
├── reading_order.py      # 143行
├── utils.py              # 129行
├── ocr_output.py         # 117行
├── consolidate.py        # 111行
├── extract_frames.py
├── deduplicate.py
├── video_hash.py
├── ocr_preprocess.py
└── book_converter/       # 既存サブパッケージ
```

### Source Code - Target Structure

```text
src/
├── cli/                  # CLIエントリーポイント
│   ├── __init__.py
│   ├── extract_frames.py # Step 1: 動画→フレーム
│   ├── deduplicate.py    # Step 2: 重複除去
│   ├── split_spreads.py  # Step 2.5: 見開き分割
│   ├── detect_layout.py  # Step 3: レイアウト検出
│   ├── run_ocr.py        # Step 4: OCR実行
│   └── consolidate.py    # Step 5: 統合
│
├── rover/                # OCR統合（名称統一）
│   ├── __init__.py
│   ├── engines.py        # エンジン抽象化
│   ├── ensemble.py       # アンサンブル処理
│   ├── alignment.py      # 文字アライメント
│   └── output.py         # 出力フォーマット
│
├── preprocessing/        # 前処理
│   ├── __init__.py
│   ├── frames.py         # フレーム抽出
│   ├── deduplicate.py    # 重複検出
│   ├── split_spread.py   # 見開き分割
│   └── hash.py           # ハッシュ計算
│
├── layout/               # レイアウト解析
│   ├── __init__.py
│   ├── detector.py       # 検出
│   ├── figures.py        # 図形検出
│   └── reading_order.py  # 読み順
│
├── book_converter/       # 既存（変更なし）
│
└── utils.py              # 共通ユーティリティ

tests/
├── unit/
├── integration/
└── contract/
```

**Structure Decision**: 機能別サブパッケージ構造を採用。`cli/`にエントリーポイント、`rover/`にOCR統合、`preprocessing/`に前処理、`layout/`にレイアウト解析を配置。

## Complexity Tracking

該当なし。Constitution違反の正当化が必要な項目はない。

## Pipeline Steps Mapping

| Step | Current | Target CLI | Target Module |
|------|---------|------------|---------------|
| 0 | video_hash.py | (内部処理) | preprocessing/hash.py |
| 1 | extract_frames.py | cli/extract_frames.py | preprocessing/frames.py |
| 2 | deduplicate.py | cli/deduplicate.py | preprocessing/deduplicate.py |
| 2.5 | split_spread.py | cli/split_spreads.py | preprocessing/split_spread.py |
| 3 | ocr_yomitoku.py (layout) | cli/detect_layout.py | layout/detector.py |
| 4 | ocr_rover.py | cli/run_ocr.py | rover/ensemble.py |
| 5 | consolidate.py | cli/consolidate.py | (既存流用) |

## Naming Unification

| Current Name | Target Name | Affected Files |
|--------------|-------------|----------------|
| yomitoku | rover | 9ファイル |
| rover-ocr | rover | 9ファイル |
| ocr_yomitoku.py | layout/detector.py | モジュール移動 |
| ocr_rover.py | rover/ensemble.py | モジュール移動 |

## Out of Scope

以下は別Issue（011-lint-file-split）で対応:
- ruff導入とpre-commit hook設定
- 600行超ファイルの分割（ocr_ensemble.py: 699行、ocr_engines.py: 613行）

## Fallback Code to Remove

Based on grep results, these fallback patterns need review:

1. `ocr_integrated.py:59` - ENGINE_PRIORITY["FALLBACK"]
2. `layout_ocr.py:99` - ocr_with_fallback()
3. `layout_ocr.py:258` - should_fallback()
4. `book_converter/parser.py:584` - "Legacy patterns below for backward compatibility"

Note: Some fallbacks are legitimate error handling (e.g., LLM failure → rule-based). Only remove backward compatibility fallbacks, not error recovery.
