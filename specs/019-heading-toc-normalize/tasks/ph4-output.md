# Phase 4 Output: US3 - 正規化スクリプトの生成

**Date**: 2026-03-03
**Status**: Completed
**User Story**: US3 - 正規化スクリプトの生成

## Executed Tasks

- [x] T048 RED テストを読む: specs/019-heading-toc-normalize/red-tests/ph4-test.md
- [x] T049 [US3] generate_sed_script() を実装: src/book_converter/normalization_rules.py
- [x] T050 [US3] preview_diff() を実装: src/book_converter/normalization_rules.py
- [x] T051 [US3] apply_rules() を実装: src/book_converter/normalization_rules.py
- [x] T052 `make test` で PASS を確認 (GREEN)
- [x] T053 `make test` で全テスト PASS を確認（US1, US2 含む）
- [x] T054 `make coverage` でカバレッジ ≥80% を確認
- [x] T055 フェーズ結果を出力: specs/019-heading-toc-normalize/tasks/ph4-output.md

## Changed Files

| File | Change Type | Summary |
|------|-------------|---------|
| src/book_converter/normalization_rules.py | Modified | generate_sed_script(), preview_diff(), apply_rules() を実装（stub から完全実装へ） |
| specs/019-heading-toc-normalize/tasks.md | Modified | T048-T055 を完了としてマーク |

## Implementation Details

### generate_sed_script()

NormalizationRule から POSIX 互換 sed コマンドを生成する関数を実装:

**sed スクリプト生成戦略**:
1. NONE アクションルールはスキップ（変更不要）
2. 特殊文字エスケープ: `\`, `/`, `&` を正しくエスケープ
3. 行頭・行末アンカー: `^` と `$` を使用して行全体マッチ
4. POSIX 互換: GNU 拡張（`-r`, `-E`, `\d`）を使用しない

**エスケープ順序**:
- エスケープ順序が重要: `\` → `/` → `&` の順でエスケープ
- `\` を先にエスケープしないと、後続のエスケープシーケンスが壊れる

**出力形式**:
```bash
sed -i 's/^ORIGINAL$/NORMALIZED/' book.md
```

**実装のポイント**:
- 空ルールリストは空文字列を返す
- 各ルールは1行の sed コマンドに変換
- 特殊文字（C++, /, &）を含む見出しも正しく処理

### preview_diff()

ルール適用前後の差分プレビューを生成する関数を実装:

**差分表示戦略**:
1. content を行分割し、各ルールの line_number で対象行を特定
2. 対象行が original と一致する場合のみ差分行を生成
3. フォーマット: `- Line N: "original" -> "normalized"`

**実装のポイント**:
- 空ルールリストは空文字列を返す
- 行番号は 1-indexed（人間が読みやすい形式）
- 矢印記号 `->` で変換を明示

**エッジケース対応**:
- 行番号が範囲外の場合はスキップ
- 対象行が original と一致しない場合もスキップ（既に変更済み）

### apply_rules()

NormalizationRule を content に適用して変更後の content を返す関数を実装:

**ルール適用戦略**:
1. content を行分割（不変性を保つため新しいリスト）
2. 各ルールの line_number で対象行を特定
3. 対象行が original と一致する場合のみ normalized に置換
4. 行を結合して新しい文字列を返す

**不変性の保証**:
- 元の content は変更しない
- 新しい文字列を返す
- 行リストを変更する際も元のリストは変更しない

**実装のポイント**:
- 空ルールリストは content をそのまま返す
- 改行構造を保持（split/join で改行数は変わらない）
- 特殊文字を含む行も正しく置換

**エッジケース対応**:
- 空 content でもエラーにならない
- 行番号が範囲外のルールは無視
- 対象行が original と一致しない場合も無視（既に変更済み）

## Test Results

```
============================= test session starts ==============================
tests/book_converter/test_normalization_rules.py::TestGenerateSedScript::test_generate_sed_script_single_rule PASSED
tests/book_converter/test_normalization_rules.py::TestGenerateSedScript::test_generate_sed_script_multiple_rules PASSED
tests/book_converter/test_normalization_rules.py::TestGenerateSedScript::test_generate_sed_script_escape_special_chars PASSED
tests/book_converter/test_normalization_rules.py::TestGenerateSedScript::test_generate_sed_script_empty_rules PASSED
tests/book_converter/test_normalization_rules.py::TestGenerateSedScript::test_generate_sed_script_posix_compatible PASSED
tests/book_converter/test_normalization_rules.py::TestGenerateSedScript::test_generate_sed_script_anchored_pattern PASSED
tests/book_converter/test_normalization_rules.py::TestGenerateSedScript::test_generate_sed_script_format_only_rule PASSED
tests/book_converter/test_normalization_rules.py::TestGenerateSedScript::test_generate_sed_script_unicode_heading PASSED
tests/book_converter/test_normalization_rules.py::TestPreviewDiff::test_preview_diff_changes PASSED
tests/book_converter/test_normalization_rules.py::TestPreviewDiff::test_preview_diff_no_changes PASSED
tests/book_converter/test_normalization_rules.py::TestPreviewDiff::test_preview_diff_multiple_changes PASSED
tests/book_converter/test_normalization_rules.py::TestPreviewDiff::test_preview_diff_shows_arrow_or_separator PASSED
tests/book_converter/test_normalization_rules.py::TestApplyRules::test_apply_rules_single_change PASSED
tests/book_converter/test_normalization_rules.py::TestApplyRules::test_apply_rules_multiple_changes PASSED
tests/book_converter/test_normalization_rules.py::TestApplyRules::test_apply_rules_no_rules PASSED
tests/book_converter/test_normalization_rules.py::TestApplyRules::test_apply_rules_preserves_newlines PASSED
tests/book_converter/test_normalization_rules.py::TestApplyRules::test_apply_rules_returns_new_string PASSED
tests/book_converter/test_normalization_rules.py::TestApplyRules::test_apply_rules_special_chars PASSED
tests/book_converter/test_normalization_rules.py::TestApplyRules::test_apply_rules_empty_content PASSED
============================== 31 passed in 0.15s ==============================

