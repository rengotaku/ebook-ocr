# Phase 2 テスト実装 (RED) 結果

**日付**: 2026-02-08
**フェーズ**: Phase 2 - User Story 1（繰り返し柱の自動除外）
**ステータス**: RED (FAIL)

## サマリー

| 項目 | 値 |
|------|-----|
| フェーズ | Phase 2 (US1) |
| 作成テスト数 | 47 |
| FAIL テスト数 | 47 |
| PASS テスト数（既存） | 293 |
| RED 確認 | 完了 |

## 作成テストファイル

| ファイル | 説明 |
|----------|------|
| `tests/book_converter/test_models.py` | ExclusionPattern, HeadingAnalysis モデルテスト (新規作成) |
| `tests/book_converter/test_analyzer.py` | 柱検出、パターンマッチング、level再配置テスト (拡張) |
| `tests/book_converter/test_transformer.py` | readAloud属性付与テスト (拡張) |

## FAIL テスト一覧

### T010: ExclusionPattern モデルテスト (`test_models.py`)

| テストメソッド | 期待動作 |
|---------------|----------|
| `test_exclusion_pattern_fields_exist` | ExclusionPattern dataclass のフィールド存在確認 |
| `test_exclusion_pattern_static_type` | static タイプのパターン定義確認 |
| `test_exclusion_pattern_is_immutable` | frozen dataclass でイミュータブル確認 |
| `test_exclusion_pattern_id_validation` | id の形式バリデーション |
| `test_exclusion_pattern_priority_range` | priority が 1-100 の範囲 |
| `test_exclusion_pattern_static_requires_pattern` | static タイプで pattern 必須 |
| `test_exclusion_pattern_dynamic_pattern_is_none` | dynamic タイプで pattern が None |
| `test_exclusion_pattern_valid_regex` | pattern が有効な正規表現 |

### T011: HeadingAnalysis モデルテスト (`test_models.py`)

| テストメソッド | 期待動作 |
|---------------|----------|
| `test_heading_analysis_fields_exist` | HeadingAnalysis dataclass のフィールド存在確認 |
| `test_heading_analysis_multiple_levels` | 複数 level での出現をトラッキング |
| `test_heading_analysis_is_immutable` | frozen dataclass でイミュータブル確認 |
| `test_heading_analysis_text_non_empty` | text が非空文字列 |
| `test_heading_analysis_level_range` | level が 1-3 の範囲 |
| `test_heading_analysis_count_positive` | count が 1 以上 |
| `test_heading_analysis_levels_non_empty_tuple` | levels が空でないタプル |
| `test_heading_analysis_running_head_detection` | is_running_head で柱判定結果保持 |
| `test_heading_analysis_unicode_text` | Unicode テキストの保持 |

### T012: 柱検出テスト (`test_analyzer.py`)

| テストメソッド | 期待動作 |
|---------------|----------|
| `test_analyze_headings_returns_analysis_list` | analyze_headings が HeadingAnalysis リスト返却 |
| `test_analyze_headings_counts_occurrences` | 各 heading テキストの出現回数カウント |
| `test_analyze_headings_tracks_levels` | 同一テキストの出現 level トラッキング |
| `test_analyze_headings_empty_list` | 空リスト入力で空リスト返却 |
| `test_detect_running_head_above_threshold` | 出現率 50% 以上で柱検出 |
| `test_detect_running_head_below_threshold` | 出現率 50% 未満は柱非検出 |
| `test_detect_running_head_level_1_only` | level=1 のみ柱候補 |
| `test_detect_running_head_most_frequent` | 最頻出 level=1 heading を柱検出 |

### T013: ページ番号パターンテスト (`test_analyzer.py`)

| テストメソッド | 期待動作 |
|---------------|----------|
| `test_match_page_number_pattern` | `X.X.X タイトル — N / M` 形式マッチング |
| `test_match_page_number_em_dash` | 全角ダッシュ（—）のマッチング |
| `test_match_page_number_horizontal_bar` | 横棒（―）のマッチング |
| `test_no_match_normal_heading` | 通常見出しはマッチしない |
| `test_no_match_empty_string` | 空文字列はマッチしない |

### T014: level再配置テスト (`test_analyzer.py`)

