# Phase 4: Test Implementation (RED) 結果

**日時**: 2026-02-07
**フェーズ**: Phase 4 Test Implementation (RED)
**ステータス**: 完了 (54テストFAIL = RED確認)

## サマリー

| 項目 | 値 |
|------|-----|
| Phase | 4 - User Story 3: TTS図表説明制御とメタデータ分離 |
| FAILテスト数 | 54 |
| PASSテスト数 | 147 (既存テストに影響なし) |
| テストファイル | test_parser.py, test_transformer.py |
| 対象機能 | Figure解析、PageMetadata解析、readAloud属性 |

## FAILテスト一覧

### test_parser.py (28テスト)

| テストクラス | テストメソッド | 期待動作 |
|-------------|---------------|----------|
| TestParseFigureComment | test_parse_figure_comment_basic | `<!-- FIGURE: path -->` パターン解析 |
| TestParseFigureComment | test_parse_figure_comment_with_spaces | スペース含む図コメント解析 |
| TestParseFigureComment | test_parse_figure_comment_with_japanese_path | 日本語パス解析 |
| TestParseFigureComment | test_parse_figure_comment_jpg_extension | JPG拡張子対応 |
| TestParseFigureComment | test_parse_figure_comment_case_insensitive | 大文字小文字無視 |
| TestParseFigureComment | test_parse_non_figure_comment_returns_none | 非図コメントでNone |
| TestParseFigureComment | test_parse_figure_comment_empty_path | 空パス処理 |
| TestParseFigureComment | test_parse_figure_comment_complex_path | 複雑なパス解析 |
| TestParseFigureDescription | test_parse_figure_with_description | 図+説明文解析 |
| TestParseFigureDescription | test_parse_figure_with_multiline_description | 複数行説明文 |
| TestParseFigureDescription | test_parse_figure_without_description | 説明文なし |
| TestParseFigureDescription | test_parse_figure_with_caption | キャプション付き |
| TestParseFigureDescription | test_parse_figure_returns_figure_type | Figure型返却 |
| TestParseFigureDescription | test_parse_figure_default_read_aloud | デフォルト'optional' |
| TestParseFigureDescription | test_parse_figure_empty_lines_returns_none | 空行でNone |
| TestParseFigureDescription | test_parse_figure_no_comment_returns_none | コメントなしでNone |
| TestParseFigureDescription | test_parse_figure_preserves_unicode_description | Unicode説明文保持 |
| TestParsePageMetadata | test_parse_page_metadata_simple | `N / M` 形式解析 |
| TestParsePageMetadata | test_parse_page_metadata_with_section_name | セクション名付き解析 |
| TestParsePageMetadata | test_parse_page_metadata_chapter_page_type | chapter-page判定 |
| TestParsePageMetadata | test_parse_page_metadata_section_page_type | section-page判定 |
| TestParsePageMetadata | test_parse_page_metadata_unknown_type | unknown判定 |
| TestParsePageMetadata | test_parse_page_metadata_invalid_format | 無効形式でNone |
| TestParsePageMetadata | test_parse_page_metadata_returns_type | PageMetadata型返却 |
| TestParsePageMetadata | test_parse_page_metadata_large_numbers | 大きな数値対応 |
| TestParsePageMetadata | test_parse_page_metadata_single_page | 単一ページ (1/1) |
| TestParsePageMetadata | test_parse_page_metadata_with_extra_spaces | 余分スペース許容 |
| TestParsePageMetadata | test_parse_page_metadata_preserves_original_text | 元テキスト保持 |

### test_transformer.py (26テスト)

| テストクラス | テストメソッド | 期待動作 |
|-------------|---------------|----------|
| TestTransformFigure | test_transform_figure_basic | 基本的な図XML変換 |
| TestTransformFigure | test_transform_figure_with_caption | キャプション変換 |
| TestTransformFigure | test_transform_figure_with_description | 説明文変換 |
| TestTransformFigure | test_transform_figure_read_aloud_optional | readAloud='optional' |
| TestTransformFigure | test_transform_figure_read_aloud_true | readAloud='true' |
| TestTransformFigure | test_transform_figure_read_aloud_false | readAloud='false' |
| TestTransformFigure | test_transform_figure_returns_element | Element型返却 |
| TestTransformFigure | test_transform_figure_full | 全属性変換 |
| TestTransformFigure | test_transform_figure_xml_serialization | XMLシリアライズ |
| TestTransformFigure | test_transform_figure_with_continued | continued属性 |
| TestTransformFigure | test_transform_figure_preserves_unicode | Unicode保持 |
| TestTransformPageMetadata | test_transform_page_metadata_basic | 基本メタデータ変換 |
| TestTransformPageMetadata | test_transform_page_metadata_section_page | section-page変換 |
| TestTransformPageMetadata | test_transform_page_metadata_unknown_type | unknown変換 |
| TestTransformPageMetadata | test_transform_page_metadata_returns_element | Element型返却 |
| TestTransformPageMetadata | test_transform_page_metadata_none_returns_none | NoneでNone |
| TestTransformPageMetadata | test_transform_page_metadata_with_section_name | セクション名変換 |
| TestTransformPageMetadata | test_transform_page_metadata_read_aloud_false | readAloud='false' |
| TestTransformPageMetadata | test_transform_page_metadata_xml_serialization | XMLシリアライズ |
| TestTransformPageMetadata | test_transform_page_metadata_preserves_original_text | 元テキスト保持 |
| TestReadAloudInheritance | test_figure_file_read_aloud_false | file要素readAloud='false' |
| TestReadAloudInheritance | test_figure_caption_read_aloud_true | caption要素readAloud='true' |
| TestReadAloudInheritance | test_figure_description_inherits_parent | description親継承 |
| TestReadAloudInheritance | test_figure_description_inherits_true | 親true時の継承 |
| TestReadAloudInheritance | test_figure_description_inherits_false | 親false時の継承 |
| TestReadAloudInheritance | test_page_metadata_always_read_aloud_false | pageMetadata常にfalse |

