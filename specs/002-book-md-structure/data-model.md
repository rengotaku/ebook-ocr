# Data Model: Book Markdown to XML

**Date**: 2026-02-07
**Feature**: 002-book-md-structure

## Overview

Markdown形式のbook.mdをXML形式のbook.xmlに変換するためのデータモデル定義。
すべてのエンティティはイミュータブル（Constitution IV. Immutability 準拠）。

## Entities

### Book

書籍全体を表すルートエンティティ。

```python
@dataclass(frozen=True)
class Book:
    """書籍全体"""
    metadata: BookMetadata
    pages: tuple[Page, ...]  # イミュータブルなタプル
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| metadata | BookMetadata | Yes | 書籍メタデータ |
| pages | tuple[Page, ...] | Yes | ページのリスト（順序保持） |

---

### BookMetadata

書籍のメタデータ。

```python
@dataclass(frozen=True)
class BookMetadata:
    """書籍メタデータ"""
    title: str
    isbn: str | None = None
    source_format: str = "markdown"
    conversion_date: str = ""  # ISO 8601 形式
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| title | str | Yes | - | 書籍タイトル |
| isbn | str \| None | No | None | ISBN番号 |
| source_format | str | No | "markdown" | 元形式 |
| conversion_date | str | No | "" | 変換日時（ISO 8601） |

---

### Page

1つの物理ページを表すエンティティ。

```python
@dataclass(frozen=True)
class Page:
    """1ページ"""
    number: str  # 空文字列許容（エラー時）
    source_file: str
    announcement: PageAnnouncement | None
    content: Content
    figures: tuple[Figure, ...] = ()
    metadata: PageMetadata | None = None
    continued: bool = False
    page_type: str = "normal"  # "normal", "cover", "colophon", "toc"
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| number | str | Yes | - | ページ番号（空=抽出失敗） |
| source_file | str | Yes | - | 元画像ファイル名 |
| announcement | PageAnnouncement \| None | No | None | ページ読み上げ |
| content | Content | Yes | - | 本文コンテンツ |
| figures | tuple[Figure, ...] | No | () | 図表リスト |
| metadata | PageMetadata \| None | No | None | ページメタデータ |
| continued | bool | No | False | 前ページからの継続 |
| page_type | str | No | "normal" | ページ種別 |

---

### PageAnnouncement

ページ切り替え時のTTSアナウンス。

```python
@dataclass(frozen=True)
class PageAnnouncement:
    """ページ読み上げ"""
    text: str  # "42ページ"
    format: str = "simple"  # "simple", "chapter"
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| text | str | Yes | - | 読み上げテキスト |
| format | str | No | "simple" | フォーマット種別 |

---

### Content

ページの本文コンテンツ。

```python
@dataclass(frozen=True)
class Content:
    """本文コンテンツ"""
    elements: tuple[ContentElement, ...]
    read_aloud: bool = True
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| elements | tuple[ContentElement, ...] | Yes | - | コンテンツ要素リスト |
| read_aloud | bool | No | True | TTS読み上げフラグ |

---

### ContentElement (Union Type)

コンテンツ要素の共用体型。

```python
ContentElement = Heading | Paragraph | List
```

---

### Heading

見出し要素。

```python
@dataclass(frozen=True)
class Heading:
    """見出し"""
    level: int  # 1, 2, 3（0=エラー）
    text: str
    read_aloud: bool = True
```

| Field | Type | Required | Default | Validation | Description |
|-------|------|----------|---------|------------|-------------|
| level | int | Yes | - | 1-3, 0=error | 階層レベル |
| text | str | Yes | - | 非空 | 見出しテキスト |
| read_aloud | bool | No | True | - | TTS読み上げ |

---

### Paragraph

段落要素。

```python
@dataclass(frozen=True)
class Paragraph:
    """段落"""
    text: str
    read_aloud: bool = True
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| text | str | Yes | - | 段落テキスト |
| read_aloud | bool | No | True | TTS読み上げ |

---

### List

リスト要素。

```python
@dataclass(frozen=True)
class List:
    """リスト"""
    items: tuple[str, ...]
    read_aloud: bool = True
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| items | tuple[str, ...] | Yes | - | リスト項目 |
| read_aloud | bool | No | True | TTS読み上げ |

---

### Figure

図表要素。

```python
@dataclass(frozen=True)
class Figure:
    """図表"""
    file: str
    caption: str = ""
    description: str = ""
    read_aloud: str = "optional"  # "true", "false", "optional"
    continued: bool = False
```

| Field | Type | Required | Default | Validation | Description |
|-------|------|----------|---------|------------|-------------|
| file | str | Yes | - | - | 図ファイルパス |
| caption | str | No | "" | - | 図タイトル |
| description | str | No | "" | - | 図の説明 |
| read_aloud | str | No | "optional" | true/false/optional | TTS制御 |
| continued | bool | No | False | - | 複数ページ継続 |

---

### PageMetadata

ページ内メタデータ（「3 / 7」など）。

```python
@dataclass(frozen=True)
class PageMetadata:
    """ページメタデータ"""
    text: str  # 元の表記 "はじめに 1 / 3"
    meta_type: str = "chapter-page"  # "chapter-page", "section-page", "unknown"
    section_name: str = ""  # "はじめに"
    current: int = 0  # 1
    total: int = 0  # 3
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| text | str | Yes | - | 元の表記 |
| meta_type | str | No | "chapter-page" | メタデータ種別 |
| section_name | str | No | "" | セクション名 |
| current | int | No | 0 | 現在ページ（0=未抽出） |
| total | int | No | 0 | 総ページ（0=未抽出） |

---

### ConversionError

変換エラー情報。

```python
@dataclass(frozen=True)
class ConversionError:
    """変換エラー"""
    error_type: str  # "PAGE_NUMBER_NOT_FOUND", etc.
    message: str
    page_number: str = ""
    line_number: int = 0
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| error_type | str | Yes | - | エラー種別 |
| message | str | Yes | - | エラーメッセージ |
| page_number | str | No | "" | 該当ページ番号 |
| line_number | int | No | 0 | 該当行番号 |

---

### ConversionResult

変換結果。

```python
@dataclass(frozen=True)
class ConversionResult:
    """変換結果"""
    success: bool
    total_pages: int
    error_count: int
    errors: tuple[ConversionError, ...] = ()
    output_path: str = ""
```

| Field | Type | Required | Default | Description |
|-------|------|----------|---------|-------------|
| success | bool | Yes | - | 成功フラグ |
| total_pages | int | Yes | - | 総ページ数 |
| error_count | int | Yes | - | エラー数 |
| errors | tuple[ConversionError, ...] | No | () | エラー詳細 |
| output_path | str | No | "" | 出力ファイルパス |

---

## Relationships

```
Book
├── BookMetadata (1:1)
└── Page (1:N)
    ├── PageAnnouncement (1:0..1)
    ├── Content (1:1)
    │   └── ContentElement (1:N)
    │       ├── Heading
    │       ├── Paragraph
    │       └── List
    ├── Figure (1:N)
    └── PageMetadata (1:0..1)
```

## State Transitions

本機能ではステート遷移なし（バッチ変換のため）。

## Validation Rules

| Entity | Field | Rule | Error Type |
|--------|-------|------|------------|
| Page | number | 数字のみ（空許容） | PAGE_NUMBER_NOT_FOUND |
| Heading | level | 1-3の整数 | HEADING_LEVEL_AMBIGUOUS |
| Figure | file | 空でない | FIGURE_PATH_INVALID |
| PageMetadata | meta_type | chapter-page/section-page/unknown | PAGE_META_PARSE_FAILED |
