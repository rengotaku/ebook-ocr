# Phase 4 テスト実装 (RED) 結果

**Date**: 2026-02-21
**Phase**: Phase 4 - User Story 1 - パーサー統合
**Status**: RED - 14件のテストがFAIL

## サマリー

| 項目 | 値 |
|------|-----|
| Phase | 4 |
| FAILテスト数 | 14 |
| 既存テスト | 1328 passed, 6 skipped |
| テストファイル | 2ファイル |

### テストファイル一覧

| ファイル | テスト数 | 状態 |
|---------|---------|------|
| `tests/unit/book_converter/parser/test_code.py` | 6 | 全てFAIL |
| `tests/unit/book_converter/test_xml_builder.py` | 8 | 全てFAIL |

---

## FAILテスト一覧

### T035: コードパーサーテスト (`tests/unit/book_converter/parser/test_code.py`)

| テストメソッド | 期待動作 | FAIL理由 |
|---------------|---------|----------|
| `TestParseCodeRegion::test_parse_code_region` | CODE領域dictからCode dataclassを生成 | `ModuleNotFoundError: src.book_converter.parser.code` |
| `TestParseCodeRegion::test_parse_code_region_default_confidence` | confidence未指定時にデフォルト1.0 | 同上 |
| `TestParseCodeRegion::test_parse_code_preserves_formatting` | 改行・インデントが保持される | 同上 |
| `TestParseCodeRegion::test_parse_code_with_special_chars` | `<`, `>`, `&` 等の特殊文字処理 | 同上 |
| `TestParseCodeRegion::test_parse_code_with_empty_text` | 空のコードブロック処理 | 同上 |
| `TestParseCodeRegion::test_parse_code_with_unicode` | Unicode/日本語コメント含むコード | 同上 |

### T036: XMLビルダーテスト (`tests/unit/book_converter/test_xml_builder.py`)

| テストメソッド | 期待動作 | FAIL理由 |
|---------------|---------|----------|
| `TestTransformCode::test_build_xml_with_code` | Code要素が`<code>`タグとして出力 | `ImportError: cannot import name 'transform_code'` |
| `TestTransformCode::test_code_element_has_read_aloud_false` | `readAloud="false"`属性設定 | 同上 |
| `TestTransformCode::test_code_element_escapes_special_chars` | XML特殊文字エスケープ | 同上 |
| `TestTransformCode::test_code_element_preserves_newlines` | 改行保持 | 同上 |
| `TestTransformCode::test_code_element_preserves_indentation` | インデント保持 | 同上 |
| `TestTransformCode::test_code_element_empty_text` | 空テキストCode要素 | 同上 |
| `TestTransformSectionWithCode::test_section_with_code_element_in_xml` | Section内のCode要素がXML出力 | `assert 0 == 1` (code要素未出力) |
| `TestTransformSectionWithCode::test_section_with_mixed_elements` | Code/Paragraph混在Section | `assert 2 == 3` (Code要素スキップ) |

---

## 実装ヒント

### コードパーサー (`src/book_converter/parser/code.py`)

```python
from src.book_converter.models import Code

def parse_code_region(region: dict) -> Code:
    """CODE領域のdictからCode dataclassを生成する"""
    text = region.get("ocr_text", "")
    confidence = region.get("confidence", 1.0)
    return Code(text=text, confidence=confidence)
```

### XMLトランスフォーマー (`src/book_converter/transformer.py`)

1. `transform_code()` 関数を追加:

```python
def transform_code(code: Code) -> Element:
    """Code要素をXML Elementに変換する"""
    elem = Element("code")
    elem.set("readAloud", "false")
    elem.text = code.text
    return elem
```

2. `transform_section()` にCode分岐を追加:

```python
elif isinstance(child, Code):
    child_elem = transform_code(child)
    elem.append(child_elem)
```

3. importに `Code` を追加

---

## FAIL出力例

```
FAILED tests/unit/book_converter/parser/test_code.py::TestParseCodeRegion::test_parse_code_region
  - ModuleNotFoundError: No module named 'src.book_converter.parser.code'

FAILED tests/unit/book_converter/test_xml_builder.py::TestTransformCode::test_build_xml_with_code
  - ImportError: cannot import name 'transform_code' from 'src.book_converter.transformer'

FAILED tests/unit/book_converter/test_xml_builder.py::TestTransformSectionWithCode::test_section_with_code_element_in_xml
  - assert 0 == 1 (code子要素が見つからない)

================= 14 failed, 1328 passed, 6 skipped in 22.19s =================
```
