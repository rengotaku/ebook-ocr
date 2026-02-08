# Phase 4 REDテスト: User Story 3 - 参照・メタ情報の除外

**日付**: 2026-02-08
**フェーズ**: Phase 4 - User Story 3 (RED)
**ステータス**: RED (9テストFAIL)

## サマリー

| 項目 | 値 |
|------|-----|
| フェーズ | Phase 4: User Story 3 - 参照・メタ情報の除外 |
| FAILテスト数 | 9 |
| PASSテスト数 (既存) | 371 |
| テストファイル | tests/book_converter/test_analyzer.py |

## FAILテスト一覧

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|----------|
| test_analyzer.py | TestWebsiteReferencePatternMatching::test_match_website_reference_exact | 「Webサイト」完全一致でreferenceパターンにマッチ |
| test_analyzer.py | TestWebsiteReferencePatternMatching::test_website_reference_read_aloud_false | 「Webサイト」見出しがreadAloud=Falseとなる |
| test_analyzer.py | TestFootnotePatternMatching::test_match_footnote_simple | 「注3.1」がfootnoteパターンにマッチ |
| test_analyzer.py | TestFootnotePatternMatching::test_match_footnote_double_digit | 「注10.2」がfootnoteパターンにマッチ |
| test_analyzer.py | TestFootnotePatternMatching::test_match_footnote_large_numbers | 「注123.45」がfootnoteパターンにマッチ |
| test_analyzer.py | TestFootnotePatternMatching::test_match_footnote_with_trailing_text | 「注3.1 補足説明」がfootnoteパターンにマッチ |
| test_analyzer.py | TestFootnotePatternMatching::test_footnote_read_aloud_false | 「注3.1」見出しがreadAloud=Falseとなる |
| test_analyzer.py | TestUserStory3Integration::test_mixed_headings_with_reference_and_footnote | 混合見出しで参照・脚注が正しく除外される |
| test_analyzer.py | TestUserStory3Integration::test_all_exclusion_patterns_together | 全除外パターン(US1-3)が正しく適用される |

## 実装ヒント

### config.py に追加するパターン

```python
# 低優先度: 参照表記（完全一致）
ExclusionPattern(
    id="reference",
    priority=30,
    pattern=r"^Webサイト$",
    pattern_type="static",
    description="Webサイト参照リンク表記",
),
# 低優先度: 脚注番号（先頭マッチ）
ExclusionPattern(
    id="footnote",
    priority=30,
    pattern=r"^注\d+\.\d+",
    pattern_type="static",
    description="脚注番号（注X.X形式）",
),
```

### パターン仕様

1. **reference パターン**: `^Webサイト$`
   - 完全一致のみ（前後に文字があるとマッチしない）
   - 大文字「Web」のみ対応（小文字「web」はマッチしない）

2. **footnote パターン**: `^注\d+\.\d+`
   - 先頭マッチ（後続テキストがあってもマッチ）
   - 「注X.X」形式（X=1桁以上の数字）
   - 「注3.1」「注10.2」「注123.45」などにマッチ
   - 「注3.1 補足説明」もマッチ（先頭パターン）

## FAIL出力例

```
============================= test session starts ==============================
platform linux -- Python 3.13.11, pytest-9.0.2, pluggy-1.6.0
collected 380 items

...
tests/book_converter/test_analyzer.py::TestWebsiteReferencePatternMatching::test_match_website_reference_exact FAILED
tests/book_converter/test_analyzer.py::TestWebsiteReferencePatternMatching::test_website_reference_read_aloud_false FAILED
tests/book_converter/test_analyzer.py::TestFootnotePatternMatching::test_match_footnote_simple FAILED
tests/book_converter/test_analyzer.py::TestFootnotePatternMatching::test_match_footnote_double_digit FAILED
tests/book_converter/test_analyzer.py::TestFootnotePatternMatching::test_match_footnote_large_numbers FAILED
tests/book_converter/test_analyzer.py::TestFootnotePatternMatching::test_match_footnote_with_trailing_text FAILED
tests/book_converter/test_analyzer.py::TestFootnotePatternMatching::test_footnote_read_aloud_false FAILED
tests/book_converter/test_analyzer.py::TestUserStory3Integration::test_mixed_headings_with_reference_and_footnote FAILED
tests/book_converter/test_analyzer.py::TestUserStory3Integration::test_all_exclusion_patterns_together FAILED
...

=================================== FAILURES ===================================
____ TestWebsiteReferencePatternMatching.test_match_website_reference_exact ____
tests/book_converter/test_analyzer.py:768: in test_match_website_reference_exact
    assert result is not None
E   AssertionError: assert None is not None

_______ TestFootnotePatternMatching.test_match_footnote_simple ________
tests/book_converter/test_analyzer.py:807: in test_match_footnote_simple
    assert result is not None
E   AssertionError: assert None is not None

=========================== short test summary info ============================
FAILED tests/book_converter/test_analyzer.py::TestWebsiteReferencePatternMatching::test_match_website_reference_exact
FAILED tests/book_converter/test_analyzer.py::TestWebsiteReferencePatternMatching::test_website_reference_read_aloud_false
FAILED tests/book_converter/test_analyzer.py::TestFootnotePatternMatching::test_match_footnote_simple
FAILED tests/book_converter/test_analyzer.py::TestFootnotePatternMatching::test_match_footnote_double_digit
FAILED tests/book_converter/test_analyzer.py::TestFootnotePatternMatching::test_match_footnote_large_numbers
FAILED tests/book_converter/test_analyzer.py::TestFootnotePatternMatching::test_match_footnote_with_trailing_text
FAILED tests/book_converter/test_analyzer.py::TestFootnotePatternMatching::test_footnote_read_aloud_false
FAILED tests/book_converter/test_analyzer.py::TestUserStory3Integration::test_mixed_headings_with_reference_and_footnote
FAILED tests/book_converter/test_analyzer.py::TestUserStory3Integration::test_all_exclusion_patterns_together
======================== 9 failed, 371 passed in 0.41s =========================
```

