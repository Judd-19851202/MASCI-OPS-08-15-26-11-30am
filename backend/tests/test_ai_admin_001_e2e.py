"""End-to-end verification for AI-ADMIN-001 admin AI configuration endpoints via public URL."""
import os
import re
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    # fall back to reading frontend env
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")

ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=30,
    )
    assert r.status_code == 200, f"multi-login failed: {r.status_code} {r.text[:400]}"
    data = r.json()
    # tokens are in portal_tokens.admin
    token = (data.get("portal_tokens") or {}).get("admin")
    assert token, f"admin token missing in {list(data.keys())}"
    return token


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"X-Admin-Token": admin_token, "Content-Type": "application/json"}


def _no_sk_key(text: str):
    """Ensure no 'sk-<something>' style raw key present."""
    matches = re.findall(r"sk-[A-Za-z0-9_\-]{10,}", text)
    assert not matches, f"Found raw API key(s) in response: {matches[:3]}"


class TestAuthGating:
    def test_status_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/admin/ai/config/status", timeout=15)
        assert r.status_code in (401, 403), f"expected 401/403, got {r.status_code}"

    def test_tenants_requires_auth(self):
        r = requests.get(f"{BASE_URL}/api/admin/ai/tenants", timeout=15)
        assert r.status_code in (401, 403)

    def test_put_requires_auth(self):
        r = requests.put(
            f"{BASE_URL}/api/admin/ai/tenants/masci/capabilities",
            json={"tenant_ai_enabled": True},
            timeout=15,
        )
        assert r.status_code in (401, 403)


class TestStatusEndpoint:
    def test_status_ok_and_no_keys(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/ai/config/status", headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text[:400]
        body = r.json()
        _no_sk_key(r.text)
        providers = body.get("providers") or {}
        assert providers, "providers dict missing"
        for name, meta in providers.items():
            assert "key_present" in meta, f"{name} missing key_present"
            assert isinstance(meta["key_present"], bool), f"{name}.key_present not bool"

    def test_tenants_contains_masci(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/ai/tenants", headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text[:400]
        body = r.json()
        tenants = body.get("tenants") if isinstance(body, dict) else body
        assert tenants, f"no tenants in response: {body}"
        ids = [t.get("id") or t.get("tenant_id") or t.get("slug") or t for t in tenants]
        assert any("masci" in str(x).lower() for x in ids), f"masci not found in {ids}"


class TestProviderTest:
    def test_anthropic_test_endpoint(self, admin_headers):
        r = requests.post(
            f"{BASE_URL}/api/admin/ai/providers/anthropic/test",
            headers=admin_headers,
            timeout=30,
        )
        assert r.status_code == 200, r.text[:400]
        body = r.json()
        for k in ("provider", "flag_env", "flag_enabled", "key_env", "key_present", "status"):
            assert k in body, f"missing key {k} in {list(body.keys())}"
        _no_sk_key(r.text)
        # explicit check: real ANTHROPIC_API_KEY value must not be present
        real = os.environ.get("ANTHROPIC_API_KEY", "")
        if real and len(real) > 8:
            assert real not in r.text, "Real ANTHROPIC_API_KEY leaked in response!"


class TestCapabilitiesRoundTrip:
    def test_put_and_audit(self, admin_headers):
        # flip on
        payload = {
            "tenant_ai_enabled": True,
            "daily_report_summary_enabled": True,
            "note": "Testing agent verification",
        }
        r = requests.put(
            f"{BASE_URL}/api/admin/ai/tenants/masci/capabilities",
            headers=admin_headers,
            json=payload,
            timeout=20,
        )
        assert r.status_code == 200, r.text[:500]
        body = r.json()
        assert "changed_fields" in body, f"changed_fields missing: {list(body.keys())}"
        assert "modules" in body, f"modules missing: {list(body.keys())}"
        _no_sk_key(r.text)

        # audit
        ar = requests.get(
            f"{BASE_URL}/api/admin/ai/tenants/masci/audit",
            headers=admin_headers,
            timeout=15,
        )
        assert ar.status_code == 200, ar.text[:400]
        abody = ar.json()
        entries = abody.get("entries") or abody.get("audit") or (abody if isinstance(abody, list) else [])
        assert entries, f"no audit entries: {abody}"
        first = entries[0]
        # actor non-empty or note matches
        actor = first.get("actor") or first.get("actor_email") or ""
        note = first.get("note") or ""
        assert actor or "Testing agent" in note, f"neither actor nor note present: {first}"
        _no_sk_key(ar.text)

    def test_cleanup_reset(self, admin_headers):
        payload = {
            "tenant_ai_enabled": False,
            "daily_report_summary_enabled": False,
            "note": "test cleanup",
        }
        r = requests.put(
            f"{BASE_URL}/api/admin/ai/tenants/masci/capabilities",
            headers=admin_headers,
            json=payload,
            timeout=20,
        )
        assert r.status_code == 200, r.text[:500]
