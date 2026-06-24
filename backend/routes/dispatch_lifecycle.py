"""
routes/dispatch_lifecycle.py · iter392 · Phase 11.1 · DLS Backend Foundation.

Backend foundation for the Dispatch Lifecycle System.

Scope (iter392):
  • 3 Mongo collections (tenant-ready from day 1):
      - dispatch_assignments  (operational current truth)
      - dispatch_state_events (append-only analytics/audit truth)
      - haul_cycles           (derived cycle summary truth)
  • State-machine wiring (forgiving mode — see dispatch_lifecycle module).
  • REST API for create / read / transition / cancel / reassign.
  • RBAC: writes = dispatch+admin, reads = any portal token.

Out of scope (deferred):
  • Driver magic-link session (iter393).
  • Frontend (iter393 / iter394).
  • Governance detectors, CSV exports, notifications fan-out (iter395).
  • Glossary / coaching / ES translations (iter396).

Doctrine: lifecycle truth first. Operations never get trapped by rigid
validation. Every transition is recorded — non-standard ones are tagged
for future governance review.
"""
from __future__ import annotations

import asyncio
import logging
import os
import uuid
from datetime import datetime, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Header, Query, Request
from pydantic import BaseModel, Field

import dispatch_lifecycle as DLS

logger = logging.getLogger("dispatch_lifecycle_routes")

DEFAULT_TENANT_ID = "masci"
_BOARD_DEFAULT_LIMIT = 200
_BOARD_MAX_LIMIT = 500
_HISTORY_DEFAULT_LIMIT = 500
_HISTORY_MAX_LIMIT = 2000


# ════════════════════════════════════════════════════════════════════
# Helpers
# ════════════════════════════════════════════════════════════════════
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _new_id() -> str:
    return str(uuid.uuid4())


def _resolve_tenant(x_tenant_id: Optional[str]) -> str:
    """Tenant resolution. iter392 is single-tenant — but every record
    carries ``tenant_id`` so a future multi-tenant phase can filter
    without schema migration. Operators can pass ``X-Tenant-Id`` to
    override the default."""
    if x_tenant_id and isinstance(x_tenant_id, str) and x_tenant_id.strip():
        return x_tenant_id.strip()
    return DEFAULT_TENANT_ID


def _actor_label(actor: Dict[str, Any]) -> str:
    """Best-effort human label for state_history.by_name."""
    if not isinstance(actor, dict):
        return "system"
    return (
        actor.get("name")
        or actor.get("email")
        or actor.get("_actor")
        or "actor"
    )


def _actor_role(actor: Dict[str, Any]) -> str:
    if not isinstance(actor, dict):
        return "system"
    return actor.get("_actor") or "actor"


# ════════════════════════════════════════════════════════════════════
# Pydantic models
# ════════════════════════════════════════════════════════════════════
class AssignmentCreate(BaseModel):
    truck_id: str = Field(..., min_length=1, max_length=80)
    driver_id: Optional[str] = None
    driver_name: Optional[str] = ""
    project_number: Optional[str] = ""
    project_name: Optional[str] = ""
    material: Optional[str] = ""
    source_location: Optional[str] = ""
    destination: Optional[str] = ""
    loader_operator_name: Optional[str] = ""
    note: Optional[str] = ""
    # iter408 · Phase 14.2 · Haul Type continuity
    haul_type: Optional[str] = "Material"
    trailer_id: Optional[str] = ""
    trailer_label: Optional[str] = ""
    carrier: Optional[str] = ""
    equipment_id: Optional[str] = ""
    equipment_label: Optional[str] = ""
    pickup_location: Optional[str] = ""
    dropoff_location: Optional[str] = ""
    # iter410 · Phase 15.1 · Tanker / Liquid Asphalt continuity
    liquid_product: Optional[str] = ""


class TransitionRequest(BaseModel):
    to_state: str = Field(..., min_length=1, max_length=64)
    note: Optional[str] = ""
    correction_reason: Optional[str] = ""
    wait_reason: Optional[str] = ""          # captured when to_state == WAITING
    geo: Optional[Dict[str, Any]] = None     # optional {lat,lng,accuracy}


class CancelRequest(BaseModel):
    reason: str = Field(..., min_length=1, max_length=240)


class ReassignRequest(BaseModel):
    new_driver_id: Optional[str] = None
    new_driver_name: Optional[str] = ""
    new_truck_id: Optional[str] = None
    reason: Optional[str] = ""


# ─── Phase D-1.1 · Driver acknowledgement ──────────────────────────
class AcknowledgementRequest(BaseModel):
    """D-1.1 · Explicit assignment acknowledgement.

    method:   "tap" | "auto-transition" | "dispatcher-on-behalf"
    device:   free-text user-agent / device label (best-effort)
    note:     optional driver note at ack time
    """
    method: Optional[str] = "tap"
    device: Optional[str] = ""
    note: Optional[str] = ""


# ─── Phase D-1.5 · In-flight revision ──────────────────────────────
class RevisionRequest(BaseModel):
    """D-1.5 · Dispatcher revises mutable fields on an active assignment.

    Only these fields may be revised. Truck/driver changes still go
    through /reassign (the audit + history shape is different).
    """
    source_location: Optional[str] = None
    destination: Optional[str] = None
    dropoff_location: Optional[str] = None
    material: Optional[str] = None
    liquid_product: Optional[str] = None
    load_count: Optional[int] = None          # additive — new field
    scheduled_at: Optional[str] = None        # ISO timestamp · additive
    note: Optional[str] = None                # dispatcher note
    reason: str = Field(..., min_length=1, max_length=240)


# Fields revision is allowed to mutate (used by route + audit).
REVISABLE_FIELDS = (
    "source_location",
    "destination",
    "dropoff_location",
    "material",
    "liquid_product",
    "load_count",
    "scheduled_at",
    "note",
)


