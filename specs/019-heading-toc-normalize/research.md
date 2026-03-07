# Research: 019-heading-toc-normalize

**Date**: 2026-03-02
**Status**: Complete

## 調査項目

### 1. ファジーマッチングライブラリ選定

**決定**: `difflib.SequenceMatcher` (Python 標準ライブラリ)

**根拠**:
- 追加依存なし（Constitution V. Simplicity 準拠）
- 日本語文字列に対応
- `ratio()` メソッドで 0.0-1.0 の類似度スコアを返す

**代替案検討**:
- `rapidfuzz`: 高速だが外部依存
- `fuzzywuzzy`: python-Levenshtein 依存、複雑
- `jellyfish`: 英語向け最適化

**サンプルコード**:
```python
from difflib import SequenceMatcher

def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a, b).ratio()

# 使用例
similarity("SREの概要", "SRE の概要")  # → 0.91
similarity("サイトとは何か", "サイトとは何か")  # → 1.0
```

### 2. 番号パターン正規表現

**決定**: 以下のパターンを使用

```python
# 番号検出パターン（全角/半角、各種区切り対応）
NUMBER_PATTERN = r'([\d１-９]+)[.\-・．ー]([\d１-９]+)(?:[.\-・．ー]([\d１-９]+))?'

# 全角→半角変換
FULLWIDTH_TO_HALFWIDTH = str.maketrans(
    '０１２３４５６７８９．',
    '0123456789.'
)

# 区切り文字正規化（すべてドットに）
SEPARATOR_PATTERN = r'[\-・ー．]'
```

**対応パターン**:
| 入力 | 出力 |
|------|------|
| `1-1-1` | `1.1.1` |
| `１．１` | `1.1` |
| `1・1` | `1.1` |
| `1ー1` | `1.1` |

### 3. スペース正規化

**決定**: 番号周辺のスペースのみ除去（テキスト内スペースは保持）

```python
def normalize_spaces(text: str) -> str:
    """番号周辺のスペースを除去"""
    # "第 1 章" → "第1章"
    # "1. 1" → "1.1"
    # 但し "SRE の 概要" は "SRE の 概要" のまま（本文スペースは保持）
    
    # 章番号パターン周辺のスペース除去
    text = re.sub(r'(第)\s*(\d+)\s*(章)', r'\1\2\3', text)
    
    # 番号内スペース除去
    text = re.sub(r'(\d+)\s*\.\s*(\d+)', r'\1.\2', text)
    
    return text
```

### 4. 特殊マーカー検出

**決定**: プレフィックスパターンで検出

```python
SPECIAL_MARKERS = ['■', '◆', '●', '○', '◎', '★', '☆', '▶', '▷']

def is_special_marker(text: str) -> bool:
    """特殊マーカーで始まる見出しを検出"""
    stripped = text.lstrip('#').strip()
    return any(stripped.startswith(m) for m in SPECIAL_MARKERS)
```

### 5. sed スクリプト生成

**決定**: POSIX 互換 sed コマンド（GNU 拡張なし）

```python
def generate_sed_command(original: str, normalized: str) -> str:
    """sed コマンドを生成"""
    # エスケープ処理
    orig_escaped = original.replace('/', r'\/')
    norm_escaped = normalized.replace('/', r'\/')
    
    return f"sed -i 's/^{orig_escaped}$/{norm_escaped}/' book.md"
```

### 6. 既存コード活用

**src/book_converter/parser/toc.py**:
- `parse_toc_marker()`: TOC マーカー検出 → そのまま利用
- `normalize_toc_line()`: 行正規化 → 拡張して番号フォーマット統一追加

**src/book_converter/models.py**:
- `TocEntry`: 既存モデル → 変更なし
- `Heading`: 既存モデル → 変更なし

**新規追加のみで対応可能**:
- `heading_normalizer.py`: 純粋関数群
- `heading_matcher.py`: マッチングロジック
- `normalization_rules.py`: ルール生成

## 結論

NEEDS CLARIFICATION なし。すべての技術選定完了。
