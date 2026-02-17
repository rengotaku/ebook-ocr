# Phase 5 REDテスト出力: User Story 4 - list/figure要素の出力

**Date**: 2026-02-16
**Branch**: 009-converter-redesign
**Status**: RED (FAIL確認済み)

## サマリ

| 項目 | 値 |
|------|-----|
| フェーズ | Phase 5 (RED) |
| 対象 | User Story 4 - list/figure要素の出力 |
| FAILテスト数 | 56 |
| テストファイル数 | 3 |

## FAILテスト一覧

### T057: List.list_type 属性テスト (8 FAIL)

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|---------|
| test_models.py | TestListTypeAttribute::test_list_has_list_type_field | List に list_type フィールドが存在する |
| test_models.py | TestListTypeAttribute::test_list_type_unordered | list_type="unordered" で作成可能 |
| test_models.py | TestListTypeAttribute::test_list_type_ordered | list_type="ordered" で作成可能 |
| test_models.py | TestListTypeAttribute::test_list_type_default_value | デフォルト値は "unordered" |
| test_models.py | TestListTypeAttribute::test_list_type_field_type_annotation | 型アノテーションが str |
| test_models.py | TestListTypeAttribute::test_list_is_immutable | frozen dataclass |
| test_models.py | TestListTypeAttribute::test_list_type_with_unicode_items | Unicode項目対応 |
| test_models.py | TestListTypeAttribute::test_list_type_empty_items | 空リスト対応 |

### T058: リスト変換テスト (10 FAIL)

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|---------|
| test_transformer.py | TestTransformListType::test_transform_list_exists | transform_list 関数が存在 |
| test_transformer.py | TestTransformListType::test_transform_list_unordered | type="unordered" 属性出力 |
| test_transformer.py | TestTransformListType::test_transform_list_ordered | type="ordered" 属性出力 |
| test_transformer.py | TestTransformListType::test_transform_list_has_item_children | item 子要素生成 |
| test_transformer.py | TestTransformListType::test_transform_list_xml_format | XML形式検証 |
| test_transformer.py | TestTransformListType::test_transform_list_ordered_xml_format | ordered XML形式 |
| test_transformer.py | TestTransformListType::test_transform_list_empty_items | 空リスト変換 |
| test_transformer.py | TestTransformListType::test_transform_list_unicode_items | Unicode項目変換 |
| test_transformer.py | TestTransformListType::test_transform_list_single_item | 単一項目変換 |
| test_transformer.py | TestTransformListType::test_transform_list_returns_element | Element型返却 |

### T059: Figure.path, marker 属性テスト (10 FAIL)

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|---------|
| test_models.py | TestFigurePathMarker::test_figure_has_path_field | Figure に path フィールドが存在 |
| test_models.py | TestFigurePathMarker::test_figure_has_marker_field | Figure に marker フィールドが存在 |
| test_models.py | TestFigurePathMarker::test_figure_path_required | path は必須フィールド |
| test_models.py | TestFigurePathMarker::test_figure_path_and_marker | path, marker で作成可能 |
| test_models.py | TestFigurePathMarker::test_figure_marker_optional | marker はオプション |
| test_models.py | TestFigurePathMarker::test_figure_read_aloud_default_false | read_aloud デフォルト false |
| test_models.py | TestFigurePathMarker::test_figure_is_immutable | frozen dataclass |
| test_models.py | TestFigurePathMarker::test_figure_marker_with_various_formats | 様々なマーカー形式 |
| test_models.py | TestFigurePathMarker::test_figure_path_various_extensions | 様々な拡張子 |
| test_models.py | TestFigurePathMarker::test_figure_unicode_marker | Unicodeマーカー |

### T060: 図プレースホルダー検出テスト (18 FAIL)

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|---------|
| test_parser.py | TestParseFigurePlaceholder::test_parse_figure_placeholder_exists | 関数存在確認 |
| test_parser.py | TestParseFigurePlaceholder::test_detect_simple_figure | [図] 検出 |
| test_parser.py | TestParseFigurePlaceholder::test_detect_figure_with_number | [図1] 検出 |
| test_parser.py | TestParseFigurePlaceholder::test_detect_figure_with_space_number | [図 1] 検出 |
| test_parser.py | TestParseFigurePlaceholder::test_detect_figure_with_hyphen_number | [図1-1] 検出 |
| test_parser.py | TestParseFigurePlaceholder::test_detect_photo | [写真] 検出 |
| test_parser.py | TestParseFigurePlaceholder::test_detect_photo_with_number | [写真1] 検出 |
| test_parser.py | TestParseFigurePlaceholder::test_detect_table | [表] 検出 |
| test_parser.py | TestParseFigurePlaceholder::test_detect_table_with_number | [表1] 検出 |
| test_parser.py | TestParseFigurePlaceholder::test_detect_illustration | [イラスト] 検出 |
| test_parser.py | TestParseFigurePlaceholder::test_detect_graph | [グラフ] 検出 |
| test_parser.py | TestParseFigurePlaceholder::test_detect_chart | [チャート] 検出 |
| test_parser.py | TestParseFigurePlaceholder::test_non_figure_returns_none | 非図はNone |
| test_parser.py | TestParseFigurePlaceholder::test_detect_figure_in_line | 行内の図検出 |
| test_parser.py | TestParseFigurePlaceholder::test_detect_multiple_figures_returns_first | 複数図は最初を返す |
| test_parser.py | TestParseFigurePlaceholder::test_figure_with_label | ラベル付き図 |
| test_parser.py | TestParseFigurePlaceholder::test_empty_line_returns_none | 空行はNone |
| test_parser.py | TestParseFigurePlaceholder::test_whitespace_only_returns_none | 空白のみはNone |

