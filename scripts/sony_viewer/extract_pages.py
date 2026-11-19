#!/usr/bin/env python3
"""Sony 電子書籍ビューアの HAR からページ画像を復元する.

使い方::

    python3 scripts/sony_viewer/extract_pages.py download_openbook -o pages

HAR はブラウザの DevTools から「Export HAR」で保存したもの。
出力は ``pages/0000.webp`` のようにビューアのページ番号で並ぶ。
復号には Node（18 以上）を使う。詳しい形式は同じディレクトリの README.md を参照。
"""

from __future__ import annotations

import argparse
import base64
import io
import json
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import sony_viewer_format as fmt  # noqa: E402

RUNNER = Path(__file__).resolve().parent / "decrypt_runner.js"


@dataclass
class Page:
    """1 ページ分の材料."""

    content_id: str
    index: int
    width: int
    height: int
    scrambled: bool
    encrypted: bool
    image: bytes
    header: bytes | None = None
    mimetype: str | None = None


def read_har(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)["log"]["entries"]


def entry_body(entry: dict) -> bytes:
    content = entry["response"]["content"]
    if not content.get("size"):
        return b""
    text = content.get("text", "")
    if content.get("encoding") == "base64":
        return base64.b64decode(text)
    return text.encode("utf-8")


def content_id_of(url: str) -> str:
    """``/viewer/<contentId>/image?...`` から contentId を取り出す."""
    parts = urlsplit(url).path.split("/")
    return parts[-2] if len(parts) >= 2 else ""


def query_indices(url: str) -> str | None:
    values = parse_qs(urlsplit(url).query).get("indices")
    return values[0] if values else None


def json_of(entry: dict) -> dict:
    try:
        return json.loads(entry["response"]["content"]["text"])
    except (KeyError, json.JSONDecodeError):
        return {}


def collect(entries: list[dict]) -> dict:
    """HAR から束・メタ・復号ワーカーを集める."""
    sources: dict = {
        "header_bundles": {},
        "image_bundles": {},
        "page_metas": {},
        "book_types": {},
        "seed_shifts": {},
        "worker": None,
    }
    for entry in entries:
        url = entry["request"]["url"]
        if not url.startswith("https://viewer.ebookstore.sony.jp/viewer/"):
            continue
        body = entry_body(entry)
        content_id = content_id_of(url)
        path = urlsplit(url).path
        indices = query_indices(url)

        if body and path.endswith("/decrypt"):
            sources["worker"] = body
        elif body and path.endswith("/header") and indices is not None:
            sources["header_bundles"][(content_id, indices)] = body
        elif body and path.endswith("/image") and indices is not None:
            key = (content_id, indices)
            if len(body) > len(sources["image_bundles"].get(key, b"")):
                sources["image_bundles"][key] = body
            shift = parse_qs(urlsplit(url).query).get("v")
            if shift:
                sources["seed_shifts"][content_id] = int(shift[0])
        elif body and path.endswith("/image_url") and indices is not None:
            metas = json_of(entry).get("data", {}).get("meta")
            if metas:
                sources["page_metas"][(content_id, indices)] = metas
        elif body and path.endswith("/meta"):
            book_type = json_of(entry).get("data", {}).get("type")
            if book_type:
                sources["book_types"][content_id] = book_type
    return sources


def parse_header_bundle(body: bytes) -> tuple[list[dict], list[bytes]]:
    metas: list[dict] = []
    pages: list[bytes] = []
    payloads = fmt.split_bundle(body)
    for position in range(0, len(payloads) - 1, 2):
        metas.append(fmt.parse_meta(payloads[position]))
        pages.append(payloads[position + 1])
    return metas, pages


def build_pages(bundle_key: tuple[str, str], image_body: bytes, sources: dict) -> list[Page]:
    """1 つの画像束からページのリストを作る."""
    content_id, indices = bundle_key
    header_metas, header_pages = ([], [])
    if bundle_key in sources["header_bundles"]:
        header_metas, header_pages = parse_header_bundle(sources["header_bundles"][bundle_key])
    fallback = sources["page_metas"].get(bundle_key, [])

    pages: list[Page] = []
    for position, chunk in enumerate(fmt.split_bundle(image_body)):
        meta = header_metas[position] if position < len(header_metas) else None
        if meta is None and position < len(fallback):
            meta = fallback[position]
        if meta is None:
            with Image.open(io.BytesIO(chunk)) as image:
                meta = {"width": image.width, "height": image.height, "isCrypted": False, "isScrambled": True}
        header = header_pages[position] if position < len(header_pages) else None
        if meta.get("isCrypted") and header is None:
            continue
        pages.append(
            Page(
                content_id=content_id,
                index=int(indices.split(",")[position]),
                width=int(meta["width"]),
                height=int(meta["height"]),
                scrambled=bool(meta.get("isScrambled", True)),
                encrypted=bool(meta.get("isCrypted", False)),
                image=chunk,
                header=header,
                mimetype=meta.get("mimetype"),
            )
        )
    return pages


