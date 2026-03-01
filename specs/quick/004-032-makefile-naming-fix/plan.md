---
status: completed
created: 2026-03-01
branch: quick/004-032-makefile-naming-fix
issue: 32
---

# 032-makefile-naming-fix

## 概要

Makefile の命名不整合と設定問題を修正。後方互換性は全て削除。

## ゴール

- [x] 非推奨変数・引数を完全削除
- [x] USE_LLM_TOC_CLASSIFIER を設定可能に
- [x] Legacy targets を完全削除

## スコープ外

- trim 変数命名（#34 で対応済み）
- 変数グループ化（別 Issue で対応）

## 前提条件

- 後方互換性は考慮しない（破壊的変更OK）

---

## 実装タスク

### Phase 1: 非推奨変数・引数の削除

- [x] T001 [Makefile] ASPECT_RATIO 変数定義を削除（L61）
- [x] T002 [Makefile] split-spreads から --aspect-ratio 引数削除（L75）
- [x] T003 [Makefile] OCR_TIMEOUT 変数定義を削除（L14）

### Phase 2: 設定の改善

- [x] T004 [Makefile] USE_LLM 変数を追加し converter ターゲットで使用（L182）

### Phase 3: Legacy/非推奨ターゲット削除

- [x] T005 [Makefile] test-run ターゲットを削除（L174-175）
- [x] T006 [Makefile] yomitoku-detect ターゲットを削除（L160-162）
- [x] T007 [Makefile] rover-ocr ターゲットを削除（L164-166）
- [x] T008 [Makefile] build-book ターゲットを削除（L168-170）
- [x] T009 [Makefile] Legacy セクションコメントを削除（L158-159）

### Phase 4: 確認

- [x] T010 `make help` でヘルプ表示確認
- [x] T011 `make lint` 通過確認

---

## リスク

| レベル | 内容 |
|-------|------|
| MEDIUM | Legacy targets 削除で古いスクリプト/ドキュメントが壊れる → Issue で告知済み |

---

## 完了条件

- [x] 全タスク完了
- [x] make help 正常動作
- [x] make lint 通過
