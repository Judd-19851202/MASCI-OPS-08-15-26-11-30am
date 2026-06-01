"""Sprint 1G · Photo Viewer Forensic Remediation regression tests.

Authorized scope: validate the fix for the production lightbox failure
"Photo data unavailable or corrupt." The defect was that
``get_photo_raw`` and ``get_photo_raw_batch`` returned the raw R2
pointer (``photo://bucket/key``) as the ``data_url`` field, but the
frontend lightbox's renderable check only accepts strings starting
with ``data:image/``, ``blob:``, or ``http``. The fix is to mint a
short-lived presigned HTTPS URL when the source ref is an R2 pointer,
while preserving the legacy base64 branch for any pre-migration
records.

These tests run against the in-memory FakeDb harness used by the
existing job-photos test suite — they exercise the route handler
logic in isolation without needing a real R2 client. The presign call
is monkey-patched to a synthetic HTTPS URL so the tests run offline
and deterministically.
"""
from __future__ import annotations

import asyncio
import os
import sys
from typing import Any, Dict, List

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class _FakeAsyncCursor:
    def __init__(self, docs: List[Dict[str, Any]]):
        self._docs = docs

    async def to_list(self, length: int | None = None):
        return list(self._docs) if length is None else list(self._docs)[:length]


class _FakeCollection:
    def __init__(self, docs: List[Dict[str, Any]] | None = None):
        self._docs = docs or []

    async def find_one(self, query, projection=None):
        for d in self._docs:
            if all(d.get(k) == v for k, v in query.items()):
                if not projection:
                    return dict(d)
                proj_no_id = {k: v for k, v in projection.items() if k != "_id"}
                if proj_no_id:
                    return {k: d.get(k) for k in proj_no_id.keys() if k in d}
                return {k: v for k, v in d.items() if k != "_id"}
        return None

    def find(self, query=None, projection=None):
        query = query or {}
        out = []
        for d in self._docs:
            ok = True
            for k, v in query.items():
                if isinstance(v, dict) and "$in" in v:
                    if d.get(k) not in v["$in"]:
                        ok = False
                        break
                elif d.get(k) != v:
                    ok = False
                    break
            if ok:
                out.append(dict(d))
        return _FakeAsyncCursor(out)


class _FakeDb:
    def __init__(self):
        self.job_photos = _FakeCollection([])
        self.daily_reports = _FakeCollection([])

    def __getitem__(self, name: str):
        return getattr(self, name, _FakeCollection([]))


def _run(coro):
    return asyncio.run(coro)


# ──────────────────────────────────────────────────────────────────────
# Helpers — build the registered router and pull out the raw handler.
# ──────────────────────────────────────────────────────────────────────
def _get_handlers(db, monkeypatch):
    """Register the job-photos router and harvest the underlying
    handler functions so we can unit-test them without spinning up
    FastAPI/uvicorn. Monkeypatches ``compute_pm_scope`` to grant the
    test caller access to every project."""
    from routes import job_photos as jp_mod
    from fastapi import FastAPI

    class _AllAllowingScope:
        def allows(self, project_number):
            return True

    async def _allow_all(_db, _actor):
        return _AllAllowingScope()

    monkeypatch.setattr(jp_mod, "compute_pm_scope", _allow_all)

    app = FastAPI()
    async def _require_caller():
        return {"role": "admin"}
    async def _noop_send(*a, **kw):
        return None
    jp_mod.attach_routes(app, db, _require_caller, _noop_send)
    handlers: Dict[tuple, Any] = {}
    for r in jp_mod.router.routes:
        if hasattr(r, "endpoint") and hasattr(r, "path") and hasattr(r, "methods"):
            handlers[(r.path, tuple(sorted(r.methods)))] = r.endpoint
    return handlers


