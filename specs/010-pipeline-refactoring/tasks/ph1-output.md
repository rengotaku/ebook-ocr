# Phase 1 Output: Setup（現状分析）

**Date**: 2026-02-18
**Feature**: 010-pipeline-refactoring

## Summary

現在のコードベースを分析し、リファクタリングの準備を完了した。

## Current Structure Analysis

### T001: pipeline.py 分析

| 関数 | 役割 |
|------|------|
| `run_pipeline()` | メインパイプライン実行 |
| `load_config()` | 設定読み込み |
| `main()` | CLIエントリーポイント |

**パイプラインステップ**:
1. `extract_frames()` - フレーム抽出
2. `deduplicate_frames()` - 重複除去
3. `split_spread_pages()` - 見開き分割
4. `detect_layout_yomitoku()` - レイアウト検出
5. `run_rover_batch()` - OCR実行
6. `consolidate_rover_output()` - 統合

### T002-T007: 各スクリプト分析

| ファイル | 主要関数 | CLI対応 |
|----------|----------|---------|
| `extract_frames.py` | `extract_frames()` | あり |
| `deduplicate.py` | `deduplicate_frames()` | あり |
| `split_spread.py` | `split_spread_pages()`, `renumber_pages()` | あり |
| `ocr_yomitoku.py` | `detect_layout_yomitoku()`, `ocr_page_yomitoku()` | あり |
| `ocr_rover.py` | `run_rover_batch()`, `run_rover_ocr()` | あり |
| `consolidate.py` | `consolidate_rover_output()` | あり |

### T008: 既存テスト

```
tests/
├── test_cleanup.py
├── test_layout_ocr.py
├── test_ocr_ensemble.py
├── test_detect_figures.py
├── test_utils.py
├── test_deduplicate.py
├── test_split_spread.py
├── conftest.py
├── test_ocr_rover.py
├── test_ocr_alignment.py
├── test_ocr_integrated.py
├── test_ocr_preprocess.py
├── test_reading_order.py
├── test_ocr_engines.py
└── book_converter/
    ├── test_page_grouper.py
    ├── test_cli.py
    ├── test_schema_validation.py
    ├── test_xml_builder.py
    ├── test_analyzer.py
    ├── test_e2e.py
    ├── test_e2e_toc.py
    ├── test_transformer.py
    ├── test_integration.py
    ├── test_models.py
    └── test_parser.py
```

## T009: 「yomitoku」「rover-ocr」の使用箇所

### yomitoku 関連（主要ファイル）

| ファイル | 使用例 |
|----------|--------|
| `ocr_ensemble.py` | `_yomitoku_analyzer`, `ocr_yomitoku_engine()` |
| `ocr_integrated.py` | ENGINE_PRIORITY, `ocr_yomitoku_engine()` |
| `layout_ocr.py` | `ocr_page_yomitoku()`, `run_yomitoku_ocr()` |
| `ocr_rover.py` | ENGINE_WEIGHTS["yomitoku"], `yomitoku_device` |
| `ocr_engines.py` | `run_yomitoku_with_boxes()` |
| `pipeline.py` | `yomitoku_device`, `detect_layout_yomitoku()` |
| `ocr_yomitoku.py` | 全体がyomitoku関連 |
| `ocr_alignment.py` | weight設定 |

**リネーム対象**:
- 変数: `yomitoku_device` → `device`
- 関数名: 統一パターンへ移行
- コメント/docstring: 更新

## T010: 後方互換性フォールバックコード

### 除去対象（Category A: backward compatibility）

| ファイル | 行 | コード |
|----------|-----|--------|
| `book_converter/parser.py` | 584 | "Legacy patterns below for backward compatibility" |
| `book_converter/parser.py` | 597 | "Chapter pattern 2: ... - legacy" |

### リネーム対象（Category C: naming only）

| ファイル | 行 | 変更内容 |
|----------|-----|----------|
| `ocr_integrated.py` | 59 | `ENGINE_PRIORITY["FALLBACK"]` → `ENGINE_PRIORITY["DEFAULT"]` |

### 維持対象（Category B: error recovery）

以下はエラーリカバリ用のフォールバックで維持する:
- `layout_ocr.py:99` - `ocr_with_fallback()`: OCRエンジン連鎖
- `layout_ocr.py:258` - `should_fallback()`: 低カバレッジ検出
- `book_converter/toc_classifier.py:154,202` - LLM失敗時のフォールバック
- `book_converter/parser.py:516,1523,1696` - ルールベースフォールバック
- `book_converter/page_grouper.py:193,246` - パターンマッチングフォールバック

## T011: テスト状態

```
======================= 1191 passed, 6 skipped in 2.05s ========================
```

**結果**: 全テストパス

## Transformation Plan Summary

### CLI作成対象

| 新CLIスクリプト | 元ソース | 主要関数 |
|----------------|----------|----------|
| `cli/extract_frames.py` | `extract_frames.py` | `extract_frames()` |
| `cli/deduplicate.py` | `deduplicate.py` | `deduplicate_frames()` |
| `cli/split_spreads.py` | `split_spread.py` | `split_spread_pages()` |
| `cli/detect_layout.py` | `ocr_yomitoku.py` | `detect_layout_yomitoku()` |
| `cli/run_ocr.py` | `ocr_rover.py` | `run_rover_batch()` |
| `cli/consolidate.py` | `consolidate.py` | `consolidate_rover_output()` |

### パッケージ移動計画

```
src/
├── cli/                  # 新規作成
├── preprocessing/        # 新規作成（extract_frames, deduplicate, split_spread, video_hash）
├── layout/               # 新規作成（ocr_yomitoku のレイアウト部分、detect_figures, reading_order）
├── rover/                # 新規作成（ocr_rover, ocr_engines, ocr_alignment, ocr_output）
├── book_converter/       # 既存維持
└── utils.py              # 既存維持
```

## Ready for Phase 2

Phase 1完了。次フェーズ（Phase 2: US1 - CLIスクリプト分解）に進む準備完了。
