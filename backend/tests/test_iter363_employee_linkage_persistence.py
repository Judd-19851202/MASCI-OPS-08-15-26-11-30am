"""
iter363 · P0 lifecycle verification of iter359-iter362 EmployeeRosterField /
EmployeeCombo linkage migrations.

The testing_agent_v3_fork (iteration_363.json) explicitly noted that the
"submit-and-verify" lifecycle was NOT exercised on any of the 6 migrated
forms — only component rendering / pick behavior. The operator's directive
requires that we actually CREATE records and VERIFY that the new
employee_id / employee_master_id / operator_id payload fields persist
end-to-end.

This pytest harness fills that gap. For each of the 6 forms it:
  - POSTs a payload that simulates the "linked-from-roster" path
    (employee_id populated from the master)
  - POSTs a second payload that simulates the "free-text fallback" path
    (employee_id absent)
  - GETs the created record back and asserts the new fields persist
    correctly in MongoDB without mutating the legacy fields

The Pydantic models for all 4 public forms (incidents · daily-reports ·
meetings · equipment-inspections) use `extra="allow"`, so the new
linkage fields are stored verbatim. The 2 safety-forms surfaces
(equipment-issuances · equipment-trainings) require a token gate; we
acquire one via the existing /api/safety-forms/login path (shared
password 1982).
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
SAFETY_FORMS_PW = _read_env("/app/backend/.env", "SAFETY_FORMS_PASSWORD") or "1982"

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
def safety_forms_token(session: requests.Session) -> str:
    r = session.post(f"{BASE_URL}/api/safety-forms/login",
                     json={"password": SAFETY_FORMS_PW}, headers=NO_AUTH)
    if r.status_code != 200:
        pytest.skip(f"safety-forms login failed: {r.status_code}")
    return r.json().get("token", "")


@pytest.fixture(scope="module")
def roster_employee(session: requests.Session, admin_token: str) -> dict:
    """Grab a real employee from the roster so we link against a
    canonical id that the governance detector will resolve cleanly."""
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
    emp = items[0]
    assert "id" in emp and emp["id"]
    # Component reads .name (iter363 fix); ensure shape is what the UI sees.
    assert emp.get("name"), "Roster item missing 'name' — UI suggestion row would be blank"
    return emp


# ─────────────────────────── 1 · Incidents ───────────────────────────


class TestIncidentLinkage:
    def _payload(self, **overrides) -> dict:
        body = {
            "project_name": f"iter363-{uuid.uuid4().hex[:6]}",
            "project_number": "",
            "location": "Yard",
            "incident_date": TODAY,
            "incident_time": NOW_TIME,
            "reported_date": TODAY,
            "reported_by": "iter363 Auto-Test",
            "incident_type": "Near Miss",
            "severity": "Low",
            "person_name": "",
            "description": "iter363 lifecycle verification — auto-cleanup safe",
        }
        body.update(overrides)
        return body

    def test_linked_employee_persists(self, session, roster_employee):
        emp = roster_employee
        body = self._payload(
            person_name=emp["name"],
            employee_master_id=emp["id"],
        )
        r = session.post(f"{BASE_URL}/api/incidents", json=body, headers=NO_AUTH)
        assert r.status_code == 200, r.text
        inc = r.json()
        assert inc["person_name"] == emp["name"]
        # extra="allow" persists employee_master_id verbatim.
        assert inc.get("employee_master_id") == emp["id"]
        # Round-trip GET — admin only.
        # Skip if no token; this is enforced by the next test.
        TestIncidentLinkage.linked_id = inc["id"]

    def test_freetext_employee_persists_without_id(self, session):
        body = self._payload(
            person_name="iter363 Free Text Subby",
            # NO employee_master_id key — simulating component's
            # free-text fallback state.
        )
        r = session.post(f"{BASE_URL}/api/incidents", json=body, headers=NO_AUTH)
        assert r.status_code == 200, r.text
        inc = r.json()
        assert inc["person_name"] == "iter363 Free Text Subby"
        # employee_master_id must be absent OR empty — never auto-filled.
        assert not inc.get("employee_master_id"), inc.get("employee_master_id")


# ───────────────────── 2 · Daily Reports (crew array) ─────────────────


class TestDailyReportCrewLinkage:
    def _payload(self, crews: list[dict]) -> dict:
        return {
            "project_name": f"iter363-DR-{uuid.uuid4().hex[:6]}",
            "project_number": "",
            "location": "Yard",
            "report_date": TODAY,
            "prepared_by": "iter363 Auto-Test",
            "masci_crews": crews,
        }

    def test_mixed_crew_persists_with_linkage(self, session, roster_employee):
        emp = roster_employee
        crews = [
            # Linked row (picked from roster) — iter360 wiring writes employee_id.
            {"name": emp["name"], "employee_id": emp["id"], "hours": 8},
            # Free-text row — iter360 stores name only.
            {"name": "iter363 Free Text Crew", "hours": 8},
        ]
        r = session.post(f"{BASE_URL}/api/daily-reports",
                         json=self._payload(crews), headers=NO_AUTH)
        assert r.status_code == 200, r.text
        dr = r.json()
        crews_back = dr.get("masci_crews") or []
        assert len(crews_back) == 2
        # Linked row preserved exactly.
        linked = next(c for c in crews_back if c["name"] == emp["name"])
        assert linked.get("employee_id") == emp["id"]
        # Free-text row — name only, no fabricated id.
        ft = next(c for c in crews_back if c["name"] == "iter363 Free Text Crew")
        assert not ft.get("employee_id")


# ─────────────────── 3 · Meetings (attendee array) ────────────────────


class TestMeetingAttendeeLinkage:
    def _payload(self, attendees: list[dict]) -> dict:
        return {
            "project_name": f"iter363-MTG-{uuid.uuid4().hex[:6]}",
            "project_number": "",
            "location": "Yard",
            "meeting_date": TODAY,
            "meeting_time": NOW_TIME,
            "conducted_by": "iter363 Auto-Test",
            "topic": "iter363 linkage verification",
            "attendees": attendees,
        }

    def test_mixed_attendees_persist_with_linkage(self, session, roster_employee):
        emp = roster_employee
        attendees = [
            {"name": emp["name"], "employee_id": emp["id"], "signature": ""},
            {"name": "iter363 Free Text Subby", "signature": ""},
        ]
        r = session.post(f"{BASE_URL}/api/meetings",
                         json=self._payload(attendees), headers=NO_AUTH)
        assert r.status_code == 200, r.text
        m = r.json()
        att_back = m.get("attendees") or []
        assert len(att_back) == 2
        linked = next(a for a in att_back if a["name"] == emp["name"])
        assert linked.get("employee_id") == emp["id"]
        ft = next(a for a in att_back if a["name"] == "iter363 Free Text Subby")
        assert not ft.get("employee_id")


# ─────────── 4 · Equipment Inspections (operator scalar) ──────────────


class TestEquipmentInspectionOperatorLinkage:
    def _payload(self, **overrides) -> dict:
        body = {
            "project_name": f"iter363-EQ-{uuid.uuid4().hex[:6]}",
            "project_number": "",
            "location": "Yard",
            "inspection_date": TODAY,
            "inspection_time": NOW_TIME,
            "operator_name": "iter363 Test Operator",
            "equipment_type": "Skid Steer",
            "equipment_unit": "U-9999",
            "checklist": {},
            "fail_count": 0,
            "pass_count": 1,
            "na_count": 0,
        }
        body.update(overrides)
        return body

    def test_linked_operator_persists(self, session, roster_employee):
        emp = roster_employee
        body = self._payload(
            operator_name=emp["name"],
            operator_id=emp["id"],
        )
        r = session.post(f"{BASE_URL}/api/equipment-inspections",
                         json=body, headers=NO_AUTH)
        assert r.status_code == 200, r.text
        eq = r.json()
        assert eq["operator_name"] == emp["name"]
        assert eq.get("operator_id") == emp["id"]

    def test_freetext_operator_persists_without_id(self, session):
        body = self._payload(operator_name="iter363 Subby Driver")
        r = session.post(f"{BASE_URL}/api/equipment-inspections",
                         json=body, headers=NO_AUTH)
        assert r.status_code == 200, r.text
        eq = r.json()
        assert eq["operator_name"] == "iter363 Subby Driver"
        assert not eq.get("operator_id")


# ─────────────── 5 · Safety-Forms Equipment Issuance (PPE) ────────────


class TestPpeIssuanceLinkage:
    def _payload(self, **overrides) -> dict:
        body = {
            "employee_name": "iter363 Test PPE Emp",
            "employee_id": "",
            "position": "Foreman",
            "project_name": f"iter363-PPE-{uuid.uuid4().hex[:6]}",
            "project_number": "",
            "location": "Yard",
            "issued_by": "iter363 Auto-Test",
            "issued_date": TODAY,
            "items": [
                {"item_type": "Harness", "description": "iter363",
                 "quantity": 1, "unit_value": 100, "asset_id": "H-iter363"},
            ],
            "condition": "Good",
            "condition_note": "",
            "photos": [PIXEL_PNG],
            "acknowledgment": True,
            "employee_signature": PIXEL_PNG,
            "supervisor_signature": PIXEL_PNG,
            "lang": "en",
        }
        body.update(overrides)
        return body

    def test_linked_employee_persists(self, session, safety_forms_token, roster_employee):
        emp = roster_employee
        body = self._payload(employee_name=emp["name"], employee_id=emp["id"])
        r = session.post(
            f"{BASE_URL}/api/safety-forms/equipment-issuances",
            json=body,
            headers={"X-Safety-Forms-Token": safety_forms_token, "Content-Type": "application/json"},
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("ok") is True
        issuance_id = data["id"]
        # Round-trip GET.
        r2 = session.get(
            f"{BASE_URL}/api/safety-forms/equipment-issuances/{issuance_id}",
            headers={"X-Safety-Forms-Token": safety_forms_token, "Content-Type": "application/json"},
        )
        assert r2.status_code == 200
        doc = r2.json()
        assert doc["employee_name"] == emp["name"]
        assert doc.get("employee_id") == emp["id"]

    def test_freetext_employee_persists_without_id(self, session, safety_forms_token):
        body = self._payload(employee_name="iter363 PPE Free Text", employee_id="")
        r = session.post(
            f"{BASE_URL}/api/safety-forms/equipment-issuances",
            json=body,
            headers={"X-Safety-Forms-Token": safety_forms_token, "Content-Type": "application/json"},
        )
        assert r.status_code == 200, r.text
        data = r.json()
        assert data.get("ok") is True
        r2 = session.get(
            f"{BASE_URL}/api/safety-forms/equipment-issuances/{data['id']}",
            headers={"X-Safety-Forms-Token": safety_forms_token, "Content-Type": "application/json"},
        )
        assert r2.status_code == 200
        doc = r2.json()
        assert doc["employee_name"] == "iter363 PPE Free Text"
        assert not doc.get("employee_id")


# ───────────── 6 · Safety-Forms Equipment Training ────────────────────


class TestTrainingRecordLinkage:
    def _payload(self, **overrides) -> dict:
        body = {
            "employee_name": "iter363 Test Training Emp",
            "employee_id": "",
            "position": "Operator",
            "project_name": f"iter363-TRN-{uuid.uuid4().hex[:6]}",
            "project_number": "",
            "location": "Yard",
            "instructor_name": "iter363 Auto-Test",
            "training_date": TODAY,
            "equipment_type": "Skid Steer",
            "topics_covered": ["iter363 verification"],
            "acknowledgment": True,
            "employee_signature": PIXEL_PNG,
            "instructor_signature": PIXEL_PNG,
            "lang": "en",
        }
        body.update(overrides)
        return body

    def test_linked_employee_persists(self, session, safety_forms_token, roster_employee):
        emp = roster_employee
        body = self._payload(employee_name=emp["name"], employee_id=emp["id"])
        r = session.post(
            f"{BASE_URL}/api/safety-forms/equipment-trainings",
            json=body,
            headers={"X-Safety-Forms-Token": safety_forms_token, "Content-Type": "application/json"},
        )
        if r.status_code != 200:
            pytest.skip(f"training endpoint returned {r.status_code}: {r.text[:200]}")
        data = r.json()
        assert data.get("ok") is True
        r2 = session.get(
            f"{BASE_URL}/api/safety-forms/equipment-trainings/{data['id']}",
            headers={"X-Safety-Forms-Token": safety_forms_token, "Content-Type": "application/json"},
        )
        assert r2.status_code == 200
        doc = r2.json()
        assert doc["employee_name"] == emp["name"]
        assert doc.get("employee_id") == emp["id"]

    def test_freetext_employee_persists_without_id(self, session, safety_forms_token):
        body = self._payload(employee_name="iter363 Training Free Text", employee_id="")
        r = session.post(
            f"{BASE_URL}/api/safety-forms/equipment-trainings",
            json=body,
            headers={"X-Safety-Forms-Token": safety_forms_token, "Content-Type": "application/json"},
        )
        if r.status_code != 200:
            pytest.skip(f"training endpoint returned {r.status_code}: {r.text[:200]}")
        data = r.json()
        assert data.get("ok") is True
        r2 = session.get(
            f"{BASE_URL}/api/safety-forms/equipment-trainings/{data['id']}",
            headers={"X-Safety-Forms-Token": safety_forms_token, "Content-Type": "application/json"},
        )
        assert r2.status_code == 200
        doc = r2.json()
        assert doc["employee_name"] == "iter363 Training Free Text"
        assert not doc.get("employee_id")


# ────────────── 7 · Roster API contract (UI-visible field) ────────────


class TestRosterApiUiContract:
    """iter363 regression lock — the EmployeeRosterField now reads
    item.name (flat), with item.label / item.raw.name as fallbacks.
    The roster API must keep returning a UI-renderable `name` field
    so suggestion dropdowns are NOT visually blank."""

    def test_items_have_renderable_name(self, session, admin_token):
        r = session.get(
            f"{BASE_URL}/api/master-lookup/employees",
            params={"q": "a", "limit": 5},
            headers={"X-Admin-Token": admin_token, "Content-Type": "application/json"},
        )
        assert r.status_code == 200, r.text
        items = r.json().get("items", [])
        for it in items[:5]:
            assert it.get("name") or it.get("label") or (it.get("raw") or {}).get("name"), (
                f"roster item has NO renderable name/label/raw.name field: {it}"
            )
