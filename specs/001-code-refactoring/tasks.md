# Tasks: コードベースリファクタリング

**Input**: Design documents from `specs/001-code-refactoring/`
**Prerequisites**: plan.md (required), spec.md (required), research.md, quickstart.md

**Tests**: TDD is MANDATORY for User Story phases. Each phase follows テスト実装 (RED) → 実装 (GREEN) → 検証 workflow.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: No dependencies (different files, execution order free)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## User Story Summary

| ID  | Title                                  | Priority | FR          | Scenario               |
|-----|----------------------------------------|----------|-------------|------------------------|
| US1 | 共有ユーティリティ抽出・モジュール結合解消 | P1       | FR-001,002  | ユーティリティ統合・インポート修正 |
| US2 | デッドコード・レガシー依存の除去           | P2       | FR-003,004  | ocr.py削除・依存パッケージ除去 |
| US3 | 自動テストスイートの導入                  | P3       | FR-006,007,008 | テスト追加・リソース管理改善 |

## Path Conventions

- **Source**: `src/` at repository root
- **Tests**: `tests/` at repository root
- **Feature Dir**: `specs/001-code-refactoring/`

---

## Phase 1: Setup (Shared Infrastructure) — NO TDD

**Purpose**: 現行コードの確認、テスト基盤の初期化、Makefile 更新

- [X] T001 Read current implementation: src/ocr_deepseek.py, src/ocr.py, src/describe_figures.py to confirm duplication locations
- [X] T002 [P] Read current implementation: src/pipeline.py, src/deduplicate.py to confirm import structure
- [X] T003 [P] Add pytest to requirements.txt
- [X] T004 [P] Add `test` target to Makefile: `$(PYTHON) -m pytest tests/ -v`
- [X] T005 [P] Create tests/__init__.py (empty)
- [X] T006 [P] Create tests/conftest.py with shared fixtures (tmp_path, sample image factory)
- [X] T007 Run `make setup` to install pytest dependency
- [X] T008 Generate phase output: specs/001-code-refactoring/tasks/ph1-output.md

---

## Phase 2: User Story 1 — 共有ユーティリティ抽出・モジュール結合解消 (Priority: P1) MVP

**Goal**: 重複関数を `src/utils.py` に統合し、`ocr_deepseek.py` → `ocr.py` の結合を解消する。パイプライン出力は変更しない。

**Independent Test**: `src/utils.py` の各関数が正しく動作し、`ocr_deepseek.py` が `ocr.py` に依存しないこと。`make test` で全テスト PASS。

### 入力

- [x] T009 Read previous phase output: specs/001-code-refactoring/tasks/ph1-output.md

### テスト実装 (RED)

- [x] T010 [P] [US1] Implement test_encode_image_file (正常系: 既知画像のbase64検証) in tests/test_utils.py
- [x] T011 [P] [US1] Implement test_encode_pil_image (PIL Image → base64 ラウンドトリップ) in tests/test_utils.py
- [x] T012 [P] [US1] Implement test_format_figure_markers (layout入力 → マーカー文字列出力) in tests/test_utils.py
- [x] T013 [P] [US1] Implement test_format_figure_markers_empty (空layout → 空文字列) in tests/test_utils.py
- [x] T014 [P] [US1] Implement test_format_figure_markers_low_confidence (min_confidence以下 → 除外) in tests/test_utils.py
- [x] T015 [P] [US1] Implement test_mask_figure_regions (白塗りマスクの座標・ピクセル検証) in tests/test_utils.py
- [x] T016 [P] [US1] Implement test_mask_figure_regions_no_figures (図なし → 元画像をそのまま返す) in tests/test_utils.py
- [x] T017 [P] [US1] Implement test_mask_figure_regions_clamp (bbox が画像境界を超える場合のクランプ検証) in tests/test_utils.py
- [x] T018 Verify `make test` FAIL (RED) — src/utils.py が存在しないため ImportError
- [x] T019 Generate RED output: specs/001-code-refactoring/red-tests/ph2-test.md

### 実装 (GREEN)

- [x] T020 Read RED tests: specs/001-code-refactoring/red-tests/ph2-test.md
- [x] T021 [US1] Create src/utils.py with encode_image_file(), encode_pil_image(), format_figure_markers(), mask_figure_regions()
- [x] T022 [US1] Update src/ocr_deepseek.py: replace `from src.ocr import _format_figure_markers` with `from src.utils import format_figure_markers`; remove local `_encode_image`, `_encode_pil_image`, `_mask_figure_regions` definitions; update all call sites
- [x] T023 [US1] Update src/describe_figures.py: replace local `_encode_image` with `from src.utils import encode_image_file`; update call site in `_describe_single()`
- [x] T024 Verify `make test` PASS (GREEN)

### 検証

- [x] T025 Verify `make test` passes all tests (no regressions)
- [x] T026 Verify `python -c "from src.ocr_deepseek import ocr_page_deepseek"` succeeds without importing src.ocr
- [x] T027 Generate phase output: specs/001-code-refactoring/tasks/ph2-output.md

