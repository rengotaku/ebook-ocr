# Tasks: ROVER OCR再設計

**Input**: `/specs/008-rover-redesign/` の設計ドキュメント
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/api.md ✅

**Tests**: TDD は User Story フェーズで必須。各フェーズは Test Implementation (RED) → Implementation (GREEN) → Verification のワークフローに従う。

**Language**: 日本語

**Organization**: タスクはユーザーストーリー毎にグループ化し、各ストーリーの独立した実装とテストを可能にする。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 依存関係なし（異なるファイル、実行順序自由）
- **[Story]**: 所属するユーザーストーリー（例: US1, US2, US3）
- ファイルパスを説明に含める

## User Story Summary

| ID | Title | Priority | FR | Scenario |
|----|-------|----------|----|----------|
| US1 | 基本的なOCR補完 | P1 | FR-001,003,005,006 | yomitoku欠損を他エンジンから補完 |
| US2 | ゴミ出力の除外 | P1 | FR-004 | 低信頼度・ゴミ文字列の除外 |
| US3 | 文字レベルの投票による精度向上 | P2 | FR-002,003,005,009 | difflib文字アライメント + 重み付き投票 |
| US4 | 処理前後の比較可能性 | P2 | FR-007,008 | raw/とrover/ディレクトリ出力 |

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root

---

## Phase 1: Setup (共有インフラストラクチャ) — NO TDD

**Purpose**: プロジェクト初期化、既存コードレビュー、変更準備

- [x] T001 現在の実装を読む: src/ocr_engines.py
- [x] T002 [P] 現在の実装を読む: src/ocr_rover.py
- [x] T003 [P] 既存テストを読む: tests/test_ocr_rover.py（存在する場合）
- [x] T004 [P] 既存テストを読む: tests/conftest.py
- [x] T005 新規モジュールのスケルトン作成: src/ocr_preprocess.py
- [x] T006 [P] 新規モジュールのスケルトン作成: src/ocr_alignment.py
- [x] T007 フェーズ出力を生成: specs/008-rover-redesign/tasks/ph1-output.md

---

## Phase 2: US1 + US2 - 基本的なOCR補完 + ゴミ出力の除外 (Priority: P1) MVP

**Goal**: yomitokuの欠損を他エンジン（PaddleOCR, EasyOCR）から補完し、ゴミ出力を除外する基本機能

**Independent Test**: 意図的に欠損を含むyomitoku出力と、ゴミ出力を含むテストデータで、補完とフィルタが正しく動作することを確認

### Input

- [x] T008 前フェーズ出力を読む: specs/008-rover-redesign/tasks/ph1-output.md

### Test Implementation (RED)

- [x] T009 [P] [US2] ゴミ判定テストを実装: tests/test_ocr_rover.py::test_is_garbage_*
  - 空文字列 → ゴミ
  - confidence < 0.5 → ゴミ
  - 日本語なし5文字以下ASCII → ゴミ
  - 同一文字5回以上繰り返し → ゴミ
- [x] T010 [P] [US2] 信頼度正規化テストを実装: tests/test_ocr_rover.py::test_normalize_confidence_*
  - yomitoku: 0.4 → 0.0, 0.7 → 0.5, 1.0 → 1.0
  - paddleocr: 0.85 → 0.0, 0.925 → 0.5, 1.0 → 1.0
  - easyocr: 0.25 → 0.0, 0.625 → 0.5, 1.0 → 1.0
- [x] T011 [P] [US1] 行クラスタリングテストを実装: tests/test_ocr_rover.py::test_cluster_lines_by_y
- [x] T012 [P] [US1] 行アライメントテストを実装: tests/test_ocr_rover.py::test_align_lines_by_y
- [x] T013 [P] [US1] 基本的な補完テストを実装: tests/test_ocr_rover.py::test_rover_merge_basic
  - yomitoku欠損行がpaddleocrから補完されることを確認
- [x] T014 `make test` FAIL (RED) を確認
- [x] T015 RED出力を生成: specs/008-rover-redesign/red-tests/ph2-test.md

### Implementation (GREEN)

- [ ] T016 REDテストを読む: specs/008-rover-redesign/red-tests/ph2-test.md
- [ ] T017 [P] [US2] is_garbage関数を実装: src/ocr_rover.py
- [ ] T018 [P] [US2] normalize_confidence関数を実装: src/ocr_rover.py
- [ ] T019 [P] [US1] TextWithBox, OCRLine データクラスを実装: src/ocr_rover.py
- [ ] T020 [P] [US1] cluster_lines_by_y関数を実装: src/ocr_rover.py
- [ ] T021 [US1] align_lines_by_y関数を実装: src/ocr_rover.py
- [ ] T022 [US1] 基本的なrover_merge（行レベル投票）を実装: src/ocr_rover.py
- [ ] T023 `make test` PASS (GREEN) を確認

### Verification

- [ ] T024 `make test` が全テスト通過することを確認（リグレッションなし）
- [ ] T025 フェーズ出力を生成: specs/008-rover-redesign/tasks/ph2-output.md

