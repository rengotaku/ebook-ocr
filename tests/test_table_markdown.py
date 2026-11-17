"""表を Markdown にする処理のテスト (#101)."""

from __future__ import annotations

from types import SimpleNamespace

from src.layout.table import table_grid, table_regions, table_to_markdown


def cell(row: int, col: int, contents: str, row_span: int = 1, col_span: int = 1) -> SimpleNamespace:
    return SimpleNamespace(
        row=row,
        col=col,
        row_span=row_span,
        col_span=col_span,
        contents=contents,
        box=[0, 0, 10, 10],
    )


def make_table(cells: list, rows: int, cols: int, box: list[int] | None = None) -> SimpleNamespace:
    return SimpleNamespace(n_row=rows, n_col=cols, cells=cells, box=box or [10, 20, 400, 200], score=0.9)


class TestTableGrid:
    def test_cells_are_placed_by_row_and_col(self) -> None:
        table = make_table([cell(1, 1, "項目"), cell(1, 2, "値"), cell(2, 1, "本体価格"), cell(2, 2, "5 万円")], 2, 2)

        assert table_grid(table) == [["項目", "値"], ["本体価格", "5 万円"]]

    def test_empty_cell_does_not_shift_columns(self) -> None:
        """空のセルがあっても列を詰めない."""
        table = make_table([cell(1, 1, "A"), cell(1, 3, "C"), cell(2, 1, "1"), cell(2, 2, "2")], 2, 3)

        assert table_grid(table) == [["A", "", "C"], ["1", "2", ""]]

    def test_span_text_stays_in_top_left(self) -> None:
        table = make_table([cell(1, 1, "結合", col_span=2), cell(1, 3, "X"), cell(2, 1, "a"), cell(2, 2, "b")], 2, 3)

        assert table_grid(table) == [["結合", "", "X"], ["a", "b", ""]]


class TestTableToMarkdown:
    def test_builds_markdown_table(self) -> None:
        table = make_table([cell(1, 1, "項目"), cell(1, 2, "値"), cell(2, 1, "本体価格"), cell(2, 2, "5 万円")], 2, 2)

        assert table_to_markdown(table) == "| 項目 | 値 |\n| --- | --- |\n| 本体価格 | 5 万円 |"

    def test_pipe_and_newline_in_cell(self) -> None:
        table = make_table([cell(1, 1, "A|B"), cell(1, 2, "1"), cell(2, 1, "改行\nあり"), cell(2, 2, "2")], 2, 2)

        markdown = table_to_markdown(table)

        assert "A\\|B" in markdown
        assert "改行<br>あり" in markdown

    def test_one_row_is_not_a_table(self) -> None:
        table = make_table([cell(1, 1, "A"), cell(1, 2, "B")], 1, 2)

        assert table_to_markdown(table) == ""

    def test_one_column_is_not_a_table(self) -> None:
        table = make_table([cell(1, 1, "A"), cell(2, 1, "B")], 2, 1)

        assert table_to_markdown(table) == ""


class TestTableRegions:
    def test_builds_table_region(self) -> None:
        table = make_table([cell(1, 1, "A"), cell(1, 2, "B"), cell(2, 1, "1"), cell(2, 2, "2")], 2, 2)

        regions = table_regions([table])

        assert len(regions) == 1
        assert regions[0]["type"] == "TABLE"
        assert regions[0]["bbox"] == [10, 20, 400, 200]
        assert regions[0]["text"].startswith("| A | B |")

    def test_unbuildable_table_is_dropped(self) -> None:
        table = make_table([cell(1, 1, "A")], 1, 1)

        assert table_regions([table]) == []

    def test_table_without_box_is_dropped(self) -> None:
        table = make_table([cell(1, 1, "A"), cell(1, 2, "B"), cell(2, 1, "1"), cell(2, 2, "2")], 2, 2)
        table.box = None

        assert table_regions([table]) == []


