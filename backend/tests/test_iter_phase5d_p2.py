"""Phase 5D · P2 — FL token (X-FL-Token) accepted by /api/notifications.

Verifies the one-file backend change in routes/integrations/_deps.py:
  - X-FL-Token now resolves a per-user FL account on /api/notifications.
  - No regression on the existing 6 portal tokens.
  - No-token / bad-token still returns 401.
  - Public/anonymous incident POST still works.
  - Governance / incidents.csv / corrective-actions endpoints still 200.
"""
import os
import time
import uuid
import requests
import pytest

BASE_URL = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
API = f"{BASE_URL}/api"

SUPER_EMAIL = "jaymn.judd@mascigc.com"
SUPER_PW = "Maddix123!"
FL_EMAIL = "fieldleader@mascigc.com"
FL_PW = "FieldLead2026!"


@pytest.fixture(scope="module")
def portal_tokens():
    """Multi-login → per-portal tokens for admin/safety/hr/pm/shop/dispatch."""
    r = requests.post(f"{API}/auth/multi-login",
                      json={"email": SUPER_EMAIL, "password": SUPER_PW}, timeout=30)
    assert r.status_code == 200, f"multi-login failed: {r.status_code} {r.text}"
    tokens = r.json().get("portal_tokens") or {}
    assert tokens.get("admin"), "no admin token returned"
    return tokens


@pytest.fixture(scope="module")
def fl_token():
    r = requests.post(f"{API}/field-leadership/portal/login",
                      json={"email": FL_EMAIL, "password": FL_PW}, timeout=30)
    assert r.status_code == 200, f"FL login failed: {r.status_code} {r.text}"
    body = r.json()
    tok = body.get("token")
    assert tok and "." in tok, f"FL token malformed: {tok!r}"
    return tok


# ─── P2: FL token now accepted on /api/notifications ─────────────────
class TestFLNotificationsAcceptance:
    def test_fl_notifications_returns_200(self, fl_token):
        r = requests.get(f"{API}/notifications",
                         headers={"X-FL-Token": fl_token}, timeout=20)
        assert r.status_code == 200, f"FL /notifications expected 200, got {r.status_code}: {r.text[:200]}"
        body = r.json()
        assert "items" in body and "count" in body, f"shape: {list(body.keys())}"
        assert isinstance(body["items"], list)
        assert isinstance(body["count"], int)

    def test_fl_unread_count_returns_200(self, fl_token):
        r = requests.get(f"{API}/notifications/unread-count",
                         headers={"X-FL-Token": fl_token}, timeout=20)
        assert r.status_code == 200, f"expected 200, got {r.status_code}: {r.text[:200]}"

    def test_fl_random_token_rejected(self):
        bad = f"{uuid.uuid4().hex}.{uuid.uuid4().hex}"
        # X-Admin-Token="" suppresses conftest auto-inject of admin token
        r = requests.get(f"{API}/notifications",
                         headers={"X-FL-Token": bad, "X-Admin-Token": ""}, timeout=20)
        assert r.status_code == 401, f"random FL token should 401, got {r.status_code}"


# ─── P2 regression: existing portals still work + no-token still 401 ──
class TestNotificationsRegression:
    def test_no_token_401(self):
        # X-Admin-Token="" suppresses conftest auto-inject; nothing else set
        r = requests.get(f"{API}/notifications",
                         headers={"X-Admin-Token": ""}, timeout=20)
        assert r.status_code == 401

    def test_no_token_unread_401(self):
        r = requests.get(f"{API}/notifications/unread-count",
                         headers={"X-Admin-Token": ""}, timeout=20)
        assert r.status_code == 401

    @pytest.mark.parametrize("hdr_key", [
        "X-Admin-Token", "X-Safety-Token", "X-HR-Token",
        "X-PM-Token", "X-Dispatch-Token", "X-Shop-Token",
    ])
    def test_existing_portal_tokens_still_200(self, portal_tokens, hdr_key):
        portal_key = hdr_key.replace("X-", "").replace("-Token", "").lower()
        # Map header name back to multi-login key
        key_map = {"admin": "admin", "safety": "safety", "hr": "hr",
                   "pm": "pm", "dispatch": "dispatch", "shop": "shop"}
        tok = portal_tokens.get(key_map[portal_key])
        if not tok:
            pytest.skip(f"no {portal_key} token in multi-login response")
        r = requests.get(f"{API}/notifications",
                         headers={hdr_key: tok}, timeout=20)
        assert r.status_code == 200, f"{hdr_key} expected 200, got {r.status_code}: {r.text[:200]}"


# ─── Phase 5D smoke: zero-regression checks on adjacent endpoints ─────
class TestPhase5DSmoke:
    def test_governance_summary_200(self, portal_tokens):
        r = requests.get(f"{API}/admin/governance/summary",
                         headers={"X-Admin-Token": portal_tokens["admin"]}, timeout=30)
        assert r.status_code == 200, f"governance summary: {r.status_code} {r.text[:200]}"

    def test_incidents_csv_200(self, portal_tokens):
        r = requests.get(f"{API}/incidents.csv",
                         headers={"X-Admin-Token": portal_tokens["admin"]}, timeout=30)
        assert r.status_code == 200

    def test_corrective_actions_list_200(self, portal_tokens):
        # CAPA list requires safety token specifically (admin not sufficient)
        tok = portal_tokens.get("safety")
        if not tok:
            pytest.skip("no safety token")
        r = requests.get(f"{API}/safety/corrective-actions",
                         headers={"X-Safety-Token": tok}, timeout=30)
        assert r.status_code == 200, f"CAPA list: {r.status_code} {r.text[:200]}"

    def test_anonymous_incident_post_still_works(self):
        idem = f"TEST_iter5d_{uuid.uuid4().hex[:8]}"
        payload = {
            "project_name": "TEST_phase5d",
            "project_number": "TEST-0000",
            "incident_date": "2026-01-15",
            "incident_time": "10:00",
            "location": "TEST_field",
            "incident_type": "Near Miss",
            "severity": "low",
            "description": "Phase 5D anonymous POST regression test",
            "reported_date": "2026-01-15",
            "reported_by": "Pytest",
            "supervisor_name": "Pytest Sup",
            "idempotency_key": idem,
        }
        r = requests.post(f"{API}/incidents", json=payload, timeout=30)
        assert r.status_code == 200, f"public incident POST: {r.status_code} {r.text[:300]}"
        body = r.json()
        # Backend either returns the doc directly or nested in {ok, record}
        rec = body.get("record") or body
        assert rec.get("id"), f"no id in response: {body}"
        assert rec.get("doc_id"), f"no doc_id in response: {body}"
