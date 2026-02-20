# Tasks: CI Lint Migration

**Input**: Design documents from `/specs/013-ci-lint-migration/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, quickstart.md

**Tests**: TDD対象外（CI/DevOps設定ファイルのため、手動検証を使用）

**Organization**: タスクはユーザーストーリーごとにグループ化され、各ストーリーは独立して実装・検証可能

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 依存関係なし（異なるファイル、実行順序自由）
- **[Story]**: このタスクが属するユーザーストーリー（US1, US2, US3）
- 説明には正確なファイルパスを含める

## User Story Summary

| ID | Title | Priority | FR | 独立テスト |
|----|-------|----------|----|-----------|
| US1 | CIでの品質チェック自動化 | P1 | FR-001,002,003,006 | PR作成→CI実行確認 |
| US2 | Claude Code開発時のリアルタイムフィードバック | P2 | FR-004 | ファイル編集→ruff実行確認 |
| US3 | pre-commit依存の削減 | P3 | FR-005 | コミット時ブロックなし確認 |

## Path Conventions

- **Configuration**: `.github/workflows/`, `.claude/`, `.pre-commit-config.yaml`
- **Feature docs**: `specs/013-ci-lint-migration/`

---

## Phase 1: Setup（現状分析）— NO TDD

**Purpose**: 現在の設定を確認し、変更に備える

- [X] T001 現在の`.pre-commit-config.yaml`を確認
- [X] T002 [P] 現在の`.claude/settings.local.json`を確認
- [X] T003 [P] 現在の`pyproject.toml`のruff/pylint設定を確認
- [X] T004 [P] `.github/workflows/`ディレクトリの有無を確認
- [X] T005 フェーズ出力を生成: specs/013-ci-lint-migration/tasks/ph1-output.md

---

## Phase 2: User Story 1 - CIでの品質チェック自動化 (Priority: P1) MVP

**Goal**: GitHub ActionsでPR作成時にpylint/ruffを自動実行

**独立テスト**: PRを作成し、CIワークフローがlintを実行することを確認

### Input

- [X] T006 前フェーズ出力を読む: specs/013-ci-lint-migration/tasks/ph1-output.md

### Implementation

- [X] T007 [US1] `.github/workflows/`ディレクトリを作成
- [X] T008 [US1] GitHub Actions lint workflowを作成: `.github/workflows/lint.yml`
  - トリガー: `pull_request` (branches: main)
  - paths: `src/**/*.py`, `tests/**/*.py`, `pyproject.toml`
  - jobs: checkout, setup-python 3.13, install deps, ruff check, ruff format --check, pylint
- [X] T009 [US1] ワークフローをpushしてCI実行を確認

### Verification

- [X] T010 [US1] テスト用PRを作成してCI動作を確認
- [X] T011 フェーズ出力を生成: specs/013-ci-lint-migration/tasks/ph2-output.md

**Checkpoint**: US1完了後、PRでCIが実行されることを確認

---

## Phase 3: User Story 2 - Claude Codeフック設定 (Priority: P2)

**Goal**: ファイル編集後にruffが自動実行される

**独立テスト**: Claude Codeでファイル編集後、ruffが実行されることを確認

### Input

- [X] T012 セットアップ分析を読む: specs/013-ci-lint-migration/tasks/ph1-output.md
- [X] T013 前フェーズ出力を読む: specs/013-ci-lint-migration/tasks/ph2-output.md

### Implementation

- [X] T014 [P] [US2] `.claude/hooks/`ディレクトリを作成
- [X] T015 [US2] ruff lintフックスクリプトを作成: `.claude/hooks/ruff-lint.sh`
  - stdin からJSON読み取り（jq使用）
  - `.py`ファイルのみ対象
  - ruff check --fix + ruff format 実行
  - exit 0（警告のみ、ブロックしない）
- [X] T016 [US2] 実行権限を付与: `chmod +x .claude/hooks/ruff-lint.sh`
- [X] T017 [US2] Claude Code設定を作成: `.claude/settings.json`
  - hooks.PostToolUse設定
  - matcher: "Edit|Write"
  - command: ruff-lint.shを参照

### Verification

- [X] T018 [US2] Claude Codeセッションを開始してフック動作を確認
- [X] T019 フェーズ出力を生成: specs/013-ci-lint-migration/tasks/ph3-output.md

**Checkpoint**: US2完了後、ファイル編集時にruffが自動実行されることを確認

---

## Phase 4: User Story 3 - pre-commit削減 (Priority: P3)

**Goal**: pre-commitからruff/pylintを削除

**独立テスト**: コミット時にlintでブロックされないことを確認

### Input

- [X] T020 セットアップ分析を読む: specs/013-ci-lint-migration/tasks/ph1-output.md
- [X] T021 前フェーズ出力を読む: specs/013-ci-lint-migration/tasks/ph3-output.md

### Implementation

- [X] T022 [US3] `.pre-commit-config.yaml`からruff設定を削除
- [X] T023 [US3] `.pre-commit-config.yaml`からpylint設定を削除
- [X] T024 [US3] 設定が空になる場合、repos: [] に設定（または削除検討）

### Verification

- [X] T025 [US3] `git commit`でブロックされないことを確認
- [X] T026 [US3] `pre-commit run --all-files`で残存フックを確認
- [X] T027 フェーズ出力を生成: specs/013-ci-lint-migration/tasks/ph4-output.md

**Checkpoint**: US3完了後、コミットがスムーズに完了することを確認

---

## Phase 5: Polish & 最終検証 — NO TDD

**Purpose**: 全体の整合性確認とクリーンアップ

### Input

- [X] T028 セットアップ分析を読む: specs/013-ci-lint-migration/tasks/ph1-output.md
- [X] T029 前フェーズ出力を読む: specs/013-ci-lint-migration/tasks/ph4-output.md

### Implementation

- [X] T030 [P] quickstart.mdに沿ったセットアップ手順の検証
- [X] T031 [P] Branch Protection設定の確認（GitHub UI）
- [X] T032 [P] 不要になった設定やファイルの削除

### Verification

- [X] T033 SC-001確認: PRでCIが自動実行され、lint結果が表示される
- [X] T034 SC-002確認: lint違反のあるPRがマージ不可（Branch Protection）
- [X] T035 SC-003確認: Claude Codeでのファイル編集後5秒以内にruffフィードバック
- [X] T036 SC-004確認: pre-commit実行時間が短縮される（lint除去分）
- [X] T037 フェーズ出力を生成: specs/013-ci-lint-migration/tasks/ph5-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: 依存なし - メインエージェント直接実行
- **Phase 2 (US1 - CI)**: Phase 1に依存 - phase-executor実行
- **Phase 3 (US2 - hooks)**: Phase 2に依存 - phase-executor実行
- **Phase 4 (US3 - pre-commit)**: Phase 3に依存 - phase-executor実行
- **Phase 5 (Polish)**: 全フェーズに依存 - phase-executor実行

### ユーザーストーリー間の独立性

```
US1 (CI) ────────────────────→ 独立して検証可能（PRでCI確認）
                               ↓
