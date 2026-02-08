# Tasks: 目次情報の保持

**Input**: `/specs/004-toc-structure/` の設計ドキュメント
**Prerequisites**: plan.md, spec.md, data-model.md, contracts/, research.md, quickstart.md

**Tests**: TDDはUser Storyフェーズで必須。Test Implementation (RED) → Implementation (GREEN) → Verification のワークフローに従う。

**Organization**: タスクはユーザーストーリーごとにグループ化され、各ストーリーの独立した実装とテストを可能にする。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 依存関係なし（異なるファイル、実行順序自由）
- **[Story]**: タスクが属するユーザーストーリー（例: US1, US2, US3, US4）
- 説明には正確なファイルパスを含める

## User Story Summary

| ID | Title | Priority | FR | Scenario |
|----|-------|----------|----|----------|
| US1 | 目次マーカーによる目次認識 | P1 | FR-001,002,004,007 | tocマーカーで`<tableOfContents>`生成 |
| US2 | 章・節タイトルの構造化 | P1 | FR-003,005,008 | パターン抽出で`<entry>`生成 |
| US3 | 目次の読み上げ制御 | P2 | FR-006 | readAloud="false"設定 |
| US4 | コンテンツ範囲マーカー | P2 | FR-009,010,011,012,013 | content/skipマーカー処理 |

## Path Conventions

- **Source**: `src/book_converter/`
- **Tests**: `tests/book_converter/`
- **Specs**: `specs/004-toc-structure/`

---

## Phase 1: Setup (既存コード調査) — NO TDD

**Purpose**: 既存実装の理解と変更箇所の特定

- [X] T001 既存モデル実装を確認: src/book_converter/models.py
- [X] T002 [P] 既存パーサー実装を確認: src/book_converter/parser.py
- [X] T003 [P] 既存トランスフォーマー実装を確認: src/book_converter/transformer.py
- [X] T004 [P] 既存テストを確認: tests/book_converter/test_parser.py
- [X] T005 [P] 既存テストを確認: tests/book_converter/test_transformer.py
- [X] T006 [P] 既存テストを確認: tests/book_converter/test_integration.py
- [X] T007 新規XSDスキーマを確認: specs/004-toc-structure/contracts/book.xsd
- [X] T008 `make test` で既存テストがパスすることを確認
- [X] T009 フェーズ出力を生成: specs/004-toc-structure/tasks/ph1-output.md

---

## Phase 2: US1+US2 目次マーカー認識と構造化 (Priority: P1) MVP

**Goal**: `<!-- toc -->`マーカーで囲まれた目次テキストを認識し、章・節パターンを抽出して`<tableOfContents>`と`<entry>`要素を生成する

**Independent Test**: book.mdに目次マーカーと「第1章 タイトル ... 15」形式のテキストを追加し、変換後のXMLに正しい`<tableOfContents>`と`<entry>`が生成されることを確認

### Input

- [ ] T010 前フェーズ出力を読み込み: specs/004-toc-structure/tasks/ph1-output.md

### Test Implementation (RED)

- [ ] T011 [P] [US1] 目次マーカー検出テストを実装: tests/book_converter/test_parser.py（`parse_toc_marker()`）
- [ ] T012 [P] [US2] 章パターン（第N章）抽出テストを実装: tests/book_converter/test_parser.py（`parse_toc_entry()`）
- [ ] T013 [P] [US2] 節パターン（N.N、N.N.N）抽出テストを実装: tests/book_converter/test_parser.py
- [ ] T014 [P] [US2] ページ番号抽出テストを実装: tests/book_converter/test_parser.py（ドットリーダー、罫線形式）
- [ ] T015 [P] [US1] TocEntry/TableOfContentsモデルテストを実装: tests/book_converter/test_parser.py
- [ ] T016 [P] [US1] tableOfContents変換テストを実装: tests/book_converter/test_transformer.py（`transform_table_of_contents()`）
- [ ] T017 [P] [US2] entry変換テストを実装: tests/book_converter/test_transformer.py（`transform_toc_entry()`）
- [ ] T018 [P] [US1] 統合テスト（目次マーカーあり）を実装: tests/book_converter/test_integration.py
- [ ] T019 [P] [US1] 統合テスト（目次マーカーなし、後方互換）を実装: tests/book_converter/test_integration.py
- [ ] T020 `make test` FAIL を確認 (RED)
- [ ] T021 RED出力を生成: specs/004-toc-structure/red-tests/ph2-test.md

### Implementation (GREEN)

