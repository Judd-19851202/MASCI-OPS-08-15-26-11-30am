from __future__ import annotations

import os
import time

import pytest
import requests

BASE_URL = os.environ.get("TEST_BASE_URL", "http://127.0.0.1:8001").rstrip("/")
ADMIN_EMAIL = "jaymn.judd@mascigc.com"
ADMIN_PASSWORD = "Maddix123!"


def _request(method, path, *, headers=None, json=None, timeout=30):
    last_error = None
    for _ in range(4):
        try:
            response = requests.request(
                method,
                f"{BASE_URL}{path}",
                headers=headers,
                json=json,
                timeout=timeout,
            )
            if response.status_code < 500:
                return response
            last_error = RuntimeError(f"server returned {response.status_code}")
        except Exception as exc:  # pragma: no cover - network retry branch
            last_error = exc
        time.sleep(1)
    raise last_error


@pytest.fixture(scope="module")
def auth_headers():
    response = _request("POST", "/api/auth/multi-login", json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}, timeout=20)
    response.raise_for_status()
    data = response.json()
    return {
        "X-Admin-Token": data["portal_tokens"]["admin"],
        "X-Directory-Token": data["session_token"],
    }


def _assert_ots_contract(payload, expected_claim=None):
    ots = payload.get("ots_truth")
    assert ots, "ots_truth must be present"
    for key in [
        "truth_subject",
        "canonical_owner",
        "evidence_state",
        "evidence_quality",
        "evidence_confidence",
        "truth_evaluation",
        "permitted_claim",
        "claim_ceiling",
        "claim_basis",
        "evaluation_timestamp",
        "audit_reference",
    ]:
        assert key in ots, f"ots_truth missing {key}"
    if expected_claim:
        assert ots["permitted_claim"] == expected_claim
    rel = payload.get("truth_relationship")
    assert rel, "truth_relationship must be present"
    compat = payload.get("compatibility")
    assert compat, "compatibility must be present"
    assert compat.get("breaking_api_changes") == 0


def test_platform_data_truth_ots_contract():
    response = _request("GET", "/api/platform/data-truth", timeout=20)
    response.raise_for_status()
    data = response.json()
    _assert_ots_contract(data, expected_claim="CORRELATED")
    assert data["verified"] == data["ok"], "legacy field should remain consistent"


def test_recovery_snapshot_ots_contract(auth_headers):
    response = _request("GET", "/api/admin/recovery/snapshot", headers=auth_headers, timeout=120)
    response.raise_for_status()
    data = response.json()
    _assert_ots_contract(data, expected_claim="CORRELATED")
    assert data["ots_truth"]["claim_ceiling"] == "CORRELATED"


def test_backup_verification_state_ots_contract(auth_headers):
    response = _request("GET", "/api/admin/backup-verification/state", headers=auth_headers, timeout=20)
    response.raise_for_status()
    data = response.json()
    _assert_ots_contract(data, expected_claim="OBSERVED")
    assert data["enabled"] in [True, False]


def test_backup_verification_preview_ots_contract(auth_headers):
    response = _request("GET", "/api/admin/backup-verification/preview", headers=auth_headers, timeout=120)
    response.raise_for_status()
    data = response.json()
    assert data.get("ok") is True
    report = data.get("report") or {}
    _assert_ots_contract(report)
    assert report["ots_truth"]["claim_ceiling"] == "VALIDATED"


def test_backup_trust_score_ots_contract(auth_headers):
    response = _request("GET", "/api/admin/backup-trust-score", headers=auth_headers, timeout=90)
    response.raise_for_status()
    data = response.json()
    _assert_ots_contract(data, expected_claim="CORRELATED")
    assert data["ots_truth"]["claim_ceiling"] == "CORRELATED"


def test_deployment_readiness_ots_contract(auth_headers):
    response = _request("GET", "/api/admin/deployment-readiness", headers=auth_headers, timeout=20)
    response.raise_for_status()
    data = response.json()
    _assert_ots_contract(data)
    assert data["decision"] in ["pass", "fail"]
    assert data["ots_truth"]["claim_ceiling"] == "CERTIFIED"


def test_deployment_history_contains_historical_ots_truth(auth_headers):
    response = _request("GET", "/api/admin/deployment-readiness/history?limit=1", headers=auth_headers, timeout=20)
    response.raise_for_status()
    data = response.json()
    if data.get("events"):
        row = data["events"][0]
        assert "ots_truth" in row, "historical ledger row must preserve ots_truth"
        assert row["ots_truth"]["claim_ceiling"] == "CERTIFIED"


def test_integration_truth_ots_contract(auth_headers):
    response = _request("GET", "/api/admin/integrations/truth-status", headers=auth_headers, timeout=20)
    response.raise_for_status()
    data = response.json()
    _assert_ots_contract(data, expected_claim="CORRELATED")
