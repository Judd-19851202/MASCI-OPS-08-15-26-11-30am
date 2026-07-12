"""Iter 33 — Soft-delete + 14-day archive + restore.

Verifies the new safety net behind every 🗑️ button on the master lists:
  - Employees, Suppliers, Equipment Master, Jobs Master.

Each row that gets deleted is hidden from the active list, surfaced in
the /archive endpoint, and recoverable via the /restore endpoint. The
hard-purge is best-effort on every list call (skipped here — the sweep
window is 14 days, but we exercise the round-trip).
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
    "https://backup-forensics.preview.emergentagent.com",
).rstrip("/")
API = f"{BASE}/api"
ADMIN_PWD = os.environ.get("ADMIN_PASSWORD") or _read_env("ADMIN_PASSWORD") or "Maddix123!"


@pytest.fixture(scope="module")
def tok():
    r = requests.post(f"{API}/admin/login", json={"password": ADMIN_PWD}, timeout=15)
    return r.json()["token"]


def _h(tok):
    return {"X-Admin-Token": tok}


# ---------- Employees ----------
def test_employee_soft_delete_archive_restore(tok):
    h = _h(tok)
    # Add
    name = f"SD {uuid.uuid4().hex[:6]}"
    eid = requests.post(f"{API}/admin/employees", json={"name": name}, headers=h, timeout=15).json()["id"]
    # Delete -> soft
    r = requests.delete(f"{API}/admin/employees/{eid}", headers=h, timeout=15)
    assert r.status_code == 200
    body = r.json()
    assert body.get("soft_deleted") is True
    assert body.get("retain_days") == 14
    # Active list excludes
    active = requests.get(f"{API}/employees", timeout=15).json().get("items", [])
    assert not any(x["id"] == eid for x in active)
    # Archive includes
    arch = requests.get(f"{API}/admin/employees/archive", headers=h, timeout=15).json().get("items", [])
    assert any(x["id"] == eid for x in arch)
    # Restore
    r = requests.post(f"{API}/admin/employees/{eid}/restore", headers=h, timeout=15)
    assert r.status_code == 200
    assert r.json().get("name") == name
    # Active list contains again
    active = requests.get(f"{API}/employees", timeout=15).json().get("items", [])
    assert any(x["id"] == eid for x in active)
    # Cleanup -> back to archive
    requests.delete(f"{API}/admin/employees/{eid}", headers=h, timeout=15)


# ---------- Suppliers ----------
def test_supplier_soft_delete_archive_restore(tok):
    h = _h(tok)
    name = f"SD {uuid.uuid4().hex[:6]}"
    sid = requests.post(f"{API}/admin/suppliers", json={"name": name}, headers=h, timeout=15).json()["id"]
    requests.delete(f"{API}/admin/suppliers/{sid}", headers=h, timeout=15)
    # Active excludes
    active = requests.get(f"{API}/suppliers", timeout=15).json().get("items", [])
    assert not any(x["id"] == sid for x in active)
    # Archive includes
    arch = requests.get(f"{API}/admin/suppliers/archive", headers=h, timeout=15).json().get("items", [])
    assert any(x["id"] == sid for x in arch)
    # Restore
    r = requests.post(f"{API}/admin/suppliers/{sid}/restore", headers=h, timeout=15)
    assert r.status_code == 200
    requests.delete(f"{API}/admin/suppliers/{sid}", headers=h, timeout=15)


# ---------- Equipment Master ----------
def test_equipment_master_soft_delete_archive_restore(tok):
    h = _h(tok)
    unit = f"SD-{uuid.uuid4().hex[:6]}"
    requests.post(f"{API}/admin/equipment-master", json={"unit_number": unit, "make": "X"}, headers=h, timeout=15)
    requests.delete(f"{API}/admin/equipment-master/{unit}", headers=h, timeout=15)
    # Active excludes
    active = requests.get(f"{API}/equipment-master", timeout=15).json().get("items", [])
    assert not any(x.get("unit_number") == unit for x in active)
    # Archive includes
    arch = requests.get(f"{API}/admin/equipment-master/archive", headers=h, timeout=15).json().get("items", [])
    assert any(x.get("unit_number") == unit for x in arch)
    # Restore by unit_number key
    r = requests.post(f"{API}/admin/equipment-master/{unit}/restore", headers=h, timeout=15)
    assert r.status_code == 200
    # POST with same unit_number on a soft-deleted row should restore (not 409)
    requests.delete(f"{API}/admin/equipment-master/{unit}", headers=h, timeout=15)
    r = requests.post(f"{API}/admin/equipment-master", json={"unit_number": unit, "make": "X"}, headers=h, timeout=15)
    assert r.status_code in (200, 201), r.text
    requests.delete(f"{API}/admin/equipment-master/{unit}", headers=h, timeout=15)


# ---------- Jobs Master ----------
def test_jobs_soft_delete_archive_restore(tok):
    h = _h(tok)
    pn = f"SD-{uuid.uuid4().hex[:6]}"
    job = requests.post(
        f"{API}/admin/jobs",
        json={"project_number": pn, "project_name": "TEST_SD_test", "location": "Tville"},
        headers=h,
        timeout=15,
    ).json()
    jid = job["id"]
    r = requests.delete(f"{API}/admin/jobs/{jid}", headers=h, timeout=15)
    assert r.status_code == 200
    assert r.json().get("soft_deleted") is True
    # Active excludes
    active = requests.get(f"{API}/admin/jobs", headers=h, timeout=15).json().get("items", [])
    assert not any(x["id"] == jid for x in active)
    # Archive includes
    arch = requests.get(f"{API}/admin/jobs/archive", headers=h, timeout=15).json().get("items", [])
    assert any(x["id"] == jid for x in arch)
    # Restore
    r = requests.post(f"{API}/admin/jobs/{jid}/restore", headers=h, timeout=15)
    assert r.status_code == 200
    # Cleanup
    requests.delete(f"{API}/admin/jobs/{jid}", headers=h, timeout=15)


def test_archive_404_when_not_archived(tok):
    h = _h(tok)
    r = requests.post(f"{API}/admin/employees/no-such-id/restore", headers=h, timeout=15)
    assert r.status_code == 404
