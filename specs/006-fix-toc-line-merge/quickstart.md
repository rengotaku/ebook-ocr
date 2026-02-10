# Quickstart: TOC解析改行結合とページ欠損修正

**Feature**: 006-fix-toc-line-merge
**Date**: 2026-02-09

## 概要

この機能は、PDFから変換されたマークダウンファイルのTOCセクションで改行により分割されたエントリを正しく結合し、ページ欠損を防止します。

## 変更対象ファイル

| ファイル | 変更内容 |
|----------|----------|
| `src/book_converter/parser.py` | `merge_toc_lines()` 追加、`normalize_toc_line()` 拡張、`parse_toc_entry()` 拡張 |
| `src/book_converter/page_grouper.py` | `validate_page_count()` 追加、`group_pages_by_toc()` 修正 |
| `tests/book_converter/test_parser.py` | 新パターンのテスト追加 |
| `tests/book_converter/test_page_grouper.py` | ページ欠損検出テスト追加 |

## 実装フェーズ

### Phase 1: TOC行結合 (FR-001, FR-002, FR-003)

1. `merge_toc_lines()` 関数を追加
2. `_parse_single_page_content()` 内でTOCパース前に呼び出し
3. テスト: Chapter/Episode/Column パターンの結合

### Phase 2: parse_toc_entry拡張 (FR-004, FR-007)

1. `normalize_toc_line()` に `**text**` 除去を追加
2. `parse_toc_entry()` に `Chapter N タイトル` パターン追加
3. テスト: 新パターンの認識

### Phase 3: ページ欠損防止 (FR-005)

1. `group_pages_by_toc()` でTOCにマッチしないページをfront-matterに配置
2. すべてのページが出力に含まれることを保証
3. テスト: 181ページ入力 → 181ページ出力

### Phase 4: エラー検出 (FR-008)

1. `validate_page_count()` 関数を追加
2. 50%未満でエラーメッセージ出力
3. テスト: 欠損時のエラーメッセージ確認

### Phase 5: 回帰テスト (FR-006)

1. 既存テストがすべてパスすることを確認
2. `4fd5500620491ebe/book.md` の変換結果が変わらないことを確認

## TDDサイクル

各Phaseで以下のサイクルを実施：

1. **RED**: テストを書く（失敗を確認）
2. **GREEN**: 最小限の実装でテストをパス
3. **REFACTOR**: コードを整理

## 検証コマンド

```bash
# 全テスト実行
make test

# 特定テストのみ
pytest tests/book_converter/test_parser.py -v
pytest tests/book_converter/test_page_grouper.py -v

# 問題ファイルでの手動検証
python -m src.book_converter.cli convert output/157012a97dcbebed/book.md -o /tmp/test.xml
grep -c "<page " /tmp/test.xml  # 181であることを確認
```

## 成功基準チェック

| 基準 | 検証方法 |
|------|----------|
| SC-001: TOC結合 | XMLに「Chapter」「Episode」「Column」の単独エントリがない |
| SC-002: ページ数 | `grep -c "<page " output.xml` で181 |
| SC-003: 回帰なし | 正常ファイルの出力が変わらない |
| SC-004: テスト成功 | `make test` がパス |
| SC-005: エラー検出 | 50%欠損時にエラーメッセージ出力 |
