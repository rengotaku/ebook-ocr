"""Data models for page grouper module."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class FlattenStats:
    """Statistics from page flattening operation."""

    pages_flattened: int = 0
    headings_removed: int = 0

    def __iadd__(self, other: "FlattenStats") -> "FlattenStats":
        """Add another stats object to this one."""
        self.pages_flattened += other.pages_flattened
        self.headings_removed += other.headings_removed
        return self


@dataclass(frozen=True)
class SectionNumber:
    """Parsed section number with hierarchy information."""

    raw: str
    parts: tuple[int, ...]
    level: int  # 1=chapter, 2=section, 3=subsection

    @property
    def chapter_num(self) -> int:
        """Return the chapter number (first part)."""
        return self.parts[0]

    @property
    def effective_parts(self) -> tuple[int, ...]:
        """Strip trailing zeros to get effective hierarchy parts.

        Handles numbering like 1.0.0 (chapter), 1.1.0 (section), 1.1.1 (subsection).
        """
        parts_list = list(self.parts)
        while len(parts_list) > 1 and parts_list[-1] == 0:
            parts_list.pop()
        return tuple(parts_list)

    @property
    def is_chapter(self) -> bool:
        """Return True if this is a chapter number."""
        return len(self.effective_parts) == 1

    @property
    def is_section(self) -> bool:
        """Return True if this is a section number."""
        return len(self.effective_parts) == 2

    @property
    def is_subsection(self) -> bool:
        """Return True if this is a subsection number."""
        return len(self.effective_parts) >= 3


@dataclass(frozen=True)
class TOCEntry:
    """TOC entry from XML."""

    level: int  # 1=chapter, 2=section, 3=subsection
    number: str  # "1", "1.1", "1.1.1"
    title: str
