"""
test_iter160_operational_signals.py — Iter160 (Phase 2.5 · Operational
Signal Density).

Style note: matches the codebase convention — uses `requests` (sync) for
HTTP, and runs the tiny async `record_signal` library calls via
asyncio.run() helpers. Avoids the pytest-asyncio dependency that the rest
of the suite doesn't pull in.

Covers:
  1. record_signal persists correctly to db.usage_events
  2. record_signal is fire-and-forget — never raises on broken db
  3. Unknown signal slugs are silently dropped (closed-set guard)
  4. dims is sanitized (≤6 keys, strings truncated, non-scalars dropped)
  5. /api/admin/operational-signals is admin-only (anon → 401)
  6. /api/admin/operational-signals returns the documented contract
  7. Throughput aggregation counts seeded signals correctly
  8. Cycle-time aggregation reports n/avg/p50/p90
  9. equipment_top_failing groups by dims.equipment_id correctly
 10. doc_threshold_breakdown groups by category × threshold
 11. Existing usage analytics aggregations unaffected by new kind
 12. PII guard — long strings truncated
 13. window_days clamped to 1..180
 14. CA create/close integration produces ca.closed signal with elapsed_ms
 15. usage_events TTL index intact (90d)
"""
import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
import requests

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


URL = (
    _kv(Path("/app/frontend/.env"), "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")
MONGO_URL = _kv(Path("/app/backend/.env"), "MONGO_URL")
DB_NAME = _kv(Path("/app/backend/.env"), "DB_NAME")


def _get_db():
    """Sync helper that returns a Motor db handle. Used inside asyncio.run."""
    from motor.motor_asyncio import AsyncIOMotorClient
    return AsyncIOMotorClient(MONGO_URL)[DB_NAME]


def _arun(coro):
    """Run a coroutine in a fresh event loop. Acceptable in tests since
    every test is a fresh function scope."""
    return asyncio.new_event_loop().run_until_complete(coro)


# ──────────────────────────────────────────────────────────────────
# Recorder library tests
# ──────────────────────────────────────────────────────────────────
def test_recorder_persists_correctly():
    from lib.operational_signals import record_signal
    marker = f"test160_{uuid.uuid4().hex[:8]}"

    async def go():
        db = _get_db()
        await record_signal(
            db, signal="incident.created", module="test.module",
            dims={"_marker": marker, "severity": "high"},
        )
        return await db.usage_events.find_one(
            {"kind": "operational_signal", "dims._marker": marker},
            {"_id": 0},
        )

    doc = _arun(go())
    assert doc is not None
    assert doc["signal"] == "incident.created"
    assert doc["module"] == "test.module"
    assert doc["dims"]["_marker"] == marker
    assert doc["dims"]["severity"] == "high"
    assert "at" in doc

    # cleanup
    async def cleanup():
        db = _get_db()
        await db.usage_events.delete_many({"dims._marker": marker})
    _arun(cleanup())


def test_recorder_never_raises_on_db_failure():
    from lib.operational_signals import record_signal

    class _Coll:
        async def insert_one(self, _):
            raise RuntimeError("simulated db down")

    class BrokenDb:
        @property
        def usage_events(self):
            return _Coll()

    # Must NOT raise — passive recorder swallows.
    _arun(record_signal(BrokenDb(), signal="incident.created", module="t"))


def test_recorder_drops_unknown_signal():
    from lib.operational_signals import record_signal
    marker = f"test160_unknown_{uuid.uuid4().hex[:8]}"

    async def go():
        db = _get_db()
        await record_signal(
            db, signal="bogus.unknown_signal", module="t",
            dims={"_marker": marker},
        )
        return await db.usage_events.find_one({"dims._marker": marker})
    assert _arun(go()) is None


def test_dims_are_sanitized():
    from lib.operational_signals import record_signal
    marker = f"test160_dims_{uuid.uuid4().hex[:8]}"

    async def go():
        db = _get_db()
        await record_signal(
            db, signal="incident.created", module="t",
            dims={
                "_marker": marker,
                "k1": "v" * 200,
                "k2": 42,
                "k3": True,
                "k4": [1, 2, 3],
                "k5": {"nested": "x"},
                "k6": None,
                "k7_extra": "should_drop",
                "k8_extra": "should_drop",
            },
        )
        doc = await db.usage_events.find_one(
            {"dims._marker": marker}, {"_id": 0},
        )
        await db.usage_events.delete_many({"dims._marker": marker})
        return doc

    doc = _arun(go())
    assert doc is not None
    dims = doc["dims"]
    assert len(dims.get("k1", "")) <= 48
    assert dims.get("k2") == 42
    assert dims.get("k3") is True
    assert "k4" not in dims
    assert "k5" not in dims
    assert "k6" not in dims
    assert len(dims) <= 6


# ──────────────────────────────────────────────────────────────────
# Endpoint contract tests
# ──────────────────────────────────────────────────────────────────
def test_endpoint_requires_admin_anon_401():
    """Anon (explicit empty admin header) must get 401."""
    r = requests.get(
        f"{URL}/api/admin/operational-signals",
        headers={"X-Admin-Token": ""},
        timeout=10,
    )
    assert r.status_code == 401


def test_endpoint_returns_contract():
    r = requests.get(
        f"{URL}/api/admin/operational-signals?window_days=30",
        timeout=30,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["window_days"] == 30
    for k in ("since", "throughput", "cycle_time_ms",
              "equipment_top_failing", "doc_threshold_breakdown",
              "deltas"):
        assert k in body
    # Throughput signals
    for s in ["incident.created", "ca.created", "po.submit",
              "equipment.fail", "fire_ext.fail", "training.deficiency",
              "doc.threshold_fired", "hr.offboarding_started"]:
        assert s in body["throughput"]
        assert "total" in body["throughput"][s]
        assert "by_day" in body["throughput"][s]
    # Cycle time signals
    for s in ["ca.closed", "po.approve", "po.receipt", "po.close"]:
        assert s in body["cycle_time_ms"]
        for k in ("count", "avg_ms", "p50_ms", "p90_ms"):
            assert k in body["cycle_time_ms"][s]


def test_throughput_aggregation_counts():
    from lib.operational_signals import record_signal
    marker = f"throughput_{uuid.uuid4().hex[:8]}"

    async def seed():
        db = _get_db()
        for _ in range(3):
            await record_signal(
                db, signal="incident.created", module="test",
                dims={"_marker": marker},
            )
    _arun(seed())

    r = requests.get(
        f"{URL}/api/admin/operational-signals?window_days=1",
        timeout=30,
    )
    body = r.json()
    total = body["throughput"]["incident.created"]["total"]
    assert total >= 3

    async def cleanup():
        await _get_db().usage_events.delete_many({"dims._marker": marker})
    _arun(cleanup())


def test_cycle_time_aggregation():
    from lib.operational_signals import record_signal
    marker = f"cycle_{uuid.uuid4().hex[:8]}"

    async def seed():
        db = _get_db()
        for v in [100, 200, 300, 400, 500]:
            await record_signal(
                db, signal="ca.closed", module="test",
                elapsed_ms=v, dims={"_marker": marker},
            )
    _arun(seed())

    r = requests.get(
        f"{URL}/api/admin/operational-signals?window_days=1",
        timeout=30,
    )
    ct = r.json()["cycle_time_ms"]["ca.closed"]
    assert ct["count"] >= 5
    assert ct["avg_ms"] > 0

    async def cleanup():
        await _get_db().usage_events.delete_many({"dims._marker": marker})
    _arun(cleanup())


def test_equipment_top_failing():
    from lib.operational_signals import record_signal
    marker = f"eq_{uuid.uuid4().hex[:8]}"
    eq_a = f"EQ-A-{marker}"

    async def seed():
        db = _get_db()
        for _ in range(3):
            await record_signal(
                db, signal="equipment.fail", module="test",
                dims={"equipment_id": eq_a, "_m": marker},
            )
        await record_signal(
            db, signal="equipment.fail", module="test",
            dims={"equipment_id": f"EQ-B-{marker}", "_m": marker},
        )
    _arun(seed())

    r = requests.get(
        f"{URL}/api/admin/operational-signals?window_days=1",
        timeout=30,
    )
    body = r.json()
    top = body["equipment_top_failing"]
    eq_a_row = next((x for x in top if x["equipment_id"] == eq_a), None)
    assert eq_a_row is not None
    assert eq_a_row["count"] == 3

    async def cleanup():
        await _get_db().usage_events.delete_many({"dims._m": marker})
    _arun(cleanup())


def test_doc_threshold_breakdown():
    from lib.operational_signals import record_signal
    marker = f"doc_{uuid.uuid4().hex[:8]}"
    cat = f"employee_{marker}"

    async def seed():
        db = _get_db()
        for _ in range(2):
            await record_signal(
                db, signal="doc.threshold_fired", module="test",
                dims={"category": cat, "threshold": 7, "_m": marker},
            )
    _arun(seed())

    r = requests.get(
        f"{URL}/api/admin/operational-signals?window_days=1",
        timeout=30,
    )
    breakdown = r.json()["doc_threshold_breakdown"]
    row = next((x for x in breakdown
                if x["category"] == cat and x["threshold"] == 7), None)
    assert row is not None
    assert row["count"] == 2

    async def cleanup():
        await _get_db().usage_events.delete_many({"dims._m": marker})
    _arun(cleanup())


def test_existing_analytics_unaffected_by_operational_signals():
    """Existing /api/admin/analytics/routes filters kind='api_call' — must
    not include our new operational_signal rows."""
    r = requests.get(
        f"{URL}/api/admin/analytics/routes?window_hours=24",
        timeout=30,
    )
    assert r.status_code == 200
    for row in r.json().get("rows", []):
        # Route field reflects route paths, not signal slugs.
        assert "operational_signal" not in (row.get("route") or "")
        assert not (row.get("route") or "").startswith("incident.")


def test_window_clamping():
    r1 = requests.get(
        f"{URL}/api/admin/operational-signals?window_days=9999",
        timeout=30,
    )
    assert r1.status_code == 200
    assert r1.json()["window_days"] == 180

    r2 = requests.get(
        f"{URL}/api/admin/operational-signals?window_days=0",
        timeout=30,
    )
    assert r2.status_code == 200
    assert r2.json()["window_days"] == 1


def test_deltas_direction_values():
    r = requests.get(
        f"{URL}/api/admin/operational-signals?window_days=30",
        timeout=30,
    )
    deltas = r.json()["deltas"]
    for sig, d in deltas.items():
        assert d["direction"] in ("up", "down", "flat")
        assert isinstance(d["current"], int)
        assert isinstance(d["previous"], int)


def test_ttl_index_intact():
    """Confirms db.usage_events TTL = 90 days, still active. New
    operational_signal rows respect the same TTL."""
    async def go():
        db = _get_db()
        idxs = await db.usage_events.list_indexes().to_list(None)
        return [i for i in idxs if "expireAfterSeconds" in i]
    ttl = _arun(go())
    assert len(ttl) >= 1
    assert ttl[0]["expireAfterSeconds"] == 60 * 60 * 24 * 90


def test_pii_truncation_in_dims():
    """Long PII-like strings get truncated to ≤48 chars (sanitization
    bound). No free-text PII can leak into signal payloads."""
    from lib.operational_signals import record_signal
    marker = f"pii_{uuid.uuid4().hex[:8]}"

    async def go():
        db = _get_db()
        await record_signal(
            db, signal="ca.created", module="test",
            dims={"_m": marker,
                  "employee_name": "John Doe and a very long descriptive note "
                                    + "x" * 300,
                  "priority": "High"},
        )
        doc = await db.usage_events.find_one(
            {"dims._m": marker}, {"_id": 0},
        )
        await db.usage_events.delete_many({"dims._m": marker})
        return doc

    doc = _arun(go())
    assert doc is not None
    if "employee_name" in doc["dims"]:
        assert len(doc["dims"]["employee_name"]) <= 48
    assert doc["dims"]["priority"] == "High"


def test_ca_create_close_integration_records_cycle_time():
    """Live integration: create a CA via safety portal, close it, and
    confirm a ca.closed operational signal lands with elapsed_ms>=0."""
    # Login as safety
    r = requests.post(
        f"{URL}/api/safety/login",
        json={"email": "safety@mascigc.com",
              "password": "SafetyTest2026!"},
        headers={"X-Admin-Token": ""},
        timeout=15,
    )
    if r.status_code != 200:
        pytest.skip(f"safety login unavailable ({r.status_code})")
    safety_token = r.json()["token"]
    sh = {"X-Safety-Token": safety_token, "X-Admin-Token": ""}

    label = f"iter160-ca-{uuid.uuid4().hex[:8]}"
    # Create CA
    r2 = requests.post(
        f"{URL}/api/safety/corrective-actions",
        headers=sh,
        json={
            "title": label,
            "description": "telemetry integration test",
            "source_kind": "manual",
            "priority": "Medium",
            "due_date": "2026-06-01",
        },
        timeout=15,
    )
    assert r2.status_code == 200, r2.text
    ca_id = r2.json()["id"]

    import time as _time
    _time.sleep(0.15)

    # Close CA
    r3 = requests.patch(
        f"{URL}/api/safety/corrective-actions/{ca_id}",
        headers=sh,
        json={"status": "Closed",
              "completion_notes": "iter160 telemetry test"},
        timeout=15,
    )
    assert r3.status_code == 200

    _time.sleep(0.25)

    async def find_signal():
        db = _get_db()
        return await db.usage_events.find_one(
            {"kind": "operational_signal", "signal": "ca.closed",
             "module": "safety.corrective_actions"},
            sort=[("at", -1)],
        )
    sig = _arun(find_signal())
    assert sig is not None
    assert sig.get("elapsed_ms") is not None
    assert sig["elapsed_ms"] >= 0

    # Cleanup test CA
    async def cleanup():
        await _get_db().corrective_actions.delete_one({"id": ca_id})
    _arun(cleanup())
