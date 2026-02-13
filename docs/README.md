# video-separater ドキュメント

video-separaterの技術ドキュメント集です。

## 📚 ドキュメント一覧

### アーキテクチャ

- **[YOMITOKU_ARCHITECTURE.md](./YOMITOKU_ARCHITECTURE.md)**
  - yomitoku統合アーキテクチャの技術仕様
  - API仕様、データフロー、パフォーマンス
  - 対象: 開発者・技術担当者

### マイグレーション

- **[YOMITOKU_MIGRATION.md](./YOMITOKU_MIGRATION.md)**
  - YOLO + yomitoku → yomitoku統合への移行ガイド
  - 問題の背景、解決策、変更履歴
  - 対象: 既存プロジェクトのユーザー

## 🚀 クイックスタート

### v4パイプライン（最新）

```bash
# フル実行
make run VIDEO=input.mp4

# 個別ステップ（既存ページ）
make yomitoku-detect HASHDIR=output/<hash>  # Layout検出
make yomitoku-ocr HASHDIR=output/<hash>      # OCR実行
```

## 📖 仕様書

プロジェクトルートの`specs/`ディレクトリを参照:

- `specs/007-layout-region-ocr/` - Layout-aware OCR仕様

## 🔄 変更履歴

### v4 (2026-02-13)
- yomitoku統合アーキテクチャ実装
- YOLO廃止、detect_figures.py削除
- キャッシュ機構追加
- FIGURE検出対応
- タイトル認識問題解決

### v3 (2025-XX-XX)
- YOLO + yomitoku 2段階処理
- Layout-aware OCR導入

## 🐛 トラブルシューティング

問題が発生した場合:

1. [YOMITOKU_MIGRATION.md](./YOMITOKU_MIGRATION.md#トラブルシューティング) のトラブルシューティングセクション参照
2. [YOMITOKU_ARCHITECTURE.md](./YOMITOKU_ARCHITECTURE.md#デバッグ) のデバッグセクション参照
3. GitHubでIssue報告

## 📝 コントリビューション

ドキュメント改善のPR歓迎です。
