# Phase 2 テスト実装 (RED) 結果

**日付**: 2026-02-16
**ブランチ**: 009-converter-redesign
**対象**: User Story 1 - TOC階層構造の正確な反映

## サマリ

| 項目 | 値 |
|------|-----|
| フェーズ | Phase 2 |
| FAILテスト数 | 26 |
| PASSテスト数 | 8 (動的型付けによる偶発的PASS) |
| RED確認 | 完了 |

## 作成テストファイル

| ファイル | テストクラス | テスト数 |
|----------|-------------|---------|
| tests/book_converter/test_models.py | TestTocEntryLevelInt | 9 |
| tests/book_converter/test_parser.py | TestParseTocEntryLevelNumeric | 8 |
| tests/book_converter/test_parser.py | TestTocHierarchyMultiLevel | 6 |
| tests/book_converter/test_transformer.py | TestTransformTocEntryLevelNumeric | 11 |

## FAILテスト一覧

### T008: TocEntry.level int化テスト (test_models.py)

| テストメソッド | 期待動作 | 失敗理由 |
|---------------|----------|----------|
| test_toc_entry_level_type_annotation_is_int | TocEntry.level の型アノテーションが int | 現在の型は str |

### T009: parse_toc_entry level数値化テスト (test_parser.py)

| テストメソッド | 期待動作 | 失敗理由 |
|---------------|----------|----------|
| test_parse_toc_entry_level_numeric_chapter | level=1 (int) を返す | "chapter" (str) を返す |
| test_parse_toc_entry_level_numeric_section | level=2 (int) を返す | "section" (str) を返す |
| test_parse_toc_entry_level_numeric_subsection | level=3 (int) を返す | "subsection" (str) を返す |
| test_parse_toc_entry_level_numeric_episode | level (int) を返す | 文字列を返す |
| test_parse_toc_entry_level_numeric_other | level (int) を返す | "other" (str) を返す |
| test_parse_toc_entry_level_not_string | level が str ではない | str を返す |
| test_parse_toc_entry_level_1_for_chapter_en | level=1 (int) を返す | "chapter" (str) を返す |
| test_parse_toc_entry_preserves_text_and_number | level=1 (int) + 他属性保持 | "chapter" (str) を返す |

### T010: TOC階層3レベル以上テスト (test_parser.py)

| テストメソッド | 期待動作 | 失敗理由 |
|---------------|----------|----------|
| test_toc_hierarchy_3_levels | level=1,2,3 (int) | "chapter", "section", "subsection" (str) |
| test_toc_hierarchy_4_levels | level=1,2,3,4 (int) | 文字列を返す |
| test_toc_hierarchy_5_levels | level=1,2,3,4,5 (int) | 文字列を返す |
| test_toc_hierarchy_mixed_levels_order | 混在した階層で int | 文字列を返す |
| test_toc_hierarchy_level_values_are_integers | isinstance(level, int) | str のため False |
| test_toc_hierarchy_unicode_titles | Unicode + int level | 文字列を返す |

### T011: TOC XML出力テスト (test_transformer.py)

| テストメソッド | 期待動作 | 失敗理由 |
|---------------|----------|----------|
| test_transform_toc_entry_level_numeric_1 | level="1" を出力 | int 1 をそのまま出力 |
| test_transform_toc_entry_level_numeric_2 | level="2" を出力 | int 2 をそのまま出力 |
| test_transform_toc_entry_level_numeric_3 | level="3" を出力 | int 3 をそのまま出力 |
| test_transform_toc_entry_level_numeric_4 | level="4" を出力 | int 4 をそのまま出力 |
| test_transform_toc_entry_level_numeric_5 | level="5" を出力 | int 5 をそのまま出力 |
| test_transform_toc_entry_level_not_chapter_string | level="1" (not "chapter") | int 1 をそのまま出力 |
| test_transform_toc_entry_level_not_section_string | level="2" (not "section") | int 2 をそのまま出力 |
| test_transform_toc_entry_level_numeric_xml_serialization | level="1" がXMLに含まれる | int をシリアライズ不可 (TypeError) |
| test_transform_toc_entry_all_levels_xml_serialization | 全レベルがXMLに含まれる | int をシリアライズ不可 (TypeError) |
| test_transform_toc_entry_preserves_other_attributes | level="2" + 他属性 | int 2 をそのまま出力 |
| test_transform_table_of_contents_with_numeric_levels | TOC内の全エントリが数値level | int をそのまま出力 |

## 実装ヒント

### models.py (T008)

```python
# 現在
@dataclass(frozen=True)
class TocEntry:
    text: str
    level: str  # "chapter", "section", "subsection", "other"
    ...

# 変更後
@dataclass(frozen=True)
class TocEntry:
    text: str
    level: int  # 1-5
    ...
```

### parser.py (T009, T010)

```python
# 現在
def parse_toc_entry(line: str) -> TocEntry | None:
    ...
    return TocEntry(
        text=match.group(2).strip(),
        level="chapter",  # 文字列
        ...
    )

# 変更後
def parse_toc_entry(line: str) -> TocEntry | None:
    ...
    return TocEntry(
        text=match.group(2).strip(),
        level=1,  # 整数
        ...
    )
```

### transformer.py (T011)

```python
# 現在
def transform_toc_entry(entry: TocEntry) -> Element:
    element = Element("entry")
    element.set("level", entry.level)  # level がそのまま出力
    ...

# 変更後
def transform_toc_entry(entry: TocEntry) -> Element:
    element = Element("entry")
    element.set("level", str(entry.level))  # int を文字列に変換
    ...
```

## FAIL出力例

```
$ python -m pytest tests/book_converter/test_models.py::TestTocEntryLevelInt::test_toc_entry_level_type_annotation_is_int -v

FAILED tests/book_converter/test_models.py::TestTocEntryLevelInt::test_toc_entry_level_type_annotation_is_int
    AssertionError: TocEntry.level type should be int, but got str

$ python -m pytest tests/book_converter/test_parser.py::TestParseTocEntryLevelNumeric::test_parse_toc_entry_level_numeric_chapter -v

FAILED tests/book_converter/test_parser.py::TestParseTocEntryLevelNumeric::test_parse_toc_entry_level_numeric_chapter
    AssertionError: assert 'chapter' == 1
     +  where 'chapter' = TocEntry(...).level

$ python -m pytest tests/book_converter/test_transformer.py::TestTransformTocEntryLevelNumeric::test_transform_toc_entry_level_numeric_xml_serialization -v

FAILED tests/book_converter/test_transformer.py::TestTransformTocEntryLevelNumeric::test_transform_toc_entry_level_numeric_xml_serialization
    TypeError: cannot serialize 1 (type int)
```

## 次のステップ

phase-executor が Implementation (GREEN) を実行:

1. T014: RED出力確認 (このファイル)
2. T015: TocEntry.level を int に変更 (models.py)
3. T016: parse_toc_entry で level を int で返す (parser.py)
4. T017: transform_toc_entry で level を文字列として出力 (transformer.py)
5. T018: 既存コードの level 文字列参照箇所を修正
6. T019: `make test` PASS 確認
