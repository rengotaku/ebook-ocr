# Sony ビューアの HAR からページ画像を復元する

Sony 電子書籍ストアのビューア（`viewer.ebookstore.sony.jp`）が返すページ画像を、
ブラウザの通信ログ（HAR）から復元して WebP として書き出す。

画面キャプチャとページ送りを省いて ebook-ocr の入力を作るためのツール。
購入した本を自分の環境で処理する用途を想定している。

## 使い方

```bash
# 1. ビューアで本を開き、DevTools の Network タブから「Export HAR」で保存する
# 2. 復元する（出力先を省くと HAR の隣に <HAR 名>_webp/ ができる）
python3 scripts/sony_viewer/extract_pages.py ~/Downloads/download_openbook
```

```
~/Downloads/download_openbook_webp/0000.webp
~/Downloads/download_openbook_webp/0001.webp
...
```

| オプション | 意味 |
|---|---|
| `-o, --out` | 出力ディレクトリ（既定: `<HAR 名>_webp`） |
| `--limit` | 先頭 N ページだけ処理する（動作確認用） |

- 出力は `0000.webp` のようにビューアのページ番号で並ぶ。可逆 WebP（VP8L）
- 複数の本のログが混ざっている場合は `<出力先>/<contentId>/` に分かれる
- 依存: Pillow と Node（18 以上）。復号はビューアの JavaScript をそのまま使うため Node が要る

## 仕組み

### ページ束

`/image?indices=...` と `/header?indices=...` は、5 ページ分をまとめて返す。

```
[uint32 LE サイズ][データ] の繰り返し ... [uint32 LE 全体サイズ]
```

- ヘッダ束は `メタ JSON` と `ページデータ` が交互に入る
- メタは平文で、`isCrypted` / `isScrambled` / 幅・高さを持つ

### 暗号化

`isCrypted: true` のページは、ページデータが次の形になっている。

```
[uint32 ヘッダサイズ][20 バイト MAC][暗号文]
```

暗号文をビューアの固定鍵で復号すると、`[4 バイト 0][16 バイト ページ鍵][並べ替え順]` が出る。
画像本体はそのページ鍵で復号する。復号にはビューアが配信するワーカー
（`/viewer/<contentId>/decrypt`）を使う。スクリプトは HAR に入っているものを取り出すだけで、
このリポジトリには含めない。

### タイルの並べ替え

復号した画像は正しい RIFF/WEBP だが、`side` ピクセル四方のタイルが並べ替えられている。
`order[i]` 番目のタイルを `i` 番目の位置へ戻すと読める画像になる。

- 暗号化ページ: 復号したヘッダの `[20:]` が並べ替え順（先頭 uint16 が表のバイト長、次が `side`）
- 暗号化されていないページ: ビューアと同じ擬似乱数で順序を作る。`contentId` の数字と URL の `v` が種

`side` は本文が 48、マンガ（`comic`）が 152。

## ファイル構成

| ファイル | 役割 |
|---|---|
| `extract_pages.py` | CLI。HAR の解析、復号の呼び出し、保存 |
| `sony_viewer_format.py` | 束の分解、ヘッダの切り出し、順序の展開、タイルの貼り直し |
| `decrypt_runner.js` | 復号ワーカーを Node で実行する |

## 制約

- 対象は `viewer_version=14_05_00` のビューア。仕様が変われば動かなくなる
- 復号ワーカーと鍵はリポジトリに含めない。HAR から取り出す
- ストアへのログインやダウンロードの自動化は対象外。HAR は手元で取る
- ダウンロードした本体ファイル（Marlin DRM）は対象外

## テスト

```bash
python3 -m pytest tests/test_sony_viewer_format.py
```
