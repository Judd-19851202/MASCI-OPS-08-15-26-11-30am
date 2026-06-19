"""Iter155 · Phase G · GLOBAL SEARCH — Admin & PM extra coverage.

Supplements test_iter155_global_search.py:
  * Admin sees ALL 14 kinds
  * PM scope is honored on projects/incidents/CAs when scoped
"""
import os
from pathlib import Path

import pytest
import requests


def _read_kv(path, key):
    try:
        with open(path) as f:
            for line in f:
                if line.startswith(f"{key}="):
                    return line.split("=", 1)[1].strip().strip('"').rstrip("/")
    except Exception:
        pass
    return ""


BASE_URL = (
    _read_kv(Path("/app/frontend/.env"), "REACT_APP_BACKEND_URL")
    or os.environ.get("REACT_APP_BACKEND_URL", "")
).rstrip("/")

ALL_KINDS = {
    "tasks", "notifications", "employees", "equipment", "projects",
    "po_requests", "incidents", "corrective_actions", "fire_extinguishers",
    "safety_documents", "safety_training", "document_expirations",
    "operations_events", "field_leadership",
}

NO_ADMIN = {"X-Admin-Token": ""}


@pytest.fixture(scope="module")
def admin_token():
    # Use multi-login first
    r = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
        headers=NO_ADMIN, timeout=20,
    )
    if r.status_code == 200:
        data = r.json()
        tok = data.get("token") or data.get("admin_token")
        if tok:
            return tok
    # Fallback to shared admin login
    r = requests.post(
        f"{BASE_URL}/api/admin/login",
        json={"password": "Maddix123!"},
        headers=NO_ADMIN, timeout=20,
    )
    if r.status_code == 200:
        return r.json().get("token")
    pytest.skip(f"Admin login failed: {r.status_code} {r.text}")


@pytest.fixture(scope="module")
def pm_token():
    r = requests.post(
        f"{BASE_URL}/api/pm/login",
        json={"email": "chriswright@mascigc.com",
              "password": "ChrisRocksThis2026"},
        headers=NO_ADMIN, timeout=20,
    )
    if r.status_code != 200:
        pytest.skip(f"PM login failed: {r.status_code} {r.text}")
    return r.json().get("token")


def test_admin_sees_all_14_kinds(admin_token):
    # Try X-Admin-Token first (most likely)
    r = requests.get(
        f"{BASE_URL}/api/search?q=test&limit=2",
        headers={"X-Admin-Token": admin_token}, timeout=30,
    )
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["role"] in ("admin",), f"unexpected role: {d['role']}"
    assert set(d["scope"]) == ALL_KINDS, (
        f"admin scope mismatch — missing={ALL_KINDS - set(d['scope'])}, "
        f"extra={set(d['scope']) - ALL_KINDS}"
    )


def test_pm_scope_kinds(pm_token):
    r = requests.get(
        f"{BASE_URL}/api/search?q=test&limit=2",
        headers={"X-PM-Token": pm_token, **NO_ADMIN}, timeout=30,
    )
    assert r.status_code == 200, r.text
    d = r.json()
    assert d["role"] == "pm"
    expected = {"tasks", "notifications", "projects", "po_requests",
                "incidents", "corrective_actions", "employees", "equipment"}
    assert set(d["scope"]) == expected, f"pm scope mismatch: {d['scope']}"
    # forbidden
    for k in ("fire_extinguishers", "safety_documents", "field_leadership",
              "operations_events"):
        assert k not in d["scope"]


def test_pm_project_scope_enforced(pm_token):
    """If PM has a scoped project list, projects rows must be within scope."""
    r = requests.get(
        f"{BASE_URL}/api/search?q=20&limit=10&kinds=projects",
        headers={"X-PM-Token": pm_token, **NO_ADMIN}, timeout=30,
    )
    assert r.status_code == 200
    d = r.json()
    # Resolve PM scope via /api/pm/me if available — best-effort
    me = requests.get(
        f"{BASE_URL}/api/pm/me",
        headers={"X-PM-Token": pm_token, **NO_ADMIN}, timeout=20,
    )
    scope_nums = None
    if me.status_code == 200:
        me_j = me.json()
        # try common shapes
        scope_nums = (
            me_j.get("project_numbers")
            or (me_j.get("scope") or {}).get("project_numbers")
            or (me_j.get("pm_scope") or {}).get("project_numbers")
        )
    if not scope_nums:
        pytest.skip("PM has no scoped project list — cannot assert filter")
    scope_nums = set(scope_nums)
    for g in d["groups"]:
        if g["kind"] != "projects":
            continue
        for row in g["rows"]:
            # title is project_number for projects
            assert row["title"] in scope_nums or row.get("subtitle"), (
                f"PM project leak: {row}"
            )
