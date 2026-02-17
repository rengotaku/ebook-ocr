# Data Model: Converter再設計

**Date**: 2026-02-16
**Branch**: 009-converter-redesign

## エンティティ一覧

### 1. TocEntry（目次エントリ）

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| level | int | Yes | 階層レベル（1-5） |
| number | str | No | エントリ番号（"1", "2.1"等） |
| title | str | Yes | エントリタイトル |
| page | str | No | 参照ページ番号 |

**変更点**: level を str ("chapter"/"section"/"other") から int (1-5) に変更

**Validation**:
- level: 1 <= level <= 5
- title: 空文字不可

### 2. TableOfContents（目次全体）

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| entries | tuple[TocEntry, ...] | Yes | エントリのタプル |
| begin_page | str | No | TOC開始ページ |
| end_page | str | No | TOC終了ページ |

**変更なし**

### 3. StructureContainer（構造コンテナ）【新規】

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| container_type | str | Yes | コンテナ種別（"chapter", "section"等） |
| level | int | Yes | 階層レベル（1-5） |
| number | str | No | コンテナ番号（"1", "2"等） |
| title | str | Yes | コンテナタイトル（ナビゲーション用） |
| children | tuple | Yes | 子要素（StructureContainer or ContentElement） |

**XML出力例**:
```xml
<chapter number="1" title="Chapter Title">
  <heading readAloud="true">Chapter 1 Chapter Title</heading>
  <section number="1" title="Episode Title">
    <heading readAloud="true">Episode 01 Episode Title</heading>
    <paragraph>本文</paragraph>
  </section>
</chapter>
```

**Validation**:
- level: 1 <= level <= 5
- container_type: level に応じて決定（level1="chapter", level2="section"等）
- title: 空文字許容（見出しテキストから抽出）

### 4. Heading（見出し）

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| level | int | Yes | 階層レベル（1-5） |
| text | str | Yes | 見出しテキスト |
| read_aloud | bool | Yes | 読み上げ対象か |

**変更点**: level を 1-3 から 1-5 に拡張

### 5. Paragraph（段落）

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| text | str | Yes | 段落テキスト（改行なし） |
| read_aloud | bool | Yes | 読み上げ対象か |

**変更点**: text 内の改行を除去し、連続テキスト化

**Validation**:
- text: 改行文字（\n）を含まない

### 6. List（リスト）

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| items | tuple[str, ...] | Yes | リスト項目 |
| list_type | str | Yes | リスト種別（"unordered"/"ordered"） |
| read_aloud | bool | Yes | 読み上げ対象か |

**変更点**: list_type 属性を追加

### 7. Figure（図）

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| path | str | Yes | 画像ファイルパス |
| marker | str | No | 元のマーカーテキスト（"図1"等） |
| read_aloud | bool | Yes | 読み上げ対象か（常にfalse） |

**変更点**:
- file → path にリネーム
- caption, description を削除（シンプル化）
- marker を追加（元のプレースホルダー保持）

**XML出力例**:
```xml
<figure readAloud="false" path="figures/fig001.png" marker="図1" />
```

### 8. Book（書籍全体）【変更】

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| metadata | BookMetadata | Yes | 書籍メタデータ |
| toc | TableOfContents | No | 目次 |
| front_matter | tuple[ContentElement, ...] | No | 前付け（TOC前のコンテンツ） |
| chapters | tuple[StructureContainer, ...] | Yes | 章構造 |

**変更点**:
- pages を廃止
- chapters（StructureContainer）を追加
- front_matter を追加

### 9. PageComment【新規】

ページ情報はデータモデルではなく、XML生成時にコメントとして挿入。

```xml
<!-- page 42 -->
```

## 型定義

```python
ContentElement = Union[Heading, Paragraph, List, Figure]
ChildElement = Union[StructureContainer, ContentElement]
```

## 状態遷移

### MD解析フロー

```
MD Input
    ↓
Page Markers検出
    ↓
TOCマーカー検出・TOC構築
    ↓
見出し検出・階層構造構築
    ↓
段落/リスト/図検出
    ↓
StructureContainer生成
    ↓
Book生成
```

### 構造コンテナ構築ルール

1. レベル1見出し（#）検出 → 新規chapterコンテナ作成
2. レベル2見出し（##）検出 → 新規sectionコンテナ作成（現在のchapterの子）
3. レベル3-5見出し → 新規subsectionコンテナ作成（親コンテナの子）
4. 段落/リスト/図 → 現在のコンテナの子として追加
5. ページマーカー → コメントとして位置情報保持

## データフロー図

```
book.md (入力)
    │
    ├─→ parse_pages_with_errors()
    │       │
    │       └─→ TocEntry[] (level=int)
    │
    ├─→ build_structure()
    │       │
    │       ├─→ StructureContainer (chapters)
    │       │       │
    │       │       ├─→ Heading
    │       │       ├─→ Paragraph
    │       │       ├─→ List
    │       │       └─→ Figure
    │       │
    │       └─→ ContentElement[] (front_matter)
    │
    └─→ Book
            │
            └─→ build_xml()
                    │
                    └─→ book.xml (出力)
```
