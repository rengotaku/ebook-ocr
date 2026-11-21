"""Sony ビューアの HAR 抽出で、欠けた復号ワーカー・メタを補う処理のテスト."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts" / "sony_viewer"))

import extract_pages as ep  # noqa: E402

WORKER = "var n=[0,1,2,3],e=[32068017,1444563582,3125118144,1434807613];"
LARGER_WORKER = WORKER + " " * 100
ERROR_WORKER = '(function (apiError) { self.postMessage(apiError); })({"code": "PARAMETER_ERROR"});'
CID = "LT000204864002476674550001"


def har_entry(url: str, text: str = "", headers: dict[str, str] | None = None) -> dict:
    return {
        "request": {
            "url": url,
            "headers": [{"name": name, "value": value} for name, value in (headers or {}).items()],
        },
        "response": {"content": {"size": len(text), "text": text, "mimeType": "application/javascript"}},
    }


def page(encrypted: bool = True, scrambled: bool = True, content_id: str = CID) -> ep.Page:
    return ep.Page(
        content_id=content_id,
        index=0,
        width=854,
        height=1280,
        scrambled=scrambled,
        encrypted=encrypted,
        image=b"",
    )


def sources(content_id: str = CID, worker: bytes | None = None, book_types: dict | None = None) -> dict:
    return {
        "worker": worker,
        "book_types": dict(book_types or {}),
        "auth_headers": {content_id: {"x-token": "dummy-token", "x-uuid": "dummy-uuid"}},
        "viewer_version": "14_05_00",
    }


class TestDecryptWorkerDetection:
    def test_recognizes_worker_with_key(self):
        assert ep.is_decrypt_worker(WORKER.encode())

    def test_rejects_error_worker(self):
        assert not ep.is_decrypt_worker(ERROR_WORKER.encode())

    def test_rejects_missing_body(self):
        assert not ep.is_decrypt_worker(None)


class TestCollectWorker:
    def test_prefers_valid_worker_even_when_error_worker_comes_last(self):
        entries = [
            har_entry(f"https://viewer.ebookstore.sony.jp/viewer/{CID}/decrypt?viewer_version=14_05_00", WORKER),
            har_entry(f"https://viewer.ebookstore.sony.jp/viewer/{CID}/decrypt?viewer_version=14_05_00", ERROR_WORKER),
        ]
        assert ep.collect(entries)["worker"].decode() == WORKER

    def test_prefers_larger_valid_worker(self):
        entries = [
            har_entry(f"https://viewer.ebookstore.sony.jp/viewer/{CID}/decrypt?viewer_version=14_05_00", WORKER),
            har_entry(f"https://viewer.ebookstore.sony.jp/viewer/{CID}/decrypt?viewer_version=14_05_00", LARGER_WORKER),
        ]
        assert ep.collect(entries)["worker"].decode() == LARGER_WORKER


class TestCollectAuthHeaders:
    def test_keeps_auth_headers_and_viewer_version(self):
        url = f"https://viewer.ebookstore.sony.jp/viewer/{CID}/image?indices=0&viewer_version=14_05_00"
        headers = {
            "x-token": "token",
            "x-uuid": "uuid",
            "x-nmr": "nmr",
            "x-use-cache": "false",
            "x-indices": "0,1,2",
            "host": "viewer.ebookstore.sony.jp",
            "accept-encoding": "gzip, br",
        }
        collected = ep.collect([har_entry(url, "image", headers)])
        assert collected["viewer_version"] == "14_05_00"
        assert collected["auth_headers"][CID] == {
            "x-token": "token",
            "x-uuid": "uuid",
            "x-nmr": "nmr",
            "x-use-cache": "false",
        }


class TestViewerUrl:
    def test_builds_decrypt_url(self):
        assert (
            ep.viewer_url(CID, "decrypt", "14_05_00")
            == f"https://viewer.ebookstore.sony.jp/viewer/{CID}/decrypt?viewer_version=14_05_00"
        )


class TestFetchMissingAssets:
    def test_fetches_worker_when_encrypted_page_needs_it(self):
        calls: list[str] = []

        def fetch(url: str, headers: dict[str, str]) -> bytes:
            calls.append(url)
            return WORKER.encode()

        collected = sources()
        ep.fetch_missing_assets(collected, [page(encrypted=True)], fetch=fetch)
        assert collected["worker"] == WORKER.encode()
        assert calls == [ep.viewer_url(CID, "decrypt", "14_05_00")]

    def test_does_not_fetch_worker_when_pages_are_plain(self):
        def fetch(url: str, headers: dict[str, str]) -> bytes:  # pragma: no cover - 呼ばれたら失敗
            raise AssertionError(url)

        collected = sources()
        ep.fetch_missing_assets(collected, [page(encrypted=False, scrambled=False)], fetch=fetch)
        assert collected["worker"] is None

    def test_does_not_fetch_worker_when_har_already_has_it(self):
        def fetch(url: str, headers: dict[str, str]) -> bytes:  # pragma: no cover - 呼ばれたら失敗
            raise AssertionError(url)

        collected = sources(worker=WORKER.encode())
        ep.fetch_missing_assets(collected, [page(encrypted=True)], fetch=fetch)
        assert collected["worker"] == WORKER.encode()

    def test_fetches_book_type_for_plain_scrambled_page(self):
        def fetch(url: str, headers: dict[str, str]) -> bytes:
            assert url.endswith(f"/{CID}/meta?viewer_version=14_05_00")
            return b'{"data": {"type": "comic"}}'

        collected = sources()
        ep.fetch_missing_assets(collected, [page(encrypted=False, scrambled=True)], fetch=fetch)
        assert collected["book_types"][CID] == "comic"

    def test_ignores_unusable_worker_response(self):
        collected = sources()
        ep.fetch_missing_assets(collected, [page(encrypted=True)], fetch=lambda url, headers: ERROR_WORKER.encode())
        assert collected["worker"] is None


class TestRequiresDecryptWorker:
    def test_true_when_a_page_is_encrypted(self):
        assert ep.requires_decrypt_worker([page(encrypted=False), page(encrypted=True)])

    def test_false_when_all_pages_are_plain(self):
        assert not ep.requires_decrypt_worker([page(encrypted=False), page(encrypted=False)])
