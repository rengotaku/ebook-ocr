"""Tests for CLI normalize_headings.

Phase 6 RED tests: CLI サブコマンド (report, normalize, validate) のテスト。
実装が NotImplementedError のため、全て FAIL する想定。
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Sample book.md content for integration tests
# ---------------------------------------------------------------------------
SAMPLE_BOOK_MD = """\
<!-- toc -->
1.1 SREの概要 ... 015
1.1.1 サイトとは何か ... 018
1.2 信頼性とは何か ... 021
<!-- /toc -->

<!-- content -->

## 1.1 SREの概要

SREの説明文...

## サイトとは何か

サイトの説明文...

## 信頼性とは何か

信頼性の説明文...

## ■コードベース

特殊マーカーの見出し...

<!-- /content -->
"""


def _run_cli(*args: str, cwd: str | None = None) -> subprocess.CompletedProcess[str]:
    """Helper: run normalize_headings CLI via subprocess."""
    return subprocess.run(
        [sys.executable, "-m", "src.cli.normalize_headings", *args],
        capture_output=True,
        text=True,
        cwd=cwd or str(Path(__file__).resolve().parents[2]),
        timeout=30,
    )


# ===========================================================================
# report サブコマンドテスト
# ===========================================================================
class TestReportCommand:
    """Test report subcommand."""

    def test_report_command_success(self, tmp_path: Path) -> None:
        """report サブコマンドが正常に見出しパターンレポートを出力する."""
        book_md = tmp_path / "book.md"
        book_md.write_text(SAMPLE_BOOK_MD, encoding="utf-8")

        result = _run_cli("report", str(book_md))

        assert result.returncode == 0, f"stderr: {result.stderr}"
        # レポートに見出し総数が含まれる
        assert "Total" in result.stdout or "total" in result.stdout.lower()
        # パターン分布が含まれる
        assert "Pattern" in result.stdout or "pattern" in result.stdout.lower() or "numbered" in result.stdout.lower()

    def test_report_command_file_not_found(self, tmp_path: Path) -> None:
        """存在しないファイルを指定した場合にエラーを返す."""
        nonexistent = str(tmp_path / "nonexistent.md")

        result = _run_cli("report", nonexistent)

        assert result.returncode != 0
        # エラーメッセージにファイルパスまたは "not found" が含まれる (NotImplementedError ではなく)
        combined = result.stderr + result.stdout
        assert "NotImplementedError" not in combined, "Should show user-friendly error, not NotImplementedError"
        assert "not found" in combined.lower() or "no such file" in combined.lower() or "error" in combined.lower()

    def test_report_command_empty_file(self, tmp_path: Path) -> None:
        """マーカーなしファイルを指定した場合にエラーを返す."""
        book_md = tmp_path / "empty.md"
        book_md.write_text("", encoding="utf-8")

        result = _run_cli("report", str(book_md))

        # マーカーがないのでエラー
        assert result.returncode != 0
        assert "content" in result.stderr.lower()

    def test_report_command_shows_numbered_pattern(self, tmp_path: Path) -> None:
        """番号付き見出しパターンがレポートに表示される."""
        book_md = tmp_path / "book.md"
        book_md.write_text(SAMPLE_BOOK_MD, encoding="utf-8")

        result = _run_cli("report", str(book_md))

        assert result.returncode == 0, f"stderr: {result.stderr}"
        # 番号付きパターンの情報が含まれる
        stdout_lower = result.stdout.lower()
        assert "numbered" in stdout_lower or "番号" in result.stdout


# ===========================================================================
# normalize サブコマンドテスト
# ===========================================================================
class TestNormalizeCommand:
    """Test normalize subcommand."""

    def test_normalize_command_dryrun(self, tmp_path: Path) -> None:
        """normalize サブコマンドがデフォルトで dry-run プレビューを出力する."""
        book_md = tmp_path / "book.md"
        book_md.write_text(SAMPLE_BOOK_MD, encoding="utf-8")

        result = _run_cli("normalize", str(book_md))

        assert result.returncode == 0, f"stderr: {result.stderr}"
        # プレビュー出力が含まれる (変更がある場合)
        # dry-run ではファイルを変更しない
        original_content = book_md.read_text(encoding="utf-8")
        assert original_content == SAMPLE_BOOK_MD, "dry-run should not modify file"

    def test_normalize_command_apply(self, tmp_path: Path) -> None:
        """normalize --apply サブコマンドがファイルを実際に変更する."""
        book_md = tmp_path / "book.md"
        book_md.write_text(SAMPLE_BOOK_MD, encoding="utf-8")

        result = _run_cli("normalize", str(book_md), "--apply")

        assert result.returncode == 0, f"stderr: {result.stderr}"
        # --apply で変更が適用される (番号なし見出しに番号が付く等)
        modified_content = book_md.read_text(encoding="utf-8")
        # "## サイトとは何か" が "## 1.1.1 サイトとは何か" に変換されるはず
        assert "1.1.1" in modified_content or modified_content != SAMPLE_BOOK_MD

        # バックアップファイルが作成される
        backup_path = tmp_path / "book.md.bk"
        assert backup_path.exists(), "Backup file should be created"
        backup_content = backup_path.read_text(encoding="utf-8")
        assert backup_content == SAMPLE_BOOK_MD, "Backup should contain original content"

    def test_normalize_command_with_threshold(self, tmp_path: Path) -> None:
        """--threshold オプションが受け付けられる."""
        book_md = tmp_path / "book.md"
        book_md.write_text(SAMPLE_BOOK_MD, encoding="utf-8")

        result = _run_cli("normalize", str(book_md), "--threshold", "0.7")

        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_normalize_command_file_not_found(self, tmp_path: Path) -> None:
        """存在しないファイルを指定した場合にエラーを返す."""
        nonexistent = str(tmp_path / "nonexistent.md")

        result = _run_cli("normalize", nonexistent)

        assert result.returncode != 0
        combined = result.stderr + result.stdout
        assert "NotImplementedError" not in combined, "Should show user-friendly error, not NotImplementedError"
        assert "not found" in combined.lower() or "no such file" in combined.lower() or "error" in combined.lower()

    def test_normalize_duplicate_heading_shows_missing_not_fix_num(self, tmp_path: Path) -> None:
        """重複する見出し名がある場合、OCR欠落はMISSINGとなりFIX_NUMにならない."""
        # TOCに1.5.4と1.5.5がある。本文には1.5.4の見出しはあるが、
        # 1.5.5の見出しはOCR欠落で存在しない。
        # 1.5.4と1.5.5は同じタイトル「テスト項目」を持つ。
        # 期待: 1.5.5はMISSING (FIX_NUMではない)
        content = """\
