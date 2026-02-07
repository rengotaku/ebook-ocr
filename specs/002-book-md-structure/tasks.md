# Tasks: Book Markdown to XML Standardization

**入力**: `/specs/002-book-md-structure/` のデザインドキュメント
**前提条件**: plan.md (必須), spec.md (必須), research.md, data-model.md, contracts/book.xsd

**テスト**: ユーザーストーリーフェーズにはTDDが必須。各フェーズは Test Implementation (RED) → Implementation (GREEN) → Verification ワークフローに従う。

## フォーマット: `[ID] [P?] [Story] 説明`

- **[P]**: 依存関係なし（異なるファイル、実行順序自由）
- **[Story]**: タスクが属するユーザーストーリー（US1, US2, US3）
- 説明には正確なファイルパスを含める

## ユーザーストーリー概要

| ID | タイトル | 優先度 | FR | シナリオ |
|----|----------|--------|-----|----------|
| US1 | TTSページナビゲーションと音声アナウンス | P1 | FR-001,002,010,011 | ページ番号音声読み上げ、XPath検索 |
| US2 | TTSコンテンツ階層と構造解析 | P2 | FR-003,007,008,009 | 見出し階層抽出、章節構造 |
| US3 | TTS図表説明制御とメタデータ分離 | P3 | FR-004,005,006,012,013 | readAloud制御、メタデータ非読み上げ |

## パス規約

- **ソースコード**: `src/book_converter/`
- **テスト**: `tests/book_converter/`
- **Fixtures**: `tests/book_converter/fixtures/`

---

## Phase 1: Setup（共有インフラ）— TDDなし

**目的**: プロジェクト初期化、既存コード確認、変更準備

- [x] T001 `src/book_converter/` ディレクトリ構造を作成（__init__.py, parser.py, transformer.py, models.py, xml_builder.py, cli.py）
- [x] T002 [P] `tests/book_converter/` ディレクトリ構造を作成（__init__.py, test_parser.py, test_transformer.py, test_xml_builder.py, test_cli.py, fixtures/）
- [x] T003 [P] `tests/book_converter/fixtures/` にサンプルファイルを作成（sample_book.md, expected_book.xml）
- [x] T004 [P] `src/book_converter/models.py` にデータモデルを実装（data-model.md準拠: Book, Page, Heading, Paragraph, List, Figure, PageMetadata, Content, PageAnnouncement, ConversionError, ConversionResult）
- [x] T005 [P] `Makefile` に book_converter 用ターゲットを追加（test-book-converter, convert-sample）
- [x] T006 [P] `requirements.txt` に pytest 依存を追加（未追加の場合）
- [x] T007 フェーズ出力を生成: specs/002-book-md-structure/tasks/ph1-output.md

---

## Phase 2: User Story 1 - TTSページナビゲーションと音声アナウンス (Priority: P1) — MVP

**Goal**: TTSで書籍を聴く際、ページが切り替わるタイミングでページ番号が音声アナウンスされ、XPathクエリで該当ページを特定できる

**独立テスト**: 任意のページ番号（例：42ページ）を指定し、XMLファイル内で `//page[@number='42']` により該当箇所を10秒以内に見つけ、TTSで「42ページ」と読み上げられる

### Input

- [ ] T008 前フェーズ出力を読む: specs/002-book-md-structure/tasks/ph1-output.md

### Test Implementation (RED)

- [ ] T009 [P] [US1] ページマーカー解析テストを実装: tests/book_converter/test_parser.py（`--- Page N (file.png) ---` パターン）
- [ ] T010 [P] [US1] ページ番号抽出テストを実装: tests/book_converter/test_parser.py（正常系、欠落系、エッジケース）
- [ ] T011 [P] [US1] PageAnnouncementテストを実装: tests/book_converter/test_parser.py（「Nページ」フォーマット）
- [ ] T012 [P] [US1] ページXML変換テストを実装: tests/book_converter/test_transformer.py（`<page number="N" sourceFile="...">` 生成）
- [ ] T013 [P] [US1] PageAnnouncementXML変換テストを実装: tests/book_converter/test_transformer.py（`<pageAnnouncement>` 生成）
- [ ] T014 [P] [US1] 統合テストを実装: tests/book_converter/test_integration.py（Markdown→XML→XPathクエリ）
- [ ] T015 `make test` FAIL (RED) を確認
- [ ] T016 RED出力を生成: specs/002-book-md-structure/red-tests/ph2-test.md