## 作成したテストコード

### TestWebsiteReferencePatternMatching クラス (6テスト)

```python
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

        assert result is None or result.id != "reference"

    def test_no_match_website_with_suffix(self) -> None:
        """「Webサイト一覧」（接尾辞あり）はマッチしない"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "Webサイト一覧"
        result = match_exclusion_pattern(text)

        assert result is None or result.id != "reference"

    def test_no_match_website_lowercase(self) -> None:
        """「webサイト」（小文字）はマッチしない"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "webサイト"
        result = match_exclusion_pattern(text)

        assert result is None or result.id != "reference"

    def test_no_match_website_partial(self) -> None:
        """「Webサイトを参照」はマッチしない"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "Webサイトを参照"
        result = match_exclusion_pattern(text)

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
```

### TestFootnotePatternMatching クラス (8テスト)

```python
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

        assert result is not None
        assert result.id == "footnote"

    def test_no_match_footnote_without_number(self) -> None:
        """「注」のみはマッチしない"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "注"
        result = match_exclusion_pattern(text)

        assert result is None or result.id != "footnote"

    def test_no_match_footnote_in_sentence(self) -> None:
        """「本文中の注3.1を参照」（文中）はマッチしない"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "本文中の注3.1を参照"
        result = match_exclusion_pattern(text)

        assert result is None or result.id != "footnote"

    def test_no_match_different_note_format(self) -> None:
        """「注記3」（異なる形式）はマッチしない"""
        from src.book_converter.analyzer import match_exclusion_pattern

        text = "注記3"
        result = match_exclusion_pattern(text)

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
```

### TestUserStory3Integration クラス (2テスト)

```python
class TestUserStory3Integration:
    """User Story 3 の統合テスト - 参照・メタ情報の除外"""

    def test_mixed_headings_with_reference_and_footnote(self) -> None:
        """参照表記と脚注番号を含む混合見出しで正しい除外判定"""
        from src.book_converter.analyzer import apply_read_aloud_rules

        headings = [
            Heading(level=1, text="第1章：はじめに"),        # 通常 -> True
            Heading(level=2, text="Webサイト"),              # 参照 -> False
            Heading(level=2, text="1.1 概要"),               # 通常 -> True
            Heading(level=3, text="注3.1"),                  # 脚注 -> False
            Heading(level=2, text="参考文献"),               # 通常 -> True
        ]

        processed = apply_read_aloud_rules(headings, [])

        assert len(processed) == 5
        assert processed[0].read_aloud is True   # 第1章：はじめに
        assert processed[1].read_aloud is False  # Webサイト
        assert processed[2].read_aloud is True   # 1.1 概要
        assert processed[3].read_aloud is False  # 注3.1
        assert processed[4].read_aloud is True   # 参考文献

    def test_all_exclusion_patterns_together(self) -> None:
        """全除外パターン（US1, US2, US3）を含む混合見出しで正しい除外判定"""
        from src.book_converter.analyzer import apply_read_aloud_rules

        headings = [
            Heading(level=1, text="第1章：はじめに"),           # 通常 -> True
            Heading(level=2, text="◆◆◆"),                      # 装飾 -> False (US2)
            Heading(level=3, text="Section 2.3"),               # ラベル -> False (US2)
            Heading(level=2, text="Webサイト"),                 # 参照 -> False (US3)
            Heading(level=3, text="注10.5"),                    # 脚注 -> False (US3)
            Heading(level=2, text="1.1.1 概要 — 1 / 3"),        # ページ番号 -> False (US1)
            Heading(level=2, text="3.2.1 モニタリングの基本"),  # 通常 -> True
        ]

        processed = apply_read_aloud_rules(headings, [])

        assert len(processed) == 7
        assert processed[0].read_aloud is True   # 第1章：はじめに
        assert processed[1].read_aloud is False  # ◆◆◆
        assert processed[2].read_aloud is False  # Section 2.3
        assert processed[3].read_aloud is False  # Webサイト
        assert processed[4].read_aloud is False  # 注10.5
        assert processed[5].read_aloud is False  # 1.1.1 概要 — 1 / 3
        assert processed[6].read_aloud is True   # 3.2.1 モニタリングの基本
```

## 次のステップ

Phase 4 Implementation (GREEN):
1. `src/book_converter/config.py` に reference パターン追加
2. `src/book_converter/config.py` に footnote パターン追加
3. `make test` PASS (GREEN) を確認
