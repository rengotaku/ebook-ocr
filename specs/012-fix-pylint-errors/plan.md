# Implementation Plan: Pylintエラー対応

**Branch**: `012-fix-pylint-errors` | **Date**: 2026-02-19 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/012-fix-pylint-errors/spec.md`

## Summary

pylint導入により検出されたコード品質違反（too-many-lines: 7ファイル、too-many-locals: 26箇所、too-many-statements/branches: 12箇所）を解消するリファクタリング。既存機能を維持しながら、ファイル分割と関数分解を実施。

## Technical Context

**Language/Version**: Python 3.13+
**Primary Dependencies**: pylint>=3.0.0, ruff, pytest
**Storage**: N/A（ファイル構造変更のみ）
**Testing**: pytest（既存テストスイート）
**Target Platform**: Linux開発環境
**Project Type**: single（src/構造）
**Performance Goals**: N/A（リファクタリングのみ、性能変更なし）
**Constraints**: WF-001〜WF-003（pre-commitフック戦略、spec参照）
**Scale/Scope**: 7ファイル分割、26+関数リファクタリング

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | Status | Note |
|-----------|--------|------|
| I. Pipeline-First | ✅ PASS | パイプライン構造維持、各ステップの独立性は変更なし |
| II. Test-First | ⚠️ ADAPTED | リファクタリングのため既存テストで検証。新テスト不要 |
| III. Ollama Integration | ✅ N/A | Ollama関連コードは対象外 |
| IV. Immutability | ✅ PASS | 既存パターン維持 |
| V. Simplicity (YAGNI) | ✅ ALIGNED | 「1ファイル800行以下」をより厳格な500行制限に準拠 |

**Gate Result**: PASS（Test-First は既存テストで代替）

## Project Structure

### Documentation (this feature)

```text
specs/012-fix-pylint-errors/
├── spec.md              # 仕様書
├── plan.md              # 本ファイル
├── research.md          # Phase 0: リファクタリング分析
├── refactoring-map.md   # Phase 1: 分割・分解マップ
├── checklists/
│   └── requirements.md  # 品質チェックリスト
└── tasks.md             # Phase 2: タスク一覧
```

### Source Code (repository root)

```text
src/
├── book_converter/
│   ├── parser.py          # 1739行 → 分割対象（最優先）
│   ├── page_grouper.py    # 1148行 → 分割対象
│   ├── transformer.py     # 566行 → 分割対象
│   ├── cli.py             # 関数リファクタリング対象
│   └── ...
├── layout/
│   ├── detector.py        # 関数リファクタリング対象
│   └── figures.py         # 関数リファクタリング対象
├── rover/
│   ├── ensemble.py        # 593行 → 分割対象
│   ├── alignment.py       # 関数リファクタリング対象
│   └── engines/runners.py # 関数リファクタリング対象
├── layout_ocr.py          # 595行 → 分割対象
├── ocr_integrated.py      # 577行 → 分割対象
├── ocr_yomitoku.py        # 535行 → 分割対象
└── consolidate.py         # 関数リファクタリング対象

tests/
└── (既存テスト維持、importパス更新のみ)
```

**Structure Decision**: 既存src/構造を維持。大ファイルは同ディレクトリ内でサブモジュール化（例: `parser.py` → `parser/`パッケージ）

## Complexity Tracking

> Constitutionの500行未満は厳しいが、YAGNI原則に沿った適切な制限

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | - | - |

## Refactoring Strategy

### 優先順位

違反の深刻度と影響範囲に基づく優先順位：

| Priority | File | Lines | Strategy |
|----------|------|-------|----------|
| P1 | parser.py | 1739 | パッケージ化（parser/） |
| P2 | page_grouper.py | 1148 | パッケージ化（page_grouper/） |
| P3 | layout_ocr.py | 595 | 関数抽出 |
| P4 | rover/ensemble.py | 593 | 関数抽出 |
| P5 | ocr_integrated.py | 577 | 関数抽出 |
| P6 | transformer.py | 566 | 関数抽出 |
| P7 | ocr_yomitoku.py | 535 | 関数抽出 |

### 関数リファクタリング戦略

`too-many-locals`/`too-many-statements`/`too-many-branches` の解消手法：

1. **データクラス抽出**: 関連する変数をdataclassにグループ化
2. **ヘルパー関数抽出**: 独立した処理ブロックを関数に分離
3. **早期リターン**: 深いネストを早期リターンで解消
4. **辞書マッピング**: 長いif-elif連鎖を辞書ルックアップに変換

## Implementation Phases

### Phase 1: Setup & 準備
- pylint現状確認
- テストベースライン確立（pytest全パス確認）
- WF-001に従いpre-commitバイパス準備

### Phase 2: 大規模ファイル分割（P1-P2）
- parser.py パッケージ化
- page_grouper.py パッケージ化
- 各分割後にpytest確認

### Phase 3: 中規模ファイル分割（P3-P7）
- layout_ocr.py 分割
- rover/ensemble.py 分割
- ocr_integrated.py 分割
- transformer.py 分割
- ocr_yomitoku.py 分割

### Phase 4: 関数リファクタリング
- too-many-locals 解消（26箇所）
- too-many-statements 解消（6箇所）
- too-many-branches 解消（6箇所）

### Phase 5: 検証 & Polish
- WF-002に従いpre-commit全体チェック
- SC-001〜SC-004の達成確認
- テストimportパス最終確認

## Risk Analysis

| Risk | Impact | Mitigation |
|------|--------|------------|
| 循環インポート | Medium | 設計見直し優先、遅延インポートは最終手段 |
| テスト失敗 | High | 各分割後にpytest実行、失敗時は即座にロールバック |
| 公開API破壊 | Medium | `__init__.py`での再エクスポートでAPI維持 |
| コンテキスト超過 | Medium | ファイル単位で段階的に作業 |

## Next Steps

1. `/speckit.tasks` でタスク一覧を生成
2. `/speckit.implement` で実装開始
