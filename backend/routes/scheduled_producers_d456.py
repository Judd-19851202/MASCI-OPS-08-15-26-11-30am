"""
routes/scheduled_producers_d456.py — Track 14.0-NOTIFY-OWNERSHIP-LOCK
Deliverables D4 / D5 / D6.

Three idempotent scheduled producers feeding the notification spine:

  D4  Asset Document expiration       (asset_admin recipient)
  D5  HR Training expiration          (hr recipient)
  D6  Dispatch Stale Location          (dispatch recipient)

Each producer is a pure async function that walks the source collection,
computes the appropriate notification type per the D1 Ownership Matrix
(60/30/14/7/expired window for D4-D5; 30/60/240-min window for D6),
fan-outs notifications via `notification_service.fanout`, and marks the
source row with a `fires_at_threshold` list so the same threshold is
never emitted twice. Person-level recipient_user_id is resolved when
the source carries an owner field; otherwise the role bucket is used.

Admin trigger endpoints:
  POST /api/admin/notify-producers/d4/asset-docs            (preview only)
  POST /api/admin/notify-producers/d5/hr-training           (preview only)
  POST /api/admin/notify-producers/d6/dispatch-stale        (preview only)
  POST /api/admin/notify-producers/run-all                  (preview only)

These endpoints are admin-gated. In production, a background scheduler
(set up separately under `services/`) calls these same producer
functions hourly.
"""
from __future__ import annotations

import logging
from datetime import date, datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query

logger = logging.getLogger(__name__)

# Window definitions per D1 matrix.
DOC_WINDOWS = [60, 30, 14, 7]                # days, descending → ascending
TRAINING_WINDOWS = [60, 30, 14, 7]
STALE_WINDOWS_MINUTES = [30, 60, 240]


def _today() -> date:
    return datetime.now(timezone.utc).date()


def _to_date(v: Any) -> Optional[date]:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    if isinstance(v, str):
        try:
            return date.fromisoformat(v[:10])
        except Exception:
            return None
    return None


def _pick_threshold_window(days_until: int, windows: List[int]) -> Optional[int]:
    """Return the smallest window ≥ days_until (or None if outside).
    -1 sentinel returned for already-expired docs."""
    if days_until < 0:
        return -1
    for thr in sorted(windows):
        if days_until <= thr:
            return thr
    return None


def _severity_for(thr: int) -> str:
    if thr == -1:
        return "Critical"
    if thr <= 7:
        return "Critical"
    if thr <= 14:
        return "Warning"
    return "Info"


def _windowed_minutes(minutes: int, windows: List[int]) -> Optional[int]:
    """Largest applicable minute-window. -1 sentinel if exceeds the
    biggest. Returns smallest-step crossed."""
    target: Optional[int] = None
    for w in sorted(windows):
        if minutes >= w:
            target = w
    return target


