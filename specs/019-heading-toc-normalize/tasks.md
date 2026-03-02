# Tasks: book.md の見出し形式統一と TOC マッチング改善

**入力**: `/specs/019-heading-toc-normalize/` の設計ドキュメント
**前提**: plan.md, spec.md, data-model.md, research.md, quickstart.md

**テスト**: ユーザーストーリーフェーズでは TDD 必須。各フェーズは Test Implementation (RED) → Implementation (GREEN) → Verification のワークフローに従う。

**構成**: タスクはユーザーストーリー単位でグループ化し、各ストーリーを独立して実装・テスト可能にする。

## フォーマット: `[ID] [P?] [Story] 説明`

- **[P]**: 依存関係なし（別ファイル、実行順序自由）
- **[Story]**: タスクが属するユーザーストーリー（US1, US2, US3, US4）
- 説明には正確なファイルパスを含める

## ユーザーストーリー一覧

| ID | タイトル | 優先度 | FR | シナリオ |
|----|----------|--------|-----|----------|
| US1 | 見出しパターンの自動抽出 | P1 | FR-001,002,003 | heading-report コマンド |
| US2 | TOC形式への見出し正規化 | P1 | FR-004,005,006 | normalize-headings コマンド |
| US3 | 正規化スクリプトの生成 | P2 | FR-007 | sed スクリプト出力 |
| US4 | 正規化結果の検証 | P2 | FR-008,009,010,011 | validate-toc コマンド |

## パス規約

- **ソースコード**: `src/book_converter/`, `src/cli/`
- **テスト**: `tests/book_converter/`, `tests/cli/`
- **仕様出力**: `specs/019-heading-toc-normalize/tasks/`, `specs/019-heading-toc-normalize/red-tests/`

---

## Phase 1: Setup（共通インフラ）— NO TDD

**目的**: 既存コードの確認、ディレクトリ構造の準備

- [x] T001 既存の TOC パース実装を確認: src/book_converter/parser/toc.py
- [x] T002 [P] 既存の見出しパース実装を確認: src/book_converter/parser/heading.py
- [x] T003 [P] 既存のモデル定義を確認: src/book_converter/models.py
- [x] T004 [P] 新規テストディレクトリを作成: tests/book_converter/parser/ (存在確認)
- [x] T005 セットアップ結果を出力: specs/019-heading-toc-normalize/tasks/ph1-output.md

---

## Phase 2: US1 - 見出しパターンの自動抽出 (Priority: P1) MVP

**目標**: book.md から見出しパターンを抽出し、頻度レポートを生成する

**独立テスト**: `make heading-report` で見出しパターンの分類・頻度が表示される

### Input

- [x] T006 前フェーズ出力を読む: specs/019-heading-toc-normalize/tasks/ph1-output.md

### Test Implementation (RED)

- [x] T007 [P] [US1] 番号フォーマット正規化テストを実装: tests/book_converter/parser/test_heading_normalizer.py
  - test_normalize_hyphen_to_dot: `1-1-1` → `1.1.1`
  - test_normalize_fullwidth_to_halfwidth: `１．１` → `1.1`
  - test_normalize_nakaguro_to_dot: `1・1` → `1.1`
- [x] T008 [P] [US1] スペース正規化テストを実装: tests/book_converter/parser/test_heading_normalizer.py
  - test_normalize_chapter_spaces: `第 1 章` → `第1章`
  - test_normalize_number_spaces: `1. 1` → `1.1`
- [x] T009 [P] [US1] 特殊マーカー検出テストを実装: tests/book_converter/parser/test_heading_normalizer.py
  - test_is_special_marker_square: `■コードベース` → True
  - test_is_special_marker_diamond: `◆注意事項` → True
  - test_is_special_marker_normal: `SREの概要` → False
- [x] T010 [P] [US1] 見出し抽出テストを実装: tests/book_converter/parser/test_heading_normalizer.py
  - test_extract_headings: `## ` で始まる行を抽出
  - test_classify_heading_patterns: 番号あり/なし/マーカーなしの3分類
