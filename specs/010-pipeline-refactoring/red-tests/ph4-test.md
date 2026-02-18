# Phase 4 RED Test Output: フォルダ構造整理

**日付**: 2026-02-18
**Feature**: 010-pipeline-refactoring
**Phase**: Phase 4 - User Story 3 (フォルダ構造整理)
**状態**: RED (テストFAIL)

## Summary

| 項目 | 値 |
|------|-----|
| Phase | 4 |
| User Story | US3 - フォルダ構造の整理 |
| FAILテスト数 | 26 |
| PASSテスト数 | 1269 (既存) |
| SKIPテスト数 | 6 (既存) |
| テストファイル | tests/test_package_structure.py |

## テストファイル一覧

| ファイル | テスト数 | 状態 |
|----------|----------|------|
| tests/test_package_structure.py | 26 | FAIL |

## FAILテスト一覧

### TestNewPackageStructure (3件)

| テストメソッド | 期待動作 | 失敗理由 |
|----------------|----------|----------|
| test_rover_package_exists | src.rover パッケージがインポート可能 | ModuleNotFoundError: No module named 'src.rover' |
| test_preprocessing_package_exists | src.preprocessing パッケージがインポート可能 | ModuleNotFoundError: No module named 'src.preprocessing' |
| test_layout_package_exists | src.layout パッケージがインポート可能 | ModuleNotFoundError: No module named 'src.layout' |

### TestRoverImports (7件)

| テストメソッド | 期待動作 | 失敗理由 |
|----------------|----------|----------|
| test_rover_ensemble_module_exists | src.rover.ensemble モジュールがインポート可能 | ModuleNotFoundError: No module named 'src.rover' |
| test_rover_merge_importable | rover_merge が rover.ensemble からインポート可能 | ModuleNotFoundError: No module named 'src.rover' |
| test_rover_engines_module_exists | src.rover.engines モジュールがインポート可能 | ModuleNotFoundError: No module named 'src.rover' |
| test_run_all_engines_importable | run_all_engines が rover.engines からインポート可能 | ModuleNotFoundError: No module named 'src.rover' |
| test_rover_alignment_module_exists | src.rover.alignment モジュールがインポート可能 | ModuleNotFoundError: No module named 'src.rover' |
| test_align_texts_importable | align_texts_character_level が rover.alignment からインポート可能 | ModuleNotFoundError: No module named 'src.rover' |
| test_rover_output_module_exists | src.rover.output モジュールがインポート可能 | ModuleNotFoundError: No module named 'src.rover' |

### TestPreprocessingImports (7件)

| テストメソッド | 期待動作 | 失敗理由 |
|----------------|----------|----------|
| test_preprocessing_frames_module_exists | src.preprocessing.frames モジュールがインポート可能 | ModuleNotFoundError: No module named 'src.preprocessing' |
| test_extract_frames_importable | extract_frames が preprocessing.frames からインポート可能 | ModuleNotFoundError: No module named 'src.preprocessing' |
| test_preprocessing_deduplicate_module_exists | src.preprocessing.deduplicate モジュールがインポート可能 | ModuleNotFoundError: No module named 'src.preprocessing' |
| test_deduplicate_frames_importable | deduplicate_frames が preprocessing.deduplicate からインポート可能 | ModuleNotFoundError: No module named 'src.preprocessing' |
| test_preprocessing_split_spread_module_exists | src.preprocessing.split_spread モジュールがインポート可能 | ModuleNotFoundError: No module named 'src.preprocessing' |
| test_split_spread_pages_importable | split_spread_pages が preprocessing.split_spread からインポート可能 | ModuleNotFoundError: No module named 'src.preprocessing' |
| test_preprocessing_hash_module_exists | src.preprocessing.hash モジュールがインポート可能 | ModuleNotFoundError: No module named 'src.preprocessing' |

### TestLayoutImports (6件)

| テストメソッド | 期待動作 | 失敗理由 |
|----------------|----------|----------|
| test_layout_detector_module_exists | src.layout.detector モジュールがインポート可能 | ModuleNotFoundError: No module named 'src.layout' |
| test_detect_layout_importable | detect_layout が layout.detector からインポート可能 | ModuleNotFoundError: No module named 'src.layout' |
| test_layout_figures_module_exists | src.layout.figures モジュールがインポート可能 | ModuleNotFoundError: No module named 'src.layout' |
| test_detect_figures_importable | detect_figures が layout.figures からインポート可能 | ModuleNotFoundError: No module named 'src.layout' |
| test_layout_reading_order_module_exists | src.layout.reading_order モジュールがインポート可能 | ModuleNotFoundError: No module named 'src.layout' |
| test_sort_reading_order_importable | sort_reading_order が layout.reading_order からインポート可能 | ModuleNotFoundError: No module named 'src.layout' |

### TestPackageInit (3件)

| テストメソッド | 期待動作 | 失敗理由 |
|----------------|----------|----------|
| test_rover_package_has_main_exports | rover パッケージが主要関数をエクスポート | ImportError: cannot import name 'rover' from 'src' |
| test_preprocessing_package_has_main_exports | preprocessing パッケージが主要関数をエクスポート | ImportError: cannot import name 'preprocessing' from 'src' |
| test_layout_package_has_main_exports | layout パッケージが主要関数をエクスポート | ImportError: cannot import name 'layout' from 'src' |

## 実装ヒント

### 1. パッケージ作成順序

以下の順序でパッケージとモジュールを作成:

```bash
# 1. rover パッケージ
mkdir -p src/rover
touch src/rover/__init__.py

# 2. preprocessing パッケージ
mkdir -p src/preprocessing
touch src/preprocessing/__init__.py

# 3. layout パッケージ
mkdir -p src/layout
touch src/layout/__init__.py
```

