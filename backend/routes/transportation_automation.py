"""TRACK 16.10 · Transportation Automation Engine router.

Admin endpoints:
  * POST  /api/admin/transportation/automation/run        — live run
  * POST  /api/admin/transportation/automation/dry-run    — dry-run
  * GET   /api/admin/transportation/automation/runs       — history
  * GET   /api/admin/transportation/automation/actions    — queue
  * PATCH /api/admin/transportation/automation/actions/{id} — resolve/dismiss
  * GET   /api/admin/transportation/automation/forecast   — 30-day forecast
  * GET   /api/admin/transportation/automation/events     — dedupe ledger
  * GET   /api/admin/transportation/automation/health     — last run state

Dispatch visibility (read-only):
  * GET   /api/dispatch/transportation/visibility         — at-risk view
"""
from __future__ import annotations

import asyncio
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)
TENANT = "masci"

# Track 16.10 introduces these route keys. Track 16.09 pilots stay
# live; everything new defaults to dry-run audit-only.
NEW_ROUTE_KEYS = (
    ("TRANSPORT_ANNUAL_INSPECTION_REMINDER", "Annual inspection reminder", False),
    ("TRANSPORT_ANNUAL_INSPECTION_OVERDUE", "Annual inspection overdue", False),
    ("TRANSPORT_DOC_EXPIRING", "Driver/Carrier document expiring", False),
    ("TRANSPORT_DOC_OVERDUE", "Driver/Carrier document overdue", False),
    ("TRANSPORT_ORIENTATION_OVERDUE", "Orientation overdue", False),
    ("TRANSPORT_PACKET_PENDING_REVIEW", "Carrier packet pending review too long", False),
    ("TRANSPORT_ELIGIBILITY_CHANGED", "Dispatch eligibility changed", False),
    ("TRANSPORT_OVERRIDE_APPROVED", "Dispatch override approved", False),
    ("TRANSPORT_OVERRIDE_EXPIRING", "Dispatch override expiring", False),
    # TRACK 16.10A · Internal weekly digest. Marked internal_only =
    # carriers never receive this. Defaults dry-run + disabled until
    # operators populate the internal recipient list.
    ("TRANSPORT_COMMAND_DIGEST_WEEKLY", "Monday-morning Transportation Command Digest", False),
    # TRACK 16.11A · HR Sync Monitor alert. Internal-only, dry-run,
    # disabled by default — exists so action items can reference a
    # canonical route_key even though no external send is enabled.
    ("TRANSPORT_HR_SYNC_MONITOR_ALERT", "HR ↔ Transportation sync monitor alert", False),
)


async def bootstrap_track_16_10(db) -> Dict[str, Any]:
    seeded = 0
    skipped = 0
    for route_key, label, default_enabled in NEW_ROUTE_KEYS:
        existing = await db.email_routes.find_one(
            {"tenant_key": TENANT, "route_key": route_key})
        if existing:
            skipped += 1
            continue
        await db.email_routes.insert_one({
            "id": uuid.uuid4().hex, "tenant_key": TENANT,
            "route_key": route_key, "label": label,
            "to": [], "cc": [], "bcc": [],
            "enabled": default_enabled,
            "is_transportation_pilot": False,
            "internal_only": route_key == "TRANSPORT_COMMAND_DIGEST_WEEKLY" or route_key == "TRANSPORT_HR_SYNC_MONITOR_ALERT",
            "pilot_safe": route_key == "TRANSPORT_COMMAND_DIGEST_WEEKLY" or route_key == "TRANSPORT_HR_SYNC_MONITOR_ALERT",
            "track": (
                "16.10A" if route_key == "TRANSPORT_COMMAND_DIGEST_WEEKLY"
                else "16.11A" if route_key == "TRANSPORT_HR_SYNC_MONITOR_ALERT"
                else "16.10"
            ),
            "created_at": datetime.now(timezone.utc).isoformat(),
            "updated_at": datetime.now(timezone.utc).isoformat(),
        })
        seeded += 1
    logger.info(f"[track-16-10-bootstrap] new routes seeded={seeded} · "
                f"skipped={skipped}")
    return {"seeded": seeded, "skipped": skipped}


