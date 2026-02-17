# Feature Specification: Converter再設計

**Feature Branch**: `009-converter-redesign`
**Created**: 2026-02-15
**Status**: Draft
**Input**: converterの仕様を再設計。tocで階層化できるはずなのに対応できていない。chapterとheaderタグの意味が重複している。使い分けを検討せねば。paragraphが正しく別れていない。md時点で問題あり？

## 背景・現状の問題点

### 問題1: TOC階層化の欠如
- 現状: TOCエントリが `level="chapter"` と `level="other"` の2種類のみ
- Episode, Column などが `level="other"` としてフラット化されている
- 本文では `# Chapter`, `## Episode` と階層構造があるのに、TOCで反映されない

### 問題2: chapter タグと heading タグの意味重複
- 現状: XMLに `<chapter number="2" title="「仕様」で失敗">` と `<heading level="1">Chapter 2 「仕様」で失敗</heading>` が二重存在
- コンテナ（chapter）とコンテンツ（heading）の役割が不明確
- 読み上げ用途では heading で十分なはず

### 問題3: paragraph が正しく分離されない
- 連続したテキストが1つの `<paragraph>` として出力
- 論理的な段落境界（空行）が無視されている
- MDファイル時点で改行が保持されていない可能性

## User Scenarios & Testing *(mandatory)*

### User Story 1 - TOC階層構造の正確な反映 (Priority: P1)

書籍の目次構造をXML出力に正確に反映させ、Chapter > Episode > Column などの階層関係を維持する。

**Why this priority**: TOC構造は書籍全体のナビゲーションの根幹であり、これが崩れると読み上げ時の章移動やブックマーク機能が正しく動作しない。

**Independent Test**: TOCを含む書籍をconverterで処理し、出力XMLのTOC要素が入力MDの見出し階層（#, ##, ###）と一致することを確認できる。

**Acceptance Scenarios**:

1. **Given** `# Chapter 1` と `## Episode 01` を含むMDファイル, **When** converterで変換, **Then** XMLのTOCに `level="1"` と `level="2"` の階層が反映される
2. **Given** CLI引数で `--header-level1=chapter --header-level2=episode|column` を指定, **When** 変換実行, **Then** 指定キーワードが正しいレベルで階層化される
3. **Given** 3階層以上のネスト（Chapter > Section > Subsection）, **When** 変換, **Then** 全階層がTOCに反映される

---

### User Story 2 - chapter/heading タグの役割明確化 (Priority: P1)

XMLタグの役割を整理し、コンテナ要素（構造）とコンテンツ要素（読み上げ対象）を明確に分離する。

**Why this priority**: タグの意味が重複していると、読み上げエンジンが二重読みしたり、構造解析ツールが混乱する原因となる。

**Independent Test**: 変換後のXMLで、構造コンテナ（chapter等）は属性でタイトルを持ち、heading要素は読み上げ専用テキストとして存在することを確認。

**Acceptance Scenarios**:

1. **Given** `# Chapter 1 タイトル` を含むMD, **When** 変換, **Then** `<chapter number="1" title="タイトル">` コンテナが生成され、内部に `<heading readAloud="true">Chapter 1 タイトル</heading>` が読み上げ専用として生成される
2. **Given** 読み上げ用途のXML, **When** パース, **Then** 構造ナビゲーションはコンテナのtitle属性を使用し、読み上げはheading要素のテキストを使用する

---

### User Story 3 - paragraph の論理的分離 (Priority: P2)

空行で区切られた段落を個別の `<paragraph>` 要素として出力し、読み上げ時の適切な間（ま）を確保する。

**Why this priority**: 段落が分離されないと、長いテキストが一気に読み上げられ、聞き手が内容を理解しにくくなる。

**Independent Test**: 空行で区切られた複数段落を持つMDを変換し、出力XMLで段落数が一致することを確認。

**Acceptance Scenarios**:

