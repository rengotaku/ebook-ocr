"""出力（book.md / 章ファイル）の異常をルールで見つける.

生成できたかどうかではなく、中身が壊れていないかを見る（#102）。検出するだけで、
直すことはしない。

- ``empty_page`` / ``missing_region``: ``layout.json`` にテキストがあるのに出力に無い
- ``broken_paragraph``: 文末記号で終わらず、次の段落ともつながらない段落
- ``running_head``: 柱・ノンブルらしき行が本文に混ざっている
- ``duplicate_line``: 同じ行が近くに二度出ている（ページ境界での二重出力など）
- ``broken_heading``: 見出しが短すぎる・記号だけ・本文の断片
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.layout.running_head import find_running_heads, is_running_head

# 段落がここで終わっていれば文が切れていない
PARAGRAPH_ENDINGS = ("。", "．", "！", "？", "!", "?", "…", "」", "』", "）", ")", "】")
# 見出しがここで終わっていたら、見出しではなく本文の断片
HEADING_ENDINGS = ("。", "．", "！", "？", "…")
# 文の継続を表す行末（読点・中黒・開き括弧）
CONTINUATION_ENDINGS = ("、", "，", "・", "（", "(")

PAGE_MARKER_RE = re.compile(r"^--- (\d+) ---$", re.M)
RUNNING_HEAD_RE = re.compile(r"^\s*\d{0,3}\s*第\s*\d+\s*章\s+\S")
PAGE_NUMBER_ONLY_RE = re.compile(r"^[\d０-９Ⅰ-ⅿ]{1,4}$")
COMMENT_RE = re.compile(r"^<!--.*-->$")
FIGURE_LINK_RE = re.compile(r"^!\[.*\]\(.*\)$")

# 段落の途中切れを見るときの最小の長さ。短い行は見出し・ラベル・箇条書きのことが多い
MIN_PARAGRAPH_LENGTH = 40
# 同じ行の重複を見るときの最小の長さ。短い行は箇条書き・表の繰り返しが多く、本文の二重出力と区別できない
MIN_DUPLICATE_LENGTH = 60

# ページ全体 OCR にフォールバックしたページは、領域の text と出力が一致しない。
# 領域の text がこれ未満しか見つからないページは「領域別に処理していない」とみなして飛ばす
MIN_REGION_HIT_RATIO = 0.5


@dataclass(frozen=True)
class Issue:
    """検出した異常 1 件."""

    kind: str
    page: str
    detail: str

    def as_dict(self) -> dict:
        return {"kind": self.kind, "page": self.page, "detail": self.detail}


def split_pages(text: str) -> dict[str, str]:
    """``--- 0085 ---`` ごとに (ページ番号, 本文) に分ける."""
    matches = list(PAGE_MARKER_RE.finditer(text))
    pages: dict[str, str] = {}
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        pages.setdefault(match.group(1), text[start:end])
    return pages


def _normalize(text: str) -> str:
    return "".join(text.split())


def _blocks(body: str) -> list[str]:
    return [block.strip() for block in re.split(r"\n\s*\n", body) if block.strip()]


def _is_structural(block: str) -> bool:
    """見出し・注記・図・箇条書きなど、文の途中切れを判定しないブロック."""
    first = block.splitlines()[0].strip()
    return bool(
        first.startswith(("#", ">", "<!--", "!", "|"))
        or FIGURE_LINK_RE.match(first)
        or re.match(r"^[①②③④⑤⑥⑦⑧⑨⑩・·･•※*\-0-9０-９(（]", first)
    )


def check_empty_regions(
    pages: dict[str, str],
    layout: dict,
    fallback_pages: frozenset[str] = frozenset(),
) -> list[Issue]:
    """``layout.json`` にテキストがあるのに出力に無いものを探す.

    柱・ノンブルは本文から除くのが正しい（#98）ので、判定から外す。ページ全体 OCR に
    フォールバックしたページは、領域の text と出力が対応しないので判定しない。
    """
    issues: list[Issue] = []
    running_heads = find_running_heads(layout)
    for page, body in pages.items():
        if page in fallback_pages:
            continue
        page_layout = layout.get(f"{page}.webp") or layout.get(f"{page}.png") or layout.get(f"{page}.jpg")
        if not page_layout:
            continue
        page_size = page_layout.get("page_size") or [0, 0]
        texts = [
            (region.get("text") or "").strip()
            for region in page_layout.get("regions", [])
            if region.get("type") not in ("FIGURE", "CODE", "ABANDON")
            and (region.get("text") or "").strip()
            and not is_running_head(region, page_size, running_heads)
        ]
        if not texts:
            continue
        page_text = _normalize(body)
        found = [text for text in texts if _normalize(text) in page_text]
        if not found:
            issues.append(
                Issue(
                    kind="empty_page",
                    page=page,
                    detail=f"layout.json の {len(texts)} 領域がどれも出力に無い",
                )
            )
            continue
        if len(found) / len(texts) < MIN_REGION_HIT_RATIO:
            # ページ全体 OCR にフォールバックしたページ。領域の text と出力が一致しないので判定しない
            continue
        for text in texts:
            if _normalize(text) not in page_text:
                issues.append(Issue(kind="missing_region", page=page, detail=text[:40]))
    return issues


def check_broken_paragraphs(pages: dict[str, str]) -> list[Issue]:
    """文末記号で終わらず、次の段落ともつながらない段落を探す.

    紙面の段落はページをまたぐので、ページの最後の段落は次のページの先頭とつなげて見る。
    """
    issues: list[Issue] = []
    page_items = list(pages.items())
    for position, (page, body) in enumerate(page_items):
        blocks = _blocks(body)
        next_page_first = ""
        if position + 1 < len(page_items):
            following_blocks = _blocks(page_items[position + 1][1])
            next_page_first = following_blocks[0] if following_blocks else ""
        for index, block in enumerate(blocks):
            if _is_structural(block):
                continue
            text = block.replace("\n", "")
            if len(text) < MIN_PARAGRAPH_LENGTH:
                continue
            if text.endswith(PARAGRAPH_ENDINGS) or text.endswith(CONTINUATION_ENDINGS):
                continue
            following = blocks[index + 1] if index + 1 < len(blocks) else next_page_first
            if following and not _is_structural(following):
                # 次の段落（次ページの先頭を含む）が続きとして読めるなら、段落が分かれただけ
                continue
            issues.append(Issue(kind="broken_paragraph", page=page, detail=text[-40:]))
    return issues


def check_running_heads(pages: dict[str, str], page_numbers: dict[str, int] | None = None) -> list[Issue]:
    """柱・ノンブルらしき行が本文に混ざっていないか見る.

    数字だけの行は、紙面のページ番号（``book_meta.json``）と一致するときだけノンブルと
    みなす。脚注番号などを拾わないため。
    """
    issues: list[Issue] = []
    for page, body in pages.items():
        lines = [line.strip() for line in body.splitlines() if line.strip()]
        printed = (page_numbers or {}).get(page)
        for index, line in enumerate(lines):
            if RUNNING_HEAD_RE.match(line):
                issues.append(Issue(kind="running_head", page=page, detail=line[:40]))
                continue
            if printed is None or not PAGE_NUMBER_ONLY_RE.match(line):
                continue
            if (index < 2 or index >= len(lines) - 2) and line.strip() == str(printed):
                issues.append(Issue(kind="running_head", page=page, detail=line))
    return issues


def check_duplicate_lines(pages: dict[str, str]) -> list[Issue]:
    """同じ行が同じページ・隣のページに二度出ていないか見る."""
    issues: list[Issue] = []
    previous_tail: list[str] = []
    for page, body in pages.items():
        seen: set[str] = set()
        lines = [line.strip() for line in body.splitlines() if len(line.strip()) >= MIN_DUPLICATE_LENGTH]
        for line in lines:
            key = _normalize(line)
            if key in seen:
                issues.append(Issue(kind="duplicate_line", page=page, detail=line[:40]))
            seen.add(key)
        for line in lines[:3]:
            if _normalize(line) in previous_tail:
                issues.append(Issue(kind="duplicate_line", page=page, detail=f"前ページと重複: {line[:40]}"))
        previous_tail = [_normalize(line) for line in lines[-3:]]
    return issues


def check_headings(pages: dict[str, str]) -> list[Issue]:
    """見出しの異常（短すぎる・記号だけ・本文の断片）を探す."""
    issues: list[Issue] = []
    for page, body in pages.items():
        for line in body.splitlines():
            if not line.startswith("#"):
                continue
            text = line.lstrip("#").strip()
            if not text:
                issues.append(Issue(kind="broken_heading", page=page, detail="空の見出し"))
                continue
            if len(text) < 2:
                issues.append(Issue(kind="broken_heading", page=page, detail=f"短すぎる: {text}"))
                continue
            if not re.search(r"[\w\u3040-\u30ff\u4e00-\u9fff]", text):
                issues.append(Issue(kind="broken_heading", page=page, detail=f"記号だけ: {text}"))
                continue
            if text.endswith(HEADING_ENDINGS):
                issues.append(Issue(kind="broken_heading", page=page, detail=f"本文の断片: {text[:40]}"))
    return issues


def check_all(
    pages: dict[str, str],
    layout: dict | None = None,
    book_meta: dict | None = None,
) -> list[Issue]:
    """すべてのチェックを実行する."""
    meta = book_meta or {}
    issues: list[Issue] = []
    if layout:
        fallback_pages = frozenset(meta.get("fallback_pages") or ())
        issues.extend(check_empty_regions(pages, layout, fallback_pages))
    issues.extend(check_broken_paragraphs(pages))
    issues.extend(check_running_heads(pages, meta.get("page_numbers")))
    issues.extend(check_duplicate_lines(pages))
    issues.extend(check_headings(pages))
    return issues


def summarize(issues: list[Issue]) -> dict[str, int]:
    """種類ごとの件数."""
    counts: dict[str, int] = {}
    for issue in issues:
        counts[issue.kind] = counts.get(issue.kind, 0) + 1
    return counts
