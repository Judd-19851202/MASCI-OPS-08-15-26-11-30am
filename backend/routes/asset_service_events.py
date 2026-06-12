"""Track 13.26 · Phase 3 · Asset Service Event Backbone (DERIVED).

Single read endpoint that composes asset history across the six live
source collections — pre-op + DVIR, defect lifecycle, dispatch
attachments, Motive presence, material movement haul cycles, and
asset transfers — into one chronological per-unit timeline.

Doctrine
--------
* TRACK_13_18_MATERIAL_MOVEMENT_LEDGER_CERTIFICATION_AND_ARCHITECTURE.md
* TRACK_13_19_MATERIAL_MOVEMENT_LEDGER_PHASE_A_PROOF_JOIN.md
* TRACK_13_25_ASSET_CARE_SERVICE_ARCHITECTURE_CERTIFICATION.md
* TRACK_13_26A_ASSET_EVENT_SOURCE_CERTIFICATION.md

Hard rules honored
------------------
* NO new collection · NO writes · NO persistence · NO background jobs.
* Read-only over `equipment_inspections`, `fleet_defects`, `fleet_audit`,
  `operational_attachments`, `operational_events`, `haul_cycles`,
  `asset_transfers`. Future event sources surface as `unavailable_event_types`
  metadata until they exist (`pm`, `fuel`, `lube`, `grease`, `maintainx`).
* MaintainX demo data is NEVER consumed. Honest empty placeholder only.
* Date-range capped at 90 days (mirror Track 13.21 Haul Ledger).
* Output capped at 1000 events.
* Auth: `_require_any_fleet_portal` (Shop / Dispatch / Safety / Admin).
"""
from __future__ import annotations

import hashlib
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple

from fastapi import APIRouter, Depends, HTTPException, Path, Query

logger = logging.getLogger(__name__)


# ── Closed-set taxonomy (per Track 13.26A §4.2 / §4.3) ──────────────────
AVAILABLE_EVENT_TYPES: Tuple[str, ...] = (
    "preop", "dvir", "defect", "repair", "oos", "rts",
    "attachment", "note", "material", "inspection",
    "transfer", "presence",
)

# Future event types — surfaced as honest empty placeholders.
UNAVAILABLE_EVENT_TYPES: Tuple[str, ...] = (
    "pm", "fuel", "lube", "grease", "maintainx",
)

VALID_SOURCE_SYSTEMS: Tuple[str, ...] = (
    "equipment_inspections", "fleet_defects", "fleet_audit",
    "operational_attachments", "operational_events", "haul_cycles",
    "asset_transfers", "admin_audit_log",
)

_MAX_RANGE_DAYS = 90
_MAX_EVENTS = 1000


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_yyyymmdd(s: str) -> datetime:
    return datetime.strptime(s, "%Y-%m-%d").replace(tzinfo=timezone.utc)


def _iso_at_day_end(d: datetime) -> str:
    return (d + timedelta(days=1) - timedelta(seconds=1)).isoformat()


def _iso_at_day_start(d: datetime) -> str:
    return d.isoformat()


def _hash_id(*parts: Any) -> str:
    """Deterministic per-event id so multiple polls return the same ids."""
    s = "|".join(str(p) if p is not None else "" for p in parts)
    return hashlib.sha1(s.encode("utf-8")).hexdigest()[:16]


def _norm(s: Optional[str]) -> str:
    return (s or "").strip()


def _ci_regex(unit_number: str) -> Dict[str, str]:
    import re as _re
    return {"$regex": f"^{_re.escape(unit_number)}$", "$options": "i"}


def _coerce_iso(ts: Any) -> Optional[str]:
    """Coerce a stored timestamp into an ISO-8601 UTC string. Best-effort."""
    if not ts:
        return None
    if isinstance(ts, datetime):
        d = ts if ts.tzinfo else ts.replace(tzinfo=timezone.utc)
        return d.isoformat()
    s = str(ts).strip()
    if not s:
        return None
    return s


