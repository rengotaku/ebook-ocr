# Implementation Plan: Book Markdown to XML Standardization

**Branch**: `002-book-md-structure` | **Date**: 2026-02-07 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/002-book-md-structure/spec.md`

## Summary

Markdown形式のbook.mdをTTS読み上げに最適化されたXML形式（book.xml）に変換するPythonスクリプトを開発する。主要機能:
- ページマーカー抽出とXML要素化
- 見出し階層（3階層まで）の構造化
- 図表メタデータの分離と`readAloud`属性による読み上げ制御
- エラー時は警告出力して継続、空要素/コメントでマーク

## Technical Context

**Language/Version**: Python 3.13+ (Constitution準拠)
**Primary Dependencies**:
- 標準ライブラリ: `re`, `xml.etree.ElementTree`, `pathlib`, `logging`
- 外部依存なし（Pillow/OpenCV は不要、テキスト処理のみ）
**Storage**: ファイルベース（入力: book.md, 出力: book.xml）
**Testing**: pytest (Constitution準拠: TDD必須, カバレッジ≥80%)
**Target Platform**: Linux (ローカル開発環境)
**Project Type**: Single project (CLIツール)
**Performance Goals**: 100ページ/秒以上の変換速度
**Constraints**:
- 1ファイル 800行以下、1関数 50行以下 (Constitution準拠)
- 純粋関数を優先、ファイルI/Oはパイプライン境界に限定
**Scale/Scope**: 1冊の書籍（100-500ページ想定）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Pipeline-First | ✅ PASS | Markdown入力 → XML出力のパイプライン構成 |
| II. Test-First (NON-NEGOTIABLE) | ✅ PASS | pytest使用、TDD厳守、カバレッジ≥80% |
| III. Ollama Integration | ⚠️ N/A | 本機能はテキスト変換のみ、LLM不要 |
| IV. Immutability | ✅ PASS | 純粋関数でMarkdown→XML変換、中間状態なし |
| V. Simplicity (YAGNI) | ✅ PASS | 要求された機能のみ実装、過剰な抽象化なし |

**Technical Constraints Check**:
- [x] Python 3.13+
- [x] venv + requirements.txt (pytest のみ追加)
- [x] Makefile によるビルド/テスト
- [x] 1ファイル 800行以下
- [x] 1関数 50行以下

## Project Structure

### Documentation (this feature)

```text
specs/002-book-md-structure/
├── spec.md              # Feature specification (completed)
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── contracts/           # Phase 1 output (XML schema)
│   └── book.xsd         # XML Schema Definition
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
src/
├── book_converter/           # 本機能のメインモジュール
│   ├── __init__.py
│   ├── parser.py             # Markdown解析
│   ├── transformer.py        # XML変換ロジック
│   ├── models.py             # データモデル (Page, Heading, Figure等)
│   ├── xml_builder.py        # XML生成
│   └── cli.py                # CLIエントリーポイント
├── models/                   # 既存モジュール（変更なし）
├── services/                 # 既存モジュール（変更なし）
└── lib/                      # 共有ユーティリティ

tests/
├── book_converter/           # 本機能のテスト
│   ├── test_parser.py        # パーサーユニットテスト
│   ├── test_transformer.py   # 変換ロジックテスト
│   ├── test_xml_builder.py   # XML生成テスト
│   ├── test_cli.py           # CLIテスト
│   └── fixtures/             # テスト用サンプルファイル
│       ├── sample_book.md    # サンプルMarkdown
│       └── expected_book.xml # 期待されるXML出力
├── integration/              # 統合テスト
│   └── test_full_conversion.py
└── unit/                     # 既存ユニットテスト

Makefile                      # ビルド/テストコマンド追加
```

**Structure Decision**: Single project構成。既存の`src/`ディレクトリに`book_converter/`サブモジュールを追加。CLIツールとして`python -m src.book_converter.cli input.md output.xml`で実行可能。

## Complexity Tracking

> Constitution Check に違反なし。Complexity Tracking 不要。

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| (なし) | - | - |

## Phase 0: Research Summary

→ 詳細は `research.md` を参照

### Key Decisions

1. **XMLライブラリ**: `xml.etree.ElementTree`（標準ライブラリ、外部依存なし）
2. **Markdownパーサー**: 正規表現ベースの軽量パーサー（外部依存なし、要件に特化）
3. **エラーハンドリング**: XMLコメント`<!-- ERROR: ... -->`でマーク、警告ログ出力
4. **TTS属性設計**: `readAloud="true|false|optional"`で読み上げ制御

## Phase 1: Design Artifacts

→ 詳細は以下のファイルを参照

- `data-model.md`: エンティティ定義（Page, Heading, Figure, Content, PageMetadata）
- `contracts/book.xsd`: XML Schema Definition
- `quickstart.md`: 開発者向けクイックスタートガイド

## Next Steps

1. `/speckit.tasks` で Phase 2 タスク生成
2. TDD サイクルで実装開始
3. Phase ごとにコミット
