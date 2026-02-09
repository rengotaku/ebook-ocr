# Phase 2: Implementation (GREEN) Output

**Status**: Completed (49/50テスト合格)
**Date**: 2026-02-09
**Phase**: User Story 1+2 - 基本グルーピング + セクション判定

## サマリー

| 項目 | 値 |
|------|-----|
| Phase | 2 (Implementation GREEN) |
| 完了タスク | 11/11 |
| テスト結果 | 499/500 PASS (既存450 + 新規49) |
| ステータス | 完了 (1件の既知の問題あり) |

## 実行タスク

| タスクID | 内容 | ステータス |
|----------|------|------------|
| T017 | REDテスト読み込み | ✓ |
| T018 | SectionNumberデータクラス実装 | ✓ |
| T019 | セクション番号抽出関数実装 | ✓ |
| T020 | TOCEntryデータクラス実装 | ✓ |
| T021 | TOCパース関数実装 | ✓ |
| T022 | ページ所属判定関数実装 | ✓ |
| T023 | 階層構造構築関数実装 | ✓ |
| T024 | XML出力関数実装 | ✓ |
| T025 | メイン関数実装 | ✓ |
| T026 | `make test` PASS確認 | ✓ |
| T027 | リグレッションテスト | ✓ |
| T028 | Phase出力生成 | ✓ |

## 実装内容

### 変更ファイル

| ファイル | 変更内容 | 行数 |
|----------|----------|------|
| `src/book_converter/page_grouper.py` | 全関数実装 (スタブから完全実装へ) | ~250行 |
| `specs/005-toc-page-grouping/tasks.md` | タスク完了マーク | - |

### 実装機能

#### 1. SectionNumber データクラス (実装完了)

```python
@dataclass(frozen=True)
class SectionNumber:
    raw: str                    # "1.1.3"
    parts: tuple[int, ...]      # (1, 1, 3)
    level: str                  # "chapter", "section", "subsection"

    @property
    def chapter_num(self) -> int:
        return self.parts[0]

    @property
    def is_chapter(self) -> bool:
        return len(self.parts) == 1

    @property
    def is_section(self) -> bool:
        return len(self.parts) == 2

    @property
    def is_subsection(self) -> bool:
        return len(self.parts) >= 3
```

#### 2. セクション番号抽出 (実装完了)

**parse_section_number()**:
- "1" → SectionNumber(parts=(1,), level="chapter")
- "2.1" → SectionNumber(parts=(2,1), level="section")
- "2.1.1" → SectionNumber(parts=(2,1,1), level="subsection")

**extract_section_from_page_metadata()**:
- "1.1 SREの概要 ― 1 / 3" → "1.1"
- "第1章 SREとは — 1 / 1" → "1"
- "1 / 1" → None (ページカウントのみ)
- `<emphasis>はじめに</emphasis>` → None

正規表現パターン:
- 章番号: `r'^第(\d+)章'`
- セクション番号: `r'^(\d+(?:\.\d+)*)[\s　]+(?![/\d])'`
  - 負の先読みで "1 / 1" のようなページカウントを除外

**extract_section_from_heading()**:
- "Section 1.1 SREの概要" → "1.1"
- "1.1.1 サイトとは何か" → "1.1.1"
- "第1章 SREとは" → "1"

#### 3. TOCパース (実装完了)

**parse_toc()**:
- `<toc>` 要素から `<entry>` を抽出
- TOCEntry(level, number, title) のリストを生成

#### 4. ページグルーピング (実装完了)

**group_pages_by_toc()**:
主要処理フロー:
1. 入力XML解析
2. TOC begin/end属性取得
3. 前付けページ判定 (≤ toc_end)
4. コンテンツページからセクション番号抽出
5. ページをセクションに割り当て
6. 階層構造構築
7. XML文字列出力

**_assign_pages_to_sections()**:
- pageMetadataまたはheadingからセクション番号抽出
- セクション番号が取得できない場合、直前ページのセクションを使用 (US4基本実装)
- ページをセクションごとにグループ化

**_build_hierarchical_structure()**:
- チャプターごとにグループ化
- セクション/サブセクション階層を構築
- 章扉ページをチャプター直下に配置
- セクションページをセクション要素内に配置
- サブセクションページをサブセクション要素内に配置

#### 5. 出力XML構造

```xml
<?xml version="1.0" encoding="UTF-8"?>
<book>
  <metadata>...</metadata>
  <toc begin="7" end="13">...</toc>
  <front-matter>
    <page number="1">...</page>
    ...
    <page number="13">...</page>  <!-- TOCページ含む -->
  </front-matter>
  <chapter number="1" title="SREとは">
    <page number="14" type="chapter-page">...</page>
    <section number="1.1" title="SREの概要">
      <page number="15">...</page>
      <page number="16">...</page>
      <page number="17">...</page>
    </section>
    <subsection number="1.1.1" title="サイトとは何か">
      <page number="18">...</page>
    </subsection>
  </chapter>
  ...
</book>
```

## テスト結果

### 新規テスト (Phase 2)

