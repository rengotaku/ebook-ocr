# Phase 2 RED Tests: US1 - 拡張レイアウト検出

**Date**: 2026-02-13
**Status**: GREEN (実装済み - テストは全てPASS)

## Summary

| 項目 | 値 |
|------|-----|
| Phase | 2 (US1: 拡張レイアウト検出) |
| テストファイル | tests/test_detect_figures.py |
| 対象タスク | T010, T011, T012, T013 |
| 期待状態 | RED (FAIL) |
| 実際状態 | GREEN (PASS) |
| 理由 | 実装が既に完了している |

## Test Results

| テストクラス | テストメソッド | 状態 | 備考 |
|-------------|---------------|------|------|
| TestLabelTypeMapExtension | test_label_type_map_has_10_classes | PASS | 10クラス検証済み |
| TestLabelTypeMapExtension | test_label_type_map_contains_title | PASS | 'title' -> 'TITLE' |
| TestLabelTypeMapExtension | test_label_type_map_contains_plain_text | PASS | 'plain text' -> 'TEXT' |
| TestLabelTypeMapExtension | test_label_type_map_contains_abandon | PASS | 'abandon' -> 'ABANDON' |
| TestLabelTypeMapExtension | test_label_type_map_contains_figure_caption | PASS | 'figure_caption' -> 'CAPTION' |
| TestLabelTypeMapExtension | test_label_type_map_contains_table_caption | PASS | 'table_caption' -> 'CAPTION' |
| TestLabelTypeMapExtension | test_label_type_map_contains_table_footnote | PASS | 'table_footnote' -> 'FOOTNOTE' |
| TestLabelTypeMapExtension | test_label_type_map_contains_formula_caption | PASS | 'formula_caption' -> 'CAPTION' |
| TestLabelTypeMapExtension | test_label_type_map_existing_classes_preserved | PASS | table, figure, formula保持 |
| TestLayoutJsonRegionsStructure | test_detect_figures_output_uses_regions_key | PASS | 'regions' キー使用 |
| TestLayoutJsonPageSize | test_detect_figures_output_includes_page_size | PASS | page_size含む |
| TestMinAreaFiltering | test_detect_figures_filters_small_regions | PASS | 1%未満除外 |
| TestMinAreaFiltering | test_detect_figures_min_area_parameter | PASS | min_area引数あり |

## Task Status

| タスク | 説明 | 状態 | 備考 |
|--------|------|------|------|
| T010 | 全クラス検出テスト | PASS | LABEL_TYPE_MAP に10クラス含む |
| T011 | regions構造テスト | PASS | 'regions' キー使用 |
| T012 | page_sizeテスト | PASS | page_size [width, height] 含む |
| T013 | ノイズ除外テスト | PASS | min_area (1%) フィルタリング |

## Implementation Status

`src/detect_figures.py` の実装を確認した結果、以下の機能が既に完成しています:

### LABEL_TYPE_MAP (10クラス)

```python
LABEL_TYPE_MAP = {
    "title": "TITLE",
    "plain text": "TEXT",
    "abandon": "ABANDON",
    "figure": "FIGURE",
    "figure_caption": "CAPTION",
    "table": "TABLE",
    "table_caption": "CAPTION",
    "table_footnote": "FOOTNOTE",
    "isolated formula": "FORMULA",
    "formula_caption": "CAPTION",
}
```

### 出力構造 (regions + page_size)

```python
layout_data[page_name] = {
    "regions": regions,
    "page_size": [page_width, page_height],
}
```

### min_area フィルタリング

```python
def detect_figures(
    ...
    min_area: float = 0.01,  # 1% default
) -> dict:
    ...
    min_area_px = page_area * min_area
    ...
    if area < min_area_px:
        continue  # Filter out small regions (noise)
```

## Conclusion

Phase 2 の対象機能は **既に実装済み** です。テストは全て GREEN 状態です。

### 理由

ph1-output.md の分析結果に記載の通り:

> - **Phase 2 (US1)**: detect_figures.py は既に実装済み。テスト確認のみ。

### 推奨アクション

1. **Implementation (GREEN)** フェーズは **スキップ可能**
2. tasks.md の T010-T013 を `[x]` にマーク
3. Phase 2 Verification -> ph2-output.md 生成へ進む

## Related Files

- テストファイル: `/data/projects/video-separater/tests/test_detect_figures.py`
- 実装ファイル: `/data/projects/video-separater/src/detect_figures.py`
- Phase 1 分析: `/data/projects/video-separater/specs/007-layout-region-ocr/tasks/ph1-output.md`
