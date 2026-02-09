# Implementation Plan: TOC構造を利用したpageタグのグルーピング

**Branch**: `005-toc-page-grouping` | **Date**: 2026-02-09 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-toc-page-grouping/spec.md`

## Summary

book.xmlの`<toc>`タグに含まれる目次情報を利用して、フラットな`<page>`タグを`<chapter>`, `<section>`, `<subsection>`タグで階層的にグルーピングする。pageMetadataやheadingからセクション番号を抽出し、各ページを適切な階層に配置する。

## Technical Context

**Language/Version**: Python 3.13+ (Constitution準拠)
**Primary Dependencies**: xml.etree.ElementTree（標準ライブラリ）, re（正規表現）
**Storage**: ファイルベース（入力: book.xml, 出力: book.xml）
**Testing**: pytest (Constitution準拠)
**Target Platform**: Linux (ローカル開発環境)
**Project Type**: single (既存book_converterモジュールへの追加)
**Performance Goals**: 1000ページのbook.xmlを10秒以内に処理
**Constraints**: 標準ライブラリのみ使用（外部依存なし）
**Scale/Scope**: 単一のbook.xmlファイルを処理

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Pipeline-First | ✅ PASS | XML変換パイプラインのステップとして設計。入力: book.xml、出力: 階層化されたbook.xml |
| II. Test-First (NON-NEGOTIABLE) | ✅ PASS | TDD必須。pytest使用。テスト→実装→リファクタの順序を厳守 |
| III. Ollama Integration | ⬜ N/A | 本機能はOCR/VLM不使用。純粋なXML変換処理 |
| IV. Immutability & Side-Effect Isolation | ✅ PASS | 純粋関数で変換ロジックを実装。ファイルI/Oは境界に限定 |
| V. Simplicity (YAGNI) | ✅ PASS | 必要な機能のみ実装。標準ライブラリのみ使用 |

**Technical Constraints**:
- Python 3.13+ ✅
- 依存管理: requirements.txt + venv ✅ (新規依存なし)
- ビルド/テスト: Makefile ✅
- 画像処理: N/A (XML処理のみ)

## Project Structure

### Documentation (this feature)

```text
specs/005-toc-page-grouping/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── book_converter/
│   ├── __init__.py
│   ├── models.py          # 既存: データモデル
│   ├── parser.py          # 既存: book.md パーサー
│   ├── transformer.py     # 既存: 変換ロジック
│   ├── xml_builder.py     # 既存: XML出力
│   ├── cli.py             # 既存: CLI
│   └── page_grouper.py    # NEW: ページグルーピングモジュール
└── ...

tests/
├── book_converter/
│   ├── test_page_grouper.py  # NEW: グルーピングテスト
│   └── ...
└── ...
```

**Structure Decision**: 既存の`src/book_converter/`モジュールに`page_grouper.py`を追加。既存のパイプラインに統合可能な設計。

## Complexity Tracking

> 違反なし - Constitution Checkすべてパス
