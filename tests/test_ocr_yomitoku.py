"""yomitoku の結果から文字を取り出す部分のテスト（モデルは動かさない）."""

from __future__ import annotations

from types import SimpleNamespace

from src.ocr_yomitoku import paragraph_texts


def _paragraph(text: str):
    return SimpleNamespace(contents=text)


class TestParagraphTexts:
    def test_collects_paragraphs(self):
        results = SimpleNamespace(paragraphs=[_paragraph("本文1"), _paragraph("本文2")], figures=[])

        assert paragraph_texts(results) == ["本文1", "本文2"]

    def test_collects_paragraphs_inside_figures(self):
        # 図と判定された領域の段落は results.figures[].paragraphs に入る（#119）
        results = SimpleNamespace(
            paragraphs=[],
            figures=[SimpleNamespace(paragraphs=[_paragraph("図の中の文字")])],
        )

        assert paragraph_texts(results) == ["図の中の文字"]

    def test_keeps_order_and_drops_blank(self):
        results = SimpleNamespace(
            paragraphs=[_paragraph("先頭"), _paragraph("   ")],
            figures=[SimpleNamespace(paragraphs=[_paragraph("図の中")])],
        )

        assert paragraph_texts(results) == ["先頭", "図の中"]

    def test_supports_text_attribute(self):
        results = SimpleNamespace(paragraphs=[SimpleNamespace(text="属性名が text")], figures=[])

        assert paragraph_texts(results) == ["属性名が text"]

    def test_works_without_figures_attribute(self):
        results = SimpleNamespace(paragraphs=[_paragraph("本文")])

        assert paragraph_texts(results) == ["本文"]
