from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from lib.enterprise_governance import resolve_actor_from_request

from services.enterprise_governance import (
    approve_request,
    create_delegation,
    create_emergency_override,
    ensure_enterprise_governance_registry,
    ensure_identity_projection,
    get_enterprise_governance_registry,
    get_governance_overview,
    list_approval_requests,
    list_decisions,
    list_delegations,
    list_identity_projections,
    list_org_nodes,
    list_overrides,
    seed_governance_admin_surface,
)


class GovernanceEvaluationBody(BaseModel):
    action_key: str = Field(..., min_length=2, max_length=120)
    resource_type: str = Field(..., min_length=2, max_length=120)
    resource: Dict[str, Any] = Field(default_factory=dict)
    requested_context: Dict[str, Any] = Field(default_factory=dict)


class DelegationBody(BaseModel):
    delegate_user_id: str = Field(..., min_length=2, max_length=120)
    delegate_email: str = Field(..., min_length=5, max_length=160)
    permissions: List[str] = Field(default_factory=list)
    delegation_type: str = "temporary_delegation"
    reason: str = ""
    expires_at: str = ""


class ApprovalBody(BaseModel):
    note: str = ""


class OverrideBody(BaseModel):
    action_key: str = Field(..., min_length=2, max_length=120)
    module_key: str = Field(..., min_length=2, max_length=120)
    record_type: str = Field(..., min_length=2, max_length=120)
    record_id: str = Field(..., min_length=2, max_length=160)
    company_id: str = "masci"
    project_number: str = ""
    denied_policy_id: str = ""
    justification: str = Field(..., min_length=8, max_length=2000)
    operational_urgency: str = Field(..., min_length=2, max_length=200)
    evidence: List[str] = Field(default_factory=list)
    expires_at: str = ""


