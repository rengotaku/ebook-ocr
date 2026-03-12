# タスク: コードブロック視覚検出

**Input**: `/specs/021-code-block-gray-detection/` の設計ドキュメント
**Prerequisites**: plan.md (required), spec.md (required), research.md, data-model.md

**テスト**: TDD 必須。各ユーザーストーリーフェーズは Test Implementation (RED) → Implementation (GREEN) → Verification のワークフローに従う。

**構成**: タスクはユーザーストーリーごとにグループ化し、独立した実装・テストを可能にする。

## フォーマット: `[ID] [P?] [Story] 説明`

- **[P]**: 依存関係なし（異なるファイル、実行順序自由）
- **[Story]**: このタスクが属するユーザーストーリー（例: US1, US2, US3）
- 説明にはファイルパスを含める

## ユーザーストーリー概要

| ID | タイトル | 優先度 | FR | シナリオ |
|----|---------|--------|-----|---------|
| US1 | 灰色背景コードブロックの自動検出 | P1 | FR-001, FR-002 | TEXT の灰色背景 → CODE 再分類 |
| US2 | FIGURE 誤検出コードの救済 | P1 | FR-003, FR-004, FR-005, FR-006 | FIGURE テキスト分析 → CODE 再分類 |
| US3 | TEXT リージョン内コードの検出 | P1 | FR-005, FR-006 | TEXT テキスト分析 → CODE 再分類 |
| US4 | 断片化コードブロックの結合 | P2 | FR-007, FR-008 | 隣接 CODE の bbox 結合 |
| US5 | CODE リージョンの可視化と出力 | P2 | FR-009, FR-010 | 黄色描画 + [CODE: N] 出力 |

## パス規約

- **ソース**: `src/layout/`, `src/`
- **テスト**: `tests/`
- **設定**: `config.yaml`
- **機能ディレクトリ**: `specs/021-code-block-gray-detection/`

---

## Phase 1: Setup（既存コード調査・変更準備） — TDD なし

**目的**: 既存の実装を理解し、変更計画を確認する

- [x] T001 既存のレイアウト検出実装を調査: `src/layout/detector.py`
- [x] T002 [P] 既存の OCR ユーティリティを調査: `src/layout_ocr_utils.py`
- [x] T003 [P] 既存のテストを調査: `tests/test_layout_ocr.py`, `tests/test_reading_order.py`
- [x] T004 [P] 既存の設定ファイルを調査: `config.yaml`
- [x] T005 [P] `src/layout/__init__.py` のエクスポート構成を確認
- [x] T006 [P] feat/022 ブランチの既存灰色検出実装を参考として調査: `git diff main..feat/022-code-block-gray-detection -- src/layout/code_detector.py`
- [x] T007 セットアップ分析を生成: `specs/021-code-block-gray-detection/tasks/ph1-output.md`

---

## Phase 2: US1 — 灰色背景コードブロックの自動検出 (Priority: P1) MVP

**Goal**: TEXT リージョンの灰色背景を検出し CODE に再分類。OCR パイプラインで CODE をコードフェンス出力。

