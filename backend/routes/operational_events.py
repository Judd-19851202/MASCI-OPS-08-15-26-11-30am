"""
routes/operational_events.py · M-2 · Event Router.

Converts Motive presence events (geofence_enter / geofence_exit /
asset_geofence_enter / asset_geofence_exit) into a normalized
operational event spine. Reads from `motive_events` + the Verified
M-3 `operational_locations`. Writes only to its own
`operational_events` collection. Idempotent.

Constitutional posture (per M-2 brief + MOTIVE_001_CONSTITUTIONAL_AUDIT.md §G):
  • Motive verifies / corroborates / visualizes / backfills.
  • Motive NEVER creates Daily Reports, Production, Material Movement,
    Dispatch Assignments, OA events, Safety meetings, Payroll, or signs/
    approves/closes anything.
  • Unknown geofences remain UNKNOWN. Never guess.
  • No driver-behavior storage, no surveillance metrics, no productivity
    rankings, no unauthorized tracking data.
"""
from __future__ import annotations

import logging
import uuid
from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from fastapi import APIRouter, Depends, Header, HTTPException, Path, Query, Request

logger = logging.getLogger(__name__)

M2_TRUST_WORKFLOW = "operational-events-materialization"
M2_AUDIT_KIND = "operational_events.materialize"

MOTIVE_EVENT_PROJECTION = {
    "_id": 0,
    "id": 1,
    "event_family": 1,
    "event_kind": 1,
    "event_at": 1,
    "vehicle_id": 1,
    "asset_id": 1,
    "raw": 1,
    "created_at": 1,
}

LOCATION_PROJECTION = {
    "_id": 0,
    "id": 1,
    "location_type": 1,
    "name": 1,
    "project_number": 1,
    "motive_geofence_id": 1,
    "geocode_status": 1,
}

ASSET_MAPPING_PROJECTION = {
    "_id": 0,
    "provider": 1,
    "asset_kind": 1,
    "masci_equipment_id": 1,
    "motive": 1,
}

PUBLIC_EVENT_PROJECTION = {
    "_id": 0,
    "id": 1,
    "asset_key": 1,
    "asset_kind": 1,
    "asset_label": 1,
    "masci_equipment_id": 1,
    "occurred_at": 1,
    "location_type": 1,
    "location_name": 1,
    "project_number": 1,
    "event_type": 1,
    "confidence": 1,
}

# ── Event taxonomy ────────────────────────────────────────────────────
LOCATION_TYPE_TO_ARRIVAL = {
    "JOB":             ("PROJECT_ARRIVAL",        "PROJECT_DEPARTURE"),
    "ASPHALT_PLANT":   ("ASPHALT_PLANT_ARRIVAL",  "ASPHALT_PLANT_DEPARTURE"),
    "CONCRETE_PLANT":  ("CONCRETE_PLANT_ARRIVAL", "CONCRETE_PLANT_DEPARTURE"),
    "PIT":             ("PIT_ARRIVAL",            "PIT_DEPARTURE"),
    "YARD":            ("YARD_ARRIVAL",           "YARD_DEPARTURE"),
    "SHOP":            ("SHOP_ARRIVAL",           "SHOP_DEPARTURE"),
    "DISPOSAL_SITE":   ("DISPOSAL_ARRIVAL",       "DISPOSAL_DEPARTURE"),
    "VENDOR":          ("VENDOR_ARRIVAL",         "VENDOR_DEPARTURE"),
    "UNKNOWN":         ("UNKNOWN_ARRIVAL",        "UNKNOWN_DEPARTURE"),
}

PRESENCE_EVENTS = {
    "geofence_enter", "geofence_exit",
    "asset_geofence_enter", "asset_geofence_exit",
}

# Doctrinal: never emit LOW; ≥5 min dwell required for HIGH
HIGH_DWELL_MIN = 5

# Storage doctrine (M-2-8): allowed fields only. Anything resembling
# driver behavior / surveillance / ranking is REJECTED at write time.
ALLOWED_EVENT_FIELDS = {
    "id", "asset_key", "asset_kind", "asset_label",
    "motive_vehicle_id", "motive_asset_id", "masci_equipment_id",
    "occurred_at", "location_type", "location_id", "location_name",
    "project_number", "event_type", "confidence",
    "source_event_ids", "dwell_minutes_so_far",
    "created_at", "updated_at",
}
FORBIDDEN_KEYWORDS = ("driver_score", "behavior", "surveillance",
                      "ranking", "productivity_rank")


