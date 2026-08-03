from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

import io

from fastapi import APIRouter, BackgroundTasks, Body, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, Field
from fastapi.responses import StreamingResponse
from lib.enterprise_governance import governance_project_scope, resolve_actor_from_request

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
from services.project_controls_authority import (
    EVENT_CONTRACTS,
    archive_project,
    confirm_project_crew,
    ensure_project_controls_foundation,
    get_admin_project_controls_overview,
    get_project_controls_overview,
    get_project_lifecycle,
    get_project_lookahead,
    list_enterprise_work_types,
    list_project_crew_intelligence,
    list_project_mappings,
    list_project_pay_items,
    list_project_work_ledger,
    list_review_queue as list_project_controls_review_queue,
    restore_project,
    save_project_lookahead,
    set_crew_suggestion_review_state,
    set_project_lifecycle_state,
    upsert_enterprise_work_type,
    upsert_project_mapping,
    upsert_project_pay_item,
)
from services.project_budget_authority import (
    BUDGET_EVENT_CONTRACTS,
    activate_budget_import_session,
    create_budget_import_session,
    ensure_project_budget_foundation,
    export_budget_version_comparison,
    export_budget_version_rows,
    get_admin_project_budget_overview,
    get_budget_import_session_detail,
    get_project_budget_overview,
    list_budget_import_sessions,
    list_budget_review_queue,
    list_project_budget_lines,
    list_project_budget_versions,
    review_budget_import_row,
    run_project_budget_backfill,
)
from pm_auth import is_valid_pm_user_token_async


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


class WorkTypeBody(BaseModel):
    code: str = Field(..., min_length=2, max_length=80)
    name: str = Field(..., min_length=2, max_length=160)
    description: str = ""
    category: str = "General"
    keywords: List[str] = Field(default_factory=list)
    status: str = "active"
    effective_start: str = ""
    effective_end: str = ""


class ProjectPayItemBody(BaseModel):
    pay_item_id: str = ""
    project_name: str = ""
    customer_pay_item_number: str = Field(..., min_length=1, max_length=120)
    description: str = Field(..., min_length=2, max_length=240)
    unit: str = ""
    contract_quantity: float = 0.0
    contract_unit_price: float = 0.0
    contract_value: float = 0.0
    contract_id: str = ""
    phase_id: str = ""
    work_package_id: str = ""
    schedule_activity_id: str = ""
    schedule_activity_name: str = ""
    status: str = "active"
    effective_start: str = ""
    effective_end: str = ""
    billing_relevance: bool = True
    production_relevance: bool = True
    schedule_relevance: bool = True
    source: str = "manual_governed_entry"
    source_record: Dict[str, Any] = Field(default_factory=dict)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    confidence: str = "human_confirmed"


class ProjectMappingBody(BaseModel):
    pay_item_id: str = Field(..., min_length=2, max_length=180)
    mapping_id: str = ""
    primary_work_type_id: str = ""
    secondary_work_type_ids: List[str] = Field(default_factory=list)
    confidence: str = ""
    source: str = ""
    effective_start: str = ""
    effective_end: str = ""
    status: str = "pending_review"
    mapper: str = ""
    approver: str = ""
    explanation: str = ""


class LookaheadBody(BaseModel):
    status: str = "draft"
    tasks: List[Dict[str, Any]] = Field(default_factory=list)
    constraints: List[Dict[str, Any]] = Field(default_factory=list)
    comparison_note: str = ""


class LifecycleBody(BaseModel):
    next_state: str = Field(..., min_length=2, max_length=80)
    reason: str = ""


class CrewConfirmBody(BaseModel):
    suggestion_id: str = ""
    crew_id: str = ""
    crew_name: str = ""
    leader: str = ""
    members: List[str] = Field(default_factory=list)
    effective_start: str = ""
    effective_end: str = ""
    facility_scope: str = ""
    lifecycle_status: str = "active"
    source: str = ""
    confidence: str = "human_confirmed"
    signature: str = ""


class ReviewNoteBody(BaseModel):
    note: str = ""


class BudgetImportRowReviewBody(BaseModel):
    action: str = "approve"
    customer_pay_item_id: str = ""
    customer_pay_item_number: str = ""
    description: str = ""
    quantity: float = 0.0
    unit: str = ""
    unit_price: float = 0.0
    budget_amount: float = 0.0
    enterprise_work_type_id: str = ""
    project_cost_code: str = ""
    phase_id: str = ""
    work_package_id: str = ""
    schedule_activity_id: str = ""
    schedule_activity_name: str = ""
    line_kind: str = "direct_cost"
    review_note: str = ""


