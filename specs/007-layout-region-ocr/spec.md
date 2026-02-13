# Feature Specification: レイアウト検出に基づく領域別OCR

**Feature Branch**: `007-layout-region-ocr`
**Created**: 2026-02-11
**Status**: Draft
**Input**: Issue #8 - feat: レイアウト検出に基づく領域別OCR

## 概要

現在のパイプラインではページ全体を一度にDeepSeek-OCRに送信しているため、複雑なレイアウト（縦書き・横書き混在、マルチカラム、図表混在）で読み順の混乱が発生する。

YOLOによるレイアウト検出を拡張し、検出した領域毎にOCRを実行することで精度向上を図る。

## User Scenarios & Testing

### User Story 1 - 拡張レイアウト検出 (Priority: P1)

ユーザーとして、ページ内のすべてのレイアウト要素（タイトル、本文テキスト、図、表、数式、キャプション）を個別に検出してほしい。これにより、各領域の種類に応じた適切な処理が可能になる。

**Why this priority**: 領域別OCRの前提となる基盤機能。これがなければ後続の処理ができない。

**Independent Test**: 複雑なレイアウトのページ画像に対してレイアウト検出を実行し、各領域が正しく分類・検出されることを確認できる。

**Acceptance Scenarios**:

1. **Given** テキスト、タイトル、図が混在するページ画像がある, **When** レイアウト検出を実行する, **Then** 各領域が適切な種類（TEXT, TITLE, FIGURE等）で検出される
2. **Given** マンガパネルを含むページ画像がある, **When** レイアウト検出を実行する, **Then** 各パネルがFIGUREとして個別に検出される
3. **Given** 表とそのキャプションを含むページ画像がある, **When** レイアウト検出を実行する, **Then** 表はTABLE、キャプションはCAPTIONとして検出される

---

### User Story 2 - 領域別OCR処理 (Priority: P1)

ユーザーとして、検出された各領域に対して適切なOCR処理を実行してほしい。テキスト領域はDeepSeek-OCRで読み取り、図領域はVLMで説明を生成する。

**Why this priority**: メイン機能。領域検出後に各領域を適切に処理することがこの機能の核心。

**Independent Test**: 検出済みの領域情報を持つページに対してOCRを実行し、各領域が適切なエンジンで処理されることを確認できる。

**Acceptance Scenarios**:

1. **Given** TEXT領域が検出されたページがある, **When** 領域別OCRを実行する, **Then** TEXT領域はDeepSeek-OCRで読み取られる
2. **Given** FIGURE領域が検出されたページがある, **When** 領域別OCRを実行する, **Then** FIGURE領域はVLMで説明文が生成される
3. **Given** TABLE領域が検出されたページがある, **When** 領域別OCRを実行する, **Then** TABLE領域はDeepSeek-OCRで構造を保持して読み取られる
4. **Given** TITLE領域が検出されたページがある, **When** 領域別OCRを実行する, **Then** TITLE領域はDeepSeek-OCRで読み取られ、見出しとしてマークされる

---

### User Story 3 - 読み順の再構築 (Priority: P2)

ユーザーとして、検出された領域を正しい読み順で並べ替えてほしい。横書きの場合は上から下・左から右、縦書きの場合は上から下・右から左の順序で出力される。

**Why this priority**: 精度向上のための重要機能だが、基本的な領域別OCR（US1, US2）が動作すれば最低限の価値は提供できる。

**Independent Test**: 複数領域を持つページに対して読み順ソートを実行し、出力テキストが自然な読み順になることを確認できる。

**Acceptance Scenarios**:

1. **Given** 横書きレイアウトのページで複数のTEXT領域がある, **When** 読み順ソートを実行する, **Then** 上から下、左から右の順序で並べ替えられる
2. **Given** 2カラムレイアウトのページがある, **When** 読み順ソートを実行する, **Then** 左カラム全体→右カラム全体の順序で並べ替えられる
3. **Given** タイトルと本文が混在するページがある, **When** 読み順ソートを実行する, **Then** タイトルが本文より先に出力される

---

### User Story 4 - フォールバック処理 (Priority: P2)

