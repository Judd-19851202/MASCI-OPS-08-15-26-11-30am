"""
test_iter432_field_memory.py · Phase 30 · iter432
─────────────────────────────────────────────────────────────────────
Parity-lock for the Field Memory continuity primitive.

Doctrine pinned by these tests:
  1. Append-only — successful POST persists exactly one row.
  2. Role × subject_kind write matrix is enforced.
  3. Lists default to UNRESOLVED only · `include_resolved=true`
     surfaces resolved rows too.
  4. Resolve flips state AND records reason · second resolve is
     rejected (cannot double-resolve).
  5. Invalid subject_kind / empty body / bad resolve reason all
     return 400.
  6. Hard delete intentionally has no endpoint surface (no
     `DELETE` route registered).
"""
from __future__ import annotations

from typing import Any, Dict, List

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes.field_memory import build_field_memory_router


class _Cursor:
    def __init__(self, rows):
        self._rows = list(rows)

    def sort(self, *_a, **_k):
        return self

    def limit(self, *_a, **_k):
        return self

    def __aiter__(self):
        self._i = iter(self._rows)
        return self

    async def __anext__(self):
        try:
            return next(self._i)
        except StopIteration:
            raise StopAsyncIteration


class _Coll:
    def __init__(self):
        self.rows: List[Dict[str, Any]] = []

    async def insert_one(self, doc):
        self.rows.append(dict(doc))

    async def find_one(self, q, projection=None):
        for r in self.rows:
            if all(r.get(k) == v for k, v in q.items() if not isinstance(v, dict)):
                return dict(r)
        return None

    def find(self, q, projection=None):
        out = []
        for r in self.rows:
            ok = True
            for k, v in q.items():
                if isinstance(v, dict):
                    continue
                if r.get(k) != v:
                    ok = False
                    break
            if ok:
                out.append(dict(r))
        return _Cursor(out)

    async def update_one(self, q, update):
        for r in self.rows:
            if all(r.get(k) == v for k, v in q.items() if not isinstance(v, dict)):
                r.update(update.get("$set") or {})
                return type("R", (), {"modified_count": 1})
        return type("R", (), {"modified_count": 0})


class _DB:
    def __init__(self):
        self.field_memory_notes = _Coll()


def _build_app(role: str):
    async def _actor():
        return {"name": "TestOp", "role": role}
    app = FastAPI()
    app.include_router(build_field_memory_router(
        db=_DB() if False else _shared_db,
        require_any_portal_token_dep=_actor,
    ))
    return app


_shared_db = None  # rebuilt per test below


# ─────────────────────────────────────────────────────────────────
def _client(role: str, db: _DB):
    async def _actor():
        return {"name": f"Tester-{role}", "role": role}
    app = FastAPI()
    app.include_router(build_field_memory_router(
        db=db, require_any_portal_token_dep=_actor,
    ))
    return TestClient(app)


def test_iter432_field_memory_create_and_list_field_leadership():
    db = _DB()
    c = _client("field_leadership", db)
    r = c.post("/api/field-memory", json={
        "subject_kind": "project",
        "subject_id": "proj-oxford",
        "subject_label": "Oxford Road",
        "body": "Repeatedly bottlenecks near STA 112+00.",
        "tags": ["sequencing", "haul-staging"],
    })
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["id"].startswith("fm-")
    assert body["resolved"] is False
    assert body["captured_by_role"] == "field_leadership"
    assert "sequencing" in body["tags"] and "haul-staging" in body["tags"]
    # List
    lr = c.get("/api/field-memory?subject_kind=project&subject_id=proj-oxford")
    assert lr.status_code == 200
    body2 = lr.json()
    assert body2["count"] == 1
    assert body2["items"][0]["body"].startswith("Repeatedly")


def test_iter432_field_memory_shop_can_write_equipment_but_not_project():
    db = _DB()
    c = _client("shop", db)
    ok = c.post("/api/field-memory", json={
        "subject_kind": "equipment",
        "subject_id": "truck-47",
        "body": "Loses hydraulic pressure during high-temp paving cycles.",
    })
    assert ok.status_code == 200, ok.text
    bad = c.post("/api/field-memory", json={
        "subject_kind": "project",
        "subject_id": "proj-oxford",
        "body": "Shop should not be allowed to record project-wide memory.",
    })
    assert bad.status_code == 403, bad.text


