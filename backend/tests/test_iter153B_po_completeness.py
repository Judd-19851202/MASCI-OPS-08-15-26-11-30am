"""Iter153B · PO Request operational completeness — backend tests.

Tests the new Phase 2.5 PO endpoints added to surface the full
operational workflow across Field Leadership, PM, HR, and Admin:

  * GET /api/po-requests — new filters: vendor, requested_by_name,
    requested_by_user_id, mine_only, missing_receipt_only.
  * POST /api/po-requests/{id}/respond-clarification — original
    requester (or role peers) responds to a clarification request,
    moving the PO back to Pending Approval.
  * GET /api/po-requests/export.csv — Admin/PM/HR/Leadership CSV
    export with scope respected (Leadership only sees own POs).
"""
import os
import uuid
from pathlib import Path

import pytest
import requests


def _read_kv(path, key):
    try:
        with open(path) as f:
            for line in f:
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        pass
    return ""


BASE_URL = (
    _read_kv(Path("/app/frontend/.env"), "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")

HR_EMAIL = "hrmanager@mascigc.com"
HR_PW = "HRTesting2026!"
LEADERSHIP_PW = "MASCIGC"

NO_ADMIN = {"X-Admin-Token": ""}
TAG = f"TEST_iter153B_{uuid.uuid4().hex[:6]}"


@pytest.fixture(scope="module")
def hr_token():
    r = requests.post(
        f"{BASE_URL}/api/hr/login",
        json={"email": HR_EMAIL, "password": HR_PW}, timeout=20,
    )
    if r.status_code != 200:
        pytest.skip(f"HR login failed: {r.status_code}")
    return r.json()["token"]


@pytest.fixture(scope="module")
def leadership_token():
    r = requests.post(
        f"{BASE_URL}/api/field-leadership/login",
        json={"password": LEADERSHIP_PW}, timeout=20,
    )
    if r.status_code != 200:
        pytest.skip(f"FL login failed: {r.status_code}")
    return r.json()["token"]


@pytest.fixture
def submitted_po(leadership_token):
    """Create one PO, return its id. Cleanup at teardown."""
    body = {
        "project_number": f"{TAG}-PROJ",
        "vendor": f"{TAG} Vendor",
        "description": f"{TAG} description",
        "estimated_amount": 150.0,
        "category": "Materials",
        "urgency": "Normal",
    }
    r = requests.post(
        f"{BASE_URL}/api/po-requests",
        headers={"X-Leadership-Token": leadership_token, **NO_ADMIN},
        json=body, timeout=20,
    )
    assert r.status_code == 200, r.text
    po_id = r.json()["id"]
    yield po_id
    # cleanup: cancel (HR can cancel) so it doesn't pollute test data
    try:
        requests.post(f"{BASE_URL}/api/po-requests/{po_id}/cancel",
                      headers={"X-HR-Token": _hr()}, timeout=10)
    except Exception:
        pass


def _hr():
    r = requests.post(f"{BASE_URL}/api/hr/login",
                       json={"email": HR_EMAIL, "password": HR_PW}, timeout=20)
    return r.json()["token"]


# ─── new filters ─────────────────────────────────────────────────────
def test_filter_vendor(hr_token, submitted_po):
    r = requests.get(
        f"{BASE_URL}/api/po-requests",
        headers={"X-HR-Token": hr_token, **NO_ADMIN},
        params={"vendor": TAG}, timeout=20,
    )
    assert r.status_code == 200
    items = r.json()["items"]
    # All returned rows must contain TAG in vendor
    for it in items:
        assert TAG in (it.get("vendor") or "")


def test_filter_requested_by_name(hr_token, submitted_po):
    r = requests.get(
        f"{BASE_URL}/api/po-requests",
        headers={"X-HR-Token": hr_token, **NO_ADMIN},
        params={"requested_by_name": "Field Leadership"}, timeout=20,
    )
    assert r.status_code == 200
    items = r.json()["items"]
    for it in items:
        assert "leadership" in (it.get("requested_by_name") or "").lower() \
            or "field leadership" in (it.get("requested_by_name") or "").lower()


def test_filter_mine_only_leadership(leadership_token, submitted_po):
    """FL mine_only is a no-op for shared-password actor (no actor.id)
    — but it MUST NOT crash; should return the leadership-scoped list."""
    r = requests.get(
        f"{BASE_URL}/api/po-requests",
        headers={"X-Leadership-Token": leadership_token, **NO_ADMIN},
        params={"mine_only": "true"}, timeout=20,
    )
    assert r.status_code == 200
    # mine_only with no actor.id collapses to the same scope as default
    # leadership scoping — still safe and well-defined.
    assert "items" in r.json()


def test_filter_missing_receipt_only(hr_token, submitted_po):
    r = requests.get(
        f"{BASE_URL}/api/po-requests",
        headers={"X-HR-Token": hr_token, **NO_ADMIN},
        params={"missing_receipt_only": "true"}, timeout=20,
    )
    assert r.status_code == 200
    items = r.json()["items"]
    # Every row must be in the missing-receipt cohort
    for it in items:
        assert it["status"] in ("Approved", "Pending Receipt", "Overdue Receipt")
        assert not it.get("receipt_url")


# ─── respond-clarification workflow ──────────────────────────────────
def test_respond_clarification_full_cycle(
    leadership_token, hr_token, submitted_po,
):
    po_id = submitted_po
    # HR requests clarification
    r1 = requests.post(
        f"{BASE_URL}/api/po-requests/{po_id}/approve",
        headers={"X-HR-Token": hr_token, **NO_ADMIN},
        json={"action": "clarify", "notes": "Need vendor breakdown"},
        timeout=20,
    )
    assert r1.status_code == 200
    assert r1.json()["status"] == "Clarification Needed"
    # FL responds
    r2 = requests.post(
        f"{BASE_URL}/api/po-requests/{po_id}/respond-clarification",
        headers={"X-Leadership-Token": leadership_token, **NO_ADMIN},
        json={"response": "$100 lumber + $50 fasteners"},
        timeout=20,
    )
    assert r2.status_code == 200
    d = r2.json()
    assert d["status"] == "Pending Approval"
    # audit contains the response
    last = d["audit"][-1]
    assert last["action"] == "clarification_response"
    assert last["details"]["response"].startswith("$100")


def test_respond_clarification_wrong_status_409(
    leadership_token, hr_token, submitted_po,
):
    """Submitted PO (not yet clarified) cannot accept clarification responses."""
    r = requests.post(
        f"{BASE_URL}/api/po-requests/{submitted_po}/respond-clarification",
        headers={"X-Leadership-Token": leadership_token, **NO_ADMIN},
        json={"response": "test"}, timeout=20,
    )
    assert r.status_code == 409


def test_respond_clarification_validation_422(
    leadership_token, submitted_po,
):
    r = requests.post(
        f"{BASE_URL}/api/po-requests/{submitted_po}/respond-clarification",
        headers={"X-Leadership-Token": leadership_token, **NO_ADMIN},
        json={"response": ""}, timeout=20,
    )
    assert r.status_code == 422


# ─── CSV export ──────────────────────────────────────────────────────
def test_csv_export_hr(hr_token):
    r = requests.get(
        f"{BASE_URL}/api/po-requests/export.csv",
        headers={"X-HR-Token": hr_token, **NO_ADMIN}, timeout=20,
    )
    assert r.status_code == 200
    assert "text/csv" in r.headers.get("Content-Type", "")
    body = r.text
    # Header row present
    assert body.split("\n")[0].startswith("PO Number,Status,Project,Vendor,")
    assert "Content-Disposition" in {k for k in r.headers}
    assert r.headers["Content-Disposition"].startswith("attachment")


def test_csv_export_anon_401():
    r = requests.get(
        f"{BASE_URL}/api/po-requests/export.csv",
        headers=NO_ADMIN, timeout=20,
    )
    assert r.status_code == 401


def test_csv_export_filters_respected(hr_token, submitted_po):
    """Vendor filter should narrow CSV rows."""
    r = requests.get(
        f"{BASE_URL}/api/po-requests/export.csv",
        headers={"X-HR-Token": hr_token, **NO_ADMIN},
        params={"vendor": TAG}, timeout=20,
    )
    assert r.status_code == 200
    body = r.text
    # Every non-header data row must reference our tagged vendor
    lines = [l for l in body.split("\n") if l.strip()]
    for ln in lines[1:]:
        assert TAG in ln