# ──────────────────────────────────────────────────────────────────────
# 1 · /raw must return a presigned HTTPS URL for photo:// refs
# ──────────────────────────────────────────────────────────────────────
def test_raw_photo_with_r2_ref_returns_presigned_https_url(monkeypatch):
    """The production-defect scenario: source record stores
    ``photo://masci-hub/photos/.../abc.jpg``; the resolver returns an
    HTTPS presigned URL to the frontend so the lightbox's renderable
    check accepts it (``startsWith('http')``).
    """
    photo_ref = "photo://masci-hub/photos/2026/05/dr_abc/85e97aff.jpg"
    presigned = "https://masci-hub.r2.cloudflarestorage.com/photos/2026/05/dr_abc/85e97aff.jpg?X-Amz-Signature=zzz"

    db = _FakeDb()
    db.job_photos = _FakeCollection([{
        "id": "daily_report:src1:0",
        "source": "daily_report",
        "source_id": "src1",
        "photo_index": 0,
        "project_number": "26-01 - CP",
    }])
    db.daily_reports = _FakeCollection([{
        "id": "src1",
        "photos": [photo_ref],
    }])

    async def _fake_presign(ref, ttl_seconds=900):
        assert ref == photo_ref
        assert ttl_seconds == 900
        return presigned

    from photo_storage import presigned_get_url as _real_psu  # noqa: F401
    import photo_storage
    monkeypatch.setattr(photo_storage, "presigned_get_url", _fake_presign)

    from fastapi import Response
    handlers = _get_handlers(db, monkeypatch)
    handler = handlers[("/api/job-photos/{photo_id}/raw", tuple(sorted({"GET"})))]
    resp = Response()
    result = _run(handler(photo_id="daily_report:src1:0", response=resp, actor={"role": "admin"}))
    assert result["data_url"] == presigned
    assert result["data_url"].startswith("http"), (
        "Frontend lightbox only accepts data:image/, blob:, or http — got "
        f"{result['data_url'][:60]!r}"
    )
    # No-store cache header still set (iter437 doctrine)
    assert "no-store" in (resp.headers.get("Cache-Control") or "").lower()


# ──────────────────────────────────────────────────────────────────────
# 2 · /raw passes legacy data:image/ URLs through unchanged
# ──────────────────────────────────────────────────────────────────────
def test_raw_photo_with_legacy_base64_ref_passes_through(monkeypatch):
    """Backward compatibility: any pre-iter64 record that still has
    an inline ``data:image/...`` URL must round-trip unchanged. The
    presign function must NOT be invoked for these.
    """
    legacy = "data:image/jpeg;base64,/9j/4AAQSkZJRgABA" + "A" * 50
    db = _FakeDb()
    db.job_photos = _FakeCollection([{
        "id": "daily_report:lr:0",
        "source": "daily_report",
        "source_id": "lr",
        "photo_index": 0,
        "project_number": "P-LEG",
    }])
    db.daily_reports = _FakeCollection([{"id": "lr", "photos": [legacy]}])

    presign_calls = {"n": 0}

    async def _fake_presign(ref, ttl_seconds=900):
        presign_calls["n"] += 1
        return "https://should-not-be-called"

    import photo_storage
    monkeypatch.setattr(photo_storage, "presigned_get_url", _fake_presign)

    from fastapi import Response
    handlers = _get_handlers(db, monkeypatch)
    handler = handlers[("/api/job-photos/{photo_id}/raw", tuple(sorted({"GET"})))]
    result = _run(handler(photo_id="daily_report:lr:0", response=Response(), actor={"role": "admin"}))
    assert result["data_url"] == legacy
    assert presign_calls["n"] == 0, (
        "Legacy data:image/ refs must NOT trigger an R2 presign — got "
        f"{presign_calls['n']} call(s)"
    )


# ──────────────────────────────────────────────────────────────────────
# 3 · /raw-batch must presign each photo:// ref in the batch
# ──────────────────────────────────────────────────────────────────────
def test_raw_batch_presigns_each_r2_ref(monkeypatch):
    refs = [
        "photo://masci-hub/photos/2026/05/dr1/aaa.jpg",
        "photo://masci-hub/photos/2026/05/dr2/bbb.png",
    ]
    db = _FakeDb()
    db.job_photos = _FakeCollection([
        {"id": "daily_report:s1:0", "source": "daily_report", "source_id": "s1",
         "photo_index": 0, "project_number": "X"},
        {"id": "daily_report:s2:0", "source": "daily_report", "source_id": "s2",
         "photo_index": 0, "project_number": "X"},
    ])
    db.daily_reports = _FakeCollection([
        {"id": "s1", "photos": [refs[0]]},
        {"id": "s2", "photos": [refs[1]]},
    ])

    async def _fake_presign(ref, ttl_seconds=900):
        return f"https://r2.example.com/{ref.split('/')[-1]}?sig=1"

    import photo_storage
    monkeypatch.setattr(photo_storage, "presigned_get_url", _fake_presign)

    from fastapi import Response
    from routes.job_photos import BulkSelection
    handlers = _get_handlers(db, monkeypatch)
    handler = handlers[("/api/job-photos/raw-batch", tuple(sorted({"POST"})))]
    body = BulkSelection(photo_ids=["daily_report:s1:0", "daily_report:s2:0"])
    result = _run(handler(body=body, response=Response(), actor={"role": "admin"}))
    items = result["items"]
    assert len(items) == 2, items
    for it in items:
        assert it["data_url"].startswith("https://"), it
        assert it["data_url"].endswith("?sig=1"), it


