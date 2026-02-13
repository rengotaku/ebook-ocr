# Phase 3 RED テスト結果: US3 - 読み順の再構築

**日付**: 2026-02-11
**Phase**: Phase 3 (User Story 3)
**ステータス**: RED (テスト失敗確認済み)

## サマリ

| 項目 | 値 |
|------|-----|
| Phase | Phase 3 (US3 - 読み順の再構築) |
| FAILテスト数 | 20 |
| PASSテスト数 | 0 |
| テストファイル | tests/test_reading_order.py |

## FAILテスト一覧

### TestSortReadingOrderSimple (単純ソートテスト)

| テストメソッド | 期待動作 | 失敗理由 |
|--------------|---------|---------|
| test_sort_reading_order_top_to_bottom | Y座標で上から下にソート | モジュール未実装 |
| test_sort_reading_order_left_to_right_same_row | 同一行内でX座標で左から右にソート | モジュール未実装 |
| test_sort_reading_order_empty_list | 空リストを空リストで返す | モジュール未実装 |
| test_sort_reading_order_single_region | 単一領域をそのまま返す | モジュール未実装 |

### TestSortReadingOrderTwoColumn (2カラムソートテスト)

| テストメソッド | 期待動作 | 失敗理由 |
|--------------|---------|---------|
| test_sort_reading_order_two_columns_left_first | 左カラム全体が右カラムより先 | モジュール未実装 |
| test_sort_reading_order_two_columns_mixed_y | 各カラム内がY座標順 | モジュール未実装 |
| test_sort_reading_order_center_regions | 中央領域が正しく分類される | モジュール未実装 |

### TestSortReadingOrderTitlePriority (タイトル優先テスト)

| テストメソッド | 期待動作 | 失敗理由 |
|--------------|---------|---------|
| test_sort_reading_order_title_before_text_same_y | 同一Y座標でTITLEがTEXTより先 | モジュール未実装 |
| test_sort_reading_order_title_priority_with_y_sort | Y座標ソートとタイトル優先の組み合わせ | モジュール未実装 |
| test_sort_reading_order_title_at_top_of_page | ページ上部のTITLEが最初 | モジュール未実装 |

### TestRemoveOverlaps (重複除去テスト)

| テストメソッド | 期待動作 | 失敗理由 |
|--------------|---------|---------|
| test_remove_overlaps_no_overlap | 重複なしで全領域保持 | モジュール未実装 |
| test_remove_overlaps_complete_overlap | 完全重複で信頼度高い方を残す | モジュール未実装 |
| test_remove_overlaps_partial_overlap | 部分重複(50%+)で1つのみ残す | モジュール未実装 |
| test_remove_overlaps_low_overlap_both_kept | 低重複率で両方残す | モジュール未実装 |
| test_remove_overlaps_empty_list | 空リストを空リストで返す | モジュール未実装 |
| test_remove_overlaps_different_types_kept | 異なるタイプは両方残す | モジュール未実装 |

### TestSortReadingOrderEdgeCases (エッジケーステスト)

| テストメソッド | 期待動作 | 失敗理由 |
|--------------|---------|---------|
| test_sort_reading_order_unicode_content_preserved | Unicode文字を含むデータ保持 | モジュール未実装 |
| test_sort_reading_order_immutable_input | 入力リストが変更されない | モジュール未実装 |
| test_sort_reading_order_large_page | 大ページサイズで正しく動作 | モジュール未実装 |
| test_sort_reading_order_negative_coords_handled | 負の座標のエラーハンドリング | モジュール未実装 |

## 実装ヒント

### T029: sort_reading_order() 関数実装

research.mdより:

```python
def sort_reading_order(regions: list[dict], page_width: int) -> list[dict]:
    """横書きレイアウトの読み順でソート。

    アルゴリズム:
    1. カラム検出: X座標の中央値でグループ化（mid_x = page_width / 2）
    2. 各カラム内をY座標でソート
    3. 左カラム → 右カラムの順で結合

    同一Y座標の場合、TITLEがTEXTより優先される。

    Args:
        regions: 領域のリスト（type, bbox, confidenceを含む）
        page_width: ページ幅（カラム判定に使用）

    Returns:
        読み順でソートされた領域のリスト（新しいリスト、元は変更しない）
    """
    if not regions:
        return regions

    # イミュータブル: 元のリストを変更しない
    regions_copy = [r.copy() for r in regions]

    mid_x = page_width / 2
    left_col = []
    right_col = []

    for r in regions_copy:
        center_x = (r["bbox"][0] + r["bbox"][2]) / 2
        if center_x < mid_x:
            left_col.append(r)
        else:
            right_col.append(r)

    # 各カラム内をY座標でソート（同一YならTITLE優先）
    def sort_key(r):
        type_priority = 0 if r["type"] == "TITLE" else 1
        return (r["bbox"][1], type_priority)

    left_col.sort(key=sort_key)
    right_col.sort(key=sort_key)

    return left_col + right_col
```

### T030: remove_overlaps() 関数実装

data-model.mdより:

