# Feature Specification: 目次情報の保持

**Feature Branch**: `004-toc-structure`
**Created**: 2026-02-08
**Status**: Draft
**Input**: User description: "目次情報の保持"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 目次マーカーによる目次認識 (Priority: P1)

書籍のMarkdownファイル（book.md）を変換する際、ユーザーは目次ページを `<!-- toc -->` ... `<!-- /toc -->` マーカーで囲むことで、システムに目次として認識させることができる。これにより、目次は通常のコンテンツとは異なる構造化されたXML要素として出力される。

**Why this priority**: 目次認識がなければ、後続の章タイトル構造化や読み上げ制御が実現できない。すべての機能の基盤となる。

**Independent Test**: book.mdに `<!-- toc -->` マーカーを追加し、変換後のXMLに `<tableOfContents>` 要素が生成されることを確認できる。

**Acceptance Scenarios**:

1. **Given** book.mdに `<!-- toc -->` と `<!-- /toc -->` で囲まれたテキストがある, **When** 変換を実行する, **Then** XMLに `<tableOfContents>` 要素が生成される
2. **Given** book.mdに目次マーカーがない, **When** 変換を実行する, **Then** XMLに `<tableOfContents>` 要素は生成されない（既存動作を維持）
3. **Given** 目次マーカーが複数ページにまたがる, **When** 変換を実行する, **Then** 最初のマーカーから最後のマーカーまでの内容が1つの目次として処理される

---

### User Story 2 - 章・節タイトルの構造化 (Priority: P1)

目次マーカー内のテキストから、章（第N章）、節（N.N）、項（N.N.N）のパターンを自動認識し、階層構造を持った目次エントリとして出力する。各エントリにはタイトルとページ番号が含まれる。

**Why this priority**: 目次の構造化は本機能の核心であり、単なるテキストではなく意味のあるデータとして保持することで、後続処理（読み上げ、ナビゲーション等）が可能になる。

**Independent Test**: 「第1章 SREとは ... 15」のような目次行を含むbook.mdを変換し、`<entry level="chapter" number="1" title="SREとは" page="15"/>` が生成されることを確認できる。

**Acceptance Scenarios**:

1. **Given** 「第1章 タイトル」形式のテキストがある, **When** 目次を解析する, **Then** level="chapter"、適切なnumber、titleが抽出される
2. **Given** 「2.1 セクションタイトル」形式のテキストがある, **When** 目次を解析する, **Then** level="section"、number="2.1"、titleが抽出される
3. **Given** 「2.1.1 サブセクション」形式のテキストがある, **When** 目次を解析する, **Then** level="subsection"、number="2.1.1"、titleが抽出される
4. **Given** タイトルの後に「... 15」や「─── 15」のようなページ番号がある, **When** 目次を解析する, **Then** page="15"が抽出される

---

### User Story 3 - 目次の読み上げ制御 (Priority: P2)

目次要素には `readAloud="false"` 属性がデフォルトで設定され、読み上げソフトウェアが目次を読み上げないよう制御できる。

**Why this priority**: 目次は構造情報として保持するが、音声読み上げ時にすべてのエントリを読み上げるのは冗長であるため、デフォルトで読み上げをスキップする。

**Independent Test**: 変換後のXMLで `<tableOfContents readAloud="false">` となっていることを確認できる。

**Acceptance Scenarios**:

1. **Given** 目次マーカーで囲まれたテキストがある, **When** 変換を実行する, **Then** `<tableOfContents>` 要素に `readAloud="false"` 属性が設定される

---

### User Story 4 - コンテンツ範囲マーカーによる読み上げ制御 (Priority: P2)

ユーザーは `<!-- content -->` ... `<!-- /content -->` マーカーで読み上げ対象範囲を、`<!-- skip -->` ... `<!-- /skip -->` マーカーで読み上げ非対象範囲を明示できる。マーカーで囲まれていない部分はデフォルトで読み上げ非対象となる。

**Why this priority**: 索引、参考文献、奥付など読み上げ不要な部分をスキップし、本文のみを読み上げ対象とすることで、音声読み上げの品質が向上する。

**Independent Test**: `<!-- content -->`で囲まれた部分のみが`readAloud="true"`となり、それ以外が`readAloud="false"`となることを確認できる。

**Acceptance Scenarios**:

1. **Given** `<!-- content -->` ... `<!-- /content -->` で囲まれたテキストがある, **When** 変換を実行する, **Then** 該当範囲の要素に `readAloud="true"` が設定される
2. **Given** `<!-- skip -->` ... `<!-- /skip -->` で囲まれたテキストがある, **When** 変換を実行する, **Then** 該当範囲の要素に `readAloud="false"` が設定される
3. **Given** マーカーで囲まれていないテキストがある, **When** 変換を実行する, **Then** 該当範囲の要素に `readAloud="false"` が設定される（デフォルト動作）

---

### Edge Cases

