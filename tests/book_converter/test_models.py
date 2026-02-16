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


# =============================================================================
# Phase 3 (009-converter-redesign): T024 StructureContainer モデルテスト
# =============================================================================


class TestStructureContainer:
    """T024: StructureContainer dataclass テスト

    User Story 2 - chapter/heading タグの役割明確化
    StructureContainer は構造コンテナ（chapter, section, subsection）を表す
    """

    def test_structure_container_exists(self) -> None:
        """StructureContainer dataclass が存在する"""
        from src.book_converter.models import StructureContainer

        # dataclass としてインポート可能
        assert StructureContainer is not None

    def test_structure_container_has_container_type(self) -> None:
        """StructureContainer は container_type 属性を持つ"""
        from src.book_converter.models import StructureContainer

        container = StructureContainer(
            container_type="chapter",
            level=1,
            number="1",
            title="Chapter Title",
            children=(),
        )

        assert container.container_type == "chapter"

    def test_structure_container_has_level(self) -> None:
        """StructureContainer は level 属性（1-5）を持つ"""
        from src.book_converter.models import StructureContainer

        container = StructureContainer(
            container_type="section",
            level=2,
            number="1",
            title="Section Title",
            children=(),
        )

        assert container.level == 2
        assert isinstance(container.level, int)

    def test_structure_container_has_number(self) -> None:
        """StructureContainer は number 属性を持つ"""
        from src.book_converter.models import StructureContainer

        container = StructureContainer(
            container_type="chapter",
            level=1,
            number="1",
            title="Chapter Title",
            children=(),
        )

        assert container.number == "1"

    def test_structure_container_has_title(self) -> None:
        """StructureContainer は title 属性を持つ"""
        from src.book_converter.models import StructureContainer

        container = StructureContainer(
            container_type="chapter",
            level=1,
            number="1",
            title="Chapter Title",
            children=(),
        )

        assert container.title == "Chapter Title"

    def test_structure_container_has_children(self) -> None:
        """StructureContainer は children 属性を持つ"""
        from src.book_converter.models import StructureContainer

        container = StructureContainer(
            container_type="chapter",
            level=1,
            number="1",
            title="Chapter Title",
            children=(),
        )

        assert container.children == ()

    def test_structure_container_chapter_type(self) -> None:
        """container_type="chapter" のコンテナを作成できる"""
        from src.book_converter.models import StructureContainer

        container = StructureContainer(
            container_type="chapter",
            level=1,
            number="1",
            title="Chapter 1 Introduction",
            children=(),
        )

        assert container.container_type == "chapter"
        assert container.level == 1

    def test_structure_container_section_type(self) -> None:
        """container_type="section" のコンテナを作成できる"""
        from src.book_converter.models import StructureContainer

        container = StructureContainer(
            container_type="section",
            level=2,
            number="1",
            title="Episode 01 Title",
            children=(),
        )

        assert container.container_type == "section"
        assert container.level == 2

    def test_structure_container_subsection_type(self) -> None:
        """container_type="subsection" のコンテナを作成できる"""
        from src.book_converter.models import StructureContainer

        container = StructureContainer(
            container_type="subsection",
            level=3,
            number="1.1",
            title="Subsection Title",
            children=(),
        )

        assert container.container_type == "subsection"
        assert container.level == 3

    def test_structure_container_level_4(self) -> None:
        """level=4 の subsection コンテナを作成できる"""
        from src.book_converter.models import StructureContainer

        container = StructureContainer(
            container_type="subsection",
            level=4,
            number="1.1.1",
            title="Deep Subsection",
            children=(),
        )

        assert container.level == 4
        assert container.container_type == "subsection"

    def test_structure_container_level_5(self) -> None:
        """level=5 の subsection コンテナを作成できる"""
        from src.book_converter.models import StructureContainer

        container = StructureContainer(
            container_type="subsection",
            level=5,
            number="1.1.1.1",
            title="Deepest Subsection",
            children=(),
        )

        assert container.level == 5
        assert container.container_type == "subsection"

    def test_structure_container_is_immutable(self) -> None:
        """StructureContainer は frozen dataclass（イミュータブル）"""
        from src.book_converter.models import StructureContainer

        container = StructureContainer(
            container_type="chapter",
            level=1,
            number="1",
            title="Test",
            children=(),
        )

        # frozen=True なので属性変更で FrozenInstanceError が発生する
        with pytest.raises(Exception):  # FrozenInstanceError
            container.title = "changed"

    def test_structure_container_children_with_content_element(self) -> None:
        """children に ContentElement（Paragraph等）を含めることができる"""
        from src.book_converter.models import StructureContainer, Paragraph

        paragraph = Paragraph(text="This is a paragraph.")

        container = StructureContainer(
            container_type="chapter",
            level=1,
            number="1",
            title="Chapter with content",
            children=(paragraph,),
        )

        assert len(container.children) == 1
        assert isinstance(container.children[0], Paragraph)

    def test_structure_container_children_with_nested_structure(self) -> None:
        """children に StructureContainer（入れ子構造）を含めることができる"""
        from src.book_converter.models import StructureContainer

        section = StructureContainer(
            container_type="section",
            level=2,
            number="1",
            title="Section Title",
            children=(),
        )

        chapter = StructureContainer(
            container_type="chapter",
            level=1,
            number="1",
            title="Chapter Title",
            children=(section,),
        )

        assert len(chapter.children) == 1
        assert isinstance(chapter.children[0], StructureContainer)
        assert chapter.children[0].container_type == "section"

    def test_structure_container_children_mixed(self) -> None:
        """children に ContentElement と StructureContainer を混在させることができる"""
        from src.book_converter.models import StructureContainer, Heading, Paragraph

        heading = Heading(level=1, text="Chapter 1 Title")
        paragraph = Paragraph(text="Introduction text.")
        section = StructureContainer(
            container_type="section",
            level=2,
            number="1",
            title="Section Title",
            children=(),
        )

        chapter = StructureContainer(
            container_type="chapter",
            level=1,
            number="1",
            title="Chapter Title",
            children=(heading, paragraph, section),
        )

        assert len(chapter.children) == 3
        assert isinstance(chapter.children[0], Heading)
        assert isinstance(chapter.children[1], Paragraph)
        assert isinstance(chapter.children[2], StructureContainer)

    def test_structure_container_unicode_title(self) -> None:
        """title にUnicode文字を使用できる"""
        from src.book_converter.models import StructureContainer

        container = StructureContainer(
            container_type="chapter",
            level=1,
            number="1",
            title="日本語タイトル「テスト」",
            children=(),
        )

        assert container.title == "日本語タイトル「テスト」"

    def test_structure_container_empty_number(self) -> None:
        """number は空文字列も許容する"""
        from src.book_converter.models import StructureContainer

        container = StructureContainer(
            container_type="chapter",
            level=1,
            number="",
            title="Preface",
            children=(),
        )

        assert container.number == ""

    def test_structure_container_empty_title(self) -> None:
        """title は空文字列も許容する"""
        from src.book_converter.models import StructureContainer

        container = StructureContainer(
            container_type="chapter",
            level=1,
            number="1",
            title="",
            children=(),
        )

        assert container.title == ""

    def test_structure_container_all_levels_1_to_5(self) -> None:
        """全レベル（1-5）の StructureContainer を作成できる"""
        from src.book_converter.models import StructureContainer

        for level in range(1, 6):
            container_type = "chapter" if level == 1 else "section" if level == 2 else "subsection"
            container = StructureContainer(
                container_type=container_type,
                level=level,
                number=str(level),
                title=f"Level {level} Title",
                children=(),
            )

            assert container.level == level
            assert isinstance(container.level, int)


