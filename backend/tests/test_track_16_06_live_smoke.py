"""TRACK 16.06 · Transportation Experience Layer live smoke.

Exercises the new aggregation endpoints against the running preview backend
using a real admin token (jaymn.judd@mascigc.com → multi-login).
"""
from __future__ import annotations

import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL not set"

ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PW = "Maddix123!"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PW},
        timeout=30,
    )
    assert r.status_code == 200, f"multi-login failed: {r.status_code} {r.text[:300]}"
    body = r.json()
    tok = (body.get("portal_tokens") or {}).get("admin")
    assert tok, f"no admin token in response: {list(body.keys())}"
    return tok


@pytest.fixture(scope="module")
def headers(admin_token):
    return {"X-Admin-Token": admin_token, "Content-Type": "application/json"}


# ───────────────── Auth gate ─────────────────
def test_01_dashboard_anonymous_returns_401():
    r = requests.get(f"{BASE_URL}/api/admin/transportation/dashboard", timeout=45)
    assert r.status_code in (401, 403), f"expected 401/403 got {r.status_code}"


def test_02_documents_queue_anonymous_returns_401():
    r = requests.get(f"{BASE_URL}/api/admin/transportation/documents/queue", timeout=45)
    assert r.status_code in (401, 403)


def test_03_inspections_queue_anonymous_returns_401():
    r = requests.get(f"{BASE_URL}/api/admin/transportation/inspections/queue", timeout=45)
    assert r.status_code in (401, 403)


def test_04_audit_timeline_anonymous_returns_401():
    r = requests.get(f"{BASE_URL}/api/admin/transportation/audit-timeline", timeout=45)
    assert r.status_code in (401, 403)


# ───────────────── Dashboard ─────────────────
def test_05_dashboard_payload_shape(headers):
    r = requests.get(f"{BASE_URL}/api/admin/transportation/dashboard",
                     headers=headers, timeout=30)
    assert r.status_code == 200, r.text[:400]
    body = r.json()
    assert "compliance_score" in body
    assert isinstance(body["compliance_score"], int)
    assert 0 <= body["compliance_score"] <= 100
    tiles = body.get("tiles") or {}
    required_tiles = {
        "eligible_drivers", "eligible_trucks", "eligible_carriers",
        "drivers_pending_review", "carriers_pending_review",
        "trucks_pending_inspection", "documents_awaiting_review",
        "expiring_documents_30d", "annual_inspections_due_30d",
        "pending_corrections",
    }
    missing = required_tiles - set(tiles.keys())
    assert not missing, f"missing tiles: {missing}"
    buckets = body.get("buckets") or {}
    for k in ("carrier", "person", "truck"):
        assert k in buckets, f"bucket {k} missing"
    assert "disclaimer" in body and body["disclaimer"]
    # active_rate may be None if no active schedule
    assert "active_rate" in body


# ───────────────── Documents Queue ─────────────────
def test_06_documents_queue_default(headers):
    r = requests.get(f"{BASE_URL}/api/admin/transportation/documents/queue",
                     headers=headers, timeout=30)
    assert r.status_code == 200, r.text[:400]
    body = r.json()
    assert "count" in body and "items" in body
    assert isinstance(body["items"], list)
    assert body["count"] == len(body["items"])
    for it in body["items"]:
        assert it.get("scope") in ("carrier", "driver"), f"scope={it.get('scope')}"
        assert "_id" not in it


def test_07_documents_queue_filter_scope_carrier(headers):
    r = requests.get(f"{BASE_URL}/api/admin/transportation/documents/queue",
                     params={"scope": "carrier"}, headers=headers, timeout=30)
    assert r.status_code == 200
    for it in r.json().get("items", []):
        assert it.get("scope") == "carrier"


def test_08_documents_queue_filter_scope_driver(headers):
    r = requests.get(f"{BASE_URL}/api/admin/transportation/documents/queue",
                     params={"scope": "driver"}, headers=headers, timeout=30)
    assert r.status_code == 200
    for it in r.json().get("items", []):
        assert it.get("scope") == "driver"


def test_09_documents_queue_expiring_filter(headers):
    r = requests.get(f"{BASE_URL}/api/admin/transportation/documents/queue",
                     params={"expiring_within_days": 30}, headers=headers, timeout=30)
    assert r.status_code == 200
    assert "items" in r.json()


# ───────────────── Inspections Queue ─────────────────
def test_10_inspections_queue_default(headers):
    r = requests.get(f"{BASE_URL}/api/admin/transportation/inspections/queue",
                     headers=headers, timeout=30)
    assert r.status_code == 200, r.text[:400]
    body = r.json()
    assert "count" in body and "items" in body
    assert "disclaimer" in body and body["disclaimer"]
    for it in body["items"]:
        assert "_id" not in it


