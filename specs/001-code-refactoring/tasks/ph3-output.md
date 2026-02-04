# Phase 3 Output

## 作業概要
- Phase 3 - User Story 2: デッドコード・レガシー依存の除去 完了
- FAIL テスト 4 件を PASS させた (RED → GREEN)
- レガシーコード 219 行削除
- 不要依存パッケージ 3 件削除

## 修正ファイル一覧
- `src/ocr.py` - 削除 (219 行のレガシー Tesseract/EasyOCR 実装)
- `requirements.txt` - 修正 (easyocr, pytesseract, opencv-python を削除)

## テスト結果

### Before (RED)
```
4 failed, 14 passed in 0.05s

FAILED tests/test_cleanup.py::TestNoLegacyOcrImport::test_legacy_ocr_module_deleted
  AssertionError: Legacy ocr.py should be deleted but still exists

FAILED tests/test_cleanup.py::TestNoUnusedDependencies::test_no_easyocr
  AssertionError: Legacy dependency 'easyocr' found in requirements.txt

FAILED tests/test_cleanup.py::TestNoUnusedDependencies::test_no_pytesseract
  AssertionError: Legacy dependency 'pytesseract' found in requirements.txt

FAILED tests/test_cleanup.py::TestNoUnusedDependencies::test_no_opencv_python
  AssertionError: Legacy dependency 'opencv-python' found in requirements.txt
```

### After (GREEN)
```
============================== 18 passed in 0.04s ==============================

tests/test_cleanup.py::TestNoLegacyOcrImport::test_legacy_ocr_module_deleted PASSED
tests/test_cleanup.py::TestNoUnusedDependencies::test_no_easyocr PASSED
tests/test_cleanup.py::TestNoUnusedDependencies::test_no_pytesseract PASSED
tests/test_cleanup.py::TestNoUnusedDependencies::test_no_opencv_python PASSED
```

## 実装内容

### T035: src/ocr.py 削除
- 使われていないレガシー OCR モジュール (219 行) を削除
- Phase 2 で ocr_deepseek.py からの依存を解消済みのため、安全に削除可能

### T036: requirements.txt からレガシー依存削除
削除したパッケージ:
- `easyocr` - ocr.py でのみ使用
- `pytesseract` - ocr.py でのみ使用
- `opencv-python` - ocr.py でのみ使用 (注: doclayout-yolo が opencv-python を推移的依存で含むため、機能に影響なし)

残存パッケージ:
- Pillow - 画像処理で使用中
- imagehash - 重複除去で使用中
- doclayout-yolo - 図表検出で使用中
- requests - API 呼び出しで使用中
- pytest - テストフレームワーク

### T037-T038: 全テスト PASS 確認
- US2 テスト (6 tests): 全 PASS
- US1 テスト (12 tests): リグレッションなし、全 PASS
- 合計 18 tests: 全 PASS

## 次 Phase への引き継ぎ
- **US1 + US2 完了**: 共有ユーティリティ抽出 + デッドコード削除完了
- **コードベース削減**: 219 行削除 (1,167 行 → 948 行、-18.8%)
- **次 Phase**: Phase 4 - User Story 3 (自動テストスイート導入)
- **Phase 4 で必要な情報**: クリーンな src/ コードベース、既存テスト基盤 (pytest, conftest.py)

## 実装のミス・課題
- なし。全タスクが計画通り完了し、全テスト PASS。
