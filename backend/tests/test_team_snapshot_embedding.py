"""
tests/test_team_snapshot_embedding.py — Track 14.0-JOB-OWNERSHIP-FOUNDATION Phase 2B-2A.

Operational Writer Team-Snapshot Embedding Sweep certification.

Proves the four contracts required by the Phase 2B-2A directive:

  1. CREATE captures a frozen team_snapshot on every job-scoped writer.
  2. Records persisted PRE-roster-mutation keep their snapshot EXACTLY,
     even after the project roster changes (historical immutability).
  3. Records persisted POST-roster-mutation capture the NEW snapshot,
     so the helper is genuinely re-reading the active roster.
  4. Missing / unknown project_number is safe — submit must succeed
     and the record's snapshot is None or empty (no crash, no fake data).

Tests run against the live preview backend, write scratch records to
`project_team_assignments` + the operational collections, then delete
them on teardown so no fake data remains.

Test project: 26-05 (Phase-1 backfill — jaymn.judd is PM, see closure
ledger). Scratch role used for the immutability mutation is `co_pm`
so it never collides with an existing real assignment.
"""
from __future__ import annotations

import asyncio
import os
import sys
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pytest
import requests
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")
sys.path.insert(0, "/app/backend")

# ── env ─────────────────────────────────────────────────────────────
URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not URL:
    for line in Path("/app/frontend/.env").read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL"):
            URL = line.split("=", 1)[1].strip().rstrip("/")
            break

SUPER = {"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"}
PROJECT_NUMBER = "26-05"
TEST_TAG = f"phase2b-2a-{uuid.uuid4().hex[:8]}"
T = 30


# ── helpers ─────────────────────────────────────────────────────────
def _run(coro):
    """Run an async coroutine inside a synchronous test."""
    return asyncio.new_event_loop().run_until_complete(coro)


async def _get_db():
    cli = AsyncIOMotorClient(os.environ["MONGO_URL"])
    return cli, cli[os.environ["DB_NAME"]]


async def _find_one(coll: str, _id: str):
    cli, db = await _get_db()
    try:
        return await db[coll].find_one({"id": _id}, {"_id": 0})
    finally:
        cli.close()


# Cleanup ledger — collected across all tests, drained by the
# final test_cleanup function.
_ids_to_clean: dict[str, list[str]] = {
    "inspections": [],
    "meetings": [],
    "jhas": [],
    "incidents": [],
    "equipment_inspections": [],
}


# ── token fixture ───────────────────────────────────────────────────
@pytest.fixture(scope="module")
def tokens():
    r = requests.post(f"{URL}/api/auth/multi-login", json=SUPER, timeout=T)
    r.raise_for_status()
    return r.json()["portal_tokens"]


# ── sample payloads ─────────────────────────────────────────────────
def _inspection_payload(project_number: str = PROJECT_NUMBER):
    return {
        "project_name": "Phase2B-2A · Test",
        "project_number": project_number,
        "location": "test-loc",
        "inspection_date": "2026-02-12",
        "inspection_time": "08:00",
        "inspector_name": "snapshot-test",
        "foreman_name": "snapshot-test",
        "work_activity": "snapshot embedding test",
    }


def _meeting_payload():
    return {
        "project_name": "Phase2B-2A · Test",
        "project_number": PROJECT_NUMBER,
        "location": "test-loc",
        "meeting_date": "2026-02-12",
        "meeting_time": "08:00",
        "conducted_by": "snapshot-test",
        "topic": f"snapshot test {TEST_TAG}",
    }


def _jha_payload():
    return {
        "project_name": "Phase2B-2A · Test",
        "project_number": PROJECT_NUMBER,
        "location": "test-loc",
        "jha_date": "2026-02-12",
        "crew_lead": "snapshot-test",
        "job_title": f"snapshot test {TEST_TAG}",
        "task_steps": [],
    }


def _incident_payload():
    return {
        "project_name": "Phase2B-2A · Test",
        "project_number": PROJECT_NUMBER,
        "location": "test-loc",
        "incident_date": "2026-02-12",
        "incident_time": "08:00",
        "reported_date": "2026-02-12",
        "incident_type": "Near Miss",
        "severity": "Minor",
        "person_name": "snapshot-test",
        "reported_by": "snapshot-test",
        "osha_recordable": "No",
        "description": f"snapshot test {TEST_TAG}",
    }


