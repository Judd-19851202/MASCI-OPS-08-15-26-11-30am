"""
test_iter165_phase_j_idempotency.py — Phase J · Field Resiliency Layer.

Verifies the shared idempotency helper applied to the 3 priority forms:
  * POST /api/incidents
  * POST /api/daily-reports
  * POST /api/field-leadership/records (via leadership token)

Covers:
  1. Idempotency-Key header → same response on duplicate POST.
  2. Same key returns cached payload even when client sends DIFFERENT
     body (proves server-side dedup, not client cache).
  3. No duplicate database row created on repeated key.
  4. Different actors using same key are treated independently.
  5. No Idempotency-Key → handler runs normally (creates a row).
  6. Cache TTL index exists on db.idempotency_keys.
  7. Discipline: no per-form idempotency table — single shared collection.
"""
import os
import uuid
from pathlib import Path

import requests

import sys
sys.path.insert(0, "/app/backend")


def _kv(p, k):
    try:
        with open(p) as f:
            for line in f:
                if line.startswith(f"{k}="):
                    return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        pass
    return ""


URL = (_kv(Path("/app/frontend/.env"), "REACT_APP_BACKEND_URL")
       or os.environ.get("REACT_APP_BACKEND_URL", "")).rstrip("/")


def _get_db():
    import asyncio
    from motor.motor_asyncio import AsyncIOMotorClient
    return (AsyncIOMotorClient(_kv(Path("/app/backend/.env"), "MONGO_URL"))
            [_kv(Path("/app/backend/.env"), "DB_NAME")])


def _arun(coro):
    import asyncio
    return asyncio.new_event_loop().run_until_complete(coro)


# Minimal valid incident payload — matches IncidentCreate Pydantic model.
def _incident_payload(project="iter165 test", suffix=""):
    return {
        "project_name": project + suffix,
        "project_number": "TEST-J-1",
        "incident_type": "Near Miss",
        "incident_date": "2026-05-15",
        "incident_time": "10:00",
        "reported_date": "2026-05-15",
        "location": "iter165 test yard",
        "description": "iter165 idempotency test event",
        "reported_by": "iter165",
        "severity": "Low",
    }


# Minimal valid daily-report payload.
def _daily_report_payload(project="iter165 test", suffix=""):
    return {
        "project_name": project + suffix,
        "project_number": "TEST-J-1",
        "location": "iter165 yard",
        "report_date": "2026-05-15",
        "prepared_by": "iter165 prepper",
        "weather_summary": "Sunny",
        "narrative": "iter165 idempotency test",
    }


# ──────────────────────────────────────────────────────────────────
# Incidents
# ──────────────────────────────────────────────────────────────────
def test_incident_idempotent_same_response():
    key = str(uuid.uuid4())
    payload = _incident_payload(suffix=f" {key[:6]}")
    r1 = requests.post(f"{URL}/api/incidents",
                       headers={"Idempotency-Key": key,
                                "Content-Type": "application/json"},
                       json=payload, timeout=15)
    assert r1.status_code == 200, r1.text
    id1 = r1.json()["id"]
    doc_id1 = r1.json().get("doc_id")
    # Re-submit with DIFFERENT body. Server must return original.
    r2 = requests.post(f"{URL}/api/incidents",
                       headers={"Idempotency-Key": key,
                                "Content-Type": "application/json"},
                       json={**payload, "project_name": "MUTATED",
                             "severity": "High"},
                       timeout=15)
    assert r2.status_code == 200, r2.text
    assert r2.json()["id"] == id1, "must return original id (dedup)"
    assert r2.json().get("doc_id") == doc_id1
    assert r2.json()["project_name"] != "MUTATED", \
        "must return cached original payload"

    # Verify only ONE row exists in db.incidents.
    async def count_inc():
        db = _get_db()
        return await db.incidents.count_documents({"id": id1})
    assert _arun(count_inc()) == 1

    # Cleanup
    async def cleanup():
        db = _get_db()
        await db.incidents.delete_one({"id": id1})
        await db.idempotency_keys.delete_many({"key": key})
        await db.tasks.delete_many({"source_record_id": id1})
        await db.notifications.delete_many({"linked_source_record_id": id1})
    _arun(cleanup())


