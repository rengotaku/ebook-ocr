# Phase 4 Test Implementation (RED) - US4 コンテンツ範囲マーカー

## 概要

| 項目 | 値 |
|------|-----|
| フェーズ | Phase 4 (US4) |
| 対象ユーザーストーリー | US4: コンテンツ範囲マーカーによる読み上げ制御 |
| 作成テスト数 | 50 |
| RED確認 | 完了 (50 FAILED, 391 passed) |
| テストファイル | test_parser.py, test_transformer.py, test_integration.py |

## テストファイル一覧

| ファイル | 追加テストクラス | テスト数 |
|---------|-----------------|----------|
| tests/book_converter/test_parser.py | TestParseContentMarker | 9 |
| tests/book_converter/test_parser.py | TestParseSkipMarker | 8 |
| tests/book_converter/test_parser.py | TestMarkerStateStack | 10 |
| tests/book_converter/test_parser.py | TestMarkerTypeContentSkip | 4 |
| tests/book_converter/test_transformer.py | TestDefaultReadAloudFalse | 5 |
| tests/book_converter/test_transformer.py | TestContentMarkerReadAloudTrue | 5 |
| tests/book_converter/test_transformer.py | TestSkipMarkerReadAloudFalse | 4 |
| tests/book_converter/test_transformer.py | TestContentReadAloudXMLSerialization | 4 |
| tests/book_converter/test_integration.py | TestContentSkipMarkerIntegration | 11 |

## FAILテスト一覧

### Parser Tests (test_parser.py)

| テストメソッド | 期待動作 |
|--------------|---------|
| test_parse_content_start_marker | `<!-- content -->`を検出してCONTENT_STARTを返す |
| test_parse_content_end_marker | `<!-- /content -->`を検出してCONTENT_ENDを返す |
| test_parse_content_marker_case_insensitive_lowercase | 小文字contentマーカーを検出 |
| test_parse_content_marker_case_insensitive_uppercase | 大文字CONTENTマーカーを検出 |
| test_parse_content_marker_case_insensitive_mixed | 混在Contentマーカーを検出 |
| test_parse_content_marker_with_extra_spaces | 余分なスペースがあっても検出 |
| test_parse_content_end_marker_uppercase | 大文字の終了マーカーを検出 |
| test_parse_content_marker_with_leading_spaces | 先頭スペースがあっても検出 |
| test_parse_non_content_marker_returns_none | 非contentマーカーはNoneを返す |
| test_parse_skip_start_marker | `<!-- skip -->`を検出してSKIP_STARTを返す |
| test_parse_skip_end_marker | `<!-- /skip -->`を検出してSKIP_ENDを返す |
| test_parse_skip_marker_case_insensitive_uppercase | 大文字SKIPマーカーを検出 |
| test_parse_skip_marker_case_insensitive_mixed | 混在Skipマーカーを検出 |
| test_parse_skip_marker_with_extra_spaces | 余分なスペースがあっても検出 |
| test_parse_skip_end_marker_uppercase | 大文字の終了マーカーを検出 |
| test_parse_skip_marker_with_leading_spaces | 先頭スペースがあっても検出 |
| test_parse_non_skip_marker_returns_none | 非skipマーカーはNoneを返す |
| test_get_read_aloud_from_empty_stack | 空スタック → false |
| test_get_read_aloud_with_content_on_stack | contentスタック → true |
| test_get_read_aloud_with_skip_on_stack | skipスタック → false |
| test_get_read_aloud_nested_skip_in_content | content内skip → false |
| test_get_read_aloud_nested_content_in_skip | skip内content → true |
| test_get_read_aloud_after_pop_skip_from_content | skip pop後 → true |
| test_get_read_aloud_after_pop_content | content pop後 → false |
| test_get_read_aloud_deep_nesting | 深いネスト（skipで終わる） |
| test_get_read_aloud_deep_nesting_ending_with_content | 深いネスト（contentで終わる） |
| test_stack_manipulation_sequence | スタック操作シーケンス |

### Transformer Tests (test_transformer.py)

| テストメソッド | 期待動作 |
|--------------|---------|
| test_content_without_marker_has_read_aloud_false | マーカーなしcontentはreadAloud=false |
| test_paragraph_without_marker_has_read_aloud_false | マーカーなし段落はreadAloud=false |
| test_heading_without_marker_has_read_aloud_false | マーカーなし見出しはreadAloud=false |
| test_list_without_marker_has_read_aloud_false | マーカーなしリストはreadAloud=false |
| test_default_content_model_read_aloud_is_false | Content.read_aloudデフォルトはFalse |
| test_content_inside_marker_has_read_aloud_true | contentマーカー内はreadAloud=true |
| test_paragraph_inside_content_marker_has_read_aloud_true | contentマーカー内段落はreadAloud=true |
| test_heading_inside_content_marker_has_read_aloud_true | contentマーカー内見出しはreadAloud=true |
| test_list_inside_content_marker_has_read_aloud_true | contentマーカー内リストはreadAloud=true |
| test_mixed_elements_inside_content_marker_all_have_read_aloud_true | 複合要素全てreadAloud=true |
| test_content_inside_skip_marker_has_read_aloud_false | skipマーカー内はreadAloud=false |
| test_paragraph_inside_skip_marker_has_read_aloud_false | skipマーカー内段落はreadAloud=false |
| test_skip_inside_content_has_read_aloud_false | content内skipはreadAloud=false |
| test_content_inside_skip_then_back_to_skip | skip→content→skip遷移 |
| test_content_read_aloud_true_in_xml | XML出力にreadAloud=true |
| test_content_read_aloud_false_in_xml | XML出力にreadAloud=false |
| test_paragraph_read_aloud_true_in_xml | 段落XML出力にreadAloud=true |
| test_paragraph_read_aloud_false_in_xml | 段落XML出力にreadAloud=false |

