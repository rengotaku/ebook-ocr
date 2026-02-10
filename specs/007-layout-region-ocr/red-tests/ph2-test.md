# Phase 2 RED テスト結果: US1 - 拡張レイアウト検出

**日付**: 2026-02-11
**Phase**: Phase 2 (User Story 1)
**ステータス**: RED (テスト失敗確認済み)

## サマリ

| 項目 | 値 |
|------|-----|
| Phase | Phase 2 (US1 - 拡張レイアウト検出) |
| FAILテスト数 | 12 |
| PASSテスト数 | 1 |
| テストファイル | tests/test_detect_figures.py |

## FAILテスト一覧

| テストファイル | テストメソッド | 期待動作 | 失敗理由 |
|--------------|--------------|---------|---------|
| test_detect_figures.py | test_label_type_map_has_10_classes | LABEL_TYPE_MAPが10クラス含む | 現在3クラスのみ |
| test_detect_figures.py | test_label_type_map_contains_title | 'title'クラスを含む | 未実装 |
| test_detect_figures.py | test_label_type_map_contains_plain_text | 'plain text'クラスを含む | 未実装 |
| test_detect_figures.py | test_label_type_map_contains_abandon | 'abandon'クラスを含む | 未実装 |
| test_detect_figures.py | test_label_type_map_contains_figure_caption | 'figure_caption'クラスを含む | 未実装 |
| test_detect_figures.py | test_label_type_map_contains_table_caption | 'table_caption'クラスを含む | 未実装 |
| test_detect_figures.py | test_label_type_map_contains_table_footnote | 'table_footnote'クラスを含む | 未実装 |
| test_detect_figures.py | test_label_type_map_contains_formula_caption | 'formula_caption'クラスを含む | 未実装 |
| test_detect_figures.py | test_detect_figures_output_uses_regions_key | 出力が'regions'キーを使用 | 現在'figures'キー使用 |
| test_detect_figures.py | test_detect_figures_output_includes_page_size | 出力に'page_size'フィールドを含む | 未実装 |
| test_detect_figures.py | test_detect_figures_filters_small_regions | 小領域(<1%)を除外 | フィルタリング未実装 |
| test_detect_figures.py | test_detect_figures_min_area_parameter | min_areaパラメータを受け入れる | パラメータ未実装 |

## PASSテスト一覧

| テストファイル | テストメソッド | 動作確認 |
|--------------|--------------|---------|
| test_detect_figures.py | test_label_type_map_existing_classes_preserved | 既存クラス(table, figure, isolated formula)保持 |

## 実装ヒント

### T014: LABEL_TYPE_MAP を10クラスに拡張

```python
# src/detect_figures.py で以下のように変更
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

### T015: layout.json出力を regions 構造に変更

現在の出力形式:
```json
{
  "page_001.png": {
    "figures": [...]
  }
}
```

期待する出力形式:
```json
{
  "page_001.png": {
    "regions": [...],
    "page_size": [1920, 1080]
  }
}
```

変更箇所:
- Line 100: `layout_data[page_name] = {"figures": figures}` を変更
- `img.size` を取得して `page_size` に設定

### T016: 最小面積フィルタリング実装

```python
def detect_figures(
    page_dir: str,
    output_dir: str,
    figures_dir: str | None = None,
    min_confidence: float = 0.3,
    min_area: float = 0.01,  # 追加: ページ面積の1%
) -> dict:
    ...
    page_area = img.size[0] * img.size[1]
    min_area_px = page_area * min_area

    for box in r.boxes:
        bbox = [int(v) for v in box.xyxy[0].tolist()]
        area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
        if area < min_area_px:
            continue  # 小さな領域をスキップ
        ...
```

## FAIL出力例

```
$ make test
...
FAILED tests/test_detect_figures.py::TestLabelTypeMapExtension::test_label_type_map_has_10_classes
  AssertionError: LABEL_TYPE_MAP should contain 10 classes, but has 3 classes: ['table', 'figure', 'isolated formula']

FAILED tests/test_detect_figures.py::TestLayoutJsonRegionsStructure::test_detect_figures_output_uses_regions_key
  AssertionError: Page data should have 'regions' key instead of 'figures'. Got keys: ['figures']

FAILED tests/test_detect_figures.py::TestLayoutJsonPageSize::test_detect_figures_output_includes_page_size
  AssertionError: Page data should have 'page_size' key. Got keys: ['figures']

FAILED tests/test_detect_figures.py::TestMinAreaFiltering::test_detect_figures_filters_small_regions
  AssertionError: Only 1 region (large) should remain after filtering. Got 2 regions.

FAILED tests/test_detect_figures.py::TestMinAreaFiltering::test_detect_figures_min_area_parameter
  AssertionError: detect_figures() should accept 'min_area' parameter. Current parameters: ['page_dir', 'output_dir', 'figures_dir', 'min_confidence']

=================== 12 failed, 1 passed ===================
```

## 次のステップ

1. **T013**: この RED テスト結果を読み取る
2. **T014**: LABEL_TYPE_MAP を10クラスに拡張
3. **T015**: layout.json出力を regions 構造に変更、page_size追加
4. **T016**: min_area パラメータと最小面積フィルタリングを実装
5. **T017**: `make test` で全テストPASSを確認 (GREEN)
