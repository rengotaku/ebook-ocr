# Implementation Plan: GitHub Actions Lint CI

**Branch**: `017-github-actions-lint` | **Date**: 2026-02-24 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/017-github-actions-lint/spec.md`

## Summary

既存の `.github/workflows/lint.yml` を更新し、main ブランチへの push トリガーを追加。Makefile に `lint`, `ruff`, `pylint` ターゲットを追加し、ローカルと CI で同一コマンドを実行することで結果の一致を保証する。

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: ruff (既存), pylint (既存)
**Storage**: N/A
**Testing**: pytest (既存)
**Target Platform**: GitHub Actions (ubuntu-latest)
**Project Type**: single (video-separater pipeline)
**Performance Goals**: CI 完了 5 分以内
**Constraints**: pip キャッシュ利用
**Scale/Scope**: 単一リポジトリ

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Pipeline-First | ✅ Pass | CI は開発パイプラインの一部 |
| II. Test-First | ⚠️ N/A | CI 設定ファイルにユニットテストは不要 |
| III. Ollama Integration | ✅ N/A | lint CI は Ollama 不使用 |
| IV. Immutability | ✅ N/A | CI 設定には適用外 |
| V. Simplicity (YAGNI) | ✅ Pass | 最小限の変更で要件を満たす |

**Gate Result**: ✅ PASS

## Project Structure

### Documentation (this feature)

```text
specs/017-github-actions-lint/
├── spec.md              # Feature specification
├── plan.md              # This file
├── research.md          # Phase 0 output
└── tasks.md             # Phase 2 output (/speckit.tasks command)
```

### Source Code (repository root)

```text
.github/
└── workflows/
    └── lint.yml         # UPDATE: Add push trigger, use Makefile targets

Makefile                 # UPDATE: Add ruff, pylint, lint targets
```

**Structure Decision**: 既存のプロジェクト構造を維持。GitHub Actions ワークフローと Makefile の更新のみ。

## Complexity Tracking

N/A - 単純な CI 更新、複雑性なし

---

## Phase 0: Research

### Current State Analysis

#### 1. 既存の lint.yml

```yaml
# 現状
on:
  pull_request:
    branches: [main]
    paths:
      - 'src/**/*.py'
      - 'tests/**/*.py'
      - 'pyproject.toml'

# 問題点
# - push トリガーがない (FR-003 未対応)
# - Makefile を使用していない (FR-007 未対応)
```

#### 2. 既存の pyproject.toml

```toml
# ruff 設定 (既存)
[tool.ruff]
line-length = 120
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "W"]

# pylint 設定 (既存)
[tool.pylint.main]
disable = "all"
enable = [
    "too-many-lines",
    "too-many-arguments",
    "too-many-locals",
    "too-many-statements",
    "too-many-branches",
]

[tool.pylint.design]
max-module-lines = 500
max-args = 7
max-locals = 15
max-statements = 50
max-branches = 12
```

#### 3. 既存の Makefile

- `make lint` ターゲットが存在しない
- ruff/pylint の個別ターゲットなし

### Research Findings

#### 1. GitHub Actions Best Practices

**Decision**: `actions/setup-python@v5` の `cache: 'pip'` オプションを使用

**Rationale**:
- ビルトイン機能で追加設定不要
- requirements.txt と pyproject.toml のハッシュを自動でキーに使用

#### 2. Workflow Structure

**Decision**: ruff と pylint を並列ジョブとして実行

**Rationale**:
- 各 linter の結果が個別に確認可能 (FR-008)
- 片方が失敗しても他方は完了まで実行
- 並列実行で CI 時間短縮

#### 3. Makefile Integration

**Decision**: Makefile ターゲットを作成し、CI からも使用

**Rationale**:
- ローカルと CI で同一コマンド実行 (FR-007)
- `make lint` で両方実行、`make ruff`/`make pylint` で個別実行

---

## Phase 1: Design

### Workflow Design

```yaml
# .github/workflows/lint.yml (更新後)
name: Lint

on:
  push:
    branches: [main]  # NEW: main push trigger
  pull_request:
    branches: [main]

jobs:
  ruff:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'
          cache: 'pip'
          cache-dependency-path: |
            requirements.txt
            pyproject.toml
      - name: Install dependencies
        run: pip install ruff
      - name: Run ruff
        run: make ruff

  pylint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'
          cache: 'pip'
          cache-dependency-path: |
            requirements.txt
            pyproject.toml
      - name: Install dependencies
        run: |
          pip install pylint
          pip install -r requirements.txt
      - name: Run pylint
        run: make pylint
```

### Makefile Design

```makefile
# === Linting ===

ruff: ## Run ruff linter
	ruff check src/ tests/
	ruff format --check src/ tests/

pylint: ## Run pylint static analysis
	pylint --rcfile=pyproject.toml src/

lint: ruff pylint ## Run all linters (ruff + pylint)
```

### Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| 並列ジョブ | ruff/pylint が個別に確認可能、CI 時間短縮 |
| Makefile 統合 | ローカル/CI の一貫性確保 |
| paths フィルタ削除 | main push 時は常に実行、PR 時も全チェック |
| fail-under 削除 | 既存コードが基準を満たさない可能性があるため |

---

## Implementation Phases

### Phase 1: Makefile Targets

1. `ruff` ターゲット作成
2. `pylint` ターゲット作成
3. `lint` ターゲット作成（ruff + pylint）
4. ローカルで `make ruff`, `make pylint`, `make lint` 動作確認

### Phase 2: GitHub Actions Workflow

1. lint.yml に push トリガー追加
2. paths フィルタ削除（常に実行）
3. Makefile ターゲット使用に変更
4. ruff/pylint を並列ジョブに分離

### Phase 3: Polish

1. 既存の lint エラーがあれば修正（または警告レベルに調整）
2. PR 作成して CI 動作確認
3. CLAUDE.md 更新

---

## Risk Assessment

| Risk | Impact | Mitigation |
|------|--------|------------|
| pylint が既存コードで大量エラー | Medium | fail-under オプションなしで警告のみ |
| CI 時間超過 (5分) | Low | 並列ジョブで高速化済み |
| ローカルと CI でバージョン不一致 | Low | requirements.txt でバージョン固定 |

---

## Next Steps

```
/speckit.tasks
```
