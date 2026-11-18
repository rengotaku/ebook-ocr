#!/usr/bin/env python3
"""本棚・シリーズ巻一覧・購入履歴を突き合わせて冊単位のカタログを作る。"""
import csv
import glob
import json
import re
import sys
from html import unescape
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from parse_mybook import parse_html, dedupe  # noqa: E402

RAW = Path('raw')


def norm(s: str) -> str:
    return re.sub(r'\s+', ' ', unescape(re.sub(r'<[^>]+>', '', s))).strip()


def parse_series(html: str, title_id: str) -> list[dict]:
    vols, seen = [], set()
    for block in re.findall(r'<li class="bookshelfList__listBox">(.*?)</li>', html, re.S):
        m = re.search(r'name="([^"]*)"', block)
        if not m:
            continue
        from urllib.parse import parse_qs
        meta = {k: v[0] for k, v in parse_qs(unescape(m.group(1))).items()}
        aid = meta.get('aid')
        if not aid or aid in seen:
            continue
        seen.add(aid)
        img = re.search(r'<img[^>]*src="([^"]*)"', block)
        vols.append({
            'aid': aid,
            'volumeTitle': meta.get('titleName'),
            'author': meta.get('authorNm'),
            'publisher': meta.get('publisherNm'),
            'titleId': title_id,
            'coverUrl': 'https://ebookstore.sony.jp' + img.group(1) if img else None,
        })
    return vols


def parse_history(html: str) -> dict:
    """1 注文の中に複数商品が入るので、商品単位（contentDetailBox）で切り出す。"""
    out = {}
    for order in html.split('<div class="purchaseHistory__itemBoxWrapper">')[1:]:
        dm = re.search(r'purchaseHistory__paymentDate">(\d{4})年(\d{1,2})月(\d{1,2})日', order)
        date = f'{dm.group(1)}-{int(dm.group(2)):02d}-{int(dm.group(3)):02d}' if dm else None
        for chunk in order.split('<div class="purchaseHistory__contentDetailBox">')[1:]:
            am = re.search(r'name="aid" value="([A-Z0-9]+)"', chunk)
            if not am:
                continue
            title = re.search(r'purchaseHistory__detailTitileText">([^<]*)', chunk)
            label = re.search(r'name="labelName" value="([^"]*)"', chunk)
            xl = re.search(r'name="rsThumbnailLL" value="([^"]*)"', chunk)
            price_raw = ''.join(re.findall(r'purchaseHistory__detailIitemPrice">([^<]*)', chunk))
            price = re.sub(r'[^0-9]', '', price_raw) or None
            texts = [norm(t) for t in re.findall(r'purchaseHistory__detailText">([^<]*)', chunk)]
            texts = [t for t in texts if t and t != '/']
            out.setdefault(am.group(1), {
                'purchaseDate': date,
                'label': label.group(1) if label else None,
                'coverXl': ('https://ebookstore.sony.jp' + xl.group(1)) if xl else None,
                'detailTitle': norm(title.group(1)) if title else None,
                'publisher': texts[0] if texts else None,
                'seriesLabel': texts[1] if len(texts) > 1 else None,
                'price': price,
            })
    return out


def main() -> None:
    shelf_rows = []
    for f in sorted(glob.glob(str(RAW / 'shelf_true_p*.html'))):
        p = int(re.search(r'_p(\d+)', f).group(1))
        shelf_rows += parse_html(Path(f).read_text(encoding='utf-8'), p, 'true')
    for f in sorted(glob.glob(str(RAW / 'shelf_false_p*.html'))):
        p = int(re.search(r'_p(\d+)', f).group(1))
        shelf_rows += parse_html(Path(f).read_text(encoding='utf-8'), p, 'false')
    shelf = dedupe(shelf_rows)

    books: dict[str, dict] = {}
    for entry in shelf:
        tid = entry.get('titleId')
        path = RAW / 'series' / f'series_{tid}.html' if tid else None
        vols = []
        if path and path.exists() and path.stat().st_size > 5000:
            html_txt = path.read_text(encoding='utf-8')
            # シリーズページに飛べず本棚一覧が返ることがあるので、見出しで判定する
            if '本棚（シリーズ）' in html_txt[:6000]:
                vols = parse_series(html_txt, tid)
                for extra in sorted((RAW / 'series').glob(f'series_{tid}_p*.html')):
                    etext = extra.read_text(encoding='utf-8')
                    if '本棚（シリーズ）' in etext[:6000]:
                        have = {v['aid'] for v in vols}
                        vols += [v for v in parse_series(etext, tid) if v['aid'] not in have]
        if not vols:
            vols = [{
                'aid': entry['aid'], 'volumeTitle': entry['titleName'],
                'author': entry['author'], 'publisher': entry['publisher'],
                'titleId': tid, 'coverUrl': entry['image'],
            }]
        for v in vols:
            row = books.setdefault(v['aid'], {})
            row.update({
                'seriesTitle': entry['shelfTitle'],
                'volumeTitle': v['volumeTitle'],
                'author': v['author'],
                'publisher': v['publisher'],
                'titleId': tid,
                'aid': v['aid'],
                'coverUrl': row.get('coverUrl') or v['coverUrl'],
                'shelfStatus': '本棚' if entry['displayStatus'] == 'true' else '非表示',
                'hasBrowserContents': entry['hasBrowserContents'],
                'hasReaderContens': entry['hasReaderContens'],
            })

    history = {}
    for f in sorted(glob.glob(str(RAW / 'history_p*.html'))):
        history.update(parse_history(Path(f).read_text(encoding='utf-8')))

    for aid, row in books.items():
        h = history.get(aid) or {}
        row['purchaseDate'] = h.get('purchaseDate')
        row['price'] = h.get('price')
        row['label'] = h.get('label')
        row['coverXl'] = h.get('coverXl')
        if row.get('coverXl') and '/photo/' not in row['coverXl']:
            row['coverXl'] = None
        cover_url = row.get('coverUrl') or ''
        if not row['coverXl'] and cover_url.endswith('_LARGE.jpg'):
            row['coverXl'] = cover_url.replace('_LARGE.jpg', '_XLARGE.jpg')

    rows = sorted(books.values(), key=lambda r: (r.get('seriesTitle') or '', r.get('volumeTitle') or ''))
    out = Path('out')
    out.mkdir(exist_ok=True)
    (out / 'readerstore-books.json').write_text(json.dumps({
        'generatedAt': __import__('datetime').datetime.now().astimezone().isoformat(timespec='seconds'),
        'seriesCount': len({r['titleId'] for r in rows}),
        'bookCount': len(rows),
        'withPurchaseDate': sum(1 for r in rows if r.get('purchaseDate')),
        'books': rows,
    }, ensure_ascii=False, indent=2), encoding='utf-8')

    cols = ['seriesTitle', 'volumeTitle', 'author', 'publisher', 'purchaseDate', 'price',
            'label', 'titleId', 'aid', 'shelfStatus', 'hasBrowserContents',
            'hasReaderContens', 'coverXl', 'coverUrl']
    with (out / 'readerstore-books.csv').open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols, extrasaction='ignore')
        w.writeheader()
        w.writerows(rows)

    print(f'series={len({r["titleId"] for r in rows})} books={len(rows)} '
          f'withDate={sum(1 for r in rows if r.get("purchaseDate"))} historyAids={len(history)}')


if __name__ == '__main__':
    main()
