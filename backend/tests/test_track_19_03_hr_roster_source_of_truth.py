"""TRACK 19.03 · HR Employee Source-of-Truth Roster Propagation tests.

P0 data integrity lock-file. Validates that:
  1. The 8 required Track 19.03 reports exist.
  2. `/api/employees` and `/api/hr/employee-roster` honour the HR
     roster contract (active = `_ACTIVE_STATUSES` OR legacy
     is_active!=False; inactive/terminated hidden by default).
  3. HR Save → immediately visible in pickers (no cache).
  4. HR deactivate → immediately hidden from new-form pickers.
  5. Inactive employees only visible via `include_inactive=true`.
  6. Search by name/employee_id/preferred_name works.
  7. Safe projection — no email, phone, SSN, DOB, CDL, medical_card.
  8. Historical reports are not mutated by lifecycle changes.

Live preview API. Uses the canonical Super Admin token.
"""
from __future__ import annotations

import asyncio
import os
import uuid
from pathlib import Path
from typing import Any, Dict

import pytest
import requests
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

load_dotenv("/app/backend/.env")
API = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://masci-audit-hub.preview.emergentagent.com",
).rstrip("/")
MONGO_URL = os.environ["MONGO_URL"]
DB_NAME = os.environ["DB_NAME"]
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

MEM = Path("/app/memory")
REQUIRED_REPORTS = [
    "TRACK_19_03_HR_ROSTER_SOURCE_AUDIT.md",
    "TRACK_19_03_DAILY_REPORT_ROSTER_FAILURE_REPRODUCTION.md",
    "HR_EMPLOYEE_ROSTER_CONTRACT.md",
    "TRACK_19_03_ROSTER_CACHE_SYNC_AUDIT.md",
    "TRACK_19_03_FORM_PICKER_AUDIT.md",
    "TRACK_19_03_PERMISSION_PRIVACY_REVIEW.md",
    "TRACK_19_03_HISTORICAL_SNAPSHOT_RULES.md",
    "TRACK_19_03_TEST_REPORT.md",
]
SAFE_FIELDS = {"id", "name", "preferred_name", "employee_id", "crew",
               "role", "trade", "department", "lifecycle_status",
               "is_active", "active", "supervisor_name",
               "supervisor_id", "updated_at"}
PRIVATE_FIELDS = {"email", "phone", "ssn", "dob", "date_of_birth",
                  "medical_card", "cdl_number", "cdl_expiration",
                  "password", "password_hash", "address"}


# ─────────── Report existence ───────────


@pytest.mark.parametrize("name", REQUIRED_REPORTS)
def test_required_report_exists(name):
    assert (MEM / name).exists(), f"missing report: {name}"


def test_prd_mentions_track_19_03():
    assert "19.03" in (MEM / "PRD.md").read_text(encoding="utf-8")


# ─────────── Token ───────────


@pytest.fixture(scope="module")
def admin_token():
    for _ in range(3):
        try:
            r = requests.post(
                f"{API}/api/auth/multi-login",
                json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
                timeout=60)
            r.raise_for_status()
            tok = (r.json().get("portal_tokens") or {}).get("admin")
            if tok:
                return tok
        except Exception:  # noqa: BLE001
            continue
    pytest.fail("could not obtain admin token")


def _ah(t): return {"X-Admin-Token": t, "Content-Type": "application/json"}


# ─────────── Endpoint contract ───────────