=========== 1605 passed, 6 skipped, 6 warnings in 137.58s (0:02:17) ============
```

**全テスト結果**: 1605 passed, 6 skipped (全プロジェクト)

**Coverage**:
- `normalization_rules.py`: 92% (93 lines, 7 missed)
- `heading_matcher.py`: 100% (47 lines, 0 missed)
- `heading_normalizer.py`: 99% (100 lines, 1 missed)
- Total project coverage: 62%

カバレッジ詳細:
- normalization_rules.py: 未カバーは未到達の分岐ロジック (7行)
  - 主に generate_rules() 内の条件分岐で、特定のエッジケースのみで到達するパス
  - Line 48, 66, 79, 81, 85, 117, 153
- 全モジュールが目標の80%を大幅に達成

## Discovered Issues

特になし。全テスト（19個の新規テスト + 既存テスト）が PASS し、リグレッションも発生していない。

## Handoff to Next Phase

Items to implement in Phase 5 (US4 - 正規化結果の検証):
- **検証レポート機能**: ValidationReport データクラスと関連関数を実装
  - `ValidationReport`: マッチング結果のサマリー（match_rate, missing_entries, excluded_headings）
  - `find_similar_candidate()`: MISSING エントリの類似候補を検索（ファジーマッチング）
  - `generate_validation_report()`: MatchResult から ValidationReport を生成
  - `format_validation_report()`: テーブル形式のレポート出力
- **CLI統合準備**: Phase 6 で validate サブコマンドに統合される

**Reusable APIs from this phase**:
- `generate_sed_script()`: NormalizationRule から POSIX 互換 sed スクリプト生成
- `preview_diff()`: 変更前後の差分プレビュー（dry-run 用）
- `apply_rules()`: ルールを content に適用して新文字列を返す（--apply 用）

**Caveats**:
- `generate_sed_script()` は行全体マッチ（`^...$`）を使用するため、部分一致での置換は不可
- `apply_rules()` は line_number ベースで置換するため、ルール適用順序は関係ない（各ルールが独立）
- sed スクリプトのエスケープ順序（`\` → `/` → `&`）を変更すると動作しなくなる
- NONE アクションルールは sed スクリプトに含まれない（変更不要なため）
