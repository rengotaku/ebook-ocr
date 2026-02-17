# Phase 2 テスト実装 (RED)

**Date**: 2026-02-14
**Phase**: Phase 2 - US1 + US2 (基本的なOCR補完 + ゴミ出力の除外)
**Status**: RED (FAILを確認)

## サマリー

| 項目 | 値 |
|------|-----|
| Phase | 2 |
| 対象US | US1 (基本的なOCR補完), US2 (ゴミ出力の除外) |
| テストファイル | tests/test_ocr_rover.py |
| 新規テスト数 | 49 |
| FAIL数 | 25 |
| PASS数 | 24 (既存機能) |

## テストファイル一覧

| ファイル | 説明 |
|----------|------|
| tests/test_ocr_rover.py | ROVER OCRモジュールのテスト |
| tests/conftest.py | sys.path追加（src/へのパス） |

## FAILしたテスト一覧

### T009: is_garbage (ゴミ判定) - 11 FAIL

| テストメソッド | 期待動作 | FAIL理由 |
|----------------|----------|----------|
| test_is_garbage_empty_string | 空文字列 -> True | ImportError: is_garbageが未実装 |
| test_is_garbage_whitespace_only | 空白のみ -> True | ImportError: is_garbageが未実装 |
| test_is_garbage_low_confidence | confidence < 0.5 -> True | ImportError: is_garbageが未実装 |
| test_is_garbage_confidence_threshold | confidence >= 0.5の日本語 -> False | ImportError: is_garbageが未実装 |
| test_is_garbage_short_ascii_without_japanese | 5文字以下ASCII -> True | ImportError: is_garbageが未実装 |
| test_is_garbage_long_ascii_is_valid | 6文字以上ASCII -> False | ImportError: is_garbageが未実装 |
| test_is_garbage_repeated_chars | 5回以上繰り返し -> True | ImportError: is_garbageが未実装 |
| test_is_garbage_repeated_chars_threshold | 4回繰り返し -> False | ImportError: is_garbageが未実装 |
| test_is_garbage_mixed_content_with_japanese | 日本語含む -> False | ImportError: is_garbageが未実装 |
| test_is_garbage_punctuation_only | 記号のみ -> True | ImportError: is_garbageが未実装 |
| test_is_garbage_valid_japanese_text | 有効な日本語 -> False | ImportError: is_garbageが未実装 |

### T010: normalize_confidence (信頼度正規化) - 12 FAIL

| テストメソッド | 期待動作 | FAIL理由 |
|----------------|----------|----------|
| test_normalize_confidence_yomitoku_low | 0.4 -> 0.0 | ImportError: normalize_confidenceが未実装 |
| test_normalize_confidence_yomitoku_mid | 0.7 -> 0.5 | ImportError: normalize_confidenceが未実装 |
| test_normalize_confidence_yomitoku_high | 1.0 -> 1.0 | ImportError: normalize_confidenceが未実装 |
| test_normalize_confidence_paddleocr_low | 0.85 -> 0.0 | ImportError: normalize_confidenceが未実装 |
| test_normalize_confidence_paddleocr_mid | 0.925 -> 0.5 | ImportError: normalize_confidenceが未実装 |
| test_normalize_confidence_paddleocr_high | 1.0 -> 1.0 | ImportError: normalize_confidenceが未実装 |
| test_normalize_confidence_easyocr_low | 0.25 -> 0.0 | ImportError: normalize_confidenceが未実装 |
| test_normalize_confidence_easyocr_mid | 0.625 -> 0.5 | ImportError: normalize_confidenceが未実装 |
| test_normalize_confidence_easyocr_high | 1.0 -> 1.0 | ImportError: normalize_confidenceが未実装 |
| test_normalize_confidence_clamp_below_min | 0.3 (yomitoku) -> 0.0 | ImportError: normalize_confidenceが未実装 |
| test_normalize_confidence_clamp_above_max | 1.1 (yomitoku) -> 1.0 | ImportError: normalize_confidenceが未実装 |
| test_normalize_confidence_unknown_engine | 0.5 (unknown) -> 0.5 | ImportError: normalize_confidenceが未実装 |

### T013: rover_merge フィルタ - 1 FAIL

| テストメソッド | 期待動作 | FAIL理由 |
|----------------|----------|----------|
| test_rover_merge_filters_garbage | ゴミ出力がフィルタされる | ImportError: is_garbageが未実装 |