def _within_range(ts: Optional[str], from_iso: str, to_iso: str) -> bool:
    if not ts:
        return False
    return from_iso <= ts <= to_iso


# ── Per-source projectors ───────────────────────────────────────────────


async def _project_preop(
    db, unit_number: str, from_iso: str, to_iso: str,
) -> List[Dict[str, Any]]:
    """Project `equipment_inspections` (Pre-Op family) into events.

    Source: `routes/equipment.py:181-187`. The Pre-Op writer stores
    `equipment_unit` and `kind="pre_op"` (or absent for legacy rows).
    """
    out: List[Dict[str, Any]] = []
    query: Dict[str, Any] = {
        "equipment_unit": _ci_regex(unit_number),
        # Treat absent `kind` as legacy Pre-Op. iter251 introduced `kind="dvir"`
        # for trucks; DVIR rows live in the DVIR projector via truck_unit_number.
        "$or": [{"kind": "pre_op"}, {"kind": {"$exists": False}}, {"kind": None}],
    }
    async for d in db.equipment_inspections.find(query, {"_id": 0}).limit(_MAX_EVENTS):
        ts = _coerce_iso(d.get("created_at") or d.get("inspection_date"))
        if not _within_range(ts, from_iso, to_iso):
            continue
        fail_count = int(d.get("fail_count") or 0)
        subtype = "failed" if fail_count > 0 else "submitted"
        out.append({
            "event_id": _hash_id("preop", d.get("id"), ts),
            "event_type": "preop",
            "event_subtype": subtype,
            "asset_id": None,
            "unit_number": unit_number,
            "timestamp": ts,
            "actor_id": d.get("operator_employee_id") or None,
            "actor_name": d.get("operator_name") or None,
            "actor_role": "operator",
            "project_number": d.get("project_number") or None,
            "related_record_id": d.get("id"),
            "related_defect_id": None,
            "related_preop_id": d.get("id"),
            "related_dvir_id": None,
            "related_attachment_id": None,
            "related_work_order_id": None,
            "status_before": None,
            "status_after": None,
            "availability_before": None,
            "availability_after": "OOS" if fail_count > 0 else None,
            "notes": d.get("doc_id") or None,
            "source_system": "equipment_inspections",
        })

        # Shop sign-off, when present, emits a separate "inspection" event.
        signed_ts = _coerce_iso(d.get("shop_signed_off_at"))
        if signed_ts and _within_range(signed_ts, from_iso, to_iso):
            out.append({
                "event_id": _hash_id("preop_signoff", d.get("id"), signed_ts),
                "event_type": "inspection",
                "event_subtype": "shop_signed_off",
                "asset_id": None,
                "unit_number": unit_number,
                "timestamp": signed_ts,
                "actor_id": None,
                "actor_name": d.get("shop_signed_off_by") or None,
                "actor_role": "shop",
                "project_number": d.get("project_number") or None,
                "related_record_id": d.get("id"),
                "related_defect_id": None,
                "related_preop_id": d.get("id"),
                "related_dvir_id": None,
                "related_attachment_id": None,
                "related_work_order_id": None,
                "status_before": None,
                "status_after": None,
                "availability_before": None,
                "availability_after": None,
                "notes": None,
                "source_system": "equipment_inspections",
            })
    return out


