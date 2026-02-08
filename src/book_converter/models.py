"""Data models for book markdown to XML conversion.

All entities are immutable (frozen dataclasses) per Constitution IV. Immutability.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Union


class MarkerType(Enum):
    """Content marker types."""

    TOC_START = "toc_start"
    TOC_END = "toc_end"
    CONTENT_START = "content_start"
    CONTENT_END = "content_end"
    SKIP_START = "skip_start"
    SKIP_END = "skip_end"


@dataclass(frozen=True)
class BookMetadata:
    """書籍メタデータ"""

    title: str
    isbn: str | None = None
    source_format: str = "markdown"
    conversion_date: str = ""  # ISO 8601 形式


@dataclass(frozen=True)
class PageAnnouncement:
    """ページ読み上げ"""

    text: str  # "42ページ"
    format: str = "simple"  # "simple", "chapter"


@dataclass(frozen=True)
class Heading:
    """見出し"""

    level: int  # 1, 2, 3（0=エラー）
    text: str
    read_aloud: bool = True


@dataclass(frozen=True)
class Paragraph:
    """段落"""

    text: str
    read_aloud: bool = True


@dataclass(frozen=True)
class List:
    """リスト"""

    items: tuple[str, ...]
    read_aloud: bool = True


# Union type for content elements
ContentElement = Union[Heading, Paragraph, List]


@dataclass(frozen=True)
class Content:
    """本文コンテンツ"""

    elements: tuple[ContentElement, ...]
    read_aloud: bool = False


@dataclass(frozen=True)
class Figure:
    """図表"""

    file: str
    caption: str = ""
    description: str = ""
    read_aloud: str = "optional"  # "true", "false", "optional"
    continued: bool = False


@dataclass(frozen=True)
class PageMetadata:
    """ページメタデータ"""

    text: str  # 元の表記 "はじめに 1 / 3"
    meta_type: str = "chapter-page"  # "chapter-page", "section-page", "unknown"
    section_name: str = ""  # "はじめに"
    current: int = 0  # 1
    total: int = 0  # 3


@dataclass(frozen=True)
class TocEntry:
    """Table of Contents entry."""

    text: str  # エントリのタイトルテキスト
    level: str  # "chapter", "section", "subsection", "other"
    number: str = ""  # 章番号（例: "1", "2.1", "2.1.1"）
    page: str = ""  # 参照ページ番号


@dataclass(frozen=True)
class TableOfContents:
    """Complete Table of Contents."""

    entries: tuple[TocEntry, ...]
    read_aloud: bool = False


@dataclass(frozen=True)
class Page:
    """1ページ"""

    number: str  # 空文字列許容（エラー時）
    source_file: str
    content: Content
    announcement: PageAnnouncement | None = None
    figures: tuple[Figure, ...] = ()
    metadata: PageMetadata | None = None
    continued: bool = False
    page_type: str = "normal"  # "normal", "cover", "colophon", "toc"
    toc: TableOfContents | None = None


@dataclass(frozen=True)
class Book:
    """書籍全体"""

    metadata: BookMetadata
    pages: tuple[Page, ...]  # イミュータブルなタプル


@dataclass(frozen=True)
class ConversionError:
    """変換エラー"""

    error_type: str  # "PAGE_NUMBER_NOT_FOUND", etc.
    message: str
    page_number: str = ""
    line_number: int = 0


@dataclass(frozen=True)
class ConversionResult:
    """変換結果"""

    success: bool
    total_pages: int
    error_count: int
    errors: tuple[ConversionError, ...] = ()
    output_path: str = ""


@dataclass(frozen=True)
class ExclusionPattern:
    """除外パターン定義"""

    id: str  # パターン識別子 (e.g., "running-head", "page-number")
    priority: int  # 優先度 (高い方が先にマッチ試行) 1-100
    pattern: str | None  # 正規表現パターン (dynamicタイプの場合はNone)
    pattern_type: str  # "static" | "dynamic"
    description: str  # 説明 (e.g., "柱（ランニングヘッド）")


@dataclass(frozen=True)
class HeadingAnalysis:
    """heading出現頻度分析結果"""

    text: str  # headingテキスト（正規化済み）
    level: int  # 最頻出時のlevel (1-3)
    count: int  # 出現回数 (1以上)
    levels: tuple[int, ...]  # 出現したlevelのリスト（空でない）
    is_running_head: bool  # 柱として判定されたか
