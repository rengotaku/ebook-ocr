# Tasks: コードブロックタグ付け機能

**Input**: 設計ドキュメント `/specs/014-code-block-tagging/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**Tests**: TDD必須（User Storyフェーズ）。各フェーズはTest Implementation (RED) → Implementation (GREEN) → Verificationの順で実行。

**Language**: 日本語

**Organization**: タスクはUser Story単位でグループ化し、独立した実装・テストを可能にする。

## Format: `[ID] [P?] [Story] 説明`

- **[P]**: 依存なし（異なるファイル、実行順序自由）
- **[Story]**: どのUser Storyに属するか（例: US1）
- 説明には正確なファイルパスを含める

## User Story サマリー

| ID | タイトル | 優先度 | FR | シナリオ |
|----|----------|--------|-----|----------|
| US1 | コードブロックの検出とタグ付け | P1 | FR-001〜FR-006 | コード検出→CODE再分類→XML出力 |

## パス規則

- **ソースコード**: `src/` (リポジトリルート)
- **テスト**: `tests/` (リポジトリルート)
- **feature dir**: `specs/014-code-block-tagging/`

---

## Phase 1: Setup（共有インフラ）— NO TDD

**目的**: プロジェクト初期化、既存コードレビュー、依存関係確認

- [X] T001 既存のレイアウト検出実装を確認: src/layout/detector.py
- [X] T002 [P] 既存のbook_converterモデルを確認: src/book_converter/models.py
- [X] T003 [P] 既存のXMLビルダーを確認: src/book_converter/xml_builder.py
- [X] T004 [P] 既存のパーサー構造を確認: src/book_converter/parser/
- [X] T005 [P] 依存関係の追加確認: requirements.txt (guesslang追加の必要性)
- [X] T006 フェーズ出力を生成: specs/014-code-block-tagging/tasks/ph1-output.md

---

## Phase 2: User Story 1 - コード検出コア機能 (Priority: P1) MVP

**Goal**: yomitokuのTEXT領域にGuesslang判定を適用し、コード領域を識別する

**Independent Test**: TEXT領域を含むlayout.jsonを入力し、コード領域が正しくCODEタイプに再分類されることを確認

### Input

- [ ] T007 前フェーズ出力を読み込み: specs/014-code-block-tagging/tasks/ph1-output.md

### Test Implementation (RED)

- [ ] T008 [P] [US1] Guesslangコード判定のテストを実装: tests/unit/layout/test_code_detector.py
  - `test_is_code_with_python_code` - Pythonコードがコードと判定される
  - `test_is_code_with_java_code` - Javaコードがコードと判定される
  - `test_is_code_with_japanese_text` - 日本語テキストが非コードと判定される
  - `test_is_code_with_empty_string` - 空文字列が非コードと判定される
- [ ] T009 [P] [US1] CodeRegion dataclassのテストを実装: tests/unit/layout/test_code_detector.py
  - `test_code_region_creation` - CodeRegionの生成
  - `test_code_region_immutability` - frozen dataclassの不変性
- [ ] T010 [P] [US1] layout.json更新のテストを実装: tests/unit/layout/test_code_detector.py
  - `test_detect_code_in_layout` - TEXT→CODE再分類
  - `test_detect_code_preserves_non_text_regions` - FIGURE等は維持
  - `test_detect_code_with_threshold` - 閾値による判定
- [ ] T011 `make test` がFAIL (RED) することを確認
- [ ] T012 RED出力を生成: specs/014-code-block-tagging/red-tests/ph2-test.md

### Implementation (GREEN)

- [ ] T013 REDテストを読み込み: specs/014-code-block-tagging/red-tests/ph2-test.md
- [ ] T014 [P] [US1] CodeRegion dataclassを実装: src/layout/code_detector.py
- [ ] T015 [P] [US1] CodeDetectionResult dataclassを実装: src/layout/code_detector.py
- [ ] T016 [US1] is_code()関数を実装: src/layout/code_detector.py
  - Guesslangを使用したコード判定
  - 閾値パラメータ対応
- [ ] T017 [US1] detect_code_regions()関数を実装: src/layout/code_detector.py
  - layout.jsonのTEXT領域を走査
  - 各TEXT領域にGuesslang判定を適用
  - CODE判定の場合はtype変更
- [ ] T018 `make test` がPASS (GREEN) することを確認

### Verification

- [ ] T019 `make test` で全テスト通過を確認（リグレッションなし）
- [ ] T020 フェーズ出力を生成: specs/014-code-block-tagging/tasks/ph2-output.md

**Checkpoint**: コード検出コア機能が単体で動作・テスト可能

---

## Phase 3: User Story 1 - データモデル拡張 (Priority: P1)

**Goal**: Code dataclassを追加し、SectionElementに統合する

**Independent Test**: Code要素を含むSectionが正しく生成されることを確認

### Input

- [ ] T021 setup分析を読み込み: specs/014-code-block-tagging/tasks/ph1-output.md
- [ ] T022 前フェーズ出力を読み込み: specs/014-code-block-tagging/tasks/ph2-output.md

### Test Implementation (RED)

- [ ] T023 [P] [US1] Code dataclassのテストを実装: tests/unit/book_converter/test_models.py
  - `test_code_creation` - Code生成
  - `test_code_default_read_aloud_false` - readAloudデフォルトFalse
  - `test_code_immutability` - frozen dataclassの不変性
  - `test_code_with_confidence` - confidence属性
- [ ] T024 [P] [US1] SectionElement拡張のテストを実装: tests/unit/book_converter/test_models.py
  - `test_section_element_includes_code` - Union型にCode含む
  - `test_section_with_code_element` - Section.elementsにCode
- [ ] T025 `make test` がFAIL (RED) することを確認
- [ ] T026 RED出力を生成: specs/014-code-block-tagging/red-tests/ph3-test.md

### Implementation (GREEN)

- [ ] T027 REDテストを読み込み: specs/014-code-block-tagging/red-tests/ph3-test.md
- [ ] T028 [US1] Code dataclassを追加: src/book_converter/models.py
- [ ] T029 [US1] SectionElement Union型を更新: src/book_converter/models.py
- [ ] T030 `make test` がPASS (GREEN) することを確認

### Verification

- [ ] T031 `make test` で全テスト通過を確認（リグレッションなし）
- [ ] T032 フェーズ出力を生成: specs/014-code-block-tagging/tasks/ph3-output.md

**Checkpoint**: データモデルが拡張され、Code要素が使用可能

---

## Phase 4: User Story 1 - パーサー統合 (Priority: P1)

**Goal**: コード領域をパースしてCode要素を生成し、XMLに出力する

**Independent Test**: CODE領域を含むlayout.jsonから`<code readAloud="false">`が出力されることを確認

### Input

- [ ] T033 setup分析を読み込み: specs/014-code-block-tagging/tasks/ph1-output.md
- [ ] T034 前フェーズ出力を読み込み: specs/014-code-block-tagging/tasks/ph3-output.md

### Test Implementation (RED)

- [ ] T035 [P] [US1] コードパーサーのテストを実装: tests/unit/book_converter/parser/test_code.py
  - `test_parse_code_region` - CODE領域からCode要素生成
  - `test_parse_code_preserves_formatting` - 改行・インデント保持
  - `test_parse_code_with_special_chars` - 特殊文字処理
- [ ] T036 [P] [US1] XMLビルダーのテストを実装: tests/unit/book_converter/test_xml_builder.py
  - `test_build_xml_with_code` - `<code>`要素出力
  - `test_code_element_has_read_aloud_false` - readAloud属性
  - `test_code_element_escapes_special_chars` - XMLエスケープ
- [ ] T037 `make test` がFAIL (RED) することを確認
- [ ] T038 RED出力を生成: specs/014-code-block-tagging/red-tests/ph4-test.md

### Implementation (GREEN)

- [ ] T039 REDテストを読み込み: specs/014-code-block-tagging/red-tests/ph4-test.md
- [ ] T040 [P] [US1] コードパーサーモジュールを作成: src/book_converter/parser/code.py
- [ ] T041 [US1] XMLビルダーにCode要素出力を追加: src/book_converter/xml_builder.py
- [ ] T042 `make test` がPASS (GREEN) することを確認

### Verification

- [ ] T043 `make test` で全テスト通過を確認（リグレッションなし）
- [ ] T044 フェーズ出力を生成: specs/014-code-block-tagging/tasks/ph4-output.md

**Checkpoint**: パーサーとXMLビルダーが統合され、Code要素がXML出力可能

---

## Phase 5: User Story 1 - 統合テスト (Priority: P1)

**Goal**: エンドツーエンドでコード検出→XML出力のパイプラインを検証

**Independent Test**: サンプル画像からコードブロックが検出され、XMLに出力されることを確認

### Input

- [ ] T045 setup分析を読み込み: specs/014-code-block-tagging/tasks/ph1-output.md
- [ ] T046 前フェーズ出力を読み込み: specs/014-code-block-tagging/tasks/ph4-output.md

### Test Implementation (RED)

- [ ] T047 [P] [US1] パイプライン統合テストを実装: tests/integration/test_code_pipeline.py
  - `test_code_detection_pipeline` - layout.json→CODE検出→XML
  - `test_code_detection_with_mixed_content` - コードと日本語混在
  - `test_code_detection_false_positive` - コラム等の誤検出なし
- [ ] T048 `make test` がFAIL (RED) することを確認
- [ ] T049 RED出力を生成: specs/014-code-block-tagging/red-tests/ph5-test.md

### Implementation (GREEN)

- [ ] T050 REDテストを読み込み: specs/014-code-block-tagging/red-tests/ph5-test.md
- [ ] T051 [US1] 統合処理を実装（必要に応じて）
- [ ] T052 `make test` がPASS (GREEN) することを確認

### Verification

- [ ] T053 `make test` で全テスト通過を確認（リグレッションなし）
- [ ] T054 `make coverage` でカバレッジ≥80%を確認
- [ ] T055 フェーズ出力を生成: specs/014-code-block-tagging/tasks/ph5-output.md

**Checkpoint**: User Story 1が完全に機能し、独立してテスト可能

---

## Phase 6: Polish & Cross-Cutting Concerns — NO TDD

**目的**: 複数User Storyに影響する改善

### Input

- [ ] T056 setup分析を読み込み: specs/014-code-block-tagging/tasks/ph1-output.md
- [ ] T057 前フェーズ出力を読み込み: specs/014-code-block-tagging/tasks/ph5-output.md

### Implementation

- [ ] T058 [P] エッジケーステスト追加: tests/unit/layout/test_code_detector.py
  - 空のコードブロック
  - 閾値付近の判定
  - 長いコードブロック
- [ ] T059 [P] パフォーマンス検証: SC-004（20%以内の性能低下）
- [ ] T060 [P] quickstart.md検証を実行
- [ ] T061 ドキュメント更新（必要に応じて）

### Verification

- [ ] T062 `make test` で全テスト通過を確認
- [ ] T063 フェーズ出力を生成: specs/014-code-block-tagging/tasks/ph6-output.md

---

## 依存関係 & 実行順序

### フェーズ依存

- **Setup (Phase 1)**: 依存なし - メインエージェント直接実行
- **User Stories (Phase 2-5)**: TDDフロー (tdd-generator → phase-executor)
  - Phase 2: コード検出コア
  - Phase 3: データモデル拡張
  - Phase 4: パーサー統合
  - Phase 5: 統合テスト
- **Polish (Phase 6)**: 全User Story完了後 - phase-executorのみ

### 各User Storyフェーズ内（TDDフロー）

1. **Input**: setup分析(ph1) + 前フェーズ出力を読み込み
2. **Test Implementation (RED)**: テストを先に書く → `make test` FAIL確認 → RED出力生成
3. **Implementation (GREEN)**: REDテスト読み込み → 実装 → `make test` PASS確認
4. **Verification**: リグレッションなし確認 → フェーズ出力生成

### エージェント委任

- **Phase 1 (Setup)**: メインエージェント直接実行
- **Phase 2-5 (User Story)**: tdd-generator (RED) → phase-executor (GREEN + Verification)
- **Phase 6 (Polish)**: phase-executorのみ

### [P] マーカー（依存なし）

`[P]` は「他タスクへの依存なし、実行順序自由」を示す。並列実行を保証するものではない。

---

## フェーズ出力 & REDテスト成果物

### ディレクトリ構造

```
specs/014-code-block-tagging/
├── tasks.md                    # このファイル
├── tasks/
│   ├── ph1-output.md           # Phase 1出力（Setup結果）
│   ├── ph2-output.md           # Phase 2出力（コア検出GREEN結果）
│   ├── ph3-output.md           # Phase 3出力（データモデルGREEN結果）
│   ├── ph4-output.md           # Phase 4出力（パーサーGREEN結果）
│   ├── ph5-output.md           # Phase 5出力（統合テストGREEN結果）
│   └── ph6-output.md           # Phase 6出力（Polish結果）
└── red-tests/
    ├── ph2-test.md             # Phase 2 REDテスト結果
    ├── ph3-test.md             # Phase 3 REDテスト結果
    ├── ph4-test.md             # Phase 4 REDテスト結果
    └── ph5-test.md             # Phase 5 REDテスト結果
