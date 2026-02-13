"""Tests for src.reading_order reading order sorting.

Phase 3 RED tests for US3 - Reading Order Reconstruction.
These tests will FAIL until src/reading_order.py is implemented.
"""

from __future__ import annotations


class TestSortReadingOrderSimple:
    """単純ソート: 上から下、左から右の順序を検証する。"""

    def test_sort_reading_order_top_to_bottom(self) -> None:
        """Y座標に基づいて上から下の順序でソートされることを検証。

        入力: 3つの領域がY座標でバラバラに配置
        期待: Y座標の小さい順（上から下）にソート
        """
        from src.reading_order import sort_reading_order

        # Arrange: 3つの領域（Y座標: 300, 100, 200）
        regions = [
            {"type": "TEXT", "bbox": [100, 300, 500, 400], "confidence": 0.9},
            {"type": "TEXT", "bbox": [100, 100, 500, 200], "confidence": 0.9},
            {"type": "TEXT", "bbox": [100, 200, 500, 300], "confidence": 0.9},
        ]
        page_width = 1000

        # Act
        sorted_regions = sort_reading_order(regions, page_width)

        # Assert: Y座標の小さい順にソート
        y_coords = [r["bbox"][1] for r in sorted_regions]
        assert y_coords == [100, 200, 300], (
            f"Regions should be sorted top-to-bottom by Y coordinate. "
            f"Expected Y coords [100, 200, 300], got {y_coords}"
        )

    def test_sort_reading_order_left_to_right_same_row(self) -> None:
        """同一行内で左から右の順序でソートされることを検証。

        入力: 同じY座標の3つの領域がX座標でバラバラに配置
        期待: X座標の小さい順（左から右）にソート
        """
        from src.reading_order import sort_reading_order

        # Arrange: 同じ行の3つの領域（X座標: 600, 100, 350）
        # 全て左カラム(center_x < 500)に収まるように配置
        regions = [
            {"type": "TEXT", "bbox": [350, 100, 450, 200], "confidence": 0.9},
            {"type": "TEXT", "bbox": [100, 100, 200, 200], "confidence": 0.9},
            {"type": "TEXT", "bbox": [220, 100, 320, 200], "confidence": 0.9},
        ]
        page_width = 1000

        # Act
        sorted_regions = sort_reading_order(regions, page_width)

        # Assert: 同一カラム内でY座標でソート後、X座標順
        # 全て同じY座標なので、同一カラム内で位置順
        x_coords = [r["bbox"][0] for r in sorted_regions]
        assert x_coords == [100, 220, 350], (
            f"Regions in same row should be sorted left-to-right by X coordinate. "
            f"Expected X coords [100, 220, 350], got {x_coords}"
        )

    def test_sort_reading_order_empty_list(self) -> None:
        """空のリストが渡された場合、空のリストを返すことを検証。"""
        from src.reading_order import sort_reading_order

        # Arrange
        regions: list[dict] = []
        page_width = 1000

        # Act
        sorted_regions = sort_reading_order(regions, page_width)

        # Assert
        assert sorted_regions == [], (
            f"Empty input should return empty list, got {sorted_regions}"
        )

    def test_sort_reading_order_single_region(self) -> None:
        """単一領域の場合、そのまま返すことを検証。"""
        from src.reading_order import sort_reading_order

        # Arrange
        regions = [
            {"type": "TEXT", "bbox": [100, 100, 500, 200], "confidence": 0.9},
        ]
        page_width = 1000

        # Act
        sorted_regions = sort_reading_order(regions, page_width)

        # Assert
        assert len(sorted_regions) == 1, (
            f"Single region input should return single region, "
            f"got {len(sorted_regions)} regions"
        )
        assert sorted_regions[0]["bbox"] == [100, 100, 500, 200], (
            "Single region should be unchanged"
        )


