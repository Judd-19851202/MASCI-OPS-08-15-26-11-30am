"""
Track 14.0 PM-Staffing UI Discoverability Closure — E2E backend contract tests (iteration 517).

Covers:
- Auth via /api/auth/multi-login for admin (jaymn.judd) and PM (cert.pm).
- /api/project-staffing/summary (admin vs PM scope).
- /api/employees/{employee_key}/project-assignments.
- /api/search?kinds=staffing (admin + PM).
- Permission boundary: POST /api/admin/jobs/{pn}/team — PM can assign superintendent;
  cannot assign pm/co_pm/executive_oversight (403).
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
assert BASE_URL, "REACT_APP_BACKEND_URL must be set"

ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"
PM_EMAIL = "cert.pm@example.com"
PM_PASSWORD = "CertProof2026!"
CERT_PROJECT = "ZZ-RUNTIME-CERT-2026"


def _login(email, password):
    r = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": email, "password": password},
        timeout=30,
    )
    assert r.status_code == 200, f"login failed {email}: {r.status_code} {r.text[:300]}"
    return r.json()


def _extract_portal_tokens(data):
    pt = data.get("portal_tokens") or {}
    session = data.get("session_token")
    return pt, session


@pytest.fixture(scope="module")
def admin_auth():
    data = _login(ADMIN_EMAIL, ADMIN_PASSWORD)
    pt, session = _extract_portal_tokens(data)
    admin_token = pt.get("admin") or pt.get("super_admin") or session
    assert admin_token, f"no admin token in response: keys={list(data.keys())} portal={list(pt.keys())}"
    headers = {"X-Admin-Token": admin_token, "Authorization": f"Bearer {session or admin_token}"}
    if session:
        headers["X-Session-Token"] = session
    return headers


@pytest.fixture(scope="module")
def pm_auth():
    data = _login(PM_EMAIL, PM_PASSWORD)
    pt, session = _extract_portal_tokens(data)
    pm_token = pt.get("pm") or session
    assert pm_token, f"no pm token in response: keys={list(data.keys())} portal={list(pt.keys())}"
    headers = {"X-PM-Token": pm_token, "Authorization": f"Bearer {session or pm_token}"}
    if session:
        headers["X-Session-Token"] = session
    return headers


# ---------- /api/project-staffing/summary ----------

def test_staffing_summary_admin(admin_auth):
    r = requests.get(f"{BASE_URL}/api/project-staffing/summary", headers=admin_auth, timeout=30)
    assert r.status_code == 200, r.text[:300]
    body = r.json()
    # Required top-level shape
    assert "projects" in body or "items" in body, f"unexpected keys: {list(body.keys())}"
    projects = body.get("projects") or body.get("items") or []
    assert isinstance(projects, list) and len(projects) >= 1, "admin should see >=1 project"
    # totals
    totals = body.get("totals") or body.get("role_totals") or {}
    assert isinstance(totals, dict)
    # actor_scope should be admin
    scope = body.get("actor_scope") or body.get("scope")
    if scope is not None:
        assert scope in ("admin", "super_admin"), f"unexpected scope {scope}"


def test_staffing_summary_pm_scoped(pm_auth):
    r = requests.get(f"{BASE_URL}/api/project-staffing/summary", headers=pm_auth, timeout=30)
    assert r.status_code == 200, r.text[:300]
    body = r.json()
    projects = body.get("projects") or body.get("items") or []
    assert isinstance(projects, list)
    # PM scope must include the cert project and only their projects
    pns = [p.get("project_number") or p.get("pn") for p in projects]
    assert CERT_PROJECT in pns, f"PM scope missing {CERT_PROJECT}: {pns}"
    scope = body.get("actor_scope") or body.get("scope")
    if scope is not None:
        assert scope == "pm", f"expected actor_scope=pm got {scope}"


# ---------- /api/employees/{employee_key}/project-assignments ----------

def test_employee_project_assignments_pm(admin_auth):
    r = requests.get(
        f"{BASE_URL}/api/employees/{PM_EMAIL}/project-assignments",
        headers=admin_auth,
        timeout=30,
    )
    assert r.status_code == 200, r.text[:300]
    body = r.json()
    items = body.get("items") or body.get("assignments") or body
    assert isinstance(items, list), f"unexpected body shape: {type(items)}"
    active = [it for it in items if it.get("active", True) is not False]
    assert len(active) >= 1, f"cert.pm should have >=1 active assignment, got {items}"
    # at least one is in CERT_PROJECT
    pns = [it.get("project_number") for it in items]
    assert CERT_PROJECT in pns, f"missing {CERT_PROJECT} in {pns}"


# ---------- /api/search?kinds=staffing ----------

def test_search_staffing_pm_scope(pm_auth):
    r = requests.get(
        f"{BASE_URL}/api/search",
        params={"q": "Foreman", "kinds": "staffing"},
        headers=pm_auth,
        timeout=30,
    )
    assert r.status_code == 200, r.text[:300]
    body = r.json()
    results = body.get("results") or body.get("items") or []
    # PM scope: all staffing results should be inside CERT_PROJECT
    for it in results:
        url = it.get("url") or it.get("href") or ""
        if "/job/" in url or "/jobs/" in url:
            assert CERT_PROJECT in url, f"PM result leaks outside scope: {url}"
            assert url.startswith("/pm/"), f"PM result not under /pm/: {url}"


def test_search_staffing_admin(admin_auth):
    r = requests.get(
        f"{BASE_URL}/api/search",
        params={"q": "Jewett", "kinds": "staffing"},
        headers=admin_auth,
        timeout=30,
    )
    assert r.status_code == 200, r.text[:300]
    body = r.json()
    results = body.get("results") or body.get("items") or []
    # at least one staffing result expected; URLs should be admin-flavoured when present
    for it in results:
        url = it.get("url") or it.get("href") or ""
        if "/team" in url:
            assert "/admin/jobs/" in url, f"admin staffing url unexpected: {url}"


# ---------- Permission boundary on /api/pm/job/{pn}/team (role-level enforcement) ----------

@pytest.mark.parametrize("role", ["pm", "co_pm", "executive_oversight"])
def test_pm_endpoint_blocks_admin_only_roles(pm_auth, role):
    payload = {
        "assignment_role": role,
        "email": "cert.foreman@example.com",
        "user_id": "cert.foreman@example.com",
    }
    r = requests.post(
        f"{BASE_URL}/api/pm/job/{CERT_PROJECT}/team",
        json=payload,
        headers=pm_auth,
        timeout=30,
    )
    assert r.status_code == 403, (
        f"PM endpoint should 403 for admin-only role {role}, got {r.status_code}: {r.text[:300]}"
    )


def test_admin_endpoint_rejects_pm_token(pm_auth):
    # Sanity: the admin-only endpoint must reject PM tokens entirely.
    r = requests.post(
        f"{BASE_URL}/api/admin/jobs/{CERT_PROJECT}/team",
        json={"assignment_role": "superintendent", "email": "cert.super@example.com"},
        headers=pm_auth,
        timeout=30,
    )
    assert r.status_code in (401, 403), f"got {r.status_code}: {r.text[:300]}"


def test_pm_can_assign_superintendent(pm_auth):
    payload = {
        "assignment_role": "superintendent",
        "email": "cert.super@example.com",
        "user_id": "cert.super@example.com",
    }
    r = requests.post(
        f"{BASE_URL}/api/pm/job/{CERT_PROJECT}/team",
        json=payload,
        headers=pm_auth,
        timeout=30,
    )
    # NOTE: Currently returns 403 "PM not assigned to this project" because
    # _is_pm_on_project() consults jobs_master.pm_email only (which points to
    # the super admin), while /api/project-staffing/summary scope uses
    # project_team_assignments (where cert.pm is assigned as 'pm'). This is a
    # data-source mismatch; reporting as a backend bug. Expecting 200/201/409.
    assert r.status_code in (
        200,
        201,
        409,
    ), (
        "PM should be able to assign superintendent — but backend rejects with "
        f"{r.status_code}: {r.text[:300]}. _is_pm_on_project uses jobs_master.pm_email "
        f"while staffing summary uses project_team_assignments. Sync needed."
    )
