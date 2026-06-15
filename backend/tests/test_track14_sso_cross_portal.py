"""
TRACK 14.0-CROSS-PORTAL-SESSION-INHERITANCE-SINGLE-SIGN-ON — Backend tests
Covers SSO-CERT-9 (backend role gate + multi-login fanout) and supporting checks.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")

SUPER_ADMIN = {"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"}
PM_USER = {"email": "cert.pm@example.com", "password": "CertProof2026!"}
HR_USER = {"email": "cert.hr@example.com", "password": "CertProof2026!"}
SHOP_USER = {"email": "cert.shop@example.com", "password": "CertProof2026!"}
SAFETY_USER = {"email": "cert.safety@example.com", "password": "CertProof2026!"}
DISPATCH_USER = {"email": "cert.dispatch@example.com", "password": "CertProof2026!"}


def _multi_login(creds):
    r = requests.post(f"{BASE_URL}/api/auth/multi-login", json=creds, timeout=30)
    return r


@pytest.fixture(scope="module")
def super_admin_login():
    r = _multi_login(SUPER_ADMIN)
    assert r.status_code == 200, f"super admin multi-login failed: {r.status_code} {r.text[:300]}"
    return r.json()


# --- SSO-CERT-9 step 1: portal_tokens fanout for super admin ---
class TestMultiLoginFanout:
    def test_super_admin_portal_tokens_present(self, super_admin_login):
        data = super_admin_login
        assert data.get("ok") is True or "portal_tokens" in data
        pt = data.get("portal_tokens") or {}
        # Required core portals
        for key in ("admin", "pm", "hr", "shop", "safety", "dispatch"):
            assert key in pt, f"Missing portal_tokens.{key} (keys={list(pt.keys())})"
            assert pt[key], f"portal_tokens.{key} is empty/None"
        # field_leadership OR fl alias
        assert ("field_leadership" in pt) or ("fl" in pt), (
            f"Missing field_leadership/fl token. keys={list(pt.keys())}"
        )

    def test_directory_token_returned(self, super_admin_login):
        data = super_admin_login
        # directory token may live under different keys
        keys = list(data.keys())
        has_dir = (
            ("session_token" in data and data.get("session_token"))
            or ("directory_token" in data and data.get("directory_token"))
            or ("token" in data and data.get("token"))
            or ("masci_directory_token" in data and data.get("masci_directory_token"))
        )
        assert has_dir, f"No directory token in multi-login response. keys={keys}"


def _extract_directory_token(login_json):
    return (
        login_json.get("session_token")
        or login_json.get("directory_token")
        or login_json.get("token")
        or login_json.get("masci_directory_token")
        or ""
    )


# --- SSO-CERT-9 step 2: issue-portal-token for granted portals ---
class TestIssuePortalTokenGranted:
    def test_issue_safety_token(self, super_admin_login):
        tok = _extract_directory_token(super_admin_login)
        assert tok, "directory token missing"
        r = requests.post(
            f"{BASE_URL}/api/auth/issue-portal-token",
            json={"portal": "safety"},
            headers={"X-Directory-Token": tok},
            timeout=15,
        )
        assert r.status_code == 200, f"safety issue failed: {r.status_code} {r.text[:300]}"
        body = r.json()
        assert body.get("token"), f"no token in response: {body}"
        assert body.get("portal") == "safety"

    def test_issue_dispatch_token(self, super_admin_login):
        tok = _extract_directory_token(super_admin_login)
        r = requests.post(
            f"{BASE_URL}/api/auth/issue-portal-token",
            json={"portal": "dispatch"},
            headers={"X-Directory-Token": tok},
            timeout=15,
        )
        assert r.status_code == 200, f"dispatch issue failed: {r.status_code} {r.text[:300]}"
        body = r.json()
        assert body.get("token"), f"no token: {body}"

    def test_issue_field_leadership_token(self, super_admin_login):
        """SSO-CERT-9: issue-portal-token must support field_leadership.

        The frontend usePortalHydration extension expects to mint FL
        tokens via this endpoint for super-admin and FL-granted users."""
        tok = _extract_directory_token(super_admin_login)
        r = requests.post(
            f"{BASE_URL}/api/auth/issue-portal-token",
            json={"portal": "field_leadership"},
            headers={"X-Directory-Token": tok},
            timeout=15,
        )
        assert r.status_code == 200, (
            f"field_leadership issue failed (likely minter not registered): "
            f"{r.status_code} {r.text[:400]}"
        )
        body = r.json()
        assert body.get("token"), f"no token: {body}"

    def test_issue_admin_token(self, super_admin_login):
        tok = _extract_directory_token(super_admin_login)
        r = requests.post(
            f"{BASE_URL}/api/auth/issue-portal-token",
            json={"portal": "admin"},
            headers={"X-Directory-Token": tok},
            timeout=15,
        )
        assert r.status_code == 200, f"admin issue failed: {r.status_code} {r.text[:300]}"


# --- SSO-CERT-9 step 3: role gate must block escalation ---
class TestIssuePortalTokenEscalation:
    @pytest.fixture(scope="class")
    def pm_login(self):
        r = _multi_login(PM_USER)
        if r.status_code != 200:
            pytest.skip(f"PM user login unavailable: {r.status_code} {r.text[:200]}")
        return r.json()

    @pytest.fixture(scope="class")
    def hr_login(self):
        r = _multi_login(HR_USER)
        if r.status_code != 200:
            pytest.skip(f"HR user login unavailable: {r.status_code} {r.text[:200]}")
        return r.json()

    @pytest.fixture(scope="class")
    def shop_login(self):
        r = _multi_login(SHOP_USER)
        if r.status_code != 200:
            pytest.skip(f"Shop user login unavailable: {r.status_code} {r.text[:200]}")
        return r.json()

    def test_pm_user_cannot_escalate_to_admin(self, pm_login):
        tok = _extract_directory_token(pm_login)
        assert tok, "pm directory token missing"
        r = requests.post(
            f"{BASE_URL}/api/auth/issue-portal-token",
            json={"portal": "admin"},
            headers={"X-Directory-Token": tok},
            timeout=15,
        )
        assert r.status_code == 403, (
            f"P0 SECURITY: pm escalated to admin! status={r.status_code} body={r.text[:300]}"
        )

    def test_pm_user_cannot_escalate_to_safety(self, pm_login):
        tok = _extract_directory_token(pm_login)
        r = requests.post(
            f"{BASE_URL}/api/auth/issue-portal-token",
            json={"portal": "safety"},
            headers={"X-Directory-Token": tok},
            timeout=15,
        )
        # PM should not have safety unless granted; expect 403
        if r.status_code == 200:
            # Could be PM also has safety. Verify by checking portals list
            r2 = requests.get(
                f"{BASE_URL}/api/auth/me-directory",
                headers={"X-Directory-Token": tok},
                timeout=15,
            )
            portals = (r2.json().get("user") or {}).get("portals") or []
            assert "safety" in portals, f"PM escalated to safety w/o grant. portals={portals}"
        else:
            assert r.status_code == 403, f"unexpected status {r.status_code} {r.text[:300]}"

    def test_hr_user_cannot_escalate_to_admin(self, hr_login):
        tok = _extract_directory_token(hr_login)
        r = requests.post(
            f"{BASE_URL}/api/auth/issue-portal-token",
            json={"portal": "admin"},
            headers={"X-Directory-Token": tok},
            timeout=15,
        )
        assert r.status_code == 403, (
            f"P0 SECURITY: hr escalated to admin! status={r.status_code} body={r.text[:300]}"
        )

    def test_shop_user_cannot_escalate_to_admin(self, shop_login):
        tok = _extract_directory_token(shop_login)
        r = requests.post(
            f"{BASE_URL}/api/auth/issue-portal-token",
            json={"portal": "admin"},
            headers={"X-Directory-Token": tok},
            timeout=15,
        )
        assert r.status_code == 403, (
            f"P0 SECURITY: shop escalated to admin! status={r.status_code} body={r.text[:300]}"
        )

    def test_unknown_portal_rejected(self, pm_login):
        tok = _extract_directory_token(pm_login)
        r = requests.post(
            f"{BASE_URL}/api/auth/issue-portal-token",
            json={"portal": "definitely_not_a_portal"},
            headers={"X-Directory-Token": tok},
            timeout=15,
        )
        assert r.status_code == 400

    def test_unauthenticated_request_rejected(self):
        r = requests.post(
            f"{BASE_URL}/api/auth/issue-portal-token",
            json={"portal": "admin"},
            timeout=15,
        )
        assert r.status_code == 401


# --- me-directory sanity ---
class TestMeDirectory:
    def test_super_admin_me_directory(self, super_admin_login):
        tok = _extract_directory_token(super_admin_login)
        r = requests.get(
            f"{BASE_URL}/api/auth/me-directory",
            headers={"X-Directory-Token": tok},
            timeout=15,
        )
        assert r.status_code == 200
        body = r.json()
        user = body.get("user") or {}
        portals = user.get("portals") or []
        # super-admin must have all canonical portals
        for p in ("admin", "pm", "hr", "shop", "safety", "dispatch", "field_leadership"):
            assert p in portals, f"super-admin missing {p}; portals={portals}"

    def test_me_directory_unauthenticated(self):
        r = requests.get(f"{BASE_URL}/api/auth/me-directory", timeout=15)
        assert r.status_code == 401
