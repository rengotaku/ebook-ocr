# Phase 2 Test Implementation (RED) 結果

**Date**: 2026-02-21
**Phase**: Phase 2 - コード検出コア機能
**Status**: RED (全テストFAIL)

## サマリー

| 項目 | 値 |
|------|-----|
| Phase | 2 - コード検出コア機能 |
| FAILテスト数 | 13 |
| テストファイル | `tests/unit/layout/test_code_detector.py` |
| 失敗理由 | `ModuleNotFoundError: No module named 'src.layout.code_detector'` |
| 既存テスト影響 | なし (1306 passed, 6 skipped) |

## FAILテスト一覧

| テストファイル | テストメソッド | 期待する振る舞い |
|---------------|---------------|------------------|
| test_code_detector.py | `TestIsCode::test_is_code_with_python_code` | Pythonコードがコードと判定される |
| test_code_detector.py | `TestIsCode::test_is_code_with_java_code` | Javaコードがコードと判定される |
| test_code_detector.py | `TestIsCode::test_is_code_with_japanese_text` | 日本語テキストが非コードと判定される |
| test_code_detector.py | `TestIsCode::test_is_code_with_empty_string` | 空文字列が非コードと判定される |
| test_code_detector.py | `TestCodeRegion::test_code_region_creation` | CodeRegionの生成 |
| test_code_detector.py | `TestCodeRegion::test_code_region_default_ocr_text` | ocr_textのデフォルト値 |
| test_code_detector.py | `TestCodeRegion::test_code_region_immutability` | frozen dataclassの不変性 |
| test_code_detector.py | `TestCodeRegion::test_code_region_non_code` | is_code=Falseの領域表現 |
| test_code_detector.py | `TestDetectCodeInLayout::test_detect_code_in_layout` | TEXT→CODE再分類 |
| test_code_detector.py | `TestDetectCodeInLayout::test_detect_code_preserves_non_text_regions` | FIGURE等は維持 |
| test_code_detector.py | `TestDetectCodeInLayout::test_detect_code_with_threshold` | 閾値による判定制御 |
| test_code_detector.py | `TestDetectCodeInLayout::test_detect_code_returns_new_layout` | 元データの不変性 |
| test_code_detector.py | `TestDetectCodeInLayout::test_detect_code_empty_regions` | 空regionsの処理 |

## テスト構成

### TestIsCode (T008) - 4テスト

`is_code(text: str, threshold: float = 0.5) -> tuple[bool, float]` のテスト。

- Pythonコード → `(True, 0.5以上)`
- Javaコード → `(True, 0.5以上)`
- 日本語テキスト → `(False, _)`
- 空文字列 → `(False, 0.0)`

### TestCodeRegion (T009) - 4テスト

`CodeRegion` frozen dataclass のテスト。

- フィールド: `bbox`, `confidence`, `is_code`, `ocr_text`
- `ocr_text` のデフォルト値は空文字列
- frozen=True による不変性

### TestDetectCodeInLayout (T010) - 5テスト

`detect_code_regions(layout: dict, threshold: float = 0.5) -> dict` のテスト。

- TEXT領域のコード判定 → CODE再分類
- FIGURE/TITLE領域の維持
- 閾値パラメータの動作
- 元データの不変性（新辞書返却）
- 空regionsの処理

## 実装ヒント

### 必要なモジュール

`src/layout/code_detector.py` に以下を実装:

1. `CodeRegion` dataclass (frozen=True)
   - `bbox: tuple[int, int, int, int]`
   - `confidence: float`
   - `is_code: bool`
   - `ocr_text: str = ""`

2. `is_code(text: str, threshold: float = 0.5) -> tuple[bool, float]`
   - Guesslangを使用したコード判定
   - 空文字列は `(False, 0.0)` を返す

3. `detect_code_regions(layout: dict, threshold: float = 0.5) -> dict`
   - TEXT領域のみを走査
   - コード判定で閾値を超えた場合、type="CODE", label="code" に変更
   - 元の辞書を変更せず新しい辞書を返す

## FAIL出力例

```
FAILED tests/unit/layout/test_code_detector.py::TestIsCode::test_is_code_with_python_code - ModuleNotFoundError: No module named 'src.layout.code_detector'
FAILED tests/unit/layout/test_code_detector.py::TestIsCode::test_is_code_with_java_code - ModuleNotFoundError: No module named 'src.layout.code_detector'
FAILED tests/unit/layout/test_code_detector.py::TestIsCode::test_is_code_with_japanese_text - ModuleNotFoundError: No module named 'src.layout.code_detector'
FAILED tests/unit/layout/test_code_detector.py::TestIsCode::test_is_code_with_empty_string - ModuleNotFoundError: No module named 'src.layout.code_detector'
FAILED tests/unit/layout/test_code_detector.py::TestCodeRegion::test_code_region_creation - ModuleNotFoundError: No module named 'src.layout.code_detector'
FAILED tests/unit/layout/test_code_detector.py::TestCodeRegion::test_code_region_default_ocr_text - ModuleNotFoundError: No module named 'src.layout.code_detector'
FAILED tests/unit/layout/test_code_detector.py::TestCodeRegion::test_code_region_immutability - ModuleNotFoundError: No module named 'src.layout.code_detector'
FAILED tests/unit/layout/test_code_detector.py::TestCodeRegion::test_code_region_non_code - ModuleNotFoundError: No module named 'src.layout.code_detector'
FAILED tests/unit/layout/test_code_detector.py::TestDetectCodeInLayout::test_detect_code_in_layout - ModuleNotFoundError: No module named 'src.layout.code_detector'
FAILED tests/unit/layout/test_code_detector.py::TestDetectCodeInLayout::test_detect_code_preserves_non_text_regions - ModuleNotFoundError: No module named 'src.layout.code_detector'
FAILED tests/unit/layout/test_code_detector.py::TestDetectCodeInLayout::test_detect_code_with_threshold - ModuleNotFoundError: No module named 'src.layout.code_detector'
FAILED tests/unit/layout/test_code_detector.py::TestDetectCodeInLayout::test_detect_code_returns_new_layout - ModuleNotFoundError: No module named 'src.layout.code_detector'
FAILED tests/unit/layout/test_code_detector.py::TestDetectCodeInLayout::test_detect_code_empty_regions - ModuleNotFoundError: No module named 'src.layout.code_detector'
============================== 13 failed in 0.13s ==============================
```
