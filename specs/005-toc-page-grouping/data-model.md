# Data Model: TOC構造を利用したpageタグのグルーピング

**Date**: 2026-02-09
**Feature**: 005-toc-page-grouping

## Entities

### 1. TOCEntry

目次の1エントリを表現。

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| level | str | "chapter" \| "section" \| "subsection" | 必須、3値のいずれか |
| number | str | セクション番号 (例: "1", "1.1", "1.1.1") | 必須、正規表現 `^\d+(\.\d+)*$` |
| title | str | セクションタイトル | 必須、空文字不可 |

**Relationships**:
- chapter は複数の section を持つ
- section は複数の subsection を持つ

---

### 2. TOC

目次全体を表現。

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| begin | int | 目次開始ページ番号 | 必須、1以上 |
| end | int | 目次終了ページ番号 | 必須、begin以上 |
| entries | list[TOCEntry] | エントリのリスト | 空リスト可 |

---

### 3. Page

ページ要素を表現。

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| number | int | ページ番号 | 必須、1以上 |
| source_file | str | ソースファイル名 | 必須 |
| page_type | str \| None | "chapter-title" など | オプション |
| content | Element | ページコンテンツ（XMLサブツリー） | 必須 |
| detected_section | str \| None | 検出されたセクション番号 | 処理中に設定 |

---

### 4. SectionNumber

セクション番号のパース結果を表現。

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| raw | str | 生の番号文字列 (例: "1.1.3") | 必須 |
| parts | list[int] | 分解された番号 (例: [1, 1, 3]) | 1要素以上 |
| level | str | "chapter" \| "section" \| "subsection" | partsの長さから決定 |

**Derived Properties**:
- `chapter_num`: parts[0]
- `section_num`: parts[0:2] を結合 (例: "1.1")
- `is_chapter`: len(parts) == 1
- `is_section`: len(parts) == 2
- `is_subsection`: len(parts) >= 3

---

### 5. GroupedBook

グルーピング後の書籍構造を表現。

| Field | Type | Description |
|-------|------|-------------|
| metadata | Element | メタデータ要素 |
| toc | TOC | 目次 |
| front_matter | list[Page] | 前付けページ（TOC終了まで） |
| chapters | list[Chapter] | 章のリスト |

---

### 6. Chapter

章を表現。

| Field | Type | Description |
|-------|------|-------------|
| number | str | 章番号 (例: "1") |
| title | str | 章タイトル |
| title_page | Page \| None | 章扉ページ |
| sections | list[Section] | 節のリスト |
| pages | list[Page] | 章直下のページ（節に属さない） |

---

### 7. Section

節を表現。

| Field | Type | Description |
|-------|------|-------------|
| number | str | 節番号 (例: "1.1") |
| title | str | 節タイトル |
| subsections | list[Subsection] | 項のリスト |
| pages | list[Page] | 節直下のページ（項に属さない） |

---

### 8. Subsection

項を表現。

| Field | Type | Description |
|-------|------|-------------|
| number | str | 項番号 (例: "1.1.1") |
| title | str | 項タイトル |
| pages | list[Page] | 項に属するページ |

---

## State Transitions

### ページ処理状態

```
[Raw Page]
    ↓ extract_section_number()
[Page with detected_section]
    ↓ assign_to_hierarchy()
[Page in Chapter/Section/Subsection]
```

### グルーピング処理フロー

```
[Input: book.xml with flat pages]
    ↓ parse_toc()
[TOC extracted]
    ↓ extract_section_numbers_from_pages()
[Pages with section info]
    ↓ build_hierarchy()
[Grouped structure]
    ↓ serialize_to_xml()
[Output: book.xml with hierarchy]
```

---

## XML Schema (Output)

```xml
<book>
  <metadata>...</metadata>
  <toc begin="7" end="13">
    <entry level="chapter" number="1" title="..." />
    ...
  </toc>

  <front-matter>
    <page number="1">...</page>
    ...
  </front-matter>

  <chapter number="1" title="...">
    <page number="14" type="chapter-title">...</page>

    <section number="1.1" title="...">
      <page number="15">...</page>

      <subsection number="1.1.1" title="...">
        <page number="16">...</page>
      </subsection>
    </section>
  </chapter>
</book>
```
