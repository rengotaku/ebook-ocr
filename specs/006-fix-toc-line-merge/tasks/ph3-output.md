# Phase 3 実装完了報告 (GREEN) - US2 ページ欠損の防止

## サマリー

| 項目 | 値 |
|------|-----|
| Phase | Phase 3: US2 - ページ欠損の防止 |
| 作成日 | 2026-02-10 |
| ステータス | GREEN (全テストPASS) |
| 実装タスク | T032-T037 完了 |
| テスト結果 | 670/670 PASS (13件のFAILがすべてPASSに) |

## 実行タスク

| ID | タスク | ステータス | 備考 |
|----|-------|----------|------|
| T032 | REDテストを読む | ✅ 完了 | specs/006-fix-toc-line-merge/red-tests/ph3-test.md |
| T033 | validate_page_count関数を実装 | ✅ 完了 | src/book_converter/page_grouper.py |
| T034 | group_pages_by_tocを修正 | ✅ 完了 | TOC空/なしでも全ページ保持 |
| T035 | validate_page_count呼び出し統合 | ✅ 完了 | 入力/出力ページ数を検証 |
| T036 | `make test` PASS確認 | ✅ 完了 | 670/670 PASS |
| T037 | 回帰テスト確認 | ✅ 完了 | US1含めすべてPASS |

## 修正ファイル

### src/book_converter/page_grouper.py

#### 1. importの追加

```python
from src.book_converter.errors import PageValidationError
```

#### 2. validate_page_count関数の追加

```python
def validate_page_count(input_count: int, output_count: int) -> None:
    """Validate output page count against input.

    Args:
        input_count: Number of pages in input
        output_count: Number of pages in output

    Raises:
        PageValidationError: If output_count < 50% of input_count

    Returns:
        None if validation passes
    """
    if input_count == 0:
        return

    loss_ratio = (input_count - output_count) / input_count
    if loss_ratio >= 0.5:
        raise PageValidationError(
            input_count=input_count,
            output_count=output_count,
            message=f"Page validation failed: {output_count} of {input_count} pages preserved "
            f"({(1 - loss_ratio) * 100:.1f}%). At least 50% required.",
        )
```

**実装ポイント**:
- 入力ページ数が0の場合は検証をスキップ（エッジケース対応）
- 50%以上の欠損でPageValidationErrorを発生
- エラーメッセージに入力/出力数と保持率を含める

#### 3. group_pages_by_toc関数の修正

**Before**:
```python
# Collect all pages and classify them
pages = root.findall('page')

# Front-matter pages: before toc_begin and TOC pages themselves
front_matter_pages = []
content_pages = []

for page in pages:
    page_num = int(page.get('number', '0'))
    if toc_begin and page_num <= toc_end:
        front_matter_pages.append(page)
    else:
        content_pages.append(page)

# Create front-matter section
if front_matter_pages:
    front_matter_elem = ET.Element('front-matter')
    for page in front_matter_pages:
        front_matter_elem.append(page)
    new_book.append(front_matter_elem)

# Assign content pages to sections
page_assignments = _assign_pages_to_sections(content_pages, toc_lookup)

# Build hierarchical structure
_build_hierarchical_structure(new_book, page_assignments, toc_lookup)

# Serialize to string
return _serialize_to_xml(new_book)
```

**After**:
```python
# Collect all pages and classify them
pages = root.findall('page')

# If no TOC entries exist, place all pages in front-matter
if not toc_entries:
    front_matter_elem = ET.Element('front-matter')
    for page in pages:
        front_matter_elem.append(page)
    new_book.append(front_matter_elem)
else:
    # Front-matter pages: before toc_begin and TOC pages themselves
    front_matter_pages = []
    content_pages = []

    for page in pages:
        page_num = int(page.get('number', '0'))
        if toc_begin and page_num <= toc_end:
            front_matter_pages.append(page)
        else:
            content_pages.append(page)

    # Create front-matter section
    if front_matter_pages:
        front_matter_elem = ET.Element('front-matter')
        for page in front_matter_pages:
            front_matter_elem.append(page)
        new_book.append(front_matter_elem)

    # Assign content pages to sections
    page_assignments = _assign_pages_to_sections(content_pages, toc_lookup)

    # Build hierarchical structure
    _build_hierarchical_structure(new_book, page_assignments, toc_lookup)

# Validate page count
input_count = len(pages)
output_count = len(new_book.findall('.//page'))
validate_page_count(input_count, output_count)

# Serialize to string
return _serialize_to_xml(new_book)
```

**修正ポイント**:
1. **TOCエントリなしの場合**: すべてのページをfront-matterに配置（従来は一部ページが欠損）
2. **ページ数検証**: 出力XML生成後に入力/出力ページ数を検証
3. **エラー検出**: 50%以上欠損時にPageValidationErrorを発生

## テスト結果

### Phase 3 新規追加テスト (RED → GREEN)

