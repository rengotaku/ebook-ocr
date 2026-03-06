"""Heading normalizer - number format, space normalization, and pattern extraction.

Provides functions to normalize heading formats and extract heading patterns.
"""

from __future__ import annotations

import re
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
    page: str = ""  # ページ番号 (例: "163"), ページマーカーがなければ ""


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
    if not text:
        return text

    # 全角数字を半角に変換
    result = text.translate(
        str.maketrans(
            "０１２３４５６７８９",
            "0123456789"
        )
    )

    # 全角ドットを半角に変換
    result = result.replace("．", ".")

    # 番号パターン (N sep N sep N...) を検出し、区切り文字をドットに統一
    # sep は ハイフン(-), 中黒(・), ドット(.) のいずれか
    # 番号パターンは数字のみで構成され、区切り文字で連結される
    # テキスト中のハイフン (例: SRE-based) は番号パターンでないため保持

    # 番号パターン: 先頭または空白後に数字、区切り文字、数字が続くパターン
    # (?:^|\s) で先頭または空白を検出 (後読み)
    # (\d+) で数字をキャプチャ
    # ([-・\.]) で区切り文字をキャプチャ
    # (\d+) で次の数字をキャプチャ
    # (?:[-・\.](\d+))* で追加の区切り+数字を繰り返し
    pattern = r'(\d+)([-・\.])\d+(?:[-・\.]\d+)*'

    def replace_separator(match: re.Match[str]) -> str:
        """区切り文字をドットに置換"""
        matched_text = match.group(0)
        # 区切り文字を全てドットに置換
        return matched_text.replace("-", ".").replace("・", ".")

    result = re.sub(pattern, replace_separator, result)

    return result


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
    if not text:
        return text

    result = text

    # パターン1: 第 N 章 → 第N章, 第 N 節 → 第N節
    # \s+ で1つ以上のスペースを検出
    result = re.sub(r'第\s+(\d+)\s+(章|節)', r'第\1\2', result)

    # パターン2: 番号内のスペース除去 (N. N → N.N, N.  N → N.N)
    # 複数のスペースにも対応
    # 複数回適用して全ての N. N パターンを置換
    while True:
        new_result = re.sub(r'(\d+)\.\s+(\d+)', r'\1.\2', result)
        if new_result == result:
            break
        result = new_result

    return result


def is_special_marker(text: str) -> bool:
    """特殊マーカー（■、◆等）で始まるかを判定する.

    Args:
        text: 判定対象のテキスト (Markdownマーカー除去済み)

    Returns:
        特殊マーカーで始まる場合 True
    """
    if not text:
        return False

    # 特殊マーカー文字セット
    special_markers = {"■", "◆", "□", "●", "◇", "▲"}

    # 先頭文字を取得 (スペースを無視)
    stripped = text.lstrip()
    if not stripped:
        return False

    return stripped[0] in special_markers


class MissingMarkerError(Exception):
    """Required marker not found in file."""


