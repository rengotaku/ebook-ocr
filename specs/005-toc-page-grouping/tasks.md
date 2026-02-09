# Tasks: TOC構造を利用したpageタグのグルーピング

**Input**: Design documents from `/specs/005-toc-page-grouping/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: TDD必須。各User Storyフェーズは Test Implementation (RED) → Implementation (GREEN) → Verification のワークフローに従う。

**Organization**: タスクはUser Story単位でグループ化され、各ストーリーを独立して実装・テスト可能。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 依存なし（異なるファイル、実行順序自由）
- **[Story]**: タスクが属するUser Story (例: US1, US2)
- 説明に正確なファイルパスを含める

## User Story Summary

| ID | Title | Priority | FR | Scenario |
|----|-------|----------|----|----------|
| US1 | 基本的なページグルーピング | P1 | FR-001,002,003,006,009,010 | TOC→front-matter、chapter/section/subsectionへの配置 |
| US2 | ページ所属セクションの自動判定 | P1 | FR-004,005 | pageMetadata/headingからセクション番号抽出 |
| US3 | 章扉ページの識別 | P2 | FR-007 | type="chapter-title"属性付与 |
| US4 | 番号情報欠落ページの処理 | P2 | FR-008 | 直前ページのセクションに配置 |

## Path Conventions

```text
src/book_converter/
├── page_grouper.py    # NEW: メイングルーピングモジュール
├── models.py          # 既存: 必要に応じて拡張
└── cli.py             # 既存: --group-pages オプション追加

