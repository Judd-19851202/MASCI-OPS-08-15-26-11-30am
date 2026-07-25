"""TRACK 25 · SPRINT 7/8 · Trust Events aggregator tests."""
import os

import pytest
import requests
from fastapi import APIRouter, FastAPI
from fastapi.testclient import TestClient

from routes.occ_trust_events import register_occ_trust_events_routes

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://backup-forensics.preview.emergentagent.com').rstrip('/')
ADMIN_EMAIL = 'jaymn.judd@mascigc.com'
ADMIN_PASS = 'Maddix123!'


@pytest.fixture(scope='module')
def admin_headers():
    r = requests.post(f"{BASE_URL}/api/auth/multi-login",
                      json={"email": ADMIN_EMAIL, "password": ADMIN_PASS}, timeout=45)
    assert r.status_code == 200, f"Login failed: {r.status_code} {r.text[:300]}"
    data = r.json()
    tok = (data.get('portal_tokens') or {}).get('admin') or data.get('token')
    assert tok, f"No admin token in response: {list(data.keys())}"
    session_token = data.get('session_token')
    assert session_token, f"No directory session token in response: {list(data.keys())}"
    return {"X-Admin-Token": tok, "X-Directory-Token": session_token}


class TestOccTrustEvents:
    def test_endpoint_reachable(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/occ/trust-events",
                         headers=admin_headers,
                         timeout=20)
        assert r.status_code == 200, f"{r.status_code}: {r.text[:400]}"
        body = r.json()
        # envelope
        for key in ("generated_at", "counts", "by_kind", "auth_failures_in_window",
                    "unresolved_blockers", "events", "probe_errors"):
            assert key in body, f"Missing '{key}' in envelope: {list(body.keys())}"
        assert isinstance(body["counts"], dict)
        for sev in ("info", "warning", "critical"):
            assert sev in body["counts"]
        assert isinstance(body["events"], list)
        assert isinstance(body["unresolved_blockers"], list)
        assert isinstance(body["by_kind"], dict)
        assert isinstance(body["auth_failures_in_window"], int)

    def test_requires_admin(self):
        r = requests.get(f"{BASE_URL}/api/admin/occ/trust-events", timeout=30)
        assert r.status_code in (401, 403), f"Expected 401/403 without auth, got {r.status_code}"

    def test_event_shape(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/occ/trust-events?limit=10",
                         headers=admin_headers, timeout=20)
        assert r.status_code == 200
        for ev in r.json()["events"]:
            for k in ("ts", "kind", "severity", "summary", "source_endpoint", "evidence"):
                assert k in ev, f"Event missing '{k}': {ev}"
            assert ev["severity"] in ("info", "warning", "critical")

    def test_deployment_verification_event_is_classified(self, admin_headers):
        r = requests.get(f"{BASE_URL}/api/admin/occ/trust-events?limit=50",
                         headers=admin_headers, timeout=20)
        assert r.status_code == 200
        deploy_events = [ev for ev in r.json()["events"] if ev.get("kind") == "deploy"]
        assert deploy_events, "expected at least one deploy event in trust feed"


def _build_test_app():
    app = FastAPI()
    api_router = APIRouter(prefix="/api")

    def require_admin():
        return {"role": "admin"}

    register_occ_trust_events_routes(api_router, require_admin)
    app.include_router(api_router)
    return app


