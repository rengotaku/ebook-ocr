"""Tests for book converter models.

Tests for Phase 2: User Story 1 - ExclusionPattern and HeadingAnalysis models.
"""

from __future__ import annotations

import pytest
import re


# =============================================================================
# T010: ExclusionPattern モデルテスト
# =============================================================================


class TestExclusionPattern:
    """ExclusionPattern dataclass のフィールドテスト"""

    def test_exclusion_pattern_fields_exist(self) -> None:
        """ExclusionPattern には必須フィールドが存在する"""
        from src.book_converter.models import ExclusionPattern

        pattern = ExclusionPattern(
            id="running-head",
            priority=100,
            pattern=None,
            pattern_type="dynamic",
            description="柱（ランニングヘッド）",
        )

        assert pattern.id == "running-head"
        assert pattern.priority == 100
        assert pattern.pattern is None
        assert pattern.pattern_type == "dynamic"
        assert pattern.description == "柱（ランニングヘッド）"

    def test_exclusion_pattern_static_type(self) -> None:
        """static タイプのパターン定義"""
        from src.book_converter.models import ExclusionPattern

        pattern = ExclusionPattern(
            id="page-number",
            priority=90,
            pattern=r".*[―—]\s*\d+\s*/\s*\d+$",
            pattern_type="static",
            description="ページ番号表記",
        )

        assert pattern.id == "page-number"
        assert pattern.priority == 90
        assert pattern.pattern == r".*[―—]\s*\d+\s*/\s*\d+$"
        assert pattern.pattern_type == "static"

    def test_exclusion_pattern_is_immutable(self) -> None:
        """ExclusionPattern は frozen dataclass（イミュータブル）"""
        from src.book_converter.models import ExclusionPattern

        pattern = ExclusionPattern(
            id="test",
            priority=50,
            pattern=r"^test$",
            pattern_type="static",
            description="テスト",
        )

        # frozen=True なので属性変更で FrozenInstanceError が発生する
        with pytest.raises(Exception):  # FrozenInstanceError
            pattern.id = "changed"

    def test_exclusion_pattern_id_validation(self) -> None:
        """id は非空文字列、英数字とハイフンのみ"""
        from src.book_converter.models import ExclusionPattern

        # 正常なID
        pattern = ExclusionPattern(
            id="running-head-1",
            priority=100,
            pattern=None,
            pattern_type="dynamic",
            description="柱",
        )
        assert pattern.id == "running-head-1"

    def test_exclusion_pattern_priority_range(self) -> None:
        """priority は 1-100 の整数"""
        from src.book_converter.models import ExclusionPattern

        # 正常な優先度
        pattern_low = ExclusionPattern(
            id="low",
            priority=1,
            pattern=r"^test$",
            pattern_type="static",
            description="低優先度",
        )
        assert pattern_low.priority == 1

        pattern_high = ExclusionPattern(
            id="high",
            priority=100,
            pattern=r"^test$",
            pattern_type="static",
            description="高優先度",
        )
        assert pattern_high.priority == 100

    def test_exclusion_pattern_static_requires_pattern(self) -> None:
        """pattern_type='static' の場合は pattern が必須"""
        from src.book_converter.models import ExclusionPattern

        # static タイプでパターンあり
        pattern = ExclusionPattern(
            id="section-label",
            priority=50,
            pattern=r"^Section\s+\d+\.\d+$",
            pattern_type="static",
            description="章節ラベル",
        )
        assert pattern.pattern is not None

    def test_exclusion_pattern_dynamic_pattern_is_none(self) -> None:
        """pattern_type='dynamic' の場合は pattern が None"""
        from src.book_converter.models import ExclusionPattern

        pattern = ExclusionPattern(
            id="running-head",
            priority=100,
            pattern=None,
            pattern_type="dynamic",
            description="柱",
        )
        assert pattern.pattern is None
        assert pattern.pattern_type == "dynamic"

    def test_exclusion_pattern_valid_regex(self) -> None:
        """pattern は有効な正規表現"""
        from src.book_converter.models import ExclusionPattern

        pattern = ExclusionPattern(
            id="page-number",
            priority=90,
            pattern=r".*[―—]\s*\d+\s*/\s*\d+$",
            pattern_type="static",
            description="ページ番号",
        )

        # 正規表現としてコンパイル可能
        compiled = re.compile(pattern.pattern)
        assert compiled is not None

        # 実際のマッチングテスト
        assert compiled.match("1.1.1 SREの概要 — 1 / 3") is not None


