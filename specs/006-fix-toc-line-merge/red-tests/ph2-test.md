# Phase 2 Test Implementation (RED) 出力

## サマリー

| 項目 | 値 |
|------|-----|
| Phase | Phase 2: US1 - TOC改行分割エントリの結合 |
| 作成日 | 2026-02-10 |
| FAILテスト数 | 35 |
| テストファイル | tests/book_converter/test_parser.py |

## FAILテスト一覧

### TestMergeTocLinesChapter (T009)

| テストメソッド | 期待される動作 | 失敗理由 |
|----------------|----------------|----------|
| test_merge_chapter_with_number_title | 「Chapter」+「1 「企画」で失敗」を結合 | ImportError: merge_toc_lines関数が存在しない |
| test_merge_chapter_with_number_title_2 | 「Chapter」+「2 「仕様」で失敗」を結合 | ImportError |
| test_merge_multiple_chapters_in_sequence | 複数Chapterを順番に結合 | ImportError |
| test_merge_chapter_with_empty_line_between | 空行を挟んでも結合 | ImportError |
| test_chapter_standalone_not_followed_by_valid_line | 無効な次行は結合しない | ImportError |
| test_merge_chapter_preserves_unicode | Unicode保持 | ImportError |

### TestMergeTocLinesEpisode (T010)

| テストメソッド | 期待される動作 | 失敗理由 |
|----------------|----------------|----------|
| test_merge_episode_with_title | 「Episode 01」+タイトルを結合 | ImportError: merge_toc_lines関数が存在しない |
| test_merge_episode_02_with_title | 「Episode 02」+タイトルを結合 | ImportError |
| test_merge_multiple_episodes_in_sequence | 複数Episodeを順番に結合 | ImportError |
| test_merge_episode_with_multiword_title | 複数単語タイトル結合 | ImportError |
| test_episode_without_number_not_merged | 番号なしは結合しない | ImportError |
| test_merge_episode_preserves_page_number | ページ番号保持 | ImportError |

### TestMergeTocLinesColumn (T011)

| テストメソッド | 期待される動作 | 失敗理由 |
|----------------|----------------|----------|
| test_merge_column_with_title | 「Column」+タイトルを結合 | ImportError: merge_toc_lines関数が存在しない |
| test_merge_column_with_page_number | ページ番号付き結合 | ImportError |
| test_merge_multiple_columns_in_sequence | 複数Columnを順番に結合 | ImportError |
| test_merge_column_with_empty_line_between | 空行を挟んでも結合 | ImportError |
| test_column_preserves_special_characters | 特殊文字保持 | ImportError |

### TestNormalizeTocLineEmphasis (T012)

| テストメソッド | 期待される動作 | 失敗理由 |
|----------------|----------------|----------|
| test_normalize_removes_emphasis_episode | `**Episode 24**` → `Episode 24` | AssertionError: **が除去されない |
| test_normalize_removes_emphasis_column | `**Column**` → `Column` | AssertionError |
| test_normalize_removes_emphasis_chapter | `**Chapter**` → `Chapter` | AssertionError |
| test_normalize_mixed_emphasis_and_text | `**Episode 01** タイトル` → `Episode 01 タイトル` | AssertionError |
| test_normalize_multiple_emphasis_blocks | 複数の**ブロック**を除去 | AssertionError |
| test_normalize_removes_heading_markers_and_emphasis | `### **Episode 24**` → `Episode 24` | AssertionError |

### TestParseTocEntryChapterFormat (T013)

| テストメソッド | 期待される動作 | 失敗理由 |
|----------------|----------------|----------|
| test_parse_chapter_n_format | 「Chapter 1 タイトル」をchapterとして認識 | AssertionError: level='other'を返す |
| test_parse_chapter_10_format | 「Chapter 10 まとめ」を認識（2桁） | AssertionError |
| test_parse_chapter_with_page_number_dots | ページ番号（...形式）を抽出 | AssertionError |
| test_parse_chapter_with_page_number_dashes | ページ番号（---形式）を抽出 | AssertionError |
| test_parse_chapter_case_insensitive | 大文字「CHAPTER」も認識 | AssertionError |
| test_parse_chapter_lowercase | 小文字「chapter」も認識 | AssertionError |
| test_parse_chapter_preserves_unicode_title | Unicodeタイトル保持 | AssertionError |
| test_parse_chapter_without_title | 「Chapter 1」のみ（タイトルなし） | AssertionError |

### TestMergeTocLinesMixed（混合テスト）

| テストメソッド | 期待される動作 | 失敗理由 |
|----------------|----------------|----------|
| test_merge_mixed_entries | Chapter/Episode/Column混在結合 | ImportError |
| test_merge_preserves_non_mergeable_lines | 結合対象外行を保持 | ImportError |
| test_merge_empty_list | 空リストは空リストを返す | ImportError |
| test_merge_single_non_mergeable_line | 単一の結合不要行 | ImportError |

## 実装ヒント

### 1. merge_toc_lines関数の新規実装

```python
def merge_toc_lines(lines: list[str]) -> list[str]:
    """TOC行の結合を行う

    結合パターン:
    - 「Chapter」単独行 + 次行「N タイトル」 → 「Chapter N タイトル」
    - 「Episode NN」行 + 次行「タイトル」 → 「Episode NN タイトル」
    - 「Column」単独行 + 次行「タイトル」 → 「Column タイトル」

    空行は結合を妨げない（スキップして次の非空行と結合）
    """
    pass
```

### 2. normalize_toc_line関数の拡張

現在の実装:
```python
def normalize_toc_line(line: str) -> str:
    import re
    return re.sub(r'^[#\-*]+\s*', '', line.strip())
```

追加すべき処理:
- `**text**` → `text` (強調記号の除去)

### 3. parse_toc_entry関数の拡張

現在のパターン:
- `第N章 タイトル` → level="chapter"
- `N.N タイトル` → level="section"
- `N.N.N タイトル` → level="subsection"

追加すべきパターン:
- `Chapter N タイトル` → level="chapter", number="N"
- 大文字小文字を区別しない (CHAPTER, chapter, Chapter)

## FAIL出力例

```
FAILED tests/book_converter/test_parser.py::TestMergeTocLinesChapter::test_merge_chapter_with_number_title
E       ImportError: cannot import name 'merge_toc_lines' from 'src.book_converter.parser'

FAILED tests/book_converter/test_parser.py::TestNormalizeTocLineEmphasis::test_normalize_removes_emphasis_episode
E       AssertionError: assert '**Episode 24**' == 'Episode 24'
E         - Episode 24
E         + **Episode 24**

FAILED tests/book_converter/test_parser.py::TestParseTocEntryChapterFormat::test_parse_chapter_n_format
E       AssertionError: assert 'other' == 'chapter'
E         - chapter
E         + other
```

## 次のステップ

Phase 2 Implementation (GREEN):
1. T016: このREDテストを読む
2. T017: normalize_toc_lineを拡張（**強調**除去）
3. T018: merge_toc_lines関数を新規実装
4. T019: parse_toc_entryを拡張（Chapter N形式）
5. T020: _parse_single_page_contentでmerge_toc_linesを呼び出し
6. T021: `make test` PASS (GREEN) を確認
