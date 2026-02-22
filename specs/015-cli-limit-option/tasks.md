# Tasks: CLIコマンドへの--limitオプション追加

**Input**: 設計ドキュメント `/specs/015-cli-limit-option/`
**Prerequisites**: plan.md, spec.md, research.md, quickstart.md

**Tests**: TDDは必須。各User StoryフェーズはTest Implementation (RED) → Implementation (GREEN) → Verificationワークフローに従う。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 依存関係なし（異なるファイル、実行順序自由）
- **[Story]**: このタスクが属するユーザーストーリー（例: US1, US2, US3）
- 説明には正確なファイルパスを含める

## User Story Summary

| ID | Title | Priority | FR | Scenario |
|----|-------|----------|----|----------|
| US1 | パイプライン全体の短時間検証 | P1 | FR-005,006,007,009,010 | make test-run LIMIT=25 |
| US2 | 個別CLIコマンドでの画像数制限 | P2 | FR-001,002,003,004 | python -m src.cli.run_ocr --limit 10 |
| US3 | エラーハンドリング | P3 | FR-008 | --limit 0, --limit -1 でエラー |

## Path Conventions

- **Project type**: Single project
- **Source**: `src/cli/`, `src/preprocessing/`, `src/layout/`, `src/rover/`, `src/`
- **Tests**: `tests/cli/`

---

## Phase 1: Setup (既存コード分析) — NO TDD

**Purpose**: 既存コードの構造理解と変更対象ファイルの特定

- [x] T001 既存CLI実装を分析: src/cli/deduplicate.py, src/cli/detect_layout.py, src/cli/run_ocr.py, src/cli/consolidate.py
- [x] T002 [P] 基盤関数を分析: src/preprocessing/deduplicate.py, src/layout/detector.py, src/rover/ensemble.py, src/consolidate.py
- [x] T003 [P] 既存テスト構造を確認: tests/ ディレクトリ
- [x] T004 [P] Makefile構造を確認: Makefile
- [x] T005 フェーズ出力を生成: specs/015-cli-limit-option/tasks/ph1-output.md

---

## Phase 2: User Story 1 - パイプライン全体の短時間検証 (Priority: P1) MVP

**Goal**: `make test-run VIDEO=xxx LIMIT=25` で全パイプラインを25枚の画像のみで実行できるようにする

**Independent Test**: `make test-run VIDEO=input.mov LIMIT=25` を実行し、全ステップが完了して出力ファイルが生成されることを確認

### Input

- [ ] T006 前フェーズ出力を読み込み: specs/015-cli-limit-option/tasks/ph1-output.md

### Test Implementation (RED)

- [ ] T007 [P] [US1] deduplicateのlimitテストを実装: tests/cli/test_deduplicate_limit.py
  - test_limit_processes_only_n_files
  - test_no_limit_processes_all_files
  - test_limit_stderr_message
- [ ] T008 [P] [US1] detect_layoutのlimitテストを実装: tests/cli/test_detect_layout_limit.py
  - test_limit_processes_only_n_pages
  - test_no_limit_processes_all_pages
- [ ] T009 [P] [US1] run_ocrのlimitテストを実装: tests/cli/test_run_ocr_limit.py
  - test_limit_processes_only_n_pages
  - test_no_limit_processes_all_pages
- [ ] T010 [P] [US1] consolidateのlimitテストを実装: tests/cli/test_consolidate_limit.py
  - test_limit_processes_only_n_files
  - test_no_limit_processes_all_files
- [ ] T011 `make test` FAILを確認 (RED)
- [ ] T012 REDテスト出力を生成: specs/015-cli-limit-option/red-tests/ph2-test.md

### Implementation (GREEN)

- [ ] T013 REDテストを読み込み: specs/015-cli-limit-option/red-tests/ph2-test.md
- [ ] T014 [P] [US1] deduplicate CLIに--limitオプションを追加: src/cli/deduplicate.py
- [ ] T015 [P] [US1] deduplicate基盤関数にlimitパラメータを追加: src/preprocessing/deduplicate.py
- [ ] T016 [P] [US1] detect_layout CLIに--limitオプションを追加: src/cli/detect_layout.py
- [ ] T017 [P] [US1] detect_layout基盤関数にlimitパラメータを追加: src/layout/detector.py
- [ ] T018 [P] [US1] run_ocr CLIに--limitオプションを追加: src/cli/run_ocr.py
- [ ] T019 [P] [US1] run_ocr基盤関数にlimitパラメータを追加: src/rover/ensemble.py
- [ ] T020 [P] [US1] consolidate CLIに--limitオプションを追加: src/cli/consolidate.py
- [ ] T021 [P] [US1] consolidate基盤関数にlimitパラメータを追加: src/consolidate.py
- [ ] T022 [US1] Makefileにtest-runターゲットを追加: Makefile
- [ ] T023 `make test` PASSを確認 (GREEN)