# =============================================================================
# T011: HeadingAnalysis モデルテスト
# =============================================================================


class TestHeadingAnalysis:
    """HeadingAnalysis dataclass のフィールドテスト"""

    def test_heading_analysis_fields_exist(self) -> None:
        """HeadingAnalysis には必須フィールドが存在する"""
        from src.book_converter.models import HeadingAnalysis

        analysis = HeadingAnalysis(
            text="SREの知識地図",
            level=1,
            count=50,
            levels=(1,),
            is_running_head=True,
        )

        assert analysis.text == "SREの知識地図"
        assert analysis.level == 1
        assert analysis.count == 50
        assert analysis.levels == (1,)
        assert analysis.is_running_head is True

    def test_heading_analysis_multiple_levels(self) -> None:
        """同一テキストが複数レベルで出現するケース"""
        from src.book_converter.models import HeadingAnalysis

        analysis = HeadingAnalysis(
            text="SREの知識地図",
            level=1,
            count=55,
            levels=(1, 2, 3),
            is_running_head=True,
        )

        assert analysis.levels == (1, 2, 3)
        assert len(analysis.levels) == 3

    def test_heading_analysis_is_immutable(self) -> None:
        """HeadingAnalysis は frozen dataclass（イミュータブル）"""
        from src.book_converter.models import HeadingAnalysis

        analysis = HeadingAnalysis(
            text="テスト",
            level=1,
            count=10,
            levels=(1,),
            is_running_head=False,
        )

        # frozen=True なので属性変更で FrozenInstanceError が発生する
        with pytest.raises(Exception):  # FrozenInstanceError
            analysis.text = "changed"

    def test_heading_analysis_text_non_empty(self) -> None:
        """text は非空文字列"""
        from src.book_converter.models import HeadingAnalysis

        analysis = HeadingAnalysis(
            text="章タイトル",
            level=1,
            count=1,
            levels=(1,),
            is_running_head=False,
        )
        assert analysis.text == "章タイトル"
        assert len(analysis.text) > 0

    def test_heading_analysis_level_range(self) -> None:
        """level は 1-3 の整数"""
        from src.book_converter.models import HeadingAnalysis

        for level in [1, 2, 3]:
            analysis = HeadingAnalysis(
                text="テスト",
                level=level,
                count=1,
                levels=(level,),
                is_running_head=False,
            )
            assert analysis.level == level

    def test_heading_analysis_count_positive(self) -> None:
        """count は 1 以上の整数"""
        from src.book_converter.models import HeadingAnalysis

        analysis = HeadingAnalysis(
            text="テスト",
            level=1,
            count=1,
            levels=(1,),
            is_running_head=False,
        )
        assert analysis.count >= 1

    def test_heading_analysis_levels_non_empty_tuple(self) -> None:
        """levels は空でないタプル"""
        from src.book_converter.models import HeadingAnalysis

        analysis = HeadingAnalysis(
            text="テスト",
            level=2,
            count=5,
            levels=(1, 2),
            is_running_head=False,
        )
        assert isinstance(analysis.levels, tuple)
        assert len(analysis.levels) > 0

    def test_heading_analysis_running_head_detection(self) -> None:
        """is_running_head で柱判定結果を保持"""
        from src.book_converter.models import HeadingAnalysis

        # 柱として検出されたケース
        running_head = HeadingAnalysis(
            text="SREの知識地図",
            level=1,
            count=50,
            levels=(1,),
            is_running_head=True,
        )
        assert running_head.is_running_head is True

        # 通常の見出し
        normal_heading = HeadingAnalysis(
            text="まとめ",
            level=2,
            count=3,
            levels=(2,),
            is_running_head=False,
        )
        assert normal_heading.is_running_head is False

    def test_heading_analysis_unicode_text(self) -> None:
        """Unicode テキストを正しく保持"""
        from src.book_converter.models import HeadingAnalysis

        analysis = HeadingAnalysis(
            text="日本語見出し「テスト」",
            level=1,
            count=1,
            levels=(1,),
            is_running_head=False,
        )
        assert analysis.text == "日本語見出し「テスト」"


