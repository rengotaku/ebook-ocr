# Phase 3 Output: US3 - 読み順の再構築

**日付**: 2026-02-11
**Phase**: Phase 3 (US3 - 読み順の再構築)
**ステータス**: GREEN - 全テスト成功

## 作業サマリ

Phase 3では、User Story 3「読み順の再構築」を実装しました。検出された領域をbbox座標に基づいて読み順にソートし、重複領域を除去する機能を追加しました。横書きレイアウト（上から下、左から右）に対応し、2カラムレイアウトの検出と、同一Y座標でのタイトル優先ソートを実装しました。

### 完了タスク

| タスクID | 説明 | ステータス |
|---------|------|----------|
| T028 | RED テスト結果読み取り | ✅ 完了 |
| T029 | sort_reading_order() 関数実装 | ✅ 完了 |
| T030 | remove_overlaps() 関数実装 | ✅ 完了 |
| T031 | `make test` PASS 確認 (GREEN) | ✅ 完了 |
| T032 | リグレッションテスト確認 | ✅ 完了 |
| T033 | Phase 3 出力生成 | ✅ 完了 |

**進捗**: 6/6 タスク完了 (100%)

---

## 変更ファイル一覧

### 実装追加

| ファイル | 変更種別 | 説明 |
|---------|---------|------|
| src/reading_order.py | 新規 | 読み順ソートアルゴリズムと重複除去機能 |

### テスト追加

| ファイル | 変更種別 | 説明 |
|---------|---------|------|
| tests/test_reading_order.py | 既存 | Phase 3 RED テスト（20テストケース） |

---

## 実装の詳細

### 1. sort_reading_order() 関数実装 (T029)

**ファイル**: `src/reading_order.py`

**アルゴリズム**:
1. カラム検出: ページ中央 (page_width / 2) で左右カラムに分類
2. 各カラム内をY座標でソート
3. 同一Y座標の場合、TYPE_PRIORITY に基づいて TITLE を TEXT より優先
4. 同一Y座標・同一タイプの場合、X座標でソート（左から右）
5. 左カラム → 右カラムの順で結合
6. 入力リストを変更しない（イミュータブル）

**関数シグネチャ**:
```python
def sort_reading_order(regions: list[dict], page_width: int) -> list[dict]:
    """横書きレイアウトの読み順でソート。

    Args:
        regions: 領域のリスト（type, bbox, confidenceを含む）
        page_width: ページ幅（カラム判定に使用）

    Returns:
        読み順でソートされた領域のリスト（新しいリスト、元は変更しない）
    """
```

**TYPE_PRIORITY**:
```python
TYPE_PRIORITY = {
    "TITLE": 0,
    "TEXT": 1,
    "CAPTION": 2,
    "FOOTNOTE": 3,
    "FIGURE": 4,
    "TABLE": 5,
    "FORMULA": 6,
    "ABANDON": 7,
}
```

**ソートキー**:
```python
def sort_key(r: dict) -> tuple[int, int, int]:
    y = r["bbox"][1]
    type_priority = TYPE_PRIORITY.get(r["type"], 99)
    x = r["bbox"][0]
    return (y, type_priority, x)
```

### 2. remove_overlaps() 関数実装 (T030)

**ファイル**: `src/reading_order.py`

**アルゴリズム**:
1. 各領域ペアの重複率を計算（IoU: Intersection over Union）
2. 重複率が50%以上の場合、信頼度の低い方を除去
3. 異なるタイプの領域は除去しない（意図的な重複の可能性）

**関数シグネチャ**:
```python
def remove_overlaps(regions: list[dict]) -> list[dict]:
    """重複領域の検出と除去。

    Args:
        regions: 領域のリスト

    Returns:
        重複を除去した領域のリスト
    """
```

**IoU計算関数**:
```python
def iou(r1: dict, r2: dict) -> float:
    """Intersection over Union (IoU) 比率を計算。

    IoU = intersection_area / smaller_area

    Args:
        r1: 第1領域
        r2: 第2領域

    Returns:
        IoU比率 (0.0 - 1.0)
    """
```

**重複除去ロジック**:
- IoU >= 0.5: 信頼度の低い方を除去
- IoU < 0.5: 両方保持
- 異なるタイプ: 常に両方保持

---

## テスト結果

### Phase 3 テスト (tests/test_reading_order.py)

```
20 passed in 0.03s
```

#### 通過したテスト一覧