# =============================================================================
# Phase 5 (009-converter-redesign): T057 List.list_type 属性テスト
# =============================================================================


class TestListTypeAttribute:
    """T057: List.list_type 属性テスト

    User Story 4 - list/figure要素の出力
    List は list_type 属性（"unordered" または "ordered"）を持つ
    """

    def test_list_has_list_type_field(self) -> None:
        """List dataclass に list_type フィールドが存在する"""
        from src.book_converter.models import List

        # list_type フィールドが存在することを確認
        assert "list_type" in List.__dataclass_fields__, \
            "List should have list_type field"

    def test_list_type_unordered(self) -> None:
        """List(list_type="unordered") が作成できる"""
        from src.book_converter.models import List

        lst = List(
            items=("項目1", "項目2", "項目3"),
            list_type="unordered",
        )

        assert lst.list_type == "unordered"
        assert lst.items == ("項目1", "項目2", "項目3")

    def test_list_type_ordered(self) -> None:
        """List(list_type="ordered") が作成できる"""
        from src.book_converter.models import List

        lst = List(
            items=("手順1", "手順2", "手順3"),
            list_type="ordered",
        )

        assert lst.list_type == "ordered"
        assert lst.items == ("手順1", "手順2", "手順3")

    def test_list_type_default_value(self) -> None:
        """list_type のデフォルト値は "unordered" """
        from src.book_converter.models import List

        # list_type を指定せずに作成
        lst = List(items=("item1", "item2"))

        # デフォルト値は unordered
        assert lst.list_type == "unordered"

    def test_list_type_field_type_annotation(self) -> None:
        """list_type の型アノテーションが str である"""
        from src.book_converter.models import List

        field_type = List.__dataclass_fields__["list_type"].type
        assert field_type == str or field_type == "str", \
            f"List.list_type type should be str, but got {field_type}"

    def test_list_is_immutable(self) -> None:
        """List は frozen dataclass（イミュータブル）"""
        from src.book_converter.models import List

        lst = List(items=("item",), list_type="unordered")

        with pytest.raises(Exception):  # FrozenInstanceError
            lst.list_type = "ordered"

    def test_list_type_with_unicode_items(self) -> None:
        """Unicode 項目と list_type の組み合わせ"""
        from src.book_converter.models import List

        lst = List(
            items=("日本語項目「テスト」", "特殊文字&記号<>"),
            list_type="ordered",
        )

        assert lst.list_type == "ordered"
        assert lst.items[0] == "日本語項目「テスト」"

    def test_list_type_empty_items(self) -> None:
        """空のアイテムリストでも list_type を指定できる"""
        from src.book_converter.models import List

        lst = List(items=(), list_type="unordered")

        assert lst.list_type == "unordered"
        assert lst.items == ()


