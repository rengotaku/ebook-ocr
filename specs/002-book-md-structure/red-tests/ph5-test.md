# Phase 5: Test Implementation (RED) 完了レポート

**日時**: 2026-02-07
**フェーズ**: Phase 5 Test Implementation (RED)
**ステータス**: FAIL確認済み (RED)

## サマリー

| 項目 | 値 |
|------|-----|
| Phase | 5 - CLI & エラーハンドリング |
| 作成テスト数 | 64テスト |
| FAIL確認 | 64 failed, 202 passed |
| 作成ファイル | test_cli.py, test_e2e.py, test_parser.py (追加) |

## FAILテスト一覧

### tests/book_converter/test_cli.py (27テスト)

| テストクラス | テストメソッド | 期待される動作 |
|-------------|---------------|---------------|
| TestCLIArguments | test_cli_main_exists | main関数が存在する |
| TestCLIArguments | test_cli_parse_args_exists | parse_args関数が存在する |
| TestCLIArguments | test_cli_requires_input_file | 入力ファイルは必須引数 |
| TestCLIArguments | test_cli_requires_output_file | 出力ファイルは必須引数 |
| TestCLIArguments | test_cli_accepts_input_and_output | 入力と出力ファイルを受け付ける |
| TestCLIArguments | test_cli_verbose_flag | --verbose フラグを受け付ける |
| TestCLIArguments | test_cli_verbose_short_flag | -v フラグを受け付ける |
| TestCLIArguments | test_cli_quiet_flag | --quiet フラグを受け付ける |
| TestCLIArguments | test_cli_quiet_short_flag | -q フラグを受け付ける |
| TestCLIArguments | test_cli_verbose_and_quiet_mutually_exclusive | --verbose と --quiet は同時に指定不可 |
| TestCLIArguments | test_cli_default_not_verbose | デフォルトでverboseはFalse |
| TestCLIArguments | test_cli_default_not_quiet | デフォルトでquietはFalse |
| TestCLIExecution | test_cli_returns_zero_on_success | 成功時は終了コード0 |
| TestCLIExecution | test_cli_returns_nonzero_on_file_not_found | ファイル未発見時は非ゼロ |
| TestCLIExecution | test_cli_creates_output_file | 出力ファイルを生成 |
| TestCLIExecution | test_cli_verbose_outputs_progress | --verbose時に進捗出力 |
| TestCLIExecution | test_cli_quiet_suppresses_output | --quiet時は出力抑制 |
| TestCLIConversionResult | test_cli_outputs_summary_on_completion | 完了時にサマリー出力 |
| TestErrorRateWarning | test_warning_when_error_rate_exceeds_10_percent | エラー率10%超過時に警告 |
| TestErrorRateWarning | test_no_warning_when_error_rate_below_10_percent | エラー率10%以下では警告なし |
| TestErrorRateWarning | test_error_count_displayed_in_summary | サマリーにエラー数表示 |
| TestErrorRateWarning | test_error_summary_at_end | 最後にエラーサマリー表示 |
| TestCLIConvertFunction | test_convert_book_function_exists | convert_book関数が存在 |
| TestCLIConvertFunction | test_convert_book_returns_result | ConversionResultを返す |
| TestCLIConvertFunction | test_convert_book_result_has_total_pages | total_pagesを含む |
| TestCLIConvertFunction | test_convert_book_result_has_error_count | error_countを含む |
| TestCLIConvertFunction | test_convert_book_result_has_errors_list | errorsリストを含む |

### tests/book_converter/test_e2e.py (21テスト)

| テストクラス | テストメソッド | 期待される動作 |
|-------------|---------------|---------------|
| TestE2EConversion | test_convert_sample_book | sample_book.mdを変換できる |
| TestE2EConversion | test_output_is_valid_xml | 出力が有効なXML |
| TestE2EConversion | test_output_has_book_root_element | book要素がある |
| TestE2EConversion | test_output_has_metadata | metadataがある |
| TestE2EConversion | test_output_has_pages | ページがある |
| TestE2EConversion | test_output_page_count_matches_input | ページ数が入力と一致 |
| TestE2EConversion | test_pages_have_number_attribute | ページにnumber属性 |
| TestE2EConversion | test_pages_have_source_file_attribute | ページにsourceFile属性 |
| TestE2EConversion | test_pages_have_page_announcement | pageAnnouncementがある |
| TestE2EConversion | test_xpath_query_for_page | XPathでページ検索可能 |
| TestE2EConversion | test_xpath_query_for_heading | XPathで見出し検索可能 |
| TestE2EComparison | test_output_matches_expected_page_count | 期待値とページ数一致 |
| TestE2EComparison | test_output_matches_expected_page_numbers | 期待値とページ番号一致 |
| TestE2EComparison | test_output_matches_expected_source_files | 期待値とソースファイル一致 |
| TestE2EComparison | test_output_matches_expected_headings | 期待値と見出し一致 |
| TestE2EComparison | test_output_contains_figures | 図が含まれる |
| TestE2EComparison | test_output_contains_page_metadata | ページメタデータが含まれる |
| TestE2EEdgeCases | test_empty_file | 空ファイルを処理 |
| TestE2EEdgeCases | test_single_page | 1ページのファイル処理 |
| TestE2EEdgeCases | test_unicode_content | Unicode文字を処理 |
| TestE2EEdgeCases | test_many_pages | 多くのページを処理 |
| TestE2EEdgeCases | test_deep_heading_warning_in_output | 4階層見出し警告出力 |

### tests/book_converter/test_parser.py (16テスト追加)

