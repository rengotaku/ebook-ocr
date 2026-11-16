"""book.md を章ごとに分割し、LLM 向けに整形する.

入力はページマーカー（``--- 0085 ---``）で区切られた Markdown。
章の境界は「扉ページ」（本文が ``第N章`` で始まるページ）で決める。
章名は各ページの柱（``20 第1章 データ分析を設計する``）の最頻値を採用する。
"""

from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path

from src.book_meta import load_book_meta

PAGE_MARKER_RE = re.compile(r"^--- (\d+) ---\s*$", re.M)
CHAPTER_START_RE = re.compile(r"^(?:##\s*)?第\s*(\d+)\s*章")
RUNNING_HEAD_RE = re.compile(r"^\s*\d{0,3}\s*第\s*(\d+)\s*章\s+(.+?)(?:\s+\d{1,3})?\s*$")
PAGE_NUMBER_RE = re.compile(r"^\s*[\divxlcIVXLC]{1,6}\s*$")
TOC_HEAD_RE = re.compile(r"^\s*\d*\s*目次\s*\d*\s*$")
# 後付（著者一覧・参考資料・索引・奥付）の開始行
# 後付の開始行。見出し記号（##）や ● が付いていても拾う
BACK_MATTER_RE = re.compile(r"^(?:#{1,3}\s*)?(?:●\s*)?(著者一覧|参考文献|参考資料|索引|奥付|あとがき|謝辞)")
# 「1-1. 見出し」形式の節見出し（この本の節番号）
SECTION_HEAD_RE = re.compile(r"^\d+-\d+[.．]\s*\S")
# 節番号だけが 1 行に載り、見出しが次の行に来ることがある（``1-1.`` → ``分析ストーリー…``）
SECTION_NUMBER_RE = re.compile(r"^(\d+-\d+[.．])\s*$")
FIGURE_LINK_RE = re.compile(r"^!\[図\]\(([^)]*)\)\s*$")
# 図の説明の行。種別と「自動生成」が付く（``**図（表・自動生成）**: ...``）
FIGURE_CAPTION_RE = re.compile(r"^\*\*図(?:（[^）]*）)?\*\*:")
SENTENCE_ENDINGS = ("。", "．", "！", "？", "」", "』", "）")


@dataclass
class Chapter:
    """1 章分の出力."""

    number: int | None
    title: str
    start_page: str
    end_page: str
    pages: list[tuple[str, str]] = field(default_factory=list)

    @property
    def file_name(self) -> str:
        if self.number is None:
            return f"{self.title}.md"
        return f"{self.number:02d}_{_slug(self.title)}.md"


def _slug(title: str) -> str:
    cleaned = re.sub(r"[^\wぁ-んァ-ヶ一-龠ー]+", "_", title).strip("_")
    return cleaned or "chapter"


def split_pages(text: str) -> list[tuple[str, str]]:
    """``--- 0085 ---`` ごとに (ページ番号, 本文) に分ける."""
    matches = list(PAGE_MARKER_RE.finditer(text))
    pages: list[tuple[str, str]] = []
    for index, match in enumerate(matches):
        start = match.end()
        end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
        pages.append((match.group(1), text[start:end]))
    return pages


def chapter_starts(pages: list[tuple[str, str]]) -> dict[int, str]:
    """章番号ごとの開始ページ（扉ページ）を返す."""
    starts: dict[int, str] = {}
    for page, body in pages:
        first_line = next((line for line in body.splitlines() if line.strip()), "")
        match = CHAPTER_START_RE.match(first_line.strip())
        if not match:
            continue
        number = int(match.group(1))
        starts.setdefault(number, page)
    return starts


def running_head_titles(pages: list[tuple[str, str]]) -> dict[int, str]:
    """章番号ごとに、柱に出てくる章名の最頻値を返す."""
    votes: dict[int, Counter] = {}
    for _, body in pages:
        for line in body.splitlines():
            match = RUNNING_HEAD_RE.match(line)
            if match:
                votes.setdefault(int(match.group(1)), Counter())[match.group(2).strip()] += 1
    return {number: counter.most_common(1)[0][0] for number, counter in votes.items()}


