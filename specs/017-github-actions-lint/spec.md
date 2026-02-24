# Feature Specification: GitHub Actions Lint CI

**Feature Branch**: `017-github-actions-lint`
**Created**: 2026-02-24
**Status**: Draft
**Input**: GitHub Issue #26 - Add GitHub Actions for Lint (ruff + pylint)

## User Scenarios & Testing *(mandatory)*

### User Story 1 - PRのlintチェック自動実行 (Priority: P1)

開発者がPRを作成または更新すると、GitHub Actionsが自動的にlintチェック（ruff + pylint）を実行し、結果がPRのステータスとして表示される。これにより、コードレビュー前にコード品質の問題を検出できる。

**Why this priority**: PRレビューの品質向上が本機能の主目的であり、最も頻繁に使用されるフロー。pre-commitをバイパスしたコードがマージされることを防ぐ最重要機能。

**Independent Test**: PRを作成し、lintエラーを含むコードをpushして、CIが失敗ステータスを返すことを確認する。

**Acceptance Scenarios**:

1. **Given** lintエラーを含むブランチがある, **When** そのブランチからPRを作成する, **Then** CIが自動実行され、失敗ステータスがPRに表示される
2. **Given** lintエラーのないブランチがある, **When** そのブランチからPRを作成する, **Then** CIが自動実行され、成功ステータスがPRに表示される
3. **Given** 既存のPRがある, **When** 新しいコミットをpushする, **Then** CIが再度自動実行される

---

### User Story 2 - mainブランチの品質保証 (Priority: P2)

mainブランチにコードがpushされると、GitHub Actionsが自動的にlintチェックを実行する。これにより、マージ後のコード品質を継続的に監視できる。

**Why this priority**: mainブランチの品質保証は重要だが、PRでのチェックが通っていれば通常は問題ない。バックアップ的な役割。

**Independent Test**: mainブランチに直接pushし、CIが自動実行されることを確認する。

**Acceptance Scenarios**:

1. **Given** mainブランチがある, **When** 新しいコミットがmainにpushされる, **Then** CIが自動実行される
2. **Given** lintエラーを含むコードがmainにpushされた, **When** CIが実行される, **Then** 失敗ステータスが記録される

---

### User Story 3 - ローカルとCIの一貫性 (Priority: P3)

開発者がローカルで`make lint`を実行すると、CIと同じlintチェックが実行される。これにより、ローカルで事前にCIの結果を確認でき、PRの失敗を防げる。

**Why this priority**: 開発者体験の向上。ローカルで事前確認できることで、CI失敗によるフィードバックループを短縮。

**Independent Test**: ローカルで`make lint`を実行し、同じコードでCIを実行して結果が一致することを確認する。

**Acceptance Scenarios**:

1. **Given** lintエラーを含むコードがある, **When** ローカルで`make lint`を実行する, **Then** CIと同じエラーが報告される
2. **Given** lintエラーのないコードがある, **When** ローカルで`make lint`を実行する, **Then** CIと同様に成功する

---

### Edge Cases

- CIジョブがタイムアウトした場合、明確なエラーメッセージが表示される
- ruffまたはpylintのどちらか一方のみが失敗した場合、両方の結果が個別に確認できる
- 大量のファイル変更があった場合でも、制限時間内にチェックが完了する
- ネットワーク障害でpipインストールが失敗した場合、適切にリトライまたはエラー報告される

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: システムは、PRの作成時にlint CIを自動トリガーしなければならない
- **FR-002**: システムは、PRの更新（新しいコミットのpush）時にlint CIを自動トリガーしなければならない
- **FR-003**: システムは、mainブランチへのpush時にlint CIを自動トリガーしなければならない
- **FR-004**: システムは、ruffによるlintチェックを実行しなければならない
- **FR-005**: システムは、pylintによる静的解析を実行しなければならない
- **FR-006**: システムは、CIの結果をPRのステータスチェックとして表示しなければならない
- **FR-007**: `make lint`コマンドは、CIと同じlintチェックを実行しなければならない
- **FR-008**: システムは、ruffとpylintの結果を個別に確認できる形式で出力しなければならない
- **FR-009**: システムは、エラー発生時にエラー修正に必要な情報（ファイル名、行番号、エラー内容）をログに出力しなければならない
- **FR-010**: システムは、pipキャッシュを利用して依存関係のインストール時間を短縮しなければならない

### Key Entities

- **Workflow**: GitHub Actionsのワークフロー定義。トリガー条件、ジョブ、ステップを含む
- **Linter**: コード品質チェックツール（ruff、pylint）。それぞれ独立した結果を出力
- **Status Check**: PRに表示されるCI結果。成功/失敗のステータスとログへのリンクを含む

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: lintエラーがあるコードをPRに含めた場合、100%の確率でCIが失敗ステータスを返す
- **SC-002**: lintチェックが5分以内に完了する
- **SC-003**: ローカルの`make lint`とCIの結果が100%一致する
- **SC-004**: CIログから、エラー修正に必要な情報（ファイル名、行番号、エラー内容）が取得できる
- **SC-005**: ruffとpylintの結果が個別のステップとして確認できる

## Assumptions

- プロジェクトは既にruffの設定（pyproject.toml）を持っている
- pylintの設定は新規追加または既存の設定を利用する
- Python 3.13+環境で実行される
- GitHub Actionsの標準的なUbuntuランナーを使用する
- pipキャッシュはGitHub Actionsの標準キャッシュ機能を利用する

## References

- GitHub Issue #26: Add GitHub Actions for Lint (ruff + pylint)
- obsidian-importerプロジェクトの実装: `specs/061-github-actions-lint/`
