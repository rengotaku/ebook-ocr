# Phase 2 Output: US1 - 見出しパターンの自動抽出

**Date**: 2026-03-02
**Status**: Completed
**User Story**: US1 - 見出しパターンの自動抽出

## Executed Tasks

- [x] T013 RED テストを読む: specs/019-heading-toc-normalize/red-tests/ph2-test.md
- [x] T014 [P] [US1] MatchType, NormalizationAction 列挙型を追加: src/book_converter/models.py
- [x] T015 [P] [US1] normalize_number_format() を実装: src/book_converter/parser/heading_normalizer.py
- [x] T016 [P] [US1] normalize_spaces() を実装: src/book_converter/parser/heading_normalizer.py
- [x] T017 [P] [US1] is_special_marker() を実装: src/book_converter/parser/heading_normalizer.py
- [x] T018 [P] [US1] extract_headings() を実装: src/book_converter/parser/heading_normalizer.py
- [x] T019 [P] [US1] classify_heading_patterns() を実装: src/book_converter/parser/heading_normalizer.py
- [x] T020 `make test` で PASS を確認 (GREEN)
- [x] T021 `make test` で全テスト PASS を確認（リグレッションなし）
- [x] T022 `make coverage` でカバレッジ ≥80% を確認
- [x] T023 フェーズ結果を出力: specs/019-heading-toc-normalize/tasks/ph2-output.md

## Changed Files

| File | Change Type | Summary |
|------|-------------|---------|
| src/book_converter/models.py | Modified | MatchType, NormalizationAction 列挙型を追加 |
| src/book_converter/parser/heading_normalizer.py | Modified | 5つの純粋関数を実装（stub から実装へ） |
| specs/019-heading-toc-normalize/tasks.md | Modified | T013-T023 を完了としてマーク |

## Implementation Details

### MatchType, NormalizationAction 列挙型

`src/book_converter/models.py` に以下の列挙型を追加:

```python
class MatchType(Enum):
    """マッチング結果の種類"""
    EXACT = "exact"
    FUZZY = "fuzzy"
    MISSING = "missing"
    EXCLUDED = "excluded"

class NormalizationAction(Enum):
    """正規化アクションの種類"""
    ADD_NUMBER = "add_number"
    ADD_MARKER = "add_marker"
    FORMAT_ONLY = "format_only"
    NONE = "none"
```

### normalize_number_format()

番号フォーマットをドット区切り半角に統一する純粋関数:

- 全角数字 → 半角数字 (str.maketrans 使用)
- 全角ドット(．) → 半角ドット(.)
- 番号パターン内の区切り文字(ハイフン、中黒) → ドット
- テキスト中のハイフン (例: SRE-based) は保持

**実装のポイント**: 正規表現 `(\d+)([-・\.])\d+(?:[-・\.]\d+)*` で番号パターンを検出し、区切り文字を一括でドットに置換。

### normalize_spaces()

番号周辺のスペースを除去する純粋関数:

- `第 N 章` → `第N章` (章・節パターン)
- `N. N` → `N.N` (番号内スペース)

**実装のポイント**: 番号内スペース除去は while ループで複数回適用し、`1. 1. 1` → `1.1.1` のような3階層パターンにも対応。

### is_special_marker()

特殊マーカー(■◆□●◇▲)で始まるかを判定する純粋関数:

- セット検索で O(1) 判定
- 先頭スペースを無視して判定

### extract_headings()

book.md から見出し行(##, ###)を抽出する純粋関数:

- h1, h4 以上は除外
- 番号・タイトル・カテゴリを自動分類
- ヘルパー関数 `_parse_heading_text()` で分類ロジックを分離

### classify_heading_patterns()

見出しリストを3カテゴリ(NUMBERED, UNNUMBERED, SPECIAL_MARKER)に分類し、レポートを生成:

- 代表例を各カテゴリ3件まで収集
- 不変な PatternReport を返却

## Test Results

```
============================= test session starts ==============================
...
tests/book_converter/parser/test_heading_normalizer.py::TestNormalizeNumberFormat::test_normalize_hyphen_to_dot_simple PASSED
tests/book_converter/parser/test_heading_normalizer.py::TestNormalizeNumberFormat::test_normalize_fullwidth_to_halfwidth_numbers PASSED
tests/book_converter/parser/test_heading_normalizer.py::TestNormalizeSpaces::test_normalize_chapter_spaces PASSED
tests/book_converter/parser/test_heading_normalizer.py::TestNormalizeSpaces::test_normalize_number_spaces_three_levels PASSED
tests/book_converter/parser/test_heading_normalizer.py::TestIsSpecialMarker::test_is_special_marker_square PASSED
tests/book_converter/parser/test_heading_normalizer.py::TestExtractHeadings::test_extract_headings_basic PASSED
tests/book_converter/parser/test_heading_normalizer.py::TestExtractHeadings::test_extract_headings_numbered_category PASSED
tests/book_converter/parser/test_heading_normalizer.py::TestClassifyHeadingPatterns::test_classify_all_numbered PASSED
tests/book_converter/parser/test_heading_normalizer.py::TestClassifyHeadingPatterns::test_classify_large_dataset PASSED
...
============================== 62 passed in 0.15s ==============================
```

**全テスト結果**: 914 passed, 6 skipped (book_converter module のみ)

**Coverage**: 99% (src/book_converter/parser/heading_normalizer.py - 100 lines, 1 line not covered)

カバレッジ詳細:
- 未カバーは while ループ内の break 文 (line 150) のみ
- 全ての関数とエッジケースがテストされている

## Discovered Issues

特になし。全テストが PASS し、リグレッションも発生していない。

## Handoff to Next Phase

Items to implement in Phase 3 (US2 - TOC-本文マッチング):
- **heading_matcher.py** を新規作成し、TOCEntry と本文見出しのマッチングロジックを実装
- `match_toc_to_body()`: 完全一致 → 番号除去一致 → ファジーマッチのカスケード
- `find_similar_candidate()`: difflib.SequenceMatcher を使用した類似候補検索 (similarity ≥ 0.8)
- MatchResult モデルを使用してマッチング結果を返却

**Reusable APIs from this phase**:
- `normalize_number_format()`: TOC/本文の番号統一に利用可能
- `normalize_spaces()`: マッチング前の前処理に利用可能
- `is_special_marker()`: EXCLUDED カテゴリ判定に利用可能
- `extract_headings()`: 本文見出しリストの取得に利用可能

**Caveats**:
- `normalize_spaces()` の while ループは最大10回など制限を設けていないが、現実的には2-3回で収束するため問題なし
- 正規表現パターンは日本語書籍を想定しているが、英語書籍でも動作する