| テストクラス | テストメソッド | 期待される動作 |
|-------------|---------------|---------------|
| TestErrorHandlingContinueOnWarning | test_parse_pages_continues_on_missing_page_number | 欠落時も解析継続 |
| TestErrorHandlingContinueOnWarning | test_parse_pages_continues_on_invalid_heading | 不正見出しでも継続 |
| TestErrorHandlingContinueOnWarning | test_parse_pages_records_error_for_missing_number | 欠落エラー記録 |
| TestErrorHandlingContinueOnWarning | test_parse_pages_records_error_for_deep_heading | 深い見出しエラー記録 |
| TestErrorHandlingContinueOnWarning | test_error_contains_line_number | 行番号を含む |
| TestErrorHandlingXMLComment | test_xml_contains_error_comment_for_missing_number | 欠落時XMLコメント |
| TestErrorHandlingXMLComment | test_xml_contains_error_type | エラータイプを含む |
| TestErrorHandlingXMLComment | test_xml_comment_format | XMLコメント形式確認 |
| TestErrorHandlingXMLComment | test_xml_contains_error_comment_for_deep_heading | 深い見出しコメント |
| TestErrorHandlingParseWithErrors | test_function_exists | parse_pages_with_errors存在 |
| TestErrorHandlingParseWithErrors | test_returns_tuple_of_pages_and_errors | タプルを返す |
| TestErrorHandlingParseWithErrors | test_pages_are_list | ページはリスト |
| TestErrorHandlingParseWithErrors | test_errors_are_list | エラーはリスト |
| TestErrorHandlingParseWithErrors | test_no_errors_for_valid_input | 有効入力ではエラーなし |
| TestErrorHandlingParseWithErrors | test_multiple_errors_collected | 複数エラー収集 |

## 実装ヒント

### T070: CLI引数テスト

`src/book_converter/cli.py` に以下を実装:

```python
import argparse
from pathlib import Path
from src.book_converter.models import ConversionResult

def parse_args(args: list[str] | None = None) -> argparse.Namespace:
    """CLI引数をパース"""
    parser = argparse.ArgumentParser(
        description="Convert book.md to book.xml"
    )
    parser.add_argument("input", help="Input markdown file")
    parser.add_argument("output", help="Output XML file")

    # Mutually exclusive group
    group = parser.add_mutually_exclusive_group()
    group.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    group.add_argument("-q", "--quiet", action="store_true", help="Quiet mode")

    return parser.parse_args(args)

def convert_book(input_path: Path, output_path: Path) -> ConversionResult:
    """書籍を変換してConversionResultを返す"""
    # 実装
    pass

def main(args: list[str] | None = None) -> int:
    """CLIエントリーポイント"""
    parsed = parse_args(args)
    # 実装
    return 0
```

### T071: エラーハンドリングテスト

`src/book_converter/parser.py` に以下を追加:

```python
from src.book_converter.models import ConversionError

def parse_pages_with_errors(
    input_path: Path
) -> tuple[list[Page], list[ConversionError]]:
    """エラー情報を含めてページをパース"""
    pages = []
    errors = []
    # 実装
    return (pages, errors)
```

`src/book_converter/xml_builder.py` に以下を追加:

```python
def insert_error_comment(element: Element, error: ConversionError) -> None:
    """XMLコメントとしてエラーを挿入"""
    # <!-- ERROR: [type] - [message] --> 形式
    pass
```

### T072: E2Eテスト

`convert_book` 関数で以下を統合:
1. `parse_pages_with_errors` でパース
2. `transform_page` で変換
3. `build_xml` でXML生成
4. ファイル書き込み

### T073: エラー率警告テスト

```python
def main(args: list[str] | None = None) -> int:
    # ...
    result = convert_book(input_path, output_path)

    # エラー率チェック
    if result.total_pages > 0:
        error_rate = result.error_count / result.total_pages
        if error_rate > 0.10:  # 10%超過
            print(f"警告: エラー率が10%を超えています ({error_rate:.1%})", file=sys.stderr)

    return 0
```

## FAIL出力例

```
============================= test session starts ==============================
platform linux -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0
collected 266 items

tests/book_converter/test_cli.py::TestCLIArguments::test_cli_main_exists FAILED
tests/book_converter/test_cli.py::TestCLIArguments::test_cli_parse_args_exists FAILED
...

=========================== short test summary info ============================
FAILED tests/book_converter/test_cli.py::TestCLIArguments::test_cli_main_exists
FAILED tests/book_converter/test_cli.py::TestCLIArguments::test_cli_parse_args_exists
...
======================== 64 failed, 202 passed in 0.53s ========================
```

## 主なFAIL原因

1. **ImportError: cannot import name 'main' from 'src.book_converter.cli'**
   - cli.pyにmain関数が未実装

2. **ImportError: cannot import name 'parse_args' from 'src.book_converter.cli'**
   - cli.pyにparse_args関数が未実装

3. **ImportError: cannot import name 'convert_book' from 'src.book_converter.cli'**
   - cli.pyにconvert_book関数が未実装

4. **ImportError: cannot import name 'parse_pages_with_errors' from 'src.book_converter.parser'**
   - parser.pyにparse_pages_with_errors関数が未実装

## 作成ファイル

| ファイル | 変更種別 | テスト数 |
|---------|---------|---------|
| tests/book_converter/test_cli.py | 新規作成 | 27テスト |
| tests/book_converter/test_e2e.py | 新規作成 | 21テスト |
| tests/book_converter/test_parser.py | 追加 | 16テスト |

## 次ステップ

Phase 5 Implementation (GREEN):
- T076: REDテストを読む
- T077: `src/book_converter/cli.py` にmain関数を実装
- T078: `src/book_converter/parser.py` にエラーハンドリング追加
- T079: `src/book_converter/xml_builder.py` にエラーコメント挿入機能を追加
- T080: `src/book_converter/cli.py` にエラーサマリー出力を実装
- T081: `make test` PASS (GREEN) を確認
