"""Tests for bullet marker cleanup in book converter."""

from __future__ import annotations

from src.book_converter.bullet_cleanup import (
    merge_bullet_paragraphs_to_lists,
    strip_heading_markers,
)
from src.book_converter.models import (
    CodeBlock,
    Heading,
    List,
    Paragraph,
)


class TestStripHeadingMarkers:
    """heading 先頭の箇条書き記号を除去するテスト"""

    def test_strip_triangle_marker(self) -> None:
        h = Heading(level=2, text="▶対象とする読者")
        result = strip_heading_markers(h)
        assert result.text == "対象とする読者"
        assert result.level == 2

    def test_strip_square_marker(self) -> None:
        h = Heading(level=2, text="■免責")
        result = strip_heading_markers(h)
        assert result.text == "免責"

    def test_strip_circle_marker(self) -> None:
        h = Heading(level=2, text="●ご質問方法")
        result = strip_heading_markers(h)
        assert result.text == "ご質問方法"

    def test_strip_marker_with_space(self) -> None:
        h = Heading(level=2, text="▶ 対象とする読者")
        result = strip_heading_markers(h)
        assert result.text == "対象とする読者"

    def test_no_marker_unchanged(self) -> None:
        h = Heading(level=2, text="対象とする読者")
        result = strip_heading_markers(h)
        assert result.text == "対象とする読者"

    def test_preserves_read_aloud(self) -> None:
        h = Heading(level=2, text="▶謝辞", read_aloud=False)
        result = strip_heading_markers(h)
        assert result.text == "謝辞"
        assert result.read_aloud is False

    def test_preserves_line_number_and_page(self) -> None:
        h = Heading(level=3, text="▶ビジネスへの影響", line_number=42, page="15")
        result = strip_heading_markers(h)
        assert result.text == "ビジネスへの影響"
        assert result.line_number == 42
        assert result.page == "15"

    def test_numbered_heading_with_marker(self) -> None:
        h = Heading(level=2, text="▶3. 定期的なレビュー")
        result = strip_heading_markers(h)
        assert result.text == "3. 定期的なレビュー"

    def test_dot_marker(self) -> None:
        h = Heading(level=2, text="・概要")
        result = strip_heading_markers(h)
        assert result.text == "概要"

    def test_diamond_marker(self) -> None:
        h = Heading(level=2, text="◆重要なポイント")
        result = strip_heading_markers(h)
        assert result.text == "重要なポイント"

    def test_arrow_not_stripped(self) -> None:
        """→ はBULLET_MARKERSに含まれないので除去しない"""
        h = Heading(level=2, text="→次のステップ")
        result = strip_heading_markers(h)
        assert result.text == "→次のステップ"


