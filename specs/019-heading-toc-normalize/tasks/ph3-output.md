# Phase 3 Output: US2 - TOC形式への見出し正規化

**Date**: 2026-03-03
**Status**: Completed
**User Story**: US2 - TOC形式への見出し正規化

## Executed Tasks

- [x] T033 RED テストを読む: specs/019-heading-toc-normalize/red-tests/ph3-test.md
- [x] T034 [P] [US2] MatchResult データクラスを追加: src/book_converter/models.py
- [x] T035 [P] [US2] NormalizationRule データクラスを追加: src/book_converter/models.py
- [x] T036 [US2] match_toc_to_body() を実装: src/book_converter/heading_matcher.py
- [x] T037 [US2] generate_rules() を実装: src/book_converter/normalization_rules.py
- [x] T038 `make test` で PASS を確認 (GREEN)
- [x] T039 `make test` で全テスト PASS を確認（US1 含む）
- [x] T040 `make coverage` でカバレッジ ≥80% を確認
- [x] T041 フェーズ結果を出力: specs/019-heading-toc-normalize/tasks/ph3-output.md

## Changed Files

| File | Change Type | Summary |
|------|-------------|---------|
| src/book_converter/heading_matcher.py | Modified | match_toc_to_body() を実装（stub から完全実装へ） |
| src/book_converter/normalization_rules.py | Modified | generate_rules() を実装（stub から完全実装へ） |
| specs/019-heading-toc-normalize/tasks.md | Modified | T033-T041 を完了としてマーク |

## Implementation Details

### match_toc_to_body()

TOCエントリと本文見出しをマッチングする中核的な関数を実装:

**マッチング戦略** (優先順位順):
1. **完全一致**: TOCタイトルと本文見出しが完全一致（番号の有無問わず）
2. **番号除去一致**: 本文見出しから番号パターンを除去後に一致
3. **ファジーマッチ**: difflib.SequenceMatcher で類似度 ≥ threshold (default 0.8)
4. **MISSING**: マッチなし

**実装のポイント**:
- `normalize_number_format()` と `normalize_spaces()` で正規化してから比較
- `is_special_marker()` で特殊マーカー付き見出しをスキップ
- 一度マッチした見出しは再利用しない（順序保持）
- difflib.SequenceMatcher を使用したファジーマッチ

**エッジケース対応**:
- 空リスト処理
- 同名見出しの重複（出現順序で区別）
- 1000件規模のデータでもパフォーマンス問題なし

### generate_rules()

MatchResult から NormalizationRule を生成する関数を実装:

**ルール判定ロジック**:
- `body_heading.level == 0` → ADD_MARKER (マーカーなしプレーンテキスト)
- 番号なし + TOC番号あり → ADD_NUMBER
- 番号フォーマット不一致 (1-1 vs 1.1) → FORMAT_ONLY
- 既に正しい形式 → ルール生成なし (スキップ)

**除外パターン**:
- MatchType.MISSING → スキップ
- MatchType.EXCLUDED → スキップ

**正規化内容**:
- Markdown マーカー: TOC level に基づき # / ## / ### を追加
- 番号付与: TOC番号を見出しテキストに追加
- フォーマット正規化: 1-1 → 1.1 のドット区切り統一

## Test Results