### Implementation (GREEN)

- [ ] T017 REDテストを読む: specs/002-book-md-structure/red-tests/ph2-test.md
- [ ] T018 [P] [US1] `src/book_converter/parser.py` にページマーカー解析を実装（parse_page_marker関数）
- [ ] T019 [P] [US1] `src/book_converter/parser.py` にparse_pages関数を実装（Markdownをページ単位でパース）
- [ ] T020 [P] [US1] `src/book_converter/transformer.py` にtransform_page関数を実装（Page→XML Element変換）
- [ ] T021 [P] [US1] `src/book_converter/xml_builder.py` にXML出力関数を実装（serialize_element, build_xml）
- [ ] T022 [US1] コンポーネント統合（T018-T021の結合確認）
- [ ] T023 `make test` PASS (GREEN) を確認

### Verification

- [ ] T024 `make test` で全テスト通過を確認（リグレッションなし）
- [ ] T025 フェーズ出力を生成: specs/002-book-md-structure/tasks/ph2-output.md

**チェックポイント**: User Story 1は完全に機能し、独立してテスト可能

---

## Phase 3: User Story 2 - TTSコンテンツ階層と構造解析 (Priority: P2)

**Goal**: 書籍の章立て構造（章、節、小節）をXML階層から正確に抽出し、TTSで読み上げる際に適切な音声の抑揚やポーズを制御できる

**独立テスト**: XML内の任意の位置（例：ページ50）を開き、XPathクエリで親階層を辿り、「今どの章のどの節に属しているか」を3秒以内に判断できる

### Input

- [ ] T026 セットアップ分析を読む: specs/002-book-md-structure/tasks/ph1-output.md
- [ ] T027 前フェーズ出力を読む: specs/002-book-md-structure/tasks/ph2-output.md

### Test Implementation (RED)

- [ ] T028 [P] [US2] 見出し解析テストを実装: tests/book_converter/test_parser.py（`#`, `##`, `###` パターン、level 1-3）
- [ ] T029 [P] [US2] 4階層以上の見出し警告テストを実装: tests/book_converter/test_parser.py（`####` → level=3 + 警告）
- [ ] T030 [P] [US2] 段落解析テストを実装: tests/book_converter/test_parser.py（空行区切り、ContentElement生成）
- [ ] T031 [P] [US2] リスト解析テストを実装: tests/book_converter/test_parser.py（`-` / `*` 項目）
- [ ] T032 [P] [US2] Heading XML変換テストを実装: tests/book_converter/test_transformer.py（`<heading level="N">` 生成）
- [ ] T033 [P] [US2] Content XML変換テストを実装: tests/book_converter/test_transformer.py（`<content>` 内に heading/paragraph/list）
- [ ] T034 [P] [US2] 継続属性テストを実装: tests/book_converter/test_transformer.py（`continued="true"` ページ跨ぎ）
- [ ] T035 `make test` FAIL (RED) を確認
- [ ] T036 RED出力を生成: specs/002-book-md-structure/red-tests/ph3-test.md

### Implementation (GREEN)

- [ ] T037 REDテストを読む: specs/002-book-md-structure/red-tests/ph3-test.md
- [ ] T038 [P] [US2] `src/book_converter/parser.py` にparse_heading関数を実装（見出しレベル1-3抽出、4+警告）
- [ ] T039 [P] [US2] `src/book_converter/parser.py` にparse_paragraph関数を実装（段落テキスト抽出）
- [ ] T040 [P] [US2] `src/book_converter/parser.py` にparse_list関数を実装（リスト項目抽出）
- [ ] T041 [P] [US2] `src/book_converter/parser.py` にparse_content関数を実装（Heading/Paragraph/List統合）
- [ ] T042 [P] [US2] `src/book_converter/transformer.py` にtransform_content関数を実装（Content→XML）
- [ ] T043 [P] [US2] `src/book_converter/transformer.py` にcontinued属性処理を追加
- [ ] T044 [US2] コンポーネント統合（T038-T043の結合確認）
- [ ] T045 `make test` PASS (GREEN) を確認

### Verification

