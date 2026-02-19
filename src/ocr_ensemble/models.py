"""Data models for OCR ensemble results."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class EngineResult:
    """Result from a single OCR engine."""

    engine: str
    text: str
    success: bool
    error: str | None = None


@dataclass
class EnsembleResult:
    """Result from ensemble OCR processing."""

    merged: str  # Final merged text
    results: dict[str, str]  # engine_name -> text
    similarity_matrix: dict[str, dict[str, float]]  # pairwise similarities
    source: str  # Which strategy was used
    votes: dict[str, int] = field(default_factory=dict)  # engine -> vote count


@dataclass
class TextWithBox:
    """Text with bounding box information."""

    text: str
    bbox: list[int]  # [x1, y1, x2, y2]
    confidence: float = 0.0
