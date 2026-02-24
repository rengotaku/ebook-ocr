# Phase 2 Output: ローカルとCIの一貫性

**Date**: 2026-02-24
**Status**: Completed
**User Story**: US3 - ローカルとCIの一貫性

## Executed Tasks

- [x] T005 Read previous phase output: `specs/017-github-actions-lint/tasks/ph1-output.md`
- [x] T006 [US3] Makefileに`ruff`ターゲットを追加: `Makefile`
- [x] T007 [US3] Makefileに`pylint`ターゲットを追加: `Makefile`
- [x] T008 [US3] Makefileに`lint`ターゲットを追加（ruff + pylint）: `Makefile`
- [x] T009 `make ruff` を実行して動作確認
- [x] T010 `make pylint` を実行して動作確認
- [x] T011 `make lint` を実行して動作確認
- [x] T012 Edit and rename: `specs/017-github-actions-lint/tasks/ph2-output-template.md` → `ph2-output.md`

## Changed Files

| File | Change Type | Summary |
|------|-------------|---------|
| Makefile | Modified | 3つのlintターゲット（ruff, pylint, lint）を追加、.PHONYに追加 |
| specs/017-github-actions-lint/tasks.md | Modified | T005-T012をチェック済みにマーク |

## Makefile Changes Details

### 追加されたターゲット

```makefile
# === Linting ===

ruff: ## Run ruff linter
	ruff check src/ tests/
	ruff format --check src/ tests/

pylint: ## Run pylint static analysis
	pylint --rcfile=pyproject.toml src/

lint: ruff pylint ## Run all linters (ruff + pylint)
```

### .PHONYの更新

`ruff pylint lint` を `.PHONY` に追加しました。

## Test Results

### make ruff

```
ruff check src/ tests/
All checks passed!
ruff format --check src/ tests/
110 files already formatted
```

**Status**: ✅ PASS

### make pylint

```
pylint --rcfile=pyproject.toml src/
************* Module src.ocr_yomitoku
src/ocr_yomitoku.py:199:0: R0914: Too many local variables (20/15) (too-many-locals)
...（省略）...

------------------------------------------------------------------
Your code has been rated at 9.91/10
```

**Status**: ⚠️ 警告あり（既存コードの品質問題、設計通り）

Exit code 2 でエラー終了するが、これは既存コードがpylintの基準を満たしていないためで、plan.mdで想定された挙動である。

### make lint

`make ruff` → `make pylint` の順で正常に実行され、両方のlinterが動作することを確認。

## Discovered Issues

1. **pylintがexit code 2で終了**: 既存コードに多数の警告（too-many-locals, too-many-lines等）が存在
   - **解決策**: plan.mdで明記されている通り、`--fail-under` オプションなしで運用。Phase 5 (Polish) で必要に応じて修正
   - **影響**: CIでpylintジョブが失敗する可能性があるが、これは段階的品質向上のための想定された挙動

## Handoff to Next Phase

Phase 3 (US1 - PRのlintチェック自動実行) で実装する項目:
- `.github/workflows/lint.yml` の更新
  - `make ruff` と `make pylint` を使用
  - ruff/pylintを並列ジョブに分離
  - pathsフィルタ削除
  - fail-underオプション削除

注意点:
- Makefileターゲットは準備完了。Phase 3ではワークフローファイルのみ更新
- pylintの警告は既知の問題。CIでエラーになる可能性があるが、修正はPhase 5で検討
