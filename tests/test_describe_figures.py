"""図の切り出しと VLM の説明差し込みのテスト（Ollama には接続しない）."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from src.describe_figures import (
    Figure,
    OllamaUnavailable,
    crop_figures,
    describe_book,
    describe_image,
    figure_block,
    page_figures,
)


def _pages_dir(tmp_path: Path) -> Path:
    pages = tmp_path / "pages"
    pages.mkdir()
    return pages


def _book(tmp_path: Path) -> Path:
    book = tmp_path / "book.md"
    book.write_text(
        "\n--- 0001 ---\n本文1\n\n--- 0002 ---\n本文2\n\n--- 0003 ---\n本文3\n",
        encoding="utf-8",
    )
    return book


class TestPageFigures:
    def test_includes_figure_and_code_only(self):
        layout_page = {
            "regions": [
                {"type": "TEXT", "bbox": [0, 0, 100, 100]},
                {"type": "FIGURE", "bbox": [0, 0, 50, 50]},
                {"type": "CODE", "bbox": [0, 0, 80, 80]},
            ]
        }
        types = [region["type"] for region in page_figures(layout_page)]
        assert types == ["CODE", "FIGURE"]

    def test_sorts_by_area(self):
        layout_page = {
            "regions": [
                {"type": "FIGURE", "bbox": [0, 0, 10, 10]},
                {"type": "FIGURE", "bbox": [0, 0, 40, 40]},
            ]
        }
        areas = [region["bbox"][2] for region in page_figures(layout_page)]
        assert areas == [40, 10]

    def test_empty_page(self):
        assert page_figures({}) == []


class TestCropFigures:
    def test_saves_crop_with_page_stem(self, tmp_path: Path):
        page = tmp_path / "0002.webp"
        Image.new("RGB", (120, 200), "white").save(page, lossless=True)
        figures_dir = tmp_path / "figures"

        cropped = crop_figures(page, [{"type": "FIGURE", "bbox": [10, 20, 60, 120]}], figures_dir)

        assert len(cropped) == 1
        assert cropped[0][1].name == "0002_fig1.png"
        with Image.open(cropped[0][1]) as image:
            assert image.size == (50, 100)

    def test_clamps_bbox_to_image(self, tmp_path: Path):
        page = tmp_path / "0003.png"
        Image.new("RGB", (100, 100), "white").save(page)

        cropped = crop_figures(page, [{"type": "CODE", "bbox": [50, 50, 500, 500]}], tmp_path / "figures")

        with Image.open(cropped[0][1]) as image:
            assert image.size == (50, 50)

    def test_skips_empty_bbox(self, tmp_path: Path):
        page = tmp_path / "0004.png"
        Image.new("RGB", (100, 100), "white").save(page)
        assert crop_figures(page, [{"type": "FIGURE", "bbox": [10, 10, 10, 10]}], tmp_path / "figures") == []

    def test_no_regions(self, tmp_path: Path):
        page = tmp_path / "0005.png"
        Image.new("RGB", (100, 100), "white").save(page)
        assert crop_figures(page, [], tmp_path / "figures") == []


class TestDescribeImage:
    @staticmethod
    def _image(tmp_path: Path) -> Path:
        path = tmp_path / "crop.png"
        Image.new("RGB", (10, 10), "white").save(path)
        return path

    def test_returns_text(self, tmp_path: Path):
        calls = []

        def chat(path, **kwargs):
            calls.append(path)
            return "図の説明"

        assert describe_image(self._image(tmp_path), chat=chat) == "図の説明"
        assert len(calls) == 1

    def test_retries_on_empty_content(self, tmp_path: Path):
        responses = ["", "", "3 回目で成功"]

        def chat(path, **kwargs):
            return responses.pop(0)

        assert describe_image(self._image(tmp_path), chat=chat) == "3 回目で成功"

    def test_gives_up_after_retries(self, tmp_path: Path):
        calls = []

        def chat(path, **kwargs):
            calls.append(path)
            return ""

        assert describe_image(self._image(tmp_path), retries=2, fallback_model=None, chat=chat) == ""
        assert len(calls) == 3

    def test_raises_when_ollama_is_unavailable(self, tmp_path: Path):
        def chat(path, **kwargs):
            raise OllamaUnavailable("接続できない")

        try:
            describe_image(self._image(tmp_path), chat=chat)
        except OllamaUnavailable:
            return
        raise AssertionError("OllamaUnavailable が送出されていない")


class TestFigureBlock:
    def test_format(self, tmp_path: Path):
        figure = Figure(page="0002", index=1, path=tmp_path / "0002_fig1.png", description="説明文")
        assert figure_block(figure, "figures") == "![図](figures/0002_fig1.png)\n\n**図**: 説明文\n"

    def test_empty_description(self, tmp_path: Path):
        figure = Figure(page="0002", index=1, path=tmp_path / "0002_fig1.png", description="")
        assert "（説明なし）" in figure_block(figure, "figures")


class TestDescribeBook:
    @staticmethod
    def _layout(tmp_path: Path, pages: list[str]) -> Path:
        layout_path = tmp_path / "layout.json"
        layout_path.write_text(
            json.dumps({f"{page}.webp": {"regions": [{"type": "FIGURE", "bbox": [0, 0, 50, 50]}]} for page in pages}),
            encoding="utf-8",
        )
        return layout_path

    def test_inserts_block_at_end_of_page(self, tmp_path: Path):
        pages = _pages_dir(tmp_path)
        Image.new("RGB", (100, 100), "white").save(pages / "0002.webp", lossless=True)
        book = _book(tmp_path)
        layout = json.loads(self._layout(tmp_path, ["0002"]).read_text(encoding="utf-8"))

        text, figures = describe_book(
            book,
            layout,
            pages,
            tmp_path / "figures",
            describe=lambda path, **kwargs: "所得分布の棒グラフ",
        )

        assert len(figures) == 1
        assert "![図](figures/0002_fig1.png)" in text
        assert "**図**: 所得分布の棒グラフ" in text
        # 図があるページの後ろに入る（0003 の本文より前）
        assert text.index("**図**: 所得分布の棒グラフ") < text.index("--- 0003 ---")

    def test_pages_without_figures_are_unchanged(self, tmp_path: Path):
        pages = _pages_dir(tmp_path)
        book = _book(tmp_path)
        before = book.read_text(encoding="utf-8")

        text, figures = describe_book(book, {}, pages, tmp_path / "figures", describe=lambda path, **kwargs: "説明")

        assert figures == []
        assert text == before

    def test_keeps_text_when_ollama_is_down(self, tmp_path: Path):
        pages = _pages_dir(tmp_path)
        Image.new("RGB", (100, 100), "white").save(pages / "0002.webp", lossless=True)
        book = _book(tmp_path)
        before = book.read_text(encoding="utf-8")
        layout = json.loads(self._layout(tmp_path, ["0002"]).read_text(encoding="utf-8"))

        def unavailable(path, **kwargs):
            raise OllamaUnavailable("接続できない")

        text, figures = describe_book(book, layout, pages, tmp_path / "figures", describe=unavailable)

        assert figures == []
        assert text == before

    def test_skips_page_without_image(self, tmp_path: Path):
        pages = _pages_dir(tmp_path)
        book = _book(tmp_path)
        layout = json.loads(self._layout(tmp_path, ["0002"]).read_text(encoding="utf-8"))

        text, figures = describe_book(book, layout, pages, tmp_path / "figures", describe=lambda path, **k: "説明")

        assert figures == []
        assert "**図**" not in text


class TestMinimumArea:
    def test_small_regions_are_ignored(self):
        page = {
            "page_size": [1000, 1000],
            "regions": [
                {"type": "FIGURE", "bbox": [0, 0, 500, 500]},  # 25%
                {"type": "FIGURE", "bbox": [0, 0, 50, 50]},  # 0.25%
            ],
        }
        assert len(page_figures(page)) == 1

    def test_threshold_is_configurable(self):
        page = {
            "page_size": [1000, 1000],
            "regions": [{"type": "FIGURE", "bbox": [0, 0, 50, 50]}],
        }
        assert page_figures(page) == []
        assert len(page_figures(page, min_area_ratio=0.0)) == 1


class TestFallbackModel:
    @staticmethod
    def _image(tmp_path: Path) -> Path:
        path = tmp_path / "crop.png"
        Image.new("RGB", (10, 10), "white").save(path)
        return path

    def test_uses_fallback_when_primary_is_empty(self, tmp_path: Path):
        calls = []

        def chat(path, model=..., **kwargs):
            calls.append(model)
            return "" if model == "primary" else "控えのモデルの説明"

        text = describe_image(self._image(tmp_path), model="primary", fallback_model="backup", retries=0, chat=chat)

        assert text == "控えのモデルの説明"
        assert calls == ["primary", "backup"]

    def test_no_fallback_when_disabled(self, tmp_path: Path):
        calls = []

        def chat(path, model=..., **kwargs):
            calls.append(model)
            return ""

        assert describe_image(self._image(tmp_path), fallback_model=None, retries=0, chat=chat) == ""
        assert len(calls) == 1
