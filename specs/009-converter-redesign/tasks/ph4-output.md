# Phase 4 Output: User Story 3 - paragraph の論理的分離（GREEN フェーズ）

**Date**: 2026-02-16
**Branch**: 009-converter-redesign

## サマリ

| 項目 | 値 |
|------|-----|
| フェーズ | Phase 4 (GREEN) |
| タスク完了 | 7/7 (100%) |
| ステータス | 完了 |
| 実装ファイル | 1 |
| 新規関数 | 3 |

## 完了タスク

- [x] T048: REDテスト確認
- [x] T049: parse_paragraph_lines 関数実装
- [x] T050: split_paragraphs 関数実装
- [x] T051: merge_continuation_paragraphs 関数実装
- [x] T052: Phase 4 REDテスト PASS 確認
- [x] T053: リグレッション確認
- [x] T054: フェーズ出力生成

## 変更ファイル

### プロダクションコード

| ファイル | 変更内容 | 行数変更 |
|----------|---------|----------|
| src/book_converter/parser.py | 新規関数3つ追加 | +100/-0 |

### 実装した関数

#### 1. parse_paragraph_lines

複数行を改行なしで結合してParagraphを生成する関数。

```python
def parse_paragraph_lines(lines: list[str]) -> Paragraph | None:
    """複数行を改行なしで結合してParagraphを生成

    処理:
    1. 各行をstrip
    2. 空白1文字で結合
    3. 連続空白を1つに圧縮
    """
```

**特徴**:
- 改行を空白に置換
- 連続空白を単一空白に圧縮
- 空行または空白のみの場合はNone返却

#### 2. split_paragraphs

テキストを空行で分割してParagraphリストを生成する関数。

```python
def split_paragraphs(text: str) -> list[Paragraph]:
    """テキストを空行で分割してParagraphリストを生成

    処理:
    1. 空行（空白のみの行含む）で分割
    2. 各段落内の改行を除去
    3. 空の段落は除外
    """
```

**特徴**:
- 空行（\n\n）で段落分離
- スペースのみ/タブのみ/全角スペースのみの行も空行として扱う
- 各段落は parse_paragraph_lines で処理（改行除去）

#### 3. merge_continuation_paragraphs

句点で終わらない段落を次の段落と結合する関数。

```python
def merge_continuation_paragraphs(paragraphs: list[Paragraph]) -> list[Paragraph]:
    """句点で終わらない段落を次の段落と結合

    終端文字（結合しない）:
    - 句点: 。.
    - 感嘆符: !！
    - 疑問符: ?？
    - 閉じ括弧+句点: ）。」。
    """
```

**特徴**:
- 終端文字で終わる段落は次と結合しない
- 終端文字で終わらない段落は次の段落と結合
- 日本語テキストのため、結合時に空白を挿入しない
- 複数の継続段落を順次結合

## テスト結果

### Phase 4 REDテスト: 33/33 PASS

すべてのテストがPASS:
- TestParseParagraphRemoveNewlines: 8/8 PASS
- TestParagraphSplitByBlankLines: 8/8 PASS
- TestWhitespaceOnlyLineAsBlank: 6/6 PASS
- TestParagraphContinuationAcrossPages: 11/11 PASS

**合計**: 33 PASS

### リグレッション

Phase 2, 3 のテストもすべて通過:
- Phase 2 (US1): TocEntry.level int化 - すべてPASS
- Phase 3 (US2): StructureContainer, ページコメント - すべてPASS

既知の問題（Phase 2の破壊的変更による）:
- 既存テスト59件が失敗（TocEntry.level が str から int に変更されたため）
- これは Phase 2 で記録された既知の問題

## 実装の詳細

### T049: parse_paragraph_lines 実装

既存の `parse_paragraph` 関数は改行を保持していましたが、新しい `parse_paragraph_lines` 関数は改行を除去します。

```python
# 既存 parse_paragraph (改行保持)
text = "\n".join(lines).strip()

# 新規 parse_paragraph_lines (改行除去)
text = " ".join(line.strip() for line in lines)
text = re.sub(r'\s+', ' ', text).strip()
```

