# Phase 3: Test Implementation (RED) 完了レポート

**日時**: 2026-02-07
**フェーズ**: Phase 3 Test Implementation (RED)
**ステータス**: 完了 (RED確認済み)

## サマリー

| 項目 | 値 |
|------|-----|
| Phase | 3 - User Story 2: TTSコンテンツ階層と構造解析 |
| 作成テスト数 | 38テスト (新規) |
| RED確認 | 38 FAILED |
| 既存テスト | 105 passed (リグレッションなし) |
| テストファイル | test_parser.py, test_transformer.py |

## FAILテスト一覧

### test_parser.py - パーサーテスト

| テストクラス | テストメソッド | 期待される動作 |
|-------------|---------------|---------------|
| TestParseHeading | test_parse_level_1_heading | # で始まる行をlevel=1の見出しとして解析 |
| TestParseHeading | test_parse_level_2_heading | ## で始まる行をlevel=2の見出しとして解析 |
| TestParseHeading | test_parse_level_3_heading | ### で始まる行をlevel=3の見出しとして解析 |
| TestParseHeading | test_parse_heading_with_extra_spaces | 見出しマーカーと本文間のスペースを許容 |
| TestParseHeading | test_parse_heading_returns_none_for_non_heading | 見出し以外の行はNoneを返す |
| TestParseHeading | test_parse_heading_preserves_unicode | Unicode文字を正しく保持 |
| TestParseHeading | test_parse_heading_with_special_characters | 特殊文字を含む見出しを解析 |
| TestParseHeading | test_parse_heading_empty_text | テキストなしの見出しマーカー |
| TestParseHeading | test_parse_heading_returns_heading_type | 戻り値はHeading型 |
| TestParseHeadingLevel4Warning | test_level_4_heading_becomes_level_3 | #### はlevel=3に変換 |
| TestParseHeadingLevel4Warning | test_level_5_heading_becomes_level_3 | ##### もlevel=3に変換 |
| TestParseHeadingLevel4Warning | test_level_6_heading_becomes_level_3 | ###### もlevel=3に変換 |
| TestParseHeadingLevel4Warning | test_parse_heading_with_warning_returns_warning | 4階層以上は警告情報を返す |
| TestParseHeadingLevel4Warning | test_parse_heading_with_warning_no_warning_for_level_3 | level 1-3では警告なし |
| TestParseParagraph | test_parse_single_line_paragraph | 1行の段落を解析 |
| TestParseParagraph | test_parse_multiline_paragraph | 複数行の段落を結合 |
| TestParseParagraph | test_parse_paragraph_returns_paragraph_type | 戻り値はParagraph型 |
| TestParseParagraph | test_parse_paragraph_empty_lines | 空行のリストはNoneを返す |
| TestParseParagraph | test_parse_paragraph_whitespace_only | 空白のみの行はNoneを返す |
| TestParseParagraph | test_parse_paragraph_preserves_unicode | Unicode文字を正しく保持 |
| TestParseParagraph | test_parse_paragraph_trims_trailing_whitespace | 末尾の空白を除去 |
| TestParseList | test_parse_list_with_dash | - で始まる項目をリストとして解析 |
| TestParseList | test_parse_list_with_asterisk | * で始まる項目をリストとして解析 |
| TestParseList | test_parse_list_mixed_markers | - と * が混在したリスト |
| TestParseList | test_parse_list_returns_list_type | 戻り値はList型 |
| TestParseList | test_parse_list_empty_returns_none | 空のリストはNoneを返す |
| TestParseList | test_parse_list_preserves_item_content | リスト項目の内容を保持 |
| TestParseList | test_parse_list_with_leading_spaces | インデント付きリストも解析可能 |
| TestParseList | test_parse_list_items_are_tuple | itemsはイミュータブルなタプル |

### test_transformer.py - トランスフォーマーテスト

