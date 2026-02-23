# Phase 3: テスト実装 (RED) 結果

**日時**: 2026-02-23
**フェーズ**: Phase 3 - User Story 2 (後方互換性 + エッジケース)
**ステータス**: RED (4テストFAIL確認済み)

## 概要

| 項目 | 値 |
|------|-----|
| フェーズ | Phase 3 (US2) |
| FAILテスト数 | 4 |
| PASSテスト数 | 6 |
| テストファイル数 | 2 |
| 既存テストへの影響 | なし (1325 passed, 6 skipped) |

## テストファイル一覧

| ファイル | テスト数 | FAIL | PASS |
|---------|---------|------|------|
| tests/cli/test_limit_backward_compat.py | 4 | 2 | 2 |
| tests/cli/test_limit_edge_cases.py | 6 | 2 | 4 |

## FAILテスト一覧

| テストファイル | テストメソッド | 期待動作 | FAIL理由 |
|---------------|---------------|---------|----------|
| test_limit_backward_compat.py | test_deduplicate_without_limit_processes_all | --limitなしで全5フレームが出力される | 出力ファイル数が1 (知覚ハッシュにより1x1 PNGが重複判定) |
| test_limit_backward_compat.py | test_detect_layout_without_limit_processes_all | --limitなしで全5ページのレイアウト結果が出力 | layout.jsonが1ファイルのみ (ページ別出力でない) |
| test_limit_edge_cases.py | test_deduplicate_limit_greater_than_file_count | --limit 100で全3ファイルが処理される | 出力ファイル数が1 (同上: 知覚ハッシュ重複判定) |
| test_limit_edge_cases.py | test_detect_layout_limit_greater_than_file_count | --limit 100で全3ページのレイアウト結果が出力 | layout.jsonが1ファイルのみ (同上) |

## PASSテスト一覧

| テストファイル | テストメソッド | 動作確認 |
|---------------|---------------|---------|
| test_limit_backward_compat.py | test_run_ocr_without_limit_processes_all | --limitなしでOCR全ページ処理 |
| test_limit_backward_compat.py | test_consolidate_without_limit_processes_all | --limitなしでconsolidate全ページ処理 |
| test_limit_edge_cases.py | test_run_ocr_limit_greater_than_file_count | --limit > ファイル数でOCR正常動作 |
| test_limit_edge_cases.py | test_consolidate_limit_greater_than_file_count | --limit > ファイル数でconsolidate正常動作 |
| test_limit_edge_cases.py | test_deduplicate_limit_one_file | --limit 1で1ファイルのみ処理 |
| test_limit_edge_cases.py | test_consolidate_limit_one_file | --limit 1で1ファイルのみ統合 |

## 実装ヒント

### FAIL原因の分析

4つのFAILテストは共通の原因を持つ:

1. **deduplicate系 (2テスト)**: テストデータが1x1ピクセルPNGで、知覚ハッシュ (imagehash) が異なるRGB値でも同一と判定する。GREEN実装では以下の対応が必要:
   - テストデータをより異なるPNG (異なるサイズ、明確に異なるピクセルパターン) に変更する
   - または、hash_thresholdを0にして完全一致のみを重複と判定する

2. **detect_layout系 (2テスト)**: detect_layoutは `layout.json` を単一ファイルとして出力する設計。テストのアサーションが「ページ別にjsonファイルが出力される」と想定しているが、実際は異なる出力形式。GREEN実装では:
   - テストのアサーションを実際の出力形式に合わせて修正する
   - 例: layout.json内のページ数を確認する、または出力ディレクトリの存在を確認する

### GREEN実装の方向性

- テストデータの品質を上げる (より区別可能なPNG画像を生成)
- detect_layoutの出力形式を正確に把握してアサーションを修正
- 現在の実装は `--limit` なし、`--limit > ファイル数` いずれも正常に動作するため、テスト修正が中心

## FAIL出力例

```
FAILED tests/cli/test_limit_backward_compat.py::TestDeduplicateBackwardCompat::test_deduplicate_without_limit_processes_all
  AssertionError: Expected 5 output files (all frames processed), got 1
  assert 1 == 5

FAILED tests/cli/test_limit_backward_compat.py::TestDetectLayoutBackwardCompat::test_detect_layout_without_limit_processes_all
  AssertionError: Expected 5 layout results (all pages processed), got 1
  assert 1 == 5

FAILED tests/cli/test_limit_edge_cases.py::TestLimitGreaterThanFileCount::test_deduplicate_limit_greater_than_file_count
  AssertionError: Expected 3 output files (all available), got 1
  assert 1 == 3

FAILED tests/cli/test_limit_edge_cases.py::TestLimitGreaterThanFileCount::test_detect_layout_limit_greater_than_file_count
  AssertionError: Expected 3 layout results (all available), got 1
  assert 1 == 3
```

## 全体テスト結果

```
4 failed, 1325 passed, 6 skipped in 120.51s
```

既存テストへのリグレッションなし。
