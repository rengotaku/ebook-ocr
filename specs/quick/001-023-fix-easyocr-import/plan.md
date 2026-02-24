---
status: completed
created: 2026-02-24
branch: quick/001-023-fix-easyocr-import
issue: 23
---

# fix: EasyOCR fails with 'No module named ocr_preprocess'

## 概要

EasyOCR実行時に `No module named 'ocr_preprocess'` エラーが発生。
importパスが `src.` プレフィックスを含んでいないことが原因。

## ゴール

- [x] EasyOCRがpreprocessing付きで正常動作する
- [x] 同様のimportミスが他にないことを確認

## スコープ外

- ocr_preprocess.py の機能変更
- 他のOCRエンジンの変更

## 前提条件

- `src/ocr_preprocess.py` に `apply_clahe` 関数が存在（確認済み）
- プロジェクトのimportパターンは `from src.xxx import yyy`

---

## 実装タスク

### Phase 1: 修正

- [x] T001 [src/rover/engines/runners.py:321] importパスを修正
  ```python
  # Before
  from ocr_preprocess import apply_clahe
  # After
  from src.ocr_preprocess import apply_clahe
  ```

### Phase 2: 確認

- [x] T002 同様のimportミスがないか全体検索
- [x] T003 ruff check で構文エラーがないことを確認

---

## リスク

| レベル | 内容 |
|-------|------|
| LOW   | 単純なimportパス修正、影響範囲が限定的 |

---

## 完了条件

- [x] 全タスク完了
- [x] ruff check 通過
