"""TRACK 16.09 · Transportation Dispatch Gate + Email Pilot router.

Wires together:
  * POST /api/dispatch/transportation/check        — preview the gate
  * POST /api/dispatch/transportation/override     — authorized override
  * GET  /api/admin/transportation/dispatch-overrides
  * POST /api/admin/transportation/dispatch-overrides/{id}/revoke
  * GET  /api/admin/transportation/email-routes    — pilot status
  * PATCH /api/admin/transportation/email-routes/{key}

All routes are additive. Existing dispatch endpoints remain unchanged
except that ``create_assignment`` now invokes
``evaluate_dispatch_gate`` directly before persisting.
"""
from __future__ import annotations

import logging
import secrets
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field
from lib.enterprise_governance import build_governance_actor_context
from lib.enterprise_governance import governance_effective_permissions

from lib.transport_dispatch_gate import (
    evaluate_dispatch_gate, HUMAN_REASONS,
)

logger = logging.getLogger(__name__)

TENANT = "masci"

# Pilot route catalog · Track 16.09 enables real SMTP for these 4 only.
PILOT_ROUTE_KEYS = {
    "TRANSPORT_CARRIER_INVITE",
    "TRANSPORT_PACKET_NEEDS_CORRECTION",
    "TRANSPORT_ORIENTATION_ASSIGNED",
    "TRANSPORT_ORIENTATION_EXPIRING",
}

# Every transportation notification kind we know about — mapped to the
# canonical route_key. Drives the Admin Email Routes Control Panel.
ALL_TRANSPORT_KINDS = (
    ("carrier_invite", "TRANSPORT_CARRIER_INVITE", "Carrier invite"),
    ("packet_ready", "TRANSPORT_PACKET_READY", "Packet ready for submission"),
    ("packet_submitted", "TRANSPORT_PACKET_SUBMITTED", "Packet submitted"),
    ("packet_needs_correction", "TRANSPORT_PACKET_NEEDS_CORRECTION",
     "Packet needs correction"),
    ("packet_approved", "TRANSPORT_PACKET_APPROVED", "Packet approved"),
    ("driver_approved", "TRANSPORT_DRIVER_APPROVED", "Driver approved"),
    ("driver_suspended", "TRANSPORT_DRIVER_SUSPENDED", "Driver suspended"),
    ("orientation_assigned", "TRANSPORT_ORIENTATION_ASSIGNED",
     "Orientation assigned"),
    ("orientation_reminder", "TRANSPORT_ORIENTATION_REMINDER",
     "Orientation reminder"),
    ("orientation_expiring", "TRANSPORT_ORIENTATION_EXPIRING",
     "Orientation expiring"),
    ("orientation_overdue", "TRANSPORT_ORIENTATION_OVERDUE",
     "Orientation overdue"),
    ("annual_inspection_due", "TRANSPORT_ANNUAL_INSPECTION_DUE",
     "Annual inspection due"),
    ("annual_inspection_reminder", "TRANSPORT_ANNUAL_INSPECTION_REMINDER",
     "Annual inspection reminder"),
    ("annual_inspection_overdue", "TRANSPORT_ANNUAL_INSPECTION_OVERDUE",
     "Annual inspection overdue"),
    ("documents_expiring", "TRANSPORT_DOCUMENTS_EXPIRING",
     "Documents expiring"),
    ("documents_approved", "TRANSPORT_DOCUMENTS_APPROVED",
     "Documents approved"),
    ("documents_need_correction", "TRANSPORT_DOCUMENTS_NEED_CORRECTION",
     "Documents need correction"),
    ("driver_eligible", "TRANSPORT_DRIVER_ELIGIBLE", "Driver eligible"),
    ("driver_not_eligible", "TRANSPORT_DRIVER_NOT_ELIGIBLE",
     "Driver not eligible"),
    ("carrier_eligible", "TRANSPORT_CARRIER_ELIGIBLE", "Carrier eligible"),
    ("carrier_not_eligible", "TRANSPORT_CARRIER_NOT_ELIGIBLE",
     "Carrier not eligible"),
    ("dispatch_eligibility_changed", "TRANSPORT_DISPATCH_ELIGIBILITY_CHANGED",
     "Dispatch eligibility changed"),
)
KIND_TO_ROUTE = {k: r for k, r, _l in ALL_TRANSPORT_KINDS}


