"""Iter245 — PO Request consolidation tests.

Verifies:
1. GET /api/vendors is retired (404).
2. GET /api/suppliers public and returns >100 items.
3. GET /api/jobs returns active jobs.
4. POST /api/suppliers/add: creates new + case-insensitive dedupe.
5. PO submit using SupplierCombo path: project_number + vendor (normalized) persists.
"""
import os
import time
import uuid
import pytest
import requests

def _read_env_url():
    # Read REACT_APP_BACKEND_URL from frontend/.env to avoid needing env wiring
    p = "/app/frontend/.env"
    if os.path.exists(p):
        with open(p) as f:
            for line in f:
                if line.startswith("REACT_APP_BACKEND_URL="):
                    return line.split("=", 1)[1].strip()
    return os.environ.get("REACT_APP_BACKEND_URL", "")

BASE = _read_env_url().rstrip("/")
assert BASE, "REACT_APP_BACKEND_URL not configured"
API = f"{BASE}/api"
LEADERSHIP_PASSWORD = "MASCIGC"


@pytest.fixture(scope="module")
def leadership_token():
    r = requests.post(f"{API}/field-leadership/login", json={"password": LEADERSHIP_PASSWORD}, timeout=20)
    if r.status_code != 200:
        pytest.skip(f"Leadership login failed: {r.status_code} {r.text[:200]}")
    tok = r.json().get("token")
    assert tok, "leadership token missing"
    return tok


@pytest.fixture(scope="module")
def headers(leadership_token):
    return {"X-Leadership-Token": leadership_token, "Content-Type": "application/json"}


# ---- Backend retirement of /api/vendors ----
def test_vendors_endpoint_retired():
    r = requests.get(f"{API}/vendors", timeout=15)
    assert r.status_code == 404, f"Expected 404 (retired), got {r.status_code}: {r.text[:200]}"


# ---- Suppliers master list ----
def test_suppliers_list_public_and_large():
    r = requests.get(f"{API}/suppliers", timeout=20)
    assert r.status_code == 200, r.text[:300]
    data = r.json()
    items = data.get("items") or []
    assert isinstance(items, list)
    assert len(items) > 100, f"Expected >100 suppliers, got {len(items)}"
    # Sample real names referenced in problem statement
    names = {(i.get("name") or "").lower() for i in items}
    assert any("a&l" in n or "a-1" in n or "a&l remediation" in n for n in names), \
        "Expected some known supplier seed names"


# ---- Jobs list ----
def test_jobs_active_list():
    r = requests.get(f"{API}/jobs", timeout=20)
    assert r.status_code == 200, r.text[:300]
    items = r.json().get("items") or []
    assert isinstance(items, list)
    assert len(items) > 0, "Expected at least one active job"
    j = items[0]
    assert "project_number" in j and "project_name" in j


# ---- Inline supplier Add + dedupe ----
@pytest.fixture(scope="module")
def unique_vendor():
    return f"TEST_Iter245_Vendor_{uuid.uuid4().hex[:8]}"


def test_supplier_add_new(unique_vendor, headers):
    r = requests.post(f"{API}/suppliers/add", json={"name": unique_vendor},
                      headers=headers, timeout=20)
    assert r.status_code in (200, 201), r.text[:300]
    body = r.json()
    assert body.get("created") is True
    sup = body.get("supplier") or {}
    assert sup.get("name", "").lower() == unique_vendor.lower()


def test_supplier_add_dedupe_case_insensitive(unique_vendor, headers):
    # Same name in different case
    variant = unique_vendor.lower()
    r = requests.post(f"{API}/suppliers/add", json={"name": variant},
                      headers=headers, timeout=20)
    assert r.status_code in (200, 201), r.text[:300]
    body = r.json()
    assert body.get("created") is False, "Should have been deduped"
    sup = body.get("supplier") or {}
    # Returned vendor should match original casing (the one already on list)
    assert sup.get("name", "").lower() == unique_vendor.lower()


# ---- PO submission end-to-end ----
@pytest.fixture(scope="module")
def active_job():
    r = requests.get(f"{API}/jobs", timeout=20)
    items = r.json().get("items") or []
    assert items
    return items[0]


def test_po_submit_with_consolidated_vendor(active_job, unique_vendor, headers):
    payload = {
        "project_number": active_job["project_number"],
        "vendor": unique_vendor,
        "description": "Test PO iter245 — consolidation",
        "estimated_amount": 25.50,
        "category": "Materials",
        "urgency": "Normal",
        "supervisor_signature": "Iter245 Tester",
    }
    r = requests.post(f"{API}/po-requests", json=payload, headers=headers, timeout=20)
    assert r.status_code in (200, 201), f"PO create failed: {r.status_code} {r.text[:300]}"
    po = r.json()
    po_id = po.get("id")
    assert po_id, "Created PO missing id"
    assert po.get("vendor", "").lower() == unique_vendor.lower()
    assert po.get("project_number") == active_job["project_number"]

    # GET back to verify persistence
    time.sleep(0.5)
    g = requests.get(f"{API}/po-requests/{po_id}", headers=headers, timeout=20)
    assert g.status_code == 200, g.text[:300]
    got = g.json()
    assert got["vendor"] == po["vendor"]
    assert got["project_number"] == active_job["project_number"]
    assert got["description"] == payload["description"]


def test_po_validation_missing_fields(headers):
    # Missing description
    r = requests.post(f"{API}/po-requests",
                      json={"project_number": "X", "vendor": "Y"},
                      headers=headers, timeout=20)
    assert r.status_code in (400, 422), r.text[:300]