tests/book_converter/
└── test_page_grouper.py  # NEW: グルーピングテスト
```

---

## Phase 1: Setup（既存コード確認） — NO TDD

**Purpose**: 既存実装の確認、変更箇所の特定、テストデータ準備

- [ ] T001 既存実装を確認: src/book_converter/models.py
- [ ] T002 [P] 既存実装を確認: src/book_converter/xml_builder.py
- [ ] T003 [P] 既存実装を確認: src/book_converter/cli.py
- [ ] T004 [P] 既存テストを確認: tests/book_converter/
- [ ] T005 テスト用XMLデータの構造を確認: output/4fd5500620491ebe/book.xml
- [ ] T006 Phase出力を生成: specs/005-toc-page-grouping/tasks/ph1-output.md

---

## Phase 2: User Story 1+2 - 基本グルーピング＋セクション判定 (Priority: P1) MVP

**Goal**: book.xmlを読み込み、TOC情報に基づいてページを階層構造にグルーピングする。pageMetadata/headingからセクション番号を抽出して各ページの所属を判定する。

**Independent Test**: 単一のbook.xmlを処理し、front-matter/chapter/section/subsectionの階層構造が正しく生成されることを検証。

### Input

- [ ] T007 前フェーズ出力を読む: specs/005-toc-page-grouping/tasks/ph1-output.md

### Test Implementation (RED)

- [x] T008 [P] [US2] セクション番号抽出テストを実装: tests/book_converter/test_page_grouper.py::test_extract_section_from_page_metadata
- [x] T009 [P] [US2] headingからのセクション番号抽出テストを実装: tests/book_converter/test_page_grouper.py::test_extract_section_from_heading
- [x] T010 [P] [US2] セクション番号パーステストを実装: tests/book_converter/test_page_grouper.py::test_parse_section_number
- [x] T011 [P] [US1] TOCパーステストを実装: tests/book_converter/test_page_grouper.py::test_parse_toc
- [x] T012 [P] [US1] front-matterグルーピングテストを実装: tests/book_converter/test_page_grouper.py::test_group_front_matter
- [x] T013 [P] [US1] chapter/section/subsectionグルーピングテストを実装: tests/book_converter/test_page_grouper.py::test_group_pages_by_section
- [x] T014 [P] [US1] 階層構造XML生成テストを実装: tests/book_converter/test_page_grouper.py::test_build_hierarchical_xml
- [x] T015 `make test` FAIL (RED) を確認
- [x] T016 RED出力を生成: specs/005-toc-page-grouping/red-tests/ph2-test.md

### Implementation (GREEN)

- [x] T017 REDテストを読む: specs/005-toc-page-grouping/red-tests/ph2-test.md
- [x] T018 [P] [US2] SectionNumberデータクラスを実装: src/book_converter/page_grouper.py::SectionNumber
- [x] T019 [P] [US2] セクション番号抽出関数を実装: src/book_converter/page_grouper.py::extract_section_number()
- [x] T020 [P] [US1] TOCEntry/TOCデータクラスを実装: src/book_converter/page_grouper.py::TOCEntry, TOC
- [x] T021 [P] [US1] TOCパース関数を実装: src/book_converter/page_grouper.py::parse_toc()
- [x] T022 [US1] ページ所属判定関数を実装: src/book_converter/page_grouper.py::assign_pages_to_sections()
- [x] T023 [US1] 階層構造構築関数を実装: src/book_converter/page_grouper.py::build_hierarchy()
- [x] T024 [US1] XML出力関数を実装: src/book_converter/page_grouper.py::serialize_to_xml()
- [x] T025 [US1] メイン関数を実装: src/book_converter/page_grouper.py::group_pages_by_toc()
- [x] T026 `make test` PASS (GREEN) を確認

### Verification

- [x] T027 `make test` で全テストパスを確認（リグレッションなし）
- [x] T028 Phase出力を生成: specs/005-toc-page-grouping/tasks/ph2-output.md

**Checkpoint**: User Story 1+2が完全に機能し、独立してテスト可能

---

## Phase 3: User Story 3 - 章扉ページの識別 (Priority: P2)

**Goal**: 章の最初のページ（章扉ページ）を識別し、`type="chapter-title"`属性を付与する。

**Independent Test**: 章扉ページを含むbook.xmlを処理し、該当ページにtype属性が付与されることを検証。

### Input

- [x] T029 セットアップ分析を読む: specs/005-toc-page-grouping/tasks/ph1-output.md
- [x] T030 前フェーズ出力を読む: specs/005-toc-page-grouping/tasks/ph2-output.md

### Test Implementation (RED)

- [x] T031 [P] [US3] 章扉ページ判定テストを実装: tests/book_converter/test_page_grouper.py::test_identify_chapter_title_page
- [x] T032 [P] [US3] 章扉ページtype属性付与テストを実装: tests/book_converter/test_page_grouper.py::test_chapter_title_page_has_type_attribute
- [x] T033 `make test` FAIL (RED) を確認
- [x] T034 RED出力を生成: specs/005-toc-page-grouping/red-tests/ph3-test.md

### Implementation (GREEN)

- [x] T035 REDテストを読む: specs/005-toc-page-grouping/red-tests/ph3-test.md
- [x] T036 [US3] 章扉ページ判定関数を実装: src/book_converter/page_grouper.py::is_chapter_title_page()
- [x] T037 [US3] build_hierarchy()を拡張してtype属性を付与
- [x] T038 `make test` PASS (GREEN) を確認

### Verification

- [x] T039 `make test` で全テストパスを確認（US1+US2含む）
- [x] T040 Phase出力を生成: specs/005-toc-page-grouping/tasks/ph3-output.md

**Checkpoint**: User Story 1+2+3がすべて機能

---

## Phase 4: User Story 4 - 番号情報欠落ページの処理 (Priority: P2)

**Goal**: セクション番号を抽出できないページを、直前のページと同じセクションに配置する。

**Independent Test**: セクション番号情報がないページを含むbook.xmlを処理し、適切な位置に配置されることを検証。

### Input

- [x] T041 セットアップ分析を読む: specs/005-toc-page-grouping/tasks/ph1-output.md
- [x] T042 前フェーズ出力を読む: specs/005-toc-page-grouping/tasks/ph3-output.md

### Test Implementation (RED)

- [x] T043 [P] [US4] 番号欠落ページのフォールバックテストを実装: tests/book_converter/test_page_grouper.py::test_fallback_to_previous_section
- [x] T044 [P] [US4] 連続欠落ページのテストを実装: tests/book_converter/test_page_grouper.py::test_consecutive_missing_sections
- [x] T045 `make test` FAIL (RED) を確認
- [x] T046 RED出力を生成: specs/005-toc-page-grouping/red-tests/ph4-test.md

### Implementation (GREEN)

- [x] T047 REDテストを読む: specs/005-toc-page-grouping/red-tests/ph4-test.md
- [x] T048 [US4] assign_pages_to_sections()にフォールバックロジックを追加
- [x] T049 `make test` PASS (GREEN) を確認

### Verification

- [x] T050 `make test` で全テストパスを確認（US1+US2+US3含む）
- [x] T051 Phase出力を生成: specs/005-toc-page-grouping/tasks/ph4-output.md

**Checkpoint**: 全User Storyが機能

---

## Phase 5: Polish & CLI統合 — NO TDD

**Purpose**: CLI統合、コードクリーンアップ、最終検証

### Input

- [x] T052 セットアップ分析を読む: specs/005-toc-page-grouping/tasks/ph1-output.md
- [x] T053 前フェーズ出力を読む: specs/005-toc-page-grouping/tasks/ph4-output.md

### Implementation

- [x] T054 [P] CLIに--group-pagesオプションを追加: src/book_converter/cli.py
- [x] T055 [P] スタンドアロン実行機能を追加: src/book_converter/page_grouper.py::main()
- [x] T056 [P] __init__.pyにエクスポートを追加: src/book_converter/__init__.py
- [x] T057 コードクリーンアップとdocstring追加
- [x] T058 quickstart.md検証を実行

### Verification

- [x] T059 `make test` で全テストパスを確認
- [x] T060 実データ（output/4fd5500620491ebe/book.xml）でE2Eテスト
- [x] T061 Phase出力を生成: specs/005-toc-page-grouping/tasks/ph5-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: 依存なし - メインエージェント直接実行
- **Phase 2 (US1+US2)**: Phase 1完了後 - TDDフロー (tdd-generator → phase-executor)
- **Phase 3 (US3)**: Phase 2完了後 - TDDフロー
- **Phase 4 (US4)**: Phase 3完了後 - TDDフロー
- **Phase 5 (Polish)**: Phase 4完了後 - phase-executorのみ

### Agent Delegation

| Phase | Agent | 内容 |
|-------|-------|------|
| Phase 1 | Main | セットアップ、既存コード確認 |
| Phase 2 | tdd-generator → phase-executor | US1+US2 TDD |
| Phase 3 | tdd-generator → phase-executor | US3 TDD |
| Phase 4 | tdd-generator → phase-executor | US4 TDD |
| Phase 5 | phase-executor | CLI統合、Polish |

### [P] Marker Usage

- Setup tasks [P]: 異なるファイルの読み込み
- RED tests [P]: 異なるテスト関数の実装
- GREEN implementation [P]: 異なる関数/クラスの実装

---

## Phase Output & RED Test Artifacts

### Directory Structure

```
specs/005-toc-page-grouping/
├── tasks.md                    # このファイル
├── tasks/
│   ├── ph1-output.md           # Phase 1 出力 (Setup結果)
│   ├── ph2-output.md           # Phase 2 出力 (US1+US2 GREEN結果)
│   ├── ph3-output.md           # Phase 3 出力 (US3 GREEN結果)
│   ├── ph4-output.md           # Phase 4 出力 (US4 GREEN結果)
│   └── ph5-output.md           # Phase 5 出力 (Polish結果)
└── red-tests/
    ├── ph2-test.md             # Phase 2 RED テスト結果
    ├── ph3-test.md             # Phase 3 RED テスト結果
    └── ph4-test.md             # Phase 4 RED テスト結果