def _runtime_db(request: Optional[Request], db):
    state_db = getattr(getattr(getattr(request, "app", None), "state", None), "db", None)
    if state_db is not None:
        return state_db
    target = getattr(db, "get_target", lambda: None)()
    if target is not None:
        return target
    return db


async def _require_pm_or_admin_actor(runtime_db, request: Request) -> Dict[str, Any]:
    if request.headers.get("X-Admin-Token") and request.headers.get("X-Directory-Token"):
        actor = await resolve_actor_from_request(runtime_db, request, True)
        actor_kind = str(actor.get("_actor") or actor.get("role") or "").strip().lower()
        if actor_kind == "admin":
            return actor
    pm_token = request.headers.get("X-PM-Token") or ""
    if pm_token and "." in pm_token:
        pm_doc = await is_valid_pm_user_token_async(runtime_db, pm_token)
        if pm_doc:
            return {**pm_doc, "_actor": "pm", "role": "pm", "_actor_kind": "pm_user"}
    raise HTTPException(status_code=401, detail="portal authentication required")


async def _require_project_scope(runtime_db, request: Request, project_number: str) -> Dict[str, Any]:
    actor = await _require_pm_or_admin_actor(runtime_db, request)
    scope = await governance_project_scope(runtime_db, actor)
    if not scope.allows(project_number):
        raise HTTPException(status_code=403, detail="project scope denied")
    return actor


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

    @api_router.get("/api/admin/governance/project-controls/overview")
    async def governance_project_controls_overview(request: Request, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        await ensure_project_controls_foundation(runtime_db)
        return await get_admin_project_controls_overview(runtime_db)

    @api_router.post("/api/admin/governance/project-controls/backfill/run")
    async def governance_project_controls_backfill(request: Request, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        return await ensure_project_controls_foundation(runtime_db, force_backfill=True)

    @api_router.get("/api/admin/governance/project-controls/work-types")
    async def governance_project_controls_work_types(request: Request, include_archived: bool = False, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        rows = await list_enterprise_work_types(runtime_db, include_archived=include_archived)
        return {"count": len(rows), "items": rows}

    @api_router.post("/api/admin/governance/project-controls/work-types")
    async def governance_project_controls_create_work_type(request: Request, body: WorkTypeBody, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        resolved = await resolve_actor_from_request(runtime_db, request, actor)
        try:
            row = await upsert_enterprise_work_type(runtime_db, body.model_dump(), actor=resolved)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return {"ok": True, "work_type": row}

    @api_router.patch("/api/admin/governance/project-controls/work-types/{work_type_id}")
    async def governance_project_controls_update_work_type(request: Request, work_type_id: str, body: WorkTypeBody, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        resolved = await resolve_actor_from_request(runtime_db, request, actor)
        try:
            row = await upsert_enterprise_work_type(runtime_db, body.model_dump(), actor=resolved, work_type_id=work_type_id)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return {"ok": True, "work_type": row}

    @api_router.get("/api/admin/governance/project-controls/review-queue")
    async def governance_project_controls_review(request: Request, project_number: str = "", status: str = "", actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        rows = await list_project_controls_review_queue(runtime_db, project_number=project_number, status=status)
        return {"count": len(rows), "items": rows}

    @api_router.get("/api/admin/governance/project-controls/event-contracts")
    async def governance_project_controls_events(request: Request, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        await ensure_project_controls_foundation(runtime_db)
        return {"count": len(EVENT_CONTRACTS), "items": EVENT_CONTRACTS}

    @api_router.get("/api/admin/governance/project-controls/budget/overview")
    async def governance_project_budget_overview(request: Request, project_number: str = "", actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        await ensure_project_budget_foundation(runtime_db)
        return await get_admin_project_budget_overview(runtime_db, project_number=project_number)

    @api_router.post("/api/admin/governance/project-controls/budget/backfill/run")
    async def governance_project_budget_backfill(request: Request, background_tasks: BackgroundTasks, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        await ensure_project_budget_foundation(runtime_db)
        background_tasks.add_task(run_project_budget_backfill, runtime_db, force=True)
        return {"ok": True, "status": "queued", "message": "wp18c3 budget backfill queued"}

    @api_router.get("/api/admin/governance/project-controls/budget/review-queue")
    async def governance_project_budget_review(request: Request, project_number: str = "", actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        rows = await list_budget_review_queue(runtime_db, project_number=project_number)
        return {"count": len(rows), "items": rows}

    @api_router.get("/api/admin/governance/project-controls/budget/versions")
    async def governance_project_budget_versions(request: Request, project_number: str, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        rows = await list_project_budget_versions(runtime_db, project_number)
        return {"count": len(rows), "items": rows}

    @api_router.get("/api/admin/governance/project-controls/budget/versions/{version_id}/lines")
    async def governance_project_budget_lines(request: Request, version_id: str, project_number: str, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        rows = await list_project_budget_lines(runtime_db, project_number, version_id=version_id)
        return {"count": len(rows), "items": rows}

    @api_router.get("/api/admin/governance/project-controls/budget/imports")
    async def governance_project_budget_imports(request: Request, project_number: str, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        rows = await list_budget_import_sessions(runtime_db, project_number)
        return {"count": len(rows), "items": rows}

    @api_router.get("/api/admin/governance/project-controls/budget/imports/{import_id}")
    async def governance_project_budget_import_detail(request: Request, import_id: str, project_number: str, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        try:
            return await get_budget_import_session_detail(runtime_db, project_number, import_id)
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc

    @api_router.get("/api/admin/governance/project-controls/budget/export/budget")
    async def governance_project_budget_export(request: Request, project_number: str, version_id: str, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        resolved = await resolve_actor_from_request(runtime_db, request, actor)
        try:
            payload = await export_budget_version_rows(runtime_db, project_number, version_id, actor=resolved)
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc
        return StreamingResponse(
            io.StringIO(payload["content"]),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{payload["filename"]}"', "Cache-Control": "no-store"},
        )

    @api_router.get("/api/admin/governance/project-controls/budget/export/comparison")
    async def governance_project_budget_export_comparison(request: Request, project_number: str, left_version_id: str, right_version_id: str, actor=Depends(require_admin)):
        runtime_db = _runtime_db(request, db)
        resolved = await resolve_actor_from_request(runtime_db, request, actor)
        try:
            payload = await export_budget_version_comparison(runtime_db, project_number, left_version_id=left_version_id, right_version_id=right_version_id, actor=resolved)
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc
        return StreamingResponse(
            io.StringIO(payload["content"]),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{payload["filename"]}"', "Cache-Control": "no-store"},
        )

    @api_router.get("/api/pm/project-controls/overview")
    async def pm_project_controls_overview(request: Request, project_number: str):
        runtime_db = _runtime_db(request, db)
        await _require_project_scope(runtime_db, request, project_number)
        return await get_project_controls_overview(runtime_db, project_number)

    @api_router.get("/api/pm/project-controls/work-types")
    async def pm_project_controls_work_types(request: Request):
        runtime_db = _runtime_db(request, db)
        await _require_pm_or_admin_actor(runtime_db, request)
        rows = await list_enterprise_work_types(runtime_db, include_archived=False)
        return {"count": len(rows), "items": rows}

    @api_router.get("/api/pm/project-controls/projects/{project_number}/pay-items")
    async def pm_project_controls_pay_items(request: Request, project_number: str):
        runtime_db = _runtime_db(request, db)
        await _require_project_scope(runtime_db, request, project_number)
        rows = await list_project_pay_items(runtime_db, project_number)
        return {"count": len(rows), "items": rows}

    @api_router.post("/api/pm/project-controls/projects/{project_number}/pay-items")
    async def pm_project_controls_upsert_pay_item(request: Request, project_number: str, body: ProjectPayItemBody):
        runtime_db = _runtime_db(request, db)
        actor = await _require_project_scope(runtime_db, request, project_number)
        try:
            row = await upsert_project_pay_item(runtime_db, project_number, body.model_dump(), actor=actor)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return {"ok": True, "pay_item": row}

    @api_router.get("/api/pm/project-controls/projects/{project_number}/mappings")
    async def pm_project_controls_mappings(request: Request, project_number: str):
        runtime_db = _runtime_db(request, db)
        await _require_project_scope(runtime_db, request, project_number)
        rows = await list_project_mappings(runtime_db, project_number)
        return {"count": len(rows), "items": rows}

    @api_router.post("/api/pm/project-controls/projects/{project_number}/mappings")
    async def pm_project_controls_upsert_mapping(request: Request, project_number: str, body: ProjectMappingBody):
        runtime_db = _runtime_db(request, db)
        actor = await _require_project_scope(runtime_db, request, project_number)
        try:
            row = await upsert_project_mapping(runtime_db, project_number, body.model_dump(), actor=actor)
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return {"ok": True, "mapping": row}

    @api_router.get("/api/pm/project-controls/projects/{project_number}/lookahead")
    async def pm_project_controls_lookahead(request: Request, project_number: str):
        runtime_db = _runtime_db(request, db)
        await _require_project_scope(runtime_db, request, project_number)
        return await get_project_lookahead(runtime_db, project_number)

    @api_router.put("/api/pm/project-controls/projects/{project_number}/lookahead")
    async def pm_project_controls_save_lookahead(request: Request, project_number: str, body: LookaheadBody):
        runtime_db = _runtime_db(request, db)
        actor = await _require_project_scope(runtime_db, request, project_number)
        try:
            row = await save_project_lookahead(runtime_db, project_number, body.model_dump(), actor=actor)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return {"ok": True, "lookahead": row}

    @api_router.get("/api/pm/project-controls/projects/{project_number}/lifecycle")
    async def pm_project_controls_lifecycle(request: Request, project_number: str):
        runtime_db = _runtime_db(request, db)
        await _require_project_scope(runtime_db, request, project_number)
        return await get_project_lifecycle(runtime_db, project_number)

    @api_router.post("/api/pm/project-controls/projects/{project_number}/lifecycle")
    async def pm_project_controls_set_lifecycle(request: Request, project_number: str, body: LifecycleBody):
        runtime_db = _runtime_db(request, db)
        actor = await _require_project_scope(runtime_db, request, project_number)
        try:
            row = await set_project_lifecycle_state(runtime_db, project_number, actor=actor, next_state=body.next_state, reason=body.reason)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return {"ok": True, "lifecycle": row}

    @api_router.post("/api/pm/project-controls/projects/{project_number}/archive")
    async def pm_project_controls_archive(request: Request, project_number: str, body: GovernanceActionBody = Body(default=GovernanceActionBody())):
        runtime_db = _runtime_db(request, db)
        actor = await _require_project_scope(runtime_db, request, project_number)
        return {"ok": True, "lifecycle": await archive_project(runtime_db, project_number, actor=actor, reason=body.reason)}

    @api_router.post("/api/pm/project-controls/projects/{project_number}/restore")
    async def pm_project_controls_restore(request: Request, project_number: str, body: GovernanceActionBody = Body(default=GovernanceActionBody())):
        runtime_db = _runtime_db(request, db)
        actor = await _require_project_scope(runtime_db, request, project_number)
        return {"ok": True, "lifecycle": await restore_project(runtime_db, project_number, actor=actor, reason=body.reason)}

    @api_router.get("/api/pm/project-controls/projects/{project_number}/crew-intelligence")
    async def pm_project_controls_crew_intel(request: Request, project_number: str):
        runtime_db = _runtime_db(request, db)
        await _require_project_scope(runtime_db, request, project_number)
        return await list_project_crew_intelligence(runtime_db, project_number)

    @api_router.post("/api/pm/project-controls/projects/{project_number}/crew-intelligence/confirm")
    async def pm_project_controls_confirm_crew(request: Request, project_number: str, body: CrewConfirmBody):
        runtime_db = _runtime_db(request, db)
        actor = await _require_project_scope(runtime_db, request, project_number)
        try:
            row = await confirm_project_crew(runtime_db, project_number, body.model_dump(), actor=actor)
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return {"ok": True, "crew": row}

    @api_router.post("/api/pm/project-controls/projects/{project_number}/crew-intelligence/suggestions/{suggestion_id}/{action}")
    async def pm_project_controls_crew_review(request: Request, project_number: str, suggestion_id: str, action: str, body: ReviewNoteBody = Body(default=ReviewNoteBody())):
        runtime_db = _runtime_db(request, db)
        actor = await _require_project_scope(runtime_db, request, project_number)
        try:
            row = await set_crew_suggestion_review_state(runtime_db, project_number, suggestion_id, actor=actor, action=action, note=body.note)
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return {"ok": True, "review": row}

    @api_router.get("/api/pm/project-controls/projects/{project_number}/work-ledger")
    async def pm_project_controls_work_ledger(request: Request, project_number: str, limit: int = 100):
        runtime_db = _runtime_db(request, db)
        await _require_project_scope(runtime_db, request, project_number)
        rows = await list_project_work_ledger(runtime_db, project_number, limit=limit)
        return {"count": len(rows), "items": rows}

    @api_router.get("/api/pm/project-controls/projects/{project_number}/budget/overview")
    async def pm_project_budget_overview(request: Request, project_number: str):
        runtime_db = _runtime_db(request, db)
        await _require_project_scope(runtime_db, request, project_number)
        return await get_project_budget_overview(runtime_db, project_number)

    @api_router.get("/api/pm/project-controls/projects/{project_number}/budget/versions")
    async def pm_project_budget_versions(request: Request, project_number: str):
        runtime_db = _runtime_db(request, db)
        await _require_project_scope(runtime_db, request, project_number)
        rows = await list_project_budget_versions(runtime_db, project_number)
        return {"count": len(rows), "items": rows}

    @api_router.get("/api/pm/project-controls/projects/{project_number}/budget/versions/{version_id}/lines")
    async def pm_project_budget_lines(request: Request, project_number: str, version_id: str):
        runtime_db = _runtime_db(request, db)
        await _require_project_scope(runtime_db, request, project_number)
        rows = await list_project_budget_lines(runtime_db, project_number, version_id=version_id)
        return {"count": len(rows), "items": rows}

    @api_router.get("/api/pm/project-controls/projects/{project_number}/budget/review-queue")
    async def pm_project_budget_review_queue(request: Request, project_number: str):
        runtime_db = _runtime_db(request, db)
        await _require_project_scope(runtime_db, request, project_number)
        rows = await list_budget_review_queue(runtime_db, project_number=project_number)
        return {"count": len(rows), "items": rows}

    @api_router.get("/api/pm/project-controls/projects/{project_number}/budget/imports")
    async def pm_project_budget_imports(request: Request, project_number: str):
        runtime_db = _runtime_db(request, db)
        await _require_project_scope(runtime_db, request, project_number)
        rows = await list_budget_import_sessions(runtime_db, project_number)
        return {"count": len(rows), "items": rows}

    @api_router.get("/api/pm/project-controls/projects/{project_number}/budget/imports/{import_id}")
    async def pm_project_budget_import_detail(request: Request, project_number: str, import_id: str):
        runtime_db = _runtime_db(request, db)
        await _require_project_scope(runtime_db, request, project_number)
        try:
            return await get_budget_import_session_detail(runtime_db, project_number, import_id)
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc

    @api_router.post("/api/pm/project-controls/projects/{project_number}/budget/imports")
    async def pm_project_budget_create_import(
        request: Request,
        project_number: str,
        file: UploadFile = File(...),
        source_kind: str = Form("csv"),
        target_version_stage: str = Form("original_approved_budget"),
        version_name: str = Form(""),
    ):
        runtime_db = _runtime_db(request, db)
        actor = await _require_project_scope(runtime_db, request, project_number)
        data = await file.read()
        try:
            return await create_budget_import_session(
                runtime_db,
                project_number,
                filename=file.filename or "budget-upload",
                content_type=file.content_type or "application/octet-stream",
                data=data,
                source_kind=source_kind,
                target_version_stage=target_version_stage,
                version_name=version_name,
                actor=actor,
            )
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc

    @api_router.post("/api/pm/project-controls/projects/{project_number}/budget/imports/{import_id}/rows/{row_id}/review")
    async def pm_project_budget_review_row(request: Request, project_number: str, import_id: str, row_id: str, body: BudgetImportRowReviewBody):
        runtime_db = _runtime_db(request, db)
        actor = await _require_project_scope(runtime_db, request, project_number)
        try:
            row = await review_budget_import_row(runtime_db, project_number, import_id, row_id, body.model_dump(), actor=actor)
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return {"ok": True, "row": row}

    @api_router.post("/api/pm/project-controls/projects/{project_number}/budget/imports/{import_id}/activate")
    async def pm_project_budget_activate(request: Request, project_number: str, import_id: str):
        runtime_db = _runtime_db(request, db)
        actor = await _require_project_scope(runtime_db, request, project_number)
        try:
            result = await activate_budget_import_session(runtime_db, project_number, import_id, actor=actor)
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(400, str(exc)) from exc
        return {"ok": True, **result}

    @api_router.get("/api/pm/project-controls/projects/{project_number}/budget/export/budget")
    async def pm_project_budget_export(request: Request, project_number: str, version_id: str):
        runtime_db = _runtime_db(request, db)
        actor = await _require_project_scope(runtime_db, request, project_number)
        try:
            payload = await export_budget_version_rows(runtime_db, project_number, version_id, actor=actor)
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc
        return StreamingResponse(
            io.StringIO(payload["content"]),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{payload["filename"]}"', "Cache-Control": "no-store"},
        )

    @api_router.get("/api/pm/project-controls/projects/{project_number}/budget/export/comparison")
    async def pm_project_budget_export_comparison(request: Request, project_number: str, left_version_id: str, right_version_id: str):
        runtime_db = _runtime_db(request, db)
        actor = await _require_project_scope(runtime_db, request, project_number)
        try:
            payload = await export_budget_version_comparison(runtime_db, project_number, left_version_id=left_version_id, right_version_id=right_version_id, actor=actor)
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc
        return StreamingResponse(
            io.StringIO(payload["content"]),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{payload["filename"]}"', "Cache-Control": "no-store"},
        )
