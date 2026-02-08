# Tasks: heading要素へのreadAloud属性付与ルール

**入力**: `/specs/003-heading-readaloud-rules/` のデザインドキュメント
**前提条件**: plan.md (必須), spec.md (必須), research.md, data-model.md, contracts/book.xsd

**テスト**: ユーザーストーリーフェーズにはTDDが必須。各フェーズは Test Implementation (RED) → Implementation (GREEN) → Verification ワークフローに従う。

## フォーマット: `[ID] [P?] [Story] 説明`

- **[P]**: 依存関係なし（異なるファイル、実行順序自由）
- **[Story]**: タスクが属するユーザーストーリー（US1, US2, US3）
- 説明には正確なファイルパスを含める

## ユーザーストーリー概要

| ID | タイトル | 優先度 | FR | シナリオ |
|----|----------|--------|-----|----------|
| US1 | 繰り返し柱の自動除外 | P1 | FR-001,002,003,010 | 柱・ページ番号読み上げ除外 |
| US2 | 装飾・区切り記号の除外 | P2 | FR-004,005 | 装飾記号・章節ラベル除外 |
| US3 | 参照・メタ情報の除外 | P3 | FR-006 | Webサイト・脚注除外 |

## パス規約

- **ソースコード**: `src/book_converter/`
- **テスト**: `tests/book_converter/`
- **Fixtures**: `tests/book_converter/fixtures/`

---

## Phase 1: Setup（共有インフラ）— TDDなし

**目的**: プロジェクト初期化、既存コード確認、変更準備

- [X] T001 `src/book_converter/models.py` の既存コードを確認
- [X] T002 [P] `src/book_converter/transformer.py` の既存コードを確認（transform_heading関数）
- [X] T003 [P] `tests/book_converter/test_transformer.py` の既存テストを確認
- [X] T004 [P] `src/book_converter/analyzer.py` を新規作成（空のモジュール）
- [X] T005 [P] `src/book_converter/config.py` を新規作成（空のモジュール）
- [X] T006 [P] `tests/book_converter/test_analyzer.py` を新規作成（空のテストファイル）
- [X] T007 [P] `tests/book_converter/fixtures/heading_patterns.md` を新規作成（テスト用サンプルデータ）
- [X] T008 フェーズ出力を生成: specs/003-heading-readaloud-rules/tasks/ph1-output.md

---

## Phase 2: User Story 1 - 繰り返し柱の自動除外 (Priority: P1) — MVP

**Goal**: 柱（ランニングヘッド）とページ番号表記を自動検出し、`readAloud="false"`を付与

**独立テスト**: 任意のページをTTSで読み上げ、書籍タイトル（柱）やページ番号表記が音声に含まれないことを確認

### Input

- [x] T009 前フェーズ出力を読む: specs/003-heading-readaloud-rules/tasks/ph1-output.md

### Test Implementation (RED)

- [x] T010 [P] [US1] ExclusionPatternモデルテストを実装: tests/book_converter/test_models.py
- [x] T011 [P] [US1] HeadingAnalysisモデルテストを実装: tests/book_converter/test_models.py
- [x] T012 [P] [US1] 柱検出テストを実装: tests/book_converter/test_analyzer.py（analyze_headings関数、最頻出level=1検出）
- [x] T013 [P] [US1] ページ番号パターンテストを実装: tests/book_converter/test_analyzer.py（`X.X.X — N/M`形式マッチング）
- [x] T014 [P] [US1] level再配置テストを実装: tests/book_converter/test_analyzer.py（level 2,3を1に再配置）
- [x] T015 [P] [US1] readAloud属性付与テストを実装: tests/book_converter/test_transformer.py（transform_headingでreadAloud="false"出力）
- [x] T016 [P] [US1] 統合テストを実装: tests/book_converter/test_analyzer.py（Markdown→heading分析→属性付与フロー）
- [x] T017 `make test` FAIL (RED) を確認
- [x] T018 RED出力を生成: specs/003-heading-readaloud-rules/red-tests/ph2-test.md

### Implementation (GREEN)

- [x] T019 REDテストを読む: specs/003-heading-readaloud-rules/red-tests/ph2-test.md
- [x] T020 [P] [US1] `src/book_converter/models.py` にExclusionPatternを実装
- [x] T021 [P] [US1] `src/book_converter/models.py` にHeadingAnalysisを実装
- [x] T022 [P] [US1] `src/book_converter/config.py` にデフォルトパターン定義を実装（running-head, page-number）
- [x] T023 [P] [US1] `src/book_converter/analyzer.py` にanalyze_headings関数を実装（heading頻度分析）
- [x] T024 [P] [US1] `src/book_converter/analyzer.py` にdetect_running_head関数を実装（柱検出、閾値50%）
- [x] T025 [P] [US1] `src/book_converter/analyzer.py` にreassign_heading_level関数を実装（level再配置）
- [x] T026 [P] [US1] `src/book_converter/analyzer.py` にmatch_exclusion_pattern関数を実装（パターンマッチング）
- [x] T027 [P] [US1] `src/book_converter/transformer.py` のtransform_heading関数を拡張（readAloud属性出力）
- [x] T028 [US1] コンポーネント統合（T020-T027の結合確認）
- [x] T029 `make test` PASS (GREEN) を確認