### Edge Cases - 1 FAIL

| テストメソッド | 期待動作 | FAIL理由 |
|----------------|----------|----------|
| test_is_garbage_unicode_special_chars | Unicode処理 | ImportError: is_garbageが未実装 |

## PASSしたテスト一覧 (既存機能)

### T011: cluster_lines_by_y (行クラスタリング) - 8 PASS

- test_cluster_lines_by_y_empty
- test_cluster_lines_by_y_single_item
- test_cluster_lines_by_y_same_line
- test_cluster_lines_by_y_multiple_lines
- test_cluster_lines_by_y_tolerance
- test_cluster_lines_by_y_exceeds_tolerance
- test_cluster_lines_by_y_x_ordering
- test_cluster_lines_by_y_confidence_averaging

### T012: align_lines_by_y (行アライメント) - 6 PASS

- test_align_lines_by_y_empty
- test_align_lines_by_y_single_engine
- test_align_lines_by_y_same_y_different_engines
- test_align_lines_by_y_different_y
- test_align_lines_by_y_partial_coverage
- test_align_lines_by_y_three_engines

### T013: rover_merge (基本機能) - 8 PASS

- test_rover_merge_empty
- test_rover_merge_single_engine
- test_rover_merge_basic_complementation
- test_rover_merge_agreement_voting
- test_rover_merge_primary_engine_priority
- test_rover_merge_failed_engine_ignored
- test_rover_merge_gap_filling_count
- test_rover_merge_multiple_lines

### Edge Cases - 1 PASS

- test_cluster_lines_large_document

## 実装ヒント

### is_garbage (src/ocr_rover.py)

```python
def is_garbage(
    text: str,
    confidence: float,
    min_confidence: float = 0.5,
) -> bool:
    """Check if text is garbage output.

    Garbage criteria:
    1. Empty or whitespace-only
    2. confidence < min_confidence
    3. No Japanese chars and len <= 5 (ASCII fragments)
    4. Same character repeated >= 5 times
    5. Punctuation only
    """
    # 1. 空文字列・空白のみ
    if not text or not text.strip():
        return True

    # 2. 低信頼度
    if confidence < min_confidence:
        return True

    # 3. 日本語なし短ASCII
    # 4. 繰り返し文字
    # 5. 記号のみ
    ...
```

### normalize_confidence (src/ocr_rover.py)

```python
def normalize_confidence(raw_conf: float, engine: str) -> float:
    """Normalize confidence to [0, 1] scale based on engine-specific range.

    Ranges (from research):
    - yomitoku: (0.4, 1.0)
    - paddleocr: (0.85, 1.0)
    - easyocr: (0.25, 1.0)
    - unknown: (0.0, 1.0)
    """
    ranges = {
        "yomitoku": (0.4, 1.0),
        "paddleocr": (0.85, 1.0),
        "easyocr": (0.25, 1.0),
    }
    min_conf, max_conf = ranges.get(engine, (0.0, 1.0))
    normalized = (raw_conf - min_conf) / (max_conf - min_conf)
    return max(0.0, min(1.0, normalized))
```

## FAIL出力例

```
$ make test
...
tests/test_ocr_rover.py::TestIsGarbage::test_is_garbage_empty_string FAILED
tests/test_ocr_rover.py::TestIsGarbage::test_is_garbage_whitespace_only FAILED
tests/test_ocr_rover.py::TestNormalizeConfidence::test_normalize_confidence_yomitoku_low FAILED
...

E       ImportError: cannot import name 'is_garbage' from 'src.ocr_rover'
        (/data/projects/video-separater/src/ocr_rover.py)

E       ImportError: cannot import name 'normalize_confidence' from 'src.ocr_rover'
        (/data/projects/video-separater/src/ocr_rover.py)

======================== 25 failed, 24 passed in 0.19s =========================
```

## 次のステップ

1. **Implementation (GREEN)**: 以下の関数を `src/ocr_rover.py` に実装
   - `is_garbage`: ゴミ判定関数
   - `normalize_confidence`: 信頼度正規化関数
   - `rover_merge`内でのゴミフィルタ統合

2. **Verification**: `make test` で全テスト通過を確認

3. **Phase出力**: `specs/008-rover-redesign/tasks/ph2-output.md` を生成
