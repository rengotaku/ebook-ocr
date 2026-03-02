# Phase 3 RED Tests: US2 - TOC形式への見出し正規化

**Date**: 2026-03-02
**Status**: RED (FAIL verified)
**User Story**: US2 - TOC形式への見出し正規化

## Summary

| Item | Value |
|------|-------|
| Tests Created | 32 |
| Failed Count | 32 |
| Passed Count | 5 (MatchResult モデル構築テストのみ) |
| Test Files | tests/book_converter/test_heading_matcher.py, tests/book_converter/test_normalization_rules.py |

## Failed Tests

| Test File | Test Method | Expected Behavior |
|-----------|-------------|-------------------|
| test_heading_matcher.py | TestMatchResultModel::test_match_result_exact_similarity_is_one | EXACT マッチで similarity == 1.0 |
| test_heading_matcher.py | TestMatchResultModel::test_match_result_fuzzy_similarity_range | FUZZY マッチで 0.8 <= similarity < 1.0 |
| test_heading_matcher.py | TestMatchResultModel::test_match_result_missing_body_heading_is_none | MISSING で body_heading is None |
| test_heading_matcher.py | TestMatchResultModel::test_match_result_excluded | EXCLUDED で特殊マーカー付き見出し |
| test_heading_matcher.py | TestMatchResultModel::test_match_result_is_frozen | frozen dataclass (immutability) |
| test_heading_matcher.py | TestExactMatching::test_match_exact_title | TOCタイトルと本文見出しの完全一致 |
| test_heading_matcher.py | TestExactMatching::test_match_exact_with_number | 番号含む完全一致 |
| test_heading_matcher.py | TestExactMatching::test_match_exact_multiple_entries | 複数エントリの完全一致 |
| test_heading_matcher.py | TestExactMatching::test_match_exact_no_number_entry | 番号なしTOCエントリの完全一致 |
| test_heading_matcher.py | TestNumberRemovalMatching::test_match_after_number_removal | 番号除去後のタイトル一致 |
| test_heading_matcher.py | TestNumberRemovalMatching::test_match_after_number_removal_three_levels | 3階層番号での番号除去一致 |
| test_heading_matcher.py | TestNumberRemovalMatching::test_match_number_removal_with_body_having_different_number | 異なる番号でもタイトル一致 |
| test_heading_matcher.py | TestFuzzyMatching::test_fuzzy_match_above_threshold | 類似度80%以上でFUZZY判定 |
| test_heading_matcher.py | TestFuzzyMatching::test_fuzzy_match_below_threshold | 類似度80%未満でMISSING判定 |
| test_heading_matcher.py | TestFuzzyMatching::test_fuzzy_match_with_ocr_error | OCR誤認識を含む見出しのファジーマッチ |
| test_heading_matcher.py | TestFuzzyMatching::test_fuzzy_match_custom_threshold | カスタム閾値での感度調整 |
| test_heading_matcher.py | TestFuzzyMatching::test_fuzzy_match_unicode_special_chars | Unicode特殊文字を含む見出し |
| test_heading_matcher.py | TestMatchingEdgeCases::test_empty_toc_entries | 空TOCエントリ |
| test_heading_matcher.py | TestMatchingEdgeCases::test_empty_body_headings | 空本文見出し -> 全MISSING |
| test_heading_matcher.py | TestMatchingEdgeCases::test_both_empty | TOC/本文両方空 |
| test_heading_matcher.py | TestMatchingEdgeCases::test_duplicate_headings_match_by_order | 同名見出しの順序マッチ |
| test_heading_matcher.py | TestMatchingEdgeCases::test_special_marker_heading_excluded | 特殊マーカー見出しの除外 |
| test_heading_matcher.py | TestMatchingEdgeCases::test_large_dataset_performance | 1000件のパフォーマンス |
| test_heading_matcher.py | TestMatchingEdgeCases::test_emoji_in_heading | 絵文字を含む見出し |
| test_heading_matcher.py | TestMatchingEdgeCases::test_sql_special_chars_in_heading | SQL特殊文字を含む見出し |
| test_normalization_rules.py | TestGenerateRules::test_generate_rule_add_number | 番号付与ルール生成 |
| test_normalization_rules.py | TestGenerateRules::test_generate_rule_add_marker | マーカー付与ルール生成 |
| test_normalization_rules.py | TestGenerateRules::test_generate_rule_format_only | フォーマットのみ正規化 |
| test_normalization_rules.py | TestGenerateRules::test_generate_rule_none_already_correct | 変更不要ルール |
| test_normalization_rules.py | TestGenerateRules::test_generate_rule_missing_skipped | MISSINGはスキップ |
| test_normalization_rules.py | TestGenerateRules::test_generate_rules_multiple_matches | 複数マッチからのルール生成 |
| test_normalization_rules.py | TestGenerateRulesEdgeCases::test_generate_rules_empty_matches | 空マッチリスト |
| test_normalization_rules.py | TestGenerateRulesEdgeCases::test_generate_rules_excluded_match | EXCLUDEDはスキップ |
| test_normalization_rules.py | TestGenerateRulesEdgeCases::test_generated_rule_is_frozen | frozen dataclass確認 |
| test_normalization_rules.py | TestGenerateRulesEdgeCases::test_generate_rule_preserves_line_number | 行番号保持 |
| test_normalization_rules.py | TestGenerateRulesEdgeCases::test_generate_rule_with_special_chars | 特殊文字を含むルール |
| test_normalization_rules.py | TestGenerateRulesEdgeCases::test_generate_rule_fuzzy_match_add_number | ファジーマッチの番号付与 |

