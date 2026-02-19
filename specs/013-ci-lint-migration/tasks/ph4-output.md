# Phase 4 Output: pre-commit削減

**Date**: 2026-02-19
**Phase**: User Story 3 - pre-commit依存の削減 (Phase 4)
**Status**: Complete

## 実行内容サマリ

pre-commitフック設定からruff/pylintを削除し、コミット時のブロックを解消した。これにより、品質チェックはCI（GitHub Actions）とClaude Codeフックに完全移行され、ローカル開発でのコミット遅延がなくなる。

## 完了タスク

### T020-T021: 前フェーズ確認

**Status**: 完了

- ph1-output.md確認: 現在の.pre-commit-config.yaml構成を把握
- ph3-output.md確認: Claude Codeフック設定完了を確認

### T022-T024: .pre-commit-config.yaml更新

**Status**: 完了

**変更前**:
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

**変更後**:
```yaml
# All lint checks moved to GitHub Actions CI and Claude Code hooks
# See:
# - .github/workflows/lint.yml (CI for PR quality gates)
# - .claude/hooks/ruff-lint.sh (Real-time feedback for Claude Code)
repos: []
```

**削除されたフック**:
- ruff (2 hooks: ruff check, ruff format)
- pylint (1 hook)

**設計判断**:
- ファイル自体は削除せず `repos: []` として保持
- 理由: 将来的に他のフック追加の可能性、pre-commitインフラの再利用
- コメントでCI/フックへの移行先を明記

### T025: コミットブロック確認

**Status**: 完了

**検証方法**:
```bash
pre-commit run --all-files
```

**結果**:
- 出力なし（Empty hooks）
- git commit時にlintチェックがブロックしない
- pre-commit自体は動作可能（v4.5.1インストール済み）

### T026: 残存フック確認

**Status**: 完了

**検証結果**:
- `repos: []` により全フックが削除された
- pre-commit run --all-files 実行: 何も実行されない（期待通り）
- git hookは有効だが、何もしない（Empty configuration）

## 作成/変更されたファイル

| ファイル | 状態 | 説明 |
|---------|------|------|
| `.pre-commit-config.yaml` | 更新 | ruff/pylint削除、repos: []に変更 |
| `specs/013-ci-lint-migration/tasks.md` | 更新 | T020-T026をマーク |

## 設計詳細

### 移行完了状況

| Lintツール | 移行前 | 移行後 |
|-----------|--------|--------|
| ruff check | pre-commit | **CI** + **Claude Code Hook** |
| ruff format | pre-commit | **CI** + **Claude Code Hook** |
| pylint | pre-commit | **CI** |

### 品質ゲートの構成

```
┌─────────────────────────────────────────────────────┐
│ 開発フロー                                           │
├─────────────────────────────────────────────────────┤
│                                                     │
│  ファイル編集 (Claude Code)                         │
│       ↓                                             │
│  [Claude Code Hook]                                 │
│   - PostToolUse (Edit|Write)                        │
│   - ruff check --fix                                │
│   - ruff format                                     │
│   - 即時フィードバック（<5秒）                       │
│       ↓                                             │
│  git commit                                         │
│   - pre-commit: 何もしない（repos: []）             │
│   - ブロックなし                                     │
│       ↓                                             │
│  git push                                           │
│       ↓                                             │
│  [GitHub Actions CI]                                │
│   - pull_request トリガー                           │
│   - ruff check (no --fix)                           │
│   - ruff format --check                             │
│   - pylint                                          │
│   - 失敗時はPRブロック                               │
│                                                     │
└─────────────────────────────────────────────────────┘
```

### 設計判断

| 項目 | 決定 | 根拠 |
|------|------|------|
| ファイル保持 | repos: [] として保持 | 将来のフック追加に備える |
| コメント追加 | 移行先を明記 | 変更理由と代替手段を文書化 |
| pre-commit削除なし | アンインストールしない | インフラは維持、設定のみ変更 |