- [x] T011 `make test` で FAIL を確認 (RED)
- [x] T012 RED テスト結果を出力: specs/019-heading-toc-normalize/red-tests/ph2-test.md

### Implementation (GREEN)

- [x] T013 RED テストを読む: specs/019-heading-toc-normalize/red-tests/ph2-test.md
- [x] T014 [P] [US1] MatchType, NormalizationAction 列挙型を追加: src/book_converter/models.py
- [x] T015 [P] [US1] normalize_number_format() を実装: src/book_converter/parser/heading_normalizer.py
- [x] T016 [P] [US1] normalize_spaces() を実装: src/book_converter/parser/heading_normalizer.py
- [x] T017 [P] [US1] is_special_marker() を実装: src/book_converter/parser/heading_normalizer.py
- [x] T018 [P] [US1] extract_headings() を実装: src/book_converter/parser/heading_normalizer.py
- [x] T019 [P] [US1] classify_heading_patterns() を実装: src/book_converter/parser/heading_normalizer.py
- [x] T020 `make test` で PASS を確認 (GREEN)

### Verification

- [x] T021 `make test` で全テスト PASS を確認（リグレッションなし）
- [x] T022 `make coverage` でカバレッジ ≥80% を確認
- [x] T023 フェーズ結果を出力: specs/019-heading-toc-normalize/tasks/ph2-output.md

**チェックポイント**: heading_normalizer.py の純粋関数群が独立してテスト可能

---

## Phase 3: US2 - TOC形式への見出し正規化 (Priority: P1)

**目標**: TOC エントリと本文見出しをマッチングし、番号を付与する

**独立テスト**: `make normalize-headings` で正規化プレビュー（dry-run）が表示される

### Input

- [x] T024 セットアップ分析を読む: specs/019-heading-toc-normalize/tasks/ph1-output.md
- [x] T025 前フェーズ出力を読む: specs/019-heading-toc-normalize/tasks/ph2-output.md

### Test Implementation (RED)

- [x] T026 [P] [US2] MatchResult モデルテストを実装: tests/book_converter/test_heading_matcher.py
  - test_match_result_exact: similarity == 1.0
  - test_match_result_fuzzy: 0.8 <= similarity < 1.0
  - test_match_result_missing: body_heading is None
- [x] T027 [P] [US2] 完全一致マッチングテストを実装: tests/book_converter/test_heading_matcher.py
  - test_match_exact_title
  - test_match_exact_with_number
- [x] T028 [P] [US2] 番号除去マッチングテストを実装: tests/book_converter/test_heading_matcher.py
  - test_match_after_number_removal
- [x] T029 [P] [US2] ファジーマッチングテストを実装: tests/book_converter/test_heading_matcher.py
  - test_fuzzy_match_above_threshold: 類似度 80% 以上
  - test_fuzzy_match_below_threshold: 類似度 80% 未満 → MISSING
- [x] T030 [P] [US2] NormalizationRule 生成テストを実装: tests/book_converter/test_normalization_rules.py
  - test_generate_rule_add_number
  - test_generate_rule_add_marker
  - test_generate_rule_format_only
  - test_generate_rule_none
- [x] T031 `make test` で FAIL を確認 (RED)
- [x] T032 RED テスト結果を出力: specs/019-heading-toc-normalize/red-tests/ph3-test.md

### Implementation (GREEN)

- [x] T033 RED テストを読む: specs/019-heading-toc-normalize/red-tests/ph3-test.md
- [x] T034 [P] [US2] MatchResult データクラスを追加: src/book_converter/models.py
- [x] T035 [P] [US2] NormalizationRule データクラスを追加: src/book_converter/models.py
- [x] T036 [US2] match_toc_to_body() を実装: src/book_converter/heading_matcher.py
  - 完全一致 → 番号除去一致 → ファジーマッチの優先順位
  - difflib.SequenceMatcher を使用