```

---

## 実装戦略

### MVP First (Phase 1 + Phase 2)

1. Phase 1完了: Setup（既存コードレビュー）
2. Phase 2完了: コード検出コア（RED → GREEN → Verification）
3. **STOP and VALIDATE**: `make test` で全テスト通過確認
4. 手動テスト: サンプル画像でコード検出を確認

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6
2. 各フェーズでコミット: `feat(phase-N): 説明`

---

## テストカバレッジルール

**境界テスト原則**: データ変換が発生する**すべての境界**でテストを書く

```
[layout.json] → [CODE検出] → [Code生成] → [XML出力]
      ↓             ↓            ↓           ↓
    Test          Test         Test        Test
```

**チェックリスト**:
- [ ] Guesslang判定テスト
- [ ] CODE領域再分類テスト
- [ ] Code dataclass生成テスト
- [ ] **XML出力テスト**（見落としがち）
- [ ] E2Eテスト（layout.json → XML）

---

## Notes

- [P] タスク = 依存なし、実行順序自由
- [Story] ラベルでタスクをUser Storyに紐付け
- 各User Storyは独立して完了・テスト可能
- TDD: Test Implementation (RED) → FAIL確認 → Implementation (GREEN) → PASS確認
- RED出力は実装開始前に必ず生成
- 各フェーズ完了後にコミット
- チェックポイントでUser Storyを個別に検証可能
- 回避: 曖昧なタスク、同一ファイル競合、User Story間の依存でindependence破壊