- [ ] T022 REDテストを読み込み: specs/004-toc-structure/red-tests/ph2-test.md
- [ ] T023 [P] [US1] TocEntryデータクラスを追加: src/book_converter/models.py
- [ ] T024 [P] [US1] TableOfContentsデータクラスを追加: src/book_converter/models.py
- [ ] T025 [P] [US1] MarkerType列挙を追加: src/book_converter/models.py
- [ ] T026 [P] [US1] `parse_toc_marker()`を実装: src/book_converter/parser.py
- [ ] T027 [P] [US2] `parse_toc_entry()`を実装: src/book_converter/parser.py（章・節・項パターン）
- [ ] T028 [P] [US2] ページ番号抽出ロジックを実装: src/book_converter/parser.py
- [ ] T029 [US1] パーサーに目次収集ロジックを統合: src/book_converter/parser.py（`_parse_single_page_content()`拡張）
- [ ] T030 [P] [US1] `transform_toc_entry()`を実装: src/book_converter/transformer.py
- [ ] T031 [P] [US1] `transform_table_of_contents()`を実装: src/book_converter/transformer.py
- [ ] T032 [US1] トランスフォーマーに目次変換を統合: src/book_converter/transformer.py
- [ ] T033 `make test` PASS を確認 (GREEN)

### Verification

- [ ] T034 `make test` で全テストパスを確認（リグレッションなし）
- [ ] T035 `make coverage` で ≥80% を確認
- [ ] T036 フェーズ出力を生成: specs/004-toc-structure/tasks/ph2-output.md

**Checkpoint**: US1+US2が完全に機能し、独立してテスト可能

---

## Phase 3: US3 目次の読み上げ制御 (Priority: P2)

**Goal**: `<tableOfContents>`要素に`readAloud="false"`属性をデフォルトで設定する

**Independent Test**: 変換後のXMLで`<tableOfContents readAloud="false">`となっていることを確認

### Input

- [ ] T037 セットアップ分析を読み込み: specs/004-toc-structure/tasks/ph1-output.md
- [ ] T038 前フェーズ出力を読み込み: specs/004-toc-structure/tasks/ph2-output.md

### Test Implementation (RED)

- [ ] T039 [P] [US3] tableOfContentsのreadAloud属性テストを実装: tests/book_converter/test_transformer.py
- [ ] T040 [P] [US3] 統合テスト（readAloud確認）を実装: tests/book_converter/test_integration.py
- [ ] T041 `make test` FAIL を確認 (RED)
- [ ] T042 RED出力を生成: specs/004-toc-structure/red-tests/ph3-test.md

### Implementation (GREEN)

- [ ] T043 REDテストを読み込み: specs/004-toc-structure/red-tests/ph3-test.md
- [ ] T044 [US3] tableOfContentsにreadAloud="false"を設定: src/book_converter/transformer.py
- [ ] T045 `make test` PASS を確認 (GREEN)

### Verification

- [ ] T046 `make test` で全テストパスを確認（US1+US2含む）
- [ ] T047 フェーズ出力を生成: specs/004-toc-structure/tasks/ph3-output.md

**Checkpoint**: US1+US2+US3が全て機能

---

## Phase 4: US4 コンテンツ範囲マーカー (Priority: P2)

**Goal**: `<!-- content -->`で読み上げ対象、`<!-- skip -->`で非対象を明示。マーカーなしはデフォルトで読み上げ非対象。

**Independent Test**: content/skipマーカーで囲まれた部分のreadAloud属性が正しく設定されることを確認

### Input

- [ ] T048 セットアップ分析を読み込み: specs/004-toc-structure/tasks/ph1-output.md
- [ ] T049 前フェーズ出力を読み込み: specs/004-toc-structure/tasks/ph3-output.md

### Test Implementation (RED)

- [ ] T050 [P] [US4] contentマーカー検出テストを実装: tests/book_converter/test_parser.py（`parse_content_marker()`）
- [ ] T051 [P] [US4] skipマーカー検出テストを実装: tests/book_converter/test_parser.py
- [ ] T052 [P] [US4] マーカー状態スタックテストを実装: tests/book_converter/test_parser.py（ネスト処理）
- [ ] T053 [P] [US4] デフォルトreadAloud=falseテストを実装: tests/book_converter/test_transformer.py
- [ ] T054 [P] [US4] contentマーカー内readAloud=trueテストを実装: tests/book_converter/test_transformer.py
- [ ] T055 [P] [US4] skipマーカー内readAloud=falseテストを実装: tests/book_converter/test_transformer.py
- [ ] T056 [P] [US4] 統合テスト（content/skip混合）を実装: tests/book_converter/test_integration.py
- [ ] T057 `make test` FAIL を確認 (RED)
- [ ] T058 RED出力を生成: specs/004-toc-structure/red-tests/ph4-test.md

### Implementation (GREEN)

- [ ] T059 REDテストを読み込み: specs/004-toc-structure/red-tests/ph4-test.md
- [ ] T060 [P] [US4] `parse_content_marker()`を実装: src/book_converter/parser.py
- [ ] T061 [P] [US4] マーカー状態スタック管理を実装: src/book_converter/parser.py
- [ ] T062 [US4] パーサーにreadAloud状態追跡を統合: src/book_converter/parser.py
- [ ] T063 [US4] ContentモデルのreadAloudデフォルトをFalseに変更: src/book_converter/models.py
- [ ] T064 [US4] トランスフォーマーでreadAloud属性を出力: src/book_converter/transformer.py
- [ ] T065 `make test` PASS を確認 (GREEN)