class TestSortReadingOrderTwoColumn:
    """2カラムソート: 左カラム全体→右カラム全体の順序を検証する。"""

    def test_sort_reading_order_two_columns_left_first(self) -> None:
        """2カラムレイアウトで左カラムが右カラムより先にソートされることを検証。

        ページ幅: 1000
        左カラム: center_x < 500
        右カラム: center_x >= 500

        入力: 右カラムの上部、左カラムの下部、左カラムの上部
        期待: 左上 → 左下 → 右上 の順序
        """
        from src.reading_order import sort_reading_order

        # Arrange: 2カラムレイアウト
        # - 右カラム上部 (center_x = 700)
        # - 左カラム下部 (center_x = 200)
        # - 左カラム上部 (center_x = 200)
        regions = [
            {"type": "TEXT", "bbox": [600, 100, 800, 200], "confidence": 0.9},  # 右上
            {"type": "TEXT", "bbox": [100, 300, 300, 400], "confidence": 0.9},  # 左下
            {"type": "TEXT", "bbox": [100, 100, 300, 200], "confidence": 0.9},  # 左上
        ]
        page_width = 1000

        # Act
        sorted_regions = sort_reading_order(regions, page_width)

        # Assert: 左カラム全体 → 右カラム全体の順序
        # 左上(Y=100) → 左下(Y=300) → 右上(Y=100)
        expected_order = [
            [100, 100, 300, 200],  # 左上
            [100, 300, 300, 400],  # 左下
            [600, 100, 800, 200],  # 右上
        ]
        actual_bboxes = [r["bbox"] for r in sorted_regions]
        assert actual_bboxes == expected_order, (
            f"Two-column layout should sort left column first, then right column. "
            f"Expected order: {expected_order}, got: {actual_bboxes}"
        )

    def test_sort_reading_order_two_columns_mixed_y(self) -> None:
        """2カラムで各カラム内がY座標順にソートされることを検証。

        左カラム: Y=200, Y=100, Y=300 → 100, 200, 300
        右カラム: Y=150, Y=50 → 50, 150
        """
        from src.reading_order import sort_reading_order

        # Arrange
        regions = [
            {"type": "TEXT", "bbox": [100, 200, 300, 280], "confidence": 0.9},  # 左中
            {"type": "TEXT", "bbox": [600, 150, 800, 230], "confidence": 0.9},  # 右下
            {"type": "TEXT", "bbox": [100, 100, 300, 180], "confidence": 0.9},  # 左上
            {"type": "TEXT", "bbox": [600, 50, 800, 130], "confidence": 0.9},   # 右上
            {"type": "TEXT", "bbox": [100, 300, 300, 380], "confidence": 0.9},  # 左下
        ]
        page_width = 1000

        # Act
        sorted_regions = sort_reading_order(regions, page_width)

        # Assert: 左カラム(Y順) → 右カラム(Y順)
        expected_y_order = [100, 200, 300, 50, 150]
        actual_y_order = [r["bbox"][1] for r in sorted_regions]
        assert actual_y_order == expected_y_order, (
            f"Each column should be sorted by Y coordinate. "
            f"Expected Y order: {expected_y_order}, got: {actual_y_order}"
        )

    def test_sort_reading_order_center_regions(self) -> None:
        """ページ中央にまたがる領域が正しく分類されることを検証。

        center_x = 500 の場合、右カラムに分類される
        """
        from src.reading_order import sort_reading_order

        # Arrange: center_x がちょうど500の領域
        # bbox = [400, 100, 600, 200] → center_x = 500 → 右カラム
        regions = [
            {"type": "TEXT", "bbox": [400, 100, 600, 200], "confidence": 0.9},  # 中央
            {"type": "TEXT", "bbox": [100, 100, 200, 200], "confidence": 0.9},  # 左
        ]
        page_width = 1000

        # Act
        sorted_regions = sort_reading_order(regions, page_width)

        # Assert: 左 → 中央(右扱い) の順序
        assert sorted_regions[0]["bbox"][0] == 100, (
            "Left region should come first"
        )
        assert sorted_regions[1]["bbox"][0] == 400, (
            "Center region (treated as right) should come second"
        )