def deduplicate(pages: list[Page]) -> list[Page]:
    """同じ本の同じページ番号が複数の束に出てくるときは、大きい画像だけを残す.

    HAR にはサムネイル一覧用の小さい束（144x192 など）も混ざる。束の並び順によっては
    後から来たサムネイルが本文ページを上書きするため、面積で選ぶ。
    複数の本のログが混ざっていても壊れないよう、本（content_id）とページ番号の組で見る。
    """
    best: dict[tuple[str, int], Page] = {}
    for page in pages:
        key = (page.content_id, page.index)
        current = best.get(key)
        if current is None or page.width * page.height > current.width * current.height:
            best[key] = page
    return [best[key] for key in sorted(best)]


def decrypt_pages(pages: list[Page], worker: bytes, workdir: Path) -> dict[int, tuple[bytes, bytes]]:
    """暗号化ページを Node の復号ワーカーに通す."""
    targets = [page for page in pages if page.encrypted]
    if not targets:
        return {}
    node = shutil.which("node")
    if node is None:
        raise SystemExit("復号には Node（18 以上）が必要。PATH に node を入れてから実行する")

    worker_path = workdir / "decrypt_worker.js"
    worker_path.write_bytes(worker)

    jobs = []
    for page in targets:
        header_path = workdir / f"header_{page.index}.bin"
        image_path = workdir / f"image_{page.index}.bin"
        header_path.write_bytes(page.header or b"")
        image_path.write_bytes(page.image)
        jobs.append({"id": str(page.index), "header": str(header_path), "image": str(image_path)})

    jobs_path = workdir / "jobs.jsonl"
    jobs_path.write_text("\n".join(json.dumps(job) for job in jobs), encoding="utf-8")
    result = subprocess.run(
        [node, str(RUNNER), str(worker_path), str(jobs_path), str(workdir)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        raise SystemExit(f"復号に失敗した: {result.stderr.strip()}")

    recovered: dict[int, tuple[bytes, bytes]] = {}
    for line in result.stdout.splitlines():
        record = json.loads(line)
        if record.get("error") or not record.get("ok"):
            raise SystemExit(f"ページ {record.get('id')} の復号に失敗した: {record}")
        recovered[int(record["id"])] = (
            (workdir / f"{record['id']}.webp.bin").read_bytes(),
            (workdir / f"{record['id']}.order.bin").read_bytes(),
        )
    return recovered


def order_for(page: Page, recovered: dict, sources: dict) -> tuple[list[int], int]:
    if page.encrypted:
        return fmt.unpack_order(recovered[page.index][1])
    side = fmt.side_length_for(sources["book_types"].get(page.content_id), page.mimetype)
    return fmt.build_sample_order(
        page.content_id,
        sources["seed_shifts"].get(page.content_id, 1),
        page.width,
        page.height,
        side,
    )


def save_pages(pages: list[Page], recovered: dict, out_dir: Path, sources: dict) -> int:
    written = 0
    for page in pages:
        data = recovered[page.index][0] if page.encrypted else page.image
        with Image.open(io.BytesIO(data)) as image:
            image.load()
            if page.scrambled:
                order, side = order_for(page, recovered, sources)
                fixed = fmt.descramble(image, order, side, (page.width, page.height))
            else:
                fixed = image.convert("RGBA")
        target = out_dir / f"{page.index:04d}.webp"
        target.parent.mkdir(parents=True, exist_ok=True)
        fixed.save(target, lossless=True, quality=100, method=6)
        written += 1
    return written


def default_output(har: Path) -> Path:
    """HAR の隣に ``<HAR 名>_webp`` を作る."""
    return har.with_name(f"{har.name}_webp")


def output_dir(base: Path, content_id: str, multiple: bool) -> Path:
    return base / content_id if multiple else base


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Sony ビューアの HAR からページ画像を復元する")
    parser.add_argument("har", type=Path, help="DevTools で書き出した HAR")
    parser.add_argument("-o", "--out", type=Path, help="出力ディレクトリ（既定: <HAR 名>_webp）")
    parser.add_argument("--limit", type=int, help="先頭 N ページだけ処理する（動作確認用）")
    args = parser.parse_args(argv)
    out_dir = args.out or default_output(args.har)

    sources = collect(read_har(args.har))
    if not sources["image_bundles"]:
        raise SystemExit("HAR にページ画像が入っていない")
    if sources["worker"] is None:
        raise SystemExit("HAR に復号ワーカー（/decrypt）が入っていない。通信ログの取り直しが要る")

    pages: list[Page] = []
    for bundle_key, body in sources["image_bundles"].items():
        pages.extend(build_pages(bundle_key, body, sources))
    pages = deduplicate(pages)
    if args.limit:
        pages = pages[: args.limit]

    content_ids = sorted({page.content_id for page in pages})
    with tempfile.TemporaryDirectory(prefix="sony_viewer_") as tmp:
        recovered = decrypt_pages(pages, sources["worker"], Path(tmp))
        written = 0
        for content_id in content_ids:
            group = [page for page in pages if page.content_id == content_id]
            written += save_pages(group, recovered, output_dir(out_dir, content_id, len(content_ids) > 1), sources)
    print(f"{written} ページを {out_dir.resolve()} に書き出した")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
