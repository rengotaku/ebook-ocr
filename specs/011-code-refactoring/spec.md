# Feature Specification: コード品質自動化とファイルサイズ制限

**Feature Branch**: `011-code-refactoring`
**Created**: 2026-02-18
**Status**: Draft
**Input**: Issue#13 - ruff導入・pre-commit設定・ファイル分割

## User Scenarios & Testing *(mandatory)*

### User Story 1 - ruffによるコード品質チェック (Priority: P1)

開発者として、コードをコミットする前に自動的にPythonコードの品質チェック（構文エラー、未使用import、スタイル違反）が実行されることで、品質の低いコードがリポジトリに混入することを防ぎたい。

**Why this priority**: コード品質の基盤となる機能。他のすべての開発作業に影響するため最優先。

**Independent Test**: `ruff check src/` を実行し、違反がリストアップされることで単独テスト可能。

**Acceptance Scenarios**:

1. **Given** Pythonファイルに未使用importがある, **When** `ruff check` を実行, **Then** 未使用importが警告として報告される
2. **Given** Pythonファイルに構文スタイル違反がある, **When** `ruff check` を実行, **Then** 違反箇所と修正方法が提示される
3. **Given** すべてのコードが規約に準拠している, **When** `ruff check` を実行, **Then** エラーや警告なしで完了する

---

### User Story 2 - pre-commitフックによる自動実行 (Priority: P2)

開発者として、コミット時に自動的にruffチェックとフォーマットが実行されることで、手動でチェックを忘れることなく一貫したコード品質を維持したい。

**Why this priority**: P1のruff導入を前提とし、自動化により人的ミスを防止する。

**Independent Test**: `pre-commit install` 後、意図的な違反を含むコミットを試み、フックがブロックすることで単独テスト可能。

**Acceptance Scenarios**:

1. **Given** pre-commitがインストールされている, **When** 違反を含むファイルをコミットしようとする, **Then** コミットがブロックされ違反内容が表示される
2. **Given** pre-commitがインストールされている, **When** 自動修正可能な違反を含むファイルをコミットする, **Then** ruff formatが自動的にファイルを修正する
3. **Given** すべてのファイルが規約準拠, **When** コミットを実行, **Then** 正常にコミットが完了する

---

### User Story 3 - 大規模ファイルの分割 (Priority: P3)

開発者として、600行を超えるファイルが適切に分割されることで、コードの可読性と保守性を向上させたい。

**Why this priority**: P1/P2の品質チェック基盤の上で、既存の大規模ファイルを整理する。

**Independent Test**: 分割後のファイルが600行以下であり、既存テストがすべてパスすることで単独テスト可能。

**Acceptance Scenarios**:

1. **Given** `src/ocr_ensemble.py` (699行), **When** 責務ごとに分割, **Then** 各ファイルが600行以下になる
2. **Given** `src/rover/engines.py` (613行), **When** 責務ごとに分割, **Then** 各ファイルが600行以下になる
3. **Given** ファイル分割後, **When** 既存のテストスイートを実行, **Then** すべてのテストがパスする

---

### Edge Cases

- ruffの設定ファイルがない状態でruffを実行した場合、適切なエラーメッセージを表示
- pre-commitがインストールされていない環境での動作（通常のコミットは可能）
- ファイル分割時に循環importが発生した場合の対処
- **pre-commitフック失敗時**: コマンドが非ゼロ終了コードを返した場合、コミットはブロックされエラー内容が表示される。開発者は違反を修正後、再度コミットを試みる

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムは `pyproject.toml` にruff設定を追加しなければならない
- **FR-002**: ruff設定は line-length: 120, target-version: py313 を使用しなければならない
- **FR-003**: ruff設定は E (error), F (pyflakes), I (isort), W (warning) ルールを有効化しなければならない
- **FR-004**: システムは `.pre-commit-config.yaml` を作成しなければならない
- **FR-005**: pre-commitフックは `ruff check` と `ruff format` を自動実行しなければならない
- **FR-006**: `src/ocr_ensemble.py` を責務ごとに分割し、各ファイルを600行以下にしなければならない
- **FR-007**: `src/rover/engines.py` を責務ごとに分割し、各ファイルを600行以下にしなければならない
- **FR-008**: ファイル分割後も既存のすべてのテストがパスしなければならない
- **FR-009**: ファイル分割後もすべての公開APIが維持されなければならない
- **FR-010**: 実装は以下の順序で行わなければならない: (1) ruff設定追加 → (2) 既存コードのruff違反修正 → (3) ファイル分割 → (4) pre-commit設定追加。これによりsubagent作業中にpre-commitフックが干渉しない
- **FR-011**: subagent（phase-executor, tdd-generator等）の指示を更新し、コミット前に `ruff check --fix && ruff format` を実行するようにしなければならない

### Key Entities

- **ruff設定**: line-length, target-version, 有効化ルール（E, F, I, W）を定義
- **pre-commit設定**: フック実行タイミング、使用ツール、オプションを定義
- **分割対象ファイル**: ocr_ensemble.py, rover/engines.py

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: `ruff check src/` がエラー0件で完了する
- **SC-002**: すべての `.py` ファイルが `ruff format` で変更なしの状態を維持する
- **SC-003**: コミット時にpre-commitフックが自動実行され、違反があればブロックする
- **SC-004**: `src/` 配下のすべての `.py` ファイルが600行以下になる
- **SC-005**: 既存のテストスイート（`pytest`）がすべてパスする
- **SC-006**: ファイル分割前後でpublicなクラス・関数のimportパスが変更されないか、明確なマイグレーションパスが提供される
- **SC-007**: `.claude/agents/` の指示が更新され、subagentがコミット前にruff自動修正を実行する手順が含まれる

## Clarifications

### Session 2026-02-18

- Q: pre-commitフックでコマンドが0以外の場合どうなるの？ → A: コミットがブロックされ、エラー内容が表示される。開発者は手動で修正後、再度コミットを試みる。
- Q: subagentがコミットするワークフローでpre-commitは問題にならないか？ → A: 今回は問題にならない（pre-commit設定は最終フェーズ）。次回以降のsubagent作業では、コミット前に `ruff check --fix && ruff format` を実行するよう agents/ の指示を更新する。

## Assumptions

- Python 3.13+ 環境が使用される（target-version: py313）
- 開発者は `pre-commit install` を手動で実行する必要がある
- ruffはpip経由でインストール可能
- 600行制限はIssue#12の research.md で定義された基準に基づく
- **subagentワークフローとの互換性**: 今回の実装中はpre-commitフック未有効。次回以降のsubagent作業に備え、agents/の指示に `ruff check --fix && ruff format` をコミット前に実行する手順を追加する
