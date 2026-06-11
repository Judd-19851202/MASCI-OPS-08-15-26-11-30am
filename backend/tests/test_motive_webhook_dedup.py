"""
WEBHOOK-DEDUP-001 · Motive webhook deduplication certification.

These tests prove that `MotiveService.process_webhook` is idempotent under
Motive's at-least-once delivery model, multi-worker concurrency, and the
scheduler/webhook overlap case. They use the local preview database
(motor_asyncio.AsyncIOMotorClient pointing to whatever MONGO_URL the
preview backend uses) and clean up after themselves.

Run from /app/backend:
    python -m pytest tests/test_motive_webhook_dedup.py -v
"""
from __future__ import annotations
import asyncio
import json
import os
import sys
import uuid
from pathlib import Path

import pytest

# Ensure /app/backend is importable
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from motor.motor_asyncio import AsyncIOMotorClient   # noqa: E402
from services.motive_service import (                # noqa: E402
    MotiveService,
    ensure_motive_events_indexes,
    _compute_event_signature,
)


def _mongo_url() -> str:
    # Resolve MONGO_URL from /app/backend/.env if not already in env.
    env = os.environ.get("MONGO_URL")
    if env:
        return env
    envfile = Path("/app/backend/.env")
    for line in envfile.read_text().splitlines():
        if line.startswith("MONGO_URL"):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("MONGO_URL not found")


def _db_name() -> str:
    env = os.environ.get("DB_NAME")
    if env:
        return env
    envfile = Path("/app/backend/.env")
    for line in envfile.read_text().splitlines():
        if line.startswith("DB_NAME"):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    raise RuntimeError("DB_NAME not found")


@pytest.fixture
async def db():
    client = AsyncIOMotorClient(_mongo_url())
    db = client[_db_name()]
    await ensure_motive_events_indexes(db)
    yield db
    client.close()


def _payload(event_id: str = "EVT-001", lat: float = 28.93, lon: float = -80.94) -> bytes:
    body = {
        "event_id":   event_id,
        "event_type": "vehicle_gps",
        "vehicle":    {"id": 1438250, "number": "DPT002-6387"},
        "location":   {"lat": lat, "lon": lon, "located_at": "2026-06-11T09:30:00Z"},
    }
    return json.dumps(body).encode("utf-8")


@pytest.mark.asyncio
async def test_scenario_a_new_event_stored(db):
    """Scenario A — first delivery stores a row."""
    svc = MotiveService(db, {"enabled": True})
    eid = f"DEDUP-A-{uuid.uuid4().hex[:8]}"
    res = await svc.process_webhook(raw_body=_payload(eid), headers={})
    try:
        assert res["status"] == "stored"
        assert res["stored"] is True
        assert res["event_signature"]
        # Verify row exists
        count = await db.motive_events.count_documents(
            {"event_signature": res["event_signature"]},
        )
        assert count == 1
    finally:
        await db.motive_events.delete_one({"event_signature": res["event_signature"]})


@pytest.mark.asyncio
async def test_scenario_b_retry_ignored(db):
    """Scenario B — identical retry returns duplicate, does NOT create a second row."""
    svc = MotiveService(db, {"enabled": True})
    eid = f"DEDUP-B-{uuid.uuid4().hex[:8]}"
    payload = _payload(eid)

    r1 = await svc.process_webhook(raw_body=payload, headers={})
    r2 = await svc.process_webhook(raw_body=payload, headers={})
    sig = r1["event_signature"]
    try:
        assert r1["status"] == "stored"
        assert r1["stored"] is True
        assert r2["status"] == "duplicate"
        assert r2["stored"] is False
        # Exactly one row
        count = await db.motive_events.count_documents({"event_signature": sig})
        assert count == 1
    finally:
        await db.motive_events.delete_one({"event_signature": sig})


@pytest.mark.asyncio
async def test_scenario_c_100_retries_one_row(db):
    """Scenario C — 100 retries collapse to exactly one stored row."""
    svc = MotiveService(db, {"enabled": True})
    eid = f"DEDUP-C-{uuid.uuid4().hex[:8]}"
    payload = _payload(eid)

    first = await svc.process_webhook(raw_body=payload, headers={})
    sig = first["event_signature"]
    try:
        assert first["stored"] is True
        # 99 more retries
        for _ in range(99):
            r = await svc.process_webhook(raw_body=payload, headers={})
            assert r["status"] == "duplicate", r
            assert r["stored"] is False
        count = await db.motive_events.count_documents({"event_signature": sig})
        assert count == 1
    finally:
        await db.motive_events.delete_one({"event_signature": sig})


@pytest.mark.asyncio
async def test_scenario_d_concurrent_delivery(db):
    """Scenario D — concurrent inserts (race on the unique index)."""
    svc = MotiveService(db, {"enabled": True})
    eid = f"DEDUP-D-{uuid.uuid4().hex[:8]}"
    payload = _payload(eid)

    results = await asyncio.gather(
        *[svc.process_webhook(raw_body=payload, headers={}) for _ in range(20)],
        return_exceptions=True,
    )
    sig = None
    for r in results:
        if isinstance(r, dict) and r.get("event_signature"):
            sig = r["event_signature"]
            break
    try:
        assert sig is not None
        # Exactly one row landed
        count = await db.motive_events.count_documents({"event_signature": sig})
        assert count == 1
        # And exactly one "stored", rest "duplicate"
        stored = sum(1 for r in results
                     if isinstance(r, dict) and r.get("status") == "stored")
        duplicates = sum(1 for r in results
                         if isinstance(r, dict) and r.get("status") == "duplicate")
        assert stored == 1, f"expected 1 stored, got {stored}"
        assert duplicates == 19, f"expected 19 duplicates, got {duplicates}"
    finally:
        await db.motive_events.delete_one({"event_signature": sig})


@pytest.mark.asyncio
async def test_scenario_e_scheduler_webhook_overlap(db):
    """Scenario E — scheduler poll already wrote a row with the SAME
    natural identity (same vehicle, same located_at, same lat/lon).
    A subsequent webhook for the same GPS fix MUST be deduped."""
    svc = MotiveService(db, {"enabled": True})

    # Manually craft a poll-equivalent signature and pre-seed.
    sig = _compute_event_signature(
        provider="motive", event_kind="vehicle_gps",
        vehicle_id="1438250", driver_id="",
        event_at="2026-06-11T09:30:00Z",
        lat=28.93, lon=-80.94, raw_event_id=1438250,
    )
    await db.motive_events.insert_one({
        "id":              str(uuid.uuid4()),
        "provider":        "motive",
        "event_kind":      "vehicle_gps",
        "event_family":    "vehicle_gps",
        "event_signature": sig,
        "source":          "poll",
        "event_at":        "2026-06-11T09:30:00Z",
        "received_at":     "2026-06-11T09:30:00Z",
        "vehicle_id":      "1438250",
        "lat":             28.93,
        "lon":             -80.94,
        "raw":             {"id": 1438250},
    })

    # Webhook arrives carrying the same identity (vehicle.id, lat/lon, located_at).
    body = json.dumps({
        "event_type": "vehicle_gps",
        "vehicle":    {"id": 1438250},
        "location":   {"lat": 28.93, "lon": -80.94, "located_at": "2026-06-11T09:30:00Z"},
        "id":         1438250,
    }).encode("utf-8")
    res = await svc.process_webhook(raw_body=body, headers={})
    try:
        assert res["status"] == "duplicate", res
        assert res["stored"] is False
        count = await db.motive_events.count_documents({"event_signature": sig})
        assert count == 1
    finally:
        await db.motive_events.delete_one({"event_signature": sig})