- [ ] T046 `make test` で全テスト通過を確認（US1リグレッションなし）
- [ ] T047 フェーズ出力を生成: specs/002-book-md-structure/tasks/ph3-output.md

**チェックポイント**: User Stories 1 AND 2は両方とも独立して動作

---

## Phase 4: User Story 3 - TTS図表説明制御とメタデータ分離 (Priority: P3)

**Goal**: 図表の説明を読み上げるか省略するかを選択でき、ページ番号やファイル名などのメタデータが本文読み上げに混入しない

**独立テスト**: ページ内の図を含むXMLをTTSで読み上げ、`readAloud`属性に応じて図の説明が読まれる/省略される

### Input

- [ ] T048 セットアップ分析を読む: specs/002-book-md-structure/tasks/ph1-output.md
- [ ] T049 前フェーズ出力を読む: specs/002-book-md-structure/tasks/ph3-output.md

### Test Implementation (RED)

- [ ] T050 [P] [US3] 図コメント解析テストを実装: tests/book_converter/test_parser.py（`<!-- FIGURE: path -->` パターン）
- [ ] T051 [P] [US3] 図説明文解析テストを実装: tests/book_converter/test_parser.py（図コメント後のテキストをdescriptionに）
- [ ] T052 [P] [US3] ページメタデータ解析テストを実装: tests/book_converter/test_parser.py（`N / M` パターン、type判定）
- [ ] T053 [P] [US3] Figure XML変換テストを実装: tests/book_converter/test_transformer.py（`<figure readAloud="optional">` 生成）
- [ ] T054 [P] [US3] PageMetadata XML変換テストを実装: tests/book_converter/test_transformer.py（`<pageMetadata type="chapter-page">` 生成）
- [ ] T055 [P] [US3] readAloud属性継承テストを実装: tests/book_converter/test_transformer.py（file=false, caption=true, description=親継承）
- [ ] T056 `make test` FAIL (RED) を確認
- [ ] T057 RED出力を生成: specs/002-book-md-structure/red-tests/ph4-test.md

### Implementation (GREEN)

- [ ] T058 REDテストを読む: specs/002-book-md-structure/red-tests/ph4-test.md
- [ ] T059 [P] [US3] `src/book_converter/parser.py` にparse_figure関数を実装（図コメント+説明文抽出）
- [ ] T060 [P] [US3] `src/book_converter/parser.py` にparse_page_metadata関数を実装（`N / M` 形式、type判定）
- [ ] T061 [P] [US3] `src/book_converter/transformer.py` にtransform_figure関数を実装（Figure→XML）
- [ ] T062 [P] [US3] `src/book_converter/transformer.py` にtransform_page_metadata関数を実装（PageMetadata→XML）
- [ ] T063 [P] [US3] `src/book_converter/transformer.py` にreadAloud属性処理を実装（true/false/optional）
- [ ] T064 [US3] コンポーネント統合（T059-T063の結合確認）
- [ ] T065 `make test` PASS (GREEN) を確認

### Verification

- [ ] T066 `make test` で全テスト通過を確認（US1, US2リグレッションなし）
- [ ] T067 フェーズ出力を生成: specs/002-book-md-structure/tasks/ph4-output.md

**チェックポイント**: User Stories 1, 2, 3はすべて独立して動作

---

## Phase 5: CLI & エラーハンドリング — TDDなし

**目的**: CLIエントリーポイント、エラーハンドリング、E2Eテスト

### Input

- [ ] T068 セットアップ分析を読む: specs/002-book-md-structure/tasks/ph1-output.md
- [ ] T069 前フェーズ出力を読む: specs/002-book-md-structure/tasks/ph4-output.md

### Test Implementation (RED)

- [ ] T070 [P] CLI引数テストを実装: tests/book_converter/test_cli.py（input.md output.xml --verbose --quiet）
- [ ] T071 [P] エラーハンドリングテストを実装: tests/book_converter/test_parser.py（警告継続、XMLコメントマーク）
- [ ] T072 [P] E2Eテストを実装: tests/book_converter/test_e2e.py（sample_book.md → expected_book.xml 比較）
- [ ] T073 [P] エラー率警告テストを実装: tests/book_converter/test_cli.py（10%超過時の警告メッセージ）
- [ ] T074 `make test` FAIL (RED) を確認
- [ ] T075 RED出力を生成: specs/002-book-md-structure/red-tests/ph5-test.md