**Checkpoint**: US1 完了。`src/utils.py` に共有関数が統合され、`ocr_deepseek.py` は `ocr.py` に依存しない。

---

## Phase 3: User Story 2 — デッドコード・レガシー依存の除去 (Priority: P2)

**Goal**: 使われていない `ocr.py` の削除と、不要な依存パッケージ (easyocr, pytesseract, opencv-python) の除去。

**Independent Test**: `ocr.py` が存在しない状態で `make test` が PASS し、`requirements.txt` に不要パッケージが含まれないこと。

### 入力

- [ ] T028 Read previous phase output: specs/001-code-refactoring/tasks/ph2-output.md

### テスト実装 (RED)

- [ ] T029 [P] [US2] Implement test_no_legacy_ocr_import (src/ 全体で `from src.ocr import` が存在しないことを検証) in tests/test_cleanup.py
- [ ] T030 [P] [US2] Implement test_no_unused_dependencies (requirements.txt に easyocr, pytesseract, opencv-python が含まれないことを検証) in tests/test_cleanup.py
- [ ] T031 [P] [US2] Implement test_no_private_cross_imports (src/ 全体で `from src.XXX import _` パターンが存在しないことを検証) in tests/test_cleanup.py
- [ ] T032 Verify `make test` FAIL (RED) — ocr.py がまだ存在し、requirements.txt にレガシー依存が残っているため
- [ ] T033 Generate RED output: specs/001-code-refactoring/red-tests/ph3-test.md

### 実装 (GREEN)

- [ ] T034 Read RED tests: specs/001-code-refactoring/red-tests/ph3-test.md
- [ ] T035 [US2] Delete src/ocr.py
- [ ] T036 [US2] Remove easyocr, pytesseract, opencv-python from requirements.txt
- [ ] T037 Verify `make test` PASS (GREEN)

### 検証

- [ ] T038 Verify `make test` passes all tests (including US1 tests — no regressions)
- [ ] T039 Generate phase output: specs/001-code-refactoring/tasks/ph3-output.md

**Checkpoint**: US1 + US2 完了。レガシーコードと不要依存が除去され、コードベースがクリーンな状態。

---

## Phase 4: User Story 3 — 自動テストスイートの導入 (Priority: P3)

**Goal**: 主要モジュール (deduplicate, ocr_deepseek, describe_figures) のテストとリソース管理改善。

**Independent Test**: `make test` で全テスト PASS、カバレッジ目標 >=80%。

### 入力

- [ ] T040 Read previous phase output: specs/001-code-refactoring/tasks/ph3-output.md

### テスト実装 (RED) — deduplicate

- [ ] T041 [P] [US3] Implement test_deduplicate_identical_images (同一画像 → 重複検出) in tests/test_deduplicate.py
- [ ] T042 [P] [US3] Implement test_deduplicate_different_images (異なる画像 → 非重複) in tests/test_deduplicate.py
- [ ] T043 [P] [US3] Implement test_deduplicate_empty_dir (空ディレクトリ → 空リスト) in tests/test_deduplicate.py

### テスト実装 (RED) — ocr_deepseek

- [ ] T044 [P] [US3] Implement test_ocr_page_deepseek_mock (Ollama API モック → Markdown出力検証) in tests/test_ocr_deepseek.py
- [ ] T045 [P] [US3] Implement test_detect_repetition_normal (正常テキスト → None) in tests/test_ocr_deepseek.py
- [ ] T046 [P] [US3] Implement test_detect_repetition_anomaly (反復テキスト → 異常検出文字列) in tests/test_ocr_deepseek.py
- [ ] T047 [P] [US3] Implement test_detect_repetition_empty (空テキスト → None) in tests/test_ocr_deepseek.py

### テスト実装 (RED) — describe_figures

- [ ] T048 [P] [US3] Implement test_figure_marker_regex (各種マーカー文字列のマッチ検証) in tests/test_describe_figures.py
- [ ] T049 [P] [US3] Implement test_describe_single_mock (Ollama API モック → 説明文出力検証) in tests/test_describe_figures.py

- [ ] T050 Verify `make test` FAIL (RED) — テスト対象のモック設定等でインポートは通るが assertion が FAIL
- [ ] T051 Generate RED output: specs/001-code-refactoring/red-tests/ph4-test.md

### 実装 (GREEN)

- [ ] T052 Read RED tests: specs/001-code-refactoring/red-tests/ph4-test.md
- [ ] T053 [P] [US3] Apply context manager pattern to Image.open() in src/deduplicate.py (line ~42)
- [ ] T054 [P] [US3] Apply context manager pattern to Image.open() in src/ocr_deepseek.py (line ~206)
- [ ] T055 Verify `make test` PASS (GREEN)

### 検証

- [ ] T056 Verify `make test` passes all tests (US1 + US2 + US3 — no regressions)
- [ ] T057 Generate phase output: specs/001-code-refactoring/tasks/ph4-output.md

**Checkpoint**: US1 + US2 + US3 完了。テストスイート導入、リソース管理改善済み。

---