class TestDetectorIntegration:
    """表があるとき、図ではなく TABLE 領域になる."""

    def test_figure_covering_the_table_is_replaced(self) -> None:
        from unittest.mock import MagicMock

        from src.layout.detector import paragraphs_to_layout

        table = make_table([cell(1, 1, "A"), cell(1, 2, "B"), cell(2, 1, "1"), cell(2, 2, "2")], 2, 2)
        table.box = [100, 100, 400, 300]

        figure = MagicMock()
        figure.box = [100, 100, 400, 300]
        figure.paragraphs = []

        result = paragraphs_to_layout([], [figure], (800, 600), tables=[table])

        types = [region["type"] for region in result["regions"]]
        assert types == ["TABLE"]
        assert result["regions"][0]["text"].startswith("| A | B |")

    def test_text_outside_the_table_is_kept(self) -> None:
        from unittest.mock import MagicMock

        from src.layout.detector import paragraphs_to_layout

        table = make_table([cell(1, 1, "A"), cell(1, 2, "B"), cell(2, 1, "1"), cell(2, 2, "2")], 2, 2)
        table.box = [100, 100, 400, 300]

        paragraph = MagicMock()
        paragraph.box = [100, 400, 400, 500]
        paragraph.role = "plain text"
        paragraph.contents = "表の下の本文"

        result = paragraphs_to_layout([paragraph], [], (800, 600), tables=[table])

        types = sorted(region["type"] for region in result["regions"])
        assert types == ["TABLE", "TEXT"]


class TestMarkdownReady:
    """崩れた表は Markdown にしない."""

    def test_dense_table_is_ready(self) -> None:
        from src.layout.table import is_markdown_ready

        assert is_markdown_ready([["A", "B"], ["1", "2"]]) is True

    def test_half_empty_table_is_not_ready(self) -> None:
        from src.layout.table import is_markdown_ready

        assert is_markdown_ready([["A", ""], ["", "2"], ["", ""], ["3", ""]]) is False

    def test_many_empty_rows_is_not_ready(self) -> None:
        from src.layout.table import is_markdown_ready

        assert is_markdown_ready([["A", "B"], ["", ""], ["1", "2"], ["", ""]]) is False

    def test_too_many_columns_is_not_ready(self) -> None:
        from src.layout.table import is_markdown_ready

        grid = [["x"] * 13, ["y"] * 13]

        assert is_markdown_ready(grid) is False

    def test_table_with_an_empty_column_is_not_ready(self) -> None:
        # アイコン（●■◆）の列や罫線の写り込みが混じるグラフィック（#120）
        from src.layout.table import is_markdown_ready

        grid = [
            ["機能の充足", "", "経済性", "", "安全性"],
            ["ボイスメモ", "", "本体価格", "", "ウイルス耐性"],
            ["電子マネー", "", "月額料金", "", "本体の頑丈さ"],
        ]

        assert is_markdown_ready(grid) is False

    def test_table_with_a_sparse_column_is_ready(self) -> None:
        # 空が半分程度の列は許す（結合セルで 1 マスだけ空く形は実在する）
        from src.layout.table import is_markdown_ready

        grid = [
            ["A", "B", "C"],
            ["1", "", "3"],
            ["4", "", "6"],
            ["7", "8", "9"],
        ]

        assert is_markdown_ready(grid) is True


class TestUnstableTables:
    def test_unstable_table_boxes_are_returned(self) -> None:
        from src.layout.table import unstable_table_boxes

        table = make_table([cell(1, 1, "A")], 1, 1, box=[1, 2, 3, 4])

        assert unstable_table_boxes([table]) == [[1, 2, 3, 4]]

    def test_stable_table_is_not_returned(self) -> None:
        from src.layout.table import unstable_table_boxes

        table = make_table([cell(1, 1, "A"), cell(1, 2, "B"), cell(2, 1, "1"), cell(2, 2, "2")], 2, 2)

        assert unstable_table_boxes([table]) == []


class TestDetectorTableNote:
    """崩れた表の図には注記が付く."""

    def test_figure_covering_unstable_table_gets_note(self) -> None:
        from unittest.mock import MagicMock

        from src.layout.detector import paragraphs_to_layout

        table = make_table([cell(1, 1, "A")], 1, 1, box=[100, 100, 400, 300])

        figure = MagicMock()
        figure.box = [100, 100, 400, 300]
        figure.paragraphs = []

        result = paragraphs_to_layout([], [figure], (800, 600), tables=[table])

        assert [region["type"] for region in result["regions"]] == ["FIGURE"]
        assert result["regions"][0].get("table_note") is True


class TestTrailingEmptyRows:
    """表の末尾の空行は落としてから判定する."""

    def test_trailing_empty_row_is_trimmed(self) -> None:
        table = make_table(
            [cell(1, 1, "A"), cell(1, 2, "B"), cell(2, 1, "1"), cell(2, 2, "2")],
            rows=3,
            cols=2,
        )

        assert table_grid(table) == [["A", "B"], ["1", "2"]]
        assert table_to_markdown(table) == "| A | B |\n| --- | --- |\n| 1 | 2 |"
