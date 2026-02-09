# Phase 3: Test Implementation (RED) - 章扉ページの識別

**Status**: RED (テスト失敗)
**Date**: 2026-02-09
**Phase**: 3 (User Story 3 - 章扉ページの識別)

## サマリー

| 項目 | 値 |
|------|-----|
| Phase | 3 |
| User Story | US3: 章扉ページの識別 |
| 機能要件 | FR-007 |
| 新規テスト数 | 12 |
| FAILテスト数 | 10 |
| PASSテスト数 | 2 (既存機能で動作) |
| テストファイル | tests/book_converter/test_page_grouper.py |

## FAILテスト一覧

| テストファイル | テストメソッド | 期待動作 |
|---------------|----------------|----------|
| test_page_grouper.py | TestIsChapterTitlePage::test_identify_chapter_title_page_by_metadata | pageMetadataに「第N章」を含むページを章扉ページと判定 |
| test_page_grouper.py | TestIsChapterTitlePage::test_identify_chapter_title_page_by_heading | headingに「第N章」を含むページを章扉ページと判定 |
| test_page_grouper.py | TestIsChapterTitlePage::test_section_page_is_not_chapter_title | セクション番号(1.1)を持つページは章扉ページではない |
| test_page_grouper.py | TestIsChapterTitlePage::test_subsection_page_is_not_chapter_title | サブセクション番号(1.1.1)を持つページは章扉ページではない |
| test_page_grouper.py | TestIsChapterTitlePage::test_front_matter_page_is_not_chapter_title | 前付けページは章扉ページではない |
| test_page_grouper.py | TestIsChapterTitlePage::test_page_without_metadata_not_chapter_title | メタデータなしページは章扉ページではない |
| test_page_grouper.py | TestChapterTitlePageTypeAttribute::test_chapter_title_page_has_type_attribute | 章扉ページに`type="chapter-title"`属性が付与される |
| test_page_grouper.py | TestChapterTitlePageTypeAttribute::test_chapter_title_page_is_first_in_chapter | 各章の最初のページに`type="chapter-title"`属性が付与される |
| test_page_grouper.py | TestChapterTitlePageEdgeCases::test_chapter_with_only_title_page | 章扉ページのみの章でも属性が付与される |
| test_page_grouper.py | TestChapterTitlePageEdgeCases::test_multiple_chapters_all_get_type_attribute | 複数章すべての章扉ページに属性が付与される |

## PASSテスト (既存機能で動作)

| テストファイル | テストメソッド | 理由 |
|---------------|----------------|------|
| test_page_grouper.py | TestChapterTitlePageTypeAttribute::test_non_chapter_title_pages_no_type_attribute | セクション/サブセクションページにtype属性がない (現状通り) |
| test_page_grouper.py | TestChapterTitlePageTypeAttribute::test_front_matter_pages_no_type_attribute | 前付けページにtype属性がない (現状通り) |

## 新規テストクラス

### TestIsChapterTitlePage

`is_chapter_title_page(page: ET.Element) -> bool` 関数のテスト

**テスト内容**:
- pageMetadataの「第N章」パターン検出
- headingの「第N章」パターン検出
- セクション/サブセクションページの除外
- 前付けページの除外
- メタデータなしページの処理

### TestChapterTitlePageTypeAttribute

`group_pages_by_toc()` 出力における `type="chapter-title"` 属性のテスト

**テスト内容**:
- 章扉ページへの属性付与
- 各章の最初のページへの属性付与
- セクション/サブセクションページに属性がないこと
- 前付けページに属性がないこと

### TestChapterTitlePageEdgeCases

エッジケーステスト

**テスト内容**:
- 章扉ページのみの章
- 複数章のすべてに属性付与

## 実装ヒント

### is_chapter_title_page() 関数

