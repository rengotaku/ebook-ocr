# Phase 2 Output: US1+US2 目次マーカー認識と構造化 (GREEN)

**Date**: 2026-02-08
**Status**: COMPLETE

## 1. サマリー

| 項目 | 値 |
|------|-----|
| Phase | 2 (US1+US2 MVP) |
| 実施タスク | T022-T036 (15タスク) |
| テスト結果 | 371 passed (全テストPASS) |
| カバレッジ | 97% (book_converter module) |
| Status | GREEN - 全実装完了 |

## 2. 実施した作業

### 2.1 Models実装 (T023-T025)

**ファイル**: `src/book_converter/models.py`

以下の新規エンティティを追加:

- `MarkerType` (Enum): 目次マーカー種別
  - `TOC_START = "toc_start"` (<!-- toc -->)
  - `TOC_END = "toc_end"` (<!-- /toc -->)
  - `CONTENT_START`, `CONTENT_END`, `SKIP_START`, `SKIP_END` (Phase 4用)

- `TocEntry` (frozen dataclass): 目次エントリ
  - `text: str` - タイトルテキスト
  - `level: str` - "chapter", "section", "subsection", "other"
  - `number: str = ""` - 章番号
  - `page: str = ""` - ページ番号

- `TableOfContents` (frozen dataclass): 目次全体
  - `entries: tuple[TocEntry, ...]` - エントリタプル
  - `read_aloud: bool = False` - 読み上げ制御

**既存モデル拡張**:

- `Page` に `toc: TableOfContents | None = None` フィールド追加

### 2.2 Parser実装 (T026-T029)

**ファイル**: `src/book_converter/parser.py`

新規関数:

- `parse_toc_marker(line: str) -> MarkerType | None`
  - `<!-- toc -->` → `MarkerType.TOC_START`
  - `<!-- /toc -->` → `MarkerType.TOC_END`
  - 大文字小文字不区別、空白許容

- `parse_toc_entry(line: str) -> TocEntry | None`
  - 章パターン: `第N章 タイトル ... ページ` → level="chapter"
  - 節パターン: `N.N タイトル ... ページ` → level="section"
  - 項パターン: `N.N.N タイトル ... ページ` → level="subsection"
  - その他: `はじめに`, `おわりに` → level="other"
  - ページ番号抽出: ドットリーダー、罫線、空白区切り

**既存関数拡張**:

- `_parse_single_page_content()`: TOC収集ロジック統合
  - TOCマーカー検出時に`in_toc`フラグ制御
  - TOC内の行を`parse_toc_entry()`で解析
  - 複数ページにまたがるTOCをサポート (状態継承)
  - TOC終了ページに`TableOfContents`要素を生成

- `parse_pages_with_errors()`: 複数ページTOC対応
  - `in_toc`状態をページ境界で継承
  - `toc_entries_accumulated`でエントリを蓄積

- `parse_pages()`: 簡略版をリファクタリング
  - `parse_pages_with_errors()`を呼び出してエラーを無視

### 2.3 Transformer実装 (T030-T032)

**ファイル**: `src/book_converter/transformer.py`

新規関数:

- `transform_toc_entry(entry: TocEntry) -> Element`
  - `<entry level="chapter" number="1" title="SREとは" page="15"/>`
  - 属性: level (必須), number (任意), title (必須), page (任意)

- `transform_table_of_contents(toc: TableOfContents | None) -> Element | None`
  - `<tableOfContents>` 要素生成
  - 子要素として複数の`<entry>`を追加

**既存関数拡張**:

- `transform_page()`: TOC変換を統合
  - `page.toc`が存在する場合、`transform_table_of_contents()`を呼び出し
  - `<pageAnnouncement>`の後、`<content>`の前に配置

## 3. 修正したファイル

| ファイル | 変更内容 |
|---------|---------|
| src/book_converter/models.py | MarkerType, TocEntry, TableOfContents追加。Pageにtocフィールド追加 |
| src/book_converter/parser.py | parse_toc_marker, parse_toc_entry実装。_parse_single_page_content拡張 |
| src/book_converter/transformer.py | transform_toc_entry, transform_table_of_contents実装。transform_page拡張 |

## 4. テスト結果

### 4.1 全テストPASS

```
371 passed in 0.39s
```

**内訳**:
- 既存テスト: 295 passed (リグレッションなし)
- Phase 2新規テスト: 76 passed (RED → GREEN)

