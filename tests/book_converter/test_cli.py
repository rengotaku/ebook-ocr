"""CLI tests for book markdown to XML conversion.

Tests for Phase 5: CLI & Error Handling
- T070: CLI argument tests (input.md output.xml --verbose --quiet)
- T073: Error rate warning tests (>10% error rate warning message)
"""

import pytest
from pathlib import Path
from unittest.mock import patch
from io import StringIO


class TestCLIArguments:
    """T070: CLI引数テスト (input.md output.xml --verbose --quiet)"""

    def test_cli_main_exists(self) -> None:
        """CLI main関数が存在する"""
        from src.book_converter.cli import main

        assert callable(main)

    def test_cli_parse_args_exists(self) -> None:
        """CLI parse_args関数が存在する"""
        from src.book_converter.cli import parse_args

        assert callable(parse_args)

    def test_cli_requires_input_file(self) -> None:
        """入力ファイルは必須引数"""
        from src.book_converter.cli import parse_args

        with pytest.raises(SystemExit):
            parse_args([])

    def test_cli_requires_output_file(self) -> None:
        """出力ファイルは必須引数"""
        from src.book_converter.cli import parse_args

        with pytest.raises(SystemExit):
            parse_args(["input.md"])

    def test_cli_accepts_input_and_output(self) -> None:
        """入力と出力ファイルを受け付ける"""
        from src.book_converter.cli import parse_args

        args = parse_args(["input.md", "output.xml"])

        assert args.input == "input.md"
        assert args.output == "output.xml"

    def test_cli_verbose_flag(self) -> None:
        """--verbose フラグを受け付ける"""
        from src.book_converter.cli import parse_args

        args = parse_args(["input.md", "output.xml", "--verbose"])

        assert args.verbose is True

    def test_cli_verbose_short_flag(self) -> None:
        """-v フラグを受け付ける"""
        from src.book_converter.cli import parse_args

        args = parse_args(["input.md", "output.xml", "-v"])

        assert args.verbose is True

    def test_cli_quiet_flag(self) -> None:
        """--quiet フラグを受け付ける"""
        from src.book_converter.cli import parse_args

        args = parse_args(["input.md", "output.xml", "--quiet"])

        assert args.quiet is True

    def test_cli_quiet_short_flag(self) -> None:
        """-q フラグを受け付ける"""
        from src.book_converter.cli import parse_args

        args = parse_args(["input.md", "output.xml", "-q"])

        assert args.quiet is True

    def test_cli_verbose_and_quiet_mutually_exclusive(self) -> None:
        """--verbose と --quiet は同時に指定できない"""
        from src.book_converter.cli import parse_args

        with pytest.raises(SystemExit):
            parse_args(["input.md", "output.xml", "--verbose", "--quiet"])

    def test_cli_default_not_verbose(self) -> None:
        """デフォルトでverboseはFalse"""
        from src.book_converter.cli import parse_args

        args = parse_args(["input.md", "output.xml"])

        assert args.verbose is False

    def test_cli_default_not_quiet(self) -> None:
        """デフォルトでquietはFalse"""
        from src.book_converter.cli import parse_args

        args = parse_args(["input.md", "output.xml"])

        assert args.quiet is False