def register_enterprise_governance_routes(api_router: APIRouter, db, require_admin) -> None:
    @api_router.get("/api/admin/governance/overview")
    async def governance_overview(actor=Depends(require_admin)):
        await ensure_enterprise_governance_registry(db)
        await seed_governance_admin_surface(db)
        return await get_governance_overview(db)

    @api_router.get("/api/admin/governance/registry")
    async def governance_registry(actor=Depends(require_admin)):
        await ensure_enterprise_governance_registry(db)
        return await get_enterprise_governance_registry(db)

    @api_router.get("/api/admin/governance/identities")
    async def governance_identities(limit: int = 200, actor=Depends(require_admin)):
        await ensure_enterprise_governance_registry(db)
        rows = await list_identity_projections(db, limit=min(max(limit, 1), 500))
        return {"count": len(rows), "items": rows}

    @api_router.post("/api/admin/governance/identities/project")
    async def governance_project_identity(body: Dict[str, Any] = Body(...), actor=Depends(require_admin)):
        await ensure_enterprise_governance_registry(db)
        return await ensure_identity_projection(db, body)

    @api_router.get("/api/admin/governance/organization")
    async def governance_organization(actor=Depends(require_admin)):
        await seed_governance_admin_surface(db)
        rows = await list_org_nodes(db)
        return {"count": len(rows), "items": rows}

    @api_router.get("/api/admin/governance/roles")
    async def governance_roles(actor=Depends(require_admin)):
        registry = await get_enterprise_governance_registry(db)
        return {"count": len(registry.get("roles") or {}), "items": registry.get("roles") or {}}

    @api_router.get("/api/admin/governance/permissions")
    async def governance_permissions(actor=Depends(require_admin)):
        registry = await get_enterprise_governance_registry(db)
        return {"count": len(registry.get("permissions") or {}), "items": registry.get("permissions") or {}}

    @api_router.get("/api/admin/governance/policies")
    async def governance_policies(actor=Depends(require_admin)):
        registry = await get_enterprise_governance_registry(db)
        return {"count": len(registry.get("policies") or {}), "items": registry.get("policies") or {}}

    @api_router.get("/api/admin/governance/approval-flows")
    async def governance_approval_flows(actor=Depends(require_admin)):
        registry = await get_enterprise_governance_registry(db)
        items = registry.get("approval_flows") or {}
        requests = await list_approval_requests(db, limit=200)
        return {"count": len(items), "items": items, "requests": requests}

    @api_router.post("/api/admin/governance/approval-flows/requests/{request_id}/approve")
    async def governance_approve_request(request: Request, request_id: str, body: ApprovalBody, actor=Depends(require_admin)):
        try:
            resolved = await resolve_actor_from_request(db, request, actor)
            row = await approve_request(db, request_id=request_id, actor=resolved, note=body.note)
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(403, str(exc)) from exc
        return {"ok": True, "request": row}

    @api_router.get("/api/admin/governance/delegations")
    async def governance_delegations(actor=Depends(require_admin)):
        rows = await list_delegations(db, limit=200)
        return {"count": len(rows), "items": rows}

    @api_router.post("/api/admin/governance/delegations")
    async def governance_create_delegation(request: Request, body: DelegationBody, actor=Depends(require_admin)):
        resolved = await resolve_actor_from_request(db, request, actor)
        projection = await ensure_identity_projection(db, resolved)
        row = await create_delegation(
            db,
            actor=resolved,
            delegator_projection=projection,
            delegate_user_id=body.delegate_user_id,
            delegate_email=body.delegate_email,
            permissions=body.permissions,
            delegation_type=body.delegation_type,
            reason=body.reason,
            expires_at=body.expires_at,
        )
        return {"ok": True, "delegation": row}

    @api_router.get("/api/admin/governance/separation-of-duties")
    async def governance_sod(actor=Depends(require_admin)):
        registry = await get_enterprise_governance_registry(db)
        items = registry.get("separation_rules") or {}
        return {"count": len(items), "items": items}

    @api_router.get("/api/admin/governance/authority")
    async def governance_authority(actor=Depends(require_admin)):
        registry = await get_enterprise_governance_registry(db)
        return {"items": registry.get("authority_levels") or {}}

    @api_router.get("/api/admin/governance/emergency-overrides")
    async def governance_overrides(actor=Depends(require_admin)):
        rows = await list_overrides(db, limit=200)
        return {"count": len(rows), "items": rows}

    @api_router.post("/api/admin/governance/emergency-overrides")
    async def governance_create_override(request: Request, body: OverrideBody, actor=Depends(require_admin)):
        resolved = await resolve_actor_from_request(db, request, actor)
        projection = await ensure_identity_projection(db, resolved)
        row = await create_emergency_override(
            db,
            actor=resolved,
            projection=projection,
            action_key=body.action_key,
            module_key=body.module_key,
            record_type=body.record_type,
            record_id=body.record_id,
            company_id=body.company_id,
            project_number=body.project_number,
            denied_policy_id=body.denied_policy_id,
            justification=body.justification,
            operational_urgency=body.operational_urgency,
            evidence=body.evidence,
            expires_at=body.expires_at,
        )
        return {"ok": True, "override": row}

    @api_router.get("/api/admin/governance/decisions")
    async def governance_decisions(actor=Depends(require_admin)):
        rows = await list_decisions(db, limit=200)
        return {"count": len(rows), "items": rows}

    @api_router.get("/api/admin/governance/audit")
    async def governance_audit(actor=Depends(require_admin)):
        rows = [row async for row in db.enterprise_governance_audit.find({}, {"_id": 0}).sort("created_at", -1).limit(200)]
        return {"count": len(rows), "items": rows}

    @api_router.get("/api/admin/governance/versions")
    async def governance_versions(actor=Depends(require_admin)):
        registry = await get_enterprise_governance_registry(db)
        return {
            "governance_registry_version": registry.get("version"),
            "baseline_reference": "/app/memory/MASCI_OPS_PLATFORM_BASELINE_1_0.md",
            "status": "wp15-in-progress",
        }

    @api_router.get("/api/admin/governance/health")
    async def governance_health(actor=Depends(require_admin)):
        overview = await get_governance_overview(db)
        counts = overview.get("counts") or {}
        return {
            "status": "healthy" if counts.get("recent_denials", 0) < 25 else "warning",
            "counts": counts,
            "recent_decisions": overview.get("recent_decisions") or [],
        }
