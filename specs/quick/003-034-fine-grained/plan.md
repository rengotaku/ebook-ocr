---
status: completed
created: 2026-03-01
branch: quick/003-034-fine-grained
issue: "#34"
---

# Fine-grained Spread Trim Control

## 概要

見開きモードで4つのエッジ（左ページの外側/内側、右ページの内側/外側）を独立してトリム可能にする。
現在の `left_page_outer` / `right_page_outer` に加え、`left_page_inner` / `right_page_inner` を追加。

## ゴール

- [ ] TrimConfig に inner エッジ用フィールドを追加
- [ ] split_spread 処理で 4 エッジ独立トリムを適用
- [ ] CLI 引数を追加（新旧両方サポート）
- [ ] Makefile 変数を追加

## スコープ外

- 古い変数名の完全削除（後方互換性のため残す）
- preview_trim_grid の更新（別 Issue）
- config.yaml スキーマの正式な更新

## 前提条件

- 既存の TrimConfig, split_spread を拡張
- 後方互換性を維持（--left-trim, --right-trim は引き続き動作）

---

## 実装タスク

### Phase 1: TrimConfig 拡張

- [x] T001 [src/preprocessing/split_spread.py] TrimConfig に left_page_inner, right_page_inner フィールド追加

### Phase 2: トリム処理更新

- [x] T002 [src/preprocessing/split_spread.py] split_spread 関数で inner エッジのトリム適用

### Phase 3: CLI 更新

- [x] T003 [src/cli/split_spreads.py] 新しい CLI 引数追加（--left-page-outer, --left-page-inner, --right-page-inner, --right-page-outer）
- [x] T004 [P] [src/cli/split_spreads.py] 旧引数（--left-trim, --right-trim）を新引数のエイリアスとして維持

### Phase 4: Makefile 更新

- [x] T005 [Makefile] 新しい変数追加（SPREAD_LEFT_PAGE_INNER, SPREAD_RIGHT_PAGE_INNER）
- [x] T006 [P] [Makefile] 既存変数を新命名規則に更新（LEFT_TRIM → SPREAD_LEFT_PAGE_OUTER）

### Phase 5: テスト・ドキュメント

- [x] T007 [tests/preprocessing/test_split_spread.py] inner トリムのユニットテスト追加
- [x] T008 [CLAUDE.md] 新しいトリム変数のドキュメント追加

---

## リスク

| レベル | 内容 |
|-------|------|
| LOW | 後方互換性の維持（旧引数をエイリアスとして残すため問題なし） |
| LOW | 4エッジ独立トリムの組み合わせ増加によるテストケース増 |

---

## 完了条件

- [x] 全タスク完了
- [x] テスト通過（pytest）
- [x] 既存の --left-trim, --right-trim が動作継続