async def _project_dvir(
    db, unit_number: str, from_iso: str, to_iso: str,
) -> List[Dict[str, Any]]:
    """Project DVIR rows (`equipment_inspections.kind="dvir"`)."""
    out: List[Dict[str, Any]] = []
    query = {
        "kind": "dvir",
        "$or": [
            {"truck_unit_number": _ci_regex(unit_number)},
            {"trailer_unit_numbers": _ci_regex(unit_number)},
        ],
    }
    async for d in db.equipment_inspections.find(query, {"_id": 0}).limit(_MAX_EVENTS):
        ts = _coerce_iso(d.get("created_at") or d.get("inspection_date"))
        if not _within_range(ts, from_iso, to_iso):
            continue
        oos = (d.get("out_of_service") or "No") == "Yes"
        fail_count = int(d.get("fail_count") or 0)
        subtype = "failed" if fail_count > 0 else "submitted"
        out.append({
            "event_id": _hash_id("dvir", d.get("id"), ts),
            "event_type": "dvir",
            "event_subtype": subtype,
            "asset_id": None,
            "unit_number": unit_number,
            "timestamp": ts,
            "actor_id": d.get("driver_employee_id") or None,
            "actor_name": d.get("driver_name") or None,
            "actor_role": "driver",
            "project_number": None,
            "related_record_id": d.get("id"),
            "related_defect_id": None,
            "related_preop_id": None,
            "related_dvir_id": d.get("id"),
            "related_attachment_id": None,
            "related_work_order_id": None,
            "status_before": None,
            "status_after": None,
            "availability_before": None,
            "availability_after": "OOS" if oos else None,
            "notes": (d.get("deficiency_notes") or None),
            "source_system": "equipment_inspections",
        })
    return out


def _defect_unit_match(defect: Dict[str, Any], unit_number: str) -> bool:
    norm = unit_number.strip().lower()
    return (
        _norm(defect.get("truck_unit_number")).lower() == norm
        or _norm(defect.get("trailer_unit_number")).lower() == norm
    )


