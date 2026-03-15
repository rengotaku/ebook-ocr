# Phase 3 RED Tests: US2 + US3 テキスト分析によるコード検出

**Date**: 2026-03-13
**Status**: RED (FAIL verified)
**User Story**: US2 - FIGURE 誤検出コードの救済, US3 - TEXT リージョン内コードの検出

## サマリ

| 項目 | 値 |
|------|-------|
| 作成テスト数 | 41 |
| FAIL 数 | 41 |
| テストファイル | tests/test_code_detector.py |

## FAIL テスト一覧

### TestCalcSymbolRatio (9件) - T032

| テストメソッド | 期待動作 | FAIL 原因 |
|---------------|---------|----------|
| test_code_text_high_ratio | "class Foo { }" の記号比率 > 0.08 | ImportError: calc_symbol_ratio 未実装 |
| test_curly_braces_and_semicolons | "if (x > 0) { return x; }" の記号比率 > 0.08 | 同上 |
| test_japanese_text_zero_ratio | 日本語テキストの記号比率 == 0.0 | 同上 |
| test_empty_string_returns_zero | 空文字列 -> 0.0 | 同上 |
| test_only_symbols | "{}();=<>[]" の記号比率 > 0.5 | 同上 |
| test_mixed_code_and_text | Java コードの記号比率 > 0.0 | 同上 |
| test_returns_float | 戻り値が float 型 | 同上 |
| test_special_chars_unicode | Unicode テキスト -> 0.0 | 同上 |
| test_hash_and_at_symbols | "#include <stdio.h>" の記号比率 > 0.0 | 同上 |

### TestCountCodeKeywords (11件) - T033

| テストメソッド | 期待動作 | FAIL 原因 |
|---------------|---------|----------|
| test_class_extends_detected | "class Foo extends Bar" -> >= 2 | ImportError: count_code_keywords 未実装 |
| test_japanese_text_zero_keywords | 日本語テキスト -> 0 | 同上 |
| test_python_keywords | def + import -> >= 2 | 同上 |
| test_go_keywords | func + package -> >= 2 | 同上 |
| test_rust_keywords | fn + impl -> >= 2 | 同上 |
| test_sql_case_insensitive | SELECT + WHERE (大文字小文字無視) -> >= 2 | 同上 |
| test_empty_string_returns_zero | 空文字列 -> 0 | 同上 |
| test_returns_int | 戻り値が int 型 | 同上 |
| test_javascript_keywords | const + function -> >= 2 | 同上 |
| test_shell_keywords | #!/bin/ + echo -> >= 2 | 同上 |
| test_cpp_keywords | #include + std:: -> >= 2 | 同上 |

### TestDetectCodeByTextOrCondition (8件) - T034

| テストメソッド | 期待動作 | FAIL 原因 |
|---------------|---------|----------|
| test_symbol_ratio_only_returns_true | 記号のみ -> True (OR条件) | ImportError: detect_code_by_text 未実装 |
| test_keyword_only_returns_true | キーワードのみ -> True (OR条件) | 同上 |
| test_both_false_returns_false | 両方不足 -> False | 同上 |
| test_both_true_returns_true | 両方満足 -> True | 同上 |
| test_returns_bool | 戻り値が bool 型 | 同上 |
| test_empty_string_returns_false | 空文字列 -> False | 同上 |
| test_custom_thresholds | カスタム閾値の尊重 | 同上 |
| test_none_input_returns_false | None 入力 -> False | 同上 |

### TestFigureToCodeReclassification (4件) - T035

| テストメソッド | 期待動作 | FAIL 原因 |
|---------------|---------|----------|
| test_figure_with_code_paragraphs_becomes_code | コード含む FIGURE -> CODE | AssertionError: FIGURE != CODE (テキスト分析未実装) |
| test_figure_without_code_stays_figure | 非コード FIGURE -> FIGURE 維持 | PASS (現状 FIGURE のまま) |
| test_figure_without_paragraphs_stays_figure | paragraphs なし FIGURE -> FIGURE 維持 | PASS (現状 FIGURE のまま) |
| test_figure_code_region_has_code_label | FIGURE->CODE の label == "code" | AssertionError: figure != code |

### TestTextToCodeReclassification (3件) - T036

