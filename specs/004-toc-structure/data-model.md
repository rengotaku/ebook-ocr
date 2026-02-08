# Data Model: 目次情報の保持

**Date**: 2026-02-08
**Feature**: 004-toc-structure

## 1. 新規エンティティ

### 1.1 TocEntry

目次の1エントリを表す。

```python
@dataclass(frozen=True)
class TocEntry:
    """Table of Contents entry."""

    text: str              # エントリのタイトルテキスト
    level: str             # "chapter", "section", "subsection", "other"
    number: str = ""       # 章番号（例: "1", "2.1", "2.1.1"）
    page: str = ""         # 参照ページ番号
```

**属性詳細**:

| 属性 | 型 | 必須 | 説明 |
|------|-----|------|------|
| text | str | ✅ | 目次エントリのタイトル（例: "SREとは"） |
| level | str | ✅ | 階層レベル。列挙値: chapter, section, subsection, other |
| number | str | - | 章番号。例: "1", "2.1", "2.1.1"。「はじめに」等は空文字 |
| page | str | - | 参照先ページ番号。抽出できない場合は空文字 |

**level列挙値**:

| 値 | パターン | 例 |
|----|---------|-----|
| chapter | `第N章` | 第1章 SREとは |
| section | `N.N` | 2.1 SLOの理解 |
| subsection | `N.N.N` | 2.1.1 SLA |
| other | 上記以外 | はじめに、おわりに、索引 |

### 1.2 TableOfContents

目次全体を表す。

```python
@dataclass(frozen=True)
class TableOfContents:
    """Complete Table of Contents."""

    entries: tuple[TocEntry, ...]   # 目次エントリのタプル（不変）
    read_aloud: bool = False        # 読み上げ制御（デフォルト: false）
```

**属性詳細**:

| 属性 | 型 | 必須 | 説明 |
|------|-----|------|------|
| entries | tuple[TocEntry, ...] | ✅ | 目次エントリの順序付きタプル |
| read_aloud | bool | - | 読み上げ対象か。デフォルトはfalse |

### 1.3 MarkerType（列挙）

マーカー種別を表す。

```python
from enum import Enum

class MarkerType(Enum):
    """Content marker types."""

    TOC_START = "toc_start"       # <!-- toc -->
    TOC_END = "toc_end"           # <!-- /toc -->
    CONTENT_START = "content_start"  # <!-- content -->
    CONTENT_END = "content_end"   # <!-- /content -->
    SKIP_START = "skip_start"     # <!-- skip -->
    SKIP_END = "skip_end"         # <!-- /skip -->
```

## 2. 既存エンティティの拡張

### 2.1 Book

```python
@dataclass(frozen=True)
class Book:
    metadata: BookMetadata
    pages: tuple[Page, ...]
    toc: TableOfContents | None = None  # NEW: 目次（オプション）
```

### 2.2 Page

```python
@dataclass(frozen=True)
class Page:
    number: str
    source_file: str
    content: Content
    announcement: PageAnnouncement | None = None
    figures: tuple[Figure, ...] = ()
    metadata: PageMetadata | None = None
    continued: bool = False
    page_type: str = "normal"
    toc: TableOfContents | None = None  # NEW: このページの目次（オプション）
```

### 2.3 Content

```python
@dataclass(frozen=True)
class Content:
    elements: tuple[ContentElement, ...]
    read_aloud: bool = False  # CHANGED: デフォルトをFalseに変更
```

## 3. エンティティ関係図

```
Book
├── BookMetadata
├── TableOfContents (optional)
│   └── TocEntry (1..n)
└── Page (1..n)
    ├── PageAnnouncement (optional)
    ├── Content
    │   └── ContentElement (Heading | Paragraph | List)
    ├── Figure (0..n)
    ├── PageMetadata (optional)
    └── TableOfContents (optional, for TOC pages)
```

## 4. 状態遷移

### 4.1 パーサー状態

```
初期状態: NORMAL (readAloud=false)

イベント:
  <!-- toc -->     → TOC状態 (目次収集開始)
  <!-- /toc -->    → NORMAL状態 (目次収集終了)
  <!-- content --> → CONTENT状態 (readAloud=true)
  <!-- /content -->→ 前の状態に戻る
  <!-- skip -->    → SKIP状態 (readAloud=false)
  <!-- /skip -->   → 前の状態に戻る
  ページ境界       → 状態継続（リセットしない）
```

### 4.2 状態スタック

```python
# 例: content内にskipがネストした場合

初期: []                          # readAloud=false (default)
  ↓ <!-- content -->
状態: ["content"]                  # readAloud=true
  ↓ <!-- skip -->
状態: ["content", "skip"]          # readAloud=false (内側優先)
  ↓ <!-- /skip -->
状態: ["content"]                  # readAloud=true
  ↓ <!-- /content -->
状態: []                          # readAloud=false
```

## 5. バリデーションルール

### 5.1 TocEntry

- `text`: 空文字不可
- `level`: 許容値のみ（chapter, section, subsection, other）
- `number`: 形式チェックなし（空文字許容）
- `page`: 形式チェックなし（空文字許容）

### 5.2 TableOfContents

- `entries`: 空タプル不可（少なくとも1エントリ必要）

### 5.3 マーカー整合性

- 開始マーカーと終了マーカーはペアで使用
- 未終了マーカーはページ終端で暗黙的に終了
- ネストは許容（内側優先）

## 6. XML出力形式

### 6.1 TableOfContents

```xml
<tableOfContents readAloud="false">
  <entry level="other" title="はじめに" page="1"/>
  <entry level="chapter" number="1" title="SREとは" page="15"/>
  <entry level="section" number="1.1" title="SREの定義" page="16"/>
  <entry level="subsection" number="1.1.1" title="歴史" page="17"/>
  <entry level="chapter" number="2" title="信頼性の定義" page="25"/>
</tableOfContents>
```

### 6.2 readAloud属性

```xml
<!-- content -->内 -->
<paragraph readAloud="true">本文テキスト</paragraph>

<!-- skip -->内または マーカーなし -->
<paragraph readAloud="false">索引テキスト</paragraph>
```
