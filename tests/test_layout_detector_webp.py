"""webp のページもレイアウト検出できることの確認.

Sony ビューアから取り出したページは webp で配布される。ページ列挙が png 固定だと
0 件のまま静かに終わるため、拡張子ではなく中身で読める形式を受け付ける。
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from src.layout import detector


class FakeAnalysisResults:
    """yomitoku の解析結果の代わり（ページ列挙だけを確かめるため中身は空）."""

    paragraphs: list = []
    figures: list = []


class FakeAnalyzer:
    """yomitoku の DocumentAnalyzer の代わり."""

    def __init__(self) -> None:
        self.calls = 0

    def __call__(self, cv_img):  # noqa: ARG002 - 引数は本物に合わせる
        self.calls += 1
        return FakeAnalysisResults(), None, None


@pytest.fixture()
def webp_pages(tmp_path: Path) -> Path:
    pages = tmp_path / "pages"
    pages.mkdir()
    for index in (1, 2):
        Image.new("RGB", (120, 160), "white").save(pages / f"page_{index:04d}.webp", lossless=True)
    return pages


def test_processes_webp_pages(webp_pages: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    analyzer = FakeAnalyzer()
    monkeypatch.setattr(detector, "get_analyzer", lambda device="cpu": analyzer)

    out_dir = tmp_path / "layout"
    layout = detector.detect_layout_yomitoku(str(webp_pages), str(out_dir))

    assert sorted(layout) == ["page_0001.webp", "page_0002.webp"]
    assert analyzer.calls == 2


def test_writes_layout_json_for_webp_pages(webp_pages: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setattr(detector, "get_analyzer", lambda device="cpu": FakeAnalyzer())

    out_dir = tmp_path / "layout"
    detector.detect_layout_yomitoku(str(webp_pages), str(out_dir))

    saved = json.loads((out_dir / "layout.json").read_text(encoding="utf-8"))
    assert sorted(saved) == ["page_0001.webp", "page_0002.webp"]


def test_png_pages_still_work(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    pages = tmp_path / "pages"
    pages.mkdir()
    Image.new("RGB", (120, 160), "white").save(pages / "page_0001.png")

    monkeypatch.setattr(detector, "get_analyzer", lambda device="cpu": FakeAnalyzer())
    layout = detector.detect_layout_yomitoku(str(pages), str(tmp_path / "layout"))

    assert sorted(layout) == ["page_0001.png"]
