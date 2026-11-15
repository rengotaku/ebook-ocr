"""章分割と LLM 向け整形のテスト."""

from __future__ import annotations

from pathlib import Path

from src.chapter_splitter import (
    build_chapters,
    chapter_starts,
    llm_format,
    render_chapter,
    running_head_titles,
    split_file,
    split_pages,
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
        assert text == "本文です。\n\n> **図**: 概念図の説明。"

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
        assert "<!-- pages: 0002-0003 -->" in text
        assert "20 第1章" not in text


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
