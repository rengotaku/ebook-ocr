# Data Model: heading要素へのreadAloud属性付与ルール

**Date**: 2026-02-08
**Feature**: 003-heading-readaloud-rules

## 新規エンティティ

### ExclusionPattern

除外対象を定義するパターン。

```python
@dataclass(frozen=True)
class ExclusionPattern:
    """除外パターン定義"""

    id: str                    # パターン識別子 (e.g., "running-head", "page-number")
    priority: int              # 優先度 (高い方が先にマッチ試行)
    pattern: str | None        # 正規表現パターン (dynamicタイプの場合はNone)
    pattern_type: str          # "static" | "dynamic"
    description: str           # 説明 (e.g., "柱（ランニングヘッド）")
```

**Validation rules**:
- `id`: 非空文字列、英数字とハイフンのみ
- `priority`: 1-100の整数
- `pattern`: pattern_type="static"の場合は必須、有効な正規表現
- `pattern_type`: "static" または "dynamic"

### HeadingAnalysis

heading要素の出現頻度分析結果。

```python
@dataclass(frozen=True)
class HeadingAnalysis:
    """heading出現頻度分析結果"""

    text: str                  # headingテキスト（正規化済み）
    level: int                 # 最頻出時のlevel
    count: int                 # 出現回数
    levels: tuple[int, ...]    # 出現したlevelのリスト
    is_running_head: bool      # 柱として判定されたか
```

**Validation rules**:
- `text`: 非空文字列
- `level`: 1-3の整数
- `count`: 1以上の整数
- `levels`: 空でないタプル

### ReadAloudRule

readAloud属性付与ルール（内部処理用）。

```python
@dataclass(frozen=True)
class ReadAloudRule:
    """readAloud属性付与ルール"""

    pattern_id: str            # 適用されたパターンID
    read_aloud: bool           # 付与する値
    reason: str                # 理由 (e.g., "柱として検出", "ページ番号表記")
```

## 既存エンティティの変更

### Heading（変更なし）

既存のHeadingモデルには`read_aloud: bool = True`が既に存在するため、モデル自体の変更は不要。

```python
@dataclass(frozen=True)
class Heading:
    """見出し"""

    level: int           # 1, 2, 3（0=エラー）
    text: str
    read_aloud: bool = True  # ← 既存フィールド
```

**変更点**:
- parser.pyでHeadingを生成する際に、analyzer経由でread_aloud値を決定

## 関係図

```
ExclusionPattern (設定)
        │
        ▼
┌──────────────────┐
│   Analyzer       │ ← 全Headingを入力
│  (analyzer.py)   │
└────────┬─────────┘
         │
         ▼
HeadingAnalysis (分析結果)
         │
         ▼
┌──────────────────┐
│  ReadAloudRule   │ ← パターンマッチング
│    Generator     │
└────────┬─────────┘
         │
         ▼
Heading (read_aloud値設定済み)
         │
         ▼
┌──────────────────┐
│  Transformer     │
│  (transform_     │
│   heading)       │
└────────┬─────────┘
         │
         ▼
XML Element (readAloud属性付き)
```

## 状態遷移

### Heading処理フロー

```
[Raw Markdown Heading]
        │
        ▼ parse_heading()
[Heading(level, text, read_aloud=True)]  ← デフォルト値
        │
        ▼ analyze_headings()
[HeadingAnalysis集計]
        │
        ▼ apply_read_aloud_rules()
[Heading(level, text, read_aloud=False|True)]  ← ルール適用後
        │
        ▼ transform_heading()
[<heading level="N" readAloud="false|true">]
```

## データ量見積もり

| エンティティ | 1書籍あたりの件数 |
|-------------|-----------------|
| Page | 100-300 |
| Heading | 100-500 |
| ExclusionPattern | 10-20（設定） |
| HeadingAnalysis | 10-50（ユニークテキスト数） |
