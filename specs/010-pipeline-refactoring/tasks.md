# Tasks: パイプライン・リファクタリング

**Input**: 設計ドキュメント `/specs/010-pipeline-refactoring/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: TDDは User Story フェーズで必須。Test Implementation (RED) → Implementation (GREEN) → Verification のワークフローに従う。

**Language**: 日本語

**Organization**: 各ユーザーストーリーごとにタスクをグループ化し、独立した実装とテストを可能にする。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 依存関係なし（異なるファイル、実行順序自由）
- **[Story]**: タスクが属するユーザーストーリー（例: US1, US2, US3）
- 説明に正確なファイルパスを含める

## User Story Summary

| ID | Title | Priority | FR | シナリオ |
|----|-------|----------|----|----------|
| US1 | 個別スクリプトの独立実行 | P1 | FR-001, FR-002, FR-008 | CLIスクリプト分解 |
| US2 | 命名規則の統一 | P2 | FR-003 | rover統一 |
| US3 | フォルダ構造の整理 | P2 | FR-004 | 機能別サブパッケージ |
| US4 | 後方互換性コードの除去 | P2 | FR-005 | fallback削除 |
| US5 | ワークフロー手順書の作成 | P3 | FR-006, FR-007 | 手順書作成 |

## Path Conventions

- **Single project**: `src/`, `tests/`（リポジトリルート）
- 新構造: `src/cli/`, `src/rover/`, `src/preprocessing/`, `src/layout/`

---

## Phase 1: Setup（現状分析） — NO TDD

**Purpose**: 現在の実装を確認し、変更の準備を行う

- [X] T001 現在の pipeline.py を読み込み、ステップ構造を分析: src/pipeline.py
- [X] T002 [P] 現在の extract_frames.py を確認: src/extract_frames.py
- [X] T003 [P] 現在の deduplicate.py を確認: src/deduplicate.py
- [X] T004 [P] 現在の split_spread.py を確認: src/split_spread.py
- [X] T005 [P] 現在の ocr_yomitoku.py（レイアウト検出）を確認: src/ocr_yomitoku.py
- [X] T006 [P] 現在の ocr_rover.py を確認: src/ocr_rover.py
- [X] T007 [P] 現在の consolidate.py を確認: src/consolidate.py
- [X] T008 [P] 既存テストを確認: tests/
- [X] T009 「yomitoku」「rover-ocr」の使用箇所を特定: src/
- [X] T010 後方互換性フォールバックコードを特定: src/
- [X] T011 `make test` を実行して現在のテスト状態を確認
- [X] T012 フェーズ出力を生成: specs/010-pipeline-refactoring/tasks/ph1-output.md

---

## Phase 2: User Story 1 - 個別スクリプトの独立実行 (Priority: P1) MVP

**Goal**: pipeline.py を6つの独立CLIスクリプトに分解する

**Independent Test**: 各スクリプトを `python -m src.cli.<script>` で単独実行し、期待される出力が生成されることを確認

### Input

- [x] T013 前フェーズ出力を読み込み: specs/010-pipeline-refactoring/tasks/ph1-output.md

### Test Implementation (RED)

- [x] T014 [P] [US1] CLI extract_frames のテストを実装: tests/cli/test_extract_frames.py
- [x] T015 [P] [US1] CLI deduplicate のテストを実装: tests/cli/test_deduplicate.py
- [x] T016 [P] [US1] CLI split_spreads のテストを実装: tests/cli/test_split_spreads.py
- [x] T017 [P] [US1] CLI detect_layout のテストを実装: tests/cli/test_detect_layout.py
- [x] T018 [P] [US1] CLI run_ocr のテストを実装: tests/cli/test_run_ocr.py
- [x] T019 [P] [US1] CLI consolidate のテストを実装: tests/cli/test_consolidate.py
- [x] T020 [P] [US1] 入力不存在時のエラーメッセージテストを実装: tests/cli/test_error_handling.py
- [x] T021 `make test` FAIL を確認 (RED)
- [x] T022 RED出力を生成: specs/010-pipeline-refactoring/red-tests/ph2-test.md

### Implementation (GREEN)

- [x] T023 REDテストを読み込み: specs/010-pipeline-refactoring/red-tests/ph2-test.md
- [x] T024 [P] [US1] src/cli/__init__.py を作成
- [x] T025 [P] [US1] CLI extract_frames を実装: src/cli/extract_frames.py
- [x] T026 [P] [US1] CLI deduplicate を実装: src/cli/deduplicate.py
- [x] T027 [P] [US1] CLI split_spreads を実装: src/cli/split_spreads.py
- [x] T028 [P] [US1] CLI detect_layout を実装: src/cli/detect_layout.py
- [x] T029 [P] [US1] CLI run_ocr を実装: src/cli/run_ocr.py
- [x] T030 [P] [US1] CLI consolidate を実装: src/cli/consolidate.py
- [x] T031 `make test` PASS を確認 (GREEN)

### Verification

- [x] T032 `make test` で全テストがパスすることを確認
- [x] T033 各CLIスクリプトを手動実行してエラーがないことを確認
- [x] T034 フェーズ出力を生成: specs/010-pipeline-refactoring/tasks/ph2-output.md

**Checkpoint**: 6つのCLIスクリプトが独立して実行可能

---

## Phase 3: User Story 2 - 命名規則の統一 (Priority: P2)

**Goal**: 「yomitoku」「rover-ocr」などの名称を「rover」に統一

**Independent Test**: grep で旧名称が0件、新名称が正しく使用されていることを確認

### Input

- [x] T035 セットアップ分析を読み込み: specs/010-pipeline-refactoring/tasks/ph1-output.md
- [x] T036 前フェーズ出力を読み込み: specs/010-pipeline-refactoring/tasks/ph2-output.md

### Test Implementation (RED)

- [x] T037 [P] [US2] 命名規則検証テストを実装: tests/test_naming_convention.py
- [x] T038 `make test` FAIL を確認 (RED)
- [x] T039 RED出力を生成: specs/010-pipeline-refactoring/red-tests/ph3-test.md

### Implementation (GREEN)

- [ ] T040 REDテストを読み込み: specs/010-pipeline-refactoring/red-tests/ph3-test.md
- [ ] T041 [P] [US2] 変数名 yomitoku_device → device にリネーム: src/cli/*.py
- [ ] T042 [P] [US2] 関数名の「yomitoku」「rover_ocr」を統一: src/
- [ ] T043 [P] [US2] コメント・docstring の名称を更新: src/
- [ ] T044 [US2] インポート文を更新: src/
- [ ] T045 `make test` PASS を確認 (GREEN)

### Verification

- [ ] T046 `make test` で全テストがパスすることを確認
- [ ] T047 `grep -r "yomitoku\|rover-ocr" src/` が0件であることを確認
- [ ] T048 フェーズ出力を生成: specs/010-pipeline-refactoring/tasks/ph3-output.md

**Checkpoint**: 命名規則が統一され、全テストがパス

---

## Phase 4: User Story 3 - フォルダ構造の整理 (Priority: P2)

**Goal**: src/ を機能別サブパッケージに再構成

**Independent Test**: 新しいimportパスで全テストがパスすることを確認

### Input

- [ ] T049 セットアップ分析を読み込み: specs/010-pipeline-refactoring/tasks/ph1-output.md
- [ ] T050 前フェーズ出力を読み込み: specs/010-pipeline-refactoring/tasks/ph3-output.md

### Test Implementation (RED)

- [ ] T051 [P] [US3] 新パッケージ構造のインポートテストを実装: tests/test_package_structure.py
- [ ] T052 `make test` FAIL を確認 (RED)
- [ ] T053 RED出力を生成: specs/010-pipeline-refactoring/red-tests/ph4-test.md

### Implementation (GREEN)

- [ ] T054 REDテストを読み込み: specs/010-pipeline-refactoring/red-tests/ph4-test.md
- [ ] T055 [P] [US3] src/preprocessing/__init__.py を作成
- [ ] T056 [P] [US3] src/preprocessing/frames.py を作成（extract_frames.pyから移動）
- [ ] T057 [P] [US3] src/preprocessing/deduplicate.py を作成
- [ ] T058 [P] [US3] src/preprocessing/split_spread.py を作成
- [ ] T059 [P] [US3] src/preprocessing/hash.py を作成（video_hash.pyから移動）
- [ ] T060 [P] [US3] src/layout/__init__.py を作成
- [ ] T061 [P] [US3] src/layout/detector.py を作成（ocr_yomitoku.pyのレイアウト部分）
- [ ] T062 [P] [US3] src/layout/figures.py を作成（detect_figures.pyから移動）
- [ ] T063 [P] [US3] src/layout/reading_order.py を作成
- [ ] T064 [P] [US3] src/rover/__init__.py を作成
- [ ] T065 [P] [US3] src/rover/ensemble.py を作成（ocr_rover.pyから移動）
- [ ] T066 [P] [US3] src/rover/engines.py を作成（ocr_engines.pyから移動）
- [ ] T067 [P] [US3] src/rover/alignment.py を作成（ocr_alignment.pyから移動）
- [ ] T068 [P] [US3] src/rover/output.py を作成（ocr_output.pyから移動）
- [ ] T069 [US3] 全ファイルのインポート文を新しいパスに更新
- [ ] T070 [US3] CLIスクリプトのインポートを更新: src/cli/*.py
- [ ] T071 [US3] テストのインポートを更新: tests/
- [ ] T072 `make test` PASS を確認 (GREEN)

### Verification

- [ ] T073 `make test` で全テストがパスすることを確認
- [ ] T074 src/ 直下のファイル数が減少していることを確認
- [ ] T075 フェーズ出力を生成: specs/010-pipeline-refactoring/tasks/ph4-output.md

**Checkpoint**: 機能別サブパッケージ構造が完成、全テストがパス

---

## Phase 5: User Story 4 - 後方互換性コードの除去 (Priority: P2)

**Goal**: 不要な後方互換性フォールバックコードを除去

**Independent Test**: フォールバックコード除去後も全機能が動作し、テストがパス

### Input

- [ ] T076 セットアップ分析を読み込み: specs/010-pipeline-refactoring/tasks/ph1-output.md
- [ ] T077 前フェーズ出力を読み込み: specs/010-pipeline-refactoring/tasks/ph4-output.md

### Test Implementation (RED)

- [ ] T078 [P] [US4] ENGINE_PRIORITY["FALLBACK"] → "DEFAULT" の移行テスト: tests/test_fallback_removal.py
- [ ] T079 [P] [US4] book_converter/parser.py のレガシーパターン除去テスト: tests/book_converter/test_parser.py
- [ ] T080 `make test` FAIL を確認 (RED)
- [ ] T081 RED出力を生成: specs/010-pipeline-refactoring/red-tests/ph5-test.md

### Implementation (GREEN)

- [ ] T082 REDテストを読み込み: specs/010-pipeline-refactoring/red-tests/ph5-test.md
- [ ] T083 [P] [US4] ENGINE_PRIORITY["FALLBACK"] を "DEFAULT" にリネーム: src/rover/engines.py
- [ ] T084 [P] [US4] book_converter/parser.py:584 のレガシーパターンを除去
- [ ] T085 [US4] 関連する呼び出し箇所を更新
- [ ] T086 `make test` PASS を確認 (GREEN)

### Verification

- [ ] T087 `make test` で全テストがパスすることを確認
- [ ] T088 `grep -r "backward compat\|legacy" src/` が0件であることを確認
- [ ] T089 フェーズ出力を生成: specs/010-pipeline-refactoring/tasks/ph5-output.md

**Checkpoint**: 後方互換性コードが除去され、全テストがパス

---

## Phase 6: User Story 5 - ワークフロー手順書の作成 (Priority: P3)

**Goal**: 動画からXMLまでの完全なワークフロー手順書を作成

**Independent Test**: 手順書に従って新しい動画を処理し、最終出力が生成されることを確認

### Input

- [ ] T090 セットアップ分析を読み込み: specs/010-pipeline-refactoring/tasks/ph1-output.md
- [ ] T091 前フェーズ出力を読み込み: specs/010-pipeline-refactoring/tasks/ph5-output.md

### Implementation（ドキュメント作成 - TDDなし）

- [ ] T092 [US5] WORKFLOW.md を作成: docs/WORKFLOW.md
- [ ] T093 [US5] 各CLIコマンドの使用例を追加: docs/WORKFLOW.md
- [ ] T094 [US5] Markdownマーカー追加手順を追加: docs/WORKFLOW.md
- [ ] T095 [US5] トラブルシューティングセクションを追加: docs/WORKFLOW.md

### Verification

- [ ] T096 手順書に従って動画を処理できることを手動確認
- [ ] T097 フェーズ出力を生成: specs/010-pipeline-refactoring/tasks/ph6-output.md

**Checkpoint**: ワークフロー手順書が完成

---

## Phase 7: Polish & Cross-Cutting Concerns — NO TDD

**Purpose**: 旧ファイルの削除とクリーンアップ

### Input

- [ ] T098 セットアップ分析を読み込み: specs/010-pipeline-refactoring/tasks/ph1-output.md
- [ ] T099 前フェーズ出力を読み込み: specs/010-pipeline-refactoring/tasks/ph6-output.md

### Implementation

- [ ] T100 [P] 旧 pipeline.py を削除（機能は cli/ に移行済み）
- [ ] T101 [P] 旧 src/extract_frames.py を削除（preprocessing/ に移行済み）
- [ ] T102 [P] 旧 src/deduplicate.py を削除
- [ ] T103 [P] 旧 src/split_spread.py を削除
- [ ] T104 [P] 旧 src/video_hash.py を削除
- [ ] T105 [P] 旧 src/ocr_yomitoku.py を削除（layout/ に移行済み）
- [ ] T106 [P] 旧 src/detect_figures.py を削除
- [ ] T107 [P] 旧 src/reading_order.py を削除
- [ ] T108 [P] 旧 src/ocr_rover.py を削除（rover/ に移行済み）
- [ ] T109 [P] 旧 src/ocr_engines.py を削除
- [ ] T110 [P] 旧 src/ocr_alignment.py を削除
- [ ] T111 [P] 旧 src/ocr_output.py を削除
- [ ] T112 [P] 不要になったテストファイルを削除
- [ ] T113 quickstart.md の検証を実行

### Verification

- [ ] T114 `make test` で全テストがパスすることを確認
- [ ] T115 src/ 直下に残っているのは utils.py, __init__.py, book_converter/, cli/, rover/, preprocessing/, layout/ のみ
- [ ] T116 フェーズ出力を生成: specs/010-pipeline-refactoring/tasks/ph7-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 依存なし - メインエージェント直接実行
- **User Stories (Phase 2-6)**: TDDフロー (tdd-generator → phase-executor)
  - Phase 2 (US1): Phase 1 に依存
  - Phase 3 (US2): Phase 2 に依存
  - Phase 4 (US3): Phase 3 に依存
  - Phase 5 (US4): Phase 4 に依存
  - Phase 6 (US5): Phase 5 に依存（ドキュメントのみ、TDDなし）
- **Polish (Phase 7)**: 全ユーザーストーリーに依存 - phase-executor のみ

### Within Each User Story Phase (TDD Flow)

1. **Input**: セットアップ分析 (ph1) + 前フェーズ出力を読み込み
2. **Test Implementation (RED)**: テストを先に書く → `make test` FAIL を確認 → RED出力を生成
3. **Implementation (GREEN)**: REDテストを読む → 実装 → `make test` PASS を確認
4. **Verification**: リグレッションなしを確認 → フェーズ出力を生成

### Agent Delegation

- **Phase 1 (Setup)**: メインエージェント直接実行
- **Phase 2-5 (US1-US4)**: tdd-generator (RED) → phase-executor (GREEN + Verification)
- **Phase 6 (US5)**: phase-executor のみ（ドキュメント作成）
- **Phase 7 (Polish)**: phase-executor のみ

### [P] Marker (依存関係なし)

- Setup タスク [P]: 異なるファイル/ディレクトリの確認で相互依存なし
- RED テスト [P]: 異なるテストファイルへの書き込みで相互依存なし
- GREEN 実装 [P]: 異なるソースファイルへの書き込みで相互依存なし
- User Story 間: 各 Phase は前 Phase 出力に依存するため [P] 不適用

---

## Phase Output & RED Test Artifacts

### Directory Structure

```
specs/010-pipeline-refactoring/
├── tasks.md                    # このファイル
├── tasks/
│   ├── ph1-output.md           # Phase 1 出力（セットアップ結果）
│   ├── ph2-output.md           # Phase 2 出力（US1 GREEN 結果）
│   ├── ph3-output.md           # Phase 3 出力（US2 GREEN 結果）
│   ├── ph4-output.md           # Phase 4 出力（US3 GREEN 結果）
│   ├── ph5-output.md           # Phase 5 出力（US4 GREEN 結果）
│   ├── ph6-output.md           # Phase 6 出力（US5 結果）
│   └── ph7-output.md           # Phase 7 出力（最終）
└── red-tests/
    ├── ph2-test.md             # Phase 2 RED テスト結果
    ├── ph3-test.md             # Phase 3 RED テスト結果
    ├── ph4-test.md             # Phase 4 RED テスト結果
    └── ph5-test.md             # Phase 5 RED テスト結果
```

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Phase 1 完了: Setup（現状分析）
2. Phase 2 完了: User Story 1（CLIスクリプト分解）— RED → GREEN → Verification
3. **STOP and VALIDATE**: `make test` で全テストがパスすることを確認
4. 各CLIスクリプトを手動実行して検証

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7
2. 各フェーズ完了時にコミット: `feat(phase-N): description`

---

## Summary

| Phase | User Story | タスク数 | 並列タスク | 独立テスト |
|-------|------------|----------|------------|------------|
| 1 | Setup | 12 | 8 | N/A |
| 2 | US1 - CLIスクリプト分解 | 22 | 14 | 各CLI単独実行 |
| 3 | US2 - 命名規則統一 | 14 | 4 | grep で旧名称0件 |
| 4 | US3 - フォルダ構造整理 | 27 | 15 | 新importパスでテストパス |
| 5 | US4 - 後方互換性除去 | 14 | 4 | fallbackなしで動作 |
| 6 | US5 - 手順書作成 | 8 | 0 | 手順書で動画処理成功 |
| 7 | Polish | 19 | 12 | 全テストパス |
| **Total** | | **116** | **57** | |
