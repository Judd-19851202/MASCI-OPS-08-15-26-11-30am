"""
test_iter429_1_storage_summary_and_week1.py · Phase 28.1 · iter429.1
─────────────────────────────────────────────────────────────────────
Parity-lock for the two new admin surfaces shipped this phase:

1. `GET /api/admin/operational-attachments/storage-summary` ·
    admin-only JSON · returns r2_count, inline_b64_count, totals,
    migrated_pct. Used to verify R2 cold-storage convergence
    before/after running the migration script.

2. Week-1 debrief endpoints ·
    `GET  /api/admin/dls/week-1-debrief/questions`   (14 questions)
    `POST /api/admin/dls/week-1-debrief`              (writes a calm
    markdown file at /app/memory/DLS_WEEK1_LIVE_OPS_DEBRIEF_*.md)

Both surfaces are pure additions — Day-1 surface contract is verified
to remain identical (no regression on the 12-question Day-1 list, no
file-name change, no removal of legacy fields).
"""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import Any, Dict, List

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from routes.operational_attachments import build_operational_attachments_router
from routes.dispatch_day1_debrief import (
    build_day1_debrief_router, DAY1_QUESTIONS, WEEK1_QUESTIONS,
)


# ─────────────────────────────────────────────────────────────────────
# Reusable fake Mongo (only the surface the storage_summary touches)
# ─────────────────────────────────────────────────────────────────────
class _FakeCursor:
    def __init__(self, docs):
        self._docs = list(docs)

    def __aiter__(self):
        self._it = iter(self._docs)
        return self

    async def __anext__(self):
        try:
            return next(self._it)
        except StopIteration:
            raise StopAsyncIteration


class _FakeCollection:
    def __init__(self, docs: List[Dict[str, Any]] | None = None):
        self.docs = docs or []

    def aggregate(self, pipeline):
        # Tiny faithful implementation: handles the $facet pipeline our
        # storage_summary route emits.
        tenant_filter = None
        for stage in pipeline:
            if "$match" in stage:
                tenant_filter = stage["$match"].get("tenant_id")
        rows = [d for d in self.docs if d.get("tenant_id") == tenant_filter]

        by_backend_buckets: Dict[str, Dict[str, int]] = {}
        for d in rows:
            if d.get("storage_backend") == "r2":
                key = "r2"
            elif d.get("storage_backend") == "inline_b64" or (d.get("data_b64") not in (None, "")):
                key = "inline_b64"
            else:
                key = "unknown"
            bucket = by_backend_buckets.setdefault(key, {"count": 0, "total_size_bytes": 0})
            bucket["count"] += 1
            bucket["total_size_bytes"] += int(d.get("size_bytes") or 0)
        by_backend = [{"_id": k, "count": v["count"], "total_size_bytes": v["total_size_bytes"]}
                      for k, v in by_backend_buckets.items()]
        totals = [{"total": len(rows)}] if rows else [{"total": 0}]
        return _FakeCursor([{"by_backend": by_backend, "totals": totals}])

    async def find_one(self, q, projection=None):
        return None  # not used in these tests

    async def count_documents(self, q):
        return 0

    def find(self, *a, **k):
        return _FakeCursor([])

    async def insert_one(self, doc):
        self.docs.append(dict(doc))

    async def delete_one(self, q):
        return type("R", (), {"deleted_count": 1})


class _FakeDB:
    def __init__(self, docs=None):
        self.operational_attachments = _FakeCollection(docs)
        self.dispatch_assignments = _FakeCollection()


# ─────────────────────────────────────────────────────────────────────
# Dependency fakes
# ─────────────────────────────────────────────────────────────────────
async def _admin_actor():
    return {"name": "TestAdmin", "role": "admin", "admin": True, "email": "admin@masci.test"}


async def _portal_actor():
    return {"name": "TestPortal", "role": "dispatch"}


def _build_attachments_app(db):
    app = FastAPI()
    main_r, admin_r = build_operational_attachments_router(
        db,
        require_dispatch_or_admin_dep=_admin_actor,
        require_any_portal_token_dep=_portal_actor,
        require_admin_dep=_admin_actor,
    )
    app.include_router(main_r)
    app.include_router(admin_r)
    return app


def _build_debrief_app():
    app = FastAPI()
    app.include_router(build_day1_debrief_router(require_admin_dep=_admin_actor))
    return app


# ─────────────────────────────────────────────────────────────────────
# 1 · Storage summary returns honest counts (mixed inventory)
# ─────────────────────────────────────────────────────────────────────
def test_iter429_1_storage_summary_returns_honest_counts():
    docs = [
        {"id": "a", "tenant_id": "masci", "storage_backend": "r2",
         "r2_key": "k1", "size_bytes": 100},
        {"id": "b", "tenant_id": "masci", "storage_backend": "r2",
         "r2_key": "k2", "size_bytes": 200},
        {"id": "c", "tenant_id": "masci", "storage_backend": "inline_b64",
         "data_b64": "x", "size_bytes": 50},
        # Different tenant — must be excluded
        {"id": "z", "tenant_id": "other", "storage_backend": "r2",
         "r2_key": "k3", "size_bytes": 999},
    ]
    app = _build_attachments_app(_FakeDB(docs))
    client = TestClient(app)
    r = client.get("/api/admin/operational-attachments/storage-summary")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["tenant_id"] == "masci"
    assert body["total"] == 3
    assert body["r2_backed"]["count"] == 2
    assert body["r2_backed"]["total_size_bytes"] == 300
    assert body["inline_b64"]["count"] == 1
    assert body["inline_b64"]["total_size_bytes"] == 50
    # 2/3 → 66.67 %
    assert abs(body["migrated_pct"] - 66.67) < 0.05
    assert "captured_at" in body


