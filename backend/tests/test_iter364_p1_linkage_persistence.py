"""
iter364 · P1 controlled migration — submit-and-persist lifecycle verification
for the 3 newly-migrated surfaces (QA/QC inspector, CAPA assignee, Shop sign-off).

Pattern mirrors iter363's harness: POST a linked payload, GET it back,
assert the new linkage field persists. Free-text fallback path also
exercised on each surface.

Migrated surfaces in iter364:
  - QA/QC inspector field   → `inspector_id` field on /api/qaqc-inspections
  - CAPA assignee form      → `employee_master_id` on /api/safety/corrective-actions
  - Shop Pre-Op sign-off    → `signed_by_employee_id` on /api/admin/equipment-inspections/{id}/signoff
  - FL Records picker       → no new field (FL form already captured
                              employee_id; iter364 added visible status
                              indicator only — covered by frontend test agent)
  - Dispatch assignment     → no UI form exists for it today; NOT migrated
                              (per simplicity rule: don't add surfaces just to
                              host the component)
"""
from __future__ import annotations

import datetime as dt
import uuid
from pathlib import Path

import pytest
import requests


def _read_env(path: str, key: str) -> str:
    try:
        for line in Path(path).read_text().splitlines():
            if line.startswith(f"{key}="):
                return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:  # noqa: BLE001
        return ""
    return ""


BASE_URL = _read_env("/app/frontend/.env", "REACT_APP_BACKEND_URL").rstrip("/")
ADMIN_PW = _read_env("/app/backend/.env", "ADMIN_PASSWORD") or "MASCI1982!"
SAFETY_PORTAL_EMAIL = "safety@mascigc.com"

TODAY = dt.date.today().isoformat()
NOW_TIME = "10:00"

PIXEL_PNG = (
    "data:image/png;base64,"
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="
)

NO_AUTH = {"X-Admin-Token": "", "Content-Type": "application/json"}


# ───────────────────────────── fixtures ─────────────────────────────


@pytest.fixture(scope="module")
def session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def admin_token(session: requests.Session) -> str:
    r = session.post(f"{BASE_URL}/api/admin/login",
                     json={"password": ADMIN_PW}, headers=NO_AUTH)
    if r.status_code != 200:
        pytest.skip(f"admin login failed: {r.status_code}")
    return r.json().get("token", "")


@pytest.fixture(scope="module")
def safety_token(session: requests.Session) -> str:
    """Acquire a Safety portal token via the super-admin multi-login flow
    (mirrors the pattern used by other iter test fixtures)."""
    r = session.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
        headers=NO_AUTH,
    )
    if r.status_code != 200:
        pytest.skip(f"multi-login failed: {r.status_code}")
    tok = (r.json().get("portal_tokens") or {}).get("safety", "")
    if not tok:
        pytest.skip("multi-login did not return a safety portal token")
    return tok


@pytest.fixture(scope="module")
def roster_employee(session: requests.Session, admin_token: str) -> dict:
    r = session.get(
        f"{BASE_URL}/api/master-lookup/employees",
        params={"q": "a", "limit": 5},
        headers={"X-Admin-Token": admin_token, "Content-Type": "application/json"},
        timeout=15,
    )
    assert r.status_code == 200, r.text
    items = r.json().get("items", [])
    if not items:
        pytest.skip("No roster employees in preview DB.")
    return items[0]


# ───────────────────── 1 · QA/QC inspector ────────────────────────────


class TestQaqcInspectorLinkage:
    def _payload(self, **overrides) -> dict:
        body = {
            "inspection_kind": "concrete_form",
            "project_name": f"iter364-QAQC-{uuid.uuid4().hex[:6]}",
            "project_number": "",
            "location": "Yard",
            "inspection_date": TODAY,
            "inspection_time": NOW_TIME,
            "inspector_name": "iter364 Test Inspector",
            "work_area": "iter364 Station 1",
            "mix_design": "3500psi",
            "yards_ordered": "10",
            "concrete_vendor": "iter364 Vendor",
            "checklist": [],
            "inspection_notes": "iter364 lifecycle verification",
        }
        body.update(overrides)
        return body

    def test_linked_inspector_persists(self, session, roster_employee):
        emp = roster_employee
        body = self._payload(
            inspector_name=emp["name"],
            inspector_id=emp["id"],
        )
        r = session.post(f"{BASE_URL}/api/qaqc-inspections",
                         json=body, headers=NO_AUTH)
        assert r.status_code == 200, r.text
        doc = r.json()
        assert doc["inspector_name"] == emp["name"]
        # extra="allow" persists inspector_id verbatim.
        assert doc.get("inspector_id") == emp["id"], doc

    def test_freetext_inspector_persists_without_id(self, session):
        body = self._payload(inspector_name="iter364 Subby Inspector")
        r = session.post(f"{BASE_URL}/api/qaqc-inspections",
                         json=body, headers=NO_AUTH)
        assert r.status_code == 200, r.text
        doc = r.json()
        assert doc["inspector_name"] == "iter364 Subby Inspector"
        assert not doc.get("inspector_id")


# ─────────────────────── 2 · CAPA assignee ────────────────────────────


