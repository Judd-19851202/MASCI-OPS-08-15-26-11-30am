"""TRACK 22.4B-FOLLOWUP-HR regression locks.

Certifies:
  1. HR PVI token is accepted on HR-guarded endpoints (`X-HR-Token: PVI.*`).
  2. Cross-role PVI is rejected (Safety/Shop PVI cannot pass an HR gate).
  3. Same-key concurrent HR request submissions produce ONE request.
  4. Distinct-key HR submissions proceed independently.
  5. Portal-token submitter identity is inherited from the actor when
     the client omitted ``submitter_name`` — closes B-01 identity gap.
  6. Anonymous public submissions still produce truthful classification
     (no fabricated identity).
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


def _mint_pvi(role: str) -> str:
    r = httpx.post(
        f"{BACKEND_URL}/api/admin/preview-validation-identities/mint",
        headers={"X-Admin-Token": _admin_token()},
        json={"role": role, "purpose": f"HR track · {role}",
              "ttl_minutes": 30, "validation_track": "TRACK_22_4B_FOLLOWUP_HR"},
        timeout=15.0,
    )
    r.raise_for_status()
    return r.json()["token"]


@pytest.fixture(scope="module")
def hr_pvi() -> str:
    return _mint_pvi("hr")


@pytest.fixture(scope="module")
def safety_pvi() -> str:
    return _mint_pvi("safety")


async def _gather2(f1, f2):
    return await asyncio.gather(f1(), f2())


async def _gather_n(f, n):
    return await asyncio.gather(*[f(i) for i in range(n)])


# ── 1. HR PVI passes an HR-guarded endpoint ───────────────────────

def test_hr_pvi_passes_hr_endpoint(hr_pvi):
    r = httpx.get(_url("/hr/employee-requests"),
                  headers={"X-HR-Token": hr_pvi}, timeout=15.0)
    assert r.status_code == 200, r.text


# ── 2. Cross-role PVI rejected on HR endpoint ────────────────────

def test_safety_pvi_rejected_on_hr_endpoint(safety_pvi):
    r = httpx.get(_url("/hr/employee-requests"),
                  headers={"X-HR-Token": safety_pvi}, timeout=15.0)
    assert r.status_code in (401, 403), f"safety PVI must NOT pass HR gate · got {r.status_code}"


# ── 3. Anonymous rejected on HR endpoint ─────────────────────────

def test_anonymous_rejected_on_hr_endpoint():
    r = httpx.get(_url("/hr/employee-requests"), timeout=15.0)
    # This endpoint uses _require_hr_or_admin_for_queue which returns
    # 403 (not 401) for missing/invalid HR/Admin tokens — the platform
    # doctrine locked by tests/test_iter373_hr_user_parity.py.
    assert r.status_code in (401, 403)


def test_cross_role_pvi_rejected_on_hr_endpoint(safety_pvi):
    r = httpx.get(_url("/hr/employee-requests"),
                  headers={"X-HR-Token": safety_pvi}, timeout=15.0)
    # Safety PVI submitted as if it were an HR token → rejected.
    assert r.status_code in (401, 403), f"cross-role PVI must NOT pass HR gate · got {r.status_code}"


# ── 4. Same-key concurrent HR submit → ONE request ───────────────

def test_same_key_concurrent_hr_submit_one_request():
    key = f"hr-idemp-{uuid.uuid4().hex[:12]}"
    marker = f"HR-IDEMP-{uuid.uuid4().hex[:8]}"

    async def _one():
        async with httpx.AsyncClient(timeout=30.0) as ac:
            r = await ac.post(
                _url("/employee-requests"),
                headers={"Content-Type": "application/json", "Idempotency-Key": key},
                json={"kind": "new_hire", "name": marker,
                      "submitter_name": "HR IDEMP", "trade": "Operator"},
            )
            r.raise_for_status()
            return r.json()

    a, b = asyncio.run(_gather2(_one, _one))
    assert a["id"] == b["id"], f"HR idempotency broke · a={a['id']} b={b['id']}"

    async def _count() -> int:
        c = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db = c[os.environ["DB_NAME"]]
        return await db.employee_requests.count_documents({"payload.name": marker})

    assert asyncio.run(_count()) == 1


# ── 5. Distinct-key HR submits independent ───────────────────────

def test_distinct_key_hr_submits_independent():
    async def _one(i: int) -> str:
        async with httpx.AsyncClient(timeout=30.0) as ac:
            r = await ac.post(
                _url("/employee-requests"),
                headers={"Content-Type": "application/json",
                         "Idempotency-Key": f"hr-multi-{uuid.uuid4().hex[:12]}"},
                json={"kind": "new_hire", "name": f"HR MULTI {i} {uuid.uuid4().hex[:6]}",
                      "submitter_name": "HR MULTI", "trade": "Operator"},
            )
            r.raise_for_status()
            return r.json()["id"]

    ids = asyncio.run(_gather_n(_one, 5))
    assert len(set(ids)) == 5


# ── 6. B-01 · portal-token submitter identity inherited from actor ─

def test_submitter_identity_inherited_from_actor(hr_pvi):
    """A submission with an HR PVI token but NO submitter_name in the
    body must still record a non-null submitter_name derived from the
    actor. This closes the B-01 identity gap."""
    marker = f"HR-B01-{uuid.uuid4().hex[:8]}"
    r = httpx.post(
        _url("/employee-requests"),
        headers={"Content-Type": "application/json", "X-HR-Token": hr_pvi,
                 "Idempotency-Key": f"hr-b01-{uuid.uuid4().hex[:12]}"},
        json={"kind": "new_hire", "name": marker, "trade": "Operator"},
        timeout=20.0,
    )
    assert r.status_code == 200, r.text
    row = r.json()["request"]
    assert row["requested_by_role"] == "hr", row
    assert row["submitter_name"], (
        f"B-01 regression — portal submitter with no body submitter_name "
        f"must inherit actor identity · got submitter_name={row.get('submitter_name')!r}"
    )


# ── 7. Anonymous submissions preserve truthful classification ────

def test_anonymous_submission_is_truthfully_classified():
    """Anonymous public submits should NOT invent a fake submitter
    identity. requested_by_role must equal 'anonymous' / 'public'."""
    r = httpx.post(
        _url("/employee-requests"),
        headers={"Content-Type": "application/json",
                 "Idempotency-Key": f"hr-anon-{uuid.uuid4().hex[:12]}"},
        json={"kind": "new_hire", "name": f"HR-ANON-{uuid.uuid4().hex[:8]}",
              "trade": "Operator"},
        timeout=20.0,
    )
    assert r.status_code == 200, r.text
    row = r.json()["request"]
    assert row["requested_by_role"] in ("anonymous", "public"), row
    # submitter_name may be null for anonymous — never invent
    # (this is the "no fabrication" doctrine).
