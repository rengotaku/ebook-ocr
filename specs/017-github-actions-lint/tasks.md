# Tasks: GitHub Actions Lint CI

**Input**: Design documents from `/specs/017-github-actions-lint/`
**Prerequisites**: plan.md (required), spec.md (required), research.md

**Tests**: TDD N/A（CI設定ファイルのため）。検証は `make lint` の実行とCI動作確認で行う。

**Language**: Japanese

**Organization**: タスクはユーザーストーリー単位で整理され、独立した実装・検証が可能。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 依存関係なし（異なるファイル、実行順序自由）
- **[Story]**: タスクが属するユーザーストーリー（例: US1, US2, US3）
- ファイルパスを説明に含める

## User Story Summary

| ID  | Title                    | Priority | FR         | Scenario                              |
|-----|--------------------------|----------|------------|---------------------------------------|
| US1 | PRのlintチェック自動実行 | P1       | FR-001,002,004,005,006,008,009,010 | PR作成/更新時にCI自動実行 |
| US2 | mainブランチの品質保証   | P2       | FR-003     | main push時にCI自動実行              |
| US3 | ローカルとCIの一貫性     | P3       | FR-007     | make lintでCIと同じチェック          |

## Path Conventions

- **Workflow**: `.github/workflows/lint.yml`
- **Makefile**: `Makefile`（リポジトリルート）
- **Phase Output**: `specs/017-github-actions-lint/tasks/`

---

## Phase 1: Setup（既存実装の確認）— NO TDD

**Purpose**: 既存実装の確認と変更箇所の特定

- [ ] T001 既存のワークフロー確認: `.github/workflows/lint.yml`
- [ ] T002 [P] 既存のMakefile確認: `Makefile`
- [ ] T003 [P] 既存のpyproject.toml設定確認: `pyproject.toml`
- [ ] T004 Edit and rename: `specs/017-github-actions-lint/tasks/ph1-output-template.md` → `ph1-output.md`

---

## Phase 2: User Story 3 - ローカルとCIの一貫性 (Priority: P3) — 基盤

**Goal**: Makefileにlint関連ターゲットを追加し、ローカルでCIと同じチェックを実行可能にする

**Independent Test**: `make ruff`, `make pylint`, `make lint` がローカルで正常に動作することを確認

**Note**: US3を先に実装することで、US1/US2のCI設定がMakefileターゲットを利用可能になる

### Input

- [ ] T005 Read previous phase output: `specs/017-github-actions-lint/tasks/ph1-output.md`

### Implementation

- [ ] T006 [US3] Makefileに`ruff`ターゲットを追加: `Makefile`
- [ ] T007 [US3] Makefileに`pylint`ターゲットを追加: `Makefile`
- [ ] T008 [US3] Makefileに`lint`ターゲットを追加（ruff + pylint）: `Makefile`

### Verification

- [ ] T009 `make ruff` を実行して動作確認
- [ ] T010 `make pylint` を実行して動作確認
- [ ] T011 `make lint` を実行して動作確認
- [ ] T012 Edit and rename: `specs/017-github-actions-lint/tasks/ph2-output-template.md` → `ph2-output.md`

**Checkpoint**: `make lint` がローカルで正常動作すること

---

## Phase 3: User Story 1 - PRのlintチェック自動実行 (Priority: P1) — MVP

**Goal**: PR作成/更新時にGitHub Actionsでlintチェックが自動実行され、結果がPRステータスとして表示される

**Independent Test**: テストPRを作成し、lintエラーがあればCIが失敗、なければ成功することを確認

### Input

- [ ] T013 Read setup analysis: `specs/017-github-actions-lint/tasks/ph1-output.md`
- [ ] T014 Read previous phase output: `specs/017-github-actions-lint/tasks/ph2-output.md`

### Implementation

- [ ] T015 [US1] lint.ymlをruffジョブとpylintジョブに分離: `.github/workflows/lint.yml`
- [ ] T016 [US1] ruffジョブでMakefileターゲットを使用するよう変更: `.github/workflows/lint.yml`
- [ ] T017 [US1] pylintジョブでMakefileターゲットを使用するよう変更: `.github/workflows/lint.yml`
- [ ] T018 [US1] pathsフィルタを削除（常に実行）: `.github/workflows/lint.yml`
- [ ] T019 [US1] fail-underオプションを削除: `.github/workflows/lint.yml`

### Verification

- [ ] T020 `make lint` を実行してローカルで成功することを確認
- [ ] T021 変更をコミット
- [ ] T022 Edit and rename: `specs/017-github-actions-lint/tasks/ph3-output-template.md` → `ph3-output.md`