### Verification

- [ ] T024 `make test` で全テストがパスすることを確認（リグレッションなし）
- [ ] T025 フェーズ出力を生成: specs/015-cli-limit-option/tasks/ph2-output.md

**Checkpoint**: User Story 1が完全に機能し、独立してテスト可能

---

## Phase 3: User Story 2 - 個別CLIコマンドでの画像数制限 (Priority: P2)

**Goal**: 個別のCLIコマンドを`--limit N`で実行し、N個のファイルのみが処理されることを確認

**Independent Test**: `python -m src.cli.run_ocr output/pages -o output/ocr --limit 10` を実行し、10件のOCR結果のみが生成されることを確認

### Input

- [ ] T026 セットアップ分析を読み込み: specs/015-cli-limit-option/tasks/ph1-output.md
- [ ] T027 前フェーズ出力を読み込み: specs/015-cli-limit-option/tasks/ph2-output.md

### Test Implementation (RED)

- [ ] T028 [P] [US2] 後方互換性テストを追加: tests/cli/test_limit_backward_compat.py
  - test_deduplicate_without_limit_processes_all
  - test_detect_layout_without_limit_processes_all
  - test_run_ocr_without_limit_processes_all
  - test_consolidate_without_limit_processes_all
- [ ] T029 [P] [US2] limit > 画像数のエッジケーステストを追加: tests/cli/test_limit_edge_cases.py
  - test_limit_greater_than_file_count
  - test_limit_one_file
- [ ] T030 `make test` FAILを確認 (RED)
- [ ] T031 REDテスト出力を生成: specs/015-cli-limit-option/red-tests/ph3-test.md

### Implementation (GREEN)