ユーザーとして、レイアウト検出に失敗した場合や検出領域が少ない場合でも、従来通りページ全体のOCRが実行されてほしい。

**Why this priority**: 堅牢性のための機能。検出失敗時にも最低限の出力を保証する。

**Independent Test**: レイアウト検出結果が空またはカバー率が低いページに対してOCRを実行し、ページ全体OCRにフォールバックすることを確認できる。

**Acceptance Scenarios**:

1. **Given** レイアウト検出で領域が検出されなかったページがある, **When** 領域別OCRを実行する, **Then** ページ全体に対してDeepSeek-OCRが実行される
2. **Given** 検出領域がページ面積の30%未満のページがある, **When** 領域別OCRを実行する, **Then** ページ全体に対してDeepSeek-OCRが実行される

---

### Edge Cases

- 検出領域が重複している場合 → 重複部分を除去して処理
- 極端に小さい領域（ノイズ）が検出された場合 → 最小面積しきい値で除外
- ページ全体が1つの図として検出された場合 → ページ全体OCRにフォールバック
- 検出信頼度が低い領域がある場合 → 信頼度しきい値で除外

## Requirements

### Functional Requirements

- **FR-001**: システムはDocLayout-YOLOのすべての検出クラス（title, plain text, table, figure, figure_caption, table_caption, table_footnote, isolated formula, formula_caption）を検出できなければならない
- **FR-002**: システムはlayout.jsonの構造を「figures」配列から「regions」配列に拡張し、各領域の種類、位置、信頼度を格納しなければならない
- **FR-003**: システムは検出された領域の種類に応じて適切なOCRエンジンを選択しなければならない（TEXT/TITLE→DeepSeek-OCR、FIGURE→VLM）
- **FR-004**: システムは検出された領域をbbox座標に基づいて読み順にソートしなければならない
- **FR-005**: システムはソートされた各領域のOCR結果を連結して最終出力を生成しなければならない
- **FR-006**: システムは領域が検出されなかった場合、または検出領域のカバー率が低い場合にページ全体OCRにフォールバックしなければならない
- **FR-007**: システムは重複領域を検出し、重複部分を適切に処理しなければならない
- **FR-008**: システムは最小面積しきい値未満の領域をノイズとして除外しなければならない

### Key Entities

- **Region（領域）**: ページ内の検出された領域。種類（type）、位置（bbox）、信頼度（confidence）を持つ
- **Layout（レイアウト）**: ページ毎の領域リスト。読み順ソート前後の状態を持つ
- **OCR Result（OCR結果）**: 各領域のOCR出力テキスト。領域種類に応じたマークアップを含む

## Success Criteria

### Measurable Outcomes

- **SC-001**: 複雑なレイアウト（2カラム以上）のページにおいて、読み順の正確性が90%以上となる
- **SC-002**: マンガパネルを含むページにおいて、各パネルが個別のFIGUREとして80%以上の精度で検出される
- **SC-003**: 領域検出失敗時のフォールバック処理により、すべてのページで何らかのOCR出力が生成される（出力率100%）
- **SC-004**: 従来のページ全体OCRと比較して、複雑レイアウトページのOCR精度が向上する

## Assumptions

- DocLayout-YOLOは現在使用中のモデル（juliozhao/DocLayout-YOLO-DocStructBench）をそのまま使用する
- 読み順は横書き（左→右、上→下）をデフォルトとする
- フォールバックのカバー率しきい値は30%をデフォルトとする
- 最小領域面積しきい値はページ面積の1%をデフォルトとする

## Scope

### In Scope

- YOLO検出クラスの拡張
- layout.json構造の変更
- 領域別OCR dispatcher の実装
- 読み順ソートアルゴリズムの実装
- pipeline.py への統合
- フォールバック処理の実装

### Out of Scope

- マンガ専用OCR（manga-ocr）の統合
- 縦書き専用の読み順ソート（将来の拡張として検討）
- 新しいYOLOモデルの導入
- リアルタイム処理の最適化

## Dependencies

- 既存の `detect_figures.py` モジュール
- 既存の `ocr_deepseek.py` モジュール
- 既存の `describe_figures.py` モジュール
- DocLayout-YOLO モデル（juliozhao/DocLayout-YOLO-DocStructBench）
