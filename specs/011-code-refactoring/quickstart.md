# Quickstart: コード品質自動化とファイルサイズ制限

## 概要

このfeatureはruff（Pythonリンター/フォーマッター）の導入、pre-commitフックの設定、および600行超ファイルの分割を行います。

## 前提条件

- Python 3.13+
- pip（パッケージインストール用）
- git（pre-commit用）

## セットアップ

### 1. 依存関係のインストール

```bash
pip install ruff pre-commit
```

### 2. pre-commitフックの有効化

```bash
pre-commit install
```

## 使用方法

### ruffによるコードチェック

```bash
# チェックのみ
ruff check src/

# 自動修正付き
ruff check --fix src/

# フォーマット
ruff format src/
```

### pre-commitの手動実行

```bash
# すべてのファイルに対して実行
pre-commit run --all-files

# 特定のフックのみ
pre-commit run ruff --all-files
pre-commit run ruff-format --all-files
```

## 分割後のモジュール構造

### ocr_ensemble

```
src/ocr_ensemble/
├── __init__.py      # 公開API（ocr_ensemble, run_ensemble_ocr）
├── engines.py       # OCRエンジン実行（ocr_tesseract, ocr_easyocr等）
├── voting.py        # 投票・マージロジック
└── models.py        # データクラス（EngineResult, EnsembleResult）
```

### rover/engines

```
src/rover/engines/
├── __init__.py      # 公開API（run_all_engines等）
├── core.py          # エンジン初期化・データクラス
└── runners.py       # 各エンジン実行関数
```

## importの例

```python
# 既存のimportパスは変更なし
from src.ocr_ensemble import EngineResult, EnsembleResult, ocr_ensemble
from src.rover.engines import TextWithBox, EngineResult, run_all_engines
```

## 検証

### ruffチェック

```bash
# エラー0件を確認
ruff check src/
# Expected: All checks passed!
```

### テスト実行

```bash
make test
# Expected: すべてのテストがパス
```

### ファイル行数確認

```bash
find src -name "*.py" -exec wc -l {} \; | sort -rn | head -10
# Expected: 600行を超えるファイルがないこと（book_converter/除く）
```

## トラブルシューティング

### pre-commitフック失敗時

```bash
# ruff違反を修正
ruff check --fix src/
ruff format src/

# 再度コミット
git add .
git commit -m "your message"
```

### 循環import発生時

分割後のファイルで循環importが発生した場合:
1. 共通の型定義を `models.py` に集約
2. 遅延import（関数内import）を検討
3. 依存関係を見直し、一方向の依存に修正
