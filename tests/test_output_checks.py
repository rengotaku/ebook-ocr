"""出力の異常検出のテスト (#102).

わざと壊した入力を与えて、5 種類の異常がそれぞれ検出できることを確かめる。
"""

from __future__ import annotations

from src.output_checks import (
    check_all,
    check_broken_paragraphs,
    check_duplicate_lines,
    check_empty_regions,
    check_headings,
    check_running_heads,
    split_pages,
    summarize,
)

LONG_PARAGRAPH = "データ分析のストーリーは、頭のなかで考えるだけでは固まりません。書いて残しておかないと、同じことを何度も考え直してしまいます。"  # noqa: E501


def _layout(texts: list[str], size: tuple[int, int] = (960, 1280)) -> dict:
    return {
        "0001.webp": {
            "regions": [
                {"type": "TEXT", "bbox": [100, 200 + i * 60, 800, 240 + i * 60], "confidence": 1.0, "text": text}
                for i, text in enumerate(texts)
            ],
            "page_size": list(size),
        }
    }


class TestEmptyRegions:
    """layout.json にある本文が出力に無い."""

    def test_page_without_any_region_text_is_reported(self) -> None:
        issues = check_empty_regions({"0001": "別のページの本文だけ"}, _layout(["紙面にある本文"]))

        assert [issue.kind for issue in issues] == ["empty_page"]

    def test_partially_missing_region_is_reported(self) -> None:
        issues = check_empty_regions(
            {"0001": "紙面にある本文"},
            _layout(["紙面にある本文", "抜けている本文"]),
        )

        assert [issue.kind for issue in issues] == ["missing_region"]
        assert issues[0].detail == "抜けている本文"

    def test_running_head_is_not_counted_as_missing(self) -> None:
        from src.layout.running_head import find_running_heads, is_running_head

        layout = {}
        for i, number in enumerate([22, 23, 24]):
            head = {
                "type": "TEXT",
                "bbox": [114, 1194, 500, 1209],
                "confidence": 1.0,
                "text": f"{number} 第1章 データ分析を設計する",
            }
            layout[f"000{i + 1}.webp"] = {
                "regions": [
                    {"type": "TEXT", "bbox": [106, 194, 859, 900], "confidence": 1.0, "text": f"本文{i}"},
                    head,
                ],
                "page_size": [960, 1280],
            }
        # 柱は本文から除くのが正しいので、出力に無くても異常ではない
        heads = find_running_heads(layout)
        assert is_running_head(layout["0001.webp"]["regions"][1], (960, 1280), heads)

        issues = check_empty_regions({"0001": "本文0"}, layout)

        assert [issue.page for issue in issues] == []

    def test_fallback_page_is_skipped(self) -> None:
        issues = check_empty_regions(
            {"0001": "ページ全体 OCR の結果"},
            _layout(["領域の text"]),
            fallback_pages=frozenset({"0001"}),
        )

        assert issues == []


class TestBrokenParagraph:
    """文の途中で切れた段落."""

    def test_paragraph_cut_before_heading(self) -> None:
        body = f"{LONG_PARAGRAPH[:-20]}\n\n## 次の見出し\n\n本文です。"

        assert [issue.kind for issue in check_broken_paragraphs({"0001": body})] == ["broken_paragraph"]

    def test_paragraph_continues_to_next_page(self) -> None:
        body = f"{LONG_PARAGRAPH[:-20]}"
        pages = {"0001": body, "0002": "続きの文章がここから始まります。"}

        assert check_broken_paragraphs(pages) == []

    def test_finished_paragraph_is_not_reported(self) -> None:
        assert check_broken_paragraphs({"0001": f"{LONG_PARAGRAPH}\n\n## 見出し"}) == []


class TestRunningHead:
    """柱・ノンブルの混入."""

    def test_chapter_running_head_is_reported(self) -> None:
        body = "本文です。\n\n22 第1章 データ分析を設計する\n\n次の本文です。"

        assert [issue.kind for issue in check_running_heads({"0001": body})] == ["running_head"]

    def test_page_number_matching_printed_number_is_reported(self) -> None:
        body = "本文です。\n\n113\n\n次の本文です。"

        issues = check_running_heads({"0001": body}, page_numbers={"0001": 113})

        assert [issue.detail for issue in issues] == ["113"]

    def test_footnote_number_is_not_reported(self) -> None:
        """脚注番号は紙面のページ番号と一致しないので拾わない."""
        body = "本文です。\n\n1)\n\n次の本文です。"

        assert check_running_heads({"0001": body}, page_numbers={"0001": 113}) == []

    def test_body_line_is_not_reported(self) -> None:
        assert check_running_heads({"0001": "本文です。\n\n次の本文です。"}) == []


class TestDuplicateLine:
    """同じ行の重複."""

    def test_same_long_paragraph_twice_is_reported(self) -> None:
        body = f"{LONG_PARAGRAPH}\n\n{LONG_PARAGRAPH}"

        assert [issue.kind for issue in check_duplicate_lines({"0001": body})] == ["duplicate_line"]

    def test_short_list_item_repeated_is_not_reported(self) -> None:
        body = "・短い項目\n\n・短い項目"

        assert check_duplicate_lines({"0001": body}) == []


class TestBrokenHeading:
    """見出しの異常."""

    def test_one_character_heading(self) -> None:
        issues = check_headings({"0001": "## 木\n\n本文です。"})

        assert [issue.kind for issue in issues] == ["broken_heading"]

    def test_short_but_valid_heading(self) -> None:
        assert check_headings({"0001": "## 謝辞\n\n本文です。"}) == []

    def test_body_fragment_as_heading(self) -> None:
        issues = check_headings({"0001": "## 本文の断片です。\n\n本文です。"})

        assert [issue.kind for issue in issues] == ["broken_heading"]


class TestSplitPages:
    def test_splits_by_marker(self) -> None:
        pages = split_pages("--- 0001 ---\n\n本文1\n\n--- 0002 ---\n\n本文2\n")

        assert pages == {"0001": "\n\n本文1\n\n", "0002": "\n\n本文2\n"}


class TestCleanBook:
    """異常の無い入力では何も報告しない."""

    def test_clean_book_has_no_issues(self) -> None:
        pages = {"0001": f"## 見出し\n\n{LONG_PARAGRAPH}"}
        layout = _layout([LONG_PARAGRAPH])

        assert check_all(pages, layout) == []
        assert summarize([]) == {}
