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
]