- 目次マーカーが開始のみで終了がない場合 → ページ終端まで、または次のページマーカーまでを目次として処理
- 章番号のない目次エントリ（「はじめに」「おわりに」等） → level="other"、number=""として処理
- ページ番号がない目次エントリ → page=""（空文字）として処理
- 目次エントリのパターンに一致しない行 → 無視（目次エントリとして出力しない）
- contentマーカーとskipマーカーがネストしている場合 → 内側のマーカーが優先
- contentマーカーが開始のみで終了がない場合 → ページ終端または次のマーカーまでを対象範囲として処理

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムは `<!-- toc -->` マーカーを目次開始として認識しなければならない
- **FR-002**: システムは `<!-- /toc -->` マーカーを目次終了として認識しなければならない
- **FR-003**: システムは目次マーカー間のテキストから章・節・項のパターンを抽出しなければならない
- **FR-004**: システムは抽出した目次情報を `<tableOfContents>` XML要素として出力しなければならない
- **FR-005**: システムは各目次エントリを `<entry>` 要素として出力し、level、number、title、page属性を含めなければならない
- **FR-006**: システムは `<tableOfContents>` 要素に `readAloud="false"` 属性をデフォルトで設定しなければならない
- **FR-007**: 目次マーカーがない場合、システムは既存の動作を維持しなければならない（後方互換性）
- **FR-008**: 目次エントリのlevelは以下の値をサポートしなければならない：chapter、section、subsection、other
- **FR-009**: システムは `<!-- content -->` マーカーを読み上げ対象範囲の開始として認識しなければならない
- **FR-010**: システムは `<!-- /content -->` マーカーを読み上げ対象範囲の終了として認識しなければならない
- **FR-011**: システムは `<!-- skip -->` マーカーを読み上げ非対象範囲の開始として認識しなければならない
- **FR-012**: システムは `<!-- /skip -->` マーカーを読み上げ非対象範囲の終了として認識しなければならない
- **FR-013**: マーカーで囲まれていない範囲は、デフォルトで読み上げ非対象（readAloud="false"）としなければならない

### Key Entities

- **TableOfContents**: 目次全体を表すエンティティ。複数のTocEntryを持ち、読み上げ制御属性を持つ
- **TocEntry**: 目次の1エントリ。レベル（chapter/section/subsection/other）、番号、タイトル、ページ番号を持つ

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 目次マーカーで囲まれたテキストが100%正確に目次として認識される
- **SC-002**: 「第N章」「N.N」「N.N.N」形式の目次エントリが95%以上正確に解析される
- **SC-003**: 既存のbook.md変換が目次マーカーなしで100%互換性を維持する
- **SC-004**: 変換後のXMLがXSDスキーマに対して100%検証を通過する

## Assumptions

- 目次マーカーは手動でbook.mdに追加される（自動検出は行わない）
- 目次エントリのページ番号は必須ではない（空でも許容）
- 「第N章」形式は日本語書籍の標準的な章番号形式として扱う
- 節番号（N.N）は最大3レベル（N.N.N）までサポートする

## Clarifications

### Session 2026-02-08

- Q: 目次マーカーを追加するタイミングは？ → A: book.md生成後に手動で追加（book.txt → book.md → book.xml パイプラインのbook.md編集時）
- Q: 手動追加の運用は煩雑にならないか？ → A: 手動追加で許容（目次は1〜数ページのみで1回限りの作業、既存の編集フローに統合）
- Q: コンテンツ範囲マーカーの目的は？ → A: 読み上げ対象/非対象の範囲指定（索引、参考文献、奥付などをスキップ）
- Q: コンテンツ範囲マーカーの構文は？ → A: `<!-- content -->` / `<!-- skip -->` 形式（目次マーカーと統一）
- Q: マーカーなし部分のデフォルト動作は？ → A: デフォルトは読み上げ非対象（`<!-- content -->` で明示が必要）

## Pipeline Integration

本機能は既存パイプラインの `book.md → book.xml` 変換フェーズ（book_converterモジュール）で処理される。

```
video → ... → book.txt → book.md → [目次マーカー手動追加] → book.xml
                           ↑                                    ↑
                      VLM処理                            book_converter
                                                        （本機能の対象）
```

**運用フロー**:
1. パイプライン実行で `book.md` が生成される
2. ユーザーが `book.md` を編集し、以下のマーカーを追加：
   - 目次ページ: `<!-- toc -->` ... `<!-- /toc -->`
   - 本文（読み上げ対象）: `<!-- content -->` ... `<!-- /content -->`
   - 索引・参考文献等（読み上げスキップ）: `<!-- skip -->` ... `<!-- /skip -->`
3. `make converter` で `book.xml` を生成

**マーカー一覧**:
| マーカー | 用途 | readAloud |
|---------|------|-----------|
| `<!-- toc -->` | 目次範囲 | false |
| `<!-- content -->` | 読み上げ対象範囲 | true |
| `<!-- skip -->` | 読み上げ非対象範囲 | false |
| (マーカーなし) | デフォルト | false |
