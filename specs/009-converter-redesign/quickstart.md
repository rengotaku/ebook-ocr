# Quickstart: Converter v2

## 前提条件

- Python 3.13+
- venv 有効化済み

## インストール

```bash
cd /data/projects/video-separater
source .venv/bin/activate
```

## 基本的な使い方

### 1. 入力MDファイルの準備

```markdown
--- Page 1 (page_0001.png) ---

# Chapter 1 はじめに

<!-- content -->

本文の段落です。

次の段落です。

<!-- /content -->

--- Page 2 (page_0002.png) ---

## Episode 01 最初のエピソード

エピソードの本文。

- リスト項目1
- リスト項目2

[図1]
```

### 2. 変換実行

```bash
python -m src.book_converter book.md -o book.xml \
  --header-level1=chapter \
  --header-level2=episode
```

### 3. 出力確認

```xml
<?xml version="1.0" encoding="UTF-8"?>
<book>
  <metadata>
    <title>書籍タイトル</title>
  </metadata>

  <chapter number="1" title="はじめに">
    <!-- page 1 -->
    <heading readAloud="true">Chapter 1 はじめに</heading>
    <paragraph>本文の段落です。</paragraph>
    <paragraph>次の段落です。</paragraph>

    <section number="1" title="最初のエピソード">
      <!-- page 2 -->
      <heading readAloud="true">Episode 01 最初のエピソード</heading>
      <paragraph>エピソードの本文。</paragraph>
      <list type="unordered">
        <item>リスト項目1</item>
        <item>リスト項目2</item>
      </list>
      <figure readAloud="false" path="figures/fig001.png" marker="図1" />
    </section>
  </chapter>
</book>
```

## よくある使用パターン

### 複数キーワードの指定

```bash
python -m src.book_converter book.md -o book.xml \
  --header-level1=chapter \
  --header-level2="episode|column"
```

### 図マーカーのカスタマイズ

```bash
python -m src.book_converter book.md -o book.xml \
  --header-level1=chapter \
  --figure-markers="図|写真|表|イラスト"
```

### 詳細ログ出力

```bash
python -m src.book_converter book.md -o book.xml \
  --header-level1=chapter \
  --verbose
```

## テスト実行

```bash
make test
# または
pytest tests/book_converter/
```

## トラブルシューティング

### エラー: "header-level1 is required"

見出しレベル1のキーワードは必須です:

```bash
--header-level1=chapter  # または 第N章 など
```

### 段落が分離されない

MDファイルで段落間に空行があることを確認:

```markdown
段落1のテキスト。

段落2のテキスト。
```

### 図が検出されない

`--figure-markers` で正しいマーカーを指定:

```bash
--figure-markers="図|写真|表"
```
