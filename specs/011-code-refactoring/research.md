# Research: コード品質自動化とファイルサイズ制限

**Date**: 2026-02-18
**Feature**: 011-code-refactoring

## 1. ruff設定のベストプラクティス

### Decision: pyproject.toml に設定を集約

**Rationale**:
- pyproject.toml はPython標準の設定ファイル形式
- ruffはpyproject.tomlをネイティブサポート
- 単一ファイルで管理可能

**Configuration**:
```toml
[tool.ruff]
line-length = 120
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "W"]
# E: pycodestyle errors
# F: pyflakes (undefined names, unused imports)
# I: isort (import sorting)
# W: pycodestyle warnings
```

**Alternatives considered**:
- ruff.toml: プロジェクト標準外、別ファイル増加
- .ruff.toml: 同上

## 2. pre-commit設定

### Decision: ruff公式フックを使用

**Rationale**:
- ruff公式のpre-commitフックがメンテナンスされている
- ruff check + ruff format を両方実行

**Configuration**:
```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.9.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

**Hook behavior**:
- `ruff`: lint + auto-fix
- `ruff-format`: コードフォーマット
- 非ゼロ終了 → コミットブロック

## 3. ファイル分割戦略

### 3.1 src/ocr_ensemble.py (699行)

**分析結果**:
| 責務 | 行数（推定） | 関数/クラス |
|------|-------------|-------------|
| エンジン初期化 | ~50 | `_get_*` 関数群 |
| 個別OCR実行 | ~120 | `ocr_tesseract`, `ocr_easyocr`, `ocr_paddleocr`, `ocr_yomitoku_engine` |
| ボックス付きOCR | ~50 | `ocr_paddleocr_with_boxes` |
| テキスト品質検証 | ~80 | `is_garbage`, `bbox_*`, `create_text_mask` |
| 類似度計算 | ~100 | `calculate_similarity`, `calculate_similarity_matrix` |
| 投票・マージ | ~150 | `vote_best_result`, `merge_by_voting` |
| アンサンブル実行 | ~100 | `ocr_ensemble`, `run_ensemble_ocr`, `main` |
| データクラス | ~50 | `EngineResult`, `EnsembleResult`, `TextWithBox` |

**Decision**: 3ファイルに分割

1. **ocr_ensemble/engines.py** (~200行): エンジン初期化 + 個別OCR実行
2. **ocr_ensemble/voting.py** (~300行): 品質検証 + 類似度計算 + 投票・マージ
3. **ocr_ensemble/__init__.py** (~200行): データクラス + アンサンブル実行 + main

### 3.2 src/rover/engines.py (613行)

**分析結果**:
| 責務 | 行数（推定） | 関数/クラス |
|------|-------------|-------------|
| エンジン初期化 | ~50 | `_get_*` 関数群 |
| データクラス | ~30 | `TextWithBox`, `EngineResult` |
| フィルタリング | ~50 | `_is_word_inside_figures`, `_is_item_inside_figures`, `_filter_items_by_figures` |
| 各エンジン実行 | ~400 | `run_yomitoku_with_boxes`, `run_paddleocr_with_boxes`, `run_easyocr_with_boxes`, `run_tesseract_with_boxes` |
| オーケストレーション | ~30 | `run_all_engines` |

**Decision**: 2ファイルに分割

1. **rover/engines/core.py** (~200行): エンジン初期化 + データクラス + フィルタリング
2. **rover/engines/runners.py** (~400行): 各エンジン実行 + オーケストレーション

**Note**: `runners.py` が400行でも許容（600行以下）。さらに分割すると複雑性が増す。

## 4. 公開API維持戦略

### Decision: `__init__.py` でre-export

**Rationale**:
- 既存のimportパスを維持
- 内部構造の変更を隠蔽

**Example**:
```python
# src/ocr_ensemble/__init__.py
from .engines import ocr_tesseract, ocr_easyocr, ocr_paddleocr, ocr_yomitoku_engine
from .voting import merge_by_voting, vote_best_result
from .models import EngineResult, EnsembleResult, TextWithBox
```

## 5. subagent指示更新

### Decision: phase-executor.md と tdd-generator.md に追記

**追加内容**:
```markdown
## Pre-Commit Compliance

コードを書いた後、コミット前に以下を実行:

```bash
ruff check --fix src/
ruff format src/
```

これによりpre-commitフックの失敗を防止する。
```

## Summary

| Topic | Decision | Key Reason |
|-------|----------|------------|
| ruff設定 | pyproject.toml | Python標準、単一ファイル |
| pre-commit | ruff公式フック | メンテナンス済み、fix対応 |
| ocr_ensemble.py | 3ファイル分割 | 責務分離、各200-300行 |
| rover/engines.py | 2ファイル分割 | 責務分離、各200-400行 |
| 公開API | __init__.pyでre-export | 後方互換性維持 |
| subagent | agents/に追記 | 次回以降のフック対応 |

## Out of Scope

以下は本Issue範囲外:
- book_converter/parser.py (1725行) - 別途対応が必要
- book_converter/page_grouper.py (1166行) - 別途対応が必要
- その他600行以下のファイル
