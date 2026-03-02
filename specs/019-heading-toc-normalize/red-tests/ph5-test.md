# Phase 5 RED Tests: US4 - 正規化結果の検証

**Date**: 2026-03-03
**Status**: RED (FAIL verified)
**User Story**: US4 - 正規化結果の検証

## Summary

| Item | Value |
|------|-------|
| 新規テスト数 | 28 (モデル8 + スタブ関数20) |
| FAIL 数 | 20 (スタブ関数テスト) |
| PASS 数 (新規モデル) | 8 (ValidationReport データクラス) |
| PASS 数 (既存Phase3) | 25 |
| テストファイル | tests/book_converter/test_heading_matcher.py |

## 変更ファイル

| ファイル | 変更内容 |
|----------|----------|
| src/book_converter/models.py | ValidationReport データクラスを追加 |
| src/book_converter/heading_matcher.py | find_similar_candidate(), generate_validation_report(), format_validation_report() スタブを追加 |
| tests/book_converter/test_heading_matcher.py | Phase 5 テスト (20件) を追加 |

## FAIL テスト一覧

### T058: ValidationReport モデルテスト

| テストメソッド | 期待する動作 |
|---------------|-------------|
| test_validation_report_match_rate | match_rate が正しく設定される (38/42) |
| test_validation_report_match_rate_zero | マッチ数0の場合 match_rate=0.0 |
| test_validation_report_match_rate_full | 全マッチの場合 match_rate=1.0 |
| test_validation_report_missing_entries | 未マッチの TocEntry がタプルに含まれる |
| test_validation_report_missing_entries_empty | 未マッチなしの場合は空タプル |
| test_validation_report_excluded_headings | 特殊マーカー付き見出しが excluded に含まれる |
| test_validation_report_is_frozen | frozen dataclass で immutability 保証 |
| test_validation_report_empty_toc | TOCエントリ数0の場合のレポート |

### T059: 類似候補表示テスト

| テストメソッド | 期待する動作 |
|---------------|-------------|
| test_find_similar_candidate_above_threshold | 閾値以上の類似候補が返される |
| test_find_similar_candidate_exact_match | 完全一致の見出しが類似度1.0で返される |
| test_find_similar_candidate_none | 閾値未満の場合 None |
| test_find_similar_candidate_empty_headings | 空リストの場合 None |
| test_find_similar_candidate_best_match | 最も類似度が高い候補が返される |
| test_find_similar_candidate_special_marker_excluded | 特殊マーカーの扱いを検証 |
| test_find_similar_candidate_custom_threshold | カスタム閾値で感度を調整 |

### T060: レポート出力テスト

| テストメソッド | 期待する動作 |
|---------------|-------------|
| test_generate_report_basic | 基本的なレポート生成 (マッチ率計算) |
| test_generate_report_all_matched | 全マッチの場合 match_rate=1.0 |
| test_generate_report_none_matched | 全未マッチの場合 match_rate=0.0 |
| test_generate_report_excluded_headings | 除外見出しがレポートに含まれる |
| test_generate_report_empty_matches | 空マッチリストでもエラーにならない |
| test_generate_report_fuzzy_counted_as_matched | FUZZY もマッチ数にカウント |
| test_format_validation_report_table | テーブル形式出力に EXACT, TOC Entry 等が含まれる |
| test_format_validation_report_summary | サマリーに TOC Entries, Matched 等の数値が含まれる |
| test_format_validation_report_missing_with_similar | MISSING エントリに類似候補が表示される |
| test_format_validation_report_excluded_section | Excluded セクションに特殊マーカー見出しが表示される |
| test_validation_report_exit_code_zero_with_missing | MISSING 時 WARN + Exit: 0 |
| test_validation_report_exit_code_zero_all_matched | 全マッチ時 Exit: 0 |
| test_format_validation_report_empty | 空レポートでもエラーにならない |

## 実装ヒント

- `find_similar_candidate()`: difflib.SequenceMatcher で TOCエントリのテキストと見出しテキストの類似度を計算。閾値以上の最高類似度を返す
- `generate_validation_report()`: matches リストから EXACT/FUZZY を matched、MISSING を missing_entries に分類。headings から is_special_marker() で excluded を抽出
- `format_validation_report()`: spec.md の出力例に従いテーブル形式で出力。Summary, Match Details, Excluded, Status, Exit を含む
- エッジケース: 空リスト、match_rate の 0 除算回避、特殊マーカーの扱い

## make test 出力 (抜粋)

```
FAILED tests/book_converter/test_heading_matcher.py::TestFindSimilarCandidate::test_find_similar_candidate_above_threshold - NotImplementedError: find_similar_candidate is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestFindSimilarCandidate::test_find_similar_candidate_exact_match - NotImplementedError: find_similar_candidate is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestFindSimilarCandidate::test_find_similar_candidate_none - NotImplementedError: find_similar_candidate is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestFindSimilarCandidate::test_find_similar_candidate_empty_headings - NotImplementedError: find_similar_candidate is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestFindSimilarCandidate::test_find_similar_candidate_best_match - NotImplementedError: find_similar_candidate is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestFindSimilarCandidate::test_find_similar_candidate_special_marker_excluded - NotImplementedError: find_similar_candidate is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestFindSimilarCandidate::test_find_similar_candidate_custom_threshold - NotImplementedError: find_similar_candidate is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestGenerateValidationReport::test_generate_report_basic - NotImplementedError: generate_validation_report is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestGenerateValidationReport::test_generate_report_all_matched - NotImplementedError: generate_validation_report is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestGenerateValidationReport::test_generate_report_none_matched - NotImplementedError: generate_validation_report is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestGenerateValidationReport::test_generate_report_excluded_headings - NotImplementedError: generate_validation_report is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestGenerateValidationReport::test_generate_report_empty_matches - NotImplementedError: generate_validation_report is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestGenerateValidationReport::test_generate_report_fuzzy_counted_as_matched - NotImplementedError: generate_validation_report is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestFormatValidationReport::test_format_validation_report_table - NotImplementedError: format_validation_report is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestFormatValidationReport::test_format_validation_report_summary - NotImplementedError: format_validation_report is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestFormatValidationReport::test_format_validation_report_missing_with_similar - NotImplementedError: format_validation_report is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestFormatValidationReport::test_format_validation_report_excluded_section - NotImplementedError: format_validation_report is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestFormatValidationReport::test_validation_report_exit_code_zero_with_missing - NotImplementedError: format_validation_report is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestFormatValidationReport::test_validation_report_exit_code_zero_all_matched - NotImplementedError: format_validation_report is not yet implemented
FAILED tests/book_converter/test_heading_matcher.py::TestFormatValidationReport::test_format_validation_report_empty - NotImplementedError: format_validation_report is not yet implemented
======================== 20 failed, 33 passed in 0.38s =========================
```

注: ValidationReport モデルテスト (8件) は PASS している。これは ValidationReport が純粋なデータクラスであり、スタブ関数を呼ばないため。FAIL しているのは find_similar_candidate (7件), generate_validation_report (6件), format_validation_report (7件) の計20件。
