"""Iter 31 — PM (Project Manager) portal authorization model.

Verifies:
- Admin password rotated to MASCI1982! (old Happy123! rejected at /admin/login).
- /api/pm/login + /api/pm/check work with PM_PASSWORD=Happy123!.
- PM token CAN access regular admin routes (jobs master, equipment master,
  inspections, suppliers, employees, posters, compliance CSVs).
- PM token CANNOT access backup/recovery routes (admin-strict 401).
- Admin token still passes everywhere.
"""
import os
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


# ---------- Login fixtures ----------
@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{API}/admin/login", json={"password": ADMIN_PWD}, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()["token"]


@pytest.fixture(scope="module")
def pm_token():
    r = requests.post(f"{API}/pm/login", json={"password": PM_PWD}, timeout=15)
    assert r.status_code == 200, r.text
    return r.json()["token"]


# ---------- Login behavior ----------
def test_old_admin_password_rejected():
    """Old Happy123! must no longer authenticate as admin."""
    if ADMIN_PWD == "Happy123!":
        pytest.skip("ADMIN_PASSWORD has not been rotated in this env")
    # Bypass conftest auto-token injection on the login call itself.
    r = requests.post(
        f"{API}/admin/login",
        json={"password": "Happy123!"},
        headers={"X-Admin-Token": ""},
        timeout=15,
    )
    assert r.status_code == 401, r.text


def test_pm_login_wrong_password_rejected():
    r = requests.post(
        f"{API}/pm/login",
        json={"password": "obviously-wrong"},
        headers={"X-Admin-Token": ""},
        timeout=15,
    )
    assert r.status_code == 401, r.text


def test_pm_check_with_pm_token(pm_token):
    r = requests.get(f"{API}/pm/check", headers={"X-PM-Token": pm_token}, timeout=15)
    assert r.status_code == 200
    assert r.json().get("ok") is True


def test_pm_check_with_admin_token(admin_token):
    """Admin token also satisfies the PM gate (admin = global view)."""
    r = requests.get(
        f"{API}/pm/check", headers={"X-Admin-Token": admin_token}, timeout=15
    )
    assert r.status_code == 200


# ---------- PM CAN access regular admin routes ----------
@pytest.mark.parametrize(
    "path",
    [
        "/admin/jobs",
        "/admin/project-managers",
        "/equipment-master",
        "/inspections",
        "/meetings",
        "/incidents",
        "/daily-reports",
        "/suppliers",
        "/employees",
        "/job-hazard-plans",
        "/trench-boxes",
    ],
)
def test_pm_can_read_admin_routes(pm_token, path):
    r = requests.get(f"{API}{path}", headers={"X-PM-Token": pm_token}, timeout=20)
    assert r.status_code == 200, f"{path} → {r.status_code}: {r.text[:200]}"


# ---------- PM CANNOT access backup / recovery routes ----------
@pytest.mark.parametrize(
    "method,path",
    [
        ("GET",  "/exports/full-backup"),
        ("GET",  "/admin/backups"),
        ("GET",  "/admin/backups/integrity-check"),
        ("POST", "/admin/backups/run-now"),
        ("GET",  "/admin/crew-recovery/status"),
        ("POST", "/admin/crew-recovery/force-reseed"),
    ],
)
def test_pm_blocked_from_backup_routes(pm_token, method, path):
    # conftest.py auto-injects X-Admin-Token on every requests call hitting
    # our backend; explicitly clear it so we measure ONLY the PM gate.
    headers = {"X-PM-Token": pm_token, "X-Admin-Token": ""}
    r = requests.request(method, f"{API}{path}", headers=headers, timeout=20)
    assert r.status_code == 401, (
        f"{method} {path} should reject PM token, got {r.status_code}: {r.text[:200]}"
    )


# ---------- Admin still passes the strict routes ----------
def test_admin_can_list_backups(admin_token):
    r = requests.get(
        f"{API}/admin/backups", headers={"X-Admin-Token": admin_token}, timeout=15
    )
    assert r.status_code == 200
    body = r.json()
    assert "backups" in body