# =============================================================================
# Phase 2 (009-converter-redesign): T008 TocEntry.level int化テスト
# =============================================================================


class TestTocEntryLevelInt:
    """T008: TocEntry.level int化テスト

    User Story 1 - TOC階層構造の正確な反映
    TocEntry.level は int型（1-5）である必要がある
    """

    def test_toc_entry_level_type_annotation_is_int(self) -> None:
        """TocEntry.level の型アノテーションが int である"""
        from src.book_converter.models import TocEntry

        # dataclass の型アノテーションを検証
        field_type = TocEntry.__dataclass_fields__["level"].type
        # 型アノテーションが int であること
        assert field_type == int or field_type == "int", \
            f"TocEntry.level type should be int, but got {field_type}"

    def test_toc_entry_level_int_basic(self) -> None:
        """TocEntry.level が int 型で作成できる"""
        from src.book_converter.models import TocEntry

        # level=1 で作成
        entry = TocEntry(
            text="Chapter 1 タイトル",
            level=1,
            number="1",
            page="15",
        )

        assert entry.level == 1
        assert isinstance(entry.level, int)

    def test_toc_entry_level_int_level_2(self) -> None:
        """TocEntry.level=2 が作成できる"""
        from src.book_converter.models import TocEntry

        entry = TocEntry(
            text="Episode 01 タイトル",
            level=2,
            number="1",
            page="20",
        )

        assert entry.level == 2
        assert isinstance(entry.level, int)

    def test_toc_entry_level_int_level_3(self) -> None:
        """TocEntry.level=3 が作成できる"""
        from src.book_converter.models import TocEntry

        entry = TocEntry(
            text="Subsection タイトル",
            level=3,
            number="1.1",
            page="25",
        )

        assert entry.level == 3
        assert isinstance(entry.level, int)

    def test_toc_entry_level_int_level_4(self) -> None:
        """TocEntry.level=4 が作成できる"""
        from src.book_converter.models import TocEntry

        entry = TocEntry(
            text="深い階層の見出し",
            level=4,
            number="1.1.1",
            page="30",
        )

        assert entry.level == 4
        assert isinstance(entry.level, int)

    def test_toc_entry_level_int_level_5(self) -> None:
        """TocEntry.level=5 が作成できる"""
        from src.book_converter.models import TocEntry

        entry = TocEntry(
            text="最深階層の見出し",
            level=5,
            number="1.1.1.1",
            page="35",
        )

        assert entry.level == 5
        assert isinstance(entry.level, int)

    def test_toc_entry_level_int_all_levels(self) -> None:
        """TocEntry で全レベル（1-5）が int として作成できる"""
        from src.book_converter.models import TocEntry

        for level in range(1, 6):
            entry = TocEntry(
                text=f"Level {level} 見出し",
                level=level,
                number=str(level),
                page=str(level * 10),
            )
            assert entry.level == level
            assert isinstance(entry.level, int)

    def test_toc_entry_level_int_unicode_text(self) -> None:
        """Unicode テキストと int level の組み合わせ"""
        from src.book_converter.models import TocEntry

        entry = TocEntry(
            text="日本語「テスト」見出し",
            level=1,
            number="1",
            page="10",
        )

        assert entry.level == 1
        assert entry.text == "日本語「テスト」見出し"

    def test_toc_entry_level_not_string(self) -> None:
        """TocEntry.level は文字列ではない"""
        from src.book_converter.models import TocEntry

        entry = TocEntry(
            text="テスト",
            level=1,
            number="1",
            page="10",
        )

        # level は "chapter" などの文字列ではなく int
        assert entry.level != "chapter"
        assert entry.level != "1"
        assert isinstance(entry.level, int)
