from __future__ import annotations

import logging
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
from services.enterprise_hierarchy_foundation import (
    bind_existing_record,
    create_hierarchy_node,
    ensure_enterprise_hierarchy_foundation,
    get_hierarchy_node_detail,
    get_hierarchy_overview,
    get_latest_backfill_report,
    get_scope_preview,
    list_hierarchy_bindings,
    list_hierarchy_nodes,
    list_resource_assignments,
    list_review_queue,
    set_hierarchy_node_state,
    update_hierarchy_node,
)


logger = logging.getLogger(__name__)


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


class HierarchyNodeBody(BaseModel):
    code: str = Field(..., min_length=2, max_length=120)
    name: str = Field(..., min_length=2, max_length=200)
    type: str = Field(..., min_length=2, max_length=60)
    subtype: str = ""
    parent_id: Optional[str] = None
    description: str = ""
    company_scope: str = "masci"
    effective_start: str = ""
    effective_end: Optional[str] = None
    active_status: bool = True
    archive_status: bool = False
    owner_steward: str = ""
    steward: str = ""
    external_source_identifier: str = ""
    display_order: int = 0
    metadata_extension: Dict[str, Any] = Field(default_factory=dict)


class HierarchyNodePatchBody(BaseModel):
    name: Optional[str] = None
    parent_id: Optional[str] = None
    description: Optional[str] = None
    effective_start: Optional[str] = None
    effective_end: Optional[str] = None
    active_status: Optional[bool] = None
    archive_status: Optional[bool] = None
    owner_steward: Optional[str] = None
    steward: Optional[str] = None
    display_order: Optional[int] = None
    metadata_extension: Dict[str, Any] = Field(default_factory=dict)


class HierarchyBindingBody(BaseModel):
    record_type: str = Field(..., min_length=2, max_length=80)
    source_collection: str = Field(..., min_length=2, max_length=120)
    source_record_id: str = Field(..., min_length=1, max_length=200)
    source_label: str = Field(..., min_length=1, max_length=240)
    target_node_id: str = Field(..., min_length=2, max_length=240)
    binding_kind: str = Field(..., min_length=2, max_length=80)
    confidence: str = "high"
    metadata: Dict[str, Any] = Field(default_factory=dict)


class GovernanceActionBody(BaseModel):
    reason: str = ""


def _runtime_db(request: Optional[Request], db):
    state_db = getattr(getattr(getattr(request, "app", None), "state", None), "db", None)
    if state_db is not None:
        return state_db
    target = getattr(db, "get_target", lambda: None)()
    if target is not None:
        return target
    return db