def test_iter432_field_memory_dispatch_can_write_assignment_but_not_equipment():
    db = _DB()
    c = _client("dispatch", db)
    ok = c.post("/api/field-memory", json={
        "subject_kind": "assignment",
        "subject_id": "asgn-1",
        "body": "Driver reports radio dead zone past mile marker 47.",
    })
    assert ok.status_code == 200
    bad = c.post("/api/field-memory", json={
        "subject_kind": "equipment",
        "subject_id": "truck-47",
        "body": "Dispatch shouldn't record equipment-only memory.",
    })
    assert bad.status_code == 403


def test_iter432_field_memory_hr_cannot_write():
    db = _DB()
    c = _client("hr", db)
    r = c.post("/api/field-memory", json={
        "subject_kind": "project",
        "subject_id": "proj-oxford",
        "body": "HR shouldn't record operational memory.",
    })
    assert r.status_code == 403


def test_iter432_field_memory_invalid_subject_kind_400():
    db = _DB()
    c = _client("admin", db)
    r = c.post("/api/field-memory", json={
        "subject_kind": "vendor",
        "subject_id": "x",
        "body": "y",
    })
    assert r.status_code == 400


def test_iter432_field_memory_empty_body_400():
    db = _DB()
    c = _client("admin", db)
    r = c.post("/api/field-memory", json={
        "subject_kind": "project",
        "subject_id": "x",
        "body": "   ",
    })
    assert r.status_code == 400


def test_iter432_field_memory_resolve_flow():
    db = _DB()
    c = _client("field_leadership", db)
    note = c.post("/api/field-memory", json={
        "subject_kind": "project",
        "subject_id": "proj-x",
        "body": "Condition observation.",
    }).json()
    nid = note["id"]

    # Default list excludes resolved
    lr1 = c.get("/api/field-memory?subject_kind=project&subject_id=proj-x")
    assert lr1.json()["count"] == 1

    # Resolve with valid reason
    rr = c.post(f"/api/field-memory/{nid}/resolve",
                json={"reason": "condition_addressed", "note": "fixed by re-sequencing"})
    assert rr.status_code == 200, rr.text

    # Excluded from default list now
    lr2 = c.get("/api/field-memory?subject_kind=project&subject_id=proj-x")
    assert lr2.json()["count"] == 0

    # Surfaces with include_resolved=true
    lr3 = c.get("/api/field-memory?subject_kind=project&subject_id=proj-x&include_resolved=true")
    body = lr3.json()
    assert body["count"] == 1
    assert body["items"][0]["resolved"] is True
    assert body["items"][0]["resolved_reason"] == "condition_addressed"

    # Cannot double-resolve
    rr2 = c.post(f"/api/field-memory/{nid}/resolve",
                 json={"reason": "no_longer_applies"})
    assert rr2.status_code == 400


def test_iter432_field_memory_resolve_invalid_reason_400():
    db = _DB()
    c = _client("admin", db)
    note = c.post("/api/field-memory", json={
        "subject_kind": "equipment", "subject_id": "t-1", "body": "x"
    }).json()
    r = c.post(f"/api/field-memory/{note['id']}/resolve",
               json={"reason": "I changed my mind"})
    assert r.status_code == 400


def test_iter432_field_memory_resolve_missing_note_404():
    db = _DB()
    c = _client("admin", db)
    r = c.post("/api/field-memory/fm-nonexistent/resolve",
               json={"reason": "no_longer_applies"})
    assert r.status_code == 404


def test_iter432_field_memory_no_delete_endpoint_registered():
    """Append-only doctrine: there is no DELETE surface. This pins it
    in the parity-lock so a future hand cannot quietly add one."""
    async def _actor():
        return {"name": "Admin", "role": "admin"}
    db = _DB()
    app = FastAPI()
    app.include_router(build_field_memory_router(
        db=db, require_any_portal_token_dep=_actor,
    ))
    methods = []
    for r in app.routes:
        if "/field-memory" in getattr(r, "path", ""):
            for m in (getattr(r, "methods", None) or set()):
                methods.append((m, r.path))
    assert not any(m == "DELETE" for m, _ in methods), (
        f"Field Memory must remain append-only · DELETE registered: {methods}"
    )
