"""図の切り出しと VLM の説明差し込みのテスト（Ollama には接続しない）."""

from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from src.describe_figures import (
    Figure,
    OllamaUnavailable,
    clean_figure_text,
    crop_figures,
    describe_book,
    describe_image,
    drop_body_repeats,
    figure_block,
    figure_text,
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
        # 再試行 3 回 + 短い指示 1 回
        assert len(calls) == 4

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
        figure = Figure(page="0002", index=1, path=tmp_path / "0002_fig1.png", description="説明文", kind="表")
        assert figure_block(figure, "figures") == ("![図](figures/0002_fig1.png)\n\n**図（表・自動生成）**: 説明文\n")

    def test_kind_is_omitted_when_unknown(self, tmp_path: Path):
        figure = Figure(page="0002", index=1, path=tmp_path / "0002_fig1.png", description="説明文")
        assert "**図（自動生成）**: 説明文" in figure_block(figure, "figures")

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
        assert "**図（自動生成）**: 所得分布の棒グラフ" in text
        # 図があるページの後ろに入る（0003 の本文より前）
        assert text.index("**図（自動生成）**: 所得分布の棒グラフ") < text.index("--- 0003 ---")

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
        # primary（通常）→ primary（短い指示）→ backup
        assert calls == ["primary", "primary", "backup"]

    def test_no_fallback_when_disabled(self, tmp_path: Path):
        calls = []

        def chat(path, model=..., **kwargs):
            calls.append(model)
            return ""

        assert describe_image(self._image(tmp_path), fallback_model=None, retries=0, chat=chat) == ""
        # 通常の指示 1 回 + 短い指示 1 回
        assert len(calls) == 2


class TestBriefPromptRetry:
    @staticmethod
    def _image(tmp_path: Path) -> Path:
        path = tmp_path / "crop.png"
        Image.new("RGB", (10, 10), "white").save(path)
        return path

    def test_retries_with_brief_prompt_before_switching_model(self, tmp_path: Path):
        from src.describe_figures import PROMPT, PROMPT_BRIEF

        calls = []

        def chat(path, model=..., prompt=PROMPT, **kwargs):
            calls.append((model, prompt))
            return "短い指示で返った" if prompt == PROMPT_BRIEF else ""

        text = describe_image(self._image(tmp_path), model="primary", fallback_model="backup", retries=0, chat=chat)

        assert text == "短い指示で返った"
        assert calls == [("primary", PROMPT), ("primary", PROMPT_BRIEF)]

    def test_falls_back_to_model_after_brief_prompt_fails(self, tmp_path: Path):
        from src.describe_figures import PROMPT_BRIEF

        calls = []

        def chat(path, model=..., prompt=..., **kwargs):
            calls.append((model, prompt))
            return "控えの説明" if model == "backup" else ""

        text = describe_image(self._image(tmp_path), model="primary", fallback_model="backup", retries=0, chat=chat)

        assert text == "控えの説明"
        assert [c[0] for c in calls] == ["primary", "primary", "backup"]
        assert calls[1][1] == PROMPT_BRIEF


class TestAspectRatioFilter:
    def test_wide_strip_is_not_a_figure(self):
        page = {
            "page_size": [960, 1280],
            "regions": [
                {"type": "CODE", "bbox": [100, 687, 854, 735]},  # 754x48 = 15.7 倍
                {"type": "FIGURE", "bbox": [133, 143, 820, 576]},  # 687x433 = 1.6 倍
            ],
        }
        kept = page_figures(page)
        assert len(kept) == 1
        assert kept[0]["bbox"] == [133, 143, 820, 576]

    def test_threshold_is_configurable(self):
        page = {"page_size": [960, 1280], "regions": [{"type": "CODE", "bbox": [0, 0, 800, 100]}]}
        assert page_figures(page) == []
        assert len(page_figures(page, max_aspect_ratio=20.0)) == 1

    def test_zero_height_is_treated_as_infinite_aspect(self):
        page = {"page_size": [960, 1280], "regions": [{"type": "FIGURE", "bbox": [10, 10, 200, 10]}]}
        assert page_figures(page) == []


class TestParseDescription:
    """VLM の出力から種別と内容を取り出す (#100)."""

    def test_parses_kind_and_content(self):
        from src.describe_figures import parse_description

        kind, content = parse_description("種別: 表\n内容: スマホの要件表で、ボイスメモや本体価格が並んでいる。")

        assert kind == "表"
        assert content == "スマホの要件表で、ボイスメモや本体価格が並んでいる。"

    def test_unknown_kind_is_dropped(self):
        from src.describe_figures import parse_description

        kind, content = parse_description("種別: 魚の骨図\n内容: 要因を並べた図。")

        assert kind == ""
        assert content == "要因を並べた図。"

    def test_unformatted_output_is_kept_as_content(self):
        from src.describe_figures import parse_description

        kind, content = parse_description("所得分布の棒グラフです。")

        assert kind == ""
        assert content == "所得分布の棒グラフです。"

    def test_content_lines_are_joined(self):
        from src.describe_figures import parse_description

        kind, content = parse_description("種別: グラフ\n内容: 1 行目\n2 行目")

        assert kind == "グラフ"
        assert content == "1 行目2 行目"


class TestFigurePrompt:
    """プロンプトが種別の語彙を限定していること (#100)."""

    def test_prompt_lists_only_known_kinds(self):
        from src.describe_figures import FIGURE_KINDS, PROMPT

        for kind in FIGURE_KINDS:
            assert kind in PROMPT
        assert "魚の骨図" in PROMPT  # 使わない例として挙げている
        assert "固有名詞は使わない" in PROMPT


class TestTableNote:
    """表として組み立てられなかった図に注記を出す (#101)."""

    def test_note_is_rendered(self, tmp_path: Path):
        from src.layout.table import UNSTRUCTURED_NOTE

        figure = Figure(
            page="0002",
            index=1,
            path=tmp_path / "0002_fig1.png",
            description="説明文",
            kind="表",
            note=UNSTRUCTURED_NOTE,
        )

        block = figure_block(figure, "figures")

        assert f"*{UNSTRUCTURED_NOTE}*" in block

    def test_note_comes_from_region(self, tmp_path: Path):
        from src.layout.table import UNSTRUCTURED_NOTE

        pages = _pages_dir(tmp_path)
        Image.new("RGB", (100, 100), "white").save(pages / "0002.webp", lossless=True)
        book = _book(tmp_path)
        layout = {
            "0002.webp": {
                "regions": [{"type": "FIGURE", "bbox": [0, 0, 50, 50], "table_note": True}],
                "page_size": [100, 100],
            }
        }

        text, figures = describe_book(book, layout, pages, tmp_path / "figures", describe=lambda path, **kwargs: "説明")

        assert figures[0].note == UNSTRUCTURED_NOTE
        assert UNSTRUCTURED_NOTE in text


class TestFigureText:
    """図の中の文字を本文と別枠で出す (#119)."""

    @staticmethod
    def _page(tmp_path: Path) -> tuple[Path, Path]:
        pages = _pages_dir(tmp_path)
        Image.new("RGB", (100, 100), "white").save(pages / "0002.webp", lossless=True)
        return pages, _book(tmp_path)

    @staticmethod
    def _layout() -> dict:
        return {"0002.webp": {"regions": [{"type": "FIGURE", "bbox": [0, 0, 50, 50]}], "page_size": [100, 100]}}

    def test_block_includes_figure_text(self, tmp_path: Path):
        figure = Figure(
            page="0002",
            index=1,
            path=tmp_path / "0002_fig1.png",
            description="説明文",
            kind="グラフ",
            text="売上 / 利益",
        )

        block = figure_block(figure, "figures")

        assert "**図中の文字**: 売上 / 利益" in block
        # 説明の後、注記の前に置く
        assert block.index("**図（グラフ・自動生成）**:") < block.index("**図中の文字**")

    def test_block_has_no_figure_text_line_when_empty(self, tmp_path: Path):
        figure = Figure(page="0002", index=1, path=tmp_path / "0002_fig1.png", description="説明文")
        assert "図中の文字" not in figure_block(figure, "figures")

    def test_clean_drops_short_and_symbol_lines(self):
        text = "売上高\n-\n| |\nA\n利益率 20%\n"

        assert clean_figure_text(text) == "売上高 / 利益率 20%"

    def test_clean_removes_duplicate_lines(self):
        assert clean_figure_text("売上高\n売上高\n利益") == "売上高 / 利益"

    def test_clean_strips_markdown_markers(self):
        assert clean_figure_text("## 見出し\n| 項目 | 値 |") == "見出し / 項目 | 値"

    def test_clean_drops_numbers_only_lines(self):
        assert clean_figure_text("評価軸を決める\n24\n110\n-1\n(1)(2)(3)") == "評価軸を決める"

    def test_drop_body_repeats_removes_body_lines(self):
        text = "本文に出ている長い行です / 図だけの語"

        kept = drop_body_repeats(text, "ここは本文に出ている長い行です。")

        assert kept == "図だけの語"

    def test_short_labels_survive_body_repeats(self):
        # 2 文字のラベルは本文に偶然出てくるので落とさない
        assert drop_body_repeats("売上 / 利益", "売上と利益の推移を説明する。") == "売上 / 利益"

    def test_returns_empty_when_ocr_fails(self, tmp_path: Path):
        def broken(path, device):
            raise RuntimeError("CUDA out of memory")

        crop = tmp_path / "crop.png"
        Image.new("RGB", (10, 10), "white").save(crop)

        assert figure_text(crop, ocr=broken) == ""

    def test_describe_book_adds_text_without_touching_body(self, tmp_path: Path):
        pages, book = self._page(tmp_path)
        before = book.read_text(encoding="utf-8")

        text, figures = describe_book(
            book,
            self._layout(),
            pages,
            tmp_path / "figures",
            describe=lambda path, **kwargs: "所得分布の棒グラフ。縦軸は度数。",
            with_figure_text=True,
            ocr=lambda path, device: "所得 / 度数",
        )

        assert figures[0].text == "所得 / 度数"
        assert "**図中の文字**: 所得 / 度数" in text
        # 本文（ページマーカーと各行）は変わらない
        body_before = [line for line in before.splitlines() if line.startswith("本文")]
        body_after = [line for line in text.splitlines() if line.startswith("本文")]
        assert body_after == body_before

    def test_describe_book_skips_ocr_by_default(self, tmp_path: Path):
        pages, book = self._page(tmp_path)
        called = []

        text, figures = describe_book(
            book,
            self._layout(),
            pages,
            tmp_path / "figures",
            describe=lambda path, **kwargs: "説明",
            ocr=lambda path, device: called.append(path) or "文字",
        )

        assert called == []
        assert figures[0].text == ""
        assert "図中の文字" not in text
