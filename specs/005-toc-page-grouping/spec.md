# Feature Specification: TOC構造を利用したpageタグのグルーピング

**Feature Branch**: `005-toc-page-grouping`
**Created**: 2026-02-09
**Status**: Draft
**Input**: GitHub Issue #4 - TOC構造を利用したpageタグのグルーピング実装

## 概要

`book.xml`の`<toc>`タグに含まれる目次情報を利用して、フラットに並んでいる`<page>`タグを`<chapter>`, `<section>`, `<subsection>`タグで階層的にグルーピングする機能を実装する。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 基本的なページグルーピング (Priority: P1)

ユーザーがbook.xmlを処理すると、各ページが適切な章・節・項の階層構造内に配置される。TOC終了までのページは前付け（front-matter）としてグルーピングされ、それ以降のページはTOCエントリに基づいて章・節・項にグルーピングされる。

**Why this priority**: 機能の核心部分。これがなければ階層構造のXMLを生成できない。

**Independent Test**: 単一のbook.xmlを入力として与え、出力XMLが正しい階層構造を持つことを検証できる。

**Acceptance Scenarios**:

1. **Given** TOC情報を含むbook.xmlがある, **When** グルーピング処理を実行する, **Then** TOC終了ページまでが`<front-matter>`タグ内に配置される
2. **Given** chapter 1が定義されたTOCがある, **When** グルーピング処理を実行する, **Then** chapter 1に属するページが`<chapter number="1">`タグ内に配置される
3. **Given** section 1.1が定義されたTOCがある, **When** グルーピング処理を実行する, **Then** section 1.1に属するページが`<section number="1.1">`タグ内に配置される

---

### User Story 2 - ページ所属セクションの自動判定 (Priority: P1)

各ページがどのセクションに属するかを、pageMetadataやheadingタグの内容から自動的に判定する。例えば「2.1 SLOを理解する — 2 / 7」というpageMetadataからsection 2.1への所属を判定する。

**Why this priority**: グルーピングの正確性を決定する重要なロジック。

**Independent Test**: 様々なpageMetadataパターンを持つページに対して、正しいセクション番号が抽出されることを検証できる。

**Acceptance Scenarios**:

1. **Given** pageMetadataに「2.1 SLOを理解する — 2 / 7」を持つページがある, **When** セクション判定を実行する, **Then** section 2.1に所属すると判定される
2. **Given** headingに「Section 1.1」を持つページがある, **When** セクション判定を実行する, **Then** section 1.1に所属すると判定される
3. **Given** pageMetadataに「1.1.3 信頼性を制御する — 2 / 3」を持つページがある, **When** セクション判定を実行する, **Then** subsection 1.1.3に所属すると判定される

---

### User Story 3 - 章扉ページの識別 (Priority: P2)

章の最初のページ（章扉ページ）を識別し、`type="chapter-title"`属性を付与する。章扉ページは通常、章番号と章タイトルのみを含む。

**Why this priority**: 章扉ページの特別な扱いは読み上げやナビゲーションに有用だが、基本的なグルーピングには必須ではない。

**Independent Test**: 章扉ページを含むbook.xmlを処理し、該当ページにtype属性が付与されることを検証できる。

**Acceptance Scenarios**:

1. **Given** 「第1章 SREとは」のみを含むページがある, **When** グルーピング処理を実行する, **Then** そのページに`type="chapter-title"`属性が付与される

---

### User Story 4 - 番号情報欠落ページの処理 (Priority: P2)

セクション番号を抽出できないページについても、前後のページの所属情報から推測して適切な位置に配置する。

**Why this priority**: 実際のデータには番号情報が欠落したページが存在する可能性があり、それらも適切に処理する必要がある。

**Independent Test**: セクション番号情報がないページを含むbook.xmlを処理し、前後のコンテキストから適切な位置に配置されることを検証できる。

**Acceptance Scenarios**:

1. **Given** セクション番号情報がないページがsection 1.1のページの間に存在する, **When** グルーピング処理を実行する, **Then** そのページはsection 1.1に配置される
2. **Given** 連続して番号情報がないページが存在する, **When** グルーピング処理を実行する, **Then** 直前のセクションに属するものとして配置される

---

### Edge Cases

- 複数セクションの内容が1ページに混在する場合 → 最初に登場するセクション番号に基づいて配置
- subsectionに直接属するページがない場合 → 空のsubsectionタグを生成（子要素なし）
- TOCに記載されているがページが存在しないセクション → 空のタグを生成
- ページ番号が連続していない場合 → 欠番は無視し、存在するページのみ処理

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムは`<toc>`タグのbegin/end属性を読み取り、前付け範囲を特定できなければならない
- **FR-002**: システムはTOC終了ページまでのすべてのページを`<front-matter>`タグ内にグルーピングしなければならない
- **FR-003**: システムは`<toc>`内の各`<entry>`の`level`属性（chapter/section/subsection）を解釈しなければならない
- **FR-004**: システムはpageMetadataの内容からセクション番号を正規表現`^(\d+(?:\.\d+)*)[\s　]`で抽出できなければならない
- **FR-005**: システムはheadingタグの内容から「Section X.X」形式のセクション番号を抽出できなければならない
- **FR-006**: システムは抽出したセクション番号に基づいて、ページを適切なchapter/section/subsectionタグ内に配置しなければならない
- **FR-007**: システムは章扉ページを識別し、`type="chapter-title"`属性を付与しなければならない
- **FR-008**: システムはセクション番号を抽出できないページを、直前のページと同じセクションに配置しなければならない
- **FR-009**: システムは元のページの属性と子要素をすべて保持したまま、新しい階層構造に配置しなければならない
- **FR-010**: システムは出力XMLが整形式（well-formed）であることを保証しなければならない

### Key Entities

- **Page**: ページ要素。number属性、sourceFile属性、各種子要素（content, pageMetadata等）を持つ
- **TOC Entry**: 目次エントリ。level（chapter/section/subsection）、number、title属性を持つ
- **Section Number**: X.X.X形式のセクション識別子。chapterは単一数字、sectionはX.X、subsectionはX.X.X

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: すべてのページが適切な階層構造（front-matter/chapter/section/subsection）内に配置される
- **SC-002**: 処理後のXMLが整形式であり、元のページ情報（属性・子要素）が100%保持される
- **SC-003**: pageMetadataまたはheadingから95%以上のページでセクション番号が正しく抽出される
- **SC-004**: 章扉ページの90%以上が正しく識別され、type属性が付与される
- **SC-005**: 処理時間は1000ページのbook.xmlに対して10秒以内

## Assumptions

- 入力XMLは整形式であり、`<book>`をルート要素とする
- `<toc>`タグは`<book>`直下に1つのみ存在する
- TOCのbegin/end属性は正確なページ番号を示す
- ページ番号は1から始まる連番だが、欠番がある可能性がある
- セクション番号は階層的（例: chapter 1 → section 1.1 → subsection 1.1.1）
- 章扉ページは章番号・章タイトル以外のコンテンツをほとんど含まない
