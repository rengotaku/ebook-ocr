# Phase 5 RED テスト結果: US4 - フォールバック処理

**日付**: 2026-02-11
**Phase**: Phase 5 (Test Implementation - RED)
**User Story**: US4 - フォールバック処理

## サマリ

| 項目 | 値 |
|------|-----|
| Phase | 5 (US4 - フォールバック処理) |
| FAILテスト数 | 18件 |
| PASSテスト数 | 36件 (Phase 1-4 既存テスト) |
| テストファイル | tests/test_layout_ocr.py |
| ステータス | RED (実装前) |

## 追加テストクラス

| クラス名 | テスト数 | 目的 |
|---------|---------|------|
| TestCalculateCoverage | 5 | カバー率計算の正確性検証 |
| TestShouldFallback | 7 | フォールバック判定ロジック検証 |
| TestFallbackEmptyLayout | 2 | 空layout時のフォールバック検証 |
| TestFallbackLowCoverage | 3 | 低カバー率時のフォールバック検証 |
| TestFallbackSingleFigure | 1 | 全ページFIGURE時のフォールバック検証 |
| TestFallbackEdgeCases | 3 | エッジケース検証 |

## FAILテスト一覧

| テストファイル | テストメソッド | 期待される動作 | FAIL理由 |
|--------------|--------------|--------------|---------|
| test_layout_ocr.py | TestCalculateCoverage::test_calculate_coverage_single_region | 単一領域のカバー率 = 25% | `calculate_coverage` 未実装 |
| test_layout_ocr.py | TestCalculateCoverage::test_calculate_coverage_multiple_regions | 複数領域の合計カバー率 = 12.5% | `calculate_coverage` 未実装 |
| test_layout_ocr.py | TestCalculateCoverage::test_calculate_coverage_full_page | ページ全体カバー = 100% | `calculate_coverage` 未実装 |
| test_layout_ocr.py | TestCalculateCoverage::test_calculate_coverage_empty_regions | 空リスト = 0% | `calculate_coverage` 未実装 |
| test_layout_ocr.py | TestCalculateCoverage::test_calculate_coverage_real_world_example | 実世界例のカバー率計算 | `calculate_coverage` 未実装 |
| test_layout_ocr.py | TestShouldFallback::test_should_fallback_empty_regions | 空regions → True | `should_fallback` 未実装 |
| test_layout_ocr.py | TestShouldFallback::test_should_fallback_low_coverage | 4%カバー率 → True | `should_fallback` 未実装 |
| test_layout_ocr.py | TestShouldFallback::test_should_fallback_sufficient_coverage | 36%カバー率 → False | `should_fallback` 未実装 |
| test_layout_ocr.py | TestShouldFallback::test_should_fallback_exactly_30_percent | 30%カバー率 → False (境界値) | `should_fallback` 未実装 |
| test_layout_ocr.py | TestShouldFallback::test_should_fallback_custom_threshold | カスタムしきい値50% | `should_fallback` 未実装 |
| test_layout_ocr.py | TestShouldFallback::test_should_fallback_single_figure_full_page | 全ページFIGURE → True | `should_fallback` 未実装 |
| test_layout_ocr.py | TestShouldFallback::test_should_fallback_multiple_figures_not_fallback | 複数FIGURE → False | `should_fallback` 未実装 |
| test_layout_ocr.py | TestFallbackEmptyLayout::test_ocr_by_layout_fallback_empty_regions | 空layout → ページ全体OCR | `ocr_by_layout` フォールバック未統合 |
| test_layout_ocr.py | TestFallbackEmptyLayout::test_ocr_by_layout_fallback_missing_regions_key | regionsキー欠落 → フォールバック | `ocr_by_layout` フォールバック未統合 |
| test_layout_ocr.py | TestFallbackLowCoverage::test_ocr_by_layout_fallback_below_30_percent | 1%カバー率 → ページ全体OCR | `ocr_by_layout` フォールバック未統合 |
| test_layout_ocr.py | TestFallbackLowCoverage::test_ocr_by_layout_no_fallback_above_30_percent | 50%カバー率 → 通常OCR | 期待通りPASSすべき (既存動作) |
| test_layout_ocr.py | TestFallbackLowCoverage::test_ocr_by_layout_fallback_29_percent_coverage | 29%カバー率 → フォールバック | `ocr_by_layout` フォールバック未統合 |
| test_layout_ocr.py | TestFallbackSingleFigure::test_ocr_by_layout_fallback_full_page_figure | 全ページFIGURE → フォールバック | `ocr_by_layout` フォールバック未統合 |
| test_layout_ocr.py | TestFallbackEdgeCases::test_calculate_coverage_zero_page_size | ゼロページサイズハンドリング | `calculate_coverage` 未実装 |
| test_layout_ocr.py | TestFallbackEdgeCases::test_calculate_coverage_negative_bbox | 負bbox座標ハンドリング | `calculate_coverage` 未実装 |
| test_layout_ocr.py | TestFallbackEdgeCases::test_should_fallback_only_abandon_regions | ABANDONのみ → True | `should_fallback` 未実装 |