### Implementation (GREEN)

- [ ] T076 REDテストを読む: specs/002-book-md-structure/red-tests/ph5-test.md
- [ ] T077 [P] `src/book_converter/cli.py` にmain関数を実装（argparse、--verbose、--quiet）
- [ ] T078 [P] `src/book_converter/parser.py` にエラーハンドリング追加（警告継続、ConversionError生成）
- [ ] T079 [P] `src/book_converter/xml_builder.py` にエラーコメント挿入機能を追加（`<!-- ERROR: ... -->`）
- [ ] T080 [P] `src/book_converter/cli.py` にエラーサマリー出力を実装（最後に警告ログまとめて表示）
- [ ] T081 `make test` PASS (GREEN) を確認

### Verification

- [ ] T082 `make test` で全テスト通過を確認
- [ ] T083 フェーズ出力を生成: specs/002-book-md-structure/tasks/ph5-output.md

---

## Phase 6: Polish & Cross-Cutting Concerns — TDDなし

**目的**: コード品質向上、ドキュメント整備、最終検証

### Input

- [ ] T084 セットアップ分析を読む: specs/002-book-md-structure/tasks/ph1-output.md
- [ ] T085 前フェーズ出力を読む: specs/002-book-md-structure/tasks/ph5-output.md

### Implementation

- [ ] T086 [P] `make test-cov` でカバレッジ確認（≥80%目標）
- [ ] T087 [P] コード品質チェック（ruff check src/book_converter/）
- [ ] T088 [P] ファイルサイズ確認（各ファイル800行以下、各関数50行以下）
- [ ] T089 quickstart.md 検証（CLIコマンド動作確認）
- [ ] T090 book.xsd に対するXML検証テスト追加

### Verification

- [ ] T091 `make test` で全テスト通過を確認
- [ ] T092 フェーズ出力を生成: specs/002-book-md-structure/tasks/ph6-output.md

---

## 依存関係と実行順序

### フェーズ依存関係

- **Setup (Phase 1)**: 依存なし - メインエージェント直接実行
- **User Stories (Phase 2-4)**: TDDフロー（tdd-generator → phase-executor）
  - ユーザーストーリーは優先度順に順次進行（P1 → P2 → P3）
- **CLI & エラーハンドリング (Phase 5)**: TDDフロー
- **Polish (Phase 6)**: 全ユーザーストーリー完了後 - phase-executorのみ

### 各ユーザーストーリーフェーズ内 (TDDフロー)

1. **Input**: セットアップ分析(ph1) + 前フェーズ出力（前作業のコンテキスト）を読む
2. **Test Implementation (RED)**: テストをFIRST作成 → `make test` FAIL確認 → RED出力生成
3. **Implementation (GREEN)**: REDテスト読む → 実装 → `make test` PASS確認
4. **Verification**: リグレッションなし確認 → フェーズ出力生成

### エージェント委任

- **Phase 1 (Setup)**: メインエージェント直接実行
- **Phase 2-5 (User Stories, CLI)**: tdd-generator (RED) → phase-executor (GREEN + Verification)
- **Phase 6 (Polish)**: phase-executorのみ

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
specs/002-book-md-structure/
├── tasks.md                    # このファイル
├── tasks/
│   ├── ph1-output.md           # Phase 1 出力（Setup結果）
│   ├── ph2-output.md           # Phase 2 出力（US1 GREEN結果）
│   ├── ph3-output.md           # Phase 3 出力（US2 GREEN結果）
│   ├── ph4-output.md           # Phase 4 出力（US3 GREEN結果）
│   ├── ph5-output.md           # Phase 5 出力（CLI GREEN結果）
│   └── ph6-output.md           # Phase 6 出力（Polish結果）
└── red-tests/
    ├── ph2-test.md             # Phase 2 REDテスト結果（FAIL確認）
    ├── ph3-test.md             # Phase 3 REDテスト結果（FAIL確認）
    ├── ph4-test.md             # Phase 4 REDテスト結果（FAIL確認）
    └── ph5-test.md             # Phase 5 REDテスト結果（FAIL確認）
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
- [ ] 入力解析テスト
- [ ] 変換ロジックテスト
- [ ] **出力生成テスト**（見落としがち）
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