### 2. モジュール移動マッピング

| 移動元 | 移動先 | 主要関数 |
|--------|--------|----------|
| src/ocr_rover.py | src/rover/ensemble.py | rover_merge, run_rover_batch |
| src/ocr_engines.py | src/rover/engines.py | run_all_engines |
| src/ocr_alignment.py | src/rover/alignment.py | align_texts_character_level |
| src/ocr_output.py | src/rover/output.py | - |
| src/extract_frames.py | src/preprocessing/frames.py | extract_frames |
| src/deduplicate.py | src/preprocessing/deduplicate.py | deduplicate_frames |
| src/split_spread.py | src/preprocessing/split_spread.py | split_spread_pages |
| src/video_hash.py | src/preprocessing/hash.py | - |
| src/ocr_yomitoku.py (一部) | src/layout/detector.py | detect_layout (detect_layout_yomitoku) |
| src/detect_figures.py | src/layout/figures.py | detect_figures |
| src/reading_order.py | src/layout/reading_order.py | sort_reading_order |

### 3. 注意事項

- Phase 3で作成した `src/layout_detector.py` は一時的なラッパー。Phase 4完了後に削除
- 既存モジュール（`src/ocr_rover.py` 等）は Phase 7 まで維持（後方互換性のため）
- CLI層のインポートパスを新パッケージに更新必要

## FAIL出力例

```
FAILED tests/test_package_structure.py::TestNewPackageStructure::test_rover_package_exists - ModuleNotFoundError: No module named 'src.rover'
FAILED tests/test_package_structure.py::TestNewPackageStructure::test_preprocessing_package_exists - ModuleNotFoundError: No module named 'src.preprocessing'
FAILED tests/test_package_structure.py::TestNewPackageStructure::test_layout_package_exists - ModuleNotFoundError: No module named 'src.layout'
FAILED tests/test_package_structure.py::TestRoverImports::test_rover_ensemble_module_exists - ModuleNotFoundError: No module named 'src.rover'
FAILED tests/test_package_structure.py::TestRoverImports::test_rover_merge_importable - ModuleNotFoundError: No module named 'src.rover'
FAILED tests/test_package_structure.py::TestRoverImports::test_rover_engines_module_exists - ModuleNotFoundError: No module named 'src.rover'
FAILED tests/test_package_structure.py::TestRoverImports::test_run_all_engines_importable - ModuleNotFoundError: No module named 'src.rover'
FAILED tests/test_package_structure.py::TestRoverImports::test_rover_alignment_module_exists - ModuleNotFoundError: No module named 'src.rover'
FAILED tests/test_package_structure.py::TestRoverImports::test_align_texts_importable - ModuleNotFoundError: No module named 'src.rover'
FAILED tests/test_package_structure.py::TestRoverImports::test_rover_output_module_exists - ModuleNotFoundError: No module named 'src.rover'
FAILED tests/test_package_structure.py::TestPreprocessingImports::test_preprocessing_frames_module_exists - ModuleNotFoundError: No module named 'src.preprocessing'
FAILED tests/test_package_structure.py::TestPreprocessingImports::test_extract_frames_importable - ModuleNotFoundError: No module named 'src.preprocessing'
FAILED tests/test_package_structure.py::TestPreprocessingImports::test_preprocessing_deduplicate_module_exists - ModuleNotFoundError: No module named 'src.preprocessing'
FAILED tests/test_package_structure.py::TestPreprocessingImports::test_deduplicate_frames_importable - ModuleNotFoundError: No module named 'src.preprocessing'
FAILED tests/test_package_structure.py::TestPreprocessingImports::test_preprocessing_split_spread_module_exists - ModuleNotFoundError: No module named 'src.preprocessing'
FAILED tests/test_package_structure.py::TestPreprocessingImports::test_split_spread_pages_importable - ModuleNotFoundError: No module named 'src.preprocessing'
FAILED tests/test_package_structure.py::TestPreprocessingImports::test_preprocessing_hash_module_exists - ModuleNotFoundError: No module named 'src.preprocessing'
FAILED tests/test_package_structure.py::TestLayoutImports::test_layout_detector_module_exists - ModuleNotFoundError: No module named 'src.layout'
FAILED tests/test_package_structure.py::TestLayoutImports::test_detect_layout_importable - ModuleNotFoundError: No module named 'src.layout'
FAILED tests/test_package_structure.py::TestLayoutImports::test_layout_figures_module_exists - ModuleNotFoundError: No module named 'src.layout'
FAILED tests/test_package_structure.py::TestLayoutImports::test_detect_figures_importable - ModuleNotFoundError: No module named 'src.layout'
FAILED tests/test_package_structure.py::TestLayoutImports::test_layout_reading_order_module_exists - ModuleNotFoundError: No module named 'src.layout'
FAILED tests/test_package_structure.py::TestLayoutImports::test_sort_reading_order_importable - ModuleNotFoundError: No module named 'src.layout'
FAILED tests/test_package_structure.py::TestPackageInit::test_rover_package_has_main_exports - ImportError: cannot import name 'rover' from 'src'
FAILED tests/test_package_structure.py::TestPackageInit::test_preprocessing_package_has_main_exports - ImportError: cannot import name 'preprocessing' from 'src'
FAILED tests/test_package_structure.py::TestPackageInit::test_layout_package_has_main_exports - ImportError: cannot import name 'layout' from 'src'
================== 26 failed, 1269 passed, 6 skipped in 7.39s ==================
```

## 次のステップ

**Phase 4 Implementation (GREEN)**:

1. T054: このREDテストを読み込み
2. T055-T068: 新パッケージとモジュールを作成
3. T069-T071: インポートパスを更新
4. T072: `make test` PASSを確認 (GREEN)
