# Implementation Plan: book.md の見出し形式統一と TOC マッチング改善

**Branch**: `019-heading-toc-normalize` | **Date**: 2026-03-02 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/019-heading-toc-normalize/spec.md`

## Summary

book.md の見出し形式を TOC（目次）に合わせて自動正規化し、book.xml 変換時のマッチング精度を向上させる機能を実装する。既存の `src/book_converter/parser/toc.py` と `models.py` を拡張し、番号フォーマット統一（ドット区切り）、スペース正規化、ファジーマッチングを追加する。

## Technical Context

**Language/Version**: Python 3.13+ (Constitution 準拠)
**Primary Dependencies**: re (標準ライブラリ), difflib (ファジーマッチ用、標準ライブラリ)
**Storage**: ファイルベース (book.md 入力/出力)
**Testing**: pytest (Constitution 準拠、カバレッジ ≥80%)
**Target Platform**: Linux/macOS CLI
**Project Type**: Single project (既存 src/ 構造を拡張)
**Performance Goals**: 1万行以上の book.md で10秒以内に処理完了 (SC-001)
**Constraints**: 純粋関数優先、ファイル I/O はパイプライン境界に限定
**Scale/Scope**: 単一 book.md ファイル処理、TOC エントリ数 ~100件規模

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Pipeline-First | ✅ PASS | 各フェーズ（抽出→正規化→マッチング→適用→検証）が独立ステップ |
| II. Test-First | ✅ PASS | TDD 必須、pytest 使用、カバレッジ ≥80% |
| III. Ollama Integration | N/A | この機能では LLM 不使用 |
| IV. Immutability | ✅ PASS | 純粋関数で変換、元ファイル変更は明示的 --apply オプションのみ |
| V. Simplicity (YAGNI) | ✅ PASS | 必要な正規化のみ実装、過剰な設定オプションなし |

**Technical Constraints Check**:
- Python 3.13+: ✅
- 依存管理: requirements.txt + venv: ✅（新規依存なし、標準ライブラリのみ）
- ビルド/テスト: Makefile: ✅（新規ターゲット追加）
- 1ファイル 800行以下: ✅（モジュール分割で対応）
- 1関数 50行以下: ✅

## Project Structure

### Documentation (this feature)

```text
specs/019-heading-toc-normalize/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── quickstart.md        # Phase 1 output
├── checklists/          # Validation checklists
│   └── requirements.md
└── tasks.md             # Phase 2 output (/speckit.tasks)
```

### Source Code (repository root)

```text
src/
├── book_converter/
│   ├── models.py                    # 既存: TocEntry, Heading 拡張
│   ├── parser/
│   │   ├── toc.py                   # 既存: TOC パース拡張
│   │   ├── heading.py               # 既存: 見出しパース拡張
│   │   └── heading_normalizer.py    # 新規: 見出し正規化ロジック
│   ├── heading_matcher.py           # 新規: TOC-本文マッチング
│   ├── normalization_rules.py       # 新規: 正規化ルール生成
│   └── cli.py                       # 既存: CLI 拡張
├── cli/
│   └── normalize_headings.py        # 新規: 正規化 CLI エントリポイント

tests/
├── book_converter/
│   ├── parser/
│   │   └── test_heading_normalizer.py  # 新規
│   ├── test_heading_matcher.py         # 新規
│   └── test_normalization_rules.py     # 新規
└── cli/
    └── test_normalize_headings.py      # 新規
```

**Structure Decision**: 既存の `src/book_converter/` 構造を拡張。新規モジュールは機能ごとに分離（heading_normalizer, heading_matcher, normalization_rules）。CLI は `src/cli/normalize_headings.py` に追加。

## Complexity Tracking

> Constitution Check に違反なし。追加の複雑性正当化は不要。

---

## Phase 0: Research

### 技術調査項目

| 項目 | 決定 | 根拠 |
|------|------|------|
| ファジーマッチライブラリ | difflib.SequenceMatcher | 標準ライブラリ、追加依存なし、日本語対応 |
| 番号パターン正規表現 | `r'[\d１-９]+[.\-・．][\d１-９]+'` | 全角/半角、ドット/ハイフン/中黒対応 |
| スペース正規化 | `re.sub(r'\s+', '', text)` | シンプル、日本語空白も除去 |
| スクリプト出力形式 | sed コマンド（POSIX 互換） | 汎用性、bash 依存なし |

### 既存コード分析

**src/book_converter/models.py**:
- `TocEntry`: text, level, number, page フィールド → 拡張不要
- `Heading`: level, text, read_aloud フィールド → 拡張不要

**src/book_converter/parser/toc.py**:
- `normalize_toc_line()`: 既存の正規化関数 → 番号フォーマット統一を追加
- `parse_toc_entry()`: エントリ解析 → そのまま利用

**拡張ポイント**:
1. `heading_normalizer.py`: 番号フォーマット統一、スペース正規化の純粋関数群
2. `heading_matcher.py`: TOCEntry と BodyHeading のマッチングロジック
3. `normalization_rules.py`: マッチング結果から sed コマンド生成

---

## Phase 1: Design

### Data Model

既存モデルを拡張せず、新規モデルを追加:

```python
@dataclass(frozen=True)
class MatchResult:
    """TOCエントリと本文見出しのマッチング結果"""
    toc_entry: TocEntry
    body_heading: Heading | None  # None = MISSING
    match_type: MatchType  # EXACT, FUZZY, MISSING, EXCLUDED
    similarity: float  # 0.0-1.0
    line_number: int  # book.md 内の行番号

