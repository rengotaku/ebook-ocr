# Phase 2 Test Implementation (RED) 出力

**Date**: 2026-02-08
**Phase**: 2 (US1+US2 目次マーカー認識と構造化)
**Status**: RED (テストFAIL確認済み)

## 1. サマリー

| 項目 | 値 |
|------|-----|
| Phase | 2 (US1+US2 MVP) |
| FAILテスト数 | 76 |
| PASSテスト数 | 295 (既存テスト) |
| テストファイル数 | 3 |

## 2. 作成テストファイル

| ファイル | 追加テストクラス | テスト数 |
|---------|-----------------|---------|
| tests/book_converter/test_parser.py | TestParseTocMarker, TestParseTocEntry, TestTocModels | 46 |
| tests/book_converter/test_transformer.py | TestTransformTableOfContents, TestTransformTocEntry | 21 |
| tests/book_converter/test_integration.py | TestTocMarkerIntegration, TestTocMarkerBackwardCompatibility | 9 |

## 3. FAILテスト一覧

### 3.1 Parser テスト (test_parser.py)

#### TestParseTocMarker (9テスト)

| テストメソッド | 期待動作 |
|---------------|---------|
| test_parse_toc_start_marker | `<!-- toc -->` を MarkerType.TOC_START として検出 |
| test_parse_toc_end_marker | `<!-- /toc -->` を MarkerType.TOC_END として検出 |
| test_parse_toc_marker_case_insensitive_lowercase | 小文字 `<!-- toc -->` を検出 |
| test_parse_toc_marker_case_insensitive_uppercase | 大文字 `<!-- TOC -->` を検出 |
| test_parse_toc_marker_case_insensitive_mixed | 混在 `<!-- Toc -->` を検出 |
| test_parse_toc_marker_with_extra_spaces | スペース `<!--   toc   -->` を検出 |
| test_parse_toc_end_marker_uppercase | 大文字終了 `<!-- /TOC -->` を検出 |
| test_parse_non_toc_marker_returns_none | 目次マーカー以外は None を返す |
| test_parse_toc_marker_with_leading_spaces | 先頭スペース付きを検出 |

#### TestParseTocEntry (22テスト)

| テストメソッド | 期待動作 |
|---------------|---------|
| test_parse_chapter_pattern_basic | `第1章 SREとは` → level=chapter, number=1 |
| test_parse_chapter_pattern_with_page_dots | `第1章 SREとは ... 15` → page=15 |
| test_parse_chapter_pattern_with_page_line | `第2章 信頼性 ─── 25` → page=25 |
| test_parse_chapter_pattern_double_digit | `第10章 まとめ` → number=10 |
| test_parse_section_pattern_basic | `2.1 SLOの理解` → level=section |
| test_parse_section_pattern_with_page | `2.1 SLO ... 30` → page=30 |
| test_parse_subsection_pattern_basic | `2.1.1 SLA` → level=subsection |
| test_parse_subsection_pattern_with_page | `2.1.1 SLA ─── 35` → page=35 |
| test_parse_section_double_digit | `10.12 高度な設定` → number=10.12 |
| test_parse_page_number_with_dots | ドットリーダー形式 |
| test_parse_page_number_with_multiple_dots | 複数ドット形式 |
| test_parse_page_number_with_horizontal_line | 罫線形式 |
| test_parse_page_number_with_dashes | ダッシュ形式 |
| test_parse_page_number_with_spaces | 空白区切り形式 |
| test_parse_entry_without_page_number | ページ番号なし |
| test_parse_page_number_three_digits | 3桁ページ番号 |
| test_parse_other_pattern_hajimeni | `はじめに` → level=other |
| test_parse_other_pattern_owarini | `おわりに` → level=other |
| test_parse_other_pattern_index | `索引` → level=other |
| test_parse_toc_entry_empty_line | 空行は None |
| test_parse_toc_entry_whitespace_only | 空白のみは None |
| test_parse_toc_entry_preserves_unicode | Unicode保持 |

#### TestTocModels (15テスト)

| テストメソッド | 期待動作 |
|---------------|---------|
| test_toc_entry_exists | TocEntry クラスが存在 |
| test_toc_entry_is_dataclass | dataclass である |
| test_toc_entry_is_frozen | イミュータブル |
| test_toc_entry_required_fields | 必須フィールド text, level |
| test_toc_entry_optional_fields_defaults | number="", page="" |
| test_toc_entry_level_chapter | level=chapter |
| test_toc_entry_level_section | level=section |
| test_toc_entry_level_subsection | level=subsection |
| test_toc_entry_level_other | level=other |
| test_table_of_contents_exists | TableOfContents が存在 |
| test_table_of_contents_is_dataclass | dataclass である |
| test_table_of_contents_is_frozen | イミュータブル |
| test_table_of_contents_with_entries | entries タプルを保持 |
| test_table_of_contents_read_aloud_default_false | read_aloud=False がデフォルト |
| test_marker_type_exists | MarkerType 列挙が存在 |
| test_marker_type_toc_start | TOC_START の値 |
| test_marker_type_toc_end | TOC_END の値 |
| test_marker_type_is_enum | Enum である |

### 3.2 Transformer テスト (test_transformer.py)

#### TestTransformTableOfContents (7テスト)

