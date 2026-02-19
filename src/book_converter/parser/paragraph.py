"""Paragraph parsing functions."""

from __future__ import annotations

import re

from src.book_converter.models import Paragraph


def parse_paragraph_lines(lines: list[str]) -> Paragraph | None:
    """複数行を改行なしで結合してParagraphを生成

    Args:
        lines: 段落の行リスト

    Returns:
        Paragraph（改行除去済み）、空の場合はNone

    処理:
    1. 各行をstrip
    2. 空白1文字で結合
    3. 連続空白を1つに圧縮

    Example:
        >>> parse_paragraph_lines(["Line 1", "Line 2"])
        Paragraph(text="Line 1 Line 2", read_aloud=True)
        >>> parse_paragraph_lines(["日本語の", "段落です"])
        Paragraph(text="日本語の 段落です", read_aloud=True)
    """
    if not lines:
        return None

    # 各行をstripして空白で結合
    text = " ".join(line.strip() for line in lines)

    # 連続空白を1つに圧縮
    text = re.sub(r"\s+", " ", text).strip()

    if not text:
        return None

    return Paragraph(text=text, read_aloud=True)


def split_paragraphs(text: str) -> list[Paragraph]:
    """テキストを空行で分割してParagraphリストを生成

    Args:
        text: 複数段落を含むテキスト

    Returns:
        Paragraphのリスト

    処理:
    1. 空行（空白のみの行含む）で分割
    2. 各段落内の改行を除去
    3. 空の段落は除外

    Example:
        >>> split_paragraphs("Para 1\\n\\nPara 2")
        [Paragraph(text="Para 1", read_aloud=True), Paragraph(text="Para 2", read_aloud=True)]
        >>> split_paragraphs("Line 1\\nLine 2\\n\\nLine 3")
        [Paragraph(text="Line 1 Line 2", read_aloud=True), Paragraph(text="Line 3", read_aloud=True)]
    """

    if not text.strip():
        return []

    # 空行（空白のみの行含む）で分割
    # \n\n または 空白のみの行を区切りとする
    # 改良版: 空白のみの行も空行として扱う
    paragraphs = []
    current_lines = []

    for line in text.split("\n"):
        # 空白のみの行（スペース、タブ、全角スペース含む）
        if not line.strip():
            # 現在の段落を保存
            if current_lines:
                para = parse_paragraph_lines(current_lines)
                if para is not None:
                    paragraphs.append(para)
                current_lines = []
        else:
            # 非空行を段落に追加
            current_lines.append(line)

    # 最後の段落を保存
    if current_lines:
        para = parse_paragraph_lines(current_lines)
        if para is not None:
            paragraphs.append(para)

    return paragraphs


def merge_continuation_paragraphs(paragraphs: list[Paragraph]) -> list[Paragraph]:
    """句点で終わらない段落を次の段落と結合

    Args:
        paragraphs: Paragraphのリスト

    Returns:
        結合後のParagraphリスト

    終端文字（結合しない）:
    - 句点: 。.
    - 感嘆符: !！
    - 疑問符: ?？
    - 閉じ括弧+句点: ）。」。

    Example:
        >>> p1 = Paragraph(text="これは継続", read_aloud=True)
        >>> p2 = Paragraph(text="段落です。", read_aloud=True)
        >>> merge_continuation_paragraphs([p1, p2])
        [Paragraph(text="これは継続段落です。", read_aloud=True)]
    """
    if not paragraphs:
        return []

    if len(paragraphs) == 1:
        return paragraphs

    # 終端文字のパターン
    terminating_chars = {"。", ".", "!", "！", "?", "？"}

    result = []
    idx = 0

    while idx < len(paragraphs):
        current = paragraphs[idx]
        current_text = current.text.rstrip()

        # 終端文字チェック
        ends_with_terminator = False
        if current_text:
            last_char = current_text[-1]
            if last_char in terminating_chars:
                ends_with_terminator = True
            # 閉じ括弧+句点パターン: ）。 」。
            elif len(current_text) >= 2:
                last_two = current_text[-2:]
                if last_two in {"）。", "」。"}:
                    ends_with_terminator = True

        # 終端文字で終わる場合、または最後の段落の場合は結合しない
        if ends_with_terminator or idx == len(paragraphs) - 1:
            result.append(current)
            idx += 1
        else:
            # 次の段落と結合（空白なし - 日本語テキストのため）
            next_para = paragraphs[idx + 1]
            merged_text = f"{current_text}{next_para.text}".strip()
            merged = Paragraph(text=merged_text, read_aloud=current.read_aloud)
            # 結合した段落を次のイテレーションで処理するため、paragraphsを更新
            paragraphs[idx + 1] = merged
            idx += 1

    return result


def parse_paragraph(lines: list[str]) -> Paragraph | None:
    """Parse paragraph lines into a Paragraph object.

    Args:
        lines: List of paragraph lines.

    Returns:
        Paragraph object with joined text, or None if empty/whitespace only.

    Example:
        >>> parse_paragraph(["Line 1", "Line 2"])
        Paragraph(text="Line 1\\nLine 2", read_aloud=True)
    """
    if not lines:
        return None

    # Join lines and strip whitespace
    text = "\n".join(lines).strip()

    if not text:
        return None

    return Paragraph(text=text, read_aloud=True)
