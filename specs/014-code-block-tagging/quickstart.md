# Quickstart: コードブロックタグ付け機能

**Date**: 2026-02-21

## 依存インストール

```bash
# venv有効化
source venv/bin/activate

# 新規依存追加
pip install opencv-python>=4.8.0 guesslang>=2.2.1

# requirements.txt更新
pip freeze > requirements.txt
```

## 使用方法

### 1. コード検出単体

```python
from src.layout.code_detector import detect_code_regions

# 画像からコード領域を検出
result = detect_code_regions("page_001.jpg")

for region in result.regions:
    print(f"bbox: {region.bbox}, is_code: {region.is_code}, conf: {region.confidence}")
```

### 2. layout.jsonマージ

```python
from src.layout.code_detector import detect_and_merge_code_regions

# yomitoku結果にコード領域を追加
updated_layout = detect_and_merge_code_regions(
    image_path="page_001.jpg",
    layout_path="layout/page_001.json"
)

# 更新されたlayout.jsonを保存
with open("layout/page_001.json", "w") as f:
    json.dump(updated_layout, f, ensure_ascii=False, indent=2)
```

### 3. CLI使用

```bash
# レイアウト検出 + コード検出
python -m src.cli detect-layout input/ --detect-code

# コード検出のみ
python -m src.cli detect-code input/page_001.jpg

# 閾値指定
python -m src.cli detect-code input/ --code-threshold 0.6
```

## 設定オプション

| オプション | デフォルト | 説明 |
|-----------|-----------|------|
| `--detect-code` | False | コード検出を有効化 |
| `--code-threshold` | 0.6 | Guesslang信頼度閾値 |
| `--min-area-ratio` | 0.005 | 最小面積比（ページ比） |
| `--max-area-ratio` | 0.75 | 最大面積比（ページ比） |

## テスト実行

```bash
# ユニットテスト
make test-unit

# 統合テスト
make test-integration

# 特定テスト
pytest tests/unit/layout/test_code_detector.py -v
```

## トラブルシューティング

### TensorFlow警告

```
WARNING:tensorflow:...
```

→ 正常動作。GPU未使用時の警告は無視可能。

### Guesslang初回ロード遅延

初回実行時にモデルロードで数秒かかる。2回目以降はキャッシュされる。

### 枠線検出失敗

- Canny閾値を調整: `--canny-low 30 --canny-high 100`
- モルフォロジーカーネル調整: `--morph-kernel 7`
