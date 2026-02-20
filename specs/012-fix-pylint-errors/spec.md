# Feature Specification: Pylintエラー対応

**Feature Branch**: `012-fix-pylint-errors`
**Created**: 2026-02-19
**Status**: Draft
**Input**: User description: "pylintのエラーの対応"

## 背景

pylintを導入し、コード品質チェックを実施した結果、以下の違反が検出された：

| 違反タイプ | 件数 | 制限値 |
|-----------|------|--------|
| too-many-lines | 7ファイル | 500行 |
| too-many-locals | 26箇所 | 15変数 |
| too-many-statements | 6箇所 | 50文 |
| too-many-branches | 6箇所 | 12分岐 |

### 主な違反ファイル

| ファイル | 行数 | 超過率 |
|----------|------|--------|
| src/book_converter/parser.py | 1739行 | 348% |
| src/book_converter/page_grouper.py | 1148行 | 230% |
| src/layout_ocr.py | 595行 | 119% |
| src/rover/ensemble.py | 593行 | 119% |
| src/ocr_integrated.py | 577行 | 115% |
| src/book_converter/transformer.py | 566行 | 113% |
| src/ocr_yomitoku.py | 535行 | 107% |

## User Scenarios & Testing

### User Story 1 - コードベースがpylintチェックを通過する (Priority: P1)

開発者として、`pylint`コマンドを実行した際に、設定された品質基準（`too-many-*`系ルール）に対する違反が0件であることを確認したい。これにより、コードの保守性と可読性が担保される。

**Why this priority**: コード品質の基本要件。pre-commitフックでのチェックが通らなければ、コミットができない。

**Independent Test**: `pylint --rcfile=pyproject.toml src/` を実行し、`too-many-*`系の違反が0件であることを確認する。

**Acceptance Scenarios**:

1. **Given** リファクタリング後のコードベース, **When** pylintを実行, **Then** `too-many-lines`違反が0件
2. **Given** リファクタリング後のコードベース, **When** pylintを実行, **Then** `too-many-locals`違反が0件
3. **Given** リファクタリング後のコードベース, **When** pylintを実行, **Then** `too-many-statements`違反が0件
4. **Given** リファクタリング後のコードベース, **When** pylintを実行, **Then** `too-many-branches`違反が0件

---

### User Story 2 - 既存機能が正常動作する (Priority: P1)

開発者として、リファクタリング後も既存の全機能が正常に動作することを確認したい。これにより、リファクタリングによるリグレッションを防ぐ。

**Why this priority**: 機能の維持はリファクタリングの大前提。テストが通らなければリファクタリングは失敗。

**Independent Test**: `pytest`を実行し、全テストがパスすることを確認する。

**Acceptance Scenarios**:

1. **Given** リファクタリング後のコードベース, **When** `pytest`を実行, **Then** 全テストがパス
2. **Given** リファクタリング後のコードベース, **When** `ruff check`を実行, **Then** 違反が0件

---

### User Story 3 - コードの論理的分割 (Priority: P2)

開発者として、大きなファイルが論理的に分割され、各モジュールが単一責任を持つようにしたい。これにより、コードの理解と保守が容易になる。

**Why this priority**: 分割の質がコードの保守性を決定する。適切な分割は将来の開発効率を向上させる。

**Independent Test**: 各分割後のファイルが独立した責務を持ち、他のファイルと過度に結合していないことを確認する。

**Acceptance Scenarios**:

1. **Given** 1000行超のファイル, **When** 分割後, **Then** 各ファイルが500行以下
2. **Given** 分割されたモジュール, **When** インポート関係を確認, **Then** 循環参照がない

---

### Edge Cases

- **循環インポート発生時**: 設計を見直して依存関係を整理する。解消不可能な場合のみ遅延インポート（関数内import）を許容
- **公開API変更時**: 後方互換性を維持し、変更が必要な場合はFR-007に従いドキュメント化
- **テストコードのimportパス更新**: 分割に伴いテストファイルのimport文を更新する

## Requirements

### Functional Requirements

- **FR-001**: 各Pythonファイルは500行以下でなければならない
- **FR-002**: 各関数のローカル変数は15個以下でなければならない
- **FR-003**: 各関数のステートメント数は50個以下でなければならない
- **FR-004**: 各関数の分岐数は12個以下でなければならない
- **FR-005**: リファクタリング後も既存の全テストがパスしなければならない
- **FR-006**: リファクタリング後も`ruff check`が違反0件でなければならない
- **FR-007**: 公開APIは可能な限り維持し、変更が必要な場合は明示的にドキュメント化する

### Key Entities

- **モジュール**: 単一責任を持つPythonファイル。行数500行以下。
- **関数**: 明確な目的を持つ処理単位。ローカル変数15個以下、ステートメント50個以下、分岐12個以下。
- **ヘルパーモジュール**: 共通処理を抽出した補助モジュール。

## Success Criteria

### Measurable Outcomes

- **SC-001**: `pylint --rcfile=pyproject.toml src/` の実行で `too-many-*` 系違反が0件
- **SC-002**: `pytest` の実行で全テストがパス（既存テストのカバレッジ維持）
- **SC-003**: `ruff check src/` の実行で違反が0件
- **SC-004**: `pre-commit run --all-files` が成功

## Clarifications

### Session 2026-02-19

- Q: リファクタリング作業中のpre-commitフック運用方針は？ → A: 作業中は `--no-verify` を使用し、最終フェーズでフックを有効化して検証
- Q: 循環インポートが発生した場合の対処方針は？ → A: 設計を見直して依存関係を整理する。解消不可能な場合のみ遅延インポートを許容

## Constraints

### ワークフロー制約

- **WF-001**: リファクタリング作業中のコミットは `git commit --no-verify` を使用してpre-commitフックをバイパスする
- **WF-002**: 最終フェーズで `pre-commit run --all-files` を実行し、全チェックをパスすることを確認する
- **WF-003**: PRマージ前に必ずSC-004（pre-commit成功）を満たすこと

## Assumptions

- 既存のテストスイートが十分なカバレッジを持ち、リグレッション検出に有効
- 分割の単位は論理的なまとまり（クラス、関数グループ）を基準とする
- 公開APIの変更は最小限に抑える
- パフォーマンスへの影響は考慮しない（同一ロジックの再配置のみ）

## Scope

### In Scope

- `too-many-lines` 違反のある7ファイルの分割
- `too-many-locals` 違反のある関数のリファクタリング
- `too-many-statements` 違反のある関数のリファクタリング
- `too-many-branches` 違反のある関数のリファクタリング
- 関連するテストのimportパスの更新

### Out of Scope

- 新機能の追加
- パフォーマンス最適化
- ドキュメントの追加・更新
- テストカバレッジの向上
