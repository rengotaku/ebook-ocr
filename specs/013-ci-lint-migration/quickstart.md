# Quickstart: CI Lint Migration

## 概要

このガイドでは、コード品質チェックをpre-commitからGitHub Actions + Claude Codeフックに移行する手順を説明します。

## 前提条件

- GitHub リポジトリへのpush権限
- Claude Code v1.0+ インストール済み
- ruff, pylint インストール済み

## セットアップ手順

### 1. GitHub Actions ワークフロー作成

```bash
mkdir -p .github/workflows
```

`.github/workflows/lint.yml` を作成:

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

### 2. Claude Code フック設定

```bash
mkdir -p .claude/hooks
```

`.claude/hooks/ruff-lint.sh` を作成:

```bash
#!/bin/bash
# ruff-lint.sh - Auto-lint Python files after edits

INPUT=$(cat)
FILE_PATH=$(echo "$INPUT" | jq -r '.tool_input.file_path // empty')

# Only check Python files
if [[ "$FILE_PATH" != *.py ]]; then
  exit 0
fi

# Run ruff
if command -v ruff &> /dev/null; then
  ruff check --fix "$FILE_PATH" 2>&1 || true
  ruff format "$FILE_PATH" 2>&1 || true
fi

exit 0
```

実行権限付与:

```bash
chmod +x .claude/hooks/ruff-lint.sh
```

`.claude/settings.json` を作成:

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

### 3. pre-commit 設定削除

`.pre-commit-config.yaml` を更新（または削除）:

```yaml
# 空の設定または削除
repos: []
```

### 4. Branch Protection 設定（GitHub）

1. リポジトリ Settings → Branches
2. Branch protection rule追加 (main)
3. "Require status checks to pass before merging" 有効化
4. Status check: `lint` を選択

## 動作確認

### CIの確認

```bash
# テスト用ブランチ作成
git checkout -b test-lint-ci

# 意図的にlintエラーを含むファイル作成
echo "x=1" > test_lint.py

# コミット & プッシュ
git add test_lint.py
git commit -m "test: lint CI"
git push -u origin test-lint-ci

# PRを作成してCIが失敗することを確認
```

### Claude Code フックの確認

1. Claude Code でセッション開始
2. Pythonファイルを編集
3. 編集完了後、ruffが自動実行されることを確認

```bash
# ログで確認
# Claude Code のステータスバーまたはコンソールにruff出力が表示される
```

## トラブルシューティング

### CI が実行されない

- `.github/workflows/lint.yml` のパスを確認
- PRのbase branchがmainであることを確認
- `paths` フィルタに該当するファイルが変更されているか確認

### フックが動作しない

```bash
# 設定確認
cat .claude/settings.json

# スクリプト実行権限確認
ls -la .claude/hooks/ruff-lint.sh

# 手動テスト
echo '{"tool_input":{"file_path":"test.py"}}' | .claude/hooks/ruff-lint.sh
```

### ruff バージョン不一致

```bash
# ローカルバージョン確認
ruff --version

# pyproject.toml で固定
# [tool.ruff]
# required-version = ">=0.9.0"
```

## ロールバック

問題が発生した場合:

```bash
# pre-commit 復元
git checkout HEAD~1 -- .pre-commit-config.yaml
pre-commit install

# GitHub Actions 削除
rm .github/workflows/lint.yml

# Claude Code フック無効化
rm .claude/settings.json
```
