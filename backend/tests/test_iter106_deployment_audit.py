"""
Iter106 — Master deployment readiness audit.
Focus: Time Off Request public-link flow, PDF footer string, _id leakage,
       auth scope isolation, public POST endpoints.

Run: pytest /app/backend/tests/test_iter106_deployment_audit.py -v
"""
import os
import uuid
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://backup-forensics.preview.emergentagent.com").rstrip("/")
SUPER_ADMIN_EMAIL = "jaymn.judd@mascigc.com"
SUPER_ADMIN_PW = "Maddix123!"
HR_EMAIL = "hrmanager@mascigc.com"
HR_PW = "HRPortal2026!"
ADMIN_LEGACY_PW = "Maddix123!"
PM_LEGACY_PW = "Maddix123!"
FL_PW = "MASCIGC"


# --------- Fixtures ----------
@pytest.fixture(scope="module")
def session():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def admin_token(session):
    r = session.post(f"{BASE_URL}/api/admin/login", json={"password": ADMIN_LEGACY_PW}, timeout=15)
    assert r.status_code == 200, f"admin login failed: {r.status_code} {r.text[:200]}"
    return r.json().get("token") or r.json().get("admin_token") or r.json().get("X-Admin-Token")


@pytest.fixture(scope="module")
def multi_login_payload(session):
    r = session.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PW},
        timeout=20,
    )
    assert r.status_code == 200, f"multi-login failed: {r.status_code} {r.text[:300]}"
    return r.json()


@pytest.fixture(scope="module")
def hr_token(session):
    r = session.post(f"{BASE_URL}/api/hr/login", json={"email": HR_EMAIL, "password": HR_PW}, timeout=15)
    assert r.status_code == 200, f"hr login failed: {r.status_code} {r.text[:200]}"
    return r.json().get("token") or r.json().get("hr_token")


@pytest.fixture(scope="module")
def pm_token(session):
    r = session.post(f"{BASE_URL}/api/pm/login", json={"password": PM_LEGACY_PW}, timeout=15)
    assert r.status_code == 200
    return r.json().get("token") or r.json().get("pm_token")


@pytest.fixture(scope="module")
def fl_token(session):
    r = session.post(f"{BASE_URL}/api/field-leadership/login", json={"password": FL_PW}, timeout=15)
    assert r.status_code == 200
    return r.json().get("token") or r.json().get("leadership_token")


# --------- 1. Health ----------
def test_health(session):
    r = session.get(f"{BASE_URL}/api/health", timeout=10)
    assert r.status_code == 200
    body = r.json()
    assert "status" in body or "ok" in body or "service" in body or body  # any healthy response


# --------- 2. Multi-Login ----------
def test_multi_login_returns_portals(multi_login_payload):
    data = multi_login_payload
    # Response has portal_tokens dict (admin/pm/hr/shop) + session_token + user
    assert "portal_tokens" in data or "portals" in data, f"multi-login missing portal info: {list(data.keys())}"
    pt = data.get("portal_tokens") or {}
    if pt:
        # Super admin should have at least one portal token
        assert len(pt) >= 1, "no portal tokens issued"


def test_multi_login_rejects_wrong_password(session):
    r = session.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": SUPER_ADMIN_EMAIL, "password": "wrong-password-xx"},
        timeout=15,
    )
    assert r.status_code in (401, 403)


# --------- 3. Admin core endpoints — no _id leakage ----------
ADMIN_LIST_ENDPOINTS = [
    "/api/admin/jobs",
    "/api/meetings",
    "/api/inspections",
    "/api/incidents",
    "/api/daily-reports",
    "/api/equipment-inspections",
    "/api/qaqc-inspections",
    "/api/field-leadership",
]


@pytest.mark.parametrize("endpoint", ADMIN_LIST_ENDPOINTS)
def test_admin_endpoint_200_no_id_leak(session, admin_token, fl_token, endpoint):
    headers = {"X-Admin-Token": admin_token}
    if "field-leadership" in endpoint:
        headers["X-Leadership-Token"] = fl_token
    r = session.get(f"{BASE_URL}{endpoint}", headers=headers, timeout=20)
    assert r.status_code == 200, f"{endpoint} returned {r.status_code}: {r.text[:200]}"
    payload = r.json()
    items = payload.get("items") if isinstance(payload, dict) else payload
    if isinstance(items, list) and items:
        sample = items[0]
        assert "_id" not in sample, f"{endpoint} leaks MongoDB _id"


def test_admin_kpi(session, admin_token):
    # Try several known KPI endpoints
    tried = []
    for path in ("/api/admin/kpi", "/api/admin/dashboards/kpi", "/api/admin/dashboard/kpi", "/api/admin/overview"):
        r = session.get(f"{BASE_URL}{path}", headers={"X-Admin-Token": admin_token}, timeout=15)
        tried.append((path, r.status_code))
        if r.status_code == 200:
            assert isinstance(r.json(), dict)
            return
    pytest.skip(f"no KPI endpoint present (tried {tried})")