async def _project_defect(
    db, unit_number: str, from_iso: str, to_iso: str,
) -> List[Dict[str, Any]]:
    """Project the four-state defect lifecycle into discrete events.

    For each `fleet_defects` row matching the unit, emit:
      - `defect/opened`      at reported_at
      - `defect/acknowledged` at acknowledged_at (if set)
      - `repair`              at repaired_at (if set)
      - `rts`                 at cleared_at (if set)
    plus a synthetic `oos` event when `severity == "oos"`.
    """
    out: List[Dict[str, Any]] = []
    query = {
        "$or": [
            {"truck_unit_number": _ci_regex(unit_number)},
            {"trailer_unit_number": _ci_regex(unit_number)},
        ],
    }
    async for d in db.fleet_defects.find(query, {"_id": 0}).limit(_MAX_EVENTS):
        if not _defect_unit_match(d, unit_number):
            continue
        defect_id = d.get("id")
        kind = d.get("inspection_kind") or "preop"
        severity = (d.get("severity") or "").lower()
        item = d.get("item_text") or d.get("category") or "defect"

        # opened
        reported_at = _coerce_iso(d.get("reported_at"))
        if reported_at and _within_range(reported_at, from_iso, to_iso):
            out.append({
                "event_id": _hash_id("defect_opened", defect_id, reported_at),
                "event_type": "defect",
                "event_subtype": "opened",
                "asset_id": None,
                "unit_number": unit_number,
                "timestamp": reported_at,
                "actor_id": d.get("reported_by_employee_id") or None,
                "actor_name": d.get("reported_by_name") or None,
                "actor_role": "driver" if kind == "dvir" else "operator",
                "project_number": None,
                "related_record_id": defect_id,
                "related_defect_id": defect_id,
                "related_preop_id": d.get("inspection_id") if kind == "preop" else None,
                "related_dvir_id": d.get("inspection_id") if kind == "dvir" else None,
                "related_attachment_id": None,
                "related_work_order_id": None,
                "status_before": None,
                "status_after": "open",
                "availability_before": None,
                "availability_after": "OOS" if severity == "oos" else None,
                "notes": item,
                "source_system": "fleet_defects",
            })

            if severity == "oos":
                out.append({
                    "event_id": _hash_id("oos", defect_id, reported_at),
                    "event_type": "oos",
                    "event_subtype": kind,  # preop / dvir / manual_oos
                    "asset_id": None,
                    "unit_number": unit_number,
                    "timestamp": reported_at,
                    "actor_id": d.get("reported_by_employee_id") or None,
                    "actor_name": d.get("reported_by_name") or None,
                    "actor_role": "dispatch" if kind == "manual_oos" else (
                        "driver" if kind == "dvir" else "operator"
                    ),
                    "project_number": None,
                    "related_record_id": defect_id,
                    "related_defect_id": defect_id,
                    "related_preop_id": None,
                    "related_dvir_id": None,
                    "related_attachment_id": None,
                    "related_work_order_id": None,
                    "status_before": None,
                    "status_after": None,
                    "availability_before": "available",
                    "availability_after": "OOS",
                    "notes": item,
                    "source_system": "fleet_defects",
                })

        # acknowledged
        ack_at = _coerce_iso(d.get("acknowledged_at"))
        if ack_at and _within_range(ack_at, from_iso, to_iso):
            out.append({
                "event_id": _hash_id("defect_ack", defect_id, ack_at),
                "event_type": "defect",
                "event_subtype": "acknowledged",
                "asset_id": None,
                "unit_number": unit_number,
                "timestamp": ack_at,
                "actor_id": None,
                "actor_name": d.get("acknowledged_by_name") or None,
                "actor_role": "shop",
                "project_number": None,
                "related_record_id": defect_id,
                "related_defect_id": defect_id,
                "related_preop_id": None,
                "related_dvir_id": None,
                "related_attachment_id": None,
                "related_work_order_id": None,
                "status_before": "open",
                "status_after": "acknowledged",
                "availability_before": None,
                "availability_after": None,
                "notes": item,
                "source_system": "fleet_defects",
            })

        # repaired
        rep_at = _coerce_iso(d.get("repaired_at"))
        if rep_at and _within_range(rep_at, from_iso, to_iso):
            out.append({
                "event_id": _hash_id("repair", defect_id, rep_at),
                "event_type": "repair",
                "event_subtype": "completed",
                "asset_id": None,
                "unit_number": unit_number,
                "timestamp": rep_at,
                "actor_id": None,
                "actor_name": d.get("repaired_by_name") or None,
                "actor_role": "shop",
                "project_number": None,
                "related_record_id": defect_id,
                "related_defect_id": defect_id,
                "related_preop_id": None,
                "related_dvir_id": None,
                "related_attachment_id": None,
                "related_work_order_id": None,
                "status_before": "acknowledged",
                "status_after": "repaired",
                "availability_before": "OOS",
                "availability_after": "OOS",   # RTS still required
                "notes": d.get("repair_notes") or item,
                "source_system": "fleet_defects",
            })

        # cleared (= RTS verified by Dispatch / Admin)
        cleared_at = _coerce_iso(d.get("cleared_at"))
        if cleared_at and _within_range(cleared_at, from_iso, to_iso):
            out.append({
                "event_id": _hash_id("rts", defect_id, cleared_at),
                "event_type": "rts",
                "event_subtype": "verified",
                "asset_id": None,
                "unit_number": unit_number,
                "timestamp": cleared_at,
                "actor_id": None,
                "actor_name": d.get("cleared_by_name") or None,
                "actor_role": "dispatch",
                "project_number": None,
                "related_record_id": defect_id,
                "related_defect_id": defect_id,
                "related_preop_id": None,
                "related_dvir_id": None,
                "related_attachment_id": None,
                "related_work_order_id": None,
                "status_before": "repaired",
                "status_after": "cleared",
                "availability_before": "OOS",
                "availability_after": "available",
                "notes": "returned_to_service",
                "source_system": "fleet_defects",
            })
    return out


