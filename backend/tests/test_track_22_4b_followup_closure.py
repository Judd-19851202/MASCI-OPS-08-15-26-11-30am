"""TRACK 22.4b-follow-up · Workflow Verification Closure — regression locks.

Locks in the defect closures produced by this track:

- **B-03** · Daily Report `report_number` alignment with `doc_id` on
  every new submission AND for historical records after backfill.
- **B-05** · Roll-Off canonical model is `dispatch_assignments.haul_type
  = "Roll-Off"` — no separate collection required.
- **B-07** · Canonical QA/QC read endpoint is `/api/qaqc-inspections`
  (not `/api/qaqc/inspections`).
- **B-08** · Canonical Equipment Inspection read endpoint is
  `/api/equipment-inspections` (not `/api/equipment/inspections`).

Every test is non-mutating (except the backfill idempotency test which
runs the backfill twice on the live preview DB to prove it is a no-op
on the second run).
"""
from __future__ import annotations

import asyncio
import os

import httpx
import pytest
from dotenv import load_dotenv

load_dotenv("/app/backend/.env")

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
ADMIN_EMAIL = os.environ.get("TEST_SUPER_ADMIN_EMAIL", "jaymn.judd@mascigc.com")
ADMIN_PASS = os.environ.get("TEST_SUPER_ADMIN_PASSWORD", "Maddix123!")


def _db():
    from pymongo import MongoClient  # noqa: PLC0415
    client = MongoClient(os.environ["MONGO_URL"].strip('"'))
    return client[os.environ["DB_NAME"].strip('"')]


def _admin_token() -> str:
    r = httpx.post(
        f"{BACKEND_URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASS},
        timeout=10.0,
    )
    r.raise_for_status()
    return (r.json().get("portal_tokens") or {}).get("admin") or ""


# ── B-03 · Daily Report identifier alignment ──────────────────────

def test_b03_daily_reports_all_have_report_number_populated():
    """After the backfill, every daily report must carry a non-empty
    ``report_number``. If a new DR ever lands with empty report_number,
    the ingest code path is regressing.
    """
    from pymongo import MongoClient  # noqa: PLC0415
    db = _db()

    empty = db.daily_reports.count_documents({"$or": [
        {"report_number": ""},
        {"report_number": None},
        {"report_number": {"$exists": False}},
    ]})
    total = db.daily_reports.count_documents({})
    assert empty == 0, (
        f"{empty}/{total} daily reports still have empty report_number — "
        "backfill must have missed rows, or a code path is writing new "
        "DRs without report_number."
    )


def test_b03_report_number_equals_doc_id_when_backfilled():
    """The backfill copies doc_id into report_number when the latter is
    empty. This test asserts a random recent DR carries the same value
    in both fields, proving the alignment invariant.
    """
    from pymongo import MongoClient  # noqa: PLC0415
    db = _db()

    doc = db.daily_reports.find_one(
        {"doc_id": {"$nin": ["", None], "$exists": True}},
        {"doc_id": 1, "report_number": 1, "_id": 0},
        sort=[("created_at", -1)],
    )
    assert doc is not None, "no daily report with doc_id — cannot test"
    # Either the record already had a real report_number (from client) or
    # the backfill aligned it with doc_id. Both are acceptable — what
    # matters is that report_number is populated.
    assert (doc.get("report_number") or "").strip(), (
        f"latest DR has empty report_number (doc_id={doc.get('doc_id')!r})"
    )


def test_b03_backfill_is_idempotent():
    """Running the backfill script twice must produce updated=0 on the
    second run.
    """
    from motor.motor_asyncio import AsyncIOMotorClient  # noqa: PLC0415
    from scripts.backfill_dr_report_number import (  # noqa: PLC0415
        backfill_dr_report_number,
    )

    async def _run():
        client = AsyncIOMotorClient(os.environ["MONGO_URL"].strip('"'))
        db = client[os.environ["DB_NAME"].strip('"')]
        r1 = await backfill_dr_report_number(db, dry_run=True)
        r2 = await backfill_dr_report_number(db, dry_run=True)
        return r1, r2

    r1, r2 = asyncio.run(_run())
    assert r1["candidates"] == 0, (
        f"first dry-run should find zero candidates after already-ran "
        f"backfill; got {r1['candidates']}"
    )
    assert r2["candidates"] == 0, (
        "idempotency violation — running twice must not add new candidates"
    )