# ===========================================================================
# Pydantic models
# ===========================================================================
class GateCheckBody(BaseModel):
    driver_id: Optional[str] = None
    truck_id: Optional[str] = None
    carrier_id: Optional[str] = None
    override_id: Optional[str] = None


class OverrideCreateBody(BaseModel):
    driver_id: Optional[str] = None
    truck_id: Optional[str] = None
    carrier_id: Optional[str] = None
    reason_code: str = Field(..., min_length=1, max_length=80,
                             description=("One of: emergency_dispatch, "
                                          "compliance_pending_review, "
                                          "rolling_correction, other"))
    explanation: str = Field(..., min_length=10, max_length=600)
    duration_hours: int = Field(default=24, ge=1, le=168)
    acknowledgement: bool = Field(...)


class EmailRouteToggleBody(BaseModel):
    enabled: bool


# ===========================================================================
# Bootstrap · seed 4 pilot routes (and 18 audit-only entries)
# ===========================================================================
async def bootstrap_track_16_09(db) -> Dict[str, Any]:
    """Idempotently seed ``email_routes`` catalog entries for every
    transportation notification kind. The 4 pilot keys are flagged
    ``enabled=True`` (live send); all others remain ``enabled=False``
    (dry-run / audit-only)."""
    seeded = 0
    skipped = 0
    for _kind, route_key, label in ALL_TRANSPORT_KINDS:
        enabled = route_key in PILOT_ROUTE_KEYS
        existing = await db.email_routes.find_one(
            {"tenant_key": TENANT, "route_key": route_key})
        if existing:
            skipped += 1
            continue
        await db.email_routes.insert_one({
            "id": uuid.uuid4().hex, "tenant_key": TENANT,
            "route_key": route_key, "label": label,
            "to": [], "cc": [], "bcc": [],
            "enabled": enabled,
            "is_transportation_pilot": route_key in PILOT_ROUTE_KEYS,
            "track": "16.09",
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
        seeded += 1
    logger.info(f"[track-16-09-bootstrap] email routes · seeded={seeded} · "
                f"skipped={skipped}")
    return {"seeded": seeded, "skipped": skipped}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _is_override_authorized(actor: Dict[str, Any]) -> bool:
    if not actor:
        return False
    if actor.get("is_admin"):
        return True
    return "transportation_dispatch_gate.override" in set(actor.get("_governance_permissions") or [])


def _can_preview_dispatch_gate(actor: Dict[str, Any]) -> bool:
    if not actor:
        return False
    if actor.get("is_admin"):
        return True
    return "transportation_dispatch_gate.preview" in set(actor.get("_governance_permissions") or [])


# ===========================================================================
# Router
# ===========================================================================
def register_track_16_09_routes(app, db, *, require_dispatch_or_admin_dep,
                                  require_admin_dep) -> APIRouter:
    router = APIRouter(prefix="/api", tags=["transportation-dispatch-gate"])

    async def _enrich_actor(actor: Dict[str, Any]) -> Dict[str, Any]:
        raw = dict(actor or {})
        role = str(raw.get("role") or raw.get("_actor") or "").strip().lower() or "dispatch"
        raw.setdefault("id", raw.get("user_id") or raw.get("email") or role)
        raw.setdefault("email", f"{role}@dispatch-gate.local")
        raw["role"] = role
        raw["_actor"] = role
        context = await build_governance_actor_context(db, raw)
        raw["_governance_permissions"] = sorted(governance_effective_permissions(context))
        return raw

    # Inline dispatch-or-admin resolver — works around the server.py
    # wrapper that drops the FastAPI Request injection when it
    # delegates to the inner closure. Validates an X-Admin-Token first
    # (admin always wins), then falls back to an X-Dispatch-Token.
    async def _resolve_actor(
        request: Request,
        x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
        x_dispatch_token: Optional[str] = Header(default=None, alias="X-Dispatch-Token"),
    ) -> Dict[str, Any]:
        from server import (  # noqa: PLC0415
            _is_valid_directory_admin_token_async,
        )
        if x_admin_token and await _is_valid_directory_admin_token_async(x_admin_token):
            return await _enrich_actor({"role": "admin", "is_admin": True, "email": "admin"})
        if x_dispatch_token:
            try:
                from dispatch_users import (  # noqa: PLC0415
                    is_valid_dispatch_user_token_async,
                )
                u = await is_valid_dispatch_user_token_async(db, x_dispatch_token)
                if u:
                    return await _enrich_actor({"role": "dispatch", "is_admin": False, **u})
            except Exception:  # noqa: BLE001
                pass
        raise HTTPException(401, "Dispatch or Admin auth required")

    # -----------------------------------------------------------------------
    # PRECHECK — anyone with dispatch or admin can preview
    # -----------------------------------------------------------------------
    @router.post("/dispatch/transportation/check")
    async def gate_check(body: GateCheckBody,
                          actor: Any = Depends(_resolve_actor)):
        if not _can_preview_dispatch_gate(actor):
            raise HTTPException(403, "Not permitted to preview dispatch gate")
        result = await evaluate_dispatch_gate(
            db, driver_id=body.driver_id, truck_id=body.truck_id,
            carrier_id=body.carrier_id, override_id=body.override_id)
        return result

    # -----------------------------------------------------------------------
    # OVERRIDE — authorized only
    # -----------------------------------------------------------------------
    @router.post("/dispatch/transportation/override")
    async def create_override(body: OverrideCreateBody, request: Request,
                                actor: Any = Depends(_resolve_actor)):
        if not _is_override_authorized(actor):
            raise HTTPException(
                403, "Contact Admin, Operations, or Transportation Manager. "
                     "Dispatch-only users cannot approve overrides.")
        if not body.acknowledgement:
            raise HTTPException(
                422, "Acknowledgement required. Override does not mark the "
                     "compliance requirement complete.")
        # Evaluate first — we only persist overrides for genuinely blocked
        # entities.
        gate = await evaluate_dispatch_gate(
            db, driver_id=body.driver_id, truck_id=body.truck_id,
            carrier_id=body.carrier_id)
        if not gate["blocked"]:
            raise HTTPException(
                409, "Nothing to override — entity is already eligible.")
        now = datetime.now(timezone.utc)
        oid = uuid.uuid4().hex
        doc = {
            "id": oid, "tenant": TENANT,
            "driver_id": body.driver_id, "truck_id": body.truck_id,
            "carrier_id": body.carrier_id,
            "reason_code": body.reason_code,
            "explanation": body.explanation,
            "blocking_reason_codes": gate["reason_codes"],
            "blocking_reason_labels": gate["reason_labels"],
            "duration_hours": body.duration_hours,
            "approved_by_email": actor.get("email") or "admin",
            "approved_by_role": actor.get("role") or "admin",
            "approved_at": now.isoformat(),
            "expires_at": (now + timedelta(hours=body.duration_hours)).isoformat(),
            "status": "approved",
            "ip_address": (request.client.host if request.client else None),
            "user_agent": request.headers.get("user-agent", "")[:240],
            "consumed_for_assignment_id": None,
            "revoked_at": None, "revoked_by_email": None,
            "audit_version": 1,
        }
        await db.transport_dispatch_overrides.insert_one(doc.copy())
        # Audit via existing primitive (no duplicate audit system).
        try:
            from server import append_audit  # noqa: PLC0415
            await append_audit(
                db, kind="transport_dispatch_override_approve",
                entity_type="dispatch_override", entity_id=oid,
                actor={"email": doc["approved_by_email"], "role": doc["approved_by_role"]},
                old=None, new={
                    "driver_id": body.driver_id, "truck_id": body.truck_id,
                    "reason_code": body.reason_code,
                    "expires_at": doc["expires_at"],
                }, request=request,
            )
        except Exception:
            pass
        doc.pop("_id", None)
        return doc

    @router.get("/admin/transportation/dispatch-overrides")
    async def list_overrides(
        active_only: bool = Query(False),
        _: Any = Depends(require_admin_dep),
    ):
        q: Dict[str, Any] = {"tenant": TENANT}
        if active_only:
            q["status"] = "approved"
            q["expires_at"] = {"$gt": _now()}
        cur = db.transport_dispatch_overrides.find(q).sort("approved_at", -1).limit(500)
        items = []
        for d in await cur.to_list(500):
            d.pop("_id", None)
            items.append(d)
        return {"count": len(items), "items": items,
                "total": await db.transport_dispatch_overrides.count_documents(q)}

    @router.post("/admin/transportation/dispatch-overrides/{oid}/revoke")
    async def revoke_override(oid: str, request: Request,
                                _: Any = Depends(require_admin_dep)):
        row = await db.transport_dispatch_overrides.find_one(
            {"id": oid, "tenant": TENANT})
        if not row:
            raise HTTPException(404, "Override not found")
        if row.get("status") == "revoked":
            return {"ok": True, "already": "revoked"}
        await db.transport_dispatch_overrides.update_one(
            {"_id": row["_id"]},
            {"$set": {"status": "revoked", "revoked_at": _now()}})
        try:
            from server import append_audit  # noqa: PLC0415
            await append_audit(
                db, kind="transport_dispatch_override_revoke",
                entity_type="dispatch_override", entity_id=oid,
                actor={"email": "admin"}, old=None,
                new={"revoked_at": _now()}, request=request,
            )
        except Exception:
            pass
        return {"ok": True, "id": oid, "status": "revoked"}

    # -----------------------------------------------------------------------
    # EMAIL ROUTES CONTROL PANEL
    # -----------------------------------------------------------------------
    @router.get("/admin/transportation/email-routes")
    async def list_email_routes(_: Any = Depends(require_admin_dep)):
        # Read pilot status + audit summary for every TRANSPORT_* key.
        items = []
        for _kind, route_key, label in ALL_TRANSPORT_KINDS:
            row = await db.email_routes.find_one(
                {"tenant_key": TENANT, "route_key": route_key}) or {}
            to_count = len(row.get("to") or [])
            cc_count = len(row.get("cc") or [])
            bcc_count = len(row.get("bcc") or [])
            enabled = bool(row.get("enabled"))
            pilot = route_key in PILOT_ROUTE_KEYS
            # Most recent audit row for this route.
            last_audit = await db.email_routing_audit_v2.find_one(
                {"route_key": route_key, "tenant_key": TENANT},
                sort=[("ts", -1)])
            last_ts = (last_audit or {}).get("ts")
            last_dry_run = (last_audit or {}).get("dry_run", True)
            last_error = (last_audit or {}).get("error")
            status_str = "needs_configuration"
            if enabled and to_count + cc_count + bcc_count > 0:
                status_str = "active_send"
            elif pilot and to_count + cc_count + bcc_count == 0:
                status_str = "needs_configuration"
            elif not enabled:
                status_str = "audit_only"
            items.append({
                "route_key": route_key, "label": label,
                "kind": _kind, "is_pilot": pilot,
                "enabled": enabled, "status": status_str,
                "to_count": to_count, "cc_count": cc_count, "bcc_count": bcc_count,
                "last_sent_at": None if last_dry_run else last_ts,
                "last_audit_at": last_ts,
                "last_audit_dry_run": last_dry_run,
                "last_error": last_error,
            })
        return {"items": items, "pilot_route_keys": sorted(PILOT_ROUTE_KEYS)}

    @router.patch("/admin/transportation/email-routes/{route_key}")
    async def patch_email_route(route_key: str, body: EmailRouteToggleBody,
                                  request: Request,
                                  _: Any = Depends(require_admin_dep)):
        # Track 16.09 hard rule: only the 4 pilot routes may be toggled
        # via this endpoint. Activation of any other route is a future
        # track decision.
        if route_key not in PILOT_ROUTE_KEYS:
            raise HTTPException(
                403, f"Route {route_key} is not part of the Track 16.09 pilot. "
                     "Activation requires a future track sign-off.")
        existing = await db.email_routes.find_one(
            {"tenant_key": TENANT, "route_key": route_key})
        if not existing:
            raise HTTPException(404, f"Route {route_key} not found")
        await db.email_routes.update_one(
            {"_id": existing["_id"]},
            {"$set": {"enabled": bool(body.enabled), "updated_at": _now()}})
        try:
            from server import append_audit  # noqa: PLC0415
            await append_audit(
                db, kind="transport_email_route_toggle",
                entity_type="email_route", entity_id=route_key,
                actor={"email": "admin"},
                old={"enabled": existing.get("enabled")},
                new={"enabled": bool(body.enabled)}, request=request,
            )
        except Exception:
            pass
        return {"ok": True, "route_key": route_key, "enabled": bool(body.enabled)}

    app.include_router(router)
    return router
