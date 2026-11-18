#!/usr/bin/env python3
"""Reader Store 本棚 HTML を JSON / CSV に変換する。"""
import argparse
import csv
import json
import re
from html import unescape
from pathlib import Path
from urllib.parse import urlsplit

LI_RE = re.compile(r'<li class="bookshelfList__listBox">(.*?)</li>', re.S)
A_RE = re.compile(r'<a\b[^>]*?name="([^"]*)"[^>]*?>(.*?)</a>', re.S)
IMG_RE = re.compile(r'<img[^>]*class="bookshelfList__itemListImage"[^>]*>')
SRC_RE = re.compile(r'src="([^"]*)"')
TITLE_LINK_RE = re.compile(
    r'<p class="bookshelfList__itemTitle">\s*<a\b[^>]*>(.*?)</a>', re.S
)
HREF_RE = re.compile(r'href="([^"]*)"')
TOTAL_RE = re.compile(r'（(\d+)件）')
PAGER_RE = re.compile(r'page=(\d+)"')


def parse_qs(raw: str) -> dict:
    from urllib.parse import parse_qs as _p
    return {k: v[0] for k, v in _p(unescape(raw), keep_blank_values=True).items()}


def strip_tags(s: str) -> str:
    return unescape(re.sub(r'<[^>]+>', '', s)).strip()


def parse_html(html: str, list_page: int | None = None, status: str = 'true') -> list[dict]:
    rows = []
    for block in LI_RE.findall(html):
        m = A_RE.search(block)
        if not m:
            continue
        meta = parse_qs(m.group(1))
        href_m = HREF_RE.search(m.group(0))
        href = unescape(href_m.group(1)) if href_m else ''
        # href はパス付き（/mybook/series/list?titleId=...）なので、クエリだけを見る
        title_id = parse_qs(urlsplit(href).query).get('titleId')
        img_m = IMG_RE.search(block)
        img = SRC_RE.search(img_m.group(0)).group(1) if img_m else None
        if img and img.startswith('/'):
            img = 'https://ebookstore.sony.jp' + img
        title_m = TITLE_LINK_RE.search(block)
        title = strip_tags(title_m.group(1)) if title_m else meta.get('titleName')
        one_m = re.search(r'data-checkSeriesIsOne="([^"]*)"', block)
        rows.append({
            'shelfTitle': title,
            'seriesIsOne': (one_m.group(1) == 'true') if one_m else None,
            'titleName': meta.get('titleName'),
            'author': meta.get('authorNm'),
            'publisher': meta.get('publisherNm'),
            'titleId': title_id,
            'aid': meta.get('aid'),
            'isSeries': bool(title_id),
            'hasBrowserContents': meta.get('hasBrowserContents'),
            'hasReaderContens': meta.get('hasReaderContens'),
            'image': img,
            'displayStatus': status,
            'listPage': list_page,
        })
    return rows


def dedupe(rows: list[dict]) -> list[dict]:
    seen, out = set(), []
    for r in rows:
        key = f"S:{r['titleId']}" if r['titleId'] else f"A:{r['aid']}"
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def write_csv(rows: list[dict], path: Path) -> None:
    cols = ['shelfTitle', 'titleName', 'author', 'publisher', 'titleId', 'aid',
            'isSeries', 'seriesIsOne', 'hasBrowserContents', 'hasReaderContens', 'image',
            'displayStatus', 'listPage']
    with path.open('w', encoding='utf-8', newline='') as f:
        w = csv.DictWriter(f, fieldnames=cols)
        w.writeheader()
        w.writerows(rows)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('html', help='本棚ページの HTML ファイル')
    ap.add_argument('--out-dir', default='.')
    ap.add_argument('--page', type=int, default=None)
    args = ap.parse_args()

    html = Path(args.html).read_text(encoding='utf-8')
    rows = parse_html(html, args.page)
    total = TOTAL_RE.search(html)
    pages = sorted({int(x) for x in PAGER_RE.findall(html)})

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    (out / 'shelf.json').write_text(
        json.dumps({'count': len(rows), 'total': int(total.group(1)) if total else None,
                    'pages': pages, 'rows': rows}, ensure_ascii=False, indent=2),
        encoding='utf-8')
    write_csv(rows, out / 'shelf.csv')

    print(f'rows={len(rows)} total={total.group(1) if total else "-"} pages={pages}')
    for r in rows[:3]:
        print(json.dumps(r, ensure_ascii=False))


if __name__ == '__main__':
    main()
