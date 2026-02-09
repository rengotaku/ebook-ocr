# Phase 3 テスト実装 (RED) - US2 ページ欠損の防止

## サマリー

| 項目 | 値 |
|------|-----|
| Phase | Phase 3: US2 - ページ欠損の防止 |
| 作成日 | 2026-02-10 |
| ステータス | RED (FAILテスト作成完了) |
| FAILテスト数 | 13 |
| PASSテスト数 | 657 (既存653 + 新規4) |
| テストファイル | tests/book_converter/test_page_grouper.py |

## FAILテスト一覧

### TestValidatePageCountNormal (T026) - 4テスト

| テストメソッド | 期待する動作 | 失敗理由 |
|---------------|-------------|---------|
| test_validate_all_pages_present | 10入力, 10出力 -> エラーなし | ImportError: validate_page_count関数が存在しない |
| test_validate_with_toc_pages | front-matter + chapter = total -> エラーなし | ImportError |
| test_validate_exact_match | 入力数 == 出力数 -> 正常 | ImportError |
| test_validate_minor_loss_no_error | 50%未満の欠損 -> エラーなし | ImportError |

### TestValidatePageCountError (T027) - 6テスト

| テストメソッド | 期待する動作 | 失敗理由 |
|---------------|-------------|---------|
| test_validate_50_percent_loss_raises_error | 10入力, 5出力 -> PageValidationError | ImportError: validate_page_count関数が存在しない |
| test_validate_over_50_percent_loss | 10入力, 4出力 -> エラー | ImportError |
| test_validate_49_percent_loss_no_error | 10入力, 6出力 -> エラーなし | ImportError |
| test_error_message_contains_counts | エラーメッセージに入力/出力数を含む | ImportError |
| test_validate_extreme_loss | 181入力, 10出力 (実バグシナリオ) -> エラー | ImportError |
| test_validate_zero_output_raises_error | 0出力 -> エラー | ImportError |

### TestGroupPagesPreservation (T028) - 4テスト (PASS)

| テストメソッド | 期待する動作 | 結果 |
|---------------|-------------|------|
| test_all_pages_in_output | 5ページ入力 -> 5ページ出力 | PASS |
| test_pages_not_duplicated | 各ページが1回だけ出現 | PASS |
| test_page_content_preserved | ページコンテンツが保持される | PASS |
| test_181_pages_input_181_output | 181ページ -> 181ページ | PASS |

注: TestGroupPagesPreservationは既存の実装で既にPASSしている。これはUS2の一部が既に実装済みであることを示す。

### TestGroupPagesEmptyToc (T029) - 3テスト

| テストメソッド | 期待する動作 | 失敗理由 |
|---------------|-------------|---------|
| test_empty_toc_all_to_front_matter | TOCエントリなし -> 全ページfront-matter | AssertionError: 3ページ期待、1ページのみ |
| test_no_toc_element_all_to_front_matter | `<toc>`要素なし -> 全ページ保持 | AssertionError: 2ページ期待、0ページ |
| test_front_matter_preserves_order | ページ順序保持 | AssertionError: ['1', '2', '3']期待、['1']のみ |

## 新規作成ファイル

### src/book_converter/errors.py

```python
class BookConverterError(Exception):
    """Base exception for book_converter module."""

class PageValidationError(BookConverterError):
    """Raised when page validation fails.

    Attributes:
        input_count: 入力ページ数
        output_count: 出力ページ数
        message: エラーメッセージ
    """
```

## 実装ヒント

### validate_page_count関数

```python
def validate_page_count(input_count: int, output_count: int) -> None:
    """出力ページ数を入力と比較して検証する。

    Args:
        input_count: 入力ページ数
        output_count: 出力ページ数

    Raises:
        PageValidationError: output_count < input_count * 0.5 の場合
    """
    # 実装が必要
```

### group_pages_by_toc修正ポイント

1. **TOCが空の場合**: 全ページをfront-matterに配置
2. **TOC要素がない場合**: 全ページを保持（現在は0ページが出力される）
3. **TOC以降のページ**: TOCにマッチしなくてもfront-matterまたは前のセクションに配置

## FAIL出力例

```
FAILED tests/book_converter/test_page_grouper.py::TestValidatePageCountNormal::test_validate_all_pages_present
    ImportError: cannot import name 'validate_page_count' from 'src.book_converter.page_grouper'

FAILED tests/book_converter/test_page_grouper.py::TestGroupPagesEmptyToc::test_empty_toc_all_to_front_matter
    AssertionError: All 3 pages should be in front-matter, found 1

FAILED tests/book_converter/test_page_grouper.py::TestGroupPagesEmptyToc::test_no_toc_element_all_to_front_matter
    AssertionError: All 2 pages should be preserved, found 0
```

## 次のステップ

Phase 3 Implementation (GREEN):
1. T032: このREDテスト結果を読む
2. T033: validate_page_count関数を実装 (src/book_converter/page_grouper.py)
3. T034: group_pages_by_tocを修正 - TOC空/なしの場合のページ保持
4. T035: group_pages_by_tocでvalidate_page_countを呼び出し
5. T036: `make test` PASS (GREEN) を確認