### 4.2 カバレッジ

```
book_converter module: 97% coverage (目標: ≥80%)

src/book_converter/models.py       100%
src/book_converter/parser.py        97%
src/book_converter/transformer.py   98%
```

## 5. 実装の特徴

### 5.1 複数ページTOC対応

目次が複数ページにまたがる場合、TOC状態をページ境界で継承:

```
Page 1: <!-- toc --> 第1章 ... 15
Page 2: 第2章 ... 25 <!-- /toc -->
→ Page 2に全エントリを含む<tableOfContents>を生成
```

### 5.2 柔軟なパターンマッチング

- 章番号: `第1章`, `第10章` (2桁対応)
- 節番号: `2.1`, `10.12` (2桁対応)
- 項番号: `2.1.1`
- ページ番号: ドットリーダー `...`, 罫線 `───`, 空白区切り

### 5.3 大文字小文字不区別

```python
# すべて検出される
<!-- toc -->
<!-- TOC -->
<!-- Toc -->
<!--   toc   -->  # 空白も許容
```

## 6. 次フェーズへの引き継ぎ事項

### 6.1 Phase 3 (US3) で実施

- `tableOfContents`要素に`readAloud="false"`属性追加
- 現在は属性なし (デフォルト動作)

### 6.2 Phase 4 (US4) で実施

- `<!-- content -->`, `<!-- skip -->` マーカー実装
- `Content.read_aloud`デフォルトを`False`に変更
- マーカー状態スタック管理

### 6.3 既知の制限

- TOC内のエントリは現在`readAloud`制御なし
- Phase 3で`TableOfContents.read_aloud=False`をXML出力に反映

## 7. 実装上の課題と解決

### 課題1: 複数ページTOCの扱い

**問題**: TOC状態がページ境界でリセットされる

**解決**: `parse_pages_with_errors()`で状態を継承
- `in_toc`フラグをページ間で引き継ぎ
- `toc_entries_accumulated`でエントリを蓄積
- TOC終了ページに全エントリを含む`TableOfContents`生成

### 課題2: `parse_pages()`の簡略化

**問題**: 元の`parse_pages()`は空Contentしか生成しない

**解決**: `parse_pages_with_errors()`を呼び出してエラーを無視

```python
def parse_pages(input_path: Path) -> Iterator[Page]:
    pages, _ = parse_pages_with_errors(input_path)
    yield from pages
```

## 8. アーティファクト

### 8.1 新規ファイル

- specs/004-toc-structure/tasks/ph2-output.md (このファイル)

### 8.2 変更ファイル

- src/book_converter/models.py (3エンティティ追加、1フィールド追加)
- src/book_converter/parser.py (2関数追加、3関数拡張)
- src/book_converter/transformer.py (2関数追加、1関数拡張)
- specs/004-toc-structure/tasks.md (T022-T035をチェック)

## 9. 動作確認

### 9.1 TOCマーカー検出

```python
>>> from src.book_converter.parser import parse_toc_marker
>>> from src.book_converter.models import MarkerType
>>> parse_toc_marker("<!-- toc -->")
MarkerType.TOC_START
>>> parse_toc_marker("<!-- /toc -->")
MarkerType.TOC_END
```

### 9.2 TOCエントリ解析

```python
>>> from src.book_converter.parser import parse_toc_entry
>>> entry = parse_toc_entry("第1章 SREとは ... 15")
>>> entry.text
'SREとは'
>>> entry.level
'chapter'
>>> entry.number
'1'
>>> entry.page
'15'
```

### 9.3 XML出力

```xml
<page number="1" sourceFile="page_0001.png">
  <pageAnnouncement format="simple" readAloud="false">1ページ</pageAnnouncement>
  <tableOfContents>
    <entry level="other" title="はじめに" page="1"/>
    <entry level="chapter" number="1" title="SREとは" page="15"/>
    <entry level="section" number="1.1" title="SREの定義" page="16"/>
  </tableOfContents>
  <content>
    <heading level="1">目次</heading>
  </content>
</page>
```

## 10. Status

**Phase 2: COMPLETE**

- US1 (目次マーカーによる目次認識): ✅ 完了
- US2 (章・節タイトルの構造化): ✅ 完了
- テスト: ✅ 371 passed
- カバレッジ: ✅ 97% (≥80%)

**次のステップ**: Phase 3 (US3: 目次の読み上げ制御)
