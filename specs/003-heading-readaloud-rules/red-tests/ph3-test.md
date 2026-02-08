# Phase 3 テスト実装 (RED): User Story 2 - 装飾・区切り記号の除外

**日付**: 2026-02-08
**フェーズ**: Phase 3 - User Story 2（装飾・区切り記号の除外）
**ステータス**: RED（テスト FAIL 確認済み）

## サマリー

| 項目 | 値 |
|------|-----|
| フェーズ | Phase 3 (User Story 2) |
| FAILテスト数 | 16 |
| PASSテスト数 | 348（既存テスト全て） |
| テストファイル | `tests/book_converter/test_analyzer.py` |

## FAILテスト一覧

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|----------|
| test_analyzer.py | `TestDecorationPatternMatching::test_match_diamond_pattern` | `◆◆◆` が decoration パターンにマッチ |
| test_analyzer.py | `TestDecorationPatternMatching::test_match_white_diamond_pattern` | `◇◇◇` が decoration パターンにマッチ |
| test_analyzer.py | `TestDecorationPatternMatching::test_match_black_square_pattern` | `■■■` が decoration パターンにマッチ |
| test_analyzer.py | `TestDecorationPatternMatching::test_match_white_square_pattern` | `□□□` が decoration パターンにマッチ |
| test_analyzer.py | `TestDecorationPatternMatching::test_match_black_circle_pattern` | `●●●` が decoration パターンにマッチ |
| test_analyzer.py | `TestDecorationPatternMatching::test_match_white_circle_pattern` | `○○○` が decoration パターンにマッチ |
| test_analyzer.py | `TestDecorationPatternMatching::test_match_black_triangle_pattern` | `▲▲▲` が decoration パターンにマッチ |
| test_analyzer.py | `TestDecorationPatternMatching::test_match_white_triangle_pattern` | `△△△` が decoration パターンにマッチ |
| test_analyzer.py | `TestDecorationPatternMatching::test_match_mixed_decoration_pattern` | `◆◇◆` が decoration パターンにマッチ |
| test_analyzer.py | `TestDecorationPatternMatching::test_match_single_decoration_pattern` | `◆` が decoration パターンにマッチ |
| test_analyzer.py | `TestSectionLabelPatternMatching::test_match_section_label_simple` | `Section 1.1` が section-label パターンにマッチ |
| test_analyzer.py | `TestSectionLabelPatternMatching::test_match_section_label_double_digit` | `Section 10.15` が section-label パターンにマッチ |
| test_analyzer.py | `TestSectionLabelPatternMatching::test_match_section_label_with_extra_spaces` | `Section  1.2` が section-label パターンにマッチ |
| test_analyzer.py | `TestNormalHeadingNotExcluded::test_decoration_heading_should_be_excluded` | 装飾記号のみの見出しは readAloud=False |
| test_analyzer.py | `TestNormalHeadingNotExcluded::test_section_label_heading_should_be_excluded` | セクションラベルは readAloud=False |
| test_analyzer.py | `TestNormalHeadingNotExcluded::test_mixed_headings_correct_exclusion` | 混合見出しで正しい除外判定 |

## 実装ヒント

### decoration パターン

`src/book_converter/config.py` に以下のパターンを追加:

```python
ExclusionPattern(
    id="decoration",
    priority=50,
    pattern=r"^[◆◇■□●○▲△]+$",
    pattern_type="static",
    description="装飾記号（連続記号のみ）",
)
```

### section-label パターン

`src/book_converter/config.py` に以下のパターンを追加:

```python
ExclusionPattern(
    id="section-label",
    priority=50,
    pattern=r"^Section\s+\d+\.\d+$",
    pattern_type="static",
    description="章節ラベル（Section X.X形式）",
)
```

## FAIL出力例

```
============================= test session starts ==============================
collected 364 items

...

FAILED tests/book_converter/test_analyzer.py::TestDecorationPatternMatching::test_match_diamond_pattern
FAILED tests/book_converter/test_analyzer.py::TestDecorationPatternMatching::test_match_white_diamond_pattern
FAILED tests/book_converter/test_analyzer.py::TestDecorationPatternMatching::test_match_black_square_pattern
FAILED tests/book_converter/test_analyzer.py::TestDecorationPatternMatching::test_match_white_square_pattern
FAILED tests/book_converter/test_analyzer.py::TestDecorationPatternMatching::test_match_black_circle_pattern
FAILED tests/book_converter/test_analyzer.py::TestDecorationPatternMatching::test_match_white_circle_pattern
FAILED tests/book_converter/test_analyzer.py::TestDecorationPatternMatching::test_match_black_triangle_pattern
FAILED tests/book_converter/test_analyzer.py::TestDecorationPatternMatching::test_match_white_triangle_pattern
FAILED tests/book_converter/test_analyzer.py::TestDecorationPatternMatching::test_match_mixed_decoration_pattern
FAILED tests/book_converter/test_analyzer.py::TestDecorationPatternMatching::test_match_single_decoration_pattern
FAILED tests/book_converter/test_analyzer.py::TestSectionLabelPatternMatching::test_match_section_label_simple
FAILED tests/book_converter/test_analyzer.py::TestSectionLabelPatternMatching::test_match_section_label_double_digit
FAILED tests/book_converter/test_analyzer.py::TestSectionLabelPatternMatching::test_match_section_label_with_extra_spaces
FAILED tests/book_converter/test_analyzer.py::TestNormalHeadingNotExcluded::test_decoration_heading_should_be_excluded
FAILED tests/book_converter/test_analyzer.py::TestNormalHeadingNotExcluded::test_section_label_heading_should_be_excluded
FAILED tests/book_converter/test_analyzer.py::TestNormalHeadingNotExcluded::test_mixed_headings_correct_exclusion
======================== 16 failed, 348 passed in 0.47s ========================
```

## 失敗理由

`src/book_converter/config.py` の `DEFAULT_EXCLUSION_PATTERNS` に以下のパターンが未定義:

1. **decoration**: `^[◆◇■□●○▲△]+$` - 装飾記号のみで構成される文字列
2. **section-label**: `^Section\s+\d+\.\d+$` - Section X.X 形式のラベル

現在の `config.py` には `running-head` と `page-number` のみが定義されているため、
上記パターンにマッチするテストは全て FAIL となる。

## 次のステップ

Phase 3 Implementation (GREEN) で以下を実施:
1. `src/book_converter/config.py` に decoration パターンを追加 (T040)
2. `src/book_converter/config.py` に section-label パターンを追加 (T041)
3. `make test` PASS を確認 (T043)
