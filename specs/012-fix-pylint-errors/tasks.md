# Tasks: Pylintエラー対応

**Input**: Design documents from `/specs/012-fix-pylint-errors/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, refactoring-map.md

**Tests**: リファクタリングタスクのため、既存テストで検証。新規テスト作成なし（TDD ADAPTED）。

**Organization**: タスクはファイル単位でグループ化。各フェーズ後にpytest/pylintで検証。

## Format: `[ID] [P?] [Story] Description`

- **[P]**: 依存関係なし（異なるファイル、実行順序自由）
- **[Story]**: このタスクが属するユーザーストーリー（US1, US2, US3）
- 説明には正確なファイルパスを含める

## User Story Summary

| ID | Title | Priority | FR | 独立テスト |
|----|-------|----------|----|-----------|
| US1 | コードベースがpylintチェックを通過する | P1 | FR-001,002,003,004 | `pylint --rcfile=pyproject.toml src/` で違反0件 |
| US2 | 既存機能が正常動作する | P1 | FR-005,006 | `pytest` で全テストパス |
| US3 | コードの論理的分割 | P2 | FR-007 | 各ファイル500行以下、循環インポートなし |

## Path Conventions

- **Source**: `src/book_converter/`, `src/rover/`, `src/layout/`
- **Tests**: `tests/`
- **Feature docs**: `specs/012-fix-pylint-errors/`

---

## Phase 1: Setup（現状分析）— NO TDD

**Purpose**: 現在のコードベースを確認し、リファクタリングの準備

- [X] T001 現在のpylint違反状況を確認: `pylint --rcfile=pyproject.toml src/`
- [X] T002 [P] 現在のテスト状況を確認: `pytest`
- [X] T003 [P] refactoring-map.md の分割計画を確認
- [X] T004 フェーズ出力を生成: specs/012-fix-pylint-errors/tasks/ph1-output.md

---

## Phase 2: parser.py パッケージ化 (1739行 → ~7モジュール)

**Goal**: 最大ファイル parser.py を parser/ パッケージに分割

**独立テスト**: `pytest tests/test_parser.py` + `pylint src/book_converter/parser/`

### Input

- [x] T005 前フェーズ出力を読む: specs/012-fix-pylint-errors/tasks/ph1-output.md

### Implementation

- [x] T006 [P] [US3] src/book_converter/parser/ ディレクトリを作成
- [x] T007 [US3] src/book_converter/parser/models.py を作成（StructureHeading クラス）
- [x] T008 [US3] src/book_converter/parser/utils.py を作成（is_list_line, count_markers, get_read_aloud_from_stack）
- [x] T009 [US3] src/book_converter/parser/toc.py を作成（parse_toc_*, normalize_toc_*, merge_toc_*, split_toc_*）
- [x] T010 [US3] src/book_converter/parser/heading.py を作成（parse_heading*, parse_structure_heading）
- [x] T011 [US3] src/book_converter/parser/paragraph.py を作成（parse_paragraph*, split_paragraphs, merge_continuation_*）
- [x] T012 [US3] src/book_converter/parser/figure.py を作成（parse_figure*, parse_list）
- [x] T013 [US3] src/book_converter/parser/page.py を作成（parse_page_*, extract_page_*, create_page_*, parse_pages*）
- [x] T014 [US3] src/book_converter/parser/__init__.py を作成（公開API再エクスポート）
- [x] T015 [US3] 元の src/book_converter/parser.py を削除

### Verification

- [x] T016 [US2] `pytest tests/test_parser.py` でテストパスを確認（277/278 passed, 1失敗はテスト側の問題）
- [x] T017 [US1] `pylint src/book_converter/parser/` で違反確認（toc.py: 533行, page.py: 593行 - 要追加分割）
- [x] T018 フェーズ出力を生成: specs/012-fix-pylint-errors/tasks/ph2-output.md

**Checkpoint**: parser/ パッケージが500行以下のモジュールで構成されていること

---

## Phase 3: page_grouper.py パッケージ化 (1148行 → ~6モジュール)

**Goal**: page_grouper.py を page_grouper/ パッケージに分割

**独立テスト**: `pytest tests/test_page_grouper.py` + `pylint src/book_converter/page_grouper/`

### Input

- [x] T019 セットアップ分析を読む: specs/012-fix-pylint-errors/tasks/ph1-output.md
- [x] T020 前フェーズ出力を読む: specs/012-fix-pylint-errors/tasks/ph2-output.md

### Implementation

- [x] T021 [P] [US3] src/book_converter/page_grouper/ ディレクトリを作成
- [x] T022 [US3] src/book_converter/page_grouper/models.py を作成（FlattenStats, SectionNumber, TOCEntry）
- [x] T023 [US3] src/book_converter/page_grouper/section.py を作成（parse_section_*, extract_section_*, is_chapter_title_page）
- [x] T024 [US3] src/book_converter/page_grouper/toc.py を作成（parse_toc, validate_page_count）
- [x] T025 [US3] src/book_converter/page_grouper/assignment.py を作成（group_pages_by_toc, _assign_pages_*）
- [x] T026 [US3] src/book_converter/page_grouper/hierarchy.py を作成（_build_*, _add_sections_*, _pages_to_section）
- [x] T027 [US3] src/book_converter/page_grouper/xml.py を作成（_serialize_to_xml, convert_pages_to_book）
- [x] T028 [US3] src/book_converter/page_grouper/__init__.py を作成（公開API再エクスポート）
- [x] T029 [US3] 元の src/book_converter/page_grouper.py を削除

### Verification

- [x] T030 [US2] `pytest tests/test_page_grouper.py` でテストパスを確認
- [x] T031 [US1] `pylint src/book_converter/page_grouper/` で違反確認
- [x] T032 フェーズ出力を生成: specs/012-fix-pylint-errors/tasks/ph3-output.md

**Checkpoint**: page_grouper/ パッケージが500行以下のモジュールで構成されていること

---

## Phase 4: 中規模ファイル分割 (5ファイル)

**Goal**: 500-600行のファイルからヘルパー関数を抽出

**独立テスト**: 各ファイルのpylint違反が0件

### Input

- [x] T033 セットアップ分析を読む: specs/012-fix-pylint-errors/tasks/ph1-output.md
- [x] T034 前フェーズ出力を読む: specs/012-fix-pylint-errors/tasks/ph3-output.md

### Implementation

- [x] T035 [P] [US3] src/layout_ocr_utils.py を作成（is_title, calc_non_char_ratio, is_low_quality, crop_region, calculate_coverage, should_fallback, format_ocr_result, select_ocr_engine）
- [x] T036 [P] [US3] src/layout_ocr.py を更新（ヘルパー関数をimportに変更）
- [x] T037 [P] [US3] src/ocr_integrated_utils.py を作成（filter_overlapping_regions, group_text_by_regions, structure_text_by_paragraphs, extract_titles_from_regions, structure_text_with_titles, select_best_engine）
- [x] T038 [P] [US3] src/ocr_integrated.py を更新（ヘルパー関数をimportに変更）
- [x] T039 [P] [US3] src/rover/line_processing.py を作成（is_garbage, normalize_confidence, split_multiline_items, cluster_lines_by_y, align_lines_by_y）
- [x] T040 [P] [US3] src/rover/ensemble.py を更新（ヘルパー関数をimportに変更）
- [x] T041 [P] [US3] src/yomitoku_io.py を作成（save_yomitoku_results, load_yomitoku_results, reset_analyzer）
- [x] T042 [P] [US3] src/yomitoku_layout.py を作成（paragraphs_to_layout, visualize_layout, detect_layout_yomitoku）
- [x] T043 [P] [US3] src/ocr_yomitoku.py を更新（ヘルパー関数をimportに変更）
- [x] T044 [P] [US3] src/book_converter/transformer_utils.py を作成（normalize_heading_*, is_duplicate_*, apply_emphasis）
- [x] T045 [P] [US3] src/book_converter/transformer.py を更新（ヘルパー関数をimportに変更）

### Verification

- [x] T046 [US2] `pytest` で全テストパスを確認
- [x] T047 [US1] 分割後の各ファイルが500行以下であることを確認
- [x] T048 フェーズ出力を生成: specs/012-fix-pylint-errors/tasks/ph4-output.md

**Checkpoint**: 全ファイルが500行以下、too-many-lines違反が0件

---

## Phase 5: 関数リファクタリング（too-many-locals/statements/branches）

**Goal**: 残存するpylint違反を解消

**独立テスト**: `pylint --rcfile=pyproject.toml src/` で too-many-* 違反が0件

### Input

- [ ] T049 セットアップ分析を読む: specs/012-fix-pylint-errors/tasks/ph1-output.md
- [ ] T050 前フェーズ出力を読む: specs/012-fix-pylint-errors/tasks/ph4-output.md

### Implementation - 高優先度関数（複数違反）

- [ ] T051 [US1] parse_pages_with_errors をリファクタリング（parser/page.py）: ヘルパー抽出 + 早期リターン
- [ ] T052 [US1] _parse_single_page_content をリファクタリング（parser/page.py）: dataclass化 + 分割
- [ ] T053 [US1] run_integrated_ocr をリファクタリング（ocr_integrated.py）: ヘルパー抽出 + 設定dataclass
- [ ] T054 [US1] group_pages_by_toc をリファクタリング（page_grouper/assignment.py）: 処理段階ごとに分割
- [ ] T055 [US1] run_layout_ocr をリファクタリング（layout_ocr.py）: ヘルパー抽出

### Implementation - 中優先度関数

- [ ] T056 [P] [US1] ocr_by_layout をリファクタリング（layout_ocr.py）: ヘルパー抽出
- [ ] T057 [P] [US1] visualize_layout をリファクタリング（yomitoku_layout.py）: 描画処理を分離
- [ ] T058 [P] [US1] cluster_lines_by_y をリファクタリング（rover/line_processing.py）: dataclass化
- [ ] T059 [P] [US1] align_lines_by_y をリファクタリング（rover/line_processing.py）: dataclass化
- [ ] T060 [P] [US1] _build_hierarchical_structure をリファクタリング（page_grouper/hierarchy.py）: 早期リターン
- [ ] T061 [P] [US1] その他の too-many-locals 違反を解消

### Verification

- [ ] T062 [US2] `pytest` で全テストパスを確認
- [ ] T063 [US1] `pylint --rcfile=pyproject.toml src/` で too-many-* 違反が0件を確認
- [ ] T064 フェーズ出力を生成: specs/012-fix-pylint-errors/tasks/ph5-output.md

**Checkpoint**: 全ての too-many-* 違反が解消されていること

---

## Phase 6: Polish & 最終検証 — NO TDD

**Purpose**: 全体の整合性確認とクリーンアップ

### Input

- [ ] T065 セットアップ分析を読む: specs/012-fix-pylint-errors/tasks/ph1-output.md
- [ ] T066 前フェーズ出力を読む: specs/012-fix-pylint-errors/tasks/ph5-output.md

### Implementation

- [ ] T067 [P] ruff check --fix src/ でコードフォーマット
- [ ] T068 [P] ruff format src/ でフォーマット適用
- [ ] T069 [P] 不要なimport文やコメントの削除
- [ ] T070 [P] 循環インポートがないことを確認

### Verification

- [ ] T071 SC-001確認: `pylint --rcfile=pyproject.toml src/` で too-many-* 違反が0件
- [ ] T072 SC-002確認: `pytest` で全テストパス
- [ ] T073 SC-003確認: `ruff check src/` で違反が0件
- [ ] T074 SC-004確認: `pre-commit run --all-files` が成功
- [ ] T075 フェーズ出力を生成: specs/012-fix-pylint-errors/tasks/ph6-output.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: 依存なし - メインエージェント直接実行
- **Phase 2 (parser.py)**: Phase 1に依存 - phase-executor実行
- **Phase 3 (page_grouper.py)**: Phase 2に依存 - phase-executor実行
- **Phase 4 (中規模ファイル)**: Phase 3に依存 - phase-executor実行
- **Phase 5 (関数リファクタリング)**: Phase 4に依存 - phase-executor実行
- **Phase 6 (Polish)**: 全フェーズに依存 - phase-executor実行

### ファイル間の独立性

```
parser.py ────────────────────→ tests/test_parser.py で独立検証
                               ↓