```python
def remove_overlaps(regions: list[dict]) -> list[dict]:
    """重複領域の検出と除去。

    アルゴリズム:
    1. 各領域ペアの重複率を計算
    2. 重複率が50%以上の場合、信頼度の低い方を除去
    3. 異なるタイプの領域は除去しない

    Args:
        regions: 領域のリスト

    Returns:
        重複を除去した領域のリスト
    """
    if not regions:
        return []

    def calculate_overlap(r1, r2):
        x1 = max(r1["bbox"][0], r2["bbox"][0])
        y1 = max(r1["bbox"][1], r2["bbox"][1])
        x2 = min(r1["bbox"][2], r2["bbox"][2])
        y2 = min(r1["bbox"][3], r2["bbox"][3])

        if x1 >= x2 or y1 >= y2:
            return 0

        intersection = (x2 - x1) * (y2 - y1)
        area1 = (r1["bbox"][2] - r1["bbox"][0]) * (r1["bbox"][3] - r1["bbox"][1])
        area2 = (r2["bbox"][2] - r2["bbox"][0]) * (r2["bbox"][3] - r2["bbox"][1])

        return intersection / min(area1, area2)

    result = []
    removed = set()

    for i, r1 in enumerate(regions):
        if i in removed:
            continue

        keep = True
        for j, r2 in enumerate(regions):
            if i >= j or j in removed:
                continue

            # 異なるタイプは除去しない
            if r1["type"] != r2["type"]:
                continue

            overlap = calculate_overlap(r1, r2)
            if overlap >= 0.5:
                if r1["confidence"] < r2["confidence"]:
                    keep = False
                    removed.add(i)
                    break
                else:
                    removed.add(j)

        if keep:
            result.append(r1)

    return result
```

## FAIL出力例

```
$ make test
...
tests/test_reading_order.py::TestSortReadingOrderSimple::test_sort_reading_order_top_to_bottom FAILED
tests/test_reading_order.py::TestSortReadingOrderSimple::test_sort_reading_order_left_to_right_same_row FAILED
tests/test_reading_order.py::TestSortReadingOrderSimple::test_sort_reading_order_empty_list FAILED
tests/test_reading_order.py::TestSortReadingOrderSimple::test_sort_reading_order_single_region FAILED
tests/test_reading_order.py::TestSortReadingOrderTwoColumn::test_sort_reading_order_two_columns_left_first FAILED
tests/test_reading_order.py::TestSortReadingOrderTwoColumn::test_sort_reading_order_two_columns_mixed_y FAILED
tests/test_reading_order.py::TestSortReadingOrderTwoColumn::test_sort_reading_order_center_regions FAILED
tests/test_reading_order.py::TestSortReadingOrderTitlePriority::test_sort_reading_order_title_before_text_same_y FAILED
tests/test_reading_order.py::TestSortReadingOrderTitlePriority::test_sort_reading_order_title_priority_with_y_sort FAILED
tests/test_reading_order.py::TestSortReadingOrderTitlePriority::test_sort_reading_order_title_at_top_of_page FAILED
tests/test_reading_order.py::TestRemoveOverlaps::test_remove_overlaps_no_overlap FAILED
tests/test_reading_order.py::TestRemoveOverlaps::test_remove_overlaps_complete_overlap FAILED
tests/test_reading_order.py::TestRemoveOverlaps::test_remove_overlaps_partial_overlap FAILED
tests/test_reading_order.py::TestRemoveOverlaps::test_remove_overlaps_low_overlap_both_kept FAILED
tests/test_reading_order.py::TestRemoveOverlaps::test_remove_overlaps_empty_list FAILED
tests/test_reading_order.py::TestRemoveOverlaps::test_remove_overlaps_different_types_kept FAILED
tests/test_reading_order.py::TestSortReadingOrderEdgeCases::test_sort_reading_order_unicode_content_preserved FAILED
tests/test_reading_order.py::TestSortReadingOrderEdgeCases::test_sort_reading_order_immutable_input FAILED
tests/test_reading_order.py::TestSortReadingOrderEdgeCases::test_sort_reading_order_large_page FAILED
tests/test_reading_order.py::TestSortReadingOrderEdgeCases::test_sort_reading_order_negative_coords_handled FAILED

E       ModuleNotFoundError: No module named 'src.reading_order'

=================== 20 failed, 0 passed ===================
```

## 次のステップ

1. **T028**: この RED テスト結果を読み取る
2. **T029**: `sort_reading_order()` 関数を `src/reading_order.py` に実装
3. **T030**: `remove_overlaps()` 関数を `src/reading_order.py` に実装
4. **T031**: `make test` で全テストPASSを確認 (GREEN)

## テスト対象関数

### sort_reading_order(regions: list[dict], page_width: int) -> list[dict]

横書きレイアウトの読み順でソート:
- カラム検出: ページ中央で左/右カラムに分類
- 各カラム内をY座標でソート
- 同一Y座標の場合、TITLE優先
- 左→右の順で結合
- 入力リストを変更しない（イミュータブル）

### remove_overlaps(regions: list[dict]) -> list[dict]

重複領域の検出と除去:
- 重複率50%以上で信頼度の低い方を除去
- 異なるタイプの領域は除去しない
- 重複率30%未満は両方保持