# ──────────────────────────────────────────────────────────────────
# D4 — Asset Document Expiration
# ──────────────────────────────────────────────────────────────────
async def scan_asset_documents(db, dry_run: bool = False) -> Dict[str, Any]:
    """D4 producer. Walks `db.operational_attachments` where
    host_kind='asset' AND expiration_date is set. Emits one
    `asset_doc.expires_<N>d` notification per crossed threshold.
    Idempotency via per-doc `fires_at_threshold` list. Recipient role
    is `asset_admin`. Recipient user is resolved via the asset's
    assigned_user_id when present.
    """
    from routes.tasks_notifications import notification_service  # noqa: PLC0415

    today = _today()
    scanned = 0
    fired: List[Dict[str, Any]] = []

    cur = db.operational_attachments.find(
        {"host_kind": "asset", "expiration_date": {"$exists": True, "$ne": None}},
        {"_id": 0},
    )
    async for d in cur:
        scanned += 1
        exp = _to_date(d.get("expiration_date"))
        if exp is None:
            continue
        days_until = (exp - today).days
        thr = _pick_threshold_window(days_until, DOC_WINDOWS)
        if thr is None:
            continue
        already = set(d.get("fires_at_threshold") or [])
        if thr in already:
            continue
        # Compose payload.
        asset_id = d.get("host_id")
        doc_type = (d.get("type") or "document").replace("_", " ")
        label = "Expired" if thr == -1 else f"Expires in ≤{thr} days"
        ntype = "asset_doc.expired" if thr == -1 else f"asset_doc.expires_{thr}d"
        title = f"{label}: {doc_type} on {asset_id or '—'}"[:200]
        msg = (
            f"Asset {asset_id} · document type {doc_type} · expiration "
            f"{exp.isoformat()} · {label.lower()}."
        )[:2000]

        # Owner resolution via assets master (best-effort).
        recipient_user_id: Optional[str] = None
        if asset_id:
            try:
                a = await db.assets.find_one(
                    {"id": asset_id},
                    {"_id": 0, "assigned_user_id": 1, "owner_user_id": 1},
                )
                if a:
                    recipient_user_id = (
                        a.get("assigned_user_id") or a.get("owner_user_id")
                    )
            except Exception:
                pass

        # Track 14.0-JOB-OWNERSHIP-FOUNDATION Phase 2B — if the asset
        # is currently assigned to a project, walk the project's roster
        # for asset_admin → locate_coordinator → pm. Gated by env flag.
        snapshot = None
        project_number = None
        try:
            from lib.team_routing import resolve_routing, snapshot_team, ROLE_CHAIN  # noqa: PLC0415
            if asset_id:
                aa = await db.asset_assignments.find_one(
                    {"asset_id": asset_id, "active": True},
                    {"_id": 0, "project_number": 1},
                )
                if aa:
                    project_number = aa.get("project_number")
            if project_number:
                routing = await resolve_routing(
                    db,
                    project_number=project_number,
                    role_chain=ROLE_CHAIN["asset_doc.expires"],
                    fallback_role="asset_admin",
                )
                if routing.get("recipient_user_id"):
                    recipient_user_id = routing["recipient_user_id"]
                snapshot = await snapshot_team(db, project_number)
        except Exception:
            pass

        payload = {
            "type": ntype,
            "title": title,
            "message": msg,
            "severity": _severity_for(thr),
            "recipient_role": "asset_admin",
            "recipient_user_id": recipient_user_id,
            "linked_source_module": "documents.expiration",
            "linked_source_record_id": d.get("id"),
            "linked_equipment_id": asset_id,
            "link_url": "/shop/asset-care",
        }
        if snapshot:
            payload["team_snapshot"] = snapshot
            payload["linked_project_number"] = project_number
        if not dry_run:
            try:
                await notification_service.fanout(db, payload)
            except Exception as e:  # pragma: no cover
                logger.warning("D4 fanout failed: %s", e)
                continue
            await db.operational_attachments.update_one(
                {"id": d["id"]},
                {"$push": {"fires_at_threshold": thr},
                 "$set": {"last_scanned_at": datetime.now(timezone.utc)}},
            )
        fired.append({
            "id": d.get("id"), "threshold": thr, "asset_id": asset_id,
            "doc_type": d.get("type"), "expiration_date": exp.isoformat(),
        })

    return {
        "producer": "D4_asset_documents", "scanned": scanned,
        "fired": len(fired), "items": fired, "dry_run": dry_run,
        "at": datetime.now(timezone.utc).isoformat(),
    }