- [ ] T032 REDテストを読み込み: specs/015-cli-limit-option/red-tests/ph3-test.md
- [ ] T033 [US2] エッジケース対応を確認・調整（必要に応じて）: src/cli/*.py
- [ ] T034 `make test` PASSを確認 (GREEN)

### Verification

- [ ] T035 `make test` で全テストがパスすることを確認（US1含む）
- [ ] T036 フェーズ出力を生成: specs/015-cli-limit-option/tasks/ph3-output.md

**Checkpoint**: User Story 1 AND 2 が両方独立して動作

---

## Phase 4: User Story 3 - エラーハンドリング (Priority: P3)

**Goal**: `--limit 0` や `--limit -1` など不正な値に対して適切なエラーメッセージを表示

**Independent Test**: `--limit 0` を指定してエラーメッセージを確認

### Input

- [ ] T037 セットアップ分析を読み込み: specs/015-cli-limit-option/tasks/ph1-output.md
- [ ] T038 前フェーズ出力を読み込み: specs/015-cli-limit-option/tasks/ph3-output.md

### Test Implementation (RED)

- [ ] T039 [P] [US3] バリデーションエラーテストを追加: tests/cli/test_limit_validation.py
  - test_limit_zero_returns_error
  - test_limit_negative_returns_error
  - test_limit_non_integer_argparse_error
- [ ] T040 `make test` FAILを確認 (RED)
- [ ] T041 REDテスト出力を生成: specs/015-cli-limit-option/red-tests/ph4-test.md

### Implementation (GREEN)

- [ ] T042 REDテストを読み込み: specs/015-cli-limit-option/red-tests/ph4-test.md
- [ ] T043 [P] [US3] deduplicate CLIにlimitバリデーションを追加: src/cli/deduplicate.py
- [ ] T044 [P] [US3] detect_layout CLIにlimitバリデーションを追加: src/cli/detect_layout.py
- [ ] T045 [P] [US3] run_ocr CLIにlimitバリデーションを追加: src/cli/run_ocr.py
- [ ] T046 [P] [US3] consolidate CLIにlimitバリデーションを追加: src/cli/consolidate.py
- [ ] T047 `make test` PASSを確認 (GREEN)

### Verification

- [ ] T048 `make test` で全テストがパスすることを確認（US1, US2, US3含む）
- [ ] T049 フェーズ出力を生成: specs/015-cli-limit-option/tasks/ph4-output.md

**Checkpoint**: 全User Storyが完全に機能

---

## Phase 5: Polish & Cross-Cutting Concerns — NO TDD

**Purpose**: ドキュメント更新、コードクリーンアップ、最終検証

### Input

- [ ] T050 セットアップ分析を読み込み: specs/015-cli-limit-option/tasks/ph1-output.md
- [ ] T051 前フェーズ出力を読み込み: specs/015-cli-limit-option/tasks/ph4-output.md

### Implementation

- [ ] T052 [P] 各CLIの--helpメッセージを確認・調整
- [ ] T053 [P] quickstart.mdの手順で動作確認
- [ ] T054 [P] コードスタイル確認: `ruff check src/cli/`
- [ ] T055 カバレッジ確認: `make test-cov` ≥80%

### Verification

- [ ] T056 `make test` で全テストがパスすることを確認
- [ ] T057 フェーズ出力を生成: specs/015-cli-limit-option/tasks/ph5-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 依存なし - メインエージェント直接実行
- **User Stories (Phase 2-4)**: TDDフロー (tdd-generator → phase-executor)
  - Phase 2 (US1) → Phase 3 (US2) → Phase 4 (US3) の順に実行
- **Polish (Phase 5)**: 全User Story完了後 - phase-executorのみ

### Within Each User Story Phase (TDD Flow)

1. **Input**: セットアップ分析 (ph1) + 前フェーズ出力を読み込み
2. **Test Implementation (RED)**: テストを先に書く → `make test` FAILを確認 → RED出力生成
3. **Implementation (GREEN)**: REDテストを読む → 実装 → `make test` PASSを確認
4. **Verification**: リグレッションなしを確認 → フェーズ出力生成

### Agent Delegation

- **Phase 1 (Setup)**: メインエージェント直接実行
- **Phase 2-4 (User Stories)**: tdd-generator (RED) → phase-executor (GREEN + Verification)
- **Phase 5 (Polish)**: phase-executorのみ

### [P] Marker (No Dependencies)

`[P]` は「他タスクへの依存なし、実行順序自由」を示す。並列実行を保証するものではない。

- Setupタスク [P]: 異なるファイル/ディレクトリの分析で相互依存なし
- REDテスト [P]: 異なるテストファイルへの書き込みで相互依存なし
- GREEN実装 [P]: 異なるソースファイルへの書き込みで相互依存なし

---

## Phase Output & RED Test Artifacts

### Directory Structure

```
specs/015-cli-limit-option/
├── tasks.md                    # このファイル
├── tasks/
│   ├── ph1-output.md           # Phase 1出力 (Setup結果)
│   ├── ph2-output.md           # Phase 2出力 (US1 GREEN結果)
│   ├── ph3-output.md           # Phase 3出力 (US2 GREEN結果)
│   ├── ph4-output.md           # Phase 4出力 (US3 GREEN結果)
│   └── ph5-output.md           # Phase 5出力 (Polish結果)
└── red-tests/
    ├── ph2-test.md             # Phase 2 REDテスト結果 (FAIL確認)
    ├── ph3-test.md             # Phase 3 REDテスト結果 (FAIL確認)
    └── ph4-test.md             # Phase 4 REDテスト結果 (FAIL確認)
```

### Phase Output Content

各 `phN-output.md` に含める内容:
- 実行したことの概要
- 作成/変更したファイル
- テスト結果 (`make test` 出力)
- 計画からの逸脱や決定事項

### RED Test Output Content

各 `phN-test.md` に含める内容:
- 書いたテストコード
- `make test` 出力（FAIL確認）
- 失敗したテストの数と名前

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Phase 1完了: Setup (既存コード分析)
2. Phase 2完了: User Story 1 (RED → GREEN → Verification)
3. **停止して検証**: `make test` で全テストパスを確認
4. 手動テスト: `make test-run VIDEO=xxx LIMIT=25` で動作確認

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
2. 各フェーズでコミット: `feat(phase-N): description`

---

## Test Coverage Rules

**境界テスト原則**: データ変換が発生する**すべての境界**でテストを書く

```
[入力] → [ファイルリスト取得] → [スライス] → [処理] → [出力]
   ↓            ↓               ↓         ↓        ↓
 Test         Test            Test      Test     Test
```

**チェックリスト**:
- [ ] ファイルリスト取得テスト
- [ ] --limit適用テスト
- [ ] 出力ファイル数確認テスト
- [ ] 後方互換性テスト

---

## Notes

- [P] タスク = 依存なし、実行順序自由
- [Story] ラベル = 特定のUser Storyへのマッピング
- 各User Storyは独立して完成・テスト可能
- TDD: Test Implementation (RED) → FAIL確認 → Implementation (GREEN) → PASS確認
- RED出力は実装開始前に生成必須
- 各フェーズ完了後にコミット
- 任意のCheckpointで停止してStoryを独立検証可能
- 避けること: 曖昧なタスク、同一ファイル競合、Story間の独立性を壊す依存
