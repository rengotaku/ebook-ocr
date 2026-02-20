"""Data models for parser package."""

from __future__ import annotations


class StructureHeading:
    """Parsed structure heading with section info."""

    level: int  # 1=chapter, 2=section, 3=subsection
    number: str  # "1", "1.1", "1.1.1"
    title: str  # Title text after number
    raw_text: str  # Original heading text
