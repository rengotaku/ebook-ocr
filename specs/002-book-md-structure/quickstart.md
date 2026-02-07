# Quickstart: Book Markdown to XML Converter

**Feature**: 002-book-md-structure
**Date**: 2026-02-07

## Prerequisites

- Python 3.13+
- venv (recommended)

## Setup

```bash
# venv作成（未作成の場合）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# 依存インストール
pip install -r requirements.txt
```

## Usage

### CLI

```bash
# 基本的な変換
python -m src.book_converter.cli input.md output.xml

# オプション指定
python -m src.book_converter.cli input.md output.xml --verbose
python -m src.book_converter.cli input.md output.xml --quiet
```

### Python API

```python
from src.book_converter import convert_book
from pathlib import Path

# 基本的な変換
result = convert_book(
    input_path=Path("input.md"),
    output_path=Path("output.xml")
)

# 結果確認
print(f"Total pages: {result.total_pages}")
print(f"Errors: {result.error_count}")

if result.errors:
    for error in result.errors:
        print(f"  {error.error_type}: {error.message}")
```

## Input Format (book.md)

```markdown
--- Page 1 (page_0001.png) ---

<!-- FIGURE: figures/page_0001_figure1.png -->
図の説明文...

# 書籍タイトル

1 / 1

--- Page 2 (page_0002.png) ---

## 第1章 概要

本文...

- リスト項目1
- リスト項目2

はじめに 1 / 3
```

## Output Format (book.xml)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<book>
  <metadata>
    <title>書籍タイトル</title>
    <conversionDate>2026-02-07</conversionDate>
  </metadata>

  <page number="1" sourceFile="page_0001.png">
    <pageAnnouncement format="simple">1ページ</pageAnnouncement>

    <figure readAloud="optional">
      <file>figures/page_0001_figure1.png</file>
      <description>図の説明文...</description>
    </figure>

    <content readAloud="true">
      <heading level="1">書籍タイトル</heading>
    </content>

    <pageMetadata type="chapter-page">1 / 1</pageMetadata>
  </page>

  <!-- ... more pages ... -->
</book>
```

## Testing

```bash
# 全テスト実行
make test

# カバレッジ付き
make test-cov

# 特定テストのみ
pytest tests/book_converter/test_parser.py -v
```

## Development

### TDD Workflow

```bash
# 1. テスト作成（RED）
# tests/book_converter/test_parser.py にテスト追加

# 2. テスト失敗確認
pytest tests/book_converter/test_parser.py -v

# 3. 実装（GREEN）
# src/book_converter/parser.py に実装

# 4. テスト成功確認
pytest tests/book_converter/test_parser.py -v

# 5. リファクタリング
# コード改善

# 6. 全テスト確認
make test
```

### Module Structure

```
src/book_converter/
├── __init__.py          # 公開API
├── parser.py            # Markdown解析
├── transformer.py       # Page → XML変換
├── models.py            # データモデル
├── xml_builder.py       # XML生成
└── cli.py               # CLIエントリーポイント
```

### Key Functions

```python
# parser.py
def parse_pages(input_path: Path) -> Iterator[Page]:
    """Markdownをページ単位でパース"""

def parse_page_marker(line: str) -> tuple[str, str] | None:
    """ページマーカーを解析"""

def parse_heading(line: str) -> Heading | None:
    """見出しを解析"""

# transformer.py
def transform_page(page: Page) -> Element:
    """PageをXML Elementに変換"""

# xml_builder.py
def build_xml(book: Book) -> str:
    """BookをXML文字列に変換"""

# cli.py
def main() -> int:
    """CLIエントリーポイント"""
```

## Error Handling

変換中にエラーが発生した場合:

1. 警告ログを出力
2. エラー箇所をXMLコメントでマーク
3. 変換を継続
4. 最後にエラーサマリーを表示

```xml
<!-- ERROR: PAGE_NUMBER_NOT_FOUND - ページ番号を抽出できませんでした -->
<page number="" sourceFile="page_0010.png">
  ...
</page>
```

## Makefile Targets

```makefile
# 追加予定のターゲット
test-book-converter:
	pytest tests/book_converter/ -v

convert-sample:
	python -m src.book_converter.cli samples/book.md output/book.xml
```

## Next Steps

1. `/speckit.tasks` でタスク生成
2. TDDサイクルで実装
3. Phaseごとにコミット