class TestCLIExecution:
    """CLI実行テスト"""

    def test_cli_returns_zero_on_success(self, tmp_path: Path) -> None:
        """成功時は終了コード0を返す"""
        from src.book_converter.cli import main

        # Create a minimal input file
        input_file = tmp_path / "input.md"
        input_file.write_text("--- Page 1 (page_0001.png) ---\n\n# Title\n")

        output_file = tmp_path / "output.xml"

        exit_code = main([str(input_file), str(output_file)])

        assert exit_code == 0
        assert output_file.exists()

    def test_cli_returns_nonzero_on_file_not_found(self, tmp_path: Path) -> None:
        """ファイルが見つからない場合は非ゼロを返す"""
        from src.book_converter.cli import main

        output_file = tmp_path / "output.xml"

        exit_code = main(["/nonexistent/path/input.md", str(output_file)])

        assert exit_code != 0

    def test_cli_creates_output_file(self, tmp_path: Path) -> None:
        """出力ファイルを生成する"""
        from src.book_converter.cli import main

        input_file = tmp_path / "input.md"
        input_file.write_text("--- Page 1 (page_0001.png) ---\n\n# Title\n")

        output_file = tmp_path / "output.xml"

        main([str(input_file), str(output_file)])

        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")
        assert "<?xml" in content or "<book>" in content

    def test_cli_verbose_outputs_progress(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """--verbose時に進捗情報を出力"""
        from src.book_converter.cli import main

        input_file = tmp_path / "input.md"
        input_file.write_text("--- Page 1 (page_0001.png) ---\n\n# Title\n")

        output_file = tmp_path / "output.xml"

        main([str(input_file), str(output_file), "--verbose"])

        captured = capsys.readouterr()
        # 進捗情報またはログが出力されていること
        assert len(captured.out) > 0 or len(captured.err) > 0

    def test_cli_quiet_suppresses_output(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """--quiet時は出力を抑制"""
        from src.book_converter.cli import main

        input_file = tmp_path / "input.md"
        input_file.write_text("--- Page 1 (page_0001.png) ---\n\n# Title\n")

        output_file = tmp_path / "output.xml"

        main([str(input_file), str(output_file), "--quiet"])

        captured = capsys.readouterr()
        # 警告やエラー以外は出力されない
        # (エラーがなければstdoutは空)
        assert captured.out == "" or captured.out.strip() == ""


class TestCLIConversionResult:
    """CLI変換結果テスト"""

    def test_cli_outputs_summary_on_completion(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """変換完了時にサマリーを出力"""
        from src.book_converter.cli import main

        input_file = tmp_path / "input.md"
        input_file.write_text(
            "--- Page 1 (page_0001.png) ---\n\n# Title\n\n"
            "--- Page 2 (page_0002.png) ---\n\n## Chapter 1\n"
        )

        output_file = tmp_path / "output.xml"

        main([str(input_file), str(output_file)])

        captured = capsys.readouterr()
        # ページ数などのサマリーが出力される
        # "2" または "pages" または "完了" などの文字列
        output = captured.out + captured.err
        assert "2" in output or "page" in output.lower() or "完了" in output


class TestErrorRateWarning:
    """T073: エラー率警告テスト (10%超過時の警告メッセージ)"""

    def test_warning_when_error_rate_exceeds_10_percent(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """エラー率が10%を超える場合に警告を出力"""
        from src.book_converter.cli import main

        # Create a file with many errors (missing page numbers)
        # 11 pages total, with only 1 valid page number = ~90% error
        lines = []
        for i in range(11):
            if i == 0:
                lines.append(f"--- Page 1 (page_{i:04d}.png) ---\n")
            else:
                # Missing page number (error)
                lines.append(f"--- Page (page_{i:04d}.png) ---\n")
            lines.append(f"\n# Heading {i}\n\n")

        input_file = tmp_path / "input.md"
        input_file.write_text("".join(lines))

        output_file = tmp_path / "output.xml"

        main([str(input_file), str(output_file)])

        captured = capsys.readouterr()
        output = captured.out + captured.err
        # 10%超過の警告メッセージ
        assert "10%" in output or "警告" in output or "warning" in output.lower()

    def test_no_warning_when_error_rate_below_10_percent(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """エラー率が10%以下の場合は警告なし"""
        from src.book_converter.cli import main

        # Create a file with 1 error out of 20 pages = 5% error
        lines = []
        for i in range(20):
            if i == 0:
                # One missing page number
                lines.append(f"--- Page (page_{i:04d}.png) ---\n")
            else:
                lines.append(f"--- Page {i} (page_{i:04d}.png) ---\n")
            lines.append(f"\n# Heading {i}\n\n")

        input_file = tmp_path / "input.md"
        input_file.write_text("".join(lines))

        output_file = tmp_path / "output.xml"

        main([str(input_file), str(output_file)])

        captured = capsys.readouterr()
        output = captured.out + captured.err
        # 10%超過の警告メッセージは出力されない
        # (他の警告は出る可能性があるので、10%特有のメッセージを確認)
        assert "10%" not in output

    def test_error_count_displayed_in_summary(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """サマリーにエラー数が表示される"""
        from src.book_converter.cli import main

        # Create a file with some errors
        input_file = tmp_path / "input.md"
        input_file.write_text(
            "--- Page 1 (page_0001.png) ---\n\n# Title\n\n"
            "--- Page (page_0002.png) ---\n\n## Chapter 1\n"  # Missing page number
        )

        output_file = tmp_path / "output.xml"

        main([str(input_file), str(output_file)])

        captured = capsys.readouterr()
        output = captured.out + captured.err
        # エラー数または警告数が表示される
        assert "error" in output.lower() or "エラー" in output or "warning" in output.lower() or "警告" in output

    def test_error_summary_at_end(
        self, tmp_path: Path, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """最後にエラーサマリーを表示"""
        from src.book_converter.cli import main

        # Create a file with errors
        input_file = tmp_path / "input.md"
        input_file.write_text(
            "--- Page (page_0001.png) ---\n\n# Title\n\n"  # Missing page number
            "--- Page (page_0002.png) ---\n\n## Chapter 1\n"  # Missing page number
        )

        output_file = tmp_path / "output.xml"

        main([str(input_file), str(output_file)])

        captured = capsys.readouterr()
        output = captured.out + captured.err
        # サマリー情報が出力される
        assert len(output) > 0


class TestCLIConvertFunction:
    """CLI convert_book関数テスト"""

    def test_convert_book_function_exists(self) -> None:
        """convert_book関数が存在する"""
        from src.book_converter.cli import convert_book

        assert callable(convert_book)

    def test_convert_book_returns_result(self, tmp_path: Path) -> None:
        """convert_book関数がConversionResultを返す"""
        from src.book_converter.cli import convert_book
        from src.book_converter.models import ConversionResult

        input_file = tmp_path / "input.md"
        input_file.write_text("--- Page 1 (page_0001.png) ---\n\n# Title\n")

        output_file = tmp_path / "output.xml"

        result = convert_book(input_file, output_file)

        assert isinstance(result, ConversionResult)

    def test_convert_book_result_has_total_pages(self, tmp_path: Path) -> None:
        """変換結果にtotal_pagesが含まれる"""
        from src.book_converter.cli import convert_book

        input_file = tmp_path / "input.md"
        input_file.write_text(
            "--- Page 1 (page_0001.png) ---\n\n# Title\n\n"
            "--- Page 2 (page_0002.png) ---\n\n## Chapter 1\n"
        )

        output_file = tmp_path / "output.xml"

        result = convert_book(input_file, output_file)

        assert result.total_pages == 2

    def test_convert_book_result_has_error_count(self, tmp_path: Path) -> None:
        """変換結果にerror_countが含まれる"""
        from src.book_converter.cli import convert_book

        input_file = tmp_path / "input.md"
        input_file.write_text("--- Page 1 (page_0001.png) ---\n\n# Title\n")

        output_file = tmp_path / "output.xml"

        result = convert_book(input_file, output_file)

        assert hasattr(result, "error_count")
        assert isinstance(result.error_count, int)

    def test_convert_book_result_has_errors_list(self, tmp_path: Path) -> None:
        """変換結果にerrorsリストが含まれる"""
        from src.book_converter.cli import convert_book

        input_file = tmp_path / "input.md"
        input_file.write_text("--- Page (page_0001.png) ---\n\n# Title\n")  # Missing number

        output_file = tmp_path / "output.xml"

        result = convert_book(input_file, output_file)

        assert hasattr(result, "errors")
        # エラーがあればタプルに含まれる
        if result.error_count > 0:
            assert len(result.errors) > 0