## 実装ヒント

### parse_figure_comment 関数 (parser.py)

```python
def parse_figure_comment(line: str) -> str | None:
    """図コメントからファイルパスを抽出

    Pattern: <!-- FIGURE: path -->
    大文字小文字無視、前後スペース許容
    """
    import re
    pattern = r'<!--\s*[Ff][Ii][Gg][Uu][Rr][Ee]:\s*(.+?)\s*-->'
    match = re.search(pattern, line)
    if match:
        path = match.group(1).strip()
        return path if path else None
    return None
```

### parse_figure 関数 (parser.py)

```python
def parse_figure(lines: list[str]) -> Figure | None:
    """図コメント + 説明文を解析してFigureを生成

    1. 最初の行から図コメントを探す
    2. 後続の行から説明文を抽出
    3. **太字**はキャプションとして処理
    """
    if not lines:
        return None

    # 図コメントを検索
    file_path = None
    for line in lines:
        file_path = parse_figure_comment(line)
        if file_path:
            break

    if not file_path:
        return None

    # 説明文・キャプション抽出
    caption = ""
    description_lines = []
    ...

    return Figure(
        file=file_path,
        caption=caption,
        description="\n".join(description_lines),
        read_aloud="optional",
    )
```

### parse_page_metadata 関数 (parser.py)

```python
def parse_page_metadata(text: str) -> PageMetadata | None:
    """ページメタデータを解析

    Pattern: [セクション名] N / M
    例: "はじめに 1 / 3", "3 / 7", "第1章 5 / 20"
    """
    import re
    pattern = r'^(.*?)\s*(\d+)\s*/\s*(\d+)\s*$'
    match = re.match(pattern, text.strip())
    if not match:
        return None

    section_name = match.group(1).strip()
    current = int(match.group(2))
    total = int(match.group(3))

    # type判定
    meta_type = "chapter-page"
    if "節" in section_name:
        meta_type = "section-page"

    return PageMetadata(
        text=text,
        meta_type=meta_type,
        section_name=section_name,
        current=current,
        total=total,
    )
```

### transform_figure 関数 (transformer.py)

```python
def transform_figure(figure: Figure) -> Element:
    """Figure → XML Element変換

    <figure readAloud="optional">
      <file readAloud="false">path</file>
      <caption readAloud="true">タイトル</caption>
      <description>説明文</description>
    </figure>
    """
    elem = Element("figure")
    elem.set("readAloud", figure.read_aloud)

    if figure.continued:
        elem.set("continued", "true")

    # file要素 (常にreadAloud="false")
    file_elem = Element("file")
    file_elem.text = figure.file
    file_elem.set("readAloud", "false")
    elem.append(file_elem)

    # caption要素 (readAloud="true")
    if figure.caption:
        caption_elem = Element("caption")
        caption_elem.text = figure.caption
        caption_elem.set("readAloud", "true")
        elem.append(caption_elem)

    # description要素 (親を継承)
    if figure.description:
        desc_elem = Element("description")
        desc_elem.text = figure.description
        elem.append(desc_elem)

    return elem
```

### transform_page_metadata 関数 (transformer.py)

```python
def transform_page_metadata(metadata: PageMetadata | None) -> Element | None:
    """PageMetadata → XML Element変換

    <pageMetadata type="chapter-page" readAloud="false">3 / 7</pageMetadata>
    """
    if metadata is None:
        return None

    elem = Element("pageMetadata")
    elem.set("type", metadata.meta_type)
    elem.set("readAloud", "false")  # 常にfalse
    elem.text = metadata.text

    return elem
```

## FAIL出力例

```
============================= test session starts ==============================
platform linux -- Python 3.13.11, pytest-9.0.2
collected 201 items

...
tests/book_converter/test_parser.py::TestParseFigureComment::test_parse_figure_comment_basic FAILED
tests/book_converter/test_parser.py::TestParseFigureDescription::test_parse_figure_with_description FAILED
tests/book_converter/test_parser.py::TestParsePageMetadata::test_parse_page_metadata_simple FAILED
tests/book_converter/test_transformer.py::TestTransformFigure::test_transform_figure_basic FAILED
tests/book_converter/test_transformer.py::TestTransformPageMetadata::test_transform_page_metadata_basic FAILED
tests/book_converter/test_transformer.py::TestReadAloudInheritance::test_figure_file_read_aloud_false FAILED
...

======================== 54 failed, 147 passed in 0.60s ========================
```

## エラーの種類

全てのテストが `ImportError` または `AttributeError` で失敗:
- `parse_figure_comment` が存在しない
- `parse_figure` が存在しない
- `parse_page_metadata` が存在しない
- `transform_figure` が存在しない
- `transform_page_metadata` が存在しない

これは期待通りの動作です（RED phase）。

## 次ステップ

Phase 4 Implementation (GREEN) で以下を実装:
1. `src/book_converter/parser.py`:
   - `parse_figure_comment(line: str) -> str | None`
   - `parse_figure(lines: list[str]) -> Figure | None`
   - `parse_page_metadata(text: str) -> PageMetadata | None`
2. `src/book_converter/transformer.py`:
   - `transform_figure(figure: Figure) -> Element`
   - `transform_page_metadata(metadata: PageMetadata | None) -> Element | None`
3. readAloud属性の正しい設定:
   - `<file>`: readAloud="false"
   - `<caption>`: readAloud="true"
   - `<description>`: 親継承
   - `<pageMetadata>`: readAloud="false"
