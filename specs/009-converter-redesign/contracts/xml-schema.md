# XML Output Schema: book_converter v2

**Version**: 2.0.0
**Date**: 2026-02-16

## ルート要素

```xml
<?xml version="1.0" encoding="UTF-8"?>
<book>
  <metadata>...</metadata>
  <toc>...</toc>
  <front-matter>...</front-matter>
  <chapter>...</chapter>
</book>
```

## 要素定義

### `<book>` (ルート)

| Child | Cardinality | Description |
|-------|-------------|-------------|
| `<metadata>` | 1 | 書籍メタデータ |
| `<toc>` | 0..1 | 目次 |
| `<front-matter>` | 0..1 | 前付け（TOC前のコンテンツ） |
| `<chapter>` | 0..* | 章（レベル1構造コンテナ） |

### `<metadata>`

```xml
<metadata>
  <title>書籍タイトル</title>
  <isbn>1234567890123</isbn>  <!-- optional -->
</metadata>
```

### `<toc>` (目次)

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| begin | string | No | 開始ページ番号 |
| end | string | No | 終了ページ番号 |

```xml
<toc begin="5" end="7">
  <entry level="1" number="1" title="Chapter Title" page="10" />
  <entry level="2" number="1" title="Episode Title" page="15" parent="1" />
</toc>
```

#### `<entry>` (目次エントリ)

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| level | int (1-5) | Yes | 階層レベル |
| number | string | No | エントリ番号 |
| title | string | Yes | タイトル |
| page | string | No | ページ番号 |
| parent | string | No | 親エントリ番号 |

### 構造コンテナ

#### `<chapter>` (レベル1)

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| number | string | No | 章番号 |
| title | string | Yes | 章タイトル（ナビゲーション用） |

```xml
<chapter number="1" title="Chapter Title">
  <heading readAloud="true">Chapter 1 Chapter Title</heading>
  <paragraph>...</paragraph>
  <section>...</section>
</chapter>
```

#### `<section>` (レベル2)

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| number | string | No | セクション番号 |
| title | string | Yes | セクションタイトル |

```xml
<section number="1" title="Episode Title">
  <heading readAloud="true">Episode 01 Episode Title</heading>
  <paragraph>...</paragraph>
</section>
```

#### `<subsection>` (レベル3-5)

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| level | int (3-5) | Yes | 階層レベル |
| number | string | No | サブセクション番号 |
| title | string | Yes | サブセクションタイトル |

### コンテンツ要素

#### `<heading>` (見出し)

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| readAloud | boolean | Yes | 読み上げ対象か |

```xml
<heading readAloud="true">Chapter 1 タイトル</heading>
```

#### `<paragraph>` (段落)

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| (none) | - | - | 属性なし |

```xml
<paragraph>段落テキスト。改行なしの連続テキスト。</paragraph>
```

**注意**: paragraph内に改行は含まれない。

#### `<list>` (リスト)

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| type | string | Yes | "unordered" or "ordered" |

```xml
<list type="unordered">
  <item>項目1</item>
  <item>項目2</item>
</list>
```

#### `<figure>` (図)

| Attribute | Type | Required | Description |
|-----------|------|----------|-------------|
| readAloud | boolean | Yes | 常に "false" |
| path | string | Yes | 画像ファイルパス |
| marker | string | No | 元のマーカーテキスト |

```xml
<figure readAloud="false" path="figures/fig001.png" marker="図1" />
```

### ページコメント

ページ情報はXMLコメントとして保持。

```xml
<!-- page 42 -->
```

## 完全なXML例

```xml
<?xml version="1.0" encoding="UTF-8"?>
<book>
  <metadata>
    <title>サンプル書籍</title>
    <isbn>1234567890123</isbn>
  </metadata>

  <toc begin="3" end="5">
    <entry level="1" number="1" title="はじめに" page="10" />
    <entry level="1" number="2" title="Chapter 1" page="15" />
    <entry level="2" number="1" title="Episode 01" page="20" parent="2" />
  </toc>

  <front-matter>
    <!-- page 1 -->
    <heading readAloud="true">まえがき</heading>
    <paragraph>前付けの段落テキスト。</paragraph>
  </front-matter>

  <chapter number="1" title="はじめに">
    <!-- page 10 -->
    <heading readAloud="true">Chapter 1 はじめに</heading>
    <paragraph>章の導入テキスト。</paragraph>

    <section number="1" title="Episode Title">
      <!-- page 20 -->
      <heading readAloud="true">Episode 01 Episode Title</heading>
      <paragraph>セクションの本文。</paragraph>

      <list type="unordered">
        <item>項目1</item>
        <item>項目2</item>
      </list>

      <figure readAloud="false" path="figures/fig001.png" marker="図1" />
    </section>
  </chapter>
</book>
```
