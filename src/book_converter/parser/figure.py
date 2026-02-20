"""Figure and list parsing functions."""

from __future__ import annotations

import re

from src.book_converter.models import Figure, List
from src.book_converter.parser.utils import is_list_line


def parse_list(lines: list[str]) -> List | None:
    """Parse list lines into a List object.

    Supports various bullet markers (●, •, -, *, etc.) and ordered markers
    (①, 1., (1), etc.).

    Args:
        lines: List of lines containing list items.

    Returns:
        List object with items tuple, or None if empty.

    Example:
        >>> parse_list(["- Item 1", "- Item 2"])
        List(items=("Item 1", "Item 2"), list_type="unordered", read_aloud=True)
        >>> parse_list(["● 項目1", "● 項目2"])
        List(items=("項目1", "項目2"), list_type="unordered", read_aloud=True)
    """
    if not lines:
        return None

    items = []
    list_type = "unordered"  # Default

    for line in lines:
        is_list, detected_type, content = is_list_line(line)
        if is_list:
            # Set list type from first item
            if not items:
                list_type = detected_type
            items.append(content)

    if not items:
        return None

    return List(items=tuple(items), list_type=list_type, read_aloud=True)


def parse_figure_comment(line: str) -> str | None:
    """Parse a figure comment line to extract the file path.

    Args:
        line: A line from the Markdown file.

    Returns:
        File path if the line is a figure comment, None otherwise.

    Example:
        >>> parse_figure_comment("<!-- FIGURE: path/to/image.png -->")
        "path/to/image.png"
        >>> parse_figure_comment("<!-- figure: image.jpg -->")
        "image.jpg"
    """
    # Pattern: <!-- FIGURE: path --> (case insensitive)
    pattern = r"<!--\s*[Ff][Ii][Gg][Uu][Rr][Ee]:\s*(.+?)\s*-->"
    match = re.search(pattern, line)

    if match:
        path = match.group(1).strip()
        return path if path else None

    return None


def parse_figure_placeholder(line: str) -> dict | None:
    """図プレースホルダーを検出.

    [図], [図1], [図 1], [写真], [表], [イラスト], [グラフ], [チャート] を検出

    Args:
        line: テキスト行

    Returns:
        {"marker": "図1"} or None

    Example:
        >>> parse_figure_placeholder("[図1]")
        {"marker": "図1"}
        >>> parse_figure_placeholder("テキスト [写真3] テキスト")
        {"marker": "写真3"}
        >>> parse_figure_placeholder("通常のテキスト")
        None
    """
    # Pattern: [図|写真|表|イラスト|グラフ|チャート][番号・記号] ]
    pattern = r"\[(図|写真|表|イラスト|グラフ|チャート)([^\]]*)\]"
    match = re.search(pattern, line)

    if match:
        # 括弧を除去してマーカーテキストを返す
        marker = f"{match.group(1)}{match.group(2)}"
        return {"marker": marker}

    return None


def parse_figure(lines: list[str]) -> Figure | None:
    """Parse figure comment and description into a Figure object.

    Args:
        lines: List of lines that may contain a figure comment and description.

    Returns:
        Figure object if a figure comment is found, None otherwise.

    Example:
        >>> lines = [
        ...     "<!-- FIGURE: image.png -->",
        ...     "**図のタイトル**",
        ...     "図の説明文です。"
        ... ]
        >>> fig = parse_figure(lines)
        >>> fig.file
        'image.png'
    """
    if not lines:
        return None

    # Find figure comment
    file_path = None
    for line in lines:
        file_path = parse_figure_comment(line)
        if file_path:
            break

    if not file_path:
        return None

    # Extract caption and description from remaining lines
    caption = ""
    description_lines = []

    for line in lines:
        # Skip the figure comment line
        if parse_figure_comment(line):
            continue

        # Empty lines
        if not line.strip():
            continue

        # Check for bold text (caption): **text**
        bold_pattern = r"\*\*(.+?)\*\*"
        match = re.search(bold_pattern, line)

        if match and not caption:
            # First bold text becomes caption
            caption = match.group(1)
        elif line.strip():
            # Other non-empty lines become description
            description_lines.append(line.strip())

    # 新形式: path と caption のみ
    return Figure(
        path=file_path,
        caption=caption,
        marker="",
    )