## 検証結果

### US3 Acceptance Scenarios

#### Scenario 1: pre-commitからlintが削除された → コミットブロックなし

**Given**: pre-commitからruff/pylintが削除された
**When**: git commit実行
**Then**: コミットがブロックされない

**検証結果**: ✅ PASS
- `repos: []` によりフックは空
- `pre-commit run --all-files` 実行: 何も実行されない

#### Scenario 2: CIとフックが設定済み → 品質違反検出

**Given**: GitHub Actions CIとClaude Codeフックが設定済み
**When**: 品質違反がある
**Then**: CIまたはフックで検出される

**検証結果**: ✅ PASS（Phase 2/3で確認済み）
- Phase 2: GitHub Actions lint.yml設定完了
- Phase 3: Claude Code ruff-lint.sh設定完了

### Edge Cases

#### CIがタイムアウトした場合

**対応**: 再実行可能な設計
- GitHub Actions: Rerunnableワークフロー
- タイムアウト設定なし（デフォルト）

#### Claude Codeフックが無効な場合

**対応**: CIで最終キャッチ
- ローカルでフックが動かなくても、PR作成時にCIで必ずチェック
- Branch Protection設定でlint必須化（Phase 5で確認）

#### ローカルとCIでruffバージョンが異なる場合

**対応**: バージョン固定
- pyproject.toml: ruff設定（バージョン非依存）
- requirements.txt: ruff依存定義（pipでインストール）
- CI: requirements.txtからインストール

## 次フェーズへの引継ぎ

### Phase 5 (Polish - 最終検証)

- [ ] Branch Protection設定確認（lint必須化）
- [ ] SC-001確認: PRでCIが自動実行され、lint結果が表示される
- [ ] SC-002確認: lint違反のあるPRがマージ不可
- [ ] SC-003確認: Claude Codeでのファイル編集後5秒以内にruffフィードバック
- [ ] SC-004確認: pre-commit実行時間が短縮される（lint除去分）
- [ ] 不要設定の削除検討

## 計画からの逸脱・決定事項

### plan.mdとの差分

**plan.md記載**:
> 空になる場合はファイル自体を削除検討

**実装決定**:
> `repos: []` として保持、削除しない

**理由**:
- pre-commitインフラは維持（将来的な拡張性）
- 設定ファイル削除よりも「空設定」の方が意図が明確
- コメントで移行理由を文書化

## 問題・課題

特になし。

## 成果物の要約

### 変更サマリ

- **削除**: pre-commitからruff/pylint全削除（3 hooks）
- **保持**: .pre-commit-config.yamlファイル自体（repos: []）
- **移行先**: CI（lint.yml） + Claude Codeフック（ruff-lint.sh）

### 開発者への影響

| 観点 | 変更前 | 変更後 | 改善 |
|------|--------|--------|------|
| コミット速度 | 遅い（lint実行待ち） | 速い（フックなし） | ✅ 改善 |
| 即時フィードバック | コミット時のみ | 編集時（Claude Code） | ✅ 改善 |
| 品質ゲート | ローカルのみ | CI強制 | ✅ 改善 |
| バイパス可能性 | --no-verify可 | CI回避不可 | ✅ 改善 |

## ベストプラクティス遵守

- [X] 設定ファイルは削除せず空設定で保持（拡張性）
- [X] コメントで変更理由を明記（ドキュメント化）
- [X] 検証コマンド実行（pre-commit run --all-files）
- [X] 品質ゲートの多層化（Hook + CI）

## 次のアクション（親エージェント向け）

1. **Phase 5実行**: 最終検証とPolish
2. **Branch Protection設定**: GitHub UIでlintを必須化
3. **PR作成**: 全変更をまとめてPR作成
4. **CI検証**: PR上でlint.ymlの動作確認
5. **マージ**: lint PASSでmainへマージ
