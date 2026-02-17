# Phase 3 テスト実装 (RED) 結果

**日付**: 2026-02-16
**ブランチ**: 009-converter-redesign
**対象**: User Story 2 - chapter/heading タグの役割明確化

## サマリ

| 項目 | 値 |
|------|-----|
| フェーズ | Phase 3 |
| FAILテスト数 | 66 |
| PASSテスト数 | 0 |
| RED確認 | 完了 |

## 作成テストファイル

| ファイル | テストクラス | テスト数 |
|----------|-------------|---------|
| tests/book_converter/test_models.py | TestStructureContainer | 19 |
| tests/book_converter/test_transformer.py | TestTransformStructureContainer | 17 |
| tests/book_converter/test_transformer.py | TestHeadingReadAloudInStructureContainer | 9 |
| tests/book_converter/test_xml_builder.py | TestPageCommentGeneration | 9 |
| tests/book_converter/test_xml_builder.py | TestInsertPageCommentIntoContainer | 6 |
| tests/book_converter/test_xml_builder.py | TestBuildXMLWithPageComments | 3 |
| tests/book_converter/test_xml_builder.py | TestPageCommentXMLFormat | 3 |

## FAILテスト一覧

### T024: StructureContainer モデルテスト (test_models.py)

| テストメソッド | 期待動作 | 失敗理由 |
|---------------|----------|----------|
| test_structure_container_exists | StructureContainer dataclass が存在する | ImportError: cannot import name 'StructureContainer' |
| test_structure_container_has_container_type | container_type 属性を持つ | ImportError |
| test_structure_container_has_level | level 属性（1-5）を持つ | ImportError |
| test_structure_container_has_number | number 属性を持つ | ImportError |
| test_structure_container_has_title | title 属性を持つ | ImportError |
| test_structure_container_has_children | children 属性を持つ | ImportError |
| test_structure_container_chapter_type | container_type="chapter" のコンテナ | ImportError |
| test_structure_container_section_type | container_type="section" のコンテナ | ImportError |
| test_structure_container_subsection_type | container_type="subsection" のコンテナ | ImportError |
| test_structure_container_level_4 | level=4 の subsection | ImportError |
| test_structure_container_level_5 | level=5 の subsection | ImportError |
| test_structure_container_is_immutable | frozen dataclass | ImportError |
| test_structure_container_children_with_content_element | ContentElement を children に含む | ImportError |
| test_structure_container_children_with_nested_structure | StructureContainer を children に含む | ImportError |
| test_structure_container_children_mixed | 混在した children | ImportError |
| test_structure_container_unicode_title | Unicode title | ImportError |
| test_structure_container_empty_number | 空の number | ImportError |
| test_structure_container_empty_title | 空の title | ImportError |
| test_structure_container_all_levels_1_to_5 | 全レベル（1-5）対応 | ImportError |

### T025: 構造コンテナ変換テスト (test_transformer.py)

| テストメソッド | 期待動作 | 失敗理由 |
|---------------|----------|----------|
| test_transform_structure_container_exists | transform_structure_container 関数が存在 | ImportError: cannot import name 'transform_structure_container' |
| test_transform_structure_container_chapter_basic | chapter コンテナを <chapter> 要素に変換 | ImportError |
| test_transform_structure_container_chapter_number_attribute | number 属性が設定される | ImportError |
| test_transform_structure_container_chapter_title_attribute | title 属性が設定される | ImportError |
| test_transform_structure_container_section | section コンテナを <section> 要素に変換 | ImportError |
| test_transform_structure_container_subsection_level_3 | subsection (level 3) を変換 | ImportError |
| test_transform_structure_container_subsection_level_4 | subsection (level 4) に level 属性 | ImportError |
| test_transform_structure_container_subsection_level_5 | subsection (level 5) に level 属性 | ImportError |
| test_transform_structure_container_with_paragraph_child | 段落を子要素として含める | ImportError |
| test_transform_structure_container_with_heading_child | 見出しを子要素として含める | ImportError |
| test_transform_structure_container_nested_structure | 入れ子構造: chapter > section | ImportError |
| test_transform_structure_container_deep_nesting | 深い入れ子: chapter > section > subsection | ImportError |
| test_transform_structure_container_unicode_title | Unicode タイトル | ImportError |
| test_transform_structure_container_empty_number | 空の number | ImportError |
| test_transform_structure_container_returns_element | 戻り値は Element 型 | ImportError |
| test_transform_structure_container_xml_serialization | XML にシリアライズ可能 | ImportError |
| test_transform_structure_container_complete_example | 完全な例 | ImportError |

### T026: ページコメント生成テスト (test_xml_builder.py)

| テストメソッド | 期待動作 | 失敗理由 |
|---------------|----------|----------|
| test_generate_page_comment_exists | generate_page_comment 関数が存在 | ImportError: cannot import name 'generate_page_comment' |
| test_generate_page_comment_basic | 基本的なページコメント生成 | ImportError |
| test_generate_page_comment_page_1 | ページ 1 のコメント | ImportError |
| test_generate_page_comment_large_page_number | 大きなページ番号 | ImportError |
| test_generate_page_comment_format | <!-- page N --> 形式 | ImportError |
| test_generate_page_comment_returns_comment_type | Comment 型を返す | ImportError |
| test_generate_page_comment_string_page_number | 文字列ページ番号 | ImportError |
| test_generate_page_comment_empty_page_number | 空のページ番号で None | ImportError |
| test_page_comment_in_xml_structure | XML 構造内で正しく動作 | ImportError |
| test_insert_page_comment_into_chapter | chapter 要素に挿入 | ImportError: cannot import name 'insert_page_comment' |
| test_insert_page_comment_into_section | section 要素に挿入 | ImportError |
| test_insert_page_comment_preserves_existing_children | 既存の子要素を保持 | ImportError |
| test_insert_page_comment_at_beginning | 先頭に挿入 | ImportError |
| test_insert_page_comment_returns_none_for_empty_page | 空ページで何も挿入しない | ImportError |
| test_insert_multiple_page_comments | 複数コメント挿入 | ImportError |
| test_build_xml_includes_page_comments | build_xml でページコメント含む | ImportError: cannot import name 'StructureContainer' |
| test_build_xml_page_comment_in_section | section 内のページコメント | ImportError |
| test_build_xml_multiple_page_comments | 複数のページコメント | ImportError |
| test_page_comment_xml_serialization | XML シリアライズ | ImportError |
| test_page_comment_format_with_space | 空白を含むフォーマット | ImportError |
| test_page_comment_in_complete_structure | 完全な構造内でシリアライズ | ImportError |