### T061: figure XML出力テスト (10 FAIL)

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|---------|
| test_transformer.py | TestTransformFigureNewFormat::test_transform_figure_new_format_path_attribute | path 属性出力 |
| test_transformer.py | TestTransformFigureNewFormat::test_transform_figure_new_format_marker_attribute | marker 属性出力 |
| test_transformer.py | TestTransformFigureNewFormat::test_transform_figure_new_format_read_aloud_false | readAloud="false" |
| test_transformer.py | TestTransformFigureNewFormat::test_transform_figure_new_format_xml | XML形式検証 |
| test_transformer.py | TestTransformFigureNewFormat::test_transform_figure_without_marker | markerなし変換 |
| test_transformer.py | TestTransformFigureNewFormat::test_transform_figure_path_required | path 必須確認 |
| test_transformer.py | TestTransformFigureNewFormat::test_transform_figure_self_closing_element | 自己終了タグ |
| test_transformer.py | TestTransformFigureNewFormat::test_transform_figure_unicode_marker | Unicodeマーカー |
| test_transformer.py | TestTransformFigureNewFormat::test_transform_figure_various_paths | 様々なパス |
| test_transformer.py | TestTransformFigureNewFormat::test_transform_figure_returns_element | Element型返却 |

## 実装ヒント

### List.list_type 実装

```python
@dataclass(frozen=True)
class List:
    """リスト"""
    items: tuple[str, ...]
    list_type: str = "unordered"  # "unordered" | "ordered"
    read_aloud: bool = True
```

### Figure 新形式実装

```python
@dataclass(frozen=True)
class Figure:
    """図表"""
    path: str  # 必須: 画像ファイルパス
    marker: str = ""  # オプション: 元のマーカーテキスト
    read_aloud: str = "false"  # 常に "false"
```

### parse_figure_placeholder 実装

```python
def parse_figure_placeholder(line: str) -> dict | None:
    """図プレースホルダーを検出

    [図], [図1], [写真], [表], [イラスト], [グラフ], [チャート] を検出

    Returns:
        {"marker": "図1"} or None
    """
    import re
    pattern = r'\[(図|写真|表|イラスト|グラフ|チャート)[^\]]*\]'
    match = re.search(pattern, line)
    if match:
        return {"marker": match.group(0)[1:-1]}  # 括弧を除去
    return None
```

### transform_list 実装

```python
def transform_list(lst: List) -> Element:
    """List を XML Element に変換

    出力例:
    <list type="unordered">
      <item>項目1</item>
      <item>項目2</item>
    </list>
    """
    elem = Element("list")
    elem.set("type", lst.list_type)

    for item_text in lst.items:
        item_elem = Element("item")
        item_elem.text = item_text
        elem.append(item_elem)

    return elem
```

### transform_figure 新形式実装

```python
def transform_figure(figure: Figure) -> Element:
    """Figure を XML Element に変換（新形式）

    出力例:
    <figure readAloud="false" path="figures/fig001.png" marker="図1" />
    """
    elem = Element("figure")
    elem.set("readAloud", "false")
    elem.set("path", figure.path)
    if figure.marker:
        elem.set("marker", figure.marker)
    return elem
```

## FAIL出力例

```
============================= test session starts ==============================
platform linux -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0

FAILED tests/book_converter/test_models.py::TestListTypeAttribute::test_list_has_list_type_field - AssertionError: List should have list_type field
FAILED tests/book_converter/test_models.py::TestFigurePathMarker::test_figure_has_path_field - AssertionError: Figure should have path field
FAILED tests/book_converter/test_parser.py::TestParseFigurePlaceholder::test_parse_figure_placeholder_exists - ImportError: cannot import name 'parse_figure_placeholder'
FAILED tests/book_converter/test_transformer.py::TestTransformListType::test_transform_list_exists - ImportError: cannot import name 'transform_list'
FAILED tests/book_converter/test_transformer.py::TestTransformFigureNewFormat::test_transform_figure_new_format_path_attribute - TypeError: Figure.__init__() got an unexpected keyword argument 'path'

============================== 56 failed in 0.10s ==============================
```

## 作成したテストファイル

| ファイル | 追加クラス | テスト数 |
|----------|-----------|---------|
| tests/book_converter/test_models.py | TestListTypeAttribute | 8 |
| tests/book_converter/test_models.py | TestFigurePathMarker | 10 |
| tests/book_converter/test_parser.py | TestParseFigurePlaceholder | 18 |
| tests/book_converter/test_transformer.py | TestTransformListType | 10 |
| tests/book_converter/test_transformer.py | TestTransformFigureNewFormat | 10 |

## 次ステップ

Phase 5 Implementation (GREEN):
1. T064: REDテスト確認
2. T065: List に list_type 属性追加
3. T066: Figure を path, marker 属性に変更
4. T067: parse_list で list_type 判定
5. T068: 図プレースホルダー検出パターン追加
6. T069: transform_list で type 属性出力
7. T070: transform_figure を新形式に改修
8. T071: `make test` PASS (GREEN) 確認
