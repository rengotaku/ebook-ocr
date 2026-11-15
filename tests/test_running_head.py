"""柱・ノンブルを本文から除く処理のテスト (#98)."""

from __future__ import annotations

from src.layout.running_head import (
    find_running_heads,
    in_margin_band,
    is_running_head,
    normalize_running_head_text,
    printed_page_number,
    strip_running_head_lines,
)


def _page(regions: list[dict], size: tuple[int, int] = (960, 1280)) -> dict:
    return {"regions": regions, "page_size": list(size)}


def _region(text: str, bbox: list[int], region_type: str = "TEXT") -> dict:
    return {"type": region_type, "bbox": bbox, "confidence": 1.0, "text": text}


class TestNormalizeRunningHeadText:
    """柱を見比べるための正規化。"""

    def test_leading_page_number_and_trailing_number_match(self) -> None:
        a = normalize_running_head_text("22 第1章 データ分析を設計する")
        b = normalize_running_head_text("第1章 データ分析を設計する 22")
        assert a == b

    def test_different_chapter_titles_do_not_match(self) -> None:
        a = normalize_running_head_text("22 第1章 データ分析を設計する")
        b = normalize_running_head_text("23 第2章 データを事前にチェックする")
        assert a != b

    def test_page_number_only_becomes_empty(self) -> None:
        assert normalize_running_head_text("22") == ""
        assert normalize_running_head_text(" ⅲ ") == ""


class TestInMarginBand:
    """上端・下端の帯の判定。"""

    def test_bottom_line_is_in_band(self) -> None:
        region = _region("22 第1章 データ分析を設計する", [100, 1194, 400, 1209])
        assert in_margin_band(region, 1280) is True

    def test_body_line_is_not_in_band(self) -> None:
        region = _region("本文", [100, 194, 850, 268])
        assert in_margin_band(region, 1280) is False

    def test_zero_page_height(self) -> None:
        region = _region("22", [100, 1194, 400, 1209])
        assert in_margin_band(region, 0) is False


class TestFindRunningHeads:
    """複数ページに繰り返す行を柱として集める。"""

    def test_repeated_bottom_line_is_collected(self) -> None:
        layout = {}
        for i, number in enumerate([22, 23, 24]):
            layout[f"{i:04d}.webp"] = _page(
                [
                    _region("本文です。", [100, 200, 850, 800]),
                    _region(f"{number} 第1章 データ分析を設計する", [114, 1194, 500, 1209]),
                ]
            )

        heads = find_running_heads(layout)

        assert normalize_running_head_text("22 第1章 データ分析を設計する") in heads

    def test_line_on_two_pages_is_not_collected(self) -> None:
        layout = {
            "0000.webp": _page([_region("第1章 データ分析を設計する 22", [100, 1194, 500, 1209])]),
            "0001.webp": _page([_region("第1章 データ分析を設計する 23", [100, 1194, 500, 1209])]),
        }

        assert find_running_heads(layout) == frozenset()

    def test_same_line_in_body_is_not_collected(self) -> None:
        layout = {}
        for i in range(3):
            layout[f"{i:04d}.webp"] = _page([_region("章の名前", [100, 400, 500, 500])])

        assert find_running_heads(layout) == frozenset()


class TestIsRunningHead:
    """1 領域が柱・ノンブルかどうか。"""

    def test_page_number_only_is_running_head(self) -> None:
        region = _region("23", [400, 1194, 450, 1209])
        assert is_running_head(region, (960, 1280), frozenset()) is True

    def test_roman_page_number_is_running_head(self) -> None:
        region = _region("ⅲ", [400, 1194, 450, 1209])
        assert is_running_head(region, (960, 1280), frozenset()) is True

    def test_repeated_head_in_band_is_running_head(self) -> None:
        heads = find_running_heads(
            {
                f"{i:04d}.webp": _page([_region(f"第1章 章の名前 {n}", [100, 1194, 500, 1209])])
                for i, n in enumerate([10, 11, 12])
            }
        )
        region = _region("第1章 章の名前 22", [114, 1194, 500, 1209])

        assert is_running_head(region, (960, 1280), heads) is True

    def test_same_text_in_body_is_kept(self) -> None:
        heads = find_running_heads(
            {
                f"{i:04d}.webp": _page([_region(f"第1章 章の名前 {n}", [100, 1194, 500, 1209])])
                for i, n in enumerate([10, 11, 12])
            }
        )
        region = _region("第1章 章の名前 22", [114, 600, 500, 640])

        assert is_running_head(region, (960, 1280), heads) is False


class TestStripRunningHeadLines:
    """ページ全体 OCR の結果から先頭・末尾の柱・ノンブルを落とす。"""

    def test_trailing_page_number_is_removed(self) -> None:
        text = "本文の 1 行目\n本文の 2 行目\n14 目次"
        heads = frozenset({normalize_running_head_text("15 目次")})

        assert strip_running_head_lines(text, heads) == "本文の 1 行目\n本文の 2 行目"

    def test_leading_page_number_is_removed(self) -> None:
        text = "23\n本文の 1 行目"
        assert strip_running_head_lines(text, frozenset()) == "本文の 1 行目"

    def test_body_lines_are_kept(self) -> None:
        text = "本文の 1 行目\n本文の 2 行目"
        assert strip_running_head_lines(text, frozenset()) == text

    def test_line_in_the_middle_is_kept(self) -> None:
        text = "本文の 1 行目\n22\n本文の 2 行目"
        assert strip_running_head_lines(text, frozenset()) == text

    def test_page_head_is_removed_even_in_the_middle(self) -> None:
        """座標から柱と分かっている行は、OCR 結果の途中にあっても落とす."""
        text = "本文の 1 行目\n23 第2章 データを事前にチェックする\n本文の 2 行目"
        page_heads = frozenset({normalize_running_head_text("23 第2章 データを事前にチェックする")})

        assert strip_running_head_lines(text, frozenset(), page_heads) == "本文の 1 行目\n本文の 2 行目"


class TestPrintedPageNumber:
    """柱から紙面のページ番号（ノンブル）を取り出す."""

    def test_number_only(self) -> None:
        assert printed_page_number(_region("23", [430, 1194, 470, 1209])) == 23

    def test_leading_number(self) -> None:
        assert printed_page_number(_region("22 第1章 データ分析を設計する", [114, 1194, 500, 1209])) == 22

    def test_trailing_number(self) -> None:
        assert printed_page_number(_region("第1章 データ分析を設計する 23", [100, 1194, 500, 1209])) == 23

    def test_toc_head(self) -> None:
        assert printed_page_number(_region("14 目次", [100, 1193, 300, 1210])) == 14

    def test_roman_numeral_is_not_a_number(self) -> None:
        """前付のローマ数字は推測で埋めない."""
        assert printed_page_number(_region("ⅲ", [430, 1194, 470, 1209])) is None

    def test_no_number(self) -> None:
        assert (
            printed_page_number(_region("参考資料 本書のワークで使うエクセルの主な操作", [100, 1194, 800, 1210]))
            is None
        )
