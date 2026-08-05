"""WP-18C2 Project Controls Authority endpoint smoke tests."""

import os
import uuid

import pytest
import requests


BASE_URL = os.environ.get("LOCAL_BACKEND_URL", "http://127.0.0.1:8001").rstrip("/")
PREVIEW_BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://masci-audit-hub.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"
PM_EMAIL = "cert.pm@example.com"
PM_PASSWORD = "CertProof2026!"
ASSIGNED_PROJECT = "ZZ-RUNTIME-CERT-2026"


def _multi_login(email: str, password: str) -> dict:
    last_response = None
    for api_base in (BASE_URL, PREVIEW_BASE_URL):
        response = requests.post(
            f"{api_base}/api/auth/multi-login",
            json={"email": email, "password": password},
            headers={"X-Device-Id": f"wp18c2-{uuid.uuid4().hex[:8]}"},
            timeout=60,
        )
        if response.status_code == 200:
            return response.json()
        last_response = response
    assert last_response is not None
    last_response.raise_for_status()
    raise AssertionError("multi-login did not return 200")


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
    session.headers.update(
        {
            "Content-Type": "application/json",
            "X-Directory-Token": directory["session_token"],
            "X-PM-Token": directory["portal_tokens"]["pm"],
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
    items = payload if isinstance(payload, list) else (payload.get("items") or [])
    assert isinstance(items, list)
    if items:
        detail = admin_session.get(f"{BASE_URL}/api/daily-reports/{items[0]['id']}", timeout=60)
        assert detail.status_code == 200
        doc = detail.json()
        assert "work_blocks" in doc or "work_block_summary" in doc
