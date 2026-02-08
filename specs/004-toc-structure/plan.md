# Implementation Plan: 目次情報の保持

**Branch**: `004-toc-structure` | **Date**: 2026-02-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/004-toc-structure/spec.md`

## Summary

book.mdにマーカー（`<!-- toc -->`, `<!-- content -->`, `<!-- skip -->`）を追加することで、目次の構造化と読み上げ範囲制御を実現する。既存のbook_converterモジュールを拡張し、parser.py、models.py、transformer.pyに機能を追加する。

## Technical Context

**Language/Version**: Python 3.13+ (Constitution準拠)
**Primary Dependencies**: xml.etree.ElementTree（標準ライブラリ）, re（正規表現）
**Storage**: ファイルベース（入力: book.md, 出力: book.xml）
**Testing**: pytest (Constitution準拠)
**Target Platform**: Linux server（既存パイプラインと同じ）
**Project Type**: single（既存のsrc/book_converter/構造を拡張）
**Performance Goals**: N/A（バッチ処理、パフォーマンス要件なし）
**Constraints**: 既存のbook_converterモジュールを拡張、後方互換性維持
**Scale/Scope**: 単一書籍（数百ページ）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Pipeline-First | ✅ PASS | book.md → book.xml パイプラインの一部として設計 |
| II. Test-First | ✅ PASS | TDD必須、RED→GREEN→Refactorサイクル |
| III. Ollama Integration | N/A | 本機能はOllama不要（テキスト処理のみ） |
| IV. Immutability | ✅ PASS | 純粋関数、frozen dataclass使用 |
| V. Simplicity | ✅ PASS | 既存モジュール拡張のみ、新規抽象化なし |

**GATE RESULT**: ✅ ALL PASSED

## Project Structure

### Documentation (this feature)

```text
specs/004-toc-structure/
├── plan.md              # This file
├── spec.md              # Feature specification
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── book.xsd         # Updated XML schema
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── book_converter/
│   ├── models.py        # [MODIFY] Add TableOfContents, TocEntry, MarkerContext
│   ├── parser.py        # [MODIFY] Add marker parsing, TOC entry parsing
│   ├── transformer.py   # [MODIFY] Add tableOfContents transformation
│   └── xml_builder.py   # [NO CHANGE]
└── ...

tests/
├── book_converter/
│   ├── test_parser.py       # [MODIFY] Add marker/TOC parsing tests
│   ├── test_transformer.py  # [MODIFY] Add TOC transformation tests
│   └── test_integration.py  # [MODIFY] Add E2E tests with markers
└── ...
```

**Structure Decision**: 既存のsrc/book_converter/構造を拡張。新規ファイル作成は不要。

## Complexity Tracking

> No violations requiring justification.

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (none)    | -          | -                                   |