def extract_headings(lines: list[str]) -> list[HeadingInfo]:
    """book.md の行リストから見出し行を抽出する.

    ## または ### で始まる行を HeadingInfo として抽出する。
    <!-- content --> ～ <!-- /content --> マーカーの範囲内のみを対象とする。
    ページマーカー (--- Page N (filename) ---) から現在のページ番号を追跡する。

    Args:
        lines: book.md の全行リスト

    Returns:
        HeadingInfo のリスト

    Raises:
        MissingMarkerError: <!-- content --> マーカーが見つからない場合
    """
    from src.book_converter.parser.page import parse_page_marker

    result: list[HeadingInfo] = []
    current_page: str = ""

    # content マーカーの存在確認（必須）
    has_content_start = any(line.strip() == "<!-- content -->" for line in lines)
    has_content_end = any(line.strip() == "<!-- /content -->" for line in lines)

    if not has_content_start or not has_content_end:
        raise MissingMarkerError(
            "Required markers <!-- content --> and <!-- /content --> not found"
        )

    in_content_section = False

    # Markdown見出しパターン (h1-h6)
    heading_pattern = re.compile(r'^(#{1,6})\s+(.+)$')
    # 番号パターン（## なしで番号から始まる行）: 1.0.0 タイトル, 1.1 タイトル 等
    number_only_pattern = re.compile(r'^(\d+(?:\.\d+)+)\s+(.+)$')

    for line_idx, line in enumerate(lines):
        stripped = line.strip()

        # ページマーカーをチェック（content セクション外でも追跡）
        page_info = parse_page_marker(line)
        if page_info:
            current_page = page_info[0]  # (page_number, source_file)
            continue

        # content セクションの開始/終了をチェック
        if stripped == "<!-- content -->":
            in_content_section = True
            continue
        if stripped == "<!-- /content -->":
            in_content_section = False
            continue

        # content セクション外はスキップ
        if not in_content_section:
            continue

        # ## または ### で始まる見出し
        match = heading_pattern.match(line)
        if match:
            marker = match.group(1)
            text_part = match.group(2)
            level = len(marker)
            number, title, category = _parse_heading_text(text_part)

            heading_info = HeadingInfo(
                line_number=line_idx + 1,  # 1-indexed
                raw_text=line,
                level=level,
                title=title,
                number=number,
                category=category,
                page=current_page,
            )
            result.append(heading_info)
            continue

        # 番号パターンのみで始まる行（## なし）
        num_match = number_only_pattern.match(stripped)
        if num_match:
            number = num_match.group(1)
            title = num_match.group(2)

            heading_info = HeadingInfo(
                line_number=line_idx + 1,  # 1-indexed
                raw_text=line,
                level=0,  # Markdownマーカーなし
                title=title,
                number=number,
                category=HeadingCategory.NUMBERED,
                page=current_page,
            )
            result.append(heading_info)
            continue

        # 短い単独行（## なし、番号なし）- 見出し候補として認識
        # 条件:
        # - 50文字以下
        # - 文末句読点なし
        # - 空行でない
        # - コメント/リスト/マーカーで始まらない
        # - プレースホルダーテキストでない（テキスト、本文、内容、段落等を含まない）
        if (
            stripped
            and len(stripped) <= 50
            and not stripped.endswith(('。', '、', '.', ',', ':', '：'))
            and not stripped.startswith(('<!--', '---', '-', '*', '·', '#'))
            and not is_special_marker(stripped)
            and not any(w in stripped for w in ('テキスト', '本文', '内容', '段落'))
        ):
            # 番号とタイトルを解析
            number, title, category = _parse_heading_text(stripped)

            heading_info = HeadingInfo(
                line_number=line_idx + 1,  # 1-indexed
                raw_text=line,
                level=0,  # Markdownマーカーなし
                title=title,
                number=number,
                category=category,
                page=current_page,
            )
            result.append(heading_info)

    return result


def _parse_heading_text(text: str) -> tuple[str, str, HeadingCategory]:
    """見出しテキストから番号、タイトル、カテゴリを解析.

    Args:
        text: 見出しテキスト (## マーカー除去済み)

    Returns:
        (number, title, category)
    """
    # 特殊マーカーチェック
    if is_special_marker(text):
        return ("", text, HeadingCategory.SPECIAL_MARKER)

    # 番号パターン: N, N.N, N.N.N 形式
    # 先頭から番号パターンを検出
    number_pattern = re.compile(r'^(\d+(?:\.\d+)*)\s+(.+)$')
    match = number_pattern.match(text)

    if match:
        number = match.group(1)
        title = match.group(2)
        return (number, title, HeadingCategory.NUMBERED)

    # 番号なし
    return ("", text, HeadingCategory.UNNUMBERED)


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
    numbered_examples: list[str] = []
    unnumbered_examples: list[str] = []
    special_marker_examples: list[str] = []

    numbered_count = 0
    unnumbered_count = 0
    special_marker_count = 0

    for heading in headings:
        if heading.category == HeadingCategory.NUMBERED:
            numbered_count += 1
            if len(numbered_examples) < 3:  # 代表例は3件まで
                numbered_examples.append(heading.raw_text)
        elif heading.category == HeadingCategory.UNNUMBERED:
            unnumbered_count += 1
            if len(unnumbered_examples) < 3:
                unnumbered_examples.append(heading.raw_text)
        elif heading.category == HeadingCategory.SPECIAL_MARKER:
            special_marker_count += 1
            if len(special_marker_examples) < 3:
                special_marker_examples.append(heading.raw_text)

    return PatternReport(
        total=len(headings),
        numbered_count=numbered_count,
        unnumbered_count=unnumbered_count,
        special_marker_count=special_marker_count,
        numbered_examples=tuple(numbered_examples),
        unnumbered_examples=tuple(unnumbered_examples),
        special_marker_examples=tuple(special_marker_examples),
    )
