# Phase 5 RED Test Output: 後方互換性コードの除去

**日付**: 2026-02-18
**Feature**: 010-pipeline-refactoring
**Phase**: Phase 5 - User Story 4 (後方互換性コードの除去)
**状態**: RED (テストFAIL)

## 概要

| 項目 | 値 |
|------|-----|
| Phase | 5 |
| User Story | US4 - 後方互換性コードの除去 |
| FAILテスト数 | 10 |
| PASSテスト数 | 1 |
| テストファイル | 2 |

## テストファイル一覧

| ファイル | テスト数 | 状態 |
|----------|----------|------|
| `tests/test_fallback_removal.py` | 7 | 6 FAILED, 1 PASS |
| `tests/book_converter/test_parser.py` (新規テストクラス) | 4 | 3 FAILED, 1 PASS |

## FAIL テスト一覧

### tests/test_fallback_removal.py

| テストメソッド | 期待動作 | 失敗理由 |
|----------------|----------|----------|
| `TestEnginePriorityFallback::test_no_fallback_key` | ENGINE_PRIORITYに"FALLBACK"キーがない | "FALLBACK"キーがまだ存在する |
| `TestEnginePriorityFallback::test_has_default_key` | ENGINE_PRIORITYに"DEFAULT"キーがある | "DEFAULT"キーがまだない |
| `TestEnginePriorityFallback::test_default_engines_list` | DEFAULT = ["yomitoku", "paddleocr", "tesseract"] | "DEFAULT"キーがないためNone |
| `TestLegacyPatternRemoval::test_no_legacy_comment` | "Legacy patterns..."コメントがない | コメントがまだ存在する |
| `TestLegacyPatternRemoval::test_no_legacy_chapter_pattern_comment` | "- legacy"アノテーションがない | アノテーションがまだ存在する |
| `TestLegacyPatternRemoval::test_no_redundant_case_insensitive_chapter_pattern` | [Cc][Hh][Aa]...パターンがない | 冗長なパターンがまだ存在する |
| `TestLegacyPatternRemoval::test_no_japanese_chapter_legacy_pattern` | Legacy セクションに日本語章パターンがない | パターンがまだ存在する |

### tests/book_converter/test_parser.py (TestLegacyPatternRemovalInParser)

| テストメソッド | 期待動作 | 失敗理由 |
|----------------|----------|----------|
| `test_parser_has_no_legacy_patterns_comment` | "Legacy patterns..."コメントがない | コメントがまだ存在する |
| `test_parser_has_no_legacy_annotation` | "- legacy"アノテーションがない | アノテーションがまだ存在する |
| `test_parser_no_character_class_case_insensitive_pattern` | [Cc][Hh][Aa]...パターンがない | 冗長なパターンがまだ存在する |

### PASS テスト

| テストメソッド | 内容 |
|----------------|------|
| `test_parser_uses_ignorecase_for_chapter` | re.IGNORECASEが使用されていることを確認 (既存の新フォーマットで対応済み) |

## 実装ヒント

### T083: ENGINE_PRIORITY["FALLBACK"] -> "DEFAULT" リネーム

**ファイル**: `src/ocr_integrated.py` (59行目付近)

```python
# Before
ENGINE_PRIORITY = {
    ...
    "FALLBACK": ["yomitoku", "paddleocr", "tesseract"],
}

# After
ENGINE_PRIORITY = {
    ...
    "DEFAULT": ["yomitoku", "paddleocr", "tesseract"],
}
```

**注意**: "FALLBACK"を参照している箇所を全て"DEFAULT"に更新する必要あり。

### T084: book_converter/parser.py のレガシーパターン除去

**ファイル**: `src/book_converter/parser.py` (584-607行目付近)

削除対象:
1. **584行目**: `# Legacy patterns below for backward compatibility` コメント
2. **586-595行目**: `# Chapter pattern 1: 第N章 タイトル` とその処理
3. **597-607行目**: `# Chapter pattern 2: Chapter N タイトル (case insensitive) - legacy` とその処理

**削除理由**:
- 544-556行目の新フォーマット `Chapter N Title` が `re.IGNORECASE` で既にケースインセンシティブに対応
- 日本語章パターン `第N章` はハードコードされるべきでない (CLAUDE.md 準拠)
- `[Cc][Hh][Aa][Pp][Tt][Ee][Rr]` パターンは `re.IGNORECASE` と重複

### Category B (維持対象) - 削除しないこと

以下はエラーリカバリ用フォールバックのため維持:
- `layout_ocr.py:99` - `ocr_with_fallback()`: OCRエンジン連鎖
- `layout_ocr.py:258` - `should_fallback()`: 低カバレッジ検出
- `book_converter/toc_classifier.py:154,202` - LLM失敗時のフォールバック
- `book_converter/parser.py:516` - ルールベースフォールバック (LLM失敗時)

## FAIL 出力例

```
FAILED tests/test_fallback_removal.py::TestEnginePriorityFallback::test_no_fallback_key
AssertionError: ENGINE_PRIORITY should not have 'FALLBACK' key. Rename to 'DEFAULT' for clarity.
assert 'FALLBACK' not in {'TEXT': [...], 'FALLBACK': ['yomitoku', 'paddleocr', 'tesseract']}

FAILED tests/test_fallback_removal.py::TestLegacyPatternRemoval::test_no_legacy_comment
AssertionError: Remove 'Legacy patterns below for backward compatibility' comment from parser.py
assert 'Legacy patterns below for backward compatibility' not in '...'

FAILED tests/book_converter/test_parser.py::TestLegacyPatternRemovalInParser::test_parser_no_character_class_case_insensitive_pattern
AssertionError: parser.py should not use character-class case insensitivity. The new pattern with re.IGNORECASE handles case insensitivity.
assert '[Cc][Hh][Aa][Pp][Tt][Ee][Rr]' not in '...'
```

## テスト実行コマンド

```bash
# 全テスト実行
make test

# Phase 5 RED テストのみ
python -m pytest tests/test_fallback_removal.py tests/book_converter/test_parser.py::TestLegacyPatternRemovalInParser -v
```

## 次のステップ

phase-executor が Implementation (GREEN) を実行:

1. T082: RED テストを読み込み
2. T083: ENGINE_PRIORITY["FALLBACK"] を "DEFAULT" にリネーム
3. T084: book_converter/parser.py のレガシーパターンを除去
4. T085: 関連する呼び出し箇所を更新
5. T086: `make test` PASS を確認 (GREEN)
6. T087-T089: Verification
