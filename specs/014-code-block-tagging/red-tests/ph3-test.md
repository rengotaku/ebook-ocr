# Phase 3 REDテスト結果: データモデル拡張

**Date**: 2026-02-21
**Phase**: Phase 3 - User Story 1 - データモデル拡張
**Status**: RED (全テストFAIL)

## サマリー

| 項目 | 値 |
|------|-----|
| Phase | 3 |
| FAILテスト数 | 9 |
| PASSテスト数 | 1319 (既存) |
| SKIPテスト数 | 6 (既存) |
| テストファイル | `tests/unit/book_converter/test_models.py` |

## FAILテスト一覧

| テストファイル | テストメソッド | 期待する動作 |
|---------------|---------------|-------------|
| test_models.py | `TestCodeDataclass::test_code_creation` | Code要素を正しく生成できる |
| test_models.py | `TestCodeDataclass::test_code_default_read_aloud_false` | read_aloudのデフォルト値はFalse |
| test_models.py | `TestCodeDataclass::test_code_immutability` | frozen dataclassの不変性確認 |
| test_models.py | `TestCodeDataclass::test_code_with_confidence` | confidence属性が正しく設定される |
| test_models.py | `TestCodeDataclass::test_code_default_confidence` | confidenceのデフォルト値は1.0 |
| test_models.py | `TestCodeDataclass::test_code_preserves_formatting` | 改行・インデントが保持される |
| test_models.py | `TestCodeDataclass::test_code_empty_text` | 空文字列のコードブロックを生成できる |
| test_models.py | `TestSectionElementWithCode::test_section_element_includes_code` | SectionElement Union型にCodeが含まれる |
| test_models.py | `TestSectionElementWithCode::test_section_with_code_element` | Section.elementsにCode要素を含められる |

## FAIL原因

全テストが `ImportError: cannot import name 'Code' from 'src.book_converter.models'` で失敗。
`Code` dataclass がまだ `src/book_converter/models.py` に実装されていないため。

## 実装ヒント

### T027-T029: Implementation (GREEN) で必要な作業

1. **Code dataclass追加** (`src/book_converter/models.py`)
   ```python
   @dataclass(frozen=True)
   class Code:
       """コードブロック要素"""
       text: str                    # コード本体（改行・インデント保持）
       confidence: float = 1.0      # Guesslang判定確率
       read_aloud: bool = False     # TTS読み上げ（常にFalse）
   ```

2. **SectionElement Union型更新** (`src/book_converter/models.py`)
   ```python
   # Before
   SectionElement = Union[Heading, Paragraph, List, Figure]
   # After
   SectionElement = Union[Heading, Paragraph, List, Figure, Code]
   ```

### 配置場所

- `Code` dataclass は `Figure` の直後（L67付近）に配置
- `SectionElement` 定義（L89）を更新

## FAIL出力例

```
FAILED tests/unit/book_converter/test_models.py::TestCodeDataclass::test_code_creation
  - ImportError: cannot import name 'Code' from 'src.book_converter.models'
FAILED tests/unit/book_converter/test_models.py::TestCodeDataclass::test_code_default_read_aloud_false
  - ImportError: cannot import name 'Code' from 'src.book_converter.models'
FAILED tests/unit/book_converter/test_models.py::TestCodeDataclass::test_code_immutability
  - ImportError: cannot import name 'Code' from 'src.book_converter.models'
FAILED tests/unit/book_converter/test_models.py::TestCodeDataclass::test_code_with_confidence
  - ImportError: cannot import name 'Code' from 'src.book_converter.models'
FAILED tests/unit/book_converter/test_models.py::TestCodeDataclass::test_code_default_confidence
  - ImportError: cannot import name 'Code' from 'src.book_converter.models'
FAILED tests/unit/book_converter/test_models.py::TestCodeDataclass::test_code_preserves_formatting
  - ImportError: cannot import name 'Code' from 'src.book_converter.models'
FAILED tests/unit/book_converter/test_models.py::TestCodeDataclass::test_code_empty_text
  - ImportError: cannot import name 'Code' from 'src.book_converter.models'
FAILED tests/unit/book_converter/test_models.py::TestSectionElementWithCode::test_section_element_includes_code
  - ImportError: cannot import name 'Code' from 'src.book_converter.models'
FAILED tests/unit/book_converter/test_models.py::TestSectionElementWithCode::test_section_with_code_element
  - ImportError: cannot import name 'Code' from 'src.book_converter.models'

================== 9 failed, 1319 passed, 6 skipped in 21.84s ==================
```
