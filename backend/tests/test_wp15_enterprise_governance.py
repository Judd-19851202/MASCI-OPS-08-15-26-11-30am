import os
from pathlib import Path
import asyncio

import httpx
import pytest
import pytest_asyncio
from httpx import AsyncClient


def _base_url() -> str:
    env_value = os.environ.get("REACT_APP_BACKEND_URL")
    if env_value:
        return env_value.rstrip("/")
    for line in Path("/app/frontend/.env").read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            return line.split("=", 1)[1].strip().rstrip("/")
    raise RuntimeError("REACT_APP_BACKEND_URL is required for WP-15 integration tests")


@pytest_asyncio.fixture
async def async_client() -> AsyncClient:
    async with httpx.AsyncClient(base_url=_base_url(), timeout=60.0) as client:
        yield client


@pytest_asyncio.fixture
async def tokens(async_client: AsyncClient) -> dict:
    last_status = None
    for _ in range(10):
        try:
            resp = await async_client.post(
                "/api/auth/multi-login",
                json={"email": "jaymn.judd@mascigc.com", "password": "Maddix123!"},
            )
            last_status = resp.status_code
            if resp.status_code == 200:
                return resp.json()
        except httpx.HTTPError:
            last_status = "http_error"
        await asyncio.sleep(2)
    raise AssertionError(f"multi-login did not recover, last status={last_status}")


@pytest.fixture
def admin_headers(tokens: dict) -> dict:
    return {
        "X-Admin-Token": tokens["portal_tokens"]["admin"],
        "X-Directory-Token": tokens["session_token"],
    }


@pytest.fixture
def admin_actor() -> dict:
    return {
        "id": "wp15-admin",
        "email": "jaymn.judd@mascigc.com",
        "name": "WP15 Admin",
        "role": "admin",
        "is_super_admin": True,
    }


@pytest_asyncio.fixture
async def seeded_case_id(async_client: AsyncClient, admin_headers: dict) -> str:
    resp = await async_client.get("/api/admin/operations-control/cases", headers=admin_headers)
    assert resp.status_code == 200
    rows = resp.json()
    items = rows if isinstance(rows, list) else rows.get("items") or rows.get("cases") or []
    assert items, "Expected at least one seeded operations-control case"
    return items[0]["id"]


@pytest.mark.asyncio
async def test_governance_registry_and_overview(async_client: AsyncClient, admin_headers):
    registry = await async_client.get("/api/admin/governance/registry", headers=admin_headers)
    assert registry.status_code == 200
    body = registry.json()
    assert body["version"] == "1.0"
    assert "permissions" in body and "roles" in body and "policies" in body
    assert "governance_determinism_principle" in body.get("constitutional_principles", [])

    overview = await async_client.get("/api/admin/governance/overview", headers=admin_headers)
    assert overview.status_code == 200
    summary = overview.json()
    assert "counts" in summary
    assert summary["counts"]["roles"] >= 1


@pytest.mark.asyncio
async def test_governance_identity_projection(async_client: AsyncClient, admin_headers, admin_actor):
    resp = await async_client.post("/api/admin/governance/identities/project", headers=admin_headers, json=admin_actor)
    assert resp.status_code == 200
    body = resp.json()
    assert body["canonical_user_id"]
    assert body["identity_source"]


@pytest.mark.asyncio
async def test_governance_delegation_and_override(async_client: AsyncClient, admin_headers):
    delegation = await async_client.post(
        "/api/admin/governance/delegations",
        headers=admin_headers,
        json={
            "delegate_user_id": "delegated-user-1",
            "delegate_email": "delegate@example.com",
            "permissions": ["task.assign", "notification.ack"],
            "delegation_type": "temporary_delegation",
            "reason": "Coverage",
            "expires_at": "2099-01-01T00:00:00+00:00",
        },
    )
    assert delegation.status_code == 200
    delegation_body = delegation.json()["delegation"]
    assert delegation_body["status"] == "active"
    assert delegation_body["delegation_id"]
    assert delegation_body["delegator_snapshot"]["canonical_user_id"]

    override = await async_client.post(
        "/api/admin/governance/emergency-overrides",
        headers=admin_headers,
        json={
            "action_key": "operational_case.close",
            "module_key": "operations_control",
            "record_type": "operational_case",
            "record_id": "case-123",
            "company_id": "masci",
            "project_number": "24-06",
            "denied_policy_id": "operational_case_close_policy",
            "justification": "Operational urgency for preview test",
            "operational_urgency": "urgent",
            "evidence": ["preview evidence"],
            "expires_at": "2099-01-01T00:00:00+00:00",
        },
    )
    assert override.status_code == 200
    override_body = override.json()["override"]
    assert override_body["status"] == "pending_review"
    assert override_body["override_id"]
    assert override_body["policy_snapshot"]["policy_id"] == "operational_case_close_policy"
    assert "communications" in override_body
    assert "communication_error" in override_body


@pytest.mark.asyncio
async def test_governance_decisions_are_explainable_and_immutable(async_client: AsyncClient, admin_headers, seeded_case_id):
    trigger = await async_client.post(f"/api/admin/operations-control/cases/{seeded_case_id}/export", headers=admin_headers)
    assert trigger.status_code in {200, 403}

    decisions = await async_client.get("/api/admin/governance/decisions", headers=admin_headers)
    assert decisions.status_code == 200
    items = decisions.json()["items"]
    assert items
    latest = next((row for row in items if row.get("decision_id") and row.get("determinism_fingerprint")), None)
    assert latest is not None
    assert latest["decision_id"]
    assert latest["correlation_id"]
    assert latest["policy_version"]
    assert latest["policy_effective_at"]
    assert latest["decision_timestamp"]
    assert latest["immutable"] is True
    assert latest["record_mode"] == "append_only"
    assert latest["determinism_fingerprint"]
    assert latest["identity_snapshot"]["canonical_user_id"]
    assert "project_assignments" in latest["identity_snapshot"]
    assert latest["policy_evaluation"]["evaluation_outcome"] in {"allow", "deny"}
    assert latest["explanation"]["decision"] in {"APPROVED", "DENIED"}
    assert latest["explanation"]["trust_spine"]["recorded"] is True


@pytest.mark.asyncio
async def test_case_export_requires_governance(async_client: AsyncClient, admin_headers, seeded_case_id):
    resp = await async_client.post(f"/api/admin/operations-control/cases/{seeded_case_id}/export", headers=admin_headers)
    assert resp.status_code in {200, 403}
    if resp.status_code == 403:
        detail = resp.json()["detail"]
        assert detail["code"] in {"approval_required", "missing_permission", "separation_of_duties"}
        assert detail["decision_id"]
        assert detail["policy_id"]
        assert detail["policy_version"]
        assert detail["explanation"]["decision"] == "DENIED"