class MatchType(Enum):
    EXACT = "exact"
    FUZZY = "fuzzy"
    MISSING = "missing"
    EXCLUDED = "excluded"

@dataclass(frozen=True)
class NormalizationRule:
    """正規化ルール"""
    original: str  # 元の見出しテキスト
    normalized: str  # 正規化後のテキスト
    line_number: int
    action: NormalizationAction  # ADD_NUMBER, ADD_MARKER, FORMAT_ONLY, NONE

class NormalizationAction(Enum):
    ADD_NUMBER = "add_number"  # 番号付与
    ADD_MARKER = "add_marker"  # Markdownマーカー付与
    FORMAT_ONLY = "format_only"  # フォーマット正規化のみ
    NONE = "none"  # 変更なし
```

### API Contracts

**CLI Interface**:

```bash
# 見出しレポート生成
make heading-report HASHDIR=output/<hash>
python -m src.cli.normalize_headings report <book.md>

# 正規化（dry-run）
make normalize-headings HASHDIR=output/<hash>
python -m src.cli.normalize_headings normalize <book.md>

# 正規化（適用）
make normalize-headings HASHDIR=output/<hash> APPLY=1
python -m src.cli.normalize_headings normalize <book.md> --apply

# TOC検証
make validate-toc HASHDIR=output/<hash>
python -m src.cli.normalize_headings validate <book.md>
```

**Module Interface**:

```python
# heading_normalizer.py
def normalize_number_format(text: str) -> str:
    """番号フォーマットをドット区切りに統一"""

def normalize_spaces(text: str) -> str:
    """余分なスペースを除去"""

def is_special_marker(text: str) -> bool:
    """特殊マーカー（■、◆等）を検出"""

# heading_matcher.py
def match_toc_to_body(
    toc_entries: list[TocEntry],
    body_headings: list[Heading],
    similarity_threshold: float = 0.8
) -> list[MatchResult]:
    """TOCエントリと本文見出しをマッチング"""

# normalization_rules.py
def generate_rules(matches: list[MatchResult]) -> list[NormalizationRule]:
    """マッチング結果から正規化ルールを生成"""

def generate_sed_script(rules: list[NormalizationRule]) -> str:
    """sed コマンドスクリプトを生成"""
```

### Makefile Targets

```makefile
# 見出しパターン分析レポート
heading-report:
	PYTHONPATH=$(CURDIR) $(PYTHON) -m src.cli.normalize_headings report "$(HASHDIR)/book.md"

# 見出し正規化（dry-run）
normalize-headings:
	PYTHONPATH=$(CURDIR) $(PYTHON) -m src.cli.normalize_headings normalize "$(HASHDIR)/book.md" $(if $(APPLY),--apply)

# TOC検証
validate-toc:
	PYTHONPATH=$(CURDIR) $(PYTHON) -m src.cli.normalize_headings validate "$(HASHDIR)/book.md"
```

---

## Implementation Phases

### Phase A: 基盤実装 (TDD)

1. `heading_normalizer.py`: 正規化純粋関数
   - `normalize_number_format()`: 番号フォーマット統一
   - `normalize_spaces()`: スペース正規化
   - `is_special_marker()`: 特殊マーカー検出

### Phase B: マッチングエンジン (TDD)

2. `heading_matcher.py`: マッチングロジック
   - `match_toc_to_body()`: 完全一致 → 番号除去一致 → ファジーマッチ

### Phase C: ルール生成 (TDD)

3. `normalization_rules.py`: ルール生成
   - `generate_rules()`: マッチング結果 → 正規化ルール
   - `generate_sed_script()`: sed コマンド出力

### Phase D: CLI 統合

4. `src/cli/normalize_headings.py`: CLI エントリポイント
   - `report` サブコマンド
   - `normalize` サブコマンド（--apply オプション）
   - `validate` サブコマンド

### Phase E: Makefile 統合

5. Makefile ターゲット追加
   - `heading-report`
   - `normalize-headings`
   - `validate-toc`

---

## Next Steps

1. `/speckit.tasks` で tasks.md を生成
2. TDD サイクルで Phase A から実装開始
