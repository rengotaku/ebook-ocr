# Research: Book Markdown to XML Standardization

**Date**: 2026-02-07
**Feature**: 002-book-md-structure

## 1. XMLライブラリ選択

### Decision
`xml.etree.ElementTree`（Python標準ライブラリ）を使用

### Rationale
- 外部依存なし（Constitution V. Simplicity 準拠）
- Python標準ライブラリで十分な機能を提供
- XMLの生成・整形・出力がシンプルに実装可能
- パフォーマンスは十分（100ページ/秒以上達成可能）

### Alternatives Considered

| ライブラリ | 利点 | 欠点 | 採否 |
|-----------|------|------|------|
| `xml.etree.ElementTree` | 標準、シンプル、軽量 | CDATA未対応 | ✅ 採用 |
| `lxml` | 高性能、XPath完全対応 | 外部依存、C拡張必要 | ❌ |
| `xml.dom.minidom` | DOM操作可能 | メモリ消費大、低速 | ❌ |
| `defusedxml` | セキュリティ重視 | 入力信頼可能なので不要 | ❌ |

### CDATA対応について
`ElementTree`はCDATAセクションを直接サポートしないが、本用途では不要:
- 本文テキストは通常のテキストノードで十分
- 特殊文字（`<`, `>`, `&`）は自動エスケープされる

---

## 2. Markdownパーサー設計

### Decision
正規表現ベースの軽量カスタムパーサーを実装

### Rationale
- 現在のbook.mdは標準Markdownではなく、独自フォーマット
  - ページマーカー: `--- Page N (file.png) ---`
  - 図コメント: `<!-- FIGURE: path -->`
  - ページメタデータ: `1 / 1` or `はじめに 1 / 3`
- 汎用Markdownパーサーでは対応困難な独自要素が多い
- 正規表現で必要な要素のみ抽出可能
- 外部依存なし（Constitution V. Simplicity 準拠）

### Parsing Patterns

```python
# ページマーカー
PAGE_PATTERN = r'^---\s*Page\s+(\d+)\s*\(([^)]+)\)\s*---$'

# 見出し（1-3階層）
HEADING_PATTERN = r'^(#{1,3})\s+(.+)$'

# 図コメント
FIGURE_PATTERN = r'<!--\s*FIGURE:\s*(.+?)\s*-->'

# ページメタデータ（章内ページ）
PAGE_META_PATTERN = r'^(?:(.+?)\s+)?(\d+)\s*/\s*(\d+)$'

# 段落（空行で区切られたテキストブロック）
PARAGRAPH_PATTERN = r'^(?!#|---|<!--|-)(.+)$'

# リスト項目
LIST_ITEM_PATTERN = r'^[-*]\s+(.+)$'
```

### Alternatives Considered

| パーサー | 利点 | 欠点 | 採否 |
|---------|------|------|------|
| カスタム正規表現 | 軽量、独自形式対応、依存なし | 複雑なMD未対応 | ✅ 採用 |
| `markdown-it-py` | 標準MD完全対応 | 独自要素非対応、依存追加 | ❌ |
| `mistune` | 高速、拡張可能 | 依存追加、オーバースペック | ❌ |
| `pandoc` | 多形式変換 | 外部バイナリ依存 | ❌ |

---

## 3. エラーハンドリング戦略

### Decision
警告出力して継続、エラー箇所はXMLコメントでマーク

### Rationale
- 100ページ中1-2ページのエラーで全体が失敗するのは非効率
- 人手で後から修正可能にするため、エラー箇所を明示
- 変換完了後に警告サマリーを表示し、問題箇所を把握可能

### Error Marking Format

```xml
<!-- ERROR: [ERROR_TYPE] - [詳細メッセージ] -->
```

### Error Types

| エラータイプ | 発生条件 | 対処 |
|-------------|---------|------|
| `PAGE_NUMBER_NOT_FOUND` | ページ番号抽出失敗 | `number=""`（空属性） |
| `HEADING_LEVEL_AMBIGUOUS` | 見出しレベル不明 | `level=""`（空属性） |
| `FIGURE_PATH_INVALID` | 図ファイルパス不正 | `<file></file>`（空要素） |
| `PAGE_META_PARSE_FAILED` | ページメタデータ解析失敗 | `type="unknown"` |
| `UNEXPECTED_FORMAT` | 予期しない形式 | 元テキストをコメントで保存 |

