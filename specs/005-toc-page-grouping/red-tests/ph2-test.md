# Phase 2 テスト実装 (RED)

**ステータス**: RED (全テスト失敗)
**日付**: 2026-02-09
**Phase**: 2 - User Story 1+2 (基本グルーピング + セクション判定)

## サマリー

| 項目 | 値 |
|------|-----|
| Phase | 2 |
| 作成テスト数 | 50 |
| FAIL確認 | 50/50 テスト失敗 |
| テストファイル | `tests/book_converter/test_page_grouper.py` |
| スタブモジュール | `src/book_converter/page_grouper.py` |

## 作成ファイル

| ファイル | 説明 |
|----------|------|
| `tests/book_converter/test_page_grouper.py` | メインテストファイル (50テスト) |
| `src/book_converter/page_grouper.py` | スタブモジュール (NotImplementedError) |

## FAILテスト一覧

### US2: セクション番号抽出テスト (27テスト)

| テストファイル | テストメソッド | 期待動作 |
|----------------|----------------|----------|
| test_page_grouper.py | TestExtractSectionFromPageMetadata::test_extract_section_standard_format | "1.1 SREの概要 ― 1 / 3" から "1.1" を抽出 |
| test_page_grouper.py | TestExtractSectionFromPageMetadata::test_extract_section_chapter_format | "第1章 SREとは — 1 / 1" から "1" を抽出 |
| test_page_grouper.py | TestExtractSectionFromPageMetadata::test_extract_subsection_format | "2.1.1 SLA ― 2 / 3" から "2.1.1" を抽出 |
| test_page_grouper.py | TestExtractSectionFromPageMetadata::test_extract_section_deep_nesting | "1.2.3.4 深いネスト" から "1.2.3.4" を抽出 |
| test_page_grouper.py | TestExtractSectionFromPageMetadata::test_extract_section_front_matter_returns_none | emphasis付きはNone |
| test_page_grouper.py | TestExtractSectionFromPageMetadata::test_extract_section_no_section_info_returns_none | "1 / 1" はNone |
| test_page_grouper.py | TestExtractSectionFromPageMetadata::test_extract_section_empty_string_returns_none | 空文字はNone |
| test_page_grouper.py | TestExtractSectionFromPageMetadata::test_extract_section_none_input_returns_none | NoneはNone |
| test_page_grouper.py | TestExtractSectionFromPageMetadata::test_extract_section_full_width_space | 全角スペース対応 |
| test_page_grouper.py | TestExtractSectionFromHeading::test_extract_section_prefix_format | "Section 1.1 SREの概要" から "1.1" |
| test_page_grouper.py | TestExtractSectionFromHeading::test_extract_subsection_direct_format | "1.1.1 サイトとは" から "1.1.1" |
| test_page_grouper.py | TestExtractSectionFromHeading::test_extract_chapter_direct_format | "第1章 SREとは" から "1" |
| test_page_grouper.py | TestExtractSectionFromHeading::test_extract_section_no_number_returns_none | "はじめに" はNone |
| test_page_grouper.py | TestExtractSectionFromHeading::test_extract_section_empty_returns_none | 空文字はNone |
| test_page_grouper.py | TestExtractSectionFromHeading::test_extract_section_none_returns_none | NoneはNone |
| test_page_grouper.py | TestParseSectionNumber::test_parse_chapter_number | "1" → SectionNumber(parts=(1,), level="chapter") |
| test_page_grouper.py | TestParseSectionNumber::test_parse_section_number | "2.1" → SectionNumber(parts=(2,1), level="section") |
| test_page_grouper.py | TestParseSectionNumber::test_parse_subsection_number | "2.1.1" → SectionNumber(parts=(2,1,1), level="subsection") |
| test_page_grouper.py | TestParseSectionNumber::test_parse_deep_section_number | "1.2.3.4" → subsection扱い |
| test_page_grouper.py | TestParseSectionNumber::test_parse_invalid_returns_none | "abc" はNone |
| test_page_grouper.py | TestParseSectionNumber::test_parse_empty_returns_none | 空文字はNone |
| test_page_grouper.py | TestParseSectionNumber::test_parse_none_returns_none | NoneはNone |
| test_page_grouper.py | TestParseSectionNumber::test_section_number_chapter_num_property | chapter_numプロパティ |
| test_page_grouper.py | TestParseSectionNumber::test_section_number_is_chapter | is_chapterプロパティ |
| test_page_grouper.py | TestParseSectionNumber::test_section_number_is_section | is_sectionプロパティ |
| test_page_grouper.py | TestParseSectionNumber::test_section_number_is_subsection | is_subsectionプロパティ |

### US1: TOCパース・グルーピングテスト (23テスト)