| テストメソッド | 期待動作 |
|---------------|---------|
| test_transform_table_of_contents_basic | `<tableOfContents>` 要素生成 |
| test_transform_table_of_contents_returns_element | Element 型を返す |
| test_transform_table_of_contents_contains_entries | entry 子要素を含む |
| test_transform_table_of_contents_multiple_entries | 複数エントリ変換 |
| test_transform_table_of_contents_preserves_order | 順序を保持 |
| test_transform_table_of_contents_xml_serialization | XML シリアライズ可能 |
| test_transform_table_of_contents_none_returns_none | None → None |

#### TestTransformTocEntry (14テスト)

| テストメソッド | 期待動作 |
|---------------|---------|
| test_transform_toc_entry_basic | `<entry>` 要素生成 |
| test_transform_toc_entry_level_attribute | level 属性設定 |
| test_transform_toc_entry_number_attribute | number 属性設定 |
| test_transform_toc_entry_title_attribute | title 属性設定 |
| test_transform_toc_entry_page_attribute | page 属性設定 |
| test_transform_toc_entry_chapter | chapter レベル変換 |
| test_transform_toc_entry_section | section レベル変換 |
| test_transform_toc_entry_subsection | subsection レベル変換 |
| test_transform_toc_entry_other | other レベル変換 |
| test_transform_toc_entry_without_number | number 空の場合 |
| test_transform_toc_entry_without_page | page 空の場合 |
| test_transform_toc_entry_returns_element | Element 型を返す |
| test_transform_toc_entry_preserves_unicode | Unicode 保持 |
| test_transform_toc_entry_xml_serialization | XML シリアライズ可能 |

### 3.3 Integration テスト (test_integration.py)

#### TestTocMarkerIntegration (5テスト)

| テストメソッド | 期待動作 |
|---------------|---------|
| test_book_with_toc_marker_generates_table_of_contents | 目次マーカー付きで `<tableOfContents>` 生成 |
| test_toc_contains_entries | 目次にエントリ含む |
| test_toc_entry_has_correct_attributes | エントリ属性が正しい |
| test_toc_with_various_levels | 様々なレベルのエントリ |
| test_toc_spanning_multiple_pages | 複数ページにまたがる目次 |

#### TestTocMarkerBackwardCompatibility (4テスト)

| テストメソッド | 期待動作 |
|---------------|---------|
| test_book_without_toc_marker_no_table_of_contents | 目次マーカーなしで `<tableOfContents>` なし (PASS) |
| test_backward_compatible_page_structure | 既存ページ構造維持 (PASS) |
| test_backward_compatible_content_parsing | 既存コンテンツ解析維持 (FAIL - リスト解析の問題) |
| test_existing_sample_book_unchanged | sample_book.md 変更なし (PASS) |

## 4. 実装ヒント

### 4.1 models.py に追加するエンティティ

```python
from enum import Enum

class MarkerType(Enum):
    """Content marker types."""
    TOC_START = "toc_start"
    TOC_END = "toc_end"
    # Phase 4 で追加
    # CONTENT_START = "content_start"
    # CONTENT_END = "content_end"
    # SKIP_START = "skip_start"
    # SKIP_END = "skip_end"

@dataclass(frozen=True)
class TocEntry:
    """Table of Contents entry."""
    text: str              # エントリのタイトルテキスト
    level: str             # "chapter", "section", "subsection", "other"
    number: str = ""       # 章番号（例: "1", "2.1", "2.1.1"）
    page: str = ""         # 参照ページ番号

@dataclass(frozen=True)
class TableOfContents:
    """Complete Table of Contents."""
    entries: tuple[TocEntry, ...]
    read_aloud: bool = False
```

### 4.2 parser.py に追加する関数

```python
def parse_toc_marker(line: str) -> MarkerType | None:
    """Parse a TOC marker line.

    Returns MarkerType.TOC_START or TOC_END if line is a toc marker.
    Case insensitive.
    """
    ...

def parse_toc_entry(line: str) -> TocEntry | None:
    """Parse a TOC entry line.

    Patterns:
    - 第N章 タイトル ... ページ番号
    - N.N タイトル ... ページ番号
    - N.N.N タイトル ... ページ番号
    - その他 (はじめに, おわりに, etc.)
    """
    ...
```

### 4.3 transformer.py に追加する関数

```python
def transform_toc_entry(entry: TocEntry) -> Element:
    """Transform TocEntry to XML element.

    <entry level="chapter" number="1" title="SREとは" page="15"/>
    """
    ...

def transform_table_of_contents(toc: TableOfContents | None) -> Element | None:
    """Transform TableOfContents to XML element.

    <tableOfContents>
      <entry .../>
      <entry .../>
    </tableOfContents>
    """
    ...
```

## 5. FAIL出力例

```
$ make test
...
FAILED tests/book_converter/test_parser.py::TestParseTocMarker::test_parse_toc_start_marker
    ImportError: cannot import name 'parse_toc_marker' from 'src.book_converter.parser'

FAILED tests/book_converter/test_parser.py::TestTocModels::test_toc_entry_exists
    ImportError: cannot import name 'TocEntry' from 'src.book_converter.models'

FAILED tests/book_converter/test_transformer.py::TestTransformTableOfContents::test_transform_table_of_contents_basic
    ImportError: cannot import name 'transform_table_of_contents' from 'src.book_converter.transformer'
...
======================== 76 failed, 295 passed in 1.13s ========================
```

## 6. 次のステップ

1. **phase-executor** が Implementation (GREEN) を実行
2. models.py に TocEntry, TableOfContents, MarkerType を追加
3. parser.py に parse_toc_marker(), parse_toc_entry() を実装
4. transformer.py に transform_toc_entry(), transform_table_of_contents() を実装
5. `make test` PASS を確認 (GREEN)
6. Verification を実行