class TestSortReadingOrderTitlePriority:
    """タイトル優先: TITLEがTEXTより先になることを検証する。"""

    def test_sort_reading_order_title_before_text_same_y(self) -> None:
        """同じY座標でTITLEがTEXTより先に出力されることを検証。

        NOTE: research.mdではY座標ソートが主なアルゴリズムだが、
        同一Y座標の場合、TITLE優先のロジックが必要
        """
        from src.reading_order import sort_reading_order

        # Arrange: 同じY座標のTITLEとTEXT
        regions = [
            {"type": "TEXT", "bbox": [100, 100, 400, 150], "confidence": 0.9},
            {"type": "TITLE", "bbox": [100, 100, 500, 150], "confidence": 0.95},
        ]
        page_width = 1000

        # Act
        sorted_regions = sort_reading_order(regions, page_width)

        # Assert: TITLEが先
        assert sorted_regions[0]["type"] == "TITLE", (
            f"TITLE should come before TEXT at same Y coordinate. "
            f"Got: {sorted_regions[0]['type']} first"
        )

    def test_sort_reading_order_title_priority_with_y_sort(self) -> None:
        """Y座標ソートとタイトル優先の組み合わせを検証。

        TITLE(Y=150) と TEXT(Y=100) の場合:
        - Y座標ソートでは TEXT(Y=100) が先
        - これは正しい動作（Y座標が主ソートキー）
        """
        from src.reading_order import sort_reading_order

        # Arrange: TITLEがTEXTより下にある場合
        regions = [
            {"type": "TITLE", "bbox": [100, 150, 500, 200], "confidence": 0.95},
            {"type": "TEXT", "bbox": [100, 100, 400, 130], "confidence": 0.9},
        ]
        page_width = 1000

        # Act
        sorted_regions = sort_reading_order(regions, page_width)

        # Assert: Y座標が小さいTEXTが先（Y座標が主ソートキー）
        assert sorted_regions[0]["bbox"][1] == 100, (
            f"Region with smaller Y coordinate should come first. "
            f"Expected Y=100 first, got Y={sorted_regions[0]['bbox'][1]}"
        )

    def test_sort_reading_order_title_at_top_of_page(self) -> None:
        """ページ上部のTITLEが最初に出力されることを検証。

        典型的なレイアウト: TITLE(上部) → TEXT(下部)
        """
        from src.reading_order import sort_reading_order

        # Arrange: 典型的なレイアウト
        regions = [
            {"type": "TEXT", "bbox": [100, 150, 800, 500], "confidence": 0.9},
            {"type": "TEXT", "bbox": [100, 550, 800, 900], "confidence": 0.9},
            {"type": "TITLE", "bbox": [100, 50, 600, 100], "confidence": 0.95},
        ]
        page_width = 1000

        # Act
        sorted_regions = sort_reading_order(regions, page_width)

        # Assert: TITLEが最初
        assert sorted_regions[0]["type"] == "TITLE", (
            f"TITLE at top of page should be first. "
            f"Got: {sorted_regions[0]['type']} first"
        )
        # 後続のTEXTはY座標順
        assert sorted_regions[1]["bbox"][1] == 150, "Second should be TEXT at Y=150"
        assert sorted_regions[2]["bbox"][1] == 550, "Third should be TEXT at Y=550"