# ===========================================================================
# Models
# ===========================================================================
class ActionPatch(BaseModel):
    status: str = Field(..., pattern="^(in_progress|resolved|dismissed)$")
    note: Optional[str] = Field(None, max_length=600)


class RunPayload(BaseModel):
    triggered_by: Optional[str] = "admin"


# ===========================================================================
# Router
# ===========================================================================
def register_track_16_10_routes(app, db, *, require_admin_dep,
                                  require_dispatch_or_admin_dep) -> APIRouter:
    router = APIRouter(prefix="/api", tags=["transportation-automation"])

    # Inline auth resolver (mirror of Track 16.09 — see notes in that
    # router for why we bypass the server.py wrapper).
    async def _dispatch_or_admin(
        request: Request,
        x_admin_token: Optional[str] = Header(default=None, alias="X-Admin-Token"),
        x_dispatch_token: Optional[str] = Header(default=None, alias="X-Dispatch-Token"),
    ) -> Dict[str, Any]:
        from server import _is_valid_directory_admin_token_async  # noqa: PLC0415
        if x_admin_token and await _is_valid_directory_admin_token_async(x_admin_token):
            return {"role": "admin", "is_admin": True}
        if x_dispatch_token:
            try:
                from dispatch_users import is_valid_dispatch_user_token_async
                u = await is_valid_dispatch_user_token_async(db, x_dispatch_token)
                if u:
                    return {"role": "dispatch", "is_admin": False, **u}
            except Exception:  # noqa: BLE001
                pass
        raise HTTPException(401, "Dispatch or Admin auth required")

    # ----- Admin run + dry-run --------------------------------------------
    @router.post("/admin/transportation/automation/run")
    async def admin_run(body: RunPayload = RunPayload(),
                          _: Any = Depends(require_admin_dep)):
        from lib.transport_automation import run_transportation_automation
        out = await run_transportation_automation(
            db, dry_run=False, triggered_by=body.triggered_by or "admin")
        return out

    @router.post("/admin/transportation/automation/dry-run")
    async def admin_dry_run(body: RunPayload = RunPayload(),
                              _: Any = Depends(require_admin_dep)):
        from lib.transport_automation import run_transportation_automation
        out = await run_transportation_automation(
            db, dry_run=True, triggered_by=body.triggered_by or "admin-dryrun")
        return out

    @router.get("/admin/transportation/automation/runs")
    async def admin_run_history(
        limit: int = Query(20, ge=1, le=200),
        _: Any = Depends(require_admin_dep),
    ):
        cur = db.transport_automation_runs.find(
            {"tenant": TENANT}).sort("started_at", -1).limit(limit)
        items = [_strip_id(d) for d in await cur.to_list(limit)]
        return {"count": len(items), "items": items}

    @router.get("/admin/transportation/automation/health")
    async def admin_health(_: Any = Depends(require_admin_dep)):
        last = await db.transport_automation_runs.find_one(
            {"tenant": TENANT}, sort=[("started_at", -1)])
        last = _strip_id(last) if last else None
        # Route status snapshot.
        routes = await db.email_routes.find(
            {"tenant_key": TENANT, "route_key": {"$regex": "^TRANSPORT_"}}
        ).to_list(100)
        live = [r for r in routes if r.get("enabled")]
        dry_run = [r for r in routes if not r.get("enabled")]
        # Stale lock detection — last run > 72 h ago is advisory.
        scheduler_enabled = os.environ.get(
            "SCHEDULER_ENABLED", "true").lower() != "false"
        stale = False
        if last and last.get("completed_at"):
            try:
                completed = datetime.fromisoformat(
                    last["completed_at"].replace("Z", "+00:00"))
                stale = (datetime.now(timezone.utc) - completed).total_seconds() > 72 * 3600
            except Exception:  # noqa: BLE001
                pass
        return {
            "last_run": last,
            "scheduler_enabled": scheduler_enabled,
            "stale": stale,
            "routes_live": [r["route_key"] for r in live],
            "routes_dry_run": [r["route_key"] for r in dry_run],
            "stale_threshold_hours": 72,
        }

    # ----- Action Queue ----------------------------------------------------
    @router.get("/admin/transportation/automation/actions")
    async def admin_actions(
        status: str = Query("open", pattern="^(open|in_progress|resolved|dismissed|all)$"),
        severity: Optional[str] = Query(None),
        limit: int = Query(200, ge=1, le=1000),
        _: Any = Depends(require_dispatch_or_admin_dep),
    ):
        q: Dict[str, Any] = {"tenant": TENANT}
        if status != "all":
            q["status"] = status
        if severity:
            q["severity"] = severity
        cur = db.transport_action_items.find(q).sort("created_at", -1).limit(limit)
        items = [_strip_id(d) for d in await cur.to_list(limit)]
        # Bucket by severity for the command queue UI.
        buckets: Dict[str, List[Dict[str, Any]]] = {
            "blocking": [], "urgent": [], "action_required": [],
            "advisory": [], "info": [],
        }
        for it in items:
            sev = it.get("severity") or "info"
            if sev in buckets:
                buckets[sev].append(it)
            else:
                buckets["info"].append(it)
        return {"count": len(items), "items": items, "buckets": buckets}

    @router.patch("/admin/transportation/automation/actions/{aid}")
    async def admin_action_patch(aid: str, body: ActionPatch, request: Request,
                                   _: Any = Depends(require_admin_dep)):
        row = await db.transport_action_items.find_one(
            {"id": aid, "tenant": TENANT})
        if not row:
            raise HTTPException(404, "Action not found")
        upd = {"status": body.status,
                "updated_at": datetime.now(timezone.utc).isoformat()}
        if body.status in ("resolved", "dismissed"):
            upd["resolved_at"] = upd["updated_at"]
            upd["resolved_by"] = "admin"
            if body.note:
                upd["resolution_note"] = body.note
        await db.transport_action_items.update_one(
            {"_id": row["_id"]}, {"$set": upd})
        try:
            from server import append_audit  # noqa: PLC0415
            await append_audit(
                db, kind="transport_action_item_update",
                entity_type="action_item", entity_id=aid,
                actor={"email": "admin"},
                old={"status": row.get("status")},
                new=upd, request=request,
            )
        except Exception:  # noqa: BLE001
            pass
        return {"ok": True, "id": aid, **upd}

    # ----- 30-day forecast -------------------------------------------------
    @router.get("/admin/transportation/automation/forecast")
    async def admin_forecast(_: Any = Depends(require_dispatch_or_admin_dep)):
        """Reads events without inserting. Reuses the runner's scanners."""
        from lib.transport_automation import (
            _scan_truck_inspections, _scan_orientation, _scan_driver_documents,
            _scan_carrier_documents, _scan_packets, _scan_overrides,
            _parse_dt,
        )
        now = datetime.now(timezone.utc)
        horizon = now + timedelta(days=30)
        scanners = (
            ("inspections_due", _scan_truck_inspections),
            ("orientations_expiring", _scan_orientation),
            ("driver_documents_expiring", _scan_driver_documents),
            ("carrier_documents_expiring", _scan_carrier_documents),
            ("packets_pending", _scan_packets),
            ("overrides", _scan_overrides),
        )
        out: Dict[str, List[Dict[str, Any]]] = {}
        for key, fn in scanners:
            items = []
            try:
                for it in await fn(db):
                    due = _parse_dt(it.get("due_date"))
                    if due and now <= due <= horizon:
                        items.append({
                            "entity_id": it.get("entity_id"),
                            "entity_label": it.get("entity_label"),
                            "due_date": it.get("due_date"),
                            "item_kind": it.get("item_kind"),
                        })
            except Exception as e:  # noqa: BLE001
                items = [{"error": str(e)[:200]}]
            out[key] = items
        return {"horizon_days": 30, "data": out}

    # ----- Automation events ledger ---------------------------------------
    @router.get("/admin/transportation/automation/events")
    async def admin_events(
        entity_id: Optional[str] = Query(None),
        limit: int = Query(200, ge=1, le=1000),
        _: Any = Depends(require_admin_dep),
    ):
        q: Dict[str, Any] = {"tenant": TENANT}
        if entity_id:
            q["entity_id"] = entity_id
        cur = db.transport_automation_events.find(q).sort("created_at", -1).limit(limit)
        items = [_strip_id(d) for d in await cur.to_list(limit)]
        return {"count": len(items), "items": items}

    # ----- Dispatch visibility (read-only) --------------------------------
    @router.get("/dispatch/transportation/visibility")
    async def dispatch_visibility(_: Any = Depends(_dispatch_or_admin)):
        """Read-only at-risk view for dispatchers."""
        # Open action items grouped by what they affect.
        cur = db.transport_action_items.find(
            {"tenant": TENANT, "status": "open"}
        ).sort("due_date", 1).limit(500)
        items = [_strip_id(d) for d in await cur.to_list(500)]
        now = datetime.now(timezone.utc)
        soon = now + timedelta(days=7)
        expiring_this_week = []
        blocked_today = []
        at_risk = []
        for it in items:
            due = it.get("due_date")
            try:
                d = datetime.fromisoformat(str(due).replace("Z", "+00:00")) if due else None
            except Exception:  # noqa: BLE001
                d = None
            sev = it.get("severity")
            if sev in ("urgent", "blocking"):
                blocked_today.append(it)
            elif d and now <= d <= soon:
                expiring_this_week.append(it)
            else:
                at_risk.append(it)
        return {
            "expiring_this_week": expiring_this_week,
            "blocked_today": blocked_today,
            "at_risk": at_risk,
            "note": ("Read-only at-risk view. Open the Transportation "
                      "command queue to take action."),
        }

    # =========================================================
    # TRACK 16.10A · Monday-morning Transportation Command Digest
    # =========================================================
    @router.get("/admin/transportation/automation/digest/preview")
    async def digest_preview(_: Any = Depends(require_admin_dep)):
        from lib.transport_command_digest import build_transport_command_digest
        return await build_transport_command_digest(db)

    @router.post("/admin/transportation/automation/digest/dry-run")
    async def digest_dry_run(_: Any = Depends(require_admin_dep)):
        from lib.transport_command_digest import send_transport_command_digest
        return await send_transport_command_digest(
            db, dry_run=True, triggered_by="admin-dryrun")

    @router.post("/admin/transportation/automation/digest/send-now")
    async def digest_send_now(force: bool = Query(False),
                                _: Any = Depends(require_admin_dep)):
        from lib.transport_command_digest import send_transport_command_digest
        return await send_transport_command_digest(
            db, dry_run=False, force=force, triggered_by="admin")

    @router.get("/admin/transportation/automation/digest/runs")
    async def digest_run_history(
        limit: int = Query(20, ge=1, le=200),
        _: Any = Depends(require_admin_dep),
    ):
        cur = db.transport_command_digest_runs.find(
            {"tenant": TENANT}).sort("ts", -1).limit(limit)
        items = [_strip_id(d) for d in await cur.to_list(limit)]
        return {"count": len(items), "items": items}

    # =========================================================
    # TRACK 16.11A · HR Visibility + Sync Monitor (read-only)
    # =========================================================
    @router.get("/admin/transportation/hr-sync")
    async def hr_sync_health(_: Any = Depends(require_admin_dep)):
        """Live HR-health snapshot for the Transportation Dashboard /
        Command Queue widgets."""
        from lib.transport_sync_monitor import (
            transportation_dashboard_hr_health,
        )
        return await transportation_dashboard_hr_health(db)

    @router.get("/admin/transportation/hr-sync/report")
    async def hr_sync_report(
        run: bool = Query(False),
        stale_days: Optional[int] = Query(None, ge=1, le=120),
        _: Any = Depends(require_admin_dep),
    ):
        """Return the most recent consistency report. When ``run=true``,
        execute a fresh scan first (read-only by default, action items
        are still created — that is the whole point of the engine)."""
        from lib.transport_sync_monitor import (
            scan_hr_transport_consistency,
        )
        if run:
            return await scan_hr_transport_consistency(
                db, stale_days=stale_days)
        last = await db.transport_hr_sync_runs.find_one(
            {"tenant": TENANT}, sort=[("generated_at", -1)])
        if not last:
            # Cold start — run once. Idempotent.
            return await scan_hr_transport_consistency(
                db, stale_days=stale_days)
        return _strip_id(last)

    @router.get("/admin/hr/transportation-status")
    async def hr_transportation_status(
        employee_id: str = Query(...),
        _: Any = Depends(require_admin_dep),
    ):
        """Read-only single-employee Transportation status surface
        consumed by the HR Employee Profile drawer."""
        from lib.transport_sync_monitor import (
            derive_employee_transport_status,
        )
        return await derive_employee_transport_status(db, employee_id)

    @router.get("/admin/hr/transportation-readiness")
    async def hr_transportation_readiness(
        _: Any = Depends(require_admin_dep),
    ):
        """KPI bag for the HR Dashboard 'Transportation Readiness'
        widget. Read-only."""
        from lib.transport_sync_monitor import (
            hr_dashboard_transport_readiness,
        )
        return await hr_dashboard_transport_readiness(db)

    app.include_router(router)
    return router


