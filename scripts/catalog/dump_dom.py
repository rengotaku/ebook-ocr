#!/usr/bin/env python3
"""ヘッドレス Chrome（プロファイル複製）で URL を取得し DOM を保存する。

使い方: tasks ファイルに "name<TAB>url" を 1 行ずつ書き、標準入力から渡す。
  例) dump_dom.py raw/ < tasks.tsv
"""
import argparse
import os
import shutil
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

CHROME = '/opt/google/chrome/chrome'
SRC_LOCAL_STATE = Path.home() / '.config/google-chrome/Local State'
SRC_COOKIES = Path.home() / '.config/google-chrome/Default/Cookies'
FLAGS = [
    '--headless=new', '--no-first-run', '--no-default-browser-check',
    '--disable-gpu', '--disable-dev-shm-usage', '--disable-extensions',
    '--disable-background-networking', '--disable-sync', '--no-pings',
    '--disable-features=Translate,MediaRouter',
]


def make_profiles(root: Path, n: int) -> list[Path]:
    profiles = []
    for i in range(n):
        d = root / f'wp{i}'
        default = d / 'Default'
        if not default.exists():
            default.mkdir(parents=True, exist_ok=True)
            shutil.copy2(SRC_LOCAL_STATE, d / 'Local State')
            for suffix in ('', '-wal', '-shm'):
                src = Path(str(SRC_COOKIES) + suffix)
                if src.exists():
                    shutil.copy2(src, default / f'Cookies{suffix}')
        profiles.append(d)
    return profiles


def dump(profile: Path, url: str, timeout: int) -> tuple[str, int]:
    cmd = [CHROME, *FLAGS, f'--user-data-dir={profile}', '--dump-dom', url]
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=timeout)
        return p.stdout.decode('utf-8', 'replace'), p.returncode
    except subprocess.TimeoutExpired:
        return '', -1


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument('out_dir')
    ap.add_argument('--workers', type=int, default=3)
    ap.add_argument('--timeout', type=int, default=120)
    ap.add_argument('--profile-root', default='./profiles')
    args = ap.parse_args()

    tasks = []
    for line in sys.stdin:
        line = line.rstrip('\n')
        if not line or '\t' not in line:
            continue
        name, url = line.split('\t', 1)
        tasks.append((name, url))

    out = Path(args.out_dir)
    out.mkdir(parents=True, exist_ok=True)
    profiles = make_profiles(Path(args.profile_root), args.workers)

    def work(idx_task):
        idx, (name, url) = idx_task
        html, rc = dump(profiles[idx % len(profiles)], url, args.timeout)
        path = out / f'{name}.html'
        path.write_text(html, encoding='utf-8')
        return name, rc, len(html)

    with ThreadPoolExecutor(max_workers=args.workers) as ex:
        for name, rc, size in ex.map(work, enumerate(tasks)):
            print(f'{name}\trc={rc}\tsize={size}', flush=True)


if __name__ == '__main__':
    main()
