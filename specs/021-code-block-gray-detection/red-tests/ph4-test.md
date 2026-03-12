# Phase 4 RED Tests: US4 断片化コードブロックの結合

**Date**: 2026-03-13
**Status**: RED (FAIL verified)
**User Story**: US4 - 断片化コードブロックの結合

## サマリ

| 項目 | 値 |
|------|-------|
| 作成テスト数 | 33 |
| 失敗数 | 33 |
| テストファイル | tests/test_code_detector.py |

## 失敗テスト一覧

### T055: is_code_fragment() テスト (12件)

| テストファイル | テストメソッド | 期待動作 |
|-----------|-------------|-------------------|
| tests/test_code_detector.py | TestIsCodeFragment::test_closing_brace_is_fragment | "}" -> True |
| tests/test_code_detector.py | TestIsCodeFragment::test_opening_brace_is_fragment | "{" -> True |
| tests/test_code_detector.py | TestIsCodeFragment::test_ocr_misread_3_is_fragment | "3" (OCR誤読) -> True |
| tests/test_code_detector.py | TestIsCodeFragment::test_short_code_like_text_is_fragment | "});" -> True (短い記号テキスト) |
| tests/test_code_detector.py | TestIsCodeFragment::test_japanese_text_is_not_fragment | 日本語テキスト -> False |
| tests/test_code_detector.py | TestIsCodeFragment::test_long_text_is_not_fragment | 長いテキスト -> False |
| tests/test_code_detector.py | TestIsCodeFragment::test_empty_string_is_not_fragment | 空文字列 -> False |
| tests/test_code_detector.py | TestIsCodeFragment::test_none_input_is_not_fragment | None -> False |
| tests/test_code_detector.py | TestIsCodeFragment::test_returns_bool | 戻り値が bool |
| tests/test_code_detector.py | TestIsCodeFragment::test_semicolon_is_fragment | ";" -> True |
| tests/test_code_detector.py | TestIsCodeFragment::test_short_symbols_bracket_paren | "])" -> True |
| tests/test_code_detector.py | TestIsCodeFragment::test_whitespace_only_is_not_fragment | 空白のみ -> False |

### T056: merge_code_fragments() 隣接結合テスト (6件)

| テストファイル | テストメソッド | 期待動作 |
|-----------|-------------|-------------------|
| tests/test_code_detector.py | TestMergeCodeFragmentsAdjacentMerge::test_two_adjacent_codes_merged | CODE+CODE (gap=50px<80px) -> 1つのCODE |
| tests/test_code_detector.py | TestMergeCodeFragmentsAdjacentMerge::test_merged_bbox_is_bounding_rect | 結合後bboxが外接矩形 |
| tests/test_code_detector.py | TestMergeCodeFragmentsAdjacentMerge::test_three_adjacent_codes_merged | 3つの隣接CODE -> 1つ |
| tests/test_code_detector.py | TestMergeCodeFragmentsAdjacentMerge::test_single_code_returned_as_is | 単一CODE -> そのまま |
| tests/test_code_detector.py | TestMergeCodeFragmentsAdjacentMerge::test_empty_list_returns_empty | 空リスト -> 空リスト |
| tests/test_code_detector.py | TestMergeCodeFragmentsAdjacentMerge::test_returns_list | 戻り値がlist |

### T057: merge_code_fragments() 結合打ち切りテスト (3件)

| テストファイル | テストメソッド | 期待動作 |
|-----------|-------------|-------------------|
| tests/test_code_detector.py | TestMergeCodeFragmentsMergeBreak::test_code_text_code_produces_two_codes | CODE+TEXT+CODE -> 2つのCODE |
| tests/test_code_detector.py | TestMergeCodeFragmentsMergeBreak::test_text_region_preserved | TEXT領域が出力に保持 |
| tests/test_code_detector.py | TestMergeCodeFragmentsMergeBreak::test_code_title_code_not_merged | CODE+TITLE+CODE -> 結合なし |

### T058: merge_code_fragments() FRAG 結合テスト (5件)

