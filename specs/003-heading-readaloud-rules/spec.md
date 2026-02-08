# Feature Specification: heading要素へのreadAloud属性付与ルール

**Feature Branch**: `003-heading-readaloud-rules`
**Created**: 2026-02-08
**Status**: Draft
**Input**: Issue #1 - feat: heading要素へのreadAloud属性付与ルール実装

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 繰り返し柱の自動除外 (Priority: P1)

TTSで書籍を聴く際、各ページに繰り返し出現する柱（ランニングヘッド）やページ番号表記が読み上げられず、本文コンテンツのみが音声出力される。

**Why this priority**: 柱は最も高頻度（124回）で出現し、毎ページ同じ内容が読み上げられるとユーザー体験が著しく低下する。最初に解決すべき最重要課題。

**Independent Test**: 任意のページをTTSで読み上げ、書籍タイトル（柱）やページ番号表記が音声に含まれないことを確認できる。

**Acceptance Scenarios**:

1. **Given** 書籍タイトル「SREの知識地図」が柱として各ページに出現するXML, **When** TTS変換処理を実行, **Then** 柱headingに`readAloud="false"`が付与され、読み上げ対象外となる
2. **Given** ページ番号表記「1.1.1 SREの概要 — 1 / 3」形式のheading, **When** TTS変換処理を実行, **Then** 該当headingに`readAloud="false"`が付与される
3. **Given** ユニークなコンテンツ見出し「なぜSREが重要なのか」, **When** TTS変換処理を実行, **Then** `readAloud`属性は付与されない（デフォルトで読み上げ対象）

---

### User Story 2 - 装飾・区切り記号の除外 (Priority: P2)

TTS読み上げ時に、装飾記号（◆◆◆）や章節ラベル（Section X.X）などの構造マーカーが音声出力されず、コンテンツの流れが自然になる。

**Why this priority**: 装飾記号は意味を持たない視覚的要素であり、読み上げると「しかく、しかく、しかく」のような不自然な音声になる。章節ラベルも同様に構造情報であり本文ではない。

**Independent Test**: 装飾記号や章節ラベルを含むページをTTSで読み上げ、これらが音声に含まれないことを確認できる。

**Acceptance Scenarios**:

1. **Given** 「◆◆◆」装飾記号のheading, **When** TTS変換処理を実行, **Then** `readAloud="false"`が付与される
2. **Given** 「Section 3.2」形式の章節ラベル, **When** TTS変換処理を実行, **Then** `readAloud="false"`が付与される
3. **Given** 「3.2.1 モニタリングの基本」のような本文見出し, **When** TTS変換処理を実行, **Then** `readAloud`属性は付与されない

---

### User Story 3 - 参照・メタ情報の除外 (Priority: P3)

TTS読み上げ時に、Webサイト参照リンク表記や脚注番号などのメタ情報が本文から分離され、必要に応じて読み上げ制御できる。

**Why this priority**: これらは補足情報であり、本文の流れを妨げる。ただし完全除外ではなく、オプションで読み上げ可能にしたいユーザーもいる可能性がある。

**Independent Test**: 「Webサイト」や「注3.1」を含むページをTTSで読み上げ、デフォルトでは読み上げられないことを確認できる。

**Acceptance Scenarios**:

1. **Given** 「Webサイト」参照表記のheading, **When** TTS変換処理を実行, **Then** `readAloud="false"`が付与される
2. **Given** 「注3.1」形式の脚注番号heading, **When** TTS変換処理を実行, **Then** `readAloud="false"`が付与される

---

### Edge Cases

- 柱テキストが書籍ごとに異なる場合、どのように検出するか？ → 最頻出のheading level="1"を柱として自動検出
- 柱テキストに表記揺れがある場合（「——」vs「――」）→ 正規化または類似度判定で同一視
- 柱テキストがlevel 2, 3として出現している場合 → levelを1に再配置してから柱として処理
- 新しいパターンが追加された場合の拡張性 → パターンリストを外部化し設定可能に
- パターンに誤マッチした場合のユーザー体験 → 偽陽性は少数であればTTS体験への影響は軽微

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムは、書籍内で最も高頻度に出現するheading level="1"を「柱（ランニングヘッド）」として自動検出しなければならない
- **FR-002**: システムは、検出した柱パターンに一致するheadingに`readAloud="false"`属性を付与しなければならない
- **FR-003**: システムは、ページ番号表記パターン（`X.X.X ... — N/M`形式）に一致するheadingに`readAloud="false"`属性を付与しなければならない
- **FR-004**: システムは、装飾記号パターン（`◆◆◆`等）に一致するheadingに`readAloud="false"`属性を付与しなければならない
- **FR-005**: システムは、章節ラベルパターン（`Section X.X`形式）に一致するheadingに`readAloud="false"`属性を付与しなければならない
- **FR-006**: システムは、参照表記パターン（`Webサイト`、`注X.X`形式）に一致するheadingに`readAloud="false"`属性を付与しなければならない
- **FR-007**: システムは、上記パターンに一致しないheadingには`readAloud`属性を付与せず、デフォルト（読み上げ対象）のままにしなければならない
- **FR-008**: システムは、柱検出のための閾値（出現回数）を設定可能にしなければならない（デフォルト: 総ページ数の50%以上）
- **FR-009**: システムは、除外パターンをユーザーが追加・編集可能な形式で管理しなければならない
- **FR-010**: システムは、検出した柱テキストがlevel 1以外（level 2, 3）で出現している場合、そのheadingのlevelを1に再配置（修正）しなければならない

### Key Entities

- **ExclusionPattern**: 除外対象を定義するパターン（正規表現、優先度、説明）
- **HeadingAnalysis**: heading要素の出現頻度分析結果（テキスト、レベル、出現回数）
- **ReadAloudRule**: readAloud属性付与ルール（パターンID、付与値、適用条件）

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 繰り返し柱（出現回数上位）の95%以上に`readAloud="false"`が正しく付与される
- **SC-002**: ユニークなコンテンツ見出しの誤除外率（偽陽性）が1%未満である
- **SC-003**: 既存のテストスイートが100%パスする（リグレッションなし）
- **SC-004**: 変換処理時間が現行比10%以内の増加に収まる
- **SC-005**: ユーザーがパターンを追加した場合、次回変換から即座に反映される

## Assumptions

- 柱は通常、heading level="1"として最も高頻度に出現するが、OCRやマークアップの揺れにより level 2, 3 として出現することもある（その場合はlevel 1に再配置）
- ページ番号表記は「— N / M」または「― N / M」形式で統一されている
- 装飾記号は「◆◆◆」のような連続した記号で構成される
- 書籍ごとにパターンが異なる可能性があるため、設定のカスタマイズは必須
- 表記揺れ（ダッシュの種類等）は正規表現で吸収可能

## Clarifications

### Session 2026-02-08

- Q: 同一のランニングヘッドテキストがlevel 1以外にも出現する場合、どう処理すべきか？ → A: level="1"のみを柱検出対象とする。ただし、検出した柱テキストがlevel 2,3に出現している場合は、そのheadingのlevelを1に再配置（修正）する。

## Related

- Issue: https://github.com/rengotaku/ebook-ocr/issues/1
- User Story 3 (002-book-md-structure): TTS図表説明制御とメタデータ分離
- FR-004, FR-005 (002-book-md-structure): readAloud属性制御
