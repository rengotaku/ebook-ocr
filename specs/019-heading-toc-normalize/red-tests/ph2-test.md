# Phase 2 RED Tests: US1 - 見出しパターンの自動抽出

**Date**: 2026-03-02
**Status**: RED (FAIL verified)
**User Story**: US1 - 見出しパターンの自動抽出

## Summary

| Item | Value |
|------|-------|
| テスト作成数 | 62 |
| 失敗数 | 62 |
| テストファイル | tests/book_converter/parser/test_heading_normalizer.py |

## 失敗テスト一覧

| テストファイル | テストメソッド | 期待する動作 |
|-----------|-------------|-------------------|
| test_heading_normalizer.py | TestNormalizeNumberFormat::test_normalize_hyphen_to_dot_simple | `1-1` → `1.1` ハイフンをドットに変換 |
| test_heading_normalizer.py | TestNormalizeNumberFormat::test_normalize_hyphen_to_dot_three_levels | `1-1-1` → `1.1.1` 3階層ハイフン変換 |
| test_heading_normalizer.py | TestNormalizeNumberFormat::test_normalize_hyphen_to_dot_with_title | `1-1-1 タイトル` のハイフン変換 |
| test_heading_normalizer.py | TestNormalizeNumberFormat::test_normalize_fullwidth_to_halfwidth_numbers | 全角数字・ドットを半角に変換 |
| test_heading_normalizer.py | TestNormalizeNumberFormat::test_normalize_fullwidth_to_halfwidth_three_levels | 3階層全角変換 |
| test_heading_normalizer.py | TestNormalizeNumberFormat::test_normalize_fullwidth_numbers_only | 全角数字のみ半角変換 |
| test_heading_normalizer.py | TestNormalizeNumberFormat::test_normalize_fullwidth_with_title | 全角番号+タイトル変換 |
| test_heading_normalizer.py | TestNormalizeNumberFormat::test_normalize_nakaguro_to_dot | 中黒をドットに変換 |
| test_heading_normalizer.py | TestNormalizeNumberFormat::test_normalize_nakaguro_to_dot_three_levels | 3階層中黒変換 |
| test_heading_normalizer.py | TestNormalizeNumberFormat::test_normalize_mixed_separators | 混合区切り変換 |
| test_heading_normalizer.py | TestNormalizeNumberFormat::test_normalize_already_normalized | 変換不要ケース |
| test_heading_normalizer.py | TestNormalizeNumberFormat::test_normalize_no_number | 番号なしテキスト |
| test_heading_normalizer.py | TestNormalizeNumberFormat::test_normalize_single_number | 単独数字 |
| test_heading_normalizer.py | TestNormalizeNumberFormat::test_normalize_empty_string | 空文字列 |
| test_heading_normalizer.py | TestNormalizeNumberFormat::test_normalize_fullwidth_zero | 全角ゼロ |
| test_heading_normalizer.py | TestNormalizeNumberFormat::test_normalize_large_numbers | 大きい番号 |
| test_heading_normalizer.py | TestNormalizeNumberFormat::test_normalize_preserves_non_number_hyphens | テキスト中ハイフン保持 |
| test_heading_normalizer.py | TestNormalizeSpaces::test_normalize_chapter_spaces | `第 1 章` → `第1章` |
| test_heading_normalizer.py | TestNormalizeSpaces::test_normalize_section_spaces | `第 2 節` → `第2節` |
| test_heading_normalizer.py | TestNormalizeSpaces::test_normalize_chapter_with_title | 章+タイトルのスペース正規化 |
| test_heading_normalizer.py | TestNormalizeSpaces::test_normalize_number_spaces_dot | `1. 1` → `1.1` |
| test_heading_normalizer.py | TestNormalizeSpaces::test_normalize_number_spaces_three_levels | `1. 1. 1` → `1.1.1` |
| test_heading_normalizer.py | TestNormalizeSpaces::test_normalize_number_spaces_with_title | 番号+タイトルのスペース正規化 |
| test_heading_normalizer.py | TestNormalizeSpaces::test_normalize_spaces_already_clean | 変換不要ケース |
| test_heading_normalizer.py | TestNormalizeSpaces::test_normalize_spaces_number_clean | 番号内スペースなし |
| test_heading_normalizer.py | TestNormalizeSpaces::test_normalize_spaces_title_space_preserved | タイトル前スペース保持 |
| test_heading_normalizer.py | TestNormalizeSpaces::test_normalize_spaces_empty_string | 空文字列 |
| test_heading_normalizer.py | TestNormalizeSpaces::test_normalize_spaces_only_spaces | スペースのみ |
| test_heading_normalizer.py | TestNormalizeSpaces::test_normalize_spaces_multiple_spaces_in_number | 複数スペース |
| test_heading_normalizer.py | TestNormalizeSpaces::test_normalize_spaces_chapter_double_digit | 2桁章番号 |
| test_heading_normalizer.py | TestIsSpecialMarker::test_is_special_marker_square | `■コードベース` → True |
| test_heading_normalizer.py | TestIsSpecialMarker::test_is_special_marker_diamond | `◆注意事項` → True |
| test_heading_normalizer.py | TestIsSpecialMarker::test_is_special_marker_white_square | `□補足` → True |
| test_heading_normalizer.py | TestIsSpecialMarker::test_is_special_marker_black_circle | `●概要` → True |
| test_heading_normalizer.py | TestIsSpecialMarker::test_is_special_marker_white_diamond | `◇参考` → True |
| test_heading_normalizer.py | TestIsSpecialMarker::test_is_special_marker_triangle | `▲警告` → True |
| test_heading_normalizer.py | TestIsSpecialMarker::test_is_special_marker_normal_text | 通常テキスト → False |
| test_heading_normalizer.py | TestIsSpecialMarker::test_is_special_marker_numbered | 番号付きテキスト → False |
| test_heading_normalizer.py | TestIsSpecialMarker::test_is_special_marker_english | 英語テキスト → False |
| test_heading_normalizer.py | TestIsSpecialMarker::test_is_special_marker_with_markdown | マーカー付きテキスト判定 |
| test_heading_normalizer.py | TestIsSpecialMarker::test_is_special_marker_empty | 空文字列 → False |
| test_heading_normalizer.py | TestIsSpecialMarker::test_is_special_marker_marker_only | マーカーのみ → True |
| test_heading_normalizer.py | TestIsSpecialMarker::test_is_special_marker_marker_in_middle | 途中マーカー → False |
| test_heading_normalizer.py | TestIsSpecialMarker::test_is_special_marker_with_space | マーカー後スペース → True |
| test_heading_normalizer.py | TestExtractHeadings::test_extract_headings_basic | `##` 行を抽出 |
| test_heading_normalizer.py | TestExtractHeadings::test_extract_headings_with_h3 | `###` も抽出 |
| test_heading_normalizer.py | TestExtractHeadings::test_extract_headings_line_numbers | 行番号記録 (1-indexed) |
| test_heading_normalizer.py | TestExtractHeadings::test_extract_headings_numbered_category | NUMBERED 分類 |
| test_heading_normalizer.py | TestExtractHeadings::test_extract_headings_unnumbered_category | UNNUMBERED 分類 |
| test_heading_normalizer.py | TestExtractHeadings::test_extract_headings_special_marker_category | SPECIAL_MARKER 分類 |
| test_heading_normalizer.py | TestExtractHeadings::test_extract_headings_empty_lines | 空リスト |
| test_heading_normalizer.py | TestExtractHeadings::test_extract_headings_no_headings | 見出しなし |
| test_heading_normalizer.py | TestExtractHeadings::test_extract_headings_h1_excluded | h1 除外 |
| test_heading_normalizer.py | TestExtractHeadings::test_extract_headings_h4_excluded | h4 除外 |
| test_heading_normalizer.py | TestExtractHeadings::test_extract_headings_preserves_order | 出現順序保持 |
| test_heading_normalizer.py | TestExtractHeadings::test_extract_headings_with_special_chars | Unicode/特殊文字 |
| test_heading_normalizer.py | TestClassifyHeadingPatterns::test_classify_all_numbered | 全て番号付き分類 |
| test_heading_normalizer.py | TestClassifyHeadingPatterns::test_classify_mixed_patterns | 混合パターン分類 |
| test_heading_normalizer.py | TestClassifyHeadingPatterns::test_classify_empty_list | 空リスト分類 |
| test_heading_normalizer.py | TestClassifyHeadingPatterns::test_classify_includes_examples | 代表例の確認 |
| test_heading_normalizer.py | TestClassifyHeadingPatterns::test_classify_report_is_immutable | 不変性テスト |
| test_heading_normalizer.py | TestClassifyHeadingPatterns::test_classify_large_dataset | 大量データ (1000件) |

