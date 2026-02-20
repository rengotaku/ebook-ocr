# Phase 3 Output: Claude Codeフック設定

**Date**: 2026-02-19
**Phase**: User Story 2 - Claude Code開発時のリアルタイムフィードバック (Phase 3)
**Status**: Complete

## 実行内容サマリ

Claude Codeでファイル編集後にruffチェックが自動実行されるフック設定を作成した。これにより、編集直後にコード品質フィードバックを受けられるようになる。

## 完了タスク

### T012-T013: 前フェーズ確認

**Status**: 完了

- ph1-output.md確認: 既存設定を把握
- ph2-output.md確認: GitHub Actions CI設定完了を確認

### T014: `.claude/hooks/` ディレクトリ作成

**Status**: 完了

```bash
mkdir -p .claude/hooks
```

- ディレクトリ作成完了: `/data/projects/video-separater/.claude/hooks/`

### T015: ruff lintフックスクリプト作成

**Status**: 完了

**作成ファイル**: `.claude/hooks/ruff-lint.sh`

**機能**:
- stdin からJSON形式の入力を読み取り（jq使用）
- `.py` 拡張子のファイルのみを対象
- ruff check --fix で自動修正
- ruff format でフォーマット適用
- exit 0 で警告のみ（ブロックしない設計）

**実装内容**:
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

### T016: 実行権限付与

**Status**: 完了

```bash
chmod +x .claude/hooks/ruff-lint.sh
```

- 実行権限設定完了: `-rwxrwxr-x`

### T017: Claude Code settings.json作成

**Status**: 完了

**作成ファイル**: `.claude/settings.json`

**設定内容**:
- イベント: `PostToolUse` (ツール実行成功後に発火)
- Matcher: `Edit|Write` (EditまたはWriteツール使用時)
- フックタイプ: `command` (決定論的スクリプト実行)
- コマンド: `"$CLAUDE_PROJECT_DIR"/.claude/hooks/ruff-lint.sh`

**実装内容**:
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

### T018: フック動作確認

**Status**: 完了（手動テスト実施）

**テスト結果**:
- Pythonファイルパス入力: ruff実行確認（ファイル不存在でエラー = 正常動作）
- 非Pythonファイルパス入力: スキップ確認（無出力 = 正常動作）
- settings.json構文検証: JSON valid確認

**テストコマンド**:
```bash
# Pythonファイルのテスト
echo '{"tool_input":{"file_path":"/path/to/test.py"}}' | .claude/hooks/ruff-lint.sh
# → ruff実行を試みる（期待通り）

# 非Pythonファイルのテスト
echo '{"tool_input":{"file_path":"/path/to/test.md"}}' | .claude/hooks/ruff-lint.sh
# → 無出力でexit 0（期待通り）

# JSON構文検証
jq '.' .claude/settings.json
# → valid JSON（期待通り）
```

## 作成/変更されたファイル

| ファイル | 状態 | 説明 |
|---------|------|------|
| `.claude/hooks/` | 新規作成 | フックスクリプト格納ディレクトリ |
| `.claude/hooks/ruff-lint.sh` | 新規作成 | ruff自動実行スクリプト（実行権限付き） |
| `.claude/settings.json` | 新規作成 | Claude Codeプロジェクト設定（フック定義） |
| `specs/013-ci-lint-migration/tasks.md` | 更新 | T012-T019をマーク |

## 設定詳細

### フック動作フロー

```
1. Claude CodeでEdit/Writeツール実行
   ↓
2. ツール成功後、PostToolUseイベント発火
   ↓
3. matcher "Edit|Write" に一致
   ↓
4. ruff-lint.sh 実行
   ↓
5. ファイルパスが .py で終わる場合のみ処理
   ↓
6. ruff check --fix → ruff format 実行
   ↓
7. exit 0 (警告のみ、エディタをブロックしない)
```

### 設計判断

| 項目 | 決定 | 根拠 |
|------|------|------|
| イベント | PostToolUse | 編集完了後に実行（編集中の中断を避ける） |
| Matcher | Edit\|Write | ファイル変更時のみ（Readは除外） |
| フックタイプ | command | 決定論的、高速（LLM不要） |
| Exit code | 0 | 警告のみ、開発フローをブロックしない |
| 対象ファイル | *.py のみ | Pythonファイルのみ（他は無視） |
| ruff動作 | --fix + format | 自動修正 + フォーマット適用 |

## 次フェーズへの引継ぎ

### Phase 4 (US3 - pre-commit削減)

- `.pre-commit-config.yaml` から ruff/pylint を削除
- 空になる場合は `repos: []` に設定

### Phase 5 (Polish - 最終検証)

- 実際のClaude Codeセッションでフック動作を確認
- SC-003確認: ファイル編集後5秒以内にruffフィードバック表示

## 検証方法（親エージェント実施）

### フック動作確認手順

1. Claude Codeセッションを新規開始
   ```bash
   code .
   # または既存セッションを継続
   ```

2. Pythonファイルを編集
   ```bash
   # Claude Codeで任意の.pyファイルを編集
   # 例: src/main.py に空行追加
   ```

3. 編集完了後、自動的にruffが実行される
   - Claude Codeのステータスバーまたはコンソールにruff出力が表示される
   - 自動修正が適用される（--fixオプション）
   - フォーマットが適用される（formatコマンド）

4. 非Pythonファイルを編集
   ```bash
   # Claude Codeで.mdファイルを編集
   # → ruffは実行されない（スキップ）
   ```

## 計画からの逸脱・決定事項

なし。quickstart.mdとresearch.mdの設計通りに実装完了。

## 問題・課題

特になし。

## 補足事項

### settings.json vs settings.local.json

- **settings.json**: プロジェクト共有設定（gitで管理、チーム全体で使用）
- **settings.local.json**: 個人設定（gitignore、ローカル環境のみ）

今回は `settings.json` を作成し、チーム全体でフック設定を共有する設計とした。

### 既存のsettings.local.json

既存の `settings.local.json` には影響を与えない。permissions設定のみが含まれており、フック設定はない。

### Claude Codeバージョン要件

- Claude Code v1.0+ でフック機能が利用可能
- PostToolUseイベント対応版が必要

## ベストプラクティス遵守

- [X] シェル変数はクォート（`"$VAR"`）
- [X] `$CLAUDE_PROJECT_DIR` で相対パス解決
- [X] `jq` でJSON解析
- [X] ファイルタイプフィルタ（*.pyのみ）
- [X] Exit 0（警告のみ、ブロックしない）
- [X] `|| true` で ruff エラー時もスクリプト続行