class TestCapaAssigneeLinkage:
    def _payload(self, **overrides) -> dict:
        body = {
            "title": f"iter364 CAPA {uuid.uuid4().hex[:6]}",
            "description": "iter364 lifecycle verification",
            "source_kind": "manual",
            "source_id": "",
            "project_number": "",
            "assigned_to_name": "iter364 Free Text Assignee",
            "assigned_to_email": "",
            "priority": "Medium",
            "due_date": "",
            "notes": "",
        }
        body.update(overrides)
        return body

    def test_linked_assignee_persists(self, session, safety_token, roster_employee):
        emp = roster_employee
        body = self._payload(
            assigned_to_name=emp["name"],
            employee_master_id=emp["id"],
        )
        r = session.post(
            f"{BASE_URL}/api/safety/corrective-actions",
            json=body,
            headers={"X-Safety-Token": safety_token, "Content-Type": "application/json"},
        )
        assert r.status_code == 200, r.text
        ca = r.json()
        assert ca["assigned_to_name"] == emp["name"]
        assert ca.get("employee_master_id") == emp["id"]

    def test_freetext_assignee_persists_without_id(self, session, safety_token):
        body = self._payload(assigned_to_name="iter364 Sub Vendor Owner")
        r = session.post(
            f"{BASE_URL}/api/safety/corrective-actions",
            json=body,
            headers={"X-Safety-Token": safety_token, "Content-Type": "application/json"},
        )
        assert r.status_code == 200, r.text
        ca = r.json()
        assert ca["assigned_to_name"] == "iter364 Sub Vendor Owner"
        assert not ca.get("employee_master_id")


# ──────────────── 3 · Shop Pre-Op sign-off identity ───────────────────


class TestShopSignoffLinkage:
    """Shop sign-off lives on a Pre-Op inspection. We first create a
    minimal Pre-Op inspection (public endpoint), then sign off on a
    synthesized FAIL key, and confirm the new signed_by_employee_id
    field persists in the inspection's shop_signoffs[] array."""

    def _create_preop(self, session) -> str:
        body = {
            "project_name": f"iter364-PREOP-{uuid.uuid4().hex[:6]}",
            "project_number": "",
            "location": "Yard",
            "inspection_date": TODAY,
            "inspection_time": NOW_TIME,
            "operator_name": "iter364 Pre-Op Operator",
            "equipment_type": "Skid Steer",
            "equipment_unit": "U-iter364",
            "checklist": {},
            "fail_count": 1,
            "pass_count": 0,
            "na_count": 0,
            "deficiency_notes": "iter364 verification",
        }
        r = session.post(f"{BASE_URL}/api/equipment-inspections",
                         json=body, headers=NO_AUTH)
        assert r.status_code == 200, r.text
        return r.json()["id"]

    def test_linked_mechanic_signoff_persists(self, session, admin_token, roster_employee):
        emp = roster_employee
        inspection_id = self._create_preop(session)
        signoff_body = {
            "section": "iter364-section",
            "item": "iter364-item",
            "signed_by": emp["name"],
            "signed_by_employee_id": emp["id"],
            "action_taken": "Repaired",
            "notes": "iter364 lifecycle test",
        }
        r = session.post(
            f"{BASE_URL}/api/admin/equipment-inspections/{inspection_id}/signoff",
            json=signoff_body,
            headers={"X-Admin-Token": admin_token, "Content-Type": "application/json"},
        )
        assert r.status_code == 200, r.text
        body = r.json()
        signoff = body.get("signoff") or {}
        assert signoff.get("signed_by") == emp["name"]
        assert signoff.get("signed_by_employee_id") == emp["id"]
        # Round-trip via GET to confirm persistence in MongoDB array.
        r2 = session.get(
            f"{BASE_URL}/api/equipment-inspections/{inspection_id}",
            headers={"X-Admin-Token": admin_token, "Content-Type": "application/json"},
        )
        assert r2.status_code == 200
        insp = r2.json()
        sos = insp.get("shop_signoffs") or []
        assert sos, "shop_signoffs[] is empty after a sign-off"
        match = next((s for s in sos if s.get("key") == "iter364-section|iter364-item"), None)
        assert match is not None
        assert match.get("signed_by_employee_id") == emp["id"]

    def test_freetext_mechanic_signoff_persists_without_id(self, session, admin_token):
        inspection_id = self._create_preop(session)
        signoff_body = {
            "section": "iter364-section-ft",
            "item": "iter364-item-ft",
            "signed_by": "iter364 Free Text Mechanic",
            "action_taken": "Repaired",
            "notes": "free-text mechanic lifecycle test",
        }
        r = session.post(
            f"{BASE_URL}/api/admin/equipment-inspections/{inspection_id}/signoff",
            json=signoff_body,
            headers={"X-Admin-Token": admin_token, "Content-Type": "application/json"},
        )
        assert r.status_code == 200, r.text
        signoff = (r.json() or {}).get("signoff") or {}
        assert signoff.get("signed_by") == "iter364 Free Text Mechanic"
        # Default value is empty string, never fabricated.
        assert not signoff.get("signed_by_employee_id")