**Checkpoint**: US1 + US2 の基本機能が動作し、独立してテスト可能

---

## Phase 3: US3 - 文字レベルの投票による精度向上 (Priority: P2)

**Goal**: difflib.SequenceMatcherを使った文字レベルアライメントと信頼度重み付き投票で精度向上

**Independent Test**: 部分的に異なる複数エンジンの出力で、多数決で正しい文字が採用されることを確認

### Input

- [ ] T026 セットアップ分析を読む: specs/008-rover-redesign/tasks/ph1-output.md
- [ ] T027 前フェーズ出力を読む: specs/008-rover-redesign/tasks/ph2-output.md

### Test Implementation (RED)

- [ ] T028 [P] [US3] 文字レベルアライメントテストを実装: tests/test_ocr_alignment.py::test_align_texts_character_level
  - 2テキストのアライメント
  - 3テキストのアライメント
  - ギャップを含むアライメント
- [ ] T029 [P] [US3] 重み付き投票テストを実装: tests/test_ocr_alignment.py::test_weighted_vote_character
  - 全員一致 → その文字
  - 2対1 → 多数派
  - 重み付きで逆転 → 重み勝ち
- [ ] T030 [P] [US3] アライメント統合テストを実装: tests/test_ocr_alignment.py::test_vote_aligned_text
  - 「ソフトウェア」vs「ソフトウエア」→「ソフトウェア」
- [ ] T031 [P] [US3] vote_line_text更新テストを実装: tests/test_ocr_rover.py::test_vote_line_text_character_level
- [ ] T032 `make test` FAIL (RED) を確認
- [ ] T033 RED出力を生成: specs/008-rover-redesign/red-tests/ph3-test.md

### Implementation (GREEN)

- [ ] T034 REDテストを読む: specs/008-rover-redesign/red-tests/ph3-test.md
- [ ] T035 [P] [US3] AlignedPositionデータクラスを実装: src/ocr_alignment.py
- [ ] T036 [P] [US3] align_texts_character_level関数を実装: src/ocr_alignment.py
- [ ] T037 [US3] weighted_vote_character関数を実装: src/ocr_alignment.py
- [ ] T038 [US3] vote_aligned_text関数を実装: src/ocr_alignment.py
- [ ] T039 [US3] vote_line_textを文字レベル投票に更新: src/ocr_rover.py
- [ ] T040 `make test` PASS (GREEN) を確認

### Verification

- [ ] T041 `make test` が全テスト通過することを確認（US1, US2含むリグレッションなし）
- [ ] T042 `make coverage` ≥80% を確認
- [ ] T043 フェーズ出力を生成: specs/008-rover-redesign/tasks/ph3-output.md

**Checkpoint**: US1, US2, US3 が全て動作し、独立してテスト可能

---

## Phase 4: US4 - 処理前後の比較可能性 (Priority: P2)

**Goal**: 各OCRエンジンの原文出力とROVER補完後の出力を比較可能にする

**Independent Test**: 出力ディレクトリ構造を確認し、raw/とrover/の両方にファイルが存在することを確認

### Input

- [ ] T044 セットアップ分析を読む: specs/008-rover-redesign/tasks/ph1-output.md
- [ ] T045 前フェーズ出力を読む: specs/008-rover-redesign/tasks/ph3-output.md

### Test Implementation (RED)

- [ ] T046 [P] [US4] CLAHE前処理テストを実装: tests/test_ocr_preprocess.py::test_apply_clahe
  - 入出力shape一致
  - dtype維持
- [ ] T047 [P] [US4] yomitoku words信頼度取得テストを実装: tests/test_ocr_engines.py::test_yomitoku_words_confidence
- [ ] T048 [P] [US4] easyocr CLAHE適用テストを実装: tests/test_ocr_engines.py::test_easyocr_with_clahe
- [ ] T049 [P] [US4] raw出力保存テストを実装: tests/test_ocr_rover.py::test_rover_batch_raw_output
- [ ] T050 [P] [US4] rover出力保存テストを実装: tests/test_ocr_rover.py::test_rover_batch_rover_output
- [ ] T051 `make test` FAIL (RED) を確認
- [ ] T052 RED出力を生成: specs/008-rover-redesign/red-tests/ph4-test.md

### Implementation (GREEN)

- [ ] T053 REDテストを読む: specs/008-rover-redesign/red-tests/ph4-test.md
- [ ] T054 [P] [US4] apply_clahe関数を実装: src/ocr_preprocess.py
- [ ] T055 [US4] run_yomitoku_with_boxesをwords信頼度対応に更新: src/ocr_engines.py
- [ ] T056 [US4] run_easyocr_with_boxesをCLAHE前処理対応に更新: src/ocr_engines.py
- [ ] T057 [US4] run_all_enginesをTesseract除外に更新: src/ocr_engines.py
- [ ] T058 [US4] run_rover_batchを実装（raw/, rover/出力）: src/ocr_rover.py
- [ ] T059 `make test` PASS (GREEN) を確認

### Verification