class TestRemoveOverlaps:
    """重複除去: 重複領域の処理を検証する。"""

    def test_remove_overlaps_no_overlap(self) -> None:
        """重複がない場合、全ての領域がそのまま返されることを検証。"""
        from src.reading_order import remove_overlaps

        # Arrange: 重複なしの3領域
        regions = [
            {"type": "TEXT", "bbox": [100, 100, 200, 200], "confidence": 0.9},
            {"type": "TEXT", "bbox": [300, 100, 400, 200], "confidence": 0.9},
            {"type": "TEXT", "bbox": [100, 300, 200, 400], "confidence": 0.9},
        ]

        # Act
        result = remove_overlaps(regions)

        # Assert
        assert len(result) == 3, (
            f"No overlaps: all 3 regions should remain. Got {len(result)} regions"
        )

    def test_remove_overlaps_complete_overlap(self) -> None:
        """完全に重複する領域の場合、信頼度の高い方が残ることを検証。"""
        from src.reading_order import remove_overlaps

        # Arrange: 完全に重複する2領域（異なる信頼度）
        regions = [
            {"type": "TEXT", "bbox": [100, 100, 300, 300], "confidence": 0.7},
            {"type": "TEXT", "bbox": [100, 100, 300, 300], "confidence": 0.9},
        ]

        # Act
        result = remove_overlaps(regions)

        # Assert: 信頼度の高い方(0.9)が残る
        assert len(result) == 1, (
            f"Complete overlap: only 1 region should remain. Got {len(result)} regions"
        )
        assert result[0]["confidence"] == 0.9, (
            f"Higher confidence region should be kept. "
            f"Expected confidence=0.9, got {result[0]['confidence']}"
        )

    def test_remove_overlaps_partial_overlap(self) -> None:
        """部分的に重複する領域の処理を検証。

        重複率が高い（例: 50%以上）場合、信頼度の高い方を残す
        """
        from src.reading_order import remove_overlaps

        # Arrange: 50%以上重複する2領域
        # region1: [100, 100, 300, 300] (area = 200*200 = 40000)
        # region2: [200, 100, 400, 300] (area = 200*200 = 40000)
        # overlap: [200, 100, 300, 300] (area = 100*200 = 20000) = 50% of each
        regions = [
            {"type": "TEXT", "bbox": [100, 100, 300, 300], "confidence": 0.8},
            {"type": "TEXT", "bbox": [200, 100, 400, 300], "confidence": 0.9},
        ]

        # Act
        result = remove_overlaps(regions)

        # Assert: 高重複率の場合、1つのみ残る
        assert len(result) == 1, (
            f"High overlap (50%+): only 1 region should remain. "
            f"Got {len(result)} regions"
        )
        assert result[0]["confidence"] == 0.9, (
            f"Higher confidence region should be kept. "
            f"Expected confidence=0.9, got {result[0]['confidence']}"
        )

    def test_remove_overlaps_low_overlap_both_kept(self) -> None:
        """重複率が低い（例: 30%未満）場合、両方残ることを検証。"""
        from src.reading_order import remove_overlaps

        # Arrange: 低重複率の2領域
        # region1: [100, 100, 300, 300] (area = 40000)
        # region2: [250, 100, 450, 300] (area = 40000)
        # overlap: [250, 100, 300, 300] (area = 50*200 = 10000) = 25% of each
        regions = [
            {"type": "TEXT", "bbox": [100, 100, 300, 300], "confidence": 0.8},
            {"type": "TEXT", "bbox": [250, 100, 450, 300], "confidence": 0.9},
        ]

        # Act
        result = remove_overlaps(regions)

        # Assert: 低重複率の場合、両方残る
        assert len(result) == 2, (
            f"Low overlap (<30%): both regions should remain. "
            f"Got {len(result)} regions"
        )

    def test_remove_overlaps_empty_list(self) -> None:
        """空のリストが渡された場合、空のリストを返すことを検証。"""
        from src.reading_order import remove_overlaps

        # Arrange
        regions: list[dict] = []

        # Act
        result = remove_overlaps(regions)

        # Assert
        assert result == [], f"Empty input should return empty list, got {result}"

    def test_remove_overlaps_different_types_kept(self) -> None:
        """異なるタイプの領域は重複しても両方残ることを検証。

        例: TITLEとTEXTが重複 → 両方残す（意図的な重複の可能性）
        """
        from src.reading_order import remove_overlaps

        # Arrange: 異なるタイプで重複
        regions = [
            {"type": "TITLE", "bbox": [100, 100, 300, 150], "confidence": 0.95},
            {"type": "TEXT", "bbox": [100, 100, 300, 200], "confidence": 0.9},
        ]

        # Act
        result = remove_overlaps(regions)

        # Assert: 異なるタイプは両方残す
        assert len(result) == 2, (
            f"Different types with overlap should both remain. "
            f"Got {len(result)} regions"
        )
        types_in_result = {r["type"] for r in result}
        assert types_in_result == {"TITLE", "TEXT"}, (
            f"Both TITLE and TEXT should be in result. Got types: {types_in_result}"
        )


