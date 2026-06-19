"""Iter 34 — Master-list XLSX export round-trip.

Verifies one-click XLSX download for every master list. Each download:
  - Returns 200
  - Sends a Content-Disposition with a sensible filename
  - Is a valid XLSX (zipfile.is_zipfile()).
"""
import io
import os
import zipfile
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
ADMIN_PWD = os.environ.get("ADMIN_PASSWORD") or _read_env("ADMIN_PASSWORD") or "Maddix123!"
PM_PWD = os.environ.get("PM_PASSWORD") or _read_env("PM_PASSWORD") or "Maddix123!"


@pytest.fixture(scope="module")
def admin_token():
    return requests.post(f"{API}/admin/login", json={"password": ADMIN_PWD}, timeout=15).json()["token"]


@pytest.fixture(scope="module")
def pm_token():
    return requests.post(f"{API}/pm/login", json={"password": PM_PWD}, timeout=15).json()["token"]


@pytest.mark.parametrize(
    "path,expected_filename_prefix",
    [
        ("/admin/employees/export", "MASCI_employees"),
        ("/admin/suppliers/export", "MASCI_suppliers"),
        ("/admin/equipment-master/export", "MASCI_equipment"),
        ("/admin/equipment-parts/export", "MASCI_parts"),
        ("/admin/jobs/export", "MASCI_jobs"),
        ("/admin/project-managers/export", "MASCI_pms"),
    ],
)
def test_export_returns_valid_xlsx(admin_token, path, expected_filename_prefix):
    r = requests.get(f"{API}{path}", headers={"X-Admin-Token": admin_token}, timeout=20)
    assert r.status_code == 200, r.text
    cd = r.headers.get("content-disposition", "")
    assert expected_filename_prefix in cd
    # Valid XLSX = is_zipfile + has [Content_Types].xml
    buf = io.BytesIO(r.content)
    assert zipfile.is_zipfile(buf), f"{path} did not return a valid xlsx"
    with zipfile.ZipFile(buf) as z:
        assert "[Content_Types].xml" in z.namelist()


def test_export_works_with_pm_token(pm_token):
    """PMs can also export — same office workflow."""
    r = requests.get(
        f"{API}/admin/employees/export",
        headers={"X-PM-Token": pm_token, "X-Admin-Token": ""},
        timeout=20,
    )
    assert r.status_code == 200
    assert zipfile.is_zipfile(io.BytesIO(r.content))


def test_export_blocked_without_token():
    r = requests.get(
        f"{API}/admin/employees/export",
        headers={"X-Admin-Token": "", "X-PM-Token": ""},
        timeout=15,
    )
    assert r.status_code == 401
