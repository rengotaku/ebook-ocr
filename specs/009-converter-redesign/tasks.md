# Tasks: Converter再設計

**Input**: 設計ドキュメント `/specs/009-converter-redesign/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: TDD必須。各User Storyフェーズは Test Implementation (RED) → Implementation (GREEN) → Verification のワークフローに従う。

## Format: `[ID] [P?] [Story] 説明`

- **[P]**: 依存関係なし（異なるファイル、実行順序自由）
- **[Story]**: このタスクが属するユーザーストーリー（例: US1, US2, US3）
- 説明には正確なファイルパスを含める

## User Story サマリ

| ID | タイトル | 優先度 | FR | シナリオ |
|----|----------|--------|-----|----------|
| US1 | TOC階層構造の正確な反映 | P1 | FR-001,002,003,007 | MDの見出し階層がTOCに反映される |
| US2 | chapter/heading タグの役割明確化 | P1 | FR-004,008,009 | 構造コンテナとheadingの分離 |
| US3 | paragraphの論理的分離 | P2 | FR-005,006 | 空行で段落分離、改行除去 |
| US4 | list/figure要素の出力 | P2 | FR-010,011,012 | リストと図の適切な出力 |

**注意**: US4（MD生成時の段落保持）はOCR工程の責任であり、converter再設計スコープ外。

## パス規約

- **ソース**: `src/book_converter/`
- **テスト**: `tests/book_converter/`

---

## Phase 1: Setup（既存コード調査） — TDDなし

**目的**: 既存実装の把握と変更箇所の特定

- [X] T001 既存モデル確認: src/book_converter/models.py の TocEntry, Page, Heading, Paragraph, Figure, List を確認
- [X] T002 [P] 既存パーサー確認: src/book_converter/parser.py の parse_toc_entry, parse_paragraph, parse_heading を確認
- [X] T003 [P] 既存トランスフォーマー確認: src/book_converter/transformer.py の transform_page, transform_content を確認
- [X] T004 [P] 既存XMLビルダー確認: src/book_converter/xml_builder.py の build_xml を確認
- [X] T005 [P] 既存テスト確認: tests/book_converter/ の既存テストカバレッジを確認
- [X] T006 フェーズ出力生成: specs/009-converter-redesign/tasks/ph1-output.md

---

## Phase 2: User Story 1 - TOC階層構造の正確な反映 (Priority: P1) MVP

**Goal**: MDの見出しレベル（#, ##, ###等）をTOCのlevel属性（1-5）に正確にマッピング

**Independent Test**: TOCを含むMDを変換し、出力XMLのTOC要素が入力MDの見出し階層と一致することを確認

### Input

- [ ] T007 前フェーズ出力確認: specs/009-converter-redesign/tasks/ph1-output.md

### Test Implementation (RED)

- [x] T008 [P] [US1] TocEntry.level int化テスト実装: tests/book_converter/test_models.py に test_toc_entry_level_int を追加
- [x] T009 [P] [US1] parse_toc_entry level数値化テスト実装: tests/book_converter/test_parser.py に test_parse_toc_entry_level_numeric を追加
- [x] T010 [P] [US1] TOC階層3レベル以上テスト実装: tests/book_converter/test_parser.py に test_toc_hierarchy_multi_level を追加
- [x] T011 [P] [US1] TOC XML出力テスト実装: tests/book_converter/test_transformer.py に test_transform_toc_entry_level_numeric を追加
- [x] T012 `make test` FAIL (RED) 確認
- [x] T013 RED出力生成: specs/009-converter-redesign/red-tests/ph2-test.md

### Implementation (GREEN)

- [x] T014 REDテスト確認: specs/009-converter-redesign/red-tests/ph2-test.md
- [x] T015 [P] [US1] TocEntry.level を int に変更: src/book_converter/models.py
- [x] T016 [P] [US1] parse_toc_entry で level を int (1-5) で返すよう修正: src/book_converter/parser.py
- [x] T017 [P] [US1] transform_toc_entry で level を数値文字列として出力: src/book_converter/transformer.py
- [x] T018 [US1] 既存コードの level 文字列参照箇所を修正（依存: T015,T016,T017）
- [x] T019 `make test` PASS (GREEN) 確認

### Verification

- [x] T020 `make test` で全テストパス確認（リグレッションなし）
- [x] T021 フェーズ出力生成: specs/009-converter-redesign/tasks/ph2-output.md

**Checkpoint**: User Story 1 が独立して機能しテスト可能であること

---

## Phase 3: User Story 2 - chapter/heading タグの役割明確化 (Priority: P1)

**Goal**: 構造コンテナ（chapter, section等）とコンテンツ要素（heading）を明確に分離

**Independent Test**: 変換後XMLで、構造コンテナはtitle属性を持ち、heading要素は読み上げ専用として存在することを確認

### Input

- [ ] T022 セットアップ分析確認: specs/009-converter-redesign/tasks/ph1-output.md
- [ ] T023 前フェーズ出力確認: specs/009-converter-redesign/tasks/ph2-output.md

### Test Implementation (RED)

- [x] T024 [P] [US2] StructureContainer モデルテスト実装: tests/book_converter/test_models.py に test_structure_container を追加
- [x] T025 [P] [US2] 構造コンテナ変換テスト実装: tests/book_converter/test_transformer.py に test_transform_structure_container を追加
- [x] T026 [P] [US2] ページコメント生成テスト実装: tests/book_converter/test_xml_builder.py に test_page_comment を追加
- [x] T027 [P] [US2] heading readAloud属性テスト実装: tests/book_converter/test_transformer.py に test_heading_read_aloud を追加
- [x] T028 `make test` FAIL (RED) 確認
- [x] T029 RED出力生成: specs/009-converter-redesign/red-tests/ph3-test.md

### Implementation (GREEN)

- [ ] T030 REDテスト確認: specs/009-converter-redesign/red-tests/ph3-test.md
- [ ] T031 [P] [US2] StructureContainer dataclass 追加: src/book_converter/models.py
- [ ] T032 [P] [US2] Book.pages を Book.chapters (StructureContainer) に変更: src/book_converter/models.py
- [ ] T033 [P] [US2] transform_structure_container 関数追加: src/book_converter/transformer.py
- [ ] T034 [P] [US2] ページコメント生成関数追加: src/book_converter/xml_builder.py
- [ ] T035 [US2] build_xml を構造コンテナベースに改修（依存: T031-T034）: src/book_converter/xml_builder.py
- [ ] T036 [US2] parser で構造コンテナを構築するロジック追加（依存: T031）: src/book_converter/parser.py
- [ ] T037 `make test` PASS (GREEN) 確認

### Verification

- [ ] T038 `make test` で全テストパス確認（US1含むリグレッションなし）
- [ ] T039 フェーズ出力生成: specs/009-converter-redesign/tasks/ph3-output.md

**Checkpoint**: User Story 1, 2 がともに独立して機能すること

---

## Phase 4: User Story 3 - paragraph の論理的分離 (Priority: P2)

**Goal**: 空行で区切られた段落を個別の `<paragraph>` 要素として出力、paragraph内の改行除去

**Independent Test**: 空行で区切られた複数段落を持つMDを変換し、出力XMLで段落数が一致することを確認

### Input

- [ ] T040 セットアップ分析確認: specs/009-converter-redesign/tasks/ph1-output.md
- [ ] T041 前フェーズ出力確認: specs/009-converter-redesign/tasks/ph3-output.md

### Test Implementation (RED)

- [ ] T042 [P] [US3] paragraph改行除去テスト実装: tests/book_converter/test_parser.py に test_parse_paragraph_remove_newlines を追加
- [ ] T043 [P] [US3] 空行による段落分離テスト実装: tests/book_converter/test_parser.py に test_paragraph_split_by_blank_lines を追加
- [ ] T044 [P] [US3] スペースのみの行を空行として扱うテスト実装: tests/book_converter/test_parser.py に test_whitespace_only_line_as_blank を追加
- [ ] T045 [P] [US3] ページまたぎ段落結合テスト実装: tests/book_converter/test_parser.py に test_paragraph_continuation_across_pages を追加
- [ ] T046 `make test` FAIL (RED) 確認
- [ ] T047 RED出力生成: specs/009-converter-redesign/red-tests/ph4-test.md

### Implementation (GREEN)

- [ ] T048 REDテスト確認: specs/009-converter-redesign/red-tests/ph4-test.md
- [ ] T049 [P] [US3] parse_paragraph で改行を除去し連続テキスト化: src/book_converter/parser.py
- [ ] T050 [P] [US3] 空行検出ロジック追加（スペース/タブのみも空行扱い）: src/book_converter/parser.py
- [ ] T051 [US3] ページまたぎ段落結合ロジック追加（句点で終わらない段落）: src/book_converter/parser.py
- [ ] T052 `make test` PASS (GREEN) 確認

### Verification

- [ ] T053 `make test` で全テストパス確認（US1,2含むリグレッションなし）
- [ ] T054 フェーズ出力生成: specs/009-converter-redesign/tasks/ph4-output.md

**Checkpoint**: User Story 1, 2, 3 がともに独立して機能すること

---

## Phase 5: User Story 4 - list/figure要素の出力 (Priority: P2)

**Goal**: MDのリスト記法と図プレースホルダーを適切なXML要素として出力

**Independent Test**: リストと図を含むMDを変換し、`<list>` と `<figure>` 要素が正しく生成されることを確認

### Input

- [ ] T055 セットアップ分析確認: specs/009-converter-redesign/tasks/ph1-output.md
- [ ] T056 前フェーズ出力確認: specs/009-converter-redesign/tasks/ph4-output.md

### Test Implementation (RED)

- [ ] T057 [P] [US4] List.list_type 属性テスト実装: tests/book_converter/test_models.py に test_list_type_attribute を追加
- [ ] T058 [P] [US4] リスト変換テスト（unordered/ordered）実装: tests/book_converter/test_transformer.py に test_transform_list_type を追加
- [ ] T059 [P] [US4] Figure.path, marker 属性テスト実装: tests/book_converter/test_models.py に test_figure_path_marker を追加
- [ ] T060 [P] [US4] 図プレースホルダー検出テスト実装: tests/book_converter/test_parser.py に test_parse_figure_placeholder を追加
- [ ] T061 [P] [US4] figure XML出力テスト実装: tests/book_converter/test_transformer.py に test_transform_figure_new_format を追加
- [ ] T062 `make test` FAIL (RED) 確認
- [ ] T063 RED出力生成: specs/009-converter-redesign/red-tests/ph5-test.md

### Implementation (GREEN)

- [ ] T064 REDテスト確認: specs/009-converter-redesign/red-tests/ph5-test.md
- [ ] T065 [P] [US4] List に list_type 属性追加: src/book_converter/models.py
- [ ] T066 [P] [US4] Figure を path, marker 属性に変更: src/book_converter/models.py
- [ ] T067 [P] [US4] parse_list で list_type (unordered/ordered) を判定: src/book_converter/parser.py
- [ ] T068 [P] [US4] 図プレースホルダー検出パターン追加（[図], [写真], [表]等）: src/book_converter/parser.py
- [ ] T069 [P] [US4] transform_list で type 属性出力: src/book_converter/transformer.py
- [ ] T070 [P] [US4] transform_figure を新形式に改修: src/book_converter/transformer.py
- [ ] T071 `make test` PASS (GREEN) 確認

### Verification

- [ ] T072 `make test` で全テストパス確認（US1,2,3含むリグレッションなし）
- [ ] T073 フェーズ出力生成: specs/009-converter-redesign/tasks/ph5-output.md

**Checkpoint**: 全 User Story が独立して機能すること

---

## Phase 6: CLI拡張 & Polish — TDDなし

**目的**: CLI引数追加とクロスカッティング関心事の処理

### Input

- [ ] T074 セットアップ分析確認: specs/009-converter-redesign/tasks/ph1-output.md
- [ ] T075 前フェーズ出力確認: specs/009-converter-redesign/tasks/ph5-output.md

### Implementation

- [ ] T076 [P] --figure-markers CLI引数追加: src/book_converter/cli.py
- [ ] T077 [P] 廃止コード削除（transform_page, Page関連の未使用コード）
- [ ] T078 [P] 既存テストの廃止コード参照を削除: tests/book_converter/
- [ ] T079 コードクリーンアップとリファクタリング

### Verification

- [ ] T080 `make test` で全テストパス確認
- [ ] T081 `make coverage` でカバレッジ≥80%確認
- [ ] T082 quickstart.md の検証（手動テスト）
- [ ] T083 フェーズ出力生成: specs/009-converter-redesign/tasks/ph6-output.md

---

## 依存関係と実行順序

### フェーズ依存関係

- **Setup (Phase 1)**: 依存なし - メインエージェント直接実行
- **User Stories (Phase 2-5)**: TDDフロー (tdd-generator → phase-executor)
  - User Story は優先度順に逐次処理 (P1 → P2)
- **Polish (Phase 6)**: 全 User Story に依存 - phase-executor のみ

### 各 User Story フェーズ内 (TDDフロー)

1. **Input**: セットアップ分析 (ph1) + 前フェーズ出力の確認
2. **Test Implementation (RED)**: テストを先に書く → `make test` FAIL 確認 → RED出力生成
3. **Implementation (GREEN)**: REDテスト確認 → 実装 → `make test` PASS 確認
4. **Verification**: リグレッションなし確認 → フェーズ出力生成

### エージェント委譲

- **Phase 1 (Setup)**: メインエージェント直接実行
- **Phase 2-5 (User Stories)**: tdd-generator (RED) → phase-executor (GREEN + Verification)
- **Phase 6 (Polish)**: phase-executor のみ

### [P] マーカー（依存なし）

`[P]` は「他タスクへの依存なし、実行順序自由」を示す。並列実行を保証するものではない。

- Setup タスク [P]: 異なるファイル/ディレクトリ操作
- RED テスト [P]: 異なるテストファイルへの書き込み
- GREEN 実装 [P]: 異なるソースファイルへの書き込み
- User Story 間: 各フェーズは前フェーズ出力に依存するため [P] 不可

---

## フェーズ出力 & REDテストアーティファクト

### ディレクトリ構造

```
specs/009-converter-redesign/
├── tasks.md                    # このファイル
├── tasks/
│   ├── ph1-output.md           # Phase 1 出力（Setup結果）
│   ├── ph2-output.md           # Phase 2 出力（US1 GREEN結果）
│   ├── ph3-output.md           # Phase 3 出力（US2 GREEN結果）
│   ├── ph4-output.md           # Phase 4 出力（US3 GREEN結果）
│   ├── ph5-output.md           # Phase 5 出力（US4 GREEN結果）
│   └── ph6-output.md           # Phase 6 出力（Polish結果）
└── red-tests/
    ├── ph2-test.md             # Phase 2 REDテスト結果（FAIL確認）
    ├── ph3-test.md             # Phase 3 REDテスト結果
    ├── ph4-test.md             # Phase 4 REDテスト結果
    └── ph5-test.md             # Phase 5 REDテスト結果
