# Quickstart: 目次情報の保持

**Date**: 2026-02-08
**Feature**: 004-toc-structure

## 概要

book.mdにマーカーを追加することで、目次の構造化と読み上げ範囲の制御を実現します。

## マーカー一覧

| マーカー | 用途 | readAloud |
|---------|------|-----------|
| `<!-- toc -->` ... `<!-- /toc -->` | 目次範囲 | false |
| `<!-- content -->` ... `<!-- /content -->` | 読み上げ対象範囲 | true |
| `<!-- skip -->` ... `<!-- /skip -->` | 読み上げ非対象範囲 | false |
| (マーカーなし) | デフォルト | false |

## 使用例

### 入力: book.md

```markdown
--- Page 1 (page_0001.png) ---
表紙

--- Page 2 (page_0002.png) ---
<!-- toc -->
第1章 SREとは ............... 15
1.1 SREの定義 ............... 16
1.1.1 歴史 ............... 17
第2章 信頼性の定義 ............... 25
おわりに ............... 100
<!-- /toc -->

--- Page 3 (page_0003.png) ---
<!-- content -->
# 第1章 SREとは

SREはGoogleが提唱したプラクティスです。
<!-- /content -->

--- Page 100 (page_0100.png) ---
<!-- skip -->
索引
あ行: 15, 23, 45
い行: 12, 34, 56
<!-- /skip -->
```

### 出力: book.xml

```xml
<?xml version="1.0" encoding="UTF-8"?>
<book>
  <metadata>
    <title>SREの知識地図</title>
  </metadata>

  <tableOfContents readAloud="false">
    <entry level="chapter" number="1" title="SREとは" page="15"/>
    <entry level="section" number="1.1" title="SREの定義" page="16"/>
    <entry level="subsection" number="1.1.1" title="歴史" page="17"/>
    <entry level="chapter" number="2" title="信頼性の定義" page="25"/>
    <entry level="other" title="おわりに" page="100"/>
  </tableOfContents>

  <page number="1" sourceFile="page_0001.png">
    <pageAnnouncement format="simple" readAloud="false">1ページ</pageAnnouncement>
    <content readAloud="false">
      <paragraph>表紙</paragraph>
    </content>
  </page>

  <page number="2" sourceFile="page_0002.png" type="toc">
    <pageAnnouncement format="simple" readAloud="false">2ページ</pageAnnouncement>
    <tableOfContents readAloud="false">
      <!-- エントリは上記と同じ -->
    </tableOfContents>
    <content readAloud="false">
      <!-- 目次テキストは構造化されたためcontentは空または省略 -->
    </content>
  </page>

  <page number="3" sourceFile="page_0003.png">
    <pageAnnouncement format="simple" readAloud="false">3ページ</pageAnnouncement>
    <content readAloud="true">
      <heading level="1" readAloud="true">第1章 SREとは</heading>
      <paragraph readAloud="true">SREはGoogleが提唱したプラクティスです。</paragraph>
    </content>
  </page>

  <page number="100" sourceFile="page_0100.png">
    <pageAnnouncement format="simple" readAloud="false">100ページ</pageAnnouncement>
    <content readAloud="false">
      <paragraph readAloud="false">索引</paragraph>
      <paragraph readAloud="false">あ行: 15, 23, 45</paragraph>
      <paragraph readAloud="false">い行: 12, 34, 56</paragraph>
    </content>
  </page>
</book>
```

## 目次エントリのパターン

### 自動認識されるパターン

| 入力テキスト | level | number | title | page |
|-------------|-------|--------|-------|------|
| `第1章 SREとは ... 15` | chapter | 1 | SREとは | 15 |
| `1.1 SREの定義 ... 16` | section | 1.1 | SREの定義 | 16 |
| `1.1.1 歴史 ... 17` | subsection | 1.1.1 | 歴史 | 17 |
| `はじめに ... 1` | other | (空) | はじめに | 1 |
| `おわりに` | other | (空) | おわりに | (空) |

### ページ番号の抽出パターン

以下のパターンでページ番号を抽出します：

```
タイトル ... 15        # ドットリーダー
タイトル ─── 15       # 罫線
タイトル     15        # 空白（3文字以上）
```

## コマンド

```bash
# book.mdからbook.xmlを生成
make converter INPUT_MD=output/xxx/book.md OUTPUT_XML=output/xxx/book.xml

# または直接実行
python -m src.book_converter.cli output/xxx/book.md output/xxx/book.xml
```

## 運用フロー

1. パイプライン実行で `book.md` が生成される
2. `book.md` を編集し、マーカーを追加：
   - 目次ページに `<!-- toc -->` ... `<!-- /toc -->`
   - 本文に `<!-- content -->` ... `<!-- /content -->`
   - 索引・参考文献等に `<!-- skip -->` ... `<!-- /skip -->`
3. `make converter` で `book.xml` を生成

## 注意事項

- **デフォルトはreadAloud=false**: マーカーなしの部分は読み上げされません
- **contentマーカーは必須**: 読み上げたい部分は必ず`<!-- content -->`で囲んでください
- **ネスト可能**: `<!-- content -->`の中に`<!-- skip -->`を入れることができます（内側が優先）
- **ページ境界を超えて有効**: マーカーは閉じるまで複数ページにまたがって有効です
