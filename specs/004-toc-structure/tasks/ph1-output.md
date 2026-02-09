# Phase 1 Output: Setup (既存コード調査)

**Date**: 2026-02-08
**Status**: COMPLETE

## 1. 既存モデル実装 (src/book_converter/models.py)

### 確認済みエンティティ

| Entity | Type | 属性 |
|--------|------|------|
| BookMetadata | dataclass(frozen=True) | title, isbn, source_format, conversion_date |
| PageAnnouncement | dataclass(frozen=True) | text, format |
| Heading | dataclass(frozen=True) | level, text, read_aloud=True |
| Paragraph | dataclass(frozen=True) | text, read_aloud=True |
| List | dataclass(frozen=True) | items (tuple), read_aloud=True |
| Content | dataclass(frozen=True) | elements (tuple), read_aloud=True |
| Figure | dataclass(frozen=True) | file, caption, description, read_aloud, continued |
| PageMetadata | dataclass(frozen=True) | text, meta_type, section_name, current, total |
| Page | dataclass(frozen=True) | number, source_file, content, announcement, figures, metadata, continued, page_type |
| Book | dataclass(frozen=True) | metadata, pages |
| ConversionError | dataclass(frozen=True) | error_type, message, page_number, line_number |
| ConversionResult | dataclass(frozen=True) | success, total_pages, error_count, errors, output_path |

### 追加必要エンティティ (data-model.md参照)

- `TocEntry`: 目次エントリ
- `TableOfContents`: 目次全体
- `MarkerType`: マーカー種別列挙

### 既存のread_aloudデフォルト

| Entity | デフォルト値 |
|--------|-------------|
| Heading | True |
| Paragraph | True |
| List | True |
| Content | True |
| Figure | "optional" |

**重要**: Phase 4でContent.read_aloudのデフォルトをFalseに変更予定

## 2. 既存パーサー実装 (src/book_converter/parser.py)

### 確認済み関数

| 関数 | 目的 | 戻り値 |
|-----|------|-------|
| parse_page_marker | ページマーカー検出 | (page_number, source_file) \| None |
| extract_page_number | ページ番号抽出 | (page_number, source_file) |
| create_page_announcement | アナウンス生成 | PageAnnouncement \| None |
| parse_heading | 見出し解析 | Heading \| None |
| parse_heading_with_warning | 見出し警告付き | (Heading, warning) |
| parse_paragraph | 段落解析 | Paragraph \| None |
| parse_list | リスト解析 | List \| None |
| parse_figure_comment | 図コメント解析 | str \| None |
| parse_figure | 図解析 | Figure \| None |
| parse_page_metadata | メタデータ解析 | PageMetadata \| None |
| parse_pages | ページイテレータ | Iterator[Page] |
| parse_pages_with_errors | エラー付きパース | (pages, errors) |
| _parse_single_page_content | 単一ページ解析 | (Page, errors) |

### 追加必要関数

- `parse_toc_marker`: 目次マーカー検出 (`<!-- toc -->`, `<!-- /toc -->`)
- `parse_toc_entry`: 目次エントリ解析 (章・節・項パターン)
- `parse_content_marker`: コンテンツマーカー検出 (`<!-- content -->`, `<!-- skip -->`)

### 既存パターン参考

```python
# parse_figure_comment のパターン (大文字小文字不区別)
pattern = r"<!--\s*[Ff][Ii][Gg][Uu][Rr][Ee]:\s*(.+?)\s*-->"
```

## 3. 既存トランスフォーマー実装 (src/book_converter/transformer.py)

### 確認済み関数

| 関数 | 目的 | 戻り値 |
|-----|------|-------|
| apply_emphasis | 強調変換 | void (parent変更) |
| transform_page | ページ変換 | Element |
| transform_content | コンテンツ変換 | Element \| None |
| transform_page_announcement | アナウンス変換 | Element \| None |
| transform_heading | 見出し変換 | Element |
| transform_content_with_continued | 継続付きコンテンツ | Element \| None |
| transform_figure | 図変換 | Element |
| transform_page_metadata | メタデータ変換 | Element \| None |

### 追加必要関数

- `transform_toc_entry`: 目次エントリ変換
- `transform_table_of_contents`: 目次全体変換

### 既存パターン参考

```python
# Element生成パターン
elem = Element("tag_name")
elem.set("attribute", value)
child = SubElement(elem, "child_tag")
```

## 4. 既存テスト (tests/book_converter/)

### test_parser.py

- TestParsePageMarker: ページマーカーテスト
- TestExtractPageNumber: ページ番号抽出テスト
- TestCreatePageAnnouncement: アナウンステスト
- TestParseHeading: 見出しテスト
- TestParseHeadingLevel4Warning: 深い見出し警告テスト
- TestParseParagraph: 段落テスト
- TestParseList: リストテスト
- TestParseFigureComment: 図コメントテスト
- TestParseFigureDescription: 図説明テスト
- TestParsePageMetadata: メタデータテスト
- TestErrorHandling*: エラーハンドリングテスト

### test_transformer.py

- TestTransformPage: ページ変換テスト
- TestTransformPageAnnouncement: アナウンス変換テスト
- TestPageXMLStructure: XML構造テスト
- TestTransformHeading: 見出し変換テスト
- TestTransformContent: コンテンツ変換テスト
- TestTransformContentContinued: 継続属性テスト
- TestTransformFigure: 図変換テスト
- TestTransformPageMetadata: メタデータ変換テスト
- TestReadAloudInheritance: readAloud継承テスト
- TestEmphasisConversion: 強調変換テスト

### test_integration.py

- TestMarkdownToXMLConversion: 変換統合テスト
- TestXPathQuery: XPathクエリテスト
- TestTTSAnnouncement: アナウンステスト
- TestXMLStructure: XML構造テスト
- TestEdgeCases: エッジケーステスト

## 5. 新規XSDスキーマ (specs/004-toc-structure/contracts/book.xsd)

### 新規追加要素

- `tableOfContents`: readAloud属性付き
- `entry`: level, number, title, page属性
- `tocLevelEnum`: chapter, section, subsection, other

### content要素の変更

- readAloudデフォルト: `default="false"` (既存はtrue)

## 6. テスト結果

```
292 passed in 0.46s
```

全既存テストがパス。

## 7. 実装方針

### Phase 2 (US1+US2) で実装

1. **models.py**
   - TocEntry, TableOfContents, MarkerType 追加
   - 既存エンティティは変更なし

2. **parser.py**
   - parse_toc_marker() 追加
   - parse_toc_entry() 追加
   - _parse_single_page_content() 拡張（目次収集ロジック）

3. **transformer.py**
   - transform_toc_entry() 追加
   - transform_table_of_contents() 追加

### Phase 3 (US3) で実装

- tableOfContents に readAloud="false" 属性追加

### Phase 4 (US4) で実装

1. **parser.py**
   - parse_content_marker() 追加
   - マーカー状態スタック管理

2. **models.py**
   - Content.read_aloud デフォルトを False に変更

3. **transformer.py**
   - readAloud 属性の出力