## 実装ヒント

### 1. calculate_coverage() 関数

data-model.md で定義されたアルゴリズム:

```python
def calculate_coverage(regions: list[dict], page_size: tuple[int, int]) -> float:
    """検出領域がページをカバーする割合を計算。

    Args:
        regions: 領域リスト [{"bbox": [x1, y1, x2, y2], ...}, ...]
        page_size: (width, height)

    Returns:
        カバー率 (0.0 - 1.0)
    """
    if not regions or page_size[0] <= 0 or page_size[1] <= 0:
        return 0.0

    page_area = page_size[0] * page_size[1]
    total_region_area = sum(
        (r["bbox"][2] - r["bbox"][0]) * (r["bbox"][3] - r["bbox"][1])
        for r in regions
    )
    return total_region_area / page_area
```

### 2. should_fallback() 関数

research.md のフォールバック条件:

1. 領域が検出されなかった
2. 検出領域のカバー率が30%未満
3. ページ全体が1つのFIGUREとして検出された

```python
def should_fallback(
    regions: list[dict],
    page_size: tuple[int, int],
    threshold: float = 0.3,
) -> bool:
    """フォールバックが必要かどうかを判定。

    Returns:
        True: ページ全体OCRにフォールバック
        False: 領域別OCRを実行
    """
    # 条件1: 領域なし
    if not regions:
        return True

    # OCR対象領域のみをフィルタ（ABANDONを除外）
    ocr_regions = [r for r in regions if r["type"] != "ABANDON"]
    if not ocr_regions:
        return True

    # 条件2: カバー率が閾値未満
    coverage = calculate_coverage(ocr_regions, page_size)
    if coverage < threshold:
        return True

    # 条件3: 単一FIGUREがページの90%以上をカバー
    if len(ocr_regions) == 1 and ocr_regions[0]["type"] == "FIGURE":
        if coverage >= 0.9:
            return True

    return False
```

### 3. ocr_by_layout() フォールバック統合

```python
def ocr_by_layout(
    page_path: str,
    layout: dict,
    base_url: str = "http://localhost:11434",
    timeout: int = 60,
) -> list[OCRResult]:
    regions = layout.get("regions", [])
    page_size = tuple(layout.get("page_size", [0, 0]))

    # フォールバック判定
    if should_fallback(regions, page_size):
        # ページ全体OCRを実行
        img = Image.open(page_path)
        # DeepSeek-OCRでページ全体を処理
        ...
        return [OCRResult(region_type="FALLBACK", text=..., formatted=...)]

    # 通常の領域別OCR処理
    ...
```

## FAIL出力例

```
============================= test session starts ==============================
platform linux -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0
collected 54 items

tests/test_layout_ocr.py ....................................FFFFFFFFFFFFFFFFFF [100%]

================================ short test summary info ============================
FAILED tests/test_layout_ocr.py::TestCalculateCoverage::test_calculate_coverage_single_region
  - ImportError: cannot import name 'calculate_coverage' from 'src.layout_ocr'

FAILED tests/test_layout_ocr.py::TestShouldFallback::test_should_fallback_empty_regions
  - ImportError: cannot import name 'should_fallback' from 'src.layout_ocr'

FAILED tests/test_layout_ocr.py::TestFallbackEmptyLayout::test_ocr_by_layout_fallback_empty_regions
  - AssertionError: Empty regions should trigger fallback. Got: 0 results

FAILED tests/test_layout_ocr.py::TestFallbackSingleFigure::test_ocr_by_layout_fallback_full_page_figure
  - AssertionError: Fallback result type should be FALLBACK or TEXT. Got: FIGURE

======================== 18 failed, 36 passed in 0.33s =========================
```

## 次のステップ

1. **T057**: RED テスト結果を読み取り
2. **T058**: `calculate_coverage()` 関数を `src/layout_ocr.py` に実装
3. **T059**: `should_fallback()` 関数を `src/layout_ocr.py` に実装
4. **T060**: `ocr_by_layout()` にフォールバック処理を統合
5. **T061**: `make test` で全テストがPASSすることを確認 (GREEN)

---

**ステータス**: RED - phase-executor による Implementation (GREEN) 待ち
