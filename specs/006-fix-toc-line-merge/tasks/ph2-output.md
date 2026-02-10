# Phase 2 Implementation (GREEN) 出力

## サマリー

| 項目 | 値 |
|------|-----|
| Phase | Phase 2: US1 - TOC改行分割エントリの結合 |
| 実装日 | 2026-02-10 |
| ステータス | 完了 (GREEN) |
| 総テスト数 | 653 |
| PASS数 | 653 (100%) |
| FAIL数 | 0 |
| カバレッジ | parser.py: 97%, 全体: 75% |

## 実装完了タスク

| タスクID | 説明 | ステータス |
|----------|------|------------|
| T016 | REDテスト読み込み | ✅ 完了 |
| T017 | normalize_toc_line拡張（**強調**除去） | ✅ 完了 |
| T018 | merge_toc_lines関数実装 | ✅ 完了 |
| T019 | parse_toc_entry拡張（Chapter N形式認識） | ✅ 完了 |
| T020 | _parse_single_page_contentでmerge_toc_lines統合 | ✅ 完了 |
| T021 | `make test` PASS確認 | ✅ 完了 |

## 修正ファイル一覧

### src/book_converter/parser.py

#### 1. normalize_toc_line関数の拡張

**変更内容**: `**`強調マーカーの除去機能を追加

```python
def normalize_toc_line(line: str) -> str:
    """Normalize TOC line by removing markdown prefixes and emphasis markers.

    Removes heading markers (###), list markers (-, *) from the beginning,
    and ** emphasis markers from anywhere in the line.
    """
    import re
    # Remove heading markers (###), list markers (-, *) from the beginning
    line = re.sub(r'^[#\-*]+\s*', '', line.strip())
    # Remove ** emphasis markers
    line = re.sub(r'\*\*', '', line)
    return line
```

**対応するREDテスト**: TestNormalizeTocLineEmphasis (6テスト)
- `**Episode 24**` → `Episode 24`
- `**Column**` → `Column`
- `**Chapter**` → `Chapter`
- 混在パターン: `**Episode 01** タイトル` → `Episode 01 タイトル`

#### 2. merge_toc_lines関数の新規実装

**変更内容**: 改行で分割されたTOC行を結合する新規関数

```python
def merge_toc_lines(lines: list[str]) -> list[str]:
    """Merge TOC lines that are split across multiple lines.

    Patterns to merge:
    - "Chapter" + "N Title" → "Chapter N Title"
    - "Episode NN" + "Title" → "Episode NN Title"
    - "Column" + "Title" → "Column Title"
    - "第N章" already complete, no merge needed

    Empty lines between entries do not prevent merging.
    """
```

**実装の特徴**:
- 3つの不完全パターンを検出（Chapter単独、Episode NN単独、Column単独）
- Chapter の場合、次行が数字で始まる場合のみ結合（バリデーション）
- Episode/Column の場合、次行が非空であれば結合
- 空行をスキップして次の非空行と結合可能

**対応するREDテスト**: TestMergeTocLinesChapter, TestMergeTocLinesEpisode, TestMergeTocLinesColumn, TestMergeTocLinesMixed (25テスト)

#### 3. parse_toc_entry関数の拡張

**変更内容**: "Chapter N タイトル" 形式の認識を追加

```python
# Chapter pattern 2: Chapter N タイトル (case insensitive)
chapter_en_pattern = r"^[Cc][Hh][Aa][Pp][Tt][Ee][Rr]\s+(\d+)(?:\s+(.+))?$"
match = re.match(chapter_en_pattern, line)
if match:
    title = match.group(2).strip() if match.group(2) else ""
    return TocEntry(
        text=title,
        level="chapter",
        number=match.group(1),
        page=page_number,
    )
```

**実装の特徴**:
- 大文字小文字を区別しない（CHAPTER, chapter, Chapter すべて対応）
- タイトル部分がオプション（`Chapter 1` のみでも認識）
- 既存の `第N章` パターンとの互換性を維持

**対応するREDテスト**: TestParseTocEntryChapterFormat (8テスト)

#### 4. _parse_single_page_content関数の統合

**変更内容**: TOC行の収集・マージ・パース処理を統合

