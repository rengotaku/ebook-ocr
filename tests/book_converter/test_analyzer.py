"""Tests for heading analyzer.

Tests for heading frequency analysis and pattern matching.
Phase 2: User Story 1 - T012, T013, T014, T016
"""

from __future__ import annotations

from src.book_converter.models import Heading

# =============================================================================
# T012: 柱検出テスト
# =============================================================================


class TestAnalyzeHeadings:
    """analyze_headings 関数テスト - heading頻度分析"""

    def test_analyze_headings_returns_analysis_list(self) -> None:
        """analyze_headings は HeadingAnalysis のリストを返す"""
        from src.book_converter.analyzer import analyze_headings
        from src.book_converter.models import HeadingAnalysis

        headings = [
            Heading(level=1, text="SREの知識地図"),
            Heading(level=2, text="概要"),
            Heading(level=1, text="SREの知識地図"),
        ]

        result = analyze_headings(headings)

        assert isinstance(result, list)
        assert len(result) > 0
        assert all(isinstance(item, HeadingAnalysis) for item in result)

    def test_analyze_headings_counts_occurrences(self) -> None:
        """各 heading テキストの出現回数をカウント"""
        from src.book_converter.analyzer import analyze_headings

        headings = [
            Heading(level=1, text="SREの知識地図"),
            Heading(level=1, text="SREの知識地図"),
            Heading(level=1, text="SREの知識地図"),
            Heading(level=2, text="概要"),
        ]

        result = analyze_headings(headings)

        # テキスト別のカウントを確認
        analysis_map = {a.text: a for a in result}
        assert analysis_map["SREの知識地図"].count == 3
        assert analysis_map["概要"].count == 1

    def test_analyze_headings_tracks_levels(self) -> None:
        """同一テキストが出現した level をトラッキング"""
        from src.book_converter.analyzer import analyze_headings

        headings = [
            Heading(level=1, text="SREの知識地図"),
            Heading(level=2, text="SREの知識地図"),
            Heading(level=3, text="SREの知識地図"),
        ]

        result = analyze_headings(headings)

        analysis = [a for a in result if a.text == "SREの知識地図"][0]
        assert set(analysis.levels) == {1, 2, 3}

    def test_analyze_headings_empty_list(self) -> None:
        """空のリストを渡した場合は空リストを返す"""
        from src.book_converter.analyzer import analyze_headings

        result = analyze_headings([])

        assert result == []


class TestDetectRunningHead:
    """detect_running_head 関数テスト - 柱検出（閾値50%）"""

    def test_detect_running_head_above_threshold(self) -> None:
        """出現率50%以上で柱として検出"""
        from src.book_converter.analyzer import analyze_headings, detect_running_head

        # 10ページ分のheadingで、5回以上出現 = 50%以上
        headings = [Heading(level=1, text="SREの知識地図") for _ in range(6)]
        headings.extend([Heading(level=2, text="その他") for _ in range(4)])

        analyses = analyze_headings(headings)
        total_pages = 10

        result = detect_running_head(analyses, total_pages)

        running_heads = [a for a in result if a.is_running_head]
        assert len(running_heads) >= 1
        assert any(a.text == "SREの知識地図" for a in running_heads)

    def test_detect_running_head_below_threshold(self) -> None:
        """出現率50%未満は柱として検出されない"""
        from src.book_converter.analyzer import analyze_headings, detect_running_head

        # 10ページ分のheadingで、4回出現 = 40% < 50%
        headings = [Heading(level=1, text="SREの知識地図") for _ in range(4)]
        headings.extend([Heading(level=2, text="その他") for _ in range(6)])

        analyses = analyze_headings(headings)
        total_pages = 10

        result = detect_running_head(analyses, total_pages)

        running_heads = [a for a in result if a.is_running_head]
        # 50%未満なので柱として検出されない
        assert not any(a.text == "SREの知識地図" for a in running_heads)

    def test_detect_running_head_level_1_only(self) -> None:
        """level=1 の heading のみを柱候補とする"""
        from src.book_converter.analyzer import analyze_headings, detect_running_head

        headings = [Heading(level=1, text="柱タイトル") for _ in range(6)]
        headings.extend([Heading(level=2, text="サブタイトル") for _ in range(6)])

        analyses = analyze_headings(headings)
        total_pages = 10

        result = detect_running_head(analyses, total_pages)

        running_heads = [a for a in result if a.is_running_head]
        # level=1 のみが柱候補
        assert any(a.text == "柱タイトル" for a in running_heads)

    def test_detect_running_head_most_frequent(self) -> None:
        """最頻出の level=1 heading を柱として検出"""
        from src.book_converter.analyzer import analyze_headings, detect_running_head

        headings = [Heading(level=1, text="書籍タイトル") for _ in range(8)]
        headings.extend([Heading(level=1, text="別のタイトル") for _ in range(5)])

        analyses = analyze_headings(headings)
        total_pages = 10

        result = detect_running_head(analyses, total_pages)

        # 最頻出の "書籍タイトル" が柱
        running_heads = [a for a in result if a.is_running_head]
        assert any(a.text == "書籍タイトル" for a in running_heads)


