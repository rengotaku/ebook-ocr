# Quickstart: Spread モード明示指定と Trim 制御の拡張

**Feature**: 018-spread-mode-trim

## 基本的な使い方

### 1. 単ページモード（デフォルト）

```bash
# 単ページとして処理（分割なし）
make split-spreads HASHDIR=output/<hash>

# または明示的に指定
make split-spreads HASHDIR=output/<hash> SPREAD_MODE=single
```

### 2. 見開きモード

```bash
# 見開きとして処理（常に左右分割）
make split-spreads HASHDIR=output/<hash> SPREAD_MODE=spread
```

### 3. Global Trim（分割前のトリミング）

```bash
# 上下2%、左右1%をトリム
make split-spreads HASHDIR=output/<hash> \
  GLOBAL_TRIM_TOP=0.02 \
  GLOBAL_TRIM_BOTTOM=0.02 \
  GLOBAL_TRIM_LEFT=0.01 \
  GLOBAL_TRIM_RIGHT=0.01
```

### 4. Split Trim（分割後のトリミング）

```bash
# 見開き分割後、左ページの左端3%、右ページの右端3%をトリム
make split-spreads HASHDIR=output/<hash> \
  SPREAD_MODE=spread \
  LEFT_TRIM=0.03 \
  RIGHT_TRIM=0.03
```

### 5. 両方のトリムを組み合わせ

```bash
make split-spreads HASHDIR=output/<hash> \
  SPREAD_MODE=spread \
  GLOBAL_TRIM_TOP=0.02 \
  GLOBAL_TRIM_BOTTOM=0.02 \
  LEFT_TRIM=0.03 \
  RIGHT_TRIM=0.03
```

## プレビューワークフロー

### Step 1: サンプルフレーム抽出

```bash
# 動画からサンプルフレームを抽出（INTERVAL で調整、大きい値=少ないフレーム）
make preview-extract VIDEO=input.mp4 INTERVAL=3.0
```

出力: `output/<hash>/preview/frames/`

注: LIMIT パラメータは未サポート。フレーム数を減らすには INTERVAL を大きくしてください。

### Step 2: Trim プレビュー

```bash
# 抽出したフレームに trim を適用してプレビュー
make preview-trim HASHDIR=output/<hash> \
  SPREAD_MODE=spread \
  GLOBAL_TRIM_TOP=0.02 \
  GLOBAL_TRIM_LEFT=0.03
```

出力: `output/<hash>/preview/trimmed/`

### Step 3: パラメータ調整

```bash
# パラメータを変更して再実行（フレーム再抽出なし）
make preview-trim HASHDIR=output/<hash> \
  SPREAD_MODE=spread \
  GLOBAL_TRIM_TOP=0.03 \
  LEFT_TRIM=0.05
```

### Step 4: 本番実行

```bash
# 確定したパラメータでフルパイプライン実行
make run VIDEO=input.mp4 \
  SPREAD_MODE=spread \
  GLOBAL_TRIM_TOP=0.03 \
  LEFT_TRIM=0.05
```

## 設定ファイル（config.yaml）

```yaml
# config.yaml に追加
spread_mode: spread
global_trim_top: 0.02
global_trim_bottom: 0.02
global_trim_left: 0.01
global_trim_right: 0.01
spread_left_trim: 0.03
spread_right_trim: 0.03
```

設定ファイルの値は、CLI引数や環境変数で上書き可能。

## 環境変数での設定

```bash
# 環境変数で設定
export SPREAD_MODE=spread
export GLOBAL_TRIM_TOP=0.02

# 以降のコマンドで使用される
make split-spreads HASHDIR=output/<hash>
```

## トラブルシューティング

### モードが表示されない

```bash
# 処理開始時にモードが表示される
# 例: "Mode: spread"
make split-spreads HASHDIR=output/<hash> SPREAD_MODE=spread
```

### preview-trim でエラー

```bash
# フレームが存在しない場合
Error: Run preview-extract first

# 解決: preview-extract を先に実行
make preview-extract VIDEO=input.mp4
```

### trim 値が大きすぎる

```bash
# 0.5以上の値はエラー
Error: trim value must be less than 0.5

# 解決: 0.0〜0.49 の範囲で指定
```