| テストクラス | テストメソッド | 期待される動作 |
|-------------|---------------|---------------|
| TestTransformHeading | test_transform_heading_level_1 | level=1の見出しをXMLに変換 |
| TestTransformHeading | test_transform_heading_level_2 | level=2の見出しをXMLに変換 |
| TestTransformHeading | test_transform_heading_level_3 | level=3の見出しをXMLに変換 |
| TestTransformHeading | test_transform_heading_returns_element | 戻り値はElement型 |
| TestTransformHeading | test_transform_heading_preserves_unicode | Unicode文字を正しく保持 |
| TestTransformHeading | test_transform_heading_xml_serialization | XMLにシリアライズ可能 |
| TestTransformContentContinued | test_content_with_continued_true | continued=trueのコンテンツを変換 |
| TestTransformContentContinued | test_content_with_continued_false | continued=falseの場合は属性なし |
| TestTransformContentContinued | test_continued_paragraph_in_content | ページ跨ぎの段落をXMLで表現 |
| TestTransformContentContinued | test_continued_heading_spanning_pages | 見出しの後に続くページ |

## 実装ヒント

### parser.py に追加が必要な関数

#### parse_heading(line: str) -> Heading | None
```python
def parse_heading(line: str) -> Heading | None:
    """
    Markdownの見出し行を解析する。

    - # → level=1
    - ## → level=2
    - ### → level=3
    - #### 以上 → level=3 (警告を出す)

    Args:
        line: Markdown行

    Returns:
        Heading または None
    """
    # 実装: 正規表現で ^(#{1,6})\s*(.*)$ をマッチ
    pass
```

#### parse_heading_with_warning(line: str) -> tuple[Heading | None, str | None]
```python
def parse_heading_with_warning(line: str) -> tuple[Heading | None, str | None]:
    """
    見出し解析と警告を返す。

    4階層以上の場合は警告文字列を返す。
    """
    pass
```

#### parse_paragraph(lines: list[str]) -> Paragraph | None
```python
def parse_paragraph(lines: list[str]) -> Paragraph | None:
    """
    段落行リストをParagraphに変換。

    - 空行リスト → None
    - 空白のみ → None
    - 複数行 → 結合
    """
    pass
```

#### parse_list(lines: list[str]) -> List | None
```python
def parse_list(lines: list[str]) -> List | None:
    """
    リスト行をListに変換。

    - - または * で始まる行を項目として抽出
    - 項目テキストからマーカーを除去
    """
    pass
```

### transformer.py に追加が必要な関数

#### transform_heading(heading: Heading) -> Element
```python
def transform_heading(heading: Heading) -> Element:
    """
    HeadingをXML Elementに変換。

    <heading level="N">テキスト</heading>
    """
    pass
```

#### transform_content_with_continued(content: Content, continued: bool) -> Element | None
```python
def transform_content_with_continued(content: Content, continued: bool) -> Element | None:
    """
    Contentを変換し、continued属性を設定。

    continued=True の場合: <content continued="true">...</content>
    continued=False の場合: <content>...</content>
    """
    pass
```

## FAIL出力例

```
=================================== FAILURES ===================================
_________________ TestParseHeading.test_parse_level_1_heading __________________

self = <tests.book_converter.test_parser.TestParseHeading object at 0x...>

    def test_parse_level_1_heading(self) -> None:
        """# で始まる行をレベル1の見出しとして解析"""
>       from src.book_converter.parser import parse_heading
E       ImportError: cannot import name 'parse_heading' from 'src.book_converter.parser'

tests/book_converter/test_parser.py:222: ImportError
...

=========================== short test summary info ============================
FAILED tests/book_converter/test_parser.py::TestParseHeading::test_parse_level_1_heading
FAILED tests/book_converter/test_parser.py::TestParseHeading::test_parse_level_2_heading
... (38 failures total)
============================= 38 failed, 105 passed ==============================
```

## 次のステップ

1. **phase-executor** が Implementation (GREEN) を実行
2. `src/book_converter/parser.py` に以下を実装:
   - `parse_heading(line: str)`
   - `parse_heading_with_warning(line: str)`
   - `parse_paragraph(lines: list[str])`
   - `parse_list(lines: list[str])`
3. `src/book_converter/transformer.py` に以下を実装:
   - `transform_heading(heading: Heading)`
   - `transform_content_with_continued(content: Content, continued: bool)`
4. `make test` で全テストPASS (GREEN) を確認
5. Verificationで全テスト通過を確認
6. `specs/002-book-md-structure/tasks/ph3-output.md` を生成