def _strip_id(doc: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if doc is None:
        return None
    doc.pop("_id", None)
    return doc


# ===========================================================================
# Scheduler loop — daily runner under the singleton lock
# ===========================================================================
async def transport_automation_scheduler_loop(db) -> None:
    """24-hour cycle. Skips when SCHEDULER_ENABLED=false. Errors don't
    abort the loop. Reuses the existing singleton-lock pattern (caller
    supplies)."""
    while True:
        try:
            if os.environ.get("SCHEDULER_ENABLED", "true").lower() == "false":
                logger.info(
                    "[transport-automation] SCHEDULER_ENABLED=false — sleeping")
                await asyncio.sleep(3600)
                continue
            from lib.transport_automation import (
                run_transportation_automation,
            )
            res = await run_transportation_automation(
                db, dry_run=False, triggered_by="scheduler")
            logger.info(
                "[transport-automation] daily tick · "
                f"actions={res['counts']['actions_created']} · "
                f"emails_sent={res['counts']['emails_sent']} · "
                f"needs_cfg={res['counts']['emails_needs_configuration']} · "
                f"errors={res['counts']['errors']}")
            # TRACK 16.11A · Daily HR ↔ Transportation consistency scan
            # piggybacks on the existing automation cadence. No new
            # scheduler is introduced. Read-only against HR.
            try:
                from lib.transport_sync_monitor import (
                    scan_hr_transport_consistency,
                )
                sync_res = await scan_hr_transport_consistency(db)
                logger.info(
                    "[transport-hr-sync-monitor] daily tick · "
                    f"health={sync_res['health']} · "
                    f"mismatches={sync_res['counts']['sync_mismatches']} · "
                    f"actions_created={sync_res['counts']['actions_created']}")
            except Exception as _sync_e:  # noqa: BLE001
                logger.warning(
                    f"[transport-hr-sync-monitor] tick failed: {_sync_e}")
        except Exception as e:  # noqa: BLE001
            logger.exception(f"[transport-automation] loop exception: {e}")
        # 24-hour cadence.
        await asyncio.sleep(24 * 3600)


# ===========================================================================
# TRACK 16.10A · Weekly digest scheduler loop
# ===========================================================================
async def transport_command_digest_scheduler_loop(db) -> None:
    """Monday-morning cadence. Wakes every hour, fires the digest once
    per ISO week when (a) it's Monday 07:00–10:00 UTC, (b)
    SCHEDULER_ENABLED is true, and (c) the weekly dedupe key has not
    already recorded a sent / needs_configuration run."""
    while True:
        try:
            if os.environ.get("SCHEDULER_ENABLED", "true").lower() == "false":
                await asyncio.sleep(3600)
                continue
            now = datetime.now(timezone.utc)
            # Monday=0; fire between 07:00 and 10:00 UTC so prod east-
            # coast operators see it at start of day.
            is_monday_morning = (now.weekday() == 0 and 7 <= now.hour < 10)
            if is_monday_morning:
                from lib.transport_command_digest import (  # noqa: PLC0415
                    send_transport_command_digest,
                )
                res = await send_transport_command_digest(
                    db, dry_run=False, triggered_by="scheduler")
                logger.info(
                    f"[transport-command-digest] tick · status={res.get('status')} "
                    f"· dry_run={res.get('dry_run')} · skipped={res.get('skipped')}")
        except Exception as e:  # noqa: BLE001
            logger.exception(
                f"[transport-command-digest] loop exception: {e}")
        # One-hour cadence — keeps the Monday window narrow without
        # busy-spinning. Weekly dedupe key prevents duplicate sends.
        await asyncio.sleep(3600)
