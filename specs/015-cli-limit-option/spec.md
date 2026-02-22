# Feature Specification: CLIコマンドへの--limitオプション追加

**Feature Branch**: `015-cli-limit-option`
**Created**: 2026-02-22
**Status**: Draft
**Input**: GitHub Issue #19 - Add --limit option to CLI commands for quick pipeline testing

## User Scenarios & Testing *(mandatory)*

### User Story 1 - 開発者がパイプライン全体の動作を短時間で検証する (Priority: P1)

開発者として、パイプラインの全ステップを少数の画像で実行し、各ステップが正常に動作することを短時間で確認したい。AIに動作確認を依頼する際や、新機能の統合テスト時に、全画像を処理せずに全ステップの実行フローを検証できることが重要。

**Why this priority**: パイプライン全体の動作確認は開発サイクルの最も頻繁なユースケース。500ページの処理に30-60分かかるところを2-5分に短縮できれば、開発効率が大幅に向上する。

**Independent Test**: `make test-run VIDEO=xxx LIMIT=25` を実行し、全ステップが完了して出力ファイルが生成されることを確認。

**Acceptance Scenarios**:

1. **Given** 動画から抽出された500枚のフレーム画像があるとき, **When** `--limit 25` オプション付きで各CLIを実行する, **Then** 最初の25枚のみが処理され、残りの475枚はスキップされる
2. **Given** パイプラインを実行中のとき, **When** `make test-run VIDEO=input.mov LIMIT=25` を実行する, **Then** 全ステップ（重複排除→レイアウト検出→OCR→統合）が25枚の画像のみで完了する
3. **Given** `--limit` オプションが指定されたとき, **When** 処理が開始される, **Then** 標準エラー出力に処理対象画像数が表示される

---

### User Story 2 - 個別CLIコマンドで画像数を制限する (Priority: P2)

開発者として、特定のCLIコマンドのみを少数の画像でテストし、そのステップの動作を確認したい。パイプライン全体ではなく、個別のコマンドのデバッグや機能確認に使用する。

**Why this priority**: 個別コマンドのテストはパイプライン全体テストより詳細なデバッグに必要だが、頻度は低い。

**Independent Test**: `python -m src.cli.run_ocr output/pages -o output/ocr --limit 10` を実行し、10件のOCR結果のみが生成されることを確認。

**Acceptance Scenarios**:

1. **Given** 100枚の画像が入力ディレクトリにあるとき, **When** `--limit 10` を指定して `deduplicate.py` を実行する, **Then** 最初の10枚のみが重複判定され、出力される
2. **Given** `--limit` オプションが指定されていないとき, **When** CLIを実行する, **Then** 全ての画像が処理される（従来通りの動作）

---

### User Story 3 - エラーハンドリングの確認 (Priority: P3)

開発者として、limitオプションに不正な値を指定した場合に適切なエラーメッセージが表示されることを確認したい。

**Why this priority**: エラーハンドリングはユーザビリティの一部だが、正常系の動作確認より優先度は低い。

**Independent Test**: `--limit 0` や `--limit -1` を指定してエラーメッセージを確認。

**Acceptance Scenarios**:

1. **Given** `--limit 0` を指定したとき, **When** CLIを実行する, **Then** 適切なエラーメッセージが表示され、処理は行われない
2. **Given** `--limit -5` を指定したとき, **When** CLIを実行する, **Then** 適切なエラーメッセージが表示され、処理は行われない
3. **Given** `--limit abc` を指定したとき, **When** CLIを実行する, **Then** argparseが型エラーを表示する

---

### Edge Cases

- `--limit` の値が入力画像数より大きい場合はどうなるか？ → 全画像を処理する（エラーにならない）
- `--limit 1` を指定した場合、最小単位の処理ができるか？ → 1枚のみ処理される
- 入力ディレクトリに画像がない場合はどうなるか？ → 既存のエラーハンドリングに従う

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムは `deduplicate.py` に `--limit N` オプションを提供しなければならない
- **FR-002**: システムは `detect_layout.py` に `--limit N` オプションを提供しなければならない
- **FR-003**: システムは `run_ocr.py` に `--limit N` オプションを提供しなければならない
- **FR-004**: システムは `consolidate.py` に `--limit N` オプションを提供しなければならない
- **FR-005**: `--limit N` が指定された場合、システムはファイル名でソートされた最初のN個の画像のみを処理しなければならない
- **FR-006**: `--limit N` が指定された場合、システムは処理対象画像数を標準エラー出力に表示しなければならない
- **FR-007**: `--limit` が指定されていない場合、システムは全ての画像を処理しなければならない（後方互換性）
- **FR-008**: `--limit` の値が0以下の場合、システムはエラーメッセージを表示して終了しなければならない
- **FR-009**: Makefileは `test-run` ターゲットを提供し、`LIMIT` 変数で画像数制限を指定できなければならない
- **FR-010**: `test-run` ターゲットは、重複排除→レイアウト検出→OCR→統合の全ステップを順番に実行しなければならない

### Key Entities

- **画像ファイル**: 処理対象のPNG画像。ファイル名でソートされ、`--limit` が指定された場合は先頭からN個が選択される
- **CLIオプション**: `--limit` は整数値を取り、処理する画像の最大数を指定する

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 25枚の画像で全パイプラインが5分以内に完了すること（従来の500枚処理時の30-60分と比較）
- **SC-002**: `--limit` オプション使用時、処理時間が画像数に比例して短縮されること
- **SC-003**: 全4つのCLIコマンドで `--limit` オプションが利用可能であること
- **SC-004**: `make test-run` で全ステップが正常に実行され、出力ファイルが生成されること
- **SC-005**: 既存のパイプライン（`--limit` なし）の動作に影響がないこと（後方互換性）

## Assumptions

- 画像ファイルはファイル名の辞書順でソートされ、その順序で処理される
- `--limit` オプションはテスト・検証目的であり、本番処理では使用しないことを前提とする
- 各CLIの既存のヘルプメッセージ形式に従って `--limit` オプションの説明を追加する