def test_incident_no_idempotency_header_runs_normally():
    """Without Idempotency-Key, each POST creates a new row."""
    payload = _incident_payload(suffix=f" {uuid.uuid4().hex[:6]}")
    r1 = requests.post(f"{URL}/api/incidents",
                       json=payload, timeout=15)
    assert r1.status_code == 200
    r2 = requests.post(f"{URL}/api/incidents",
                       json=payload, timeout=15)
    assert r2.status_code == 200
    assert r1.json()["id"] != r2.json()["id"], \
        "no key → no dedup → must create separate rows"

    async def cleanup():
        db = _get_db()
        for rid in [r1.json()["id"], r2.json()["id"]]:
            await db.incidents.delete_one({"id": rid})
            await db.tasks.delete_many({"source_record_id": rid})
            await db.notifications.delete_many({"linked_source_record_id": rid})
    _arun(cleanup())


# ──────────────────────────────────────────────────────────────────
# Daily Reports
# ──────────────────────────────────────────────────────────────────
def test_daily_report_idempotent_same_response():
    key = str(uuid.uuid4())
    payload = _daily_report_payload(suffix=f" {key[:6]}")
    r1 = requests.post(f"{URL}/api/daily-reports",
                       headers={"Idempotency-Key": key,
                                "Content-Type": "application/json"},
                       json=payload, timeout=15)
    assert r1.status_code == 200, r1.text
    id1 = r1.json()["id"]
    r2 = requests.post(f"{URL}/api/daily-reports",
                       headers={"Idempotency-Key": key,
                                "Content-Type": "application/json"},
                       json={**payload, "weather_summary": "MUTATED"},
                       timeout=15)
    assert r2.status_code == 200
    assert r2.json()["id"] == id1
    assert r2.json()["weather_summary"] != "MUTATED"

    async def count_and_cleanup():
        db = _get_db()
        n = await db.daily_reports.count_documents({"id": id1})
        await db.daily_reports.delete_one({"id": id1})
        await db.idempotency_keys.delete_many({"key": key})
        return n
    n = _arun(count_and_cleanup())
    assert n == 1


# ──────────────────────────────────────────────────────────────────
# Field Leadership Records (requires leadership token)
# ──────────────────────────────────────────────────────────────────
def _leadership_token():
    r = requests.post(f"{URL}/api/field-leadership/login",
                      json={"password": "MASCIGC"},
                      headers={"X-Admin-Token": ""}, timeout=10)
    return r.json().get("token") if r.status_code == 200 else None


def test_field_leadership_idempotent_same_response():
    tok = _leadership_token()
    if not tok:
        import pytest
        pytest.skip("Field Leadership login unavailable")
    key = str(uuid.uuid4())
    payload = {
        "kind": "training_deficiency",
        "occurred_at": "2026-05-15T10:00:00Z",
        "submitted_by": "iter165",
        "project_number": "TEST-J-1",
        "project_name": "iter165 fl test",
        "details": {"notes": f"iter165 idempotency test {key[:8]}",
                    "topic": "PPE", "language": "en"},
    }
    hdrs = {"X-Leadership-Token": tok, "X-Admin-Token": "",
            "Idempotency-Key": key, "Content-Type": "application/json"}
    r1 = requests.post(f"{URL}/api/field-leadership",
                       headers=hdrs, json=payload, timeout=15)
    assert r1.status_code == 200, r1.text
    id1 = r1.json()["id"]
    project_name_1 = r1.json()["record"].get("project_name")
    r2 = requests.post(f"{URL}/api/field-leadership",
                       headers=hdrs,
                       json={**payload, "project_name": "MUTATED-NAME"},
                       timeout=15)
    assert r2.status_code == 200
    assert r2.json()["id"] == id1, "must return cached original"
    assert r2.json()["record"]["project_name"] == project_name_1, \
        "must return cached original payload, not the mutated second"

    async def cleanup():
        db = _get_db()
        n = await db.field_leadership_records.count_documents({"id": id1})
        await db.field_leadership_records.delete_one({"id": id1})
        await db.idempotency_keys.delete_many({"key": key})
        return n
    n = _arun(cleanup())
    assert n == 1