# ── Helpers ───────────────────────────────────────────────────────────
def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(ts: Any) -> Optional[datetime]:
    if not ts:
        return None
    if isinstance(ts, datetime):
        return ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
    s = str(ts).replace("Z", "+00:00")
    try:
        d = datetime.fromisoformat(s)
        return d if d.tzinfo else d.replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def _event_actor_key(ev: Dict[str, Any]) -> Optional[str]:
    raw = ev.get("raw") or {}
    veh = raw.get("vehicle") or {}
    asset = raw.get("asset") or {}
    if veh.get("id"):
        return f"vehicle:{veh['id']}"
    if asset.get("id"):
        return f"equipment:{asset['id']}"
    if ev.get("vehicle_id"):
        return f"vehicle:{ev['vehicle_id']}"
    if ev.get("asset_id"):
        return f"equipment:{ev['asset_id']}"
    return None


def _event_geofence_id(ev: Dict[str, Any]) -> Optional[str]:
    raw = ev.get("raw") or {}
    gf = raw.get("geofence") or {}
    gid = gf.get("id")
    return str(gid) if gid is not None and gid != "" else None


def _is_enter(ev: Dict[str, Any]) -> bool:
    f = ev.get("event_family") or ev.get("event_kind") or ""
    return f.endswith("_enter")


def _is_exit(ev: Dict[str, Any]) -> bool:
    f = ev.get("event_family") or ev.get("event_kind") or ""
    return f.endswith("_exit")


def _stable_id(actor_key: str, occurred_at_iso: str, event_type: str,
               location_id: Optional[str]) -> str:
    """Deterministic id for idempotent upserts."""
    import hashlib
    raw = f"{actor_key}|{occurred_at_iso}|{event_type}|{location_id or 'UNKNOWN'}"
    return "oe_" + hashlib.sha1(raw.encode()).hexdigest()[:24]


def _validate_doc(doc: Dict[str, Any]) -> None:
    """Constitutional storage gate (M-2-8). Rejects forbidden fields."""
    bad = [k for k in doc.keys() if k not in ALLOWED_EVENT_FIELDS]
    if bad:
        raise ValueError(f"M-2-8: forbidden fields in operational_event: {bad}")
    for k in doc.keys():
        for bw in FORBIDDEN_KEYWORDS:
            if bw in str(k).lower():
                raise ValueError(f"M-2-8: forbidden keyword '{bw}' in field '{k}'")


async def _resolve_admin_actor(db, token: Optional[str]) -> Dict[str, Any]:
    if not token or "." not in token:
        return {}
    try:
        import user_directory as _ud_local  # noqa: PLC0415
        row = await _ud_local.is_valid_directory_admin_token_async(db, token)
    except Exception:  # noqa: BLE001
        return {}
    if not row:
        return {}
    return {
        "id": row.get("id"),
        "email": row.get("email"),
        "name": row.get("name") or row.get("full_name") or row.get("email"),
        "portal": "admin",
    }


async def _write_materialize_audit(
    db,
    *,
    run_id: str,
    correlation_id: str,
    actor: Dict[str, Any],
    start: Optional[str],
    end: Optional[str],
    events_considered: int,
    routed: int,
    upserted: int,
    skipped: int,
    unknown_count: int,
    request_path: str,
) -> bool:
    doc = {
        "id": str(uuid.uuid4()),
        "ts": _now_utc().isoformat(),
        "kind": M2_AUDIT_KIND,
        "category": "operational_events",
        "action": "materialize",
        "record_id": run_id,
        "correlation_id": correlation_id,
        "actor": (actor or {}).get("name") or "unknown-admin",
        "actor_id": (actor or {}).get("id"),
        "actor_email": (actor or {}).get("email"),
        "route": request_path,
        "detail": {
            "workflow": M2_TRUST_WORKFLOW,
            "source_collection": "motive_events",
            "canonical_collection": "operational_events",
            "normalization_owner": "routes.operational_events",
            "start": start,
            "end": end,
            "events_considered": events_considered,
            "routed": routed,
            "upserted": upserted,
            "skipped_by_storage_gate": skipped,
            "unknown_location_events": unknown_count,
            "notification_contract": "none",
        },
    }
    try:
        await db.audit_events.insert_one(doc)
        return True
    except Exception as exc:  # noqa: BLE001
        logger.warning("[m2 audit] materialize audit insert failed: %s", exc)
        return False