**Checkpoint**: PR作成時にCIが自動実行され、ruffとpylintの結果が個別に確認可能

---

## Phase 4: User Story 2 - mainブランチの品質保証 (Priority: P2)

**Goal**: mainブランチへのpush時にlintチェックが自動実行される

**Independent Test**: mainブランチに直接pushし、CIが自動実行されることを確認

### Input

- [ ] T023 Read setup analysis: `specs/017-github-actions-lint/tasks/ph1-output.md`
- [ ] T024 Read previous phase output: `specs/017-github-actions-lint/tasks/ph3-output.md`

### Implementation

- [ ] T025 [US2] lint.ymlにpushトリガーを追加（branches: [main]）: `.github/workflows/lint.yml`

### Verification

- [ ] T026 YAMLの構文チェック（`python -c "import yaml; yaml.safe_load(open('.github/workflows/lint.yml'))"`)
- [ ] T027 変更をコミット
- [ ] T028 Edit and rename: `specs/017-github-actions-lint/tasks/ph4-output-template.md` → `ph4-output.md`

**Checkpoint**: mainブランチへのpush時にCIがトリガーされる設定が完了

---

## Phase 5: Polish & Cross-Cutting Concerns — NO TDD

**Purpose**: 最終確認とPR作成

### Input

- [ ] T029 Read setup analysis: `specs/017-github-actions-lint/tasks/ph1-output.md`
- [ ] T030 Read previous phase output: `specs/017-github-actions-lint/tasks/ph4-output.md`

### Implementation

- [ ] T031 [P] 既存のlintエラーがあれば修正
- [ ] T032 [P] CLAUDE.mdの更新が必要か確認

### Verification

- [ ] T033 `make lint` で全体のlintチェックが通ることを確認
- [ ] T034 PRを作成してCI動作確認
- [ ] T035 Edit and rename: `specs/017-github-actions-lint/tasks/ph5-output-template.md` → `ph5-output.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: 依存なし - メインエージェントが直接実行
- **Phase 2 (US3)**: Phase 1完了後 - Makefileターゲット作成（US1/US2の基盤）
- **Phase 3 (US1)**: Phase 2完了後 - PRトリガーとMakefileターゲット連携
- **Phase 4 (US2)**: Phase 3完了後 - pushトリガー追加
- **Phase 5 (Polish)**: 全フェーズ完了後 - 最終確認とPR作成

### User Story Dependencies

```
US3 (Makefile) ─→ US1 (PR trigger) ─→ US2 (push trigger)
    基盤           MVP               拡張
```

US3が基盤となるため、優先度P3だが最初に実装する。

### Agent Delegation

- **Phase 1 (Setup)**: メインエージェント直接実行
- **Phase 2-4**: speckit:phase-executor（TDD N/A）
- **Phase 5 (Polish)**: speckit:phase-executor

### [P] Marker (No Dependencies)

`[P]`は「他タスクへの依存なし、実行順序自由」を示す。

- T002, T003: 異なるファイルの読み取り
- T031, T032: 独立した確認作業

---

## Phase Output Artifacts

### Directory Structure

```
specs/017-github-actions-lint/
├── tasks.md                    # このファイル
└── tasks/
    ├── ph1-output.md           # Phase 1出力（Setup結果）
    ├── ph2-output.md           # Phase 2出力（US3完了）
    ├── ph3-output.md           # Phase 3出力（US1完了）
    ├── ph4-output.md           # Phase 4出力（US2完了）
    └── ph5-output.md           # Phase 5出力（Polish完了）
```

### Phase Output Format

| Output Type | Template File |
|-------------|---------------|
| `ph1-output.md` | `.specify/templates/ph1-output-template.md` |
| `phN-output.md` | `.specify/templates/phN-output-template.md` |

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2 + Phase 3)

1. Phase 1完了: 既存実装確認
2. Phase 2完了: Makefileターゲット作成（US3）
3. Phase 3完了: PRトリガー設定（US1）
4. **STOP and VALIDATE**: `make lint` が通り、PRでCIが動作することを確認

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
2. 各フェーズでコミット: `feat(017): description`

---

## Notes

- TDD N/A: CI設定ファイル（YAML, Makefile）のためユニットテスト不要
- 検証は `make lint` 実行とCI動作確認で行う
- US3を先に実装することで、US1/US2がMakefileターゲットを利用可能
- [P]タスク = 依存なし、実行順序自由
- [Story]ラベル = タスクと要件のトレーサビリティ
