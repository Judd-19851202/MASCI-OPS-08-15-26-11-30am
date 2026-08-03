"""
Iter94 — Production Readiness Audit (backend regression)
Covers: multi-portal login, issue-portal-token, directory CRUD,
backups state, field-leadership, job-photos, form-list endpoints,
per-portal /me, role isolation.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://masci-audit-hub.preview.emergentagent.com").rstrip("/")
API = f"{BASE_URL}/api"

SUPER_ADMIN_EMAIL = "jaymn.judd@mascigc.com"
SUPER_ADMIN_PW = "Maddix123!"
HR_EMAIL = "hrmanager@mascigc.com"
HR_PW = "HRPortal2026!"
PM_EMAIL = "chriswright@mascigc.com"
PM_PW = "ChrisRocksThis2026"


# ---------- shared session fixture ----------
@pytest.fixture(scope="session")
def s():
    sess = requests.Session()
    sess.headers.update({"Content-Type": "application/json"})
    return sess


@pytest.fixture(scope="session")
def multi_tokens(s):
    """Super-admin multi-login → all 4 portal tokens (iter87+)."""
    r = s.post(f"{API}/auth/multi-login", json={"email": SUPER_ADMIN_EMAIL, "password": SUPER_ADMIN_PW}, timeout=30)
    assert r.status_code == 200, f"multi-login failed: {r.status_code} {r.text[:300]}"
    data = r.json()
    assert data.get("ok") is True, data
    tokens = data.get("tokens") or data.get("portal_tokens") or {}
    # Sometimes flattened
    if not tokens and "admin_token" in data:
        tokens = {k.replace("_token", ""): data.get(k) for k in ("admin_token","pm_token","hr_token","shop_token")}
    return data, tokens


@pytest.fixture(scope="session")
def admin_headers(multi_tokens):
    data, tokens = multi_tokens
    tok = tokens.get("admin") or data.get("admin_token")
    assert tok, f"no admin token in multi-login response: keys={list(data.keys())}"
    return {"X-Admin-Token": tok}


@pytest.fixture(scope="session")
def pm_headers(multi_tokens):
    data, tokens = multi_tokens
    tok = tokens.get("pm") or data.get("pm_token")
    return {"X-PM-Token": tok} if tok else None


@pytest.fixture(scope="session")
def hr_headers(multi_tokens):
    data, tokens = multi_tokens
    tok = tokens.get("hr") or data.get("hr_token")
    return {"X-HR-Token": tok} if tok else None


@pytest.fixture(scope="session")
def shop_headers(multi_tokens):
    data, tokens = multi_tokens
    tok = tokens.get("shop") or data.get("shop_token")
    return {"X-Shop-Token": tok} if tok else None


@pytest.fixture(scope="session")
def directory_token(multi_tokens):
    data, _ = multi_tokens
    return data.get("directory_token") or data.get("session_token") or data.get("master_token")


# ---------- health ----------
def test_health(s):
    r = s.get(f"{API}/health", timeout=15)
    assert r.status_code == 200


# ---------- multi-login (iter87) ----------
def test_multi_login_returns_all_four_portal_tokens(multi_tokens):
    data, tokens = multi_tokens
    expected = {"admin", "pm", "hr", "shop"}
    have = {k for k, v in tokens.items() if v}
    assert expected.issubset(have), f"missing portal tokens: missing={expected - have} got={tokens}"


# ---------- issue-portal-token (iter88) ----------
def test_issue_portal_token_rehydrates(s, directory_token):
    if not directory_token:
        pytest.skip("no directory token in multi-login response")
    headers = {"X-Directory-Token": directory_token, "Content-Type": "application/json"}
    for portal in ("admin", "pm", "hr", "shop"):
        r = s.post(f"{API}/auth/issue-portal-token", json={"portal": portal}, headers=headers, timeout=15)
        assert r.status_code == 200, f"issue-portal-token({portal}) → {r.status_code} {r.text[:200]}"
        body = r.json()
        assert body.get("ok") is True and body.get("token"), body


# ---------- /me endpoints ----------
def test_pm_me(s, pm_headers):
    if not pm_headers:
        pytest.skip("no pm token")
    r = s.get(f"{API}/pm/me", headers=pm_headers, timeout=15)
    assert r.status_code == 200, r.text[:200]


def test_hr_me(s, hr_headers):
    if not hr_headers:
        pytest.skip("no hr token")
    r = s.get(f"{API}/hr/me", headers=hr_headers, timeout=15)
    assert r.status_code == 200, r.text[:200]


def test_shop_me(s, shop_headers):
    if not shop_headers:
        pytest.skip("no shop token")
    r = s.get(f"{API}/shop/me", headers=shop_headers, timeout=15)
    assert r.status_code == 200, r.text[:200]


# ---------- role isolation: HR-ONLY user (not super-admin) ----------
@pytest.fixture(scope="session")
def hr_only_headers(s):
    r = s.post(f"{API}/hr/login", json={"email": HR_EMAIL, "password": HR_PW}, timeout=15)
    if r.status_code != 200:
        pytest.skip(f"HR direct login failed: {r.status_code}")
    return {"X-HR-Token": r.json()["token"]}


def test_hr_only_token_rejected_on_admin(s, hr_only_headers):
    headers = {**hr_only_headers, "X-Admin-Token": ""}
    r = s.get(f"{API}/admin/directory", headers=headers, timeout=15)
    assert r.status_code in (401, 403), f"HR-only token leaked into admin route: {r.status_code}"


def test_hr_only_token_rejected_on_pm(s, hr_only_headers):
    headers = {**hr_only_headers, "X-Admin-Token": ""}
    r = s.get(f"{API}/pm/me", headers=headers, timeout=15)
    assert r.status_code in (401, 403)


# ---------- backups (iter85) ----------
def test_backups_complete_r2_state(s, admin_headers):
    r = s.get(f"{API}/admin/backups-complete-r2-state", headers=admin_headers, timeout=20)
    assert r.status_code == 200, r.text[:300]
    body = r.json()
    # accept either { ok: true, ... } or direct state dict
    assert isinstance(body, dict)


# ---------- field-leadership counts_by_kind ----------
def test_field_leadership_counts(s, admin_headers):
    r = s.get(f"{API}/field-leadership", headers=admin_headers, timeout=20)
    assert r.status_code == 200, r.text[:300]
    body = r.json()
    assert "counts_by_kind" in body or "counts" in body or "items" in body


# ---------- job-photos ----------
def test_job_photos(s, admin_headers):
    r = s.get(f"{API}/job-photos", headers=admin_headers, timeout=20)
    assert r.status_code == 200, r.text[:300]
    body = r.json()
    assert "items" in body or isinstance(body, list)


# ---------- all form-list endpoints with admin token ----------
@pytest.mark.parametrize("path", [
    "/inspections",
    "/meetings",
    "/job-hazard-plans",
    "/trench-boxes",
    "/incidents",
    "/daily-reports",
    "/equipment-inspections",
    "/qaqc-inspections",
])
def test_form_list_endpoints(s, admin_headers, path):
    r = s.get(f"{API}{path}", headers=admin_headers, timeout=25)
    assert r.status_code == 200, f"{path} → {r.status_code} {r.text[:200]}"
    # ensure no Mongo _id leakage in first item if list returned
    body = r.json()
    items = body if isinstance(body, list) else body.get("items", [])
    if items:
        first = items[0] if isinstance(items[0], dict) else {}
        assert "_id" not in first, f"{path} leaks _id"


# ---------- directory CRUD (iter90 email delivery) ----------
def test_directory_create_show_delivery(s, admin_headers):
    payload = {
        "name": "TEST_iter94 User",
        "email": f"test_iter94_{os.getpid()}@example.com",
        "portals": ["pm"],
        "delivery": "show",
        "password": "TempPass2026!",
    }
    r = s.post(f"{API}/admin/directory", json=payload, headers=admin_headers, timeout=20)
    if r.status_code == 404:
        pytest.skip("/api/admin/directory not present")
    assert r.status_code in (200, 201), r.text[:400]
    body = r.json()
    assert body.get("ok") is True
    # cleanup
    uid = (body.get("user") or {}).get("id") or body.get("id")
    if uid:
        s.delete(f"{API}/admin/directory/{uid}", headers=admin_headers, timeout=15)


def test_directory_create_email_delivery_preview_falls_back(s, admin_headers):
    """In preview, AUTO_EMAIL_REPORTS=false → should still 200 with email_sent=false (show-on-screen fallback)."""
    payload = {
        "name": "TEST_iter94 EmailUser",
        "email": f"test_iter94_email_{os.getpid()}@example.com",
        "portals": ["pm"],
        "delivery": "email",
    }
    r = s.post(f"{API}/admin/directory", json=payload, headers=admin_headers, timeout=20)
    if r.status_code == 404:
        pytest.skip("/api/admin/directory not present")
    assert r.status_code in (200, 201), r.text[:400]
    body = r.json()
    assert "email_sent" in body or body.get("ok"), body
    uid = (body.get("user") or {}).get("id") or body.get("id")
    if uid:
        s.delete(f"{API}/admin/directory/{uid}", headers=admin_headers, timeout=15)


# ---------- HR portal direct login ----------
def test_hr_direct_login(s):
    r = s.post(f"{API}/hr/login", json={"email": HR_EMAIL, "password": HR_PW}, timeout=20)
    assert r.status_code == 200, r.text[:300]
    body = r.json()
    assert body.get("ok") and body.get("token")
