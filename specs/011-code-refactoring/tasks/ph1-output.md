# Phase 1 出力: Setup（現状分析）

**日時**: 2026-02-18
**フェーズ**: Phase 1
**ステータス**: 完了

## サマリー

| 項目 | 結果 |
|------|------|
| pyproject.toml | 存在しない（新規作成対象） |
| 既存テスト | 1306 passed, 6 skipped |
| 分割対象ファイル数 | 2件 |

## T001: pyproject.toml 確認

**結果**: ファイルが存在しない → Phase 2で新規作成

## T002: src/ocr_ensemble.py 分析（699行）

### シンボル構造

| 種別 | シンボル |
|------|----------|
| 変数（グローバル） | `_tesseract`, `_easyocr_reader`, `_paddleocr_reader`, `_yomitoku_analyzer` |
| 初期化関数 | `_get_tesseract`, `_get_easyocr_reader`, `_get_paddleocr_reader`, `_get_yomitoku_analyzer` |
| OCR実行関数 | `ocr_tesseract`, `ocr_easyocr`, `ocr_paddleocr`, `ocr_yomitoku_engine`, `ocr_paddleocr_with_boxes` |
| 品質検証関数 | `is_garbage`, `bbox_iou`, `bbox_contains`, `create_text_mask` |
| 類似度計算関数 | `calculate_similarity`, `calculate_similarity_matrix` |
| 投票・マージ関数 | `vote_best_result`, `merge_by_voting` |
| アンサンブル関数 | `ocr_ensemble`, `run_ensemble_ocr`, `main` |
| データクラス | `EngineResult`, `EnsembleResult`, `TextWithBox` |

### 分割計画

| モジュール | 責務 | 移動対象 |
|------------|------|----------|
| `ocr_ensemble/models.py` | データクラス | `EngineResult`, `EnsembleResult`, `TextWithBox` |
| `ocr_ensemble/engines.py` | エンジン初期化・実行 | `_get_*`, `ocr_*` 関数群 |
| `ocr_ensemble/voting.py` | 品質検証・投票・マージ | `is_garbage`, `calculate_*`, `merge_by_voting`, `vote_best_result` |
| `ocr_ensemble/__init__.py` | 公開API | `ocr_ensemble`, `run_ensemble_ocr`, `main` + re-export |

## T003: src/rover/engines.py 分析（613行）

### シンボル構造

| 種別 | シンボル |
|------|----------|
| 変数（グローバル） | `_tesseract`, `_easyocr_reader`, `_paddleocr_reader`, `_yomitoku_analyzer` |
| 初期化関数 | `_get_tesseract`, `_get_easyocr_reader`, `_get_paddleocr_reader`, `_get_yomitoku_analyzer` |
| フィルタリング関数 | `_is_word_inside_figures`, `_is_item_inside_figures`, `_filter_items_by_figures` |
| 補助関数 | `_cluster_words_to_lines`, `_get_paragraph_confidence` |
| エンジン実行関数 | `run_yomitoku_with_boxes`, `run_paddleocr_with_boxes`, `run_easyocr_with_boxes`, `run_tesseract_with_boxes` |
| オーケストレーション | `run_all_engines` |
| データクラス | `TextWithBox` (y_center), `EngineResult` (text) |

### 分割計画

| モジュール | 責務 | 移動対象 |
|------------|------|----------|
| `rover/engines/core.py` | 初期化・データクラス・フィルタリング | `_get_*`, `TextWithBox`, `EngineResult`, `_is_*`, `_filter_*` |
| `rover/engines/runners.py` | エンジン実行・オーケストレーション | `run_*_with_boxes`, `run_all_engines`, `_cluster_*`, `_get_paragraph_*` |
| `rover/engines/__init__.py` | 公開API | re-export |

## T004: テストディレクトリ確認

| ディレクトリ/ファイル | 説明 |
|----------------------|------|
| `tests/` | テストルート |
| `tests/book_converter/` | book_converter用テスト |
| `tests/cli/` | CLI用テスト |
| `tests/test_ocr_ensemble.py` | ocr_ensemble用テスト（分割後も維持） |
| `tests/test_ocr_engines.py` | OCRエンジン用テスト |
| `tests/test_ocr_rover.py` | rover用テスト（分割後も維持） |

## T005: テスト実行結果

```
======================= 1306 passed, 6 skipped in 11.67s =======================
```

**結果**: 全テストパス（ベースライン確立）

## 次フェーズへの引き継ぎ

1. pyproject.tomlは存在しない → Phase 2で新規作成
2. ocr_ensemble.py（699行）→ 4モジュールに分割
3. rover/engines.py（613行）→ 3モジュールに分割
4. 既存テスト1306件がベースライン
5. インポートパス維持のため `__init__.py` で re-export 必須

## 注意事項

- `ocr_ensemble.py` と `rover/engines.py` の両方に同名のグローバル変数（`_tesseract` 等）が存在
- 両ファイルに同名のデータクラス（`TextWithBox`, `EngineResult`）が存在
- これらは別モジュールなので分割後も問題なし