### Integration Tests (test_integration.py)

| テストメソッド | 期待動作 |
|--------------|---------|
| test_content_marker_sets_read_aloud_true | contentマーカー内はreadAloud=true |
| test_skip_marker_sets_read_aloud_false | skipマーカー内はreadAloud=false |
| test_no_marker_defaults_to_read_aloud_false | マーカーなしはreadAloud=false |
| test_mixed_content_and_skip_markers | content/skip混在時の動作 |
| test_backward_compatible_without_content_skip_markers | 後方互換性（マーカーなし） |

### PASSEDテスト (構造確認のみ)

| テストメソッド | 確認内容 |
|--------------|---------|
| test_nested_skip_in_content | ネスト構造のXML生成 |
| test_content_spanning_multiple_pages | 複数ページにまたがるcontent |
| test_multiple_content_blocks_on_same_page | 同一ページの複数contentブロック |
| test_content_with_toc_and_skip_markers | toc/content/skip混在時の構造 |
| test_xml_read_aloud_attribute_serialization | readAloud属性の存在確認 |
| test_marker_type_content_start | MarkerType.CONTENT_START値確認 |
| test_marker_type_content_end | MarkerType.CONTENT_END値確認 |
| test_marker_type_skip_start | MarkerType.SKIP_START値確認 |
| test_marker_type_skip_end | MarkerType.SKIP_END値確認 |

## 実装ヒント

### 1. parse_content_marker関数の実装

```python
def parse_content_marker(line: str) -> MarkerType | None:
    """Parse content/skip marker line.

    Returns:
        MarkerType.CONTENT_START for <!-- content -->
        MarkerType.CONTENT_END for <!-- /content -->
        MarkerType.SKIP_START for <!-- skip -->
        MarkerType.SKIP_END for <!-- /skip -->
        None otherwise
    """
    import re

    # Content marker pattern
    content_pattern = r"<!--\s*(/?)\s*[Cc][Oo][Nn][Tt][Ee][Nn][Tt]\s*-->"
    match = re.search(content_pattern, line)
    if match:
        slash = match.group(1)
        return MarkerType.CONTENT_END if slash else MarkerType.CONTENT_START

    # Skip marker pattern
    skip_pattern = r"<!--\s*(/?)\s*[Ss][Kk][Ii][Pp]\s*-->"
    match = re.search(skip_pattern, line)
    if match:
        slash = match.group(1)
        return MarkerType.SKIP_END if slash else MarkerType.SKIP_START

    return None
```

### 2. get_read_aloud_from_stack関数の実装

```python
def get_read_aloud_from_stack(stack: list[str]) -> bool:
    """Get readAloud value from marker stack.

    Args:
        stack: List of marker types ("content" or "skip")

    Returns:
        True if top of stack is "content", False otherwise
    """
    if not stack:
        return False  # Default: readAloud=false

    top = stack[-1]
    return top == "content"
```

### 3. transform_content関数の修正

Content要素のreadAloud属性をXMLに出力するよう修正が必要:

```python
def transform_content(content: Content) -> Element:
    element = Element("content")
    element.set("readAloud", "true" if content.read_aloud else "false")
    # ... element transformation
```

### 4. Contentモデルのデフォルト値変更

```python
@dataclass(frozen=True)
class Content:
    elements: tuple[ContentElement, ...]
    read_aloud: bool = False  # Phase 4: デフォルトをFalseに変更
```

## FAIL出力例

```
FAILED tests/book_converter/test_parser.py::TestParseContentMarker::test_parse_content_start_marker
    ImportError: cannot import name 'parse_content_marker' from 'src.book_converter.parser'

FAILED tests/book_converter/test_parser.py::TestMarkerStateStack::test_get_read_aloud_from_empty_stack
    ImportError: cannot import name 'get_read_aloud_from_stack' from 'src.book_converter.parser'

FAILED tests/book_converter/test_transformer.py::TestDefaultReadAloudFalse::test_content_without_marker_has_read_aloud_false
    AssertionError: assert None == 'false'

FAILED tests/book_converter/test_transformer.py::TestDefaultReadAloudFalse::test_default_content_model_read_aloud_is_false
    AssertionError: assert True is False

FAILED tests/book_converter/test_integration.py::TestContentSkipMarkerIntegration::test_content_marker_sets_read_aloud_true
    AssertionError: assert None == 'true'
```

## 次のステップ

Phase 4 Implementation (GREEN):
1. `parse_content_marker()`関数を実装
2. `get_read_aloud_from_stack()`関数を実装
3. `Content`モデルのデフォルト値を`read_aloud=False`に変更
4. `transform_content()`でreadAloud属性を出力
5. パーサーでcontent/skipマーカーを処理
6. 全50テストがPASSすることを確認