1. **Given** 3つの段落を空行で区切ったMDページ, **When** 変換, **Then** 3つの `<paragraph>` 要素が生成される
2. **Given** 段落内の改行（ソフト改行）, **When** 変換, **Then** 改行を除去し、連続テキストとして同一 `<paragraph>` 内に出力される
3. **Given** 連続する空行（2行以上）, **When** 変換, **Then** 1つの段落区切りとして扱われる

---

### User Story 4 - MD生成時の段落保持 (Priority: P2)

OCR出力からMDを生成する際に、段落境界を適切に検出・保持する。

**Why this priority**: MD時点で段落情報が失われていると、converter では復元できない。上流工程での修正が必要。

**Independent Test**: OCR処理後のMDファイルで、視覚的に分離された段落が空行で区切られていることを確認。

**Acceptance Scenarios**:

1. **Given** 段落間に視覚的スペースがあるページ画像, **When** OCR処理, **Then** MDで空行が挿入される
2. **Given** 同一段落内の行折り返し, **When** OCR処理, **Then** 空行なしで連続テキストとして出力

---

### Edge Cases

- 見出しキーワードが本文中に出現した場合（例: 「Episode 07 は...」という文）→ 行頭マッチのみを見出しとして認識
- TOCページ自体にある見出し一覧 → TOC範囲内はスキップ
- ページをまたぐ段落 → 句点「。」で終わらない段落は継続候補とし、次ページ冒頭と結合（ただし次ページが見出しで始まる場合は結合しない）

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムは、MDの見出しレベル（#, ##, ###, ####, #####）をTOCのlevel属性（1-5）に正確にマッピングしなければならない
- **FR-002**: システムは、CLI引数 `--header-level1` 〜 `--header-level5` で指定されたキーワードを対応するレベルの見出しとして認識しなければならない
- **FR-003**: 同一レベルに複数キーワードを指定可能（パイプ区切り: `episode|column`）でなければならない
- **FR-004**: XMLの構造コンテナ要素（chapter, section等）はナビゲーション用にtitle属性を持ち、heading要素は読み上げ専用テキストとして別途生成されなければならない（役割分離: 構造=コンテナ属性、読み上げ=heading要素）
- **FR-005**: 空行で区切られたテキストブロックは個別の `<paragraph>` 要素として出力されなければならない。空行とは完全な空行またはスペース/タブのみの行を含む。paragraph内部のソフト改行（無駄な改行）は除去し、連続テキストとして出力する
- **FR-006**: ページ境界で段落が継続する場合（句点で終わらず、次ページが見出しでない）、前後ページの段落を結合して1つの段落として出力しなければならない
- **FR-007**: TOC範囲（begin〜end）内のページは構造解析対象外としなければならない
- **FR-008**: ページ要素（`<page>`）とページアナウンス要素（`<pageAnnouncement>`）は廃止し、ページ情報はXMLコメント（`<!-- page N -->`）として保持しなければならない
- **FR-009**: XML出力は論理構造（book > chapter > section > paragraph/heading/figure/list）のみで構成されなければならない
- **FR-010**: MDのリスト記法（`-`, `*`, `1.`）は `<list><item>` 要素として出力されなければならない
- **FR-011**: プレースホルダーテキスト（`[図]`, `[図N]`, `[写真]`, `[表]`等）は `<figure readAloud="false" path="xxx.png">` として出力されなければならない。抽出画像はfiguresフォルダに保存される
- **FR-012**: CLI引数 `--figure-markers` で追加の図マーカーキーワードを指定可能（パイプ区切り: `イラスト|グラフ`）

### Key Entities