def chapter_titles(pages: list[tuple[str, str]], known_titles: dict[int, str] | None = None) -> dict[int, str]:
    """章番号ごとの章名を返す.

    柱から取った章名（``book_meta.json`` の ``chapter_titles``）を優先する。柱を
    本文から除いた後でも、出版された章名がそのまま使える。無ければ扉ページの
    見出し（``## 第2章`` の次の行、または同じ行の続き）から取る。
    """
    titles: dict[int, str] = dict(known_titles or {})

    starts = chapter_starts(pages)
    opener_pages = {page: number for number, page in starts.items()}
    for page, body in pages:
        number = opener_pages.get(page)
        if number is None or number in titles:
            continue
        lines = [line.strip() for line in body.splitlines() if line.strip()]
        if not lines:
            continue
        match = CHAPTER_START_RE.match(lines[0])
        if not match:
            continue
        rest = lines[0][match.end() :].strip("# 　")
        if not rest and len(lines) > 1:
            candidate = lines[1].lstrip("# ").strip()
            # 扉ページに見出しが無いときは本文の 1 行目が来る。長い行・文末記号で終わる行は見出しとみなさない
            if len(candidate) <= 40 and not candidate.endswith(SENTENCE_ENDINGS):
                rest = candidate
        if rest:
            titles[number] = rest

    # 見出しからも取れなかった章は、本文に残っている柱の最頻値で補う
    for number, title in running_head_titles(pages).items():
        titles.setdefault(number, title)
    return titles


def build_chapters(pages: list[tuple[str, str]], known_titles: dict[int, str] | None = None) -> list[Chapter]:
    """ページ列を章ごとにまとめる（前付・後付は number=None）."""
    if not pages:
        return []
    starts = chapter_starts(pages)
    titles = chapter_titles(pages, known_titles)

    order = sorted(starts.items(), key=lambda item: item[1])
    back_start = _back_matter_start(pages)
    chapters: list[Chapter] = []
    first_start = order[0][1] if order else pages[-1][0]

    front = [page for page in pages if page[0] < first_start]
    if front:
        chapters.append(
            Chapter(number=None, title="00_front", start_page=front[0][0], end_page=front[-1][0], pages=front)
        )

    for index, (number, start) in enumerate(order):
        end = order[index + 1][1] if index + 1 < len(order) else None
        body_pages = [
            page
            for page in pages
            if page[0] >= start and (end is None or page[0] < end) and (back_start is None or page[0] < back_start)
        ]
        if not body_pages:
            continue
        title = titles.get(number) or f"第{number}章"
        chapters.append(
            Chapter(
                number=number,
                title=title,
                start_page=body_pages[0][0],
                end_page=body_pages[-1][0],
                pages=body_pages,
            )
        )

    if back_start is not None:
        back_pages = [page for page in pages if page[0] >= back_start]
        if back_pages:
            chapters.append(
                Chapter(
                    number=None,
                    title="99_back",
                    start_page=back_pages[0][0],
                    end_page=back_pages[-1][0],
                    pages=back_pages,
                )
            )
    return chapters


def _back_matter_start(pages: list[tuple[str, str]]) -> str | None:
    for page, body in pages:
        first_line = next((line for line in body.splitlines() if line.strip()), "").strip()
        if BACK_MATTER_RE.match(first_line):
            return page
    return None


def _is_running_head(line: str) -> bool:
    stripped = line.strip()
    if not stripped:
        return False
    return bool(
        RUNNING_HEAD_RE.match(line)
        or PAGE_NUMBER_RE.match(line)
        or TOC_HEAD_RE.match(line)
        or re.match(r"^\s*第\s*\d+\s*章\s+\S+\s+\d{1,3}\s*$", stripped)
    )


def _join_line(previous: str, current: str) -> str:
    """折り返された行をつなぐ（日本語は空白を入れず、英数字の境界だけ空白を入れる）."""
    if not previous:
        return current
    left = previous[-1]
    right = current[0]
    if left.isascii() and right.isascii() and (left.isalnum() or left in ".,;:!?)]}\"'") and right.isalnum():
        return f"{previous} {current}"
    return previous + current


