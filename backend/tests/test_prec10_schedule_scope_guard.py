from __future__ import annotations

from pathlib import Path

import requests


def _read_env(path: str, key: str) -> str:
    for line in Path(path).read_text().splitlines():
        if line.startswith(f"{key}="):
            return line.split("=", 1)[1].strip().strip('"').strip("'")
    return ""


BASE_URL = _read_env("/app/frontend/.env", "REACT_APP_BACKEND_URL").rstrip("/")
PM_EMAIL = "pm.scope.forensic@example.com"
PM_PASSWORD = "ForensicPm2026!"
ALLOWED_PROJECTS = {"ZZ-FOR-ASSIGN-01", "ZZ-FOR-ASSIGN-02"}
FORBIDDEN_PROJECT = "ZZ-RUNTIME-CERT-2026"


def _pm_headers() -> dict:
    r = requests.post(
        f"{BASE_URL}/api/pm/login",
        json={"email": PM_EMAIL, "password": PM_PASSWORD},
        timeout=20,
    )
    assert r.status_code == 200, r.text
    token = r.json().get("token") or r.json().get("pm_token")
    assert token, "missing PM token"
    return {"X-PM-Token": token}


def test_pm_scope_selector_only_returns_assigned_projects():
    headers = _pm_headers()
    r = requests.get(f"{BASE_URL}/api/pm/jobs", headers=headers, timeout=20)
    assert r.status_code == 200, r.text
    body = r.json()
    rows = body.get("items") or []
    returned = {row.get("project_number") for row in rows}
    assert body.get("scope") == "pm_assigned"
    assert returned == ALLOWED_PROJECTS
    assert FORBIDDEN_PROJECT not in returned


def test_pm_schedule_overview_denies_unassigned_project():
    headers = _pm_headers()
    r = requests.get(
        f"{BASE_URL}/api/pm/project-controls/projects/{FORBIDDEN_PROJECT}/schedule/overview",
        headers=headers,
        timeout=20,
    )
    assert r.status_code == 403, r.text


def test_pm_schedule_overview_allows_assigned_project():
    headers = _pm_headers()
    r = requests.get(
        f"{BASE_URL}/api/pm/project-controls/projects/ZZ-FOR-ASSIGN-01/schedule/overview",
        headers=headers,
        timeout=20,
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["project"]["project_number"] == "ZZ-FOR-ASSIGN-01"
    assert "authority_boundaries" in body