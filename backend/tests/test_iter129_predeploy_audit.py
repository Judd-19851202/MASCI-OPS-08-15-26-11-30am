"""
iter129 — Pre-Deployment Full-System QA Sweep
Covers: super-admin universal access across 6 portals, cross-portal read on operations,
write protection on /holds/transfers/assignments, pending-hold workflow, admin impersonate dispatch user.
"""
import os
import time
import pytest
import requests
import httpx

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
import pytest as _pytest
if not BASE_URL:
    _pytest.skip(
        "REACT_APP_BACKEND_URL not set · live-HTTP test skipped (parity-lock safe).",
        allow_module_level=True,
    )

SUPER_EMAIL = "jaymn.judd@mascigc.com"
SUPER_PASSWORD = "Maddix123!"


# --------- shared fixtures ---------
@pytest.fixture(scope="module")
def portal_tokens():
    r = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": SUPER_EMAIL, "password": SUPER_PASSWORD},
        timeout=20,
    )
    assert r.status_code == 200, f"multi-login failed: {r.status_code} {r.text}"
    data = r.json()
    assert data.get("ok") is True
    tokens = data.get("portal_tokens") or {}
    for p in ("admin", "pm", "shop", "hr", "safety", "dispatch"):
        assert tokens.get(p), f"Missing token for portal: {p}"
    return tokens


def _hdr(portal, tokens):
    map_ = {
        "admin": ("X-Admin-Token", tokens["admin"]),
        "pm":     ("X-PM-Token", tokens["pm"]),
        "shop":   ("X-Shop-Token", tokens["shop"]),
        "hr":     ("X-HR-Token", tokens["hr"]),
        "safety": ("X-Safety-Token", tokens["safety"]),
        "dispatch": ("X-Dispatch-Token", tokens["dispatch"]),
    }
    k, v = map_[portal]
    return {k: v}


@pytest.fixture(scope="module")
def real_asset_id(portal_tokens):
    r = requests.get(f"{BASE_URL}/api/equipment-master",
                     headers=_hdr("admin", portal_tokens), timeout=20)
    r.raise_for_status()
    for it in r.json().get("items", []):
        if (it.get("unit_number") or "").strip():
            return it["id"]
    pytest.skip("no equipment_master rows for asset_id fixture")


# --------- super-admin universal access ---------
class TestSuperAdminUniversalAccess:
    def test_admin_token_overview(self, portal_tokens):
        r = requests.get(f"{BASE_URL}/api/admin/safety/overview",
                         headers=_hdr("admin", portal_tokens), timeout=15)
        assert r.status_code == 200

    def test_pm_me(self, portal_tokens):
        r = requests.get(f"{BASE_URL}/api/pm/me",
                         headers=_hdr("pm", portal_tokens), timeout=15)
        assert r.status_code == 200

    def test_shop_me(self, portal_tokens):
        r = requests.get(f"{BASE_URL}/api/shop/me",
                         headers=_hdr("shop", portal_tokens), timeout=15)
        assert r.status_code == 200

    def test_hr_me(self, portal_tokens):
        r = requests.get(f"{BASE_URL}/api/hr/me",
                         headers=_hdr("hr", portal_tokens), timeout=15)
        assert r.status_code == 200

    def test_safety_me(self, portal_tokens):
        r = requests.get(f"{BASE_URL}/api/safety/me",
                         headers=_hdr("safety", portal_tokens), timeout=15)
        assert r.status_code == 200

    def test_dispatch_me(self, portal_tokens):
        r = requests.get(f"{BASE_URL}/api/dispatch/me",
                         headers=_hdr("dispatch", portal_tokens), timeout=15)
        assert r.status_code == 200


# --------- cross-portal reads on operations ---------
@pytest.mark.parametrize("portal", ["admin", "pm", "shop", "hr", "safety", "dispatch"])
@pytest.mark.parametrize("path", [
    "/api/operations/events",
    "/api/operations/holds",
    "/api/operations/transfers",
    "/api/operations/utilization",
    "/api/operations/idle-equipment",
])
def test_operations_read_accepts_any_portal_token(portal_tokens, portal, path):
    r = requests.get(f"{BASE_URL}{path}", headers=_hdr(portal, portal_tokens), timeout=20)
    assert r.status_code == 200, f"{portal} GET {path} → {r.status_code}: {r.text[:200]}"


# --------- write protection: only admin + dispatch allowed ---------
@pytest.mark.parametrize("portal,expected_block", [
    ("pm", True), ("shop", True), ("hr", True), ("safety", True),
])
def test_operations_write_blocks_non_admin_non_dispatch(portal_tokens, real_asset_id, portal, expected_block):
    body = {
        "asset_id": real_asset_id,
        "kind": "maintenance",
        "reason": "regression-test-write-block",
    }
    # Use httpx to bypass conftest's auto X-Admin-Token attach
    with httpx.Client(timeout=15.0) as c:
        r = c.post(f"{BASE_URL}/api/operations/holds?pending=true",
                   json=body, headers=_hdr(portal, portal_tokens))
    assert r.status_code in (401, 403), (
        f"Expected 401/403 for {portal} POST /holds, got {r.status_code}: {r.text[:200]}"
    )


