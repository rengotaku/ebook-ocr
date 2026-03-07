# Phase 4 RED Tests: US3 - 正規化スクリプトの生成

**Date**: 2026-03-03
**Status**: RED (FAIL verified)
**User Story**: US3 - 正規化スクリプトの生成

## Summary

| 項目 | 値 |
|------|-----|
| 作成テスト数 | 19 |
| FAIL 数 | 19 |
| テストファイル | tests/book_converter/test_normalization_rules.py |

## 失敗テスト一覧

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|----------|
| test_normalization_rules.py | TestGenerateSedScript::test_generate_sed_script_single_rule | 単一ルールから sed コマンド1行を生成 |
| test_normalization_rules.py | TestGenerateSedScript::test_generate_sed_script_multiple_rules | 複数ルールから複数行の sed コマンドを生成 |
| test_normalization_rules.py | TestGenerateSedScript::test_generate_sed_script_escape_special_chars | /, &, \\ 等の sed 特殊文字を正しくエスケープ |
| test_normalization_rules.py | TestGenerateSedScript::test_generate_sed_script_empty_rules | 空ルールリストから空文字列を返す |
| test_normalization_rules.py | TestGenerateSedScript::test_generate_sed_script_posix_compatible | POSIX 互換 sed コマンド（GNU 拡張なし） |
| test_normalization_rules.py | TestGenerateSedScript::test_generate_sed_script_anchored_pattern | 行頭アンカー (^) を使用したパターン |
| test_normalization_rules.py | TestGenerateSedScript::test_generate_sed_script_format_only_rule | FORMAT_ONLY ルールからも sed コマンドを生成 |
| test_normalization_rules.py | TestGenerateSedScript::test_generate_sed_script_unicode_heading | Unicode（日本語）見出しの sed スクリプト生成 |
| test_normalization_rules.py | TestPreviewDiff::test_preview_diff_changes | 変更がある場合に行番号付き差分プレビュー表示 |
| test_normalization_rules.py | TestPreviewDiff::test_preview_diff_no_changes | 変更がない場合は空の差分プレビュー |
| test_normalization_rules.py | TestPreviewDiff::test_preview_diff_multiple_changes | 複数変更の差分プレビュー |
| test_normalization_rules.py | TestPreviewDiff::test_preview_diff_shows_arrow_or_separator | 変換を示す矢印記号を含む |
| test_normalization_rules.py | TestApplyRules::test_apply_rules_single_change | 単一ルール適用で対象行のみ変更 |
| test_normalization_rules.py | TestApplyRules::test_apply_rules_multiple_changes | 複数ルールの同時適用 |
| test_normalization_rules.py | TestApplyRules::test_apply_rules_no_rules | ルールなしでコンテンツそのまま返却 |
| test_normalization_rules.py | TestApplyRules::test_apply_rules_preserves_newlines | 改行構造の保持 |
| test_normalization_rules.py | TestApplyRules::test_apply_rules_returns_new_string | 元コンテンツの不変性（新文字列を返す） |
| test_normalization_rules.py | TestApplyRules::test_apply_rules_special_chars | 特殊文字（C++, /, &）を含む行の正しい置換 |
| test_normalization_rules.py | TestApplyRules::test_apply_rules_empty_content | 空コンテンツへのルール適用 |

## 実装ヒント

- `generate_sed_script()`: NormalizationRule の original/normalized から `sed -i 's/^ORIGINAL$/NORMALIZED/'` 形式を生成。`/`, `&`, `\` のエスケープ必須。POSIX 互換（GNU 拡張なし）
- `preview_diff()`: content の各行と rules の line_number を照合し、`- Line N: "original" -> "normalized"` 形式で出力
- `apply_rules()`: content を行分割し、rules の line_number に基づいて対象行を normalized に置換。元の content は変更しない（不変性）
- エッジケース: 空ルール、空コンテンツ、特殊文字（/, &, \\, +）、Unicode 日本語文字列

## make test 出力（抜粋）

```
FAILED tests/book_converter/test_normalization_rules.py::TestGenerateSedScript::test_generate_sed_script_single_rule - NotImplementedError: generate_sed_script() is not yet implemented
FAILED tests/book_converter/test_normalization_rules.py::TestGenerateSedScript::test_generate_sed_script_multiple_rules - NotImplementedError: generate_sed_script() is not yet implemented
FAILED tests/book_converter/test_normalization_rules.py::TestGenerateSedScript::test_generate_sed_script_escape_special_chars - NotImplementedError: generate_sed_script() is not yet implemented
FAILED tests/book_converter/test_normalization_rules.py::TestGenerateSedScript::test_generate_sed_script_empty_rules - NotImplementedError: generate_sed_script() is not yet implemented
FAILED tests/book_converter/test_normalization_rules.py::TestGenerateSedScript::test_generate_sed_script_posix_compatible - NotImplementedError: generate_sed_script() is not yet implemented
FAILED tests/book_converter/test_normalization_rules.py::TestGenerateSedScript::test_generate_sed_script_anchored_pattern - NotImplementedError: generate_sed_script() is not yet implemented
FAILED tests/book_converter/test_normalization_rules.py::TestGenerateSedScript::test_generate_sed_script_format_only_rule - NotImplementedError: generate_sed_script() is not yet implemented
FAILED tests/book_converter/test_normalization_rules.py::TestGenerateSedScript::test_generate_sed_script_unicode_heading - NotImplementedError: generate_sed_script() is not yet implemented
FAILED tests/book_converter/test_normalization_rules.py::TestPreviewDiff::test_preview_diff_changes - NotImplementedError: preview_diff() is not yet implemented
FAILED tests/book_converter/test_normalization_rules.py::TestPreviewDiff::test_preview_diff_no_changes - NotImplementedError: preview_diff() is not yet implemented
FAILED tests/book_converter/test_normalization_rules.py::TestPreviewDiff::test_preview_diff_multiple_changes - NotImplementedError: preview_diff() is not yet implemented
FAILED tests/book_converter/test_normalization_rules.py::TestPreviewDiff::test_preview_diff_shows_arrow_or_separator - NotImplementedError: preview_diff() is not yet implemented
FAILED tests/book_converter/test_normalization_rules.py::TestApplyRules::test_apply_rules_single_change - NotImplementedError: apply_rules() is not yet implemented
FAILED tests/book_converter/test_normalization_rules.py::TestApplyRules::test_apply_rules_multiple_changes - NotImplementedError: apply_rules() is not yet implemented
FAILED tests/book_converter/test_normalization_rules.py::TestApplyRules::test_apply_rules_no_rules - NotImplementedError: apply_rules() is not yet implemented
FAILED tests/book_converter/test_normalization_rules.py::TestApplyRules::test_apply_rules_preserves_newlines - NotImplementedError: apply_rules() is not yet implemented
FAILED tests/book_converter/test_normalization_rules.py::TestApplyRules::test_apply_rules_returns_new_string - NotImplementedError: apply_rules() is not yet implemented
FAILED tests/book_converter/test_normalization_rules.py::TestApplyRules::test_apply_rules_special_chars - NotImplementedError: apply_rules() is not yet implemented
FAILED tests/book_converter/test_normalization_rules.py::TestApplyRules::test_apply_rules_empty_content - NotImplementedError: apply_rules() is not yet implemented
19 failed, 12 passed in 0.34s
```
