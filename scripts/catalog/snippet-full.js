// Reader Store 本棚の全データを 1 回で吸い出す
// 使い方: https://ebookstore.sony.jp/mybook/list?displayStatus=true を開いた状態で
//         DevTools Console に貼り付け → Enter（所要 2〜3 分）
(async () => {
  // href は ? 付き、name 属性は ? なしのクエリ文字列。どちらも受ける
  const qs = (u) => new URLSearchParams(((u || '').includes('?') ? u.split('?')[1] : u) || '');
  const sleep = (ms) => new Promise((r) => setTimeout(r, ms));
  const OUT = { fetchedAt: new Date().toISOString(), shelf: [], series: {}, history: null };
  const seen = new Set();
  let n = 0;

  for (const status of ['true', 'false']) {
    for (let p = 1; p <= 40; p++) {
      const url = `/mybook/list?displayStatus=${status}&page=${p}`;
      let res;
      try { res = await fetch(url, { credentials: 'same-origin' }); } catch (e) { console.warn('fail', url, e); break; }
      if (!res.ok) { console.warn(url, res.status); break; }
      const doc = new DOMParser().parseFromString(await res.text(), 'text/html');
      const lis = [...doc.querySelectorAll('li.bookshelfList__listBox')];
      console.log(`list ${status} p${p}: ${lis.length}`);
      if (!lis.length) break;
      for (const li of lis) {
        const a = li.querySelector('a.bookshelfList__itemListLink');
        if (!a) continue;
        const meta = qs(a.getAttribute('name'));
        const href = a.getAttribute('href') || '';
        const titleId = qs(href).get('titleId');
        const img = li.querySelector('img.bookshelfList__itemListImage');
        const row = {
          aid: meta.get('aid'),
          titleName: meta.get('titleName'),
          shelfTitle: (li.querySelector('.bookshelfList__itemTitle a') || {}).textContent?.trim() || meta.get('titleName'),
          author: meta.get('authorNm'),
          publisher: meta.get('publisherNm'),
          titleId: titleId || null,
          seriesIsOne: a.getAttribute('data-checkSeriesIsOne') === 'true',
          hasBrowserContents: meta.get('hasBrowserContents'),
          hasReaderContens: meta.get('hasReaderContens'),
          image: img ? new URL(img.getAttribute('src'), location.origin).href : null,
          displayStatus: status,
          listPage: p,
        };
        const key = row.titleId ? `S:${row.titleId}` : `A:${row.aid}`;
        if (seen.has(key)) continue;
        seen.add(key);
        OUT.shelf.push(row);
      }
      await sleep(600);
    }
  }
  console.log('本棚:', OUT.shelf.length, '件 / シリーズ詳細を取得します');

  const targets = OUT.shelf.filter((r) => r.titleId && !r.seriesIsOne);
  for (const r of targets) {
    const url = `/mybook/series/list?displayStatus=true&titleId=${r.titleId}&hasBrowserContents=true`;
    try {
      const res = await fetch(url, { credentials: 'same-origin' });
      OUT.series[r.titleId] = { status: res.status, html: res.ok ? await res.text() : null };
    } catch (e) {
      OUT.series[r.titleId] = { status: 0, error: String(e) };
    }
    n++;
    if (n % 10 === 0) console.log(`series ${n}/${targets.length}`);
    await sleep(500);
  }

  try {
    const h = await fetch('/mypage/download', { credentials: 'same-origin' });
    OUT.history = { status: h.status, html: h.ok ? await h.text() : null };
  } catch (e) {
    OUT.history = { status: 0, error: String(e) };
  }

  const blob = new Blob([JSON.stringify(OUT)], { type: 'application/json' });
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'readerstore-raw.json';
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 15000);
  console.log('完了: 本棚', OUT.shelf.length, '/ シリーズ', Object.keys(OUT.series).length,
              '/ 購入履歴', OUT.history.status, '→ readerstore-raw.json');
})();