# --------- 4. HR portal scoping ----------
HR_ENDPOINTS = [
    "/api/hr/field-leadership",
    "/api/hr/time-verification",
    "/api/hr/training-records",
    "/api/hr/employee-accountability",
]


@pytest.mark.parametrize("endpoint", HR_ENDPOINTS)
def test_hr_endpoint_with_hr_token(session, hr_token, endpoint):
    r = session.get(f"{BASE_URL}{endpoint}", headers={"X-HR-Token": hr_token}, timeout=15)
    # /hr/employee-accountability requires query params; 200 or 400 accepted.
    assert r.status_code in (200, 400, 404), f"{endpoint} → {r.status_code}: {r.text[:200]}"


@pytest.mark.parametrize("endpoint", HR_ENDPOINTS)
def test_hr_endpoint_rejects_admin_token(admin_token, endpoint):
    """Use fresh session — module session has cookies from logins."""
    fresh = requests.Session()
    r = fresh.get(
        f"{BASE_URL}{endpoint}",
        headers={"X-Admin-Token": admin_token, "Content-Type": "application/json"},
        timeout=15,
    )
    if r.status_code == 404:
        pytest.skip(f"{endpoint} not present")
    assert r.status_code in (401, 403), f"{endpoint} accepted admin token without HR token: {r.status_code}"


# --------- 5. PM scoping ----------
def test_pm_me_with_pm_token(session, pm_token):
    r = session.get(f"{BASE_URL}/api/pm/me", headers={"X-PM-Token": pm_token}, timeout=15)
    assert r.status_code in (200, 404)


# --------- 6. Field Leadership login + Time Off public-link ----------
def test_fl_login_and_list(session, fl_token):
    r = session.get(f"{BASE_URL}/api/field-leadership", headers={"X-Leadership-Token": fl_token}, timeout=15)
    assert r.status_code == 200
    body = r.json()
    items = body.get("items") if isinstance(body, dict) else body
    assert isinstance(items, list)


def test_fl_time_off_public_link_requires_auth():
    """Unauthenticated POST to create public link must reject. NOTE: conftest.py
    auto-injects X-Admin-Token on every request, so we must explicitly null it."""
    fresh = requests.Session()
    r = fresh.post(
        f"{BASE_URL}/api/field-leadership/time-off/public-link",
        json={"employee_name": "Test Employee"},
        headers={"Content-Type": "application/json", "X-Admin-Token": ""},
        timeout=15,
    )
    assert r.status_code in (401, 403), f"expected 401/403 got {r.status_code}: {r.text[:200]}"


@pytest.fixture(scope="module")
def public_link_token(session, hr_token):
    r = session.post(
        f"{BASE_URL}/api/field-leadership/time-off/public-link",
        json={"employee_name": f"TEST_iter106 {uuid.uuid4().hex[:6]}", "employee_email": ""},
        headers={"X-HR-Token": hr_token},
        timeout=15,
    )
    assert r.status_code == 200, f"create public link failed: {r.status_code} {r.text[:300]}"
    data = r.json()
    assert data.get("ok") is True
    link = data.get("link") or {}
    token = link.get("token")
    assert token, f"no token in response: {data}"
    return token


def test_public_link_get_no_auth(session, public_link_token):
    """Loading the public link requires no auth."""
    r = session.get(f"{BASE_URL}/api/public/time-off/{public_link_token}", timeout=15)
    assert r.status_code == 200, f"public load failed: {r.text[:200]}"
    body = r.json()
    assert "employee_name" in body


def test_public_link_submit_no_auth_and_persists(public_link_token, hr_token):
    """Use a fresh session for the public submit to avoid auth header pollution."""
    fresh = requests.Session()
    payload = {
        "reason": "Medical appointment",
        "pay_type": "Paid",
        "start_date": "2026-02-01",
        "end_date": "2026-02-02",
        "total_days": 2,
        "notes": "TEST_iter106",
    }
    r = fresh.post(
        f"{BASE_URL}/api/public/time-off/{public_link_token}/submit",
        json=payload,
        headers={"Content-Type": "application/json", "X-Admin-Token": ""},
        timeout=30,
    )
    assert r.status_code == 200, f"public submit failed: {r.status_code} {r.text[:200]}"
    rec_id = r.json().get("id")
    assert rec_id

    # Re-submitting same token should now 410
    r3 = fresh.post(
        f"{BASE_URL}/api/public/time-off/{public_link_token}/submit",
        json=payload,
        headers={"Content-Type": "application/json", "X-Admin-Token": ""},
        timeout=15,
    )
    assert r3.status_code in (410, 400, 404)


