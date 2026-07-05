"""TRACK 22.4b-followup-Safety · B-02 Safety Meeting nulls regression.

Invariants proven end-to-end via a real HTTP POST /api/meetings using a
Safety PVI token:

1. A meeting submitted with an EMPTY topic is rejected with 422.
2. A meeting submitted with an EMPTY project_name is rejected with 422.
3. A meeting submitted with an attendee whose company is empty is
   rejected with 422 (Pydantic MeetingAttendee validator).
4. A meeting submitted with a MASCI employee attendee typed by NAME
   (no employee_id, no company) has ``company="MASCI"`` auto-locked
   on the server by ``normalize_meeting_attendees``.
5. Legacy corpus invariants are held: query the DB and confirm no
   ``is_masci_employee=True`` attendee has an empty company.

This is the durable, machine-checkable proof that B-02 is closed.
"""
from __future__ import annotations

import os
import asyncio

import httpx
import pytest
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8001")
ADMIN_EMAIL = os.environ.get("TEST_SUPER_ADMIN_EMAIL", "jaymn.judd@mascigc.com")
ADMIN_PASS = os.environ.get("TEST_SUPER_ADMIN_PASSWORD", "Maddix123!")


def _admin_token() -> str:
    r = httpx.post(
        f"{BACKEND_URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASS},
        timeout=15.0,
    )
    r.raise_for_status()
    return (r.json().get("portal_tokens") or {}).get("admin") or ""


def _safety_pvi(admin_token: str) -> str:
    r = httpx.post(
        f"{BACKEND_URL}/api/admin/preview-validation-identities/mint",
        headers={"X-Admin-Token": admin_token},
        json={
            "role": "safety",
            "purpose": "B-02 regression",
            "ttl_minutes": 30,
            "validation_track": "TRACK_22_4B_FOLLOWUP_SAFETY_B02",
        },
        timeout=15.0,
    )
    r.raise_for_status()
    return r.json()["token"]


@pytest.fixture(scope="module")
def safety_pvi() -> str:
    return _safety_pvi(_admin_token())


BASE_PAYLOAD = {
    "project_name": "TRACK 22.4b-followup-Safety Verify",
    "project_number": "22-4B",
    "location": "Preview Yard",
    "meeting_date": "2026-07-05",
    "meeting_time": "07:00",
    "conducted_by": "Validation Safety",
    "topic": "PVI Verification Meeting",
    "attendees": [],
    "conductor_signature": "data:image/png;base64,iVBORw0KGgo=",
}


def _post(body: dict, safety_pvi: str) -> httpx.Response:
    return httpx.post(
        f"{BACKEND_URL}/api/meetings",
        headers={"X-Safety-Token": safety_pvi, "Content-Type": "application/json"},
        json=body,
        timeout=15.0,
    )


def test_empty_topic_rejected(safety_pvi):
    body = {**BASE_PAYLOAD, "topic": ""}
    r = _post(body, safety_pvi)
    assert r.status_code == 422, f"empty topic must be rejected: HTTP {r.status_code} · {r.text[:200]}"


def test_empty_project_name_rejected(safety_pvi):
    body = {**BASE_PAYLOAD, "project_name": ""}
    r = _post(body, safety_pvi)
    assert r.status_code == 422, f"empty project_name must be rejected: HTTP {r.status_code} · {r.text[:200]}"


def test_attendee_with_empty_company_rejected(safety_pvi):
    body = {
        **BASE_PAYLOAD,
        "attendees": [
            {
                "name": "John Doe",
                "company": "",  # blank company on a manual attendee
                "signature": "data:image/png;base64,iVBORw0KGgo=",
                "acknowledged": True,
            }
        ],
    }
    r = _post(body, safety_pvi)
    assert r.status_code == 422, f"empty company must be rejected: HTTP {r.status_code} · {r.text[:200]}"


def test_masci_employee_name_only_gets_company_autolocked(safety_pvi):
    """Attendee typed by name only (no employee_id, no non_masci flag,
    company set to a placeholder) should be resolved by the backend to
    a MASCI employee and stored with company='MASCI'."""
    # Look up a real active employee name from the DB.
    async def _first_active_name() -> str:
        c = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db = c[os.environ["DB_NAME"]]
        emp = await db.employees.find_one({"is_active": {"$ne": False}, "name": {"$exists": True, "$ne": ""}}, {"name": 1})
        return (emp or {}).get("name") or ""
    name = asyncio.run(_first_active_name())
    assert name, "no active employee in DB — cannot exercise name-based promotion"
    body = {
        **BASE_PAYLOAD,
        "attendees": [
            {
                "name": name,
                "company": "unknown",  # frontend guessed — backend must overwrite
                "signature": "data:image/png;base64,iVBORw0KGgo=",
                "acknowledged": True,
            }
        ],
    }
    r = _post(body, safety_pvi)
    assert r.status_code in (200, 201), f"submit failed: HTTP {r.status_code} · {r.text[:200]}"
    body_out = r.json()
    att = body_out["attendees"][0]
    assert att["is_masci_employee"] is True, "backend must recognize this MASCI employee by name"
    assert att["company"] == "MASCI", "company must be auto-locked to MASCI"
    assert att["attendee_type"] == "employee"


def test_legacy_corpus_has_zero_masci_null_companies():
    """Direct DB invariant — the B-02 backfill script must have left
    zero MASCI-tagged attendees with an empty company."""
    async def _check() -> int:
        c = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db = c[os.environ["DB_NAME"]]
        return await db.meetings.count_documents(
            {"attendees": {"$elemMatch": {
                "is_masci_employee": True,
                "$or": [{"company": ""}, {"company": None}],
            }}}
        )
    n = asyncio.run(_check())
    assert n == 0, f"B-02 invariant broken — {n} meetings still have MASCI attendees with empty company"


def test_legacy_corpus_has_zero_null_topics():
    async def _check() -> int:
        c = AsyncIOMotorClient(os.environ["MONGO_URL"])
        db = c[os.environ["DB_NAME"]]
        return await db.meetings.count_documents({"$or": [{"topic": ""}, {"topic": None}]})
    n = asyncio.run(_check())
    assert n == 0, f"B-02 invariant broken — {n} meetings still have null/empty topic"
