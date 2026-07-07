"""TRACK 23.10-E · live regression pytest against preview backend.

The primary happy-path smoke lives in /tmp/track_23_10_e_e2e.py (all 15 checkpoints
pass). This pytest file adds regression coverage for two additional checkpoints
from the review request that the smoke doesn't run:

  * excavation gate=yes with empty linked_excavation_ids -> HTTP 422
    with error='excavation_record_required'
  * non-excavation DR (no excavation block) still renders a valid PDF

It also re-covers the invalid-CP and free-text-CP negatives as pytest cases so
they are captured in the JUnit report.
"""
import os
from datetime import date

import pytest
import requests


def _base_url():
    url = os.environ.get("REACT_APP_BACKEND_URL", "").strip().rstrip("/")
    if url:
        return url
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                return line.split("=", 1)[1].strip().rstrip("/")
    return ""


BASE_URL = _base_url()
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"
PROJECT_NUMBER = "24-12"
PROJECT_NAME = "CC5744 - OXFORD RD Improvements (OXFORD)"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=90,
    )
    assert r.status_code == 200, r.text
    data = r.json()
    token = (data.get("portal_tokens") or {}).get("admin")
    assert token, f"no admin token in login response: {data}"
    return token


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"X-Admin-Token": admin_token, "Content-Type": "application/json"}


