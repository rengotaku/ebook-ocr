"""命名規則準拠テスト.

Phase 3 (US2): 命名規則の統一テスト
- 「yomitoku」「rover-ocr」などの名称を「rover」に統一

このテストは命名規則違反を検出し、リファクタリングが必要な箇所を明確にする。
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pytest


class TestYomitokuNamingInCLI:
    """CLIスクリプト内の「yomitoku」命名規則違反テスト."""

    @pytest.fixture
    def src_dir(self) -> Path:
        """srcディレクトリパスを取得."""
        return Path(__file__).parent.parent / "src"

    @pytest.fixture
    def cli_dir(self, src_dir: Path) -> Path:
        """CLIディレクトリパスを取得."""
        return src_dir / "cli"

    def test_no_yomitoku_device_in_cli_args(self, cli_dir: Path) -> None:
        """CLIスクリプトでyomitoku_device引数を使用していないこと.

        Expected: run_ocr.pyの呼び出しでyomitoku_device=...が使われている → FAIL
        After fix: device=... に変更 → PASS
        """
        for py_file in cli_dir.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            content = py_file.read_text()
            # yomitoku_device=args.device のような呼び出しを検出
            matches = re.findall(r"yomitoku_device\s*=", content)
            assert not matches, (
                f"{py_file.name}: yomitoku_device引数を使用しています。"
                f"deviceにリネームしてください: {matches}"
            )

    def test_no_yomitoku_in_argparse_dest(self, cli_dir: Path) -> None:
        """argparse引数にyomitokuが含まれていないこと.

        Expected: --yomitoku-device のような引数があれば → FAIL
        After fix: --device に変更 → PASS
        """
        for py_file in cli_dir.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            content = py_file.read_text()
            # --yomitoku で始まる引数を検出
            matches = re.findall(r"['\"]--yomitoku[^'\"]*['\"]", content)
            assert not matches, (
                f"{py_file.name}: yomitokuを含むargparse引数が存在します: {matches}"
            )

    def test_no_yomitoku_in_cli_variable_names(self, cli_dir: Path) -> None:
        """CLIスクリプト内にyomitoku_*変数がないこと.

        Expected: yomitoku_device, yomitoku_result などの変数があれば → FAIL
        After fix: device, result に変更 → PASS
        """
        for py_file in cli_dir.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            content = py_file.read_text()
            # yomitoku_ で始まる変数名を検出（コメント行を除く）
            lines = content.split("\n")
            violations = []
            for i, line in enumerate(lines, 1):
                # コメント行とdocstringをスキップ
                stripped = line.strip()
                if stripped.startswith("#"):
                    continue
                if re.search(r"\byomitoku_\w+\b", line):
                    violations.append(f"L{i}: {stripped}")
            assert not violations, (
                f"{py_file.name}: yomitoku_*変数が存在します:\n"
                + "\n".join(violations)
            )


class TestYomitokuFunctionNaming:
    """「yomitoku」を含む関数名の命名規則違反テスト."""

    @pytest.fixture
    def src_dir(self) -> Path:
        """srcディレクトリパスを取得."""
        return Path(__file__).parent.parent / "src"

    @pytest.fixture
    def cli_dir(self, src_dir: Path) -> Path:
        """CLIディレクトリパスを取得."""
        return src_dir / "cli"

    def test_no_detect_layout_yomitoku_import_in_cli(self, cli_dir: Path) -> None:
        """CLIでdetect_layout_yomitoku関数をインポートしていないこと.

        Expected: detect_layout.pyでdetect_layout_yomitokuをインポート → FAIL
        After fix: detect_layout関数にリネーム → PASS
        """
        detect_layout_file = cli_dir / "detect_layout.py"
        if detect_layout_file.exists():
            content = detect_layout_file.read_text()
            assert "detect_layout_yomitoku" not in content, (
                "detect_layout.py: detect_layout_yomitoku関数を使用しています。"
                "detect_layout にリネームしてください。"
            )

    def test_no_yomitoku_function_calls_in_cli(self, cli_dir: Path) -> None:
        """CLIスクリプトでyomitoku関数を直接呼び出していないこと.

        Expected: ocr_yomitoku_engine() などの呼び出しがあれば → FAIL
        After fix: 汎用名称の関数に変更 → PASS
        """
        for py_file in cli_dir.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            content = py_file.read_text()
            # yomitoku関数呼び出しを検出（インポート文を除く）
            lines = content.split("\n")
            violations = []
            for i, line in enumerate(lines, 1):
                stripped = line.strip()
                # import文とコメントをスキップ
                if stripped.startswith(("import ", "from ", "#")):
                    continue
                # 関数呼び出しパターンを検出
                if re.search(r"\b\w*yomitoku\w*\s*\(", line, re.IGNORECASE):
                    violations.append(f"L{i}: {stripped}")
            assert not violations, (
                f"{py_file.name}: yomitoku関数を呼び出しています:\n"
                + "\n".join(violations)
            )


class TestRoverOcrNaming:
    """「rover-ocr」「rover_ocr」命名規則違反テスト."""

    @pytest.fixture
    def project_root(self) -> Path:
        """プロジェクトルートパスを取得."""
        return Path(__file__).parent.parent

    def test_no_rover_ocr_in_module_names(self, project_root: Path) -> None:
        """rover-ocr または rover_ocr がモジュール名に含まれていないこと.

        rover/ensemble.py など短い名称を使用する。
        """
        src_dir = project_root / "src"
        for py_file in src_dir.rglob("*.py"):
            # ファイル名にrover-ocrまたはrover_ocrが含まれていないこと
            filename = py_file.name.lower()
            assert "rover-ocr" not in filename, (
                f"{py_file}: ファイル名にrover-ocrが含まれています"
            )
            assert "rover_ocr" not in filename, (
                f"{py_file}: ファイル名にrover_ocrが含まれています"
            )

    def test_no_rover_ocr_in_code_comments(self, project_root: Path) -> None:
        """src/cli/内のコードでrover-ocr/rover_ocrがコメントに含まれていないこと.

        Note: 一般的なsrc/全体ではなく、cli/に限定してチェックする。
        """
        cli_dir = project_root / "src" / "cli"
        for py_file in cli_dir.glob("*.py"):
            if py_file.name.startswith("__"):
                continue
            content = py_file.read_text().lower()
            # コメント行のみを抽出
            lines = content.split("\n")
            comment_lines = [
                line for line in lines
                if line.strip().startswith("#")
            ]
            comment_text = "\n".join(comment_lines)
            violations = re.findall(r"rover[-_]ocr", comment_text)
            assert not violations, (
                f"{py_file.name}: コメントにrover-ocr/rover_ocrが含まれています"
            )


class TestGrepVerification:
    """grepによる命名規則検証テスト.

    subprocess.runでgrepを実行し、旧名称の使用箇所を検出する。
    """

    @pytest.fixture
    def project_root(self) -> Path:
        """プロジェクトルートパスを取得."""
        return Path(__file__).parent.parent

    def test_grep_no_yomitoku_device_in_cli(self, project_root: Path) -> None:
        """grep検証: CLIにyomitoku_deviceがないこと.

        Expected: src/cli/run_ocr.py:38にyomitoku_device=が存在 → FAIL
        After fix: device=に変更 → PASS (grep returncode=1)
        """
        result = subprocess.run(
            ["grep", "-r", "yomitoku_device", "src/cli/"],
            capture_output=True,
            text=True,
            cwd=project_root,
        )
        # grep返り値: 0=マッチあり, 1=マッチなし, 2=エラー
        assert result.returncode == 1, (
            f"CLIにyomitoku_deviceが見つかりました:\n{result.stdout}"
        )

    def test_grep_no_detect_layout_yomitoku_in_cli(self, project_root: Path) -> None:
        """grep検証: CLIにdetect_layout_yomitokuがないこと.

        Expected: src/cli/detect_layout.pyでimportとcallが存在 → FAIL
        After fix: detect_layout関数に変更 → PASS
        """
        result = subprocess.run(
            ["grep", "-r", "detect_layout_yomitoku", "src/cli/"],
            capture_output=True,
            text=True,
            cwd=project_root,
        )
        assert result.returncode == 1, (
            f"CLIにdetect_layout_yomitokuが見つかりました:\n{result.stdout}"
        )

    def test_grep_no_ocr_yomitoku_import_in_cli(self, project_root: Path) -> None:
        """grep検証: CLIでocr_yomitokuモジュールをインポートしていないこと.

        Expected: from src.ocr_yomitoku が存在 → FAIL
        After fix: from src.layout.detector などに変更 → PASS
        """
        result = subprocess.run(
            ["grep", "-r", "from src.ocr_yomitoku", "src/cli/"],
            capture_output=True,
            text=True,
            cwd=project_root,
        )
        assert result.returncode == 1, (
            f"CLIでocr_yomitokuをインポートしています:\n{result.stdout}"
        )
