"""OMEGA · FOCP Release 2 · TR-0002 · Universal Undo / Recovery Layer.

Additive recovery extension on top of the existing transition
infrastructure. Does NOT replace ``lib/workflow_state_machine.py``,
``lib/workflow_state_events.py``, or any of the 5 lifecycle routes
(incident / daily_report / qaqc / site_inspection / payroll_variance).

What it adds (and only what it adds):
    1) A single unified "Undo last transition" endpoint that works
       across every workflow that already writes to
       ``workflow_state_events``. The endpoint:
           * Looks up the last non-undo state-event for the record
           * Reverses ``lifecycle_state`` on the canonical record back
             to that event's ``from_state``
           * Writes a NEW state_event row tagged ``evidence.undo=True``
             so the audit stream preserves both the original transition
             and its reversal (append-only — original row is NEVER
             mutated)
           * Requires Admin authority + a mandatory written reason
    2) A cross-workflow recovery audit stream endpoint for the new
       Admin Recovery Stream visibility page.

Workflow → collection map: every supported workflow's canonical
collection is registered here so the endpoint can resolve and mutate
``lifecycle_state`` consistently. Workflows the platform does not
yet expose lifecycle for are simply absent from the map and return
422 ``workflow_not_supported``.
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, Body, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict

from lib.workflow_state_events import (
    WORKFLOW_STATE_EVENTS,
    list_state_events,
    write_state_event,
)
from lib.workflow_state_machine import (
    INCIDENT_STATES,
    DAILY_REPORT_STATES,
    QAQC_STATES,
    SITE_INSPECTION_STATES,
    PAYROLL_VARIANCE_STATES,
)

logger = logging.getLogger(__name__)


# ── Supported workflow registry ─────────────────────────────────
# Each entry maps:
#   workflow_id → (mongo_collection, canonical_states_tuple,
#                  closed_timestamp_field_or_None)
WORKFLOW_REGISTRY: Dict[str, Tuple[str, Tuple[str, ...], Optional[str]]] = {
    "incident":          ("incidents",                INCIDENT_STATES,          "lifecycle_closed_at"),
    "daily_report":      ("daily_reports",            DAILY_REPORT_STATES,      "lifecycle_closed_at"),
    "qaqc_inspection":   ("qaqc_inspections",         QAQC_STATES,              "lifecycle_closed_at"),
    "site_inspection":   ("inspections",              SITE_INSPECTION_STATES,   "lifecycle_closed_at"),
    "payroll_variance":  ("payroll_variance_batches", PAYROLL_VARIANCE_STATES,  "lifecycle_finalized_at"),
}


class UndoRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")
    reason: str


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _actor_view(actor: Any) -> Dict[str, str]:
    """Best-effort projection of the heterogeneous actor onto a flat
    {role, id, name} triple for the response body. The detailed actor
    is already preserved by write_state_event."""
    if actor is True:
        return {"role": "admin", "id": "", "name": "Admin"}
    if isinstance(actor, dict):
        role = (
            actor.get("_actor")
            or actor.get("role")
            or actor.get("_actor_kind")
            or "unknown"
        )
        return {
            "role": str(role),
            "id": str(actor.get("email") or actor.get("id") or ""),
            "name": str(actor.get("name") or ""),
        }
    return {"role": "unknown", "id": "", "name": ""}


async def _find_record(db, collection: str, record_id: str) -> Optional[Dict[str, Any]]:
    """Resolve a record by UUID-or-doc_id. Mirrors the resolution
    pattern used by every lifecycle route."""
    doc = await db[collection].find_one({"id": record_id}, {"_id": 0})
    if doc:
        return doc
    return await db[collection].find_one({"doc_id": record_id}, {"_id": 0})


async def _last_real_transition(
    db, workflow: str, record_id: str
) -> Optional[Dict[str, Any]]:
    """Return the most-recent state_event row whose evidence.undo is
    NOT truthy. Used to find the transition to reverse. None when the
    record has no transition history."""
    cursor = (
        db[WORKFLOW_STATE_EVENTS]
        .find(
            {"workflow": workflow, "record_id": record_id},
            {"_id": 0},
        )
        .sort("at", -1)
        .limit(50)
    )
    rows = await cursor.to_list(50)
    for r in rows:
        ev = r.get("evidence") or {}
        if not bool(ev.get("undo")):
            return r
    return None


def register_workflow_undo_routes(
    api_router: APIRouter,
    db,
    *,
    require_admin_dep,
):
    """Wire the FOCP Release 2 · TR-0002 endpoints.

    ``require_admin_dep`` is the strict-admin dependency from
    server.py. Undo authority is admin-only by design — the doctrine
    is "operator-led recovery without engineering intervention", and
    that recovery authority sits squarely in the admin lane. Role
    expansion (Safety, PM) requires a separate Truth Register entry."""

    @api_router.post("/workflows/{workflow}/{record_id}/undo-last-transition")
    async def undo_last_transition(
        workflow: str,
        record_id: str,
        request: Request,
        payload: UndoRequest = Body(...),
        actor=Depends(require_admin_dep),
    ) -> Dict[str, Any]:
        wf = (workflow or "").strip().lower()
        if wf not in WORKFLOW_REGISTRY:
            raise HTTPException(
                status_code=422,
                detail={"code": "workflow_not_supported", "workflow": wf},
            )
        reason = (payload.reason or "").strip()
        if len(reason) < 5:
            raise HTTPException(
                status_code=422,
                detail={"code": "undo_reason_required_min5"},
            )

        collection, states, closed_field = WORKFLOW_REGISTRY[wf]
        doc = await _find_record(db, collection, record_id)
        if not doc:
            raise HTTPException(
                status_code=404,
                detail={"code": "record_not_found",
                        "workflow": wf, "record_id": record_id},
            )

        canonical_id = str(doc.get("id") or "")
        doc_id = str(doc.get("doc_id") or "")
        current_state = str(doc.get("lifecycle_state") or "").upper()

        last = await _last_real_transition(db, wf, canonical_id)
        if not last:
            raise HTTPException(
                status_code=422,
                detail={"code": "no_transition_to_undo",
                        "message": "This record has no transition history to reverse."},
            )

        # Sanity check: the workflow's current state should match the
        # last event's to_state. If it doesn't, something raced or was
        # mutated outside the lifecycle pipeline — refuse to undo
        # rather than silently corrupt state. The operator can inspect
        # the audit stream and decide what to do.
        last_to = str(last.get("to_state") or "").upper()
        last_from = last.get("from_state")
        last_from_norm = str(last_from or "").upper() if last_from else None
        if last_to and current_state and last_to != current_state:
            raise HTTPException(
                status_code=409,
                detail={
                    "code": "undo_state_mismatch",
                    "message": "Current state does not match the last recorded transition. Refusing to reverse.",
                    "current_state": current_state,
                    "last_event_to_state": last_to,
                },
            )

        # The target state must be a recognised state (or None →
        # treated as the workflow's default by callers; we refuse to
        # write a literal None lifecycle_state, but we DO allow
        # reverting to the documented default for the workflow if the
        # original from_state was empty).
        if last_from_norm and last_from_norm not in states:
            raise HTTPException(
                status_code=422,
                detail={"code": "undo_target_state_invalid",
                        "target_state": last_from_norm},
            )

        target_state = last_from_norm or states[0]
        now = _now_iso()

        update_set: Dict[str, Any] = {
            "lifecycle_state": target_state,
            "lifecycle_updated_at": now,
        }
        # If we're reversing AWAY from a terminal/closed state, clear
        # the closed timestamp field so projections stop treating the
        # record as terminal. This mirrors the reopen logic that
        # already exists per-workflow.
        if closed_field and current_state in ("CLOSED", "FINALIZED"):
            update_set[closed_field] = None

        await db[collection].update_one(
            {"id": canonical_id},
            {"$set": update_set},
        )

        # Append the undo event. evidence.undo=True is the marker the
        # recovery audit stream and _last_real_transition use to
        # distinguish original transitions from their reversals.
        event = await write_state_event(
            db,
            workflow=wf,
            record_id=canonical_id,
            record_doc_id=doc_id,
            from_state=current_state or None,
            to_state=target_state,
            actor=actor,
            reason=reason,
            evidence={
                "undo": True,
                "undone_event_id": last.get("id") or "",
                "undone_to_state": last_to,
                "undone_from_state": last_from_norm or "",
                "undone_actor_role": last.get("actor_role") or "",
                "undone_actor_name": last.get("actor_name") or "",
                "undone_at": (
                    last.get("at").isoformat()
                    if hasattr(last.get("at"), "isoformat")
                    else last.get("at") or ""
                ),
            },
            request=request,
        )
        # JSON-serialise the timestamp on the inserted event for the
        # response body.
        at = event.get("at")
        if hasattr(at, "isoformat"):
            event["at"] = at.isoformat()

        return {
            "ok": True,
            "workflow": wf,
            "record_id": canonical_id,
            "from_state": current_state,
            "to_state": target_state,
            "lifecycle_updated_at": now,
            "actor": _actor_view(actor),
            "undo_event": event,
        }

    @api_router.get("/admin/recovery/transitions")
    async def recovery_stream(
        workflow: Optional[str] = Query(default=None),
        only_undos: bool = Query(default=False),
        limit: int = Query(default=100, ge=1, le=500),
        _: bool = Depends(require_admin_dep),
    ) -> Dict[str, Any]:
        """Cross-workflow recovery audit stream.

        Defaults to the newest 100 rows across every workflow. Pass
        ?workflow=xxx to narrow, or ?only_undos=true to surface only
        reversal events (driven by evidence.undo). Used by the new
        Admin Recovery Stream page (the existing /admin/recovery
        backup-RPO dashboard is untouched)."""
        q: Dict[str, Any] = {}
        if workflow:
            wf = workflow.strip().lower()
            if wf not in WORKFLOW_REGISTRY and wf != "jha_ack":
                raise HTTPException(
                    status_code=422,
                    detail={"code": "workflow_not_supported", "workflow": wf},
                )
            q["workflow"] = wf
        if only_undos:
            q["evidence.undo"] = True

        cursor = (
            db[WORKFLOW_STATE_EVENTS]
            .find(q, {"_id": 0})
            .sort("at", -1)
            .limit(int(limit))
        )
        rows = await cursor.to_list(int(limit))
        for r in rows:
            at = r.get("at")
            if hasattr(at, "isoformat"):
                r["at"] = at.isoformat()
            # Mark undo rows up-front so the UI can colour them.
            r["is_undo"] = bool((r.get("evidence") or {}).get("undo"))

        return {
            "events": rows,
            "count": len(rows),
            "supported_workflows": sorted(list(WORKFLOW_REGISTRY.keys()) + ["jha_ack"]),
            "computed_at": _now_iso(),
        }

    @api_router.get("/workflows/{workflow}/{record_id}/last-transition")
    async def last_transition(
        workflow: str,
        record_id: str,
        actor=Depends(require_admin_dep),
    ) -> Dict[str, Any]:
        """Return the last reversible transition for a record (the row
        the undo button would target). Used by the reusable
        ``<UndoLastTransitionButton/>`` to decide whether to render and
        what summary to show. Admin-only — matches the undo gate."""
        wf = (workflow or "").strip().lower()
        if wf not in WORKFLOW_REGISTRY:
            raise HTTPException(
                status_code=422,
                detail={"code": "workflow_not_supported", "workflow": wf},
            )
        collection, _states, _closed = WORKFLOW_REGISTRY[wf]
        doc = await _find_record(db, collection, record_id)
        if not doc:
            raise HTTPException(status_code=404, detail={"code": "record_not_found"})
        canonical_id = str(doc.get("id") or "")
        last = await _last_real_transition(db, wf, canonical_id)
        if not last:
            return {"undoable": False, "reason": "no_transition_history"}
        at = last.get("at")
        if hasattr(at, "isoformat"):
            last["at"] = at.isoformat()
        return {
            "undoable": True,
            "workflow": wf,
            "record_id": canonical_id,
            "current_state": str(doc.get("lifecycle_state") or "").upper(),
            "last_event": last,
        }


__all__ = ["register_workflow_undo_routes", "WORKFLOW_REGISTRY"]
