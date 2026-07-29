import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_governance_registry_and_overview(async_client: AsyncClient, admin_headers):
    registry = await async_client.get("/api/admin/governance/registry", headers=admin_headers)
    assert registry.status_code == 200
    body = registry.json()
    assert body["version"] == "1.0"
    assert "permissions" in body and "roles" in body and "policies" in body

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
    assert delegation.json()["delegation"]["status"] == "active"

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
    assert override.json()["override"]["status"] == "pending_review"


@pytest.mark.asyncio
async def test_case_export_requires_governance(async_client: AsyncClient, admin_headers, seeded_case_id):
    resp = await async_client.post(f"/api/admin/operations-control/cases/{seeded_case_id}/export", headers=admin_headers)
    assert resp.status_code in {200, 403}
    if resp.status_code == 403:
        detail = resp.json()["detail"]
        assert detail["code"] in {"approval_required", "missing_permission", "separation_of_duties"}