def test_operations_write_admin_allowed(portal_tokens, real_asset_id):
    body = {
        "asset_id": real_asset_id,
        "kind": "maintenance",
        "reason": "iter129 admin write smoke",
    }
    r = requests.post(f"{BASE_URL}/api/operations/holds?pending=true",
                      json=body, headers=_hdr("admin", portal_tokens), timeout=15)
    assert r.status_code in (200, 201), f"admin write rejected: {r.status_code} {r.text[:200]}"
    hid = r.json().get("id")
    if hid:
        requests.post(f"{BASE_URL}/api/operations/holds/{hid}/dismiss",
                      json={"reason": "iter129 cleanup"},
                      headers=_hdr("admin", portal_tokens), timeout=15)


def test_operations_write_dispatch_allowed(portal_tokens, real_asset_id):
    body = {
        "asset_id": real_asset_id,
        "kind": "maintenance",
        "reason": "iter129 dispatch write smoke",
    }
    r = requests.post(f"{BASE_URL}/api/operations/holds?pending=true",
                      json=body, headers=_hdr("dispatch", portal_tokens), timeout=15)
    assert r.status_code in (200, 201), f"dispatch write rejected: {r.status_code} {r.text[:200]}"
    hid = r.json().get("id")
    if hid:
        requests.post(f"{BASE_URL}/api/operations/holds/{hid}/dismiss",
                      json={"reason": "iter129 cleanup"},
                      headers=_hdr("admin", portal_tokens), timeout=15)


# --------- pending maintenance hold workflow ---------
class TestPendingHoldWorkflow:
    def _create_pending(self, portal_tokens, real_asset_id):
        body = {
            "asset_id": real_asset_id,
            "kind": "maintenance",
            "reason": "iter129 pending workflow",
        }
        r = requests.post(f"{BASE_URL}/api/operations/holds?pending=true",
                          json=body, headers=_hdr("admin", portal_tokens), timeout=15)
        assert r.status_code in (200, 201), r.text
        return r.json()

    def test_create_pending_hold_status_pending(self, portal_tokens, real_asset_id):
        h = self._create_pending(portal_tokens, real_asset_id)
        assert h.get("status") == "pending"
        assert h.get("active") is False
        requests.post(f"{BASE_URL}/api/operations/holds/{h['id']}/dismiss",
                      json={"reason": "cleanup"},
                      headers=_hdr("admin", portal_tokens), timeout=15)

    def test_approve_pending(self, portal_tokens, real_asset_id):
        h = self._create_pending(portal_tokens, real_asset_id)
        r = requests.post(f"{BASE_URL}/api/operations/holds/{h['id']}/approve",
                          json={"note": "iter129 approve"},
                          headers=_hdr("admin", portal_tokens), timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("status") == "active"
        r2 = requests.post(f"{BASE_URL}/api/operations/holds/{h['id']}/approve",
                           json={"note": "second"},
                           headers=_hdr("admin", portal_tokens), timeout=15)
        assert r2.status_code == 409
        requests.post(f"{BASE_URL}/api/operations/holds/{h['id']}/dismiss",
                      json={"reason": "cleanup"},
                      headers=_hdr("admin", portal_tokens), timeout=15)

    def test_dismiss_requires_reason(self, portal_tokens, real_asset_id):
        h = self._create_pending(portal_tokens, real_asset_id)
        r = requests.post(f"{BASE_URL}/api/operations/holds/{h['id']}/dismiss",
                          json={}, headers=_hdr("admin", portal_tokens), timeout=15)
        assert r.status_code == 422
        r2 = requests.post(f"{BASE_URL}/api/operations/holds/{h['id']}/dismiss",
                           json={"reason": "regression dismiss"},
                           headers=_hdr("admin", portal_tokens), timeout=15)
        assert r2.status_code == 200
        assert r2.json().get("status") == "dismissed"


# --------- admin impersonate dispatch ---------
class TestAdminImpersonateDispatch:
    def _first_dispatch_user_id(self, portal_tokens):
        r = requests.get(f"{BASE_URL}/api/admin/dispatch-users",
                         headers=_hdr("admin", portal_tokens), timeout=15)
        assert r.status_code == 200, r.text
        users = r.json() if isinstance(r.json(), list) else r.json().get("users", [])
        assert users, "No dispatch users seeded"
        # find an enabled user
        for u in users:
            if u.get("disabled") is not True:
                return u["id"]
        return users[0]["id"]

    def test_impersonate_unknown_returns_404(self, portal_tokens):
        r = requests.post(f"{BASE_URL}/api/admin/dispatch-users/nonexistent-id-xyz/impersonate",
                          headers=_hdr("admin", portal_tokens), timeout=15)
        assert r.status_code == 404

    def test_impersonate_happy_path(self, portal_tokens):
        uid = self._first_dispatch_user_id(portal_tokens)
        r = requests.post(f"{BASE_URL}/api/admin/dispatch-users/{uid}/impersonate",
                          headers=_hdr("admin", portal_tokens), timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body.get("token")
        assert body.get("user")
        # token works on /me
        me = requests.get(f"{BASE_URL}/api/dispatch/me",
                          headers={"X-Dispatch-Token": body["token"]}, timeout=15)
        assert me.status_code == 200