```
============================= test session starts ==============================
...
tests/book_converter/test_heading_matcher.py::TestMatchResultModel::test_match_result_exact_similarity_is_one PASSED
tests/book_converter/test_heading_matcher.py::TestMatchResultModel::test_match_result_fuzzy_similarity_range PASSED
tests/book_converter/test_heading_matcher.py::TestMatchResultModel::test_match_result_missing_body_heading_is_none PASSED
tests/book_converter/test_heading_matcher.py::TestMatchResultModel::test_match_result_excluded PASSED
tests/book_converter/test_heading_matcher.py::TestMatchResultModel::test_match_result_is_frozen PASSED
tests/book_converter/test_heading_matcher.py::TestExactMatching::test_match_exact_title PASSED
tests/book_converter/test_heading_matcher.py::TestExactMatching::test_match_exact_with_number PASSED
tests/book_converter/test_heading_matcher.py::TestExactMatching::test_match_exact_multiple_entries PASSED
tests/book_converter/test_heading_matcher.py::TestExactMatching::test_match_exact_no_number_entry PASSED
tests/book_converter/test_heading_matcher.py::TestNumberRemovalMatching::test_match_after_number_removal PASSED
tests/book_converter/test_heading_matcher.py::TestNumberRemovalMatching::test_match_after_number_removal_three_levels PASSED
tests/book_converter/test_heading_matcher.py::TestNumberRemovalMatching::test_match_number_removal_with_body_having_different_number PASSED
tests/book_converter/test_heading_matcher.py::TestFuzzyMatching::test_fuzzy_match_above_threshold PASSED
tests/book_converter/test_heading_matcher.py::TestFuzzyMatching::test_fuzzy_match_below_threshold PASSED
tests/book_converter/test_heading_matcher.py::TestFuzzyMatching::test_fuzzy_match_with_ocr_error PASSED
tests/book_converter/test_heading_matcher.py::TestFuzzyMatching::test_fuzzy_match_custom_threshold PASSED
tests/book_converter/test_heading_matcher.py::TestFuzzyMatching::test_fuzzy_match_unicode_special_chars PASSED
tests/book_converter/test_heading_matcher.py::TestMatchingEdgeCases::test_empty_toc_entries PASSED
tests/book_converter/test_heading_matcher.py::TestMatchingEdgeCases::test_empty_body_headings PASSED
tests/book_converter/test_heading_matcher.py::TestMatchingEdgeCases::test_both_empty PASSED
tests/book_converter/test_heading_matcher.py::TestMatchingEdgeCases::test_duplicate_headings_match_by_order PASSED
tests/book_converter/test_heading_matcher.py::TestMatchingEdgeCases::test_special_marker_heading_excluded PASSED
tests/book_converter/test_heading_matcher.py::TestMatchingEdgeCases::test_large_dataset_performance PASSED
tests/book_converter/test_heading_matcher.py::TestMatchingEdgeCases::test_emoji_in_heading PASSED
tests/book_converter/test_heading_matcher.py::TestMatchingEdgeCases::test_sql_special_chars_in_heading PASSED
============================== 25 passed in 0.19s ==============================

tests/book_converter/test_normalization_rules.py::TestGenerateRules::test_generate_rule_add_number PASSED
tests/book_converter/test_normalization_rules.py::TestGenerateRules::test_generate_rule_add_marker PASSED
tests/book_converter/test_normalization_rules.py::TestGenerateRules::test_generate_rule_format_only PASSED
tests/book_converter/test_normalization_rules.py::TestGenerateRules::test_generate_rule_none_already_correct PASSED
tests/book_converter/test_normalization_rules.py::TestGenerateRules::test_generate_rule_missing_skipped PASSED
tests/book_converter/test_normalization_rules.py::TestGenerateRules::test_generate_rules_multiple_matches PASSED
tests/book_converter/test_normalization_rules.py::TestGenerateRulesEdgeCases::test_generate_rules_empty_matches PASSED
tests/book_converter/test_normalization_rules.py::TestGenerateRulesEdgeCases::test_generate_rules_excluded_match PASSED
tests/book_converter/test_normalization_rules.py::TestGenerateRulesEdgeCases::test_generated_rule_is_frozen PASSED
tests/book_converter/test_normalization_rules.py::TestGenerateRulesEdgeCases::test_generate_rule_preserves_line_number PASSED
tests/book_converter/test_normalization_rules.py::TestGenerateRulesEdgeCases::test_generate_rule_with_special_chars PASSED
tests/book_converter/test_normalization_rules.py::TestGenerateRulesEdgeCases::test_generate_rule_fuzzy_match_add_number PASSED
============================== 12 passed in 0.15s ==============================

=========== 1586 passed, 6 skipped, 6 warnings in 155.56s (0:02:35) ============
```

**全テスト結果**: 1586 passed, 6 skipped (全プロジェクト)

**Coverage**:
- `heading_matcher.py`: 100% (47 lines, 0 missed)
- `normalization_rules.py`: 88% (50 lines, 6 missed)
- Total project coverage: 62%

カバレッジ詳細:
- heading_matcher.py は完全にカバー
- normalization_rules.py の未カバーは未到達の分岐ロジック (6行)
- 両モジュールとも目標の80%を達成

## Discovered Issues

特になし。全テストが PASS し、リグレッションも発生していない。

## Handoff to Next Phase

Items to implement in Phase 4 (US3 - 正規化ルール適用):
- **CLI統合**: normalize_headings.py を新規作成し、3つのサブコマンドを実装
  - `report`: 見出しパターン分析レポート
  - `normalize`: 正規化（dry-run / --apply）
  - `validate`: TOC検証レポート
- **sed スクリプト生成**: generate_sed_script() を実装
- **適用機能**: apply_rules() を実装

**Reusable APIs from this phase**:
- `match_toc_to_body()`: TOC-本文マッチングエンジン（完全一致 → 番号除去 → ファジー）
- `generate_rules()`: マッチング結果から正規化ルールを生成
- MatchResult, NormalizationRule モデル: 不変データ構造

**Caveats**:
- `match_toc_to_body()` は一度マッチした見出しを再利用しないため、同名見出しは出現順序で区別される
- ファジーマッチの閾値はデフォルト 0.8 だが、similarity_threshold 引数でカスタマイズ可能
- `generate_rules()` は level=0 を「マーカーなし」として扱う（ADD_MARKER アクション）
