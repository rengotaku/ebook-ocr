# Quickstart: TOC構造を利用したpageタグのグルーピング

**Date**: 2026-02-09
**Feature**: 005-toc-page-grouping

## 概要

book.xmlの`<page>`タグを`<chapter>`, `<section>`, `<subsection>`で階層化する機能。

## 使用方法

### CLI経由

```bash
# 基本的な使用方法
python -m src.book_converter.cli input.md --output output.xml --group-pages

# 既存のbook.xmlを階層化
python -m src.book_converter.page_grouper input_book.xml output_book.xml
```

### Pythonコード

```python
from src.book_converter.page_grouper import group_pages_by_toc

# XMLファイルを読み込んで階層化
grouped_xml = group_pages_by_toc("input_book.xml")
grouped_xml.write("output_book.xml", encoding="UTF-8", xml_declaration=True)

# または ElementTree を直接渡す
import xml.etree.ElementTree as ET
tree = ET.parse("input_book.xml")
grouped_tree = group_pages_by_toc(tree)
```

## 入力形式

```xml
<book>
  <toc begin="7" end="13">
    <entry level="chapter" number="1" title="SREとは" />
    <entry level="section" number="1.1" title="SREの概要" />
    ...
  </toc>
  <page number="1">...</page>
  <page number="2">...</page>
  ...
</book>
```

## 出力形式

```xml
<book>
  <toc>...</toc>

  <front-matter>
    <page number="1">...</page>
    ...
    <page number="13">...</page>
  </front-matter>

  <chapter number="1" title="SREとは">
    <page number="14" type="chapter-title">...</page>
    <section number="1.1" title="SREの概要">
      <page number="15">...</page>
      <subsection number="1.1.1" title="...">
        ...
      </subsection>
    </section>
  </chapter>
</book>
```

## 処理ルール

1. **前付け**: TOC終了ページ（`toc[@end]`）までのページは `<front-matter>` に配置
2. **セクション判定**: `pageMetadata` または `heading` からセクション番号を抽出
3. **章扉ページ**: 章の最初のページには `type="chapter-title"` 属性を付与
4. **フォールバック**: セクション番号が不明なページは直前のセクションに配置

## テスト実行

```bash
# 全テスト実行
make test

# page_grouperのみ
pytest tests/book_converter/test_page_grouper.py -v
```

## 依存関係

- Python 3.13+
- 標準ライブラリのみ（xml.etree.ElementTree, re）
