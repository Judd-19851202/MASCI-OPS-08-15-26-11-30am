"""
MASCI Operational Certification — critical-flow regression suite.

Read-only. Cannot run unless the live pod reports `app_env=preview` and a
`*_preview` database (enforced by conftest.env_identity).

Coverage:
  1. Environment separation guardrail            (test_env_*)
  2. Service health                              (test_health)
  3. Super-admin multi-login + 7 portal tokens   (test_multi_login_*)
  4. Per-portal /me reachability                 (test_portal_me_*)
  5. Cross-portal token isolation                (test_cross_portal_*)
  6. Critical list endpoints reachable           (test_critical_lists)
  7. HR performance SLA (handoff: 10s → <3s)     (test_hr_perf_*)
  8. Public-vs-protected enforcement             (test_no_auth_*)
  9. Reference data presence                     (test_reference_data)
"""

from __future__ import annotations

import time

import pytest
import requests


# ---------------------------------------------------------------------------
# 1. Environment separation guardrail
# ---------------------------------------------------------------------------
def test_env_identity_is_preview(env_identity):
    assert env_identity["app_env"] == "preview"
    assert env_identity["db_name"].endswith("_preview"), env_identity


def test_env_identity_exposes_release(env_identity):
    # Frontend banner consumes these; must be present + non-empty.
    assert env_identity.get("source_hash")
    assert env_identity.get("release")
    assert env_identity.get("service") == "masci-hub"


# ---------------------------------------------------------------------------
# 2. Health
# ---------------------------------------------------------------------------
def test_health(base_url):
    r = requests.get(f"{base_url}/api/health", timeout=10)
    assert r.status_code == 200
    body = r.json()
    assert body.get("ok") is True
    assert body.get("service") == "masci-hub"


# ---------------------------------------------------------------------------
# 3. Multi-login
# ---------------------------------------------------------------------------
EXPECTED_PORTALS = {"admin", "pm", "shop", "hr", "safety", "dispatch", "field_leadership"}


def test_multi_login_returns_all_portals(tokens):
    assert tokens["ok"] is True
    assert set(tokens["portal_tokens"].keys()) == EXPECTED_PORTALS
    for portal, token in tokens["portal_tokens"].items():
        assert isinstance(token, str) and len(token) >= 32, portal


def test_multi_login_user_is_super_admin(tokens):
    u = tokens["user"]
    assert u["is_super_admin"] is True
    assert u["disabled"] is False
    assert u["must_change_password"] is False


def test_multi_login_session_token_present(tokens):
    assert tokens.get("session_token")


# ---------------------------------------------------------------------------
# 4. Per-portal /me reachability
# ---------------------------------------------------------------------------
@pytest.mark.parametrize(
    "endpoint,header_fixture",
    [
        ("/api/admin/check", "admin_headers"),       # admin verification
        ("/api/pm/me", "pm_headers"),
        ("/api/shop/me", "shop_headers"),
        ("/api/hr/me", "hr_headers"),
        ("/api/safety/me", "safety_headers"),
        ("/api/dispatch/me", "dispatch_headers"),
        ("/api/field-leadership/portal/me", "fl_headers"),
    ],
)
def test_portal_me(base_url, endpoint, header_fixture, request):
    headers = request.getfixturevalue(header_fixture)
    r = requests.get(f"{base_url}{endpoint}", headers=headers, timeout=10)
    assert r.status_code == 200, f"{endpoint} -> {r.status_code} body={r.text[:200]}"


# ---------------------------------------------------------------------------
# 5. Cross-portal token isolation
# ---------------------------------------------------------------------------
def test_hr_token_cannot_act_as_admin(base_url, tokens):
    """HR token in X-Admin-Token header must be rejected (401)."""
    hr = tokens["portal_tokens"]["hr"]
    r = requests.get(
        f"{base_url}/api/admin/jobs",
        headers={"X-Admin-Token": hr},
        timeout=10,
    )
    assert r.status_code in (401, 403), f"expected 401/403 got {r.status_code}"


def test_pm_token_cannot_act_as_hr(base_url, tokens):
    """PM token sent as X-HR-Token must be rejected."""
    pm = tokens["portal_tokens"]["pm"]
    r = requests.get(
        f"{base_url}/api/hr/me",
        headers={"X-HR-Token": pm},
        timeout=10,
    )
    assert r.status_code in (401, 403), f"expected 401/403 got {r.status_code}"


def test_random_token_is_rejected(base_url):
    r = requests.get(
        f"{base_url}/api/admin/jobs",
        headers={"X-Admin-Token": "not-a-real-token-deadbeef"},
        timeout=10,
    )
    assert r.status_code in (401, 403)


# ---------------------------------------------------------------------------
# 6. Critical list endpoints (admin-scoped)
# ---------------------------------------------------------------------------
CRITICAL_ADMIN_LISTS = [
    "/api/admin/jobs",
    "/api/daily-reports",
    "/api/incidents",
    "/api/meetings",
    "/api/inspections",
    "/api/jhas",
    "/api/equipment-inspections",
    "/api/equipment-inspections?limit=1",
]


@pytest.mark.parametrize("endpoint", CRITICAL_ADMIN_LISTS)
def test_critical_lists(base_url, admin_headers, endpoint):
    r = requests.get(f"{base_url}{endpoint}", headers=admin_headers, timeout=15)
    assert r.status_code == 200, f"{endpoint} -> {r.status_code} body={r.text[:200]}"
    # All list endpoints return either list or {items:[...]}; both are JSON.
    r.json()