# =============================================================================
# T013: ページ番号パターンテスト
# =============================================================================


class TestMatchExclusionPattern:
    """match_exclusion_pattern 関数テスト - パターンマッチング"""

    def test_match_page_number_pattern(self) -> None:
        """ページ番号表記 `X.X.X タイトル — N / M` をマッチ"""
        from src.book_converter.analyzer import match_exclusion_pattern

        # 正常なページ番号表記
        text = "1.1.1 SREの概要 — 1 / 3"
        result = match_exclusion_pattern(text)

        assert result is not None
        assert result.id == "page-number"

    def test_match_page_number_em_dash(self) -> None:
        """全角ダッシュ（—）を含むページ番号表記"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "2.3.4 モニタリング — 15 / 20"
        result = match_exclusion_pattern(text)

        assert result is not None
        assert result.id == "page-number"

    def test_match_page_number_horizontal_bar(self) -> None:
        """横棒（―）を含むページ番号表記"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "3.1.2 アラート設計 ― 7 / 12"
        result = match_exclusion_pattern(text)

        assert result is not None
        assert result.id == "page-number"

    def test_no_match_normal_heading(self) -> None:
        """通常の見出しはマッチしない"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "3.2.1 モニタリングの基本"
        result = match_exclusion_pattern(text)

        # ページ番号表記パターンにはマッチしない
        assert result is None or result.id != "page-number"

    def test_no_match_empty_string(self) -> None:
        """空文字列はマッチしない"""
        from src.book_converter.analyzer import match_exclusion_pattern

        result = match_exclusion_pattern("")

        assert result is None


# =============================================================================
# T014: level再配置テスト
# =============================================================================


class TestReassignHeadingLevel:
    """reassign_heading_level 関数テスト - level再配置"""

    def test_reassign_level_2_to_1(self) -> None:
        """柱テキストが level 2 で出現 → level 1 に再配置"""
        from src.book_converter.analyzer import reassign_heading_level

        heading = Heading(level=2, text="SREの知識地図")
        running_head_texts = {"SREの知識地図"}

        result = reassign_heading_level(heading, running_head_texts)

        assert result.level == 1
        assert result.text == "SREの知識地図"

    def test_reassign_level_3_to_1(self) -> None:
        """柱テキストが level 3 で出現 → level 1 に再配置"""
        from src.book_converter.analyzer import reassign_heading_level

        heading = Heading(level=3, text="SREの知識地図")
        running_head_texts = {"SREの知識地図"}

        result = reassign_heading_level(heading, running_head_texts)

        assert result.level == 1
        assert result.text == "SREの知識地図"

    def test_no_reassign_non_running_head(self) -> None:
        """柱テキスト以外は再配置しない"""
        from src.book_converter.analyzer import reassign_heading_level

        heading = Heading(level=2, text="通常の見出し")
        running_head_texts = {"SREの知識地図"}

        result = reassign_heading_level(heading, running_head_texts)

        assert result.level == 2  # 変更なし
        assert result.text == "通常の見出し"

    def test_no_reassign_already_level_1(self) -> None:
        """level 1 の柱は再配置不要"""
        from src.book_converter.analyzer import reassign_heading_level

        heading = Heading(level=1, text="SREの知識地図")
        running_head_texts = {"SREの知識地図"}

        result = reassign_heading_level(heading, running_head_texts)

        assert result.level == 1
        assert result.text == "SREの知識地図"

    def test_reassign_preserves_read_aloud(self) -> None:
        """再配置時に read_aloud 属性を保持"""
        from src.book_converter.analyzer import reassign_heading_level

        heading = Heading(level=2, text="SREの知識地図", read_aloud=False)
        running_head_texts = {"SREの知識地図"}

        result = reassign_heading_level(heading, running_head_texts)

        assert result.level == 1
        assert result.read_aloud is False

    def test_reassign_returns_new_heading(self) -> None:
        """再配置は新しい Heading オブジェクトを返す（イミュータブル）"""
        from src.book_converter.analyzer import reassign_heading_level

        heading = Heading(level=2, text="SREの知識地図")
        running_head_texts = {"SREの知識地図"}

        result = reassign_heading_level(heading, running_head_texts)

        # 新しいオブジェクトを返す（元のオブジェクトは変更されない）
        assert result is not heading


# =============================================================================
# T016: 統合テスト
# =============================================================================


class TestHeadingAnalysisIntegration:
    """Markdown → heading分析 → 属性付与フロー統合テスト"""

    def test_full_flow_running_head_detection(self) -> None:
        """柱検出から readAloud=False 付与までのフロー"""
        from src.book_converter.analyzer import (
            analyze_headings,
            apply_read_aloud_rules,
            detect_running_head,
        )

        # 10ページ分の heading を模擬
        headings = []
        for i in range(10):
            # 各ページに柱（書籍タイトル）
            headings.append(Heading(level=1, text="SREの知識地図"))
            # 各ページに本文見出し
            headings.append(Heading(level=2, text=f"セクション{i + 1}"))

        # 分析
        analyses = analyze_headings(headings)
        total_pages = 10

        # 柱検出
        analyses_with_running_head = detect_running_head(analyses, total_pages)

        # readAloud ルール適用
        processed_headings = apply_read_aloud_rules(
            headings, analyses_with_running_head
        )

        # 柱は readAloud=False
        running_head_headings = [
            h for h in processed_headings if h.text == "SREの知識地図"
        ]
        assert all(h.read_aloud is False for h in running_head_headings)

        # 本文見出しは readAloud=True
        section_headings = [
            h for h in processed_headings if h.text.startswith("セクション")
        ]
        assert all(h.read_aloud is True for h in section_headings)

    def test_full_flow_page_number_exclusion(self) -> None:
        """ページ番号表記の readAloud=False 付与フロー"""
        from src.book_converter.analyzer import apply_read_aloud_rules

        headings = [
            Heading(level=3, text="1.1.1 SREの概要 — 1 / 3"),
            Heading(level=2, text="なぜSREが重要なのか"),
            Heading(level=3, text="2.3.4 モニタリング — 15 / 20"),
        ]

        # ページ番号表記を含む heading は除外
        processed_headings = apply_read_aloud_rules(headings, [])

        # ページ番号表記は readAloud=False
        page_number_headings = [h for h in processed_headings if "—" in h.text]
        assert all(h.read_aloud is False for h in page_number_headings)

        # 通常の見出しは readAloud=True
        normal_headings = [
            h for h in processed_headings if h.text == "なぜSREが重要なのか"
        ]
        assert all(h.read_aloud is True for h in normal_headings)

    def test_full_flow_level_reassignment(self) -> None:
        """level 再配置を含むフロー"""
        from src.book_converter.analyzer import (
            analyze_headings,
            detect_running_head,
            reassign_heading_level,
        )

        headings = [
            Heading(level=1, text="SREの知識地図"),
            Heading(level=2, text="SREの知識地図"),  # level 2 で柱が出現
            Heading(level=3, text="SREの知識地図"),  # level 3 で柱が出現
        ]
        # 追加で出現回数を増やす
        headings.extend([Heading(level=1, text="SREの知識地図") for _ in range(7)])

        analyses = analyze_headings(headings)
        total_pages = 10

        analyses_with_running_head = detect_running_head(analyses, total_pages)
        running_head_texts = {
            a.text for a in analyses_with_running_head if a.is_running_head
        }

        # level 再配置
        reassigned_headings = [
            reassign_heading_level(h, running_head_texts) for h in headings
        ]

        # 全ての柱テキストは level=1 に再配置
        running_head_result = [
            h for h in reassigned_headings if h.text == "SREの知識地図"
        ]
        assert all(h.level == 1 for h in running_head_result)

    def test_full_flow_empty_headings(self) -> None:
        """空の heading リストを処理"""
        from src.book_converter.analyzer import (
            analyze_headings,
            apply_read_aloud_rules,
            detect_running_head,
        )

        headings = []

        analyses = analyze_headings(headings)
        analyses_with_running_head = detect_running_head(analyses, 0)
        processed_headings = apply_read_aloud_rules(
            headings, analyses_with_running_head
        )

        assert processed_headings == []

    def test_full_flow_unicode_headings(self) -> None:
        """Unicode テキストを含む heading を処理"""
        from src.book_converter.analyzer import (
            analyze_headings,
            apply_read_aloud_rules,
            detect_running_head,
        )

        headings = [
            Heading(level=1, text="日本語タイトル「テスト」"),
            Heading(level=1, text="日本語タイトル「テスト」"),
            Heading(level=1, text="日本語タイトル「テスト」"),
            Heading(level=1, text="日本語タイトル「テスト」"),
            Heading(level=1, text="日本語タイトル「テスト」"),
            Heading(level=1, text="日本語タイトル「テスト」"),
        ]

        analyses = analyze_headings(headings)
        total_pages = 10

        analyses_with_running_head = detect_running_head(analyses, total_pages)
        processed_headings = apply_read_aloud_rules(
            headings, analyses_with_running_head
        )

        # Unicode テキストでも正しく処理
        assert len(processed_headings) == 6
        assert all(h.read_aloud is False for h in processed_headings)


# =============================================================================
# T034: 装飾記号パターンテスト (Phase 3: User Story 2)
# =============================================================================


class TestDecorationPatternMatching:
    """装飾記号パターンテスト - ◆◆◆等の連続記号を除外"""

    def test_match_diamond_pattern(self) -> None:
        """◆◆◆（黒ひし形連続）をマッチ"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "◆◆◆"
        result = match_exclusion_pattern(text)

        assert result is not None
        assert result.id == "decoration"

    def test_match_white_diamond_pattern(self) -> None:
        """◇◇◇（白ひし形連続）をマッチ"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "◇◇◇"
        result = match_exclusion_pattern(text)

        assert result is not None
        assert result.id == "decoration"

    def test_match_black_square_pattern(self) -> None:
        """■■■（黒四角連続）をマッチ"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "■■■"
        result = match_exclusion_pattern(text)

        assert result is not None
        assert result.id == "decoration"

    def test_match_white_square_pattern(self) -> None:
        """□□□（白四角連続）をマッチ"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "□□□"
        result = match_exclusion_pattern(text)

        assert result is not None
        assert result.id == "decoration"

    def test_match_black_circle_pattern(self) -> None:
        """●●●（黒丸連続）をマッチ"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "●●●"
        result = match_exclusion_pattern(text)

        assert result is not None
        assert result.id == "decoration"

    def test_match_white_circle_pattern(self) -> None:
        """○○○（白丸連続）をマッチ"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "○○○"
        result = match_exclusion_pattern(text)

        assert result is not None
        assert result.id == "decoration"

    def test_match_black_triangle_pattern(self) -> None:
        """▲▲▲（黒三角連続）をマッチ"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "▲▲▲"
        result = match_exclusion_pattern(text)

        assert result is not None
        assert result.id == "decoration"

    def test_match_white_triangle_pattern(self) -> None:
        """△△△（白三角連続）をマッチ"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "△△△"
        result = match_exclusion_pattern(text)

        assert result is not None
        assert result.id == "decoration"

    def test_match_mixed_decoration_pattern(self) -> None:
        """◆◇◆（混合記号）をマッチ"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "◆◇◆"
        result = match_exclusion_pattern(text)

        assert result is not None
        assert result.id == "decoration"

    def test_match_single_decoration_pattern(self) -> None:
        """◆（単一記号）をマッチ"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "◆"
        result = match_exclusion_pattern(text)

        assert result is not None
        assert result.id == "decoration"

    def test_no_match_decoration_with_text(self) -> None:
        """◆ポイント（記号+テキスト）は装飾パターンにマッチしない"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "◆ポイント"
        result = match_exclusion_pattern(text)

        # 装飾パターンにはマッチしない（記号のみが対象）
        assert result is None or result.id != "decoration"