**実装の流れ**:
1. TOC_START マーカー検出時: `toc_lines = []` で収集開始
2. TOC内部: 行を `toc_lines` に蓄積（即座にパースしない）
3. TOC_END マーカー検出時:
   - `merge_toc_lines(toc_lines)` で結合
   - 結合後の各行を `parse_toc_entry()` でパース
4. ページ終了時にTOCが未終了の場合も同様に処理（unclosed TOC対応）

**対応するREDテスト**: 全てのTOC関連テスト + E2Eテスト

## テスト結果

### 新規追加テスト（RED Phase）

35個の新規テストすべてが PASS:
- TestMergeTocLinesChapter: 6テスト
- TestMergeTocLinesEpisode: 6テスト
- TestMergeTocLinesColumn: 5テスト
- TestNormalizeTocLineEmphasis: 6テスト
- TestParseTocEntryChapterFormat: 8テスト
- TestMergeTocLinesMixed: 4テスト

### 既存テスト

618個の既存テストすべてが PASS（回帰なし）

### カバレッジ

- `src/book_converter/parser.py`: 97% (457行中13行未カバー)
- `src/book_converter/`: 全モジュール平均 95%
- プロジェクト全体: 75% (OCR/pipeline部分が未カバーのため)

## 実装のポイント

### 1. バリデーション戦略

**Chapter結合のバリデーション**:
```python
if merge_pattern == 'chapter':
    # For Chapter, next line should start with a digit (N Title format)
    should_merge = bool(re.match(r'^\d+\s+', next_line))
```

これにより、以下のケースを正しく処理:
- ✅ `Chapter` + `1 「企画」で失敗` → 結合
- ❌ `Chapter` + `おわりに ... 300` → 結合しない（数字で始まらない）

### 2. 空行の扱い

空行を挟んでも結合可能:
```python
while next_idx < len(lines):
    candidate = lines[next_idx].strip()
    if candidate:
        next_line = candidate
        break
    next_idx += 1
```

### 3. Unclosed TOC対応

ページ終了時に未終了TOCの処理:
```python
# If TOC is still open at end of page, process collected lines
if in_toc and toc_lines:
    merged_toc_lines = merge_toc_lines(toc_lines)
    for merged_line in merged_toc_lines:
        toc_entry = parse_toc_entry(merged_line)
        if toc_entry is not None:
            toc_entries.append(toc_entry)
```

### 4. 大文字小文字の対応

正規表現で大文字小文字を明示的に列挙:
```python
r'^[Cc][Hh][Aa][Pp][Tt][Ee][Rr]$'  # CHAPTER, chapter, Chapter すべて対応
```

## 実装時の課題と解決

### 課題1: test_chapter_standalone_not_followed_by_valid_line失敗

**問題**: `Chapter` + `おわりに ... 300` を結合してしまう

**解決**: Chapter結合時に次行が数字で始まることをバリデーション

### 課題2: test_unclosed_toc_marker失敗

**問題**: TOCマーカーが閉じられていない場合、TOC行が処理されない

**解決**: ページ終了時に `in_toc` フラグをチェックし、未処理のTOC行を処理

## 次フェーズへの引き継ぎ事項

### Phase 3 (US2: ページ欠損の防止) への準備完了

**現在の実装状態**:
- ✅ TOC行の結合機能が完全動作
- ✅ 既存テストの回帰なし
- ✅ Chapter/Episode/Column形式の認識完了

**Phase 3で実装すべき内容**:
- `validate_page_count` 関数（ページ欠損検出）
- `group_pages_by_toc` の修正（全ページ保持）
- 50%欠損時のエラー報告

**想定される課題**:
- 問題ファイル（157012a97dcbebed）での実際のページ欠損数の確認
- TOC構造が不完全な場合のページ配置戦略

## 検証コマンド

```bash
# すべてのテスト実行
make test

# カバレッジ付きテスト実行
make test-cov

# book_converterモジュールのみテスト
make test-book-converter
```

## ファイルパス

- 実装: `/data/projects/video-separater/src/book_converter/parser.py`
- テスト: `/data/projects/video-separater/tests/book_converter/test_parser.py`
- タスク: `/data/projects/video-separater/specs/006-fix-toc-line-merge/tasks.md`