## Phase 5: Polish & Cross-Cutting Concerns — NO TDD

**Purpose**: 最終確認、クリーンアップ、ドキュメント整合性

### 入力

- [ ] T058 Read previous phase output: specs/001-code-refactoring/tasks/ph4-output.md

### 実装

- [ ] T059 [P] Verify no duplicate function definitions: `grep -rn "def encode_image_file\|def _encode_image" src/` shows single definition
- [ ] T060 [P] Verify no private cross-imports: `grep -rn "from src\.\w\+ import _" src/` returns 0 results
- [ ] T061 [P] Verify requirements.txt contains no unused packages
- [ ] T062 [P] Verify `wc -l src/*.py` shows ~15% reduction from 1167 baseline

### 検証

- [ ] T063 Run `make test` to verify all tests pass after cleanup
- [ ] T064 Generate phase output: specs/001-code-refactoring/tasks/ph5-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — メインエージェント直接実行
- **US1 (Phase 2)**: Depends on Phase 1 — TDD フロー (tdd-generator → phase-executor)
- **US2 (Phase 3)**: Depends on Phase 2 (US1 must complete first to remove ocr.py dependency) — TDD フロー
- **US3 (Phase 4)**: Depends on Phase 3 (clean codebase needed for comprehensive tests) — TDD フロー
- **Polish (Phase 5)**: Depends on all user stories — phase-executor のみ

### Within Each User Story Phase (TDD Flow)

1. **入力**: Read previous phase output (context from prior work)
2. **テスト実装 (RED)**: Write tests FIRST → verify `make test` FAIL → generate RED output
3. **実装 (GREEN)**: Read RED tests → implement → verify `make test` PASS
4. **検証**: Confirm no regressions → generate phase output

### Agent Delegation

- **Phase 1 (Setup)**: メインエージェント直接実行
- **Phase 2-4 (User Stories)**: tdd-generator (RED) → phase-executor (GREEN + 検証)
- **Phase 5 (Polish)**: phase-executor のみ

### [P] マーク（依存関係なし）

`[P]` は「他タスクとの依存関係がなく、実行順序が自由」であることを示す。並列実行を保証するものではない。

- Setup タスクの [P]: 異なるファイルへの書き込みで相互依存なし
- RED テストの [P]: 異なるテストファイル/テスト関数への書き込みで相互依存なし
- GREEN 実装の [P]: 異なるソースファイルへの書き込みで相互依存なし
- User Story 間: 各 Phase は前 Phase の出力に依存するため [P] 不可

---

## Phase Output & RED Test Artifacts

### Directory Structure

```
specs/001-code-refactoring/
├── tasks.md                    # This file
├── tasks/
│   ├── ph1-output.md           # Phase 1 output (Setup results)
│   ├── ph2-output.md           # Phase 2 output (US1 GREEN results)
│   ├── ph3-output.md           # Phase 3 output (US2 GREEN results)
│   ├── ph4-output.md           # Phase 4 output (US3 GREEN results)
│   └── ph5-output.md           # Phase 5 output (Polish results)
└── red-tests/
    ├── ph2-test.md             # Phase 2 RED test results
    ├── ph3-test.md             # Phase 3 RED test results
    └── ph4-test.md             # Phase 4 RED test results
```

### Phase Output Content

Each `phN-output.md` should contain:
- Summary of what was done
- Files created/modified
- Test results (`make test` output)
- Any decisions or deviations from the plan

### RED Test Output Content

Each `phN-test.md` should contain:
- Test code written
- `make test` output showing FAIL (RED confirmation)
- Number of failing tests and their names

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Complete Phase 1: Setup (テスト基盤の初期化)
2. Complete Phase 2: User Story 1 — 共有ユーティリティ抽出 (RED → GREEN → 検証)
3. **STOP and VALIDATE**: `make test` で全テスト通過を確認
4. `python -c "from src.ocr_deepseek import ocr_page_deepseek"` が `ocr.py` なしで成功することを確認

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
2. Each phase commits: `feat(phase-N): description`

---

## Test Coverage Rules

**境界テストの原則**: データ変換が発生する**すべての境界**でテストを書く

```
[画像入力] → [base64エンコード] → [APIリクエスト] → [レスポンスパース] → [テキスト出力]
   ↓              ↓                    ↓                 ↓                ↓
 テスト          テスト              テスト(モック)       テスト            テスト
```

**チェックリスト**:
- [ ] base64 エンコード/デコードのラウンドトリップ
- [ ] figure marker フォーマット生成
- [ ] figure mask 座標計算・クランプ
- [ ] OCR API モック応答パース
- [ ] 反復検出ロジック
- [ ] 正規表現マッチング

---

## Notes

- [P] tasks = no dependencies, execution order free
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- TDD: テスト実装 (RED) → FAIL 確認 → 実装 (GREEN) → PASS 確認
- RED output must be generated BEFORE implementation begins
- Commit after each phase completion
- Stop at any checkpoint to validate story independently
- US2 depends on US1 (must break coupling before deleting ocr.py)
- US3 depends on US2 (clean codebase needed for accurate test coverage)
