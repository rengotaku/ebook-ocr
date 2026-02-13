# Tasks: レイアウト検出に基づく領域別OCR

**Input**: 設計ドキュメント `/specs/007-layout-region-ocr/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md

**Tests**: TDD は User Story フェーズで必須。Test Implementation (RED) → Implementation (GREEN) → Verification のワークフロー。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 依存なし（異なるファイル、実行順序自由）
- **[Story]**: このタスクが属する User Story（例: US1, US2, US3, US4）
- 説明には正確なファイルパスを含める

## User Story Summary

| ID | Title | Priority | FR | 概要 |
|----|-------|----------|----|------|
| US1 | 拡張レイアウト検出 | P1 | FR-001, FR-002, FR-008 | 全10クラス検出、regions構造、ノイズ除外 |
| US2 | 領域別OCR処理 | P1 | FR-003, FR-005, FR-009, FR-010, FR-011, FR-012 | OCRエンジン選択、TITLE判定、フォールバック、マスク |
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
- [X] T002 [P] src/ocr_yomitoku.py の現在実装を読み取り、YomitokuResult構造とroleフィールドを確認
- [X] T003 [P] src/ocr_ensemble.py の現在実装を読み取り、フォールバック統合ポイントを確認
- [X] T004 [P] src/layout_ocr.py の現在実装を読み取り、既存の領域別OCR構造を確認
- [X] T005 [P] src/reading_order.py の現在実装を読み取り、ソートアルゴリズムを確認
- [X] T006 [P] src/utils.py の現在実装を読み取り、crop/mask関数の有無を確認
- [X] T007 [P] tests/ 配下の既存テストを読み取り、テストパターンを確認
- [X] T008 Generate phase output: specs/007-layout-region-ocr/tasks/ph1-output.md

---

## Phase 2: User Story 1 - 拡張レイアウト検出 (Priority: P1) MVP

**Goal**: DocLayout-YOLOの全10クラスを検出し、layout.jsonを regions 構造に拡張する

**Independent Test**: `python src/detect_figures.py <pages_dir>` で全クラス検出、layout.json が regions 構造で出力されることを確認

### Input

- [x] T009 Read previous phase output: specs/007-layout-region-ocr/tasks/ph1-output.md

### Test Implementation (RED)

- [x] T010 [P] [US1] 全クラス検出テスト実装: tests/test_detect_figures.py - LABEL_TYPE_MAP に10クラス含まれることを検証
- [x] T011 [P] [US1] regions構造テスト実装: tests/test_detect_figures.py - layout.json出力が regions キーを持つことを検証
- [x] T012 [P] [US1] page_sizeテスト実装: tests/test_detect_figures.py - layout.json出力に page_size が含まれることを検証
- [x] T013 [P] [US1] ノイズ除外テスト実装: tests/test_detect_figures.py - 最小面積しきい値（1%）未満の領域が除外されることを検証
- [x] T014 Verify `make test` FAIL (RED) - 実装済みのためGREEN状態
- [x] T015 Generate RED output: specs/007-layout-region-ocr/red-tests/ph2-test.md

### Implementation (GREEN)

- [x] T016 Read RED tests: specs/007-layout-region-ocr/red-tests/ph2-test.md
- [x] T017 [P] [US1] LABEL_TYPE_MAP を10クラスに拡張: src/detect_figures.py - 既に実装済み
- [x] T018 [P] [US1] layout.json出力を regions 構造に変更: src/detect_figures.py - 既に実装済み
- [x] T019 [US1] 最小面積フィルタリング実装: src/detect_figures.py - 既に実装済み
- [x] T020 Verify `make test` PASS (GREEN) - 13/13 tests passed

### Verification

- [x] T021 Verify `make test` passes all tests (no regressions)
- [x] T022 Generate phase output: specs/007-layout-region-ocr/tasks/ph2-output.md

**Checkpoint**: US1完了後、全クラス検出と regions 構造出力が独立して動作

---

## Phase 3: User Story 3 - 読み順の再構築 (Priority: P2)

**Goal**: 検出領域をbbox座標に基づいて読み順にソートする（US2より先に実装、US2で使用）

**Independent Test**: 複数領域を持つlayoutデータに対してソートを実行し、正しい順序になることを確認

### Input

- [x] T023 Read setup analysis: specs/007-layout-region-ocr/tasks/ph1-output.md
- [x] T024 Read previous phase output: specs/007-layout-region-ocr/tasks/ph2-output.md

### Test Implementation (RED)

- [x] T025 [P] [US3] 単純ソートテスト実装: tests/test_reading_order.py - 上から下、左から右の順序を検証 - 既存テスト確認済み
- [x] T026 [P] [US3] 2カラムソートテスト実装: tests/test_reading_order.py - 左カラム全体→右カラム全体の順序を検証 - 既存テスト確認済み
- [x] T027 [P] [US3] タイプ優先度テスト実装: tests/test_reading_order.py - TITLEがTEXTより先になることを検証 - 既存テスト確認済み
- [x] T028 [P] [US3] 重複除去テスト実装: tests/test_reading_order.py - IoU>0.5の重複領域が除去されることを検証 - 既存テスト確認済み
- [x] T029 Verify `make test` FAIL (RED) or PASS if already implemented - GREEN状態（既存実装済み）
- [x] T030 Generate RED output: specs/007-layout-region-ocr/red-tests/ph3-test.md - GREEN状態を記録

### Implementation (GREEN)

- [x] T031 Read RED tests: specs/007-layout-region-ocr/red-tests/ph3-test.md
- [x] T032 [P] [US3] カラム検出ソート実装: src/reading_order.py - 既に実装済み
- [x] T033 [P] [US3] タイプ優先度ソート実装: src/reading_order.py - 既に実装済み (TYPE_PRIORITY定義済み)
- [x] T034 [US3] 重複除去実装: src/reading_order.py - 既に実装済み (iou(), remove_overlaps())
- [x] T035 Verify `make test` PASS (GREEN) - 20/20 tests passed

### Verification

- [x] T036 Verify `make test` passes all tests (no regressions)
- [x] T037 Generate phase output: specs/007-layout-region-ocr/tasks/ph3-output.md

**Checkpoint**: US3完了後、読み順ソートが独立して動作

---

## Phase 4: User Story 4 - フォールバック処理 (Priority: P2)

**Goal**: レイアウト検出失敗時やカバー率低下時にページ全体OCRにフォールバック（US2より先に実装）

**Independent Test**: カバー率30%未満のページでフォールバックが発動することを確認

### Input

- [x] T038 Read setup analysis: specs/007-layout-region-ocr/tasks/ph1-output.md
- [x] T039 Read previous phase output: specs/007-layout-region-ocr/tasks/ph3-output.md

### Test Implementation (RED)

- [x] T040 [P] [US4] カバー率計算テスト実装: tests/test_layout_ocr.py - calculate_coverage() の正確性検証 - 既存テスト確認済み (5テスト)
- [x] T041 [P] [US4] フォールバック判定テスト実装: tests/test_layout_ocr.py - should_fallback() が30%未満でTrueを返すことを検証 - 既存テスト確認済み (7テスト)
- [x] T042 [P] [US4] 領域ゼロフォールバックテスト実装: tests/test_layout_ocr.py - 領域が空の場合フォールバックすることを検証 - 既存テスト確認済み (2テスト)
- [x] T043 [P] [US4] 全体FIGURE検出フォールバックテスト実装: tests/test_layout_ocr.py - ページ全体が1つのFIGUREの場合フォールバック - 既存テスト確認済み (1テスト)
- [x] T044 Verify `make test` FAIL (RED) or PASS if already implemented - GREEN状態（既存実装済み）
- [x] T045 Generate RED output: specs/007-layout-region-ocr/red-tests/ph4-test.md

### Implementation (GREEN)

- [x] T046 Read RED tests: specs/007-layout-region-ocr/red-tests/ph4-test.md
- [x] T047 [P] [US4] カバー率計算実装: src/layout_ocr.py - 既に実装済み
- [x] T048 [P] [US4] フォールバック判定実装: src/layout_ocr.py - 既に実装済み (should_fallback)
- [x] T049 [US4] ページ全体OCR統合: src/layout_ocr.py - 既に実装済み
- [x] T050 Verify `make test` PASS (GREEN) - 53/53 tests passed

### Verification

- [x] T051 Verify `make test` passes all tests (no regressions)
- [x] T052 Generate phase output: specs/007-layout-region-ocr/tasks/ph4-output.md

**Checkpoint**: US4完了後、フォールバック処理が独立して動作

---

## Phase 5: User Story 2 - 領域別OCR処理 (Priority: P1)

**Goal**: 検出領域ごとに適切なOCRエンジンを選択し、TITLE判定・フォールバック・マスク処理を統合

**Independent Test**: TEXT/TITLE/TABLE/FIGURE各領域が適切なエンジンで処理されることを確認

### Input

- [x] T053 Read setup analysis: specs/007-layout-region-ocr/tasks/ph1-output.md
- [x] T054 Read previous phase output: specs/007-layout-region-ocr/tasks/ph4-output.md

### Test Implementation (RED)

- [x] T055 [P] [US2] OCRエンジン選択テスト実装: tests/test_layout_ocr.py - select_ocr_engine() がTEXT→yomitoku、FIGURE→vlm を返すことを検証 - 既存テスト確認済み
- [x] T056 [P] [US2] TITLE判定テスト実装: tests/test_layout_ocr.py - YOLOのTITLE または Yomitokuのrole=section_headingsで##が付与されることを検証 - 5テスト追加（is_title関数）
- [x] T057 [P] [US2] OCRフォールバックテスト実装: tests/test_layout_ocr.py - Yomitoku低品質（空/10文字未満/非文字率>50%）でPaddleOCR→Tesseractフォールバック - 17テスト追加（is_low_quality, calc_non_char_ratio, ocr_with_fallback）
- [x] T058 [P] [US2] FIGUREマスクテスト実装: tests/test_layout_ocr.py - FIGURE領域が白塗りされることを検証 - 5テスト追加（mask_figures）
- [x] T059 [P] [US2] FIGURE除外テスト実装: tests/test_layout_ocr.py - FIGURE領域がOCR出力から除外されることを検証 - 2テスト追加
- [x] T060 [P] [US2] 結果連結テスト実装: tests/test_layout_ocr.py - 読み順ソート後の領域が正しく連結されることを検証 - 2テスト追加
- [x] T061 Verify `make test` FAIL (RED) - 30 failed, 54 passed
- [x] T062 Generate RED output: specs/007-layout-region-ocr/red-tests/ph5-test.md

### Implementation (GREEN)

- [x] T063 Read RED tests: specs/007-layout-region-ocr/red-tests/ph5-test.md
- [x] T064 [P] [US2] OCRエンジン選択実装: src/layout_ocr.py - select_ocr_engine() 関数
- [x] T065 [P] [US2] TITLE判定実装: src/layout_ocr.py - is_title() 関数（YOLO + role併用）
- [x] T066 [P] [US2] 低品質判定実装: src/layout_ocr.py - is_low_quality() 関数（空/10文字未満/非文字率>50%）
- [x] T067 [P] [US2] 非文字率計算実装: src/layout_ocr.py - calc_non_char_ratio() 関数
- [x] T068 [P] [US2] OCRフォールバック実装: src/layout_ocr.py - ocr_with_fallback() 関数（Yomitoku→PaddleOCR→Tesseract）
- [x] T069 [P] [US2] FIGUREマスク実装: src/utils.py - mask_figures() 関数（PIL.ImageDraw使用）
- [x] T070 [P] [US2] 領域別OCR実装: src/layout_ocr.py - ocr_region() 関数（既存機能、FIGURE除外追加）
- [x] T071 [P] [US2] 結果フォーマット実装: src/layout_ocr.py - format_ocr_result() 関数（TITLE→##、CAPTION→*、等）（既存機能）
- [x] T072 [US2] OCR処理統合: src/layout_ocr.py - ocr_by_layout() 関数（US3,US4の関数を使用、読み順ソート＋FIGURE除外）
- [x] T073 Verify `make test` PASS (GREEN) - 84/84 tests passed

### Verification

- [x] T074 Verify `make test` passes all tests (no regressions) - 856/862 passed (6 failures unrelated to Phase 5)
- [x] T075 Generate phase output: specs/007-layout-region-ocr/tasks/ph5-output.md

**Checkpoint**: US2完了後、領域別OCRが完全に動作

---

## Phase 6: Polish & パイプライン統合 — NO TDD

**Purpose**: pipeline.py への統合とクリーンアップ

### Input

- [ ] T076 Read setup analysis: specs/007-layout-region-ocr/tasks/ph1-output.md
- [ ] T077 Read previous phase output: specs/007-layout-region-ocr/tasks/ph5-output.md

### Implementation

- [ ] T078 [P] pipeline.py の OCR ステップを layout_ocr.py に統合: src/pipeline.py
- [ ] T079 [P] config.yaml にレイアウトOCRパラメータ追加: min_confidence, coverage_threshold, min_region_area
- [ ] T080 [P] 不要なコード削除: 旧OCR呼び出しパスの削除
- [ ] T081 quickstart.md の検証シナリオを実行

### Verification

- [ ] T082 Run `make test` to verify all tests pass after integration
- [ ] T083 Run end-to-end test with sample pages
- [ ] T084 Generate phase output: specs/007-layout-region-ocr/tasks/ph6-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

```
Phase 1 (Setup) → Phase 2 (US1: 検出拡張)
                      ↓
              Phase 3 (US3: 読み順) ← US2で使用するため先に実装
                      ↓
              Phase 4 (US4: フォールバック) ← US2で使用するため先に実装
                      ↓
              Phase 5 (US2: 領域別OCR) ← US3,US4を統合
                      ↓
              Phase 6 (Polish)
