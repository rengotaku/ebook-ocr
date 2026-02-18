"""Tests for src.detect_figures layout detection.

Phase 2 RED tests for US1 - Extended Layout Detection.
These tests will FAIL until implementation is complete.
"""

from __future__ import annotations

from src.layout.figures import LABEL_TYPE_MAP


class TestLabelTypeMapExtension:
    """LABEL_TYPE_MAP が10クラスを含むことを検証する。"""

    def test_label_type_map_has_10_classes(self) -> None:
        """LABEL_TYPE_MAP が10クラスを含むことを検証。

        DocLayout-YOLOの全クラス:
        - title, plain text, abandon, figure, figure_caption,
        - table, table_caption, table_footnote, isolated formula, formula_caption
        """
        expected_count = 10
        actual_count = len(LABEL_TYPE_MAP)

        assert actual_count == expected_count, (
            f"LABEL_TYPE_MAP should contain {expected_count} classes, "
            f"but has {actual_count} classes: {list(LABEL_TYPE_MAP.keys())}"
        )

    def test_label_type_map_contains_title(self) -> None:
        """LABEL_TYPE_MAP が 'title' クラスを含むことを検証。"""
        assert "title" in LABEL_TYPE_MAP, (
            "'title' class should be in LABEL_TYPE_MAP"
        )
        assert LABEL_TYPE_MAP["title"] == "TITLE", (
            f"'title' should map to 'TITLE', got '{LABEL_TYPE_MAP.get('title')}'"
        )

    def test_label_type_map_contains_plain_text(self) -> None:
        """LABEL_TYPE_MAP が 'plain text' クラスを含むことを検証。"""
        assert "plain text" in LABEL_TYPE_MAP, (
            "'plain text' class should be in LABEL_TYPE_MAP"
        )
        assert LABEL_TYPE_MAP["plain text"] == "TEXT", (
            f"'plain text' should map to 'TEXT', got '{LABEL_TYPE_MAP.get('plain text')}'"
        )

    def test_label_type_map_contains_abandon(self) -> None:
        """LABEL_TYPE_MAP が 'abandon' クラスを含むことを検証。"""
        assert "abandon" in LABEL_TYPE_MAP, (
            "'abandon' class should be in LABEL_TYPE_MAP"
        )
        assert LABEL_TYPE_MAP["abandon"] == "ABANDON", (
            f"'abandon' should map to 'ABANDON', got '{LABEL_TYPE_MAP.get('abandon')}'"
        )

    def test_label_type_map_contains_figure_caption(self) -> None:
        """LABEL_TYPE_MAP が 'figure_caption' クラスを含むことを検証。"""
        assert "figure_caption" in LABEL_TYPE_MAP, (
            "'figure_caption' class should be in LABEL_TYPE_MAP"
        )
        assert LABEL_TYPE_MAP["figure_caption"] == "CAPTION", (
            f"'figure_caption' should map to 'CAPTION', got '{LABEL_TYPE_MAP.get('figure_caption')}'"
        )

    def test_label_type_map_contains_table_caption(self) -> None:
        """LABEL_TYPE_MAP が 'table_caption' クラスを含むことを検証。"""
        assert "table_caption" in LABEL_TYPE_MAP, (
            "'table_caption' class should be in LABEL_TYPE_MAP"
        )
        assert LABEL_TYPE_MAP["table_caption"] == "CAPTION", (
            f"'table_caption' should map to 'CAPTION', got '{LABEL_TYPE_MAP.get('table_caption')}'"
        )

    def test_label_type_map_contains_table_footnote(self) -> None:
        """LABEL_TYPE_MAP が 'table_footnote' クラスを含むことを検証。"""
        assert "table_footnote" in LABEL_TYPE_MAP, (
            "'table_footnote' class should be in LABEL_TYPE_MAP"
        )
        assert LABEL_TYPE_MAP["table_footnote"] == "FOOTNOTE", (
            f"'table_footnote' should map to 'FOOTNOTE', got '{LABEL_TYPE_MAP.get('table_footnote')}'"
        )

    def test_label_type_map_contains_formula_caption(self) -> None:
        """LABEL_TYPE_MAP が 'formula_caption' クラスを含むことを検証。"""
        assert "formula_caption" in LABEL_TYPE_MAP, (
            "'formula_caption' class should be in LABEL_TYPE_MAP"
        )
        assert LABEL_TYPE_MAP["formula_caption"] == "CAPTION", (
            f"'formula_caption' should map to 'CAPTION', got '{LABEL_TYPE_MAP.get('formula_caption')}'"
        )

    def test_label_type_map_existing_classes_preserved(self) -> None:
        """既存クラス (table, figure, isolated formula) が保持されていることを検証。"""
        # table
        assert "table" in LABEL_TYPE_MAP, "'table' should be in LABEL_TYPE_MAP"
        assert LABEL_TYPE_MAP["table"] == "TABLE", (
            f"'table' should map to 'TABLE', got '{LABEL_TYPE_MAP.get('table')}'"
        )

        # figure
        assert "figure" in LABEL_TYPE_MAP, "'figure' should be in LABEL_TYPE_MAP"
        assert LABEL_TYPE_MAP["figure"] == "FIGURE", (
            f"'figure' should map to 'FIGURE', got '{LABEL_TYPE_MAP.get('figure')}'"
        )

        # isolated formula
        assert "isolated formula" in LABEL_TYPE_MAP, (
            "'isolated formula' should be in LABEL_TYPE_MAP"
        )
        assert LABEL_TYPE_MAP["isolated formula"] == "FORMULA", (
            f"'isolated formula' should map to 'FORMULA', "
            f"got '{LABEL_TYPE_MAP.get('isolated formula')}'"
        )


