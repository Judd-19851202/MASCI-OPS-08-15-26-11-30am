"""
routes/equipment_detection.py · M-DR-1 · Equipment Auto-Discovery.

Surface what Motive observed at a project on a given day. Motive
SUGGESTS — foreman VERIFIES — foreman AUTHORS. This module does NOT
mutate any Daily Report. It is a read-only suggestion API.

Doctrine: MOTIVE_001_CONSTITUTIONAL_AUDIT.md §E + M3_GEOCODE_FOUNDATION
(uses Verified geofence linkages as the only source of project↔fence
truth). Drive-through false-positives suppressed via the 5-minute dwell
gate per audit §E.4.

Confidence bands (per M-DR-1 brief MDR1-4):
  HIGH    — inside a Verified project geofence with dwell ≥ 5 minutes
  MEDIUM  — inside a Verified geofence but dwell < 5 minutes
            (drive-through suspect; foreman should still see it)
  LOW     — NEVER auto-presented. Reserved for proximity/near-geofence
            heuristics that would require map context to verify. We
            store nothing diagnostic in this module (no side effects).

Mounted at /api/equipment-detection/{project_number}/{date} — read-only.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, Path

logger = logging.getLogger(__name__)

# Doctrinal dwell floor (audit §E.4). Anything shorter is a suspected
# drive-through and downgraded to MEDIUM.
HIGH_DWELL_MIN = 5

# Event families we consider for presence detection.
PRESENCE_EVENTS = {
    "geofence_enter", "geofence_exit",            # vehicles
    "asset_geofence_enter", "asset_geofence_exit",  # asset gateways
}


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


def _hhmm(dt: Optional[datetime]) -> Optional[str]:
    return dt.strftime("%H:%M") if dt else None


def _event_geofence_id(ev: Dict[str, Any]) -> Optional[str]:
    """Return the str geofence id encoded inside the event payload."""
    raw = ev.get("raw") or {}
    gf = raw.get("geofence") or {}
    gid = gf.get("id")
    return str(gid) if gid is not None and gid != "" else None


def _event_actor_key(ev: Dict[str, Any]) -> Optional[str]:
    """Stable detection_key for the asset acting in this event.
    Vehicles: vehicle:<motive_vehicle_id>
    Equipment: equipment:<motive_asset_id>"""
    raw = ev.get("raw") or {}
    vehicle = raw.get("vehicle") or {}
    asset = raw.get("asset") or {}
    if vehicle.get("id"):
        return f"vehicle:{vehicle['id']}"
    if asset.get("id"):
        return f"equipment:{asset['id']}"
    # Fallback to top-level (poll-sourced events)
    if ev.get("vehicle_id"):
        return f"vehicle:{ev['vehicle_id']}"
    if ev.get("asset_id"):
        return f"equipment:{ev['asset_id']}"
    return None


def _is_enter(ev: Dict[str, Any]) -> bool:
    f = ev.get("event_family") or ev.get("event_kind") or ""
    return f.endswith("_enter")


def _is_exit(ev: Dict[str, Any]) -> bool:
    f = ev.get("event_family") or ev.get("event_kind") or ""
    return f.endswith("_exit")


def _confidence(total_minutes: float, has_verified_geofence: bool) -> str:
    """Apply MDR1-4 banding rules."""
    if not has_verified_geofence:
        return "LOW"
    if total_minutes >= HIGH_DWELL_MIN:
        return "HIGH"
    return "MEDIUM"


def build_equipment_detection_router(db) -> APIRouter:
    router = APIRouter(prefix="/api", tags=["equipment-detection"])

    @router.get("/equipment-detection/{project_number}/{date}")
    async def detect(
        project_number: str = Path(..., min_length=1, max_length=64),
        date: str = Path(..., pattern=r"^\d{4}-\d{2}-\d{2}$"),
    ):
        """Return equipment Motive observed at ``project_number`` on
        ``date`` (UTC day window). No DB writes. No notifications.
        No OA events. No Daily Report mutation."""
        # 0. Validate date first (fail-fast on impossible months/days).
        try:
            day_start = datetime.fromisoformat(date).replace(tzinfo=timezone.utc)
        except ValueError as e:
            raise HTTPException(400, f"Bad date: {e}") from e
        day_end = day_start + timedelta(days=1)
        day_start_s = day_start.isoformat()
        day_end_s = day_end.isoformat()

        # 1. Find the project's Verified geofence linkages (M-3 output).
        verified_locations: List[Dict[str, Any]] = []
        async for loc in db.operational_locations.find({
            "project_number": project_number,
            "geocode_status": "Verified",
        }):
            loc.pop("_id", None)
            verified_locations.append(loc)

        # If no verified geofences, return an empty payload that explains
        # why so the UI can render a helpful "no detection — link a
        # geofence first" hint.
        if not verified_locations:
            return {
                "ok": True,
                "project_number": project_number,
                "date": date,
                "detections": [],
                "verified_geofences": 0,
                "no_detection_reason": "no_verified_geofence",
            }

        verified_gids = {loc.get("motive_geofence_id"): loc
                        for loc in verified_locations
                        if loc.get("motive_geofence_id")}
        if not verified_gids:
            return {
                "ok": True,
                "project_number": project_number,
                "date": date,
                "detections": [],
                "verified_geofences": len(verified_locations),
                "no_detection_reason": "no_motive_geofence_id_linked",
            }

        # 2. Day window in UTC (validated above).

        # 3. Pull events in window for our geofences.
        # event_at is stored as ISO string in this codebase (verified by
        # the schema audit).
        events: List[Dict[str, Any]] = []
        async for ev in db.motive_events.find({
            "event_family": {"$in": list(PRESENCE_EVENTS)},
            "event_at": {"$gte": day_start_s, "$lt": day_end_s},
        }):
            gid = _event_geofence_id(ev)
            if gid and gid in verified_gids:
                ev.pop("_id", None)
                events.append(ev)

        # 4. Group events per actor (vehicle or equipment).
        grouped: Dict[str, List[Dict[str, Any]]] = {}
        for ev in events:
            key = _event_actor_key(ev)
            if not key:
                continue
            grouped.setdefault(key, []).append(ev)

        # 5. Compute dwell + collect metadata per actor.
        now_utc = datetime.now(timezone.utc)
        detections: List[Dict[str, Any]] = []

        for actor_key, evs in grouped.items():
            evs.sort(key=lambda e: _parse_iso(e.get("event_at")) or now_utc)
            # Pair enters → exits.
            total_min = 0.0
            first_seen: Optional[datetime] = None
            last_seen: Optional[datetime] = None
            pairs: List[Dict[str, Any]] = []
            i = 0
            while i < len(evs):
                ev = evs[i]
                ts = _parse_iso(ev.get("event_at"))
                if not ts:
                    i += 1
                    continue
                if _is_enter(ev):
                    first_seen = first_seen or ts
                    # Look ahead for the next exit for this actor.
                    j = i + 1
                    exit_ts: Optional[datetime] = None
                    while j < len(evs):
                        if _is_exit(evs[j]):
                            exit_ts = _parse_iso(evs[j].get("event_at"))
                            break
                        j += 1
                    if exit_ts:
                        diff = (exit_ts - ts).total_seconds() / 60.0
                        total_min += max(0.0, diff)
                        last_seen = max(last_seen, exit_ts) if last_seen else exit_ts
                        pairs.append({"enter": ts.isoformat(),
                                      "exit": exit_ts.isoformat(),
                                      "minutes": round(diff, 1)})
                        # Resume search past this pair
                        i = j + 1
                        continue
                    # Open enter (still on site as of "now")
                    open_diff = (now_utc - ts).total_seconds() / 60.0
                    total_min += max(0.0, min(open_diff, (day_end - day_start).total_seconds() / 60.0))
                    last_seen = max(last_seen, now_utc) if last_seen else now_utc
                    pairs.append({"enter": ts.isoformat(),
                                  "exit": None,
                                  "minutes": round(open_diff, 1),
                                  "still_on_site": True})
                    break  # No more enters processed for this actor
                elif _is_exit(ev):
                    # Exit without a same-day enter → leftover from
                    # yesterday; do not infer presence.
                    last_seen = max(last_seen, ts) if last_seen else ts
                    i += 1
                else:
                    i += 1

            if total_min <= 0 and not first_seen:
                continue  # nothing observed

            # 6. Resolve actor → human-readable label via asset_mappings.
            kind, raw_id = actor_key.split(":", 1) if ":" in actor_key else ("", "")
            label = actor_key
            masci_equipment_id: Optional[str] = None
            mapping_doc: Optional[Dict[str, Any]] = None
            if kind == "vehicle":
                mapping_doc = await db.asset_mappings.find_one({
                    "provider": "motive",
                    "asset_kind": "vehicle",
                    "motive.vehicle_id": raw_id,
                })
                if mapping_doc:
                    m = mapping_doc.get("motive") or {}
                    parts = [str(p).strip() for p in
                             [m.get("year"), m.get("make"), m.get("model")]
                             if p]
                    label = " ".join(parts).strip() or f"Vehicle {raw_id}"
                    masci_equipment_id = mapping_doc.get("masci_equipment_id")
            elif kind == "equipment":
                mapping_doc = await db.asset_mappings.find_one({
                    "provider": "motive",
                    "asset_kind": "equipment",
                    "motive.asset_id": raw_id,
                })
                if mapping_doc:
                    m = mapping_doc.get("motive") or {}
                    label = (m.get("name") or "").strip() or f"Asset {raw_id}"
                    masci_equipment_id = mapping_doc.get("masci_equipment_id")
                else:
                    # Fall back to the event's asset.name if no mapping.
                    for ev in evs:
                        a = (ev.get("raw") or {}).get("asset") or {}
                        if a.get("name"):
                            label = a["name"]
                            break

            # If we still couldn't resolve a label, fall back to actor key.
            if not label or label == actor_key:
                label = actor_key.replace(":", " ").title()

            # 7. Pick the (most-frequent) geofence as the attribution.
            gid_counts: Dict[str, int] = {}
            for ev in evs:
                g = _event_geofence_id(ev)
                if g:
                    gid_counts[g] = gid_counts.get(g, 0) + 1
            top_gid = max(gid_counts, key=gid_counts.get) if gid_counts else None
            top_loc = verified_gids.get(top_gid) if top_gid else None

            conf = _confidence(total_min, has_verified_geofence=bool(top_gid))

            # MDR1-4 NEVER auto-presents LOW. If we somehow ended up LOW
            # despite being inside a verified fence, gate it out.
            if conf == "LOW":
                continue

            detections.append({
                "detection_key": actor_key,
                "label": label,
                "asset_kind": kind,
                "motive_vehicle_id": raw_id if kind == "vehicle" else None,
                "motive_asset_id": raw_id if kind == "equipment" else None,
                "masci_equipment_id": masci_equipment_id,
                "first_seen": _hhmm(first_seen),
                "last_seen": _hhmm(last_seen),
                "dwell_minutes": int(round(total_min)),
                "confidence": conf,
                "geofence": ({"id": top_gid, "name": (top_loc or {}).get("name")}
                             if top_loc else None),
                "pairs": pairs,
                "source": "motive",
            })

        # 8. Sort: HIGH first, then by first_seen ascending.
        order = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}
        detections.sort(key=lambda d: (order.get(d["confidence"], 9),
                                       d.get("first_seen") or "99:99"))

        return {
            "ok": True,
            "project_number": project_number,
            "date": date,
            "detections": detections,
            "verified_geofences": len(verified_locations),
            "events_considered": len(events),
        }

    return router


__all__ = ["build_equipment_detection_router"]
