# Phase 1 Output: Setup

**Date**: 2026-03-13
**Status**: Completed

## Executed Tasks

- [x] T001 既存のレイアウト検出実装を調査: `src/layout/detector.py`
- [x] T002 既存の OCR ユーティリティを調査: `src/layout_ocr_utils.py`
- [x] T003 既存のテストを調査: `tests/test_layout_ocr.py`, `tests/test_reading_order.py`
- [x] T004 既存の設定ファイルを調査: `config.yaml`
- [x] T005 `src/layout/__init__.py` のエクスポート構成を確認
- [x] T006 feat/022 ブランチの既存灰色検出実装を参考として調査
- [x] T007 セットアップ分析を生成

## Existing Code Analysis

### src/layout/detector.py (293行)

**Structure**:
- `get_analyzer(device)`: yomitoku DocumentAnalyzer の遅延初期化
- `paragraphs_to_layout(paragraphs, figures, page_size)`: yomitoku 結果を layout.json 形式に変換
- `visualize_layout(img_path, paragraphs, figures, output_path)`: バウンディングボックスを画像に描画
- `save_yomitoku_results()` / `load_yomitoku_results()`: キャッシュ管理
- `detect_layout_yomitoku(pages_dir, output_dir, ...)`: メイン検出関数
- `detect_layout = detect_layout_yomitoku`: エイリアス

**Required Updates**:
1. `paragraphs_to_layout()`: `cv_img=None` キーワード引数追加。灰色背景検出 + テキスト分析呼び出し。アスペクト比フィルタ。FIGURE テキスト分析。末尾で `merge_code_fragments()` 呼び出し
2. `detect_layout_yomitoku()`: `paragraphs_to_layout()` に `cv_img=cv_img` を渡す。サマリ出力に `[CODE: N]` 追加
3. `visualize_layout()`: `layout_regions` パラメータ追加。CODE リージョンを黄色描画

### src/layout_ocr_utils.py (188行)

**Structure**:
- `is_title(region, yomitoku_result)`: TITLE 判定
- `calc_non_char_ratio(text)`: 非文字率計算
- `is_low_quality(text, min_length, max_non_char_ratio)`: 低品質判定
- `crop_region(img, bbox)`: PIL Image クロップ
- `calculate_coverage(regions, page_size)`: カバー率計算
- `should_fallback(regions, page_size, threshold)`: フォールバック判定
- `format_ocr_result(region_type, text)`: Markdown フォーマット（TITLE→`##`, TEXT→そのまま, FIGURE→空）
- `select_ocr_engine(region_type)`: OCR エンジン選択（FIGURE/ABANDON→skip, その他→yomitoku）

**Required Updates**:
1. `format_ocr_result()`: `"CODE"` → `` ```\n{text}\n``` `` 分岐追加
2. `select_ocr_engine()`: `"CODE"` → `"yomitoku"` 分岐追加（現状 else で yomitoku だが明示的に追加）

### src/layout/__init__.py (11行)

**Structure**:
- `detector`, `figures`, `reading_order` をインポート・エクスポート

**Required Updates**:
1. `code_detector` を import/export に追加

### config.yaml (57行)

**Structure**:
- ビデオ・出力・フレーム抽出・OCR・VLM・レイアウト・スプレッド関連設定

**Required Updates**:
1. `code_detection` セクション追加（Phase 5 で実装）

## Existing Test Analysis

- `tests/test_layout_ocr.py`: OCR エンジン選択、フォーマット、フォールバック、リージョン処理のテスト。CODE 関連テストなし → 追加必要
- `tests/test_reading_order.py`: 読み順ソート、重複除去のテスト。CODE 対応不要
- **Does not exist**: `tests/test_code_detector.py` → 新規作成（灰色検出、テキスト分析、断片結合）

**Required Fixtures**:
- 灰色/白/黒画像の numpy 配列生成ヘルパー（`tests/test_code_detector.py` 内）
- リージョン dict 生成ヘルパー

## feat/022 ブランチ参照結果

### src/layout/code_detector.py (94行) - feat/022

**実装済み機能**:
- `_clip_bbox(cv_img, bbox)`: bbox を画像サイズにクリップ
- `_compute_gray_ratio(cropped, saturation_max, value_min, value_max)`: HSV 灰色画素比率計算
- `detect_gray_background(cv_img, bbox, threshold, saturation_max, value_min, value_max)`: 灰色背景判定

**設計参考ポイント**:
- HSV 色空間: 彩度(S) < 30、明度(V) 50-200 の条件
- bbox クリップ + ゼロサイズチェック
- None/空入力のガード

**021 での追加実装**:
- `detect_code_by_text()`: 記号比率 + キーワード判定
- `calc_symbol_ratio()`: 記号比率計算
- `count_code_keywords()`: キーワードカウント
- `EXTENDED_KEYWORDS`: 25言語対応キーワード定数
- `is_code_fragment()`: 断片判定
- `merge_code_fragments()`: 断片結合

## Technical Decisions

1. **新規ファイル `src/layout/code_detector.py`**: コード検出ロジックを独立モジュールとして配置。detector.py の肥大化を防ぐ
2. **feat/022 のコードは TDD で再実装**: コピーではなく設計参考として使用。テスト先行で品質保証
3. **`paragraphs_to_layout()` への統合**: 既存関数にパラメータ追加。新関数ではなく既存フローに組み込み。後方互換性を `cv_img=None` で維持
4. **FIGURE テキスト取得**: yomitoku の `figure.paragraphs` フィールドから取得。追加 OCR 不要

## Handoff to Next Phase

Phase 2 (US1 灰色背景コード検出) で実装するもの:
- `src/layout/code_detector.py`: `detect_gray_background()` を TDD で再実装（feat/022 参考）
- `src/layout/detector.py`: `paragraphs_to_layout()` に `cv_img` パラメータ追加 + 灰色判定呼び出し + アスペクト比フィルタ
- `src/layout/detector.py`: `detect_layout_yomitoku()` で `cv_img` を渡す
- `src/layout_ocr_utils.py`: `format_ocr_result()` に CODE 追加、`select_ocr_engine()` に CODE 追加
- `src/layout/__init__.py`: `code_detector` エクスポート追加
- `tests/test_code_detector.py`: 新規作成（灰色検出テスト）
- `tests/test_layout_ocr.py`: CODE テスト追加

既存コードで再利用可能:
- `paragraphs_to_layout()` の構造（regions リスト構築パターン）
- `format_ocr_result()` の分岐パターン
- feat/022 の HSV 灰色検出ロジック（設計参考）

注意事項:
- `paragraphs_to_layout()` は `cv_img=None` デフォルトで後方互換維持が必須
- アスペクト比 > 8.0 の帯状リージョンフィルタを忘れずに
- FIGURE の `paragraphs` 属性アクセスは `hasattr` でガード必要
