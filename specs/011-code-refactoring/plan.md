# Implementation Plan: コード品質自動化とファイルサイズ制限

**Branch**: `011-code-refactoring` | **Date**: 2026-02-18 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/011-code-refactoring/spec.md`

## Summary

ruff（Pythonリンター/フォーマッター）の導入、pre-commitフックの設定、および600行超ファイルの分割を行う。実装順序: ruff設定 → 既存コード修正 → ファイル分割 → pre-commit設定 → subagent指示更新。

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: ruff, pre-commit
**Storage**: N/A（設定ファイルのみ）
**Testing**: pytest（既存テストの維持）
**Target Platform**: Linux開発環境
**Project Type**: single
**Performance Goals**: N/A（開発ツール設定）
**Constraints**: 既存テストがすべてパスすること、公開APIの維持
**Scale/Scope**: 分割対象ファイル2件（ocr_ensemble.py: 699行, rover/engines.py: 613行）

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Notes |
|-----------|--------|-------|
| I. Pipeline-First | ✅ PASS | コード品質ツールは全パイプラインに適用 |
| II. Test-First | ⚠️ PARTIAL | ツール設定はTDD不要、ファイル分割はテスト維持で検証 |
| III. Ollama Integration | ✅ N/A | OCR関連コードは影響受けるが機能変更なし |
| IV. Immutability | ✅ N/A | リファクタリングのみ、機能変更なし |
| V. Simplicity (YAGNI) | ✅ PASS | 1ファイル800行以下→600行以下に強化 |

**Gate Result**: ✅ PASS

## Project Structure

### Documentation (this feature)

```text
specs/011-code-refactoring/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output（設定ファイル構造）
├── quickstart.md        # Phase 1 output
└── tasks.md             # Phase 2 output
```

### Source Code (repository root)

```text
src/
├── ocr_ensemble.py      # 699行 → 分割対象
├── rover/
│   └── engines.py       # 613行 → 分割対象
├── cli/
├── preprocessing/
├── layout/
└── book_converter/

.claude/
└── agents/
    ├── phase-executor.md  # 更新対象（ruff実行手順追加）
    └── tdd-generator.md   # 更新対象（ruff実行手順追加）

pyproject.toml           # 新規作成（ruff設定）
.pre-commit-config.yaml  # 新規作成
```

**Structure Decision**: 既存の single project 構造を維持。設定ファイルはリポジトリルートに配置。

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| なし | - | - |
