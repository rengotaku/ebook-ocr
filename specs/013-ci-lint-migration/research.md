# Research: CI Lint Migration

**Date**: 2026-02-19
**Branch**: `013-ci-lint-migration`

## 調査項目

1. Claude Code フック機能
2. GitHub Actions lint ワークフロー
3. pre-commit 削減の影響

---

## 1. Claude Code フック機能

### フック設定構造

```json
{
  "hooks": {
    "EventName": [
      {
        "matcher": "pattern",
        "hooks": [
          {
            "type": "command",
            "command": "script.sh"
          }
        ]
      }
    ]
  }
}
```

### 設定ファイルの優先順位

| スコープ | ファイル | 用途 |
|----------|----------|------|
| Managed | `managed-settings.json` | 組織全体 |
| User | `~/.claude/settings.json` | 全プロジェクト |
| **Project** | `.claude/settings.json` | **単一プロジェクト（共有可）** |
| Local | `.claude/settings.local.json` | 単一プロジェクト（gitignore） |

### フックタイプ

| タイプ | 用途 |
|--------|------|
| `command` | シェルスクリプト実行（決定論的） |
| `prompt` | LLMベース単発判断（Haiku） |
| `agent` | LLMベースマルチターン（ツール使用可） |

### イベント一覧

| イベント | 発火タイミング | Matcher |
|----------|---------------|---------|
| `PostToolUse` | ツール成功後 | ツール名 (`Edit`, `Write`) |
| `PreToolUse` | ツール実行前（ブロック可） | ツール名 |
| `SessionStart` | セッション開始 | 起動方法 |
| `Stop` | 応答完了 | なし |

### ruffフックに最適な設定

**推奨**: `PostToolUse` + `Edit|Write` matcher

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Edit|Write",
        "hooks": [
          {
            "type": "command",
            "command": "\"$CLAUDE_PROJECT_DIR\"/.claude/hooks/ruff-lint.sh"
          }
        ]
      }
    ]
  }
}
```

### フックスクリプト構造

```bash
#!/bin/bash
# ruff-lint.sh

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Pythonファイルのみ対象
if [[ "$FILE_PATH" != *.py ]]; then
  exit 0
fi

# ruff実行
ruff check --fix "$FILE_PATH" 2>&1
ruff format "$FILE_PATH" 2>&1

exit 0  # 警告のみ、ブロックしない
```

### ベストプラクティス

| プラクティス | 詳細 |
|-------------|------|
| `$CLAUDE_PROJECT_DIR` | プロジェクトルートからの相対パス |
| シェル変数はクォート | `"$VAR"` でスペース対応 |
| Exit 0 | 警告のみ、ブロックしない |
| Exit 2 | ブロック（stderrがフィードバック） |
| `jq` でJSON解析 | 入力はJSON形式 |
| ファイルタイプフィルタ | 不要なファイルはスキップ |

---

## 2. GitHub Actions lint ワークフロー

### 推奨構成

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

      - name: Install dependencies
        run: |
          pip install ruff pylint
          pip install -r requirements.txt

      - name: Run ruff check
        run: ruff check src/ tests/

      - name: Run ruff format check
        run: ruff format --check src/ tests/

      - name: Run pylint
        run: pylint --rcfile=pyproject.toml src/
```

### Branch Protection

- **Required status checks**: `lint` job を必須に
- **Require branches to be up to date**: オプション

---

## 3. pre-commit 削減の影響

### 現状

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.9.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format

  - repo: https://github.com/pylint-dev/pylint
    rev: v3.3.4
    hooks:
      - id: pylint
        args: [--rcfile=pyproject.toml]
        files: ^src/.*\.py$
```

### 削減後

```yaml
repos: []
# または .pre-commit-config.yaml 自体を削除
```

### 影響分析

| 観点 | 現状（pre-commit） | 変更後（CI + hook） |
|------|-------------------|-------------------|
| ローカル即時フィードバック | ✅ コミット時 | ✅ 編集時（Claude Code） |
| バイパス防止 | ⚠️ --no-verify可 | ✅ CIで強制 |
| 実行速度 | ❌ コミット遅延 | ✅ 非同期 |
| 設定複雑度 | Medium | Low |

---

## 決定事項

| 項目 | 決定 | 根拠 |
|------|------|------|
| Claude Code フック設定先 | `.claude/settings.json` | プロジェクト共有可 |
| フックイベント | `PostToolUse` | 編集完了後に実行 |
| フックタイプ | `command` | 決定論的、高速 |
| CI トリガー | `pull_request` | PR品質ゲート |
| pre-commit | 全削除 | CI + hookで代替 |

## 代替案の検討

| 代替案 | 評価 | 採用/却下理由 |
|--------|------|--------------|
| pre-commit維持 + CI追加 | ⚠️ 部分採用 | 重複実行、設定複雑化 |
| CIのみ（hook なし） | ❌ 却下 | 即時フィードバックなし |
| GitHub App (super-linter等) | ❌ 却下 | 設定の自由度低下 |