**理由**: paragraph内の改行はレイアウトの都合であり、論理的な意味を持たないため。

### T050: split_paragraphs 実装

空行検出ロジック:

```python
for line in text.split('\n'):
    if not line.strip():  # 空白のみの行も空行として扱う
        # 現在の段落を保存
        if current_lines:
            para = parse_paragraph_lines(current_lines)
            if para is not None:
                paragraphs.append(para)
            current_lines = []
    else:
        current_lines.append(line)
```

**特徴**:
- `line.strip()` により、スペース/タブ/全角スペースのみの行を空行として検出
- 空の段落（空白のみ）は除外

### T051: merge_continuation_paragraphs 実装

終端文字チェック:

```python
terminating_chars = {'。', '.', '!', '！', '?', '？'}

if current_text:
    last_char = current_text[-1]
    if last_char in terminating_chars:
        ends_with_terminator = True
    # 閉じ括弧+句点パターン: ）。 」。
    elif len(current_text) >= 2:
        last_two = current_text[-2:]
        if last_two in {'）。', '」。'}:
            ends_with_terminator = True
```

結合ロジック:

```python
# 日本語テキストのため、空白なしで結合
merged_text = f"{current_text}{next_para.text}".strip()
```

**設計判断**: 日本語テキストでは単語間に空白が不要なため、結合時に空白を挿入しない。

## 実装上の注意点

### immutability維持

- すべての関数は新しいParagraphオブジェクトを生成
- 入力の paragraphs リストを直接変更せず、新しいリストを返却

### 日本語テキスト対応

- 空白のみの行検出: 全角スペース（　）も対応
- 段落結合: 空白なしで結合（日本語の自然な表記）

### エッジケース処理

- 空リスト入力 → 空リスト返却
- 空白のみの段落 → 除外（None返却）
- 単一段落 → そのまま返却（結合不要）

## 次フェーズへの引継ぎ事項

### Phase 5へのインプット

Phase 5 (User Story 4) では list/figure 要素の出力を実装:

1. **List.list_type 属性追加**
   - unordered ("ul") / ordered ("ol") を識別

2. **Figure.path, marker 属性追加**
   - file → path にリネーム
   - marker 追加（元のプレースホルダー保持）

3. **図プレースホルダー検出**
   - [図], [写真], [表] 等のパターン検出

### 残存課題

1. **parserロジック未統合**
   - `parse_paragraph_lines`, `split_paragraphs`, `merge_continuation_paragraphs` は独立した関数として実装
   - 既存の `_parse_single_page_content` への統合は Phase 5 以降で検討

2. **既存 parse_paragraph との共存**
   - 既存の `parse_paragraph` 関数（改行保持）と新規 `parse_paragraph_lines` 関数（改行除去）が共存
   - 後方互換性のため既存関数は削除していない

3. **既存テストの更新**
   - Phase 2の破壊的変更（TocEntry.level型変更）に対応するテスト更新が未完了
   - 59件のテスト失敗が残存（既知の問題）

## 検証

```bash
# Phase 4 REDテスト全PASS確認
python -m pytest tests/book_converter/test_parser.py::TestParseParagraphRemoveNewlines -v
python -m pytest tests/book_converter/test_parser.py::TestParagraphSplitByBlankLines -v
python -m pytest tests/book_converter/test_parser.py::TestWhitespaceOnlyLineAsBlank -v
python -m pytest tests/book_converter/test_parser.py::TestParagraphContinuationAcrossPages -v

# Phase 2, 3 テスト確認（リグレッションなし）
python -m pytest tests/book_converter/test_models.py::TestTocEntryLevelInt -v
python -m pytest tests/book_converter/test_models.py::TestStructureContainer -v
python -m pytest tests/book_converter/test_transformer.py::TestTransformStructureContainer -v
python -m pytest tests/book_converter/test_xml_builder.py::TestPageCommentGeneration -v
```

## ステータス

**Phase 4 完了** - User Story 3 (paragraph の論理的分離) の実装が完了。すべてのREDテストがPASSし、リグレッションなし。
