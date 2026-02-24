# Tasks: Spread モード明示指定と Trim 制御の拡張

**Input**: Design documents from `/specs/018-spread-mode-trim/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: TDD は User Story フェーズで必須。各フェーズは Test Implementation (RED) → Implementation (GREEN) → Verification のワークフローに従う。

**Organization**: タスクはユーザーストーリーごとにグループ化され、各ストーリーの独立した実装とテストを可能にする。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 依存関係なし（異なるファイル、実行順序自由）
- **[Story]**: タスクが属するユーザーストーリー（例: US1, US2, US3）
- 説明には正確なファイルパスを含める

## User Story Summary

| ID | Title | Priority | FR | Scenarios |
|----|-------|----------|----|-----------|
| US1 | Spread モード明示指定 | P1 | FR-001〜005 | 5 |
| US2 | 2段階 Trim 制御 | P2 | FR-006〜009 | 4 |
| US3 | パイプライン統合とプレビュー | P3 | FR-010〜014 | 5 |

## Path Conventions

- **Source**: `src/preprocessing/split_spread.py`, `src/cli/split_spreads.py`
- **Tests**: `tests/preprocessing/test_split_spread.py`
- **Config**: `config.yaml`, `Makefile`

---

## Phase 1: Setup（既存コード分析）— NO TDD

**Purpose**: 既存実装の確認と変更準備

- [x] T001 既存実装を確認: src/preprocessing/split_spread.py
- [x] T002 [P] 既存CLIを確認: src/cli/split_spreads.py
- [x] T003 [P] 既存設定を確認: config.yaml
- [x] T004 [P] 既存Makefileを確認: Makefile（split-spreads ターゲット）
- [x] T005 [P] 既存テストを確認: tests/preprocessing/（存在しない）
- [x] T006 Edit: specs/018-spread-mode-trim/tasks/ph1-output.md

---

## Phase 2: User Story 1 - Spread モード明示指定 (Priority: P1) MVP

**Goal**: `--mode` オプションで single/spread を明示的に指定可能にする

**Independent Test**: `--mode=spread` で見開き画像が分割され、`--mode=single` で分割されないことを確認

### Input

- [x] T007 前フェーズの出力を読む: specs/018-spread-mode-trim/tasks/ph1-output.md

### Test Implementation (RED)

- [x] T008 [P] [US1] mode=single でコピーのみのテスト実装: tests/preprocessing/test_split_spread.py
- [x] T009 [P] [US1] mode=spread で常に分割のテスト実装: tests/preprocessing/test_split_spread.py
- [x] T010 [P] [US1] デフォルト mode=single のテスト実装: tests/preprocessing/test_split_spread.py
- [x] T011 [P] [US1] 環境変数 SPREAD_MODE 読み込みのテスト実装: tests/preprocessing/test_split_spread.py
- [x] T012 [P] [US1] CLI引数が環境変数より優先されるテスト実装: tests/preprocessing/test_split_spread.py
- [x] T013 [P] [US1] モード表示（stdout）のテスト実装: tests/preprocessing/test_split_spread.py
- [x] T014 `make test` で FAIL を確認 (RED)
- [x] T015 RED 出力を生成: specs/018-spread-mode-trim/red-tests/ph2-test.md

### Implementation (GREEN)

- [x] T016 RED テストを読む: specs/018-spread-mode-trim/red-tests/ph2-test.md
- [x] T017 [P] [US1] SpreadMode enum を追加: src/preprocessing/split_spread.py
- [x] T018 [P] [US1] split_spread_pages() に mode 引数を追加: src/preprocessing/split_spread.py
- [x] T019 [P] [US1] get_spread_mode() 関数を追加（環境変数/デフォルト）: src/preprocessing/split_spread.py
- [x] T020 [US1] モード表示ロジックを追加: src/preprocessing/split_spread.py
- [x] T021 [P] [US1] CLI に --mode 引数を追加: src/cli/split_spreads.py
- [x] T022 [P] [US1] config.yaml に spread_mode 設定を追加: config.yaml
- [x] T023 [P] [US1] Makefile に SPREAD_MODE 変数を追加: Makefile
- [x] T024 `make test` で PASS を確認 (GREEN)

### Verification

- [x] T025 `make test` で全テスト通過を確認（リグレッションなし）
- [x] T026 検証用動画でテスト: movies/n3-failers-in-developing-softwear.mov (spread)
- [x] T027 検証用動画でテスト: movies/n5-sre.mov (single)
- [x] T028 Edit: specs/018-spread-mode-trim/tasks/ph2-output.md

**Checkpoint**: US1 は独立して機能し、テスト可能であること

---

## Phase 3: User Story 2 - 2段階 Trim 制御 (Priority: P2)

**Goal**: 分割前に全体画像に対して上下左右のトリミング（global-trim）を適用可能にする

**Independent Test**: `--global-trim-*` オプションで画像がトリミングされ、分割後に `--left-trim` / `--right-trim` が適用されることを確認

### Input

- [x] T029 Setup 分析を読む: specs/018-spread-mode-trim/tasks/ph1-output.md
- [x] T030 前フェーズの出力を読む: specs/018-spread-mode-trim/tasks/ph2-output.md

### Test Implementation (RED)

- [x] T031 [P] [US2] global-trim-top/bottom 適用のテスト実装: tests/preprocessing/test_split_spread.py
- [x] T032 [P] [US2] global-trim-left/right 適用のテスト実装: tests/preprocessing/test_split_spread.py
- [x] T033 [P] [US2] global-trim → split-trim の順序テスト実装: tests/preprocessing/test_split_spread.py
- [x] T034 [P] [US2] 単ページモードでの global-trim テスト実装: tests/preprocessing/test_split_spread.py
- [x] T035 [P] [US2] trim 値範囲外（0.5以上）エラーテスト実装: tests/preprocessing/test_split_spread.py
- [x] T036 `make test` で FAIL を確認 (RED)
- [x] T037 RED 出力を生成: specs/018-spread-mode-trim/red-tests/ph3-test.md

### Implementation (GREEN)

- [x] T038 RED テストを読む: specs/018-spread-mode-trim/red-tests/ph3-test.md
- [x] T039 [P] [US2] TrimConfig dataclass を追加: src/preprocessing/split_spread.py
- [x] T040 [P] [US2] apply_global_trim() 関数を追加: src/preprocessing/split_spread.py
- [x] T041 [P] [US2] validate_trim_value() 関数を追加: src/preprocessing/split_spread.py
- [x] T042 [US2] split_spread_pages() に global-trim 統合: src/preprocessing/split_spread.py
- [x] T043 [P] [US2] CLI に --global-trim-* 引数を追加: src/cli/split_spreads.py
- [x] T044 [P] [US2] config.yaml に global_trim_* 設定を追加: config.yaml
- [x] T045 [P] [US2] Makefile に GLOBAL_TRIM_* 変数を追加: Makefile
- [x] T046 `make test` で PASS を確認 (GREEN)

### Verification

- [x] T047 `make test` で全テスト通過を確認（US1 含むリグレッションなし）
- [x] T048 Edit: specs/018-spread-mode-trim/tasks/ph3-output.md

**Checkpoint**: US1 および US2 が独立して機能すること

---

## Phase 4: User Story 3 - パイプライン統合とプレビュー (Priority: P3)

**Goal**: 2段階プレビュー（preview-extract / preview-trim）と make run への統合

**Independent Test**: `make preview-extract` でフレーム抽出、`make preview-trim` で trim 適用（フレーム再抽出なし）を確認

### Input

- [ ] T049 Setup 分析を読む: specs/018-spread-mode-trim/tasks/ph1-output.md
- [ ] T050 前フェーズの出力を読む: specs/018-spread-mode-trim/tasks/ph3-output.md

### Test Implementation (RED)

- [ ] T051 [P] [US3] preview-extract ターゲットのテスト実装: tests/test_makefile_targets.py
- [ ] T052 [P] [US3] preview-trim ターゲットのテスト実装: tests/test_makefile_targets.py
- [ ] T053 [P] [US3] preview/ 空時のエラーハンドリングテスト実装: tests/preprocessing/test_split_spread.py
- [ ] T054 [P] [US3] make run に split-spreads 統合のテスト実装: tests/test_makefile_targets.py
- [ ] T055 `make test` で FAIL を確認 (RED)
- [ ] T056 RED 出力を生成: specs/018-spread-mode-trim/red-tests/ph4-test.md

### Implementation (GREEN)

- [ ] T057 RED テストを読む: specs/018-spread-mode-trim/red-tests/ph4-test.md
- [ ] T058 [P] [US3] Makefile に preview-extract ターゲットを追加: Makefile
- [ ] T059 [P] [US3] Makefile に preview-trim ターゲットを追加: Makefile
- [ ] T060 [US3] split_spreads.py に preview/ ディレクトリ確認ロジックを追加: src/cli/split_spreads.py
- [ ] T061 [US3] Makefile の run ターゲットに split-spreads ステップを追加: Makefile
- [ ] T062 `make test` で PASS を確認 (GREEN)

### Verification

- [ ] T063 `make test` で全テスト通過を確認（US1, US2 含むリグレッションなし）
- [ ] T064 `make preview-extract VIDEO=movies/n3-failers-in-developing-softwear.mov LIMIT=3` で動作確認
- [ ] T065 `make preview-trim` で trim プレビュー確認
- [ ] T066 Edit: specs/018-spread-mode-trim/tasks/ph4-output.md

**Checkpoint**: 全ユーザーストーリーが独立して機能すること

---

## Phase 5: Polish & クロスカッティング — NO TDD

**Purpose**: 最終調整とドキュメント更新

### Input

- [ ] T067 Setup 分析を読む: specs/018-spread-mode-trim/tasks/ph1-output.md
- [ ] T068 前フェーズの出力を読む: specs/018-spread-mode-trim/tasks/ph4-output.md

### Implementation

- [ ] T069 [P] 廃止予定の is_spread_image() 関数に deprecation warning を追加（互換性のため残す）: src/preprocessing/split_spread.py
- [ ] T070 [P] config.yaml の spread_aspect_ratio 設定を非推奨コメント追加: config.yaml
- [ ] T071 [P] quickstart.md の検証: specs/018-spread-mode-trim/quickstart.md
- [ ] T072 [P] CLAUDE.md に config.yaml 設定項目を追加: CLAUDE.md

### Verification

- [ ] T073 `make test` で全テスト通過を最終確認
- [ ] T074 `make lint` で lint エラーなしを確認
- [ ] T075 Edit: specs/018-spread-mode-trim/tasks/ph5-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 依存なし - メインエージェント直接実行
- **User Stories (Phase 2-4)**: TDD フロー（speckit:tdd-generator → speckit:phase-executor）
  - US1 (Phase 2) → US2 (Phase 3) → US3 (Phase 4) の順で実行
- **Polish (Phase 5)**: 全ユーザーストーリー完了後 - speckit:phase-executor のみ

### Within Each User Story Phase (TDD Flow)

1. **Input**: Setup 分析 (ph1) + 前フェーズ出力を読む
2. **Test Implementation (RED)**: テストを先に書く → `make test` FAIL を確認 → RED 出力生成
3. **Implementation (GREEN)**: RED テストを読む → 実装 → `make test` PASS を確認
4. **Verification**: リグレッションなしを確認 → フェーズ出力生成

### Agent Delegation

- **Phase 1 (Setup)**: メインエージェント直接実行
- **Phase 2-4 (User Stories)**: speckit:tdd-generator (RED) → speckit:phase-executor (GREEN + Verification)
- **Phase 5 (Polish)**: speckit:phase-executor のみ

---

## Phase Output & RED Test Artifacts

### Directory Structure

```
specs/018-spread-mode-trim/
├── tasks.md                    # 本ファイル
├── tasks/
│   ├── ph1-output.md           # Phase 1 出力（Setup 結果）
│   ├── ph2-output.md           # Phase 2 出力（US1 GREEN 結果）
│   ├── ph3-output.md           # Phase 3 出力（US2 GREEN 結果）
│   ├── ph4-output.md           # Phase 4 出力（US3 GREEN 結果）
│   └── ph5-output.md           # Phase 5 出力（Polish 結果）
└── red-tests/
    ├── ph2-test.md             # Phase 2 RED テスト結果
    ├── ph3-test.md             # Phase 3 RED テスト結果
    └── ph4-test.md             # Phase 4 RED テスト結果
```

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Phase 1 完了: Setup（既存コード分析）
2. Phase 2 完了: US1 - Spread モード明示指定（RED → GREEN → Verification）
3. **STOP and VALIDATE**: `make test` で全テスト通過を確認
4. 検証用動画で手動テスト

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
2. 各フェーズでコミット: `feat(phase-N): description`

---

## Test Data

| ファイル | モード | 用途 |
|---------|--------|------|
| `movies/n3-failers-in-developing-softwear.mov` | `spread` | 見開き分割テスト |
| `movies/n5-sre.mov` | `single` | 単ページテスト |

---

## Notes

- [P] タスク = 依存関係なし、実行順序自由
- [Story] ラベルは特定のユーザーストーリーへのトレーサビリティ用
- 各ユーザーストーリーは独立して完了・テスト可能であること
- TDD: Test Implementation (RED) → Verify FAIL → Implementation (GREEN) → Verify PASS
- RED 出力は実装開始前に生成すること
- 各フェーズ完了後にコミット
- チェックポイントでストーリーを独立して検証可能