| テストクラス | テストメソッド | 検証内容 |
|------------|--------------|---------|
| TestSortReadingOrderSimple | test_sort_reading_order_top_to_bottom | Y座標で上から下にソート |
| TestSortReadingOrderSimple | test_sort_reading_order_left_to_right_same_row | 同一行内で左から右にソート |
| TestSortReadingOrderSimple | test_sort_reading_order_empty_list | 空リストを空リストで返す |
| TestSortReadingOrderSimple | test_sort_reading_order_single_region | 単一領域をそのまま返す |
| TestSortReadingOrderTwoColumn | test_sort_reading_order_two_columns_left_first | 左カラム全体が右カラムより先 |
| TestSortReadingOrderTwoColumn | test_sort_reading_order_two_columns_mixed_y | 各カラム内がY座標順 |
| TestSortReadingOrderTwoColumn | test_sort_reading_order_center_regions | 中央領域が正しく分類される |
| TestSortReadingOrderTitlePriority | test_sort_reading_order_title_before_text_same_y | 同一Y座標でTITLEがTEXTより先 |
| TestSortReadingOrderTitlePriority | test_sort_reading_order_title_priority_with_y_sort | Y座標ソートとタイトル優先の組み合わせ |
| TestSortReadingOrderTitlePriority | test_sort_reading_order_title_at_top_of_page | ページ上部のTITLEが最初 |
| TestRemoveOverlaps | test_remove_overlaps_no_overlap | 重複なしで全領域保持 |
| TestRemoveOverlaps | test_remove_overlaps_complete_overlap | 完全重複で信頼度高い方を残す |
| TestRemoveOverlaps | test_remove_overlaps_partial_overlap | 部分重複(50%+)で1つのみ残す |
| TestRemoveOverlaps | test_remove_overlaps_low_overlap_both_kept | 低重複率で両方残す |
| TestRemoveOverlaps | test_remove_overlaps_empty_list | 空リストを空リストで返す |
| TestRemoveOverlaps | test_remove_overlaps_different_types_kept | 異なるタイプは両方残す |
| TestSortReadingOrderEdgeCases | test_sort_reading_order_unicode_content_preserved | Unicode文字を含むデータ保持 |
| TestSortReadingOrderEdgeCases | test_sort_reading_order_immutable_input | 入力リストが変更されない |
| TestSortReadingOrderEdgeCases | test_sort_reading_order_large_page | 大ページサイズで正しく動作 |
| TestSortReadingOrderEdgeCases | test_sort_reading_order_negative_coords_handled | 負の座標のエラーハンドリング |

### リグレッションテスト

関連テストファイル全て通過:
- `tests/test_reading_order.py`: 20/20 PASS
- `tests/test_detect_figures.py`: 13/13 PASS (Phase 2)
- `tests/test_ocr_deepseek.py`: 8/8 PASS
- `tests/test_utils.py`: 12/12 PASS

**合計**: 53/53 テスト成功

**Note**: book_converter モジュールの一部テスト（3件）は Phase 3 実装前から失敗しており、Phase 3 の変更とは無関係です。

---

## 次フェーズへの引き継ぎ

### 実装完了項目

1. ✅ **sort_reading_order()**: 2カラムレイアウト対応の読み順ソート
2. ✅ **remove_overlaps()**: 重複領域の検出と除去
3. ✅ **iou()**: Intersection over Union 計算

### 後続フェーズでの利用可能な機能

- `sort_reading_order(regions, page_width)`: 領域リストを読み順にソート
  - 横書きレイアウト（上→下、左→右）に対応
  - 2カラムレイアウトの自動検出
  - タイトル優先ソート（同一Y座標の場合）
  - イミュータブル（元のリストを変更しない）

- `remove_overlaps(regions)`: 重複領域の除去
  - IoU >= 0.5 で信頼度の低い方を除去
  - 異なるタイプの領域は保持

### Phase 4 で実装予定の機能

**User Story 2: 領域別OCR処理**
- 検出された各領域に対して適切なOCRエンジンを選択
- TEXT/TITLE → DeepSeek-OCR
- FIGURE → VLM (gemma3:12b)
- TABLE → DeepSeek-OCR (構造保持)
- 複数領域のOCR結果を連結

**依存関係**:
- Phase 4は、Phase 2で実装した `regions` 構造と Phase 3 で実装した `sort_reading_order()` を使用

---

## 発見した問題点

### なし

すべてのテストが成功し、既存機能への影響もありません。

---

## 備考

### カラム検出アルゴリズム

現在の実装は単純な中央分割（page_width / 2）を使用しています:
- `center_x < mid_x`: 左カラム
- `center_x >= mid_x`: 右カラム

**将来の拡張可能性**:
- 3カラム以上のレイアウト対応
- 動的なカラム幅検出
- 縦書きレイアウト対応

### イミュータビリティの遵守

`sort_reading_order()` 関数は入力リストを変更せず、新しいリストを返します:
```python
regions_copy = [r.copy() for r in regions]
```

これにより、以下のテストが成功します:
- `test_sort_reading_order_immutable_input`

### 重複除去のしきい値

現在の実装では IoU >= 0.5 で除去しています。この値は以下のテストで検証されています:
- `test_remove_overlaps_partial_overlap`: 50%重複で除去
- `test_remove_overlaps_low_overlap_both_kept`: 25%重複で保持

---

**ステータス**: ✅ Phase 3 完了 - 次は Phase 4 (US2 - 領域別OCR処理) へ