## Implementation Hints

- `match_toc_to_body()`: 完全一致 -> 番号除去一致 -> ファジーマッチのカスケード戦略。difflib.SequenceMatcher を使用
- `generate_rules()`: MatchResult の match_type と body_heading の状態から NormalizationAction を判定
- Edge cases: 空リスト、同名見出し重複、特殊マーカー除外、1000件規模のデータ

## Stub Files Created

| File | Purpose |
|------|---------|
| src/book_converter/heading_matcher.py | match_toc_to_body() スタブ (NotImplementedError) |
| src/book_converter/normalization_rules.py | generate_rules() スタブ (NotImplementedError) |

## Models Added

| Model | Location | Fields |
|-------|----------|--------|
| MatchResult | src/book_converter/models.py | toc_entry, body_heading, match_type, similarity, line_number |
| NormalizationRule | src/book_converter/models.py | original, normalized, line_number, action |

## make test Output (excerpt)

```
FAILED tests/book_converter/test_heading_matcher.py::TestExactMatching::test_match_exact_title - NotImplementedError: match_toc_to_body is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestExactMatching::test_match_exact_with_number - NotImplementedError: match_toc_to_body is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestExactMatching::test_match_exact_multiple_entries - NotImplementedError: match_toc_to_body is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestExactMatching::test_match_exact_no_number_entry - NotImplementedError: match_toc_to_body is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestNumberRemovalMatching::test_match_after_number_removal - NotImplementedError: match_toc_to_body is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestNumberRemovalMatching::test_match_after_number_removal_three_levels - NotImplementedError: match_toc_to_body is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestNumberRemovalMatching::test_match_number_removal_with_body_having_different_number - NotImplementedError: match_toc_to_body is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestFuzzyMatching::test_fuzzy_match_above_threshold - NotImplementedError: match_toc_to_body is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestFuzzyMatching::test_fuzzy_match_below_threshold - NotImplementedError: match_toc_to_body is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestFuzzyMatching::test_fuzzy_match_with_ocr_error - NotImplementedError: match_toc_to_body is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestFuzzyMatching::test_fuzzy_match_custom_threshold - NotImplementedError: match_toc_to_body is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestFuzzyMatching::test_fuzzy_match_unicode_special_chars - NotImplementedError: match_toc_to_body is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestMatchingEdgeCases::test_empty_toc_entries - NotImplementedError: match_toc_to_body is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestMatchingEdgeCases::test_empty_body_headings - NotImplementedError: match_toc_to_body is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestMatchingEdgeCases::test_both_empty - NotImplementedError: match_toc_to_body is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestMatchingEdgeCases::test_duplicate_headings_match_by_order - NotImplementedError: match_toc_to_body is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestMatchingEdgeCases::test_special_marker_heading_excluded - NotImplementedError: match_toc_to_body is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestMatchingEdgeCases::test_large_dataset_performance - NotImplementedError: match_toc_to_body is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestMatchingEdgeCases::test_emoji_in_heading - NotImplementedError: match_toc_to_body is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestMatchingEdgeCases::test_sql_special_chars_in_heading - NotImplementedError: match_toc_to_body is not yet implemented
FAILED tests/book_converter/test_normalization_rules.py::TestGenerateRules::test_generate_rule_add_number - NotImplementedError: generate_rules is not yet implemented
FAILED tests/book_converter/test_normalization_rules.py::TestGenerateRules::test_generate_rule_add_marker - NotImplementedError: generate_rules is not yet implemented
FAILED tests/book_converter/test_normalization_rules.py::TestGenerateRules::test_generate_rule_format_only - NotImplementedError: generate_rules is not yet implemented
FAILED tests/book_converter/test_normalization_rules.py::TestGenerateRules::test_generate_rule_none_already_correct - NotImplementedError: generate_rules is not yet implemented
FAILED tests/book_converter/test_normalization_rules.py::TestGenerateRules::test_generate_rule_missing_skipped - NotImplementedError: generate_rules is not yet implemented
FAILED tests/book_converter/test_normalization_rules.py::TestGenerateRules::test_generate_rules_multiple_matches - NotImplementedError: generate_rules is not yet implemented
FAILED tests/book_converter/test_normalization_rules.py::TestGenerateRulesEdgeCases::test_generate_rules_empty_matches - NotImplementedError: generate_rules is not yet implemented
FAILED tests/book_converter/test_normalization_rules.py::TestGenerateRulesEdgeCases::test_generate_rules_excluded_match - NotImplementedError: generate_rules is not yet implemented
FAILED tests/book_converter/test_normalization_rules.py::TestGenerateRulesEdgeCases::test_generated_rule_is_frozen - NotImplementedError: generate_rules is not yet implemented
FAILED tests/book_converter/test_normalization_rules.py::TestGenerateRulesEdgeCases::test_generate_rule_preserves_line_number - NotImplementedError: generate_rules is not yet implemented
FAILED tests/book_converter/test_normalization_rules.py::TestGenerateRulesEdgeCases::test_generate_rule_with_special_chars - NotImplementedError: generate_rules is not yet implemented
FAILED tests/book_converter/test_normalization_rules.py::TestGenerateRulesEdgeCases::test_generate_rule_fuzzy_match_add_number - NotImplementedError: generate_rules is not yet implemented
32 failed, 5 passed in 0.23s
```

## Existing Tests (regression check)

```
1549 passed, 6 skipped, 6 warnings in 165.92s
```

既存テストにリグレッションなし。