class TestLayoutJsonRegionsStructure:
    """layout.json 出力が 'regions' キーを持つことを検証する。"""

    def test_detect_figures_output_uses_regions_key(self, tmp_path) -> None:
        """detect_figures() の出力が 'figures' ではなく 'regions' キーを使用することを検証。

        現在の出力:
        {"page_001.png": {"figures": [...]}}

        期待する出力:
        {"page_001.png": {"regions": [...], "page_size": [w, h]}}
        """
        import json
        from unittest.mock import MagicMock, patch

        from PIL import Image

        # テスト用ページ画像を作成
        page_dir = tmp_path / "pages"
        page_dir.mkdir()
        img = Image.new("RGB", (1920, 1080), color=(255, 255, 255))
        img.save(page_dir / "page_001.png")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # tolist()メソッドを持つbboxモック
        mock_bbox = MagicMock()
        mock_bbox.tolist.return_value = [100, 100, 500, 500]

        # YOLOモデルをモック（検出結果を返す）
        mock_box = MagicMock()
        mock_box.cls = [0]  # class index
        mock_box.conf = [0.95]  # confidence
        mock_box.xyxy = [mock_bbox]  # bbox with tolist()

        mock_result = MagicMock()
        mock_result.boxes = [mock_box]
        mock_result.names = {0: "figure"}  # 既存クラスを使用

        mock_model = MagicMock()
        mock_model.predict.return_value = [mock_result]

        # detect_figures imports inside the function, so we need to patch the modules
        with patch.dict("sys.modules", {
            "doclayout_yolo": MagicMock(YOLOv10=MagicMock(return_value=mock_model)),
            "huggingface_hub": MagicMock(hf_hub_download=MagicMock(return_value="/tmp/model.pt")),
        }):
            # Force reload to pick up mocked modules
            import importlib

            import src.layout.figures
            importlib.reload(src.layout.figures)
            layout = src.layout.figures.detect_figures(str(page_dir), str(output_dir))

        # layout.json を読み込み
        layout_path = output_dir / "layout.json"
        if layout_path.exists():
            layout_data = json.loads(layout_path.read_text(encoding="utf-8"))
        else:
            layout_data = layout

        # 出力にデータがある場合、regions キーを確認
        if layout_data:
            page_key = list(layout_data.keys())[0]
            page_data = layout_data[page_key]

            assert "regions" in page_data, (
                f"Page data should have 'regions' key instead of 'figures'. "
                f"Got keys: {list(page_data.keys())}"
            )
            assert "figures" not in page_data, (
                "'figures' key should be replaced with 'regions'"
            )


class TestLayoutJsonPageSize:
    """layout.json 出力に page_size が含まれることを検証する。"""

    def test_detect_figures_output_includes_page_size(self, tmp_path) -> None:
        """detect_figures() の出力に page_size フィールドが含まれることを検証。

        期待する構造:
        {
            "page_001.png": {
                "regions": [...],
                "page_size": [1920, 1080]
            }
        }
        """
        import json
        from unittest.mock import MagicMock, patch

        from PIL import Image

        # テスト用ページ画像を作成
        page_dir = tmp_path / "pages"
        page_dir.mkdir()
        expected_width = 1920
        expected_height = 1080
        img = Image.new("RGB", (expected_width, expected_height), color=(255, 255, 255))
        img.save(page_dir / "page_001.png")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # tolist()メソッドを持つbboxモック
        mock_bbox = MagicMock()
        mock_bbox.tolist.return_value = [100, 100, 500, 500]

        # YOLOモデルをモック（検出結果を返す）
        mock_box = MagicMock()
        mock_box.cls = [0]
        mock_box.conf = [0.95]
        mock_box.xyxy = [mock_bbox]  # bbox with tolist()

        mock_result = MagicMock()
        mock_result.boxes = [mock_box]
        mock_result.names = {0: "figure"}  # 既存クラスを使用

        mock_model = MagicMock()
        mock_model.predict.return_value = [mock_result]

        # detect_figures imports inside the function, so we need to patch the modules
        with patch.dict("sys.modules", {
            "doclayout_yolo": MagicMock(YOLOv10=MagicMock(return_value=mock_model)),
            "huggingface_hub": MagicMock(hf_hub_download=MagicMock(return_value="/tmp/model.pt")),
        }):
            # Force reload to pick up mocked modules
            import importlib

            import src.layout.figures
            importlib.reload(src.layout.figures)
            layout = src.layout.figures.detect_figures(str(page_dir), str(output_dir))

        # layout.json を読み込み
        layout_path = output_dir / "layout.json"
        if layout_path.exists():
            layout_data = json.loads(layout_path.read_text(encoding="utf-8"))
        else:
            layout_data = layout

        # page_size フィールドを確認
        if layout_data:
            page_key = list(layout_data.keys())[0]
            page_data = layout_data[page_key]

            assert "page_size" in page_data, (
                f"Page data should have 'page_size' key. Got keys: {list(page_data.keys())}"
            )

            page_size = page_data["page_size"]
            assert isinstance(page_size, list), (
                f"page_size should be a list, got {type(page_size)}"
            )
            assert len(page_size) == 2, (
                f"page_size should have 2 elements [width, height], got {page_size}"
            )
            assert page_size[0] == expected_width, (
                f"page_size width should be {expected_width}, got {page_size[0]}"
            )
            assert page_size[1] == expected_height, (
                f"page_size height should be {expected_height}, got {page_size[1]}"
            )


