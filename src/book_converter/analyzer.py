"""Heading analyzer for readAloud attribute determination.

Analyzes heading frequency and patterns to determine which headings
should be excluded from TTS reading (readAloud="false").
"""

from __future__ import annotations

import re
from collections import defaultdict

from src.book_converter.models import Heading, HeadingAnalysis, ExclusionPattern
from src.book_converter.config import DEFAULT_EXCLUSION_PATTERNS


def analyze_headings(headings: list[Heading]) -> list[HeadingAnalysis]:
    """heading頻度分析

    Args:
        headings: 分析対象のheadingリスト

    Returns:
        HeadingAnalysisのリスト（各ユニークテキストの出現頻度情報）
    """
    if not headings:
        return []

    # テキストごとの統計情報を集計
    stats: dict[str, dict] = defaultdict(lambda: {
        "count": 0,
        "levels": [],
        "level_counts": defaultdict(int)
    })

    for heading in headings:
        text = heading.text
        level = heading.level

        stats[text]["count"] += 1
        stats[text]["levels"].append(level)
        stats[text]["level_counts"][level] += 1

    # HeadingAnalysisオブジェクトを生成
    analyses = []
    for text, data in stats.items():
        # 最頻出レベルを決定
        most_frequent_level = max(
            data["level_counts"].items(),
            key=lambda x: (x[1], -x[0])  # 出現数が多い順、同数なら小さいlevel優先
        )[0]

        # 出現したlevelsをソート済みタプルに変換
        unique_levels = tuple(sorted(set(data["levels"])))

        analysis = HeadingAnalysis(
            text=text,
            level=most_frequent_level,
            count=data["count"],
            levels=unique_levels,
            is_running_head=False,  # 初期値、detect_running_headで更新
        )
        analyses.append(analysis)

    return analyses


def detect_running_head(
    analyses: list[HeadingAnalysis],
    total_pages: int
) -> list[HeadingAnalysis]:
    """柱検出（閾値50%）

    Args:
        analyses: heading分析結果リスト
        total_pages: 総ページ数

    Returns:
        is_running_headフラグを更新したHeadingAnalysisリスト
    """
    if not analyses or total_pages == 0:
        return analyses

    # level=1 の heading のみを柱候補とする
    level_1_analyses = [a for a in analyses if a.level == 1]

    if not level_1_analyses:
        return analyses

    # 最頻出のlevel=1 headingを特定
    most_frequent = max(level_1_analyses, key=lambda a: a.count)

    # 出現率が50%以上なら柱として判定
    threshold = total_pages * 0.5
    running_head_texts = set()

    if most_frequent.count >= threshold:
        running_head_texts.add(most_frequent.text)

    # is_running_headフラグを更新した新しいリストを生成
    updated_analyses = []
    for analysis in analyses:
        if analysis.text in running_head_texts:
            # 新しいHeadingAnalysisを生成（イミュータブル）
            updated = HeadingAnalysis(
                text=analysis.text,
                level=analysis.level,
                count=analysis.count,
                levels=analysis.levels,
                is_running_head=True,
            )
            updated_analyses.append(updated)
        else:
            updated_analyses.append(analysis)

    return updated_analyses


def match_exclusion_pattern(text: str) -> ExclusionPattern | None:
    """パターンマッチング

    Args:
        text: マッチング対象のテキスト

    Returns:
        マッチしたExclusionPattern、マッチなしはNone
    """
    if not text:
        return None

    # 優先度順にパターンをチェック
    for pattern in DEFAULT_EXCLUSION_PATTERNS:
        # dynamicタイプはこの関数では処理しない
        if pattern.pattern_type == "dynamic":
            continue

        # staticタイプのパターンマッチング
        if pattern.pattern:
            try:
                if re.match(pattern.pattern, text):
                    return pattern
            except re.error:
                # 無効な正規表現の場合はスキップ
                continue

    return None


def reassign_heading_level(
    heading: Heading,
    running_head_texts: set[str]
) -> Heading:
    """level再配置

    柱テキストがlevel 2,3で出現している場合、level 1に再配置する。

    Args:
        heading: 対象のHeading
        running_head_texts: 柱として判定されたテキストのセット

    Returns:
        level再配置後の新しいHeadingオブジェクト（イミュータブル）
    """
    # 柱テキストかつlevel != 1 の場合に再配置
    if heading.text in running_head_texts and heading.level != 1:
        return Heading(
            level=1,
            text=heading.text,
            read_aloud=heading.read_aloud,
        )

    # それ以外は元のheadingを返す
    return heading


def apply_read_aloud_rules(
    headings: list[Heading],
    analyses: list[HeadingAnalysis]
) -> list[Heading]:
    """readAloud属性付与

    Args:
        headings: 対象のheadingリスト
        analyses: heading分析結果（柱検出済み）

    Returns:
        readAloud属性を設定した新しいHeadingリスト
    """
    if not headings:
        return []

    # 柱テキストのセットを作成
    running_head_texts = {
        a.text for a in analyses if a.is_running_head
    }

    # 各headingにルールを適用
    processed = []
    for heading in headings:
        # パターンマッチング
        matched_pattern = match_exclusion_pattern(heading.text)

        # readAloud値を決定
        if heading.text in running_head_texts:
            # 柱として検出された場合
            new_heading = Heading(
                level=heading.level,
                text=heading.text,
                read_aloud=False,
            )
        elif matched_pattern:
            # 除外パターンにマッチした場合
            new_heading = Heading(
                level=heading.level,
                text=heading.text,
                read_aloud=False,
            )
        else:
            # それ以外は元のread_aloud値を保持
            new_heading = heading

        processed.append(new_heading)

    return processed