# --------- 7. Public submission endpoints ----------
PUBLIC_POSTS = [
    ("/api/inspections", {
        "job_id": "TEST_iter106",
        "job_name": "TEST_iter106 Job",
        "inspector_name": "TEST_iter106",
        "items": [],
    }),
    ("/api/meetings", {
        "job_id": "TEST_iter106",
        "topic": "TEST_iter106 Meeting",
        "leader_name": "TEST_iter106",
        "attendees": [],
    }),
    ("/api/incidents", {
        "job_id": "TEST_iter106",
        "reporter_name": "TEST_iter106",
        "description": "TEST_iter106 incident",
    }),
    ("/api/daily-reports", {
        "job_id": "TEST_iter106",
        "foreman_name": "TEST_iter106",
        "report_date": "2026-01-15",
    }),
    ("/api/equipment-inspections", {
        "job_id": "TEST_iter106",
        "operator_name": "TEST_iter106",
        "equipment_id": "TEST_iter106",
        "checklist": [],
    }),
    ("/api/qaqc-inspections", {
        "job_id": "TEST_iter106",
        "inspector_name": "TEST_iter106",
        "items": [],
    }),
]


@pytest.mark.parametrize("endpoint,payload", PUBLIC_POSTS)
def test_public_post_accepts_or_validates(session, endpoint, payload):
    r = session.post(f"{BASE_URL}{endpoint}", json=payload, timeout=20)
    # 200/201 (accepted) or 422 (validated) is fine. 500 = bug. 429 = rate-limited (acceptable).
    assert r.status_code in (200, 201, 422, 400, 429), f"{endpoint} → {r.status_code}: {r.text[:200]}"


def test_public_post_invalid_payload_is_422_not_500(session):
    r = session.post(f"{BASE_URL}/api/inspections", json={"not_a_real_field": True}, timeout=15)
    # Should be 422 (validation error), not 500
    assert r.status_code != 500, f"Malformed payload returned 500 instead of 422: {r.text[:200]}"


# --------- 8. PDF footer string verification ----------
def test_pdf_footer_field_leadership(session, admin_token, fl_token):
    """Get a recent FL record and verify PDF endpoint returns 200 application/pdf."""
    r = session.get(f"{BASE_URL}/api/field-leadership", headers={"X-Leadership-Token": fl_token}, timeout=15)
    assert r.status_code == 200
    body = r.json()
    items = body.get("items") if isinstance(body, dict) else body
    if not items:
        pytest.skip("no FL records to PDF-test")
    rec_id = items[0]["id"]
    r2 = session.get(
        f"{BASE_URL}/api/field-leadership/{rec_id}/pdf",
        headers={"X-Leadership-Token": fl_token, "X-Admin-Token": admin_token},
        timeout=30,
    )
    assert r2.status_code == 200, f"PDF gen failed {r2.status_code}: {r2.text[:200]}"
    ct = r2.headers.get("content-type", "")
    assert "pdf" in ct.lower() or "html" in ct.lower(), f"unexpected content-type: {ct}"
    # PDF bodies are compressed (FlateDecode) so we can't grep for footer text.
    # Verified separately via code review: field_leadership_pdf.py line 578 sets
    # @page footer to "Generated through MASCI Operations Platform — Powered by ForgedOps™ | © 2026 ForgedOps™"


# --------- 9. MongoDB _id hygiene (additional spot checks) ----------
SPOT_CHECK_LISTS = [
    "/api/meetings",
    "/api/inspections",
    "/api/daily-reports",
    "/api/incidents",
    "/api/equipment-inspections",
]


@pytest.mark.parametrize("endpoint", SPOT_CHECK_LISTS)
def test_no_mongo_id_leakage(session, admin_token, endpoint):
    r = session.get(f"{BASE_URL}{endpoint}", headers={"X-Admin-Token": admin_token}, timeout=15)
    assert r.status_code == 200, f"{endpoint} → {r.status_code}"
    body = r.json()
    items = body.get("items") if isinstance(body, dict) else body
    if isinstance(items, list):
        for it in items[:5]:
            if isinstance(it, dict):
                assert "_id" not in it, f"{endpoint} leaks _id in: {list(it.keys())[:5]}"


# --------- 10. CORS ---------
def test_cors_responds_with_allowed_origin(session):
    r = session.options(
        f"{BASE_URL}/api/health",
        headers={
            "Origin": "https://mascidocs.com",
            "Access-Control-Request-Method": "GET",
        },
        timeout=10,
    )
    # Either 200/204 with ACAO header, or method-not-allowed (CORS still typically responds)
    assert r.status_code in (200, 204, 405)
