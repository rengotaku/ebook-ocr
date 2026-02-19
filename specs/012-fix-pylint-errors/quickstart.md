# Quickstart: Pylintエラー対応リファクタリング

## 前提条件

```bash
# pylintがインストールされていること
pip install "pylint>=3.0.0"

# 現在の違反状況を確認
pylint --rcfile=pyproject.toml src/
```

## ワークフロー

### 1. 作業開始前

```bash
# テストベースライン確認
pytest

# ruffチェック
ruff check src/
```

### 2. 作業中のコミット

```bash
# pre-commitをバイパス（WF-001準拠）
git commit --no-verify -m "refactor: ..."
```

### 3. ファイル分割パターン

#### パッケージ化（大規模ファイル用）

```bash
# 例: parser.py → parser/
mkdir src/book_converter/parser
touch src/book_converter/parser/__init__.py

# モジュール作成後
mv src/book_converter/parser.py src/book_converter/parser.py.bak
# テスト確認後にバックアップ削除
```

#### ヘルパー抽出（中規模ファイル用）

```bash
# 例: layout_ocr.py → layout_ocr.py + layout_ocr_utils.py
touch src/layout_ocr_utils.py
# 関数を移動後、元ファイルでimport
```

### 4. 関数リファクタリングパターン

#### too-many-locals対策

```python
# Before
def process():
    x1, y1, x2, y2 = get_bbox()
    width = x2 - x1
    height = y2 - y1
    # ... 15+ variables

# After: dataclassを使用
@dataclass
class BBox:
    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def width(self) -> int:
        return self.x2 - self.x1
```

#### too-many-branches対策

```python
# Before
if type == "a":
    do_a()
elif type == "b":
    do_b()
elif type == "c":
    do_c()

# After: 辞書ディスパッチ
handlers = {"a": do_a, "b": do_b, "c": do_c}
handlers[type]()
```

### 5. 各フェーズ後の確認

```bash
# テスト
pytest

# pylint（進捗確認）
pylint --rcfile=pyproject.toml src/ | grep -c "too-many"
```

### 6. 最終検証（Phase 5）

```bash
# WF-002: pre-commit全体チェック
pre-commit run --all-files

# SC-001: pylint違反0件
pylint --rcfile=pyproject.toml src/

# SC-002: pytest全パス
pytest

# SC-003: ruff違反0件
ruff check src/
```

## トラブルシューティング

### 循環インポート発生時

1. 依存関係を確認
2. 共通部分を別モジュールに抽出
3. 最終手段: 遅延インポート（関数内import）

### テスト失敗時

1. import文を確認
2. `__init__.py`の再エクスポートを確認
3. 必要に応じてロールバック

### pylint違反が残る場合

```bash
# 詳細確認
pylint --rcfile=pyproject.toml src/file.py

# 特定ルールのみ
pylint --disable=all --enable=too-many-locals src/file.py
```