# =============================================================================
# Phase 5 (009-converter-redesign): T059 Figure.path, marker 属性テスト
# =============================================================================


class TestFigurePathMarker:
    """T059: Figure.path, marker 属性テスト

    User Story 4 - list/figure要素の出力
    Figure は path（必須）と marker（オプション）属性を持つ
    """

    def test_figure_has_path_field(self) -> None:
        """Figure dataclass に path フィールドが存在する"""
        from src.book_converter.models import Figure

        assert "path" in Figure.__dataclass_fields__, \
            "Figure should have path field"

    def test_figure_has_marker_field(self) -> None:
        """Figure dataclass に marker フィールドが存在する"""
        from src.book_converter.models import Figure

        assert "marker" in Figure.__dataclass_fields__, \
            "Figure should have marker field"

    def test_figure_path_required(self) -> None:
        """Figure の path は必須フィールド"""
        from src.book_converter.models import Figure

        fig = Figure(path="figures/fig001.png")

        assert fig.path == "figures/fig001.png"

    def test_figure_path_and_marker(self) -> None:
        """Figure(path="...", marker="図1") が作成できる"""
        from src.book_converter.models import Figure

        fig = Figure(
            path="figures/fig001.png",
            marker="図1",
        )

        assert fig.path == "figures/fig001.png"
        assert fig.marker == "図1"

    def test_figure_marker_optional(self) -> None:
        """marker はオプションフィールド（デフォルト空文字列）"""
        from src.book_converter.models import Figure

        fig = Figure(path="figures/img.png")

        # marker を指定しない場合は空文字列
        assert fig.marker == ""

    def test_figure_is_immutable(self) -> None:
        """Figure は frozen dataclass（イミュータブル）"""
        from src.book_converter.models import Figure

        fig = Figure(path="figures/fig001.png", marker="図1")

        with pytest.raises(Exception):  # FrozenInstanceError
            fig.path = "changed.png"

    def test_figure_marker_with_various_formats(self) -> None:
        """様々なマーカー形式をサポート"""
        from src.book_converter.models import Figure

        test_cases = [
            ("図1", "figures/fig001.png"),
            ("図 1", "figures/fig002.png"),
            ("写真1", "figures/photo001.png"),
            ("表1", "figures/table001.png"),
            ("イラスト", "figures/illust001.png"),
        ]

        for marker, path in test_cases:
            fig = Figure(path=path, marker=marker)
            assert fig.marker == marker, f"Failed for marker: {marker}"
            assert fig.path == path

    def test_figure_path_various_extensions(self) -> None:
        """様々なファイル拡張子をサポート"""
        from src.book_converter.models import Figure

        extensions = ["png", "jpg", "jpeg", "gif", "svg", "webp"]

        for ext in extensions:
            fig = Figure(path=f"figures/image.{ext}")
            assert fig.path == f"figures/image.{ext}"

    def test_figure_unicode_marker(self) -> None:
        """Unicode マーカーをサポート"""
        from src.book_converter.models import Figure

        fig = Figure(
            path="figures/fig001.png",
            marker="図1「サンプル画像」",
        )

        assert fig.marker == "図1「サンプル画像」"
