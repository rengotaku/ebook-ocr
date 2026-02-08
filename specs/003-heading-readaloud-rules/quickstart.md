# Quickstart: heading要素へのreadAloud属性付与ルール

**Date**: 2026-02-08
**Feature**: 003-heading-readaloud-rules

## 概要

book_converterに heading要素の `readAloud` 属性自動付与機能を追加します。繰り返し出現する柱（ランニングヘッド）、ページ番号表記、装飾記号などを検出し、TTS読み上げ対象から除外します。

## 前提条件

- Python 3.13+
- 既存のbook_converter環境がセットアップ済み
- pytest が利用可能

```bash
# 環境確認
python --version  # Python 3.13+
make test         # 既存テストがパスすることを確認
```

## 基本的な使い方

### 1. 標準変換（デフォルトパターン適用）

```bash
# Markdown → XML 変換（readAloud属性が自動付与される）
python -m src.book_converter.cli input.md output.xml
```

### 2. 変換結果の確認

```xml
<!-- 柱（ランニングヘッド）: 読み上げ対象外 -->
<heading level="1" readAloud="false">SREの知識地図——基礎知識から現場での実践まで</heading>

<!-- ページ番号表記: 読み上げ対象外 -->
<heading level="3" readAloud="false">1.1.1 SREの概要 — 1 / 3</heading>

<!-- 装飾記号: 読み上げ対象外 -->
<heading level="2" readAloud="false">◆◆◆</heading>

<!-- 通常の見出し: 読み上げ対象（属性なしまたはtrue） -->
<heading level="2">なぜSREが重要なのか</heading>
```

### 3. カスタムパターンの追加

```python
# config.local.py を作成してパターンを追加
CUSTOM_EXCLUSION_PATTERNS = [
    {
        "id": "custom-header",
        "priority": 80,
        "pattern": r"^第\d+章\s",
        "pattern_type": "static",
        "description": "章タイトルプレフィックス",
    },
]
```

```bash
# カスタム設定を使用
python -m src.book_converter.cli input.md output.xml --config config.local.py
```

## デフォルト除外パターン

| ID | 優先度 | パターン | 説明 |
|----|--------|----------|------|
| running-head | 100 | (動的検出) | 柱（ランニングヘッド） |
| page-number | 90 | `.*[―—]\s*\d+\s*/\s*\d+$` | ページ番号表記 |
| section-label | 50 | `^Section\s+\d+\.\d+$` | 章節ラベル |
| decoration | 50 | `^[◆◇■□●○▲△]+$` | 装飾記号 |
| reference | 30 | `^Webサイト$` | 参照表記 |
| footnote | 30 | `^注\d+\.\d+` | 脚注番号 |

## テスト実行

```bash
# 全テスト実行
make test

# analyzer関連のテストのみ
pytest tests/book_converter/test_analyzer.py -v

# readAloud属性関連のテストのみ
pytest tests/book_converter/test_transformer.py -k "read_aloud" -v
```

## トラブルシューティング

### 柱が検出されない

柱検出の閾値（デフォルト: 総ページ数の50%）を下げる:

```bash
python -m src.book_converter.cli input.md output.xml --running-head-threshold 0.3
```

### 誤って除外されている見出しがある

`--verbose` オプションで除外理由を確認:

```bash
python -m src.book_converter.cli input.md output.xml --verbose
```

出力例:
```
[INFO] Detected running head: "SREの知識地図..." (124 occurrences)
[INFO] Excluded heading (page-number): "1.1.1 SREの概要 — 1 / 3"
[INFO] Excluded heading (decoration): "◆◆◆"
```

## 次のステップ

1. `make test` で既存テストがパスすることを確認
2. サンプル書籍で変換を実行し、readAloud属性を確認
3. 必要に応じてカスタムパターンを追加
