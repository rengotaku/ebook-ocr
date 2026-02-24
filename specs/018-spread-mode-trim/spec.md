# Feature Specification: Spread モード明示指定と Trim 制御の拡張

**Feature Branch**: `018-spread-mode-trim`
**Created**: 2026-02-24
**Status**: Draft
**Input**: Issue #29 - feat: Add explicit spread mode option instead of auto-detection

## Clarifications

### Session 2026-02-24

- Q: `auto` モードは必要か？ → A: 不要。削除する。
- Q: モード未指定時のデフォルト動作は？ → A: `single`（単ページ）をデフォルトにし、使用モードを標準出力に表示する。
- Q: 分割後の上下 trim は必要か？ → A: 不要。global-trim で上下は対応済み、split-trim は左右（外側エッジ）のみ。
- Q: プレビューのワークフローは？ → A: 2段階に分ける。(1) フレーム生成（1回のみ）、(2) 生成済みフレームに対して trim 適用（パラメータ変更時は繰り返し可能）。動画からのフレーム再生成を避ける。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Spread モードの明示指定 (Priority: P1)

ユーザーは、画像が単ページか見開きかを明示的に指定することで、アスペクト比による自動判別の誤判定を防ぎたい。

従来の自動判別では、横長の単ページが見開きと誤判定されたり、縦長の見開きが単ページと誤判定されることがあった。ユーザーは書籍の形式を事前に把握しているため、明示的に指定できる方が確実に正しい処理ができる。

**Why this priority**: 誤判定は後続のOCR処理全体に影響するため、最も基本的かつ重要な機能。

**Independent Test**: 単一の画像ファイルに対して `--mode=spread` または `--mode=single` を指定し、期待通りに分割されるか/されないかを確認できる。

**Acceptance Scenarios**:

1. **Given** 見開き画像がある, **When** `--mode=spread` を指定して実行, **Then** 画像が左右2ページに分割される
2. **Given** 単ページ画像がある, **When** `--mode=single` を指定して実行, **Then** 画像は分割されずそのまま出力される
3. **Given** 任意の画像がある, **When** モード未指定で実行, **Then** デフォルトの `single` モードで処理され、使用モードが標準出力に表示される
4. **Given** 環境変数 `SPREAD_MODE=spread` が設定されている, **When** CLI引数でモード未指定で実行, **Then** 環境変数の値が使用され、使用モードが標準出力に表示される
5. **Given** 任意のモードで実行, **When** 処理開始時, **Then** 「Mode: single」または「Mode: spread」が標準出力に表示される

---

### User Story 2 - 2段階 Trim 制御 (Priority: P2)

ユーザーは、画像の余白を分割前（全体）と分割後（ページ単位）の2段階でトリミングしたい。

書籍スキャン画像では、スキャナーの黒枠、ページ端の汚れ、中央の綴じ代など、様々な余白が発生する。分割前に全体の外枠をトリミングし、分割後に各ページの端をトリミングすることで、OCRに最適な画像を得られる。

**Why this priority**: Spread モードが正しく動作する前提で、画像品質の向上に寄与する。

**Independent Test**: サンプル画像に対して global-trim と split-trim を適用し、出力画像のサイズと内容を確認できる。

**Acceptance Scenarios**:

1. **Given** 上下左右に黒枠がある見開き画像, **When** `--global-trim-top=0.02 --global-trim-bottom=0.02` を指定, **Then** 分割前に上下2%がトリミングされる
2. **Given** 見開き画像, **When** `--left-trim=0.03 --right-trim=0.03` を指定, **Then** 分割後の左ページの左端3%、右ページの右端3%がトリミングされる
3. **Given** 単ページモードの画像, **When** global-trim パラメータを指定, **Then** 単ページにも global-trim が適用される
4. **Given** trim パラメータ未指定, **When** 実行, **Then** トリミングなし（0%）で処理される

---

### User Story 3 - パイプライン統合とプレビュー (Priority: P3)

ユーザーは、フルパイプライン実行前に少数のサンプル画像でトリミング結果をプレビューし、パラメータを調整したい。

書籍ごとにスキャン状態が異なるため、最適な trim パラメータは事前に確認が必要。プレビュー機能により、全ページ処理前にパラメータを確定できる。

**プレビューは2段階ワークフロー**:
1. **フレーム生成**: 動画からサンプルフレームを抽出（1回のみ実行）
2. **Trim プレビュー**: 生成済みフレームに対して trim を適用（パラメータ変更時は繰り返し実行可能）

この分離により、trim パラメータ調整のたびに動画からフレームを再生成する必要がなくなる。

**Why this priority**: パイプライン統合は P1/P2 の機能が安定してから行うべき。

**Independent Test**: 2つのコマンドを順に実行し、フレーム生成とtrim適用が独立して動作することを確認できる。

**Acceptance Scenarios**:

