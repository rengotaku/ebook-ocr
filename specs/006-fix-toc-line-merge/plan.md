# Implementation Plan: TOC解析改行結合とページ欠損修正

**Branch**: `006-fix-toc-line-merge` | **Date**: 2026-02-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/006-fix-toc-line-merge/spec.md`

## Summary

TOCセクション内で改行によって分割されたエントリ（Chapter、Episode、Column）を正しく結合し、page_grouperでのページ欠損を防止する。50%以上のページ欠損時にはエラーを報告する機能を追加。

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: xml.etree.ElementTree（標準ライブラリ）, re（正規表現）
**Storage**: ファイルベース（入力: book.md, 出力: book.xml）
**Testing**: pytest
**Target Platform**: Linux/macOS CLI
**Project Type**: single
**Performance Goals**: 数百ページの書籍を数秒で処理
**Constraints**: 既存の正常動作を壊さない（回帰なし）
**Scale/Scope**: 1ファイル単位の処理

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Pipeline-First | ✅ PASS | parser.py → xml_builder.py → page_grouper.py の既存パイプラインに沿う |
| II. Test-First (NON-NEGOTIABLE) | ✅ PASS | TDDで実装、pytest使用 |
| III. Ollama Integration | N/A | 今回の機能にOllamaは不要 |
| IV. Immutability & Side-Effect Isolation | ✅ PASS | parse_toc_entry等は純粋関数として実装 |
| V. Simplicity (YAGNI) | ✅ PASS | 要求された機能のみ実装 |

## Project Structure

### Documentation (this feature)

```text
specs/006-fix-toc-line-merge/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/
└── book_converter/
    ├── parser.py        # 修正対象: merge_toc_lines(), parse_toc_entry()拡張
    ├── page_grouper.py  # 修正対象: ページ欠損防止、エラー検出
    ├── models.py        # 既存: TocEntry, Page
    └── ...

tests/
└── book_converter/
    ├── test_parser.py        # テスト追加対象
    ├── test_page_grouper.py  # テスト追加対象
    └── fixtures/             # テストデータ追加
```

**Structure Decision**: 既存の`src/book_converter/`構造を維持。新規ファイル作成なし、既存ファイルへの機能追加のみ。

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| なし | - | - |