# ──────────────────────────────────────────────────────────────────
# D5 — HR Training Expiration
# ──────────────────────────────────────────────────────────────────
async def scan_hr_training(db, dry_run: bool = False) -> Dict[str, Any]:
    """D5 producer. Walks `db.safety_training_records` with
    `expiration_date` set. Emits one `hr_training.expires_<N>d`
    notification per crossed threshold. Routes to `hr`. Person-level
    recipient resolves to the employee's `supervisor_user_id` via the
    employees collection when available.
    """
    from routes.tasks_notifications import notification_service  # noqa: PLC0415

    today = _today()
    scanned = 0
    fired: List[Dict[str, Any]] = []

    cur = db.safety_training_records.find(
        {"expiration_date": {"$exists": True, "$ne": None}},
        {"_id": 0},
    )
    async for d in cur:
        scanned += 1
        exp = _to_date(d.get("expiration_date"))
        if exp is None:
            continue
        days_until = (exp - today).days
        thr = _pick_threshold_window(days_until, TRAINING_WINDOWS)
        if thr is None:
            continue
        already = set(d.get("fires_at_threshold") or [])
        if thr in already:
            continue
        label = "Expired" if thr == -1 else f"Expires in ≤{thr} days"
        ntype = "hr_training.expired" if thr == -1 else f"hr_training.expires_{thr}d"
        cert = d.get("certification_type") or d.get("training_name") or "training"
        emp_name = d.get("employee_name") or d.get("employee_id") or "—"
        title = f"{label}: {cert} · {emp_name}"[:200]
        msg = (
            f"Employee {emp_name} · {cert} · expiration "
            f"{exp.isoformat()} · {label.lower()}."
        )[:2000]

        # Supervisor lookup for person-level routing.
        recipient_user_id: Optional[str] = None
        emp_master_id = d.get("employee_master_id") or d.get("employee_id")
        if emp_master_id:
            try:
                e = await db.employees.find_one(
                    {"id": emp_master_id},
                    {"_id": 0, "supervisor_user_id": 1, "hr_owner_user_id": 1},
                )
                if e:
                    recipient_user_id = (
                        e.get("supervisor_user_id") or e.get("hr_owner_user_id")
                    )
            except Exception:
                pass

        payload = {
            "type": ntype,
            "title": title,
            "message": msg,
            "severity": _severity_for(thr),
            "recipient_role": "hr",
            "recipient_user_id": recipient_user_id,
            "linked_source_module": "hr.training",
            "linked_source_record_id": d.get("id"),
            "linked_employee_id": emp_master_id,
            "link_url": "/hr/training",
        }
        if not dry_run:
            try:
                await notification_service.fanout(db, payload)
            except Exception as e:  # pragma: no cover
                logger.warning("D5 fanout failed: %s", e)
                continue
            await db.safety_training_records.update_one(
                {"id": d["id"]},
                {"$push": {"fires_at_threshold": thr},
                 "$set": {"last_scanned_at": datetime.now(timezone.utc)}},
            )
        fired.append({
            "id": d.get("id"), "threshold": thr, "employee": emp_name,
            "certification": cert, "expiration_date": exp.isoformat(),
        })

    return {
        "producer": "D5_hr_training", "scanned": scanned,
        "fired": len(fired), "items": fired, "dry_run": dry_run,
        "at": datetime.now(timezone.utc).isoformat(),
    }


