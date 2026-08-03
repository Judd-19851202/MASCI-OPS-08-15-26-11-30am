"""TRACK 15.46 — Friction Reduction Backend Tests
Tests FR-02 (verdict reasons), FR-15 (recent-context prefill) endpoints.
"""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://masci-audit-hub.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(
        f"{BASE_URL}/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=30,
    )
    assert r.status_code == 200, f"multi-login failed: {r.status_code} {r.text[:200]}"
    body = r.json()
    tokens = body.get("portal_tokens") or {}
    tok = tokens.get("admin") or body.get("admin_token") or body.get("token")
    assert tok, f"no admin token in response: keys={list(body.keys())}"
    return tok


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    return {"X-Admin-Token": admin_token, "Content-Type": "application/json"}


# === FR-02 · Executive Overview verdict_reasons ===
class TestExecutiveOverviewVerdictReasons:
    def test_overview_returns_required_keys(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/executive/overview", headers=admin_headers, timeout=30)
        assert r.status_code == 200, f"got {r.status_code}: {r.text[:300]}"
        data = r.json()
        for key in ["verdict", "verdict_reasons", "tiles", "foundation_version"]:
            assert key in data, f"missing key '{key}' in response (keys={list(data.keys())})"

    def test_verdict_reasons_is_array_of_strings(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/executive/overview", headers=admin_headers, timeout=30)
        data = r.json()
        reasons = data["verdict_reasons"]
        assert isinstance(reasons, list), f"verdict_reasons must be list, got {type(reasons)}"
        for item in reasons:
            assert isinstance(item, str), f"reason must be string, got {type(item)}: {item!r}"
            assert len(item) > 0, "reason cannot be empty"

    def test_verdict_label_valid(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/executive/overview", headers=admin_headers, timeout=30)
        data = r.json()
        verdict = data["verdict"]
        # Accept color tokens or label tokens
        assert verdict in ("GREEN", "YELLOW", "RED", "HEALTHY", "NEEDS_ATTENTION", "ACTION_REQUIRED"), \
            f"unexpected verdict={verdict!r}"

    def test_verdict_reasons_present_when_not_green(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/executive/overview", headers=admin_headers, timeout=30)
        data = r.json()
        verdict = data["verdict"]
        reasons = data["verdict_reasons"]
        if verdict in ("YELLOW", "RED", "NEEDS_ATTENTION", "ACTION_REQUIRED"):
            assert len(reasons) >= 1, f"verdict={verdict} but no reasons supplied"


# === FR-15 · Daily Report recent-context prefill ===
class TestRecentContextPrefill:
    def test_recent_context_26_07_returns_required_keys(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/jobs/26-07/recent-context", headers=admin_headers, timeout=30)
        assert r.status_code == 200, f"got {r.status_code}: {r.text[:300]}"
        data = r.json()
        for key in ["superintendent", "masci_crews", "equipment", "source_report_date"]:
            assert key in data, f"missing key '{key}' (keys={list(data.keys())})"

    def test_recent_context_26_07_has_crews_and_equipment(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/jobs/26-07/recent-context", headers=admin_headers, timeout=30)
        data = r.json()
        crews = data.get("masci_crews") or []
        equipment = data.get("equipment") or []
        assert isinstance(crews, list)
        assert isinstance(equipment, list)
        assert len(crews) >= 1, f"expected >=1 crew, got {len(crews)}"
        assert len(equipment) >= 1, f"expected >=1 equipment row, got {len(equipment)}"

    def test_recent_context_does_not_include_signatures(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/jobs/26-07/recent-context", headers=admin_headers, timeout=30)
        data = r.json()
        # Per spec, prefill MUST NOT include signature / clock-time fields
        crews = data.get("masci_crews") or []
        for crew in crews:
            if isinstance(crew, dict):
                # Allow these fields to exist but should be empty/None
                for blocked in ("signature", "signature_data", "signed_at"):
                    val = crew.get(blocked)
                    assert val in (None, "", False), f"crew has populated {blocked}: {val!r}"

    def test_recent_context_unknown_job_handles_gracefully(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/jobs/ZZ-NONE-9999/recent-context", headers=admin_headers, timeout=30)
        # Should be 200 with empty arrays OR 404 — both acceptable
        assert r.status_code in (200, 404), f"got {r.status_code}: {r.text[:200]}"
        if r.status_code == 200:
            data = r.json()
            assert isinstance(data.get("masci_crews", []), list)