### Verification

- [ ] T066 `make test` で全テストパスを確認（全US含む）
- [ ] T067 `make coverage` で ≥80% を確認
- [ ] T068 フェーズ出力を生成: specs/004-toc-structure/tasks/ph4-output.md

**Checkpoint**: US1+US2+US3+US4が全て機能し、独立してテスト可能

---

## Phase 5: Polish & Cross-Cutting Concerns — NO TDD

**Purpose**: 最終検証、ドキュメント整備、クリーンアップ

### Input

- [ ] T069 セットアップ分析を読み込み: specs/004-toc-structure/tasks/ph1-output.md
- [ ] T070 前フェーズ出力を読み込み: specs/004-toc-structure/tasks/ph4-output.md

### Implementation

- [ ] T071 [P] XSDスキーマを本番に反映: specs/002-book-md-structure/contracts/book.xsd を更新
- [ ] T072 [P] quickstart.md の検証を実行（サンプル変換テスト）
- [ ] T073 [P] E2Eテストを追加: tests/book_converter/test_e2e.py（実際のbook.mdサンプル使用）
- [ ] T074 コードクリーンアップとリファクタリング
- [ ] T075 `make test` で全テストパスを確認

### Verification

- [ ] T076 `make test` で全テストパスを確認
- [ ] T077 `make coverage` で ≥80% を確認
- [ ] T078 フェーズ出力を生成: specs/004-toc-structure/tasks/ph5-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: 依存なし - メインエージェント直接実行
- **Phase 2 (US1+US2)**: TDDフロー (tdd-generator → phase-executor)
- **Phase 3 (US3)**: Phase 2完了後 - TDDフロー
- **Phase 4 (US4)**: Phase 3完了後 - TDDフロー
- **Phase 5 (Polish)**: 全US完了後 - phase-executor のみ

### Within Each User Story Phase (TDD Flow)

1. **Input**: セットアップ分析 (ph1) + 前フェーズ出力を読み込み
2. **Test Implementation (RED)**: テストを先に書く → `make test` FAIL確認 → RED出力生成
3. **Implementation (GREEN)**: REDテストを読み込み → 実装 → `make test` PASS確認
4. **Verification**: リグレッションなし確認 → フェーズ出力生成

### Agent Delegation

- **Phase 1 (Setup)**: メインエージェント直接実行
- **Phase 2-4 (User Stories)**: tdd-generator (RED) → phase-executor (GREEN + Verification)
- **Phase 5 (Polish)**: phase-executor のみ

### [P] Marker (No Dependencies)

`[P]` は「他タスクへの依存なし、実行順序自由」を示す。並列実行を保証するものではない。

---

## Phase Output & RED Test Artifacts

### Directory Structure

```
specs/004-toc-structure/
├── tasks.md                    # このファイル
├── tasks/
│   ├── ph1-output.md           # Phase 1 出力（セットアップ結果）
│   ├── ph2-output.md           # Phase 2 出力（US1+US2 GREEN結果）
│   ├── ph3-output.md           # Phase 3 出力（US3 GREEN結果）
│   ├── ph4-output.md           # Phase 4 出力（US4 GREEN結果）
│   └── ph5-output.md           # Phase 5 出力（最終検証）
└── red-tests/
    ├── ph2-test.md             # Phase 2 REDテスト結果
    ├── ph3-test.md             # Phase 3 REDテスト結果
    └── ph4-test.md             # Phase 4 REDテスト結果
```

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Phase 1: Setup（既存コード調査）を完了
2. Phase 2: US1+US2（目次マーカー認識と構造化）を完了
3. **STOP and VALIDATE**: `make test` で全テストパスを確認
4. 手動テスト: サンプルbook.mdで目次変換を確認

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
2. 各フェーズでコミット: `feat(phase-N): 説明`

---

## Test Coverage Rules

**Boundary Test Principle**: データ変換が発生する**すべての境界**でテストを書く

```
[book.md] → [Parser] → [Models] → [Transformer] → [XML Builder] → [book.xml]
    ↓          ↓          ↓            ↓               ↓
  Test       Test       Test         Test            Test
```

**チェックリスト**:
- [ ] マーカー解析テスト（parse_toc_marker, parse_content_marker）
- [ ] 目次エントリ解析テスト（parse_toc_entry）
- [ ] モデル生成テスト（TocEntry, TableOfContents）
- [ ] 変換ロジックテスト（transform_toc_entry, transform_table_of_contents）
- [ ] **XML出力テスト**（readAloud属性、entry要素）
- [ ] E2Eテスト（book.md → book.xml）

---

## Notes

- [P] タスク = 依存なし、実行順序自由
- [Story] ラベル = トレーサビリティのため特定USにマップ
- 各USは独立して完了・テスト可能
- TDD: Test Implementation (RED) → FAIL確認 → Implementation (GREEN) → PASS確認
- RED出力は実装開始前に必ず生成
- 各フェーズ完了後にコミット
- チェックポイントで各ストーリーを独立検証可能