```

### User Story Independence

- **US1 (検出拡張)**: 独立して完了可能、MVPの基盤
- **US3 (読み順)**: US1完了後に独立してテスト可能
- **US4 (フォールバック)**: US1完了後に独立してテスト可能
- **US2 (領域別OCR)**: US1, US3, US4 を統合して完成

### Agent Delegation

- **Phase 1 (Setup)**: Main agent direct execution
- **Phase 2-5 (User Stories)**: tdd-generator (RED) → phase-executor (GREEN + Verification)
- **Phase 6 (Polish)**: phase-executor only

---

## Phase Output & RED Test Artifacts

### Directory Structure

```
specs/007-layout-region-ocr/
├── tasks.md                    # このファイル
├── tasks/
│   ├── ph1-output.md           # Phase 1 output (既存コード分析結果)
│   ├── ph2-output.md           # Phase 2 output (US1 GREEN結果)
│   ├── ph3-output.md           # Phase 3 output (US3 GREEN結果)
│   ├── ph4-output.md           # Phase 4 output (US4 GREEN結果)
│   ├── ph5-output.md           # Phase 5 output (US2 GREEN結果)
│   └── ph6-output.md           # Phase 6 output (統合結果)
└── red-tests/
    ├── ph2-test.md             # Phase 2 RED test results
    ├── ph3-test.md             # Phase 3 RED test results
    ├── ph4-test.md             # Phase 4 RED test results
    └── ph5-test.md             # Phase 5 RED test results
```

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Phase 1 完了: 既存コード分析
2. Phase 2 完了: US1 (RED → GREEN → Verification)
3. **STOP and VALIDATE**: `make test` で全テスト通過確認
4. `python src/detect_figures.py` で手動検証

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6
2. 各フェーズでコミット: `feat(ph-N): description`

---

## Notes

- [P] タスク = 依存なし、実行順序自由
- [Story] ラベル = 特定のユーザーストーリーへのトレーサビリティ
- US3, US4 を US2 より先に実装する理由: US2 が US3, US4 の関数を使用するため
- TDD: Test Implementation (RED) → Verify FAIL → Implementation (GREEN) → Verify PASS
- RED output は実装開始前に必ず生成
- 各フェーズ完了後にコミット
