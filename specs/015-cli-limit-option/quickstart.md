# Quickstart: CLIコマンドへの--limitオプション追加

**Branch**: 015-cli-limit-option

## 概要

各CLIコマンドに`--limit N`オプションを追加し、処理する画像数を制限する機能。

## 使用方法

### 個別CLIコマンド

```bash
# 最初の25枚のみ重複排除
python -m src.cli.deduplicate output/frames -o output/pages --limit 25

# 最初の10枚のみレイアウト検出
python -m src.cli.detect_layout output/pages -o output/layout --limit 10

# 最初の5枚のみOCR
python -m src.cli.run_ocr output/pages -o output/ocr --limit 5

# 最初の5ファイルのみ統合
python -m src.cli.consolidate output/ocr -o output --limit 5
```

### Makefile経由

```bash
# 25枚制限でフルパイプライン実行
make test-run VIDEO=input.mov LIMIT=25

# 制限なしでフルパイプライン（既存動作）
make test-run VIDEO=input.mov
```

## 開発者向け

### テスト実行

```bash
# 全テスト
make test

# limit機能のテストのみ
pytest tests/cli/test_*_limit.py -v
```

### 実装パターン

```python
# CLI層
parser.add_argument("--limit", type=int, help="Process only first N files")

# 基盤関数層
def process_files(input_dir, output_dir, *, limit=None):
    files = sorted(Path(input_dir).glob("*.png"))
    if limit:
        print(f"Limiting to {limit} files", file=sys.stderr)
        files = files[:limit]
    # ... process files
```

## 期待される効果

| 指標 | 通常処理 | LIMIT=25 |
|------|----------|----------|
| 処理時間 | 30-60分 | 2-5分 |
| 画像数 | 500枚 | 25枚 |
| ユースケース | 本番処理 | 動作確認・デバッグ |
