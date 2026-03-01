---
status: completed
created: 2026-02-28
branch: quick/002-033-preview-trim-grid
issue: 33
---

# Preview Trim Grid Visualization

## 概要

プレビュー画像にトリムガイドライン（グリッド）を描画し、最適なトリム値を視覚的に特定できるようにする。
試行錯誤の繰り返しを排除し、1回の実行で全候補値を確認可能にする。

## ゴール

- [x] `make preview-trim-grid` でトリムガイド付き画像を生成
- [x] 色分けされたライン（Top:赤, Bottom:青, Left:緑, Right:黄）で方向を識別
- [x] 各ラインに比率ラベル（例: "T:0.15"）を表示
- [x] step/max 値をパラメータで設定可能

## スコープ外

- 実際のトリム処理の変更
- インタラクティブな調整UI
- spread_left_trim / spread_right_trim のガイド表示（今回は global_trim のみ）

## 前提条件

- 既存の `preview-extract` で frames が生成済み
- Pillow (PIL) を使用（既存依存）
- spread_mode は参照するが、描画ロジックは同一

---

## 実装タスク

### Phase 1: CLI スクリプト作成

- [x] T001 [src/cli/preview_trim_grid.py] CLIエントリポイント作成（argparse）
- [x] T002 [src/cli/preview_trim_grid.py] 描画ロジック実装（ImageDraw）

### Phase 2: Makefile 統合

- [x] T003 [Makefile] `preview-trim-grid` ターゲット追加

### Phase 3: テスト・確認

- [x] T004 [tests/cli/test_preview_trim_grid.py] ユニットテスト作成
- [x] T005 動作確認（実際のプレビュー画像で検証）

---

## 技術設計

### CLI インターフェース

```bash
python -m src.cli.preview_trim_grid <input_dir> -o <output_dir> \
  --step 0.05 --max 0.30 --spread-mode single
```

### 描画仕様

| 方向 | 色 | ラベル | 描画位置 |
|------|-----|--------|---------|
| Top | 赤 (#FF0000) | T:0.05 | 画像上端から下向き |
| Bottom | 青 (#0000FF) | B:0.05 | 画像下端から上向き |
| Left | 緑 (#00FF00) | L:0.05 | 画像左端から右向き |
| Right | 橙 (#FFA500) | R:0.05 | 画像右端から左向き |

### ファイル構成

```
output/<hash>/preview/
├── frames/           # 入力（既存）
│   ├── page_001.png
│   └── ...
└── trim-grid/        # 出力（新規）
    ├── page_001.png  # ガイドライン付き
    └── ...
```

---

## リスク

| レベル | 内容 |
|-------|------|
| LOW | ライン色が画像と被って見づらい場合がある（半透明オーバーレイで対応可能） |
| LOW | フォントサイズが画像サイズに適さない場合（相対サイズで対応） |

---

## 完了条件

- [x] 全タスク完了
- [x] テスト通過
- [x] `make preview-trim-grid` が正常動作
- [x] ドキュメント（CLAUDE.md）更新
