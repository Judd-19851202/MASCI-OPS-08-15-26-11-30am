"""
test_iter429_op_attachments_r2.py · Phase 28 · iter429
─────────────────────────────────────────────────────────────────────
Parity-lock for the R2 cold-storage refactor of `operational_attachments`.

Doctrine
--------
1. Uploads MUST land on R2 when `photo_storage.is_configured()` is True ·
   the stored Mongo doc must carry `storage_backend="r2"` + `r2_key` and
   MUST NOT carry `data_b64`.
2. When R2 is NOT configured the legacy inline_b64 path is preserved ·
   guaranteeing preview/dev environments without R2 creds keep working.
3. Fetch must transparently read from R2 when `r2_key` is present and
   fall back to inline base64 for legacy rows.

These tests are PURE unit tests against the router factory · no live
network · no live Mongo · `photo_storage` is monkey-patched.
"""
from __future__ import annotations

import base64
import hashlib
from typing import Any, Dict, List

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes.operational_attachments import build_operational_attachments_router


# ─────────────────────────────────────────────────────────────────────
# In-memory Mongo stand-in (only the surface the router touches)
# ─────────────────────────────────────────────────────────────────────
class _FakeCursor:
    def __init__(self, docs: List[Dict[str, Any]]):
        self._docs = docs

    def sort(self, *_a, **_k):
        return self

    def __aiter__(self):
        self._it = iter(self._docs)
        return self

    async def __anext__(self):
        try:
            return next(self._it)
        except StopIteration:
            raise StopAsyncIteration


class _FakeCollection:
    def __init__(self):
        self.docs: List[Dict[str, Any]] = []

    async def find_one(self, q, projection=None):
        for d in self.docs:
            if all(d.get(k) == v for k, v in q.items() if not isinstance(v, dict)):
                return dict(d)
        return None

    async def count_documents(self, q):
        n = 0
        for d in self.docs:
            if all(d.get(k) == v for k, v in q.items() if not isinstance(v, dict)):
                n += 1
        return n

    def find(self, q, projection=None):
        out = []
        for d in self.docs:
            ok = True
            for k, v in q.items():
                if isinstance(v, dict):
                    continue
                if d.get(k) != v:
                    ok = False
                    break
            if ok:
                out.append(dict(d))
        return _FakeCursor(out)

    async def insert_one(self, doc):
        self.docs.append(dict(doc))
        return type("R", (), {"inserted_id": doc.get("id")})

    async def delete_one(self, q):
        self.docs = [d for d in self.docs
                     if not all(d.get(k) == v for k, v in q.items())]
        return type("R", (), {"deleted_count": 1})


class _FakeDB:
    def __init__(self):
        self.operational_attachments = _FakeCollection()
        self.dispatch_assignments = _FakeCollection()


# ─────────────────────────────────────────────────────────────────────
# Test dependencies
# ─────────────────────────────────────────────────────────────────────
async def _admin_actor():
    return {"name": "TestAdmin", "role": "admin", "admin": True}


async def _portal_actor():
    return {"name": "TestPortal", "role": "dispatch"}


def _png_bytes() -> bytes:
    # Smallest possible PNG (1x1 transparent).
    return base64.b64decode(
        "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mNkYAAAAAYAAjCB0C8AAAAASUVORK5CYII="
    )


def _build_app(db):
    app = FastAPI()
    main_r, admin_r = build_operational_attachments_router(
        db,
        require_dispatch_or_admin_dep=_admin_actor,
        require_any_portal_token_dep=_portal_actor,
    )
    app.include_router(main_r)
    app.include_router(admin_r)
    return app