<!-- toc -->
1.5.4 テスト項目 ... 216
1.5.5 テスト項目 ... 217
1.5.6 次の項目 ... 218
<!-- /toc -->

<!-- content -->

## 1.5.4 テスト項目

テスト本文...

## 1.5.6 次の項目

次の本文...

<!-- /content -->
"""
        book_md = tmp_path / "book.md"
        book_md.write_text(content, encoding="utf-8")

        result = _run_cli("normalize", str(book_md))

        assert result.returncode == 0, f"stderr: {result.stderr}"
        # 1.5.5 should be MISSING, not MISSING(NUM) / FIX_NUM
        lines = result.stdout.splitlines()
        for line in lines:
            if "1.5.5" in line:
                assert "FIX_NUM" not in line, (
                    f"Duplicate heading '1.5.5 テスト項目' should be MISSING, not FIX_NUM: {line}"
                )
                assert "MISSING(NUM)" not in line, (
                    f"Duplicate heading '1.5.5 テスト項目' should be MISSING, not MISSING(NUM): {line}"
                )

    def test_normalize_command_dryrun_shows_preview(self, tmp_path: Path) -> None:
        """dry-run で変更プレビューが表示される."""
        book_md = tmp_path / "book.md"
        book_md.write_text(SAMPLE_BOOK_MD, encoding="utf-8")

        result = _run_cli("normalize", str(book_md))

        assert result.returncode == 0, f"stderr: {result.stderr}"
        # プレビューに変更行情報が含まれる (Line や -> 等)
        stdout = result.stdout
        # 少なくとも何らかの出力がある
        assert len(stdout) > 0


# ===========================================================================
# validate サブコマンドテスト
# ===========================================================================
class TestValidateCommand:
    """Test validate subcommand."""

    def test_validate_command_success(self, tmp_path: Path) -> None:
        """validate サブコマンドが検証レポートを出力する."""
        book_md = tmp_path / "book.md"
        book_md.write_text(SAMPLE_BOOK_MD, encoding="utf-8")

        result = _run_cli("validate", str(book_md))

        assert result.returncode == 0, f"stderr: {result.stderr}"
        # 検証レポートのヘッダが含まれる
        assert "Validation Report" in result.stdout or "validation" in result.stdout.lower()
        # サマリー情報が含まれる
        assert "TOC" in result.stdout or "toc" in result.stdout.lower()

    def test_validate_command_warn_exit_code(self, tmp_path: Path) -> None:
        """MISSING エントリがあっても exit code は 0 である."""
        # 意図的にマッチしない TOC エントリを含む book.md
        content = """\
<!-- toc -->
1.1 存在しない見出し ... 001
1.2 もう一つの存在しない見出し ... 002
<!-- /toc -->

<!-- content -->

