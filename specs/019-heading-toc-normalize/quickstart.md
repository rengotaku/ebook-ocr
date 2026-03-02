# Quickstart: 019-heading-toc-normalize

**Date**: 2026-03-02

## 概要

book.md の見出し形式を TOC（目次）に合わせて自動正規化するツール。

## 前提条件

- Python 3.13+
- book.md に `<!-- toc -->` ... `<!-- /toc -->` マーカーが存在

## 基本的な使い方

### 1. 見出しパターン分析

```bash
# book.md の見出しパターンをレポート
make heading-report HASHDIR=output/<hash>

# または直接実行
python -m src.cli.normalize_headings report output/<hash>/book.md
```

**出力例**:
```
Heading Pattern Report
======================
Total headings: 42

Pattern Distribution:
  ## N.N タイトル     : 25 (59.5%)
  ## タイトル         : 12 (28.6%)
  タイトル（マーカーなし）: 5 (11.9%)

Number Format:
  ドット区切り (1.1)  : 20
  ハイフン区切り (1-1): 5
  番号なし           : 17
```

### 2. 正規化プレビュー（dry-run）

```bash
# 変更内容をプレビュー（ファイル変更なし）
make normalize-headings HASHDIR=output/<hash>
```

**出力例**:
```
Normalization Preview
=====================
Changes: 17

- Line 52: "## SREの概要" → "## 1.1 SREの概要"
- Line 68: "サイトとは何か" → "### 1.1.1 サイトとは何か"
- Line 85: "## 1-1 信頼性" → "## 1.1 信頼性"

Warnings:
- Line 0: TOC entry "第1章 SREとは" has no matching body heading (MISSING)

Run with APPLY=1 to apply changes.
```

### 3. 正規化を適用

```bash
# 変更を book.md に適用
make normalize-headings HASHDIR=output/<hash> APPLY=1
```

### 4. TOC 検証

```bash
# 正規化後のマッチング率を検証
make validate-toc HASHDIR=output/<hash>
```

**出力例**:
```
TOC Validation Report
=====================
TOC Entries:     42
Body Headings:   40
Matched:         38 (95.0%)

Missing in Body (2):
  - 第1章 SREとは
  - 第2章 信頼性を定義...

Excluded (special markers):
  - ## ■コードベース
  - ## ■コードの送信
```

## 正規化ルール

### 番号フォーマット

| 変換前 | 変換後 |
|--------|--------|
| `1-1-1` | `1.1.1` |
| `１．１` | `1.1` |
| `1・1` | `1.1` |

### スペース

| 変換前 | 変換後 |
|--------|--------|
| `第 1 章` | `第1章` |
| `1. 1` | `1.1` |

### 特殊マーカー

以下の文字で始まる見出しはマッチング対象外:
- `■`, `◆`, `●`, `○`, `◎`, `★`, `☆`, `▶`, `▷`

## トラブルシューティング

### MISSING 警告が多い

TOC にあるが本文にない見出しがある場合:
1. `make validate-toc` で欠落一覧を確認
2. book.md を手動で確認し、欠落見出しを追加

### マッチング率が低い

1. `make heading-report` でパターン分布を確認
2. OCR 誤認識がある場合、ファジーマッチ閾値を調整

```bash
# 閾値を下げる（デフォルト: 0.8）
python -m src.cli.normalize_headings normalize book.md --threshold 0.7
```
