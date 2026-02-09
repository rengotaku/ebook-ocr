# タスク: TOC解析改行結合とページ欠損修正

**入力**: 設計ドキュメント `/specs/006-fix-toc-line-merge/`
**前提条件**: plan.md, spec.md, research.md, data-model.md, quickstart.md

**テスト**: TDDは必須。各フェーズはTest Implementation (RED) → Implementation (GREEN) → Verificationのワークフローに従う。

**構成**: タスクはユーザーストーリーごとにグループ化され、各ストーリーの独立した実装とテストを可能にする。

## フォーマット: `[ID] [P?] [Story] 説明`

- **[P]**: 依存関係なし（異なるファイル、実行順序自由）
- **[Story]**: このタスクが属するユーザーストーリー（US1, US2, US3など）
- 説明には正確なファイルパスを含める

## ユーザーストーリー概要

| ID | タイトル | 優先度 | FR | シナリオ |
|----|----------|--------|-----|----------|
| US1 | TOC改行分割エントリの結合 | P1 | FR-001,002,003,004,007 | シナリオ1-3 |
| US2 | ページ欠損の防止 | P1 | FR-005,008 | シナリオ1-4 |
| US3 | 既存動作の保持 | P1 | FR-006 | シナリオ1-2 |

## パス規約

- **ソースコード**: `src/book_converter/`
- **テスト**: `tests/book_converter/`
- **設計ドキュメント**: `specs/006-fix-toc-line-merge/`

---

## Phase 1: Setup（共有インフラ）— NO TDD

**目的**: 既存コードのレビューと変更準備

- [X] T001 既存実装を確認: src/book_converter/parser.py（parse_toc_entry, normalize_toc_line）
- [X] T002 [P] 既存実装を確認: src/book_converter/page_grouper.py（group_pages_by_toc）
- [X] T003 [P] 既存テストを確認: tests/book_converter/test_parser.py
- [X] T004 [P] 既存テストを確認: tests/book_converter/test_page_grouper.py
- [X] T005 問題ファイルのTOC構造を分析: output/157012a97dcbebed/book.md
- [X] T006 正常ファイルのTOC構造を分析: output/4fd5500620491ebe/book.md（回帰テスト用ベースライン）
- [X] T007 フェーズ出力を生成: specs/006-fix-toc-line-merge/tasks/ph1-output.md

---

## Phase 2: User Story 1 - TOC改行分割エントリの結合 (優先度: P1) MVP

**目標**: Chapter、Episode、Columnの分割行を正しく結合し、parse_toc_entryで認識可能にする

**独立テスト**: 改行で分割されたTOCを含むマークダウンを入力し、XMLのTOCエントリが正しく結合されていることを確認

### Input

- [X] T008 前フェーズ出力を読む: specs/006-fix-toc-line-merge/tasks/ph1-output.md

### Test Implementation (RED)

- [X] T009 [P] [US1] merge_toc_linesのテストを実装: tests/book_converter/test_parser.py（Chapter結合）
- [X] T010 [P] [US1] merge_toc_linesのテストを実装: tests/book_converter/test_parser.py（Episode結合）
- [X] T011 [P] [US1] merge_toc_linesのテストを実装: tests/book_converter/test_parser.py（Column結合）
- [X] T012 [P] [US1] normalize_toc_lineのテストを実装: tests/book_converter/test_parser.py（**強調**除去）
- [X] T013 [P] [US1] parse_toc_entryのテストを実装: tests/book_converter/test_parser.py（Chapter N形式認識）
- [X] T014 `make test` FAIL (RED) を確認
- [X] T015 RED出力を生成: specs/006-fix-toc-line-merge/red-tests/ph2-test.md

### Implementation (GREEN)

- [X] T016 REDテストを読む: specs/006-fix-toc-line-merge/red-tests/ph2-test.md
- [X] T017 [P] [US1] normalize_toc_lineを拡張（**強調**除去）: src/book_converter/parser.py
- [X] T018 [P] [US1] merge_toc_lines関数を実装: src/book_converter/parser.py
- [X] T019 [US1] parse_toc_entryを拡張（Chapter N形式）: src/book_converter/parser.py
- [X] T020 [US1] _parse_single_page_contentでmerge_toc_linesを呼び出し: src/book_converter/parser.py
- [X] T021 `make test` PASS (GREEN) を確認

### Verification

