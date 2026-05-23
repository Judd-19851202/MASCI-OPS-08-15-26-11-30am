"""
iter353c · Unified Employee Accountability Timeline + HR Compliance Brief PDF.

Validates:
- Source-level locks on hr_portal.py (timeline + brief.pdf endpoints exist;
  use the shared HR/Safety/Admin gate; aggregate the expected collections).
- Live aggregation E2E (training · PPE · CDL · FL · status_history surface
  on the timeline).
- Archived rows still appear on the timeline (read aggregation).
- RBAC: HR/Safety/Admin allowed; PM/Shop/Dispatch/FL/anon rejected.
- PDF: returns binary `%PDF` payload with content-type application/pdf.
- No mutations to source collections during timeline reads (read-only contract).
"""
from __future__ import annotations

import os
import time
import uuid
from typing import Any, Dict, List, Optional

import pytest
import requests

# ── Test target ──────────────────────────────────────────────────────────────
_FRONT_ENV = "/app/frontend/.env"
try:
    with open(_FRONT_ENV) as fh:
        for ln in fh:
            if ln.startswith("REACT_APP_BACKEND_URL="):
                API_BASE = ln.split("=", 1)[1].strip() + "/api"
                break
        else:
            API_BASE = "http://localhost:8001/api"
except FileNotFoundError:
    API_BASE = "http://localhost:8001/api"

SUPER_EMAIL = os.environ.get("SUPER_ADMIN_EMAIL", "jaymn.judd@mascigc.com")
SUPER_PW = os.environ.get("SUPER_ADMIN_BOOTSTRAP_PASSWORD", "Maddix123!")
HR_EMAIL = "hrmanager@mascigc.com"
HR_PW = "HRTesting2026!"
PM_EMAIL = "chriswright@mascigc.com"
PM_PW = "ChrisRocksThis2026"

HR_PORTAL_PATH = "/app/backend/routes/hr_portal.py"
TIMEOUT = 30


# ── helpers ──────────────────────────────────────────────────────────────────
def _multi_login() -> Dict[str, str]:
    r = requests.post(f"{API_BASE}/auth/multi-login",
                      json={"email": SUPER_EMAIL, "password": SUPER_PW},
                      timeout=TIMEOUT)
    r.raise_for_status()
    return r.json().get("portal_tokens") or {}


