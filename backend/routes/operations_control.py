"""TRACK 24.17 · Operations Control Center API routes.

Endpoints (all require super-admin authentication):

* ``GET  /api/admin/operations-control/overview``
* ``GET  /api/admin/operations-control/operations``
* ``GET  /api/admin/operations-control/operations/{operation_id}``
* ``POST /api/admin/operations-control/operations/{operation_id}/dry-run``
* ``POST /api/admin/operations-control/operations/{operation_id}/apply``
* ``GET  /api/admin/operations-control/audit``
* ``GET  /api/admin/operations-control/audit/{action_id}``

Every mutation writes an ``operations_audit`` row. Destructive /
data-migration operations require a matching recent dry-run and an
exact confirmation phrase.
"""
from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from fastapi import APIRouter, Body, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from lib.trust_reconciliation import reconcile_shared_foundation
from lib.shared_capabilities import occ_operation_capability, shell_signout_capability, truth_action_capability
from services.operations_control import build_registry
from services.operations_control import audit as occ_audit
from services.operations_control.control_plane import (
    build_baseline_snapshot,
    build_readiness_evidence_package,
    ensure_registry_snapshot,
    get_communication_by_id,
    list_recent_baselines,
    list_recent_communications,
    list_recent_control_plane_events,
    list_recent_evidence_packages,
    run_due_escalations,
)
from services.operations_control.case_management import (
    acknowledge_case_communication,
    build_case_assembly,
    build_case_relationship_graph,
    build_case_timeline,
    capture_case_evidence_package,
    create_case_task,
    create_preview_case_certification_record,
    ensure_case_management_indexes,
    export_case_evidence_package,
    get_case_by_id,
    include_case_in_baseline,
    link_related_case,
    list_cases,
    run_case_certification_chain,
    transition_case,
)
from services.operations_control.registry import operations_control_plane_registry_summary
from lib.enterprise_governance import require_governed_action
from lib.release_scope import is_release_deferred, raise_release_deferred_404


class CaseTransitionBody(BaseModel):
    to_status: str = Field(..., min_length=2, max_length=64)
    reason: str = ""
    resolution_summary: str = ""
    root_cause: str = ""
    verification_notes: str = ""
    duplicate_of_case_id: str = ""


class CaseTaskBody(BaseModel):
    title: str = Field(..., min_length=2, max_length=200)
    description: str = ""
    assignee_role: str = "pm"
    priority: str = "High"
    due_minutes: int = 1440


class CaseCommunicationAckBody(BaseModel):
    note: str = ""


class CaseLinkBody(BaseModel):
    related_case_id: str = Field(..., min_length=4, max_length=120)
    note: str = ""


class CaseBaselineBody(BaseModel):
    baseline_name: str = "Operations Control Plane v1"