- [ ] T060 `make test` が全テスト通過することを確認（全USリグレッションなし）
- [ ] T061 `make coverage` ≥80% を確認
- [ ] T062 フェーズ出力を生成: specs/008-rover-redesign/tasks/ph4-output.md

**Checkpoint**: US1, US2, US3, US4 が全て動作し、独立してテスト可能

---

## Phase 5: Polish & 横断的関心事 — NO TDD

**Purpose**: 複数ユーザーストーリーに影響する改善

### Input

- [ ] T063 セットアップ分析を読む: specs/008-rover-redesign/tasks/ph1-output.md
- [ ] T064 前フェーズ出力を読む: specs/008-rover-redesign/tasks/ph4-output.md

### Implementation

- [ ] T065 [P] 廃止されたコードを削除（tesseract関連）
- [ ] T066 [P] 古いROVER実装を削除（行レベル投票のみの古いコード）
- [ ] T067 [P] コードクリーンアップとリファクタリング
- [ ] T068 Makefile `rover-ocr` ターゲットを更新
- [ ] T069 quickstart.md の検証を実行

### Verification

- [ ] T070 `make test` が全テスト通過することを確認
- [ ] T071 `make coverage` ≥80% を確認
- [ ] T072 パイプライン統合確認（実際の画像でROVER実行）
- [ ] T073 フェーズ出力を生成: specs/008-rover-redesign/tasks/ph5-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: 依存関係なし - Main agent 直接実行
- **User Stories (Phase 2-4)**: TDD フロー (tdd-generator → phase-executor)
  - User stories は優先度順に進行 (P1 → P2)
- **Polish (Phase 5)**: 全 user stories 完了後 - phase-executor のみ

### Within Each User Story Phase (TDD Flow)

1. **Input**: セットアップ分析 (ph1) + 前フェーズ出力を読む
2. **Test Implementation (RED)**: テストを先に書く → `make test` FAIL 確認 → RED出力生成
3. **Implementation (GREEN)**: REDテストを読む → 実装 → `make test` PASS 確認
4. **Verification**: リグレッションなしを確認 → フェーズ出力生成

### Agent Delegation

- **Phase 1 (Setup)**: Main agent 直接実行
- **Phase 2-4 (User Stories)**: tdd-generator (RED) → phase-executor (GREEN + Verification)
- **Phase 5 (Polish)**: phase-executor のみ

### [P] Marker (依存関係なし)

`[P]` は「他タスクへの依存なし、実行順序自由」を示す。並列実行を保証するものではない。

---

## Phase Output & RED Test Artifacts

### Directory Structure

```
specs/008-rover-redesign/
├── tasks.md                    # このファイル
├── tasks/
│   ├── ph1-output.md           # Phase 1 出力 (Setup結果)
│   ├── ph2-output.md           # Phase 2 出力 (US1+US2 GREEN結果)
│   ├── ph3-output.md           # Phase 3 出力 (US3 GREEN結果)
│   ├── ph4-output.md           # Phase 4 出力 (US4 GREEN結果)
│   └── ph5-output.md           # Phase 5 出力 (Polish結果)
└── red-tests/
    ├── ph2-test.md             # Phase 2 REDテスト結果 (FAIL確認)
    ├── ph3-test.md             # Phase 3 REDテスト結果 (FAIL確認)
    └── ph4-test.md             # Phase 4 REDテスト結果 (FAIL確認)
```

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Phase 1 完了: Setup (既存コードレビュー)
2. Phase 2 完了: US1 + US2 (RED → GREEN → Verification)
3. **STOP and VALIDATE**: `make test` で全テスト通過を確認
4. 必要に応じて手動テストで検証

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
2. 各フェーズでコミット: `feat(phase-N): description`

---

## Test Coverage Rules

**Boundary Test Principle**: データ変換が発生する**すべての境界**でテストを書く

```
[Image Input] → [CLAHE] → [OCR Engine] → [Garbage Filter] → [Line Clustering] → [Char Alignment] → [Voting] → [Output]
     ↓            ↓           ↓              ↓                  ↓                    ↓              ↓          ↓
   Test         Test        Test           Test               Test                 Test           Test       Test
```

**Checklist**:
- [ ] 入力処理テスト (CLAHE)
- [ ] エンジン出力テスト (信頼度取得)
- [ ] ゴミフィルタテスト
- [ ] 行クラスタリング/アライメントテスト
- [ ] **文字レベルアライメントテスト** (重要: 新機能)
- [ ] **投票テスト** (重要: 新機能)
- [ ] 出力生成テスト (raw/, rover/)
- [ ] End-to-Endテスト (画像 → 最終出力)

---

## Notes

- [P] タスク = 依存関係なし、実行順序自由
- [Story] ラベルはタスクをユーザーストーリーにマッピング
- 各ユーザーストーリーは独立して完了・テスト可能であるべき
- TDD: Test Implementation (RED) → Verify FAIL → Implementation (GREEN) → Verify PASS
- RED出力は実装開始前に生成必須
- 各フェーズ完了後にコミット
- 任意のチェックポイントで停止してストーリーを独立検証可能
- 避けるべき: 曖昧なタスク、同一ファイル競合、独立性を損なうストーリー間依存
