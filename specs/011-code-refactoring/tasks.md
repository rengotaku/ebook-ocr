# Tasks: コード品質自動化とファイルサイズ制限

**Input**: 設計ドキュメント `/specs/011-code-refactoring/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md

**Tests**: このfeatureはリファクタリング・設定変更のため、従来のTDDではなく既存テストの維持で検証する。

**Language**: 日本語

**Organization**: FR-010の実装順序制約に従い、User Storyの順序を調整（US1 → US3 → US2）。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 依存関係なし（異なるファイル、実行順序自由）
- **[Story]**: タスクが属するユーザーストーリー（例: US1, US2, US3）
- 説明に正確なファイルパスを含める

## User Story Summary

| ID | Title | Priority | FR | シナリオ |
|----|-------|----------|----|----------|
| US1 | ruffによるコード品質チェック | P1 | FR-001, FR-002, FR-003 | ruff check実行 |
| US2 | pre-commitフックによる自動実行 | P2 | FR-004, FR-005 | コミット時フック |
| US3 | 大規模ファイルの分割 | P3 | FR-006, FR-007, FR-008, FR-009 | 600行以下に分割 |

**実装順序**: FR-010により (1) ruff設定 → (2) 既存コード修正 → (3) ファイル分割 → (4) pre-commit設定

## Path Conventions

- **Single project**: `src/`, `tests/`（リポジトリルート）
- 設定ファイル: `pyproject.toml`, `.pre-commit-config.yaml`（リポジトリルート）
- subagent指示: `.claude/agents/`

---

## Phase 1: Setup（現状分析） — NO TDD

**Purpose**: 現在の実装を確認し、変更の準備を行う

- [X] T001 現在のpyproject.tomlの有無を確認（存在しない場合は新規作成対象）
- [X] T002 [P] 分割対象ファイル src/ocr_ensemble.py の構造を分析（699行）
- [X] T003 [P] 分割対象ファイル src/rover/engines.py の構造を分析（613行）
- [X] T004 [P] 既存テストを確認: tests/
- [X] T005 `make test` を実行して現在のテスト状態を確認
- [X] T006 フェーズ出力を生成: specs/011-code-refactoring/tasks/ph1-output.md

---

## Phase 2: User Story 1 - ruffによるコード品質チェック (Priority: P1) MVP

**Goal**: ruffを導入し、既存コードを規約準拠させる

**Independent Test**: `ruff check src/` がエラー0件で完了する

### Input

- [X] T007 前フェーズ出力を読み込み: specs/011-code-refactoring/tasks/ph1-output.md

### Implementation

- [X] T008 [US1] pyproject.toml を作成し、ruff設定を追加:
  - line-length: 120
  - target-version: "py313"
  - select: ["E", "F", "I", "W"]
- [X] T009 [US1] `ruff check src/` を実行して違反を確認
- [X] T010 [US1] `ruff check --fix src/` を実行して自動修正可能な違反を修正
- [X] T011 [US1] `ruff format src/` を実行してフォーマットを適用
- [X] T012 [US1] 残りの手動修正が必要な違反を修正: src/

### Verification

- [X] T013 `ruff check src/` がエラー0件で完了することを確認
- [X] T014 `ruff format --check src/` が変更なしで完了することを確認
- [X] T015 `make test` で全テストがパスすることを確認
- [X] T016 フェーズ出力を生成: specs/011-code-refactoring/tasks/ph2-output.md

**Checkpoint**: ruff check/formatがクリーンな状態

---

## Phase 3: User Story 3 - 大規模ファイルの分割 (Priority: P3)

**Goal**: 600行超ファイルを責務ごとに分割し、公開APIを維持する

**Independent Test**: 分割後のファイルが600行以下であり、既存テストがすべてパスする

**Note**: FR-010により、pre-commit設定（US2）の前にファイル分割を実施

### Input

- [X] T017 セットアップ分析を読み込み: specs/011-code-refactoring/tasks/ph1-output.md
- [X] T018 前フェーズ出力を読み込み: specs/011-code-refactoring/tasks/ph2-output.md

### Implementation (ocr_ensemble.py 分割)

- [X] T019 [P] [US3] src/ocr_ensemble/ ディレクトリを作成
- [X] T020 [P] [US3] src/ocr_ensemble/models.py を作成（EngineResult, EnsembleResult, TextWithBox）
- [X] T021 [P] [US3] src/ocr_ensemble/engines.py を作成（_get_* + ocr_* 関数）
- [X] T022 [P] [US3] src/ocr_ensemble/voting.py を作成（is_garbage, calculate_similarity, merge_by_voting等）
- [X] T023 [US3] src/ocr_ensemble/__init__.py を作成（公開API re-export + ocr_ensemble, run_ensemble_ocr, main）
- [X] T024 [US3] 旧 src/ocr_ensemble.py を削除

### Implementation (rover/engines.py 分割)

- [X] T025 [P] [US3] src/rover/engines/ ディレクトリを作成
- [X] T026 [P] [US3] src/rover/engines/core.py を作成（_get_*, TextWithBox, EngineResult, フィルタリング関数）
- [X] T027 [P] [US3] src/rover/engines/runners.py を作成（run_*_with_boxes, run_all_engines）
- [X] T028 [US3] src/rover/engines/__init__.py を作成（公開API re-export）
- [X] T029 [US3] 旧 src/rover/engines.py を削除

### Import更新

- [X] T030 [US3] 内部import文を更新: src/rover/*.py（engines.pyを参照する箇所）
- [X] T031 [US3] 内部import文を更新: src/cli/*.py（ocr_ensemble, rover/enginesを参照する箇所）
- [X] T032 [US3] テストのimport文を更新: tests/

### Verification

- [X] T033 `ruff check src/` がエラー0件で完了することを確認
- [X] T034 `ruff format --check src/` が変更なしで完了することを確認
- [X] T035 `make test` で全テストがパスすることを確認
- [X] T036 src/ocr_ensemble/ 配下の各ファイルが600行以下であることを確認
- [X] T037 src/rover/engines/ 配下の各ファイルが600行以下であることを確認
- [X] T038 フェーズ出力を生成: specs/011-code-refactoring/tasks/ph3-output.md

**Checkpoint**: ファイル分割完了、全テストパス、公開API維持

---

## Phase 4: User Story 2 - pre-commitフックによる自動実行 (Priority: P2)

**Goal**: pre-commitフックを設定し、コミット時に自動チェックを実行

**Independent Test**: `pre-commit run --all-files` が正常に実行される

### Input

- [X] T039 セットアップ分析を読み込み: specs/011-code-refactoring/tasks/ph1-output.md
- [X] T040 前フェーズ出力を読み込み: specs/011-code-refactoring/tasks/ph3-output.md

### Implementation

- [X] T041 [US2] .pre-commit-config.yaml を作成:
  - repo: https://github.com/astral-sh/ruff-pre-commit
  - rev: v0.9.6
  - hooks: ruff (--fix), ruff-format

### Verification

- [X] T042 `pre-commit run --all-files` が正常に完了することを確認
- [X] T043 フェーズ出力を生成: specs/011-code-refactoring/tasks/ph4-output.md

**Checkpoint**: pre-commit設定完了

---

## Phase 5: Polish & Cross-Cutting Concerns — NO TDD

**Purpose**: subagent指示の更新とクリーンアップ

### Input

- [ ] T044 セットアップ分析を読み込み: specs/011-code-refactoring/tasks/ph1-output.md
- [ ] T045 前フェーズ出力を読み込み: specs/011-code-refactoring/tasks/ph4-output.md

### Implementation

- [ ] T046 [P] .claude/agents/phase-executor.md にruff実行手順を追加:
  - コミット前に `ruff check --fix src/ && ruff format src/` を実行
- [ ] T047 [P] .claude/agents/tdd-generator.md にruff実行手順を追加:
  - コミット前に `ruff check --fix src/ && ruff format src/` を実行
- [ ] T048 quickstart.md の検証を実行

### Verification

- [ ] T049 `make test` で全テストがパスすることを確認
- [ ] T050 `ruff check src/` がエラー0件で完了することを確認
- [ ] T051 フェーズ出力を生成: specs/011-code-refactoring/tasks/ph5-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 依存なし - メインエージェント直接実行
- **User Story 1 (Phase 2)**: Phase 1 に依存
- **User Story 3 (Phase 3)**: Phase 2 に依存（FR-010: ruff修正後にファイル分割）
- **User Story 2 (Phase 4)**: Phase 3 に依存（FR-010: ファイル分割後にpre-commit）
- **Polish (Phase 5)**: Phase 4 に依存

### Agent Delegation

- **Phase 1 (Setup)**: メインエージェント直接実行
- **Phase 2-4 (US1, US3, US2)**: phase-executor（設定変更・リファクタリングのためTDD不要）
- **Phase 5 (Polish)**: phase-executor のみ

### [P] Marker (依存関係なし)

- Setup タスク [P]: 異なるファイルの確認で相互依存なし
- ファイル作成 [P]: 異なるファイルへの書き込みで相互依存なし
- Phase 間: 前 Phase 出力に依存するため [P] 不適用

---

## Phase Output Artifacts

### Directory Structure

```
specs/011-code-refactoring/
├── tasks.md                    # このファイル
├── tasks/
│   ├── ph1-output.md           # Phase 1 出力（セットアップ結果）
│   ├── ph2-output.md           # Phase 2 出力（US1 ruff設定結果）
│   ├── ph3-output.md           # Phase 3 出力（US3 ファイル分割結果）
│   ├── ph4-output.md           # Phase 4 出力（US2 pre-commit結果）
│   └── ph5-output.md           # Phase 5 出力（最終）
└── (red-tests/ なし - このfeatureはTDD不要)
```

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Phase 1 完了: Setup（現状分析）
2. Phase 2 完了: User Story 1（ruff設定 + 違反修正）
3. **STOP and VALIDATE**: `ruff check src/` がエラー0件、`make test` がパス

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
2. 各フェーズ完了時にコミット: `feat(phase-N): description`

---

## Summary

| Phase | User Story | タスク数 | 並列タスク | 独立テスト |
|-------|------------|----------|------------|------------|
| 1 | Setup | 6 | 3 | N/A |
| 2 | US1 - ruff設定 | 10 | 0 | ruff check エラー0件 |
| 3 | US3 - ファイル分割 | 22 | 8 | 600行以下 + make test |
| 4 | US2 - pre-commit | 5 | 0 | pre-commit run 成功 |
| 5 | Polish | 8 | 2 | make test + ruff check |
| **Total** | | **51** | **13** | |
