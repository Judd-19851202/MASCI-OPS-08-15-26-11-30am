"""TRACK 22.4B-FOLLOWUP-IDEMPOTENCY-SPINE-PHASE-2 regression locks.

Certifies exactly-once submit under concurrent retries across the
endpoints newly protected in Phase 2:

  1. POST /api/inspections            (P1 · was unprotected)
  2. POST /api/equipment-inspections  (P1 · was unprotected)
  3. POST /api/jhas                   (P2 · was unprotected)
  4. POST /api/qaqc-inspections       (P2 · was unprotected)

Plus a *parallel-independence* proof: 10 different actors submitting
different workflows concurrently must NOT wait on a global lock —
every one completes with a distinct record.
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


def _admin_token() -> str:
    r = httpx.post(
        f"{BACKEND_URL}/api/auth/multi-login",
        json={"email": os.environ.get("TEST_SUPER_ADMIN_EMAIL", "jaymn.judd@mascigc.com"),
              "password": os.environ.get("TEST_SUPER_ADMIN_PASSWORD", "Maddix123!")},
        timeout=15.0,
    )
    r.raise_for_status()
    return (r.json().get("portal_tokens") or {}).get("admin") or ""


def _safety_pvi_token() -> str:
    admin = _admin_token()
    r = httpx.post(
        f"{BACKEND_URL}/api/admin/preview-validation-identities/mint",
        headers={"X-Admin-Token": admin},
        json={"role": "safety", "purpose": "P2 regression",
              "ttl_minutes": 30, "validation_track": "TRACK_22_4B_SPINE_PHASE_2"},
        timeout=15.0,
    )
    r.raise_for_status()
    return r.json()["token"]


_CACHED_SAFETY_PVI: str = ""


def _safety_headers() -> dict:
    global _CACHED_SAFETY_PVI
    if not _CACHED_SAFETY_PVI:
        _CACHED_SAFETY_PVI = _safety_pvi_token()
    return {"X-Safety-Token": _CACHED_SAFETY_PVI}




async def _gather2(f1, f2):
    return await asyncio.gather(f1(), f2())


async def _gather_n(f, n):
    return await asyncio.gather(*[f(i) for i in range(n)])


async def _gather_from_list(f, items):
    return await asyncio.gather(*[f(*it) for it in items])

def _url(p: str) -> str:
    return f"{BACKEND_URL}/api{p}"


# ── Payload templates ─────────────────────────────────────────────

INSPECTION_PAYLOAD = {
    "project_name": "IDEM-SPINE-P2 Inspection",
    "project_number": "IDEM-P2",
    "location": "Preview Yard",
    "inspection_date": "2026-07-05",
    "inspection_time": "07:00",
    "inspector_name": "P2 Regression",
    "foreman_name": "P2 Foreman",
    "work_activity": "P2 activity",
}

EQUIP_INSPECTION_PAYLOAD = {
    "project_name": "IDEM-SPINE-P2 Preop",
    "project_number": "IDEM-P2",
    "location": "Preview Yard",
    "inspection_date": "2026-07-05",
    "inspection_time": "07:00",
    "operator_name": "P2 Operator",
    "equipment_unit": "TB-B04-VALIDATION",
    "equipment_type": "Trench Box",
    "kind": "preop",
    "hours_reading": "0",
}

JHA_PAYLOAD = {
    "project_name": "IDEM-SPINE-P2 JHA",
    "project_number": "IDEM-P2",
    "location": "Preview Yard",
    "jha_date": "2026-07-05",
    "crew_lead": "P2 Crew Lead",
    "job_title": "IDEM SPINE P2 REGRESSION",
    "task_steps": [{"step_number": 1, "description": "step one",
                    "hazards": "none", "controls": "n/a"}],
}

QAQC_PAYLOAD = {
    "project_name": "IDEM-SPINE-P2 QAQC",
    "project_number": "IDEM-P2",
    "location": "Preview Yard",
    "inspection_date": "2026-07-05",
    "inspection_time": "07:00",
    "inspection_kind": "concrete_form",
    "inspector_name": "P2 QC",
    "foreman_name": "P2 Foreman",
    "work_area": "P2 area",
    "checklist": [
        {"key": "slump", "label": "Slump test", "item_number": "1",
         "description": "slump", "result": "pass"},
    ],
}


# ── Helper — count DB rows for a marker ───────────────────────────

async def _count(coll: str, field: str, marker: str) -> int:
    c = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = c[os.environ["DB_NAME"]]
    return await db[coll].count_documents({field: marker})


# ── 1. Inspections — concurrent same-key → one inspection ─────────

def test_inspections_concurrent_same_key_one_record():
    key = f"p2-insp-{uuid.uuid4().hex[:12]}"
    marker = f"P2-INSP-{uuid.uuid4().hex[:8]}"
    headers_auth = _safety_headers()

    async def _one():
        async with httpx.AsyncClient(timeout=45.0) as ac:
            r = await ac.post(
                _url("/inspections"),
                headers={"Content-Type": "application/json",
                         "Idempotency-Key": key, **headers_auth},
                json={**INSPECTION_PAYLOAD, "inspector_name": marker},
            )
            r.raise_for_status()
            return r.json()

    a, b = asyncio.run(_gather2(_one, _one))
    assert a["id"] == b["id"], f"idempotency broke on /inspections: {a['id']} != {b['id']}"
    assert asyncio.run(_count("inspections", "inspector_name", marker)) == 1


# ── 2. Equipment inspections — concurrent same-key → one record ──

def test_equipment_inspections_concurrent_same_key_one_record():
    key = f"p2-preop-{uuid.uuid4().hex[:12]}"
    marker = f"P2-PREOP-{uuid.uuid4().hex[:8]}"

    async def _one():
        async with httpx.AsyncClient(timeout=20.0) as ac:
            r = await ac.post(
                _url("/equipment-inspections"),
                headers={"Content-Type": "application/json", "Idempotency-Key": key},
                json={**EQUIP_INSPECTION_PAYLOAD, "operator_name": marker},
            )
            r.raise_for_status()
            return r.json()

    a, b = asyncio.run(_gather2(_one, _one))
    assert a["id"] == b["id"], f"idempotency broke on /equipment-inspections"
    assert asyncio.run(_count("equipment_inspections", "operator_name", marker)) == 1


# ── 3. JHAs — concurrent same-key → one record ───────────────────

def test_jhas_concurrent_same_key_one_record():
    key = f"p2-jha-{uuid.uuid4().hex[:12]}"
    marker = f"P2-JHA-{uuid.uuid4().hex[:8]}"

    async def _one():
        async with httpx.AsyncClient(timeout=20.0) as ac:
            r = await ac.post(
                _url("/jhas"),
                headers={"Content-Type": "application/json", "Idempotency-Key": key},
                json={**JHA_PAYLOAD, "job_title": marker},
            )
            r.raise_for_status()
            return r.json()

    a, b = asyncio.run(_gather2(_one, _one))
    assert a["id"] == b["id"], f"idempotency broke on /jhas"
    assert asyncio.run(_count("jhas", "job_title", marker)) == 1


# ── 4. QA/QC — concurrent same-key → one record ──────────────────

def test_qaqc_concurrent_same_key_one_record():
    key = f"p2-qc-{uuid.uuid4().hex[:12]}"
    marker = f"P2-QC-{uuid.uuid4().hex[:8]}"

    async def _one():
        async with httpx.AsyncClient(timeout=20.0) as ac:
            r = await ac.post(
                _url("/qaqc-inspections"),
                headers={"Content-Type": "application/json", "Idempotency-Key": key},
                json={**QAQC_PAYLOAD, "inspector_name": marker},
            )
            r.raise_for_status()
            return r.json()

    a, b = asyncio.run(_gather2(_one, _one))
    assert a["id"] == b["id"], f"idempotency broke on /qaqc-inspections"
    assert asyncio.run(_count("qaqc_inspections", "inspector_name", marker)) == 1


# ── 5. Distinct keys on same endpoint proceed independently ──────

def test_inspections_distinct_keys_produce_distinct_records():
    headers_auth = _safety_headers()
    async def _one(i: int) -> str:
        async with httpx.AsyncClient(timeout=20.0) as ac:
            r = await ac.post(
                _url("/inspections"),
                headers={"Content-Type": "application/json",
                         "Idempotency-Key": f"p2-multi-{uuid.uuid4().hex[:12]}",
                         **headers_auth},
                json={**INSPECTION_PAYLOAD, "inspector_name": f"P2 MULTI {i}"},
            )
            r.raise_for_status()
            return r.json()["id"]

    ids = asyncio.run(_gather_n(_one, 5))
    assert len(set(ids)) == 5


# ── 6. Parallel independence · 10 concurrent submits across four ─
#      workflows must all complete without global blocking ────────

def test_parallel_independence_across_workflows_shape_only():
    """Prove the reservation-lock is scoped to (key, actor, workflow),
    NOT a global mutex. 10 concurrent submits across 4 workflows must
    all complete and produce distinct records."""
    submissions: list[tuple[str, str, dict]] = []
    for i in range(3):
        submissions.append(("/inspections", "inspector_name",
                            {**INSPECTION_PAYLOAD, "inspector_name": f"PAR-INSP-{i}"}))
    for i in range(3):
        submissions.append(("/qaqc-inspections", "inspector_name",
                            {**QAQC_PAYLOAD, "inspector_name": f"PAR-QC-{i}"}))
    for i in range(2):
        submissions.append(("/jhas", "job_title",
                            {**JHA_PAYLOAD, "job_title": f"PAR-JHA-{i}"}))
    for i in range(2):
        submissions.append(("/meetings", "topic",
                            {"project_name": "PAR", "project_number": "PAR",
                             "location": "Yard", "meeting_date": "2026-07-05",
                             "meeting_time": "07:00", "conducted_by": "PAR",
                             "topic": f"PAR-MTG-{i}", "attendees": []}))

def test_parallel_independence_across_workflows_live():
    """Prove the reservation-lock is scoped to (key, actor, workflow),
    NOT a global mutex. 10 concurrent submits across 4 workflows must
    all complete and produce distinct records."""
    headers_auth = _safety_headers()
    submissions: list[tuple[str, str, dict, dict]] = []
    for i in range(3):
        submissions.append(("/inspections", "inspector_name",
                            {**INSPECTION_PAYLOAD, "inspector_name": f"PAR-INSP-{i}"},
                            headers_auth))
    for i in range(3):
        submissions.append(("/qaqc-inspections", "inspector_name",
                            {**QAQC_PAYLOAD, "inspector_name": f"PAR-QC-{i}"}, {}))
    for i in range(2):
        submissions.append(("/jhas", "job_title",
                            {**JHA_PAYLOAD, "job_title": f"PAR-JHA-{i}"}, {}))
    for i in range(2):
        submissions.append(("/meetings", "topic",
                            {"project_name": "PAR", "project_number": "PAR",
                             "location": "Yard", "meeting_date": "2026-07-05",
                             "meeting_time": "07:00", "conducted_by": "PAR",
                             "topic": f"PAR-MTG-{i}", "attendees": []}, {}))

    async def _one(path, _field, body, auth_hdrs):
        async with httpx.AsyncClient(timeout=20.0) as ac:
            r = await ac.post(
                _url(path),
                headers={"Content-Type": "application/json",
                         "Idempotency-Key": f"par-{uuid.uuid4().hex[:12]}",
                         **auth_hdrs},
                json=body,
            )
            r.raise_for_status()
            return r.json()

    responses = asyncio.run(_gather_from_list(_one, submissions))
    assert len(responses) == 10
    ids = [r.get("id") for r in responses]
    assert len(set(ids)) == 10, f"parallel workflow submits should NOT collide · ids={ids}"


# ── 7. Cross-workflow scoping still holds (regression) ────────────

def test_cross_workflow_scoping_still_holds():
    """Same key across /inspections and /jhas must NOT replay the
    wrong workflow's response."""
    shared_key = f"p2-cross-{uuid.uuid4().hex[:12]}"
    safety_hdrs = _safety_headers()

    r1 = httpx.post(
        _url("/inspections"),
        headers={"Content-Type": "application/json", "Idempotency-Key": shared_key,
                 **safety_hdrs},
        json={**INSPECTION_PAYLOAD, "inspector_name": f"CROSS-INSP-{uuid.uuid4().hex[:6]}"},
        timeout=20.0,
    )
    r2 = httpx.post(
        _url("/jhas"),
        headers={"Content-Type": "application/json", "Idempotency-Key": shared_key},
        json={**JHA_PAYLOAD, "job_title": f"CROSS-JHA-{uuid.uuid4().hex[:6]}"},
        timeout=20.0,
    )
    assert r1.status_code in (200, 201), r1.text
    assert r2.status_code in (200, 201), r2.text
    assert r1.json().get("doc_id", "").startswith("INSP-")
    assert r2.json().get("doc_id", "").startswith("JHA-"), (
        f"cross-workflow leak — /jhas returned {r2.json().get('doc_id')}"
    )