def _equipment_payload():
    return {
        "project_name": "Phase2B-2A · Test",
        "project_number": PROJECT_NUMBER,
        "location": "test-loc",
        "inspection_date": "2026-02-12",
        "inspection_time": "08:00",
        "operator_name": "snapshot-test",
        "equipment_type": "Skid Steer",
        "equipment_unit": f"TEST-{TEST_TAG[:6]}",
    }


# ── helper-direct tests ─────────────────────────────────────────────
def test_helper_safe_with_none():
    async def go():
        cli, db = await _get_db()
        try:
            from lib.team_routing import snapshot_team
            assert await snapshot_team(db, None) is None
            assert await snapshot_team(db, "") is None
            res = await snapshot_team(db, "DOES-NOT-EXIST-9999")
            # Unknown project returns the standard shape with empty buckets.
            assert res is not None
            assert res["project_number"] == "DOES-NOT-EXIST-9999"
            assert all(len(v) == 0 for v in res["members"].values())
        finally:
            cli.close()
    _run(go())


def test_helper_returns_real_roster_for_known_project():
    async def go():
        cli, db = await _get_db()
        try:
            from lib.team_routing import snapshot_team
            res = await snapshot_team(db, PROJECT_NUMBER)
            assert res is not None
            assert res["project_number"] == PROJECT_NUMBER
            pm_emails = [m.get("email")
                         for m in (res["members"].get("pm") or [])]
            assert "jaymn.judd@mascigc.com" in pm_emails, res
        finally:
            cli.close()
    _run(go())


# ── writer-level tests ──────────────────────────────────────────────
def test_writer_inspection_captures_snapshot(tokens):
    h = {"X-Admin-Token": tokens["admin"], "Content-Type": "application/json"}
    r = requests.post(f"{URL}/api/inspections",
                      json=_inspection_payload(), headers=h, timeout=T)
    assert r.status_code == 200, r.text
    rec_id = r.json()["id"]
    _ids_to_clean["inspections"].append(rec_id)

    doc = _run(_find_one("inspections", rec_id))
    assert doc is not None
    snap = doc.get("team_snapshot")
    assert snap, "team_snapshot must be embedded on create"
    assert snap["project_number"] == PROJECT_NUMBER
    pm_emails = [m.get("email") for m in (snap["members"].get("pm") or [])]
    assert "jaymn.judd@mascigc.com" in pm_emails, snap


def test_writer_meeting_captures_snapshot():
    r = requests.post(f"{URL}/api/meetings",
                      json=_meeting_payload(), timeout=T)
    assert r.status_code == 200, r.text
    rec_id = r.json()["id"]
    _ids_to_clean["meetings"].append(rec_id)

    doc = _run(_find_one("meetings", rec_id))
    assert doc and doc.get("team_snapshot")
    assert doc["team_snapshot"]["project_number"] == PROJECT_NUMBER


def test_writer_jha_captures_snapshot():
    r = requests.post(f"{URL}/api/jhas",
                      json=_jha_payload(), timeout=T)
    assert r.status_code == 200, r.text
    rec_id = r.json()["id"]
    _ids_to_clean["jhas"].append(rec_id)

    doc = _run(_find_one("jhas", rec_id))
    assert doc and doc.get("team_snapshot")


def test_writer_incident_captures_snapshot(tokens):
    h = {"X-Admin-Token": tokens["admin"], "Content-Type": "application/json"}
    r = requests.post(f"{URL}/api/incidents",
                      json=_incident_payload(), headers=h, timeout=T)
    assert r.status_code == 200, r.text
    rec_id = r.json()["id"]
    _ids_to_clean["incidents"].append(rec_id)

    doc = _run(_find_one("incidents", rec_id))
    assert doc and doc.get("team_snapshot")
    assert doc["team_snapshot"]["project_number"] == PROJECT_NUMBER


def test_writer_equipment_preop_captures_snapshot():
    r = requests.post(f"{URL}/api/equipment-inspections",
                      json=_equipment_payload(), timeout=T)
    assert r.status_code == 200, r.text
    rec_id = r.json()["id"]
    _ids_to_clean["equipment_inspections"].append(rec_id)

    doc = _run(_find_one("equipment_inspections", rec_id))
    assert doc and doc.get("team_snapshot")


def test_missing_project_number_is_safe(tokens):
    h = {"X-Admin-Token": tokens["admin"], "Content-Type": "application/json"}
    payload = _inspection_payload(project_number="")
    r = requests.post(f"{URL}/api/inspections", json=payload,
                      headers=h, timeout=T)
    assert r.status_code == 200, r.text
    rec_id = r.json()["id"]
    _ids_to_clean["inspections"].append(rec_id)

    doc = _run(_find_one("inspections", rec_id))
    assert doc is not None
    # No project → snapshot helper returns None → no team_snapshot key.
    assert "team_snapshot" not in doc or doc.get("team_snapshot") is None