def test_occ_trust_events_binds_to_trust_spine_and_canonical_deployment_readiness(monkeypatch):
    calls = []

    async def fake_get(_client, path, headers):  # noqa: ARG001
        calls.append(path)
        if path.startswith("/api/admin/audit"):
            return {"entries": [{"at": "2026-07-25T20:00:00+00:00", "actor_email": "ops@example.com", "action": "login_failure", "outcome": "failed"}]}
        if path.startswith("/api/admin/scheduler-runs"):
            return {"items": [{"started_at": "2026-07-25T19:59:00+00:00", "scheduler": "po_digest", "slot_key": "slot-1", "status": "done"}]}
        if path.startswith("/api/admin/operations-control/audit"):
            return {"audit": [{"ts": "2026-07-25T19:58:00+00:00", "operation_id": "op-1", "mode": "apply", "action_id": "oa-1"}]}
        if path == "/api/admin/deployment-readiness":
            return {
                "generated_at": "2026-07-25T19:57:00+00:00",
                "decision": "pass",
                "blocking_gates": [],
                "advisory_findings": [{"id": "advisory-1", "category": "workflow", "summary": "Preview advisory", "evidence": "sample", "remediation": "inspect"}],
                "truth_relationship": {
                    "role": "CANONICAL_OWNER",
                    "canonical_owner_id": "bcss_recovery_certification",
                    "canonical_owner_route": "/api/admin/deployment-readiness",
                },
            }
        if path == "/api/admin/trust-spine":
            return {
                "truth_relationship": {
                    "role": "CANONICAL_OWNER",
                    "canonical_owner_id": "trust_spine",
                    "canonical_owner_route": "/api/admin/trust-spine",
                }
            }
        raise AssertionError(f"unexpected path {path}")

    monkeypatch.setattr("routes.occ_trust_events._get", fake_get)

    client = TestClient(_build_test_app())
    response = client.get("/api/admin/occ/trust-events")

    assert response.status_code == 200
    body = response.json()
    assert "/api/admin/deployment-readiness" in calls
    assert "/api/admin/deploy-readiness" not in calls
    assert "/api/admin/trust-spine" in calls
    assert body["truth_surface"]["surface_id"] == "occ_trust_events"
    assert body["truth_relationship"]["role"] == "AGGREGATOR"
    assert body["truth_relationship"]["canonical_owner_id"] == "trust_spine"
    assert body["truth_relationship"]["canonical_owner_route"] == "/api/admin/trust-spine"
    assert body["ots_truth"]["truth_subject"] == "shared_operational_trust_event_feed"
    assert body["ots_truth"]["claim_ceiling"] == "OBSERVED"
    assert body["compatibility"]["breaking_api_changes"] == 0
    for key in ("generated_at", "counts", "by_kind", "auth_failures_in_window", "unresolved_blockers", "events", "probe_errors"):
        assert key in body


def test_occ_trust_events_suppresses_exact_duplicates_and_discloses_conflicts(monkeypatch):
    async def fake_get(_client, path, headers):  # noqa: ARG001
        if path.startswith("/api/admin/audit"):
            return {
                "entries": [
                    {"at": "2026-07-25T20:00:00+00:00", "actor_email": "ops@example.com", "action": "multi_login", "outcome": "ok"},
                    {"at": "2026-07-25T20:00:00+00:00", "actor_email": "ops@example.com", "action": "multi_login", "outcome": "ok"},
                ]
            }
        if path.startswith("/api/admin/scheduler-runs"):
            return {"items": []}
        if path.startswith("/api/admin/operations-control/audit"):
            return {"audit": []}
        if path == "/api/admin/deployment-readiness":
            return {
                "generated_at": "2026-07-25T19:57:00+00:00",
                "decision": "pass",
                "blocking_gates": [{"id": "gate-1", "summary": "should not coexist with pass", "category": "workflow", "evidence": "sample", "remediation": "inspect"}],
                "advisory_findings": [],
                "truth_relationship": {
                    "role": "CANONICAL_OWNER",
                    "canonical_owner_id": "bcss_recovery_certification",
                    "canonical_owner_route": "/api/admin/deployment-readiness",
                },
            }
        if path == "/api/admin/trust-spine":
            return {
                "truth_relationship": {
                    "role": "DERIVED_CONSUMER",
                    "canonical_owner_id": "trust_spine",
                    "canonical_owner_route": "/api/admin/trust-spine",
                }
            }
        raise AssertionError(f"unexpected path {path}")

    monkeypatch.setattr("routes.occ_trust_events._get", fake_get)

    client = TestClient(_build_test_app())
    response = client.get("/api/admin/occ/trust-events")

    assert response.status_code == 200
    body = response.json()
    assert body["duplicate_suppression_count"] == 1
    assert len([ev for ev in body["events"] if ev["kind"] == "auth"]) == 1
    assert body["truth_relationship"]["has_conflict"] is True
    assert any("Trust Spine authority verification failed" in item for item in body["truth_relationship"]["conflicts"])
    assert any("reported pass while blocking gates were still present" in item for item in body["truth_relationship"]["conflicts"])
