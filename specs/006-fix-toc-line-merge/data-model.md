# Data Model: TOC解析改行結合とページ欠損修正

**Feature**: 006-fix-toc-line-merge
**Date**: 2026-02-09

## Entities

### TocEntry (既存)

TOCの1エントリを表すデータクラス。

| Field | Type | Description | Validation |
|-------|------|-------------|------------|
| text | str | エントリのタイトル | 非空 |
| level | str | 階層レベル | "chapter" \| "section" \| "subsection" \| "other" |
| number | str | 章番号（任意） | 数字またはドット区切り数字 |
| page | str | ページ番号（任意） | 数字文字列 |

**既存の定義** (`models.py`):
```python
@dataclass(frozen=True)
class TocEntry:
    text: str
    level: str = "other"
    number: str = ""
    page: str = ""
```

### Page (既存)

書籍の1ページを表すデータクラス。

| Field | Type | Description |
|-------|------|-------------|
| number | str | ページ番号 |
| source_file | str | 元画像ファイル名 |
| content | Content | ページ内容 |
| announcement | PageAnnouncement \| None | ページアナウンス |
| figures | tuple[Figure, ...] | 図のリスト |
| metadata | PageMetadata \| None | メタデータ |
| continued | bool | 前ページからの継続フラグ |
| page_type | str | ページタイプ |

## New Functions

### merge_toc_lines (新規)

TOCセクション内の分割された行を結合する前処理関数。

**Signature**:
```python
def merge_toc_lines(lines: list[str]) -> list[str]:
    """
    TOCセクション内の分割された行を結合する。

    Args:
        lines: TOCセクション内の行リスト

    Returns:
        結合後の行リスト

    Examples:
        >>> merge_toc_lines(["Chapter", "", "1 「企画」で失敗"])
        ["Chapter 1 「企画」で失敗"]
        >>> merge_toc_lines(["Episode 01", "タイトル"])
        ["Episode 01 タイトル"]
    """
```

**結合パターン**:
1. `Chapter` (単独) + 次の非空行
2. `Episode NN` + 次の非空行
3. `Column` (単独) + 次の非空行
4. `**キーワード**` パターンも対象

### validate_page_count (新規)

ページ欠損を検出する検証関数。

**Signature**:
```python
def validate_page_count(
    input_page_count: int,
    output_page_count: int,
    has_toc: bool
) -> tuple[bool, str | None]:
    """
    ページ数の整合性を検証する。

    Args:
        input_page_count: 入力ページ数
        output_page_count: 出力ページ数
        has_toc: TOCが存在するか

    Returns:
        (is_valid, error_message)
        - is_valid: 検証結果（Trueなら問題なし）
        - error_message: エラー時のメッセージ（Noneなら問題なし）

    Examples:
        >>> validate_page_count(181, 10, True)
        (False, "ページ欠損エラー: 181ページ中10ページ (5.5%) のみ出力")
        >>> validate_page_count(181, 181, True)
        (True, None)
    """
```

## State Transitions

### TOC Parsing State

```
[Initial Lines]
    ↓ normalize_toc_line (既存)
[Normalized Lines]
    ↓ merge_toc_lines (新規)
[Merged Lines]
    ↓ parse_toc_entry (拡張)
[TocEntry Objects]
```

## Relationships

```
book.md
    ↓ parse_pages_with_errors()
Pages[] + TocEntries[]
    ↓ build_xml()
book.xml (flat)
    ↓ group_pages_by_toc()
book.xml (hierarchical)
    ↓ validate_page_count()
[OK] or [ERROR with message]
```
