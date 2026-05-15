"""
Iter142 — Integration health probes + alert emission + deploy-readiness.
Tests against the live preview backend via REACT_APP_BACKEND_URL.
"""
import os
import time
from datetime import datetime

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "https://safety-audit-mobile-1.preview.emergentagent.com").rstrip("/")
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"

EXPECTED_PROBE_IDS = {"mongo", "r2", "resend", "maintainx", "motive", "emergent_llm"}


@pytest.fixture(scope="module")
def admin_token():
    r = requests.post(f"{BASE_URL}/api/auth/multi-login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
                      timeout=15)
    assert r.status_code == 200, f"multi-login failed: {r.status_code} {r.text}"
    data = r.json()
    tok = data.get("token") or data.get("directory_token") or data.get("session_token")
    # Need to find the admin portal token. Look at endpoints commonly used.
    if not tok:
        pytest.skip(f"Login returned no token: {data}")
    return tok


@pytest.fixture(scope="module")
def admin_headers(admin_token):
    # Most admin endpoints use X-Admin-Token. Try issuing a portal token.
    sess = requests.Session()
    # Try issue portal admin token
    r = sess.post(
        f"{BASE_URL}/api/auth/issue-portal-token",
        json={"portal": "admin"},
        headers={"X-Directory-Token": admin_token},
        timeout=10,
    )
    portal_tok = None
    if r.status_code == 200:
        portal_tok = r.json().get("token")
    # Fallback: legacy admin login
    if not portal_tok:
        r2 = requests.post(f"{BASE_URL}/api/admin/login",
                           json={"password": "MASCI1982!"},
                           timeout=10)
        if r2.status_code == 200:
            portal_tok = r2.json().get("token")
    if not portal_tok:
        pytest.skip("Could not obtain admin portal token")
    return {"X-Admin-Token": portal_tok, "Content-Type": "application/json"}


# ── Integration Health Endpoint ──────────────────────────────────────
class TestIntegrationHealth:
    def test_health_returns_6_probes(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/integrations/health",
                         headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "overall_status" in data
        assert data["overall_status"] in ("ok", "degraded", "down")
        assert "checked_at" in data
        # parse ISO
        datetime.fromisoformat(data["checked_at"].replace("Z", "+00:00"))
        assert "probes" in data and isinstance(data["probes"], list)
        assert len(data["probes"]) == 6
        ids = {p["id"] for p in data["probes"]}
        assert ids == EXPECTED_PROBE_IDS, f"Got: {ids}"
        for p in data["probes"]:
            assert {"id", "name", "status", "latency_ms", "message", "checked_at"}.issubset(p.keys())
            assert p["status"] in ("ok", "degraded", "down", "disabled")
            assert isinstance(p["latency_ms"], int)

    def test_probe_status_expectations(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/integrations/health",
                         headers=admin_headers, timeout=15)
        data = r.json()
        by_id = {p["id"]: p for p in data["probes"]}
        # Mongo and R2 must be ok
        assert by_id["mongo"]["status"] == "ok", by_id["mongo"]
        assert by_id["r2"]["status"] == "ok", by_id["r2"]
        # Resend ok or degraded
        assert by_id["resend"]["status"] in ("ok", "degraded"), by_id["resend"]
        # MaintainX, Motive disabled + mocked
        assert by_id["maintainx"]["status"] == "disabled", by_id["maintainx"]
        assert by_id["maintainx"].get("mocked") is True
        assert by_id["motive"]["status"] == "disabled", by_id["motive"]
        assert by_id["motive"].get("mocked") is True
        # Emergent LLM ok
        assert by_id["emergent_llm"]["status"] == "ok", by_id["emergent_llm"]

    def test_probe_timeout_safety(self, admin_headers):
        """Even with a slow probe, response should be 200, not 500."""
        t0 = time.time()
        r = requests.get(f"{BASE_URL}/api/admin/integrations/health",
                         headers=admin_headers, timeout=15)
        elapsed = time.time() - t0
        assert r.status_code == 200
        # Should complete in well under 6s thanks to 5s per-probe timeout
        assert elapsed < 8, f"Took {elapsed}s"


# ── Alert Emission Idempotency ───────────────────────────────────────
class TestAlertEmission:
    def test_emit_alerts_idempotent(self, admin_headers):
        # First call
        r1 = requests.get(f"{BASE_URL}/api/admin/integrations/health?emit_alerts=true",
                          headers=admin_headers, timeout=15)
        assert r1.status_code == 200
        d1 = r1.json()
        assert "alerts_emitted" in d1
        # Second call right after — should be 0 because nothing changed
        r2 = requests.get(f"{BASE_URL}/api/admin/integrations/health?emit_alerts=true",
                          headers=admin_headers, timeout=15)
        assert r2.status_code == 200
        d2 = r2.json()
        assert d2["alerts_emitted"] == 0, f"Idempotency broken: {d2}"

    def test_alerts_list_iso_dates(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/integrations/alerts",
                         headers=admin_headers, timeout=15)
        assert r.status_code == 200
        data = r.json()
        assert "rows" in data and "count" in data
        assert data["count"] == len(data["rows"])
        # Newest first
        ats = [row["at"] for row in data["rows"]]
        # All `at` must be ISO strings, never datetime / dict
        for a in ats:
            assert isinstance(a, str), f"at is not str: {type(a)}"
            datetime.fromisoformat(a.replace("Z", "+00:00"))
        # Verify sort newest-first
        assert ats == sorted(ats, reverse=True), "Not sorted newest first"
        # disabled probes (maintainx, motive) MUST never appear in alerts
        for row in data["rows"]:
            assert row.get("status") != "disabled", f"disabled in alerts: {row}"


# ── Deploy Readiness ─────────────────────────────────────────────────
class TestDeployReadiness:
    def test_deploy_readiness_includes_integrations(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/deploy-readiness",
                         headers=admin_headers, timeout=15)
        assert r.status_code == 200, r.text
        data = r.json()
        assert "overall_status" in data
        assert data["overall_status"] != "blocked", data
        checks = data.get("checks") or data.get("detail_checks") or []
        assert len(checks) == 12, f"Expected 12 checks, got {len(checks)}: {[c.get('id') for c in checks]}"
        ids = {c.get("id") for c in checks}
        assert "integrations_health" in ids, f"Missing integrations_health: {ids}"
