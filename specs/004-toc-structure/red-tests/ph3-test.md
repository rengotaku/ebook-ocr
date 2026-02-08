# Phase 3 REDテスト結果: US3 目次の読み上げ制御

**Date**: 2026-02-08
**Status**: RED (FAIL確認済み)

## 1. サマリー

| 項目 | 値 |
|------|-----|
| Phase | 3 (US3: 目次の読み上げ制御) |
| FAILテスト数 | 9 |
| PASSテスト数 | 373 (既存テスト + Phase 2テスト) |
| テストファイル | test_transformer.py, test_integration.py |

## 2. 作成したテストファイル

| ファイル | クラス | 新規テスト数 |
|---------|--------|-------------|
| tests/book_converter/test_transformer.py | TestTableOfContentsReadAloud | 6 |
| tests/book_converter/test_integration.py | TestTocReadAloudIntegration | 5 |

## 3. FAILテスト一覧

### 3.1 test_transformer.py (6 FAIL)

| テストメソッド | 期待される動作 | 失敗理由 |
|---------------|---------------|---------|
| `test_table_of_contents_has_read_aloud_false_attribute` | tableOfContentsにreadAloud="false"属性が設定される | `element.get("readAloud")` が `None` を返す |
| `test_table_of_contents_default_read_aloud_is_false` | tableOfContentsのreadAloudデフォルト値はfalse | `element.get("readAloud")` が `None` を返す |
| `test_table_of_contents_read_aloud_in_xml_output` | XMLシリアライズ時にreadAloud属性が含まれる | `'readAloud="false"'` がXML文字列に含まれない |
| `test_page_level_toc_has_read_aloud_false` | ページレベルの目次もreadAloud="false"を持つ | `toc_elem.get("readAloud")` が `None` を返す |
| `test_book_level_toc_has_read_aloud_false` | ブックレベルの目次もreadAloud="false"を持つ | `element.get("readAloud")` が `None` を返す |
| `test_empty_toc_still_has_read_aloud_false` | 空の目次でもreadAloud="false"が設定される | `element.get("readAloud")` が `None` を返す |

### 3.2 test_integration.py (5 FAIL, うち2テストはreadAloud以外の期待値問題で3 FAIL)

| テストメソッド | 期待される動作 | 失敗理由 |
|---------------|---------------|---------|
| `test_generated_xml_contains_read_aloud_false` | 生成されたXMLにreadAloud="false"が含まれる | `toc.get("readAloud")` が `None` を返す |
| `test_multi_entry_toc_read_aloud_false` | 複数エントリの目次でもreadAloud="false"が設定される | `toc.get("readAloud")` が `None` を返す |
| `test_multi_page_toc_read_aloud_false` | 複数ページにまたがる目次でもreadAloud="false"が設定される | `toc.get("readAloud")` が `None` を返す |
| `test_xml_string_contains_read_aloud_attribute` | XMLシリアライズ結果にreadAloud="false"が文字列として含まれる | PASSした可能性あり (他のreadAloud属性) |
| `test_backward_compatible_without_toc_marker` | 目次マーカーなしの場合、tableOfContentsは生成されない | PASS (後方互換テスト) |

## 4. 実装ヒント

### 4.1 修正対象

**ファイル**: `src/book_converter/transformer.py`

**関数**: `transform_table_of_contents()`

### 4.2 現在の実装 (抜粋)

```python
def transform_table_of_contents(toc: TableOfContents | None) -> Element | None:
    if toc is None:
        return None

    elem = Element("tableOfContents")

    # Add entries
    for entry in toc.entries:
        entry_elem = transform_toc_entry(entry)
        elem.append(entry_elem)

    return elem
```

### 4.3 必要な変更

`elem = Element("tableOfContents")` の後に以下を追加:

```python
elem.set("readAloud", "false")
```

または、モデルの `toc.read_aloud` 値を使用:

```python
elem.set("readAloud", "true" if toc.read_aloud else "false")
```

**注意**: `TableOfContents.read_aloud` のデフォルトは `False` なので、どちらの実装でも結果は同じになる。

## 5. FAILサンプル出力

```
FAILED tests/book_converter/test_transformer.py::TestTableOfContentsReadAloud::test_table_of_contents_has_read_aloud_false_attribute
    def test_table_of_contents_has_read_aloud_false_attribute(self) -> None:
        """tableOfContentsにreadAloud="false"属性が設定される"""
        from src.book_converter.transformer import transform_table_of_contents
        from src.book_converter.models import TocEntry, TableOfContents

        entry = TocEntry(text="第1章", level="chapter", number="1", page="15")
        toc = TableOfContents(entries=(entry,), read_aloud=False)

        element = transform_table_of_contents(toc)

        assert element is not None
>       assert element.get("readAloud") == "false"
E       AssertionError: assert None == 'false'
```

```
FAILED tests/book_converter/test_integration.py::TestTocReadAloudIntegration::test_generated_xml_contains_read_aloud_false
>       assert toc.get("readAloud") == "false"
E       AssertionError: assert None == 'false'
```

## 6. 関連要件

- **FR-006**: システムは `<tableOfContents>` 要素に `readAloud="false"` 属性をデフォルトで設定しなければならない
- **US3 Acceptance Scenarios**: 目次マーカーで囲まれたテキストがある場合、`<tableOfContents>` 要素に `readAloud="false"` 属性が設定される

## 7. 次のステップ

1. **phase-executor** が `transform_table_of_contents()` に `readAloud="false"` 属性を追加
2. `make test` でPASS確認 (GREEN)
3. リグレッションなし確認
4. Phase 3出力生成: `specs/004-toc-structure/tasks/ph3-output.md`
