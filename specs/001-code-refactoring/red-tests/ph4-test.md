# Phase 4 RED Tests

## Summary
- Phase: Phase 4 - User Story 3: Auto Test Suite Introduction
- FAIL test count: 3
- PASS test count: 35 (including 18 existing + 17 new passing)
- Total new tests: 20
- Test files: tests/test_deduplicate.py, tests/test_ocr_deepseek.py, tests/test_describe_figures.py

## FAIL Test List

| Test File | Test Method | Expected Behavior |
|-----------|-------------|-------------------|
| tests/test_deduplicate.py | TestDeduplicateDifferentImages::test_deduplicate_different_images | Different colored images (red/green/blue) should all be kept (3 pages). Fails because solid-color phash produces similar hashes within threshold=8. GREEN phase needs to use patterned images or adjust test. |
| tests/test_deduplicate.py | TestDeduplicateContextManager::test_context_manager_usage | Image.open() in deduplicate.py should use `with` statement (FR-008). Currently uses bare `Image.open()` without context manager. |
| tests/test_ocr_deepseek.py | TestOcrDeepseekContextManager::test_context_manager_usage | Image.open() in ocr_deepseek.py should use `with` statement (FR-008). Currently uses bare `Image.open()` without context manager. |

## PASS Test List (new tests that already pass)

| Test File | Test Method | Verified Behavior |
|-----------|-------------|-------------------|
| tests/test_deduplicate.py | test_deduplicate_identical_images | Identical images deduplicated to 1 page |
| tests/test_deduplicate.py | test_deduplicate_empty_dir | Empty directory returns [] |
| tests/test_deduplicate.py | test_output_files_named_page | Output files follow page_NNNN.png naming |
| tests/test_ocr_deepseek.py | test_ocr_page_deepseek_mock | Mocked Ollama API returns OCR text |
| tests/test_ocr_deepseek.py | test_ocr_page_deepseek_strips_whitespace | Whitespace stripped from response |
| tests/test_ocr_deepseek.py | test_detect_repetition_normal | Normal text returns None |
| tests/test_ocr_deepseek.py | test_detect_repetition_anomaly | 20 repeated lines triggers detection |
| tests/test_ocr_deepseek.py | test_detect_repetition_boundary | 11 repeated lines (boundary) triggers detection |
| tests/test_ocr_deepseek.py | test_detect_repetition_empty | Empty string returns None |
| tests/test_ocr_deepseek.py | test_detect_repetition_whitespace_only | Whitespace-only returns None |
| tests/test_describe_figures.py | test_figure_marker_with_confidence | FIGURE marker with confidence matches correctly |
| tests/test_describe_figures.py | test_table_marker_without_confidence | TABLE marker without confidence matches |
| tests/test_describe_figures.py | test_plain_text_no_match | Plain text does not match |
| tests/test_describe_figures.py | test_figure_marker_in_multiline | Marker found in multiline text |
| tests/test_describe_figures.py | test_marker_findall_multiple | Multiple markers found via finditer |
| tests/test_describe_figures.py | test_describe_single_mock | Mocked VLM API returns description |
| tests/test_describe_figures.py | test_describe_single_strips_whitespace | Whitespace stripped from VLM response |

## Implementation Hints

### FAIL 1: test_deduplicate_different_images
- Solid-color images produce similar perceptual hashes (phash)
- GREEN phase option A: Use patterned/complex images in test that produce distinct hashes
- GREEN phase option B: Adjust test expectations for phash behavior with solid colors

### FAIL 2-3: context_manager_usage (deduplicate.py, ocr_deepseek.py)
- `src/deduplicate.py` line 42: `img = Image.open(frame_path)` -> `with Image.open(frame_path) as img:`
- `src/ocr_deepseek.py` line 160: `raw_img = Image.open(page_path)` -> `with Image.open(page_path) as raw_img:`
- These are FR-008 resource management pattern fixes

## FAIL Output
```
FAILED tests/test_deduplicate.py::TestDeduplicateDifferentImages::test_deduplicate_different_images
  AssertionError: Different images should all be kept, got 1 instead of 3

FAILED tests/test_deduplicate.py::TestDeduplicateContextManager::test_context_manager_usage
  AssertionError: Image.open should use context manager (with statement) to ensure file handles are properly closed

FAILED tests/test_ocr_deepseek.py::TestOcrDeepseekContextManager::test_context_manager_usage
  AssertionError: Image.open should use context manager (with statement) to ensure file handles are properly closed

========================= 3 failed, 35 passed in 0.22s =========================
```