US2 (hooks) ─────────────────→ 独立して検証可能（Claude Codeで確認）
                               ↓
US3 (pre-commit) ────────────→ 独立して検証可能（コミットで確認）
```

### [P] Marker（依存関係なし）

- T002, T003, T004: 異なるファイルの読み取り
- T014: ディレクトリ作成（他タスクと独立）
- T030, T031, T032: 異なる検証項目

---

## Phase Output Artifacts

### Directory Structure

```
specs/013-ci-lint-migration/
├── tasks.md                    # 本ファイル
└── tasks/
    ├── ph1-output.md           # Phase 1出力（現状分析結果）
    ├── ph2-output.md           # Phase 2出力（US1 CI設定結果）
    ├── ph3-output.md           # Phase 3出力（US2 hooks設定結果）
    ├── ph4-output.md           # Phase 4出力（US3 pre-commit削減結果）
    └── ph5-output.md           # Phase 5出力（最終検証結果）
```

### Phase Output Content

各`phN-output.md`には以下を含める:
- 実行内容のサマリ
- 作成/変更されたファイル
- 検証結果
- 計画からの逸脱や決定事項

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Phase 1完了: Setup（現状分析）
2. Phase 2完了: US1（CI設定）
3. **STOP and VALIDATE**: PRでCI動作確認
4. PRをマージせずに次フェーズへ

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
2. 各フェーズ完了時にコミット: `feat(phase-N): description`

---

## Notes

- TDD対象外: CI/DevOps設定は手動検証
- [P] tasks = 依存関係なし、実行順序自由
- [Story] label = タスクと特定のユーザーストーリーのマッピング
- 各ユーザーストーリーは独立して完了・検証可能
- フェーズ完了ごとにコミット
- 任意のチェックポイントで停止してストーリーを独立検証可能
