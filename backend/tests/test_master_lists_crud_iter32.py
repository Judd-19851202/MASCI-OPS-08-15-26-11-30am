"""Iter 32 — Single-row CRUD on master lists.

Verifies the new endpoints added so admins/PMs/(shop, where applicable)
can add, edit, and delete one row at a time on:
  - employees       (admin / PM)
  - suppliers       (admin / PM)
  - equipment-master (admin / PM / shop)

The bulk-replace XLSX upload paths already had coverage; this iter is
focused on the per-row inline path.
"""
import os
import uuid
from pathlib import Path

import pytest
import requests


def _read_env(key: str) -> str:
    p = Path("/app/backend/.env")
    if not p.exists():
        return ""
    for line in p.read_text().splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip().strip('"')
    return ""


BASE = os.environ.get(
    "REACT_APP_BACKEND_URL",
    "https://safety-audit-mobile-1.preview.emergentagent.com",
).rstrip("/")
API = f"{BASE}/api"
ADMIN_PWD = os.environ.get("ADMIN_PASSWORD") or _read_env("ADMIN_PASSWORD") or "MASCI1982!"
PM_PWD = os.environ.get("PM_PASSWORD") or _read_env("PM_PASSWORD") or "Happy123!"
SHOP_PWD = os.environ.get("SHOP_PASSWORD") or _read_env("SHOP_PASSWORD") or "Nothappy123!"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{API}/admin/login", json={"password": ADMIN_PWD}, timeout=15)
    return r.json()["token"]


@pytest.fixture(scope="module")
def pm_token():
    r = requests.post(f"{API}/pm/login", json={"password": PM_PWD}, timeout=15)
    return r.json()["token"]


@pytest.fixture(scope="module")
def shop_token():
    r = requests.post(f"{API}/shop/login", json={"password": SHOP_PWD}, timeout=15)
    return r.json().get("token", "")


# ---------- Employees ----------
def test_employee_full_crud(admin_token):
    h = {"X-Admin-Token": admin_token}
    name = f"PYTEST {uuid.uuid4().hex[:6]}"
    # Create
    r = requests.post(f"{API}/admin/employees", json={"name": name, "trade": "Operator"}, headers=h, timeout=15)
    assert r.status_code in (200, 201), r.text
    eid = r.json().get("id")
    assert eid
    # Update
    r = requests.put(f"{API}/admin/employees/{eid}", json={"trade": "Foreman"}, headers=h, timeout=15)
    assert r.status_code == 200, r.text
    assert r.json()["trade"] == "Foreman"
    # Required-name guard
    r = requests.put(f"{API}/admin/employees/{eid}", json={"name": "  "}, headers=h, timeout=15)
    assert r.status_code == 400
    # Delete
    r = requests.delete(f"{API}/admin/employees/{eid}", headers=h, timeout=15)
    assert r.status_code == 200
    # 404 after delete
    r = requests.put(f"{API}/admin/employees/{eid}", json={"trade": "x"}, headers=h, timeout=15)
    assert r.status_code == 404


def test_employee_pm_can_edit(pm_token, admin_token):
    """PM token can edit too (relaxed require_admin)."""
    h_admin = {"X-Admin-Token": admin_token, "X-PM-Token": ""}
    h_pm = {"X-PM-Token": pm_token, "X-Admin-Token": ""}
    name = f"PYTEST {uuid.uuid4().hex[:6]}"
    eid = requests.post(f"{API}/admin/employees", json={"name": name}, headers=h_admin, timeout=15).json()["id"]
    try:
        r = requests.put(f"{API}/admin/employees/{eid}", json={"trade": "PM-edited"}, headers=h_pm, timeout=15)
        assert r.status_code == 200
        assert r.json()["trade"] == "PM-edited"
    finally:
        requests.delete(f"{API}/admin/employees/{eid}", headers=h_admin, timeout=15)


# ---------- Suppliers ----------
def test_supplier_edit_and_active_toggle(admin_token):
    h = {"X-Admin-Token": admin_token}
    name = f"PYTEST {uuid.uuid4().hex[:6]}"
    sid = requests.post(f"{API}/admin/suppliers", json={"name": name}, headers=h, timeout=15).json()["id"]
    try:
        r = requests.put(f"{API}/admin/suppliers/{sid}", json={"is_active": False}, headers=h, timeout=15)
        assert r.status_code == 200
        assert r.json()["is_active"] is False
        r = requests.put(f"{API}/admin/suppliers/{sid}", json={"name": "  "}, headers=h, timeout=15)
        assert r.status_code == 400
    finally:
        requests.delete(f"{API}/admin/suppliers/{sid}", headers=h, timeout=15)


# ---------- Equipment Master ----------
def test_equipment_master_full_crud(admin_token):
    h = {"X-Admin-Token": admin_token}
    unit = f"PYTEST-{uuid.uuid4().hex[:6]}"
    payload = {
        "unit_number": unit,
        "year": "2025",
        "make": "PyMake",
        "model": "Mod-1",
        "category": "Misc Equipment",
        "preop_equipment_type": "Other",
    }
    r = requests.post(f"{API}/admin/equipment-master", json=payload, headers=h, timeout=15)
    assert r.status_code in (200, 201), r.text
    new = r.json()
    assert new["unit_number"] == unit
    # Duplicate guard
    r = requests.post(f"{API}/admin/equipment-master", json=payload, headers=h, timeout=15)
    assert r.status_code == 409
    # Update by unit_number key
    r = requests.put(f"{API}/admin/equipment-master/{unit}", json={"comments": "edited"}, headers=h, timeout=15)
    assert r.status_code == 200
    assert r.json()["comments"] == "edited"
    # Delete
    r = requests.delete(f"{API}/admin/equipment-master/{unit}", headers=h, timeout=15)
    assert r.status_code == 200
    # 404 after delete
    r = requests.delete(f"{API}/admin/equipment-master/{unit}", headers=h, timeout=15)
    assert r.status_code == 404


def test_equipment_master_shop_can_crud(shop_token, admin_token):
    """Mechanics need to add/edit/delete units they're servicing."""
    if not shop_token:
        pytest.skip("Shop login not configured")
    h_shop = {"X-Shop-Token": shop_token, "X-Admin-Token": ""}
    h_admin = {"X-Admin-Token": admin_token}
    unit = f"PYTEST-SHOP-{uuid.uuid4().hex[:6]}"
    r = requests.post(
        f"{API}/admin/equipment-master",
        json={"unit_number": unit, "make": "ShopMake"},
        headers=h_shop,
        timeout=15,
    )
    assert r.status_code in (200, 201), r.text
    try:
        r = requests.put(
            f"{API}/admin/equipment-master/{unit}",
            json={"comments": "shop-edited"},
            headers=h_shop,
            timeout=15,
        )
        assert r.status_code == 200
        assert r.json()["comments"] == "shop-edited"
    finally:
        requests.delete(f"{API}/admin/equipment-master/{unit}", headers=h_admin, timeout=15)
