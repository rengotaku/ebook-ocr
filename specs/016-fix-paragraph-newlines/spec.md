# Feature Specification: paragraphタグの不要な改行を削除

**Feature Branch**: `016-fix-paragraph-newlines`
**Created**: 2026-02-24
**Status**: Draft
**Input**: GitHub Issue#21 - Fix: Remove unwanted newlines in paragraph tags in book.xml

## User Scenarios & Testing *(mandatory)*

### User Story 1 - book.xmlの段落テキストが正しくフォーマットされる (Priority: P1)

書籍変換を実行するユーザーとして、生成されるbook.xmlの`<paragraph>`タグ内のテキストが不要な改行を含まず、単一行の読みやすいテキストとして出力されることを期待する。

**Why this priority**: これが本Issueの唯一かつ核心的な要件。XML出力の品質に直接影響し、後続の処理（読み上げ等）に支障をきたす可能性がある。

**Independent Test**: book.mdを変換し、出力されたbook.xmlの`<paragraph>`タグ内に改行文字が含まれていないことを確認することで完全にテスト可能。

**Acceptance Scenarios**:

1. **Given** 複数行にわたるテキストを含むbook.mdファイル, **When** 変換処理を実行, **Then** 出力されるbook.xmlの`<paragraph>`タグ内のテキストは改行なしの単一行となる
2. **Given** 行末・行頭に余分な空白を含むテキスト, **When** 変換処理を実行, **Then** 連続する空白は単一のスペースに正規化される

---

### Edge Cases

- 空のパラグラフ（空白のみの行）の場合、空文字列またはスペースのみのテキストとして処理される
- 日本語と英語が混在するテキストでも、不要な改行は削除される
- 強調タグ（emphasis）を含むテキストでも、改行削除処理は正常に動作する

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムは `parse_paragraph` 関数において、複数行のテキストを結合する際に改行文字（`\n`）ではなくスペースで結合しなければならない
- **FR-002**: システムは結合後のテキストに含まれる連続する空白文字を単一のスペースに正規化しなければならない
- **FR-003**: システムは既存の `parse_paragraph_lines` 関数と同等のテキスト正規化ロジックを `parse_paragraph` 関数に適用しなければならない

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: book.xmlの`<paragraph>`タグ内に改行文字（`\n`）が含まれないこと
- **SC-002**: 変換処理において既存のテスト（存在する場合）がすべてパスすること
- **SC-003**: 複数行テキストの変換結果が「スペース区切りの単一行」として出力されること

## Assumptions

- 修正対象は `src/book_converter/parser/paragraph.py` の `parse_paragraph` 関数のみ
- 同ファイル内の `parse_paragraph_lines` 関数（10-42行目）が正しい参照実装として存在する
- 修正は2-3行程度の軽微な変更
- 後方互換性への影響はない（改行文字はもともと意図しない出力）