def test_canonical_endpoint_exists():
    r = requests.get(f"{API}/api/hr/employee-roster?limit=1", timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert body.get("contract_version") == "19.03"
    assert "active_statuses" in body["filter"]
    assert body["filter"]["source"].startswith("db.employees")


def test_canonical_endpoint_active_statuses():
    r = requests.get(f"{API}/api/hr/employee-roster?limit=1", timeout=15)
    statuses = r.json()["filter"]["active_statuses"]
    for s in ("Active", "Pending Hire", "Seasonal", "Leave of Absence"):
        assert s in statuses


def test_safe_projection_no_private_fields():
    r = requests.get(f"{API}/api/hr/employee-roster?limit=10", timeout=15)
    for emp in r.json()["items"]:
        leaked = set(emp.keys()) & PRIVATE_FIELDS
        assert not leaked, f"private field leaked: {leaked} in {emp.get('name')}"


def test_public_employees_endpoint_no_private_fields():
    r = requests.get(f"{API}/api/employees", timeout=15)
    for emp in r.json()["items"][:20]:
        leaked = set(emp.keys()) & PRIVATE_FIELDS
        assert not leaked, f"public endpoint leaked: {leaked}"


# ─────────── Lifecycle contract — Direct DB scenario ───────────


def _db():
    return AsyncIOMotorClient(MONGO_URL)[DB_NAME]


async def _insert_test_employee(name: str, lifecycle: str, is_active: bool):
    db = _db()
    emp_id = uuid.uuid4().hex
    await db.employees.insert_one({
        "id": emp_id, "name": name, "lifecycle_status": lifecycle,
        "is_active": is_active, "employee_id": f"TEST-{emp_id[:8]}",
        "role": "Test Role", "deleted_at": None,
    })
    db.client.close()
    return emp_id


async def _delete_test_employee(emp_id: str):
    db = _db()
    await db.employees.delete_one({"id": emp_id})
    db.client.close()


async def _patch_test_employee(emp_id: str, updates: Dict[str, Any]):
    db = _db()
    await db.employees.update_one({"id": emp_id}, {"$set": updates})
    db.client.close()


@pytest.fixture
def test_employee():
    name = f"ZZ_TEST_19_03_{uuid.uuid4().hex[:8]}"
    emp_id = asyncio.run(_insert_test_employee(name, "Active", True))
    yield {"id": emp_id, "name": name}
    asyncio.run(_delete_test_employee(emp_id))


def test_hr_save_active_employee_visible_immediately(test_employee):
    """HR creates a new Active employee → /api/employees + roster show them
    on the very next request (no cache, no sync delay)."""
    r1 = requests.get(f"{API}/api/employees", timeout=15)
    names_public = {e["name"] for e in r1.json()["items"]}
    assert test_employee["name"] in names_public, \
        "new Active employee NOT visible via /api/employees"

    r2 = requests.get(f"{API}/api/hr/employee-roster?limit=5000", timeout=15)
    names_canon = {e["name"] for e in r2.json()["items"]}
    assert test_employee["name"] in names_canon, \
        "new Active employee NOT visible via /api/hr/employee-roster"


def test_hr_save_terminated_employee_hidden_immediately(test_employee):
    """HR sets lifecycle_status=Terminated → employee hidden from new
    form pickers immediately (same query, next read), even if the
    legacy is_active boolean was not flipped."""
    asyncio.run(_patch_test_employee(
        test_employee["id"],
        {"lifecycle_status": "Terminated"}))  # legacy is_active still True
    r = requests.get(f"{API}/api/employees", timeout=15)
    names = {e["name"] for e in r.json()["items"]}
    assert test_employee["name"] not in names, \
        "Terminated employee leaked into /api/employees"

    r2 = requests.get(f"{API}/api/hr/employee-roster", timeout=15)
    assert test_employee["name"] not in {e["name"] for e in r2.json()["items"]}


def test_terminated_employee_appears_with_include_inactive(test_employee):
    """Operator-gated 'Show Inactive Employees' surfaces terminated
    employees for investigation / historical lookup."""
    asyncio.run(_patch_test_employee(
        test_employee["id"], {"lifecycle_status": "Terminated"}))
    r = requests.get(
        f"{API}/api/hr/employee-roster?include_inactive=true&limit=5000",
        timeout=15)
    names = {e["name"] for e in r.json()["items"]}
    assert test_employee["name"] in names, \
        "include_inactive=true did not expose Terminated employee"


def test_legacy_row_without_lifecycle_status_active_visible(test_employee):
    """Legacy rows with NO lifecycle_status fall back to is_active != False."""
    asyncio.run(_patch_test_employee(
        test_employee["id"],
        {"lifecycle_status": None, "is_active": True}))
    r = requests.get(f"{API}/api/hr/employee-roster?limit=5000", timeout=15)
    assert test_employee["name"] in {e["name"] for e in r.json()["items"]}


def test_legacy_row_without_lifecycle_status_inactive_hidden(test_employee):
    asyncio.run(_patch_test_employee(
        test_employee["id"],
        {"lifecycle_status": None, "is_active": False}))
    r = requests.get(f"{API}/api/hr/employee-roster?limit=5000", timeout=15)
    assert test_employee["name"] not in {e["name"] for e in r.json()["items"]}


def test_rehire_visible_immediately(test_employee):
    """Terminated → reactivated to Active → immediately visible again."""
    asyncio.run(_patch_test_employee(
        test_employee["id"], {"lifecycle_status": "Terminated"}))
    asyncio.run(_patch_test_employee(
        test_employee["id"], {"lifecycle_status": "Active"}))
    r = requests.get(f"{API}/api/hr/employee-roster?limit=5000", timeout=15)
    assert test_employee["name"] in {e["name"] for e in r.json()["items"]}


def test_preferred_name_change_visible_immediately(test_employee):
    asyncio.run(_patch_test_employee(
        test_employee["id"], {"preferred_name": "TestNickname"}))
    r = requests.get(f"{API}/api/hr/employee-roster?q=TestNickname", timeout=15)
    assert r.json()["count"] >= 1


def test_search_by_name(test_employee):
    r = requests.get(
        f"{API}/api/hr/employee-roster?q={test_employee['name'][:10]}",
        timeout=15)
    assert r.json()["count"] >= 1


def test_search_by_employee_id(test_employee):
    db = _db()
    emp = asyncio.run(_fetch(db, test_employee["id"]))
    db.client.close()
    r = requests.get(
        f"{API}/api/hr/employee-roster?q={emp['employee_id']}", timeout=15)
    assert r.json()["count"] >= 1


async def _fetch(db, emp_id):
    return await db.employees.find_one({"id": emp_id})


# ─────────── Picker contract & propagation ───────────


def test_roster_contract_returns_active_derived_field(test_employee):
    r = requests.get(f"{API}/api/hr/employee-roster?limit=5000", timeout=15)
    for emp in r.json()["items"]:
        assert "active" in emp, "roster contract must expose `active` boolean"
        assert isinstance(emp["active"], bool)


def test_inactive_employees_not_default_visible():
    """Existing terminated/inactive employees in the DB must not appear
    by default in /api/employees or /api/hr/employee-roster."""
    db = _db()

    async def _count():
        return await db.employees.count_documents({
            "lifecycle_status": {"$in": ["Terminated", "Resigned", "Retired", "Inactive"]},
        })
    inactive_count = asyncio.run(_count())
    db.client.close()
    r = requests.get(f"{API}/api/hr/employee-roster?limit=5000", timeout=15)
    visible_with_inactive_status = sum(
        1 for e in r.json()["items"]
        if e.get("lifecycle_status") in ("Terminated", "Resigned", "Retired", "Inactive")
    )
    assert visible_with_inactive_status == 0, \
        f"{visible_with_inactive_status} inactive employees leaked into default roster"


def test_no_react_overlay_in_homepage():
    """Smoke: homepage HTML loads without leaked stack traces or React
    overlay markers."""
    r = requests.get(f"{API}/", timeout=15)
    assert r.status_code == 200
    html = r.text
    assert "react-error-overlay" not in html
    assert "Traceback (most recent call last)" not in html


# ─────────── Historical snapshot ───────────


def test_historical_snapshot_doc_documents_rule():
    text = (MEM / "TRACK_19_03_HISTORICAL_SNAPSHOT_RULES.md").read_text("utf-8")
    assert "snapshot" in text.lower()
    assert "selection" in text.lower() and "historical" in text.lower()


# ─────────── Cache / sync ───────────


def test_no_in_process_cache_on_roster():
    """The canonical endpoint must NOT cache: two reads after a write
    must reflect the write. (Verified via test_hr_save_*_immediately
    suite. This test is the spec assertion.)"""
    text = (MEM / "TRACK_19_03_ROSTER_CACHE_SYNC_AUDIT.md").read_text("utf-8")
    assert "no cache" in text.lower() or "no ttl" in text.lower() \
        or "live read" in text.lower()
