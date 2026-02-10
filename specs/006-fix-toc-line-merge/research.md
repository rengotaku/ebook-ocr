# Research: TOC解析改行結合とページ欠損修正

**Feature**: 006-fix-toc-line-merge
**Date**: 2026-02-09

## 1. TOC行結合パターンの調査

### Decision
TOCセクション内で以下のパターンを検出し、次の非空行と結合する：
- `Chapter` (単独行)
- `Episode NN` (NNは2桁番号)
- `Column` (単独行)
- `**キーワード**` (マークダウン強調で囲まれた上記)

### Rationale
実際の問題ファイル（157012a97dcbebed/book.md）を分析した結果、PDFからOCR変換時に改行が挿入され、TOCエントリが分割されていることが判明。結合対象は日本語技術書で一般的に使用されるパターンに限定。

### Alternatives Considered
1. **すべての行を結合**: 過剰結合のリスク、既存正常ファイルに影響
2. **空行のみで区切り**: 元データに空行がない場合に対応不可
3. **正規表現で完全一致**: 柔軟性に欠ける

## 2. parse_toc_entry拡張

### Decision
`Chapter N タイトル` 形式を認識する新パターンを追加：
- `^Chapter\s+(\d+)\s+(.+)$` → level="chapter", number=N, title=残り

### Rationale
既存の `第N章 タイトル` パターンと並列で、英語表記のChapterにも対応。`parse_toc_entry` 関数内で既存パターンの後に追加することで後方互換性を維持。

### Alternatives Considered
1. **別関数で実装**: コード重複、メンテナンス困難
2. **前処理で置換**: 「Chapter 1」→「第1章」に変換後パース → 情報損失

## 3. ページ欠損防止メカニズム

### Decision
`page_grouper.py` の `group_pages_by_toc` 関数で：
1. すべてのページを最初にカウント
2. グルーピング後のページ数をカウント
3. 50%未満の場合、警告メッセージを出力
4. TOCにマッチしないページは `front-matter` または最初のchapterに配置

### Rationale
現状、TOCが正しくパースされないとchapter要素が生成されず、ページが割り当て先を失って欠損する。フォールバック機構により、最悪の場合でもページは保持される。

### Alternatives Considered
1. **エラーで処理中断**: ユーザーが結果を確認できない
2. **すべてfront-matterに配置**: 構造情報が完全に失われる
3. **閾値なしで常に警告**: ノイズが多すぎる

## 4. 既存テストの確認

### Decision
既存のテストスイートを実行し、すべてパスすることを確認してから新機能を追加。

### Rationale
回帰を防ぐため、既存動作が保持されていることをテストで保証。

### Test Files to Verify
- `tests/book_converter/test_parser.py` - parse_toc_entry テスト
- `tests/book_converter/test_page_grouper.py` - group_pages_by_toc テスト
- `tests/book_converter/test_integration.py` - E2Eテスト

## 5. マークダウン強調記号の処理

### Decision
`normalize_toc_line` 関数を拡張して `**text**` パターンを除去：
```python
line = re.sub(r'\*\*(.+?)\*\*', r'\1', line)
```

### Rationale
問題ファイルには `**Episode 24**` のような強調記号付きエントリが存在。既存の `normalize_toc_line` に追加することで一貫性を維持。

### Alternatives Considered
1. **parse_toc_entry内で処理**: 正規表現が複雑化
2. **別の前処理関数**: コード分散
