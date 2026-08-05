"""
routes/asset_transfers.py — Phase I · Asset Transfer System.

Thin event collection (`db.asset_transfers`) tracking the LIFECYCLE of
moving equipment between locations/projects. Equipment ownership and
`current_location` remain on `db.equipment_master` (the single SOT).
The transfer record is an EVENT — NOT a duplicate asset ledger.

Lifecycle (closed enum):
    Draft → Requested → Approved → In Transit → Received → Closed
Terminal exits: Rejected · Cancelled

Discipline rules:
  * NO duplicate asset SOT — equipment_master is the single source.
  * `equipment_master.location` is mutated ONLY on Received (atomic).
  * State machine prevents invalid jumps (e.g., Requested → Closed).
  * Tasks + Notifications fan out via `lib/event_fanout.py` (idempotent).
  * Receiving signature uses unified `signatures.py`
    (source_module=`equipment.transfer`, source_record_id=transfer_id).
  * Audit log via `lib/audit.py::append_audit` on the transfer doc.
  * PM scope via `compute_pm_scope` — list/detail filtered to PM's
    projects (from_project OR to_project must be in scope).

Endpoints:
  GET    /api/asset-transfers                 — list with filters
  GET    /api/asset-transfers/{id}            — detail
  POST   /api/asset-transfers                 — create as Requested
  POST   /api/asset-transfers/{id}/approve    — admin/dispatch
  POST   /api/asset-transfers/{id}/reject     — admin/dispatch (with reason)
  POST   /api/asset-transfers/{id}/in-transit — dispatch
  POST   /api/asset-transfers/{id}/receive    — pm/dispatch/admin (with sig payload)
  POST   /api/asset-transfers/{id}/cancel     — requester or admin
  POST   /api/asset-transfers/{id}/close      — admin/dispatch (after Received)
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from lib.enterprise_governance import governance_project_scope_numbers

logger = logging.getLogger(__name__)


# ── Closed enum guarded by validators ───────────────────────────────
STATUS_VALUES = {
    "Draft", "Requested", "Approved", "In Transit",
    "Received", "Closed", "Rejected", "Cancelled",
}

# Allowed transitions: from → set(to). Anything not listed → 422.
TRANSITIONS: Dict[str, set] = {
    "Draft":      {"Requested", "Cancelled"},
    "Requested":  {"Approved", "Rejected", "Cancelled"},
    "Approved":   {"In Transit", "Cancelled"},
    "In Transit": {"Received", "Cancelled"},
    "Received":   {"Closed"},
    "Closed":     set(),
    "Rejected":   set(),
    "Cancelled":  set(),
}

# Roles that may perform each transition.
TRANSITION_ROLES: Dict[str, set] = {
    "approve":    {"admin", "dispatch"},
    "reject":     {"admin", "dispatch"},
    "in-transit": {"admin", "dispatch"},
    "receive":    {"admin", "dispatch", "pm"},
    "cancel":     {"admin", "dispatch", "pm", "shop"},  # also requester
    "close":      {"admin", "dispatch"},
}

# Roles that may CREATE (request) a transfer.
REQUEST_ROLES = {"admin", "dispatch", "pm", "shop"}


class TransferCreate(BaseModel):
    equipment_id: str = Field(..., min_length=1, max_length=64)
    to_project_number: str = Field(..., min_length=1, max_length=64)
    to_location_label: Optional[str] = Field(default=None, max_length=200)
    from_project_number: Optional[str] = Field(default=None, max_length=64)
    from_location_label: Optional[str] = Field(default=None, max_length=200)
    requested_for: Optional[str] = Field(default=None, max_length=200,
        description="Recipient/PM name at destination (free text)")
    reason: Optional[str] = Field(default=None, max_length=2000)


class TransitionBody(BaseModel):
    notes: Optional[str] = Field(default=None, max_length=2000)
    reason: Optional[str] = Field(default=None, max_length=2000)


class ReceiveBody(BaseModel):
    notes: Optional[str] = Field(default=None, max_length=2000)
    # Optional receiving signature payload. Capture via unified engine.
    signer_name: Optional[str] = Field(default=None, max_length=160)
    signature_image: Optional[str] = Field(default=None,
        max_length=2_000_000,
        description="data:image/png;base64,... captured signature")
    refusal: bool = False
    refusal_reason: Optional[str] = Field(default=None, max_length=2000)


def build_asset_transfers_router(db, require_any_portal_token) -> APIRouter:
    router = APIRouter(tags=["asset-transfers"])

    # ── Helpers ──────────────────────────────────────────────────
    def _role(actor: Dict[str, Any]) -> str:
        return actor.get("_actor") or actor.get("role") or "admin"

    def _actor_label(actor: Dict[str, Any]) -> str:
        return (actor.get("name") or actor.get("email")
                or actor.get("_actor") or "actor")[:160]

    async def _pm_scope_nums(actor: Dict[str, Any]) -> Optional[List[str]]:
        """Return None for unrestricted (admin/dispatch/shop/safety), or
        list of project_numbers for PM."""
        role = _role(actor)
        if role != "pm":
            return None
        return await governance_project_scope_numbers(db, actor)

    async def _ensure_indexes():
        await db.asset_transfers.create_index("id", unique=True)
        await db.asset_transfers.create_index("doc_id", unique=True, sparse=True)
        await db.asset_transfers.create_index("status")
        await db.asset_transfers.create_index("equipment_id")
        await db.asset_transfers.create_index("from_project_number")
        await db.asset_transfers.create_index("to_project_number")
        await db.asset_transfers.create_index("created_at")

    async def _audit(transfer_id: str, action: str,
                     actor: Dict[str, Any], details: Optional[Dict] = None):
        try:
            from lib.audit import append_audit  # noqa: PLC0415
            await append_audit(
                db,
                collection="asset_transfers",
                record_id=transfer_id,
                action=action,
                actor={"role": _role(actor),
                       "name": _actor_label(actor)},
                details=details or {},
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("[asset_transfer] audit %s failed: %s", action, e)

    async def _fan(transfer: Dict[str, Any], event: str, actor: Dict[str, Any]):
        """Idempotent fan-out via shared event_fanout. `event` keys map
        to (task, notification) shapes."""
        try:
            from lib.event_fanout import emit_task_and_notification, emit_notification  # noqa: PLC0415
        except Exception as e:  # noqa: BLE001
            logger.warning("[asset_transfer] event_fanout import failed: %s", e)
            return

        tid = transfer["id"]
        eq = transfer.get("equipment_id") or ""
        to_pn = transfer.get("to_project_number") or ""
        from_pn = transfer.get("from_project_number") or ""

        try:
            if event == "requested":
                await emit_task_and_notification(
                    db,
                    task={
                        "title": f"Asset transfer approval needed · {eq}",
                        "description": (f"Transfer {tid} requested by "
                                        f"{_actor_label(actor)} from "
                                        f"{from_pn or '—'} to {to_pn}")[:4000],
                        "source_module": "asset.transfer",
                        "source_record_id": tid,
                        "linked_project_number": to_pn,
                        "linked_equipment_id": eq,
                        "assignee_role": "dispatch",
                        "priority": "Medium",
                        "created_by": {"role": "system", "via": "asset_transfer.requested"},
                    },
                    notification={
                        "type": "asset_transfer.requested",
                        "title": f"Asset transfer requested · {eq}",
                        "message": (f"From {from_pn or '—'} → {to_pn}")[:200],
                        "severity": "Info",
                        "recipient_role": "pm",
                        "linked_source_module": "asset.transfer",
                        "linked_source_record_id": tid,
                        "linked_project_number": from_pn or to_pn,
                        "linked_equipment_id": eq,
                    },
                )
            elif event == "approved":
                # Notify requester (best effort by role generally)
                await emit_notification(db, {
                    "type": "asset_transfer.approved",
                    "title": f"Asset transfer approved · {eq}",
                    "message": (f"Approved · ready for pickup → {to_pn}")[:200],
                    "severity": "Info",
                    "recipient_role": "pm",
                    "linked_source_module": "asset.transfer",
                    "linked_source_record_id": tid,
                    "linked_project_number": from_pn or to_pn,
                    "linked_equipment_id": eq,
                })
                # Dispatch pickup task
                await emit_task_and_notification(
                    db,
                    task={
                        "title": f"Pick up asset · {eq}",
                        "description": (f"Transfer {tid} approved. Source: "
                                        f"{from_pn or '—'} → {to_pn}.")[:4000],
                        "source_module": "asset.transfer",
                        "source_record_id": tid,
                        "linked_project_number": to_pn,
                        "linked_equipment_id": eq,
                        "assignee_role": "dispatch",
                        "priority": "Medium",
                        "created_by": {"role": "system", "via": "asset_transfer.approved"},
                    },
                    notification={
                        "type": "asset_transfer.dispatch_pickup",
                        "title": f"Dispatch pickup ready · {eq}",
                        "message": (f"Pickup from {from_pn or '—'}")[:200],
                        "severity": "Info",
                        "recipient_role": "dispatch",
                        "linked_source_module": "asset.transfer",
                        "linked_source_record_id": tid,
                    },
                )
            elif event == "in_transit":
                await emit_notification(db, {
                    "type": "asset_transfer.in_transit",
                    "title": f"Asset inbound · {eq}",
                    "message": (f"En route to {to_pn}")[:200],
                    "severity": "Info",
                    "recipient_role": "pm",
                    "linked_source_module": "asset.transfer",
                    "linked_source_record_id": tid,
                    "linked_project_number": to_pn,
                    "linked_equipment_id": eq,
                })
            elif event == "received":
                # Source PM + Dispatch closed loop
                await emit_notification(db, {
                    "type": "asset_transfer.received",
                    "title": f"Asset received · {eq}",
                    "message": (f"At {to_pn} · from {from_pn or '—'}")[:200],
                    "severity": "Info",
                    "recipient_role": "pm",
                    "linked_source_module": "asset.transfer",
                    "linked_source_record_id": tid,
                    "linked_project_number": from_pn or to_pn,
                    "linked_equipment_id": eq,
                })
                await emit_notification(db, {
                    "type": "asset_transfer.received",
                    "title": f"Asset received · {eq}",
                    "message": (f"At {to_pn}")[:200],
                    "severity": "Info",
                    "recipient_role": "dispatch",
                    "linked_source_module": "asset.transfer",
                    "linked_source_record_id": tid,
                })
            elif event == "rejected":
                await emit_notification(db, {
                    "type": "asset_transfer.rejected",
                    "title": f"Asset transfer rejected · {eq}",
                    "message": (transfer.get("rejection_reason") or "Rejected")[:200],
                    "severity": "Warning",
                    "recipient_role": "pm",
                    "linked_source_module": "asset.transfer",
                    "linked_source_record_id": tid,
                    "linked_project_number": from_pn or to_pn,
                    "linked_equipment_id": eq,
                })
        except Exception as e:  # noqa: BLE001
            logger.warning("[asset_transfer] fan %s failed: %s", event, e)

    def _strip(doc: Dict[str, Any]) -> Dict[str, Any]:
        if not doc:
            return doc
        doc.pop("_id", None)
        return doc

    async def _load_equipment(equipment_id: str) -> Optional[Dict[str, Any]]:
        return await db.equipment_master.find_one(
            {"id": equipment_id}, {"_id": 0})

    async def _assert_can_view(transfer: Dict[str, Any],
                               actor: Dict[str, Any]) -> None:
        """403 if PM and transfer doesn't touch a project in their scope."""
        nums = await _pm_scope_nums(actor)
        if nums is None:
            return
        from_pn = transfer.get("from_project_number")
        to_pn = transfer.get("to_project_number")
        if from_pn in nums or to_pn in nums:
            return
        raise HTTPException(403, "Out of project scope.")

    def _validate_transition(current: str, target: str) -> None:
        if current not in TRANSITIONS or target not in STATUS_VALUES:
            raise HTTPException(422, f"invalid status: {current} → {target}")
        if target not in TRANSITIONS[current]:
            raise HTTPException(422,
                f"transition not allowed: {current} → {target}")

    def _require_role(actor: Dict[str, Any], allowed: set) -> str:
        role = _role(actor)
        if role not in allowed:
            raise HTTPException(403,
                f"role '{role}' not permitted (need one of "
                f"{sorted(allowed)})")
        return role

    # ── Routes ───────────────────────────────────────────────────
    @router.get("/api/asset-transfers")
    async def list_transfers(
        actor: Dict[str, Any] = Depends(require_any_portal_token),
        status: Optional[str] = Query(default=None),
        doc_id: Optional[str] = Query(default=None),
        equipment_id: Optional[str] = Query(default=None),
        project_number: Optional[str] = Query(default=None),
        audience: Optional[str] = Query(
            default=None,
            description=(
                "Optional audience filter. `operator` strips audit / test / "
                "demo / validation / smoke / sample residue using the canonical "
                "`backend/lib/transfer_visibility.py` rules — see Track 15.83B. "
                "Omit (or pass anything else) to receive the unfiltered list, "
                "preserving the existing default behavior for admin/audit "
                "callers."
            ),
        ),
        limit: int = Query(default=200, ge=1, le=500),
    ) -> Dict[str, Any]:
        q: Dict[str, Any] = {}
        if status:
            q["status"] = status
        if doc_id:
            q["doc_id"] = doc_id.strip().upper()
        if equipment_id:
            q["equipment_id"] = equipment_id
        if project_number:
            q["$or"] = [
                {"from_project_number": project_number},
                {"to_project_number": project_number},
            ]
        # PM scope
        nums = await _pm_scope_nums(actor)
        if nums is not None:
            if not nums:
                return {"items": [], "total": 0}
            scope_clause = {"$or": [
                {"from_project_number": {"$in": nums}},
                {"to_project_number": {"$in": nums}},
            ]}
            q = {"$and": [q, scope_clause]} if q else scope_clause
        items: List[Dict[str, Any]] = []
        async for d in db.asset_transfers.find(
            q, {"_id": 0}
        ).sort("created_at", -1).limit(limit):
            items.append(d)

        # TRACK 15.83B — opt-in operator audience filtering. Backend
        # canonical so the dispatch landing surface (and any future
        # native client) shares the same trust rules.
        if (audience or "").strip().lower() == "operator":
            from lib.transfer_visibility import (
                filter_operator_visible_transfers,
            )  # noqa: PLC0415 — local import keeps cold-import paths tiny
            visible, suppressed = filter_operator_visible_transfers(items)
            return {
                "items": list(visible),
                "total": len(visible),
                "audience": "operator",
                "suppressed_count": suppressed,
            }

        return {"items": items, "total": len(items)}

    @router.get("/api/asset-transfers/{tid}")
    async def get_transfer(
        tid: str,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        doc = await db.asset_transfers.find_one({"id": tid}, {"_id": 0})
        if not doc:
            raise HTTPException(404, "Not found")
        await _assert_can_view(doc, actor)
        return doc

    @router.post("/api/asset-transfers")
    async def create_transfer(
        body: TransferCreate,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        await _ensure_indexes()
        _require_role(actor, REQUEST_ROLES)
        eq = await _load_equipment(body.equipment_id)
        if not eq:
            raise HTTPException(404, "equipment not found")

        # If from_project is omitted, infer from equipment_master.
        from_pn = body.from_project_number or eq.get("current_project_number")
        from_loc = body.from_location_label or eq.get("location") or ""

        now = datetime.now(timezone.utc)
        doc = {
            "id": str(uuid.uuid4()),
            "status": "Requested",
            "equipment_id": body.equipment_id,
            "equipment_unit_id": eq.get("unit_id") or eq.get("unit_number") or eq.get("asset_id"),
            "equipment_label": (eq.get("name") or eq.get("unit_id")
                                or eq.get("asset_id")
                                or body.equipment_id)[:200],
            "equipment_category": eq.get("category") or "",
            "equipment_type": eq.get("type") or eq.get("asset_type") or "",
            # Track 13.31B-D5 · canonical taxonomy snapshot (read-side resolver).
            "canonical_asset_class": eq.get("asset_class") or None,
            "canonical_asset_type": eq.get("asset_type") or None,
            "canonical_taxonomy_verified": bool(eq.get("taxonomy_verified")),
            "from_project_number": from_pn,
            "from_location_label": from_loc[:200] if from_loc else None,
            "to_project_number": body.to_project_number,
            "to_location_label": body.to_location_label,
            "requested_for": body.requested_for,
            "reason": body.reason,
            "requested_by": _actor_label(actor),
            "requested_by_role": _role(actor),
            "rejection_reason": None,
            "approved_at": None,
            "in_transit_at": None,
            "received_at": None,
            "closed_at": None,
            "cancelled_at": None,
            "rejected_at": None,
            "receiver_signature_id": None,
            "created_at": now,
            "updated_at": now,
            "audit": [],
        }
        from doc_ids import ensure_doc_id  # noqa: PLC0415
        await ensure_doc_id(db, doc, "ATR", when=now)
        # ── Phase 2B-2A · Job-ownership team_snapshot embed ──
        # Anchor on the originating (from) project. Cross-job moves
        # preserve the roster at the moment of request.
        try:
            from lib.team_routing import snapshot_team  # noqa: PLC0415
            _snap = await snapshot_team(db, doc.get("from_project_number"))
            if _snap:
                doc["team_snapshot"] = _snap
        except Exception:  # noqa: BLE001
            pass
        await db.asset_transfers.insert_one(doc)
        await _audit(doc["id"], "requested", actor,
                     {"to_project_number": body.to_project_number})
        await _fan(doc, "requested", actor)
        return _strip(doc)

    async def _transition(
        tid: str, action: str, target: str,
        actor: Dict[str, Any],
        timestamp_field: Optional[str] = None,
        extra: Optional[Dict[str, Any]] = None,
    ):
        """Generic state-machine apply. Returns (doc, transitioned: bool)
        where transitioned=False indicates an idempotent re-click (no
        side effects fired)."""
        existing = await db.asset_transfers.find_one(
            {"id": tid}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "Not found")
        await _assert_can_view(existing, actor)
        _require_role(actor, TRANSITION_ROLES[action])
        # Idempotency: if already at target, return as-is (no double fan).
        if existing.get("status") == target:
            return existing, False
        _validate_transition(existing.get("status"), target)

        now = datetime.now(timezone.utc)
        update: Dict[str, Any] = {"status": target, "updated_at": now}
        if timestamp_field:
            update[timestamp_field] = now
        if extra:
            update.update(extra)
        await db.asset_transfers.update_one(
            {"id": tid, "status": existing["status"]},
            {"$set": update},
        )
        await _audit(tid, action, actor, extra or {})
        doc = await db.asset_transfers.find_one({"id": tid}, {"_id": 0})
        return doc, True

    @router.post("/api/asset-transfers/{tid}/approve")
    async def approve(
        tid: str, body: TransitionBody = TransitionBody(),
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        doc, did = await _transition(
            tid, "approve", "Approved", actor,
            timestamp_field="approved_at",
            extra={"approval_notes": body.notes} if body.notes else None,
        )
        if did:
            await _fan(doc, "approved", actor)
        return doc

    @router.post("/api/asset-transfers/{tid}/reject")
    async def reject(
        tid: str, body: TransitionBody,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        if not body.reason:
            raise HTTPException(422, "reason is required to reject a transfer")
        doc, did = await _transition(
            tid, "reject", "Rejected", actor,
            timestamp_field="rejected_at",
            extra={"rejection_reason": body.reason[:2000]},
        )
        if did:
            await _fan(doc, "rejected", actor)
        return doc

    @router.post("/api/asset-transfers/{tid}/in-transit")
    async def mark_in_transit(
        tid: str, body: TransitionBody = TransitionBody(),
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        doc, did = await _transition(
            tid, "in-transit", "In Transit", actor,
            timestamp_field="in_transit_at",
        )
        if did:
            await _fan(doc, "in_transit", actor)
            # Phase 5 — trench-aware sync (safe no-op for non-trench assets)
            try:
                from routes.trench_transport_bridge import on_transfer_in_transit  # noqa: PLC0415
                await on_transfer_in_transit(db, transfer=doc, actor_label=_actor_label(actor))
            except Exception as _e:  # noqa: BLE001
                logger.warning("[asset_transfer] trench sync (in_transit) failed: %s", _e)
        return doc

    @router.post("/api/asset-transfers/{tid}/receive")
    async def receive(
        tid: str, body: ReceiveBody,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        # Receive REQUIRES a signature OR a refusal record — protects
        # against silent receipt.
        if not body.refusal and not body.signature_image:
            raise HTTPException(422,
                "receive requires a signature_image or refusal=true")

        # Apply the state transition first.
        doc, did = await _transition(
            tid, "receive", "Received", actor,
            timestamp_field="received_at",
            extra={"receive_notes": body.notes} if body.notes else None,
        )

        # Only capture signature + sync equipment if a real transition
        # happened (idempotent re-click stays silent).
        if did:
            try:
                from routes.signatures import signature_service  # noqa: PLC0415
                sig_payload = {
                    "source_module": "equipment.transfer",
                    "source_record_id": tid,
                    "signer_name": (body.signer_name
                                    or _actor_label(actor))[:160],
                    "signature_type": "receiver",
                    "signature_image": body.signature_image,
                    "refusal": body.refusal,
                    "refusal_reason": body.refusal_reason,
                    "created_by": {"role": _role(actor),
                                   "name": _actor_label(actor)},
                }
                sig = await signature_service.capture(db, sig_payload)
                await db.asset_transfers.update_one(
                    {"id": tid},
                    {"$set": {"receiver_signature_id": sig.get("id")}},
                )
                doc["receiver_signature_id"] = sig.get("id")
            except Exception as e:  # noqa: BLE001
                logger.warning("[asset_transfer] signature capture failed: %s", e)

            # ATOMIC equipment_master location update — ONLY on Received.
            try:
                await db.equipment_master.update_one(
                    {"id": doc["equipment_id"]},
                    {"$set": {
                        "current_project_number": doc.get("to_project_number"),
                        "location": doc.get("to_location_label")
                                     or doc.get("to_project_number") or "",
                        "updated_at": datetime.now(timezone.utc),
                    }},
                )
            except Exception as e:  # noqa: BLE001
                logger.warning("[asset_transfer] equipment_master sync failed: %s", e)

            await _fan(doc, "received", actor)
            # Phase 5 — trench-aware sync (safe no-op for non-trench assets)
            try:
                from routes.trench_transport_bridge import on_transfer_received  # noqa: PLC0415
                await on_transfer_received(db, transfer=doc, actor_label=_actor_label(actor))
            except Exception as _e:  # noqa: BLE001
                logger.warning("[asset_transfer] trench sync (received) failed: %s", _e)
        return doc

    @router.post("/api/asset-transfers/{tid}/cancel")
    async def cancel(
        tid: str, body: TransitionBody = TransitionBody(),
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        # Requester can cancel their own; admin/dispatch can cancel any.
        existing = await db.asset_transfers.find_one(
            {"id": tid}, {"_id": 0})
        if not existing:
            raise HTTPException(404, "Not found")
        role = _role(actor)
        if role not in {"admin", "dispatch"}:
            if existing.get("requested_by") != _actor_label(actor):
                raise HTTPException(403, "Only requester or admin may cancel.")
        doc, _did = await _transition(
            tid, "cancel", "Cancelled", actor,
            timestamp_field="cancelled_at",
            extra={"cancel_notes": body.notes} if body.notes else None,
        )
        if _did:
            try:
                from routes.trench_transport_bridge import on_transfer_cancelled  # noqa: PLC0415
                await on_transfer_cancelled(db, transfer=doc, actor_label=_actor_label(actor))
            except Exception as _e:  # noqa: BLE001
                logger.warning("[asset_transfer] trench sync (cancel) failed: %s", _e)
        return doc

    @router.post("/api/asset-transfers/{tid}/close")
    async def close(
        tid: str, body: TransitionBody = TransitionBody(),
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        doc, _did = await _transition(
            tid, "close", "Closed", actor,
            timestamp_field="closed_at",
        )
        return doc

    return router


__all__ = ["build_asset_transfers_router", "STATUS_VALUES", "TRANSITIONS"]