- [x] T037 [US2] generate_rules() を実装: src/book_converter/normalization_rules.py
- [x] T038 `make test` で PASS を確認 (GREEN)

### Verification

- [x] T039 `make test` で全テスト PASS を確認（US1 含む）
- [x] T040 `make coverage` でカバレッジ ≥80% を確認
- [x] T041 フェーズ結果を出力: specs/019-heading-toc-normalize/tasks/ph3-output.md

**チェックポイント**: マッチングエンジンが独立してテスト可能

---

## Phase 4: US3 - 正規化スクリプトの生成 (Priority: P2)

**目標**: 正規化ルールを sed スクリプトとして出力する

**独立テスト**: 生成された sed スクリプトが別の book.md に適用可能

### Input

- [x] T042 セットアップ分析を読む: specs/019-heading-toc-normalize/tasks/ph1-output.md
- [x] T043 前フェーズ出力を読む: specs/019-heading-toc-normalize/tasks/ph3-output.md

### Test Implementation (RED)

- [x] T044 [P] [US3] sed スクリプト生成テストを実装: tests/book_converter/test_normalization_rules.py
  - test_generate_sed_script_single_rule
  - test_generate_sed_script_multiple_rules
  - test_generate_sed_script_escape_special_chars
- [x] T045 [P] [US3] 差分プレビューテストを実装: tests/book_converter/test_normalization_rules.py
  - test_preview_diff_changes
  - test_preview_diff_no_changes
- [x] T046 `make test` で FAIL を確認 (RED)
- [x] T047 RED テスト結果を出力: specs/019-heading-toc-normalize/red-tests/ph4-test.md

### Implementation (GREEN)

- [ ] T048 RED テストを読む: specs/019-heading-toc-normalize/red-tests/ph4-test.md
- [ ] T049 [US3] generate_sed_script() を実装: src/book_converter/normalization_rules.py
- [ ] T050 [US3] preview_diff() を実装: src/book_converter/normalization_rules.py
- [ ] T051 [US3] apply_rules() を実装: src/book_converter/normalization_rules.py
- [ ] T052 `make test` で PASS を確認 (GREEN)

### Verification

- [ ] T053 `make test` で全テスト PASS を確認（US1, US2 含む）
- [ ] T054 `make coverage` でカバレッジ ≥80% を確認
- [ ] T055 フェーズ結果を出力: specs/019-heading-toc-normalize/tasks/ph4-output.md

**チェックポイント**: sed スクリプト生成が独立してテスト可能

---

## Phase 5: US4 - 正規化結果の検証 (Priority: P2)

**目標**: TOC-本文マッチング検証レポートを出力する

**独立テスト**: `make validate-toc` で検証レポート（テーブル形式）が表示される

### Input

- [ ] T056 セットアップ分析を読む: specs/019-heading-toc-normalize/tasks/ph1-output.md
- [ ] T057 前フェーズ出力を読む: specs/019-heading-toc-normalize/tasks/ph4-output.md

### Test Implementation (RED)

- [ ] T058 [P] [US4] ValidationReport モデルテストを実装: tests/book_converter/test_heading_matcher.py
  - test_validation_report_match_rate
  - test_validation_report_missing_entries
  - test_validation_report_excluded_headings
- [ ] T059 [P] [US4] 類似候補表示テストを実装: tests/book_converter/test_heading_matcher.py
  - test_find_similar_candidate_above_threshold
  - test_find_similar_candidate_none
- [ ] T060 [P] [US4] レポート出力テストを実装: tests/book_converter/test_heading_matcher.py
  - test_format_validation_report_table
  - test_format_validation_report_summary
  - test_validation_report_exit_code
- [ ] T061 `make test` で FAIL を確認 (RED)
- [ ] T062 RED テスト結果を出力: specs/019-heading-toc-normalize/red-tests/ph5-test.md

### Implementation (GREEN)

