"""Configuration for heading exclusion patterns.

Defines default patterns for detecting headings that should be
excluded from TTS reading (readAloud="false").
"""

from __future__ import annotations

from src.book_converter.models import ExclusionPattern


# デフォルト除外パターン（優先度順）
DEFAULT_EXCLUSION_PATTERNS: list[ExclusionPattern] = [
    # 高優先度: 柱（動的検出）
    ExclusionPattern(
        id="running-head",
        priority=100,
        pattern=None,
        pattern_type="dynamic",
        description="柱（ランニングヘッド）",
    ),
    # 高優先度: ページ番号表記（全角ダッシュ or 横棒）
    ExclusionPattern(
        id="page-number",
        priority=90,
        pattern=r".*[―—]\s*\d+\s*/\s*\d+$",
        pattern_type="static",
        description="ページ番号表記",
    ),
    # 中優先度: 装飾記号（連続記号のみ）
    ExclusionPattern(
        id="decoration",
        priority=50,
        pattern=r"^[◆◇■□●○▲△]+$",
        pattern_type="static",
        description="装飾記号（連続記号のみ）",
    ),
    # 中優先度: 章節ラベル（Section X.X形式）
    ExclusionPattern(
        id="section-label",
        priority=50,
        pattern=r"^Section\s+\d+\.\d+$",
        pattern_type="static",
        description="章節ラベル（Section X.X形式）",
    ),
]
