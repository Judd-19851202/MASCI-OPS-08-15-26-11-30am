"""WP-18C2 Project Controls Authority endpoint smoke tests."""

import os

import pytest
import requests


BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"
PM_EMAIL = "cert.pm@example.com"
PM_PASSWORD = "CertProof2026!"
ASSIGNED_PROJECT = "ZZ-RUNTIME-CERT-2026"


def _multi_login(email: str, password: str) -> dict:
    response = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": email, "password": password},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


def _pm_login(email: str, password: str) -> dict:
    response = requests.post(
        f"{BASE_URL}/api/pm/login",
        json={"email": email, "password": password},
        timeout=60,
    )
    response.raise_for_status()
    return response.json()


@pytest.fixture
def admin_session():
    session = requests.Session()
    tokens = _multi_login(ADMIN_EMAIL, ADMIN_PASSWORD)
    session.headers.update(
        {
            "Content-Type": "application/json",
            "X-Directory-Token": tokens["session_token"],
            "X-Admin-Token": tokens["portal_tokens"]["admin"],
        }
    )
    yield session
    session.close()


@pytest.fixture
def pm_session():
    session = requests.Session()
    directory = _multi_login(PM_EMAIL, PM_PASSWORD)
    pm = _pm_login(PM_EMAIL, PM_PASSWORD)
    session.headers.update(
        {
            "Content-Type": "application/json",
            "X-Directory-Token": directory["session_token"],
            "X-PM-Token": pm["token"],
        }
    )
    yield session
    session.close()


def test_wp18c2_admin_overview(admin_session):
    response = admin_session.get(f"{BASE_URL}/api/admin/governance/project-controls/overview", timeout=60)
    assert response.status_code == 200
    payload = response.json()
    assert "summary" in payload
    assert payload["summary"]["enterprise_work_types"] >= 1


def test_wp18c2_admin_work_types(admin_session):
    response = admin_session.get(f"{BASE_URL}/api/admin/governance/project-controls/work-types", timeout=60)
    assert response.status_code == 200
    payload = response.json()
    assert payload["count"] >= 1


def test_wp18c2_pm_scope_denied_for_unassigned_project(pm_session):
    response = pm_session.get(
        f"{BASE_URL}/api/pm/project-controls/overview?project_number=NOT-ASSIGNED-001",
        timeout=60,
    )
    assert response.status_code == 403


def test_wp18c2_pm_project_surfaces(pm_session):
    endpoints = [
        f"/api/pm/project-controls/overview?project_number={ASSIGNED_PROJECT}",
        f"/api/pm/project-controls/projects/{ASSIGNED_PROJECT}/pay-items",
        f"/api/pm/project-controls/projects/{ASSIGNED_PROJECT}/mappings",
        f"/api/pm/project-controls/projects/{ASSIGNED_PROJECT}/lookahead",
        f"/api/pm/project-controls/projects/{ASSIGNED_PROJECT}/lifecycle",
        f"/api/pm/project-controls/projects/{ASSIGNED_PROJECT}/crew-intelligence",
        f"/api/pm/project-controls/projects/{ASSIGNED_PROJECT}/work-ledger?limit=5",
    ]
    for endpoint in endpoints:
        response = pm_session.get(f"{BASE_URL}{endpoint}", timeout=60)
        assert response.status_code == 200, endpoint


def test_wp18c2_daily_reports_include_work_blocks(admin_session):
    response = admin_session.get(f"{BASE_URL}/api/daily-reports?limit=5", timeout=60)
    assert response.status_code == 200
    payload = response.json()
    items = payload.get("items") or []
    assert isinstance(items, list)
    if items:
        assert "work_blocks" in items[0] or "work_block_summary" in items[0]
