# Phase 4 Output: 中規模ファイル分割

**Date**: 2026-02-19
**Branch**: `012-fix-pylint-errors`
**Status**: COMPLETE

## 実行サマリ

| Task | Description | Status |
|------|-------------|--------|
| T033 | ph1-output.md読込 | ✅ |
| T034 | ph3-output.md読込 | ✅ |
| T035 | layout_ocr_utils.py 作成 | ✅ |
| T036 | layout_ocr.py 更新 | ✅ |
| T037 | ocr_integrated_utils.py 作成 | ✅ |
| T038 | ocr_integrated.py 更新 | ✅ |
| T039 | rover/line_processing.py 作成 | ✅ |
| T040 | rover/ensemble.py 更新 | ✅ |
| T041 | yomitoku_io.py 作成 | ✅ |
| T042 | yomitoku_layout.py 作成 | ✅ |
| T043 | ocr_yomitoku.py 更新 | ✅ |
| T044 | book_converter/transformer_utils.py 作成 | ✅ |
| T045 | book_converter/transformer.py 更新 | ✅ |
| T046 | pytest確認 | ✅ (1306 passed, 6 skipped) |
| T047 | 行数確認 | ✅ (全ファイル500行以下) |
| T048 | ph4-output.md生成 | ✅ |

## 成果物

### 作成されたファイル

```
src/
├── layout_ocr_utils.py          # 211行: layout_ocr.py からヘルパー抽出
├── ocr_integrated_utils.py      # 325行: ocr_integrated.py からヘルパー抽出
├── yomitoku_io.py               # 64行: ocr_yomitoku.py からI/O関数抽出
├── yomitoku_layout.py           # 208行: ocr_yomitoku.py からレイアウト関数抽出
├── rover/
│   └── line_processing.py       # 318行: rover/ensemble.py からライン処理抽出
└── book_converter/
    └── transformer_utils.py     # 113行: transformer.py からユーティリティ抽出
```

**Total**: 1,239行の新規ヘルパーコード

### 更新されたファイル

| File | Before | After | 削減率 |
|------|--------|-------|--------|
| `src/layout_ocr.py` | 595行 | 423行 | -29% |
| `src/ocr_integrated.py` | 577行 | 294行 | -49% |
| `src/rover/ensemble.py` | 593行 | 332行 | -44% |
| `src/ocr_yomitoku.py` | 535行 | 282行 | -47% |
| `src/book_converter/transformer.py` | 566行 | 458行 | -19% |

**Total**: 2,866行 → 1,789行 (削減: 1,077行、-38%)

### テスト更新

以下のテストファイルでimport文を更新:
- `tests/book_converter/test_transformer.py`: transformer_utils からimport
- `tests/test_layout_ocr.py`: layout_ocr_utils からimport
- `tests/test_ocr_rover.py`: rover/line_processing からimport
- `src/book_converter/page_grouper/hierarchy.py`: transformer_utils からimport

## Pylint検証結果

### Before (Phase 4開始前)

```
too-many-lines 違反: 5ファイル
- layout_ocr.py: 595行
- ocr_integrated.py: 577行
- rover/ensemble.py: 593行
- ocr_yomitoku.py: 535行
- transformer.py: 566行
```

### After (Phase 4完了後)

```
too-many-lines 違反: 0ファイル

全ファイルが500行以下:
- layout_ocr.py: 423行 ✅
- ocr_integrated.py: 294行 ✅
- rover/ensemble.py: 332行 ✅
- ocr_yomitoku.py: 282行 ✅
- transformer.py: 458行 ✅
```

**改善率**: 5ファイル → 0ファイル (100%解消)

## Pytest検証結果

```
1306 passed, 6 skipped in 21.43s
```

全テストパス。後方互換性完全維持。

## モジュール設計

### layout_ocr_utils.py

抽出された関数:
- `is_title()`: タイトル判定
- `calc_non_char_ratio()`: 非文字率計算
- `is_low_quality()`: 低品質判定
- `crop_region()`: 領域クロップ
- `calculate_coverage()`: カバー率計算
- `should_fallback()`: フォールバック判定
- `format_ocr_result()`: フォーマット適用
- `select_ocr_engine()`: エンジン選択

### ocr_integrated_utils.py