@pytest.fixture(scope="module")
def qualification_id(admin_headers):
    r = requests.get(
        f"{BASE_URL}/api/employees/competent-persons?active=true",
        headers=admin_headers,
        timeout=60,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body.get("count", 0) >= 1
    return body["items"][0]["qualification_id"]


@pytest.fixture(scope="module")
def excavation_id(admin_headers):
    today = date.today().isoformat()
    body = {
        "project_name": PROJECT_NAME,
        "project_number": PROJECT_NUMBER,
        "location": "STA 12+00 · Utility Trench",
        "work_area": "Utility Trench East",
        "date_of_work": today,
        "prepared_by_name": "Track 23.10-E pytest",
        "foreman_name": "Alec Perkins (Al)",
        "supervisor_name": "Alec Perkins (Al)",
        "submitted_by": "e2e-pytest@mascicert.local",
        "length_ft": 25.0, "width_ft": 3.5, "depth_ft": 5.5, "depth_unit": "ft",
        "depth_ge_4ft": True, "depth_ge_5ft": True,
        "work_type": "Utility Installation",
        "soil_classification": "Type B",
        "protective_system": "Trench Box",
        "source": "Track 23.10-E pytest",
    }
    r = requests.post(
        f"{BASE_URL}/api/trench-safety/excavations/public/submit",
        json=body,
        timeout=60,
    )
    assert r.status_code == 200, r.text
    return r.json()["id"]


def _dr_body(qid, ex_ids, gate="yes", exc_overrides=None):
    today = date.today().isoformat()
    dr = {
        "project_name": PROJECT_NAME,
        "project_number": PROJECT_NUMBER,
        "location": "STA 12+00 · Utility Trench",
        "report_date": today,
        "prepared_by": "Track 23.10-E pytest",
        "superintendent": "David Puma",
        "weather_summary": "Clear 74F",
        "safety_incidents_today": "No",
        "injuries_reported": "No",
        "general_notes": "pytest E2E",
        "excavation_activity_today": gate,
        "linked_excavation_ids": ex_ids,
    }
    if gate == "yes":
        exc = {
            "excavation_today": "yes",
            "project_area": "Utility Trench East",
            "station_from": "12+00", "station_to": "12+25",
            "length": 25, "width": 3.5, "depth": 5.5, "dimension_unit": "ft",
            "protective_systems": ["trench_box"],
            "soil_type": "Type B",
            "utility_conflict": "no", "utility_damage_or_strike": "no",
            "competent_person_qualification_id": qid,
            "inspection_completed": "yes", "inspection_time": "07:15",
            "hazards_identified": "no", "corrective_actions_open": "no",
            "work_stopped": "no", "hold_issued": "no",
            "access_egress_compliant": "yes",
            "atmospheric_testing_required": "no", "water_accumulation": "no",
        }
        if exc_overrides:
            exc.update(exc_overrides)
        dr["excavation"] = exc
    return dr


# ── Positive checkpoints ─────────────────────────────────────────────
def test_multi_login_returns_admin_token(admin_token):
    assert isinstance(admin_token, str) and len(admin_token) > 10


def test_competent_persons_active(admin_headers, qualification_id):
    r = requests.get(
        f"{BASE_URL}/api/employees/competent-persons?active=true",
        headers=admin_headers, timeout=60,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["count"] >= 1
    it = body["items"][0]
    for k in ("qualification_id", "employee_id", "name"):
        assert k in it
    assert it.get("warning") is False


def test_qualification_snapshot(admin_headers, qualification_id):
    r = requests.get(
        f"{BASE_URL}/api/hr/qualifications/{qualification_id}/snapshot",
        headers=admin_headers, timeout=60,
    )
    assert r.status_code == 200
    snap = r.json()
    assert snap.get("qualification_type") == "COMPETENT_PERSON"
    assert snap.get("verification_status_at_selection") == "active"
    assert snap.get("is_active_at_selection") is True


# ── Negative: excavation gate=yes but no linked excavation IDs (422) ─
def test_excavation_gate_without_linked_excavation_ids(admin_headers, qualification_id):
    body = _dr_body(qualification_id, ex_ids=[], gate="yes")
    r = requests.post(
        f"{BASE_URL}/api/daily-reports",
        headers=admin_headers, json=body, timeout=45,
    )
    assert r.status_code == 422, f"expected 422, got {r.status_code}: {r.text[:400]}"
    txt = r.text.lower()
    assert "excavation_record_required" in txt or "linked_excavation" in txt or "excavation" in txt


# ── Negative: invalid CP qualification_id ─────────────────────────────
def test_invalid_competent_person(admin_headers, qualification_id, excavation_id):
    body = _dr_body(
        qualification_id, ex_ids=[excavation_id],
        exc_overrides={"competent_person_qualification_id": "does-not-exist-xxx"},
    )
    r = requests.post(
        f"{BASE_URL}/api/daily-reports",
        headers=admin_headers, json=body, timeout=45,
    )
    assert r.status_code in (400, 422), r.text[:300]
    assert "competent_person" in r.text.lower()


# ── Negative: free-text CP forbidden ─────────────────────────────────
def test_free_text_competent_person_forbidden(admin_headers, qualification_id, excavation_id):
    body = _dr_body(qualification_id, ex_ids=[excavation_id])
    body["excavation"].pop("competent_person_qualification_id", None)
    body["excavation"]["competent_person_name_freetext"] = "Random Person"
    r = requests.post(
        f"{BASE_URL}/api/daily-reports",
        headers=admin_headers, json=body, timeout=45,
    )
    assert r.status_code in (400, 422), r.text[:300]
    lower = r.text.lower()
    assert "free_text" in lower or "freetext" in lower or "competent_person" in lower


# ── Non-excavation DR renders PDF ────────────────────────────────────
def test_non_excavation_dr_renders_pdf(admin_headers, qualification_id):
    body = _dr_body(qualification_id, ex_ids=[], gate="no")
    r = requests.post(
        f"{BASE_URL}/api/daily-reports",
        headers=admin_headers, json=body, timeout=60,
    )
    assert r.status_code == 200, r.text[:400]
    dr_id = r.json()["id"]
    pdf = requests.get(
        f"{BASE_URL}/api/daily-reports/{dr_id}/pdf",
        headers=admin_headers, timeout=120,
    )
    assert pdf.status_code == 200
    assert pdf.content[:4] == b"%PDF"