def llm_format(body: str) -> str:
    """1 章分の本文を、LLM に読ませる前提で整形する.

    - 紙面の折り返しを戻して段落にする（空行が段落の区切り）
    - 柱・ノンブル・ページ番号だけの行を落とす
    - 図の画像リンクを外し、説明文（``**図**: ...``）だけを引用として残す
    - 見出し（``##``）はそのまま
    """
    paragraphs: list[str] = []
    buffer = ""
    pending_section = ""

    def flush() -> None:
        nonlocal buffer
        if buffer:
            paragraphs.append(buffer)
            buffer = ""

    for raw in body.splitlines():
        line = raw.strip()
        if not line:
            # 紙面では 1 行ごとに空行が入るため、空行は段落の区切りとして扱わない。
            # 文末で終わったときだけ段落を切る（折り返しの復元は _join_line が担う）。
            continue
        figure_link = FIGURE_LINK_RE.match(line)
        if figure_link:
            # LLM 用でも原画像の場所は注記として残す（#99）
            flush()
            paragraphs.append(f"<!-- 図: {figure_link.group(1)} -->")
            continue
        if FIGURE_CAPTION_RE.match(line):
            flush()
            paragraphs.append(f"> {line}")
            continue
        if CHAPTER_START_RE.match(line) and len(line) < 40:
            # 章扉の「第N章 章名」は H1 と重複するので落とす（`## 第5章` も含む）
            flush()
            continue
        if line.startswith("#"):
            flush()
            paragraphs.append(line)
            continue
        if SECTION_NUMBER_RE.match(line):
            flush()
            pending_section = SECTION_NUMBER_RE.match(line).group(1)
            continue
        if pending_section:
            paragraphs.append(f"## {pending_section} {line}")
            pending_section = ""
            continue
        if SECTION_HEAD_RE.match(line) and len(line) < 60:
            flush()
            paragraphs.append(f"## {line}")
            continue
        if _is_running_head(line):
            continue
        if buffer and not buffer.endswith(SENTENCE_ENDINGS) and not line.startswith(("・", "①", "②", "③", "④", "⑤")):
            buffer = _join_line(buffer, line)
        else:
            flush()
            buffer = line
    flush()
    return "\n\n".join(paragraphs)


def render_chapter(
    chapter: Chapter,
    llm: bool = True,
    page_numbers: dict[str, int] | None = None,
) -> str:
    """1 章分の Markdown を組み立てる.

    各ページの先頭に ``<!-- page 0085 (紙面 86) -->`` の注記を置き、
    どの段落が紙面のどこから来たかを辿れるようにする（#99）。紙面のページ番号が
    分からないページは ``<!-- page 0085 -->`` だけにする（推測で埋めない）。
    """
    header = [f"# {chapter.title}" if chapter.number is None else f"# 第{chapter.number}章 {chapter.title}"]
    header.append(f"<!-- pages: {chapter.start_page}-{chapter.end_page} / pages-dir: pages / figures-dir: figures -->")

    page_bodies: list[tuple[str, str]] = []
    for page, body in chapter.pages:
        text = llm_format(body) if llm else body.strip()
        if text:
            page_bodies.append((page, text))

    if page_bodies and chapter.title and page_bodies[0][1].startswith(chapter.title):
        # 章扉の章名が本文の頭に残ることがあるので落とす（H1 と重複する）
        first_page, first_text = page_bodies[0]
        page_bodies[0] = (first_page, first_text[len(chapter.title) :].lstrip())

    body_parts = []
    for page, text in page_bodies:
        if not text:
            continue
        printed = (page_numbers or {}).get(page)
        marker = f"<!-- page {page} (紙面 {printed}) -->" if printed is not None else f"<!-- page {page} -->"
        body_parts.append(f"{marker}\n\n{text}")
    return "\n".join(header) + "\n\n" + "\n\n".join(body_parts) + "\n"


def write_page_numbers_csv(out_dir: Path, page_numbers: dict[str, int]) -> Path | None:
    """ページ番号と紙面のページ番号（ノンブル）の対応表を書き出す."""
    if not page_numbers:
        return None
    target = out_dir / "_pages.csv"
    lines = ["page,printed", *(f"{page},{page_numbers[page]}" for page in sorted(page_numbers))]
    target.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return target


def split_file(
    book_md: Path,
    out_dir: Path,
    llm: bool = True,
    book_meta: dict | None = None,
) -> list[Path]:
    """book.md を章ごとのファイルに書き出し、書いたパスを返す."""
    meta = book_meta if book_meta is not None else load_book_meta(book_md)
    page_numbers = meta.get("page_numbers") or {}
    chapters = build_chapters(split_pages(book_md.read_text(encoding="utf-8")), meta.get("chapter_titles") or {})
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for chapter in chapters:
        target = out_dir / chapter.file_name
        target.write_text(render_chapter(chapter, llm=llm, page_numbers=page_numbers), encoding="utf-8")
        written.append(target)
    write_page_numbers_csv(out_dir, page_numbers)
    return written
