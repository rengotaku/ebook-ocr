# Data Model: 019-heading-toc-normalize

**Date**: 2026-03-02
**Status**: Complete

## エンティティ定義

### 既存エンティティ（変更なし）

#### TocEntry
```python
@dataclass(frozen=True)
class TocEntry:
    """Table of Contents entry."""
    text: str       # エントリのタイトルテキスト
    level: int      # 階層レベル（1-5）
    number: str     # 章番号（例: "1", "2.1", "2.1.1"）
    page: str       # 参照ページ番号
```

#### Heading
```python
@dataclass(frozen=True)
class Heading:
    """見出し（TOC外の見出し用）"""
    level: int      # 1, 2, 3（0=エラー）
    text: str
    read_aloud: bool  # skip区間ではFalse
```

### 新規エンティティ

#### MatchType
```python
class MatchType(Enum):
    """マッチング結果の種類"""
    EXACT = "exact"       # 完全一致
    FUZZY = "fuzzy"       # ファジーマッチ（類似度80%以上）
    MISSING = "missing"   # TOCエントリに対応する本文見出しなし
    EXCLUDED = "excluded" # 特殊マーカー付き（マッチング対象外）
```

#### MatchResult
```python
@dataclass(frozen=True)
class MatchResult:
    """TOCエントリと本文見出しのマッチング結果"""
    toc_entry: TocEntry
    body_heading: Heading | None  # None = MISSING
    match_type: MatchType
    similarity: float             # 0.0-1.0
    line_number: int              # book.md 内の行番号（1-indexed）
```

**制約**:
- `similarity` は `match_type == EXACT` の場合 1.0
- `similarity` は `match_type == FUZZY` の場合 0.8 以上 1.0 未満
- `body_heading` は `match_type == MISSING` の場合 None
- `line_number` は 1 以上

#### NormalizationAction
```python
class NormalizationAction(Enum):
    """正規化アクションの種類"""
    ADD_NUMBER = "add_number"     # 番号付与（## タイトル → ## 1.1 タイトル）
    ADD_MARKER = "add_marker"     # Markdownマーカー付与（タイトル → ## 1.1 タイトル）
    FORMAT_ONLY = "format_only"   # フォーマット正規化のみ（1-1 → 1.1）
    NONE = "none"                 # 変更なし
```

#### NormalizationRule
```python
@dataclass(frozen=True)
class NormalizationRule:
    """正規化ルール"""
    original: str           # 元の見出しテキスト（行全体）
    normalized: str         # 正規化後のテキスト
    line_number: int        # book.md 内の行番号（1-indexed）
    action: NormalizationAction
```

**制約**:
- `action == NONE` の場合 `original == normalized`
- `line_number` は 1 以上

#### ValidationReport
```python
@dataclass(frozen=True)
class ValidationReport:
    """TOC検証レポート"""
    toc_entry_count: int          # TOCエントリ総数
    body_heading_count: int       # 本文見出し総数
    matched_count: int            # マッチ数
    match_rate: float             # マッチ率（0.0-1.0）
    missing_entries: tuple[TocEntry, ...]      # 本文に存在しないTOCエントリ
    excluded_headings: tuple[Heading, ...]     # マッチング対象外の見出し
```

## リレーション図

```
TocEntry 1 ─────────── 0..1 MatchResult
                            │
                            │ match_type
                            │ similarity
                            │
Heading 0..1 ───────────────┘

MatchResult * ─────────── 1 NormalizationRule

NormalizationRule * ───── 1 ValidationReport
```

## 状態遷移

### マッチングフロー

```
[TOC Entry] + [Body Headings]
        │
        ▼
    ┌───────────────┐
    │ 完全一致検索   │
    └───────┬───────┘
            │
    ┌───────┴───────┐
    │ 見つかった？   │
    └───────┬───────┘
        YES │ NO
            │  │
    ┌───────┘  └──────┐
    ▼                  ▼
EXACT           ┌──────────────┐
                │ 番号除去一致  │
                └──────┬───────┘
                       │
               ┌───────┴───────┐
               │ 見つかった？   │
               └───────┬───────┘
                   YES │ NO
                       │  │
               ┌───────┘  └──────┐
               ▼                  ▼
           EXACT           ┌──────────────┐
           (add_number)    │ ファジーマッチ │
                           └──────┬───────┘
                                  │
                          ┌───────┴───────┐
                          │ 類似度 ≥ 80%? │
                          └───────┬───────┘
                              YES │ NO
                                  │  │
                          ┌───────┘  └──────┐
                          ▼                  ▼
                       FUZZY             MISSING
```

## バリデーションルール

### TocEntry
- `text` は空文字不可
- `level` は 1-5 の範囲
- `number` は空または `N`, `N.N`, `N.N.N` 形式

### Heading
- `level` は 1-3 の範囲（0はエラー状態）
- `text` は空文字不可

### MatchResult
- `match_type == EXACT` → `similarity == 1.0`
- `match_type == FUZZY` → `0.8 <= similarity < 1.0`
- `match_type == MISSING` → `body_heading is None`
- `match_type == EXCLUDED` → `is_special_marker(body_heading.text) == True`

### NormalizationRule
- `action == NONE` → `original == normalized`
- `action != NONE` → `original != normalized`
