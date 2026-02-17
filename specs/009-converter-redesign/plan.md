# Implementation Plan: Converter再設計

**Branch**: `009-converter-redesign` | **Date**: 2026-02-16 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/009-converter-redesign/spec.md`

## Summary

Converterモジュール（book_converter）を再設計し、以下を実現:
1. TOC階層構造の正確な反映（level 1-5対応）
2. chapter/heading タグの役割明確化（コンテナ vs 読み上げ専用）
3. paragraph の論理的分離（空行ベース、改行除去）
4. list/figure要素の適切な出力
5. ページ要素廃止 → XMLコメント化

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: xml.etree.ElementTree（標準ライブラリ）, re（正規表現）
**Storage**: ファイルベース（入力: book.md, 出力: book.xml, figures/）
**Testing**: pytest (Constitution準拠: カバレッジ ≥80%)
**Target Platform**: Linux (ローカル開発環境)
**Project Type**: single
**Performance Goals**: 1冊（数百ページ）を10秒以内に変換
**Constraints**: メモリ使用量 <500MB
**Scale/Scope**: 1冊ずつ処理、バッチ処理なし

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Gate | Status | Notes |
|------|--------|-------|
| Pipeline-First | ✅ PASS | 単一ステップ（MD→XML）として設計 |
| Test-First (NON-NEGOTIABLE) | ✅ PASS | TDD必須、pytestでカバレッジ≥80% |
| Ollama Integration | N/A | OCRは上流工程、converterは使用しない |
| Immutability | ✅ PASS | 既存models.pyはfrozen dataclass |
| Simplicity (YAGNI) | ✅ PASS | 要求機能のみ実装、過剰な抽象化なし |

## Project Structure

### Documentation (this feature)

```text
specs/009-converter-redesign/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── book_converter/       # 既存モジュール（リファクタリング対象）
│   ├── models.py         # データモデル（拡張）
│   ├── parser.py         # MDパーサー（リファクタリング）
│   ├── xml_builder.py    # XML生成（リファクタリング）
│   ├── cli.py            # CLIエントリポイント（拡張）
│   ├── config.py         # 設定管理
│   ├── analyzer.py       # 分析ユーティリティ
│   ├── transformer.py    # 変換ロジック
│   ├── toc_classifier.py # TOC分類
│   ├── page_grouper.py   # ページグループ化
│   └── errors.py         # エラー定義
└── ...

tests/
├── book_converter/       # 既存テスト（拡張）
│   ├── test_models.py
│   ├── test_parser.py
│   ├── test_xml_builder.py
│   └── ...
└── ...
```

**Structure Decision**: 既存の `src/book_converter/` モジュールをリファクタリング。新規ファイル追加は最小限に抑え、既存構造を維持。

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| なし | - | - |