# ---------------------------------------------------------------------------
# 7. HR performance SLA — handoff fixed 10s → ~0.5s; we assert <3s with 2x margin
# ---------------------------------------------------------------------------
HR_PERF_ENDPOINTS = [
    "/api/hr/time-verification",
    "/api/hr/driver-qualification/dashboard",
    "/api/hr/training-records",
]
HR_PERF_BUDGET_MS = 3000


@pytest.mark.parametrize("endpoint", HR_PERF_ENDPOINTS)
def test_hr_perf_budget(base_url, hr_headers, endpoint):
    start = time.monotonic()
    r = requests.get(f"{base_url}{endpoint}", headers=hr_headers, timeout=15)
    elapsed_ms = int((time.monotonic() - start) * 1000)
    assert r.status_code == 200, f"{endpoint} -> {r.status_code}"
    assert elapsed_ms < HR_PERF_BUDGET_MS, (
        f"{endpoint} took {elapsed_ms}ms (budget {HR_PERF_BUDGET_MS}ms) — "
        "performance regression"
    )


# ---------------------------------------------------------------------------
# 8. Auth enforcement — protected endpoints must 401 without a token
# ---------------------------------------------------------------------------
PROTECTED_NO_AUTH = [
    "/api/admin/jobs",
    "/api/daily-reports",
    "/api/incidents",
    "/api/meetings",
    "/api/inspections",
    "/api/jhas",
    "/api/hr/me",
    "/api/pm/me",
    "/api/shop/me",
    "/api/safety/me",
    "/api/dispatch/me",
    "/api/field-leadership/portal/me",
]


@pytest.mark.parametrize("endpoint", PROTECTED_NO_AUTH)
def test_no_auth_protected_endpoints_401(base_url, endpoint):
    r = requests.get(f"{base_url}{endpoint}", timeout=10)
    assert r.status_code in (401, 403), f"{endpoint} -> {r.status_code} (expected 401/403)"


# ---------------------------------------------------------------------------
# 9. Reference data must be present in the preview DB
# ---------------------------------------------------------------------------
def test_reference_data_employees(base_url):
    """The public /api/employees endpoint must return real employees."""
    r = requests.get(f"{base_url}/api/employees", timeout=15)
    assert r.status_code == 200
    body = r.json()
    items = body if isinstance(body, list) else body.get("items") or body.get("employees")
    assert items, "no employees returned"
    assert len(items) >= 10, f"expected >=10 employees, got {len(items)}"


def test_reference_data_jobs(base_url, admin_headers):
    r = requests.get(f"{base_url}/api/admin/jobs", headers=admin_headers, timeout=15)
    assert r.status_code == 200
    body = r.json()
    items = body if isinstance(body, list) else body.get("items") or body.get("jobs")
    assert isinstance(items, list), f"unexpected shape: {type(items).__name__}"


# ---------------------------------------------------------------------------
# 10. Cluster capacity probe (iter437) — public read, always returns 200
#     with a severity field. The frontend ClusterCapacityBanner depends on
#     this contract. A regression here means the banner stops surfacing
#     write-block conditions.
# ---------------------------------------------------------------------------
def test_cluster_capacity_endpoint(base_url):
    r = requests.get(f"{base_url}/api/cluster/capacity", timeout=10)
    assert r.status_code == 200, r.text[:200]
    body = r.json()
    assert body.get("ok") is True
    assert isinstance(body.get("storage_used_mb"), (int, float))
    assert isinstance(body.get("storage_used_pct"), (int, float))
    assert isinstance(body.get("tier_quota_mb"), int)
    assert body.get("severity") in {"ok", "warning", "critical"}
    assert isinstance(body.get("dbs"), dict)


def test_cluster_capacity_no_auth_required(base_url):
    """Banner must render on the public login page, before any portal token
    has been issued. Endpoint MUST work with zero headers."""
    r = requests.get(f"{base_url}/api/cluster/capacity", timeout=10)
    assert r.status_code == 200


# ---------------------------------------------------------------------------
# 11. Cluster capacity HISTORY (iter437 Phase Sigma-II) — drift detection
# ---------------------------------------------------------------------------
def test_cluster_capacity_history_default_window(base_url):
    r = requests.get(f"{base_url}/api/cluster/capacity/history", timeout=10)
    assert r.status_code == 200, r.text[:200]
    body = r.json()
    assert body.get("ok") is True
    assert body.get("days") == 7
    assert isinstance(body.get("samples"), int)
    assert "rows" in body and isinstance(body["rows"], list)


def test_cluster_capacity_history_validates_days_range(base_url):
    """days=0 → 422 (out of range, ge=1)."""
    r = requests.get(f"{base_url}/api/cluster/capacity/history?days=0", timeout=10)
    assert r.status_code == 422, r.text[:200]

    r = requests.get(f"{base_url}/api/cluster/capacity/history?days=120", timeout=10)
    assert r.status_code == 422, r.text[:200]


def test_cluster_capacity_history_no_auth_required(base_url):
    """Same public surface as the live probe — drift widget loads pre-login."""
    r = requests.get(f"{base_url}/api/cluster/capacity/history?days=1", timeout=10)
    assert r.status_code == 200