| テストメソッド | 期待動作 |
|---------------|----------|
| `test_reassign_level_2_to_1` | 柱テキスト level 2 → level 1 再配置 |
| `test_reassign_level_3_to_1` | 柱テキスト level 3 → level 1 再配置 |
| `test_no_reassign_non_running_head` | 柱以外は再配置しない |
| `test_no_reassign_already_level_1` | level 1 は再配置不要 |
| `test_reassign_preserves_read_aloud` | 再配置時に read_aloud 保持 |
| `test_reassign_returns_new_heading` | 新しい Heading オブジェクト返却（イミュータブル） |

### T015: readAloud属性付与テスト (`test_transformer.py`)

| テストメソッド | 期待動作 |
|---------------|----------|
| `test_heading_read_aloud_false_attribute` | `Heading(read_aloud=False)` で `readAloud="false"` 出力 |
| `test_heading_read_aloud_true_default` | `Heading(read_aloud=True)` で属性省略可 |
| `test_heading_read_aloud_false_xml_serialization` | `readAloud="false"` の XML シリアライズ |
| `test_heading_read_aloud_preserves_other_attributes` | readAloud と他属性を両方出力 |
| `test_heading_read_aloud_false_in_content` | Content 内 Heading で readAloud 反映 |
| `test_heading_read_aloud_unicode_text` | Unicode テキストで readAloud=False 出力 |
| `test_multiple_headings_mixed_read_aloud` | 複数 heading で readAloud 混在 |

### T016: 統合テスト (`test_analyzer.py`)

| テストメソッド | 期待動作 |
|---------------|----------|
| `test_full_flow_running_head_detection` | 柱検出 → readAloud=False 付与フロー |
| `test_full_flow_page_number_exclusion` | ページ番号表記の readAloud=False 付与 |
| `test_full_flow_level_reassignment` | level 再配置を含むフロー |
| `test_full_flow_empty_headings` | 空 heading リスト処理 |
| `test_full_flow_unicode_headings` | Unicode heading 処理 |

## 実装ヒント

### models.py への追加

```python
@dataclass(frozen=True)
class ExclusionPattern:
    """除外パターン定義"""
    id: str
    priority: int
    pattern: str | None
    pattern_type: str  # "static" | "dynamic"
    description: str

@dataclass(frozen=True)
class HeadingAnalysis:
    """heading出現頻度分析結果"""
    text: str
    level: int
    count: int
    levels: tuple[int, ...]
    is_running_head: bool
```

### analyzer.py への追加

```python
def analyze_headings(headings: list[Heading]) -> list[HeadingAnalysis]:
    """heading頻度分析"""
    ...

def detect_running_head(
    analyses: list[HeadingAnalysis],
    total_pages: int
) -> list[HeadingAnalysis]:
    """柱検出（閾値50%）"""
    ...

def match_exclusion_pattern(text: str) -> ExclusionPattern | None:
    """パターンマッチング"""
    ...

def reassign_heading_level(
    heading: Heading,
    running_head_texts: set[str]
) -> Heading:
    """level再配置"""
    ...

def apply_read_aloud_rules(
    headings: list[Heading],
    analyses: list[HeadingAnalysis]
) -> list[Heading]:
    """readAloud属性付与"""
    ...
```

### transformer.py への変更

```python
def transform_heading(heading: Heading) -> Element:
    elem = Element("heading")
    elem.set("level", str(heading.level))
    elem.text = heading.text

    # readAloud=False の場合は属性を出力
    if not heading.read_aloud:
        elem.set("readAloud", "false")

    return elem
```

## FAIL 出力例

```
FAILED tests/book_converter/test_models.py::TestExclusionPattern::test_exclusion_pattern_fields_exist
    ImportError: cannot import name 'ExclusionPattern' from 'src.book_converter.models'

FAILED tests/book_converter/test_analyzer.py::TestAnalyzeHeadings::test_analyze_headings_returns_analysis_list
    ImportError: cannot import name 'analyze_headings' from 'src.book_converter.analyzer'

FAILED tests/book_converter/test_transformer.py::TestHeadingReadAloudAttribute::test_heading_read_aloud_false_attribute
    AssertionError: assert None == 'false'
```

## 次のステップ

1. phase-executor が `specs/003-heading-readaloud-rules/red-tests/ph2-test.md` を読む
2. Implementation (GREEN) フェーズでテストをパスする実装を行う
3. `make test` で全テスト通過を確認
