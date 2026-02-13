# Phase 4 RED Output: US4 - フォールバック処理

**Date**: 2026-02-13
**Status**: GREEN (All tests pass - already implemented)

## 概要

| 項目 | 値 |
|------|-----|
| Phase | 4 |
| User Story | US4 - フォールバック処理 |
| テスト対象 | calculate_coverage(), should_fallback(), ocr_by_layout() |
| テストファイル | tests/test_layout_ocr.py |
| FAILテスト数 | 0 (全て GREEN) |
| PASSテスト数 | 21 (US4関連) |

## 分析結果

Phase 1 分析 (`ph1-output.md`) で判明した通り、US4 の機能は既に実装済みでした。

### 実装済みコード (`src/layout_ocr.py`)

1. **`calculate_coverage()`** (lines 241-259)
   - 領域面積の合計 / ページ面積 を計算
   - 空領域リストまたはゼロページサイズの場合は 0.0 を返す

2. **`should_fallback()`** (lines 262-302)
   - 条件1: 領域なし → フォールバック
   - 条件2: OCR対象領域なし (ABANDONのみ) → フォールバック
   - 条件3: カバー率が閾値未満 (デフォルト30%) → フォールバック
   - 条件4: 単一FIGUREがページの90%以上をカバー → フォールバック

3. **`ocr_by_layout()`** (lines 305-360)
   - `should_fallback()` を呼び出し、フォールバック時は Yomitoku でページ全体OCR
   - フォールバック結果は `region_type="FALLBACK"` として返される

## テスト一覧

### TestCalculateCoverage (5テスト)

| テストメソッド | 検証内容 | 状態 |
|---------------|---------|------|
| test_calculate_coverage_single_region | 単一領域のカバー率計算 (50x50 on 100x100 = 25%) | PASS |
| test_calculate_coverage_multiple_regions | 複数領域の合計カバー率 | PASS |
| test_calculate_coverage_full_page | ページ全体カバーで100% | PASS |
| test_calculate_coverage_empty_regions | 空領域リストで0% | PASS |
| test_calculate_coverage_real_world_example | 実際のページに近い複雑なレイアウト | PASS |

### TestShouldFallback (7テスト)

| テストメソッド | 検証内容 | 状態 |
|---------------|---------|------|
| test_should_fallback_empty_regions | 空領域でフォールバック | PASS |
| test_should_fallback_low_coverage | 30%未満でフォールバック (4%テスト) | PASS |
| test_should_fallback_sufficient_coverage | 30%以上でフォールバックしない (36%テスト) | PASS |
| test_should_fallback_exactly_30_percent | 境界値30%でフォールバックしない | PASS |
| test_should_fallback_custom_threshold | カスタム閾値 (50%閾値で40%カバー率 → フォールバック) | PASS |
| test_should_fallback_single_figure_full_page | 単一FIGUREが90%以上でフォールバック | PASS |
| test_should_fallback_multiple_figures_not_fallback | 複数FIGURE+TEXTでフォールバックしない | PASS |

### TestFallbackEmptyLayout (2テスト)

| テストメソッド | 検証内容 | 状態 |
|---------------|---------|------|
| test_ocr_by_layout_fallback_empty_regions | 領域なしでページ全体OCR実行 | PASS |
| test_ocr_by_layout_fallback_missing_regions_key | regionsキーなしでフォールバック | PASS |

### TestFallbackLowCoverage (3テスト)

| テストメソッド | 検証内容 | 状態 |
|---------------|---------|------|
| test_ocr_by_layout_fallback_below_30_percent | 1%カバー率でフォールバック | PASS |
| test_ocr_by_layout_no_fallback_above_30_percent | 50%カバー率でフォールバックしない | PASS |
| test_ocr_by_layout_fallback_29_percent_coverage | 境界値直下29%でフォールバック | PASS |

### TestFallbackSingleFigure (1テスト)

| テストメソッド | 検証内容 | 状態 |
|---------------|---------|------|
| test_ocr_by_layout_fallback_full_page_figure | ページ全体がFIGUREでフォールバック | PASS |

### TestFallbackEdgeCases (3テスト)

