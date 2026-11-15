"""章分割と LLM 向け整形のテスト."""

from __future__ import annotations

from pathlib import Path

from src.chapter_splitter import (
    build_chapters,
    chapter_starts,
    chapter_titles,
    llm_format,
    render_chapter,
    running_head_titles,
    split_file,
    split_pages,
    write_page_numbers_csv,
)

BOOK = """\
--- 0000 ---

表紙

--- 0001 ---

はじめに

--- 0002 ---

第1章 データ分析を設計する

この章では…

20 第1章 データ分析を設計する

分析の概念図は、先述の

ストーリーを語るものです。

--- 0003 ---

1-1.

見える化って何?

「プロローグ」で述べた

問題です。

![図](figures/0003_fig1.png)

**図**: 概念図の説明。

21 第1章 データ分析を設計する

--- 0004 ---

第2章 データをチェックする

この章では…

--- 0005 ---

--- 0006 ---

●著者一覧

河村 真一
"""


class TestSplitPages:
    def test_splits_by_marker(self):
        pages = split_pages(BOOK)
        assert [page for page, _ in pages] == ["0000", "0001", "0002", "0003", "0004", "0005", "0006"]

    def test_empty_when_no_marker(self):
        assert split_pages("本文だけ") == []


class TestChapterStarts:
    def test_detects_opener_pages(self):
        starts = chapter_starts(split_pages(BOOK))
        assert starts == {1: "0002", 2: "0004"}


class TestRunningHeadTitles:
    def test_most_frequent_title(self):
        titles = running_head_titles(split_pages(BOOK))
        assert titles[1] == "データ分析を設計する"


class TestChapterTitles:
    """章名は扉ページの見出しから取る（柱を本文から除いても章名が残るように）."""

    def test_title_from_opener_line(self):
        titles = chapter_titles(split_pages(BOOK))
        assert titles[1] == "データ分析を設計する"
        assert titles[2] == "データをチェックする"

    def test_title_from_line_after_chapter_number(self):
        book = "--- 0050 ---\n\n## 第2章\nデータを事前にチェックする\n\n本文です。\n"
        assert chapter_titles(split_pages(book))[2] == "データを事前にチェックする"

    def test_falls_back_to_running_head_when_opener_has_no_title(self):
        book = "--- 0002 ---\n\n第1章\n本文がすぐ始まる。\n\n20 第1章 データ分析を設計する\n"
        assert chapter_titles(split_pages(book))[1] == "データ分析を設計する"

    def test_known_titles_from_book_meta_win(self):
        titles = chapter_titles(split_pages(BOOK), {1: "柱から取った章名"})
        assert titles[1] == "柱から取った章名"

    def test_body_lines_do_not_become_titles(self):
        book = "--- 0002 ---\n\n第2章\nデータを事前にチェックする\n\n第3章の理解度チェック\n"
        titles = chapter_titles(split_pages(book))
        assert titles[2] == "データを事前にチェックする"
        assert 3 not in titles


class TestBuildChapters:
    def test_front_chapters_and_back(self):
        chapters = build_chapters(split_pages(BOOK))
        names = [(chapter.number, chapter.title, chapter.start_page, chapter.end_page) for chapter in chapters]
        assert names == [
            (None, "00_front", "0000", "0001"),
            (1, "データ分析を設計する", "0002", "0003"),
            (2, "データをチェックする", "0004", "0005"),
            (None, "99_back", "0006", "0006"),
        ]

    def test_file_name_is_ordered(self):
        chapters = build_chapters(split_pages(BOOK))
        assert chapters[1].file_name == "01_データ分析を設計する.md"
        assert chapters[0].file_name == "00_front.md"


class TestLlmFormat:
    def test_joins_wrapped_lines(self):
        text = llm_format("分析の概念図は、先述の\n\nストーリーを語るものです。\n")
        assert text == "分析の概念図は、先述のストーリーを語るものです。"

    def test_drops_running_heads_and_page_numbers(self):
        text = llm_format("本文です。\n\n20 第1章 データ分析を設計する\n\n42\n\n14 目次\n")
        assert "第1章" not in text
        assert "42" not in text
        assert "目次" not in text
        assert text == "本文です。"

    def test_figure_caption_becomes_quote(self):
        text = llm_format("本文です。\n\n![図](figures/0003_fig1.png)\n\n**図**: 概念図の説明。\n")
        assert "![" not in text
        assert text == "本文です。\n\n<!-- 図: figures/0003_fig1.png -->\n\n> **図**: 概念図の説明。"

    def test_figure_keeps_relative_image_path_as_comment(self):
        text = llm_format("![図](figures/0086_fig1.png)\n\n**図**: 説明。\n")
        assert "<!-- 図: figures/0086_fig1.png -->" in text

    def test_section_number_on_its_own_line(self):
        text = llm_format("1-1.\n\n見える化って何?\n")
        assert text == "## 1-1. 見える化って何?"

    def test_chapter_title_line_is_dropped(self):
        text = llm_format("第1章 データ分析を設計する\n\n本文です。\n")
        assert text == "本文です。"


class TestRenderChapter:
    def test_title_is_heading_and_pages_noted(self):
        chapter = build_chapters(split_pages(BOOK))[1]
        text = render_chapter(chapter)
        assert text.startswith("# 第1章 データ分析を設計する\n")
        assert "<!-- pages: 0002-0003 / pages-dir: pages / figures-dir: figures -->" in text
        assert "20 第1章" not in text

    def test_each_page_gets_a_page_comment(self):
        chapter = build_chapters(split_pages(BOOK))[1]
        text = render_chapter(chapter)
        assert "<!-- page 0002 -->" in text
        assert "<!-- page 0003 -->" in text

    def test_page_comment_includes_printed_page_number(self):
        chapter = build_chapters(split_pages(BOOK))[1]
        text = render_chapter(chapter, page_numbers={"0002": 20, "0003": 21})
        assert "<!-- page 0002 (紙面 20) -->" in text
        assert "<!-- page 0003 (紙面 21) -->" in text

    def test_page_comment_omits_unknown_printed_number(self):
        chapter = build_chapters(split_pages(BOOK))[1]
        text = render_chapter(chapter, page_numbers={"0002": 20})
        assert "<!-- page 0003 -->" in text


class TestSplitFile:
    def test_writes_each_chapter(self, tmp_path: Path):
        book = tmp_path / "book.md"
        book.write_text(BOOK, encoding="utf-8")

        written = split_file(book, tmp_path / "chapters")

        assert [path.name for path in written] == [
            "00_front.md",
            "01_データ分析を設計する.md",
            "02_データをチェックする.md",
            "99_back.md",
        ]
        assert "概念図の説明" in (tmp_path / "chapters" / "01_データ分析を設計する.md").read_text(encoding="utf-8")


class TestPageNumbers:
    """紙面のページ番号（ノンブル）の対応表 (#99)."""

    def test_writes_csv(self, tmp_path: Path) -> None:
        path = write_page_numbers_csv(tmp_path, {"0003": 21, "0002": 20})

        assert path == tmp_path / "_pages.csv"
        assert path.read_text(encoding="utf-8") == "page,printed\n0002,20\n0003,21\n"

    def test_no_csv_when_empty(self, tmp_path: Path) -> None:
        assert write_page_numbers_csv(tmp_path, {}) is None
