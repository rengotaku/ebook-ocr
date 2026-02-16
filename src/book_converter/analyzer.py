"""Heading analyzer for readAloud attribute determination.

Analyzes heading frequency and patterns to determine which headings
should be excluded from TTS reading (readAloud="false").
"""

from __future__ import annotations

import re
from collections import defaultdict

from src.book_converter.models import Heading, HeadingAnalysis, ExclusionPattern
from src.book_converter.config import DEFAULT_EXCLUSION_PATTERNS


# 表記ゆれ正規化用の文字マッピング（ダッシュ類を統一）
_DASH_CHARS = "—–―‐−ー－"  # em dash, en dash, horizontal bar, hyphen, minus, katakana dash, fullwidth hyphen
_NORMALIZED_DASH = "-"  # ASCII hyphen-minus


def normalize_text(text: str) -> str:
    """表記ゆれ正規化（柱検出用）

    ダッシュ類の文字（—, –, ―, ‐, −, ー, －）を
    統一された文字に正規化する。

    Args:
        text: 正規化対象のテキスト

    Returns:
        正規化されたテキスト
    """
    if not text:
        return text

    result = text
    for dash in _DASH_CHARS:
        result = result.replace(dash, _NORMALIZED_DASH)
    return result


def analyze_headings(headings: list[Heading]) -> list[HeadingAnalysis]:
    """heading頻度分析

    表記ゆれ（ダッシュ類の違い）を正規化して集計する。

    Args:
        headings: 分析対象のheadingリスト

    Returns:
        HeadingAnalysisのリスト（各ユニークテキストの出現頻度情報）
    """
    if not headings:
        return []

    # 正規化テキストごとの統計情報を集計
    stats: dict[str, dict] = defaultdict(lambda: {
        "count": 0,
        "levels": [],
        "level_counts": defaultdict(int),
        "original_text": None,  # 最初に出現したオリジナルテキスト
    })

    for heading in headings:
        normalized = normalize_text(heading.text)
        level = heading.level

        # 最初のオリジナルテキストを保存
        if stats[normalized]["original_text"] is None:
            stats[normalized]["original_text"] = heading.text

        stats[normalized]["count"] += 1
        stats[normalized]["levels"].append(level)
        stats[normalized]["level_counts"][level] += 1

    # HeadingAnalysisオブジェクトを生成
    analyses = []
    for normalized_text, data in stats.items():
        # 最頻出レベルを決定
        most_frequent_level = max(
            data["level_counts"].items(),
            key=lambda x: (x[1], -x[0])  # 出現数が多い順、同数なら小さいlevel優先
        )[0]

        # 出現したlevelsをソート済みタプルに変換
        unique_levels = tuple(sorted(set(data["levels"])))

        # 正規化テキストを使用（比較用）
        analysis = HeadingAnalysis(
            text=normalized_text,
            level=most_frequent_level,
            count=data["count"],
            levels=unique_levels,
            is_running_head=False,  # 初期値、detect_running_headで更新
        )
        analyses.append(analysis)

    return analyses


def detect_running_head(
    analyses: list[HeadingAnalysis],
    total_pages: int,
    threshold_ratio: float = 0.5
) -> list[HeadingAnalysis]:
    """柱検出（デフォルト閾値50%）

    Args:
        analyses: heading分析結果リスト
        total_pages: 総ページ数
        threshold_ratio: 柱検出閾値（総ページ数に対する比率、デフォルト: 0.5）

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

    # 指定された閾値以上なら柱として判定
    # ただし、最低でも2回以上出現する必要がある（1回だけの出現は running head ではない）
    threshold = max(total_pages * threshold_ratio, 2)
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
    正規化テキストで比較する。

    Args:
        heading: 対象のHeading
        running_head_texts: 柱として判定されたテキストのセット（正規化済み）

    Returns:
        level再配置後の新しいHeadingオブジェクト（イミュータブル）
    """
    # 正規化テキストで柱判定
    normalized = normalize_text(heading.text)

    # 柱テキストかつlevel != 1 の場合に再配置
    if normalized in running_head_texts and heading.level != 1:
        return Heading(
            level=1,
            text=heading.text,
            read_aloud=heading.read_aloud,
        )

    # それ以外は元のheadingを返す
    return heading


def apply_read_aloud_rules(
    headings: list[Heading],
    analyses: list[HeadingAnalysis],
    verbose: bool = False
) -> list[Heading]:
    """readAloud属性付与

    Args:
        headings: 対象のheadingリスト
        analyses: heading分析結果（柱検出済み）
        verbose: 除外理由を標準出力に表示するかどうか

    Returns:
        readAloud属性を設定した新しいHeadingリスト
    """
    if not headings:
        return []

    # 柱テキスト（正規化済み）のセットを作成
    running_head_texts = {
        a.text for a in analyses if a.is_running_head
    }

    # 柱検出情報を表示（verbose モード）
    if verbose and running_head_texts:
        for analysis in analyses:
            if analysis.is_running_head:
                print(f"[INFO] Detected running head: \"{analysis.text}\" ({analysis.count} occurrences)")

    # 各headingにルールを適用
    processed = []
    for heading in headings:
        # パターンマッチング
        matched_pattern = match_exclusion_pattern(heading.text)

        # 正規化テキストで柱判定
        normalized_heading_text = normalize_text(heading.text)

        # readAloud値を決定
        if normalized_heading_text in running_head_texts:
            # 柱として検出された場合
            new_heading = Heading(
                level=heading.level,
                text=heading.text,
                read_aloud=False,
            )
            if verbose:
                print(f"[INFO] Excluded heading (running-head): \"{heading.text}\"")
        elif matched_pattern:
            # 除外パターンにマッチした場合
            new_heading = Heading(
                level=heading.level,
                text=heading.text,
                read_aloud=False,
            )
            if verbose:
                print(f"[INFO] Excluded heading ({matched_pattern.id}): \"{heading.text}\"")
        else:
            # それ以外は元のread_aloud値を保持
            new_heading = heading

        processed.append(new_heading)

    return processed