# =============================================================================
# T035: 章節ラベルパターンテスト (Phase 3: User Story 2)
# =============================================================================


class TestSectionLabelPatternMatching:
    """章節ラベルパターンテスト - Section X.X形式を除外"""

    def test_match_section_label_simple(self) -> None:
        """Section 1.1 をマッチ"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "Section 1.1"
        result = match_exclusion_pattern(text)

        assert result is not None
        assert result.id == "section-label"

    def test_match_section_label_double_digit(self) -> None:
        """Section 10.15 をマッチ"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "Section 10.15"
        result = match_exclusion_pattern(text)

        assert result is not None
        assert result.id == "section-label"

    def test_match_section_label_with_extra_spaces(self) -> None:
        """Section  1.2（スペース複数）をマッチ"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "Section  1.2"
        result = match_exclusion_pattern(text)

        assert result is not None
        assert result.id == "section-label"

    def test_no_match_section_label_with_title(self) -> None:
        """Section 1.1 概要（ラベル+タイトル）はセクションラベルにマッチしない"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "Section 1.1 概要"
        result = match_exclusion_pattern(text)

        # タイトル付きはセクションラベルパターンにマッチしない
        assert result is None or result.id != "section-label"

    def test_no_match_lowercase_section(self) -> None:
        """section 1.1（小文字）はマッチしない"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "section 1.1"
        result = match_exclusion_pattern(text)

        # 大文字Sectionのみがマッチ
        assert result is None or result.id != "section-label"


# =============================================================================
# T036: 本文見出し除外されないテスト (Phase 3: User Story 2)
# =============================================================================


class TestNormalHeadingNotExcluded:
    """本文見出しが誤って除外されないことを確認"""

    def test_normal_heading_not_excluded_numbered(self) -> None:
        """番号付き見出し「3.2.1 モニタリングの基本」は除外されない"""
        from src.book_converter.analyzer import apply_read_aloud_rules

        headings = [
            Heading(level=2, text="3.2.1 モニタリングの基本"),
        ]

        processed = apply_read_aloud_rules(headings, [])

        assert len(processed) == 1
        # 通常の見出しはreadAloud=True
        assert processed[0].read_aloud is True

    def test_normal_heading_not_excluded_simple(self) -> None:
        """シンプルな見出し「概要」は除外されない"""
        from src.book_converter.analyzer import apply_read_aloud_rules

        headings = [
            Heading(level=2, text="概要"),
        ]

        processed = apply_read_aloud_rules(headings, [])

        assert len(processed) == 1
        assert processed[0].read_aloud is True

    def test_normal_heading_not_excluded_with_colon(self) -> None:
        """コロン付き見出し「第1章：はじめに」は除外されない"""
        from src.book_converter.analyzer import apply_read_aloud_rules

        headings = [
            Heading(level=1, text="第1章：はじめに"),
        ]

        processed = apply_read_aloud_rules(headings, [])

        assert len(processed) == 1
        assert processed[0].read_aloud is True

    def test_heading_with_symbol_in_text_not_excluded(self) -> None:
        """テキスト内に記号を含む「◆ポイント」は除外されない"""
        from src.book_converter.analyzer import apply_read_aloud_rules

        headings = [
            Heading(level=2, text="◆ポイント"),
        ]

        processed = apply_read_aloud_rules(headings, [])

        # 記号のみではないのでデコレーションパターンにマッチしない
        assert len(processed) == 1
        assert processed[0].read_aloud is True

    def test_heading_with_section_keyword_not_excluded(self) -> None:
        """'Section'を含む本文見出し「Section 1.1 概要」は除外されない"""
        from src.book_converter.analyzer import apply_read_aloud_rules

        headings = [
            Heading(level=2, text="Section 1.1 概要"),
        ]

        processed = apply_read_aloud_rules(headings, [])

        # タイトル付きなのでセクションラベルパターンにマッチしない
        assert len(processed) == 1
        assert processed[0].read_aloud is True

    def test_decoration_heading_should_be_excluded(self) -> None:
        """装飾記号のみの見出し「◆◆◆」は除外される"""
        from src.book_converter.analyzer import apply_read_aloud_rules

        headings = [
            Heading(level=2, text="◆◆◆"),
        ]

        processed = apply_read_aloud_rules(headings, [])

        assert len(processed) == 1
        # 装飾記号のみはreadAloud=False
        assert processed[0].read_aloud is False

    def test_section_label_heading_should_be_excluded(self) -> None:
        """セクションラベル「Section 1.1」は除外される"""
        from src.book_converter.analyzer import apply_read_aloud_rules

        headings = [
            Heading(level=3, text="Section 1.1"),
        ]

        processed = apply_read_aloud_rules(headings, [])

        assert len(processed) == 1
        # セクションラベルはreadAloud=False
        assert processed[0].read_aloud is False

    def test_mixed_headings_correct_exclusion(self) -> None:
        """混合見出しで正しい除外判定"""
        from src.book_converter.analyzer import apply_read_aloud_rules

        headings = [
            Heading(level=1, text="第1章：はじめに"),        # 通常 → True
            Heading(level=2, text="◆◆◆"),                   # 装飾 → False
            Heading(level=2, text="1.1 概要"),               # 通常 → True
            Heading(level=3, text="Section 2.3"),            # ラベル → False
            Heading(level=2, text="3.2.1 モニタリングの基本"),  # 通常 → True
        ]

        processed = apply_read_aloud_rules(headings, [])

        assert len(processed) == 5
        # 通常見出しはTrue
        assert processed[0].read_aloud is True  # 第1章：はじめに
        # 装飾記号はFalse
        assert processed[1].read_aloud is False  # ◆◆◆
        # 通常見出しはTrue
        assert processed[2].read_aloud is True  # 1.1 概要
        # セクションラベルはFalse
        assert processed[3].read_aloud is False  # Section 2.3
        # 通常見出しはTrue
        assert processed[4].read_aloud is True  # 3.2.1 モニタリングの基本


# =============================================================================
# T048: Webサイト参照パターンテスト (Phase 4: User Story 3)
# =============================================================================


class TestWebsiteReferencePatternMatching:
    """Webサイト参照パターンテスト - 単独で「Webサイト」のみの見出しを除外"""

    def test_match_website_reference_exact(self) -> None:
        """「Webサイト」（完全一致）をマッチ"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "Webサイト"
        result = match_exclusion_pattern(text)

        assert result is not None
        assert result.id == "reference"

    def test_no_match_website_with_prefix(self) -> None:
        """「参考Webサイト」（前置詞あり）はマッチしない"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "参考Webサイト"
        result = match_exclusion_pattern(text)

        # 完全一致のみなのでマッチしない
        assert result is None or result.id != "reference"

    def test_no_match_website_with_suffix(self) -> None:
        """「Webサイト一覧」（接尾辞あり）はマッチしない"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "Webサイト一覧"
        result = match_exclusion_pattern(text)

        # 完全一致のみなのでマッチしない
        assert result is None or result.id != "reference"

    def test_no_match_website_lowercase(self) -> None:
        """「webサイト」（小文字）はマッチしない"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "webサイト"
        result = match_exclusion_pattern(text)

        # 大文字Webのみがマッチ
        assert result is None or result.id != "reference"

    def test_no_match_website_partial(self) -> None:
        """「Webサイトを参照」はマッチしない"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "Webサイトを参照"
        result = match_exclusion_pattern(text)

        # 完全一致のみなのでマッチしない
        assert result is None or result.id != "reference"

    def test_website_reference_read_aloud_false(self) -> None:
        """「Webサイト」見出しはreadAloud=Falseとなる"""
        from src.book_converter.analyzer import apply_read_aloud_rules

        headings = [
            Heading(level=2, text="Webサイト"),
        ]

        processed = apply_read_aloud_rules(headings, [])

        assert len(processed) == 1
        assert processed[0].read_aloud is False


