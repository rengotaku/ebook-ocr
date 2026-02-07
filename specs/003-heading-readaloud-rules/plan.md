# Implementation Plan: heading要素へのreadAloud属性付与ルール

**Branch**: `003-heading-readaloud-rules` | **Date**: 2026-02-08 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-heading-readaloud-rules/spec.md`

## Summary

繰り返し出現するheading要素（柱、ページ番号表記、装飾記号等）に`readAloud="false"`を自動付与し、TTS読み上げ対象から除外する。既存の`src/book_converter/transformer.py`を拡張し、heading要素の出現頻度分析とパターンマッチングによる属性付与ロジックを追加する。

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: xml.etree.ElementTree（標準ライブラリ）, re（正規表現）
**Storage**: 設定ファイル（パターン定義）はYAMLまたはJSON形式
**Testing**: pytest
**Target Platform**: Linux/macOS CLI
**Project Type**: Single project (既存のbook_converter拡張)
**Performance Goals**: 変換処理時間が現行比10%以内の増加
**Constraints**: 既存テストスイート100%パス、偽陽性1%未満
**Scale/Scope**: 書籍1冊あたり100-300ページ、heading要素は100-500件程度

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Evidence |
|-----------|--------|----------|
| I. Pipeline-First | ✅ PASS | 変換パイプラインの一部として実装、既存transformer.pyを拡張 |
| II. Test-First | ✅ PASS | TDD必須、tdd-generator → phase-executor フロー |
| III. Ollama Integration | N/A | 本機能はOllama不使用（パターンマッチングのみ） |
| IV. Immutability | ✅ PASS | 既存の frozen dataclass を維持、新規エンティティも不変 |
| V. Simplicity (YAGNI) | ✅ PASS | 最小限の拡張（analyzer.py新規 + transformer.py修正） |

**Technical Constraints Check**:
- [x] Python 3.13+
- [x] pytest for testing
- [x] Makefile targets
- [x] 1ファイル800行以下、1関数50行以下

## Project Structure

### Documentation (this feature)

```text
specs/003-heading-readaloud-rules/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (book.xsd拡張)
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/book_converter/
├── __init__.py
├── models.py            # 既存 + ExclusionPattern, HeadingAnalysis追加
├── parser.py            # 既存（変更なし）
├── transformer.py       # 既存 + readAloud属性付与ロジック追加
├── analyzer.py          # 新規: heading頻度分析、柱検出
├── cli.py               # 既存 + 設定ファイル読み込みオプション追加
└── config.py            # 新規: デフォルトパターン定義

tests/book_converter/
├── test_analyzer.py     # 新規: analyzer.pyのテスト
├── test_transformer.py  # 既存 + readAloud属性テスト追加
├── test_models.py       # 既存 + 新規モデルテスト
└── fixtures/
    └── heading_patterns.md  # 新規: パターンマッチング用テストデータ
```

**Structure Decision**: 既存のbook_converter構造を維持し、analyzer.pyとconfig.pyを新規追加。最小限の変更で機能を実現。

## Complexity Tracking

> 該当なし（Constitution違反なし）