| テストファイル | テストメソッド | 期待動作 |
|-----------|-------------|-------------------|
| tests/test_code_detector.py | TestMergeCodeFragmentsFragMerge::test_code_frag_code_merged | CODE+TEXT("}")+CODE -> 1つ |
| tests/test_code_detector.py | TestMergeCodeFragmentsFragMerge::test_code_frag_ocr_misread_code_merged | CODE+TEXT("3")+CODE -> 1つ |
| tests/test_code_detector.py | TestMergeCodeFragmentsFragMerge::test_frag_merged_bbox_covers_all | FRAG含む結合bboxが3領域をカバー |
| tests/test_code_detector.py | TestMergeCodeFragmentsFragMerge::test_code_frag_brace_opening_code_merged | CODE+TEXT("{")+CODE -> 1つ |
| tests/test_code_detector.py | TestMergeCodeFragmentsFragMerge::test_non_fragment_text_breaks_merge | CODE+長いTEXT+CODE -> 2つ |

### T059: merge_code_fragments() ギャップ超過テスト (3件)

| テストファイル | テストメソッド | 期待動作 |
|-----------|-------------|-------------------|
| tests/test_code_detector.py | TestMergeCodeFragmentsGapExceeded::test_large_gap_not_merged | gap=150px>80px -> 結合しない |
| tests/test_code_detector.py | TestMergeCodeFragmentsGapExceeded::test_custom_gap_threshold | カスタム閾値が尊重される |
| tests/test_code_detector.py | TestMergeCodeFragmentsGapExceeded::test_exact_threshold_boundary | 閾値境界の一貫した動作 |

### T060: merge_code_fragments() イミュータブル性テスト (4件)

| テストファイル | テストメソッド | 期待動作 |
|-----------|-------------|-------------------|
| tests/test_code_detector.py | TestMergeCodeFragmentsImmutability::test_input_list_not_mutated | 入力リストが変更されない |
| tests/test_code_detector.py | TestMergeCodeFragmentsImmutability::test_input_region_dicts_not_mutated | 入力dictが変更されない |
| tests/test_code_detector.py | TestMergeCodeFragmentsImmutability::test_input_bbox_lists_not_mutated | bbox配列が変更されない |
| tests/test_code_detector.py | TestMergeCodeFragmentsImmutability::test_result_is_new_list | 戻り値が新しいリスト |

## 実装ヒント

- `is_code_fragment(text)`: 短いテキスト(<20文字)で記号比率が高い or `}` / `{` / `3` (OCR誤読) のみ -> True。None/空/空白 -> False
- `merge_code_fragments(regions, gap_threshold=80)`: y座標ソート済みregionsを走査。隣接CODE/FRAGをgap閾値で結合。non-CODEかつnon-FRAGが来たら結合打ち切り。結合bbox=外接矩形。イミュータブル（入力変更不可）
- エッジケース: 空リスト、単一要素、None入力、境界値gap

## make test 出力 (抜粋)

```
FAILED tests/test_code_detector.py::TestIsCodeFragment::test_closing_brace_is_fragment - ImportError: cannot import name 'is_code_fragment'
FAILED tests/test_code_detector.py::TestIsCodeFragment::test_opening_brace_is_fragment - ImportError: cannot import name 'is_code_fragment'
FAILED tests/test_code_detector.py::TestMergeCodeFragmentsAdjacentMerge::test_two_adjacent_codes_merged - ImportError: cannot import name 'merge_code_fragments'
FAILED tests/test_code_detector.py::TestMergeCodeFragmentsMergeBreak::test_code_text_code_produces_two_codes - ImportError: cannot import name 'merge_code_fragments'
FAILED tests/test_code_detector.py::TestMergeCodeFragmentsFragMerge::test_code_frag_code_merged - ImportError: cannot import name 'merge_code_fragments'
FAILED tests/test_code_detector.py::TestMergeCodeFragmentsGapExceeded::test_large_gap_not_merged - ImportError: cannot import name 'merge_code_fragments'
FAILED tests/test_code_detector.py::TestMergeCodeFragmentsImmutability::test_input_list_not_mutated - ImportError: cannot import name 'merge_code_fragments'
... (33 tests total)
=== 33 failed, 1643 passed, 2 skipped, 131 deselected, 6 warnings in 28.34s ===
```
