from __future__ import annotations

import os
import time
from pathlib import Path

import pytest
import requests


def _default_base_url():
    configured = os.environ.get("TEST_BASE_URL")
    if configured:
        return configured.rstrip("/")
    frontend_env = Path("/app/frontend/.env")
    if frontend_env.exists():
        for line in frontend_env.read_text().splitlines():
            if line.startswith("REACT_APP_BACKEND_URL="):
                return line.split("=", 1)[1].strip().rstrip("/")
    return "http://127.0.0.1:8001"


BASE_URL = _default_base_url()
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
        except Exception as exc:
            last_error = exc
        time.sleep(1)
    raise last_error


@pytest.fixture(scope="module")
def auth_headers():
    response = _request(
        "POST",
        "/api/auth/multi-login",
        json={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
        timeout=20,
    )
    response.raise_for_status()
    data = response.json()
    return {
        "X-Admin-Token": data["portal_tokens"]["admin"],
        "X-Directory-Token": data["session_token"],
    }


def test_trust_spine_ots_contract(auth_headers):
    response = _request("GET", "/api/admin/trust-spine", headers=auth_headers, timeout=20)
    response.raise_for_status()
    payload = response.json()

    for field in [
        "track",
        "generated_at",
        "platform_band",
        "canonical_status",
        "truth_surface",
        "truth_relationship",
        "total_events_24h",
        "total_failed_24h",
        "workflow_count",
        "workflows",
        "allowed_stages",
        "ots_truth",
        "compatibility",
    ]:
        assert field in payload

    ots = payload["ots_truth"]
    for field in [
        "truth_subject",
        "canonical_owner",
        "evidence_state",
        "evidence_quality",
        "evidence_confidence",
        "truth_evaluation",
        "permitted_claim",
        "claim_ceiling",
        "claim_basis",
        "unknowns",
        "contradictory_evidence",
        "evaluation_timestamp",
        "audit_reference",
    ]:
        assert field in ots
    assert ots["claim_ceiling"] == "VALIDATED"
    assert payload["compatibility"]["breaking_api_changes"] == 0

    if payload["workflows"]:
        row = payload["workflows"][0]
        assert "ots_truth" in row
        assert "truth_relationship" in row
        assert row["ots_truth"]["claim_ceiling"] == "VALIDATED"
