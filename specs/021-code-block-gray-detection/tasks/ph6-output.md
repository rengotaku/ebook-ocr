# Phase 6 Output: Polish & Cross-Cutting Concerns

**Date**: 2026-03-13
**Status**: Completed
**User Story**: N/A - Polish フェーズ（コード品質・ドキュメント整備）

## 実行タスク

- [x] T087 セットアップ分析を読む: `specs/021-code-block-gray-detection/tasks/ph1-output.md`
- [x] T088 前フェーズの出力を読む: `specs/021-code-block-gray-detection/tasks/ph5-output.md`
- [x] T089 `src/layout/code_detector.py` のファイルサイズ確認（480行、800行以下）、分割不要
- [x] T090 不要な import やデッドコードを削除
- [x] T091 quickstart.md の手順確認・修正（`make ocr` → `make run-ocr` の誤記訂正）
- [x] T092 `make test` で全テスト通過を確認
- [x] T093 `make lint` で lint エラーなしを確認
- [x] T094 フェーズ出力を生成: `specs/021-code-block-gray-detection/tasks/ph6-output.md`

## 変更ファイル

| ファイル | 変更種別 | 概要 |
|---------|---------|------|
| `src/layout/code_detector.py` | 変更 | `_OCR_MISREADS` をモジュールレベル定数に移動（`is_code_fragment()` 内の関数ローカル定義を解消） |
| `src/layout_ocr_utils.py` | 変更 | `select_ocr_engine()` の冗長な `elif region_type == "CODE": return "yomitoku"` を削除（直後の `else: return "yomitoku"` と同値だった） |
| `specs/021-code-block-gray-detection/quickstart.md` | 変更 | `make ocr` → `make run-ocr` に誤記訂正（実際の Makefile ターゲット名と一致させた） |

## テスト結果

```
========= 1698 passed, 2 skipped, 131 deselected, 6 warnings in 33.43s =========
```

- 全 1698 テスト PASS
- Phase 2〜5 の全テスト含むリグレッションなし

**Coverage**: 計測対象外（make test のみ実行）

## ファイルサイズ確認結果

| ファイル | 行数 | 判定 |
|---------|------|------|
| `src/layout/code_detector.py` | 480行 | 800行以下 → 分割不要 |
| `src/layout/detector.py` | 404行 | 800行以下 → 分割不要 |
| `src/layout_ocr_utils.py` | 191行 | 800行以下 → 分割不要 |

## quickstart.md 確認結果

### ファイル・関数の存在確認

| quickstart.md 記載 | 実際の場所 | 状態 |
|-------------------|-----------|------|
| `src/layout/code_detector.py` | `src/layout/code_detector.py` | 存在 |
| `src/layout/detector.py` | `src/layout/detector.py` | 存在 |
| `src/layout_ocr_utils.py` | `src/layout_ocr_utils.py` | 存在 |
| `config.yaml` の `code_detection` セクション | `config.yaml` | 存在 |
| `tests/test_code_detector.py` | `tests/test_code_detector.py` | 存在 |
| `make detect-layout HASHDIR=...` | Makefile `detect-layout` ターゲット | 存在 |
| `make run-ocr HASHDIR=...` (修正済み) | Makefile `run-ocr` ターゲット | 存在 |
| `make test` | Makefile `test` ターゲット | 存在 |
| `make lint` | Makefile `lint` ターゲット | 存在 |

### 修正内容

- **誤記**: `make ocr HASHDIR=output/<hash>` → **正**: `make run-ocr HASHDIR=output/<hash>`
  - Makefile に `ocr` ターゲットは存在せず、実際のターゲット名は `run-ocr`

## 発見した課題

1. **`_OCR_MISREADS` の関数ローカル定義**: `is_code_fragment()` 内で `frozenset` が呼び出しごとに再生成されていた → モジュールレベル定数 `_OCR_MISREADS` に移動して解消
2. **`select_ocr_engine()` の冗長な分岐**: `elif region_type == "CODE": return "yomitoku"` と `else: return "yomitoku"` が同値だった → `elif` を削除してシンプルな `if/return` パターンに整理
3. **quickstart.md の誤記**: `make ocr` は存在しないターゲット → `make run-ocr` に訂正

## 次フェーズへの引き継ぎ

Phase 6 は最終フェーズ（Polish）。すべてのユーザーストーリー（US1〜US5）の実装が完了した。

### 確立したインターフェース（全フェーズ通じた最終状態）

- `src/layout/code_detector.py`:
  - `detect_gray_background(cv_img, bbox, ...)` → 灰色背景判定
  - `detect_code_by_text(text, ...)` → テキスト分析によるコード判定
  - `calc_symbol_ratio(text)` → 記号比率計算
  - `count_code_keywords(text)` → キーワードカウント
  - `is_code_fragment(text)` → 断片判定
  - `merge_code_fragments(regions, gap_threshold)` → 断片結合
  - `load_code_detection_config(config_path)` → 設定読み込み
- `src/layout/detector.py`:
  - `paragraphs_to_layout(paragraphs, figures, page_size, cv_img=None)` → CODE 検出統合済み
  - `visualize_layout(img_path, paragraphs, figures, output_path, layout_regions=None)` → CODE 黄色描画対応
- `src/layout_ocr_utils.py`:
  - `format_ocr_result("CODE", text)` → コードフェンス出力
  - `select_ocr_engine("CODE")` → "yomitoku" 返却
- `config.yaml` の `code_detection` セクション: 全8閾値が外部設定化

### 注意事項

- `load_code_detection_config()` は Phase 5 で追加されたが、既存の各検出関数（`detect_gray_background()` 等）の呼び出し側への統合は実装されていない。実際の動作では各関数のデフォルト値が使用される。config.yaml の閾値変更を各検出関数に反映させるには、呼び出し側での明示的な統合が必要。
