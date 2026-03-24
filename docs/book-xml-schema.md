# book.xml Schema Reference

**Version**: 2.1.0
**Last Updated**: 2026-03-24

book.xml は ebook-ocr パイプラインの最終出力であり、text-reading-with-llm の入力として使用される。

## 出力形式

2つの形式をサポート:

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
  <toc>...</toc>           <!-- optional -->

  <!-- Modern 形式 -->
  <front-matter>...</front-matter>  <!-- optional -->
  <chapter>...</chapter>

  <!-- Legacy 形式 -->
  <page>...</page>
</book>
```

## 要素定義

### `<metadata>`

```xml
<metadata>
  <title>書籍タイトル</title>
  <isbn>1234567890123</isbn>        <!-- optional -->
  <sourceFormat>markdown</sourceFormat>
  <conversionDate>2026-03-24</conversionDate>  <!-- optional, ISO 8601 -->
</metadata>
```

### `<toc>` (目次)

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| begin | string | No | TOC 開始ページ番号 |
| end | string | No | TOC 終了ページ番号 |

```xml
<toc begin="5" end="7">
  <entry level="1" number="1" title="はじめに" page="10" />
  <entry level="2" number="1" title="概要" page="15" />
</toc>
```

#### `<entry>`

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| level | int (1-5) | Yes | 階層レベル |
| number | string | No | エントリ番号 (e.g., "1", "2.1") |
| title | string | Yes | タイトル |
| page | string | No | ページ番号 |

---

## Modern 形式 (chapter-based)

### `<chapter>`

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| number | string | No | 章番号 |
| title | string | Yes | 章タイトル |

```xml
<chapter number="1" title="はじめに">
  <!-- page 10 -->
  <heading readAloud="true">Chapter 1 はじめに</heading>
  <paragraph>導入テキスト。</paragraph>
  <section number="1" title="概要">...</section>
</chapter>
```

### `<section>`

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| number | string | No | セクション番号 |
| title | string | Yes | セクションタイトル |

```xml
<section number="1" title="概要">
  <!-- page 15 -->
  <heading readAloud="true">1.1 概要</heading>
  <paragraph>セクション本文。</paragraph>
</section>
```

### `<front-matter>`

TOC より前のコンテンツ。子要素はコンテンツ要素と同じ。

---

## Legacy 形式 (page-based)

### `<page>`

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| number | string | Yes | ページ番号 |
| sourceFile | string | Yes | ソース画像ファイル名 |
| continued | boolean | No | 前ページからの継続 |
| type | string | No | "normal", "cover", "colophon", "toc" |

```xml
<page number="1" sourceFile="page_0001.png">
  <pageAnnouncement format="simple">1ページ</pageAnnouncement>
  <figure readAloud="optional">
    <file>figures/page_0001_figure1.png</file>
    <description>表紙の画像</description>
  </figure>
  <content readAloud="true">
    <heading level="1">サンプル書籍タイトル</heading>
    <paragraph>本文テキスト。</paragraph>
  </content>
  <pageMetadata type="chapter-page">はじめに 1 / 3</pageMetadata>
</page>
```

#### `<pageAnnouncement>`

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| format | string | "simple" | フォーマット種類 |

#### `<content>`

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| readAloud | boolean | Yes | 読み上げ対象か |

#### `<pageMetadata>`

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| type | string | "chapter-page" | "chapter-page", "section-page", "unknown" |

---

## コンテンツ要素 (共通)

### `<heading>`

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| level | int (1-3) | Legacy のみ | 見出しレベル (Modern では省略) |
| readAloud | boolean | Modern のみ | 読み上げ対象か |

```xml
<!-- Legacy -->
<heading level="2">第1章 はじめに</heading>

<!-- Modern -->
<heading readAloud="true">Chapter 1 はじめに</heading>
```

**注意**: 4 階層以上の見出しは level=3 に統合され、エラーコメントが挿入される。

### `<paragraph>`

```xml
<paragraph>段落テキスト。改行を含む場合がある。</paragraph>
```

テキスト内の `**太字**` は `<em>太字</em>` に変換される。

### `<list>`

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| type | string | Modern のみ | "unordered" or "ordered" |

```xml
<list type="unordered">
  <item>項目1</item>
  <item>項目2</item>
</list>
```

### `<code>`

| Attribute | Type | Default | Description |
|-----------|------|---------|-------------|
| readAloud | boolean | "false" | 常に false |
| language | string | "" | 言語ヒント |

```xml
<code readAloud="false" language="python">print("hello")</code>
```

### `<figure>`

Modern 形式 (self-closing):

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| path | string | Yes | 画像ファイルパス |
| caption | string | No | キャプション |
| marker | string | No | 元のマーカーテキスト (e.g., "図1") |

```xml
<figure readAloud="false" path="figures/fig001.png" marker="図1" />
```

Legacy 形式 (子要素あり):

```xml
<figure readAloud="optional">
  <file>figures/page_0001_figure1.png</file>
  <caption readAloud="true">図の説明</caption>
  <description>詳細な説明</description>
</figure>
```

### `<em>` (強調)

heading, paragraph, item 内のインライン要素:

```xml
<paragraph>通常テキスト<em>強調テキスト</em>続きのテキスト。</paragraph>
```

---

## エラーコメント

変換エラーは XML コメントとして埋め込まれる:

```xml
<!-- ERROR: HEADING_LEVEL_EXCEEDED - 4階層以上の見出しは level=3 に統合されました -->
```

## ページコメント

Modern 形式では、ページ境界が XML コメントで記録される:

```xml
<!-- page 42 -->
```

## 完全な XML 例 (Modern)

```xml
<?xml version="1.0" encoding="UTF-8"?>
<book>
  <metadata>
    <title>サンプル書籍</title>
    <sourceFormat>markdown</sourceFormat>
  </metadata>

  <toc begin="3" end="5">
    <entry level="1" number="1" title="はじめに" page="10" />
    <entry level="2" number="1" title="概要" page="15" />
  </toc>

  <front-matter>
    <!-- page 1 -->
    <heading readAloud="true">まえがき</heading>
    <paragraph>前付けテキスト。</paragraph>
  </front-matter>

  <chapter number="1" title="はじめに">
    <!-- page 10 -->
    <heading readAloud="true">Chapter 1 はじめに</heading>
    <paragraph>導入テキスト。</paragraph>

    <section number="1" title="概要">
      <!-- page 15 -->
      <heading readAloud="true">1.1 概要</heading>
      <paragraph>本文テキスト。</paragraph>

      <list type="unordered">
        <item>項目1</item>
        <item>項目2</item>
      </list>

      <figure readAloud="false" path="figures/fig001.png" marker="図1" />
    </section>
  </chapter>
</book>
```
