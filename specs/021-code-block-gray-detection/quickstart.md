# Quickstart: コードブロック視覚検出

**Feature**: 021-code-block-gray-detection

## 開発環境セットアップ

```bash
# ブランチ切り替え
git checkout 021-code-block-gray-detection

# 依存インストール（OpenCV は既にインストール済み）
source venv/bin/activate
pip install -r requirements.txt

# テスト実行
make test
```

## ファイル構成

| ファイル | 役割 |
|---------|------|
| `src/layout/code_detector.py` | 新規: 灰色背景検出 + テキスト分析 + 断片結合 |
| `src/layout/detector.py` | 変更: paragraphs_to_layout() にコード判定統合 |
| `src/layout_ocr_utils.py` | 変更: CODE フォーマット + エンジン選択追加 |
| `config.yaml` | 変更: code_detection セクション追加 |
| `tests/test_code_detector.py` | 新規: コード検出テスト |
| `tests/test_layout_ocr.py` | 変更: CODE テスト追加 |

## 実行方法

```bash
# レイアウト検出（CODE 検出含む）
make detect-layout HASHDIR=output/<hash>

# OCR 実行（CODE はコードフェンスで出力）
make run-ocr HASHDIR=output/<hash>

# テスト
make test           # 高速テスト
make test-cov       # カバレッジ付き
make lint           # リント
```

## 設定変更

`config.yaml` の `code_detection` セクションで閾値調整:

```yaml
code_detection:
  gray_background_threshold: 0.7   # 灰色画素比率
  symbol_ratio_threshold: 0.08     # 記号比率
  keyword_threshold: 2             # キーワード数
  fragment_gap_threshold: 80       # 結合ギャップ(px)
```

## 検証方法

1. `make detect-layout` 実行後、`layout.json` に `"type": "CODE"` リージョンが存在することを確認
2. `layouts/` の可視化画像で CODE リージョンが黄色で描画されることを目視確認
3. `make ocr` 実行後、出力テキストにコードフェンス（` ``` `）が含まれることを確認