class TestMergeBulletParagraphsToLists:
    """連続する記号付き paragraph を list に変換するテスト"""

    def test_two_consecutive_bullets_become_list(self) -> None:
        elements = (
            Paragraph(text="●コードの品質が大事な理由"),
            Paragraph(text="●高品質なコードが達成すべき4つのゴール"),
        )
        result = merge_bullet_paragraphs_to_lists(elements)
        assert len(result) == 1
        assert isinstance(result[0], List)
        assert result[0].items == (
            "コードの品質が大事な理由",
            "高品質なコードが達成すべき4つのゴール",
        )

    def test_three_consecutive_bullets(self) -> None:
        elements = (
            Paragraph(text="■ サーバーのURL"),
            Paragraph(text="■ メッセージ文字列の送信"),
            Paragraph(text="■文字列から送信可能なフォーマットへのシリアライズ"),
        )
        result = merge_bullet_paragraphs_to_lists(elements)
        assert len(result) == 1
        assert isinstance(result[0], List)
        assert len(result[0].items) == 3
        assert result[0].items[0] == "サーバーのURL"

    def test_single_bullet_not_converted(self) -> None:
        elements = (
            Paragraph(text="●孤立した項目"),
            Paragraph(text="通常のテキスト"),
        )
        result = merge_bullet_paragraphs_to_lists(elements)
        assert len(result) == 2
        assert isinstance(result[0], Paragraph)
        assert isinstance(result[1], Paragraph)

    def test_non_bullet_paragraphs_unchanged(self) -> None:
        elements = (
            Paragraph(text="通常のテキスト1"),
            Paragraph(text="通常のテキスト2"),
        )
        result = merge_bullet_paragraphs_to_lists(elements)
        assert len(result) == 2
        assert all(isinstance(e, Paragraph) for e in result)

    def test_mixed_elements_preserved(self) -> None:
        elements = (
            Paragraph(text="本章の内容"),
            Paragraph(text="●コードの品質が大事な理由"),
            Paragraph(text="●高品質なコードが達成すべき4つのゴール"),
            Paragraph(text="●高品質のコードを書くことで時間と労力を節約する方法"),
            Paragraph(text="これまでに、さまざまなソフトウェアを利用してきたでしょう。"),
        )
        result = merge_bullet_paragraphs_to_lists(elements)
        assert len(result) == 3
        assert isinstance(result[0], Paragraph)
        assert result[0].text == "本章の内容"
        assert isinstance(result[1], List)
        assert len(result[1].items) == 3
        assert isinstance(result[2], Paragraph)

    def test_heading_breaks_bullet_run(self) -> None:
        elements = (
            Paragraph(text="●項目1"),
            Heading(level=2, text="見出し"),
            Paragraph(text="●項目2"),
        )
        result = merge_bullet_paragraphs_to_lists(elements)
        assert len(result) == 3
        assert isinstance(result[0], Paragraph)  # 孤立 → 変換なし
        assert isinstance(result[1], Heading)
        assert isinstance(result[2], Paragraph)  # 孤立 → 変換なし

    def test_different_markers_not_merged(self) -> None:
        """異なる記号は別のリストとして扱う"""
        elements = (
            Paragraph(text="●項目A"),
            Paragraph(text="■項目B"),
        )
        result = merge_bullet_paragraphs_to_lists(elements)
        # 異なる記号なので連続としない
        assert len(result) == 2
        assert isinstance(result[0], Paragraph)
        assert isinstance(result[1], Paragraph)

    def test_same_marker_required(self) -> None:
        """同一記号のみ連続とみなす"""
        elements = (
            Paragraph(text="■項目1"),
            Paragraph(text="■項目2"),
            Paragraph(text="●項目3"),
            Paragraph(text="●項目4"),
        )
        result = merge_bullet_paragraphs_to_lists(elements)
        assert len(result) == 2
        assert isinstance(result[0], List)
        assert result[0].items == ("項目1", "項目2")
        assert isinstance(result[1], List)
        assert result[1].items == ("項目3", "項目4")

    def test_preserves_read_aloud_true(self) -> None:
        elements = (
            Paragraph(text="●項目1", read_aloud=True),
            Paragraph(text="●項目2", read_aloud=True),
        )
        result = merge_bullet_paragraphs_to_lists(elements)
        assert isinstance(result[0], List)
        assert result[0].read_aloud is True

    def test_preserves_read_aloud_false(self) -> None:
        elements = (
            Paragraph(text="●項目1", read_aloud=False),
            Paragraph(text="●項目2", read_aloud=False),
        )
        result = merge_bullet_paragraphs_to_lists(elements)
        assert isinstance(result[0], List)
        assert result[0].read_aloud is False

    def test_empty_elements(self) -> None:
        result = merge_bullet_paragraphs_to_lists(())
        assert result == ()

    def test_code_block_not_affected(self) -> None:
        elements = (
            CodeBlock(text="print('hello')"),
            Paragraph(text="●項目1"),
            Paragraph(text="●項目2"),
        )
        result = merge_bullet_paragraphs_to_lists(elements)
        assert len(result) == 2
        assert isinstance(result[0], CodeBlock)
        assert isinstance(result[1], List)

    def test_multiple_runs_in_sequence(self) -> None:
        elements = (
            Paragraph(text="●項目A1"),
            Paragraph(text="●項目A2"),
            Paragraph(text="通常テキスト"),
            Paragraph(text="■項目B1"),
            Paragraph(text="■項目B2"),
        )
        result = merge_bullet_paragraphs_to_lists(elements)
        assert len(result) == 3
        assert isinstance(result[0], List)
        assert result[0].items == ("項目A1", "項目A2")
        assert isinstance(result[1], Paragraph)
        assert isinstance(result[2], List)
        assert result[2].items == ("項目B1", "項目B2")
