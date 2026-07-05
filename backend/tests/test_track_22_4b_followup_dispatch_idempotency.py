"""TRACK 22.4B-FOLLOWUP-DISPATCH-IDEMPOTENCY regression locks.

Certifies exactly-once submit on the dispatch assignment write path,
including the Roll-Off variant (canonical `haul_type="Roll-Off"`).

Uses super-admin token for the write gate (dispatch|admin allowed).
Does NOT touch Motive routes or read paths.

Invariants:
  1. Same-key concurrent dispatch assignment → exactly one row.
  2. Same-key concurrent Roll-Off assignment → exactly one row with
     canonical `haul_type="Roll-Off"` (no roll_off_assignments coll).
  3. Distinct-key parallel dispatch submissions proceed independently.
  4. Cross-workflow scoping — a dispatch key cannot replay onto a
     Daily Report submission (or vice-versa).
  5. RBAC unchanged — anonymous still 401.
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


def _admin_token() -> str:
    r = httpx.post(
        f"{BACKEND_URL}/api/auth/multi-login",
        json={"email": os.environ.get("TEST_SUPER_ADMIN_EMAIL", "jaymn.judd@mascigc.com"),
              "password": os.environ.get("TEST_SUPER_ADMIN_PASSWORD", "Maddix123!")},
        timeout=15.0,
    )
    r.raise_for_status()
    return (r.json().get("portal_tokens") or {}).get("admin") or ""


_CACHED_ADMIN: str = ""


def _admin_headers() -> dict:
    global _CACHED_ADMIN
    if not _CACHED_ADMIN:
        _CACHED_ADMIN = _admin_token()
    return {"X-Admin-Token": _CACHED_ADMIN}


async def _gather2(f1, f2):
    return await asyncio.gather(f1(), f2())


async def _gather_n(f, n):
    return await asyncio.gather(*[f(i) for i in range(n)])


def _base_body(**overrides) -> dict:
    body = {
        "truck_id": "TRUCK-IDEMP-TEST",
        "driver_name": "DispIdempotency Driver",
        "project_number": "IDEMP-DISP",
        "project_name": "IDEMPOTENCY DISPATCH",
        "material": "Base rock",
        "source_location": "Pit A",
        "destination": "Yard",
    }
    body.update(overrides)
    return body


async def _count_assignments(marker: str) -> int:
    c = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = c[os.environ["DB_NAME"]]
    return await db.dispatch_assignments.count_documents({"project_name": marker})


async def _count_rolloff_in_canonical(marker: str) -> tuple[int, int]:
    """Returns (canonical dispatch_assignments count · roll_off_assignments count)."""
    c = AsyncIOMotorClient(os.environ["MONGO_URL"])
    db = c[os.environ["DB_NAME"]]
    canonical = await db.dispatch_assignments.count_documents(
        {"project_name": marker, "haul_type": "Roll-Off"},
    )
    # legacy collection MUST NOT be used
    legacy = 0
    try:
        legacy = await db.roll_off_assignments.count_documents({"project_name": marker})
    except Exception:
        legacy = 0
    return canonical, legacy


# ── 1. Same-key concurrent dispatch → one assignment ─────────────

def test_same_key_concurrent_dispatch_creates_one_assignment():
    key = f"disp-idemp-{uuid.uuid4().hex[:12]}"
    marker = f"DISP-IDEMP-{uuid.uuid4().hex[:8]}"
    headers = {"Content-Type": "application/json", "Idempotency-Key": key, **_admin_headers()}

    async def _one():
        async with httpx.AsyncClient(timeout=60.0) as ac:
            r = await ac.post(_url("/dispatch/assignments"),
                              headers=headers,
                              json=_base_body(project_name=marker))
            r.raise_for_status()
            return r.json()

    a, b = asyncio.run(_gather2(_one, _one))
    aid = (a.get("assignment") or {}).get("id") or ""
    bid = (b.get("assignment") or {}).get("id") or ""
    assert aid and aid == bid, f"idempotency broke on /dispatch/assignments · a={aid} b={bid}"
    assert asyncio.run(_count_assignments(marker)) == 1


# ── 2. Same-key concurrent Roll-Off → one canonical Roll-Off ─────

def test_same_key_concurrent_rolloff_creates_one_canonical_assignment():
    key = f"disp-rolloff-{uuid.uuid4().hex[:12]}"
    marker = f"DISP-ROLLOFF-{uuid.uuid4().hex[:8]}"
    headers = {"Content-Type": "application/json", "Idempotency-Key": key, **_admin_headers()}

    async def _one():
        async with httpx.AsyncClient(timeout=60.0) as ac:
            r = await ac.post(_url("/dispatch/assignments"),
                              headers=headers,
                              json=_base_body(project_name=marker, haul_type="Roll-Off"))
            r.raise_for_status()
            return r.json()

    a, b = asyncio.run(_gather2(_one, _one))
    aid = (a.get("assignment") or {}).get("id") or ""
    bid = (b.get("assignment") or {}).get("id") or ""
    assert aid == bid, f"Roll-Off idempotency broke · a={aid} b={bid}"
    canonical, legacy = asyncio.run(_count_rolloff_in_canonical(marker))
    assert canonical == 1, f"Roll-Off must appear once in canonical dispatch_assignments (got {canonical})"
    assert legacy == 0, (
        "Roll-Off must NEVER be written to roll_off_assignments — canonical model "
        f"is dispatch_assignments.haul_type='Roll-Off'. Found {legacy} legacy rows."
    )
    # Haul type field explicitly preserved.
    haul = (a.get("assignment") or {}).get("haul_type")
    assert haul == "Roll-Off", f"canonical haul_type must be 'Roll-Off', got {haul!r}"


# ── 3. Distinct-key parallel submissions independent ─────────────

def test_distinct_key_parallel_dispatch_independent():
    headers = _admin_headers()

    async def _one(i: int) -> str:
        async with httpx.AsyncClient(timeout=30.0) as ac:
            r = await ac.post(
                _url("/dispatch/assignments"),
                headers={"Content-Type": "application/json",
                         "Idempotency-Key": f"disp-parallel-{uuid.uuid4().hex[:12]}",
                         **headers},
                json=_base_body(project_name=f"DISP-PAR-{i}"),
            )
            r.raise_for_status()
            return (r.json().get("assignment") or {}).get("id") or ""

    ids = asyncio.run(_gather_n(_one, 5))
    assert len(ids) == 5 and all(ids), ids
    assert len(set(ids)) == 5, f"parallel distinct-key dispatch submits should NOT collide · ids={ids}"


# ── 4. Cross-workflow scoping — dispatch key cannot replay onto DR ──

def test_dispatch_key_does_not_replay_onto_daily_reports():
    shared_key = f"disp-cross-{uuid.uuid4().hex[:12]}"
    marker = f"DISP-CROSS-{uuid.uuid4().hex[:6]}"
    headers = _admin_headers()

    r1 = httpx.post(
        _url("/dispatch/assignments"),
        headers={"Content-Type": "application/json", "Idempotency-Key": shared_key, **headers},
        json=_base_body(project_name=marker),
        timeout=30.0,
    )
    assert r1.status_code in (200, 201), r1.text
    assn = (r1.json().get("assignment") or {})
    assert assn.get("id"), r1.text

    r2 = httpx.post(
        _url("/daily-reports"),
        headers={"Content-Type": "application/json", "Idempotency-Key": shared_key},
        json={"project_name": marker, "project_number": "IDEMP-DISP",
              "location": "y", "report_date": "2026-07-05", "prepared_by": "cross"},
        timeout=30.0,
    )
    assert r2.status_code in (200, 201), r2.text
    dr_doc = r2.json()
    assert dr_doc.get("doc_id", "").startswith("DR-"), (
        f"cross-workflow leak — /daily-reports returned {dr_doc.get('doc_id')!r} "
        f"instead of a fresh DR"
    )


# ── 5. RBAC unchanged — anonymous still 401 ──────────────────────

def test_anonymous_dispatch_submit_still_401():
    r = httpx.post(_url("/dispatch/assignments"),
                   headers={"Content-Type": "application/json",
                            "Idempotency-Key": f"anon-{uuid.uuid4().hex[:8]}"},
                   json=_base_body(project_name="ANON-SHOULD-401"),
                   timeout=20.0)
    assert r.status_code == 401, f"anonymous dispatch submit must 401 · got {r.status_code}"


# ── 6. Motive posture shape stable (regression proof) ───────────

def test_motive_posture_shape_stable():
    """Track 22.4a shipped a Motive posture endpoint whose shape is
    part of the operator trust contract. Regressing to prove the
    dispatch idempotency wrap did NOT alter it."""
    r = httpx.get(_url("/motive/posture"),
                  headers=_admin_headers(),
                  timeout=15.0)
    if r.status_code == 404:
        pytest.skip("Motive posture endpoint not exposed in this preview")
    assert r.status_code == 200, r.text
    body = r.json()
    # Locked keys from Track 22.4a operator-trust repair.
    for k in ("last_success_ts", "last_success_age_seconds", "state"):
        assert k in body, f"Motive posture shape must contain {k!r} · body={body}"
