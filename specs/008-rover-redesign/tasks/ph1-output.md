# Phase 1 Output: Setup

**Date**: 2026-02-14
**Status**: 完了

## 実行タスク

- [x] T001 現在の実装を読む: src/ocr_engines.py
- [x] T002 現在の実装を読む: src/ocr_rover.py
- [x] T003 既存テストを読む: tests/test_ocr_rover.py（存在しない）
- [x] T004 既存テストを読む: tests/conftest.py
- [x] T005 新規モジュールのスケルトン作成: src/ocr_preprocess.py
- [x] T006 新規モジュールのスケルトン作成: src/ocr_alignment.py
- [x] T007 フェーズ出力を生成

## 既存コード分析

### src/ocr_engines.py

**構造**:
- `TextWithBox` データクラス: テキスト + bbox + confidence
- `EngineResult` データクラス: エンジン結果
- 各エンジン関数: `run_yomitoku_with_boxes`, `run_paddleocr_with_boxes`, `run_easyocr_with_boxes`, `run_tesseract_with_boxes`
- `run_all_engines`: 全エンジン実行

**更新が必要な箇所**:
1. `run_yomitoku_with_boxes`: 現在 `confidence = 1.0` 固定 → `words.rec_score` から取得に変更
2. `run_easyocr_with_boxes`: CLAHE前処理オプション追加
3. `run_all_engines`: デフォルトエンジンからtesseract除外

### src/ocr_rover.py

**構造**:
- `ENGINE_WEIGHTS`: エンジン重み (yomitoku=1.5, paddleocr=1.2, easyocr=1.0, tesseract=0.8)
- `OCRLine`, `AlignedLine`, `ROVERResult` データクラス
- `cluster_lines_by_y`: y座標で行クラスタリング
- `align_lines_by_y`: 複数エンジンの行アライメント
- `calculate_text_similarity`: テキスト類似度計算
- `vote_line_text`: 行レベル投票（**更新必要**: 文字レベルに変更）
- `rover_merge`: ROVER統合処理
- `run_rover_ocr`, `run_rover_batch`: 実行関数

**更新が必要な箇所**:
1. `vote_line_text`: 行レベル→文字レベル投票に変更
2. ゴミフィルタ関数追加: `is_garbage`, `normalize_confidence`
3. `rover_merge`: ゴミフィルタ追加、文字レベル投票統合
4. tesseract除外

### tests/conftest.py

**既存フィクスチャ**:
- `sample_image`: 一時ディレクトリに100x80の画像を作成
- `sample_pil_image`: PIL Imageを直接返す
- `sample_layout`: レイアウト辞書（figure/tableの位置情報）

**追加が必要なフィクスチャ**:
- `sample_text_with_boxes`: TextWithBoxのリスト
- `sample_engine_results`: 複数エンジンの結果

### 既存テスト

- `tests/test_ocr_ensemble.py`: アンサンブル関連
- `tests/test_ocr_integrated.py`: 統合テスト
- `tests/test_ocr_rover.py`: **存在しない** → 新規作成

## 新規作成ファイル

### src/ocr_preprocess.py (スケルトン)

- `apply_clahe`: CLAHE前処理関数 (Phase 4で実装)

### src/ocr_alignment.py (スケルトン)

- `AlignedPosition`: 文字位置データクラス
- `align_texts_character_level`: 文字レベルアライメント
- `weighted_vote_character`: 単一位置の重み付き投票
- `vote_aligned_text`: 全位置の投票統合

## 技術的決定事項

1. **モジュール分離**: 文字レベルアライメントは `ocr_alignment.py` に分離（単一責任）
2. **後方互換性**: 既存の `cluster_lines_by_y`, `align_lines_by_y` は維持
3. **信頼度正規化**: 投票前に各エンジンの信頼度を[0,1]に正規化

## 次フェーズへの引き継ぎ

Phase 2 (US1+US2) で実装するもの:
- `is_garbage`: ゴミ判定関数
- `normalize_confidence`: 信頼度正規化関数
- `cluster_lines_by_y`: 既存コードを流用可能
- `align_lines_by_y`: 既存コードを流用可能
- 基本的な `rover_merge`: ゴミフィルタ + 行レベル投票（Phase 3で文字レベルに拡張）