### Logging Strategy

```python
import logging

logger = logging.getLogger('book_converter')

# 変換中
logger.warning(f"Page {page_num}: {error_type} - {message}")

# 変換完了後のサマリー
logger.info(f"Conversion complete: {total_pages} pages, {error_count} errors")
if error_count > total_pages * 0.1:
    logger.warning(f"High error rate: {error_count}/{total_pages} ({error_rate:.1%})")
```

---

## 4. TTS読み上げ制御設計

### Decision
`readAloud`属性で3段階制御: `true`, `false`, `optional`

### Rationale
- `true`: 常に読み上げ（本文、見出し）
- `false`: 常にスキップ（ファイル名、メタデータ）
- `optional`: ユーザー設定に依存（図の説明）

### 属性配置

| 要素 | デフォルト | 説明 |
|-----|-----------|------|
| `<content>` | `true` | 本文は常に読み上げ |
| `<heading>` | `true` | 見出しは常に読み上げ |
| `<paragraph>` | `true` | 段落は常に読み上げ |
| `<list>` | `true` | リストは常に読み上げ |
| `<figure>` | `optional` | ユーザー設定で制御 |
| `<description>` | 親継承 | `<figure>`の設定を継承 |
| `<file>` | `false` | ファイル名は読まない |
| `<caption>` | `true` | 図のタイトルは読む |
| `<pageMetadata>` | `false` | メタデータは読まない |
| `<pageAnnouncement>` | `true` | ページ番号アナウンス |

---

## 5. パフォーマンス考慮

### Decision
ストリーミング処理（1ページずつ処理・出力）

### Rationale
- メモリ効率: 500ページの書籍でも全体をメモリに保持しない
- パフォーマンス目標: 100ページ/秒以上達成可能
- シンプル実装: 複雑なバッファリング不要

### Implementation Approach

```python
def convert(input_path: Path, output_path: Path) -> ConversionResult:
    """ストリーミング変換"""
    with open(output_path, 'w', encoding='utf-8') as out:
        out.write('<?xml version="1.0" encoding="UTF-8"?>\n<book>\n')

        for page in parse_pages(input_path):
            xml_element = transform_page(page)
            out.write(serialize_element(xml_element))
            out.write('\n')

        out.write('</book>\n')

    return ConversionResult(...)
```

---

## 6. テスト戦略

### Decision
pytest + fixtures によるTDD

### Rationale
- Constitution II. Test-First 準拠
- カバレッジ≥80%目標
- Red-Green-Refactor サイクル厳守

### Test Categories

| カテゴリ | 対象 | 優先度 |
|---------|------|--------|
| Unit | parser.py 各関数 | P0 |
| Unit | transformer.py 各関数 | P0 |
| Unit | xml_builder.py 各関数 | P0 |
| Integration | 1ページ変換 | P1 |
| Integration | 複数ページ変換 | P1 |
| Integration | エラーケース | P1 |
| E2E | CLI引数処理 | P2 |
| E2E | ファイル入出力 | P2 |

### Fixtures

```text
tests/book_converter/fixtures/
├── sample_book.md           # 完全なサンプル（5ページ）
├── expected_book.xml        # 期待されるXML出力
├── page_with_figure.md      # 図を含むページ
├── page_with_heading.md     # 複数階層見出し
├── page_with_list.md        # リスト含むページ
├── malformed_page.md        # エラーケース用
└── expected_errors.xml      # エラーマーキング期待値
```

---

## Summary

すべての技術選択がConstitution準拠であることを確認:

| 領域 | 選択 | Constitution準拠 |
|------|------|-----------------|
| XMLライブラリ | `xml.etree.ElementTree` | ✅ V. Simplicity |
| Markdownパーサー | カスタム正規表現 | ✅ V. Simplicity |
| エラー処理 | 警告継続 + コメントマーク | ✅ I. Pipeline-First |
| TTS制御 | `readAloud`属性 | ✅ IV. Immutability |
| パフォーマンス | ストリーミング処理 | ✅ V. YAGNI |
| テスト | pytest + fixtures | ✅ II. Test-First |
