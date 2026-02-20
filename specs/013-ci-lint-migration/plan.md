# Implementation Plan: CI Lint Migration

**Branch**: `013-ci-lint-migration` | **Date**: 2026-02-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/013-ci-lint-migration/spec.md`

## Summary

pylint/ruffのコード品質チェックをpre-commitからGitHub Actions CIに移行し、ruffについてはClaude Codeフックでリアルタイムフィードバックも提供する。これにより、ローカル開発の遅延を解消しつつ、PRレベルでの品質ゲートを確保する。

## Technical Context

**Language/Version**: YAML（GitHub Actions）, Bash（hooks）
**Primary Dependencies**: ruff, pylint（既存）, GitHub Actions
**Storage**: N/A
**Testing**: 手動検証（CI実行確認、フック動作確認）
**Target Platform**: GitHub Actions（ubuntu-latest）, Claude Code v1.0+
**Project Type**: DevOps/設定ファイル
**Performance Goals**: ruffフック実行 <5秒
**Constraints**: GitHub Actionsの無料枠内、mainブランチ保護
**Scale/Scope**: 設定ファイル4件（workflow, hook, settings, pre-commit）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Note |
|-----------|--------|------|
| I. Pipeline-First | ✅ N/A | 設定ファイルのみ、パイプライン影響なし |
| II. Test-First | ⚠️ ADAPTED | CI設定は手動検証、TDD対象外 |
| III. Ollama Integration | ✅ N/A | 関係なし |
| IV. Immutability | ✅ N/A | 関係なし |
| V. Simplicity (YAGNI) | ✅ PASS | 最小限の設定変更のみ |

**Gate Result**: PASS

## Project Structure

### Documentation (this feature)

```text
specs/013-ci-lint-migration/
├── spec.md              # 仕様書
├── plan.md              # 本ファイル
├── research.md          # Phase 0: Claude Codeフック調査
├── quickstart.md        # Phase 1: セットアップガイド
├── checklists/
│   └── requirements.md  # 品質チェックリスト
└── tasks.md             # Phase 2: タスク一覧
```

### Configuration Files (repository root)

```text
.github/
└── workflows/
    └── lint.yml              # 新規: CI lintワークフロー

.claude/
├── settings.json             # 新規: プロジェクト設定（フック定義）
├── settings.local.json       # 既存: ローカル設定
└── hooks/
    └── ruff-lint.sh          # 新規: ruff lintフック

.pre-commit-config.yaml       # 変更: ruff/pylint削除
pyproject.toml                # 既存: ruff/pylint設定維持
```

**Structure Decision**: 設定ファイルのみの追加・変更。ソースコード変更なし。

## Complexity Tracking

> Constitution Check違反なし

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| なし | - | - |

## Implementation Phases

### Phase 1: GitHub Actions CI設定

**FR-001, FR-002, FR-003, FR-006対応**

1. `.github/workflows/lint.yml` 作成
   - トリガー: `pull_request` (main向け)
   - Jobs: ruff check, ruff format --check, pylint
   - Python 3.13, pip install from requirements.txt

2. Branch Protection設定確認
   - Status check required: `lint`

### Phase 2: Claude Codeフック設定

**FR-004対応**

1. `.claude/hooks/ruff-lint.sh` 作成
   - PostToolUse (Edit|Write) トリガー
   - Pythonファイルのみ対象
   - ruff format + ruff check 実行

2. `.claude/settings.json` 作成
   - hooks設定追加

### Phase 3: pre-commit削減

**FR-005対応**

1. `.pre-commit-config.yaml` 更新
   - ruff削除
   - pylint削除
   - 空になる場合はファイル自体を削除検討

### Phase 4: 検証 & Polish

1. PRを作成してCI動作確認
2. Claude Codeでファイル編集してフック動作確認
3. pre-commit run --all-files で残存フック確認

## Risk Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| CI失敗でPRブロック | Medium | lint修正後に再push |
| フック未設定の開発者 | Low | CIで最終キャッチ |
| ruffバージョン不一致 | Low | pyproject.toml + requirements.txtで固定 |

## Next Steps

1. `/speckit.tasks` でタスク一覧を生成
2. Phase 1から順次実装