# ─────────────────────────────────────────────────────────────────────
# 2 · Storage summary on empty tenant → migrated_pct=100 (no-op tenant)
# ─────────────────────────────────────────────────────────────────────
def test_iter429_1_storage_summary_empty_tenant():
    app = _build_attachments_app(_FakeDB(docs=[]))
    client = TestClient(app)
    r = client.get("/api/admin/operational-attachments/storage-summary")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["total"] == 0
    assert body["r2_backed"]["count"] == 0
    assert body["inline_b64"]["count"] == 0
    assert body["migrated_pct"] == 100.0  # nothing to migrate → trivially complete


# ─────────────────────────────────────────────────────────────────────
# 3 · Day-1 question contract preserved · NO REGRESSION
# ─────────────────────────────────────────────────────────────────────
def test_iter429_1_day1_contract_preserved():
    app = _build_debrief_app()
    client = TestClient(app)
    r = client.get("/api/admin/dls/day-1-debrief/questions")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["debrief_type"] == "day-1"
    assert len(body["questions"]) == 12
    # IDs must remain q1..q12 stable (operators answer the same questions)
    assert [q["id"] for q in body["questions"]] == [f"q{i}" for i in range(1, 13)]


# ─────────────────────────────────────────────────────────────────────
# 4 · Week-1 question contract · exactly 14 doctrine-locked questions
# ─────────────────────────────────────────────────────────────────────
def test_iter429_1_week1_questions_contract():
    app = _build_debrief_app()
    client = TestClient(app)
    r = client.get("/api/admin/dls/week-1-debrief/questions")
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["debrief_type"] == "week-1"
    assert len(body["questions"]) == 14
    assert [q["id"] for q in body["questions"]] == [f"q{i}" for i in range(1, 15)]
    # First and last questions are doctrine-locked — guard them.
    labels = [q["label"] for q in body["questions"]]
    assert labels[0] == "What friction repeated more than once?"
    assert labels[-1] == "What is the highest-value surgical improvement now?"


# ─────────────────────────────────────────────────────────────────────
# 5 · Week-1 submit writes the markdown file under DLS_WEEK1_* prefix
# ─────────────────────────────────────────────────────────────────────
def test_iter429_1_week1_submit_writes_markdown(monkeypatch, tmp_path):
    # Redirect the memory dir to a tmp path so the test doesn't pollute
    # /app/memory.
    import routes.dispatch_day1_debrief as _mod
    monkeypatch.setattr(_mod, "_MEMORY_DIR", tmp_path)

    app = _build_debrief_app()
    client = TestClient(app)
    r = client.post(
        "/api/admin/dls/week-1-debrief",
        json={
            "answers": {"q1": "Photos repeated · users kept retaking them"},
            "operational_notes": "Calm pattern this week.",
            "doctrine_observations": "Restraint held — no feature drift.",
        },
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["ok"] is True
    assert body["debrief_type"] == "week-1"
    assert body["question_count"] == 14
    assert body["filename"].startswith("DLS_WEEK1_LIVE_OPS_DEBRIEF_")
    assert body["filename"].endswith(".md")
    # File actually exists and contains our answer text.
    written = tmp_path / body["filename"]
    assert written.exists()
    md = written.read_text("utf-8")
    assert "Week-1 Live Ops Debrief" in md
    assert "Photos repeated" in md
    assert "Restraint held" in md


# ─────────────────────────────────────────────────────────────────────
# 6 · Day-1 submit still writes DLS_DAY1_* (legacy parity guard)
# ─────────────────────────────────────────────────────────────────────
def test_iter429_1_day1_submit_legacy_prefix(monkeypatch, tmp_path):
    import routes.dispatch_day1_debrief as _mod
    monkeypatch.setattr(_mod, "_MEMORY_DIR", tmp_path)

    app = _build_debrief_app()
    client = TestClient(app)
    r = client.post(
        "/api/admin/dls/day-1-debrief",
        json={"answers": {"q1": "dispatch paused on issuance"}},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["debrief_type"] == "day-1"
    assert body["question_count"] == 12
    assert body["filename"].startswith("DLS_DAY1_LIVE_OPS_DEBRIEF_")


# ─────────────────────────────────────────────────────────────────────
# 7 · Unknown debrief_type via POST body is overridden by URL
# ─────────────────────────────────────────────────────────────────────
def test_iter429_1_url_truth_overrides_body(monkeypatch, tmp_path):
    import routes.dispatch_day1_debrief as _mod
    monkeypatch.setattr(_mod, "_MEMORY_DIR", tmp_path)

    app = _build_debrief_app()
    client = TestClient(app)
    # Hit /day-1-debrief but try to spoof body as week-1 — must be ignored.
    r = client.post(
        "/api/admin/dls/day-1-debrief",
        json={"answers": {"q1": "x"}, "debrief_type": "week-1"},
    )
    body = r.json()
    assert body["debrief_type"] == "day-1"
    assert body["question_count"] == 12  # Day-1 questions, not Week-1