## 実装ヒント

- `normalize_number_format()`: 正規表現で番号パターン (N-N, N・N, N．N) を検出し、ドット区切り半角に置換。テキスト中のハイフン (SRE-based) は番号パターンでないため保持する
- `normalize_spaces()`: `第\s+\d+\s+章` パターンのスペース除去、番号内 `\d+\.\s+\d+` のスペース除去
- `is_special_marker()`: 先頭文字が特殊マーカー文字セット (■◆□●◇▲) に含まれるか判定
- `extract_headings()`: `^#{2,3}\s` パターンで行を検出し、HeadingInfo を生成。番号・カテゴリの解析を含む
- `classify_heading_patterns()`: HeadingInfo の category フィールドで集計し PatternReport を生成

## make test 出力 (抜粋)

```
FAILED tests/book_converter/parser/test_heading_normalizer.py::TestNormalizeNumberFormat::test_normalize_hyphen_to_dot_simple - NotImplementedError: normalize_number_format is not implemented yet
FAILED tests/book_converter/parser/test_heading_normalizer.py::TestNormalizeNumberFormat::test_normalize_fullwidth_to_halfwidth_numbers - NotImplementedError: normalize_number_format is not implemented yet
FAILED tests/book_converter/parser/test_heading_normalizer.py::TestNormalizeNumberFormat::test_normalize_nakaguro_to_dot - NotImplementedError: normalize_number_format is not implemented yet
FAILED tests/book_converter/parser/test_heading_normalizer.py::TestNormalizeSpaces::test_normalize_chapter_spaces - NotImplementedError: normalize_spaces is not implemented yet
FAILED tests/book_converter/parser/test_heading_normalizer.py::TestNormalizeSpaces::test_normalize_number_spaces_dot - NotImplementedError: normalize_spaces is not implemented yet
FAILED tests/book_converter/parser/test_heading_normalizer.py::TestIsSpecialMarker::test_is_special_marker_square - NotImplementedError: is_special_marker is not implemented yet
FAILED tests/book_converter/parser/test_heading_normalizer.py::TestExtractHeadings::test_extract_headings_basic - NotImplementedError: extract_headings is not implemented yet
FAILED tests/book_converter/parser/test_heading_normalizer.py::TestClassifyHeadingPatterns::test_classify_all_numbered - NotImplementedError: classify_heading_patterns is not implemented yet
...
62 failed in 0.40s
```