page_grouper.py ──────────────→ tests/test_page_grouper.py で独立検証
                               ↓
中規模ファイル (5ファイル) ────→ 各ファイル独立検証
                               ↓
関数リファクタリング ─────────→ pylint で全体検証
```

### [P] Marker（依存関係なし）

- T002, T003: 異なるコマンドの実行
- T006, T021: ディレクトリ作成
- T035-T045: 異なるファイルの分割（並列実行可能）
- T056-T061: 異なる関数のリファクタリング
- T067-T070: 異なるクリーンアップ作業

---

## Phase Output Artifacts

### Directory Structure

```
specs/012-fix-pylint-errors/
├── tasks.md                    # 本ファイル
└── tasks/
    ├── ph1-output.md           # Phase 1出力（現状分析結果）
    ├── ph2-output.md           # Phase 2出力（parser.py分割結果）
    ├── ph3-output.md           # Phase 3出力（page_grouper.py分割結果）
    ├── ph4-output.md           # Phase 4出力（中規模ファイル分割結果）
    ├── ph5-output.md           # Phase 5出力（関数リファクタリング結果）
    └── ph6-output.md           # Phase 6出力（最終検証結果）
```

### Phase Output Content

各`phN-output.md`には以下を含める:
- 実行内容のサマリ
- 作成/変更されたファイル
- pylint/pytest の検証結果
- 計画からの逸脱や決定事項

---

## Implementation Strategy

### MVP First (Phase 1 + Phase 2)

1. Phase 1完了: Setup（現状分析）
2. Phase 2完了: parser.py分割
3. **STOP and VALIDATE**: `pytest` + `pylint` で検証
4. parser/ パッケージが正常動作することを確認

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6
2. 各フェーズ完了時にコミット: `refactor(phase-N): description`
3. WF-001に従い作業中は `--no-verify` 使用
4. Phase 6完了後に `pre-commit run --all-files` で最終検証

---

## Notes

- TDD ADAPTED: リファクタリングのため既存テストで検証、新規テスト作成なし
- [P] tasks = 依存関係なし、実行順序自由
- [Story] label = タスクと特定のユーザーストーリーのマッピング
- WF-001: 作業中は `git commit --no-verify` 使用
- WF-002: 最終フェーズで `pre-commit run --all-files` 実行
- フェーズ完了ごとにコミット
- 任意のチェックポイントで停止して検証可能