| テストメソッド | 期待動作 | FAIL 原因 |
|---------------|---------|----------|
| test_text_with_code_contents_becomes_code | コード含む TEXT -> CODE | AssertionError: TEXT != CODE (テキスト分析未実装) |
| test_text_with_normal_japanese_stays_text | 日本語 TEXT -> TEXT 維持 | PASS (現状 TEXT のまま) |
| test_text_code_region_has_code_label | TEXT->CODE の label == "code" | AssertionError: plain text != code |

### TestTitleSkipsTextAnalysis (2件) - T037

| テストメソッド | 期待動作 | FAIL 原因 |
|---------------|---------|----------|
| test_title_with_code_like_text_stays_title | TITLE -> TITLE 維持 (テキスト分析スキップ) | PASS (現状 TITLE のまま) |
| test_title_label_preserved | TITLE label 保持 | PASS (現状 section_headings のまま) |

### TestJapaneseFalsePositive (4件) - T038

| テストメソッド | 期待動作 | FAIL 原因 |
|---------------|---------|----------|
| test_general_japanese_prose_stays_text | 日本語本文 -> TEXT 維持 | PASS (現状 TEXT のまま) |
| test_japanese_with_technical_terms_stays_text | 技術用語含む日本語 -> TEXT 維持 | PASS (現状 TEXT のまま) |
| test_japanese_punctuation_not_counted_as_symbols | 日本語句読点の記号比率 == 0.0 | ImportError: calc_symbol_ratio 未実装 |
| test_figure_with_japanese_caption_stays_figure | 日本語キャプション FIGURE -> FIGURE 維持 | PASS (現状 FIGURE のまま) |

### TestMultiLanguageKeywords (8件) - T039

| テストメソッド | 期待動作 | FAIL 原因 |
|---------------|---------|----------|
| test_python_def_import | def + import -> >= 2 | ImportError: count_code_keywords 未実装 |
| test_go_func_package | func + package -> >= 2 | 同上 |
| test_rust_fn_impl | fn + impl -> >= 2 | 同上 |
| test_java_class_public_void | class + public + void -> >= 2 | 同上 |
| test_ruby_require_module | require + module -> >= 2 | 同上 |
| test_iac_dockerfile_keywords | FROM + WORKDIR + RUN -> >= 2 | 同上 |
| test_sql_select_where_case_insensitive | select + where (小文字) -> >= 2 | 同上 |
| test_mixed_language_keywords | 複数言語混在 -> >= 3 | 同上 |

## 実装ヒント

- `calc_symbol_ratio(text)`: `{ } ( ) ; = < > [ ] ! & | + - * / % # @ ^ ~ \` を対象記号としてカウント。空文字列 -> 0.0。日本語句読点は含めない
- `count_code_keywords(text)`: EXTENDED_KEYWORDS 定数から大文字小文字無視でマッチ。25言語対応
- `detect_code_by_text(text, sym_threshold=0.08, kw_threshold=2)`: OR 条件（記号比率 > sym_threshold OR キーワード数 >= kw_threshold）
- `paragraphs_to_layout()` への統合: FIGURE は figure.paragraphs のテキストを取得して判定。TEXT は paragraph.contents で判定。TITLE はスキップ
- エッジケース: None 入力、空文字列、日本語句読点の非カウント

## make test 出力 (抜粋)

```
FAILED tests/test_code_detector.py::TestCalcSymbolRatio::test_code_text_high_ratio - ImportError: cannot import name 'calc_symbol_ratio'
FAILED tests/test_code_detector.py::TestCountCodeKeywords::test_class_extends_detected - ImportError: cannot import name 'count_code_keywords'
FAILED tests/test_code_detector.py::TestDetectCodeByTextOrCondition::test_symbol_ratio_only_returns_true - ImportError: cannot import name 'detect_code_by_text'
FAILED tests/test_code_detector.py::TestFigureToCodeReclassification::test_figure_with_code_paragraphs_becomes_code - assert 'FIGURE' == 'CODE'
FAILED tests/test_code_detector.py::TestTextToCodeReclassification::test_text_with_code_contents_becomes_code - assert 'TEXT' == 'CODE'
FAILED tests/test_code_detector.py::TestJapaneseFalsePositive::test_japanese_punctuation_not_counted_as_symbols - ImportError: cannot import name 'calc_symbol_ratio'
FAILED tests/test_code_detector.py::TestMultiLanguageKeywords::test_python_def_import - ImportError: cannot import name 'count_code_keywords'
=== 41 failed, 1602 passed, 2 skipped, 131 deselected, 6 warnings in 28.42s ===
```
