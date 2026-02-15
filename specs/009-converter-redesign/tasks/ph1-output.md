# Phase 1 Output: Setup（既存コード調査）

**Date**: 2026-02-16
**Branch**: 009-converter-redesign

## 完了タスク

- [x] T001 既存モデル確認
- [x] T002 既存パーサー確認
- [x] T003 既存トランスフォーマー確認
- [x] T004 既存XMLビルダー確認
- [x] T005 既存テスト確認

## 既存コード分析結果

### 1. models.py (282行)

| Entity | 現状 | 変更必要性 |
|--------|------|-----------|
| `TocEntry` | level: str ("chapter"/"section"/"subsection"/"other") | → level: int (1-5) |
| `Page` | 構造コンテナとして使用 | → 廃止、XMLコメント化 |
| `Heading` | level: int (1-3) | → level: int (1-5) |
| `Paragraph` | text: str (改行保持) | → 改行除去、連続テキスト化 |
| `Figure` | file, caption, description, read_aloud | → path, marker, read_aloud=false |
| `List` | items: tuple[str, ...] | → list_type追加 |
| `HeaderLevelConfig` | level1-5対応済み | そのまま使用可 |
| `Book` | pages: tuple[Page, ...] | → chapters: tuple[StructureContainer, ...] |

**追加が必要なモデル**:
- `StructureContainer` (新規): chapter/section等の構造コンテナ

### 2. parser.py (主要関数)

| 関数 | 現状 | 変更必要性 |
|------|------|-----------|
| `parse_toc_entry` | level="chapter" 等の文字列を返す | → level=int (1-5) を返す |
| `parse_paragraph` | `"\n".join(lines)` で改行保持 | → 改行除去、連続テキスト化 |
| `parse_heading` | level 4+ → 3 に統合 | → level 1-5 のまま保持 |
| `parse_list` | items tuple を返す | → list_type 判定追加 |
| `parse_figure` | file, caption, description | → path, marker 対応 |

**追加が必要な関数**:
- 空行検出ロジック（スペース/タブのみも空行扱い）
- 図プレースホルダー検出（[図], [写真], [表]等）

### 3. transformer.py (390行)

| 関数 | 現状 | 変更必要性 |
|------|------|-----------|
| `transform_toc_entry` | level="chapter" を出力 | → level="1" 等の数値文字列 |
| `transform_page` | `<page>` 要素を生成 | → 廃止 |
| `transform_content` | `<content>` ラッパー | → 廃止検討 |
| `transform_figure` | file, caption, description 子要素 | → path, marker 属性 |

**追加が必要な関数**:
- `transform_structure_container`: chapter/section変換
- ページコメント生成

### 4. xml_builder.py (142行)

| 関数 | 現状 | 変更必要性 |
|------|------|-----------|
| `build_xml` | pages ループで transform_page | → chapters ループに変更 |
| `build_xml_with_errors` | 同上 | → 同上 |

**追加が必要な機能**:
- ページコメント挿入 (`<!-- page N -->`)
- front-matter セクション生成

### 5. テスト現状

```
tests/book_converter/
├── test_models.py          # モデルテスト
├── test_parser.py          # パーサーテスト
├── test_transformer.py     # トランスフォーマーテスト
├── test_xml_builder.py     # XMLビルダーテスト
├── test_cli.py             # CLIテスト
├── test_analyzer.py        # 分析ユーティリティテスト
├── test_e2e.py             # E2Eテスト
├── test_e2e_toc.py         # TOC E2Eテスト
├── test_integration.py     # 統合テスト
├── test_page_grouper.py    # ページグループ化テスト
└── test_schema_validation.py # スキーマ検証テスト
```

**テスト実行結果**: 999 tests collected, all passed

## 変更影響分析

### 高影響ファイル
1. `models.py`: TocEntry.level数値化、StructureContainer追加、Figure拡張
2. `parser.py`: paragraph改行除去、TOC level数値化、figure検出追加
3. `transformer.py`: transform_page廃止、structure container変換追加
4. `xml_builder.py`: 構造コンテナベースの生成ロジック

### 低影響ファイル
1. `cli.py`: --figure-markers引数追加

### 後方互換性
- **破壊的変更**: XML出力形式が根本的に変わる
- 既存テストの多くはPage/Content構造に依存 → リファクタリング必要

## 実装方針

### User Story 1 (Phase 2)
- TocEntry.level を str → int に変更
- parse_toc_entry で level を int で返す
- transform_toc_entry で level を数値文字列で出力

### User Story 2 (Phase 3)
- StructureContainer dataclass 追加
- Book.pages → Book.chapters に変更
- transform_structure_container 関数追加
- ページコメント生成

### User Story 3 (Phase 4)
- parse_paragraph で改行除去
- 空行検出（スペースのみも含む）
- ページまたぎ段落結合

### User Story 4 (Phase 5)
- List.list_type 属性追加
- Figure を path, marker に変更
- 図プレースホルダー検出

## 次のステップ

Phase 2: User Story 1 - TOC階層構造の正確な反映（TDDフロー）
1. tdd-generator で REDテスト実装
2. phase-executor で GREEN実装
