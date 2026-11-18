#!/usr/bin/env python3
"""本棚 JSON の表紙画像を covers/ に保存する。"""
import argparse
import json
import time
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/156.0 Safari/537.36'


def fetch(url: str) -> tuple[int, bytes, str]:
    req = Request(url, headers={'User-Agent': UA})
    try:
        with urlopen(req, timeout=30) as r:
            return r.status, r.read(), r.headers.get('Content-Type', '')
    except HTTPError as e:
        return e.code, b'', e.headers.get('Content-Type', '') if e.headers else ''
    except URLError as e:
        return 0, b'', str(e.reason)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('json', help='表紙 URL を含む JSON')
    ap.add_argument('--out-dir', default='out')
    ap.add_argument('--sleep', type=float, default=0.4)
    ap.add_argument('--limit', type=int, default=0)
    args = ap.parse_args()

    data = json.loads(Path(args.json).read_text(encoding='utf-8'))
    rows = data.get('books') or data.get('rows') or data.get('shelf') or []
    target = Path(args.out_dir) / 'covers'
    target.mkdir(parents=True, exist_ok=True)

    ok = skip = fail = 0
    for i, r in enumerate(rows, 1):
        url = r.get('coverXl') or r.get('coverUrl') or r.get('image')
        if not url or len(url) < 40:
            skip += 1
            continue
        name = (r.get('aid') or f'row{i}') + '.jpg'
        path = target / name
        if path.exists() and path.stat().st_size > 0:
            skip += 1
            continue
        try:
            status, body, ctype = fetch(url)
            if status == 200 and body[:2] == b'\xff\xd8':
                path.write_bytes(body)
                ok += 1
            elif status == 404 and '_XLARGE.jpg' in url:
                status, body, ctype = fetch(url.replace('_XLARGE.jpg', '_LARGE.jpg'))
                if status == 200 and body[:2] == b'\xff\xd8':
                    path.write_bytes(body)
                    ok += 1
                else:
                    fail += 1
                    print(f'NG(alt) {status} {url}')
            else:
                fail += 1
                print(f'NG {status} {ctype} {url}')
        except Exception as e:  # noqa: BLE001
            fail += 1
            print(f'ERR {e} {url}')
        if args.limit and i >= args.limit:
            break
        time.sleep(args.sleep)

    print(f'saved={ok} skipped={skip} failed={fail} dir={target}')


if __name__ == '__main__':
    main()