def register_enterprise_governance_routes(api_router: APIRouter, db, require_admin) -> None:
    @api_router.get("/api/admin/governance/overview")
    async def governance_overview(request: Request, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        await ensure_enterprise_governance_registry(runtime_db)
        await seed_governance_admin_surface(runtime_db)
        return await get_governance_overview(runtime_db)

    @api_router.get("/api/admin/governance/registry")
    async def governance_registry(request: Request, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        await ensure_enterprise_governance_registry(runtime_db)
        return await get_enterprise_governance_registry(runtime_db)

    @api_router.get("/api/admin/governance/identities")
    async def governance_identities(request: Request, limit: int = 200, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        await ensure_enterprise_governance_registry(runtime_db)
        rows = await list_identity_projections(runtime_db, limit=min(max(limit, 1), 500))
        return {"count": len(rows), "items": rows}

    @api_router.post("/api/admin/governance/identities/project")
    async def governance_project_identity(request: Request, body: Dict[str, Any] = Body(...), actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        await ensure_enterprise_governance_registry(runtime_db)
        return await ensure_identity_projection(runtime_db, body)

    @api_router.get("/api/admin/governance/organization")
    async def governance_organization(request: Request, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        await ensure_enterprise_hierarchy_foundation(runtime_db)
        rows = await list_hierarchy_nodes(runtime_db)
        return {"count": len(rows), "items": rows}

    @api_router.get("/api/admin/governance/hierarchy/overview")
    async def governance_hierarchy_overview(request: Request, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        return await get_hierarchy_overview(runtime_db)

    @api_router.post("/api/admin/governance/hierarchy/backfill/run")
    async def governance_hierarchy_backfill_run(request: Request, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        return await ensure_enterprise_hierarchy_foundation(runtime_db, force=True)

    @api_router.get("/api/admin/governance/hierarchy/backfill/latest")
    async def governance_hierarchy_backfill_latest(request: Request, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        return await get_latest_backfill_report(runtime_db)

    @api_router.get("/api/admin/governance/hierarchy/nodes")
    async def governance_hierarchy_nodes(
        request: Request,
        node_type: str = "",
        parent_id: str = "",
        search: str = "",
        include_archived: bool = False,
        actor=Depends(require_admin),
    ):
        runtime_db = _runtime_db(request, db)
        rows = await list_hierarchy_nodes(
            runtime_db,
            node_type=node_type,
            parent_id=parent_id,
            search=search,
            include_archived=include_archived,
        )
        return {"count": len(rows), "items": rows}

    @api_router.get("/api/admin/governance/hierarchy/nodes/{node_id}")
    async def governance_hierarchy_node_detail(request: Request, node_id: str, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        try:
            return await get_hierarchy_node_detail(runtime_db, node_id)
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc

    @api_router.get("/api/admin/governance/hierarchy/nodes/{node_id}/children")
    async def governance_hierarchy_node_children(request: Request, node_id: str, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        try:
            detail = await get_hierarchy_node_detail(runtime_db, node_id)
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc
        return {"count": len(detail["children"]), "items": detail["children"]}

    @api_router.get("/api/admin/governance/hierarchy/nodes/{node_id}/ancestry")
    async def governance_hierarchy_node_ancestry(request: Request, node_id: str, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        try:
            detail = await get_hierarchy_node_detail(runtime_db, node_id)
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc
        return {"count": len(detail["ancestry"]), "items": detail["ancestry"]}

    @api_router.post("/api/admin/governance/hierarchy/nodes")
    async def governance_hierarchy_create_node(request: Request, body: HierarchyNodeBody, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        try:
            resolved = await resolve_actor_from_request(runtime_db, request, actor)
            node = await create_hierarchy_node(runtime_db, body=body.model_dump(), actor=resolved)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            logger.exception("governance hierarchy create failed")
            raise HTTPException(500, "governance_hierarchy_create_failed") from exc
        return {"ok": True, "node": node}

    @api_router.patch("/api/admin/governance/hierarchy/nodes/{node_id}")
    async def governance_hierarchy_update_node(request: Request, node_id: str, body: HierarchyNodePatchBody, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        try:
            resolved = await resolve_actor_from_request(runtime_db, request, actor)
            node = await update_hierarchy_node(runtime_db, node_id=node_id, body=body.model_dump(exclude_none=True), actor=resolved)
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            logger.exception("governance hierarchy update failed")
            raise HTTPException(500, "governance_hierarchy_update_failed") from exc
        return {"ok": True, "node": node}

    @api_router.post("/api/admin/governance/hierarchy/nodes/{node_id}/activate")
    async def governance_hierarchy_activate_node(request: Request, node_id: str, body: GovernanceActionBody = Body(default=GovernanceActionBody()), actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        try:
            resolved = await resolve_actor_from_request(runtime_db, request, actor)
            node = await set_hierarchy_node_state(runtime_db, node_id=node_id, actor=resolved, action="activate", reason=body.reason)
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return {"ok": True, "node": node}

    @api_router.post("/api/admin/governance/hierarchy/nodes/{node_id}/deactivate")
    async def governance_hierarchy_deactivate_node(request: Request, node_id: str, body: GovernanceActionBody = Body(default=GovernanceActionBody()), actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        try:
            resolved = await resolve_actor_from_request(runtime_db, request, actor)
            node = await set_hierarchy_node_state(runtime_db, node_id=node_id, actor=resolved, action="deactivate", reason=body.reason)
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return {"ok": True, "node": node}

    @api_router.post("/api/admin/governance/hierarchy/nodes/{node_id}/archive")
    async def governance_hierarchy_archive_node(request: Request, node_id: str, body: GovernanceActionBody = Body(default=GovernanceActionBody()), actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        try:
            resolved = await resolve_actor_from_request(runtime_db, request, actor)
            node = await set_hierarchy_node_state(runtime_db, node_id=node_id, actor=resolved, action="archive", reason=body.reason)
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return {"ok": True, "node": node}

    @api_router.get("/api/admin/governance/hierarchy/bindings")
    async def governance_hierarchy_bindings(request: Request, status: str = "", record_type: str = "", actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        rows = await list_hierarchy_bindings(runtime_db, status=status, record_type=record_type)
        return {"count": len(rows), "items": rows}

    @api_router.post("/api/admin/governance/hierarchy/bindings")
    async def governance_hierarchy_bind_record(request: Request, body: HierarchyBindingBody, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        try:
            resolved = await resolve_actor_from_request(runtime_db, request, actor)
            row = await bind_existing_record(runtime_db, actor=resolved, **body.model_dump())
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return {"ok": True, "binding": row}

    @api_router.get("/api/admin/governance/hierarchy/review-queue")
    async def governance_hierarchy_review_queue(request: Request, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        rows = await list_review_queue(runtime_db)
        return {"count": len(rows), "items": rows}

    @api_router.get("/api/admin/governance/hierarchy/resource-assignments")
    async def governance_hierarchy_resource_assignments(request: Request, resource_type: str = "", actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        rows = await list_resource_assignments(runtime_db, resource_type=resource_type)
        return {"count": len(rows), "items": rows}

    @api_router.get("/api/admin/governance/hierarchy/scope")
    async def governance_hierarchy_scope(request: Request, email: str = "", actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        return await get_scope_preview(runtime_db, email=email)

    @api_router.get("/api/admin/governance/roles")
    async def governance_roles(request: Request, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        registry = await get_enterprise_governance_registry(runtime_db)
        return {"count": len(registry.get("roles") or {}), "items": registry.get("roles") or {}}

    @api_router.get("/api/admin/governance/permissions")
    async def governance_permissions(request: Request, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        registry = await get_enterprise_governance_registry(runtime_db)
        return {"count": len(registry.get("permissions") or {}), "items": registry.get("permissions") or {}}

    @api_router.get("/api/admin/governance/policies")
    async def governance_policies(request: Request, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        registry = await get_enterprise_governance_registry(runtime_db)
        return {"count": len(registry.get("policies") or {}), "items": registry.get("policies") or {}}

    @api_router.get("/api/admin/governance/approval-flows")
    async def governance_approval_flows(request: Request, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        registry = await get_enterprise_governance_registry(runtime_db)
        items = registry.get("approval_flows") or {}
        requests = await list_approval_requests(runtime_db, limit=200)
        return {"count": len(items), "items": items, "requests": requests}

    @api_router.post("/api/admin/governance/approval-flows/requests/{request_id}/approve")
    async def governance_approve_request(request: Request, request_id: str, body: ApprovalBody, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        try:
            resolved = await resolve_actor_from_request(runtime_db, request, actor)
            row = await approve_request(runtime_db, request_id=request_id, actor=resolved, note=body.note)
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc
        except PermissionError as exc:
            raise HTTPException(403, str(exc)) from exc
        except Exception as exc:  # noqa: BLE001
            logger.exception("governance approval failed")
            raise HTTPException(500, "governance_approval_failed") from exc
        return {"ok": True, "request": row}

    @api_router.get("/api/admin/governance/delegations")
    async def governance_delegations(request: Request, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        rows = await list_delegations(runtime_db, limit=200)
        return {"count": len(rows), "items": rows}

    @api_router.post("/api/admin/governance/delegations")
    async def governance_create_delegation(request: Request, body: DelegationBody, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        try:
            resolved = await resolve_actor_from_request(runtime_db, request, actor)
            projection = await ensure_identity_projection(runtime_db, resolved)
            row = await create_delegation(
                runtime_db,
                actor=resolved,
                delegator_projection=projection,
                delegate_user_id=body.delegate_user_id,
                delegate_email=body.delegate_email,
                permissions=body.permissions,
                delegation_type=body.delegation_type,
                reason=body.reason,
                expires_at=body.expires_at,
            )
        except Exception as exc:  # noqa: BLE001
            logger.exception("governance delegation failed")
            raise HTTPException(500, "governance_delegation_failed") from exc
        return {"ok": True, "delegation": row}

    @api_router.get("/api/admin/governance/separation-of-duties")
    async def governance_sod(request: Request, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        registry = await get_enterprise_governance_registry(runtime_db)
        items = registry.get("separation_rules") or {}
        return {"count": len(items), "items": items}

    @api_router.get("/api/admin/governance/authority")
    async def governance_authority(request: Request, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        registry = await get_enterprise_governance_registry(runtime_db)
        return {"items": registry.get("authority_levels") or {}}

    @api_router.get("/api/admin/governance/emergency-overrides")
    async def governance_overrides(request: Request, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        rows = await list_overrides(runtime_db, limit=200)
        return {"count": len(rows), "items": rows}

    @api_router.post("/api/admin/governance/emergency-overrides")
    async def governance_create_override(request: Request, body: OverrideBody, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        try:
            resolved = await resolve_actor_from_request(runtime_db, request, actor)
            projection = await ensure_identity_projection(runtime_db, resolved)
            row = await create_emergency_override(
                runtime_db,
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
        except Exception as exc:  # noqa: BLE001
            logger.exception("governance emergency override failed")
            raise HTTPException(500, "governance_override_failed") from exc
        return {"ok": True, "override": row}

    @api_router.get("/api/admin/governance/decisions")
    async def governance_decisions(request: Request, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        rows = await list_decisions(runtime_db, limit=200)
        return {"count": len(rows), "items": rows}

    @api_router.get("/api/admin/governance/audit")
    async def governance_audit(request: Request, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        rows = [row async for row in runtime_db.enterprise_governance_audit.find({}, {"_id": 0}).sort("created_at", -1).limit(200)]
        return {"count": len(rows), "items": rows}

    @api_router.get("/api/admin/governance/versions")
    async def governance_versions(request: Request, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        registry = await get_enterprise_governance_registry(runtime_db)
        return {
            "governance_registry_version": registry.get("version"),
            "baseline_reference": "/app/memory/MASCI_OPS_PLATFORM_BASELINE_1_0.md",
            "architecture_freeze_reference": "/app/WP15_ARCHITECTURE_FREEZE.md",
            "constitutional_standard_reference": "/app/WP15_CONSTITUTIONAL_GOVERNANCE_STANDARD.md",
            "operational_health_dashboard_route": "/admin/governance",
            "status": "wp15-architecture-frozen",
        }

    @api_router.get("/api/admin/governance/health")
    async def governance_health(request: Request, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        overview = await get_governance_overview(runtime_db)
        counts = overview.get("counts") or {}
        return {
            "status": "healthy" if counts.get("recent_denials", 0) < 25 else "warning",
            "counts": counts,
            "recent_decisions": overview.get("recent_decisions") or [],
        }
