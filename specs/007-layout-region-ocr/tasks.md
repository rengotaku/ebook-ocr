# Tasks: レイアウト検出に基づく領域別OCR

**Input**: 設計ドキュメント `/specs/007-layout-region-ocr/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md

**Tests**: TDD は User Story フェーズで必須。Test Implementation (RED) → Implementation (GREEN) → Verification のワークフロー。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 依存なし（異なるファイル、実行順序自由）
- **[Story]**: このタスクが属する User Story（例: US1, US2, US3, US4）
- 説明には正確なファイルパスを含める

## User Story Summary

| ID | Title | Priority | FR | Scenario |
|----|-------|----------|----|----------|
| US1 | 拡張レイアウト検出 | P1 | FR-001, FR-002, FR-008 | 全クラス検出、regions構造、ノイズ除外 |
| US2 | 領域別OCR処理 | P1 | FR-003, FR-005 | OCRエンジン選択、結果連結 |
| US3 | 読み順の再構築 | P2 | FR-004, FR-007 | 座標ソート、重複除去 |
| US4 | フォールバック処理 | P2 | FR-006 | カバー率判定、ページ全体OCR |

## Path Conventions

- **Source**: `src/` at repository root
- **Tests**: `tests/` at repository root
- **Feature docs**: `specs/007-layout-region-ocr/`

---

## Phase 1: Setup（既存コード分析）— NO TDD

**Purpose**: 既存コードの確認と変更準備

- [X] T001 src/detect_figures.py の現在実装を読み取り、LABEL_TYPE_MAP と TARGET_LABELS を確認
- [X] T002 [P] src/ocr_deepseek.py の現在実装を読み取り、領域別OCR統合ポイントを確認
- [X] T003 [P] src/utils.py の現在実装を読み取り、crop/mask関数を確認
- [X] T004 [P] tests/test_ocr_deepseek.py の既存テストを読み取り、テストパターンを確認
- [X] T005 Generate phase output: specs/007-layout-region-ocr/tasks/ph1-output.md

---

## Phase 2: User Story 1 - 拡張レイアウト検出 (Priority: P1) MVP

**Goal**: DocLayout-YOLOの全10クラスを検出し、layout.jsonを regions 構造に拡張する

**Independent Test**: `make detect HASHDIR=...` で全クラス検出、layout.json が regions 構造で出力されることを確認

### Input

- [x] T006 Read previous phase output: specs/007-layout-region-ocr/tasks/ph1-output.md

### Test Implementation (RED)

- [x] T007 [P] [US1] 全クラス検出テスト実装: tests/test_detect_figures.py - LABEL_TYPE_MAP に10クラス含まれることを検証
- [x] T008 [P] [US1] regions構造テスト実装: tests/test_detect_figures.py - layout.json出力が regions キーを持つことを検証
- [x] T009 [P] [US1] page_sizeテスト実装: tests/test_detect_figures.py - layout.json出力に page_size が含まれることを検証
- [x] T010 [P] [US1] ノイズ除外テスト実装: tests/test_detect_figures.py - 最小面積しきい値未満の領域が除外されることを検証
- [x] T011 Verify `make test` FAIL (RED)
- [x] T012 Generate RED output: specs/007-layout-region-ocr/red-tests/ph2-test.md

### Implementation (GREEN)

- [x] T013 Read RED tests: specs/007-layout-region-ocr/red-tests/ph2-test.md
- [x] T014 [P] [US1] LABEL_TYPE_MAP を10クラスに拡張: src/detect_figures.py
- [x] T015 [P] [US1] layout.json出力を regions 構造に変更: src/detect_figures.py - figures → regions、page_size 追加
- [x] T016 [US1] 最小面積フィルタリング実装: src/detect_figures.py - min_area パラメータ追加
- [x] T017 Verify `make test` PASS (GREEN)

### Verification

- [x] T018 Verify `make test` passes all tests (no regressions)
- [x] T019 Generate phase output: specs/007-layout-region-ocr/tasks/ph2-output.md

**Checkpoint**: US1完了後、全クラス検出と regions 構造出力が独立して動作

---

## Phase 3: User Story 3 - 読み順の再構築 (Priority: P2)

**Goal**: 検出領域をbbox座標に基づいて読み順にソートする

**Independent Test**: 複数領域を持つlayoutデータに対してソートを実行し、正しい順序になることを確認

### Input

- [x] T020 Read setup analysis: specs/007-layout-region-ocr/tasks/ph1-output.md
- [x] T021 Read previous phase output: specs/007-layout-region-ocr/tasks/ph2-output.md

### Test Implementation (RED)

- [x] T022 [P] [US3] 単純ソートテスト実装: tests/test_reading_order.py - 上から下、左から右の順序を検証
- [x] T023 [P] [US3] 2カラムソートテスト実装: tests/test_reading_order.py - 左カラム全体→右カラム全体の順序を検証
- [x] T024 [P] [US3] タイトル優先テスト実装: tests/test_reading_order.py - TITLEがTEXTより先になることを検証
- [x] T025 [P] [US3] 重複除去テスト実装: tests/test_reading_order.py - 重複領域の処理を検証
- [x] T026 Verify `make test` FAIL (RED)
- [x] T027 Generate RED output: specs/007-layout-region-ocr/red-tests/ph3-test.md

### Implementation (GREEN)

- [x] T028 Read RED tests: specs/007-layout-region-ocr/red-tests/ph3-test.md
- [x] T029 [P] [US3] sort_reading_order() 関数実装: src/reading_order.py - カラム検出 + Y座標ソート
- [x] T030 [P] [US3] remove_overlaps() 関数実装: src/reading_order.py - 重複領域の検出と除去
- [x] T031 Verify `make test` PASS (GREEN)

### Verification

- [x] T032 Verify `make test` passes all tests (including US1 regressions)
- [x] T033 Generate phase output: specs/007-layout-region-ocr/tasks/ph3-output.md

**Checkpoint**: US1 + US3 完了後、検出と読み順ソートが独立して動作

---

## Phase 4: User Story 2 - 領域別OCR処理 (Priority: P1)

**Goal**: 検出された各領域に対して適切なOCRエンジンを選択して処理する

**Independent Test**: 複数種類の領域を持つページに対してOCRを実行し、各領域が適切に処理されることを確認

### Input

- [x] T034 Read setup analysis: specs/007-layout-region-ocr/tasks/ph1-output.md
- [x] T035 Read previous phase output: specs/007-layout-region-ocr/tasks/ph3-output.md

### Test Implementation (RED)

- [x] T036 [P] [US2] TEXT領域OCRテスト実装: tests/test_layout_ocr.py - TEXT領域がDeepSeek-OCRで処理されることを検証
- [x] T037 [P] [US2] FIGURE領域OCRテスト実装: tests/test_layout_ocr.py - FIGURE領域がVLMで処理されることを検証（モック使用）
- [x] T038 [P] [US2] TITLE領域OCRテスト実装: tests/test_layout_ocr.py - TITLE領域が見出しマークアップで出力されることを検証
- [x] T039 [P] [US2] 結果連結テスト実装: tests/test_layout_ocr.py - 複数領域のOCR結果が正しく連結されることを検証
- [x] T040 Verify `make test` FAIL (RED)
- [x] T041 Generate RED output: specs/007-layout-region-ocr/red-tests/ph4-test.md

### Implementation (GREEN)

- [x] T042 Read RED tests: specs/007-layout-region-ocr/red-tests/ph4-test.md
- [x] T043 [P] [US2] crop_region() 関数実装: src/layout_ocr.py - 領域クロップユーティリティ
- [x] T044 [P] [US2] select_ocr_engine() 関数実装: src/layout_ocr.py - 領域種類に応じたエンジン選択
- [x] T045 [P] [US2] format_ocr_result() 関数実装: src/layout_ocr.py - 領域種類に応じたマークアップ
- [x] T046 [US2] ocr_by_layout() 関数実装: src/layout_ocr.py - 領域別OCR dispatcher（T043-T045を統合）
- [x] T047 Verify `make test` PASS (GREEN)

### Verification

- [x] T048 Verify `make test` passes all tests (including US1, US3 regressions)
- [x] T049 Generate phase output: specs/007-layout-region-ocr/tasks/ph4-output.md

**Checkpoint**: US1 + US2 + US3 完了後、検出→ソート→OCRの一連の処理が動作

---

## Phase 5: User Story 4 - フォールバック処理 (Priority: P2)

**Goal**: レイアウト検出失敗時やカバー率低下時にページ全体OCRにフォールバックする

**Independent Test**: 空のlayout または低カバー率のページに対してOCRを実行し、ページ全体OCRが実行されることを確認

### Input

- [x] T050 Read setup analysis: specs/007-layout-region-ocr/tasks/ph1-output.md
- [x] T051 Read previous phase output: specs/007-layout-region-ocr/tasks/ph4-output.md

### Test Implementation (RED)

- [x] T052 [P] [US4] 空layout フォールバックテスト実装: tests/test_layout_ocr.py - 領域なしでページ全体OCRが実行されることを検証
- [x] T053 [P] [US4] 低カバー率フォールバックテスト実装: tests/test_layout_ocr.py - 30%未満でページ全体OCRが実行されることを検証
- [x] T054 [P] [US4] カバー率計算テスト実装: tests/test_layout_ocr.py - calculate_coverage() の正確性を検証
- [x] T055 Verify `make test` FAIL (RED)
- [x] T056 Generate RED output: specs/007-layout-region-ocr/red-tests/ph5-test.md

### Implementation (GREEN)

- [x] T057 Read RED tests: specs/007-layout-region-ocr/red-tests/ph5-test.md
- [x] T058 [P] [US4] calculate_coverage() 関数実装: src/layout_ocr.py - 検出領域のカバー率計算
- [x] T059 [US4] should_fallback() 関数実装: src/layout_ocr.py - フォールバック判定ロジック
- [x] T060 [US4] ocr_by_layout() にフォールバック統合: src/layout_ocr.py
- [x] T061 Verify `make test` PASS (GREEN)

### Verification

- [x] T062 Verify `make test` passes all tests (including US1-US3 regressions)
- [x] T063 Generate phase output: specs/007-layout-region-ocr/tasks/ph5-output.md

**Checkpoint**: 全User Story完了、すべてのシナリオが独立して動作

---

## Phase 6: Polish & パイプライン統合 — NO TDD

**Purpose**: パイプラインへの統合と最終検証

### Input

- [x] T064 Read setup analysis: specs/007-layout-region-ocr/tasks/ph1-output.md
- [x] T065 Read previous phase output: specs/007-layout-region-ocr/tasks/ph5-output.md

### Implementation

- [x] T066 [P] src/pipeline.py に領域別OCR統合: detect_figures → reading_order → layout_ocr の呼び出し順序
- [x] T067 [P] config.yaml にパラメータ追加: coverage_threshold, min_region_area
- [x] T068 Makefile 更新: 新規ターゲット追加（必要に応じて）
- [x] T069 quickstart.md の検証: 手順が動作することを確認

### Verification

- [x] T070 Run `make test` to verify all tests pass after integration
- [x] T071 Generate phase output: specs/007-layout-region-ocr/tasks/ph6-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: 依存なし - Main agent 直接実行
- **Phase 2 (US1)**: Phase 1 に依存 - TDD flow
- **Phase 3 (US3)**: Phase 2 に依存 - TDD flow（読み順はUS1の出力を使用）
- **Phase 4 (US2)**: Phase 3 に依存 - TDD flow（OCRはソート後の領域を使用）
- **Phase 5 (US4)**: Phase 4 に依存 - TDD flow
- **Phase 6 (Polish)**: Phase 5 に依存 - phase-executor のみ

### Agent Delegation

- **Phase 1**: Main agent 直接実行
- **Phase 2-5**: tdd-generator (RED) → phase-executor (GREEN + Verification)
- **Phase 6**: phase-executor のみ

### [P] Marker Summary

| Phase | Parallel Tasks |
|-------|---------------|
| Phase 1 | T002, T003, T004 |
| Phase 2 | T007-T010 (RED), T014-T015 (GREEN) |
| Phase 3 | T022-T025 (RED), T029-T030 (GREEN) |
| Phase 4 | T036-T039 (RED), T043-T045 (GREEN) |
| Phase 5 | T052-T054 (RED), T058 (GREEN) |
| Phase 6 | T066-T067 |

---

## Phase Output & RED Test Artifacts

### Directory Structure

```
specs/007-layout-region-ocr/
├── tasks.md                    # このファイル
├── tasks/
│   ├── ph1-output.md           # Phase 1 出力（セットアップ結果）
│   ├── ph2-output.md           # Phase 2 出力（US1 GREEN結果）
│   ├── ph3-output.md           # Phase 3 出力（US3 GREEN結果）
│   ├── ph4-output.md           # Phase 4 出力（US2 GREEN結果）
│   ├── ph5-output.md           # Phase 5 出力（US4 GREEN結果）
│   └── ph6-output.md           # Phase 6 出力（最終結果）
└── red-tests/
    ├── ph2-test.md             # Phase 2 RED テスト結果
    ├── ph3-test.md             # Phase 3 RED テスト結果
    ├── ph4-test.md             # Phase 4 RED テスト結果
    └── ph5-test.md             # Phase 5 RED テスト結果
```

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Phase 1 完了: セットアップ（既存コード分析）
2. Phase 2 完了: User Story 1（拡張レイアウト検出）
3. **STOP and VALIDATE**: `make test` で全テスト通過を確認
4. 手動テスト: `make detect HASHDIR=...` で layout.json を確認

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6
2. 各フェーズでコミット: `feat(phase-N): description`

---

## Notes

- [P] タスク = 依存なし、実行順序自由
- [Story] ラベルは特定の User Story へのトレーサビリティ
- 各 User Story は独立して完了・テスト可能
- TDD: Test Implementation (RED) → FAIL確認 → Implementation (GREEN) → PASS確認
- RED出力は実装開始前に生成必須
- 各フェーズ完了後にコミット
- 任意のチェックポイントで停止して独立検証可能
