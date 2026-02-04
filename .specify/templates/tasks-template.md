---
description: "Task list template for feature implementation (TDD mandatory)"
---

# Tasks: [FEATURE NAME]

**Input**: Design documents from `.specify/features/[###-feature-name]/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**TDD is MANDATORY**: User Story phases MUST follow TDD workflow (テスト実装 RED → 実装 GREEN → 検証).

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Source**: `src/` at repository root
- **Tests**: `tests/` at repository root
- Adjust based on plan.md structure

<!--
  ============================================================================
  IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

  The /speckit.tasks command MUST replace these with actual tasks based on:
  - User stories from spec.md (with their priorities P1, P2, P3...)
  - Feature requirements from plan.md
  - Entities from data-model.md
  - Endpoints from contracts/

  Tasks MUST be organized by user story so each story can be:
  - Implemented independently
  - Tested independently
  - Delivered as an MVP increment

  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure
**Executor**: メインエージェント（NO TDD）

- [ ] T001 Create project structure per implementation plan
- [ ] T002 Setup pytest configuration in tests/conftest.py
- [ ] T003 [P] Add test/coverage targets to Makefile
- [ ] T004 Generate phase output: {FEATURE_DIR}/tasks/ph1-output.md

---

## Phase 2: User Story 1 - [Title] (Priority: P1) MVP

**Goal**: [Brief description of what this story delivers]
**Independent Test**: [How to verify this story works on its own]
**Executor**: tdd-generator (RED) → phase-executor (GREEN)

### 入力
- [ ] T005 Read previous phase output: {FEATURE_DIR}/tasks/ph1-output.md

### テスト実装 (RED)
- [ ] T006 [P] [US1] Implement tests for {feature} in tests/test_{name}.py
- [ ] T007 Verify `make test` FAIL (RED)
- [ ] T008 Generate RED output: {FEATURE_DIR}/red-tests/ph2-test.md

### 実装 (GREEN)
- [ ] T009 Read RED tests: {FEATURE_DIR}/red-tests/ph2-test.md
- [ ] T010 [P] [US1] Implement {feature} in src/{name}.py
- [ ] T011 Verify `make test` PASS (GREEN)

### 検証
- [ ] T012 Verify `make coverage` >=80%
- [ ] T013 Generate phase output: {FEATURE_DIR}/tasks/ph2-output.md

**Checkpoint**: User Story 1 should be fully functional and testable independently

---

## Phase 3: User Story 2 - [Title] (Priority: P2)

**Goal**: [Brief description of what this story delivers]
**Independent Test**: [How to verify this story works on its own]
**Executor**: tdd-generator (RED) → phase-executor (GREEN)

### 入力
- [ ] T014 Read previous phase output: {FEATURE_DIR}/tasks/ph2-output.md

### テスト実装 (RED)
- [ ] T015 [P] [US2] Implement tests for {feature} in tests/test_{name}.py
- [ ] T016 Verify `make test` FAIL (RED)
- [ ] T017 Generate RED output: {FEATURE_DIR}/red-tests/ph3-test.md

### 実装 (GREEN)
- [ ] T018 Read RED tests: {FEATURE_DIR}/red-tests/ph3-test.md
- [ ] T019 [P] [US2] Implement {feature} in src/{name}.py
- [ ] T020 Verify `make test` PASS (GREEN)

### 検証
- [ ] T021 Verify `make coverage` >=80%
- [ ] T022 Generate phase output: {FEATURE_DIR}/tasks/ph3-output.md

**Checkpoint**: User Stories 1 AND 2 should both work independently

---

[Add more user story phases as needed, following the same TDD pattern]

---

## Phase N: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories
**Executor**: phase-executor のみ（NO TDD）

- [ ] TXXX [P] Code cleanup and refactoring
- [ ] TXXX [P] Performance optimization across all stories
- [ ] TXXX Run `make test` to verify all tests pass
- [ ] TXXX Generate phase output: {FEATURE_DIR}/tasks/phN-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - メインエージェント直接実行
- **User Stories (Phase 2+)**: Depend on Setup completion - TDD フロー
  - User stories proceed sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all user stories being complete - phase-executor のみ

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Setup (Phase 1)
- **User Story 2 (P2)**: Can start after US1 complete
- **User Story 3 (P3)**: Can start after US2 complete

### TDD サブエージェント役割

- **tdd-generator** (model: opus): テスト実装 (RED) → `red-tests/ph{N}-test.md` 出力
- **phase-executor** (model: sonnet): 実装 (GREEN) → 検証 → `tasks/ph{N}-output.md` 出力

### フォルダ構成

```
{FEATURE_DIR}/
├── red-tests/           # tdd-generator 出力（FAIL テスト情報）
│   ├── ph2-test.md
│   └── ph3-test.md
└── tasks/               # phase-executor 出力（Phase 完了情報）
    ├── ph1-output.md
    └── ph2-output.md
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: User Story 1 (TDD: RED → GREEN → 検証)
3. **STOP and VALIDATE**: Test User Story 1 independently
4. Deploy/demo if ready

### Incremental Delivery

1. Setup → Foundation ready
2. User Story 1 → TDD → Test → Deploy/Demo (MVP!)
3. User Story 2 → TDD → Test → Deploy/Demo
4. Each story adds value without breaking previous stories

---

## Test Coverage Rules

**境界テスト原則**: データ変換の境界でテストする。
- パイプラインの各ステップの入出力
- Ollama API のレスポンスパース
- ファイル I/O の境界（画像読み込み、テキスト出力）
- エッジケース: 空入力、破損ファイル、タイムアウト

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- TDD: Verify tests FAIL before implementing
- Commit after each phase completion
- Avoid: vague tasks, same file conflicts, cross-story dependencies