def test_unknown_project_number_is_safe(tokens):
    h = {"X-Admin-Token": tokens["admin"], "Content-Type": "application/json"}
    payload = _inspection_payload(project_number=f"UNKNOWN-{TEST_TAG[:6]}")
    r = requests.post(f"{URL}/api/inspections", json=payload,
                      headers=h, timeout=T)
    assert r.status_code == 200, r.text
    rec_id = r.json()["id"]
    _ids_to_clean["inspections"].append(rec_id)

    doc = _run(_find_one("inspections", rec_id))
    assert doc is not None
    snap = doc.get("team_snapshot")
    # Helper returns standard shape with empty buckets for unknown project.
    assert snap is not None
    assert snap["project_number"].startswith("UNKNOWN-")
    assert all(len(v) == 0 for v in snap["members"].values())


def test_snapshot_immutability_across_roster_mutation(tokens):
    """Historical records keep their original snapshot when the active
    roster changes; new records capture the new state."""
    h = {"X-Admin-Token": tokens["admin"], "Content-Type": "application/json"}

    async def insert_scratch_assignment():
        cli, db = await _get_db()
        try:
            await db.project_team_assignments.insert_one({
                "id": f"asn-{TEST_TAG}",
                "assignment_id": f"asn-{TEST_TAG}",
                "project_number": PROJECT_NUMBER,
                "assignment_role": "co_pm",
                "user_id": f"scratch-{TEST_TAG}",
                "email": f"{TEST_TAG}@scratch.test",
                "display_name": "Phase2B-2A scratch co_pm",
                "active": True,
                "assignment_status": "ACTIVE",
                "is_primary": False,
                "assignment_tag": TEST_TAG,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })
        finally:
            cli.close()

    # Phase 1 · capture "before" record.
    r1 = requests.post(f"{URL}/api/inspections",
                       json=_inspection_payload(), headers=h, timeout=T)
    assert r1.status_code == 200, r1.text
    before_id = r1.json()["id"]
    _ids_to_clean["inspections"].append(before_id)
    before_doc = _run(_find_one("inspections", before_id))
    assert before_doc and before_doc.get("team_snapshot")
    before_snap = before_doc["team_snapshot"]

    # Phase 2 · mutate roster — add a scratch co_pm row.
    _run(insert_scratch_assignment())

    # Phase 3 · re-read before-record. Snapshot MUST be unchanged.
    before_doc_again = _run(_find_one("inspections", before_id))
    assert before_doc_again["team_snapshot"] == before_snap, (
        "Historical record snapshot was mutated by roster change.")

    # Phase 4 · submit a new record. Its snapshot MUST contain the
    # scratch co_pm.
    r2 = requests.post(f"{URL}/api/inspections",
                       json=_inspection_payload(), headers=h, timeout=T)
    assert r2.status_code == 200, r2.text
    after_id = r2.json()["id"]
    _ids_to_clean["inspections"].append(after_id)
    after_doc = _run(_find_one("inspections", after_id))
    assert after_doc and after_doc.get("team_snapshot")
    new_co_pm_uids = [
        m.get("user_id")
        for m in (after_doc["team_snapshot"]["members"].get("co_pm") or [])
    ]
    assert f"scratch-{TEST_TAG}" in new_co_pm_uids, (
        after_doc["team_snapshot"])

    # And the BEFORE record still does NOT have the scratch user.
    before_co_pm_uids = [
        m.get("user_id")
        for m in (before_snap["members"].get("co_pm") or [])
    ]
    assert f"scratch-{TEST_TAG}" not in before_co_pm_uids


def test_zzz_cleanup():
    """Run last (zzz prefix) — delete every scratch record + assignment."""

    async def go():
        cli, db = await _get_db()
        try:
            for coll, ids in _ids_to_clean.items():
                if ids:
                    await db[coll].delete_many({"id": {"$in": ids}})
            await db.project_team_assignments.delete_many(
                {"assignment_tag": TEST_TAG})

            for coll, ids in _ids_to_clean.items():
                if ids:
                    remaining = await db[coll].count_documents(
                        {"id": {"$in": ids}})
                    assert remaining == 0, (
                        f"{coll} still has {remaining} scratch rows")
            scratch_assignments = await db.project_team_assignments.count_documents(
                {"assignment_tag": TEST_TAG})
            assert scratch_assignments == 0
        finally:
            cli.close()
    _run(go())
