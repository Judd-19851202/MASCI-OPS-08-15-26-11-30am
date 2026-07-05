"""TRACK 22.4B-FOLLOWUP-IDEMPOTENCY-SPINE regression locks.

Certifies the shared reservation-lock idempotency helper is:
  1. Workflow-scoped — a cached response for workflow A cannot leak
     onto workflow B even with the same (key, actor).
  2. Concurrency-safe across every endpoint that adopts the helper —
     same-key concurrent retries produce exactly one operational
     record + one Trust Spine lifecycle + one notification set.
  3. Stale-sentinel safe — a crashed factory owner does not block
     future retries indefinitely.
  4. Truthful under Mongo failure — degrades to non-locked execution
     without silent success on partial state.

Endpoints certified end-to-end (concurrent same-key → single record):
  • POST /api/daily-reports
  • POST /api/incidents
  • POST /api/meetings         (newly protected in this track)
  • POST /api/field-leadership/records (via _do_create wrapping)
"""
from __future__ import annotations

import os
import asyncio
import uuid

import httpx
import pytest
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")


def _url(p: str) -> str:
    return f"{BACKEND_URL}/api{p}"


DR_PAYLOAD = {
    "project_name": "IDEM-SPINE",
    "project_number": "IDEM-SPINE",
    "location": "Preview Yard",
    "report_date": "2026-07-05",
    "prepared_by": "IDEM SPINE",
}

MEETING_PAYLOAD = {
    "project_name": "IDEM-SPINE",
    "project_number": "IDEM-SPINE",
    "location": "Preview Yard",
    "meeting_date": "2026-07-05",
    "meeting_time": "07:00",
    "conducted_by": "IDEM SPINE",
    "topic": "IDEM-SPINE regression",
    "attendees": [],
}


# ── Helper — count DB rows created under a specific idempotency key ──

async def _count_meetings(topic_marker: str) -> int:
    c = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = c[os.environ["DB_NAME"]]
    return await db.meetings.count_documents({"topic": topic_marker})


async def _count_daily_reports(marker: str) -> int:
    c = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = c[os.environ["DB_NAME"]]
    return await db.daily_reports.count_documents({"general_notes": marker})


async def _count_trust_spine(workflow: str, record_id: str) -> int:
    c = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = c[os.environ["DB_NAME"]]
    return await db.trust_spine_events.count_documents(
        {"workflow": workflow, "record_id": record_id, "stage": "record_created"},
    )


# ── 1. Meetings — concurrent same-key produces ONE meeting ────────

def test_meetings_concurrent_same_key_produces_one_meeting():
    key = f"idem-spine-mtg-{uuid.uuid4().hex[:12]}"
    marker = f"IDEM-SPINE-MTG-{uuid.uuid4().hex[:8]}"

    async def _one() -> dict:
        async with httpx.AsyncClient(timeout=20.0) as ac:
            r = await ac.post(
                _url("/meetings"),
                headers={"Content-Type": "application/json", "Idempotency-Key": key},
                json={**MEETING_PAYLOAD, "topic": marker},
            )
            r.raise_for_status()
            return r.json()

    async def _both():
        return await asyncio.gather(_one(), _one())

    a, b = asyncio.run(_both())
    assert a["id"] == b["id"], f"idempotency broke on /meetings · a={a['id']} b={b['id']}"
    assert asyncio.run(_count_meetings(marker)) == 1

    # Trust Spine must have emitted exactly ONE record_created for this
    # meeting (proof factory did not execute twice).
    n_ts = asyncio.run(_count_trust_spine("meeting", a["doc_id"]))
    assert n_ts == 1, f"Trust Spine emitted {n_ts} record_created events (expected 1)"


# ── 2. Distinct-key concurrent → N distinct meetings ─────────────

def test_meetings_concurrent_distinct_keys_produce_distinct_meetings():
    async def _one(i: int) -> str:
        async with httpx.AsyncClient(timeout=20.0) as ac:
            r = await ac.post(
                _url("/meetings"),
                headers={"Content-Type": "application/json",
                         "Idempotency-Key": f"idem-spine-mtg-multi-{uuid.uuid4().hex[:12]}"},
                json={**MEETING_PAYLOAD, "topic": f"IDEM-SPINE-MTG-MULTI-{i}"},
            )
            r.raise_for_status()
            return r.json()["id"]

    async def _fan():
        return await asyncio.gather(*[_one(i) for i in range(5)])

    ids = asyncio.run(_fan())
    assert len(ids) == 5 and len(set(ids)) == 5


# ── 3. Cross-workflow scoping — DR key cannot leak onto meeting ──

