# Phase 4 テスト実装 (RED): User Story 3 - paragraph の論理的分離

**日付**: 2026-02-16
**ブランチ**: 009-converter-redesign

## サマリ

| 項目 | 値 |
|------|-----|
| フェーズ | Phase 4 (RED) |
| ユーザーストーリー | US3: paragraphの論理的分離 |
| FAILテスト数 | 33 |
| テストファイル | tests/book_converter/test_parser.py |

## FAILテスト一覧

### T042: TestParseParagraphRemoveNewlines (8テスト)

| テストファイル | テストメソッド | 期待動作 |
|---------------|----------------|----------|
| test_parser.py | test_parse_paragraph_remove_newlines_basic | 複数行を改行なしで結合 |
| test_parser.py | test_parse_paragraph_remove_newlines_japanese | 日本語段落の改行除去 |
| test_parser.py | test_parse_paragraph_remove_newlines_single_line | 1行段落はそのまま |
| test_parser.py | test_parse_paragraph_consecutive_spaces_compression | 連続空白を1つに圧縮 |
| test_parser.py | test_parse_paragraph_empty_list_returns_none | 空リストはNone |
| test_parser.py | test_parse_paragraph_whitespace_only_returns_none | 空白のみはNone |
| test_parser.py | test_parse_paragraph_preserves_content | Unicode内容を保持 |
| test_parser.py | test_parse_paragraph_read_aloud_default_true | read_aloud=True |

### T043: TestParagraphSplitByBlankLines (8テスト)

| テストファイル | テストメソッド | 期待動作 |
|---------------|----------------|----------|
| test_parser.py | test_split_paragraphs_by_blank_lines_basic | 空行で3段落に分離 |
| test_parser.py | test_split_paragraphs_multiple_blank_lines | 複数空行も1区切り |
| test_parser.py | test_split_paragraphs_single_paragraph | 空行なしは1段落 |
| test_parser.py | test_split_paragraphs_multiline_in_paragraph | 段落内改行は除去 |
| test_parser.py | test_split_paragraphs_empty_text | 空テキストは空リスト |
| test_parser.py | test_split_paragraphs_only_blank_lines | 空行のみは空リスト |
| test_parser.py | test_split_paragraphs_returns_paragraph_objects | Paragraphオブジェクト |
| test_parser.py | test_split_paragraphs_leading_trailing_blank_lines | 先頭末尾空行は無視 |

### T044: TestWhitespaceOnlyLineAsBlank (6テスト)

| テストファイル | テストメソッド | 期待動作 |
|---------------|----------------|----------|
| test_parser.py | test_space_only_line_as_blank | スペースのみは空行 |
| test_parser.py | test_tab_only_line_as_blank | タブのみは空行 |
| test_parser.py | test_mixed_whitespace_line_as_blank | 混在空白も空行 |
| test_parser.py | test_full_width_space_as_blank | 全角スペースも空行 |
| test_parser.py | test_consecutive_whitespace_lines | 連続空白行も1区切り |
| test_parser.py | test_whitespace_line_does_not_create_empty_paragraph | 空段落は生成しない |

### T045: TestParagraphContinuationAcrossPages (11テスト)

| テストファイル | テストメソッド | 期待動作 |
|---------------|----------------|----------|
| test_parser.py | test_continuation_basic | 句点なし段落は次と結合 |
| test_parser.py | test_no_continuation_with_period | 句点ありは結合しない |
| test_parser.py | test_continuation_multiple_paragraphs | 複数継続段落を結合 |
| test_parser.py | test_continuation_exclamation_mark | 感嘆符で終わると結合しない |
| test_parser.py | test_continuation_question_mark | 疑問符で終わると結合しない |
| test_parser.py | test_continuation_japanese_period | 日本語句点で結合しない |
| test_parser.py | test_continuation_closing_bracket_period | 閉じ括弧+句点で結合しない |
| test_parser.py | test_continuation_empty_list | 空リストは空リスト |
| test_parser.py | test_continuation_single_paragraph | 1段落はそのまま |
| test_parser.py | test_continuation_preserves_read_aloud | read_aloud属性保持 |
| test_parser.py | test_continuation_trailing_whitespace_period | 末尾空白+句点も結合しない |

## 実装ヒント

### T042: parse_paragraph_lines 関数

```python
def parse_paragraph_lines(lines: list[str]) -> Paragraph | None:
    """複数行を改行なしで結合してParagraphを生成

    Args:
        lines: 段落の行リスト

    Returns:
        Paragraph（改行除去済み）、空の場合はNone

    処理:
    1. 各行をstrip
    2. 空白1文字で結合
    3. 連続空白を1つに圧縮
    """
    pass
```

### T043-T044: split_paragraphs 関数

```python
def split_paragraphs(text: str) -> list[Paragraph]:
    """テキストを空行で分割してParagraphリストを生成

    Args:
        text: 複数段落を含むテキスト

    Returns:
        Paragraphのリスト

    処理:
    1. 空行（空白のみの行含む）で分割
    2. 各段落内の改行を除去
    3. 空の段落は除外
    """
    pass
```

### T045: merge_continuation_paragraphs 関数

```python
def merge_continuation_paragraphs(paragraphs: list[Paragraph]) -> list[Paragraph]:
    """句点で終わらない段落を次の段落と結合

    Args:
        paragraphs: Paragraphのリスト

    Returns:
        結合後のParagraphリスト

    終端文字（結合しない）:
    - 句点: 。.
    - 感嘆符: !！
    - 疑問符: ?？
    - 閉じ括弧+句点: ）。」。
    """
    pass
```

## FAIL出力例

```
============================= test session starts ==============================
platform linux -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0

tests/book_converter/test_parser.py::TestParseParagraphRemoveNewlines::test_parse_paragraph_remove_newlines_basic FAILED
tests/book_converter/test_parser.py::TestParseParagraphRemoveNewlines::test_parse_paragraph_remove_newlines_japanese FAILED
...

=================================== FAILURES ===================================
_ TestParseParagraphRemoveNewlines.test_parse_paragraph_remove_newlines_basic __

    def test_parse_paragraph_remove_newlines_basic(self) -> None:
        """複数行が改行なしで結合される"""
>       from src.book_converter.parser import parse_paragraph_lines
E       ImportError: cannot import name 'parse_paragraph_lines' from 'src.book_converter.parser'

tests/book_converter/test_parser.py:2774: ImportError

...

============================== 33 failed in 0.08s ==============================
```

## 次のステップ

1. **GREEN実装**:
   - `parse_paragraph_lines` 関数を `src/book_converter/parser.py` に追加
   - `split_paragraphs` 関数を追加
   - `merge_continuation_paragraphs` 関数を追加

2. **検証**:
   - `make test` で全33テストがPASSすることを確認
   - リグレッションがないことを確認