### Verification

- [x] T030 `make test` で全テスト通過を確認（リグレッションなし）
- [x] T031 フェーズ出力を生成: specs/003-heading-readaloud-rules/tasks/ph2-output.md

**チェックポイント**: User Story 1は完全に機能し、独立してテスト可能

---

## Phase 3: User Story 2 - 装飾・区切り記号の除外 (Priority: P2)

**Goal**: 装飾記号（◆◆◆）と章節ラベル（Section X.X）を除外

**独立テスト**: 装飾記号や章節ラベルを含むページをTTSで読み上げ、これらが音声に含まれないことを確認

### Input

- [x] T032 セットアップ分析を読む: specs/003-heading-readaloud-rules/tasks/ph1-output.md
- [x] T033 前フェーズ出力を読む: specs/003-heading-readaloud-rules/tasks/ph2-output.md

### Test Implementation (RED)

- [x] T034 [P] [US2] 装飾記号パターンテストを実装: tests/book_converter/test_analyzer.py（`◆◆◆`等の連続記号）
- [x] T035 [P] [US2] 章節ラベルパターンテストを実装: tests/book_converter/test_analyzer.py（`Section X.X`形式）
- [x] T036 [P] [US2] 本文見出し除外されないテストを実装: tests/book_converter/test_analyzer.py（「3.2.1 モニタリングの基本」はreadAloud=true）
- [x] T037 `make test` FAIL (RED) を確認
- [x] T038 RED出力を生成: specs/003-heading-readaloud-rules/red-tests/ph3-test.md

### Implementation (GREEN)

- [x] T039 REDテストを読む: specs/003-heading-readaloud-rules/red-tests/ph3-test.md
- [x] T040 [P] [US2] `src/book_converter/config.py` にdecorationパターンを追加
- [x] T041 [P] [US2] `src/book_converter/config.py` にsection-labelパターンを追加
- [x] T042 [US2] コンポーネント統合（T040-T041の結合確認）
- [x] T043 `make test` PASS (GREEN) を確認

### Verification

- [x] T044 `make test` で全テスト通過を確認（US1リグレッションなし）
- [x] T045 フェーズ出力を生成: specs/003-heading-readaloud-rules/tasks/ph3-output.md

**チェックポイント**: User Stories 1 AND 2は両方とも独立して動作

---

## Phase 4: User Story 3 - 参照・メタ情報の除外 (Priority: P3)

**Goal**: Webサイト参照リンク表記と脚注番号を除外

**独立テスト**: 「Webサイト」や「注3.1」を含むページをTTSで読み上げ、デフォルトでは読み上げられないことを確認

### Input

- [x] T046 セットアップ分析を読む: specs/003-heading-readaloud-rules/tasks/ph1-output.md
- [x] T047 前フェーズ出力を読む: specs/003-heading-readaloud-rules/tasks/ph3-output.md

### Test Implementation (RED)

- [x] T048 [P] [US3] Webサイト参照パターンテストを実装: tests/book_converter/test_analyzer.py（`^Webサイト$`マッチング）
- [x] T049 [P] [US3] 脚注番号パターンテストを実装: tests/book_converter/test_analyzer.py（`注X.X`形式）
- [x] T050 `make test` FAIL (RED) を確認
- [x] T051 RED出力を生成: specs/003-heading-readaloud-rules/red-tests/ph4-test.md

### Implementation (GREEN)

- [x] T052 REDテストを読む: specs/003-heading-readaloud-rules/red-tests/ph4-test.md
- [x] T053 [P] [US3] `src/book_converter/config.py` にreferenceパターンを追加
- [x] T054 [P] [US3] `src/book_converter/config.py` にfootnoteパターンを追加
- [x] T055 [US3] コンポーネント統合（T053-T054の結合確認）
- [x] T056 `make test` PASS (GREEN) を確認

### Verification

- [x] T057 `make test` で全テスト通過を確認（US1, US2リグレッションなし）
- [x] T058 フェーズ出力を生成: specs/003-heading-readaloud-rules/tasks/ph4-output.md

**チェックポイント**: User Stories 1, 2, 3はすべて独立して動作

---

## Phase 5: Polish & Cross-Cutting Concerns — TDDなし

**目的**: コード品質向上、CLI統合、最終検証

### Input

- [ ] T059 セットアップ分析を読む: specs/003-heading-readaloud-rules/tasks/ph1-output.md
- [ ] T060 前フェーズ出力を読む: specs/003-heading-readaloud-rules/tasks/ph4-output.md

### Implementation