- [ ] T063 RED テストを読む: specs/019-heading-toc-normalize/red-tests/ph5-test.md
- [ ] T064 [P] [US4] ValidationReport データクラスを追加: src/book_converter/models.py
- [ ] T065 [US4] find_similar_candidate() を実装: src/book_converter/heading_matcher.py
- [ ] T066 [US4] generate_validation_report() を実装: src/book_converter/heading_matcher.py
- [ ] T067 [US4] format_validation_report() を実装: src/book_converter/heading_matcher.py
  - テーブル形式（#, TOC Entry, Body Heading, Type, Sim%, Line#, Page）
- [ ] T068 `make test` で PASS を確認 (GREEN)

### Verification

- [ ] T069 `make test` で全テスト PASS を確認（US1-US3 含む）
- [ ] T070 `make coverage` でカバレッジ ≥80% を確認
- [ ] T071 フェーズ結果を出力: specs/019-heading-toc-normalize/tasks/ph5-output.md

**チェックポイント**: 検証レポート生成が独立してテスト可能

---

## Phase 6: CLI 統合 — TDD

**目標**: normalize_headings CLI エントリポイントを実装する

### Input

- [ ] T072 セットアップ分析を読む: specs/019-heading-toc-normalize/tasks/ph1-output.md
- [ ] T073 前フェーズ出力を読む: specs/019-heading-toc-normalize/tasks/ph5-output.md

### Test Implementation (RED)

- [ ] T074 [P] CLI report サブコマンドテストを実装: tests/cli/test_normalize_headings.py
  - test_report_command_success
  - test_report_command_file_not_found
- [ ] T075 [P] CLI normalize サブコマンドテストを実装: tests/cli/test_normalize_headings.py
  - test_normalize_command_dryrun
  - test_normalize_command_apply
- [ ] T076 [P] CLI validate サブコマンドテストを実装: tests/cli/test_normalize_headings.py
  - test_validate_command_success
  - test_validate_command_warn_exit_code
- [ ] T077 `make test` で FAIL を確認 (RED)
- [ ] T078 RED テスト結果を出力: specs/019-heading-toc-normalize/red-tests/ph6-test.md

### Implementation (GREEN)

- [ ] T079 RED テストを読む: specs/019-heading-toc-normalize/red-tests/ph6-test.md
- [ ] T080 CLI エントリポイントを実装: src/cli/normalize_headings.py
  - argparse による report/normalize/validate サブコマンド
  - --apply, --threshold オプション
- [ ] T081 `make test` で PASS を確認 (GREEN)

### Verification

- [ ] T082 `make test` で全テスト PASS を確認
- [ ] T083 `make coverage` でカバレッジ ≥80% を確認
- [ ] T084 フェーズ結果を出力: specs/019-heading-toc-normalize/tasks/ph6-output.md

---

## Phase 7: Makefile 統合 & Polish — NO TDD

**目的**: Makefile ターゲット追加、最終検証

### Input

- [ ] T085 セットアップ分析を読む: specs/019-heading-toc-normalize/tasks/ph1-output.md
- [ ] T086 前フェーズ出力を読む: specs/019-heading-toc-normalize/tasks/ph6-output.md

### Implementation

- [ ] T087 [P] Makefile に heading-report ターゲットを追加: Makefile
- [ ] T088 [P] Makefile に normalize-headings ターゲットを追加: Makefile
- [ ] T089 [P] Makefile に validate-toc ターゲットを追加: Makefile
- [ ] T090 quickstart.md の手順を検証

### Verification

- [ ] T091 `make test` で全テスト PASS を確認
- [ ] T092 `make heading-report` の動作確認（サンプル book.md で）
- [ ] T093 `make normalize-headings` の動作確認
- [ ] T094 `make validate-toc` の動作確認
- [ ] T095 フェーズ結果を出力: specs/019-heading-toc-normalize/tasks/ph7-output.md

---

## 依存関係 & 実行順序

### フェーズ依存関係

