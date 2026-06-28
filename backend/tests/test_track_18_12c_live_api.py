"""TRACK 18.12C live API regression — dispatch session access + admin-only walls."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://safety-audit-mobile-1.preview.emergentagent.com").rstrip("/")
DISPATCH_EMAIL = "dispatch@mascigc.com"
DISPATCH_PW = "DispatchTest2026!"
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PW = "Maddix123!"


@pytest.fixture(scope="module")
def dispatch_token():
    r = requests.post(f"{BASE_URL}/api/dispatch/login",
                      json={"email": DISPATCH_EMAIL, "password": DISPATCH_PW}, timeout=30)
    assert r.status_code == 200, f"dispatch login failed: {r.status_code} {r.text[:200]}"
    return r.json()["token"]


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/multi-login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PW}, timeout=30)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text[:200]}"
    return r.json()["portal_tokens"]["admin"]


def _h_dispatch(t):
    return {"X-Dispatch-Token": t}


def _h_both(at, dt):
    return {"X-Admin-Token": at, "X-Dispatch-Token": dt}


# --- DISPATCH must reach OPS-GUARD workspaces ---
OPS_GUARD_ENDPOINTS = [
    "/api/admin/transportation/carriers",
    "/api/admin/transportation/persons",
    "/api/admin/transportation/trucks",
    "/api/admin/transportation/documents/queue",
    "/api/admin/transportation/inspections/queue",
    "/api/admin/transportation/orientation/dashboard",
    "/api/admin/transportation/orientation/modules",
    "/api/admin/transportation/orientation/assignments",
    "/api/admin/transportation/orientation/certificates",
    "/api/admin/transportation/automation/actions",
    "/api/admin/transportation/automation/forecast",
    "/api/admin/transportation/intelligence/cleanup-signals",
    "/api/admin/transportation/compliance/summary",
]


@pytest.mark.parametrize("path", OPS_GUARD_ENDPOINTS)
def test_dispatch_can_access_ops_guard(dispatch_token, path):
    r = requests.get(f"{BASE_URL}{path}", headers=_h_dispatch(dispatch_token), timeout=30)
    # 200 = real data; 404 = endpoint typo; we accept 200 strictly
    assert r.status_code == 200, f"{path} -> {r.status_code} {r.text[:200]}"


# --- ADMIN-STRICT endpoints must reject dispatch token ---
ADMIN_STRICT_ENDPOINTS = [
    "/api/admin/transportation/audit-timeline",
    "/api/admin/transportation/intelligence/dashboard",
    "/api/admin/transportation/intelligence/recommendations",
    "/api/admin/transportation/intelligence/predictions",
    "/api/admin/transportation/intelligence/dispatch-learning",
    "/api/admin/transportation/email-routes",
    "/api/admin/transportation/hr-sync",
]


@pytest.mark.parametrize("path", ADMIN_STRICT_ENDPOINTS)
def test_admin_strict_rejects_dispatch_token(dispatch_token, path):
    r = requests.get(f"{BASE_URL}{path}", headers=_h_dispatch(dispatch_token), timeout=30)
    assert r.status_code in (401, 403), f"{path} should reject dispatch, got {r.status_code}: {r.text[:200]}"
    body = r.text.lower()
    assert "admin" in body or "login" in body or "forbidden" in body or "unauthorized" in body, (
        f"{path} response missing admin-required signal: {r.text[:200]}"
    )


# --- ADMIN must reach both OPS-GUARD AND admin-strict endpoints ---
@pytest.mark.parametrize("path", OPS_GUARD_ENDPOINTS + ADMIN_STRICT_ENDPOINTS)
def test_admin_can_access_all(admin_token, path):
    r = requests.get(f"{BASE_URL}{path}", headers={"X-Admin-Token": admin_token}, timeout=30)
    assert r.status_code == 200, f"admin denied at {path}: {r.status_code} {r.text[:200]}"


# --- Data magnitude sanity (real data, not restricted stubs) ---
def test_dispatch_drivers_real_data(dispatch_token):
    r = requests.get(f"{BASE_URL}/api/admin/transportation/persons",
                     headers=_h_dispatch(dispatch_token), timeout=30)
    assert r.status_code == 200
    data = r.json()
    rows = data.get("rows") or data.get("items") or data
    assert isinstance(rows, list) and len(rows) >= 1, f"expected drivers, got {len(rows) if isinstance(rows, list) else type(rows)}"


def test_dispatch_carriers_real_data(dispatch_token):
    r = requests.get(f"{BASE_URL}/api/admin/transportation/carriers",
                     headers=_h_dispatch(dispatch_token), timeout=30)
    assert r.status_code == 200
    data = r.json()
    rows = data.get("rows") or data.get("items") or data
    assert isinstance(rows, list) and len(rows) >= 1


def test_dispatch_trucks_real_data(dispatch_token):
    r = requests.get(f"{BASE_URL}/api/admin/transportation/trucks",
                     headers=_h_dispatch(dispatch_token), timeout=30)
    assert r.status_code == 200
    data = r.json()
    rows = data.get("rows") or data.get("items") or data
    assert isinstance(rows, list) and len(rows) >= 1