async def _project_haul_cycles(
    db, unit_number: str, from_iso: str, to_iso: str,
) -> List[Dict[str, Any]]:
    """Project `haul_cycles` for the unit (truck_id == unit_number)."""
    out: List[Dict[str, Any]] = []
    query = {"truck_id": _ci_regex(unit_number)}
    async for d in db.haul_cycles.find(query, {"_id": 0}).limit(_MAX_EVENTS):
        ts = _coerce_iso(d.get("completed_at") or d.get("started_at"))
        if not _within_range(ts, from_iso, to_iso):
            continue
        out.append({
            "event_id": _hash_id("haul", d.get("id"), ts),
            "event_type": "material",
            "event_subtype": d.get("haul_type") or "cycle",
            "asset_id": None,
            "unit_number": unit_number,
            "timestamp": ts,
            "actor_id": None,
            "actor_name": d.get("driver_name") or None,
            "actor_role": "driver",
            "project_number": d.get("project_number") or None,
            "related_record_id": d.get("id"),
            "related_defect_id": None,
            "related_preop_id": None,
            "related_dvir_id": None,
            "related_attachment_id": None,
            "related_work_order_id": None,
            "status_before": None,
            "status_after": "completed",
            "availability_before": None,
            "availability_after": None,
            "notes": d.get("material") or None,
            "source_system": "haul_cycles",
        })
    return out


async def _project_motive_presence(
    db, unit_number: str, from_iso: str, to_iso: str,
) -> List[Dict[str, Any]]:
    """Project Motive geofence events from `operational_events`.

    Match strategy: case-insensitive on `asset_label` (M-2 stores the
    human-readable unit label here per `routes/operational_events.py`).
    """
    out: List[Dict[str, Any]] = []
    query = {"asset_label": _ci_regex(unit_number)}
    async for d in db.operational_events.find(query, {"_id": 0}).limit(_MAX_EVENTS):
        ts = _coerce_iso(d.get("occurred_at"))
        if not _within_range(ts, from_iso, to_iso):
            continue
        out.append({
            "event_id": _hash_id("presence", d.get("id"), ts),
            "event_type": "presence",
            "event_subtype": d.get("event_type"),
            "asset_id": d.get("masci_equipment_id") or None,
            "unit_number": unit_number,
            "timestamp": ts,
            "actor_id": None,
            "actor_name": None,
            "actor_role": "motive",
            "project_number": d.get("project_number") or None,
            "related_record_id": d.get("id"),
            "related_defect_id": None,
            "related_preop_id": None,
            "related_dvir_id": None,
            "related_attachment_id": None,
            "related_work_order_id": None,
            "status_before": None,
            "status_after": None,
            "availability_before": None,
            "availability_after": None,
            "notes": d.get("location_name") or None,
            "source_system": "operational_events",
        })
    return out


async def _project_transfers(
    db, unit_number: str, from_iso: str, to_iso: str,
) -> List[Dict[str, Any]]:
    """Project `asset_transfers` (TRANSFER · RETIRE · ACTIVATE)."""
    out: List[Dict[str, Any]] = []
    query = {"unit_number": _ci_regex(unit_number)}
    async for d in db.asset_transfers.find(query, {"_id": 0}).limit(_MAX_EVENTS):
        ts = _coerce_iso(d.get("created_at"))
        if not _within_range(ts, from_iso, to_iso):
            continue
        kind = (d.get("type") or "TRANSFER").lower()
        out.append({
            "event_id": _hash_id("transfer", d.get("id"), ts),
            "event_type": "transfer",
            "event_subtype": kind,
            "asset_id": d.get("equipment_id") or d.get("asset_id") or None,
            "unit_number": unit_number,
            "timestamp": ts,
            "actor_id": None,
            "actor_name": d.get("created_by") or None,
            "actor_role": "admin",
            "project_number": d.get("to_project_number") or d.get("from_project_number") or None,
            "related_record_id": d.get("id"),
            "related_defect_id": None,
            "related_preop_id": None,
            "related_dvir_id": None,
            "related_attachment_id": None,
            "related_work_order_id": None,
            "status_before": d.get("from_location") or None,
            "status_after": d.get("to_location") or None,
            "availability_before": None,
            "availability_after": None,
            "notes": d.get("reason") or None,
            "source_system": "asset_transfers",
        })
    return out


# ── Router factory ──────────────────────────────────────────────────────


