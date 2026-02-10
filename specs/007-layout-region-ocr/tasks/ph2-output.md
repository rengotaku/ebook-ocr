# Phase 2 Output: US1 - 拡張レイアウト検出

**日付**: 2026-02-11
**Phase**: Phase 2 (US1 - 拡張レイアウト検出)
**ステータス**: GREEN - 全テスト成功

## 作業サマリ

Phase 2では、User Story 1「拡張レイアウト検出」を実装しました。DocLayout-YOLOの全10クラスを検出し、layout.jsonの構造を`figures`から`regions`に拡張し、ページサイズ情報と最小面積フィルタリングを追加しました。

### 完了タスク

| タスクID | 説明 | ステータス |
|---------|------|----------|
| T013 | RED テスト結果読み取り | ✅ 完了 |
| T014 | LABEL_TYPE_MAP を10クラスに拡張 | ✅ 完了 |
| T015 | layout.json出力を regions 構造に変更 | ✅ 完了 |
| T016 | 最小面積フィルタリング実装 | ✅ 完了 |
| T017 | `make test` PASS 確認 (GREEN) | ✅ 完了 |
| T018 | リグレッションテスト確認 | ✅ 完了 |
| T019 | Phase 2 出力生成 | ✅ 完了 |

**進捗**: 7/7 タスク完了 (100%)

---

## 変更ファイル一覧

### 実装変更

| ファイル | 変更種別 | 説明 |
|---------|---------|------|
| src/detect_figures.py | 修正 | LABEL_TYPE_MAP 10クラス拡張、regions構造、min_area実装 |

### テスト追加

| ファイル | 変更種別 | 説明 |
|---------|---------|------|
| tests/test_detect_figures.py | 新規 | Phase 2 RED テスト（13テストケース） |

---

## 実装の詳細

### 1. LABEL_TYPE_MAP 拡張 (T014)

**変更前** (3クラス):
```python
LABEL_TYPE_MAP = {
    "table": "TABLE",
    "figure": "FIGURE",
    "isolated formula": "FORMULA",
}
```

**変更後** (10クラス):
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

### 2. layout.json 構造変更 (T015)

**変更前**:
```json
{
  "page_001.png": {
    "figures": [...]
  }
}
```

**変更後**:
```json
{
  "page_001.png": {
    "regions": [...],
    "page_size": [1920, 1080]
  }
}
```

**実装箇所**:
- Line 69-71: `figures` → `regions` 変数名変更
- Line 76-77: ページサイズ取得 (`img.size`)
- Line 101-104: 出力構造変更（`regions`キー + `page_size`キー）

### 3. 最小面積フィルタリング (T016)

**関数シグネチャ変更**:
```python
def detect_figures(
    page_dir: str,
    output_dir: str,
    figures_dir: str | None = None,
    min_confidence: float = 0.3,
    min_area: float = 0.01,  # 新規: ページ面積の1%
) -> dict:
```

**フィルタリングロジック** (Line 78-81):
```python
page_area = page_width * page_height
min_area_px = page_area * min_area

# 検出ループ内
area = (bbox[2] - bbox[0]) * (bbox[3] - bbox[1])
if area < min_area_px:
    continue  # 小さな領域をスキップ
```

---

## テスト結果

### Phase 2 テスト (tests/test_detect_figures.py)

```
13 passed, 4 warnings
```

#### 通過したテスト一覧

| テストクラス | テストメソッド | 検証内容 |
|------------|--------------|---------|
| TestLabelTypeMapExtension | test_label_type_map_has_10_classes | 10クラス含むことを確認 |
| TestLabelTypeMapExtension | test_label_type_map_contains_title | 'title'クラス存在確認 |
| TestLabelTypeMapExtension | test_label_type_map_contains_plain_text | 'plain text'クラス存在確認 |
| TestLabelTypeMapExtension | test_label_type_map_contains_abandon | 'abandon'クラス存在確認 |
| TestLabelTypeMapExtension | test_label_type_map_contains_figure_caption | 'figure_caption'クラス存在確認 |
| TestLabelTypeMapExtension | test_label_type_map_contains_table_caption | 'table_caption'クラス存在確認 |
| TestLabelTypeMapExtension | test_label_type_map_contains_table_footnote | 'table_footnote'クラス存在確認 |
| TestLabelTypeMapExtension | test_label_type_map_contains_formula_caption | 'formula_caption'クラス存在確認 |
| TestLabelTypeMapExtension | test_label_type_map_existing_classes_preserved | 既存クラス保持確認 |
| TestLayoutJsonRegionsStructure | test_detect_figures_output_uses_regions_key | 'regions'キー使用確認 |
| TestLayoutJsonPageSize | test_detect_figures_output_includes_page_size | 'page_size'フィールド存在確認 |
| TestMinAreaFiltering | test_detect_figures_filters_small_regions | 小領域除外確認 |
| TestMinAreaFiltering | test_detect_figures_min_area_parameter | min_areaパラメータ存在確認 |

### リグレッションテスト

関連テストファイル全て通過:
- `tests/test_detect_figures.py`: 13/13 PASS
- `tests/test_ocr_deepseek.py`: 8/8 PASS
- `tests/test_utils.py`: 12/12 PASS

**合計**: 33/33 テスト成功

---

## 次フェーズへの引き継ぎ

### 実装完了項目

1. ✅ **LABEL_TYPE_MAP 拡張**: 3クラス → 10クラス
2. ✅ **regions 構造**: `figures` → `regions` + `page_size`
3. ✅ **最小面積フィルタリング**: `min_area` パラメータ (デフォルト: 0.01 = 1%)

### 後続フェーズでの利用可能な機能

- `detect_figures()`関数は10種類の領域（TITLE, TEXT, ABANDON, FIGURE, CAPTION, TABLE, FOOTNOTE, FORMULA）を検出可能
- `layout.json`は新しい`regions`構造で出力され、各ページの`page_size`情報を含む
- 小さなノイズ領域（デフォルトでページ面積の1%未満）は自動的に除外される

### Phase 3 で実装予定の機能

**User Story 3: 読み順の再構築**
- `regions`配列をbbox座標に基づいて読み順にソート
- 2カラムレイアウトの検出とソート
- 重複領域の検出と除去

**依存関係**:
- Phase 3は、Phase 2で実装した`regions`構造を入力として使用

---

## 発見した問題点

### なし

すべてのテストが成功し、既存機能への影響もありません。

---

## 備考

### DocLayout-YOLO クラスマッピング

| DocLayout-YOLO ラベル | 内部タイプ | 用途 |
|---------------------|----------|------|
| title | TITLE | タイトル・見出し |
| plain text | TEXT | 本文テキスト |
| abandon | ABANDON | 除外領域 |
| figure | FIGURE | 図・画像 |
| figure_caption | CAPTION | 図のキャプション |
| table | TABLE | 表 |
| table_caption | CAPTION | 表のキャプション |
| table_footnote | FOOTNOTE | 表の注釈 |
| isolated formula | FORMULA | 数式 |
| formula_caption | CAPTION | 数式のキャプション |

### フィルタリングパラメータ

- **min_confidence**: 0.3 (デフォルト) - YOLO検出信頼度しきい値
- **min_area**: 0.01 (デフォルト) - ページ面積に対する最小領域面積比率

---

**ステータス**: ✅ Phase 2 完了 - 次は Phase 3 (US3 - 読み順の再構築) へ