抽出された関数:
- `filter_overlapping_regions()`: 重複領域フィルタ
- `group_text_by_regions()`: テキストグループ化
- `structure_text_by_paragraphs()`: 段落構造化
- `extract_titles_from_regions()`: タイトル抽出
- `structure_text_with_titles()`: タイトル構造化
- `select_best_engine()`: 最適エンジン選択

定数:
- `ENGINE_PRIORITY`: エンジン優先度マップ

### rover/line_processing.py

抽出されたクラス:
- `OCRLine`: OCR行データクラス
- `AlignedLine`: 整列行データクラス

抽出された関数:
- `is_garbage()`: ガベージ判定
- `normalize_confidence()`: 信頼度正規化
- `split_multiline_items()`: 複数行分割
- `cluster_lines_by_y()`: Y座標クラスタリング
- `align_lines_by_y()`: Y座標整列

### yomitoku_io.py

抽出された関数:
- `save_yomitoku_results()`: 結果保存
- `load_yomitoku_results()`: 結果読込
- `reset_analyzer()`: アナライザーリセット

### yomitoku_layout.py

抽出された関数:
- `paragraphs_to_layout()`: レイアウト変換
- `visualize_layout()`: レイアウト可視化
- `detect_layout_yomitoku()`: レイアウト検出

### book_converter/transformer_utils.py

抽出された関数:
- `normalize_heading_for_comparison()`: 見出し正規化
- `is_duplicate_heading()`: 重複判定
- `apply_emphasis()`: 強調適用

## 後方互換性

### 再エクスポート

`ocr_integrated.py` で ENGINE_PRIORITY を再エクスポート:
```python
from src.ocr_integrated_utils import ENGINE_PRIORITY
__all__ = ["ENGINE_PRIORITY", ...]
```

既存コードは変更不要:
```python
# Before & After (同じ!)
from src.ocr_integrated import ENGINE_PRIORITY
```

## 次フェーズへの引き継ぎ

### Phase 5での対応が必要な項目

Phase 4で残存する複雑度違反（関数レベル）:

1. **too-many-locals 違反**: 以下の関数が複雑すぎる
   - `parser/page.py::parse_pages_with_errors` (20 locals)
   - `parser/page.py::_parse_single_page_content` (29 locals)
   - `ocr_integrated.py::run_integrated_ocr` (26 locals)
   - `page_grouper/assignment.py::group_pages_by_toc` (31 locals)
   - `layout_ocr.py::run_layout_ocr` (28 locals)
   - その他 (rover, yomitoku, detector 等)

2. **too-many-branches 違反**:
   - `parser/page.py::parse_pages_with_errors` (22 branches)
   - `parser/page.py::_parse_single_page_content` (14 branches)
   - `page_grouper/hierarchy.py::_add_sections_to_chapter` (17 branches)

3. **too-many-statements 違反**:
   - `parser/page.py::parse_pages_with_errors` (70 statements)
   - `parser/page.py::_parse_single_page_content` (57 statements)
   - `ocr_integrated.py::run_integrated_ocr` (65 statements)
   - `page_grouper/assignment.py::group_pages_by_toc` (55 statements)
   - `layout_ocr.py::run_layout_ocr` (60 statements)

### 推奨される改善策

**関数分解戦略**:
1. **データクラス化**: 関連する変数をdataclassにまとめる
2. **ヘルパー関数抽出**: 独立した処理ブロックを分離
3. **早期リターン**: 深いネストを解消
4. **辞書マッピング**: 長いif-elif連鎖を変換

## 問題点と解決策

### 問題1: テストインポート更新が必要

**原因**:
- ヘルパー関数を新モジュールに移動
- テストが元のモジュールから直接インポート

**解決策**:
- テストのimport文を更新
- sed コマンドで一括置換

### 問題2: 循環インポートリスク

**現状**:
- hierarchy.py が transformer_utils から is_duplicate_heading をimport
- transformer.py は hierarchy を直接importしていない

**結論**: 循環インポートなし。設計上問題なし。

## 備考

- WF-001に従い、作業中は `git commit --no-verify` 使用可
- ruff check --fix && ruff format 実行済み
- 循環インポート問題なし
- 全1306テストパス（100%）
- too-many-lines違反: 5ファイル → 0ファイル (100%解消)