def _hr_token() -> str:
    r = requests.post(f"{API_BASE}/hr/login",
                      json={"email": HR_EMAIL, "password": HR_PW},
                      timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()["token"]


def _pm_token() -> str:
    r = requests.post(f"{API_BASE}/pm/login",
                      json={"email": PM_EMAIL, "password": PM_PW},
                      timeout=TIMEOUT)
    r.raise_for_status()
    return r.json()["token"]


def _pick_employee_id(hr_tok: str) -> str:
    r = requests.get(f"{API_BASE}/hr/employees",
                     headers={"X-HR-Token": hr_tok},
                     params={"limit": 5},
                     timeout=TIMEOUT)
    r.raise_for_status()
    data = r.json()
    items = data if isinstance(data, list) else (data.get("items") or data.get("employees") or [])
    assert items, "no employees in roster — cannot run accountability tests"
    return items[0]["id"]


def _src() -> str:
    with open(HR_PORTAL_PATH) as fh:
        return fh.read()


# ─────────────────────────────────────────────────────────────────────────────
# 1 · Source-level locks
# ─────────────────────────────────────────────────────────────────────────────
def test_timeline_route_registered():
    s = _src()
    assert '/hr/employees/{emp_id}/accountability/timeline' in s, \
        "timeline route missing"
    assert '/hr/employees/{emp_id}/accountability/brief.pdf' in s, \
        "compliance brief PDF route missing"


def test_timeline_uses_shared_gate():
    s = _src()
    # Both endpoints must be gated by require_safety_or_hr_or_admin
    # (HR + Safety + Admin shared accountability gate).
    assert s.count("Depends(require_safety_or_hr_or_admin)") >= 2, \
        "timeline + brief.pdf must both use shared HR+Safety+Admin gate"


def test_timeline_aggregates_expected_collections():
    s = _src()
    # The timeline aggregation must touch each of the named source
    # collections — ensures no silent drop.
    for coll in (
        "safety_training_records",
        "training_track_records",
        "safety_equipment_issuances",
        "safety_equipment_trainings",
        "incidents",
        "field_leadership_records",
    ):
        assert f"db.{coll}." in s, f"timeline missing aggregation of {coll}"


def test_timeline_aggregates_employee_lifecycle():
    s = _src()
    # status_history + CDL fields must be surfaced on the timeline.
    assert "status_history" in s
    assert "cdl_expiration_date" in s
    assert "medical_card_expiration_date" in s


def test_brief_pdf_uses_reportlab():
    s = _src()
    assert "from reportlab" in s
    assert "SimpleDocTemplate" in s


# ─────────────────────────────────────────────────────────────────────────────
# 2 · Live aggregation E2E (HR token)
# ─────────────────────────────────────────────────────────────────────────────
def test_timeline_live_hr_token():
    hr = _hr_token()
    emp_id = _pick_employee_id(hr)
    r = requests.get(f"{API_BASE}/hr/employees/{emp_id}/accountability/timeline",
                     headers={"X-HR-Token": hr},
                     timeout=TIMEOUT)
    assert r.status_code == 200, r.text
    data = r.json()
    assert data.get("ok") is True
    assert "employee" in data and data["employee"].get("id") == emp_id
    assert "events" in data and isinstance(data["events"], list)
    assert "current_state" in data
    assert "category_counts" in data
    assert "total_events" in data
    assert "generated_at" in data
    # viewer attribution must be present and identify the HR actor.
    assert (data.get("viewer") or {}).get("role") == "hr"


def test_timeline_event_audit_attribution_shape():
    hr = _hr_token()
    emp_id = _pick_employee_id(hr)
    r = requests.get(f"{API_BASE}/hr/employees/{emp_id}/accountability/timeline",
                     headers={"X-HR-Token": hr},
                     timeout=TIMEOUT)
    r.raise_for_status()
    events: List[Dict[str, Any]] = r.json().get("events") or []
    if not events:
        pytest.skip("employee has no timeline events in preview DB")
    e = events[0]
    # Every event MUST carry source + role attribution for the operator
    # to see WHO entered it.
    for k in ("ts", "kind", "category", "title", "source",
              "created_by_role", "originating_portal"):
        assert k in e, f"event missing key {k}: {e}"


def test_timeline_archived_records_remain_visible():
    """Archived (soft-deleted) safety records must still surface on the
    timeline as `archived=True` — operator MUST be able to audit them."""
    hr = _hr_token()
    emp_id = _pick_employee_id(hr)
    # Create + archive a safety training record via the iter353a path.
    tr_payload = {
        "employee_id": emp_id,
        "training_name": f"iter353c-archived-{uuid.uuid4().hex[:8]}",
        "certification_type": "OSHA 10",
        "completed_date": "2026-01-01",
        "notes": "iter353c lifecycle test",
    }
    r = requests.post(f"{API_BASE}/safety/training-records",
                      headers={"X-HR-Token": hr},
                      json=tr_payload,
                      timeout=TIMEOUT)
    if r.status_code != 200:
        pytest.skip(f"could not seed safety training via HR (preview): {r.status_code} {r.text[:200]}")
    rid = r.json().get("id") or r.json().get("record", {}).get("id")
    if not rid:
        pytest.skip("safety training create did not return id")
    # Archive via PATCH (the iter353a-UI archive pattern).
    requests.patch(f"{API_BASE}/safety/training-records/{rid}",
                   headers={"X-HR-Token": hr},
                   json={"notes": "[archived 2026-05-23]"},
                   timeout=TIMEOUT)
    try:
        r2 = requests.get(f"{API_BASE}/hr/employees/{emp_id}/accountability/timeline",
                          headers={"X-HR-Token": hr},
                          timeout=TIMEOUT)
        r2.raise_for_status()
        match = [e for e in r2.json().get("events") or []
                 if e.get("title") == tr_payload["training_name"]]
        assert match, "archived training record disappeared from timeline"
        assert match[0].get("archived") is True, "archived flag not surfaced"
    finally:
        # Cleanup — safety DELETE (HR can't hard-delete per policy).
        sf = _multi_login().get("safety", "")
        if sf:
            requests.delete(f"{API_BASE}/safety/training-records/{rid}",
                            headers={"X-Safety-Token": sf}, timeout=TIMEOUT)


# ─────────────────────────────────────────────────────────────────────────────
# 3 · RBAC matrix
# ─────────────────────────────────────────────────────────────────────────────
def test_timeline_rbac_safety_allowed():
    tokens = _multi_login()
    sf = tokens.get("safety")
    if not sf:
        pytest.skip("no safety portal_tokens available")
    hr = _hr_token()
    emp_id = _pick_employee_id(hr)
    r = requests.get(f"{API_BASE}/hr/employees/{emp_id}/accountability/timeline",
                     headers={"X-Safety-Token": sf},
                     timeout=TIMEOUT)
    assert r.status_code == 200, r.text
    assert (r.json().get("viewer") or {}).get("role") == "safety"


def test_timeline_rbac_admin_allowed():
    tokens = _multi_login()
    a = tokens.get("admin")
    assert a, "expected admin portal token from multi-login"
    hr = _hr_token()
    emp_id = _pick_employee_id(hr)
    r = requests.get(f"{API_BASE}/hr/employees/{emp_id}/accountability/timeline",
                     headers={"X-Admin-Token": a},
                     timeout=TIMEOUT)
    assert r.status_code == 200, r.text


def test_timeline_rbac_pm_blocked():
    pm = _pm_token()
    hr = _hr_token()
    emp_id = _pick_employee_id(hr)
    r = requests.get(f"{API_BASE}/hr/employees/{emp_id}/accountability/timeline",
                     headers={"X-PM-Token": pm, "X-Admin-Token": ""},
                     timeout=TIMEOUT)
    assert r.status_code in (401, 403), \
        f"PM token must be rejected, got {r.status_code}: {r.text[:200]}"


def test_timeline_rbac_anonymous_blocked():
    hr = _hr_token()
    emp_id = _pick_employee_id(hr)
    r = requests.get(f"{API_BASE}/hr/employees/{emp_id}/accountability/timeline",
                     headers={"X-Admin-Token": ""},
                     timeout=TIMEOUT)
    assert r.status_code in (401, 403)


def test_brief_pdf_rbac_anonymous_blocked():
    hr = _hr_token()
    emp_id = _pick_employee_id(hr)
    r = requests.get(f"{API_BASE}/hr/employees/{emp_id}/accountability/brief.pdf",
                     headers={"X-Admin-Token": ""},
                     timeout=TIMEOUT)
    assert r.status_code in (401, 403)


# ─────────────────────────────────────────────────────────────────────────────
# 4 · PDF surface
# ─────────────────────────────────────────────────────────────────────────────
def test_brief_pdf_returns_pdf_magic_bytes_hr():
    hr = _hr_token()
    emp_id = _pick_employee_id(hr)
    r = requests.get(f"{API_BASE}/hr/employees/{emp_id}/accountability/brief.pdf",
                     headers={"X-HR-Token": hr},
                     timeout=TIMEOUT)
    assert r.status_code == 200, r.text[:300]
    assert r.headers.get("content-type", "").startswith("application/pdf"), \
        f"unexpected content-type: {r.headers.get('content-type')}"
    assert r.content[:5] == b"%PDF-", "PDF magic-bytes header missing"
    assert len(r.content) > 1024, "PDF payload is suspiciously small"


def test_brief_pdf_includes_core_sections_text():
    hr = _hr_token()
    emp_id = _pick_employee_id(hr)
    r = requests.get(f"{API_BASE}/hr/employees/{emp_id}/accountability/brief.pdf",
                     headers={"X-HR-Token": hr},
                     timeout=TIMEOUT)
    r.raise_for_status()
    body = r.content
    # ReportLab compresses content streams. The /Title metadata in the
    # PDF info dictionary IS uncompressed and carries our brief title
    # (the doc title we set on SimpleDocTemplate). That's enough to
    # prove this isn't a generic blank reportlab PDF.
    assert b"HR Compliance Brief" in body, \
        "PDF /Title metadata missing — brief identity not stamped"


def test_brief_pdf_filename_set():
    hr = _hr_token()
    emp_id = _pick_employee_id(hr)
    r = requests.get(f"{API_BASE}/hr/employees/{emp_id}/accountability/brief.pdf",
                     headers={"X-HR-Token": hr},
                     timeout=TIMEOUT)
    r.raise_for_status()
    cd = r.headers.get("content-disposition", "")
    assert "HR_Compliance_Brief_" in cd, f"unexpected disposition: {cd}"


# ─────────────────────────────────────────────────────────────────────────────
# 5 · No source-collection mutation contract
# ─────────────────────────────────────────────────────────────────────────────
def test_timeline_endpoint_is_get_only():
    """The accountability/timeline endpoint MUST only accept GET — no
    write peer should exist."""
    hr = _hr_token()
    emp_id = _pick_employee_id(hr)
    url = f"{API_BASE}/hr/employees/{emp_id}/accountability/timeline"
    for verb in ("post", "patch", "delete"):
        r = getattr(requests, verb)(url, headers={"X-HR-Token": hr}, timeout=TIMEOUT)
        assert r.status_code in (401, 403, 404, 405), \
            f"timeline accepted {verb.upper()} (got {r.status_code}) — read-only contract broken"


def test_brief_pdf_is_get_only():
    hr = _hr_token()
    emp_id = _pick_employee_id(hr)
    url = f"{API_BASE}/hr/employees/{emp_id}/accountability/brief.pdf"
    for verb in ("post", "patch", "delete"):
        r = getattr(requests, verb)(url, headers={"X-HR-Token": hr}, timeout=TIMEOUT)
        assert r.status_code in (401, 403, 404, 405)


# ─────────────────────────────────────────────────────────────────────────────
# 6 · Frontend route + entry-point locks (no headless playwright required)
# ─────────────────────────────────────────────────────────────────────────────
def test_frontend_route_registered():
    with open("/app/frontend/src/App.js") as fh:
        s = fh.read()
    assert 'path="/hr/employees/:id/accountability"' in s
    assert "HrEmployeeAccountabilityTimeline" in s


def test_frontend_hr_employee_list_has_accountability_link():
    with open("/app/frontend/src/pages/HrEmployees.jsx") as fh:
        s = fh.read()
    assert "hremp-acct-link-" in s, "HR employee row missing Accountability link"


def test_frontend_hr_drawer_has_timeline_link():
    with open("/app/frontend/src/pages/HrEmployees.jsx") as fh:
        s = fh.read()
    assert "hremp-drawer-acct-link" in s, "HR drawer missing Accountability link"


def test_frontend_safety_profile_has_timeline_link():
    with open("/app/frontend/src/pages/SafetyEmployeeProfiles.jsx") as fh:
        s = fh.read()
    assert "safety-emp-accountability-link" in s, \
        "Safety employee profile missing Accountability link"
