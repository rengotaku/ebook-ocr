# Data Model: コード品質自動化とファイルサイズ制限

**Date**: 2026-02-18
**Feature**: 011-code-refactoring

## 設定ファイル構造

### pyproject.toml（ruff設定）

```toml
[tool.ruff]
line-length = 120
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "W"]
```

| フィールド | 型 | 説明 |
|-----------|-----|------|
| line-length | int | 1行の最大文字数（120） |
| target-version | str | Pythonバージョン（"py313"） |
| select | list[str] | 有効化するルールセット |

### .pre-commit-config.yaml

```yaml
repos:
  - repo: https://github.com/astral-sh/ruff-pre-commit
    rev: v0.9.6
    hooks:
      - id: ruff
        args: [--fix]
      - id: ruff-format
```

| フィールド | 型 | 説明 |
|-----------|-----|------|
| repos | list | 使用するフックリポジトリのリスト |
| repo | str | フックリポジトリURL |
| rev | str | 使用するバージョンタグ |
| hooks | list | 有効化するフック |
| args | list[str] | フックに渡す引数 |

## 分割後のモジュール構造

### src/ocr_ensemble/ （新規パッケージ）

```
src/ocr_ensemble/
├── __init__.py      # 公開API re-export
├── engines.py       # OCRエンジン初期化・実行
├── voting.py        # 品質検証・類似度計算・投票マージ
└── models.py        # データクラス（EngineResult, EnsembleResult, TextWithBox）
```

### src/rover/engines/ （ディレクトリ化）

```
src/rover/engines/
├── __init__.py      # 公開API re-export
├── core.py          # エンジン初期化・データクラス・フィルタリング
└── runners.py       # 各エンジン実行・オーケストレーション
```

## 公開API一覧

### ocr_ensemble

| シンボル | 型 | 元の場所 | 新しい場所 |
|---------|-----|---------|-----------|
| EngineResult | class | ocr_ensemble.py:88 | ocr_ensemble/models.py |
| EnsembleResult | class | ocr_ensemble.py:96 | ocr_ensemble/models.py |
| TextWithBox | class | ocr_ensemble.py:215 | ocr_ensemble/models.py |
| ocr_tesseract | function | ocr_ensemble.py:106 | ocr_ensemble/engines.py |
| ocr_easyocr | function | ocr_ensemble.py:120 | ocr_ensemble/engines.py |
| ocr_paddleocr | function | ocr_ensemble.py:137 | ocr_ensemble/engines.py |
| ocr_yomitoku_engine | function | ocr_ensemble.py:174 | ocr_ensemble/engines.py |
| ocr_ensemble | function | ocr_ensemble.py | ocr_ensemble/__init__.py |
| run_ensemble_ocr | function | ocr_ensemble.py | ocr_ensemble/__init__.py |

### rover/engines

| シンボル | 型 | 元の場所 | 新しい場所 |
|---------|-----|---------|-----------|
| TextWithBox | class | engines.py:74 | engines/core.py |
| EngineResult | class | engines.py:87 | engines/core.py |
| run_yomitoku_with_boxes | function | engines.py | engines/runners.py |
| run_paddleocr_with_boxes | function | engines.py | engines/runners.py |
| run_easyocr_with_boxes | function | engines.py | engines/runners.py |
| run_tesseract_with_boxes | function | engines.py | engines/runners.py |
| run_all_engines | function | engines.py | engines/runners.py |

## 移行後のimportパス

### Before
```python
from src.ocr_ensemble import EngineResult, EnsembleResult, ocr_ensemble
from src.rover.engines import TextWithBox, EngineResult, run_all_engines
```

### After（同じ）
```python
from src.ocr_ensemble import EngineResult, EnsembleResult, ocr_ensemble
from src.rover.engines import TextWithBox, EngineResult, run_all_engines
```

**Note**: `__init__.py` で re-export するため、外部からのimportパスは変更なし。
