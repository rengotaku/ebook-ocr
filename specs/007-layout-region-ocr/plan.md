# Implementation Plan: レイアウト検出に基づく領域別OCR

**Branch**: `007-layout-region-ocr` | **Date**: 2026-02-11 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/007-layout-region-ocr/spec.md`

## Summary

YOLOによるレイアウト検出を拡張（3クラス→9クラス）し、検出した領域毎に適切なOCRエンジン（DeepSeek-OCR/VLM）を選択して処理する。領域は読み順にソートされ、結合されて最終出力となる。検出失敗時は従来のページ全体OCRにフォールバックする。

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: doclayout-yolo, Pillow, requests, pyyaml
**Storage**: ファイルベース（layout.json, book.txt, book.md）
**Testing**: pytest, pytest-cov
**Target Platform**: Linux/macOS CLI
**Project Type**: Single（CLIパイプライン）
**Performance Goals**: ページあたり2-4秒（OCR込み）
**Constraints**: Ollama API依存、GPUなしでも動作
**Scale/Scope**: 書籍1冊（100-500ページ）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Evidence |
|------|--------|----------|
| I. Pipeline-First | ✅ Pass | 既存パイプラインのStep 3/4を拡張。各ステップは独立実行可能 |
| II. Test-First (NON-NEGOTIABLE) | ✅ Pass | TDD: RED→GREEN→Refactor サイクルで実装 |
| III. Ollama Integration | ✅ Pass | 既存のDeepSeek-OCR/VLMをそのまま使用 |
| IV. Immutability & Side-Effect Isolation | ✅ Pass | 領域ソート等は純粋関数で実装。ファイルI/Oは境界のみ |
| V. Simplicity (YAGNI) | ✅ Pass | 既存モジュールを拡張。新規モジュールは1つのみ |

## Project Structure

### Documentation (this feature)

```text
specs/007-layout-region-ocr/
├── spec.md              # 仕様書
├── plan.md              # このファイル
├── research.md          # Phase 0 出力
├── data-model.md        # Phase 1 出力
├── quickstart.md        # Phase 1 出力
└── tasks.md             # Phase 2 出力
```

### Source Code (repository root)

```text
src/
├── detect_figures.py    # 変更: LABEL_TYPE_MAP 拡張、regions 構造
├── ocr_deepseek.py      # 変更なし（再利用）
├── describe_figures.py  # 変更なし（再利用）
├── layout_ocr.py        # 新規: 領域別OCR dispatcher
├── reading_order.py     # 新規: 読み順ソートアルゴリズム
├── pipeline.py          # 変更: 新OCR戦略の統合
└── utils.py             # 変更: 領域クロップ関数追加

tests/
├── test_detect_figures.py  # 新規: 拡張検出テスト
├── test_layout_ocr.py      # 新規: 領域別OCRテスト
├── test_reading_order.py   # 新規: 読み順ソートテスト
└── fixtures/
    └── sample_pages/       # テスト用ページ画像
```

**Structure Decision**: 既存の単一プロジェクト構造を維持。新規モジュール2つ（`layout_ocr.py`, `reading_order.py`）を追加。

## Complexity Tracking

> 違反なし - 追加の正当化不要