1. **Given** 動画ファイルがある, **When** `make preview-extract VIDEO=input.mp4 LIMIT=5` を実行, **Then** 5枚のサンプルフレームが preview/ ディレクトリに出力される
2. **Given** preview/ にフレームが存在する, **When** `make preview-trim HASHDIR=output/<hash>` を実行, **Then** フレームに trim が適用されプレビュー画像が生成される
3. **Given** preview/ にフレームが存在する, **When** trim パラメータを変更して `make preview-trim` を再実行, **Then** 動画からの再抽出なしで新しい trim 結果がプレビューされる
4. **Given** プレビュー結果を確認済み, **When** `make run VIDEO=input.mp4 SPREAD_MODE=spread` を実行, **Then** split-spreads ステップを含むフルパイプラインが実行される
5. **Given** config.yaml に spread/trim 設定がある, **When** `make run` を実行, **Then** 設定ファイルの値がデフォルトとして使用される

---

### Edge Cases

- **モードと画像の不一致**: `--mode=spread` 指定時に明らかに単ページの画像が入力された場合 → 警告を出力するが処理は続行（ユーザーの意図を尊重）
- **trim 値の範囲外**: trim 値が0未満または0.5以上の場合 → エラーで処理を停止
- **空の入力ディレクトリ**: 処理対象の画像がない場合 → 警告メッセージを出力して正常終了
- **既存の originals/ ディレクトリ**: 再実行時に originals/ が存在する場合 → 既存の originals から再処理（現行動作を維持）
- **preview/ が空で preview-trim 実行**: フレームが存在しない場合 → エラーメッセージを出力し、先に preview-extract を実行するよう案内

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムは spread モードを `single`（単ページ）と `spread`（見開き）の2種類から選択できること
- **FR-002**: システムは環境変数 `SPREAD_MODE` でモードを設定できること
- **FR-003**: システムは CLI 引数 `--mode` でモードを設定でき、環境変数より優先されること
- **FR-004**: システムはモード未指定時に `single` をデフォルトとして使用すること
- **FR-005**: システムは処理開始時に使用モードを標準出力に表示すること（例: 「Mode: single」）
- **FR-006**: システムは global-trim（上下左右）を分割前の画像に適用できること
- **FR-007**: システムは split-trim（左ページ外側、右ページ外側）を分割後の画像に適用できること
- **FR-008**: システムは単ページモードでも global-trim を適用できること
- **FR-009**: システムはデフォルトで trim 0% で動作すること
- **FR-010**: システムは config.yaml から spread/trim 設定を読み込めること
- **FR-011**: システムは `make run` のパイプラインに split-spreads ステップを統合すること
- **FR-012**: システムは `make preview-extract` でサンプルフレームを動画から抽出できること
- **FR-013**: システムは `make preview-trim` で生成済みフレームに対して trim をプレビューできること
- **FR-014**: システムはフレーム抽出と trim プレビューを独立して実行でき、trim プレビューはフレーム再抽出なしで繰り返し実行可能なこと

### Key Entities

- **SpreadMode**: 画像の処理モード（single: 単ページ、spread: 見開き）
- **TrimConfig**: トリミング設定（global: 上下左右、split: 左外側・右外側）
- **ProcessingResult**: 処理結果（入力ファイル、出力ファイル、適用されたモード/trim）
- **PreviewState**: プレビュー状態（extracted: フレーム抽出済み、trimmed: trim適用済み）

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: ユーザーは2つのモード（single/spread）を明示的に指定でき、100%の確率で指定通りに処理される
- **SC-002**: global-trim と split-trim の両方を指定した場合、正しい順序（global → split）で適用される
- **SC-003**: 処理実行時に使用モードが標準出力に表示され、ユーザーが現在の設定を確認できる
- **SC-004**: プレビューの trim 調整時に動画からのフレーム再抽出が発生しないこと
- **SC-005**: パイプライン統合後も、従来の個別コマンド実行と同一の結果が得られる

## Assumptions

- ユーザーは書籍の形式（単ページ/見開き）を事前に把握している
- trim 値は0〜0.5（50%）の範囲で指定される（それ以上は意味をなさない）
- プレビュー機能は CLI 環境での利用を想定（GUI プレビューは対象外）
- プレビュー用フレームは preview/ ディレクトリに保存され、trim 調整中は保持される

## Test Data

検証用の動画ファイル:

| ファイル | モード | 説明 |
|---------|--------|------|
| `movies/n3-failers-in-developing-softwear.mov` | `spread` | 1フレームに2ページ格納（見開き） |
| `movies/n5-sre.mov` | `single` | 1フレームに1ページ格納（単ページ） |

## Out of Scope

- 自動余白検出（getbbox による自動トリミング）は別機能として検討
- アスペクト比による自動判別（auto モード）- 廃止
- ページごとに異なるモードを指定する機能
- GUI ベースのプレビュー/パラメータ調整インターフェース
