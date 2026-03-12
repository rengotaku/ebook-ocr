# Phase 2 Output: US1 灰色背景コードブロックの自動検出

**Date**: 2026-03-13
**Status**: Completed
**User Story**: US1 - 灰色背景コードブロックの自動検出

## 実行タスク

- [x] T019 RED テストを読む: `specs/021-code-block-gray-detection/red-tests/ph2-test.md`
- [x] T020 `detect_gray_background()` を実装: HSV 色空間で灰色画素比率を計算 in `src/layout/code_detector.py`（新規ファイル）
- [x] T021 `format_ocr_result()` に CODE 分岐を追加: `` ```\n{text}\n``` `` in `src/layout_ocr_utils.py`
- [x] T022 `select_ocr_engine()` に CODE 分岐を追加: → "yomitoku" in `src/layout_ocr_utils.py`
- [x] T023 `paragraphs_to_layout()` に `cv_img` パラメータ追加 + 灰色判定呼び出し + アスペクト比フィルタ in `src/layout/detector.py`
- [x] T024 `detect_layout_yomitoku()` で `cv_img` を `paragraphs_to_layout()` に渡す in `src/layout/detector.py`
- [x] T025 `src/layout/__init__.py` に `code_detector` を export 追加
- [x] T026 `make test` で PASS を確認 (GREEN)
- [x] T027 `make test` で全テスト通過（リグレッションなし）を確認
- [x] T028 `make lint` で lint エラーなしを確認
- [x] T029 フェーズ出力を生成: `specs/021-code-block-gray-detection/tasks/ph2-output.md`

## 変更ファイル

| ファイル | 変更種別 | 概要 |
|---------|---------|------|
| `src/layout/code_detector.py` | 新規 | HSV 色空間を使った灰色背景検出: `detect_gray_background()`, `_clip_bbox()`, `_compute_gray_ratio()` |
| `src/layout/detector.py` | 変更 | `paragraphs_to_layout()` に `cv_img=None` パラメータ追加 + 灰色背景判定 + アスペクト比フィルタ。`detect_layout_yomitoku()` で `cv_img` を渡すように変更 |
| `src/layout_ocr_utils.py` | 変更 | `format_ocr_result()` に CODE 分岐追加（コードフェンス出力）。`select_ocr_engine()` に明示的な CODE 分岐追加（yomitoku 返却） |
| `src/layout/__init__.py` | 変更 | `code_detector` モジュールを import/export に追加 |
| `tests/test_code_detector.py` | 変更 | lint 修正: 未使用 `pytest` import 削除、import ソート修正（RED テスト作成時に混入した style 問題） |

## テスト結果

```
========= 1594 passed, 2 skipped, 131 deselected, 6 warnings in 27.77s =========
```

- RED テスト 31 件（test_code_detector.py 25件 + test_layout_ocr.py 6件）がすべて GREEN に転換
- リグレッションなし（既存テスト継続通過）
- lint: `make lint` パス（ruff check + ruff format + pylint --exit-zero）

**Coverage**: 計測対象外（make test のみ実行、80% 目標は別途確認）

## 実装の詳細

### `detect_gray_background()` アルゴリズム

1. 入力ガード: `cv_img=None`、空 bbox、ゼロサイズ bbox、負座標 bbox → False 返却
2. bbox を画像境界にクリップ（`_clip_bbox()`）
3. クリップ後のゼロサイズチェック
4. クロップ領域を BGR → HSV 変換
5. 灰色画素マスク: `saturation < 30 AND value >= 50 AND value <= 200`
6. 灰色画素比率を計算 → `threshold`（デフォルト 0.7）以上なら True

### アスペクト比フィルタ（`paragraphs_to_layout()` 内）

- `width / height > 8.0` の帯状リージョンはスキップ（ヘッダー行の誤検出防止）
- フィルタは `paragraphs_to_layout()` に実装（`detect_gray_background()` ではなく）

### 後方互換性

- `paragraphs_to_layout(paragraphs, figures, page_size)` の3引数シグネチャは引き続き動作
- `cv_img=None`（デフォルト）の場合、灰色検出は完全スキップ

## 発見した課題

1. **test_code_detector.py の lint エラー**: RED テスト作成時に未使用 `pytest` import とインポートソート問題が混入していた。テスト論理に影響しない style 修正として対応（`pytest` import 削除 + ruff 自動整形）

## 次フェーズへの引き継ぎ

Phase 3（US2 + US3 テキスト分析によるコード検出）で実装するもの:

- **確立したインターフェース**:
  - `src/layout/code_detector.py`: 灰色検出モジュールが存在。US2/US3 の追加関数をここに実装
  - `paragraphs_to_layout()`: `cv_img` パラメータ追加済み。テキスト分析呼び出しもここに追加
  - CODE リージョンの `type="CODE"`, `label="code"` フォーマット確定

- **Phase 3 で追加する関数**:
  - `calc_symbol_ratio(text)`: 記号文字比率計算
  - `count_code_keywords(text)`: 拡張キーワードカウント
  - `detect_code_by_text(text, ...)`: OR 条件判定
  - `EXTENDED_KEYWORDS`: 25言語対応キーワード定数

- **注意事項**:
  - TITLE（section_headings）はテキスト分析もスキップ（灰色検出と同様）
  - FIGURE の `paragraphs` 属性アクセスは `hasattr` でガード必要
  - テキスト分析は灰色検出と組み合わせる形で `paragraphs_to_layout()` に統合