```

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Phase 1完了: Setup（既存コード確認）
2. Phase 2完了: User Story 1+2（基本グルーピング＋セクション判定）
3. **STOP and VALIDATE**: `make test`で全テストパスを確認
4. 実データで手動検証

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
2. 各フェーズでコミット: `feat(phase-N): description`

---

## Test Coverage Rules

**Boundary Test Principle**: データ変換が発生するすべての境界でテストを書く

```
[book.xml Input] → [TOC Parse] → [Section Extract] → [Page Assign] → [Hierarchy Build] → [XML Output]
       ↓               ↓              ↓                  ↓                 ↓                ↓
     Test            Test           Test              Test              Test             Test
```

**チェックリスト**:
- [ ] TOCパーステスト
- [ ] セクション番号抽出テスト
- [ ] ページ所属判定テスト
- [ ] 階層構造構築テスト
- [ ] XML出力テスト
- [ ] E2Eテスト（入力→最終出力）

---

## Notes

- [P] tasks = 依存なし、実行順序自由
- [Story] ラベルはタスクを特定のUser Storyにマッピング
- 各User Storyは独立して完了・テスト可能
- TDD: Test Implementation (RED) → FAIL確認 → Implementation (GREEN) → PASS確認
- RED出力は実装開始前に生成必須
- 各フェーズ完了後にコミット
- チェックポイントで独立してストーリーを検証可能