## 全く関係ない見出し

テスト本文...

<!-- /content -->
"""
        book_md = tmp_path / "book.md"
        book_md.write_text(content, encoding="utf-8")

        result = _run_cli("validate", str(book_md))

        # MISSING があっても exit 0 (CI でブロックしない)
        assert result.returncode == 0, f"stderr: {result.stderr}"
        # WARN ステータスまたは MISSING 情報が含まれる
        stdout = result.stdout
        assert "WARN" in stdout or "MISSING" in stdout or "missing" in stdout.lower()

    def test_validate_command_file_not_found(self, tmp_path: Path) -> None:
        """存在しないファイルを指定した場合にエラーを返す."""
        nonexistent = str(tmp_path / "nonexistent.md")

        result = _run_cli("validate", nonexistent)

        assert result.returncode != 0
        combined = result.stderr + result.stdout
        assert "NotImplementedError" not in combined, "Should show user-friendly error, not NotImplementedError"
        assert "not found" in combined.lower() or "no such file" in combined.lower() or "error" in combined.lower()

    def test_validate_command_shows_match_details(self, tmp_path: Path) -> None:
        """検証レポートにマッチ詳細テーブルが含まれる."""
        book_md = tmp_path / "book.md"
        book_md.write_text(SAMPLE_BOOK_MD, encoding="utf-8")

        result = _run_cli("validate", str(book_md))

        assert result.returncode == 0, f"stderr: {result.stderr}"
        # テーブルまたは詳細情報が含まれる
        stdout = result.stdout
        assert "Match" in stdout or "match" in stdout.lower() or "EXACT" in stdout or "FUZZY" in stdout

    def test_validate_command_shows_excluded(self, tmp_path: Path) -> None:
        """特殊マーカー見出しが Excluded セクションに表示される."""
        book_md = tmp_path / "book.md"
        book_md.write_text(SAMPLE_BOOK_MD, encoding="utf-8")

        result = _run_cli("validate", str(book_md))

        assert result.returncode == 0, f"stderr: {result.stderr}"
        # Excluded セクションに特殊マーカー見出しが含まれる
        stdout = result.stdout
        assert "Excluded" in stdout or "excluded" in stdout.lower()

    def test_validate_command_with_threshold(self, tmp_path: Path) -> None:
        """--threshold オプションが受け付けられる."""
        book_md = tmp_path / "book.md"
        book_md.write_text(SAMPLE_BOOK_MD, encoding="utf-8")

        result = _run_cli("validate", str(book_md), "--threshold", "0.6")

        assert result.returncode == 0, f"stderr: {result.stderr}"


# ===========================================================================
# CLI 共通テスト
# ===========================================================================
class TestCLICommon:
    """Test common CLI behavior."""

    def test_no_subcommand_shows_help(self) -> None:
        """サブコマンドなしで実行した場合にヘルプが表示される."""
        result = _run_cli()

        # argparse はサブコマンドなしで error (returncode != 0) を返す
        assert result.returncode != 0
        combined = result.stderr + result.stdout
        assert "NotImplementedError" not in combined, "Should show argparse help, not NotImplementedError"
        assert "usage" in combined.lower() or "error" in combined.lower()

    def test_help_flag(self) -> None:
        """--help フラグでヘルプが表示される."""
        result = _run_cli("--help")

        assert result.returncode == 0
        assert "report" in result.stdout
        assert "normalize" in result.stdout
        assert "validate" in result.stdout

    def test_report_help_flag(self) -> None:
        """report --help でサブコマンドヘルプが表示される."""
        result = _run_cli("report", "--help")

        assert result.returncode == 0
        assert "book" in result.stdout.lower() or "file" in result.stdout.lower()

    def test_normalize_help_flag(self) -> None:
        """normalize --help でサブコマンドヘルプが表示される."""
        result = _run_cli("normalize", "--help")

        assert result.returncode == 0
        assert "--apply" in result.stdout
        assert "--threshold" in result.stdout

    def test_validate_help_flag(self) -> None:
        """validate --help でサブコマンドヘルプが表示される."""
        result = _run_cli("validate", "--help")

        assert result.returncode == 0
        assert "book" in result.stdout.lower() or "file" in result.stdout.lower()

    def test_invalid_subcommand(self) -> None:
        """無効なサブコマンドでエラーを返す."""
        result = _run_cli("invalid_command")

        assert result.returncode != 0
        combined = result.stderr + result.stdout
        assert "NotImplementedError" not in combined, "Should show argparse error, not NotImplementedError"

    def test_module_runnable(self) -> None:
        """python -m src.cli.normalize_headings で実行可能."""
        result = _run_cli("--help")

        assert result.returncode == 0
        assert "usage" in result.stdout.lower()