# =============================================================================
# T049: 脚注番号パターンテスト (Phase 4: User Story 3)
# =============================================================================


class TestFootnotePatternMatching:
    """脚注番号パターンテスト - 「注X.X」形式を除外"""

    def test_match_footnote_simple(self) -> None:
        """「注3.1」をマッチ"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "注3.1"
        result = match_exclusion_pattern(text)

        assert result is not None
        assert result.id == "footnote"

    def test_match_footnote_double_digit(self) -> None:
        """「注10.2」（2桁）をマッチ"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "注10.2"
        result = match_exclusion_pattern(text)

        assert result is not None
        assert result.id == "footnote"

    def test_match_footnote_large_numbers(self) -> None:
        """「注123.45」（大きな数字）をマッチ"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "注123.45"
        result = match_exclusion_pattern(text)

        assert result is not None
        assert result.id == "footnote"

    def test_match_footnote_with_trailing_text(self) -> None:
        """「注3.1 補足説明」（後続テキストあり）もマッチ"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "注3.1 補足説明"
        result = match_exclusion_pattern(text)

        # 先頭マッチパターンなので後続テキストがあってもマッチ
        assert result is not None
        assert result.id == "footnote"

    def test_no_match_footnote_without_number(self) -> None:
        """「注」のみはマッチしない"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "注"
        result = match_exclusion_pattern(text)

        # 数字パターンがないのでマッチしない
        assert result is None or result.id != "footnote"

    def test_no_match_footnote_in_sentence(self) -> None:
        """「本文中の注3.1を参照」（文中）はマッチしない"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "本文中の注3.1を参照"
        result = match_exclusion_pattern(text)

        # 先頭が「注」ではないのでマッチしない
        assert result is None or result.id != "footnote"

    def test_no_match_different_note_format(self) -> None:
        """「注記3」（異なる形式）はマッチしない"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "注記3"
        result = match_exclusion_pattern(text)

        # 「注X.X」形式ではないのでマッチしない
        assert result is None or result.id != "footnote"

    def test_footnote_read_aloud_false(self) -> None:
        """「注3.1」見出しはreadAloud=Falseとなる"""
        from src.book_converter.analyzer import apply_read_aloud_rules

        headings = [
            Heading(level=3, text="注3.1"),
        ]

        processed = apply_read_aloud_rules(headings, [])

        assert len(processed) == 1
        assert processed[0].read_aloud is False


# =============================================================================
# 統合テスト: User Story 3 パターン (Phase 4)
# =============================================================================


class TestUserStory3Integration:
    """User Story 3 の統合テスト - 参照・メタ情報の除外"""

    def test_mixed_headings_with_reference_and_footnote(self) -> None:
        """参照表記と脚注番号を含む混合見出しで正しい除外判定"""
        from src.book_converter.analyzer import apply_read_aloud_rules

        headings = [
            Heading(level=1, text="第1章：はじめに"),        # 通常 → True
            Heading(level=2, text="Webサイト"),              # 参照 → False
            Heading(level=2, text="1.1 概要"),               # 通常 → True
            Heading(level=3, text="注3.1"),                  # 脚注 → False
            Heading(level=2, text="参考文献"),               # 通常 → True
        ]

        processed = apply_read_aloud_rules(headings, [])

        assert len(processed) == 5
        # 通常見出しはTrue
        assert processed[0].read_aloud is True  # 第1章：はじめに
        # 参照表記はFalse
        assert processed[1].read_aloud is False  # Webサイト
        # 通常見出しはTrue
        assert processed[2].read_aloud is True  # 1.1 概要
        # 脚注番号はFalse
        assert processed[3].read_aloud is False  # 注3.1
        # 通常見出しはTrue
        assert processed[4].read_aloud is True  # 参考文献

    def test_all_exclusion_patterns_together(self) -> None:
        """全除外パターン（US1, US2, US3）を含む混合見出しで正しい除外判定"""
        from src.book_converter.analyzer import apply_read_aloud_rules

        headings = [
            Heading(level=1, text="第1章：はじめに"),           # 通常 → True
            Heading(level=2, text="◆◆◆"),                      # 装飾 → False (US2)
            Heading(level=3, text="Section 2.3"),               # ラベル → False (US2)
            Heading(level=2, text="Webサイト"),                 # 参照 → False (US3)
            Heading(level=3, text="注10.5"),                    # 脚注 → False (US3)
            Heading(level=2, text="1.1.1 概要 — 1 / 3"),        # ページ番号 → False (US1)
            Heading(level=2, text="3.2.1 モニタリングの基本"),  # 通常 → True
        ]

        processed = apply_read_aloud_rules(headings, [])

        assert len(processed) == 7
        # 通常見出しはTrue
        assert processed[0].read_aloud is True  # 第1章：はじめに
        # 装飾記号はFalse
        assert processed[1].read_aloud is False  # ◆◆◆
        # セクションラベルはFalse
        assert processed[2].read_aloud is False  # Section 2.3
        # 参照表記はFalse
        assert processed[3].read_aloud is False  # Webサイト
        # 脚注番号はFalse
        assert processed[4].read_aloud is False  # 注10.5
        # ページ番号表記はFalse
        assert processed[5].read_aloud is False  # 1.1.1 概要 — 1 / 3
        # 通常見出しはTrue
        assert processed[6].read_aloud is True  # 3.2.1 モニタリングの基本


# =============================================================================
# 表記ゆれ正規化テスト
# =============================================================================


class TestNormalizeText:
    """normalize_text 関数テスト - ダッシュ類の正規化"""

    def test_normalize_em_dash(self) -> None:
        """em dash (—) を正規化"""
        from src.book_converter.analyzer import normalize_text

        result = normalize_text("SREの知識地図——基礎知識")
        assert "—" not in result
        assert "-" in result

    def test_normalize_horizontal_bar(self) -> None:
        """horizontal bar (―) を正規化"""
        from src.book_converter.analyzer import normalize_text

        result = normalize_text("SREの知識地図――基礎知識")
        assert "―" not in result
        assert "-" in result

    def test_normalize_en_dash(self) -> None:
        """en dash (–) を正規化"""
        from src.book_converter.analyzer import normalize_text

        result = normalize_text("2020–2025")
        assert "–" not in result
        assert "-" in result

    def test_normalize_katakana_dash(self) -> None:
        """カタカナ長音 (ー) を正規化"""
        from src.book_converter.analyzer import normalize_text

        result = normalize_text("データー")
        assert "ー" not in result
        assert "-" in result

    def test_normalize_fullwidth_hyphen(self) -> None:
        """全角ハイフン (－) を正規化"""
        from src.book_converter.analyzer import normalize_text

        result = normalize_text("半角－全角")
        assert "－" not in result
        assert "-" in result

    def test_normalize_empty_string(self) -> None:
        """空文字列は空文字列を返す"""
        from src.book_converter.analyzer import normalize_text

        assert normalize_text("") == ""

    def test_normalize_no_dash_unchanged(self) -> None:
        """ダッシュを含まないテキストは変更なし"""
        from src.book_converter.analyzer import normalize_text

        text = "通常のテキスト"
        assert normalize_text(text) == text


class TestRunningHeadWithTextVariation:
    """表記ゆれを含む柱検出テスト"""

    def test_detect_running_head_with_dash_variation(self) -> None:
        """ダッシュの違い（―― vs ——）を同じ柱として検出"""
        from src.book_converter.analyzer import analyze_headings, detect_running_head

        headings = [
            # 61回: horizontal bar (――)
            *[Heading(level=1, text="SREの知識地図――基礎知識から現場まで") for _ in range(61)],
            # 36回: em dash (——)
            *[Heading(level=1, text="SREの知識地図——基礎知識から現場まで") for _ in range(36)],
        ]

        analyses = analyze_headings(headings)
        analyses = detect_running_head(analyses, total_pages=97, threshold_ratio=0.5)

        # 合計97回出現なので、50%閾値 (48.5) を超える → 柱として検出されるべき
        running_heads = [a for a in analyses if a.is_running_head]
        assert len(running_heads) == 1
        assert running_heads[0].count == 97

    def test_apply_rules_with_dash_variation(self) -> None:
        """ダッシュ表記ゆれを持つ見出しに正しくreadAloud=falseを設定"""
        from src.book_converter.analyzer import (
            analyze_headings,
            apply_read_aloud_rules,
            detect_running_head,
        )

        headings = [
            Heading(level=1, text="SREの知識地図――基礎知識"),  # horizontal bar
            Heading(level=1, text="SREの知識地図——基礎知識"),  # em dash
            Heading(level=1, text="SREの知識地図――基礎知識"),  # horizontal bar
            Heading(level=2, text="第1章"),
        ]

        analyses = analyze_headings(headings)
        analyses = detect_running_head(analyses, total_pages=4, threshold_ratio=0.5)

        processed = apply_read_aloud_rules(headings, analyses)

        # 柱テキスト（表記ゆれを含む）はreadAloud=false
        assert processed[0].read_aloud is False  # horizontal bar
        assert processed[1].read_aloud is False  # em dash
        assert processed[2].read_aloud is False  # horizontal bar
        # 通常見出しはreadAloud=true
        assert processed[3].read_aloud is True