# ════════════════════════════════════════════════════════════════════
# Index setup
# ════════════════════════════════════════════════════════════════════
async def ensure_dispatch_lifecycle_indexes(db) -> None:
    """Create the indexes that power the operational board, history
    queries, and future tenant filtering. Safe to call multiple times
    (Mongo dedupes by index spec)."""
    try:
        await asyncio.gather(
            # dispatch_assignments — operational current truth
            db.dispatch_assignments.create_index(
                [("tenant_id", 1), ("current_state", 1), ("assigned_at", -1)],
                name="da_tenant_state_assigned",
            ),
            db.dispatch_assignments.create_index(
                [("tenant_id", 1), ("truck_id", 1), ("current_state", 1)],
                name="da_tenant_truck_state",
            ),
            db.dispatch_assignments.create_index(
                [("tenant_id", 1), ("driver_id", 1), ("assigned_at", -1)],
                name="da_tenant_driver_assigned",
            ),
            db.dispatch_assignments.create_index(
                [("tenant_id", 1), ("project_number", 1), ("assigned_at", -1)],
                name="da_tenant_project_assigned",
            ),
            db.dispatch_assignments.create_index("id", unique=True, name="da_id_unique"),
            # D-1.4 · Reminder scan index — finds un-acked active
            # assignments efficiently for the reminder scheduler.
            db.dispatch_assignments.create_index(
                [("tenant_id", 1), ("current_state", 1), ("acked_at", 1), ("assigned_at", 1)],
                name="da_unacked_scan",
            ),

            # dispatch_state_events — append-only audit/analytics truth
            db.dispatch_state_events.create_index(
                [("tenant_id", 1), ("assignment_id", 1), ("at", 1)],
                name="dse_tenant_assignment_at",
            ),
            db.dispatch_state_events.create_index(
                [("tenant_id", 1), ("at", -1)],
                name="dse_tenant_at_desc",
            ),
            db.dispatch_state_events.create_index(
                [("tenant_id", 1), ("standard", 1), ("at", -1)],
                name="dse_tenant_standard_at",
            ),
            db.dispatch_state_events.create_index("id", unique=True, name="dse_id_unique"),

            # haul_cycles — derived cycle summary truth (one row per
            # completed cycle)
            db.haul_cycles.create_index(
                [("tenant_id", 1), ("completed_at", -1)],
                name="hc_tenant_completed_desc",
            ),
            db.haul_cycles.create_index(
                [("tenant_id", 1), ("truck_id", 1), ("completed_at", -1)],
                name="hc_tenant_truck_completed",
            ),
            db.haul_cycles.create_index(
                [("tenant_id", 1), ("project_number", 1), ("completed_at", -1)],
                name="hc_tenant_project_completed",
            ),
            db.haul_cycles.create_index(
                "assignment_id", unique=True, name="hc_assignment_unique",
            ),
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[dispatch-lifecycle-index] {e}")


# ════════════════════════════════════════════════════════════════════
# Core transition engine
# ════════════════════════════════════════════════════════════════════
async def _record_transition(
    db,
    *,
    assignment: Dict[str, Any],
    to_state: str,
    actor: Dict[str, Any],
    note: str = "",
    correction_reason: str = "",
    wait_reason: str = "",
    geo: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """The single transition writer. Updates the assignment, appends to
    state_history[], mirrors a row into dispatch_state_events, and if
    the destination is COMPLETE writes a derived haul_cycles row.

    Returns the updated assignment dict (without _id)."""
    tenant_id = assignment.get("tenant_id") or DEFAULT_TENANT_ID
    from_state = assignment.get("current_state")
    classification = DLS.classify_transition(from_state, to_state)
    standard = bool(classification["standard"])
    warning_tag = classification["warning_tag"]
    warning_tags = list(classification["warning_tags"])

    at_iso = _now_iso()
    by_name = _actor_label(actor)
    by_role = _actor_role(actor)

    history_entry = {
        "from_state": from_state,
        "to_state": to_state,
        "at": at_iso,
        "by_name": by_name,
        "by_role": by_role,
        "standard": standard,
        "warning_tag": warning_tag,
        "warning_tags": warning_tags,
        "note": note or "",
        "correction_reason": correction_reason or "",
        "wait_reason": wait_reason or "",
        "geo": geo or None,
    }

    update_fields: Dict[str, Any] = {
        "current_state": to_state,
        "updated_at": at_iso,
        "last_transition_at": at_iso,
    }
    if to_state == DLS.WAITING:
        update_fields["current_wait_reason"] = wait_reason or ""
    else:
        # Clear stale wait reason whenever leaving WAITING.
        update_fields["current_wait_reason"] = ""
    if to_state == DLS.COMPLETE:
        update_fields["completed_at"] = at_iso
    if to_state == DLS.OFF_SHIFT:
        update_fields["ended_at"] = at_iso

    await db.dispatch_assignments.update_one(
        {"id": assignment["id"]},
        {
            "$set": update_fields,
            "$push": {"state_history": history_entry},
        },
    )

    # Mirror into the append-only event stream (always — even for
    # the seed ASSIGNED entry written by create()).
    event_doc = {
        "id": _new_id(),
        "tenant_id": tenant_id,
        "assignment_id": assignment["id"],
        "truck_id": assignment.get("truck_id"),
        "driver_id": assignment.get("driver_id"),
        "driver_name": assignment.get("driver_name") or "",
        "project_number": assignment.get("project_number") or "",
        "from_state": from_state,
        "to_state": to_state,
        "standard": standard,
        "warning_tag": warning_tag,
        "warning_tags": warning_tags,
        "at": at_iso,
        "by_name": by_name,
        "by_role": by_role,
        "note": note or "",
        "correction_reason": correction_reason or "",
        "wait_reason": wait_reason or "",
        "geo": geo or None,
    }
    await db.dispatch_state_events.insert_one(event_doc)

    # Derive haul_cycles row on COMPLETE. Idempotent via unique
    # assignment_id index — replay-safe.
    if to_state == DLS.COMPLETE:
        await _materialize_haul_cycle(
            db, assignment_id=assignment["id"], tenant_id=tenant_id,
        )

    # Return the updated assignment (re-read so the caller gets a
    # consistent snapshot, including the newly appended history row).
    updated = await db.dispatch_assignments.find_one(
        {"id": assignment["id"]}, {"_id": 0},
    )
    return updated or {}


# ════════════════════════════════════════════════════════════════════
# Phase D-1 · Acknowledgement, Revision, and Notification helpers
# ════════════════════════════════════════════════════════════════════
def _auto_sms_enabled() -> bool:
    """D-2.5 · Env-driven gate for auto-SMS on assignment create.

    Returns True only when ``DISPATCH_AUTO_SMS_ON_ASSIGN`` is truthy AND
    the underlying SMS provider is configured (sms_enabled). Operator
    keeps both knobs to avoid spurious sends in preview / pre-prod.
    """
    raw = (os.environ.get("DISPATCH_AUTO_SMS_ON_ASSIGN") or "").strip().lower()
    if raw not in ("1", "true", "yes", "on"):
        return False
    # Late import to avoid a hard dependency at module load — the
    # services package is optional in test environments.
    try:
        from services.sms_provider import sms_enabled  # noqa: PLC0415
        return sms_enabled()
    except Exception:
        return False


def _twilio_creds_configured() -> bool:
    """D-2.7 · For webhook signature enforcement. Returns True when
    Twilio SID + token + from-number are all present. We use this so
    the webhook only enforces signature checks when the operator has
    actually wired credentials — otherwise the route is callable for
    smoke tests in preview.
    """
    return all(
        (os.environ.get(k) or "").strip()
        for k in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_FROM_NUMBER")
    )


async def _issue_link_and_sms(
    db,
    *,
    assignment: Dict[str, Any],
    triggered_by: str,
    issued_by_name: str,
    issued_by_role: str,
) -> Dict[str, Any]:
    """D-2 · Compose the SMS pipeline for one assignment.

    1. Look up driver employee record for phone number.
    2. Issue a fresh magic link tied to (driver_id, assignment_id).
    3. Build the SMS body and dispatch via the provider adapter.
    4. Return ``{magic_link_url, sms_result}`` for the caller to feed
       into ``_fire_assignment_notification(... sms_result=...)``.

    Never raises — returns ``sms_result`` with status='skipped'/'failed'
    on any error. Caller decides whether to surface fallback messaging.
    """
    # Lazy imports keep the lifecycle module portable in test runs.
    from services.sms_provider import (  # noqa: PLC0415
        send_sms,
        build_magic_link_body,
        sms_enabled,
        normalize_phone,
        mask_phone,
    )
    import driver_sessions as DS  # noqa: PLC0415

    out: Dict[str, Any] = {"magic_link_url": None, "sms_result": None}
    tenant_id = assignment.get("tenant_id") or DEFAULT_TENANT_ID
    driver_id = (assignment.get("driver_id") or "").strip()

    # 1. Look up driver phone (best effort)
    phone: Optional[str] = None
    if driver_id:
        try:
            emp = await db.employees.find_one(
                {"id": driver_id},
                {"_id": 0, "phone": 1, "mobile_phone": 1, "personal_phone": 1, "full_name": 1},
            )
            if emp:
                phone = (
                    (emp.get("phone") or "").strip()
                    or (emp.get("mobile_phone") or "").strip()
                    or (emp.get("personal_phone") or "").strip()
                ) or None
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[issue-link-and-sms] employee lookup failed: {e}")

    # If SMS provider not available, skip the link issuance to avoid
    # minting unused tokens — return early with a skipped marker.
    if not sms_enabled():
        out["sms_result"] = {
            "ok": False,
            "status": "skipped",
            "provider": None,
            "provider_message_id": None,
            "destination_phone_masked": mask_phone(phone or ""),
            "triggered_by": triggered_by,
            "error_summary": "SMS disabled or credentials missing",
        }
        return out

    # Normalize before we even mint the link — invalid phone means
    # "fall back to copy-link" and we save the magic-token budget.
    norm_phone = normalize_phone(phone)
    if not norm_phone:
        out["sms_result"] = {
            "ok": False,
            "status": "skipped",
            "provider": (os.environ.get("SMS_PROVIDER") or "twilio"),
            "provider_message_id": None,
            "destination_phone_masked": mask_phone(phone or ""),
            "triggered_by": triggered_by,
            "error_summary": "Phone missing or not E.164-normalizable",
        }
        return out

    # 2. Issue magic link via existing iter393 helper.
    magic_link_url = None
    try:
        result = await DS.issue_magic_link(
            db,
            tenant_id=tenant_id,
            driver_id=driver_id,
            driver_name=assignment.get("driver_name") or "",
            truck_id=assignment.get("truck_id") or None,
            assignment_id=assignment.get("id"),
            issued_by_name=issued_by_name or "Dispatch",
            issued_by_role=issued_by_role or "dispatch",
        )
        # Compose the public driver landing URL. Backend doesn't know
        # the frontend host directly — operator config injects it via
        # PUBLIC_FRONTEND_URL. Falling back to a relative path is OK:
        # the link still works behind any proxy that serves both.
        host = (os.environ.get("PUBLIC_FRONTEND_URL") or "").rstrip("/")
        token = result["token"]
        magic_link_url = (f"{host}/d/{token}") if host else f"/d/{token}"
        out["magic_link_url"] = magic_link_url
    except DS.DriverIneligibleError as e:
        out["sms_result"] = {
            "ok": False,
            "status": "failed",
            "provider": None,
            "provider_message_id": None,
            "destination_phone_masked": mask_phone(norm_phone),
            "triggered_by": triggered_by,
            "error_summary": f"Driver ineligible: {e.code}",
        }
        return out
    except Exception as e:  # noqa: BLE001
        out["sms_result"] = {
            "ok": False,
            "status": "failed",
            "provider": None,
            "provider_message_id": None,
            "destination_phone_masked": mask_phone(norm_phone),
            "triggered_by": triggered_by,
            "error_summary": f"Magic link issuance failed: {type(e).__name__}",
        }
        return out

    # 3. Dispatch SMS.
    body = build_magic_link_body(
        assignment=assignment,
        magic_link_url=magic_link_url,
    )
    # D-2.7 · forward Twilio status callbacks back to ourselves so the
    # board sees queued → sent → delivered transitions land in
    # delivery_log[] without a separate sync pass.
    status_callback_url: Optional[str] = None
    backend_host = (os.environ.get("PUBLIC_BACKEND_URL") or "").rstrip("/")
    if backend_host and assignment.get("id"):
        status_callback_url = (
            f"{backend_host}/api/dispatch/sms/twilio-status-callback"
            f"?assignment_id={assignment['id']}"
        )
    sms_result = await send_sms(
        to_phone=norm_phone,
        body=body,
        triggered_by=triggered_by,
        status_callback_url=status_callback_url,
    )
    out["sms_result"] = sms_result
    return out


async def _record_acknowledgement(
    db,
    *,
    assignment: Dict[str, Any],
    actor: Dict[str, Any],
    method: str,
    device: str,
    note: str,
    target_revision: Optional[int] = None,
) -> Dict[str, Any]:
    """D-1.1 · Stamp ACK on the assignment and emit one audit event.

    If ``target_revision`` is provided, the ack is for that revision_seq
    (D-1.5 re-ack flow). Otherwise it's the initial assignment ack.

    Idempotent — calling twice with the same target_revision just
    refreshes acked_at (and adds another audit event so dispatch can
    see double-taps if they happen).
    """
    tenant_id = assignment.get("tenant_id") or DEFAULT_TENANT_ID
    at_iso = _now_iso()
    by_name = _actor_label(actor)
    by_role = _actor_role(actor)
    target_rev = (
        target_revision
        if target_revision is not None
        else int(assignment.get("revision_seq") or 0)
    )

    set_fields: Dict[str, Any] = {
        "acked_at": at_iso,
        "acked_by": by_name,
        "ack_method": method or "tap",
        "ack_device": (device or "")[:240],
        "ack_revision_seq": target_rev,
        "updated_at": at_iso,
    }
    # Clear the pending-revision banner once driver acks the latest rev.
    if target_rev >= int(assignment.get("revision_seq") or 0):
        set_fields["revision_pending"] = False

    history_entry = {
        "from_state": assignment.get("current_state"),
        "to_state": assignment.get("current_state"),
        "at": at_iso,
        "by_name": by_name,
        "by_role": by_role,
        "standard": True,
        "warning_tag": "ACKNOWLEDGED",
        "warning_tags": ["ACKNOWLEDGED"],
        "note": note or "",
        "correction_reason": "",
        "wait_reason": "",
        "geo": None,
        "ack_method": method or "tap",
        "ack_device": (device or "")[:240],
        "ack_revision_seq": target_rev,
    }

    await db.dispatch_assignments.update_one(
        {"id": assignment["id"]},
        {"$set": set_fields, "$push": {"state_history": history_entry}},
    )
    await db.dispatch_state_events.insert_one({
        "id": _new_id(),
        "tenant_id": tenant_id,
        "assignment_id": assignment["id"],
        "truck_id": assignment.get("truck_id"),
        "driver_id": assignment.get("driver_id"),
        "driver_name": assignment.get("driver_name") or "",
        "project_number": assignment.get("project_number") or "",
        "from_state": assignment.get("current_state"),
        "to_state": assignment.get("current_state"),
        "standard": True,
        "warning_tag": "ACKNOWLEDGED",
        "warning_tags": ["ACKNOWLEDGED"],
        "at": at_iso,
        "by_name": by_name,
        "by_role": by_role,
        "note": note or "",
        "correction_reason": "",
        "wait_reason": "",
        "geo": None,
        "ack_method": method or "tap",
        "ack_device": (device or "")[:240],
        "ack_revision_seq": target_rev,
    })
    return await db.dispatch_assignments.find_one(
        {"id": assignment["id"]}, {"_id": 0},
    ) or {}


async def _record_revision(
    db,
    *,
    assignment: Dict[str, Any],
    actor: Dict[str, Any],
    changes: Dict[str, Any],
    reason: str,
) -> Dict[str, Any]:
    """D-1.5 · Persist a revision and emit one audit event.

    - Stamps the new field values on the assignment.
    - Appends a row to ``revision_history[]`` capturing before/after.
    - Increments ``revision_seq`` (starts at 0; first revise → 1).
    - Resets ``acked_at = None`` and sets ``revision_pending = True``
      so the driver must re-acknowledge.
    - Writes one ``dispatch_state_events`` row tagged REVISED.
    """
    tenant_id = assignment.get("tenant_id") or DEFAULT_TENANT_ID
    at_iso = _now_iso()
    by_name = _actor_label(actor)
    by_role = _actor_role(actor)
    new_seq = int(assignment.get("revision_seq") or 0) + 1

    before: Dict[str, Any] = {}
    after: Dict[str, Any] = {}
    set_fields: Dict[str, Any] = {
        "revision_seq": new_seq,
        "revision_pending": True,
        "acked_at": None,
        "acked_by": None,
        "ack_method": None,
        "ack_device": None,
        "ack_revision_seq": None,
        "last_revised_at": at_iso,
        "last_revised_by_name": by_name,
        "last_revised_by_role": by_role,
        "updated_at": at_iso,
    }
    for fld in REVISABLE_FIELDS:
        if fld in changes and changes[fld] is not None:
            before[fld] = assignment.get(fld)
            new_val = changes[fld]
            if isinstance(new_val, str):
                new_val = new_val.strip()
            after[fld] = new_val
            set_fields[fld] = new_val

    revision_entry = {
        "revision_seq": new_seq,
        "at": at_iso,
        "by_name": by_name,
        "by_role": by_role,
        "reason": reason or "",
        "before": before,
        "after": after,
    }

    await db.dispatch_assignments.update_one(
        {"id": assignment["id"]},
        {
            "$set": set_fields,
            "$push": {
                "revision_history": revision_entry,
                "state_history": {
                    "from_state": assignment.get("current_state"),
                    "to_state": assignment.get("current_state"),
                    "at": at_iso,
                    "by_name": by_name,
                    "by_role": by_role,
                    "standard": True,
                    "warning_tag": "REVISED",
                    "warning_tags": ["REVISED"],
                    "note": reason or "",
                    "correction_reason": "",
                    "wait_reason": "",
                    "geo": None,
                    "revision_seq": new_seq,
                    "revision_before": before,
                    "revision_after": after,
                },
            },
        },
    )
    await db.dispatch_state_events.insert_one({
        "id": _new_id(),
        "tenant_id": tenant_id,
        "assignment_id": assignment["id"],
        "truck_id": assignment.get("truck_id"),
        "driver_id": assignment.get("driver_id"),
        "driver_name": assignment.get("driver_name") or "",
        "project_number": assignment.get("project_number") or "",
        "from_state": assignment.get("current_state"),
        "to_state": assignment.get("current_state"),
        "standard": True,
        "warning_tag": "REVISED",
        "warning_tags": ["REVISED"],
        "at": at_iso,
        "by_name": by_name,
        "by_role": by_role,
        "note": reason or "",
        "correction_reason": "",
        "wait_reason": "",
        "geo": None,
        "revision_seq": new_seq,
        "revision_before": before,
        "revision_after": after,
    })
    return await db.dispatch_assignments.find_one(
        {"id": assignment["id"]}, {"_id": 0},
    ) or {}


async def _fire_assignment_notification(
    db,
    *,
    assignment: Dict[str, Any],
    event: str,
    send_email_fn: Optional[Callable[..., Awaitable[bool]]] = None,
    magic_link_url: Optional[str] = None,
    sms_result: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """D-1.3 / D-2.6 · Best-effort notification fan-out for an assignment.

    Reuses existing rails:
      - bell: writes to ``db.tasks`` (the same collection the rest of
        the platform uses for the bell feed). assignee_role="dispatch"
        so dispatchers see it; we never spam the driver's bell because
        drivers don't have a portal account.
      - email: optional ``send_email_fn`` (server.py passes
        ``_safety_send_email`` — same Resend wrapper used everywhere).
      - sms (D-2): caller may pass a pre-computed ``sms_result`` from
        ``services.sms_provider.send_sms`` so the SMS attempt is part
        of the same delivery_log fan-out + audit event.

    Records the attempt + outcome in ``delivery_log[]`` on the
    assignment. Never raises — notification failure must not crash
    assignment creation/revision.
    """
    tenant_id = assignment.get("tenant_id") or DEFAULT_TENANT_ID
    at_iso = _now_iso()
    delivery_entries: List[Dict[str, Any]] = []

    # ─── 1. Bell task (dispatcher inbox) ───────────────────────────
    try:
        title = (
            f"Dispatch {event} · {assignment.get('truck_id') or '—'}"
            f" → {assignment.get('driver_name') or 'unassigned'}"
        )
        body_bits = []
        if assignment.get("project_number"):
            body_bits.append(f"#{assignment.get('project_number')}")
        if assignment.get("source_location"):
            body_bits.append(f"Plant: {assignment.get('source_location')}")
        if assignment.get("destination"):
            body_bits.append(f"Dest: {assignment.get('destination')}")
        if assignment.get("material"):
            body_bits.append(f"Material: {assignment.get('material')}")
        bell_task = {
            "id": _new_id(),
            "tenant_id": tenant_id,
            "kind": f"dispatch_{event}",
            "title": title[:200],
            "description": " · ".join(body_bits)[:400],
            "assignee_role": "dispatch",
            "assignee_id": None,
            "assignment_id": assignment.get("id"),
            "truck_id": assignment.get("truck_id"),
            "driver_id": assignment.get("driver_id"),
            "magic_link_url": magic_link_url,
            "status": "open",
            "created_at": at_iso,
            "updated_at": at_iso,
            "source": "dispatch_lifecycle_v1",
        }
        await db.tasks.insert_one(bell_task)
        delivery_entries.append({
            "channel": "bell",
            "target": "dispatch",
            "at": at_iso,
            "ok": True,
            "error": None,
        })
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[dispatch-notify] bell write failed: {e}")
        delivery_entries.append({
            "channel": "bell",
            "target": "dispatch",
            "at": at_iso,
            "ok": False,
            "error": f"{type(e).__name__}: {e}",
        })

    # ─── 2. Email (driver, if email exists on employees row) ───────
    driver_email: Optional[str] = None
    try:
        if send_email_fn and assignment.get("driver_id"):
            emp = await db.employees.find_one(
                {"id": assignment["driver_id"]},
                {"_id": 0, "email": 1, "full_name": 1},
            )
            if emp and emp.get("email"):
                driver_email = emp["email"]
    except Exception:
        driver_email = None

    if driver_email and send_email_fn:
        try:
            subject = f"MASCI Dispatch · {event.replace('_', ' ').title()}"
            html_lines = [
                f"<p>Hello {assignment.get('driver_name') or 'driver'},</p>",
                f"<p>You have a dispatch assignment ({event}):</p>",
                "<ul>",
            ]
            for k_label, k_field in (
                ("Project", "project_number"),
                ("Project name", "project_name"),
                ("Truck", "truck_id"),
                ("Plant / load site", "source_location"),
                ("Destination", "destination"),
                ("Material", "material"),
                ("Note", "note"),
            ):
                v = assignment.get(k_field)
                if v:
                    html_lines.append(f"<li><strong>{k_label}:</strong> {v}</li>")
            html_lines.append("</ul>")
            if magic_link_url:
                html_lines.append(
                    f'<p><a href="{magic_link_url}">Open assignment</a> · '
                    "single-use, expires in 15 minutes.</p>"
                )
            html_lines.append(
                "<p>This is an automated dispatch message. Reply to your "
                "dispatcher for changes.</p>"
            )
            sent = await send_email_fn(driver_email, subject, "".join(html_lines))
            delivery_entries.append({
                "channel": "email",
                "target": driver_email,
                "at": _now_iso(),
                "ok": bool(sent),
                "error": None if sent else "send_email_fn returned False (gated)",
            })
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[dispatch-notify] email failed: {e}")
            delivery_entries.append({
                "channel": "email",
                "target": driver_email,
                "at": _now_iso(),
                "ok": False,
                "error": f"{type(e).__name__}: {e}",
            })

    # ─── 3. Append delivery log on the assignment ──────────────────
    if sms_result:
        delivery_entries.append({
            "channel": "sms",
            "target": sms_result.get("destination_phone_masked") or "",
            "at": _now_iso(),
            "ok": bool(sms_result.get("ok")),
            "status": sms_result.get("status"),
            "provider": sms_result.get("provider"),
            "provider_message_id": sms_result.get("provider_message_id"),
            "triggered_by": sms_result.get("triggered_by") or "auto",
            "error": sms_result.get("error_summary"),
        })
    try:
        await db.dispatch_assignments.update_one(
            {"id": assignment["id"]},
            {"$push": {"delivery_log": {"$each": delivery_entries}}},
        )
    except Exception as e:  # noqa: BLE001
        logger.warning(f"[dispatch-notify] delivery_log append failed: {e}")

    # ─── 4. SMS audit event in dispatch_state_events ───────────────
    # The bell + email already touch the assignment doc; the state
    # event stream is the dispatcher-side audit trail.
    if sms_result:
        try:
            tenant_id = assignment.get("tenant_id") or DEFAULT_TENANT_ID
            at_iso = _now_iso()
            await db.dispatch_state_events.insert_one({
                "id": _new_id(),
                "tenant_id": tenant_id,
                "assignment_id": assignment.get("id"),
                "truck_id": assignment.get("truck_id"),
                "driver_id": assignment.get("driver_id"),
                "driver_name": assignment.get("driver_name") or "",
                "project_number": assignment.get("project_number") or "",
                "from_state": assignment.get("current_state"),
                "to_state": assignment.get("current_state"),
                "standard": True,
                "warning_tag": "SMS_ATTEMPTED",
                "warning_tags": ["SMS_ATTEMPTED"],
                "at": at_iso,
                "by_name": sms_result.get("triggered_by") or "auto",
                "by_role": "dispatch_sms",
                "note": "",
                "correction_reason": "",
                "wait_reason": "",
                "geo": None,
                "sms_status": sms_result.get("status"),
                "sms_provider": sms_result.get("provider"),
                "sms_provider_message_id": sms_result.get("provider_message_id"),
                "sms_destination_phone_masked": sms_result.get("destination_phone_masked"),
                "sms_error_summary": sms_result.get("error_summary"),
                "sms_triggered_by": sms_result.get("triggered_by") or "auto",
            })
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[dispatch-notify] sms audit insert failed: {e}")

    return {
        "ok": True,
        "event": event,
        "entries": delivery_entries,
    }


async def _materialize_haul_cycle(db, *, assignment_id: str, tenant_id: str) -> None:
    """Build the haul_cycles summary row for a completed assignment.

    Pulls timing facts straight off state_history. Idempotent.
    """
    assignment = await db.dispatch_assignments.find_one(
        {"id": assignment_id}, {"_id": 0},
    )
    if not assignment:
        return
    history: List[Dict[str, Any]] = list(assignment.get("state_history") or [])
    if not history:
        return

    started_at = assignment.get("assigned_at") or (history[0].get("at") if history else None)
    completed_at = assignment.get("completed_at") or history[-1].get("at")

    def _epoch(iso: Optional[str]) -> Optional[float]:
        if not iso:
            return None
        try:
            return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp()
        except Exception:
            return None

    started_epoch = _epoch(started_at)
    completed_epoch = _epoch(completed_at)
    total_seconds: Optional[int] = None
    if started_epoch is not None and completed_epoch is not None:
        total_seconds = max(0, int(completed_epoch - started_epoch))

    # Compute wait_seconds — time spent in WAITING blocks across the
    # cycle, derived from the timestamps in state_history.
    wait_seconds = 0
    for idx, entry in enumerate(history):
        if entry.get("to_state") != DLS.WAITING:
            continue
        wait_start = _epoch(entry.get("at"))
        if wait_start is None:
            continue
        # Find the next transition out of WAITING. If none, use
        # completed_epoch as the wait end.
        wait_end = completed_epoch
        for later in history[idx + 1:]:
            ep = _epoch(later.get("at"))
            if ep is not None:
                wait_end = ep
                break
        if wait_end is not None and wait_end >= wait_start:
            wait_seconds += int(wait_end - wait_start)

    cycle_doc = {
        "id": _new_id(),
        "tenant_id": tenant_id,
        "assignment_id": assignment_id,
        "truck_id": assignment.get("truck_id"),
        "driver_id": assignment.get("driver_id"),
        "driver_name": assignment.get("driver_name") or "",
        "project_number": assignment.get("project_number") or "",
        "project_name": assignment.get("project_name") or "",
        "material": assignment.get("material") or "",
        "source_location": assignment.get("source_location") or "",
        "destination": assignment.get("destination") or "",
        # iter409 · Phase 14.3 · cycle continuity for haul-type-aware
        # PM production awareness. Additive — historical cycles will
        # simply read these fields as empty strings.
        "haul_type": assignment.get("haul_type") or "Material",
        "equipment_label": assignment.get("equipment_label") or "",
        "pickup_location": assignment.get("pickup_location") or "",
        "dropoff_location": assignment.get("dropoff_location") or "",
        # iter410 · Phase 15.1 · Tanker continuity carried into cycle truth
        "liquid_product": assignment.get("liquid_product") or "",
        "started_at": started_at,
        "completed_at": completed_at,
        "total_seconds": total_seconds,
        "wait_seconds": wait_seconds,
        "operating_seconds": (
            max(0, (total_seconds or 0) - wait_seconds) if total_seconds is not None else None
        ),
        "transitions": len(history),
        "non_standard_transitions": sum(
            1 for h in history if not h.get("standard", True)
        ),
        "created_at": _now_iso(),
    }
    try:
        await db.haul_cycles.insert_one(cycle_doc)
    except Exception as e:  # noqa: BLE001
        # Duplicate (assignment_id unique) — log and move on. The
        # earlier-written row is the canonical summary.
        logger.info(f"[haul_cycle] dedupe assignment_id={assignment_id}: {e}")


# ════════════════════════════════════════════════════════════════════
# Router factory
# ════════════════════════════════════════════════════════════════════
def build_dispatch_lifecycle_router(
    db,
    require_dispatch_or_admin_dep: Callable[..., Awaitable[Dict[str, Any]]],
    require_any_portal_token_dep: Callable[..., Awaitable[Dict[str, Any]]],
    send_email_fn: Optional[Callable[..., Awaitable[bool]]] = None,
) -> APIRouter:
    """Build the DLS router.

    Args:
      db: motor database handle.
      require_dispatch_or_admin_dep: WRITE gate. Reused from server.py
        (same gate that protects /api/dispatch/* writes today).
      require_any_portal_token_dep: READ gate. Lets PMs / Safety / HR /
        Shop / FL / Admin see haul activity tied to their portal — no
        new auth surface introduced.
      send_email_fn: Optional async Resend wrapper for D-1.3 driver
        email notification. When None (e.g. in tests), bell-only
        notification is emitted and no email is attempted.
    """
    router = APIRouter(prefix="/api/dispatch", tags=["dispatch-lifecycle"])

    # ────────────────────────────────────────────────────────────────
    # CREATE
    # ────────────────────────────────────────────────────────────────
    @router.post("/assignments")
    async def create_assignment(
        body: AssignmentCreate,
        actor: Dict[str, Any] = Depends(require_dispatch_or_admin_dep),
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        at_iso = _now_iso()
        assignment_id = _new_id()
        by_name = _actor_label(actor)
        by_role = _actor_role(actor)

        seed_history_entry = {
            "from_state": None,
            "to_state": DLS.ASSIGNED,
            "at": at_iso,
            "by_name": by_name,
            "by_role": by_role,
            "standard": True,
            "warning_tag": None,
            "warning_tags": [],
            "note": body.note or "",
            "correction_reason": "",
            "wait_reason": "",
            "geo": None,
        }
        doc = {
            "id": assignment_id,
            "tenant_id": tenant_id,
            "truck_id": body.truck_id.strip(),
            "driver_id": (body.driver_id or "").strip() or None,
            "driver_name": (body.driver_name or "").strip(),
            "project_number": (body.project_number or "").strip(),
            "project_name": (body.project_name or "").strip(),
            "material": (body.material or "").strip(),
            "source_location": (body.source_location or "").strip(),
            "destination": (body.destination or "").strip(),
            "loader_operator_name": (body.loader_operator_name or "").strip(),
            # iter408 · Phase 14.2 · Haul Type continuity (additive,
            # backward-compatible — legacy assignments simply default
            # haul_type to "Material" via the model).
            "haul_type": (body.haul_type or "Material").strip() or "Material",
            "trailer_id": (body.trailer_id or "").strip(),
            "trailer_label": (body.trailer_label or "").strip(),
            "carrier": (body.carrier or "").strip(),
            "equipment_id": (body.equipment_id or "").strip(),
            "equipment_label": (body.equipment_label or "").strip(),
            "pickup_location": (body.pickup_location or "").strip(),
            "dropoff_location": (body.dropoff_location or "").strip(),
            # iter410 · Phase 15.1 · Tanker / Liquid Asphalt continuity
            "liquid_product": (body.liquid_product or "").strip(),
            "current_state": DLS.ASSIGNED,
            "current_wait_reason": "",
            "assigned_at": at_iso,
            "assigned_by_name": by_name,
            "assigned_by_role": by_role,
            "last_transition_at": at_iso,
            "completed_at": None,
            "ended_at": None,
            "cancelled_at": None,
            "cancel_reason": None,
            "state_history": [seed_history_entry],
            "wait_events": [],
            "motive_validation": None,
            # ─── Phase D-1 · ack + revision + delivery fields ──────
            "acked_at": None,
            "acked_by": None,
            "ack_method": None,
            "ack_device": None,
            "ack_revision_seq": None,
            "revision_seq": 0,
            "revision_pending": False,
            "revision_history": [],
            "last_revised_at": None,
            "last_revised_by_name": None,
            "last_revised_by_role": None,
            "load_count": None,
            "scheduled_at": None,
            "delivery_log": [],
            "reminder_sent_at": None,
            "reminder_count": 0,
            "created_at": at_iso,
            "updated_at": at_iso,
            "source": "dispatch_lifecycle_v1",
        }
        await db.dispatch_assignments.insert_one(doc)

        # TRACK 15.76 · Trust Spine — dispatch assignment lifecycle.
        # Dispatch is a non-email workflow; emits the operational
        # stages directly (record_created → routing_resolved →
        # dashboard_updated → audit_written → completed).
        try:
            from lib.trust_spine import (  # noqa: PLC0415
                emit_record_created, emit_workflow_stage,
                STAGE_ROUTING_RESOLVED, STAGE_DASHBOARD_UPDATED,
                STAGE_AUDIT_WRITTEN, STAGE_COMPLETED,
            )
            _spine_rec = {
                "id": assignment_id, "doc_id": assignment_id,
                "project_number": doc.get("project_number") or "",
            }
            _spine_mod = "routes/dispatch_lifecycle.py:create_assignment"
            await emit_record_created(
                db, workflow="dispatch-assignment", record=_spine_rec,
                module=_spine_mod,
            )
            await emit_workflow_stage(
                db, workflow="dispatch-assignment",
                stage=STAGE_ROUTING_RESOLVED, record=_spine_rec,
                module="driver+truck binding", status="ok",
            )
            await emit_workflow_stage(
                db, workflow="dispatch-assignment",
                stage=STAGE_DASHBOARD_UPDATED, record=_spine_rec,
                module="dispatch_assignments.insert_one", status="ok",
            )
            await emit_workflow_stage(
                db, workflow="dispatch-assignment",
                stage=STAGE_AUDIT_WRITTEN, record=_spine_rec,
                module="dispatch_state_events", status="ok",
            )
            await emit_workflow_stage(
                db, workflow="dispatch-assignment",
                stage=STAGE_COMPLETED, record=_spine_rec,
                module=_spine_mod, status="ok",
            )
        except Exception:  # noqa: BLE001
            pass

        # Mirror the seed ASSIGNED into the event stream.
        event_doc = {
            "id": _new_id(),
            "tenant_id": tenant_id,
            "assignment_id": assignment_id,
            "truck_id": doc["truck_id"],
            "driver_id": doc["driver_id"],
            "driver_name": doc["driver_name"],
            "project_number": doc["project_number"],
            "from_state": None,
            "to_state": DLS.ASSIGNED,
            "standard": True,
            "warning_tag": None,
            "warning_tags": [],
            "at": at_iso,
            "by_name": by_name,
            "by_role": by_role,
            "note": body.note or "",
            "correction_reason": "",
            "wait_reason": "",
            "geo": None,
        }
        await db.dispatch_state_events.insert_one(event_doc)

        # Re-read to drop _id (insert_one mutates the input dict).
        out = await db.dispatch_assignments.find_one({"id": assignment_id}, {"_id": 0})

        # ─── D-1.3 + D-2.5 · Auto-notify + optional auto-SMS ───────
        # Never crash create on notification failure.
        try:
            sms_result = None
            magic_link_url = None
            if _auto_sms_enabled() and out:
                # Build magic link + SMS body, ship it.
                sms_outcome = await _issue_link_and_sms(
                    db,
                    assignment=out,
                    triggered_by="auto",
                    issued_by_name=by_name,
                    issued_by_role=by_role,
                )
                sms_result = sms_outcome.get("sms_result")
                magic_link_url = sms_outcome.get("magic_link_url")
            await _fire_assignment_notification(
                db,
                assignment=out or doc,
                event="new_assignment",
                send_email_fn=send_email_fn,
                magic_link_url=magic_link_url,
                sms_result=sms_result,
            )
            # Re-read so the response carries delivery_log.
            out = await db.dispatch_assignments.find_one(
                {"id": assignment_id}, {"_id": 0},
            )
        except Exception as _notify_err:  # noqa: BLE001
            logger.warning(f"[dispatch-create-notify] {_notify_err}")

        return {"ok": True, "assignment": out}

    # ────────────────────────────────────────────────────────────────
    # LIST · BOARD · DETAIL (cross-portal read)
    # ────────────────────────────────────────────────────────────────
    @router.get("/assignments/board")
    async def get_board(
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
        limit: int = Query(_BOARD_DEFAULT_LIMIT, ge=1, le=_BOARD_MAX_LIMIT),
    ):
        """Live operational board — active assignments (anything not
        in a terminal state) sorted by assigned_at desc."""
        tenant_id = _resolve_tenant(x_tenant_id)
        query = {
            "tenant_id": tenant_id,
            "current_state": {"$nin": [DLS.COMPLETE, DLS.OFF_SHIFT]},
            "cancelled_at": None,
        }
        cursor = (
            db.dispatch_assignments
            .find(query, {"_id": 0})
            .sort("assigned_at", -1)
            .limit(limit)
        )
        rows = await cursor.to_list(length=limit)
        return {"ok": True, "tenant_id": tenant_id, "count": len(rows), "assignments": rows}

    @router.get("/assignments")
    async def list_assignments(
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
        truck_id: Optional[str] = None,
        driver_id: Optional[str] = None,
        project_number: Optional[str] = None,
        state: Optional[str] = None,
        include_completed: bool = False,
        limit: int = Query(100, ge=1, le=_BOARD_MAX_LIMIT),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        query: Dict[str, Any] = {"tenant_id": tenant_id}
        if truck_id:
            query["truck_id"] = truck_id
        if driver_id:
            query["driver_id"] = driver_id
        if project_number:
            query["project_number"] = project_number
        if state:
            query["current_state"] = state
        elif not include_completed:
            query["current_state"] = {"$nin": [DLS.COMPLETE, DLS.OFF_SHIFT]}
            query["cancelled_at"] = None
        cursor = (
            db.dispatch_assignments
            .find(query, {"_id": 0})
            .sort("assigned_at", -1)
            .limit(limit)
        )
        rows = await cursor.to_list(length=limit)
        return {"ok": True, "tenant_id": tenant_id, "count": len(rows), "assignments": rows}

    @router.get("/assignments/{assignment_id}")
    async def get_assignment(
        assignment_id: str,
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        doc = await db.dispatch_assignments.find_one(
            {"id": assignment_id, "tenant_id": tenant_id}, {"_id": 0},
        )
        if not doc:
            raise HTTPException(404, "Assignment not found")
        return {"ok": True, "assignment": doc}

    # ────────────────────────────────────────────────────────────────
    # TRANSITION (write — forgiving mode)
    # ────────────────────────────────────────────────────────────────
    @router.post("/assignments/{assignment_id}/transition")
    async def transition_assignment(
        assignment_id: str,
        body: TransitionRequest,
        actor: Dict[str, Any] = Depends(require_dispatch_or_admin_dep),
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        assignment = await db.dispatch_assignments.find_one(
            {"id": assignment_id, "tenant_id": tenant_id}, {"_id": 0},
        )
        if not assignment:
            raise HTTPException(404, "Assignment not found")
        if assignment.get("cancelled_at"):
            raise HTTPException(
                409,
                "Assignment is cancelled — create a new assignment instead of transitioning.",
            )
        to_state = body.to_state.strip()
        if not to_state:
            raise HTTPException(422, "to_state is required")
        # Forgiving mode: we accept any to_state. classify_transition
        # tags non-canonical and non-standard transitions.
        updated = await _record_transition(
            db,
            assignment=assignment,
            to_state=to_state,
            actor=actor,
            note=body.note or "",
            correction_reason=body.correction_reason or "",
            wait_reason=body.wait_reason or "",
            geo=body.geo,
        )
        latest = (updated.get("state_history") or [])[-1] if updated else None
        return {
            "ok": True,
            "assignment": updated,
            "transition": latest,
        }

    # ────────────────────────────────────────────────────────────────
    # CANCEL
    # ────────────────────────────────────────────────────────────────
    @router.post("/assignments/{assignment_id}/cancel")
    async def cancel_assignment(
        assignment_id: str,
        body: CancelRequest,
        actor: Dict[str, Any] = Depends(require_dispatch_or_admin_dep),
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        assignment = await db.dispatch_assignments.find_one(
            {"id": assignment_id, "tenant_id": tenant_id}, {"_id": 0},
        )
        if not assignment:
            raise HTTPException(404, "Assignment not found")
        if assignment.get("cancelled_at"):
            raise HTTPException(409, "Already cancelled")

        at_iso = _now_iso()
        by_name = _actor_label(actor)
        by_role = _actor_role(actor)
        history_entry = {
            "from_state": assignment.get("current_state"),
            "to_state": "CANCELLED",
            "at": at_iso,
            "by_name": by_name,
            "by_role": by_role,
            "standard": False,
            "warning_tag": "CANCELLED",
            "warning_tags": ["CANCELLED"],
            "note": body.reason,
            "correction_reason": "",
            "wait_reason": "",
            "geo": None,
        }
        await db.dispatch_assignments.update_one(
            {"id": assignment_id},
            {
                "$set": {
                    "cancelled_at": at_iso,
                    "cancel_reason": body.reason,
                    "updated_at": at_iso,
                    "last_transition_at": at_iso,
                },
                "$push": {"state_history": history_entry},
            },
        )
        await db.dispatch_state_events.insert_one({
            "id": _new_id(),
            "tenant_id": tenant_id,
            "assignment_id": assignment_id,
            "truck_id": assignment.get("truck_id"),
            "driver_id": assignment.get("driver_id"),
            "driver_name": assignment.get("driver_name") or "",
            "project_number": assignment.get("project_number") or "",
            "from_state": assignment.get("current_state"),
            "to_state": "CANCELLED",
            "standard": False,
            "warning_tag": "CANCELLED",
            "warning_tags": ["CANCELLED"],
            "at": at_iso,
            "by_name": by_name,
            "by_role": by_role,
            "note": body.reason,
            "correction_reason": "",
            "wait_reason": "",
            "geo": None,
        })
        out = await db.dispatch_assignments.find_one({"id": assignment_id}, {"_id": 0})
        return {"ok": True, "assignment": out}

    # ────────────────────────────────────────────────────────────────
    # REASSIGN
    # ────────────────────────────────────────────────────────────────
    @router.post("/assignments/{assignment_id}/reassign")
    async def reassign_assignment(
        assignment_id: str,
        body: ReassignRequest,
        actor: Dict[str, Any] = Depends(require_dispatch_or_admin_dep),
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        assignment = await db.dispatch_assignments.find_one(
            {"id": assignment_id, "tenant_id": tenant_id}, {"_id": 0},
        )
        if not assignment:
            raise HTTPException(404, "Assignment not found")
        if assignment.get("cancelled_at"):
            raise HTTPException(409, "Cannot reassign a cancelled assignment")
        if assignment.get("current_state") in DLS.TERMINAL_STATES:
            raise HTTPException(
                409,
                "Cannot reassign an assignment in a terminal state",
            )
        if not (body.new_driver_id or body.new_driver_name or body.new_truck_id):
            raise HTTPException(
                422,
                "Provide at least one of: new_driver_id, new_driver_name, new_truck_id",
            )

        at_iso = _now_iso()
        by_name = _actor_label(actor)
        by_role = _actor_role(actor)

        set_fields: Dict[str, Any] = {
            "updated_at": at_iso,
            "last_transition_at": at_iso,
        }
        if body.new_driver_id is not None:
            set_fields["driver_id"] = body.new_driver_id or None
        if body.new_driver_name:
            set_fields["driver_name"] = body.new_driver_name
        if body.new_truck_id:
            set_fields["truck_id"] = body.new_truck_id

        history_entry = {
            "from_state": assignment.get("current_state"),
            "to_state": assignment.get("current_state"),
            "at": at_iso,
            "by_name": by_name,
            "by_role": by_role,
            "standard": True,
            "warning_tag": "REASSIGNED",
            "warning_tags": ["REASSIGNED"],
            "note": body.reason or "",
            "correction_reason": "",
            "wait_reason": "",
            "geo": None,
            "reassign_to_driver_id": set_fields.get("driver_id"),
            "reassign_to_driver_name": set_fields.get("driver_name"),
            "reassign_to_truck_id": set_fields.get("truck_id"),
            "reassign_from_driver_id": assignment.get("driver_id"),
            "reassign_from_driver_name": assignment.get("driver_name"),
            "reassign_from_truck_id": assignment.get("truck_id"),
        }
        await db.dispatch_assignments.update_one(
            {"id": assignment_id},
            {"$set": set_fields, "$push": {"state_history": history_entry}},
        )
        await db.dispatch_state_events.insert_one({
            "id": _new_id(),
            "tenant_id": tenant_id,
            "assignment_id": assignment_id,
            "truck_id": set_fields.get("truck_id") or assignment.get("truck_id"),
            "driver_id": set_fields.get("driver_id", assignment.get("driver_id")),
            "driver_name": set_fields.get("driver_name") or assignment.get("driver_name") or "",
            "project_number": assignment.get("project_number") or "",
            "from_state": assignment.get("current_state"),
            "to_state": assignment.get("current_state"),
            "standard": True,
            "warning_tag": "REASSIGNED",
            "warning_tags": ["REASSIGNED"],
            "at": at_iso,
            "by_name": by_name,
            "by_role": by_role,
            "note": body.reason or "",
            "correction_reason": "",
            "wait_reason": "",
            "geo": None,
        })
        out = await db.dispatch_assignments.find_one({"id": assignment_id}, {"_id": 0})
        return {"ok": True, "assignment": out}

    # ────────────────────────────────────────────────────────────────
    # D-1.1 · ACKNOWLEDGE (dispatcher-on-behalf)
    # The primary driver-side path lives in routes/dispatch_driver.py
    # (driver session token). This endpoint lets a dispatcher record
    # an ack on behalf of a driver who confirmed by phone/radio.
    # ────────────────────────────────────────────────────────────────
    @router.post("/assignments/{assignment_id}/acknowledge")
    async def acknowledge_on_behalf(
        assignment_id: str,
        body: AcknowledgementRequest,
        actor: Dict[str, Any] = Depends(require_dispatch_or_admin_dep),
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        assignment = await db.dispatch_assignments.find_one(
            {"id": assignment_id, "tenant_id": tenant_id}, {"_id": 0},
        )
        if not assignment:
            raise HTTPException(404, "Assignment not found")
        if assignment.get("cancelled_at"):
            raise HTTPException(409, "Cannot acknowledge a cancelled assignment")
        method = (body.method or "dispatcher-on-behalf").strip() or "dispatcher-on-behalf"
        updated = await _record_acknowledgement(
            db,
            assignment=assignment,
            actor=actor,
            method=method,
            device=body.device or "",
            note=body.note or "",
        )
        return {"ok": True, "assignment": updated}

    # ────────────────────────────────────────────────────────────────
    # D-2.4 · MANUAL "Text Magic Link" · dispatcher-triggered
    # ────────────────────────────────────────────────────────────────
    @router.post("/assignments/{assignment_id}/send-magic-sms")
    async def send_magic_sms(
        assignment_id: str,
        actor: Dict[str, Any] = Depends(require_dispatch_or_admin_dep),
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        """Dispatcher taps "Text Magic Link" in AssignmentDrawer.

        Returns a structured payload so the frontend can:
          - show a success toast when ``sms_result.status == "sent"``
          - fall back to copy-link when SMS is disabled, phone is
            missing, or the provider failed (status != "sent")

        Always returns 200 — the operational outcome lives in the body.
        Failure scenarios are not HTTP errors because the system has a
        clean fallback (copy-link) in every case.
        """
        tenant_id = _resolve_tenant(x_tenant_id)
        assignment = await db.dispatch_assignments.find_one(
            {"id": assignment_id, "tenant_id": tenant_id}, {"_id": 0},
        )
        if not assignment:
            raise HTTPException(404, "Assignment not found")
        if assignment.get("cancelled_at"):
            raise HTTPException(409, "Assignment is cancelled")

        outcome = await _issue_link_and_sms(
            db,
            assignment=assignment,
            triggered_by="dispatcher",
            issued_by_name=_actor_label(actor),
            issued_by_role=_actor_role(actor),
        )
        # Persist + audit via the existing fan-out helper.
        try:
            await _fire_assignment_notification(
                db,
                assignment=assignment,
                event="manual_sms",
                send_email_fn=None,                     # email not duplicated for manual SMS
                magic_link_url=outcome.get("magic_link_url"),
                sms_result=outcome.get("sms_result"),
            )
        except Exception as _e:  # noqa: BLE001
            logger.warning(f"[send-magic-sms-notify] {_e}")

        sms_result = outcome.get("sms_result") or {}
        return {
            "ok": True,
            "sms_status": sms_result.get("status"),
            "sms_ok": bool(sms_result.get("ok")),
            "destination_phone_masked": sms_result.get("destination_phone_masked"),
            "error_summary": sms_result.get("error_summary"),
            "magic_link_url": outcome.get("magic_link_url"),
            "fallback": (
                "copy-link"
                if not sms_result.get("ok")
                else None
            ),
        }

    # ────────────────────────────────────────────────────────────────
    # D-2.7 · Twilio status callback receiver
    # ────────────────────────────────────────────────────────────────
    # Twilio POSTs a form-encoded body with these key fields:
    #   MessageSid, MessageStatus, To, From, ErrorCode (optional),
    #   ErrorMessage (optional). We accept the request, verify the
    #   X-Twilio-Signature header, then update the matching
    #   delivery_log[] entry on the assignment_id passed as query
    #   string. No new collection. No new schema.
    # ────────────────────────────────────────────────────────────────
    @router.post("/sms/twilio-status-callback")
    async def twilio_status_callback(
        request: Request,
        assignment_id: str = Query(default=""),
    ):
        from services.sms_provider import verify_twilio_signature  # noqa: PLC0415

        # Twilio sends application/x-www-form-urlencoded.
        try:
            form = await request.form()
            form_params: Dict[str, Any] = dict(form)
        except Exception:
            form_params = {}

        # Verify signature.
        signature = request.headers.get("X-Twilio-Signature")
        # We must reconstruct the full URL Twilio used (including the
        # query string) for the signature to validate. Behind an
        # ingress, request.url already reflects the public URL.
        full_url = str(request.url)
        verified = verify_twilio_signature(
            signature=signature, full_url=full_url, form_params=form_params,
        )
        if not verified:
            # Soft-fail when the operator has not yet provisioned creds
            # (e.g. preview env) so the route is still introspectable.
            # In production with creds set, an unverified request is
            # rejected with 403.
            if _twilio_creds_configured():
                raise HTTPException(403, "Invalid Twilio signature")

        message_sid = str(form_params.get("MessageSid") or "").strip()
        message_status = str(form_params.get("MessageStatus") or "").strip().lower()
        error_code = str(form_params.get("ErrorCode") or "").strip()
        error_message = str(form_params.get("ErrorMessage") or "").strip()
        if not message_sid or not message_status:
            raise HTTPException(400, "Missing MessageSid/MessageStatus")
        if not assignment_id:
            # No assignment context — silently ack so Twilio doesn't
            # keep retrying.
            return {"ok": True, "ignored": "no assignment_id"}

        # Atomically patch the matching delivery_log[] entry. We use
        # the array-filter positional operator to target exactly the
        # row with this provider_message_id.
        update_fields = {
            "delivery_log.$[entry].status": message_status,
            "delivery_log.$[entry].provider_status_at": _now_iso(),
        }
        if error_code or error_message:
            update_fields["delivery_log.$[entry].error"] = (
                f"Twilio {error_code}: {error_message}".strip(": ")
            )[:240]
        await db.dispatch_assignments.update_one(
            {"id": assignment_id},
            {"$set": update_fields},
            array_filters=[{"entry.provider_message_id": message_sid}],
        )

        # Append a one-line audit row to dispatch_state_events so the
        # board's audit drawer surfaces the carrier-side transitions.
        try:
            assignment = await db.dispatch_assignments.find_one(
                {"id": assignment_id}, {"_id": 0, "tenant_id": 1, "truck_id": 1,
                                         "driver_id": 1, "driver_name": 1,
                                         "project_number": 1, "current_state": 1},
            )
            if assignment:
                await db.dispatch_state_events.insert_one({
                    "id": _new_id(),
                    "tenant_id": assignment.get("tenant_id") or DEFAULT_TENANT_ID,
                    "assignment_id": assignment_id,
                    "truck_id": assignment.get("truck_id"),
                    "driver_id": assignment.get("driver_id"),
                    "driver_name": assignment.get("driver_name") or "",
                    "project_number": assignment.get("project_number") or "",
                    "from_state": assignment.get("current_state"),
                    "to_state": assignment.get("current_state"),
                    "standard": True,
                    "warning_tag": "SMS_STATUS",
                    "warning_tags": ["SMS_STATUS"],
                    "at": _now_iso(),
                    "by_name": "twilio",
                    "by_role": "dispatch_sms",
                    "note": "",
                    "correction_reason": "",
                    "wait_reason": "",
                    "geo": None,
                    "sms_provider_message_id": message_sid,
                    "sms_status": message_status,
                    "sms_error_summary": (
                        f"Twilio {error_code}: {error_message}".strip(": ")
                        if (error_code or error_message) else None
                    ),
                })
        except Exception as _e:  # noqa: BLE001
            logger.warning(f"[twilio-status-audit] {_e}")

        return {"ok": True, "message_sid": message_sid, "status": message_status}

    # ────────────────────────────────────────────────────────────────
    # D-1.5 · REVISE in-flight
    # Mutable fields only — truck/driver changes still flow through
    # /reassign. Resets ack and sets revision_pending=True.
    # ────────────────────────────────────────────────────────────────
    @router.post("/assignments/{assignment_id}/revise")
    async def revise_assignment(
        assignment_id: str,
        body: RevisionRequest,
        actor: Dict[str, Any] = Depends(require_dispatch_or_admin_dep),
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        assignment = await db.dispatch_assignments.find_one(
            {"id": assignment_id, "tenant_id": tenant_id}, {"_id": 0},
        )
        if not assignment:
            raise HTTPException(404, "Assignment not found")
        if assignment.get("cancelled_at"):
            raise HTTPException(409, "Cannot revise a cancelled assignment")
        if assignment.get("current_state") in DLS.TERMINAL_STATES:
            raise HTTPException(
                409,
                "Cannot revise an assignment in a terminal state",
            )

        # Build the changes dict from the request body, including only
        # the explicitly-set fields. Pydantic gives us model_dump with
        # exclude_unset=True.
        body_dump = body.model_dump(exclude_unset=True, exclude={"reason"})
        changes = {k: v for k, v in body_dump.items() if k in REVISABLE_FIELDS}
        if not changes:
            raise HTTPException(
                422,
                "Provide at least one revisable field to change",
            )

        updated = await _record_revision(
            db,
            assignment=assignment,
            actor=actor,
            changes=changes,
            reason=body.reason or "",
        )

        # Fire notification for the revision so dispatch sees a bell
        # entry + driver gets an email (re-ack required). Same
        # best-effort gate as create.
        try:
            await _fire_assignment_notification(
                db,
                assignment=updated,
                event="revision",
                send_email_fn=send_email_fn,
                magic_link_url=None,
            )
            updated = await db.dispatch_assignments.find_one(
                {"id": assignment_id}, {"_id": 0},
            )
        except Exception as _notify_err:  # noqa: BLE001
            logger.warning(f"[dispatch-revise-notify] {_notify_err}")

        return {"ok": True, "assignment": updated}
    # ────────────────────────────────────────────────────────────────
    @router.get("/state-events")
    async def list_state_events(
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
        assignment_id: Optional[str] = None,
        non_standard_only: bool = False,
        limit: int = Query(_HISTORY_DEFAULT_LIMIT, ge=1, le=_HISTORY_MAX_LIMIT),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        query: Dict[str, Any] = {"tenant_id": tenant_id}
        if assignment_id:
            query["assignment_id"] = assignment_id
        if non_standard_only:
            query["standard"] = False
        cursor = (
            db.dispatch_state_events
            .find(query, {"_id": 0})
            .sort("at", -1)
            .limit(limit)
        )
        rows = await cursor.to_list(length=limit)
        return {"ok": True, "tenant_id": tenant_id, "count": len(rows), "events": rows}

    # ────────────────────────────────────────────────────────────────
    # HAUL CYCLES (derived summary — read)
    # ────────────────────────────────────────────────────────────────
    @router.get("/haul-cycles")
    async def list_haul_cycles(
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
        truck_id: Optional[str] = None,
        driver_id: Optional[str] = None,
        project_number: Optional[str] = None,
        limit: int = Query(100, ge=1, le=500),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        query: Dict[str, Any] = {"tenant_id": tenant_id}
        if truck_id:
            query["truck_id"] = truck_id
        if driver_id:
            query["driver_id"] = driver_id
        if project_number:
            query["project_number"] = project_number
        cursor = (
            db.haul_cycles
            .find(query, {"_id": 0})
            .sort("completed_at", -1)
            .limit(limit)
        )
        rows = await cursor.to_list(length=limit)
        return {"ok": True, "tenant_id": tenant_id, "count": len(rows), "cycles": rows}

    # ────────────────────────────────────────────────────────────────
    # META — canonical state list (consumed by future driver UI)
    # ────────────────────────────────────────────────────────────────
    @router.get("/lifecycle/states")
    async def get_canonical_states(
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
    ):
        return {
            "ok": True,
            "states": DLS.CANONICAL_STATES,
            "terminal": sorted(DLS.TERMINAL_STATES),
            "operational": sorted(DLS.OPERATIONAL_STATES),
            "preferred_next": {
                s: DLS.allowed_next_states(s) for s in DLS.CANONICAL_STATES
            },
        }

    # ────────────────────────────────────────────────────────────────
    # iter409 · Phase 14.3 · PM Haul Activity (production awareness)
    # ────────────────────────────────────────────────────────────────
    @router.get("/haul-activity")
    async def haul_activity_summary(
        actor: Dict[str, Any] = Depends(require_any_portal_token_dep),  # noqa: ARG001
        project_number: Optional[str] = Query(default=None),
        project_numbers: Optional[str] = Query(default=None),
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        """Calm, role-agnostic production awareness.

        PM Hub renders this as a "Haul Activity" tile, scoped to the
        PM's project_numbers. The same endpoint serves any portal that
        cares — admin, dispatch, FL — so we don't fork the data path.

        Doctrine:
          * Derived only from `dispatch_assignments` + `haul_cycles`
            (no new collection).
          * Numbers, not graphs. No analytics drift.
          * "Today" = UTC calendar day boundary of `started_at`.
          * Empty project_number → tenant-wide summary (admin/dispatch).

        Query options:
          - project_number=PRJ-1
          - project_numbers=PRJ-1,PRJ-2,PRJ-3
        """
        tenant_id = _resolve_tenant(x_tenant_id)
        targets: List[str] = []
        if project_number:
            targets.append(project_number.strip())
        if project_numbers:
            targets.extend(
                [p.strip() for p in project_numbers.split(",") if p.strip()],
            )
        targets = list({p for p in targets if p})

        # Day boundary in UTC
        now = datetime.now(timezone.utc)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        day_start_iso = day_start.isoformat()

        # Base match: tenant + (optional) project scope
        base_match: Dict[str, Any] = {"tenant_id": tenant_id}
        if targets:
            base_match["project_number"] = {"$in": targets}

        # ── Loads completed today (haul_cycles is canonical) ──────
        loads_completed_today = 0
        equipment_moves_completed_today = 0
        material_loads_completed_today = 0
        try:
            cycle_match = dict(base_match)
            cycle_match["completed_at"] = {"$gte": day_start_iso}
            async for c in db.haul_cycles.find(
                cycle_match,
                {"_id": 0, "haul_type": 1},
            ):
                loads_completed_today += 1
                if (c.get("haul_type") or "Material") == "Equipment Move":
                    equipment_moves_completed_today += 1
                else:
                    material_loads_completed_today += 1
        except Exception:
            pass

        # ── Active hauls + state-based signals (dispatch_assignments) ──
        active_hauls = 0
        equipment_moves_active = 0
        waiting_on_plant = 0
        waiting_on_dump = 0
        breakdown_impacts = 0
        try:
            active_match = dict(base_match)
            active_match["current_state"] = {"$nin": list(DLS.TERMINAL_STATES)}
            async for a in db.dispatch_assignments.find(
                active_match,
                {
                    "_id": 0, "current_state": 1, "current_wait_reason": 1,
                    "haul_type": 1,
                },
            ):
                active_hauls += 1
                state = a.get("current_state") or ""
                wait = (a.get("current_wait_reason") or "").upper()
                if state == DLS.BREAKDOWN:
                    breakdown_impacts += 1
                if state == DLS.WAITING:
                    if "PLANT" in wait:
                        waiting_on_plant += 1
                    elif "DUMP" in wait or "SITE" in wait:
                        waiting_on_dump += 1
                if (a.get("haul_type") or "Material") == "Equipment Move":
                    equipment_moves_active += 1
        except Exception:
            pass

        # ── Top materials today (small, calm, capped at 5) ─────────
        top_materials: List[Dict[str, Any]] = []
        try:
            pipeline = [
                {"$match": {
                    "tenant_id": tenant_id,
                    "completed_at": {"$gte": day_start_iso},
                    "material": {"$nin": [None, "", "Equipment Move"]},
                    **({"project_number": {"$in": targets}} if targets else {}),
                }},
                {"$group": {
                    "_id": "$material",
                    "count": {"$sum": 1},
                }},
                {"$sort": {"count": -1}},
                {"$limit": 5},
            ]
            async for row in db.haul_cycles.aggregate(pipeline):
                if row.get("_id"):
                    top_materials.append({
                        "label": row["_id"],
                        "loads": int(row.get("count") or 0),
                    })
        except Exception:
            pass

        return {
            "ok": True,
            "tenant_id": tenant_id,
            "scope": "project" if targets else "tenant",
            "project_numbers": targets,
            "as_of": now.isoformat(),
            "day_window_start": day_start_iso,
            "loads_completed_today": loads_completed_today,
            "material_loads_completed_today": material_loads_completed_today,
            "equipment_moves_completed_today": equipment_moves_completed_today,
            "active_hauls": active_hauls,
            "equipment_moves_active": equipment_moves_active,
            "waiting_on_plant": waiting_on_plant,
            "waiting_on_dump": waiting_on_dump,
            "breakdown_impacts": breakdown_impacts,
            "top_materials": top_materials,
        }

    return router


# ════════════════════════════════════════════════════════════════════
# iter412 · Phase 16.1 · Admin DLS Health Summary
# ════════════════════════════════════════════════════════════════════
def build_dls_admin_health_router(
    db,
    require_admin_dep: Callable[..., Awaitable[Dict[str, Any]]],
) -> APIRouter:
    """Single read-only health endpoint for Day-1 live ops monitoring.

    GET /api/admin/dls/health-summary

    Doctrine:
      - Admin only · single JSON read · no charts · no scores · no KPIs.
      - Computed on demand from existing collections; zero new
        collections, zero stored summaries, zero new write surface.
      - status ∈ {quiet, flowing, attention} — no scoring.
      - Notes carry small operational reasons for the status (≤3 entries).
    """
    router = APIRouter(prefix="/api/admin/dls", tags=["dispatch-lifecycle-health"])

    @router.get("/health-summary")
    async def dls_health_summary(
        actor: Dict[str, Any] = Depends(require_admin_dep),  # noqa: ARG001
        x_tenant_id: Optional[str] = Header(default=None, alias="X-Tenant-Id"),
    ):
        tenant_id = _resolve_tenant(x_tenant_id)
        now = datetime.now(timezone.utc)
        day_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        day_iso = day_start.isoformat()
        date_str = now.strftime("%Y-%m-%d")

        # ── Active assignments + state classification ──────────────
        active_assignments = 0
        waiting_count = 0
        breakdown_count = 0
        oldest_waiting_minutes = 0
        oldest_stuck_minutes = 0
        try:
            cur = db.dispatch_assignments.find(
                {
                    "tenant_id": tenant_id,
                    "current_state": {"$nin": list(DLS.TERMINAL_STATES)},
                },
                {
                    "_id": 0, "current_state": 1, "last_transition_at": 1,
                },
            )
            async for a in cur:
                active_assignments += 1
                state = a.get("current_state") or ""
                lt = a.get("last_transition_at")
                age_min = 0
                if lt:
                    try:
                        ts = datetime.fromisoformat(lt.replace("Z", "+00:00"))
                        age_min = int(max(0, (now - ts).total_seconds() // 60))
                    except Exception:
                        age_min = 0
                if state == DLS.WAITING:
                    waiting_count += 1
                    if age_min > oldest_waiting_minutes:
                        oldest_waiting_minutes = age_min
                if state == DLS.BREAKDOWN:
                    breakdown_count += 1
                if age_min > oldest_stuck_minutes:
                    oldest_stuck_minutes = age_min
        except Exception:
            pass

        # ── Today's flow signals ───────────────────────────────────
        assignments_created_today = 0
        haul_counts = {
            "Material": 0, "Equipment Move": 0,
            "Tanker / Liquid Asphalt": 0,
            "Spoils / Dump": 0, "Support / Misc": 0,
        }
        try:
            cur2 = db.dispatch_assignments.find(
                {"tenant_id": tenant_id, "created_at": {"$gte": day_iso}},
                {"_id": 0, "haul_type": 1},
            )
            async for a in cur2:
                assignments_created_today += 1
                ht = (a.get("haul_type") or "Material").strip() or "Material"
                if ht in haul_counts:
                    haul_counts[ht] += 1
        except Exception:
            pass

        completed_cycles_today = 0
        try:
            completed_cycles_today = await db.haul_cycles.count_documents({
                "tenant_id": tenant_id,
                "completed_at": {"$gte": day_iso},
            })
        except Exception:
            pass

        transitions_today = 0
        try:
            transitions_today = await db.dispatch_state_events.count_documents({
                "tenant_id": tenant_id,
                "occurred_at": {"$gte": day_iso},
            })
        except Exception:
            pass

        # ── Active shifts (driver sessions still open today) ───────
        active_shifts = 0
        try:
            active_shifts = await db.dispatch_driver_sessions.count_documents({
                "tenant_id": tenant_id,
                "$or": [
                    {"ended_at": None},
                    {"ended_at": {"$exists": False}},
                ],
            })
        except Exception:
            pass

        # ── Findings today (reuse governance computation surface) ──
        findings_today = 0
        try:
            findings_today = (
                (1 if breakdown_count > 0 else 0)
                + (1 if oldest_waiting_minutes >= 45 else 0)
                + (1 if oldest_stuck_minutes >= 30 else 0)
            )
        except Exception:
            findings_today = 0

        # ── Status classification ──────────────────────────────────
        notes: List[str] = []
        if breakdown_count > 0:
            notes.append(f"{breakdown_count} breakdown(s) active")
        if oldest_waiting_minutes >= 45:
            notes.append(f"longest wait {oldest_waiting_minutes} min")
        if oldest_stuck_minutes >= 60:
            notes.append(f"oldest active assignment {oldest_stuck_minutes} min in state")

        if (
            active_assignments == 0
            and active_shifts == 0
            and findings_today == 0
            and breakdown_count == 0
        ):
            status = "quiet"
        elif (
            breakdown_count > 0
            or oldest_waiting_minutes >= 45
            or oldest_stuck_minutes >= 60
            or findings_today > 0
        ):
            status = "attention"
        else:
            status = "flowing"

        return {
            "ok": True,
            "tenant_id": tenant_id,
            "date": date_str,
            "as_of": now.isoformat(),
            "active_shifts": active_shifts,
            "active_assignments": active_assignments,
            "assignments_created_today": assignments_created_today,
            "completed_cycles_today": completed_cycles_today,
            "transitions_today": transitions_today,
            "waiting_count": waiting_count,
            "breakdown_count": breakdown_count,
            "oldest_waiting_minutes": oldest_waiting_minutes,
            "oldest_stuck_minutes": oldest_stuck_minutes,
            "findings_today": findings_today,
            "haul_types_today": haul_counts,
            "status": status,
            "notes": notes[:3],
        }

    return router


__all__ = [
    "build_dispatch_lifecycle_router",
    "build_dls_admin_health_router",
    "ensure_dispatch_lifecycle_indexes",
    "DEFAULT_TENANT_ID",
]