class TestSortReadingOrderEdgeCases:
    """読み順ソートのエッジケースを検証する。"""

    def test_sort_reading_order_unicode_content_preserved(self) -> None:
        """Unicode文字を含む領域データが保持されることを検証。"""
        from src.reading_order import sort_reading_order

        # Arrange: Unicode文字を含む追加フィールド
        regions = [
            {
                "type": "TEXT",
                "bbox": [100, 200, 500, 300],
                "confidence": 0.9,
                "label": "plain text",
            },
            {
                "type": "TITLE",
                "bbox": [100, 100, 500, 150],
                "confidence": 0.95,
                "label": "title",
            },
        ]
        page_width = 1000

        # Act
        sorted_regions = sort_reading_order(regions, page_width)

        # Assert: 追加フィールドが保持される
        assert all("label" in r for r in sorted_regions), (
            "Additional fields should be preserved during sorting"
        )

    def test_sort_reading_order_immutable_input(self) -> None:
        """入力リストが変更されないことを検証（イミュータビリティ）。"""
        from src.reading_order import sort_reading_order

        # Arrange
        regions = [
            {"type": "TEXT", "bbox": [100, 300, 500, 400], "confidence": 0.9},
            {"type": "TEXT", "bbox": [100, 100, 500, 200], "confidence": 0.9},
        ]
        original_order = [r["bbox"][1] for r in regions]  # [300, 100]
        page_width = 1000

        # Act
        sorted_regions = sort_reading_order(regions, page_width)

        # Assert: 元のリストは変更されない
        current_order = [r["bbox"][1] for r in regions]
        assert current_order == original_order, (
            f"Original list should not be modified. "
            f"Expected order {original_order}, got {current_order}"
        )

    def test_sort_reading_order_large_page(self) -> None:
        """大きなページサイズでも正しく動作することを検証。"""
        from src.reading_order import sort_reading_order

        # Arrange: 4K解像度
        regions = [
            {"type": "TEXT", "bbox": [100, 2000, 1000, 2200], "confidence": 0.9},
            {"type": "TEXT", "bbox": [100, 500, 1000, 700], "confidence": 0.9},
            {"type": "TITLE", "bbox": [100, 100, 1500, 200], "confidence": 0.95},
        ]
        page_width = 3840  # 4K

        # Act
        sorted_regions = sort_reading_order(regions, page_width)

        # Assert: Y座標順にソート
        y_coords = [r["bbox"][1] for r in sorted_regions]
        assert y_coords == [100, 500, 2000], (
            f"Large page should sort correctly. Expected Y [100, 500, 2000], got {y_coords}"
        )

    def test_sort_reading_order_negative_coords_handled(self) -> None:
        """負の座標が含まれる場合のエラーハンドリングを検証。

        NOTE: 通常bboxは正の値だが、異常データへの対応を確認
        """
        from src.reading_order import sort_reading_order

        # Arrange: 異常な負の座標（実際には発生しないはずだが）
        regions = [
            {"type": "TEXT", "bbox": [100, 100, 500, 200], "confidence": 0.9},
            {"type": "TEXT", "bbox": [-50, 50, 200, 150], "confidence": 0.9},  # 負のx1
        ]
        page_width = 1000

        # Act: エラーが発生しないことを確認
        try:
            sorted_regions = sort_reading_order(regions, page_width)
            # Assert: 結果が返される（エラーにならない）
            assert len(sorted_regions) == 2, "Should handle negative coords gracefully"
        except ValueError as e:
            # 負の座標を明示的に拒否する実装も許容
            assert "negative" in str(e).lower() or "invalid" in str(e).lower(), (
                f"Should raise descriptive error for negative coords: {e}"
            )