class TestMinAreaFiltering:
    """最小面積しきい値未満の領域が除外されることを検証する。"""

    def test_detect_figures_filters_small_regions(self, tmp_path) -> None:
        """ページ面積の1%未満の小さな領域がノイズとして除外されることを検証。

        ページサイズ: 1920x1080 = 2,073,600 px
        1% = 20,736 px

        テストケース:
        - 大きな領域 (400x400 = 160,000 px) → 保持
        - 小さな領域 (50x50 = 2,500 px) → 除外 (< 1%)
        """
        import json
        from unittest.mock import MagicMock, patch

        from PIL import Image

        # テスト用ページ画像を作成
        page_dir = tmp_path / "pages"
        page_dir.mkdir()
        img = Image.new("RGB", (1920, 1080), color=(255, 255, 255))
        img.save(page_dir / "page_001.png")

        output_dir = tmp_path / "output"
        output_dir.mkdir()

        # 大きな領域用bboxモック
        large_bbox = MagicMock()
        large_bbox.tolist.return_value = [100, 100, 500, 500]  # 400x400 = 160,000 px

        # 大きな領域 (160,000 px = 7.7%) - 既存クラス使用
        large_box = MagicMock()
        large_box.cls = [0]
        large_box.conf = [0.95]
        large_box.xyxy = [large_bbox]

        # 小さな領域用bboxモック
        small_bbox = MagicMock()
        small_bbox.tolist.return_value = [600, 600, 650, 650]  # 50x50 = 2,500 px

        # 小さな領域 (2,500 px = 0.12%) - 既存クラス使用
        small_box = MagicMock()
        small_box.cls = [1]
        small_box.conf = [0.90]
        small_box.xyxy = [small_bbox]

        mock_result = MagicMock()
        mock_result.boxes = [large_box, small_box]
        mock_result.names = {0: "figure", 1: "table"}  # 既存クラスを使用

        mock_model = MagicMock()
        mock_model.predict.return_value = [mock_result]

        # detect_figures imports inside the function, so we need to patch the modules
        with patch.dict("sys.modules", {
            "doclayout_yolo": MagicMock(YOLOv10=MagicMock(return_value=mock_model)),
            "huggingface_hub": MagicMock(hf_hub_download=MagicMock(return_value="/tmp/model.pt")),
        }):
            # Force reload to pick up mocked modules
            import importlib

            import src.layout.figures
            importlib.reload(src.layout.figures)
            layout = src.layout.figures.detect_figures(str(page_dir), str(output_dir))

        # layout.json を読み込み
        layout_path = output_dir / "layout.json"
        if layout_path.exists():
            layout_data = json.loads(layout_path.read_text(encoding="utf-8"))
        else:
            layout_data = layout

        # 小さな領域が除外されていることを確認
        if layout_data:
            page_key = list(layout_data.keys())[0]
            page_data = layout_data[page_key]

            # regions キーを使用（現在は figures キーなので失敗する）
            regions_key = "regions" if "regions" in page_data else "figures"
            regions = page_data.get(regions_key, [])

            # 大きな領域のみが残っているべき
            region_count = len(regions)
            assert region_count == 1, (
                f"Only 1 region (large) should remain after filtering. "
                f"Got {region_count} regions. "
                f"Small regions (<1% of page area) should be filtered out."
            )

    def test_detect_figures_min_area_parameter(self) -> None:
        """detect_figures() が min_area パラメータを受け入れることを検証。"""
        import inspect

        from src.layout.figures import detect_figures

        sig = inspect.signature(detect_figures)
        param_names = list(sig.parameters.keys())

        assert "min_area" in param_names, (
            f"detect_figures() should accept 'min_area' parameter. "
            f"Current parameters: {param_names}"
        )
