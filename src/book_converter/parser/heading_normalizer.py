"""Heading normalizer - number format, space normalization, and pattern extraction.

Stub module for TDD RED phase. All functions raise NotImplementedError.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class HeadingCategory(Enum):
    """見出しの分類カテゴリ"""

    NUMBERED = "numbered"  # 番号付き見出し (例: ## 1.1 SREの概要)
    UNNUMBERED = "unnumbered"  # 番号なし見出し (例: ## SREの概要)
    SPECIAL_MARKER = "special_marker"  # 特殊マーカー付き (例: ## ■コードベース)


@dataclass(frozen=True)
class HeadingInfo:
    """抽出された見出し情報"""

    line_number: int  # 1-indexed
    raw_text: str  # 元のテキスト (例: "## 1.1 SREの概要")
    level: int  # Markdownレベル (1-3)
    title: str  # タイトル部分 (例: "SREの概要")
    number: str  # 番号部分 (例: "1.1"), なければ ""
    category: HeadingCategory


@dataclass(frozen=True)
class PatternReport:
    """見出しパターンレポート"""

    total: int
    numbered_count: int
    unnumbered_count: int
    special_marker_count: int
    numbered_examples: tuple[str, ...]
    unnumbered_examples: tuple[str, ...]
    special_marker_examples: tuple[str, ...]


def normalize_number_format(text: str) -> str:
    """番号フォーマットをドット区切り半角に統一する.

    変換:
    - ハイフン区切り → ドット区切り (1-1-1 → 1.1.1)
    - 全角数字・全角ドット → 半角 (１．１ → 1.1)
    - 中黒 → ドット (1・1 → 1.1)

    Args:
        text: 正規化対象のテキスト

    Returns:
        番号フォーマットが統一されたテキスト
    """
    raise NotImplementedError("normalize_number_format is not implemented yet")


def normalize_spaces(text: str) -> str:
    """番号周辺の余分なスペースを除去する.

    変換:
    - 第 1 章 → 第1章
    - 1. 1 → 1.1

    Args:
        text: 正規化対象のテキスト

    Returns:
        スペースが正規化されたテキスト
    """
    raise NotImplementedError("normalize_spaces is not implemented yet")


def is_special_marker(text: str) -> bool:
    """特殊マーカー（■、◆等）で始まるかを判定する.

    Args:
        text: 判定対象のテキスト (Markdownマーカー除去済み)

    Returns:
        特殊マーカーで始まる場合 True
    """
    raise NotImplementedError("is_special_marker is not implemented yet")


def extract_headings(lines: list[str]) -> list[HeadingInfo]:
    """book.md の行リストから見出し行を抽出する.

    ## または ### で始まる行を HeadingInfo として抽出する。

    Args:
        lines: book.md の全行リスト

    Returns:
        HeadingInfo のリスト
    """
    raise NotImplementedError("extract_headings is not implemented yet")


def classify_heading_patterns(headings: list[HeadingInfo]) -> PatternReport:
    """見出しリストをパターン別に分類し、レポートを生成する.

    分類:
    - NUMBERED: 番号付き見出し
    - UNNUMBERED: 番号なし見出し
    - SPECIAL_MARKER: 特殊マーカー付き見出し

    Args:
        headings: HeadingInfo のリスト

    Returns:
        PatternReport
    """
    raise NotImplementedError("classify_heading_patterns is not implemented yet")