- [ ] T061 [P] `src/book_converter/cli.py` に `--running-head-threshold` オプションを追加（FR-008）
- [ ] T062 [P] `src/book_converter/cli.py` に `--verbose` オプションで除外理由表示を追加
- [ ] T063 [P] `make test-cov` でカバレッジ確認（≥80%目標）
- [ ] T064 [P] コード品質チェック（ruff check src/book_converter/）
- [ ] T065 [P] ファイルサイズ確認（各ファイル800行以下、各関数50行以下）
- [ ] T066 quickstart.md 検証（CLIコマンド動作確認）
- [ ] T067 book.xsd に対するXML検証テスト追加

### Verification

- [ ] T068 `make test` で全テスト通過を確認
- [ ] T069 フェーズ出力を生成: specs/003-heading-readaloud-rules/tasks/ph5-output.md

---

## 依存関係と実行順序

### フェーズ依存関係

- **Setup (Phase 1)**: 依存なし - メインエージェント直接実行
- **User Stories (Phase 2-4)**: TDDフロー（tdd-generator → phase-executor）
  - ユーザーストーリーは優先度順に順次進行（P1 → P2 → P3）
- **Polish (Phase 5)**: 全ユーザーストーリー完了後 - phase-executorのみ

### 各ユーザーストーリーフェーズ内 (TDDフロー)

1. **Input**: セットアップ分析(ph1) + 前フェーズ出力（前作業のコンテキスト）を読む
2. **Test Implementation (RED)**: テストをFIRST作成 → `make test` FAIL確認 → RED出力生成
3. **Implementation (GREEN)**: REDテスト読む → 実装 → `make test` PASS確認
4. **Verification**: リグレッションなし確認 → フェーズ出力生成

### エージェント委任

- **Phase 1 (Setup)**: メインエージェント直接実行
- **Phase 2-4 (User Stories)**: tdd-generator (RED) → phase-executor (GREEN + Verification)
- **Phase 5 (Polish)**: phase-executorのみ

### [P] マーカー（依存なし）

`[P]` は「他タスクへの依存なし、実行順序自由」を示す。並列実行を保証するものではない。

- Setup タスク [P]: 異なるファイル/ディレクトリ作成で相互依存なし
- RED テスト [P]: 異なるテストファイルへの書き込みで相互依存なし
- GREEN 実装 [P]: 異なるソースファイルへの書き込みで相互依存なし
- ユーザーストーリー間: 各フェーズは前フェーズ出力に依存するため [P] 適用不可

---

## フェーズ出力 & REDテスト成果物

### ディレクトリ構造

```
specs/003-heading-readaloud-rules/
├── tasks.md                    # このファイル
├── tasks/
│   ├── ph1-output.md           # Phase 1 出力（Setup結果）
│   ├── ph2-output.md           # Phase 2 出力（US1 GREEN結果）
│   ├── ph3-output.md           # Phase 3 出力（US2 GREEN結果）
│   ├── ph4-output.md           # Phase 4 出力（US3 GREEN結果）
│   └── ph5-output.md           # Phase 5 出力（Polish結果）
└── red-tests/
    ├── ph2-test.md             # Phase 2 REDテスト結果（FAIL確認）
    ├── ph3-test.md             # Phase 3 REDテスト結果（FAIL確認）
    └── ph4-test.md             # Phase 4 REDテスト結果（FAIL確認）
```

### フェーズ出力内容

各 `phN-output.md` には以下を含める:
- 実施内容のサマリー
- 作成/修正したファイル
- テスト結果（`make test` 出力）
- 計画からの逸脱や決定事項

### REDテスト出力内容

各 `phN-test.md` には以下を含める:
- 作成したテストコード
- `make test` 出力（FAIL=RED確認）
- 失敗テスト数と名前

---

## 実装戦略

### MVP First (Phase 1 + Phase 2)

1. Phase 1 完了: Setup（既存コード確認）
2. Phase 2 完了: User Story 1（RED → GREEN → Verification）
3. **停止と検証**: `make test` で全テスト通過確認
4. 必要に応じて手動テスト検証

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
2. 各フェーズでコミット: `feat(phase-N): description`

---

## テストカバレッジルール

**境界テスト原則**: データ変換が発生する**すべての境界**でテストを書く

```
[Heading Text] → [Analyze] → [Pattern Match] → [Attribute Assignment] → [XML Output]
      ↓             ↓              ↓                   ↓                    ↓
    Test          Test           Test               Test                 Test
```

**チェックリスト**:
- [ ] heading頻度分析テスト
- [ ] パターンマッチングテスト
- [ ] readAloud属性付与テスト
- [ ] **XML出力テスト**（見落としがち）
- [ ] E2Eテスト（入力 → 最終出力）

---

## 注意事項

- [P] タスク = 依存なし、実行順序自由
- [Story] ラベルはタスクを特定のユーザーストーリーに紐付けてトレーサビリティ確保
- 各ユーザーストーリーは独立して完了・テスト可能であるべき
- TDD: Test Implementation (RED) → FAIL確認 → Implementation (GREEN) → PASS確認
- RED出力は実装開始前に必ず生成
- 各フェーズ完了後にコミット
- 任意のチェックポイントで停止してストーリーを独立検証可能
- 避けるべき: 曖昧なタスク、同一ファイル競合、ストーリー間独立性を壊す依存関係