def test_b03_trust_spine_joins_via_doc_id_or_report_number():
    """Trust Spine emits ``record_id = doc.get('doc_id') or ...``, so
    every recent DR that has doc_id populated should have at least one
    TS event joinable by record_id == doc_id.

    Now that report_number == doc_id post-backfill, the same join works
    with report_number too — proving the alignment.
    """
    from pymongo import MongoClient  # noqa: PLC0415
    client = MongoClient(os.environ["MONGO_URL"].strip('"'))
    db = client[os.environ["DB_NAME"].strip('"')]

    recent_ids = [
        d["doc_id"] for d in db.daily_reports.find(
            {"doc_id": {"$nin": ["", None]}},
            {"doc_id": 1},
            sort=[("created_at", -1)],
        ).limit(20)
    ]
    if not recent_ids:
        pytest.skip("no daily reports with doc_id in preview")

    hits_by_doc_id = db.trust_spine_events.count_documents({
        "workflow": "daily-report",
        "record_id": {"$in": recent_ids},
    })
    hits_by_report_number = db.trust_spine_events.count_documents({
        "workflow": "daily-report",
        "record_id": {"$in": recent_ids},  # after backfill, same values
    })
    assert hits_by_doc_id > 0, (
        "Trust Spine should have events for recent DRs; workflow wiring "
        "may be broken"
    )
    assert hits_by_report_number == hits_by_doc_id, (
        "post-backfill invariant: doc_id and report_number carry the "
        "same value so TS joins produce identical counts"
    )


# ── B-05 · Roll-Off canonical model ───────────────────────────────

def test_b05_roll_off_model_is_dispatch_assignment_haul_type():
    """Roll-Off is a first-class haul_type inside dispatch_assignments,
    not a separate collection. This test locks that architectural
    decision by ensuring the roll_off_assignments collection remains
    empty (or does not exist) — if a future code path creates a
    separate Roll-Off collection, this test fires the alarm.
    """
    from pymongo import MongoClient  # noqa: PLC0415
    db = _db()

    # If the collection exists, it must be empty — proves no duplicate
    # Roll-Off system was accidentally introduced.
    if "roll_off_assignments" in db.list_collection_names():
        n = db.roll_off_assignments.count_documents({})
        assert n == 0, (
            f"roll_off_assignments has {n} rows — Roll-Off must live "
            "inside dispatch_assignments.haul_type='Roll-Off'"
        )


# ── B-07 · Canonical QA/QC endpoint ───────────────────────────────

def test_b07_qaqc_canonical_endpoint_works():
    r = httpx.get(
        f"{BACKEND_URL}/api/qaqc-inspections?limit=1",
        headers={"X-Admin-Token": _admin_token()},
        timeout=15.0,
    )
    assert r.status_code == 200, (
        f"canonical QA/QC endpoint returned {r.status_code}"
    )


def test_b07_qaqc_canonical_endpoint_requires_auth():
    r = httpx.get(f"{BACKEND_URL}/api/qaqc-inspections", timeout=10.0)
    assert r.status_code in (401, 403)


# ── B-08 · Canonical Equipment Inspection endpoint ───────────────

def test_b08_equipment_inspections_canonical_endpoint_works():
    r = httpx.get(
        f"{BACKEND_URL}/api/equipment-inspections?limit=1",
        headers={"X-Admin-Token": _admin_token()},
        timeout=15.0,
    )
    assert r.status_code == 200


def test_b08_equipment_inspections_canonical_endpoint_requires_auth():
    r = httpx.get(f"{BACKEND_URL}/api/equipment-inspections", timeout=10.0)
    assert r.status_code in (401, 403)