# ──────────────────────────────────────────────────────────────────
# Library-level guarantees
# ──────────────────────────────────────────────────────────────────
def test_ttl_index_present_on_idempotency_keys():
    """The shared collection must have a TTL index so cached rows
    self-clean after 90 days."""
    async def go():
        db = _get_db()
        # Ensure indexes (idempotent — same call the helper makes).
        from lib.idempotency import ensure_indexes, TTL_SECONDS
        await ensure_indexes(db)
        idxs = await db.idempotency_keys.list_indexes().to_list(None)
        ttl_idxs = [i for i in idxs if "expireAfterSeconds" in i]
        return ttl_idxs, TTL_SECONDS
    ttl_idxs, expected = _arun(go())
    assert len(ttl_idxs) >= 1
    assert ttl_idxs[0]["expireAfterSeconds"] == expected


def test_no_per_form_idempotency_collections():
    """Discipline guard — only ONE shared collection."""
    async def go():
        db = _get_db()
        cols = await db.list_collection_names()
        return [c for c in cols
                if c.startswith("idempotency") and c != "idempotency_keys"]
    bad = _arun(go())
    assert bad == [], f"discipline violation: per-form idem collections {bad}"


def test_different_actor_with_same_key_creates_separate_record():
    """Cross-actor dedup MUST NOT happen — same key from different
    actors should produce different records."""
    key = str(uuid.uuid4())
    payload = _incident_payload(suffix=f" {key[:6]}")
    # Submit 1 — anon (no admin token; conftest auto-injects admin for
    # tests, so this lands as the 'admin/jaymn' actor identity).
    r1 = requests.post(f"{URL}/api/incidents",
                       headers={"Idempotency-Key": key,
                                "Content-Type": "application/json"},
                       json=payload, timeout=15)
    assert r1.status_code == 200
    id1 = r1.json()["id"]

    # Submit 2 — explicitly anon (no admin token forced).
    # NOTE: This route is rate_limit_public_post — both submissions are
    # technically "public POST" from the server's perspective, and they
    # share the same actor_id ("public:unknown"). So we expect dedup
    # within the same actor — and that's the correct behavior. This
    # test instead verifies the actor_id derivation by simulating two
    # distinct actor dicts at the library level.
    import asyncio
    from lib.idempotency import with_idempotency

    async def go():
        db = _get_db()
        # Call with actor A
        a_response = await with_idempotency(
            db, key + "-libtest", {"id": "user-A"},
            lambda: _async_return({"ok": "A"}))
        # Call with actor B using SAME key — should NOT be deduped.
        b_response = await with_idempotency(
            db, key + "-libtest", {"id": "user-B"},
            lambda: _async_return({"ok": "B"}))
        await db.idempotency_keys.delete_many({"key": key + "-libtest"})
        return a_response, b_response

    async def _async_return(v):
        return v

    a, b = _arun(go())
    assert a == {"ok": "A"}
    assert b == {"ok": "B"}, \
        "different actors must not share idempotency cache"

    # Cleanup the incident.
    async def cleanup():
        db = _get_db()
        await db.incidents.delete_one({"id": id1})
        await db.idempotency_keys.delete_many({"key": key})
        await db.tasks.delete_many({"source_record_id": id1})
        await db.notifications.delete_many({"linked_source_record_id": id1})
    _arun(cleanup())


def test_library_caches_response_correctly():
    """Direct library-level test — repeated calls with same (key, actor)
    skip the factory entirely after the first execution."""
    import asyncio
    from lib.idempotency import with_idempotency

    key = f"iter165-libtest-{uuid.uuid4().hex[:8]}"

    counter = {"n": 0}
    async def factory():
        counter["n"] += 1
        return {"n_executions": counter["n"], "marker": key}

    async def go():
        db = _get_db()
        r1 = await with_idempotency(db, key, {"id": "actor-X"}, factory)
        r2 = await with_idempotency(db, key, {"id": "actor-X"}, factory)
        r3 = await with_idempotency(db, key, {"id": "actor-X"}, factory)
        await db.idempotency_keys.delete_many({"key": key})
        return r1, r2, r3

    r1, r2, r3 = _arun(go())
    assert r1 == r2 == r3, "must return same cached response"
    assert counter["n"] == 1, \
        f"factory must run exactly ONCE, got {counter['n']}"
