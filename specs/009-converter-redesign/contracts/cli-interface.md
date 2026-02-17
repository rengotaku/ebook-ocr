# CLI Interface Contract: book_converter

**Version**: 2.0.0
**Date**: 2026-02-16

## コマンド

```bash
python -m src.book_converter <input.md> [options]
```

## 必須引数

| Argument | Type | Description |
|----------|------|-------------|
| `input` | Path | 入力MDファイルパス |

## オプション引数

### 出力制御

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `-o, --output` | Path | `<input>.xml` | 出力XMLファイルパス |
| `--figures-dir` | Path | `figures/` | 図画像の出力ディレクトリ |

### 見出しレベル設定

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--header-level1` | str | (required) | レベル1キーワード（パイプ区切り可） |
| `--header-level2` | str | `""` | レベル2キーワード |
| `--header-level3` | str | `""` | レベル3キーワード |
| `--header-level4` | str | `""` | レベル4キーワード |
| `--header-level5` | str | `""` | レベル5キーワード |

**例**:
```bash
--header-level1=chapter --header-level2="episode|column"
```

### 図マーカー設定

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--figure-markers` | str | `"図|写真|表"` | 図マーカーキーワード（パイプ区切り） |

**例**:
```bash
--figure-markers="図|写真|表|イラスト|グラフ"
```

### デバッグ・その他

| Option | Type | Default | Description |
|--------|------|---------|-------------|
| `--verbose, -v` | flag | `false` | 詳細ログ出力 |
| `--dry-run` | flag | `false` | 変換せずに解析結果のみ表示 |
| `--version` | flag | - | バージョン表示 |

## 終了コード

| Code | Meaning |
|------|---------|
| 0 | 成功 |
| 1 | 入力ファイルエラー |
| 2 | 変換エラー |
| 3 | 出力エラー |

## 使用例

### 基本使用

```bash
python -m src.book_converter book.md -o book.xml \
  --header-level1=chapter \
  --header-level2="episode|column"
```

### 詳細ログ付き

```bash
python -m src.book_converter book.md -o book.xml \
  --header-level1=chapter \
  --header-level2=episode \
  --figure-markers="図|写真|表" \
  --verbose
```

### ドライラン（解析のみ）

```bash
python -m src.book_converter book.md --dry-run \
  --header-level1=chapter
```
