"""Tests for new package structure (Phase 4: フォルダ構造整理).

このテストは新しいパッケージ構造が正しくインポート可能であることを検証する。
Phase 4の実装が完了するまで、これらのテストはFAILする（RED状態）。

新パッケージ構造:
- src/rover/: OCR統合（ocr_rover.py, ocr_engines.py, ocr_alignment.py, ocr_output.pyから移動）
- src/preprocessing/: 前処理（extract_frames.py, deduplicate.py, split_spread.py, video_hash.pyから移動）
- src/layout/: レイアウト解析（ocr_yomitoku.py, detect_figures.py, reading_order.pyから移動）
"""

import importlib


class TestNewPackageStructure:
    """新パッケージ構造がインポート可能であることを検証するテスト."""

    def test_rover_package_exists(self):
        """src.rover パッケージがインポート可能であることを検証."""
        rover = importlib.import_module("src.rover")
        assert rover is not None
        assert hasattr(rover, "__name__")
        assert rover.__name__ == "src.rover"

    def test_preprocessing_package_exists(self):
        """src.preprocessing パッケージがインポート可能であることを検証."""
        preprocessing = importlib.import_module("src.preprocessing")
        assert preprocessing is not None
        assert hasattr(preprocessing, "__name__")
        assert preprocessing.__name__ == "src.preprocessing"

    def test_layout_package_exists(self):
        """src.layout パッケージがインポート可能であることを検証."""
        layout = importlib.import_module("src.layout")
        assert layout is not None
        assert hasattr(layout, "__name__")
        assert layout.__name__ == "src.layout"


class TestRoverImports:
    """rover パッケージのエクスポートを検証するテスト."""

    def test_rover_ensemble_module_exists(self):
        """src.rover.ensemble モジュールがインポート可能であることを検証."""
        ensemble = importlib.import_module("src.rover.ensemble")
        assert ensemble is not None

    def test_rover_merge_importable(self):
        """rover_merge 関数が rover.ensemble からインポート可能であることを検証."""
        from src.rover.ensemble import rover_merge

        assert callable(rover_merge)

    def test_rover_engines_module_exists(self):
        """src.rover.engines モジュールがインポート可能であることを検証."""
        engines = importlib.import_module("src.rover.engines")
        assert engines is not None

    def test_run_all_engines_importable(self):
        """run_all_engines 関数が rover.engines からインポート可能であることを検証."""
        from src.rover.engines import run_all_engines

        assert callable(run_all_engines)

    def test_rover_alignment_module_exists(self):
        """src.rover.alignment モジュールがインポート可能であることを検証."""
        alignment = importlib.import_module("src.rover.alignment")
        assert alignment is not None

    def test_align_texts_importable(self):
        """align_texts_character_level 関数が rover.alignment からインポート可能であることを検証."""
        from src.rover.alignment import align_texts_character_level

        assert callable(align_texts_character_level)

    def test_rover_output_module_exists(self):
        """src.rover.output モジュールがインポート可能であることを検証."""
        output = importlib.import_module("src.rover.output")
        assert output is not None


class TestPreprocessingImports:
    """preprocessing パッケージのエクスポートを検証するテスト."""

    def test_preprocessing_frames_module_exists(self):
        """src.preprocessing.frames モジュールがインポート可能であることを検証."""
        frames = importlib.import_module("src.preprocessing.frames")
        assert frames is not None

    def test_extract_frames_importable(self):
        """extract_frames 関数が preprocessing.frames からインポート可能であることを検証."""
        from src.preprocessing.frames import extract_frames

        assert callable(extract_frames)

    def test_preprocessing_deduplicate_module_exists(self):
        """src.preprocessing.deduplicate モジュールがインポート可能であることを検証."""
        deduplicate = importlib.import_module("src.preprocessing.deduplicate")
        assert deduplicate is not None

    def test_deduplicate_frames_importable(self):
        """deduplicate_frames 関数が preprocessing.deduplicate からインポート可能であることを検証."""
        from src.preprocessing.deduplicate import deduplicate_frames

        assert callable(deduplicate_frames)

    def test_preprocessing_split_spread_module_exists(self):
        """src.preprocessing.split_spread モジュールがインポート可能であることを検証."""
        split_spread = importlib.import_module("src.preprocessing.split_spread")
        assert split_spread is not None

    def test_split_spread_pages_importable(self):
        """split_spread_pages 関数が preprocessing.split_spread からインポート可能であることを検証."""
        from src.preprocessing.split_spread import split_spread_pages

        assert callable(split_spread_pages)

    def test_preprocessing_hash_module_exists(self):
        """src.preprocessing.hash モジュールがインポート可能であることを検証."""
        hash_module = importlib.import_module("src.preprocessing.hash")
        assert hash_module is not None


class TestLayoutImports:
    """layout パッケージのエクスポートを検証するテスト."""

    def test_layout_detector_module_exists(self):
        """src.layout.detector モジュールがインポート可能であることを検証."""
        detector = importlib.import_module("src.layout.detector")
        assert detector is not None

    def test_detect_layout_importable(self):
        """detect_layout 関数が layout.detector からインポート可能であることを検証."""
        from src.layout.detector import detect_layout

        assert callable(detect_layout)

    def test_layout_figures_module_exists(self):
        """src.layout.figures モジュールがインポート可能であることを検証."""
        figures = importlib.import_module("src.layout.figures")
        assert figures is not None

    def test_detect_figures_importable(self):
        """detect_figures 関数が layout.figures からインポート可能であることを検証."""
        from src.layout.figures import detect_figures

        assert callable(detect_figures)

    def test_layout_reading_order_module_exists(self):
        """src.layout.reading_order モジュールがインポート可能であることを検証."""
        reading_order = importlib.import_module("src.layout.reading_order")
        assert reading_order is not None

    def test_sort_reading_order_importable(self):
        """sort_reading_order 関数が layout.reading_order からインポート可能であることを検証."""
        from src.layout.reading_order import sort_reading_order

        assert callable(sort_reading_order)


class TestPackageInit:
    """各パッケージの__init__.pyが適切にモジュールをエクスポートしていることを検証."""

    def test_rover_package_has_main_exports(self):
        """rover パッケージが主要な関数をエクスポートしていることを検証."""
        from src import rover

        # 主要関数がパッケージレベルでアクセス可能
        assert hasattr(rover, "rover_merge") or hasattr(rover, "ensemble")

    def test_preprocessing_package_has_main_exports(self):
        """preprocessing パッケージが主要な関数をエクスポートしていることを検証."""
        from src import preprocessing

        # 主要関数がパッケージレベルでアクセス可能
        assert hasattr(preprocessing, "extract_frames") or hasattr(preprocessing, "frames")

    def test_layout_package_has_main_exports(self):
        """layout パッケージが主要な関数をエクスポートしていることを検証."""
        from src import layout

        # 主要関数がパッケージレベルでアクセス可能
        assert hasattr(layout, "detect_layout") or hasattr(layout, "detector")