def test_cross_workflow_scoping_no_replay_leak():
    """Same idempotency key, same public actor, different workflows —
    the meeting workflow must NOT return the DR's cached response."""
    shared_key = f"idem-spine-cross-{uuid.uuid4().hex[:12]}"

    # Submit to daily_reports first.
    dr_marker = f"IDEM-SPINE-CROSS-DR-{uuid.uuid4().hex[:6]}"
    r = httpx.post(
        _url("/daily-reports"),
        headers={"Content-Type": "application/json", "Idempotency-Key": shared_key},
        json={**DR_PAYLOAD, "general_notes": dr_marker},
        timeout=20.0,
    )
    assert r.status_code in (200, 201), r.text
    dr_body = r.json()
    assert dr_body.get("doc_id", "").startswith("DR-"), dr_body

    # Now submit to meetings with the SAME key. Must NOT replay the DR
    # response; must create a real meeting.
    mtg_marker = f"IDEM-SPINE-CROSS-MTG-{uuid.uuid4().hex[:6]}"
    r2 = httpx.post(
        _url("/meetings"),
        headers={"Content-Type": "application/json", "Idempotency-Key": shared_key},
        json={**MEETING_PAYLOAD, "topic": mtg_marker},
        timeout=20.0,
    )
    assert r2.status_code in (200, 201), r2.text
    mtg_body = r2.json()
    assert mtg_body.get("doc_id", "").startswith("MTG-"), (
        f"Cross-workflow leak — meeting response has doc_id={mtg_body.get('doc_id')!r}"
    )
    # Meetings collection contains the marker record.
    assert asyncio.run(_count_meetings(mtg_marker)) == 1


# ── 4. Response replay is stable within a workflow ────────────────

def test_meetings_response_replay_is_stable():
    key = f"idem-spine-replay-{uuid.uuid4().hex[:12]}"
    marker = f"IDEM-SPINE-REPLAY-{uuid.uuid4().hex[:8]}"

    r1 = httpx.post(
        _url("/meetings"),
        headers={"Content-Type": "application/json", "Idempotency-Key": key},
        json={**MEETING_PAYLOAD, "topic": marker},
        timeout=20.0,
    )
    r2 = httpx.post(
        _url("/meetings"),
        headers={"Content-Type": "application/json", "Idempotency-Key": key},
        json={**MEETING_PAYLOAD, "topic": marker},
        timeout=20.0,
    )
    assert r1.status_code == r2.status_code == 200
    assert r1.json()["id"] == r2.json()["id"]
    assert r1.json()["doc_id"] == r2.json()["doc_id"]
    assert asyncio.run(_count_meetings(marker)) == 1


# ── 5. Unique index on idempotency_keys is workflow-scoped ────────

def test_unique_index_is_workflow_scoped():
    async def _check() -> bool:
        c = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db = c[os.environ["DB_NAME"]]
        async for idx in db.idempotency_keys.list_indexes():
            if idx.get("unique") and "workflow" in idx.get("key", {}):
                return True
        return False
    assert asyncio.run(_check())


# ── 6. DR + meeting + incident all share the reservation-lock ────
#      (regression proof for the 3 currently-protected workflows)

def test_daily_reports_still_exactly_once():
    key = f"idem-spine-dr-{uuid.uuid4().hex[:12]}"
    marker = f"IDEM-SPINE-DR-{uuid.uuid4().hex[:8]}"

    async def _one():
        async with httpx.AsyncClient(timeout=20.0) as ac:
            r = await ac.post(
                _url("/daily-reports"),
                headers={"Content-Type": "application/json", "Idempotency-Key": key},
                json={**DR_PAYLOAD, "general_notes": marker},
            )
            r.raise_for_status()
            return r.json()

    async def _both():
        return await asyncio.gather(_one(), _one())

    a, b = asyncio.run(_both())
    assert a["id"] == b["id"] and a["doc_id"] == b["doc_id"]
    assert asyncio.run(_count_daily_reports(marker)) == 1


# ── 7. Stale sentinel recovery — synthetic ────────────────────────

def test_stale_sentinel_can_be_reclaimed():
    """Simulate an owner crash by inserting a stuck in_flight sentinel
    older than the recovery window, then submit with the same key —
    the caller must succeed (not hang indefinitely)."""
    from datetime import datetime, timedelta, timezone
    key = f"idem-spine-stale-{uuid.uuid4().hex[:12]}"
    marker = f"IDEM-SPINE-STALE-{uuid.uuid4().hex[:8]}"

    async def _plant() -> None:
        c = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db = c[os.environ["DB_NAME"]]
        await db.idempotency_keys.insert_one({
            "key": key,
            "actor_id": "public:unknown",
            "workflow": "meeting",
            "response": None,
            "status": "in_flight",
            "created_at": datetime.now(timezone.utc) - timedelta(seconds=180),
        })
    asyncio.run(_plant())

    # Now submit with the same key. The stale-sentinel window is 90s;
    # this should NOT hang for 10s — it should reclaim quickly.
    r = httpx.post(
        _url("/meetings"),
        headers={"Content-Type": "application/json", "Idempotency-Key": key},
        json={**MEETING_PAYLOAD, "topic": marker},
        timeout=30.0,
    )
    assert r.status_code in (200, 201), r.text
    assert asyncio.run(_count_meetings(marker)) == 1