```

### フェーズ出力内容

各 `phN-output.md` に含める内容:
- 実施した作業のサマリ
- 作成/変更したファイル
- テスト結果（`make test` 出力）
- 計画からの逸脱や決定事項

### REDテスト出力内容

各 `phN-test.md` に含める内容:
- 書いたテストコード
- `make test` 出力（FAIL確認、RED状態）
- 失敗テスト数とテスト名

---

## 実装戦略

### MVP First (Phase 1 + Phase 2)

1. Phase 1 完了: Setup（既存コード調査）
2. Phase 2 完了: User Story 1 (RED → GREEN → Verification)
3. **検証ポイント**: `make test` で全テストパス確認
4. 必要に応じて手動テストで検証

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6
2. 各フェーズでコミット: `feat(phase-N): description`

---

## テストカバレッジルール

**境界テスト原則**: データ変換が発生する**すべての境界**でテストを書く

```
[Input] → [Parse] → [Transform] → [Output Generation] → [File Write]
   ↓         ↓          ↓              ↓                   ↓
 Test      Test       Test           Test                Test
```

**チェックリスト**:
- [ ] 入力パーステスト
- [ ] 変換ロジックテスト
- [ ] **出力生成テスト**（見落としがち）
- [ ] End-to-Endテスト（入力 → 最終出力）

---

## Notes

- [P] タスク = 依存なし、実行順序自由
- [Story] ラベル = タスクの追跡性のために特定のユーザーストーリーにマップ
- 各ユーザーストーリーは独立して完了・テスト可能であること
- TDD: Test Implementation (RED) → FAIL確認 → Implementation (GREEN) → PASS確認
- RED出力は実装開始前に必ず生成
- 各フェーズ完了後にコミット
- どのチェックポイントでも停止してストーリーを独立検証可能
- 避けるべき: 曖昧なタスク、同一ファイルの競合、ストーリー間の依存による独立性の喪失