def register_operations_control_routes(
    api_router: APIRouter, db, require_admin,
    get_database_authority_plan: Optional[Callable[[], Any]] = None,
):
    """Attach the OCC endpoints to the platform's ``api_router``."""

    registry = build_registry(db)

    def _payload_envelope(payload: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        envelope = dict(payload or {})
        envelope["_db"] = db
        envelope["_database_authority_plan"] = get_database_authority_plan() if callable(get_database_authority_plan) else None
        runtime_identity_getter = getattr(api_router, "_get_runtime_identity", None)
        envelope["_runtime_identity_bundle"] = runtime_identity_getter() if callable(runtime_identity_getter) else None
        return envelope

    async def _actor_dict(actor: Any) -> Dict[str, Any]:
        # `require_admin` returns different shapes across the codebase;
        # normalize to a stable envelope.
        if isinstance(actor, dict):
            return {
                "id": actor.get("id") or actor.get("email") or "admin",
                "email": actor.get("email") or "",
                "role": actor.get("role") or "admin",
            }
        return {"id": "admin", "email": "", "role": "admin"}

    def _op_or_404(operation_id: str):
        op = registry.get(operation_id)
        if not op:
            raise HTTPException(404, f"unknown operation: {operation_id}")
        return op

    @api_router.get("/admin/operations-control/overview")
    async def overview(actor=Depends(require_admin)):
        """Cheap read-only fan-out over every status_fn."""
        cards = []
        for op in registry.values():
            card: Dict[str, Any] = {**op.to_public_dict()}
            latest_dry_run = await occ_audit.latest_for_operation(
                db,
                operation_id=op.id,
                mode="dry_run",
            )
            latest_apply = await occ_audit.latest_for_operation(
                db,
                operation_id=op.id,
                mode="apply",
            )
            card["capability"] = occ_operation_capability(
                {**op.to_public_dict(), "confirmation_phrase": op.confirmation_phrase},
                available=bool(op.status_fn or op.apply_fn or op.dry_run_fn),
                disabled_reason=op.manual_reason or "",
            )
            card["repair_contract"] = {
                "dry_run_required": bool(op.requires_dry_run),
                "confirmation_phrase": op.confirmation_phrase,
                "last_dry_run": latest_dry_run,
                "last_apply": latest_apply,
            }
            if op.status_fn:
                try:
                    card["status_snapshot"] = await op.status_fn(_payload_envelope())
                except Exception as e:  # noqa: BLE001
                    card["status_snapshot"] = {
                        "status": "unavailable", "error": str(e)[:200],
                    }
            cards.append(card)
        return {"count": len(cards), "operations": cards}

    @api_router.get("/admin/operations-control/registry")
    async def control_plane_registry(actor=Depends(require_admin)):
        await ensure_case_management_indexes(db)
        snapshot = await ensure_registry_snapshot(db)
        return {
            "registry": operations_control_plane_registry_summary(),
            "snapshot": snapshot,
        }

    @api_router.get("/admin/operations-control/cases")
    async def control_plane_cases(
        status: Optional[str] = None,
        severity: Optional[str] = None,
        project_number: Optional[str] = None,
        limit: int = 200,
        actor=Depends(require_admin),
    ):
        await ensure_case_management_indexes(db)
        return await list_cases(
            db,
            status=status,
            severity=severity,
            project_number=project_number,
            limit=min(max(limit, 1), 500),
        )

    @api_router.get("/admin/operations-control/cases/{case_id}")
    async def control_plane_case_detail(case_id: str, actor=Depends(require_admin)):
        await ensure_case_management_indexes(db)
        row = await get_case_by_id(db, case_id)
        if not row:
            raise HTTPException(404, f"unknown case_id: {case_id}")
        return row

    @api_router.get("/admin/operations-control/cases/{case_id}/assembly")
    async def control_plane_case_assembly(case_id: str, actor=Depends(require_admin)):
        await ensure_case_management_indexes(db)
        try:
            return await build_case_assembly(db, case_id)
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc

    @api_router.get("/admin/operations-control/cases/{case_id}/timeline")
    async def control_plane_case_timeline(case_id: str, actor=Depends(require_admin)):
        await ensure_case_management_indexes(db)
        try:
            rows = await build_case_timeline(db, case_id)
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc
        return {"count": len(rows), "timeline": rows}

    @api_router.get("/admin/operations-control/cases/{case_id}/graph")
    async def control_plane_case_graph(case_id: str, actor=Depends(require_admin)):
        await ensure_case_management_indexes(db)
        try:
            return await build_case_relationship_graph(db, case_id)
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc

    @api_router.post("/admin/operations-control/cases/{case_id}/transitions")
    async def control_plane_case_transition(
        request: Request,
        case_id: str,
        body: CaseTransitionBody,
        actor=Depends(require_admin),
    ):
        await ensure_case_management_indexes(db)
        actor_dict = await _actor_dict(actor)
        try:
            case_doc = await get_case_by_id(db, case_id)
            if not case_doc:
                raise HTTPException(404, f"unknown case_id: {case_id}")
            await require_governed_action(
                db,
                actor=actor_dict,
                action_key="operational_case.close" if str(body.to_status).upper() == "CLOSED" else "operational_case.transition",
                resource_type="operational_case",
                resource=case_doc,
                requested_context={"project_number": case_doc.get("project_number"), "target_status": body.to_status},
                request=request,
            )
            row = await transition_case(
                db,
                case_id=case_id,
                to_status=body.to_status,
                actor=actor_dict,
                reason=body.reason,
                resolution_summary=body.resolution_summary,
                root_cause=body.root_cause,
                verification_notes=body.verification_notes,
                duplicate_of_case_id=body.duplicate_of_case_id,
            )
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        return {"ok": True, "case": row}

    @api_router.post("/admin/operations-control/cases/{case_id}/tasks")
    async def control_plane_case_create_task(
        case_id: str,
        body: CaseTaskBody,
        actor=Depends(require_admin),
    ):
        await ensure_case_management_indexes(db)
        actor_dict = await _actor_dict(actor)
        try:
            return await create_case_task(
                db,
                case_id=case_id,
                actor=actor_dict,
                title=body.title,
                description=body.description,
                assignee_role=body.assignee_role,
                priority=body.priority,
                due_minutes=body.due_minutes,
            )
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc

    @api_router.post("/admin/operations-control/cases/{case_id}/communications/{communication_id}/ack")
    async def control_plane_case_ack_communication(
        case_id: str,
        communication_id: str,
        body: CaseCommunicationAckBody,
        actor=Depends(require_admin),
    ):
        await ensure_case_management_indexes(db)
        actor_dict = await _actor_dict(actor)
        try:
            row = await acknowledge_case_communication(
                db,
                case_id=case_id,
                communication_id=communication_id,
                actor=actor_dict,
                note=body.note,
            )
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc
        return {"ok": True, "case": row}

    @api_router.post("/admin/operations-control/cases/{case_id}/related")
    async def control_plane_case_link_related(
        case_id: str,
        body: CaseLinkBody,
        actor=Depends(require_admin),
    ):
        await ensure_case_management_indexes(db)
        actor_dict = await _actor_dict(actor)
        try:
            row = await link_related_case(
                db,
                case_id=case_id,
                related_case_id=body.related_case_id,
                actor=actor_dict,
                note=body.note,
            )
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc
        except ValueError as exc:
            raise HTTPException(422, str(exc)) from exc
        return {"ok": True, "case": row}

    @api_router.post("/admin/operations-control/cases/{case_id}/evidence")
    async def control_plane_case_capture_evidence(case_id: str, actor=Depends(require_admin)):
        await ensure_case_management_indexes(db)
        actor_dict = await _actor_dict(actor)
        try:
            evidence = await capture_case_evidence_package(db, case_id=case_id, actor=actor_dict)
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc
        return {"ok": True, "evidence": evidence}

    @api_router.post("/admin/operations-control/cases/{case_id}/baseline")
    async def control_plane_case_include_baseline(
        request: Request,
        case_id: str,
        body: CaseBaselineBody,
        actor=Depends(require_admin),
    ):
        await ensure_case_management_indexes(db)
        actor_dict = await _actor_dict(actor)
        try:
            case_doc = await get_case_by_id(db, case_id)
            if not case_doc:
                raise HTTPException(404, f"unknown case_id: {case_id}")
            await require_governed_action(
                db,
                actor=actor_dict,
                action_key="baseline.capture",
                resource_type="operational_case",
                resource=case_doc,
                requested_context={"project_number": case_doc.get("project_number"), "baseline_name": body.baseline_name},
                request=request,
            )
            baseline = await include_case_in_baseline(
                db,
                case_id=case_id,
                actor=actor_dict,
                baseline_name=body.baseline_name,
            )
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc
        return {"ok": True, "baseline": baseline}

    @api_router.post("/admin/operations-control/cases/{case_id}/export")
    async def control_plane_case_export(request: Request, case_id: str, actor=Depends(require_admin)):
        await ensure_case_management_indexes(db)
        actor_dict = await _actor_dict(actor)
        try:
            case_doc = await get_case_by_id(db, case_id)
            if not case_doc:
                raise HTTPException(404, f"unknown case_id: {case_id}")
            await require_governed_action(
                db,
                actor=actor_dict,
                action_key="evidence.export",
                resource_type="operational_case",
                resource=case_doc,
                requested_context={"project_number": case_doc.get("project_number")},
                request=request,
            )
            export_row = await export_case_evidence_package(db, case_id=case_id, actor=actor_dict)
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc
        return {"ok": True, "export": export_row}

    @api_router.post("/admin/operations-control/certifications/preview-daily-report")
    async def control_plane_create_preview_case_certification(actor=Depends(require_admin)):
        if is_release_deferred("internal_certification_route"):
            raise_release_deferred_404("internal_certification_route")
        await ensure_case_management_indexes(db)
        actor_dict = await _actor_dict(actor)
        return await create_preview_case_certification_record(db, actor=actor_dict)

    @api_router.post("/admin/operations-control/certifications/run")
    async def control_plane_run_certification(request: Request, actor=Depends(require_admin)):
        if is_release_deferred("internal_certification_route"):
            raise_release_deferred_404("internal_certification_route")
        await ensure_case_management_indexes(db)
        actor_dict = await _actor_dict(actor)
        await require_governed_action(
            db,
            actor=actor_dict,
            action_key="baseline.capture",
            resource_type="operations_control_certification",
            resource={"id": "oppc-v1-certification", "project_number": ""},
            requested_context={"scope": "platform_certification"},
            request=request,
        )
        return await run_case_certification_chain(db, actor=actor_dict)

    @api_router.get("/admin/operations-control/events")
    async def control_plane_events(
        workflow_id: Optional[str] = None,
        limit: int = 50,
        actor=Depends(require_admin),
    ):
        rows = await list_recent_control_plane_events(db, workflow_id=workflow_id, limit=limit)
        return {"count": len(rows), "events": rows}

    @api_router.get("/admin/operations-control/communications")
    async def control_plane_communications(
        workflow_id: Optional[str] = None,
        limit: int = 50,
        actor=Depends(require_admin),
    ):
        rows = await list_recent_communications(db, workflow_id=workflow_id, limit=limit)
        return {"count": len(rows), "communications": rows}

    @api_router.get("/admin/operations-control/communications/{communication_id}")
    async def control_plane_communication_get(communication_id: str, actor=Depends(require_admin)):
        row = await get_communication_by_id(db, communication_id)
        if not row:
            raise HTTPException(404, f"unknown communication_id: {communication_id}")
        return row

    @api_router.post("/admin/operations-control/escalations/run")
    async def control_plane_run_escalations(actor=Depends(require_admin)):
        return await run_due_escalations(db)

    @api_router.get("/admin/operations-control/evidence")
    async def control_plane_evidence(
        workflow_id: Optional[str] = None,
        limit: int = 10,
        actor=Depends(require_admin),
    ):
        rows = await list_recent_evidence_packages(db, workflow_id=workflow_id, limit=limit)
        return {"count": len(rows), "evidence": rows}

    @api_router.post("/admin/operations-control/evidence")
    async def control_plane_capture_evidence(
        payload: Optional[Dict[str, Any]] = Body(default=None),
        actor=Depends(require_admin),
    ):
        actor_dict = await _actor_dict(actor)
        body = payload or {}
        workflow_id = str(body.get("workflow_id") or "oppc.daily_report_to_oppc").strip() or "oppc.daily_report_to_oppc"
        record_id = str(body.get("record_id") or "").strip() or None
        evidence = await build_readiness_evidence_package(
            db,
            workflow_id=workflow_id,
            actor_label=actor_dict.get("email") or actor_dict.get("id") or "admin",
            record_id=record_id,
        )
        return {"ok": True, "evidence": evidence}

    @api_router.get("/admin/operations-control/baselines")
    async def control_plane_baselines(limit: int = 10, actor=Depends(require_admin)):
        rows = await list_recent_baselines(db, limit=limit)
        return {"count": len(rows), "baselines": rows}

    @api_router.post("/admin/operations-control/baselines")
    async def control_plane_capture_baseline(
        payload: Optional[Dict[str, Any]] = Body(default=None),
        actor=Depends(require_admin),
    ):
        actor_dict = await _actor_dict(actor)
        baseline_name = str((payload or {}).get("baseline_name") or "Operations Control Plane v1").strip() or "Operations Control Plane v1"
        baseline = await build_baseline_snapshot(
            db,
            baseline_name=baseline_name,
            actor_label=actor_dict.get("email") or actor_dict.get("id") or "admin",
        )
        return {"ok": True, "baseline": baseline}

    @api_router.get("/admin/shared-capabilities")
    async def shared_capabilities(actor=Depends(require_admin)):
        shell_caps = [
            shell_signout_capability(portal="admin", route="/api/auth/multi-logout"),
            shell_signout_capability(portal="pm", route="/api/auth/multi-logout"),
            shell_signout_capability(portal="hr", route="/api/auth/multi-logout"),
            shell_signout_capability(portal="safety", route="/api/auth/multi-logout"),
            shell_signout_capability(portal="dispatch", route="/api/auth/multi-logout"),
            shell_signout_capability(portal="shop", route="/api/auth/multi-logout"),
        ]
        truth_caps = [truth_action_capability(surface_id="integration_truth", route="/api/admin/integrations/truth-status")]
        occ_caps = [
            occ_operation_capability(
                {**op.to_public_dict(), "confirmation_phrase": op.confirmation_phrase},
                available=bool(op.status_fn or op.apply_fn or op.dry_run_fn),
                disabled_reason=op.manual_reason or "",
            )
            for op in registry.values()
        ]
        return {"count": len(shell_caps) + len(truth_caps) + len(occ_caps), "capabilities": shell_caps + truth_caps + occ_caps}

    @api_router.get("/admin/trust-reconciliation")
    async def trust_reconciliation(actor=Depends(require_admin)):
        return reconcile_shared_foundation()

    @api_router.get("/admin/operations-control/operations")
    async def list_operations(actor=Depends(require_admin)):
        return {
            "count": len(registry),
            "operations": [op.to_public_dict() for op in registry.values()],
        }

    @api_router.get(
        "/admin/operations-control/operations/{operation_id}",
    )
    async def get_operation(operation_id: str, actor=Depends(require_admin)):
        op = _op_or_404(operation_id)
        return op.to_public_dict()

    @api_router.post(
        "/admin/operations-control/operations/{operation_id}/dry-run",
    )
    async def dry_run(
        operation_id: str,
        payload: Optional[Dict[str, Any]] = Body(default=None),
        actor=Depends(require_admin),
    ):
        op = _op_or_404(operation_id)
        if not op.dry_run_fn:
            raise HTTPException(
                400, f"operation `{operation_id}` has no dry-run handler",
            )
        actor_dict = await _actor_dict(actor)
        p = _payload_envelope(payload)
        p["actor_email"] = actor_dict.get("email")
        try:
            result = await op.dry_run_fn(p)
            error = None
        except Exception as e:  # noqa: BLE001
            result = {"status": "failed", "error": str(e)[:400]}
            error = str(e)[:400]
        action_id = await occ_audit.write(
            db, operation_id=operation_id, mode="dry_run",
            actor=actor_dict, risk=op.risk.value, result=result,
            reason=(payload or {}).get("reason"), error=error,
        )
        return {"action_id": action_id, "result": result}

    @api_router.post(
        "/admin/operations-control/operations/{operation_id}/apply",
    )
    async def apply(
        operation_id: str,
        payload: Optional[Dict[str, Any]] = Body(default=None),
        actor=Depends(require_admin),
    ):
        op = _op_or_404(operation_id)
        if not op.apply_fn:
            raise HTTPException(
                400,
                f"operation `{operation_id}` is read-only or "
                "manual-required; no apply handler.",
            )
        p = _payload_envelope(payload)

        # Enforce dry-run + confirmation contracts.
        if op.requires_dry_run and not p.get("dry_run_id"):
            raise HTTPException(400, "dry_run_id required")
        if op.requires_dry_run:
            recent_dry_run = await occ_audit.latest_for_operation(
                db,
                operation_id=operation_id,
                mode="dry_run",
                dry_run_id=str(p.get("dry_run_id") or ""),
            )
            if not recent_dry_run:
                raise HTTPException(400, "dry_run_id is missing, expired, or does not belong to this operation")
        if op.confirmation_phrase and (
            p.get("confirmation_phrase") != op.confirmation_phrase
        ):
            raise HTTPException(
                400,
                f"confirmation_phrase must equal '{op.confirmation_phrase}'",
            )

        actor_dict = await _actor_dict(actor)
        p["actor_email"] = actor_dict.get("email")
        error: Optional[str] = None
        try:
            result = await op.apply_fn(p)
            if isinstance(result, dict) and result.get("status") == "failed":
                error = str(result.get("error") or "")[:400]
        except Exception as e:  # noqa: BLE001
            result = {"status": "failed", "error": str(e)[:400]}
            error = str(e)[:400]

        action_id = await occ_audit.write(
            db, operation_id=operation_id, mode="apply",
            actor=actor_dict, risk=op.risk.value, result=result,
            before=result.get("before") if isinstance(result, dict) else None,
            after=result.get("after") if isinstance(result, dict) else None,
            confirmation_phrase=p.get("confirmation_phrase"),
            dry_run_id=p.get("dry_run_id"),
            reason=p.get("reason"), error=error,
        )
        return {"action_id": action_id, "result": result}

    @api_router.get("/admin/operations-control/audit")
    async def audit_list(
        limit: int = 100,
        operation_id: Optional[str] = None,
        actor_id: Optional[str] = None,
        actor=Depends(require_admin),
    ):
        rows = await occ_audit.list_recent(
            db, limit=limit, operation_id=operation_id, actor_id=actor_id,
        )
        return {"count": len(rows), "audit": rows}

    @api_router.get("/admin/operations-control/audit/summary")
    async def audit_summary(limit: int = 200, actor=Depends(require_admin)):
        rows = await occ_audit.list_recent(db, limit=limit)
        by_mode: Dict[str, int] = {}
        by_operation: Dict[str, int] = {}
        failures = 0
        for row in rows:
            mode = str(row.get("mode") or "unknown")
            op_id = str(row.get("operation_id") or "unknown")
            by_mode[mode] = by_mode.get(mode, 0) + 1
            by_operation[op_id] = by_operation.get(op_id, 0) + 1
            if row.get("error"):
                failures += 1
        top_operations = [
            {"operation_id": op_id, "count": count}
            for op_id, count in sorted(by_operation.items(), key=lambda item: (-item[1], item[0]))[:10]
        ]
        return {
            "count": len(rows),
            "by_mode": by_mode,
            "failure_count": failures,
            "top_operations": top_operations,
        }

    @api_router.get("/admin/operations-control/audit/{action_id}")
    async def audit_get(action_id: str, actor=Depends(require_admin)):
        row = await occ_audit.get(db, action_id)
        if not row:
            raise HTTPException(404, f"unknown action_id: {action_id}")
        return row

    return api_router