# ──────────────────────────────────────────────────────────────────────
# 4 · /raw-batch skips photos whose presign fails (no whole-batch fail)
# ──────────────────────────────────────────────────────────────────────
def test_raw_batch_skips_failed_presign_does_not_break_others(monkeypatch):
    db = _FakeDb()
    db.job_photos = _FakeCollection([
        {"id": "daily_report:good:0", "source": "daily_report", "source_id": "good",
         "photo_index": 0, "project_number": "X"},
        {"id": "daily_report:bad:0", "source": "daily_report", "source_id": "bad",
         "photo_index": 0, "project_number": "X"},
    ])
    db.daily_reports = _FakeCollection([
        {"id": "good", "photos": ["photo://b/k/good.jpg"]},
        {"id": "bad", "photos": ["photo://b/k/bad.jpg"]},
    ])

    async def _fake_presign(ref, ttl_seconds=900):
        if "bad" in ref:
            raise RuntimeError("synthetic R2 outage")
        return f"https://r2.example.com/{ref.split('/')[-1]}"

    import photo_storage
    monkeypatch.setattr(photo_storage, "presigned_get_url", _fake_presign)

    from fastapi import Response
    from routes.job_photos import BulkSelection
    handlers = _get_handlers(db, monkeypatch)
    handler = handlers[("/api/job-photos/raw-batch", tuple(sorted({"POST"})))]
    body = BulkSelection(photo_ids=["daily_report:good:0", "daily_report:bad:0"])
    result = _run(handler(body=body, response=Response(), actor={"role": "admin"}))
    items = result["items"]
    assert len(items) == 1, items  # only the good one
    assert items[0]["id"] == "daily_report:good:0"
    assert items[0]["data_url"].startswith("https://")


# ──────────────────────────────────────────────────────────────────────
# 5 · /raw still returns 404 for unknown photo_id (no regression)
# ──────────────────────────────────────────────────────────────────────
def test_raw_unknown_photo_id_returns_404(monkeypatch):
    db = _FakeDb()
    db.job_photos = _FakeCollection([])
    db.daily_reports = _FakeCollection([])

    async def _fake_presign(ref, ttl_seconds=900):
        return "should-not-be-called"

    import photo_storage
    monkeypatch.setattr(photo_storage, "presigned_get_url", _fake_presign)

    from fastapi import Response, HTTPException
    handlers = _get_handlers(db, monkeypatch)
    handler = handlers[("/api/job-photos/{photo_id}/raw", tuple(sorted({"GET"})))]
    with pytest.raises(HTTPException) as ei:
        _run(handler(photo_id="does-not-exist:nope:0", response=Response(), actor={"role": "admin"}))
    assert ei.value.status_code == 404


# ──────────────────────────────────────────────────────────────────────
# 6 · /raw returns 500 if presign raises (clear failure mode)
# ──────────────────────────────────────────────────────────────────────
def test_raw_presign_failure_returns_500_not_silent_url(monkeypatch):
    db = _FakeDb()
    db.job_photos = _FakeCollection([{
        "id": "daily_report:p:0", "source": "daily_report", "source_id": "p",
        "photo_index": 0, "project_number": "X",
    }])
    db.daily_reports = _FakeCollection([
        {"id": "p", "photos": ["photo://b/k/p.jpg"]},
    ])

    async def _fake_presign(ref, ttl_seconds=900):
        raise RuntimeError("simulated R2 client outage")

    import photo_storage
    monkeypatch.setattr(photo_storage, "presigned_get_url", _fake_presign)

    from fastapi import Response, HTTPException
    handlers = _get_handlers(db, monkeypatch)
    handler = handlers[("/api/job-photos/{photo_id}/raw", tuple(sorted({"GET"})))]
    with pytest.raises(HTTPException) as ei:
        _run(handler(photo_id="daily_report:p:0", response=Response(), actor={"role": "admin"}))
    assert ei.value.status_code == 500
    assert "presign" in (ei.value.detail or "").lower()