| テストファイル | テストメソッド | 期待動作 |
|----------------|----------------|----------|
| test_page_grouper.py | TestParseToc::test_parse_toc_basic | TOC XMLから7エントリをパース |
| test_page_grouper.py | TestParseToc::test_parse_toc_chapter_entry | chapterエントリの属性検証 |
| test_page_grouper.py | TestParseToc::test_parse_toc_section_entry | sectionエントリの属性検証 |
| test_page_grouper.py | TestParseToc::test_parse_toc_subsection_entry | subsectionエントリの属性検証 |
| test_page_grouper.py | TestParseToc::test_parse_toc_empty | 空TOCは空リスト |
| test_page_grouper.py | TestParseToc::test_parse_toc_begin_end_attributes | begin/end属性の保持 |
| test_page_grouper.py | TestGroupFrontMatter::test_group_front_matter_basic | ページ1-6がfront-matterに配置 |
| test_page_grouper.py | TestGroupFrontMatter::test_group_front_matter_includes_toc_pages | TOCページ(7-13)もfront-matter |
| test_page_grouper.py | TestGroupFrontMatter::test_group_front_matter_preserves_page_content | ページ内容の保持 |
| test_page_grouper.py | TestGroupPagesBySection::test_group_pages_creates_chapter | chapter要素の生成 |
| test_page_grouper.py | TestGroupPagesBySection::test_group_pages_creates_section | section要素の生成 |
| test_page_grouper.py | TestGroupPagesBySection::test_group_pages_creates_subsection | subsection要素の生成 |
| test_page_grouper.py | TestGroupPagesBySection::test_group_pages_section_contains_pages | sectionにページ配置 |
| test_page_grouper.py | TestGroupPagesBySection::test_group_pages_subsection_contains_pages | subsectionにページ配置 |
| test_page_grouper.py | TestBuildHierarchicalXml::test_build_preserves_metadata | metadataの保持 |
| test_page_grouper.py | TestBuildHierarchicalXml::test_build_preserves_toc | toc要素の保持 |
| test_page_grouper.py | TestBuildHierarchicalXml::test_build_structure_order | 要素順序 (metadata, toc, front-matter, chapter) |
| test_page_grouper.py | TestBuildHierarchicalXml::test_build_well_formed_xml | 整形式XML |
| test_page_grouper.py | TestBuildHierarchicalXml::test_build_page_preserves_all_attributes | ページ属性の保持 |
| test_page_grouper.py | TestBuildHierarchicalXml::test_build_page_preserves_all_children | ページ子要素の保持 |
| test_page_grouper.py | TestBuildHierarchicalXml::test_build_no_flat_pages_at_book_level | book直下にフラットページなし |
| test_page_grouper.py | TestEdgeCases::test_book_without_toc | TOCなしブック |
| test_page_grouper.py | TestEdgeCases::test_empty_chapter | 空チャプター |
| test_page_grouper.py | TestEdgeCases::test_unicode_in_titles | Unicodeタイトル |

## 実装ヒント

### SectionNumber データクラス

```python
@dataclass(frozen=True)
class SectionNumber:
    raw: str           # "1.1.3"
    parts: tuple[int, ...]  # (1, 1, 3)
    level: str         # "chapter", "section", "subsection"

    @property
    def chapter_num(self) -> int:
        return self.parts[0]

    @property
    def is_chapter(self) -> bool:
        return len(self.parts) == 1

    @property
    def is_section(self) -> bool:
        return len(self.parts) == 2

    @property
    def is_subsection(self) -> bool:
        return len(self.parts) >= 3
```

### セクション番号抽出正規表現

```python
# pageMetadataパターン
# "1.1 SREの概要 ― 1 / 3" → "1.1"
# "第1章 SREとは — 1 / 1" → "1"
SECTION_PATTERN = r'^(\d+(?:\.\d+)*)[\s　]'
CHAPTER_PATTERN = r'^第(\d+)章'

# headingパターン
# "Section 1.1 SREの概要" → "1.1"
HEADING_SECTION_PATTERN = r'^Section\s+(\d+(?:\.\d+)*)'
```

### group_pages_by_toc 処理フロー

1. 入力XMLをパース
2. TOC要素からbegin/end取得
3. 各ページからセクション番号抽出
4. ページをfront-matter/chapter/section/subsectionに振り分け
5. 階層構造XMLを構築
6. 文字列として出力

## FAIL出力例

```
$ make test
PYTHONPATH=/data/projects/video-separater .venv/bin/python -m pytest tests/book_converter/test_page_grouper.py -v

tests/book_converter/test_page_grouper.py::TestExtractSectionFromPageMetadata::test_extract_section_standard_format FAILED
tests/book_converter/test_page_grouper.py::TestExtractSectionFromPageMetadata::test_extract_section_chapter_format FAILED
...
=========================== short test summary info ============================
FAILED tests/book_converter/test_page_grouper.py::TestExtractSectionFromPageMetadata::test_extract_section_standard_format - NotImplementedError: extract_section_from_page_metadata not implemented
FAILED tests/book_converter/test_page_grouper.py::TestExtractSectionFromPageMetadata::test_extract_section_chapter_format - NotImplementedError: extract_section_from_page_metadata not implemented
...
============================== 50 failed in 0.27s ==============================
```

## 次のステップ

phase-executor が Implementation (GREEN) を実行:

1. `specs/005-toc-page-grouping/red-tests/ph2-test.md` を読む
2. `src/book_converter/page_grouper.py` を実装
3. `make test` PASS (GREEN) を確認
4. Verification実行