- **Setup (Phase 1)**: 依存なし - メインエージェント直接実行
- **User Stories (Phase 2-6)**: TDD フロー (speckit:tdd-generator → speckit:phase-executor)
  - 優先度順に順次進行 (P1 → P2)
- **Polish (Phase 7)**: 全ストーリー完了後 - speckit:phase-executor のみ

### 各ユーザーストーリーフェーズ内 (TDD フロー)

1. **Input**: セットアップ分析 (ph1) + 前フェーズ出力を読む
2. **Test Implementation (RED)**: テストを先に書く → `make test` FAIL 確認 → RED 出力生成
3. **Implementation (GREEN)**: RED テストを読む → 実装 → `make test` PASS 確認
4. **Verification**: リグレッションなし確認 → フェーズ出力生成

### エージェント委譲

- **Phase 1 (Setup)**: メインエージェント直接実行
- **Phase 2-6 (User Stories)**: speckit:tdd-generator (RED) → speckit:phase-executor (GREEN + Verification)
- **Phase 7 (Polish)**: speckit:phase-executor のみ

### [P] マーカー（依存関係なし）

`[P]` は「他タスクへの依存なし、実行順序自由」を示す。並列実行を保証するものではない。

---

## フェーズ出力 & RED テスト成果物

### ディレクトリ構造

```
specs/019-heading-toc-normalize/
├── tasks.md                    # このファイル
├── tasks/
│   ├── ph1-output.md           # Phase 1 出力（セットアップ結果）
│   ├── ph2-output.md           # Phase 2 出力（US1 GREEN 結果）
│   ├── ph3-output.md           # Phase 3 出力（US2 GREEN 結果）
│   ├── ph4-output.md           # Phase 4 出力（US3 GREEN 結果）
│   ├── ph5-output.md           # Phase 5 出力（US4 GREEN 結果）
│   ├── ph6-output.md           # Phase 6 出力（CLI GREEN 結果）
│   └── ph7-output.md           # Phase 7 出力（最終結果）
└── red-tests/
    ├── ph2-test.md             # Phase 2 RED テスト結果
    ├── ph3-test.md             # Phase 3 RED テスト結果
    ├── ph4-test.md             # Phase 4 RED テスト結果
    ├── ph5-test.md             # Phase 5 RED テスト結果
    └── ph6-test.md             # Phase 6 RED テスト結果
```

---

## 実装戦略

### MVP First (Phase 1 + Phase 2)

1. Phase 1 完了: Setup（既存コード確認）
2. Phase 2 完了: US1 - 見出しパターン抽出 (RED → GREEN → Verification)
3. **検証**: `make test` で全テスト PASS 確認
4. heading_normalizer.py の純粋関数群が動作確認可能

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6 → Phase 7
2. 各フェーズ完了時にコミット: `feat(phase-N): description`

---

## テストカバレッジルール

**境界テスト原則**: データ変換が発生する**すべての境界**でテストを書く

```
[Input] → [Parse] → [Normalize] → [Match] → [Rule Gen] → [Output]
   ↓         ↓          ↓           ↓          ↓           ↓
 Test      Test       Test        Test       Test        Test
```

**チェックリスト**:
- [ ] 入力パーステスト（TOC, 見出し抽出）
- [ ] 正規化ロジックテスト（番号フォーマット、スペース）
- [ ] マッチングロジックテスト（EXACT, FUZZY, MISSING）
- [ ] **出力生成テスト**（見落としがち）
- [ ] End-to-End テスト（入力 → 最終出力）

---

## Notes

- [P] タスク = 依存関係なし、実行順序自由
- [Story] ラベルはタスクを特定のユーザーストーリーにマッピング
- 各ユーザーストーリーは独立して完了・テスト可能
- TDD: Test Implementation (RED) → Verify FAIL → Implementation (GREEN) → Verify PASS
- RED 出力は実装開始前に必ず生成
- 各フェーズ完了時にコミット
- 曖昧なタスク、同一ファイル競合、ストーリー間依存（独立性を損なう）を避ける