| テストメソッド | 検証内容 | 状態 |
|---------------|---------|------|
| test_calculate_coverage_zero_page_size | ゼロページサイズのハンドリング | PASS |
| test_calculate_coverage_negative_bbox | 負のbbox座標のハンドリング | PASS |
| test_should_fallback_only_abandon_regions | ABANDONのみでフォールバック | PASS |

## テスト実行結果

```
$ python -m pytest tests/test_layout_ocr.py -v

============================= test session starts ==============================
platform linux -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0
collected 53 items

tests/test_layout_ocr.py::TestCalculateCoverage::test_calculate_coverage_single_region PASSED
tests/test_layout_ocr.py::TestCalculateCoverage::test_calculate_coverage_multiple_regions PASSED
tests/test_layout_ocr.py::TestCalculateCoverage::test_calculate_coverage_full_page PASSED
tests/test_layout_ocr.py::TestCalculateCoverage::test_calculate_coverage_empty_regions PASSED
tests/test_layout_ocr.py::TestCalculateCoverage::test_calculate_coverage_real_world_example PASSED
tests/test_layout_ocr.py::TestShouldFallback::test_should_fallback_empty_regions PASSED
tests/test_layout_ocr.py::TestShouldFallback::test_should_fallback_low_coverage PASSED
tests/test_layout_ocr.py::TestShouldFallback::test_should_fallback_sufficient_coverage PASSED
tests/test_layout_ocr.py::TestShouldFallback::test_should_fallback_exactly_30_percent PASSED
tests/test_layout_ocr.py::TestShouldFallback::test_should_fallback_custom_threshold PASSED
tests/test_layout_ocr.py::TestShouldFallback::test_should_fallback_single_figure_full_page PASSED
tests/test_layout_ocr.py::TestShouldFallback::test_should_fallback_multiple_figures_not_fallback PASSED
tests/test_layout_ocr.py::TestFallbackEmptyLayout::test_ocr_by_layout_fallback_empty_regions PASSED
tests/test_layout_ocr.py::TestFallbackEmptyLayout::test_ocr_by_layout_fallback_missing_regions_key PASSED
tests/test_layout_ocr.py::TestFallbackLowCoverage::test_ocr_by_layout_fallback_below_30_percent PASSED
tests/test_layout_ocr.py::TestFallbackLowCoverage::test_ocr_by_layout_no_fallback_above_30_percent PASSED
tests/test_layout_ocr.py::TestFallbackLowCoverage::test_ocr_by_layout_fallback_29_percent_coverage PASSED
tests/test_layout_ocr.py::TestFallbackSingleFigure::test_ocr_by_layout_fallback_full_page_figure PASSED
tests/test_layout_ocr.py::TestFallbackEdgeCases::test_calculate_coverage_zero_page_size PASSED
tests/test_layout_ocr.py::TestFallbackEdgeCases::test_calculate_coverage_negative_bbox PASSED
tests/test_layout_ocr.py::TestFallbackEdgeCases::test_should_fallback_only_abandon_regions PASSED

============================= 53 passed in 17.49s ==============================
```

## タスク完了状況

| Task | Status | Notes |
|------|--------|-------|
| T038 | ✅ | ph1-output.md 読み込み |
| T039 | ✅ | ph3-output.md 読み込み |
| T040 | ✅ | カバー率計算テスト - 既存テスト確認 (5テスト) |
| T041 | ✅ | フォールバック判定テスト - 既存テスト確認 (7テスト) |
| T042 | ✅ | 領域ゼロフォールバックテスト - 既存テスト確認 (2テスト) |
| T043 | ✅ | 全体FIGUREフォールバックテスト - 既存テスト確認 (1テスト) |
| T044 | ✅ | make test GREEN（既存実装済み）|
| T045 | ✅ | このファイル生成 |

## 結論

- **Phase 4 (US4) の機能は既に実装済み**
- 全21テストが PASS
- 追加テスト実装は不要
- Implementation (GREEN) フェーズをスキップ可能

## 次のフェーズ

Phase 4 Implementation (GREEN) → Verification → Phase 5: US2 - 領域別OCR処理 (TDD)
