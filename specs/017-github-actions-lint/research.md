# Research: GitHub Actions Lint CI

**Date**: 2026-02-24
**Feature**: 017-github-actions-lint

## Research Tasks

1. 既存実装の分析
2. GitHub Actions best practices for Python linting
3. Makefile integration strategy

---

## 1. 既存実装の分析

### 現状の lint.yml

```yaml
name: Lint

on:
  pull_request:
    branches: [main]
    paths:
      - 'src/**/*.py'
      - 'tests/**/*.py'
      - 'pyproject.toml'

jobs:
  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'
          cache: 'pip'
      - name: Install dependencies
        run: |
          pip install ruff pylint
          pip install -r requirements.txt
      - name: Run ruff check
        run: ruff check src/ tests/
      - name: Run ruff format check
        run: ruff format --check src/ tests/
      - name: Run pylint
        run: pylint --rcfile=pyproject.toml --fail-under=9.9 src/
```

### 問題点

| 要件 | 現状 | 対応 |
|------|------|------|
| FR-001: PR 作成時トリガー | ✅ 対応済み | - |
| FR-002: PR 更新時トリガー | ✅ 対応済み | - |
| FR-003: main push トリガー | ❌ 未対応 | `push` トリガー追加 |
| FR-007: make lint | ❌ 未対応 | Makefile ターゲット追加 |
| FR-008: 個別結果確認 | ⚠️ 部分対応 | 並列ジョブに分離 |

---

## 2. GitHub Actions Best Practices

### Decision: 並列ジョブ構成

**Rationale**:
- ruff と pylint を別ジョブで実行
- 片方が失敗しても他方は完了まで実行
- GitHub UI で個別の結果が確認可能

**Alternatives considered**:
- 単一ジョブで順次実行 → 結果が混在して確認しづらい
- matrix strategy → 同じツールの複数バージョン向け、今回は不要

### Decision: actions/setup-python の cache 機能

**Rationale**:
- `cache: 'pip'` オプションで pip キャッシュ自動管理
- `cache-dependency-path` で requirements.txt と pyproject.toml を指定
- 別途 `actions/cache` を使う必要なし

**Key configuration**:
```yaml
- uses: actions/setup-python@v5
  with:
    python-version: '3.13'
    cache: 'pip'
    cache-dependency-path: |
      requirements.txt
      pyproject.toml
```

---

## 3. Makefile Integration Strategy

### Decision: 3 つのターゲットを作成

```makefile
ruff:     # ruff check + format check
pylint:   # pylint 静的解析
lint:     # ruff + pylint 両方実行
```

**Rationale**:
- ローカルと CI で同じコマンドを実行
- 個別実行と一括実行の両方に対応
- CI では `make ruff` と `make pylint` を並列実行

**Alternatives considered**:
- シェルスクリプト → Makefile の方がプロジェクト標準に合致
- 直接コマンド実行 → ローカル/CI の一貫性が保てない

---

## 4. pylint fail-under 設定

### Decision: fail-under オプションを削除

**Rationale**:
- 既存コードが 9.9 スコアを満たさない可能性
- 段階的に品質向上を目指す
- 最初は警告として表示、後で fail-under を導入

**Current pylint config** (pyproject.toml):
```toml
[tool.pylint.main]
disable = "all"
enable = [
    "too-many-lines",
    "too-many-arguments",
    "too-many-locals",
    "too-many-statements",
    "too-many-branches",
]
```

既存設定は ruff と重複しないサイズ制限系のみ有効化しており、妥当。

---

## Summary

| Topic | Decision | Rationale |
|-------|----------|-----------|
| ジョブ構成 | 並列（ruff/pylint 別ジョブ） | 個別結果確認、CI 時間短縮 |
| キャッシュ | setup-python の cache: 'pip' | ビルトイン機能、追加設定不要 |
| Makefile | 3 ターゲット作成 | ローカル/CI 一貫性 |
| fail-under | 削除 | 段階的品質向上 |