- **TOCEntry**: 目次エントリ。level（1-5）, number, title を持つ
- **StructureContainer**: chapter, section, subsection などの構造コンテナ。子要素（下位コンテナ、ContentElement）を含む。ページ要素は廃止
- **ContentElement**: heading, paragraph, figure, list などの読み上げ対象コンテンツ
- **List**: 箇条書き/番号付きリスト。type属性（unordered/ordered）を持ち、子要素として `<item>` を含む
- **PageComment**: XMLコメント形式（`<!-- page N -->`）で原本ページ位置を保持。読み上げ対象外

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: TOCの階層レベルがMDの見出しレベルと100%一致する
- **SC-002**: 構造コンテナとコンテンツ要素の二重表現が0件になる
- **SC-003**: 空行で区切られた段落が正しく分離され、MDの段落数とXMLの `<paragraph>` 数が一致する
- **SC-004**: 既存の書籍データ（5冊以上）で変換が正常に完了し、論理構造（chapter/section/paragraph）のみで読み上げが正常に動作する

## Assumptions

- MDファイルは `# `, `## `, `### ` などの標準Markdownヘッダー記法を使用
- 段落の区切りは空行（連続する改行）で表現される
- キーワード設定が行われない場合、デフォルトの見出し解析は行わない（設定必須）
- 読み上げ用途を主目的とし、構造ナビゲーションは副次的機能

## Clarifications

### Session 2026-02-15

- Q: 構造コンテナ（chapter等）に title 属性がある場合、heading 要素をどう扱うか？ → A: heading要素は読み上げ専用テキストとして残し、構造コンテナのtitleとは別目的で併用
- Q: ページをまたぐ段落の扱い → A: 句点「。」で終わらない段落を継続候補とし、次ページ冒頭と結合する（ただし次ページが見出しで始まる場合は結合しない）
- Q: 段落結合時のページ番号アナウンス → A: ページ要素とページアナウンスを廃止し、ページ情報はコメント（`<!-- page 42 -->`）として残す。読み上げは論理構造（chapter > section > paragraph）のみ

### Session 2026-02-16

- Q: paragraph細分化の上流責任 → A: 空行がない場合は1 paragraphとして出力。段落分離はOCR工程の責任。paragraph内の無駄な改行は除去する
- Q: 箇条書き（リスト）の扱い → A: リスト記法（`-`, `1.`）は `<list><item>` 要素として別出力
- Q: 空行の定義 → A: スペース/タブのみの行も空行として扱い、段落区切りとする
- Q: figure要素の検出と出力 → A: プレースホルダー（`[図]`, `[写真]`, `[表]`等）を検出。抽出画像はfiguresフォルダに保存し、`<figure readAloud="false" path="xxx.png">` として出力
- Q: ドキュメント整合性管理 → A: テストで検証（pytestでXML出力をdata-model/xml-schemaと照合）

## Sample Output

出力XMLの構造例（詳細スキーマは `contracts/xml-schema.md` 参照）:

### 構造概要

```xml
<book>
  <metadata>...</metadata>
  <toc>
    <entry level="1" number="1" title="Chapter Title" />
    <entry level="2" number="1" title="Episode Title" parent="1" />
  </toc>
  <front-matter>
    <!-- page N -->
    <heading readAloud="true">見出し</heading>
    <paragraph>段落テキスト</paragraph>
  </front-matter>
  <chapter number="1" title="Chapter Title">
    <heading readAloud="true">Chapter 1 Chapter Title</heading>
    <section number="1" title="Episode Title">
      <heading readAloud="true">Episode 01 Episode Title</heading>
      <paragraph>本文</paragraph>
    </section>
  </chapter>
</book>
```

### タグ役割一覧

| タグ | 役割 | 属性 |
|------|------|------|
| `<chapter>` | 構造コンテナ（ナビゲーション用） | number, title |
| `<section>` | 構造コンテナ（Episode/Column等） | number, title |
| `<heading>` | 読み上げ専用テキスト | readAloud |
| `<paragraph>` | 段落（読み上げ対象） | - |
| `<list>` | 箇条書き/番号リスト | type (unordered/ordered) |
| `<item>` | リスト項目 | - |
| `<figure>` | 図・写真・表（読み飛ばし） | readAloud, path |
| `<!-- page N -->` | ページ位置情報（コメント） | - |
