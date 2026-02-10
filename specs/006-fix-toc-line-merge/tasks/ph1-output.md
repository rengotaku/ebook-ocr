# Phase 1: Setup - Output Report

## Summary
既存コードとテストファイルの分析を完了し、問題の根本原因を特定。

## Findings

### 問題の根本原因
TOCセクション内でエントリが複数行に分割されている:

```markdown
<!-- toc -->
Episode 01
なんでもできる「全部入りソフトウェア」
Episode 02
みんなの願いをかなえたい「八方美人仕様」
```

期待される形式（1行で完結）:
```markdown
<!-- toc -->
Episode 01 なんでもできる「全部入りソフトウェア」
Episode 02 みんなの願いをかなえたい「八方美人仕様」
```

### 関連ファイル
- `src/book_converter/parser.py` - TOCパーサー（parse_toc_entry関数）
- `src/book_converter/page_grouper.py` - ページグルーピング
- `tests/book_converter/test_parser.py` - 既存パーサーテスト

### 既存TOC処理の確認
- `parse_toc_marker()` - マーカー検出（正常）
- `parse_toc_entry()` - 個別行解析（行結合機能なし）
- `parse_pages_with_errors()` - ページ・TOC解析（要拡張）

### 必要な変更
1. **US1**: TOC行結合ロジックの追加
   - 不完全行の検出（番号パターンのみ、タイトルなし）
   - 次行との結合処理

2. **US2**: ページ欠損防止
   - 改行結合時のソースファイル情報の保持
   - ページマーカーとの関連付け維持

3. **US3**: 既存動作の保持
   - 正常形式（1行完結）のTOCは変更なし
   - 既存テストが全てパス

## Status
- [X] T001: 既存parserモジュール確認
- [X] T002: 既存page_grouperモジュール確認
- [X] T003: テストファイル確認
- [X] T004: テストカバレッジ確認
- [X] T005: 問題ファイルTOC構造分析
- [X] T006: 正常ファイルTOC構造比較
- [X] T007: 分析レポート作成
- [X] T008: Phase 1完了

## Next Phase
Phase 2 (US1): TOC改行分割エントリの結合 - TDD