- [ ] T022 `make test` で全テスト成功を確認（回帰なし）
- [ ] T023 フェーズ出力を生成: specs/006-fix-toc-line-merge/tasks/ph2-output.md

**チェックポイント**: US1が独立して動作・テスト可能であることを確認

---

## Phase 3: User Story 2 - ページ欠損の防止 (優先度: P1)

**目標**: TOC構造が不完全でもすべてのページをXML出力に含め、50%以上欠損時はエラー報告

**独立テスト**: 181ページ入力時に181ページすべてが出力XMLに含まれることを確認

### Input

- [x] T024 セットアップ分析を読む: specs/006-fix-toc-line-merge/tasks/ph1-output.md
- [x] T025 前フェーズ出力を読む: specs/006-fix-toc-line-merge/tasks/ph2-output.md

### Test Implementation (RED)

- [x] T026 [P] [US2] validate_page_countのテストを実装: tests/book_converter/test_page_grouper.py（正常ケース）
- [x] T027 [P] [US2] validate_page_countのテストを実装: tests/book_converter/test_page_grouper.py（50%欠損エラー）
- [x] T028 [P] [US2] group_pages_by_tocのテストを実装: tests/book_converter/test_page_grouper.py（全ページ保持）
- [x] T029 [P] [US2] group_pages_by_tocのテストを実装: tests/book_converter/test_page_grouper.py（TOC空でもfront-matter配置）
- [x] T030 `make test` FAIL (RED) を確認
- [x] T031 RED出力を生成: specs/006-fix-toc-line-merge/red-tests/ph3-test.md

### Implementation (GREEN)

- [X] T032 REDテストを読む: specs/006-fix-toc-line-merge/red-tests/ph3-test.md
- [X] T033 [P] [US2] validate_page_count関数を実装: src/book_converter/page_grouper.py
- [X] T034 [US2] group_pages_by_tocを修正（全ページ保持）: src/book_converter/page_grouper.py
- [X] T035 [US2] group_pages_by_tocでvalidate_page_countを呼び出し: src/book_converter/page_grouper.py
- [X] T036 `make test` PASS (GREEN) を確認

### Verification

- [X] T037 `make test` で全テスト成功を確認（US1含む回帰なし）
- [X] T038 フェーズ出力を生成: specs/006-fix-toc-line-merge/tasks/ph3-output.md

**チェックポイント**: US1とUS2が両方とも独立して動作

---

## Phase 4: User Story 3 - 既存動作の保持 (優先度: P1)

**目標**: 既存の正常ファイル（4fd5500620491ebe）の変換結果が変更されないことを確認

**独立テスト**: 正常ファイルを再変換し、TOC構造とページ数が同一であることを確認

### Input

- [x] T039 セットアップ分析を読む: specs/006-fix-toc-line-merge/tasks/ph1-output.md
- [x] T040 前フェーズ出力を読む: specs/006-fix-toc-line-merge/tasks/ph3-output.md

### Test Implementation (RED)

- [x] T041 [P] [US3] 回帰テストを実装: tests/book_converter/test_integration.py（1行形式TOC保持）
- [x] T042 [P] [US3] E2Eテストを実装: tests/book_converter/test_e2e_toc.py（正常ファイル変換結果不変）
- [x] T043 `make test` PASS (回帰テストのため既存動作をテスト - 全PASS)
- [x] T044 RED出力を生成: specs/006-fix-toc-line-merge/red-tests/ph4-test.md

### Implementation (GREEN)

- [x] T045 REDテストを読む: specs/006-fix-toc-line-merge/red-tests/ph4-test.md
- [x] T046 [US3] 既存コードに変更が必要な場合のみ修正: src/book_converter/parser.py
- [x] T047 `make test` PASS (GREEN) を確認

### Verification

- [x] T048 `make test` で全テスト成功を確認（US1, US2含む回帰なし）
- [x] T049 手動検証: output/4fd5500620491ebe/book.mdを変換し結果を比較
- [x] T050 フェーズ出力を生成: specs/006-fix-toc-line-merge/tasks/ph4-output.md

**チェックポイント**: すべてのユーザーストーリーが完了し、回帰なし

---

## Phase 5: Polish & Cross-Cutting Concerns — NO TDD

**目的**: 複数のユーザーストーリーに影響する改善

### Input