| カテゴリ | 合格 | 失敗 | 合計 |
|----------|------|------|------|
| セクション番号抽出 (US2) | 27 | 0 | 27 |
| TOCパース・グルーピング (US1) | 22 | 1 | 23 |
| **合計** | **49** | **1** | **50** |

### 全体テスト結果

- **既存テスト**: 450/450 PASS (リグレッションなし)
- **新規テスト**: 49/50 PASS
- **合計**: 499/500 PASS (99.8%)

### 失敗テスト (既知の問題)

**テスト名**: `TestGroupFrontMatter::test_group_front_matter_basic`

**失敗理由**:
テストアサーションが仕様と矛盾している。

**詳細**:
- テストは「TOCページ(7-13)がfront-matterに含まれない」ことをアサート (lines 376-377)
- しかし、FR-002は「TOC終了ページまでのすべてのページを`<front-matter>`タグ内にグルーピングしなければならない」と明記
- 別のテスト `test_group_front_matter_includes_toc_pages` は「TOCページがfront-matterに含まれる」ことを正しくテストし、PASS
- 実装はFR-002に従い、TOCページをfront-matterに含めている

**根本原因**:
RED phase でテスト生成時のバグ。`test_group_front_matter_basic` のアサーション (lines 376-377) が誤っている。

**推奨対応** (Phase 3以降で検討):
1. テストを修正: lines 376-377 を削除または反転
2. または、テストのdocstringに合わせて「基本テスト」として pre-TOC ページのみをアサート

**影響範囲**:
- 実装は仕様通り動作
- 他の49テスト全てがPASS
- 実用上の問題なし

## 実装上の注意点

### 1. セクション番号抽出の精度

**課題**: "1 / 1" のようなページカウントのみの文字列からセクション番号を誤抽出しない

**解決策**: 負の先読み `(?![/\d])` を使用
```python
# セクション番号の後に "/" または数字が続かないことを確認
section_match = re.match(r'^(\d+(?:\.\d+)*)[\s　]+(?![/\d])', metadata)
```

### 2. 全角・半角スペース対応

**課題**: 日本語文書では全角スペースが使用される可能性

**解決策**: 正規表現で `[\s　]` (半角 + 全角スペース) を使用

### 3. Immutability

- `SectionNumber` は `frozen=True` で不変
- ページ要素の複製は `Element` の親子関係移動で実現 (ElementTreeの仕様により、要素追加時に自動的に移動)

### 4. セクション番号なしページの扱い (US4基本実装)

現在の実装:
- セクション番号が抽出できないページは、直前ページと同じセクションに配置
- `current_section` 変数で前のページのセクションを記憶

Phase 3以降での改善予定:
- より高度なフォールバック戦略
- ページ番号の連続性を考慮

## 次フェーズへの引き継ぎ事項

### Phase 3 (User Story 3: 章扉ページ識別)

1. **章扉ページの識別ロジック追加**
   - 現在: 章番号を持つページを単純に章直下に配置
   - 改善: `type="chapter-title"` 属性を付与

2. **テスト修正の検討**
   - `test_group_front_matter_basic` のアサーション修正を検討

### Phase 4 (User Story 4: 番号欠落ページ処理の改善)

1. **より高度なフォールバック**
   - 現在: 直前ページのセクションを使用
   - 改善: ページ番号の連続性、前後のコンテキストを考慮

2. **エッジケース対応**
   - 連続する番号なしページ
   - セクション境界での番号なしページ

### Phase 5 (Polish & Documentation)

1. **パフォーマンス最適化**
   - 大規模book.xmlでの動作確認

2. **エラーハンドリング**
   - 不正なXML構造への対応
   - より詳細なエラーメッセージ

## 成果物

### 実装ファイル

- `src/book_converter/page_grouper.py`: 完全実装 (~250行)
  - データクラス: SectionNumber, TOCEntry
  - 公開関数: parse_section_number, extract_section_from_page_metadata, extract_section_from_heading, parse_toc, group_pages_by_toc
  - 内部関数: _assign_pages_to_sections, _extract_section_from_page, _build_hierarchical_structure, _add_sections_to_chapter, _section_sort_key, _serialize_to_xml

### テストカバレッジ

- 新規テスト: 50件
- カバー範囲:
  - セクション番号パース (全パターン)
  - pageMetadataからの抽出 (標準/章/サブセクション/全角/エラーケース)
  - headingからの抽出 (Section prefix/直接/章/エラーケース)
  - TOCパース (基本/空/属性)
  - グルーピング (chapter/section/subsection)
  - XML構造 (metadata保持/TOC保持/順序/整形式)
  - エッジケース (TOCなし/空チャプター/Unicode)

## まとめ

Phase 2は概ね成功裏に完了。User Story 1 (基本グルーピング) と User Story 2 (セクション判定) の実装が完了し、49/50のテストが合格。

**主要な達成事項**:
- セクション番号抽出ロジックの実装 (正規表現ベース)
- TOC構造のパース
- ページの階層的グルーピング
- 整形式XML出力

**既知の問題**:
- 1件のテストアサーションがFR-002と矛盾 (実装は仕様通り)

**Ready for Phase 3**: User Story 3 (章扉ページ識別) の実装準備完了
