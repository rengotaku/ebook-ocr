"""book_meta.json（紙面のページ番号・章名）の読み書きテスト (#99)."""

from __future__ import annotations

import json
from pathlib import Path

from src.book_meta import load_book_meta, write_book_meta


class TestWriteBookMeta:
    def test_writes_both_sections(self, tmp_path: Path) -> None:
        path = write_book_meta(tmp_path, {"0021": 22, "0020": 21}, {2: "データを事前にチェックする", 1: "設計"})

        assert path == tmp_path / "book_meta.json"
        data = json.loads(path.read_text(encoding="utf-8"))
        assert data["page_numbers"] == {"0020": 21, "0021": 22}
        assert data["chapter_titles"] == {"1": "設計", "2": "データを事前にチェックする"}

    def test_nothing_to_write(self, tmp_path: Path) -> None:
        assert write_book_meta(tmp_path, {}, {}) is None
        assert not (tmp_path / "book_meta.json").exists()


class TestLoadBookMeta:
    def test_loads_next_to_book_md(self, tmp_path: Path) -> None:
        book = tmp_path / "book.md"
        book.write_text("本文\n", encoding="utf-8")
        (tmp_path / "book_meta.json").write_text(
            json.dumps({"page_numbers": {"0021": 22}, "chapter_titles": {"1": "設計"}}), encoding="utf-8"
        )

        meta = load_book_meta(book)

        assert meta["page_numbers"] == {"0021": 22}
        assert meta["chapter_titles"] == {1: "設計"}

    def test_loads_from_ocr_output_dir(self, tmp_path: Path) -> None:
        book = tmp_path / "book.md"
        book.write_text("本文\n", encoding="utf-8")
        (tmp_path / "ocr_output").mkdir()
        (tmp_path / "ocr_output" / "book_meta.json").write_text(
            json.dumps({"page_numbers": {"0021": 22}}), encoding="utf-8"
        )

        assert load_book_meta(book)["page_numbers"] == {"0021": 22}

    def test_missing_file_returns_empty(self, tmp_path: Path) -> None:
        book = tmp_path / "book.md"
        book.write_text("本文\n", encoding="utf-8")

        assert load_book_meta(book) == {"page_numbers": {}, "chapter_titles": {}, "fallback_pages": []}