**独立テスト**: 灰色背景画像を含む TEXT リージョンが CODE に再分類され、` ``` ` フェンスで出力されることを確認

### Input

- [x] T008 前フェーズの出力を読む: `specs/021-code-block-gray-detection/tasks/ph1-output.md`

### Test Implementation (RED)

- [x] T009 [P] [US1] `detect_gray_background()` の基本テストを実装: 灰色画像→True、白画像→False、黒画像→False in `tests/test_code_detector.py`
- [x] T010 [P] [US1] `detect_gray_background()` の閾値境界テストを実装: threshold=0.7 前後の mixed 画像 in `tests/test_code_detector.py`
- [x] T011 [P] [US1] `detect_gray_background()` の入力バリデーションテストを実装: None 画像、範囲外 bbox、ゼロサイズ bbox in `tests/test_code_detector.py`
- [x] T012 [P] [US1] アスペクト比フィルタテストを実装: 横長帯状リージョン(ratio>8)は CODE 判定しない in `tests/test_code_detector.py`
- [x] T013 [P] [US1] `paragraphs_to_layout()` 統合テストを実装: cv_img ありで灰色 TEXT が CODE に変換される in `tests/test_code_detector.py`
- [x] T014 [P] [US1] `paragraphs_to_layout()` 後方互換テストを実装: cv_img=None で従来通り TEXT のまま in `tests/test_code_detector.py`
- [x] T015 [P] [US1] `format_ocr_result("CODE", text)` テストを実装: コードフェンス囲み in `tests/test_layout_ocr.py`
- [x] T016 [P] [US1] `select_ocr_engine("CODE")` テストを実装: "yomitoku" を返す in `tests/test_layout_ocr.py`
- [x] T017 `make test` で FAIL を確認 (RED)
- [x] T018 RED 出力を生成: `specs/021-code-block-gray-detection/red-tests/ph2-test.md`

### Implementation (GREEN)

- [x] T019 RED テストを読む: `specs/021-code-block-gray-detection/red-tests/ph2-test.md`
- [x] T020 [P] [US1] `detect_gray_background()` を実装: HSV 色空間で灰色画素比率を計算 in `src/layout/code_detector.py`（新規ファイル）
- [x] T021 [P] [US1] `format_ocr_result()` に CODE 分岐を追加: ` ```\n{text}\n``` ` in `src/layout_ocr_utils.py`
- [x] T022 [P] [US1] `select_ocr_engine()` に CODE 分岐を追加: → "yomitoku" in `src/layout_ocr_utils.py`
- [x] T023 [US1] `paragraphs_to_layout()` に `cv_img` パラメータ追加 + 灰色判定呼び出し + アスペクト比フィルタ in `src/layout/detector.py`
- [x] T024 [US1] `detect_layout_yomitoku()` で `cv_img` を `paragraphs_to_layout()` に渡す in `src/layout/detector.py`
- [x] T025 [US1] `src/layout/__init__.py` に `code_detector` を export 追加
- [x] T026 `make test` で PASS を確認 (GREEN)

### Verification

- [x] T027 `make test` で全テスト通過（リグレッションなし）を確認
- [x] T028 `make lint` で lint エラーなしを確認
- [x] T029 フェーズ出力を生成: `specs/021-code-block-gray-detection/tasks/ph2-output.md`

**Checkpoint**: 灰色背景の TEXT リージョンが CODE に再分類され、コードフェンスで出力される。白背景や帯状ヘッダーは誤判定しない。

---

## Phase 3: US2 + US3 — テキスト分析によるコード検出 (Priority: P1)

**Goal**: 記号比率 + 拡張キーワードで TEXT + FIGURE リージョンのコードを検出し CODE に再分類

**独立テスト**: プログラミング記号を含むテキストが CODE と判定され、日本語本文は TEXT のまま維持されること

### Input

- [x] T030 セットアップ分析を読む: `specs/021-code-block-gray-detection/tasks/ph1-output.md`
- [x] T031 前フェーズの出力を読む: `specs/021-code-block-gray-detection/tasks/ph2-output.md`

### Test Implementation (RED)

- [x] T032 [P] [US2] `calc_symbol_ratio()` テストを実装: コードテキスト→高比率、日本語テキスト→0.0 in `tests/test_code_detector.py`
- [x] T033 [P] [US2] `count_code_keywords()` テストを実装: "class Foo extends Bar"→>=2、"日本語テキスト"→0 in `tests/test_code_detector.py`
- [x] T034 [P] [US2] `detect_code_by_text()` の OR 条件テストを実装: 記号比率のみ True、キーワードのみ True、両方 False in `tests/test_code_detector.py`
- [x] T035 [P] [US2] FIGURE → CODE 再分類テストを実装: コードテキスト含む FIGURE が CODE に変換 in `tests/test_code_detector.py`
- [x] T036 [P] [US3] TEXT → CODE 再分類テストを実装: コードテキスト含む TEXT が CODE に変換 in `tests/test_code_detector.py`
- [x] T037 [P] [US3] TITLE スキップテストを実装: section_headings リージョンはテキスト分析をスキップ in `tests/test_code_detector.py`
- [x] T038 [P] [US2] 日本語本文 false positive なしテストを実装: 一般的な日本語テキストが TEXT のまま in `tests/test_code_detector.py`
- [x] T039 [P] [US2] 多言語キーワードテストを実装: Python(def/import), Go(func/package), Rust(fn/impl) のキーワード検出 in `tests/test_code_detector.py`
- [x] T040 `make test` で FAIL を確認 (RED)
- [x] T041 RED 出力を生成: `specs/021-code-block-gray-detection/red-tests/ph3-test.md`

### Implementation (GREEN)

- [x] T042 RED テストを読む: `specs/021-code-block-gray-detection/red-tests/ph3-test.md`
- [x] T043 [P] [US2] `EXTENDED_KEYWORDS` 定数を定義（25言語対応キーワードリスト） in `src/layout/code_detector.py`
- [x] T044 [P] [US2] `calc_symbol_ratio(text)` を実装: 記号文字の比率を計算 in `src/layout/code_detector.py`
- [x] T045 [P] [US2] `count_code_keywords(text)` を実装: 拡張キーワードの出現数をカウント in `src/layout/code_detector.py`
- [x] T046 [US2] `detect_code_by_text(text, sym_threshold, kw_threshold)` を実装: OR 条件判定 in `src/layout/code_detector.py`
- [x] T047 [US2] `paragraphs_to_layout()` に FIGURE テキスト分析を追加: figure.paragraphs からテキスト取得 → detect_code_by_text() in `src/layout/detector.py`
- [x] T048 [US3] `paragraphs_to_layout()` に TEXT テキスト分析を追加: paragraph.contents → detect_code_by_text()（TITLE はスキップ） in `src/layout/detector.py`
- [x] T049 `make test` で PASS を確認 (GREEN)

### Verification

- [x] T050 `make test` で全テスト通過（リグレッションなし）を確認
- [x] T051 `make lint` で lint エラーなしを確認
- [x] T052 フェーズ出力を生成: `specs/021-code-block-gray-detection/tasks/ph3-output.md`

**Checkpoint**: TEXT + FIGURE 両方のリージョンでテキスト分析によるコード検出が動作。日本語本文の false positive なし。

---

## Phase 4: US4 — 断片化コードブロックの結合 (Priority: P2)

**Goal**: 隣接する CODE パラグラフを bbox 近接度で1つの CODE リージョンに結合

**独立テスト**: 垂直ギャップが閾値以内の CODE リージョンが1つに結合され、間に non-CODE がある場合は結合しないこと

### Input

- [x] T053 セットアップ分析を読む: `specs/021-code-block-gray-detection/tasks/ph1-output.md`
- [x] T054 前フェーズの出力を読む: `specs/021-code-block-gray-detection/tasks/ph3-output.md`

### Test Implementation (RED)

- [x] T055 [P] [US4] `is_code_fragment()` テストを実装: "}"→True, "3"→True, "日本語"→False in `tests/test_code_detector.py`
- [x] T056 [P] [US4] `merge_code_fragments()` 隣接結合テストを実装: CODE+CODE(gap<80px)→1つのCODE in `tests/test_code_detector.py`
- [x] T057 [P] [US4] `merge_code_fragments()` 結合打ち切りテストを実装: CODE+TEXT+CODE→2つのCODE in `tests/test_code_detector.py`
- [x] T058 [P] [US4] `merge_code_fragments()` FRAG 結合テストを実装: CODE+FRAG+CODE→1つのCODE in `tests/test_code_detector.py`
- [x] T059 [P] [US4] `merge_code_fragments()` ギャップ超過テストを実装: CODE+CODE(gap>80px)→2つのCODE in `tests/test_code_detector.py`
- [x] T060 [P] [US4] `merge_code_fragments()` イミュータブル性テストを実装: 入力リストが変更されない in `tests/test_code_detector.py`
- [x] T061 `make test` で FAIL を確認 (RED)
- [x] T062 RED 出力を生成: `specs/021-code-block-gray-detection/red-tests/ph4-test.md`

### Implementation (GREEN)

- [x] T063 RED テストを読む: `specs/021-code-block-gray-detection/red-tests/ph4-test.md`
- [x] T064 [P] [US4] `is_code_fragment(text)` を実装: 短いテキストの断片判定 in `src/layout/code_detector.py`
- [x] T065 [US4] `merge_code_fragments(regions, gap_threshold)` を実装: 隣接 CODE/FRAG の結合 + 外接矩形計算 in `src/layout/code_detector.py`
- [x] T066 [US4] `paragraphs_to_layout()` 末尾で `merge_code_fragments()` を呼び出し in `src/layout/detector.py`
- [x] T067 `make test` で PASS を確認 (GREEN)

### Verification

- [x] T068 `make test` で全テスト通過（リグレッションなし）を確認
- [x] T069 `make lint` で lint エラーなしを確認
- [x] T070 フェーズ出力を生成: `specs/021-code-block-gray-detection/tasks/ph4-output.md`

**Checkpoint**: 断片化された CODE パラグラフが正しく結合される。non-CODE による結合打ち切りも動作。

---

## Phase 5: US5 + 設定外部化 — 可視化・出力・設定 (Priority: P2)

**Goal**: CODE の可視化、標準出力表示、閾値の設定ファイル外部化

**独立テスト**: レイアウト画像で CODE が黄色描画され、config.yaml の閾値変更が反映されること

### Input

- [x] T071 セットアップ分析を読む: `specs/021-code-block-gray-detection/tasks/ph1-output.md`
- [x] T072 前フェーズの出力を読む: `specs/021-code-block-gray-detection/tasks/ph4-output.md`

### Test Implementation (RED)

- [x] T073 [P] [US5] `visualize_layout()` CODE 色分けテストを実装: layout_regions に CODE があれば黄色で描画 in `tests/test_code_detector.py`
- [x] T074 [P] [US5] `detect_layout_yomitoku()` の CODE 数サマリ出力テストを実装: stdout に `[CODE: N]` が含まれる in `tests/test_code_detector.py`
- [x] T075 [P] [US5] 設定読み込みテストを実装: config.yaml の code_detection セクションからデフォルト値取得 in `tests/test_code_detector.py`
- [x] T076 `make test` で FAIL を確認 (RED)
- [x] T077 RED 出力を生成: `specs/021-code-block-gray-detection/red-tests/ph5-test.md`

### Implementation (GREEN)

- [x] T078 RED テストを読む: `specs/021-code-block-gray-detection/red-tests/ph5-test.md`
- [x] T079 [P] [US5] `visualize_layout()` に `layout_regions` パラメータ追加 + CODE 黄色描画 in `src/layout/detector.py`
- [x] T080 [P] [US5] `detect_layout_yomitoku()` のサマリ出力に CODE 数表示を追加 in `src/layout/detector.py`
- [x] T081 [P] [US5] `config.yaml` に `code_detection` セクションを追加（全閾値のデフォルト値） in `config.yaml`
- [x] T082 [US5] `src/layout/code_detector.py` に config.yaml 読み込み関数を追加し、各関数でデフォルト値を設定から取得
- [x] T083 `make test` で PASS を確認 (GREEN)

### Verification

- [x] T084 `make test` で全テスト通過（リグレッションなし）を確認
- [x] T085 `make lint` で lint エラーなしを確認
- [x] T086 フェーズ出力を生成: `specs/021-code-block-gray-detection/tasks/ph5-output.md`

**Checkpoint**: CODE が可視化画像で黄色描画。config.yaml で閾値調整可能。

---

## Phase 6: Polish & Cross-Cutting Concerns — TDD なし

**目的**: コード品質、ドキュメント整備

### Input

- [x] T087 セットアップ分析を読む: `specs/021-code-block-gray-detection/tasks/ph1-output.md`
- [x] T088 前フェーズの出力を読む: `specs/021-code-block-gray-detection/tasks/ph5-output.md`

### Implementation

- [x] T089 [P] `src/layout/code_detector.py` のファイルサイズ確認（800行以下）、必要に応じて分割
- [x] T090 [P] 不要な import やデッドコードを削除
- [x] T091 quickstart.md の手順に従い動作確認

### Verification

- [x] T092 `make test` で全テスト通過を確認
- [x] T093 `make lint` で lint エラーなしを確認
- [x] T094 フェーズ出力を生成: `specs/021-code-block-gray-detection/tasks/ph6-output.md`

---

## 依存関係 & 実行順序

### フェーズ依存関係

- **Setup (Phase 1)**: 依存なし — メインエージェント直接実行
- **US1 灰色背景 (Phase 2)**: Phase 1 に依存 — TDD フロー
- **US2+US3 テキスト分析 (Phase 3)**: Phase 2 に依存（CODE タイプ・フォーマットが前提）— TDD フロー
- **US4 断片結合 (Phase 4)**: Phase 3 に依存（CODE リージョン生成が前提）— TDD フロー
- **US5 可視化・設定 (Phase 5)**: Phase 4 に依存 — TDD フロー
- **Polish (Phase 6)**: 全フェーズに依存 — speckit:phase-executor のみ

### エージェント委譲

- **Phase 1 (Setup)**: メインエージェント直接実行
- **Phase 2-5 (ユーザーストーリー)**: speckit:tdd-generator (RED) → speckit:phase-executor (GREEN + Verification)
- **Phase 6 (Polish)**: speckit:phase-executor のみ

### [P] マーカー（依存なし）

- RED テスト [P]: 同じテストファイル内でも独立したテスト関数なら並行可能
- GREEN 実装 [P]: 異なるファイルへの変更は並行可能
- フェーズ間: 各フェーズは前フェーズの出力に依存するため [P] 不可

---

## フェーズ出力 & RED テストアーティファクト

### ディレクトリ構造

```
specs/021-code-block-gray-detection/
├── tasks.md                    # このファイル
├── tasks/
│   ├── ph1-output.md           # Phase 1 出力（Setup 結果）
│   ├── ph2-output.md           # Phase 2 出力（US1 灰色背景 GREEN 結果）
│   ├── ph3-output.md           # Phase 3 出力（US2+US3 テキスト分析 GREEN 結果）
│   ├── ph4-output.md           # Phase 4 出力（US4 断片結合 GREEN 結果）
│   ├── ph5-output.md           # Phase 5 出力（US5 可視化・設定 GREEN 結果）
│   └── ph6-output.md           # Phase 6 出力（Polish 結果）
└── red-tests/
    ├── ph2-test.md             # Phase 2 RED テスト（灰色背景 FAIL 確認）
    ├── ph3-test.md             # Phase 3 RED テスト（テキスト分析 FAIL 確認）
    ├── ph4-test.md             # Phase 4 RED テスト（断片結合 FAIL 確認）
    └── ph5-test.md             # Phase 5 RED テスト（可視化・設定 FAIL 確認）