# ─────────────────────────────────────────────────────────────────────
# 1 · R2 configured path · upload writes r2_key · no data_b64
# ─────────────────────────────────────────────────────────────────────
def test_iter429_upload_lands_in_r2_when_configured(monkeypatch):
    db = _FakeDB()
    # Seed a host assignment so the upload validates.
    db.dispatch_assignments.docs.append(
        {"id": "asgn-1", "tenant_id": "masci"}
    )

    uploaded_bytes_holder: Dict[str, bytes] = {}

    async def fake_upload(data, *, ext, source_id, content_type):
        uploaded_bytes_holder["data"] = data
        uploaded_bytes_holder["ext"] = ext
        return "photo://test-bucket/photos/preview/2026/02/key.png"

    monkeypatch.setattr("photo_storage.is_configured", lambda: True)
    monkeypatch.setattr("photo_storage.upload_photo_bytes", fake_upload)

    app = _build_app(db)
    client = TestClient(app)

    png = _png_bytes()
    r = client.post(
        "/api/operational-attachments/upload",
        data={
            "host_kind": "assignment",
            "host_id": "asgn-1",
            "attachment_type": "load_photo",
        },
        files={"file": ("tiny.png", png, "image/png")},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["storage_backend"] == "r2"
    # The stored doc should carry r2_key and NOT data_b64
    stored = db.operational_attachments.docs[0]
    assert stored["storage_backend"] == "r2"
    assert stored["r2_key"] == "photos/preview/2026/02/key.png"
    assert "data_b64" not in stored
    assert stored["sha256"] == hashlib.sha256(png).hexdigest()
    # Bytes uploaded match exactly
    assert uploaded_bytes_holder["data"] == png


# ─────────────────────────────────────────────────────────────────────
# 2 · R2 unconfigured path · upload falls back to inline_b64
# ─────────────────────────────────────────────────────────────────────
def test_iter429_upload_falls_back_when_r2_unconfigured(monkeypatch):
    db = _FakeDB()
    db.dispatch_assignments.docs.append(
        {"id": "asgn-2", "tenant_id": "masci"}
    )
    monkeypatch.setattr("photo_storage.is_configured", lambda: False)

    app = _build_app(db)
    client = TestClient(app)

    png = _png_bytes()
    r = client.post(
        "/api/operational-attachments/upload",
        data={
            "host_kind": "assignment",
            "host_id": "asgn-2",
            "attachment_type": "load_photo",
        },
        files={"file": ("tiny.png", png, "image/png")},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["storage_backend"] == "inline_b64"
    stored = db.operational_attachments.docs[0]
    assert stored["storage_backend"] == "inline_b64"
    assert "r2_key" not in stored
    assert base64.b64decode(stored["data_b64"]) == png


# ─────────────────────────────────────────────────────────────────────
# 3 · Fetch reads from R2 when storage_backend == "r2"
# ─────────────────────────────────────────────────────────────────────
def test_iter429_fetch_reads_from_r2(monkeypatch):
    db = _FakeDB()
    payload = _png_bytes()
    db.operational_attachments.docs.append({
        "id": "att-r2",
        "tenant_id": "masci",
        "host_kind": "assignment",
        "host_id": "asgn-3",
        "type": "load_photo",
        "storage_backend": "r2",
        "r2_key": "photos/preview/2026/02/abc.png",
        "content_type": "image/png",
        "filename": "abc.png",
        "uploaded_by": "x", "uploaded_role": "admin",
        "uploaded_at": "2026-02-01T00:00:00+00:00",
    })

    async def fake_read(ref):
        assert ref.endswith("photos/preview/2026/02/abc.png")
        return payload
    monkeypatch.setattr("photo_storage.read_photo_bytes", fake_read)

    app = _build_app(db)
    client = TestClient(app)
    r = client.get("/api/operational-attachments/att-r2/file")
    assert r.status_code == 200, r.text
    assert r.content == payload


# ─────────────────────────────────────────────────────────────────────
# 4 · Legacy inline_b64 row still fetches transparently
# ─────────────────────────────────────────────────────────────────────
def test_iter429_fetch_falls_back_to_inline_b64():
    db = _FakeDB()
    payload = _png_bytes()
    db.operational_attachments.docs.append({
        "id": "att-legacy",
        "tenant_id": "masci",
        "host_kind": "assignment",
        "host_id": "asgn-4",
        "type": "load_photo",
        "storage_backend": "inline_b64",
        "data_b64": base64.b64encode(payload).decode("ascii"),
        "content_type": "image/png",
        "filename": "legacy.png",
        "uploaded_by": "x", "uploaded_role": "admin",
        "uploaded_at": "2025-12-01T00:00:00+00:00",
    })
    app = _build_app(db)
    client = TestClient(app)
    r = client.get("/api/operational-attachments/att-legacy/file")
    assert r.status_code == 200, r.text
    assert r.content == payload