```python
def is_chapter_title_page(page: ET.Element) -> bool:
    """章扉ページかどうかを判定する。

    判定条件:
    1. pageMetadataに「第N章」パターンが含まれる
    2. または headingに「第N章」パターンが含まれる
    3. セクション番号(X.X)を持つページは除外
    """
    # pageMetadata から判定
    page_metadata = page.find('pageMetadata')
    if page_metadata is not None:
        metadata_text = ''.join(page_metadata.itertext())
        # 「第N章」パターンをチェック
        if re.match(r'^第\d+章', metadata_text):
            return True
        # emphasis タグ（前付け）は除外
        if '<emphasis>' in ET.tostring(page_metadata, encoding='unicode'):
            return False

    # heading から判定
    content = page.find('content')
    if content is not None:
        heading = content.find('heading')
        if heading is not None:
            heading_text = ''.join(heading.itertext())
            if re.match(r'^第\d+章', heading_text):
                return True

    return False
```

### build_hierarchy() の拡張

章直下のページ (章番号のみを持つページ) に `type="chapter-title"` 属性を付与する。

```python
# 章扉ページの場合、type属性を付与
if is_chapter_title_page(page):
    page.set('type', 'chapter-title')
```

## FAIL出力例

```
=========================== FAILURES ===========================
_______ TestIsChapterTitlePage.test_identify_chapter_title_page_by_metadata _______

self = <tests.book_converter.test_page_grouper.TestIsChapterTitlePage object at 0x...>

    def test_identify_chapter_title_page_by_metadata(self) -> None:
        """Page with '第N章' in pageMetadata is identified as chapter title page."""
        page_xml = """<page number="14" sourceFile="page_0014.png">
            <pageMetadata type="chapter-page" readAloud="false">第1章 SREとは — 1 / 1</pageMetadata>
            <content readAloud="false">
                <heading level="1" readAloud="false">第1章 SREとは</heading>
            </content>
        </page>"""
        page = ET.fromstring(page_xml)
        result = is_chapter_title_page(page)
>       assert result is True
E       NotImplementedError: is_chapter_title_page not implemented yet

tests/book_converter/test_page_grouper.py:662: NotImplementedError
---------------------------------------------------------------
_______ TestChapterTitlePageTypeAttribute.test_chapter_title_page_has_type_attribute _______

self = <tests.book_converter.test_page_grouper.TestChapterTitlePageTypeAttribute object at 0x...>

    def test_chapter_title_page_has_type_attribute(self) -> None:
        ...
        chapter_title_page = chapter1.find("page[@number='2']")
        assert chapter_title_page is not None
>       assert chapter_title_page.get("type") == "chapter-title"
E       AssertionError: assert None == 'chapter-title'

tests/book_converter/test_page_grouper.py:757: AssertionError
=========================== short test summary info ============================
FAILED tests/book_converter/test_page_grouper.py::TestIsChapterTitlePage::test_identify_chapter_title_page_by_metadata
FAILED tests/book_converter/test_page_grouper.py::TestIsChapterTitlePage::test_identify_chapter_title_page_by_heading
FAILED tests/book_converter/test_page_grouper.py::TestIsChapterTitlePage::test_section_page_is_not_chapter_title
FAILED tests/book_converter/test_page_grouper.py::TestIsChapterTitlePage::test_subsection_page_is_not_chapter_title
FAILED tests/book_converter/test_page_grouper.py::TestIsChapterTitlePage::test_front_matter_page_is_not_chapter_title
FAILED tests/book_converter/test_page_grouper.py::TestIsChapterTitlePage::test_page_without_metadata_not_chapter_title
FAILED tests/book_converter/test_page_grouper.py::TestChapterTitlePageTypeAttribute::test_chapter_title_page_has_type_attribute
FAILED tests/book_converter/test_page_grouper.py::TestChapterTitlePageTypeAttribute::test_chapter_title_page_is_first_in_chapter
FAILED tests/book_converter/test_page_grouper.py::TestChapterTitlePageEdgeCases::test_chapter_with_only_title_page
FAILED tests/book_converter/test_page_grouper.py::TestChapterTitlePageEdgeCases::test_multiple_chapters_all_get_type_attribute
======================== 10 failed, 502 passed in 0.51s ========================
```

## 次のステップ

1. **GREEN Phase**: `is_chapter_title_page()` 関数を実装
2. **GREEN Phase**: `group_pages_by_toc()` で `type="chapter-title"` 属性を付与
3. **Verification**: 全テスト (US1+US2+US3) がPASSすることを確認
