# book.xml Schema Reference

**Version**: 2.1.0
**Last Updated**: 2026-03-25

book.xml は ebook-ocr パイプラインの最終出力であり、text-reading-with-llm の入力として使用される。

## スキーマ検証

```bash
# XSD によるプログラム的検証
make validate-xml HASHDIR=output/<hash>
```

XSD 定義: [`docs/book.xsd`](book.xsd)

## 出力形式

| 形式 | フラグ | 説明 |
|------|--------|------|
| Legacy (page-based) | なし（デフォルト） | フラットなページ構造 |
| Modern (chapter-based) | `--group-pages` | 章・セクションの階層構造 |

現在のパイプライン (`make run`) は `--group-pages` を使用し、Modern 形式を出力する。

## ルート構造

```xml
<?xml version="1.0" encoding="UTF-8"?>
<book>
  <metadata>...</metadata>
  <toc>...</toc>              <!-- optional -->
  <front-matter>...</front-matter>  <!-- optional, Modern のみ -->
  <chapter>...</chapter>      <!-- Modern 形式 -->
  <page>...</page>            <!-- Legacy 形式 -->
</book>
```

## 要素定義

### `<metadata>`

```xml
<metadata>
  <title>書籍タイトル</title>
  <isbn>1234567890123</isbn>              <!-- optional -->
  <sourceFormat>markdown</sourceFormat>   <!-- optional -->
  <conversionDate>2026-03-25</conversionDate>  <!-- optional -->
</metadata>
```

### `<toc>` (目次)

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| begin | string | No | TOC 開始ページ番号 |
| end | string | No | TOC 終了ページ番号 |

#### `<entry>`

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| level | positiveInteger | Yes | 階層レベル (1-5) |
| number | string | No | エントリ番号 |
| title | string | Yes | タイトル |
| page | string | No | ページ番号 |

---

## Modern 形式 (chapter-based)

### `<front-matter>`

TOC より前のコンテンツ。子要素: heading, paragraph, list, figure, code。

### `<chapter>`

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| number | string | No | 章番号 |
| title | string | Yes | 章タイトル |

子要素: heading, paragraph, list, figure, code, section。

### `<section>`

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| number | string | No | セクション番号 |
| title | string | Yes | セクションタイトル |

子要素: heading, paragraph, list, figure, code。

---

## Legacy 形式 (page-based)

### `<page>`

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| number | string | Yes | ページ番号 |
| sourceFile | string | Yes | ソース画像ファイル名 |
| continued | string | No | 前ページからの継続 |
| type | string | No | "normal", "cover", "colophon", "toc" |

子要素: pageAnnouncement, figure, content, pageMetadata。

---

## コンテンツ要素 (共通)

### `<heading>`

| Attribute | Type | Description |
|-----------|------|-------------|
| level | positiveInteger | 見出しレベル (Legacy のみ) |
| readAloud | string | 読み上げ対象か |

テキスト内の `**太字**` は `<em>太字</em>` に変換される。

### `<paragraph>`

| Attribute | Type | Description |
|-----------|------|-------------|
| readAloud | string | "false" のみ出力 (skip 区間) |

### `<list>`

| Attribute | Type | Description |
|-----------|------|-------------|
| readAloud | string | "false" のみ出力 |
| type | string | "unordered" or "ordered" |

### `<code>`

| Attribute | Type | Description |
|-----------|------|-------------|
| readAloud | string | 常に "false" |
| language | string | 言語ヒント |

### `<figure>`

Modern (self-closing): `path` (required), `caption`, `marker` 属性。
Legacy (子要素あり): `file`, `caption`, `description` 子要素。

### `<em>`

heading, paragraph, item 内のインライン強調要素。
