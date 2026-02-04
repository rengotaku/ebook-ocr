# Phase 3 RED Tests

## サマリー
- Phase: Phase 3 - US2 デッドコード・レガシー依存の除去
- FAIL テスト数: 4
- PASS テスト数: 2 (既に修正済みのインポートパターン)
- テストファイル: tests/test_cleanup.py

## FAIL テスト一覧

| テストファイル | テストメソッド | 期待動作 |
|---------------|---------------|---------|
| tests/test_cleanup.py | TestNoLegacyOcrImport::test_legacy_ocr_module_deleted | src/ocr.py が削除されていること |
| tests/test_cleanup.py | TestNoUnusedDependencies::test_no_easyocr | requirements.txt に easyocr が含まれないこと |
| tests/test_cleanup.py | TestNoUnusedDependencies::test_no_pytesseract | requirements.txt に pytesseract が含まれないこと |
| tests/test_cleanup.py | TestNoUnusedDependencies::test_no_opencv_python | requirements.txt に opencv-python が含まれないこと |

## PASS テスト一覧 (Phase 2 で既に修正済み)

| テストファイル | テストメソッド | 理由 |
|---------------|---------------|------|
| tests/test_cleanup.py | TestNoLegacyOcrImport::test_no_legacy_ocr_import_in_src | Phase 2 で ocr_deepseek.py のインポートを修正済み |
| tests/test_cleanup.py | TestNoPrivateCrossImports::test_no_private_cross_imports | Phase 2 でプライベート関数のクロスインポートを解消済み |

## 実装ヒント
- `src/ocr.py` を削除する (219行のレガシーコード)
- `requirements.txt` から以下を削除する:
  - `easyocr`
  - `pytesseract`
  - `opencv-python`
- 削除後に `make test` で全 18 テスト PASS を確認する

## FAIL 出力例
```
FAILED tests/test_cleanup.py::TestNoLegacyOcrImport::test_legacy_ocr_module_deleted
  AssertionError: Legacy ocr.py should be deleted but still exists at /data/projects/video-separater/src/ocr.py

FAILED tests/test_cleanup.py::TestNoUnusedDependencies::test_no_easyocr
  AssertionError: Legacy dependency 'easyocr' found in requirements.txt: ['easyocr']

FAILED tests/test_cleanup.py::TestNoUnusedDependencies::test_no_pytesseract
  AssertionError: Legacy dependency 'pytesseract' found in requirements.txt: ['pytesseract']

FAILED tests/test_cleanup.py::TestNoUnusedDependencies::test_no_opencv_python
  AssertionError: Legacy dependency 'opencv-python' found in requirements.txt: ['opencv-python']
```

## make test 全出力
```
tests/test_cleanup.py::TestNoLegacyOcrImport::test_no_legacy_ocr_import_in_src PASSED
tests/test_cleanup.py::TestNoLegacyOcrImport::test_legacy_ocr_module_deleted FAILED
tests/test_cleanup.py::TestNoUnusedDependencies::test_no_easyocr FAILED
tests/test_cleanup.py::TestNoUnusedDependencies::test_no_pytesseract FAILED
tests/test_cleanup.py::TestNoUnusedDependencies::test_no_opencv_python FAILED
tests/test_cleanup.py::TestNoPrivateCrossImports::test_no_private_cross_imports PASSED
tests/test_utils.py (12 tests) ALL PASSED

4 failed, 14 passed in 0.05s
```
