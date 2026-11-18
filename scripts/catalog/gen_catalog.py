#!/usr/bin/env python3
"""readerstore-books.json から表紙つきの一覧 HTML を作る。"""
import html
import json
from pathlib import Path

d = json.loads(Path('out/readerstore-books.json').read_text(encoding='utf-8'))
books = d['books']


def esc(s) -> str:
    return html.escape(str(s)) if s else ''


cards = []
for b in books:
    meta = ' / '.join(x for x in (esc(b.get('author')), esc(b.get('publisher'))) if x)
    date = esc(b.get('purchaseDate') or '購入日不明')
    price = f"¥{esc(b['price'])}" if b.get('price') else ''
    label = esc(b.get('label'))
    series = esc(b.get('seriesTitle'))
    vol = esc(b.get('volumeTitle'))
    cards.append(f'''<article class="card" data-q="{esc(series)} {esc(b.get('author'))} {vol}">
  <img src="covers/{esc(b['aid'])}.jpg" alt="{vol}" loading="lazy" width="323" height="500">
  <h2>{series}</h2>
  <p class="vol">{vol}</p>
  <p class="meta">{meta}</p>
  <p class="sub">{label}</p>
  <p class="date">{date} <span class="price">{price}</span></p>
  <p class="shelf">{esc(b.get('shelfStatus'))}</p>
</article>''')

with_date = sum(1 for b in books if b.get('purchaseDate'))
html_out = f'''<!DOCTYPE html>
<html lang="ja"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Reader Store 蔵書カタログ（{len(books)}冊）</title>
<style>
:root{{--bg:#141416;--fg:#e8e6e3;--dim:#9a9691;--line:#2a2a2e;--accent:#7fb3d5}}
*{{box-sizing:border-box}}
body{{margin:0;background:var(--bg);color:var(--fg);font-family:system-ui,"Noto Sans JP",sans-serif}}
header{{position:sticky;top:0;background:rgba(20,20,22,.94);border-bottom:1px solid var(--line);padding:16px 20px;backdrop-filter:blur(8px);z-index:2}}
h1{{margin:0 0 4px;font-size:17px;font-weight:600}}
.stats{{color:var(--dim);font-size:12px}}
input{{margin-top:10px;width:min(420px,100%);padding:8px 10px;border-radius:6px;border:1px solid var(--line);background:#1c1c20;color:var(--fg);font-size:14px}}
main{{display:grid;grid-template-columns:repeat(auto-fill,minmax(158px,1fr));gap:18px;padding:20px}}
.card{{margin:0}}
.card img{{width:100%;height:auto;display:block;border-radius:3px;background:#222;box-shadow:0 2px 10px rgba(0,0,0,.45)}}
h2{{font-size:13px;font-weight:600;margin:8px 0 1px;line-height:1.35}}
.vol{{font-size:11px;color:var(--dim);margin:0 0 4px;line-height:1.3}}
.meta{{font-size:11px;color:var(--dim);margin:0;line-height:1.3}}
.sub{{font-size:10px;color:#6f6b67;margin:2px 0 0;line-height:1.3}}
.date{{font-size:11px;margin:6px 0 0;color:var(--accent);font-variant-numeric:tabular-nums}}
.price{{color:var(--dim)}}
.shelf{{font-size:10px;color:#6f6b67;margin:1px 0 0}}
.hidden{{display:none}}
</style></head><body>
<header>
  <h1>Reader Store 蔵書カタログ</h1>
  <p class="stats">{len(books)} 冊 / {d['seriesCount']} シリーズ・シリーズ未展開 0・購入日あり {with_date} 冊（{with_date*100//len(books)}%）</p>
  <input id="q" type="search" placeholder="書名・著者で絞り込み" autocomplete="off">
</header>
<main id="grid">
{''.join(cards)}
</main>
<script>
const q = document.getElementById('q');
q.addEventListener('input', () => {{
  const t = q.value.trim().toLowerCase();
  for (const c of document.querySelectorAll('.card'))
    c.classList.toggle('hidden', t && !c.dataset.q.toLowerCase().includes(t));
}});
</script>
</body></html>'''

Path('out/catalog.html').write_text(html_out, encoding='utf-8')
print(f'catalog.html written: {len(books)} cards, {with_date} with date')