```

### フェーズ出力フォーマット

| 出力タイプ | テンプレート |
|-----------|-------------|
| `ph1-output.md` | `.specify/templates/ph1-output-template.md` |
| `phN-output.md` | `.specify/templates/phN-output-template.md` |
| `phN-test.md` | `.specify/templates/red-test-template.md` |

---

## 実装戦略

### MVP First (Phase 1 + Phase 2)

1. Phase 1 完了: Setup（既存コード調査）
2. Phase 2 完了: US1 灰色背景コード検出 (RED → GREEN → Verification)
3. **停止して検証**: `make test` で全テスト通過を確認
4. 灰色背景の書籍で手動検証

### Full Delivery

1. Phase 1 → Phase 2 → Phase 3 → Phase 4 → Phase 5 → Phase 6
2. 各フェーズ完了時にコミット: `feat(phase-N): description`

---

## テストカバレッジルール

**境界テスト原則**: データ変換が発生するすべての境界でテストを書く

```
[画像入力] → [灰色検出] → [テキスト分析] → [断片結合] → [layout.json 出力]
    ↓           ↓            ↓              ↓              ↓
  テスト      テスト        テスト          テスト          テスト
```

**チェックリスト**:
- [ ] 灰色背景検出テスト（HSV 閾値境界）
- [ ] テキスト分析テスト（記号比率 + キーワード）
- [ ] 断片結合テスト（bbox 近接 + 結合打ち切り）
- [ ] **paragraphs_to_layout() 統合テスト**（入力→最終出力）
- [ ] OCR フォーマットテスト（CODE → コードフェンス）

---

## 備考

- [P] タスク = 依存なし、実行順序自由
- [Story] ラベルはタスクを特定のユーザーストーリーにマッピング
- US2 と US3 は同じテキスト分析ロジックを共有するため Phase 3 で統合実装
- feat/022 ブランチの実装は設計参考として使用（コードのコピーではなく TDD で再実装）
- 閾値は1冊の書籍で検証済み。他書籍で要チューニングの可能性あり
