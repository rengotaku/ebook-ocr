# 蔵書カタログの抽出

Reader Store（`ebookstore.sony.jp`）の蔵書を、書誌・表紙・購入日までローカルに落とす。本文（電子書籍ファイルの中身）は Marlin DRM で暗号化されていて取得できないため対象外。

出力は 1 冊 1 行の JSON / CSV、表紙画像のディレクトリ、表紙つきの一覧 HTML。

## ファイル

| ファイル | 役割 |
|---|---|
| `dump_dom.py` | ログイン済みプロファイルの複製でヘッドレス Chrome を起動し、URL の DOM を保存する |
| `parse_mybook.py` | 本棚ページの HTML を 1 冊 1 行に変換する |
| `build_books.py` | 本棚・シリーズ巻一覧・購入履歴を突き合わせてカタログを作る |
| `download_covers.py` | 表紙画像を `covers/<商品ID>.jpg` に保存する |
| `gen_catalog.py` | 表紙つきの一覧 HTML を生成する |
| `snippet-full.js` | ブラウザの DevTools コンソールに貼ると、同じデータを 1 回で吸い出す（Chrome を再起動したくない場合用） |

## 前提

- Python 3.10 以上。外部ライブラリは使っていない（標準ライブラリのみ）
- Linux の Google Chrome（`/opt/google/chrome/chrome`）。パスは `dump_dom.py` の `CHROME` で変えられる
- 自分のアカウントでログイン済みの Chrome プロファイルがあること
- `dump_dom.py` はプロファイルの `Cookies` と `Local State` を複製して使う。元のプロファイルは書き換えない。Chrome を起動したままだと `Cookies` がロックされる場合があるので、そのときは一度 Chrome を終了してから実行する

## 実行手順

```bash
# 1. 本棚の全ページを取る（24 件/ページ）
printf '%s\t%s\n' \
  'shelf_true_p1' 'https://ebookstore.sony.jp/mybook/list?displayStatus=true&page=1' \
  'shelf_true_p2' 'https://ebookstore.sony.jp/mybook/list?displayStatus=true&page=2' \
  | python3 dump_dom.py raw

# 2. 非表示にした本も取る（displayStatus=false）

# 3. 購入履歴を全ページ取る（8 注文/ページ）
for p in $(seq 1 29); do
  printf 'history_p%s\thttps://ebookstore.sony.jp/mypage/download?page=%s\n' "$p" "$p"
done | python3 dump_dom.py raw

# 4. シリーズの巻一覧を取る（本棚の href から titleId を集める）

# 5. カタログを作る
python3 parse_mybook.py raw/shelf_true_p1.html --page 1 --out-dir out
python3 build_books.py

# 6. 表紙を落として一覧 HTML を作る
python3 download_covers.py out/readerstore-books.json --out-dir out
python3 gen_catalog.py
```

## 出力

```
out/
  readerstore-books.json   1 冊 1 レコード（304 冊）
  readerstore-books.csv    同じ内容の CSV
  catalog.html             表紙つき一覧（絞り込みつき）
  covers/<商品ID>.jpg      表紙画像
raw/
  shelf_*.html             本棚のページ
  series/*.html            シリーズの巻一覧
  history_p*.html          購入履歴
```

## 実測値

| 項目 | 値 |
|---|---|
| 本棚のエントリ | 172 件 |
| 非表示にした本 | 31 件 |
| 巻に展開した結果 | 304 冊 / 202 シリーズ |
| 購入日が埋まった冊数 | 199 冊（65%） |
| 表紙 | 304 枚（XLARGE 323×500 が大半、無い商品は LARGE 161×250） |
| 処理時間 | 本棚 8 ページで約 30 秒、シリーズ 202 件で約 6 分、表紙 304 枚で約 2 分 |

## 注意

- 取得は 1 リクエスト 0.4〜0.6 秒あけている。並列は 2〜3 まで。ストアの規約には過大な通信を禁じる条項（第21条(15)）がある
- 本文のダウンロード（`/mybook/download`）は対象外。復号は行わない
- シリーズの巻一覧は、まれに本棚一覧がそのまま返る。`本棚（シリーズ）` という見出しが入っているかで判定し、入っていなければ 1 冊だけのシリーズとして扱う
- ページ送りのあるシリーズは 24 件で切れるので、`page=2` 以降も取る

## 由来

このディレクトリのスクリプトは issue #67 の本文に書かれていたものをそのまま移した。取得できるデータと取得できないデータの調査は #66。