# ──────────────────────────────────────────────────────────────────
# D6 — Dispatch Stale Location
# ──────────────────────────────────────────────────────────────────
async def scan_dispatch_stale_locations(db, dry_run: bool = False) -> Dict[str, Any]:
    """D6 producer. Walks active dispatch assignments that carry a
    `last_position_at` field (from telematics). Emits one
    `dispatch.stale_location_<N>m` notification per crossed window
    (30/60/240 min). Routes to `dispatch` role; person-level recipient
    is `assigned_dispatcher_id` when set on the assignment.

    Defensive: if the assignment doesn't carry `last_position_at`,
    skip it. Live fleet_positions integration is dormant in preview, so
    this producer is a no-op until telematics arrives.
    """
    from routes.tasks_notifications import notification_service  # noqa: PLC0415

    now = datetime.now(timezone.utc)
    scanned = 0
    fired: List[Dict[str, Any]] = []

    # Active states only — `current_state` is the dispatch lifecycle key.
    ACTIVE_STATES = {"En Route", "Loading", "Hauling", "Unloading", "Loaded", "Active"}
    cur = db.dispatch_assignments.find(
        {"current_state": {"$in": list(ACTIVE_STATES)}},
        {"_id": 0},
    )
    async for d in cur:
        scanned += 1
        last_seen = d.get("last_position_at") or d.get("last_seen_at")
        if not last_seen:
            continue
        if isinstance(last_seen, str):
            try:
                last_seen_dt = datetime.fromisoformat(last_seen.replace("Z", "+00:00"))
            except Exception:
                continue
        elif isinstance(last_seen, datetime):
            last_seen_dt = last_seen
            if last_seen_dt.tzinfo is None:
                last_seen_dt = last_seen_dt.replace(tzinfo=timezone.utc)
        else:
            continue
        minutes = int((now - last_seen_dt).total_seconds() // 60)
        thr = _windowed_minutes(minutes, STALE_WINDOWS_MINUTES)
        if thr is None:
            continue
        already = set(d.get("stale_fires") or [])
        if thr in already:
            continue
        sev = "Critical" if thr >= 240 else ("Warning" if thr >= 60 else "Info")
        ntype = f"dispatch.stale_location_{thr}m"
        truck = d.get("truck_id") or d.get("equipment_id") or "—"
        driver = d.get("driver_name") or "—"
        title = (
            f"Stale location ≥{thr} min: {truck} · {driver}"
        )[:200]
        msg = (
            f"Truck {truck} (driver {driver}) has not reported a position "
            f"in ≥{thr} minutes (last seen {last_seen_dt.isoformat()})."
        )[:2000]

        payload = {
            "type": ntype,
            "title": title,
            "message": msg,
            "severity": sev,
            "recipient_role": "dispatch",
            "recipient_user_id": d.get("assigned_dispatcher_id"),
            "linked_source_module": "dispatch.fleet_position",
            "linked_source_record_id": d.get("id"),
            "linked_equipment_id": d.get("truck_id") or d.get("equipment_id"),
            "link_url": "/dispatch-portal",
        }
        if not dry_run:
            try:
                await notification_service.fanout(db, payload)
            except Exception as e:  # pragma: no cover
                logger.warning("D6 fanout failed: %s", e)
                continue
            await db.dispatch_assignments.update_one(
                {"id": d["id"]},
                {"$push": {"stale_fires": thr},
                 "$set": {"last_stale_scan_at": now}},
            )
        fired.append({
            "id": d.get("id"), "threshold_min": thr, "truck": truck,
            "driver": driver, "last_seen": last_seen_dt.isoformat(),
        })

    return {
        "producer": "D6_dispatch_stale", "scanned": scanned,
        "fired": len(fired), "items": fired, "dry_run": dry_run,
        "at": now.isoformat(),
    }


# ──────────────────────────────────────────────────────────────────
# Admin trigger endpoints
# ──────────────────────────────────────────────────────────────────
def register_scheduled_producers_d456(
    app, db, require_admin_dep: Callable,
) -> APIRouter:
    router = APIRouter(tags=["notify-producers"])

    @router.post("/api/admin/notify-producers/d4/asset-docs")
    async def run_d4(
        dry_run: bool = Query(default=False),
        actor=Depends(require_admin_dep),  # noqa: ARG001
    ):
        return await scan_asset_documents(db, dry_run=dry_run)

    @router.post("/api/admin/notify-producers/d5/hr-training")
    async def run_d5(
        dry_run: bool = Query(default=False),
        actor=Depends(require_admin_dep),  # noqa: ARG001
    ):
        return await scan_hr_training(db, dry_run=dry_run)

    @router.post("/api/admin/notify-producers/d6/dispatch-stale")
    async def run_d6(
        dry_run: bool = Query(default=False),
        actor=Depends(require_admin_dep),  # noqa: ARG001
    ):
        return await scan_dispatch_stale_locations(db, dry_run=dry_run)

    @router.post("/api/admin/notify-producers/run-all")
    async def run_all(
        dry_run: bool = Query(default=False),
        actor=Depends(require_admin_dep),  # noqa: ARG001
    ):
        d4 = await scan_asset_documents(db, dry_run=dry_run)
        d5 = await scan_hr_training(db, dry_run=dry_run)
        d6 = await scan_dispatch_stale_locations(db, dry_run=dry_run)
        return {"d4": d4, "d5": d5, "d6": d6,
                "at": datetime.now(timezone.utc).isoformat()}

    app.include_router(router)
    return router


__all__ = [
    "scan_asset_documents",
    "scan_hr_training",
    "scan_dispatch_stale_locations",
    "register_scheduled_producers_d456",
]