- [ ] T051 セットアップ分析を読む: specs/006-fix-toc-line-merge/tasks/ph1-output.md
- [ ] T052 前フェーズ出力を読む: specs/006-fix-toc-line-merge/tasks/ph4-output.md

### Implementation

- [ ] T053 [P] 問題ファイル（157012a97dcbebed）での最終検証
- [ ] T054 [P] 正常ファイル（4fd5500620491ebe）での最終検証
- [ ] T055 quickstart.mdの検証手順を実行
- [ ] T056 コードクリーンアップ（不要なコメント削除等）

### Verification

- [ ] T057 `make test` で全テスト成功を確認
- [ ] T058 `make coverage` でカバレッジ≥80%を確認
- [ ] T059 フェーズ出力を生成: specs/006-fix-toc-line-merge/tasks/ph5-output.md

---

## 依存関係 & 実行順序

### フェーズ依存関係

- **Setup (Phase 1)**: 依存なし - メインエージェント直接実行
- **User Stories (Phase 2-4)**: TDDフロー (tdd-generator → phase-executor)
  - ユーザーストーリーは優先順位順に進行 (P1 → P1 → P1)
- **Polish (Phase 5)**: すべてのユーザーストーリー完了後 - phase-executorのみ

### 各ユーザーストーリーフェーズ内（TDDフロー）

1. **Input**: セットアップ分析(ph1) + 前フェーズ出力を読む
2. **Test Implementation (RED)**: テストを先に書く → `make test` FAIL確認 → RED出力生成
3. **Implementation (GREEN)**: REDテストを読む → 実装 → `make test` PASS確認
4. **Verification**: 回帰なし確認 → フェーズ出力生成

### エージェント委任

- **Phase 1 (Setup)**: メインエージェント直接実行
- **Phase 2-4 (User Stories)**: tdd-generator (RED) → phase-executor (GREEN + Verification)
- **Phase 5 (Polish)**: phase-executorのみ

### [P] マーカー（依存なし）

`[P]` は「他タスクへの依存なし、実行順序自由」を示す。並列実行を保証するものではない。

---

## フェーズ出力 & REDテスト成果物

### ディレクトリ構造

```
specs/006-fix-toc-line-merge/
├── tasks.md                    # このファイル
├── tasks/
│   ├── ph1-output.md           # Phase 1 出力 (Setup結果)
│   ├── ph2-output.md           # Phase 2 出力 (US1 GREEN結果)
│   ├── ph3-output.md           # Phase 3 出力 (US2 GREEN結果)
│   ├── ph4-output.md           # Phase 4 出力 (US3 GREEN結果)
│   └── ph5-output.md           # Phase 5 出力 (Polish結果)
└── red-tests/
    ├── ph2-test.md             # Phase 2 REDテスト結果
    ├── ph3-test.md             # Phase 3 REDテスト結果
    └── ph4-test.md             # Phase 4 REDテスト結果
```

---

## 実装戦略

### MVP First (Phase 1 + Phase 2)

1. Phase 1完了: Setup（既存コードレビュー）
2. Phase 2完了: User Story 1 (RED → GREEN → Verification)
3. **停止して検証**: `make test` で全テスト成功を確認
4. 手動テストで検証（必要に応じて）

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5
2. 各フェーズでコミット: `feat(phase-N): 説明`

---

## テストカバレッジルール

**境界テスト原則**: データ変換が発生する**すべての境界**でテストを書く

```
[Input] → [Parse] → [Transform] → [Output Generation] → [File Write]
   ↓         ↓          ↓              ↓                   ↓
 Test      Test       Test           Test                Test
```

**チェックリスト**:
- [ ] 入力パースのテスト
- [ ] 変換ロジックのテスト
- [ ] **出力生成のテスト**（見落としがち）
- [ ] E2Eテスト（入力 → 最終出力）

---

## 備考

- [P] タスク = 依存なし、実行順序自由
- [Story] ラベルはタスクを特定のユーザーストーリーにマップ
- 各ユーザーストーリーは独立して完了・テスト可能
- TDD: Test Implementation (RED) → FAIL確認 → Implementation (GREEN) → PASS確認
- RED出力は実装開始前に生成必須
- 各フェーズ完了後にコミット
- 任意のチェックポイントで停止してストーリーを独立検証可能
- 避けるべき: 曖昧なタスク、同一ファイル競合、独立性を壊すストーリー間依存
