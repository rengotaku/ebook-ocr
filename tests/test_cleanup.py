"""Tests to verify dead code and legacy dependencies are removed.

Phase 3 RED tests: src/ocr.py still exists and requirements.txt
still contains legacy dependencies, so these tests will FAIL.
"""

from __future__ import annotations

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_DIR = PROJECT_ROOT / "src"
REQUIREMENTS_TXT = PROJECT_ROOT / "requirements.txt"


class TestNoLegacyOcrImport:
    """src/ 内のモジュールが legacy ocr.py をインポートしていないこと。"""

    def test_no_legacy_ocr_import_in_src(self) -> None:
        """src/ 内の .py ファイルに 'from src.ocr import' や 'import src.ocr' が存在しないこと。"""
        legacy_patterns = [
            re.compile(r"^\s*from\s+src\.ocr\s+import\b"),
            re.compile(r"^\s*import\s+src\.ocr\b"),
        ]
        violations: list[str] = []

        for py_file in sorted(SRC_DIR.glob("*.py")):
            # ocr.py 自体は検査対象外
            if py_file.name == "ocr.py":
                continue
            content = py_file.read_text(encoding="utf-8")
            for i, line in enumerate(content.splitlines(), start=1):
                for pattern in legacy_patterns:
                    if pattern.search(line):
                        violations.append(f"{py_file.name}:{i}: {line.strip()}")

        assert violations == [], (
            "Legacy ocr.py imports found:\n" + "\n".join(violations)
        )

    def test_legacy_ocr_module_deleted(self) -> None:
        """レガシー ocr.py が削除されていること。"""
        ocr_path = SRC_DIR / "ocr.py"
        assert not ocr_path.exists(), (
            f"Legacy ocr.py should be deleted but still exists at {ocr_path}"
        )


class TestNoUnusedDependencies:
    """requirements.txt にレガシー依存が含まれないこと。

    Note: easyocr と pytesseract は ROVER multi-engine OCR で使用されるため、
    現在は有効な依存関係です（008-rover-redesign で追加）。
    """

    def test_no_opencv_python(self) -> None:
        """requirements.txt に opencv-python が含まれないこと。"""
        content = REQUIREMENTS_TXT.read_text(encoding="utf-8")
        lines = [
            line.strip().lower()
            for line in content.splitlines()
            if line.strip() and not line.strip().startswith("#")
        ]
        matching = [l for l in lines if l == "opencv-python" or l.startswith("opencv-python")]
        assert matching == [], (
            f"Legacy dependency 'opencv-python' found in requirements.txt: {matching}"
        )


class TestNoPrivateCrossImports:
    """src/ 内のモジュール間でプライベート関数をインポートしていないこと。"""

    def test_no_private_cross_imports(self) -> None:
        """src/ 内に 'from src.xxx import _something' パターンが存在しないこと。"""
        private_import_pattern = re.compile(
            r"^\s*from\s+src\.\w+\s+import\s+.*\b_\w+"
        )
        violations: list[str] = []

        for py_file in sorted(SRC_DIR.glob("*.py")):
            content = py_file.read_text(encoding="utf-8")
            for i, line in enumerate(content.splitlines(), start=1):
                if private_import_pattern.search(line):
                    violations.append(f"{py_file.name}:{i}: {line.strip()}")

        assert violations == [], (
            "Private cross-imports found:\n" + "\n".join(violations)
        )
