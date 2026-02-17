# Phase 7 出力: 出力フォーマット簡素化 (US5)

**Date**: 2026-02-17
**Status**: GREEN (PASS confirmed)

## 概要

Phase 7 では、XML出力から冗長なタグを削除し、より簡潔な構造に変更した。

## 実装内容

### 1. 新規関数追加 (transformer.py)

#### normalize_heading_for_comparison()
- 見出しテキストから "Chapter N" / "Section N.N" プレフィックスを除去
- 空白を正規化
- 比較用の正規化されたテキストを返す

```python
normalize_heading_for_comparison("Chapter 1 「企画」で失敗")
# -> "1 「企画」で失敗"
```

#### is_duplicate_heading()
- 見出しがコンテナ（chapter/section）のタイトルと重複するか判定
- container_number + container_title と比較

```python
is_duplicate_heading("Chapter 1 「企画」で失敗", "1", "「企画」で失敗")
# -> True (重複)

is_duplicate_heading("すべての要求に応えてしまう", "1.1", "なんでもできる")
# -> False (構造と無関係な見出し、保持される)
```

### 2. _flatten_pages_in_element() 関数追加 (page_grouper.py)

ページ構造をフラット化する関数:
- `<page>` → `<!-- page N -->` コメントに変換
- `<content>` タグの子要素を直接親要素に展開
- `<pageAnnouncement>` タグを削除
- `<pageMetadata>` タグを削除
- 重複する heading を削除（is_duplicate_heading で判定）
- 再帰的に chapter/section/subsection/front-matter を処理

### 3. 出力形式の変更

#### Before (旧形式)
```xml
<chapter number="1" title="「企画」で失敗">
  <page number="2" sourceFile="page_0002.png">
    <pageMetadata>第1章 「企画」で失敗 — 1 / 1</pageMetadata>
    <content>
      <heading level="1">Chapter 1 「企画」で失敗</heading>
      <paragraph>説明文</paragraph>
    </content>
  </page>
  <section number="1.1" title="なんでもできる">
    <page number="3" sourceFile="page_0003.png">
      ...
    </page>
  </section>
</chapter>
```

#### After (新形式)
```xml
<chapter number="1" title="「企画」で失敗">
  <!-- page 2 -->
  <paragraph>説明文</paragraph>
  <section number="1.1" title="なんでもできる">
    <!-- page 3 -->
    ...
  </section>
</chapter>
```

## テスト結果

### テストファイル

1. **tests/book_converter/test_transformer.py**
   - `TestNormalizeHeadingForComparison` (6 tests)
   - `TestIsDuplicateHeading` (5 tests)
   - `TestNonStructuralHeadingPreserved` (1 test)

2. **tests/book_converter/test_page_grouper.py**
   - `TestPhase7OutputSimplification` (8 tests)
   - 既存テストを新形式に対応するよう更新

### テスト実行結果

```
$ make test
======================= 1191 passed, 6 skipped in 1.88s ========================
```

## 削除されたタグ

| タグ | 理由 |
|------|------|
| `<page>` | ページ境界はコメントで表現 |
| `<content>` | コンテンツは親要素に直接配置 |
| `<pageAnnouncement>` | ページ告知は不要 |
| `<pageMetadata>` | ページメタデータは不要 |

## 保持されるタグ

| タグ | 説明 |
|------|------|
| `<chapter>` | チャプター構造 |
| `<section>` | セクション構造 |
| `<subsection>` | サブセクション構造 |
| `<front-matter>` | 前付け |
| `<heading>` | 構造と無関係な見出しのみ |
| `<paragraph>` | 段落 |
| `<list>` | リスト |
| `<figure>` | 図 |

## 削除される見出し

chapter/section の title 属性と重複する見出し:
- "Chapter N タイトル" → 削除（N がコンテナ番号と一致）
- "Section N.M タイトル" → 削除（N.M がコンテナ番号と一致）

## 保持される見出し

構造と無関係な見出し:
- "すべての要求に応えてしまう" → 保持
- コンテナ番号と一致しない見出しは全て保持

## 検証チェックリスト

- [X] `<page>` タグなし
- [X] `<content>` タグなし
- [X] `<pageAnnouncement>` タグなし
- [X] `<pageMetadata>` タグなし
- [X] ページコメント `<!-- page N -->` 存在
- [X] 重複 chapter heading 削除
- [X] 重複 section heading 削除
- [X] 非構造的 heading 保持
- [X] コンテンツ要素（paragraph等）保持

## 次のステップ

- [ ] xml-schema.md をバージョン 2.1.0 に更新