### T027: heading readAloud属性テスト (test_transformer.py)

| テストメソッド | 期待動作 | 失敗理由 |
|---------------|----------|----------|
| test_heading_in_structure_container_has_read_aloud_true | 構造コンテナ内の heading は readAloud="true" | ImportError: cannot import name 'transform_structure_container' |
| test_heading_read_aloud_true_attribute_value | readAloud 属性の値は "true" 文字列 | ImportError |
| test_heading_in_nested_structure_has_read_aloud_true | 入れ子構造内の heading も readAloud='true' | ImportError |
| test_heading_read_aloud_xml_serialization | readAloud 属性が XML にシリアライズ | ImportError |
| test_heading_text_preserved_in_structure_container | heading テキストが保持される | ImportError |
| test_heading_unicode_text_with_read_aloud | Unicode テキストの heading | ImportError |
| test_multiple_headings_in_structure_container | 複数の heading が全て readAloud="true" | ImportError |
| test_heading_without_read_aloud_gets_false | read_aloud=False は readAloud="false" | ImportError |
| test_heading_read_aloud_mixed_values | 混在する read_aloud 値 | ImportError |

## 実装ヒント

### models.py (T024)

```python
# 追加が必要な dataclass
@dataclass(frozen=True)
class StructureContainer:
    """構造コンテナ（chapter, section, subsection）"""

    container_type: str  # "chapter", "section", "subsection"
    level: int  # 1-5
    number: str  # 章番号（空許容）
    title: str  # タイトル（ナビゲーション用）
    children: tuple  # StructureContainer or ContentElement のタプル
```

### transformer.py (T025, T027)

```python
# 追加が必要な関数
def transform_structure_container(container: StructureContainer) -> Element:
    """StructureContainer を XML 要素に変換

    - container_type="chapter" → <chapter number="N" title="...">
    - container_type="section" → <section number="N" title="...">
    - container_type="subsection" → <subsection level="N" number="..." title="...">
    - 子要素の heading は readAloud="true" または "false" を出力
    """
    ...
```

### xml_builder.py (T026)

```python
from xml.etree.ElementTree import Comment

# 追加が必要な関数
def generate_page_comment(page_number: int | str) -> Comment | None:
    """ページコメントを生成

    Args:
        page_number: ページ番号（整数または文字列）

    Returns:
        Comment: <!-- page N --> 形式のコメント
        None: page_number が空の場合
    """
    if not page_number:
        return None
    return Comment(f" page {page_number} ")

def insert_page_comment(element: Element, page_number: int | str) -> None:
    """要素の先頭にページコメントを挿入"""
    comment = generate_page_comment(page_number)
    if comment is not None:
        element.insert(0, comment)
```

## FAIL出力例

```
$ python -m pytest tests/book_converter/test_models.py::TestStructureContainer::test_structure_container_exists -v

FAILED tests/book_converter/test_models.py::TestStructureContainer::test_structure_container_exists
    ImportError: cannot import name 'StructureContainer' from 'src.book_converter.models'

$ python -m pytest tests/book_converter/test_transformer.py::TestTransformStructureContainer::test_transform_structure_container_exists -v

FAILED tests/book_converter/test_transformer.py::TestTransformStructureContainer::test_transform_structure_container_exists
    ImportError: cannot import name 'transform_structure_container' from 'src.book_converter.transformer'

$ python -m pytest tests/book_converter/test_xml_builder.py::TestPageCommentGeneration::test_generate_page_comment_exists -v

FAILED tests/book_converter/test_xml_builder.py::TestPageCommentGeneration::test_generate_page_comment_exists
    ImportError: cannot import name 'generate_page_comment' from 'src.book_converter.xml_builder'

$ python -m pytest tests/book_converter/test_transformer.py::TestHeadingReadAloudInStructureContainer::test_heading_in_structure_container_has_read_aloud_true -v

FAILED tests/book_converter/test_transformer.py::TestHeadingReadAloudInStructureContainer::test_heading_in_structure_container_has_read_aloud_true
    ImportError: cannot import name 'transform_structure_container' from 'src.book_converter.transformer'
```

## 次のステップ

phase-executor が Implementation (GREEN) を実行:

1. T030: RED出力確認 (このファイル)
2. T031: StructureContainer dataclass 追加 (models.py)
3. T032: Book.chapters (StructureContainer) 追加 (models.py)
4. T033: transform_structure_container 関数追加 (transformer.py)
5. T034: ページコメント生成関数追加 (xml_builder.py)
6. T035: build_xml を構造コンテナベースに改修 (xml_builder.py)
7. T036: parser で構造コンテナを構築 (parser.py)
8. T037: `make test` PASS 確認