def test_11_inspections_queue_filter_result_ready(headers):
    r = requests.get(f"{BASE_URL}/api/admin/transportation/inspections/queue",
                     params={"result": "ready"}, headers=headers, timeout=30)
    assert r.status_code == 200
    for it in r.json().get("items", []):
        assert it.get("result") == "ready"


# ───────────────── Audit Timeline ─────────────────
def test_12_audit_timeline_default(headers):
    r = requests.get(f"{BASE_URL}/api/admin/transportation/audit-timeline",
                     headers=headers, timeout=30)
    assert r.status_code == 200, r.text[:400]
    body = r.json()
    assert "count" in body and "items" in body
    # All items should be transport_ prefixed kinds (default kind_prefix)
    for it in body["items"]:
        kind = (it.get("kind") or "").lower()
        assert kind.startswith("transport_"), f"audit item kind not transport_*: {kind}"
        assert "_id" not in it
    # Sorted descending by ts (best-effort: check first two if present)
    items = body["items"]
    if len(items) >= 2:
        ts_list = [i.get("ts") for i in items if i.get("ts")]
        assert ts_list == sorted(ts_list, reverse=True), "audit not sorted ts desc"


def test_13_audit_timeline_entity_filter(headers):
    r = requests.get(f"{BASE_URL}/api/admin/transportation/audit-timeline",
                     params={"entity_type": "carrier"}, headers=headers, timeout=30)
    assert r.status_code == 200
    for it in r.json().get("items", []):
        assert it.get("entity_type") == "carrier"


# ───────────────── Workspace endpoints ─────────────────
def test_14_carrier_workspace_404_on_unknown(headers):
    r = requests.get(
        f"{BASE_URL}/api/admin/transportation/carriers/does-not-exist-zzz/workspace",
        headers=headers, timeout=30)
    assert r.status_code == 404


def test_15_driver_workspace_404_on_unknown(headers):
    r = requests.get(
        f"{BASE_URL}/api/admin/transportation/persons/does-not-exist-zzz/workspace",
        headers=headers, timeout=30)
    assert r.status_code == 404


def test_16_truck_workspace_404_on_unknown(headers):
    r = requests.get(
        f"{BASE_URL}/api/admin/transportation/trucks/does-not-exist-zzz/workspace",
        headers=headers, timeout=30)
    assert r.status_code == 404


def test_17_carrier_workspace_happy_path(headers):
    """Fetch a real carrier id from existing collection (read-only)."""
    # Find an existing carrier via Phase 1 list endpoint.
    r = requests.get(f"{BASE_URL}/api/admin/transportation/carriers",
                     headers=headers, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"phase1 carriers list returned {r.status_code}; can't get id")
    items = r.json() if isinstance(r.json(), list) else (r.json().get("items") or [])
    if not items:
        pytest.skip("no carriers in db to exercise workspace")
    cid = items[0].get("id")
    assert cid
    w = requests.get(f"{BASE_URL}/api/admin/transportation/carriers/{cid}/workspace",
                     headers=headers, timeout=30)
    assert w.status_code == 200, w.text[:400]
    wb = w.json()
    for k in ("carrier", "drivers", "trucks", "documents",
              "packet", "active_rate", "eligibility", "disclaimer"):
        assert k in wb, f"workspace missing {k}"
    assert wb["carrier"]["id"] == cid
    assert isinstance(wb["drivers"], list)
    assert isinstance(wb["trucks"], list)
    assert isinstance(wb["documents"], list)


def test_18_truck_workspace_happy_path(headers):
    r = requests.get(f"{BASE_URL}/api/admin/transportation/trucks",
                     headers=headers, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"trucks list returned {r.status_code}")
    items = r.json() if isinstance(r.json(), list) else (r.json().get("items") or [])
    if not items:
        pytest.skip("no trucks to exercise workspace")
    tid = items[0].get("id")
    w = requests.get(f"{BASE_URL}/api/admin/transportation/trucks/{tid}/workspace",
                     headers=headers, timeout=30)
    assert w.status_code == 200, w.text[:400]
    body = w.json()
    for k in ("truck", "carrier", "inspections", "eligibility", "disclaimer"):
        assert k in body
    assert isinstance(body["inspections"], list)


def test_19_driver_workspace_happy_path(headers):
    r = requests.get(f"{BASE_URL}/api/admin/transportation/persons",
                     headers=headers, timeout=30)
    if r.status_code != 200:
        pytest.skip(f"persons list returned {r.status_code}")
    items = r.json() if isinstance(r.json(), list) else (r.json().get("items") or [])
    if not items:
        pytest.skip("no persons to exercise workspace")
    pid = items[0].get("id")
    w = requests.get(f"{BASE_URL}/api/admin/transportation/persons/{pid}/workspace",
                     headers=headers, timeout=30)
    assert w.status_code == 200, w.text[:400]
    body = w.json()
    for k in ("driver", "carrier", "documents", "eligibility",
              "hr_linkage", "disclaimer"):
        assert k in body