# ── Pure router function (testable in isolation) ──────────────────────
def route_motive_events(
    presence_events: List[Dict[str, Any]],
    op_locations_by_gid: Dict[str, Dict[str, Any]],
    asset_label_resolver: Callable[[str], Tuple[str, Optional[str], str]],
    now_utc: Optional[datetime] = None,
) -> List[Dict[str, Any]]:
    """Deterministic, pure router. Given raw Motive presence events and a
    snapshot of Verified ``operational_locations`` keyed by motive
    geofence id, returns normalized operational events.

    ``asset_label_resolver(actor_key)`` returns
    ``(label, masci_equipment_id, asset_kind)``.

    Idempotent — calling twice with the same inputs produces the same
    output list with identical ``id`` fields.
    """
    now_utc = now_utc or _now_utc()
    routed: List[Dict[str, Any]] = []

    # Group by actor
    by_actor: Dict[str, List[Dict[str, Any]]] = {}
    for ev in presence_events:
        key = _event_actor_key(ev)
        if not key:
            continue
        by_actor.setdefault(key, []).append(ev)

    for actor_key, evs in by_actor.items():
        evs.sort(key=lambda e: _parse_iso(e.get("event_at")) or now_utc)

        label, masci_id, asset_kind = asset_label_resolver(actor_key)
        veh_id = actor_key.split(":", 1)[1] if actor_key.startswith("vehicle:") else None
        ast_id = actor_key.split(":", 1)[1] if actor_key.startswith("equipment:") else None

        # M-2-3 Deduplication: collapse contiguous enter (or contiguous
        # exit) events for the same geofence into a single transition.
        # We emit ARRIVAL only when the actor's "current location"
        # changes. We emit DEPARTURE only when the actor leaves the
        # tracked geofence and we have a paired enter to compute dwell.
        current_loc_id: Optional[str] = None
        current_enter_ts: Optional[datetime] = None
        current_enter_src_id: Optional[str] = None

        for ev in evs:
            ts = _parse_iso(ev.get("event_at"))
            if not ts:
                continue
            gid = _event_geofence_id(ev)
            loc = op_locations_by_gid.get(gid) if gid else None
            location_type = (loc or {}).get("location_type") or "UNKNOWN"
            location_id = (loc or {}).get("id")
            location_name = (loc or {}).get("name") or "(unknown geofence)"
            project_number = (loc or {}).get("project_number") if location_type == "JOB" else None
            arrival_type, departure_type = LOCATION_TYPE_TO_ARRIVAL.get(
                location_type, LOCATION_TYPE_TO_ARRIVAL["UNKNOWN"]
            )

            if _is_enter(ev):
                # Dedupe: if we're already inside the same geofence,
                # skip (re-enter noise).
                if current_loc_id == gid:
                    continue
                # If we were inside a different location and never saw
                # its exit, synthesize a DEPARTURE for the previous one
                # at this timestamp (open-pair closure).
                if current_loc_id is not None and current_enter_ts is not None:
                    prev_loc = op_locations_by_gid.get(current_loc_id) if current_loc_id else None
                    prev_loc_type = (prev_loc or {}).get("location_type") or "UNKNOWN"
                    _, prev_dep_type = LOCATION_TYPE_TO_ARRIVAL.get(
                        prev_loc_type, LOCATION_TYPE_TO_ARRIVAL["UNKNOWN"]
                    )
                    dwell_min = (ts - current_enter_ts).total_seconds() / 60.0
                    conf = "HIGH" if dwell_min >= HIGH_DWELL_MIN and prev_loc_type != "UNKNOWN" else "MEDIUM"
                    if conf == "LOW":
                        pass  # never emit
                    else:
                        occurred_at_iso = ts.isoformat()
                        doc = {
                            "id": _stable_id(actor_key, occurred_at_iso,
                                             prev_dep_type, current_loc_id),
                            "asset_key": actor_key, "asset_kind": asset_kind,
                            "asset_label": label,
                            "motive_vehicle_id": veh_id,
                            "motive_asset_id": ast_id,
                            "masci_equipment_id": masci_id,
                            "occurred_at": occurred_at_iso,
                            "location_type": prev_loc_type,
                            "location_id": current_loc_id,
                            "location_name": (prev_loc or {}).get("name") or "(unknown geofence)",
                            "project_number": (prev_loc or {}).get("project_number") if prev_loc_type == "JOB" else None,
                            "event_type": prev_dep_type,
                            "confidence": conf,
                            "source_event_ids": [current_enter_src_id, ev.get("id")],
                            "dwell_minutes_so_far": int(round(dwell_min)),
                        }
                        routed.append(doc)
                # New arrival
                occurred_at_iso = ts.isoformat()
                arr_conf = "HIGH" if location_type != "UNKNOWN" else "MEDIUM"
                arr_doc = {
                    "id": _stable_id(actor_key, occurred_at_iso,
                                     arrival_type, location_id or gid),
                    "asset_key": actor_key, "asset_kind": asset_kind,
                    "asset_label": label,
                    "motive_vehicle_id": veh_id,
                    "motive_asset_id": ast_id,
                    "masci_equipment_id": masci_id,
                    "occurred_at": occurred_at_iso,
                    "location_type": location_type,
                    "location_id": location_id or gid,
                    "location_name": location_name,
                    "project_number": project_number,
                    "event_type": arrival_type,
                    "confidence": arr_conf,
                    "source_event_ids": [ev.get("id")],
                    "dwell_minutes_so_far": 0,
                }
                routed.append(arr_doc)
                current_loc_id = gid
                current_enter_ts = ts
                current_enter_src_id = ev.get("id")

            elif _is_exit(ev):
                # Dedupe: orphan exit (no matching enter) → emit a
                # departure with minimal confidence ONLY if it concerns
                # the current location we're tracking. Otherwise skip.
                if gid != current_loc_id or current_loc_id is None:
                    continue
                dwell_min = (ts - current_enter_ts).total_seconds() / 60.0 if current_enter_ts else 0.0
                conf = "HIGH" if dwell_min >= HIGH_DWELL_MIN and location_type != "UNKNOWN" else "MEDIUM"
                occurred_at_iso = ts.isoformat()
                routed.append({
                    "id": _stable_id(actor_key, occurred_at_iso,
                                     departure_type, location_id or gid),
                    "asset_key": actor_key, "asset_kind": asset_kind,
                    "asset_label": label,
                    "motive_vehicle_id": veh_id,
                    "motive_asset_id": ast_id,
                    "masci_equipment_id": masci_id,
                    "occurred_at": occurred_at_iso,
                    "location_type": location_type,
                    "location_id": location_id or gid,
                    "location_name": location_name,
                    "project_number": project_number,
                    "event_type": departure_type,
                    "confidence": conf,
                    "source_event_ids": [current_enter_src_id, ev.get("id")],
                    "dwell_minutes_so_far": int(round(max(0.0, dwell_min))),
                })
                current_loc_id = None
                current_enter_ts = None
                current_enter_src_id = None

    return routed