def build_asset_service_events_router(
    db,
    require_any_fleet_portal_dep: Callable[..., Awaitable[Dict[str, Any]]],
) -> APIRouter:
    """Factory for the Asset Service Event Backbone router."""
    router = APIRouter(prefix="/api/assets", tags=["asset-service-events"])

    @router.get("/{unit_number}/timeline")
    async def asset_timeline(
        unit_number: str = Path(..., min_length=1, max_length=64),
        date_from: Optional[str] = Query(None, alias="from", description="YYYY-MM-DD inclusive · defaults to today − 90 days"),
        date_to: Optional[str] = Query(None, alias="to", description="YYYY-MM-DD inclusive · defaults to today"),
        event_type: Optional[str] = Query(None, description=f"Filter by event_type. One of: {','.join(AVAILABLE_EVENT_TYPES)}"),
        source_system: Optional[str] = Query(None, description=f"Filter by source_system. One of: {','.join(VALID_SOURCE_SYSTEMS)}"),
        limit: int = Query(default=500, ge=1, le=_MAX_EVENTS),
        _actor: Dict[str, Any] = Depends(require_any_fleet_portal_dep),  # noqa: ARG001
    ) -> Dict[str, Any]:
        # ── Validate filters ────────────────────────────────────────
        if event_type and event_type not in AVAILABLE_EVENT_TYPES and event_type not in UNAVAILABLE_EVENT_TYPES:
            raise HTTPException(
                422,
                f"event_type must be one of {list(AVAILABLE_EVENT_TYPES) + list(UNAVAILABLE_EVENT_TYPES)}",
            )
        if source_system and source_system not in VALID_SOURCE_SYSTEMS:
            raise HTTPException(
                422, f"source_system must be one of {list(VALID_SOURCE_SYSTEMS)}"
            )

        # ── Resolve range ───────────────────────────────────────────
        today = datetime.now(timezone.utc).replace(
            hour=0, minute=0, second=0, microsecond=0,
        )
        if date_to:
            try:
                d_to = _parse_yyyymmdd(date_to)
            except ValueError:
                raise HTTPException(422, "to must be YYYY-MM-DD")
        else:
            d_to = today

        if date_from:
            try:
                d_from = _parse_yyyymmdd(date_from)
            except ValueError:
                raise HTTPException(422, "from must be YYYY-MM-DD")
        else:
            d_from = d_to - timedelta(days=_MAX_RANGE_DAYS)

        if d_to < d_from:
            raise HTTPException(422, "to must be ≥ from")
        if (d_to - d_from).days > _MAX_RANGE_DAYS:
            raise HTTPException(
                422,
                f"Date range exceeds {_MAX_RANGE_DAYS} days · narrow the window.",
            )

        from_iso = _iso_at_day_start(d_from)
        to_iso = _iso_at_day_end(d_to)

        # ── Resolve asset (case-insensitive) ────────────────────────
        unit_clean = _norm(unit_number)
        if not unit_clean:
            raise HTTPException(422, "unit_number required")
        asset = await db.equipment_master.find_one(
            {"unit_number": _ci_regex(unit_clean)},
            {"_id": 0, "id": 1, "unit_number": 1},
        )
        asset_id = (asset or {}).get("id")
        canonical_unit = (asset or {}).get("unit_number") or unit_clean

        # ── Project events from each available source ────────────────
        all_events: List[Dict[str, Any]] = []
        # If a source_system filter is set, skip sources that don't match.
        wanted_source = source_system

        if not wanted_source or wanted_source == "equipment_inspections":
            all_events.extend(await _project_preop(db, canonical_unit, from_iso, to_iso))
            all_events.extend(await _project_dvir(db, canonical_unit, from_iso, to_iso))
        if not wanted_source or wanted_source == "fleet_defects":
            all_events.extend(await _project_defect(db, canonical_unit, from_iso, to_iso))
        if not wanted_source or wanted_source == "haul_cycles":
            all_events.extend(await _project_haul_cycles(db, canonical_unit, from_iso, to_iso))
        if not wanted_source or wanted_source == "operational_events":
            all_events.extend(await _project_motive_presence(db, canonical_unit, from_iso, to_iso))
        if not wanted_source or wanted_source == "asset_transfers":
            all_events.extend(await _project_transfers(db, canonical_unit, from_iso, to_iso))

        # Patch in asset_id where we can.
        if asset_id:
            for ev in all_events:
                if ev.get("asset_id") is None:
                    ev["asset_id"] = asset_id

        # ── Filter by event_type (post-projection) ──────────────────
        if event_type:
            all_events = [
                e for e in all_events
                if e.get("event_type") == event_type
            ]

        # ── Sort newest-first; cap to `limit` ───────────────────────
        all_events.sort(key=lambda e: e.get("timestamp") or "", reverse=True)
        if len(all_events) > limit:
            all_events = all_events[:limit]

        # ── Counts ───────────────────────────────────────────────────
        counts_by_type: Dict[str, int] = {t: 0 for t in AVAILABLE_EVENT_TYPES}
        counts_by_source: Dict[str, int] = {s: 0 for s in VALID_SOURCE_SYSTEMS}
        for e in all_events:
            t = e.get("event_type")
            if t in counts_by_type:
                counts_by_type[t] += 1
            s = e.get("source_system")
            if s in counts_by_source:
                counts_by_source[s] += 1

        # ── Honest empty placeholders for future event types ────────
        unavailable = [
            {
                "event_type": t,
                "available": False,
                "reason": _unavailable_reason(t),
                "future_track": _future_track(t),
            }
            for t in UNAVAILABLE_EVENT_TYPES
        ]

        return {
            "unit_number": canonical_unit,
            "asset_id": asset_id,
            "range": {
                "from": d_from.strftime("%Y-%m-%d"),
                "to": d_to.strftime("%Y-%m-%d"),
                "max_days": _MAX_RANGE_DAYS,
            },
            "filters": {
                "event_type": event_type,
                "source_system": source_system,
                "limit": limit,
            },
            "events": all_events,
            "counts": {
                "total": len(all_events),
                "by_event_type": counts_by_type,
                "by_source_system": counts_by_source,
            },
            "unavailable_event_types": unavailable,
            "doctrine": {
                "derived": True,
                "persistent_collection": False,
                "spec": "TRACK_13_26_ASSET_SERVICE_EVENT_BACKBONE.md",
                "certification": "TRACK_13_26A_ASSET_EVENT_SOURCE_CERTIFICATION.md",
                "generated_at": _now_iso(),
            },
        }

    return router


def _unavailable_reason(event_type: str) -> str:
    return {
        "pm": "No `pm_schedules` collection exists yet. PM lifecycle is unimplemented.",
        "fuel": "No `fuel_service_visits` collection exists yet. Fuel events unimplemented.",
        "lube": "Lube events ride on the fuel/lube visit form (not yet implemented).",
        "grease": "Grease events ride on the fuel/lube visit form (not yet implemented).",
        "maintainx": "MaintainX integration is stubbed only. `MAINTAINX_API_KEY` not configured.",
    }.get(event_type, "Future event source — not yet implemented.")


def _future_track(event_type: str) -> str:
    return {
        "pm": "Track 13.31 (PM Engine)",
        "fuel": "Track 13.29 (Fuel/Lube Job Visit Form)",
        "lube": "Track 13.29 (Fuel/Lube Job Visit Form)",
        "grease": "Track 13.29 (Fuel/Lube Job Visit Form)",
        "maintainx": "Track 13.32 (MaintainX Integration)",
    }.get(event_type, "TBD")


__all__ = [
    "build_asset_service_events_router",
    "AVAILABLE_EVENT_TYPES",
    "UNAVAILABLE_EVENT_TYPES",
    "VALID_SOURCE_SYSTEMS",
]
