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

from fastapi import APIRouter, Body, Depends, HTTPException

from lib.trust_reconciliation import reconcile_shared_foundation
from lib.shared_capabilities import occ_operation_capability, shell_signout_capability, truth_action_capability
from services.operations_control import build_registry
from services.operations_control import audit as occ_audit


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
            card["capability"] = occ_operation_capability(
                {**op.to_public_dict(), "confirmation_phrase": op.confirmation_phrase},
                available=bool(op.status_fn or op.apply_fn or op.dry_run_fn),
                disabled_reason=op.manual_reason or "",
            )
            if op.status_fn:
                try:
                    card["status_snapshot"] = await op.status_fn(_payload_envelope())
                except Exception as e:  # noqa: BLE001
                    card["status_snapshot"] = {
                        "status": "unavailable", "error": str(e)[:200],
                    }
            cards.append(card)
        return {"count": len(cards), "operations": cards}

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

    @api_router.get("/admin/operations-control/audit/{action_id}")
    async def audit_get(action_id: str, actor=Depends(require_admin)):
        row = await occ_audit.get(db, action_id)
        if not row:
            raise HTTPException(404, f"unknown action_id: {action_id}")
        return row

    return api_router