# ── Router builder ────────────────────────────────────────────────────
def build_operational_events_router(db, require_admin_dep: Callable) -> APIRouter:
    router = APIRouter(prefix="/api", tags=["operational-events"])

    async def _load_op_locations() -> Dict[str, Dict[str, Any]]:
        """All Verified op_locations keyed by motive_geofence_id."""
        out: Dict[str, Dict[str, Any]] = {}
        async for loc in db.operational_locations.find({
            "geocode_status": "Verified",
            "motive_geofence_id": {"$nin": [None, ""]},
        }, LOCATION_PROJECTION):
            out[str(loc["motive_geofence_id"])] = loc
        return out

    async def _load_any_locations() -> Dict[str, Dict[str, Any]]:
        out: Dict[str, Dict[str, Any]] = {}
        async for loc in db.operational_locations.find({
            "motive_geofence_id": {"$nin": [None, ""]},
        }, LOCATION_PROJECTION):
            out[str(loc["motive_geofence_id"])] = loc
        return out

    async def _build_resolver():
        veh_cache: Dict[str, Dict[str, Any]] = {}
        ast_cache: Dict[str, Dict[str, Any]] = {}
        async for d in db.asset_mappings.find({"provider": "motive"}, ASSET_MAPPING_PROJECTION):
            m = d.get("motive") or {}
            if d.get("asset_kind") == "vehicle" and m.get("vehicle_id"):
                veh_cache[str(m["vehicle_id"])] = d
            elif d.get("asset_kind") == "equipment" and m.get("asset_id"):
                ast_cache[str(m["asset_id"])] = d

        def resolve(actor_key: str) -> Tuple[str, Optional[str], str]:
            try:
                kind, rid = actor_key.split(":", 1)
            except ValueError:
                return (actor_key, None, "unknown")
            if kind == "vehicle":
                d = veh_cache.get(rid)
                if d:
                    m = d.get("motive") or {}
                    parts = [str(p).strip() for p in
                             [m.get("year"), m.get("make"), m.get("model")] if p]
                    return (" ".join(parts).strip() or f"Vehicle {rid}",
                            d.get("masci_equipment_id"), "vehicle")
                return (f"Vehicle {rid}", None, "vehicle")
            d = ast_cache.get(rid)
            if d:
                m = d.get("motive") or {}
                return ((m.get("name") or "").strip() or f"Asset {rid}",
                        d.get("masci_equipment_id"), "equipment")
            return (f"Asset {rid}", None, "equipment")
        return resolve

    async def _ensure_indexes():
        try:
            await db.operational_events.create_index("id", unique=True)
            await db.operational_events.create_index("asset_key")
            await db.operational_events.create_index("occurred_at")
            await db.operational_events.create_index("project_number", sparse=True)
            await db.operational_events.create_index("event_type")
            await db.operational_events.create_index("location_type")
            await db.operational_events.create_index([("asset_key", 1), ("occurred_at", -1)])
            await db.operational_events.create_index([("project_number", 1), ("location_type", 1), ("occurred_at", 1)])
        except Exception as e:  # noqa: BLE001
            logger.warning(f"[m2 indexes] {e}")

    # ── ADMIN — materialize a window into operational_events ──────────
    @router.post("/admin/operational-events/materialize",
                 dependencies=[Depends(require_admin_dep)])
    async def materialize(
        request: Request,
        start: Optional[str] = Query(default=None),
        end: Optional[str] = Query(default=None),
        x_admin_token: Optional[str] = Header(default=None),
    ):
        """Run the router over `[start, end)` (ISO timestamps) or the
        full window if unset. Idempotent on stable id."""
        from lib.trust_spine import (  # noqa: PLC0415
            STAGE_AUDIT_WRITTEN,
            STAGE_COMPLETED,
            STAGE_DASHBOARD_UPDATED,
            STAGE_NOTIFICATION_QUEUED,
            STAGE_RECIPIENTS_BUILT,
            STAGE_ROUTING_RESOLVED,
            STAGE_VALIDATION_COMPLETE,
            emit_record_created,
            emit_workflow_stage,
        )

        await _ensure_indexes()
        run = {
            "id": f"m2-run-{uuid.uuid4().hex}",
            "project_number": "",
            "window_start": start,
            "window_end": end,
        }
        actor = await _resolve_admin_actor(db, x_admin_token)
        correlation_id = await emit_record_created(
            db,
            workflow=M2_TRUST_WORKFLOW,
            record=run,
            module="routes.operational_events.materialize",
        )
        q: Dict[str, Any] = {"event_family": {"$in": list(PRESENCE_EVENTS)}}
        if start:
            q.setdefault("event_at", {})["$gte"] = start
        if end:
            q.setdefault("event_at", {})["$lt"] = end
        try:
            await emit_workflow_stage(
                db,
                workflow=M2_TRUST_WORKFLOW,
                stage=STAGE_VALIDATION_COMPLETE,
                record=run,
                module="routes.operational_events.materialize",
                status="ok",
                remediation="materialize window accepted for deterministic normalization",
            )

            events: List[Dict[str, Any]] = []
            async for ev in db.motive_events.find(q, MOTIVE_EVENT_PROJECTION):
                events.append(ev)
            op_by_gid = await _load_op_locations()
            resolver = await _build_resolver()
            routed = route_motive_events(events, op_by_gid, resolver)

            await emit_workflow_stage(
                db,
                workflow=M2_TRUST_WORKFLOW,
                stage=STAGE_ROUTING_RESOLVED,
                record=run,
                module="routes.operational_events.materialize",
                status="ok",
                remediation=f"routed {len(routed)} normalized events from {len(events)} raw presence events",
            )

            upserted, skipped = 0, 0
            for doc in routed:
                try:
                    _validate_doc({**doc, "created_at": "x", "updated_at": "x"})
                except ValueError as ve:  # constitutional fail
                    logger.error(f"[m2 storage gate] {ve}")
                    skipped += 1
                    continue
                now = _now_utc().isoformat()
                await db.operational_events.update_one(
                    {"id": doc["id"]},
                    {"$set": {**doc, "updated_at": now},
                     "$setOnInsert": {"created_at": now}},
                    upsert=True,
                )
                upserted += 1

            unknown_count = sum(1 for d in routed if d["location_type"] == "UNKNOWN")
            audit_ok = await _write_materialize_audit(
                db,
                run_id=run["id"],
                correlation_id=correlation_id,
                actor=actor,
                start=start,
                end=end,
                events_considered=len(events),
                routed=len(routed),
                upserted=upserted,
                skipped=skipped,
                unknown_count=unknown_count,
                request_path=str(request.url.path),
            )

            await emit_workflow_stage(
                db,
                workflow=M2_TRUST_WORKFLOW,
                stage=STAGE_RECIPIENTS_BUILT,
                record=run,
                module="routes.operational_events.materialize",
                status="skipped",
                failure_reason="no notification recipients for operational event materialization",
                remediation="notification sequencing is not part of the Family 3C materialization contract",
            )
            await emit_workflow_stage(
                db,
                workflow=M2_TRUST_WORKFLOW,
                stage=STAGE_NOTIFICATION_QUEUED,
                record=run,
                module="routes.operational_events.materialize",
                status="skipped",
                failure_reason="no notification fanout for operational event materialization",
                remediation="operational event materialization persists canonical rows and direct read models only",
            )
            await emit_workflow_stage(
                db,
                workflow=M2_TRUST_WORKFLOW,
                stage=STAGE_AUDIT_WRITTEN,
                record=run,
                module="routes.operational_events.materialize",
                status="ok" if audit_ok else "failed",
                failure_reason=None if audit_ok else "append-only audit_events write failed",
                remediation=None if audit_ok else "inspect audit_events write path and Mongo logs for the materialization run",
            )
            await emit_workflow_stage(
                db,
                workflow=M2_TRUST_WORKFLOW,
                stage=STAGE_DASHBOARD_UPDATED,
                record=run,
                module="routes.operational_events.materialize",
                status="ok",
                remediation="admin dashboard and direct consumers now read the refreshed canonical operational events",
            )
            await emit_workflow_stage(
                db,
                workflow=M2_TRUST_WORKFLOW,
                stage=STAGE_COMPLETED,
                record=run,
                module="routes.operational_events.materialize",
                status="ok",
            )

            return {
                "ok": True,
                "events_considered": len(events),
                "routed": len(routed),
                "upserted": upserted,
                "skipped_by_storage_gate": skipped,
                "unknown_location_events": unknown_count,
            }
        except Exception as exc:  # noqa: BLE001
            await emit_workflow_stage(
                db,
                workflow=M2_TRUST_WORKFLOW,
                stage=STAGE_COMPLETED,
                record=run,
                module="routes.operational_events.materialize",
                status="failed",
                failure_reason=type(exc).__name__,
                remediation="inspect routes.operational_events.materialize and MongoDB write logs for the failing materialization window",
            )
            raise

    # ── ADMIN — Operational Trust Audit (M-2 audit) ───────────────────
    @router.get("/admin/operational-events/audit",
                dependencies=[Depends(require_admin_dep)])
    async def audit():
        pres = {"event_family": {"$in": list(PRESENCE_EVENTS)}}
        events: List[Dict[str, Any]] = []
        async for ev in db.motive_events.find(pres, MOTIVE_EVENT_PROJECTION):
            events.append(ev)

        actor_pairs: Set[Tuple[str, str]] = set()
        observed_days_set: Set[str] = set()
        ev_gids: Set[str] = set()
        bycat: Dict[str, int] = {}
        latencies_ms: List[float] = []
        geofence_counter: Counter[str] = Counter()

        op_by_gid = await _load_op_locations()
        any_op = await _load_any_locations()
        for ev in events:
            raw = ev.get("raw") or {}
            veh_id = str(ev.get("vehicle_id") or ((raw.get("vehicle") or {}).get("id") or ""))
            ast_id = str(ev.get("asset_id") or ((raw.get("asset") or {}).get("id") or ""))
            actor_pairs.add((veh_id, ast_id))

            event_at = str(ev.get("event_at") or "")
            if len(event_at) >= 10:
                observed_days_set.add(event_at[:10])

            gid = _event_geofence_id(ev)
            if not gid:
                continue
            ev_gids.add(gid)
            geofence_counter[gid] += 1
            loc = any_op.get(gid)
            cat = (loc or {}).get("location_type") or "UNKNOWN"
            bycat[cat] = bycat.get(cat, 0) + 1
            if len(latencies_ms) < 50:
                et = _parse_iso((raw.get("event_time")))
                ca = _parse_iso(ev.get("created_at"))
                if et and ca:
                    latencies_ms.append((ca - et).total_seconds() * 1000.0)

        assets_emitting = len(actor_pairs)
        total_presence = len(events)
        observed_days = len(observed_days_set)
        avg_per_day = round(total_presence / max(1, observed_days), 2)
        unmatched = len(ev_gids - set(any_op.keys()))

        resolver = await _build_resolver()
        routed = route_motive_events(events, op_by_gid, resolver)
        dedupe_savings = max(0, len(events) - len(routed))

        # Q6 — asset_mappings without masci_equipment_id
        total_assets = await db.asset_mappings.count_documents({})
        mapped = await db.asset_mappings.count_documents(
            {"masci_equipment_id": {"$nin": [None, ""]}}
        )

        avg_latency_ms = round(sum(latencies_ms) / len(latencies_ms), 1) if latencies_ms else None

        # Q8 — top fences
        top_named = []
        for gid, count in geofence_counter.most_common(5):
            loc = any_op.get(gid)
            name = (loc or {}).get("name")
            if not name:
                gf = await db.motive_geofences.find_one({"motive_geofence_id": gid}, {"_id": 0, "name": 1})
                name = (gf or {}).get("name") if gf else "(unmapped)"
            top_named.append({"motive_geofence_id": gid, "events": count,
                              "name": name,
                              "location_type": (loc or {}).get("location_type") or "UNKNOWN"})

        # Q10 — accuracy estimate: % of routed events whose location is
        # NOT UNKNOWN.
        if routed:
            known = sum(1 for d in routed if d["location_type"] != "UNKNOWN")
            accuracy_pct = round(100.0 * known / len(routed), 1)
        else:
            accuracy_pct = 0.0

        # Lowest-confidence category — categories where >50% confidence
        # is MEDIUM
        cat_conf: Dict[str, Dict[str, int]] = {}
        for d in routed:
            cat = d["location_type"]
            slot = cat_conf.setdefault(cat, {"HIGH": 0, "MEDIUM": 0})
            slot[d["confidence"]] = slot.get(d["confidence"], 0) + 1
        lowest_conf_cat = None
        worst_share = 1.0
        for cat, counts in cat_conf.items():
            tot = sum(counts.values())
            if tot < 1:
                continue
            share_high = counts.get("HIGH", 0) / tot
            if share_high < worst_share:
                worst_share = share_high
                lowest_conf_cat = cat

        return {
            "ok": True,
            "answers": {
                "q1_assets_generating_events": assets_emitting,
                "q2_presence_events_total": total_presence,
                "q2_observed_days": observed_days,
                "q2_avg_events_per_day": avg_per_day,
                "q3_distinct_geofences_in_events": len(ev_gids),
                "q3_unmatched_geofences": unmatched,
                "q4_discarded_events": dedupe_savings,
                "q5_duplicates_collapsed": dedupe_savings,
                "q6_asset_mappings_total": total_assets,
                "q6_asset_mappings_masci_mapped": mapped,
                "q6_asset_mappings_unmapped": total_assets - mapped,
                "q7_avg_webhook_latency_ms": avg_latency_ms,
                "q8_top_geofences": top_named,
                "q9_event_distribution_by_category": bycat,
                "q9_lowest_confidence_category": lowest_conf_cat,
                "q10_accuracy_pct_estimate": accuracy_pct,
            },
        }

    # ── ADMIN — Operations dashboard counts (M-2-7) ───────────────────
    @router.get("/admin/operational-events/dashboard",
                dependencies=[Depends(require_admin_dep)])
    async def dashboard(
        date: Optional[str] = Query(default=None, pattern=r"^\d{4}-\d{2}-\d{2}$"),
    ):
        """Counts of distinct assets currently 'at' each category, where
        'at' = last operational_event for that asset is an ARRIVAL of
        that type."""
        # Per-asset latest event
        pipe: List[Dict[str, Any]] = []
        if date:
            pipe.append({"$match": {"occurred_at": {"$lte": f"{date}T23:59:59+00:00"}}})
        pipe.extend([
            {"$sort": {"asset_key": 1, "occurred_at": -1}},
            {"$group": {
                "_id": "$asset_key",
                "last": {"$first": "$$ROOT"},
            }},
        ])
        latest = await db.operational_events.aggregate(pipe).to_list(length=None)
        buckets: Dict[str, int] = {
            "Equipment On Projects": 0,
            "Equipment At Plants": 0,
            "Equipment At Yard": 0,
            "Equipment At Shop": 0,
            "Equipment At Disposal Sites": 0,
            "Equipment At Pits": 0,
            "Unknown Location": 0,
        }
        for r in latest:
            ev = r["last"]
            et = (ev.get("event_type") or "")
            lt = (ev.get("location_type") or "UNKNOWN")
            if not et.endswith("_ARRIVAL"):
                continue  # last action was a departure → not at any location
            if lt == "JOB":
                buckets["Equipment On Projects"] += 1
            elif lt in ("ASPHALT_PLANT", "CONCRETE_PLANT"):
                buckets["Equipment At Plants"] += 1
            elif lt == "PIT":
                buckets["Equipment At Pits"] += 1
            elif lt == "YARD":
                buckets["Equipment At Yard"] += 1
            elif lt == "SHOP":
                buckets["Equipment At Shop"] += 1
            elif lt == "DISPOSAL_SITE":
                buckets["Equipment At Disposal Sites"] += 1
            else:
                buckets["Unknown Location"] += 1
        return {"ok": True, "as_of": date or _now_utc().isoformat(),
                "buckets": buckets,
                "total_assets_with_state": len(latest)}

    # ── PUBLIC — Daily Report MOTIVE VERIFICATION (M-2-5) ─────────────
    @router.get("/operational-events/project-day/{project_number}/{date}")
    async def project_day(
        project_number: str = Path(..., min_length=1, max_length=64),
        date: str = Path(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    ):
        """List per-asset arrival/departure summaries for one project on
        one UTC day. Read-only. Used by the Daily Report MOTIVE
        VERIFICATION pane."""
        try:
            day = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
        except ValueError as e:
            raise HTTPException(400, f"Bad date: {e}") from e
        day_start = day.isoformat()
        day_end = (day + timedelta(days=1)).isoformat()

        rows: List[Dict[str, Any]] = []
        async for ev in db.operational_events.find({
            "project_number": project_number,
            "location_type": "JOB",
            "occurred_at": {"$gte": day_start, "$lt": day_end},
        }, PUBLIC_EVENT_PROJECTION).sort("occurred_at", 1):
            rows.append(ev)

        # Collapse per-asset to first arrival + last departure / still-on-site
        per_asset: Dict[str, Dict[str, Any]] = {}
        for ev in rows:
            ak = ev["asset_key"]
            slot = per_asset.setdefault(ak, {
                "asset_key": ak, "asset_kind": ev.get("asset_kind"),
                "asset_label": ev.get("asset_label"),
                "masci_equipment_id": ev.get("masci_equipment_id"),
                "first_seen": None, "last_seen": None,
                "still_on_site": False,
            })
            t = (ev.get("occurred_at") or "")[11:16]  # HH:MM
            if ev["event_type"] == "PROJECT_ARRIVAL":
                if slot["first_seen"] is None or t < slot["first_seen"]:
                    slot["first_seen"] = t
                slot["still_on_site"] = True
            elif ev["event_type"] == "PROJECT_DEPARTURE":
                if slot["last_seen"] is None or t > slot["last_seen"]:
                    slot["last_seen"] = t
                slot["still_on_site"] = False
        out = sorted(per_asset.values(),
                     key=lambda r: r.get("first_seen") or "99:99")
        return {"ok": True, "project_number": project_number, "date": date,
                "assets": out, "total_events": len(rows)}

    # ── PUBLIC — Per-asset timeline (M-2-4) ───────────────────────────
    @router.get("/operational-events/timeline/{detection_key}/{date}")
    async def timeline(
        detection_key: str = Path(..., min_length=1, max_length=128),
        date: str = Path(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    ):
        try:
            day = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
        except ValueError as e:
            raise HTTPException(400, f"Bad date: {e}") from e
        day_start = day.isoformat()
        day_end = (day + timedelta(days=1)).isoformat()
        out: List[Dict[str, Any]] = []
        async for ev in db.operational_events.find({
            "asset_key": detection_key,
            "occurred_at": {"$gte": day_start, "$lt": day_end},
        }, PUBLIC_EVENT_PROJECTION).sort("occurred_at", 1):
            out.append(ev)
        return {"ok": True, "detection_key": detection_key, "date": date,
                "events": out}

    # ── PUBLIC — Dispatch verification chip (M-2-6) ───────────────────
    @router.get("/operational-events/dispatch-status/{asset_key}")
    async def dispatch_status(asset_key: str = Path(...)):
        """Returns the current (latest) state for an asset. Visibility
        only. Never modifies dispatch assignments."""
        ev = await db.operational_events.find_one(
            {"asset_key": asset_key},
            PUBLIC_EVENT_PROJECTION,
            sort=[("occurred_at", -1)],
        )
        if not ev:
            return {"ok": True, "asset_key": asset_key, "state": "UNKNOWN",
                    "detail": None}
        et = ev.get("event_type") or ""
        state = ("ARRIVED" if et.endswith("_ARRIVAL")
                 else "DEPARTED" if et.endswith("_DEPARTURE")
                 else "EN_ROUTE")
        return {"ok": True, "asset_key": asset_key, "state": state,
                "event_type": et,
                "location_type": ev.get("location_type"),
                "location_name": ev.get("location_name"),
                "occurred_at": ev.get("occurred_at"),
                "confidence": ev.get("confidence")}

    return router


__all__ = [
    "build_operational_events_router",
    "route_motive_events",
    "LOCATION_TYPE_TO_ARRIVAL",
    "PRESENCE_EVENTS",
    "HIGH_DWELL_MIN",
    "ALLOWED_EVENT_FIELDS",
    "FORBIDDEN_KEYWORDS",
]
