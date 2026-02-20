# Feature Specification: CI Lint Migration

**Feature Branch**: `013-ci-lint-migration`
**Created**: 2026-02-19
**Status**: Draft
**Input**: User description: "pylintはgitactionで行うようにしたほうが良さそう。ruffも同じ実行しても。で、ruffにかぎっては、claudecode hookベースに変更"

## 背景

現在、コード品質チェックはpre-commitフックで実行されている：
- ruff（lint + format）
- pylint（too-many-*系ルール）

この構成には以下の課題がある：
1. **ローカル開発の遅延**: コミット毎にpylint実行で待ち時間が発生
2. **バイパスの誘惑**: `--no-verify`でスキップされやすい
3. **CI未活用**: GitHub Actionsでの品質ゲートがない

## User Scenarios & Testing

### User Story 1 - CIでの品質チェック自動化 (Priority: P1)

開発者として、プルリクエスト作成時にCIでコード品質チェックが自動実行されることで、品質基準を満たさないコードがマージされることを防ぎたい。

**Why this priority**: 品質ゲートの確実な適用が主目的。CIでの実行により、ローカル設定に依存しない一貫したチェックが可能。

**Independent Test**: PRを作成し、CIワークフローがpylintとruffを実行することを確認する。

**Acceptance Scenarios**:

1. **Given** PRが作成された, **When** CIが実行される, **Then** pylintチェックが実行される
2. **Given** PRが作成された, **When** CIが実行される, **Then** ruffチェックが実行される
3. **Given** lintエラーがある, **When** CIが完了する, **Then** PRがブロックされる

---

### User Story 2 - Claude Code開発時のリアルタイムフィードバック (Priority: P2)

開発者として、Claude Codeでコード編集後にruffチェックが自動実行され、即座にフィードバックを受けたい。これにより、コミット前に問題を発見できる。

**Why this priority**: 開発体験の向上。Claude Codeフックはpre-commitより柔軟で、編集直後にフィードバックを提供できる。

**Independent Test**: Claude Codeでファイル編集後、ruffフックが実行されることを確認する。

**Acceptance Scenarios**:

1. **Given** Pythonファイルを編集, **When** 保存/編集完了, **Then** ruffチェックが自動実行される
2. **Given** ruffエラーがある, **When** フックが実行される, **Then** エラーが表示される

---

### User Story 3 - pre-commit依存の削減 (Priority: P3)

開発者として、pre-commitへの依存を最小化し、CI + Claude Codeフックで品質チェックを完結させたい。

**Why this priority**: 設定の簡素化とメンテナンス負荷軽減。複数の品質ゲートを統合。

**Independent Test**: pre-commit設定からruff/pylintを削除し、CI + フックで品質が維持されることを確認する。

**Acceptance Scenarios**:

1. **Given** pre-commitからlintが削除された, **When** コミット, **Then** コミットがブロックされない
2. **Given** CIとフックが設定済み, **When** 品質違反がある, **Then** CIまたはフックで検出される

---

### Edge Cases

- **CIがタイムアウトした場合**: 再実行可能な設計にする
- **Claude Codeフックが無効な場合**: CIで最終的にキャッチされる
- **ローカルとCIでruffバージョンが異なる場合**: バージョン固定で対応

## Requirements

### Functional Requirements

- **FR-001**: GitHub ActionsワークフローでPR作成時にpylintを実行する
- **FR-002**: GitHub ActionsワークフローでPR作成時にruff checkを実行する
- **FR-003**: GitHub ActionsワークフローでPR作成時にruff formatチェックを実行する
- **FR-004**: Claude Codeフックでファイル編集後にruffを実行する
- **FR-005**: pre-commit設定からpylintとruffを削除する
- **FR-006**: CIでのlint失敗時にPRマージをブロックする

## Success Criteria

### Measurable Outcomes

- **SC-001**: PRでCIが自動実行され、lint結果が表示される
- **SC-002**: lint違反のあるPRがマージ不可になる
- **SC-003**: Claude Codeでのファイル編集後5秒以内にruffフィードバックが表示される
- **SC-004**: pre-commit実行時間が短縮される（lint除去分）

## Assumptions

- GitHub Actionsが利用可能
- Claude Code v1.0+でフック機能が利用可能
- ruff/pylintのバージョンはpyproject.tomlで管理される
- mainブランチへの直接pushは禁止されている（PRワークフロー前提）

## Scope

### In Scope

- GitHub Actionsワークフロー作成（lint.yml）
- Claude Codeフック設定（python-lint.sh）
- pre-commit設定からのlint削除
- 設定ファイルの更新（pyproject.toml依存維持）

### Out of Scope

- pytestのCI化（別issue）
- デプロイワークフロー
- セキュリティスキャン（別issue）
- pre-commit自体の完全削除（他のフックが残る可能性）