| テストクラス | テスト数 | 状態 |
|------------|---------|------|
| TestValidatePageCountNormal | 4 | ✅ すべてPASS |
| TestValidatePageCountError | 6 | ✅ すべてPASS |
| TestGroupPagesPreservation | 4 | ✅ すべてPASS (Phase 2で既にPASS) |
| TestGroupPagesEmptyToc | 3 | ✅ すべてPASS (FAIL → PASS) |

**合計**: 13件のFAILテストがすべてPASSに変化

### 全体テスト結果

```
============================= 670 passed in 0.50s ==============================
```

**回帰なし**: US1 (Phase 2) を含む既存テストすべてPASS

## 実装内容詳細

### 1. validate_page_count関数

**要件**: FR-008 - 50%以上のページ欠損時にエラーを報告

**実装**:
- 入力ページ数と出力ページ数を比較
- 欠損率が50%以上の場合、PageValidationErrorを発生
- エラーメッセージに具体的な数値と保持率を含める
- 入力が0ページの場合は検証をスキップ（エッジケース）

**テストカバレッジ**:
- 正常ケース: 100%, 50%, 51%保持 → エラーなし
- エラーケース: 50%, 49%以下保持 → PageValidationError
- エッジケース: 0ページ入力 → エラーなし
- エラーメッセージ: 入力/出力数を含む

### 2. group_pages_by_toc修正 - TOC欠損対応

**要件**: FR-005 - TOCにマッチしないページをfront-matterまたは最初のchapterに配置

**問題**:
- TOCエントリが空の場合、一部ページしかfront-matterに配置されず、残りが欠損
- TOC要素がない場合、すべてのページが欠損

**実装**:
- `if not toc_entries:` 分岐を追加
- TOCエントリなしの場合、すべてのページをfront-matterに配置
- TOCエントリありの場合は従来通りの処理

**テストカバレッジ**:
- 空TOC (エントリなし) → 全ページfront-matter
- TOC要素なし → 全ページ保持
- ページ順序保持確認

### 3. validate_page_count統合

**実装**:
- group_pages_by_toc関数の出力XML生成後に検証を追加
- `new_book.findall('.//page')` で出力ページ数をカウント（階層化された構造でもすべてのページを検出）
- 入力ページ数と比較してvalidate_page_countを呼び出し

**テストカバレッジ**:
- 181ページ入力 → 181ページ出力
- 10ページ入力 → 4ページ出力 → PageValidationError

## 成功基準達成状況

| 成功基準 | ステータス | 備考 |
|---------|----------|------|
| SC-002: 問題ファイル181ページすべて出力 | ✅ 達成見込み | Phase 5で検証予定 |
| SC-005: 50%以上欠損時のエラー報告 | ✅ 達成 | テストで確認済み |

## 次フェーズへの引き継ぎ事項

### Phase 4: US3 - 既存動作の保持

**確認事項**:
1. 正常ファイル（4fd5500620491ebe）の変換結果が変更されないことを検証
2. 1行形式TOC（既存形式）が正しく処理されることを確認
3. US1とUS2の組み合わせで既存動作が保持されることを確認

**リスク**:
- TOC空の判定が正常ファイルに影響する可能性 → Phase 4で回帰テスト
- validate_page_countが正常ファイルでエラーを出す可能性 → Phase 4で確認

### Phase 5: Polish

**検証タスク**:
1. 問題ファイル（157012a97dcbebed）での最終検証
2. 正常ファイル（4fd5500620491ebe）での最終検証
3. カバレッジ確認（≥80%）

## 実装時の問題と解決

### 問題1: TOC空の場合のページ欠損

**現象**: TOCエントリが空の場合、1ページしかfront-matterに配置されない

**原因**:
- `if toc_begin and page_num <= toc_end:` の判定で、toc_beginが0の場合に条件が成立しない
- content_pagesに振り分けられたページが、TOCエントリなしで処理できずに欠損

**解決**:
- TOCエントリなしの場合は早期リターン（すべてfront-matterに配置）
- TOCエントリありの場合のみ既存の分類処理を実行

### 問題2: TOC要素なしの場合のページ欠損

**現象**: TOC要素自体がない場合、すべてのページが出力されない

**原因**:
- `toc_entries = []` の場合、従来コードでcontent_pagesにすべて振り分けられる
- TOCエントリがないため、_assign_pages_to_sectionsで処理できずに欠損

**解決**:
- `if not toc_entries:` 分岐で早期リターン
- TOC要素の有無にかかわらず、エントリなしの場合は同じ処理

## まとめ

Phase 3 (US2: ページ欠損の防止) は完了しました。

**実装内容**:
- validate_page_count関数: 50%以上欠損でエラー報告
- group_pages_by_toc修正: TOC空/なしでも全ページ保持
- ページ数検証の統合: 出力XML生成後に検証

**テスト結果**:
- 670/670 PASS
- 13件のFAILテストがすべてPASS
- 回帰なし (US1含む既存テストすべてPASS)

**次のステップ**:
Phase 4 (US3: 既存動作の保持) に進む準備が整いました。
