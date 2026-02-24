# Phase 1 Output: Setup

**Date**: 2026-02-24
**Status**: Completed

## Executed Tasks

- [x] T001 既存のワークフロー確認: `.github/workflows/lint.yml`
- [x] T002 既存のMakefile確認: `Makefile`
- [x] T003 既存のpyproject.toml設定確認: `pyproject.toml`
- [x] T004 Phase 1出力作成

## Existing Code Analysis

### .github/workflows/lint.yml

**Structure**:
- `on.pull_request`: PR時のみトリガー（mainブランチ、paths指定あり）
- `jobs.lint`: 単一ジョブで ruff + pylint を順次実行

**Required Updates**:
1. トリガー: `pull_request` のみ → `push` トリガー追加（FR-003）
2. pathsフィルタ: 削除（常に実行）
3. ジョブ構成: 単一ジョブ → `ruff` と `pylint` の並列ジョブに分離（FR-008）
4. 実行コマンド: 直接コマンド → `make ruff`, `make pylint` 使用（FR-007）
5. pylint: `--fail-under=9.9` → 削除（段階的品質向上のため）

### Makefile

**Structure**:
- テストターゲット: `test`, `test-cov`, `coverage`
- lintターゲット: **存在しない**

**Required Updates**:
1. `ruff` ターゲット追加: `ruff check src/ tests/` + `ruff format --check src/ tests/`
2. `pylint` ターゲット追加: `pylint --rcfile=pyproject.toml src/`
3. `lint` ターゲット追加: `ruff` + `pylint` の依存ターゲット
4. `.PHONY` 更新: `ruff pylint lint` 追加

### pyproject.toml

**Structure**:
- `[tool.ruff]`: line-length=120, target-version="py313"
- `[tool.ruff.lint]`: select=["E", "F", "I", "W"]
- `[tool.pylint.main]`: サイズ制限系のみ有効化
- `[tool.pylint.design]`: max-module-lines=500 等

**Required Updates**:
- 変更不要（既存設定で十分）

## Existing Test Analysis

- テスト: `tests/` ディレクトリに pytest テストあり
- lint関連テスト: **不要**（CI設定ファイルのためユニットテストなし）

## Technical Decisions

1. **Makefileターゲット**: venv不使用でグローバル `ruff`/`pylint` を直接実行
   - 理由: CI環境ではグローバルにインストールするため
2. **fail-under削除**: 既存コードがスコア基準を満たさない可能性があるため
3. **並列ジョブ**: ruff/pylint を別ジョブで実行し、個別結果確認を可能に

## Handoff to Next Phase

Phase 2 (US3 - ローカルとCIの一貫性) で実装する項目:
- `make ruff`: ruff check + format check
- `make pylint`: pylint 静的解析
- `make lint`: 上記両方を実行

注意点:
- Makefileの既存ターゲットと一貫性のあるスタイルで追加
- helpに表示されるようコメント追加
