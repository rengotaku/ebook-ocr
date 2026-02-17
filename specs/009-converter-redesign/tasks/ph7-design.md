# Phase 7: 出力フォーマット簡素化 - 設計書

**Date**: 2026-02-17
**Status**: Draft

## 概要

XML出力から冗長なタグを削除し、より簡潔な構造に変更する。

## 要件

### R1: page, pageAnnouncement, content タグの削除

**現状**:
```xml
<chapter number="1" title="「企画」で失敗">
  <page number="22" sourceFile="page_0022">
    <pageAnnouncement format="simple" readAloud="false">22ページ</pageAnnouncement>
    <content readAloud="true">
      <heading level="1" readAloud="true">Chapter 1 「企画」で失敗</heading>
    </content>
  </page>
</chapter>
```

**変更後**:
```xml
<chapter number="1" title="「企画」で失敗">
  <!-- page 22 -->
  <heading level="1" readAloud="true">Chapter 1 「企画」で失敗</heading>
</chapter>
```

**変更点**:
- `<page>` タグ → `<!-- page N -->` コメントに変更
- `<pageAnnouncement>` タグ → 削除（ページコメントに統合）
- `<content>` タグ → 削除（子要素を直接出力）

### R2: 重複 heading の除去

chapter/section の title と同じ内容を持つ heading **のみ** 出力しない。

**重要**: chapter/section に該当しない heading はそのまま出力する。

```xml
<!-- 出力しない: chapter title と重複 -->
<heading level="1">Chapter 1 「企画」で失敗</heading>

<!-- 出力しない: section title と重複 -->
<heading level="2">Section 1.1 なんでもできる...</heading>

<!-- そのまま出力: chapter/section title と無関係 -->
<heading level="2" readAloud="true">すべての要求に応えてしまう</heading>
<heading level="2" readAloud="true">◎ソフトウェア開発は難しい</heading>
```

**比較ロジック**:
```
chapter title: "「企画」で失敗"
heading text:  "Chapter 1 「企画」で失敗"
                ↓ 正規化
                "1 「企画」で失敗"
                ↓ 比較
                "{number} {title}" と一致 → 出力しない
```

**正規化ルール**:
1. `Chapter N` → `N` (レベル1)
2. `Section N.N` → `N.N` (レベル2)
3. 先頭/末尾の空白を除去
4. 連続空白を単一空白に正規化

**例**:
```
入力 heading: "Chapter 1 「企画」で失敗"
正規化後: "1 「企画」で失敗"
chapter title: "「企画」で失敗", number: "1"
比較: "1 「企画」で失敗" == f"{number} {title}" → 一致 → 除外

入力 heading: "Section 1.1 なんでもできる「全部入りソフトウェア」"
正規化後: "1.1 なんでもできる「全部入りソフトウェア」"
section title: "なんでもできる「全部入りソフトウェア」", number: "1.1"
比較: "1.1 なんでもできる「全部入りソフトウェア」" == f"{number} {title}" → 一致 → 除外
```

## 影響範囲

### 変更対象ファイル

| ファイル | 変更内容 |
|----------|----------|
| `src/book_converter/transformer.py` | page/content タグ除去、heading 重複除去ロジック |
| `src/book_converter/xml_builder.py` | ページコメント生成の修正 |
| `tests/book_converter/test_transformer.py` | 新規テスト追加 |
| `specs/009-converter-redesign/contracts/xml-schema.md` | スキーマ更新 |

### 変更しないファイル

- `src/book_converter/models.py` - データモデルは変更なし
- `src/book_converter/parser.py` - パース処理は変更なし
- `src/book_converter/cli.py` - CLI引数は変更なし

## 実装方針

### Step 1: heading 重複除去関数

```python
def _normalize_heading_for_comparison(heading_text: str) -> str:
    """heading テキストを比較用に正規化.

    "Chapter 1 Title" → "1 Title"
    "Section 1.1 Title" → "1.1 Title"
    """
    # Chapter N / Section N.N パターンを除去
    text = re.sub(r'^Chapter\s+(\d+)\s*', r'\1 ', heading_text, flags=re.IGNORECASE)
    text = re.sub(r'^Section\s+(\d+\.\d+)\s*', r'\1 ', text, flags=re.IGNORECASE)
    # 空白正規化
    text = ' '.join(text.split())
    return text.strip()


def _is_duplicate_heading(
    heading_text: str,
    container_number: str | None,
    container_title: str,
) -> bool:
    """heading が構造コンテナのタイトルと重複するか判定."""
    normalized = _normalize_heading_for_comparison(heading_text)

    if container_number:
        expected = f"{container_number} {container_title}"
    else:
        expected = container_title

    return normalized == expected
```

### Step 2: transform 関数の修正

1. `transform_page` → 廃止、ページ番号のみコメント出力
2. `transform_content` → 廃止、子要素を直接返す
3. 構造コンテナ出力時に heading 重複チェック

### Step 3: xml_builder の修正

- ページコメント `<!-- page N -->` の生成
- page/content タグを含まない構造

## テスト計画

### Unit Tests

1. `test_normalize_heading_chapter` - "Chapter 1 Title" → "1 Title"
2. `test_normalize_heading_section` - "Section 1.1 Title" → "1.1 Title"
3. `test_is_duplicate_heading_true` - 重複判定 True ケース（chapter/section title と一致）
4. `test_is_duplicate_heading_false` - 重複判定 False ケース（chapter/section title と不一致）
5. `test_non_structural_heading_preserved` - 構造と無関係な heading が保持されること
6. `test_no_page_content_tags` - page/content タグが出力されないこと
7. `test_page_comment_format` - ページコメントフォーマット

### Integration Tests

1. `test_e2e_output_format` - 完全な出力フォーマット検証
2. `test_e2e_mixed_headings` - 重複/非重複 heading の混在ケース

## 出力例（期待値）

```xml
<?xml version="1.0" encoding="UTF-8"?>
<book>
  <metadata>
    <title>サンプル書籍</title>
  </metadata>

  <toc begin="5" end="7">
    <entry level="1" number="1" title="「企画」で失敗" page="22" />
    <entry level="2" number="1.1" title="なんでもできる..." page="23" />
  </toc>

  <front-matter>
    <!-- page 1 -->
    <paragraph>前付けテキスト。</paragraph>
  </front-matter>

  <chapter number="1" title="「企画」で失敗">
    <!-- page 22 -->
    <!-- "Chapter 1 「企画」で失敗" は title と重複のため省略 -->

    <section number="1.1" title="なんでもできる...">
      <!-- page 23 -->
      <!-- "Section 1.1 なんでもできる..." は title と重複のため省略 -->
      <paragraph>セクション本文。</paragraph>

      <!-- page 24 -->
      <heading level="2" readAloud="true">すべての要求に応えてしまう</heading>
      <paragraph>これは chapter/section title と無関係なので出力される。</paragraph>

      <heading level="2" readAloud="true">◎ソフトウェア企画の難しさ</heading>
      <paragraph>本文の小見出しもそのまま出力される。</paragraph>
    </section>
  </chapter>
</book>
```

## リスク

1. **後方互換性**: 既存の page/content タグに依存するコードがある場合は破壊的変更
   - 対策: xml-schema.md をバージョン 2.1.0 に更新

2. **heading 重複判定の誤検出**: 正規化ロジックが不完全な場合、本来出力すべき heading が削除される
   - 対策: 複数パターンのテストケースで検証

## 次のステップ

1. [x] 設計レビュー
2. [ ] テスト実装 (RED)
3. [ ] 実装 (GREEN)
4. [ ] スキーマドキュメント更新
5. [ ] tasks.md 更新
