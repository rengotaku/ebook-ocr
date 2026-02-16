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
class Heading:
    """見出し（TOC外の見出し用）"""

    level: int  # 1, 2, 3（0=エラー）
    text: str
    read_aloud: bool = True  # skip区間ではFalse


@dataclass(frozen=True)
class Paragraph:
    """段落"""

    text: str
    read_aloud: bool = True  # skip区間ではFalse


@dataclass(frozen=True)
class List:
    """リスト"""

    items: tuple[str, ...]
    list_type: str = "unordered"  # "unordered" or "ordered"
    read_aloud: bool = True  # skip区間ではFalse


@dataclass(frozen=True)
class Figure:
    """図表"""

    path: str  # 必須: 画像ファイルパス
    caption: str = ""  # 図の説明
    marker: str = ""  # オプション: 元のマーカーテキスト


@dataclass(frozen=True)
class TocEntry:
    """Table of Contents entry."""

    text: str  # エントリのタイトルテキスト
    level: int  # 階層レベル（1-5）
    number: str = ""  # 章番号（例: "1", "2.1", "2.1.1"）
    page: str = ""  # 参照ページ番号


@dataclass(frozen=True)
class TableOfContents:
    """Complete Table of Contents."""

    entries: tuple[TocEntry, ...]
    begin_page: str = ""  # TOCが開始するページ番号
    end_page: str = ""  # TOCが終了するページ番号


# Section の子要素
SectionElement = Union[Heading, Paragraph, List, Figure]


@dataclass(frozen=True)
class Section:
    """セクション（chapter直下）"""

    number: str  # セクション番号（例: "1.1"）
    title: str  # タイトル（ナビゲーション用）
    elements: tuple[SectionElement, ...] = ()


@dataclass(frozen=True)
class Chapter:
    """章"""

    number: str  # 章番号（例: "1"）
    title: str  # タイトル（ナビゲーション用）
    sections: tuple[Section, ...] = ()


@dataclass(frozen=True)
class Book:
    """書籍全体"""

    metadata: BookMetadata
    toc: TableOfContents | None = None
    chapters: tuple[Chapter, ...] = ()
    # Legacy: pages 属性（段階的に削除予定）
    pages: tuple["Page", ...] = ()


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


@dataclass(frozen=True)
class MarkerStats:
    """マーカー統計"""

    toc: int = 0  # <!-- toc --> 開始マーカー数
    content: int = 0  # <!-- content --> 開始マーカー数
    skip: int = 0  # <!-- skip --> 開始マーカー数


@dataclass(frozen=True)
class HeaderLevelConfig:
    """見出しレベルとキーワードのマッピング設定.

    CLI引数から構築される設定。
    例: --header-level1=chapter --header-level2=episode|column

    Attributes:
        level1: レベル1キーワード (e.g., ("chapter",))
        level2: レベル2キーワード (e.g., ("episode", "column"))
        level3: レベル3キーワード
        level4: レベル4キーワード
        level5: レベル5キーワード
    """

    level1: tuple[str, ...] = ()
    level2: tuple[str, ...] = ()
    level3: tuple[str, ...] = ()
    level4: tuple[str, ...] = ()
    level5: tuple[str, ...] = ()

    def get_level_for_keyword(self, keyword: str) -> int | None:
        """キーワードに対応するレベルを返す.

        Args:
            keyword: 検索するキーワード (case-insensitive)

        Returns:
            レベル (1-5) or None
        """
        keyword_lower = keyword.lower()
        if keyword_lower in (k.lower() for k in self.level1):
            return 1
        if keyword_lower in (k.lower() for k in self.level2):
            return 2
        if keyword_lower in (k.lower() for k in self.level3):
            return 3
        if keyword_lower in (k.lower() for k in self.level4):
            return 4
        if keyword_lower in (k.lower() for k in self.level5):
            return 5
        return None

    def get_keywords_for_level(self, level: int) -> tuple[str, ...]:
        """レベルに対応するキーワードを返す.

        Args:
            level: レベル (1-5)

        Returns:
            キーワードのタプル
        """
        return getattr(self, f"level{level}", ())

    def has_any_config(self) -> bool:
        """設定が存在するかどうか."""
        return bool(self.level1 or self.level2 or self.level3 or self.level4 or self.level5)

    @staticmethod
    def from_cli_args(
        level1: str | None = None,
        level2: str | None = None,
        level3: str | None = None,
        level4: str | None = None,
        level5: str | None = None,
    ) -> "HeaderLevelConfig":
        """CLI引数から設定を構築.

        Args:
            level1-5: パイプ区切りのキーワード (e.g., "episode|column")

        Returns:
            HeaderLevelConfig
        """
        def parse(value: str | None) -> tuple[str, ...]:
            if not value:
                return ()
            return tuple(k.strip() for k in value.split("|") if k.strip())

        return HeaderLevelConfig(
            level1=parse(level1),
            level2=parse(level2),
            level3=parse(level3),
            level4=parse(level4),
            level5=parse(level5),
        )


# ============================================================
# Legacy models (parser.py との互換性用、段階的に削除予定)
# ============================================================

@dataclass(frozen=True)
class PageAnnouncement:
    """ページ読み上げ (Legacy)"""

    text: str
    format: str = "simple"


@dataclass(frozen=True)
class Content:
    """本文コンテンツ (Legacy)"""

    elements: tuple[Union[Heading, Paragraph, List], ...]
    read_aloud: bool = False


@dataclass(frozen=True)
class PageMetadata:
    """ページメタデータ (Legacy)"""

    text: str
    meta_type: str = "chapter-page"
    section_name: str = ""
    current: int = 0
    total: int = 0


@dataclass(frozen=True)
class Page:
    """1ページ (Legacy)"""

    number: str
    source_file: str
    content: Content
    announcement: PageAnnouncement | None = None
    figures: tuple[Figure, ...] = ()
    metadata: PageMetadata | None = None
    continued: bool = False
    page_type: str = "normal"


@dataclass(frozen=True)
class StructureContainer:
    """構造コンテナ (Legacy)"""

    container_type: str
    level: int
    number: str
    title: str
    children: tuple  # StructureContainer or ContentElement


# Legacy union type
ContentElement = Union[Heading, Paragraph, List]
