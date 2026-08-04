"""Daily Job Reports routes.

Extracted from server.py 2026-04-28 (P1 refactor batch 3).

Phase V.2 · Wave-1A (2026-05-29): elite upgrade.
  - POST restored (M1 freeze partially reverted per operator authorization)
  - Structured `production[]` and `constraints[]` fields added
  - Advisory flags (RFI / Schedule) derived server-side at submit
  - Audit footer endpoint exposes SHA256 + doc_id + rendered_at
  - DELETE stays frozen (historical immutability preserved)
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
import tempfile
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, File, Form, HTTPException, Request, UploadFile
from pydantic import BaseModel, ConfigDict, Field

from lib.async_jobs import (
    complete_async_job_binary,
    create_async_job,
    fail_async_job,
    mark_async_job_processing,
)
from lib.enterprise_governance import governance_project_scope_allows, governance_project_scope_filter
from pm_auth import compute_pm_scope
from lib.synthetic_dr_filter import apply_synthetic_dr_exclusion
from services.operations_control.control_plane import ingest_daily_report_submission
from services.cost_codes.foundation import (
    FINANCIAL_FIELDS,
    load_project_assignments,
    normalize_cost_code_actual_rows,
    now_iso,
    recompute_project_progress,
)
from services.project_controls_authority import sync_crew_observation_for_report, sync_work_blocks_for_report
from lib.notification_delivery import STATUS_PENDING, delivery_contract


logger = logging.getLogger(__name__)


# ── Phase V.2 · Wave-1A · Structured production + constraints ────────


_PRODUCTION_UNITS = {
    "EA", "LF", "FT", "MI", "SF", "SY", "AC", "CY", "YD", "CF", "LB", "TON",
    "LOAD", "TRIP", "DELIVERY", "TRUCKLOAD", "ROLL_OFF", "DUMPSTER", "GAL", "L",
    "LF_PIPE", "JOINT", "SECTION", "TON_ASPHALT", "SY_MILLING", "SY_TACK",
    "CY_CONCRETE", "VALVE", "STRUCTURE", "MANHOLE", "CATCH_BASIN", "INLET", "BOX",
    "SIGN", "POLE", "DEVICE", "TREE", "STUMP", "SHRUB", "PAIR", "SET", "ROLL",
    "BUNDLE", "PALLET", "OTHER",
}
_CONSTRAINT_TYPES = {
    "weather", "utility", "survey", "material", "equipment",
    "trucking", "mot", "cei_inspection", "owner_engineer", "safety", "other",
}
# Advisory flag heuristics (deterministic · no LLM · operator-defined).
# Constraint types that often trigger an RFI candidate signal:
_RFI_CANDIDATE_TYPES = {"utility", "owner_engineer", "cei_inspection", "survey"}
# Constraint types that often correlate with schedule impact:
_SCHEDULE_IMPACT_TYPES = {"weather", "utility", "material", "equipment", "mot"}


def _draft_health_aggregation_pipeline(since_30d: datetime) -> List[Dict[str, Any]]:
    actor_identity_expr = {"$ifNull": ["$meta.actorIdentity", "__device_scope__"]}
    choice_expr = {"$ifNull": ["$meta.choice", None]}
    return [
        {
            "$match": {
                "event": {
                    "$in": [
                        "draft.write.ok",
                        "draft.write.fail",
                        "quota.warning",
                        "draft.restore.offered",
                        "draft.restore.action",
                    ]
                },
                "ts": {"$gte": since_30d},
            }
        },
        {"$sort": {"ts": -1}},
        {
            "$group": {
                "_id": {
                    "formKey": "$formKey",
                    "deviceId": "$deviceId",
                    "actorIdentity": actor_identity_expr,
                },
                "formKey": {"$first": "$formKey"},
                "deviceId": {"$first": "$deviceId"},
                "actorIdentity": {"$first": actor_identity_expr},
                "latest_event": {"$first": "$event"},
                "latest_ts": {"$first": "$ts"},
                "latest_choice": {"$first": choice_expr},
                "last_write_ok_ts": {"$max": {"$cond": [{"$eq": ["$event", "draft.write.ok"]}, "$ts", None]}},
                "last_failed_ts": {"$max": {"$cond": [{"$eq": ["$event", "draft.write.fail"]}, "$ts", None]}},
                "last_quota_ts": {"$max": {"$cond": [{"$eq": ["$event", "quota.warning"]}, "$ts", None]}},
                "last_restore_offered_ts": {"$max": {"$cond": [{"$eq": ["$event", "draft.restore.offered"]}, "$ts", None]}},
                "last_restore_ts": {
                    "$max": {
                        "$cond": [
                            {
                                "$and": [
                                    {"$eq": ["$event", "draft.restore.action"]},
                                    {"$eq": [choice_expr, "restore"]},
                                ]
                            },
                            "$ts",
                            None,
                        ]
                    }
                },
                "last_discard_ts": {
                    "$max": {
                        "$cond": [
                            {
                                "$and": [
                                    {"$eq": ["$event", "draft.restore.action"]},
                                    {"$eq": [choice_expr, "discard"]},
                                ]
                            },
                            "$ts",
                            None,
                        ]
                    }
                },
                "last_commit_ts": {
                    "$max": {
                        "$cond": [
                            {
                                "$and": [
                                    {"$eq": ["$event", "draft.restore.action"]},
                                    {"$eq": [choice_expr, "commit"]},
                                ]
                            },
                            "$ts",
                            None,
                        ]
                    }
                },
                "events_30d": {"$sum": 1},
                "legacy_actor_rows": {
                    "$sum": {
                        "$cond": [
                            {"$ifNull": ["$meta.actorIdentity", False]},
                            0,
                            1,
                        ]
                    }
                },
            }
        },
    ]


def _summarize_draft_entities(grouped_rows: List[Dict[str, Any]], *, now: datetime) -> Dict[str, Any]:
    hour_ago = now - timedelta(hours=1)
    day_ago = now - timedelta(days=1)
    buckets: Dict[str, int] = {
        "active_lt_1h": 0,
        "stale_1h_to_24h": 0,
        "abandoned_gt_24h": 0,
        "failed_last_24h": 0,
        "quota_warn_last_24h": 0,
        "restore_offered_last_24h": 0,
        "restored_last_24h": 0,
        "discarded_last_24h": 0,
        "committed_last_24h": 0,
    }
    per_form_last_24h: Dict[str, int] = {}
    distinct_entities_30d = 0
    open_entities_30d = 0
    legacy_grouped_entities_30d = 0

    def _as_dt(value: Any) -> Optional[datetime]:
        if isinstance(value, datetime):
            return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
        return None

    for row in grouped_rows:
        distinct_entities_30d += 1
        latest_event = str(row.get("latest_event") or "")
        latest_choice = str(row.get("latest_choice") or "")
        latest_ts = _as_dt(row.get("latest_ts"))
        last_write_ok_ts = _as_dt(row.get("last_write_ok_ts"))
        last_failed_ts = _as_dt(row.get("last_failed_ts"))
        last_quota_ts = _as_dt(row.get("last_quota_ts"))
        last_restore_offered_ts = _as_dt(row.get("last_restore_offered_ts"))
        last_restore_ts = _as_dt(row.get("last_restore_ts"))
        last_discard_ts = _as_dt(row.get("last_discard_ts"))
        last_commit_ts = _as_dt(row.get("last_commit_ts"))
        legacy_grouped_entities_30d += int(row.get("legacy_actor_rows") or 0) > 0

        if last_quota_ts and last_quota_ts >= day_ago:
            buckets["quota_warn_last_24h"] += 1
        if last_restore_offered_ts and last_restore_offered_ts >= day_ago:
            buckets["restore_offered_last_24h"] += 1
        if last_restore_ts and last_restore_ts >= day_ago:
            buckets["restored_last_24h"] += 1
        if last_discard_ts and last_discard_ts >= day_ago:
            buckets["discarded_last_24h"] += 1
        if last_commit_ts and last_commit_ts >= day_ago:
            buckets["committed_last_24h"] += 1
        if last_failed_ts and last_failed_ts >= day_ago and latest_event == "draft.write.fail":
            buckets["failed_last_24h"] += 1

        if latest_ts and latest_ts >= day_ago:
            form_key = str(row.get("formKey") or "unknown")
            per_form_last_24h[form_key] = per_form_last_24h.get(form_key, 0) + 1

        entity_closed = latest_event == "draft.restore.action" and latest_choice in {"commit", "discard"}
        if entity_closed or not last_write_ok_ts:
            continue
        open_entities_30d += 1
        if last_write_ok_ts >= hour_ago:
            buckets["active_lt_1h"] += 1
        elif last_write_ok_ts >= day_ago:
            buckets["stale_1h_to_24h"] += 1
        else:
            buckets["abandoned_gt_24h"] += 1

    confidence = "HIGH"
    if distinct_entities_30d == 0:
        confidence = "UNKNOWN"
    elif legacy_grouped_entities_30d > 0:
        confidence = "MEDIUM"

    return {
        "buckets": buckets,
        "per_form_last_24h": dict(sorted(per_form_last_24h.items(), key=lambda item: (-item[1], item[0]))[:20]),
        "entity_basis": {
            "primary_key": ["formKey", "deviceId", "meta.actorIdentity"],
            "legacy_fallback": "deviceId + formKey when actorIdentity is absent in historical telemetry",
            "schema_version": "draft-entity-v2",
        },
        "definitions": {
            "active_lt_1h": "open draft entity with latest successful save less than 1 hour old",
            "stale_1h_to_24h": "open draft entity with latest successful save between 1 and 24 hours old",
            "abandoned_gt_24h": "open draft entity with latest successful save older than 24 hours",
            "failed_last_24h": "draft entity whose latest observed telemetry event in the last 24 hours is draft.write.fail",
            "restored_last_24h": "draft entity restored by operator action in the last 24 hours",
            "discarded_last_24h": "draft entity explicitly discarded by operator action in the last 24 hours",
            "committed_last_24h": "draft entity explicitly committed/cleared after successful submit in the last 24 hours",
            "expired_state": "not directly observable from current telemetry schema",
        },
        "entity_confidence": confidence,
        "distinct_entities_30d": distinct_entities_30d,
        "open_entities_30d": open_entities_30d,
        "legacy_grouped_entities_30d": legacy_grouped_entities_30d,
        "limitations": [] if confidence == "HIGH" else [
            "Historical telemetry rows without meta.actorIdentity are grouped at deviceId + formKey scope and may merge same-device cross-user legacy rows.",
        ],
    }


class ProductionRow(BaseModel):
    """One structured production entry on a Daily Report.

    Additive — coexists with the legacy free-text `activities[]` field.

    TRACK 26.02 · P0 recovery:
      * `unit` widened from `Literal[...]` → `str` so the UI can post
        either canonical codes ("TON", "CY", "LF") OR field-vernacular
        labels ("Tons", "Cubic Yards", "Loads"). Normalization happens
        server-side via `_normalize_unit()` at write time.
      * `extra="forbid"` → `extra="ignore"` so UI-provided helper fields
        (`unit_snapshot`, `unit_code`, `percent_complete`,
        `activity_code`, `cost_code_snapshot`) don't 422 the whole
        payload. Unknown fields are silently dropped.
    """
    model_config = ConfigDict(extra="ignore")

    row_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""                       # what was placed/installed/poured
    quantity: float = 0.0                       # > 0 when row has substance
    unit: str = "OTHER"                         # canonical code; normalized server-side
    custom_unit_label: Optional[str] = None     # required short description when unit=OTHER
    unit_snapshot: Optional[str] = None         # UI-visible label/code kept for PDF/email parity
    unit_code: Optional[str] = None             # UI helper preserved for audit/debug parity
    station_from: Optional[str] = None          # e.g. "12+50"
    station_to: Optional[str] = None            # e.g. "13+00"
    location: Optional[str] = None              # free-text fallback for non-station jobs
    notes: Optional[str] = None                 # ≤ 280 chars · voice or text
    percent_complete: Optional[float] = None
    activity_code: Optional[str] = None
    cost_code_snapshot: Optional[str] = None


class WorkBlockRow(BaseModel):
    model_config = ConfigDict(extra="ignore")

    work_block_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    title: str = ""
    contract_id: str = ""
    phase_id: str = ""
    work_package_id: str = ""
    pay_item_id: str = ""
    customer_pay_item_number: str = ""
    cost_code: str = ""
    primary_work_type_id: str = ""
    work_type_ids: List[str] = Field(default_factory=list)
    schedule_activity_id: str = ""
    schedule_activity_name: str = ""
    installed_quantity: float = 0.0
    unit: str = ""
    location: str = ""
    work_area: str = ""
    field_notes: str = ""
    labor_entries: List[Dict[str, Any]] = Field(default_factory=list)
    equipment_entries: List[Dict[str, Any]] = Field(default_factory=list)
    material_entries: List[Dict[str, Any]] = Field(default_factory=list)
    subcontractor_entries: List[Dict[str, Any]] = Field(default_factory=list)
    constraint_entries: List[Dict[str, Any]] = Field(default_factory=list)
    photo_refs: List[str] = Field(default_factory=list)
    attachment_refs: List[str] = Field(default_factory=list)
    qaqc_refs: List[Dict[str, Any]] = Field(default_factory=list)
    safety_refs: List[Dict[str, Any]] = Field(default_factory=list)
    schedule_actual_proposal_status: str = "proposed_only"


# TRACK 26.02 · label → canonical code normalizer for production rows.
# Every entry lower-cased for a case-insensitive lookup. Anything the
# operator writes that is not in this map is preserved as-is in
# `custom_unit_label` so the PDF/email render exactly what they typed.
_UNIT_LABEL_TO_CODE = {
    "lf": "LF", "linear feet": "LF", "linear foot": "LF", "linear ft": "LF",
    "ft": "FT", "feet": "FT", "foot": "FT",
    "mi": "MI", "mile": "MI", "miles": "MI",
    "sf": "SF", "square feet": "SF", "square foot": "SF",
    "sy": "SY", "square yards": "SY", "square yard": "SY", "sq yd": "SY",
    "sq yds": "SY",
    "cy": "CY", "cubic yards": "CY", "cubic yard": "CY", "cu yd": "CY",
    "cu yds": "CY",
    "yd": "YD", "yard": "YD", "yards": "YD",
    "cf": "CF", "cubic feet": "CF", "cubic foot": "CF", "cu ft": "CF",
    "lb": "LB", "pound": "LB", "pounds": "LB",
    "ton": "TON", "tons": "TON", "tn": "TON",
    "ea": "EA", "each": "EA",
    "acre": "AC", "acres": "AC", "ac": "AC",
    "gal": "GAL", "gallons": "GAL", "gallon": "GAL",
    "l": "L", "liter": "L", "liters": "L",
    "load": "LOAD", "loads": "LOAD",
    "trip": "TRIP", "trips": "TRIP",
    "delivery": "DELIVERY", "deliveries": "DELIVERY",
    "truckload": "TRUCKLOAD", "truckloads": "TRUCKLOAD", "truck_load": "TRUCKLOAD",
    "roll_off": "ROLL_OFF", "roll off": "ROLL_OFF", "roll-off": "ROLL_OFF",
    "roll-off containers": "ROLL_OFF",
    "dumpster": "DUMPSTER", "dumpsters": "DUMPSTER",
    "lf pipe": "LF_PIPE", "lf_pipe": "LF_PIPE", "pipe": "LF_PIPE",
    "joint": "JOINT", "joints": "JOINT",
    "section": "SECTION", "sections": "SECTION",
    "ton asphalt": "TON_ASPHALT", "ton_asphalt": "TON_ASPHALT",
    "sy milling": "SY_MILLING", "sy_milling": "SY_MILLING",
    "sy tack": "SY_TACK", "sy_tack": "SY_TACK",
    "cy concrete": "CY_CONCRETE", "cy_concrete": "CY_CONCRETE",
    "valve": "VALVE", "valves": "VALVE",
    "structure": "STRUCTURE", "structures": "STRUCTURE",
    "manhole": "MANHOLE", "manholes": "MANHOLE",
    "catch basin": "CATCH_BASIN", "catch basins": "CATCH_BASIN", "catch_basin": "CATCH_BASIN",
    "inlet": "INLET", "inlets": "INLET",
    "box": "BOX", "boxes": "BOX",
    "sign": "SIGN", "signs": "SIGN",
    "pole": "POLE", "poles": "POLE",
    "device": "DEVICE", "devices": "DEVICE",
    "tree": "TREE", "trees": "TREE",
    "stump": "STUMP", "stumps": "STUMP",
    "shrub": "SHRUB", "shrubs": "SHRUB",
    "set": "SET", "sets": "SET",
    "roll": "ROLL", "rolls": "ROLL",
    "bundle": "BUNDLE", "bundles": "BUNDLE",
    "pallet": "PALLET", "pallets": "PALLET",
    "pair": "PAIR", "pairs": "PAIR",
    "other": "OTHER", "": "OTHER",
}

_CANONICAL_UNIT_CODES = set(_PRODUCTION_UNITS)


def _canonical_or_custom_unit_payload(row: Dict[str, Any]) -> Dict[str, Any]:
    raw_unit = (row.get("unit") or "").strip().upper()
    snapshot = (row.get("unit_snapshot") or "").strip()
    custom = (row.get("custom_unit_label") or "").strip()
    if raw_unit == "TRUCK_LOAD":
        raw_unit = "TRUCKLOAD"
        row["unit"] = "TRUCKLOAD"
    if raw_unit in _CANONICAL_UNIT_CODES:
        if snapshot and snapshot.upper() != raw_unit and not custom:
            if raw_unit == "OTHER":
                row["custom_unit_label"] = snapshot.replace("Other —", "").strip()
            else:
                row["custom_unit_label"] = snapshot
        return row
    if snapshot and snapshot.upper() in _CANONICAL_UNIT_CODES and not raw_unit:
        row["unit"] = snapshot.upper()
        return row
    return row


def _normalize_unit(row: Dict[str, Any]) -> Dict[str, Any]:
    """Coerce ``row.unit`` to a canonical code. Preserve the original
    label as ``custom_unit_label`` when it does not map to a canonical
    code so PDFs/emails render exactly what the operator typed.

    Idempotent — safe to call multiple times.
    """
    row = _canonical_or_custom_unit_payload(row)
    raw = (row.get("unit") or "").strip()
    if raw in _CANONICAL_UNIT_CODES:
        if raw == "OTHER":
            row["custom_unit_label"] = (row.get("custom_unit_label") or "").strip()
        return row
    key = raw.lower()
    if key in _UNIT_LABEL_TO_CODE:
        canonical = _UNIT_LABEL_TO_CODE[key]
        # If the operator typed a non-canonical variant (e.g. "Tons"),
        # preserve it as custom_unit_label so PDF/email keep the
        # operator's word choice.
        if canonical == "OTHER" and raw and raw != "OTHER" and not row.get("custom_unit_label"):
            row["custom_unit_label"] = raw
        row["unit"] = canonical
        return row
    # Unmapped free-text unit (e.g. "cubes" from a foreman): store
    # OTHER + preserve the original as custom_unit_label.
    if raw:
        if not row.get("custom_unit_label"):
            row["custom_unit_label"] = raw
        row["unit"] = "OTHER"
    else:
        row["unit"] = "OTHER"
    return row


def _ensure_other_unit_descriptions(rows: List[Dict[str, Any]], field_name: str) -> None:
    for idx, row in enumerate(rows):
        if (row.get("unit") or "") == "OTHER":
            desc = (row.get("custom_unit_label") or "").strip()
            if not desc:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "other_unit_description_required",
                        "field": field_name,
                        "row_index": idx,
                        "message": "OTHER units require a short description.",
                    },
                )


def _validate_location_weather_parity(payload_dict: Dict[str, Any]) -> None:
    source = (payload_dict.get("location_source") or "").strip()
    lat = payload_dict.get("gps_lat")
    lng = payload_dict.get("gps_lng")
    wx = payload_dict.get("weather_snapshot_meta") or {}
    has_location_facts = bool(
        source
        or lat is not None
        or lng is not None
        or payload_dict.get("gps_accuracy") is not None
        or str(payload_dict.get("location_captured_at") or "").strip()
    )
    has_structured_weather = bool(wx or (payload_dict.get("weather_snapshots") or []))
    if not has_location_facts and not has_structured_weather:
        return
    if has_location_facts and not source:
        raise HTTPException(status_code=422, detail={"error": "location_source_required"})
    if lat is not None and not (-90 <= float(lat) <= 90):
        raise HTTPException(status_code=422, detail={"error": "invalid_latitude"})
    if lng is not None and not (-180 <= float(lng) <= 180):
        raise HTTPException(status_code=422, detail={"error": "invalid_longitude"})
    if has_structured_weather:
        if not source:
            raise HTTPException(status_code=422, detail={"error": "location_source_required"})
        if wx.get("gps_lat") is None or wx.get("gps_lng") is None:
            raise HTTPException(status_code=422, detail={"error": "weather_coordinates_missing"})
        if lat is None or lng is None:
            raise HTTPException(status_code=422, detail={"error": "report_coordinates_missing"})
        if float(wx.get("gps_lat")) != float(lat) or float(wx.get("gps_lng")) != float(lng):
            raise HTTPException(status_code=422, detail={"error": "weather_coordinates_mismatch"})
        if not str(wx.get("observation_timestamp") or wx.get("peak_timestamp") or "").strip():
            raise HTTPException(status_code=422, detail={"error": "weather_timestamp_required"})


# TRACK 26.02 · canonical constraint categories (lower-case).
_CANONICAL_CONSTRAINT_TYPES = {
    "weather", "utility", "survey", "material", "equipment",
    "trucking", "mot", "cei_inspection", "owner_engineer",
    "safety", "other",
}


def _normalize_constraint_type(row: Dict[str, Any]) -> Dict[str, Any]:
    """Case-normalize constraint_type to lower-case. Unknown categories
    are collapsed to ``other`` while preserving the original word in
    ``notes`` (prepended) so no operator context is lost.
    """
    raw = (row.get("constraint_type") or "").strip()
    if not raw:
        row["constraint_type"] = "other"
        return row
    lowered = raw.lower()
    if lowered in _CANONICAL_CONSTRAINT_TYPES:
        row["constraint_type"] = lowered
        return row
    # Unknown category: prepend the operator's word into notes so the
    # information isn't lost, then bucket to "other".
    existing_notes = (row.get("notes") or "").strip()
    prefix = f"[{raw}]"
    if existing_notes:
        row["notes"] = f"{prefix} {existing_notes}"
    else:
        row["notes"] = prefix
    row["constraint_type"] = "other"
    return row


class ConstraintRow(BaseModel):
    """One structured constraint/delay entry on a Daily Report.

    TRACK 26.02 · P0 recovery:
      * `constraint_type` widened from `Literal[...]` → `str` so the UI
        can post any case ("WEATHER", "Weather", "weather") without a
        422. Normalization happens server-side via
        `_normalize_constraint_type()` at write time — unknown
        categories are bucketed to "other" and the original word is
        preserved in the row's notes.
      * `extra="forbid"` → `extra="ignore"` so future UI-side helper
        fields don't 422 the whole payload.
    """
    model_config = ConfigDict(extra="ignore")

    row_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    constraint_type: str = "other"
    hours_impact: Optional[float] = None        # 0–24 · optional
    notes: Optional[str] = None                 # ≤ 280 chars · voice or text
    # Advisory flags derived server-side · operator can override on the row.
    may_require_rfi: bool = False
    may_affect_schedule: bool = False


class DailyReportCreate(BaseModel):
    """Daily site activity log (replaces Fieldwire daily reports)."""
    model_config = ConfigDict(extra="allow")

    project_name: str
    project_number: Optional[str] = ""
    location: str
    report_date: str  # YYYY-MM-DD
    report_number: Optional[str] = ""
    prepared_by: str
    superintendent: Optional[str] = ""

    weather_summary: Optional[str] = ""
    weather_snapshots: List[Dict[str, Any]] = Field(default_factory=list)
    weather_snapshot_meta: Optional[Dict[str, Any]] = None
    gps_lat: Optional[float] = None
    gps_lng: Optional[float] = None
    gps_accuracy: Optional[float] = None
    location_captured_at: Optional[str] = ""
    location_permission_status: Optional[str] = "unknown"
    location_capture_result: Optional[str] = ""
    location_source: Optional[str] = ""
    location_error_code: Optional[str] = ""
    location_error_message: Optional[str] = ""
    location_capture_origin: Optional[str] = ""
    location_capture_attempts: Optional[int] = 0

    schedule_delays: Optional[str] = "No"
    schedule_delays_notes: Optional[str] = ""
    weather_impact: Optional[str] = "No"
    weather_impact_notes: Optional[str] = ""
    safety_incidents_today: Optional[str] = "No"
    injuries_reported: Optional[str] = "No"
    incident_notes: Optional[str] = ""
    safety_notified: Optional[str] = ""
    safety_contact_person: Optional[str] = ""
    safety_contact_time: Optional[str] = ""
    incident_report_filled: Optional[str] = ""
    incident_report_time: Optional[str] = ""
    general_notes: Optional[str] = ""

    masci_crews: List[Dict[str, Any]] = Field(default_factory=list)
    subcontractors: List[Dict[str, Any]] = Field(default_factory=list)
    visitors: List[Dict[str, Any]] = Field(default_factory=list)
    equipment: List[Dict[str, Any]] = Field(default_factory=list)
    materials: List[Dict[str, Any]] = Field(default_factory=list)
    activities: List[Dict[str, Any]] = Field(default_factory=list)

    # MM-ENTRY-002 · K-MM-1 · Outbound material capture.
    # Foreman-authored rows describing material physically LEAVING the
    # project (millings hauled to recycling, unsuitable dirt offsite,
    # demo debris, trees, contaminated material, etc.). Each row:
    #   {material, quantity, unit, hauler, destination,
    #    ticket_or_manifest, notes}
    # Required-at-form-time: material, quantity, unit. Other fields
    # optional so the field workflow stays fast.
    # NO new collection. NO direction toggle on `materials[]` (which
    # remains inbound-only). NO production[] reuse (MM-001B-F1 doctrine).
    outbound_materials: List[Dict[str, Any]] = Field(default_factory=list)

    # Phase V.2 · Wave-1A · structured production + constraints.
    production: List[ProductionRow] = Field(default_factory=list)
    constraints: List[ConstraintRow] = Field(default_factory=list)
    cost_code_quantities: List[Dict[str, Any]] = Field(default_factory=list)
    work_blocks: List[WorkBlockRow] = Field(default_factory=list)

    photos: List[str] = Field(default_factory=list)
    photo_observations: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    photo_intelligence_status: Optional[str] = ""

    # ────────────────────────────────────────────────────────────
    # TRACK 15.62 · Daily Report Recovery (additive · feature-flagged
    # consumption by the new NewDailyReport guided-narrative workflow).
    # All five fields below are optional and default empty. Legacy
    # clients submitting without them continue to work unchanged.
    # The aggregator and PDF render layers read these when present
    # and fall back to `general_notes` / `activities[]` otherwise.
    # ────────────────────────────────────────────────────────────

    # Structured narrative — six guided-prompt sections that, taken
    # together, form the operational story of the day. Stored as a
    # dict so adding a seventh prompt later does not require a model
    # change. Keys (when present): work_completed, delays, inspections,
    # materials_received, follow_ups, tomorrow_plan.
    narrative_sections: Optional[Dict[str, str]] = None

    # Per-photo captions, parallel to `photos[]`. `photo_captions[i]`
    # captions `photos[i]` when present; missing entries are rendered
    # without a caption (legacy behaviour).
    photo_captions: Optional[List[str]] = None

    prepared_by_signature: Optional[str] = ""
    superintendent_signature: Optional[str] = ""
    distribution_list: Optional[List[str]] = Field(default=None, max_length=20)

    # TRACK 19.04 · Unified attachment envelope.
    # `attachments[]` accepts already-uploaded document metadata blobs
    # (see `/api/daily-reports/attachments/upload`). One list, all
    # non-photo file kinds — PDFs, Excel, CSV. Photos continue to live
    # in `photos[]` for backward compat and PDF-embed continuity.
    # Each entry:
    #   { attachment_ref, mime_type, extension, category, filename,
    #     file_size, uploaded_at }
    attachments: Optional[List[Dict[str, Any]]] = Field(default_factory=list)

    # ────────────────────────────────────────────────────────────
    # TRACK 22.9A · Daily Report Draft Summary Assist.
    # `ai_accepted_summary` is the supervisor-accepted narrative
    # (may be AI-generated, AI-then-edited, or the deterministic
    # fallback). Additive · defaults empty · absence is normal for
    # legacy reports. `ai_accepted_summary_meta` captures the
    # provenance so downstream consumers (PM/PDF/ODS) can honestly
    # label the source. Provider metadata is masked; raw keys are
    # never persisted.
    # ────────────────────────────────────────────────────────────
    ai_accepted_summary: Optional[str] = ""
    ai_accepted_summary_meta: Optional[Dict[str, Any]] = None

    # ────────────────────────────────────────────────────────────
    # TRACK 24.13 · Evidence Intelligence Manifest.
    # Optional canonical manifest built by
    # `services.dr_evidence.build_manifest`. When present, downstream
    # consumers (PDF, PM email, DR viewer, ODS confidence gating)
    # can render an honest "what the AI actually saw" audit trail
    # alongside the accepted summary. Persisting it lets a PM verify
    # the summary was grounded in real evidence.
    # ────────────────────────────────────────────────────────────
    evidence_manifest: Optional[Dict[str, Any]] = None

    # TRACK 27.11A · production-safe certification lane.
    certification_record: bool = False
    synthetic_record: bool = False
    hidden_from_operations: bool = False
    email_dispatch_suppressed: bool = False
    certification_track_id: Optional[str] = None
    certification_run_id: Optional[str] = None
    certification_release_source_hash: Optional[str] = None
    certification_release_reason: Optional[str] = None
    certification_required_workflows: Optional[List[str]] = None
    certification_delivery_override_requested: bool = False
    certification_authorized_recipient: Optional[str] = None
    certification_override_ttl_minutes: Optional[int] = None
    schedule_actual_candidates: Optional[List[Dict[str, Any]]] = Field(default_factory=list)
    schedule_actual_candidate_summary: Optional[Dict[str, Any]] = None


class DailyReport(DailyReportCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    doc_id: Optional[str] = ""  # human-readable: DR-YYYY-NNNNN, stamped on insert
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    # Wave-1A · audit envelope. Computed at insert; never client-supplied.
    audit_envelope_sha256: Optional[str] = ""
    # DR-FIX-3 · R9 · Prepared By Directory Binding.
    #   prepared_by_identity   structured identity when a portal token
    #                          is presented (admin, pm, fl, hr, safety,
    #                          shop, dispatch, leadership). None / empty
    #                          when FSI fallback path (public submit).
    #   prepared_by_bound      True when prepared_by_identity is populated.
    #                          Lets audits discriminate directory-bound
    #                          submissions from FSI fallback without
    #                          exposing structured identity in UI.
    prepared_by_identity: Optional[Dict[str, Any]] = None
    prepared_by_bound: bool = False


def _is_field_or_mobile_actor(actor: Any) -> bool:
    if not isinstance(actor, dict):
        return False
    role = str(actor.get("role") or actor.get("_actor") or actor.get("_actor_kind") or "").strip().lower()
    return role in {"hr", "fl", "field_leadership", "leadership", "safety", "dispatch", "shop", "safety_forms"}


def _strip_financial_fields(value: Any) -> Any:
    if isinstance(value, list):
        return [_strip_financial_fields(item) for item in value]
    if not isinstance(value, dict):
        return value
    clean: Dict[str, Any] = {}
    for key, raw in value.items():
        if key in FINANCIAL_FIELDS:
            continue
        clean[key] = _strip_financial_fields(raw)
    return clean


def _sanitize_daily_report_for_actor(doc: Dict[str, Any], actor: Any) -> Dict[str, Any]:
    if not _is_field_or_mobile_actor(actor):
        return doc
    clean = _strip_financial_fields(doc)
    progress = clean.get("job_cost_code_progress")
    if isinstance(progress, dict):
        codes = progress.get("codes") or []
        if isinstance(codes, list):
            progress["codes"] = [_strip_financial_fields(row) for row in codes]
    return clean


class DraftPhotoIntelligenceBody(BaseModel):
    form_key: str = Field(min_length=1, max_length=180)
    payload: Dict[str, Any] = Field(default_factory=dict)
    force: bool = False


class VoiceTranscriptionResponse(BaseModel):
    ok: bool = True
    english_text: str = ""
    work_performed: str = ""
    activities: str = ""
    detected_language: Optional[str] = None
    provider: Optional[str] = None
    model: Optional[str] = None
    latency_ms: int = 0


# ── Phase V.2 · Wave-1A · helpers ───────────────────────────────────


def _derive_advisory_flags(report: DailyReport) -> None:
    """Set `may_require_rfi` + `may_affect_schedule` on each constraint
    row based on its `constraint_type`. Operator-defined heuristic —
    informational only · no workflow change.

    Doctrine: ADVISORY_FLAG_CERTIFICATION.md
    """
    for row in report.constraints:
        if not isinstance(row, ConstraintRow):
            continue
        if row.constraint_type in _RFI_CANDIDATE_TYPES:
            row.may_require_rfi = True
        if row.constraint_type in _SCHEDULE_IMPACT_TYPES:
            row.may_affect_schedule = True


def _flatten_schedule_source(schedule_doc: Optional[Dict[str, Any]]) -> str:
    if not isinstance(schedule_doc, dict):
        return ""
    chunks: List[str] = []
    for key in (
        "project_name",
        "project_number",
        "current_phase",
        "description",
        "scope",
        "lookahead",
        "lookahead_notes",
        "tomorrow_plan",
        "future_schedule_activity",
        "next_major_work",
        "milestones",
    ):
        value = schedule_doc.get(key)
        if isinstance(value, str) and value.strip():
            chunks.append(value.strip())
        elif isinstance(value, list):
            chunks.extend(str(item).strip() for item in value if str(item).strip())
        elif isinstance(value, dict):
            chunks.extend(f"{k}: {v}" for k, v in value.items() if str(v).strip())
    return " | ".join(chunks)


def _extract_report_fact_lines(report_doc: Dict[str, Any]) -> List[str]:
    lines: List[str] = []
    if not isinstance(report_doc, dict):
        return lines
    production = report_doc.get("production") or []
    for row in production:
        if not isinstance(row, dict):
            continue
        desc = str(row.get("description") or "").strip()
        qty = row.get("quantity")
        unit = str(row.get("unit_snapshot") or row.get("unit") or "").strip()
        if desc:
            quant = ""
            if qty not in (None, ""):
                quant = f" ({qty} {unit})".strip()
            lines.append(f"production: {desc}{quant}")
    for key in ("general_notes", "weather_summary", "schedule_delays_notes", "incident_notes"):
        value = str(report_doc.get(key) or "").strip()
        if value:
            lines.append(f"{key}: {value}")
    ns = report_doc.get("narrative_sections") or {}
    if isinstance(ns, dict):
        for key in ("work_completed", "tomorrow_plan", "follow_ups"):
            value = str(ns.get(key) or "").strip()
            if value:
                lines.append(f"{key}: {value}")
    return lines[:20]


async def _find_schedule_source(db, project_number: str) -> Optional[Dict[str, Any]]:
    pn = str(project_number or "").strip()
    if not pn:
        return None
    collections = [
        ("jobs_master", {"project_number": pn}),
        ("operational_links", {"project_number": pn}),
        ("project_threads", {"project_number": pn}),
    ]
    projection = {
        "_id": 0,
        "project_name": 1,
        "project_number": 1,
        "current_phase": 1,
        "description": 1,
        "scope": 1,
        "lookahead": 1,
        "lookahead_notes": 1,
        "tomorrow_plan": 1,
        "future_schedule_activity": 1,
        "next_major_work": 1,
        "milestones": 1,
    }
    for coll_name, query in collections:
        try:
            row = await db[coll_name].find_one(query, projection)
            if row:
                row["_source_collection"] = coll_name
                return row
        except Exception:
            continue
    return None


async def _build_watchdog_flags(db, doc: Dict[str, Any]) -> Dict[str, Any]:
    project_number = str(doc.get("project_number") or "").strip()
    report_date = str(doc.get("report_date") or "").strip()
    schedule_doc = await _find_schedule_source(db, project_number)
    schedule_summary = _flatten_schedule_source(schedule_doc)

    yesterday = None
    if project_number and report_date:
        try:
            rows = await db.daily_reports.find(
                {"project_number": project_number, "report_date": {"$lt": report_date}},
                {"_id": 0},
            ).sort("report_date", -1).limit(1).to_list(1)
            yesterday = rows[0] if rows else None
        except Exception:
            yesterday = None

    today_lines = _extract_report_fact_lines(doc)
    conflicts: List[Dict[str, Any]] = []
    y_tomorrow = str(((yesterday or {}).get("narrative_sections") or {}).get("tomorrow_plan") or "").strip()
    todays_work = " ".join(today_lines).lower()
    if y_tomorrow and todays_work and y_tomorrow.lower() not in todays_work:
        conflicts.append({
            "type": "yesterday_plan_mismatch",
            "severity": "medium",
            "message": "Yesterday's planned work does not clearly appear in today's report.",
            "evidence": {
                "yesterday_tomorrow_plan": y_tomorrow[:400],
                "today_excerpt": " | ".join(today_lines)[:500],
            },
        })

    today_delay = str(doc.get("schedule_delays") or "").strip().lower() == "yes"
    if schedule_summary and today_delay:
        conflicts.append({
            "type": "schedule_delay_against_plan",
            "severity": "medium",
            "message": "Today's report marks a schedule delay while a scheduled work plan exists for this project.",
            "evidence": {
                "schedule_source": (schedule_doc or {}).get("_source_collection") or "unknown",
                "schedule_excerpt": schedule_summary[:500],
                "delay_notes": str(doc.get("schedule_delays_notes") or "")[:300],
            },
        })

    if schedule_summary and today_lines:
        schedule_words = {w for w in re.findall(r"[a-zA-Z]{5,}", schedule_summary.lower())}
        today_words = {w for w in re.findall(r"[a-zA-Z]{5,}", " ".join(today_lines).lower())}
        if schedule_words and today_words and schedule_words.isdisjoint(today_words):
            conflicts.append({
                "type": "schedule_scope_mismatch",
                "severity": "low",
                "message": "Today's reported work does not appear to overlap with the currently available schedule source.",
                "evidence": {
                    "schedule_source": (schedule_doc or {}).get("_source_collection") or "unknown",
                    "schedule_excerpt": schedule_summary[:500],
                    "today_excerpt": " | ".join(today_lines)[:500],
                },
            })

    return {
        "has_conflicts": bool(conflicts),
        "requires_pm_review": bool(conflicts),
        "schedule_source": {
            "collection": (schedule_doc or {}).get("_source_collection") or None,
            "summary": schedule_summary[:700],
        },
        "yesterday_report": {
            "id": (yesterday or {}).get("id") or None,
            "doc_id": (yesterday or {}).get("doc_id") or None,
            "report_date": (yesterday or {}).get("report_date") or None,
        },
        "conflicts": conflicts,
        "checked_at": datetime.now(timezone.utc).isoformat(),
    }


async def _run_daily_reports_csv_export(db, actor: Any) -> Dict[str, Any]:
    import csv as _csv  # noqa: PLC0415
    import io as _io    # noqa: PLC0415

    # Canonical PM-scope alias preserved for the release-gate regression
    # suite. Empty PM scope must short-circuit to an empty CSV without any
    # data queries.
    if isinstance(actor, dict) and str(actor.get("role") or "").lower() == "pm":
        pm_scope = await compute_pm_scope(db, actor)
        if pm_scope.is_definitively_empty():
            buf = _io.StringIO()
            fields = [
                "report_number", "report_date", "project_number", "project_name",
                "location", "prepared_by", "superintendent", "weather_summary",
                "schedule_delays", "weather_impact",
                "safety_incidents_today", "injuries_reported",
                "crew_count", "sub_count", "visitor_count", "photo_count",
                "created_at",
            ]
            writer = _csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
            writer.writeheader()
            return {
                "content": buf.getvalue().encode("utf-8"),
                "filename": "daily_reports.csv",
                "content_type": "text/csv; charset=utf-8",
                "rows": 0,
            }

    scope_query = await governance_project_scope_filter(db, actor)
    if scope_query is None:
        buf = _io.StringIO()
        fields = [
            "report_number", "report_date", "project_number", "project_name",
            "location", "prepared_by", "superintendent", "weather_summary",
            "schedule_delays", "weather_impact",
            "safety_incidents_today", "injuries_reported",
            "crew_count", "sub_count", "visitor_count", "photo_count",
            "created_at",
        ]
        writer = _csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        return {
            "content": buf.getvalue().encode("utf-8"),
            "filename": "daily_reports.csv",
            "content_type": "text/csv; charset=utf-8",
            "rows": 0,
        }
    match_stage = apply_synthetic_dr_exclusion(scope_query)
    pipeline = [
        {"$match": match_stage},
        {"$sort": {"report_date": -1, "created_at": -1}},
        {"$limit": 5000},
        {"$project": {
            "_id": 0, "id": 1, "report_number": 1, "project_name": 1,
            "project_number": 1, "location": 1, "report_date": 1,
            "prepared_by": 1, "superintendent": 1, "weather_summary": 1,
            "schedule_delays": 1, "weather_impact": 1,
            "safety_incidents_today": 1, "injuries_reported": 1,
            "created_at": 1,
            "crew_count": {"$size": {"$ifNull": ["$masci_crews", []]}},
            "sub_count": {"$size": {"$ifNull": ["$subcontractors", []]}},
            "visitor_count": {"$size": {"$ifNull": ["$visitors", []]}},
            "photo_count": {"$size": {"$ifNull": ["$photos", []]}},
        }},
    ]
    docs = await db.daily_reports.aggregate(pipeline).to_list(5000)
    buf = _io.StringIO()
    fields = [
        "report_number", "report_date", "project_number", "project_name",
        "location", "prepared_by", "superintendent", "weather_summary",
        "schedule_delays", "weather_impact",
        "safety_incidents_today", "injuries_reported",
        "crew_count", "sub_count", "visitor_count", "photo_count",
        "created_at",
    ]
    writer = _csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
    writer.writeheader()
    for d in docs:
        writer.writerow({f: (d.get(f) if d.get(f) is not None else "") for f in fields})
    return {
        "content": buf.getvalue().encode("utf-8"),
        "filename": "daily_reports.csv",
        "content_type": "text/csv; charset=utf-8",
        "rows": len(docs),
    }


async def _run_daily_reports_csv_job(db, job_id: str, actor: Any) -> None:
    try:
        await mark_async_job_processing(job_id, message="Building daily reports export…")
        export = await _run_daily_reports_csv_export(db, actor)
        await complete_async_job_binary(
            job_id,
            content=export.get("content") or b"",
            filename=str(export.get("filename") or "daily_reports.csv"),
            media_type=str(export.get("content_type") or "text/csv; charset=utf-8"),
            result_meta={
                "filename": export.get("filename") or "daily_reports.csv",
                "content_type": export.get("content_type") or "text/csv; charset=utf-8",
                "rows": export.get("rows") or 0,
            },
        )
    except Exception as exc:  # noqa: BLE001
        await fail_async_job(
            job_id,
            error_code="daily_reports_csv_export_failed",
            message=str(exc)[:500] or "CSV export failed",
        )


def _apply_certification_record_safety(doc: Dict[str, Any]) -> Dict[str, Any]:
    if not bool(doc.get("certification_record")):
        return doc
    doc["certification_record"] = True
    doc["synthetic_record"] = True
    doc["hidden_from_operations"] = True
    allow_controlled_routing = bool(
        doc.get("certification_lane_allows_email")
        and isinstance(doc.get("routing_override"), dict)
        and bool(doc.get("routing_override", {}).get("enabled"))
    )
    doc["email_dispatch_suppressed"] = not allow_controlled_routing
    doc["certification_track_id"] = str(doc.get("certification_track_id") or "27.11B")
    doc["certification_run_id"] = doc.get("certification_run_id")
    doc["certification_release_source_hash"] = doc.get("certification_release_source_hash")
    doc["certification_release_reason"] = doc.get("certification_release_reason")
    doc["certification_delivery_override_requested"] = bool(
        doc.get("certification_delivery_override_requested")
    )
    doc["certification_authorized_recipient"] = doc.get("certification_authorized_recipient")
    doc["certification_override_ttl_minutes"] = doc.get("certification_override_ttl_minutes")
    required = doc.get("certification_required_workflows")
    if required is None:
        doc["certification_required_workflows"] = []
    elif isinstance(required, list):
        doc["certification_required_workflows"] = [str(x) for x in required if str(x).strip()]
    else:
        doc["certification_required_workflows"] = [str(required)]
    return doc


def _should_schedule_daily_report_email(doc: Dict[str, Any]) -> bool:
    return not bool(doc.get("email_dispatch_suppressed"))


def _audit_envelope(doc: Dict[str, Any]) -> Dict[str, Any]:
    """Project the daily_report into the canonical hash envelope.
    Excludes transient + audit fields so the hash is content-stable
    across re-renders.

    Doctrine: DAILY_REPORT_AUDIT_FOOTER_CERTIFICATION.md
    """
    excluded = {"_id", "audit_envelope_sha256", "created_at"}
    return {k: v for k, v in doc.items() if k not in excluded}


def _compute_audit_envelope_sha256(doc: Dict[str, Any]) -> str:
    env = _audit_envelope(doc)
    return hashlib.sha256(
        json.dumps(env, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


class DailyReportSummary(BaseModel):
    id: str
    project_name: str
    project_number: str
    location: str
    report_date: str
    prepared_by: str
    weather_summary: str
    photo_count: int
    crew_count: int
    sub_count: int
    visitor_count: int
    created_at: str


def register_daily_reports_routes(api_router: APIRouter, db, require_admin, rate_limit_public_post, schedule_auto_email, require_admin_pm_or_hr_read=None):
    """Attach Daily Report endpoints to the shared router.

    TRACK 15.13E — `require_admin_pm_or_hr_read` is an OPTIONAL extra
    dep that, when supplied, replaces `require_admin` on the single
    read endpoint `GET /api/daily-reports/{report_id}` so HR can view
    Daily Reports. All mutation routes stay on the strict admin/PM gate.
    """

    async def _sanitize_inline_photos(doc: Dict[str, Any]) -> Dict[str, int]:
        """Batch H · GAP-1 write-path defense (2026-05-30).

        Walks the same three nested photo paths as the
        `scripts/migrate_dr_photos.py` migration script and replaces any
        inline `data:image/...` base64 with a canonical `photo://` reference
        BEFORE the doc is persisted. Idempotent: entries that are already
        `photo://` refs (or empty) are skipped. R2 misconfiguration is a
        soft failure — the submit still succeeds with inline base64 (legacy
        behavior preserved) so a user is never blocked by a storage outage.

        Returns counters: {photos, sub_photos, mat_photos, errors}.
        """
        counters = {"photos": 0, "sub_photos": 0, "mat_photos": 0, "errors": 0}
        try:
            from photo_storage import upload_data_url, is_configured  # noqa: PLC0415
        except Exception:
            return counters
        if not is_configured():
            return counters

        dr_id = (doc.get("id") or "unknown")[:32]

        async def _walk(lst, source_id: str, key: str) -> None:
            if not isinstance(lst, list):
                return
            for i, item in enumerate(lst):
                if isinstance(item, str) and item.startswith("data:image/"):
                    try:
                        ref = await upload_data_url(item, source_id=source_id)
                        lst[i] = ref
                        counters[key] += 1
                    except Exception:
                        # Soft fail — leave inline; counted for observability
                        counters["errors"] += 1

        # Path 1 — top-level photos[]
        await _walk(doc.get("photos"), f"dr_{dr_id}", "photos")
        # Path 2 — subcontractors[*].photos[]
        for sub in (doc.get("subcontractors") or []):
            if isinstance(sub, dict):
                await _walk(sub.get("photos"), f"dr_{dr_id}_sub", "sub_photos")
        # Path 3 — materials[*].ticket_photos[]
        for mat in (doc.get("materials") or []):
            if isinstance(mat, dict):
                await _walk(mat.get("ticket_photos"), f"dr_{dr_id}_mat", "mat_photos")
        return counters

    @api_router.post("/transcribe", response_model=VoiceTranscriptionResponse)
    async def transcribe_voice_note(
        audio: UploadFile = File(...),
        field_hint: str = Form("work_performed"),
        language_hint: str = Form("auto"),
        project_number: str = Form(""),
    ):
        import os  # noqa: PLC0415
        from dotenv import load_dotenv  # noqa: PLC0415
        from emergentintegrations.llm.chat import LlmChat, UserMessage  # noqa: PLC0415
        from emergentintegrations.llm.openai.speech_to_text import OpenAISpeechToText  # noqa: PLC0415
        from services.ai_gateway.task_router import route  # noqa: PLC0415

        load_dotenv("/app/backend/.env")
        api_key = str(os.environ.get("EMERGENT_LLM_KEY") or "").strip()
        if not api_key:
            raise HTTPException(status_code=503, detail="Voice transcription is unavailable because the LLM key is missing.")

        raw_bytes = await audio.read()
        if not raw_bytes:
            raise HTTPException(status_code=400, detail="Audio upload was empty.")

        filename = str(audio.filename or "voice.webm")
        suffix = filename[filename.rfind("."):] if "." in filename else ".webm"
        started_at = datetime.now(timezone.utc)
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            tmp.write(raw_bytes)
            tmp_path = tmp.name

        try:
            client = OpenAISpeechToText(api_key=api_key)
            transcript = await client.transcribe(
                tmp_path,
                model="whisper-1",
                response_format="verbose_json",
                prompt=(
                    "Transcribe construction site speech accurately. Preserve technical terms, "
                    "equipment names, dimensions, stationing, numbers, cost codes, and acronyms exactly."
                ),
                language=None if language_hint == "auto" else language_hint,
                temperature=0,
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=502, detail=f"Transcription failed: {str(exc)[:300]}") from exc
        finally:
            try:
                os.unlink(tmp_path)
            except Exception:
                pass

        raw_text = str(getattr(transcript, "text", "") or "").strip()
        if not raw_text:
            raise HTTPException(status_code=422, detail="No speech was detected in the uploaded audio.")

        detected_language = str(getattr(transcript, "language", "") or language_hint or "auto").strip() or None
        english_text = raw_text
        if detected_language and detected_language.lower() not in {"", "en", "english"}:
            provider, model = route("translation_es_en")
            chat = LlmChat(
                api_key=api_key,
                session_id=f"voice-to-report-{uuid.uuid4().hex[:10]}",
                system_message=(
                    "Translate any construction-site speech into clear English. Preserve technical terms, "
                    "equipment names, dimensions, stationing, IDs, and acronyms exactly. Return only the English text."
                ),
            ).with_model(provider, model)
            translated = await chat.send_message(UserMessage(text=raw_text))
            if str(translated or "").strip():
                english_text = str(translated).strip()

        normalized_hint = str(field_hint or "work_performed").strip().lower()
        work_performed = english_text if normalized_hint in {"work_performed", "both", "auto"} else ""
        activities = english_text if normalized_hint in {"activities", "both", "auto"} else ""
        latency_ms = int((datetime.now(timezone.utc) - started_at).total_seconds() * 1000)

        return VoiceTranscriptionResponse(
            ok=True,
            english_text=english_text,
            work_performed=work_performed,
            activities=activities,
            detected_language=detected_language,
            provider="openai",
            model="whisper-1",
            latency_ms=latency_ms,
        )

    @api_router.post("/daily-reports", response_model=DailyReport, dependencies=[Depends(rate_limit_public_post)])
    async def create_daily_report(payload: DailyReportCreate, request: Request, background_tasks: BackgroundTasks):
        # ── Phase V.2 · Wave-1A · POST RESTORED (M1 freeze partial revert) ──
        # Per operator directive (2026-05-29 · Wave-1A authorization):
        #   "Restore POST /api/daily-reports. Keep DELETE = 410."
        # Doctrine: /app/memory/WAVE_1A_IMPLEMENTATION_REPORT.md
        # Idempotent submit (Phase J · Field Resiliency) preserved.
        # ── Phase 10A-B · OMEGA Correction Directive · Correction 1 ──
        # Excavation Activity gate: if the foreman selects "Excavation
        # Activity Today? = YES" the Daily Report MUST be linked to at
        # least one excavation record (existing or freshly created).
        _p = payload.model_dump()
        _accepted_summary = str(_p.get("ai_accepted_summary") or "").strip()
        _accepted_meta = _p.get("ai_accepted_summary_meta") or {}
        _accepted_at = str(_accepted_meta.get("accepted_at") or "").strip()
        _accepted_source = str(_accepted_meta.get("source") or "").strip().lower()
        if not _accepted_summary:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "approved_summary_required",
                    "message": (
                        "Daily Report submission is blocked until one executive "
                        "summary is approved and frozen into the record."
                    ),
                },
            )
        if not _accepted_at:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "approved_summary_metadata_required",
                    "message": "Approved Executive Summary is missing the approval timestamp.",
                },
            )
        if _accepted_source not in {"ai", "edited", "fallback", "manual"}:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "approved_summary_source_invalid",
                    "message": "Approved Executive Summary is missing a valid source label.",
                },
            )
        _exc_activity = str(_p.get("excavation_activity_today") or "").strip().lower()
        _linked_excs = _p.get("linked_excavation_ids") or []
        if _exc_activity in ("yes", "true", "y", "1"):
            if not _linked_excs:
                raise HTTPException(
                    status_code=422,
                    detail={
                        "error": "excavation_record_required",
                        "message": (
                            "Excavation Activity Today is YES but no Excavation "
                            "Record is linked. Create a new excavation record "
                            "or link an existing one before submitting the Daily Report."
                        ),
                    },
                )

        from lib.idempotency import with_idempotency, idem_key_from_request  # noqa: PLC0415
        key = idem_key_from_request(request)

        async def _do_create():
            # ── TRACK 26.02 · P0 recovery · unit + constraint normalize ──
            # Normalize every production/constraint row BEFORE the
            # DailyReport internal model is built. Every downstream
            # consumer (PDF, email, AI evidence, ODS ingest, KPI
            # readers) then sees canonical codes.
            payload_dict = payload.model_dump()
            try:
                payload_dict["production"] = [
                    _normalize_unit(dict(r)) for r in (payload_dict.get("production") or [])
                ]
                _ensure_other_unit_descriptions(payload_dict["production"], "production")
            except HTTPException:
                raise
            except Exception:  # noqa: BLE001
                pass
            try:
                payload_dict["materials"] = [
                    _normalize_unit(dict(r)) for r in (payload_dict.get("materials") or [])
                ]
                _ensure_other_unit_descriptions(payload_dict["materials"], "materials")
            except HTTPException:
                raise
            except Exception:  # noqa: BLE001
                pass
            try:
                payload_dict["outbound_materials"] = [
                    _normalize_unit(dict(r)) for r in (payload_dict.get("outbound_materials") or [])
                ]
                _ensure_other_unit_descriptions(payload_dict["outbound_materials"], "outbound_materials")
            except HTTPException:
                raise
            except Exception:  # noqa: BLE001
                pass
            try:
                normalized_equipment = []
                for r in (payload_dict.get("equipment") or []):
                    row = dict(r)
                    run = row.get("run_time")
                    idle = row.get("idle_time")
                    if run not in (None, "") and row.get("hours_used") in (None, ""):
                        row["hours_used"] = run
                    if idle not in (None, "") and row.get("idle_hours") in (None, ""):
                        row["idle_hours"] = idle
                    if row.get("run_time") in (None, "") and row.get("hours_used") not in (None, ""):
                        row["run_time"] = row.get("hours_used")
                    if row.get("idle_time") in (None, "") and row.get("idle_hours") not in (None, ""):
                        row["idle_time"] = row.get("idle_hours")
                    normalized_equipment.append(row)
                payload_dict["equipment"] = normalized_equipment
            except Exception:  # noqa: BLE001
                pass
            _validate_location_weather_parity(payload_dict)
            try:
                payload_dict["constraints"] = [
                    _normalize_constraint_type(dict(r)) for r in (payload_dict.get("constraints") or [])
                ]
            except Exception:  # noqa: BLE001
                pass
            try:
                assignments = await load_project_assignments(db, payload_dict.get("project_number") or "")
                payload_dict["cost_code_quantities"] = normalize_cost_code_actual_rows(
                    payload_dict.get("cost_code_quantities") or [],
                    assignments=assignments,
                    report_location=str(payload_dict.get("location") or "").strip(),
                )
                if not payload_dict["cost_code_quantities"]:
                    payload_dict["cost_code_quantities"] = []
            except Exception:  # noqa: BLE001
                raise HTTPException(status_code=422, detail="Invalid project cost-code actuals payload")
            report = DailyReport(**payload_dict)
            # ── DR-FIX-3 · R9 · Prepared By Directory Binding ──────
            # Inspect incoming portal tokens; if one resolves to a
            # known directory user, attach structured identity for
            # audit. FSI/public path: prepared_by_bound stays False.
            try:
                from lib.prepared_by_resolver import resolve_prepared_by_identity  # noqa: PLC0415
                _identity = await resolve_prepared_by_identity(db, request)
                if _identity:
                    report.prepared_by_identity = _identity
                    report.prepared_by_bound = True
            except Exception:  # noqa: BLE001 — best-effort audit binding
                pass
            # Wave-1A · advisory flag derivation (deterministic · operator-defined).
            _derive_advisory_flags(report)
            doc = report.model_dump()
            try:
                from lib.governed_certification_lane import (  # noqa: PLC0415
                    apply_governed_daily_report_lane,
                    is_governed_certification_project,
                )

                project_doc = None
                if bool(doc.get("certification_record")) or is_governed_certification_project(doc):
                    project_doc = await db.jobs_master.find_one(
                        {"project_number": doc.get("project_number")},
                        {
                            "_id": 0,
                            "project_number": 1,
                            "project_name": 1,
                            "pm_email": 1,
                            "co_pm_emails": 1,
                            "active": 1,
                        },
                    )
                doc = apply_governed_daily_report_lane(doc, project_doc=project_doc)
                if doc.get("certification_record") and not doc.get("certification_release_source_hash"):
                    try:
                        from server import _SOURCE_HASH  # noqa: PLC0415

                        doc["certification_release_source_hash"] = _SOURCE_HASH
                    except Exception:  # noqa: BLE001
                        pass
            except Exception:  # noqa: BLE001
                pass
            doc = _apply_certification_record_safety(doc)
            # Stamp human-readable doc ID (DR-2026-00001) so the form, the PDF,
            # and the admin search bar can all reference the same number.
            from doc_ids import ensure_doc_id  # local import to keep startup fast
            await ensure_doc_id(db, doc, "DR", when=doc.get("report_date") or doc.get("created_at"))
            report.doc_id = doc["doc_id"]
            # ── TRACK 22.4b-followup-DR · B-03 FINAL ELIMINATION ─────
            # The canonical identity for a Daily Report is `doc_id`
            # (atomic, minted from doc_id_counters). `report_number`
            # historically drifted because the frontend pre-filled it
            # from GET /daily-reports/next-number with a `DR-YYYYMMDD-
            # NNN` shape that never reconciles with the atomic
            # `DR-YYYY-NNNNN` doc_id. We now UNCONDITIONALLY mirror
            # doc_id onto report_number so every downstream consumer
            # (Trust Spine, PDFs, ODS, search, notifications, admin
            # audit) joins on exactly one identity. The old guard only
            # handled the empty-string case, which is why the 271
            # legacy skew rows exist. Do NOT reintroduce a conditional
            # here — that is the exact drift this fix removes.
            doc["report_number"] = doc["doc_id"]
            report.report_number = doc["doc_id"]
            # Batch H · GAP-1 write-path defense — convert inline base64 to
            # photo:// refs BEFORE the audit hash is computed, so the hash
            # reflects the canonical (post-sanitization) saved state.
            _photo_sanitization_counters = await _sanitize_inline_photos(doc)  # noqa: F841
            photo_observations = [
                row for row in (doc.get("photo_observations") or []) if isinstance(row, dict)
            ]
            if photo_observations:
                doc["ai_photo_observations"] = photo_observations
            if isinstance(doc.get("photos"), list) and doc.get("photos"):
                doc["photo_intelligence_status"] = "queued"
                doc["photo_observations"] = []
                accepted_meta = dict(doc.get("ai_accepted_summary_meta") or {})
                accepted_meta["photo_intelligence_status"] = "queued"
                accepted_meta["photo_observations"] = []
                doc["ai_accepted_summary_meta"] = accepted_meta
            doc["conflict_watchdog"] = await _build_watchdog_flags(db, doc)
            if doc["conflict_watchdog"].get("requires_pm_review"):
                doc["pm_review_required"] = True
            try:
                work_block_result = await sync_work_blocks_for_report(db, doc)
                doc["work_blocks"] = work_block_result.get("work_blocks") or []
                doc["work_block_summary"] = work_block_result.get("work_block_summary") or {}
                doc["work_blocks_version"] = "wp18c2.v1"
                doc["work_blocks_governed_at"] = now_iso()
            except Exception:  # noqa: BLE001
                doc.setdefault("work_blocks", [])
                doc.setdefault("work_block_summary", {
                    "work_block_count": 0,
                    "blocks_with_pay_item": 0,
                    "blocks_with_schedule_activity": 0,
                    "labor_rows": 0,
                    "equipment_rows": 0,
                    "material_rows": 0,
                    "subcontractor_rows": 0,
                    "constraint_rows": 0,
                })
            # Wave-1A · audit envelope hash (continuity + tamper detection).
            doc["audit_envelope_sha256"] = _compute_audit_envelope_sha256(doc)
            # Build the response dict from the sanitized doc so the API
            # response matches what was persisted (refs not inline).
            _notification_contract = delivery_contract()
            doc["business_state"] = "submitted"
            doc["notification_state"] = STATUS_PENDING
            doc["notification_delivery_mode"] = _notification_contract.get("delivery_mode")
            doc["notification_environment"] = _notification_contract.get("environment")
            doc["notification_provider"] = _notification_contract.get("provider")
            doc["notification_provider_required"] = bool(_notification_contract.get("provider_acceptance_required"))
            doc["notification_provider_configured"] = bool(_notification_contract.get("provider_configured"))
            doc["notification_provider_validation_status"] = _notification_contract.get("provider_validation_status")
            doc["notification_capture_available"] = bool(_notification_contract.get("capture_required"))
            report_dict = dict(doc)
            # ── Phase 2B-2A · Job-ownership team_snapshot embed ──
            # Freeze the active project roster at submit time so future
            # roster changes never rewrite historical truth on this record.
            try:
                from lib.team_routing import snapshot_team  # noqa: PLC0415
                _snap = await snapshot_team(db, doc.get("project_number"))
                if _snap:
                    doc["team_snapshot"] = _snap
                    report_dict["team_snapshot"] = _snap
            except Exception:  # noqa: BLE001 — snapshot is best-effort
                pass
            await db.daily_reports.insert_one(doc)
            try:
                await sync_crew_observation_for_report(db, doc)
            except Exception:  # noqa: BLE001
                pass
            try:
                from services.project_schedule_actuals_spine import sync_schedule_actual_candidates_for_report  # noqa: PLC0415

                schedule_actuals = await sync_schedule_actual_candidates_for_report(
                    db,
                    doc,
                    actor={"email": doc.get("prepared_by") or "field", "role": "daily_report_submit"},
                )
                report_dict["schedule_actual_candidates"] = schedule_actuals.get("items") or []
                report_dict["schedule_actual_candidate_summary"] = {
                    "count": int(schedule_actuals.get("count") or 0),
                    "pending": int(schedule_actuals.get("pending") or 0),
                    "approved": int(schedule_actuals.get("approved") or 0),
                    "version_id": schedule_actuals.get("version_id") or "",
                }
            except Exception:  # noqa: BLE001
                report_dict.setdefault("schedule_actual_candidates", [])
                report_dict.setdefault("schedule_actual_candidate_summary", {"count": 0, "pending": 0, "approved": 0, "version_id": ""})
            progress_snapshot = await recompute_project_progress(db, doc.get("project_number") or "")
            if progress_snapshot:
                doc["job_cost_code_progress"] = progress_snapshot
                report_dict["job_cost_code_progress"] = progress_snapshot
            doc.pop("_id", None)
            # DR-CUTOVER-001 · Wire V1 submission into the ODS spine so
            # PM/Admin Operational Intelligence dashboards see REAL
            # production data (not just QA V2 drafts). Best-effort:
            # never block a submit on ODS emission.
            try:
                from services.ods_spine import ingest_dr_v1_report  # noqa: PLC0415
                await ingest_dr_v1_report(
                    db, doc, actor=doc.get("prepared_by") or "supervisor",
                    trigger="event",
                )
            except Exception:  # noqa: BLE001
                pass
            # ── TRACK 22.9B · Photo Intelligence first-pass (async) ──
            # Schedule a background task that runs the vision analyzer
            # over every attached photo. Never blocks the submit
            # response. If the pod is recycled before the task runs, a
            # reconciler loop will pick up any jobs left as `pending`
            # or `failed` in `dr_v1_photo_intel_jobs`.
            try:
                from services.photo_intelligence import (  # noqa: PLC0415
                    enqueue_v1_report, process_v1_report,
                )
                # Enqueue synchronously (fast: only inserts pending
                # job docs). This guarantees the reconciler owns the
                # retry contract even if the process crashes before
                # BackgroundTasks fires.
                await enqueue_v1_report(db, doc)
                # Fire-and-forget the actual analysis pass.
                background_tasks.add_task(process_v1_report, db, dict(doc))
            except Exception:  # noqa: BLE001
                # Best-effort — never surface a photo-intel error to
                # the field UI. Reconciler will catch up next pass.
                pass
            # ── TRACK 23.10-E · Daily Report V3 Excavation service ──
            # Consumes the Track 23.10-B Qualifications Engine + emits
            # Track 23.10-C ODS facts + attaches the readiness snapshot
            # onto the doc. Raises 400 when Competent Person selection
            # is not from the active registry.
            try:
                from services.daily_report_v3_excavation import (  # noqa: PLC0415
                    process_excavation_on_submit,
                )
                await process_excavation_on_submit(db, doc)
            except HTTPException:
                # Rethrow — invalid excavation submissions must fail.
                raise
            except Exception:                                     # noqa: BLE001
                # Never fail a non-excavation submit on this hook.
                pass
            # ── Phase 10A-B · Correction 1 · two-way Excavation linkage ──
            # Stamp this daily report ID onto every linked excavation
            # record so the relationship is queryable from both sides.
            try:
                _linked_ids = doc.get("linked_excavation_ids") or []
                if _linked_ids:
                    await db.trench_excavations.update_many(
                        {"id": {"$in": list(_linked_ids)}},
                        {"$addToSet": {
                            "daily_report_links": {
                                "daily_report_id": doc.get("id"),
                                "report_number": doc.get("doc_id") or doc.get("report_number") or "",
                                "linked_at": doc.get("created_at"),
                            },
                        }},
                    )
            except Exception:
                pass  # never block a submit on linkage
            # Mirror photos into the Job Photos library (Phase 1 read-only).
            try:
                from routes.job_photos import index_record_photos
                await index_record_photos(db, "daily_report", doc)
            except Exception:
                pass  # never block a submit on indexing
            # TRACK 15.76 · Trust Spine — open the record's lifecycle.
            # The correlation_id is attached to ``doc`` so the universal
            # email dispatcher and audit writer reuse it across stages.
            try:
                from lib.trust_spine import emit_record_created  # noqa: PLC0415
                await emit_record_created(
                    db, workflow="daily-report", record=doc,
                    module="routes/daily_reports.py",
                )
            except Exception:  # noqa: BLE001
                pass
            try:
                from lib.trust_spine import emit_record_created, emit_workflow_stage  # noqa: PLC0415

                for actual_row in (doc.get("cost_code_quantities") or []):
                    code = str(actual_row.get("cost_code") or actual_row.get("code") or "").strip()
                    if not code:
                        continue
                    actual_record = {
                        "id": f"{doc.get('project_number') or ''}:{doc.get('doc_id') or doc.get('id') or ''}:{code}",
                        "doc_id": f"{doc.get('project_number') or ''}:{doc.get('doc_id') or doc.get('id') or ''}:{code}",
                        "project_number": doc.get("project_number") or "",
                    }
                    await emit_record_created(
                        db,
                        workflow="oppc-daily-actuals",
                        record=actual_record,
                        module="routes/daily_reports.py:cost_code_quantities",
                        event_name="daily_actual_recorded",
                    )
                    await emit_workflow_stage(
                        db,
                        workflow="oppc-daily-actuals",
                        stage="validation_complete",
                        record=actual_record,
                        module="routes/daily_reports.py:cost_code_quantities",
                        event_name="quantity_updated",
                    )
                    await emit_workflow_stage(
                        db,
                        workflow="oppc-daily-actuals",
                        stage="audit_written",
                        record=actual_record,
                        module="routes/daily_reports.py:masci_crews",
                        event_name="labor_actual_updated",
                    )
                    await emit_workflow_stage(
                        db,
                        workflow="oppc-daily-actuals",
                        stage="dashboard_updated",
                        record=actual_record,
                        module="routes/daily_reports.py:equipment",
                        event_name="equipment_actual_updated",
                    )
                    await emit_workflow_stage(
                        db,
                        workflow="oppc-daily-actuals",
                        stage="completed",
                        record=actual_record,
                        module="routes/daily_reports.py",
                        event_name="completed",
                    )
            except Exception:  # noqa: BLE001
                pass
            try:
                control_plane_result = await ingest_daily_report_submission(
                    db,
                    report=doc,
                    actor_label=str(payload.prepared_by or doc.get("prepared_by") or "field").strip() or "field",
                )
                doc["operations_control_plane"] = {
                    "enabled": True,
                    "workflow_id": "oppc.daily_report_to_oppc",
                    "event_ids": [
                        control_plane_result.get("event", {}).get("id")
                    ],
                    "communication_ids": [
                        row.get("id") for row in (control_plane_result.get("communications") or []) if row.get("id")
                    ],
                    "registry_event_id": "oppc.daily_report.submitted",
                    "registry_version": "operations-control-plane-v1",
                    "last_processed_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
                    "case_id": ((control_plane_result.get("case_result") or {}).get("case") or {}).get("id") or "",
                    "case_number": ((control_plane_result.get("case_result") or {}).get("case") or {}).get("case_number") or "",
                    "case_event_id": ((control_plane_result.get("case_result") or {}).get("case_event") or {}).get("id") or "",
                    "case_communication_ids": [
                        row.get("id") for row in (((control_plane_result.get("case_result") or {}).get("case_communications") or [])) if row.get("id")
                    ],
                    "case_policy_decision": (control_plane_result.get("case_result") or {}).get("decision") or {},
                }
                doc["email_dispatch_suppressed"] = True
                if control_plane_result.get("communications"):
                    first_comm = (control_plane_result.get("communications") or [])[0]
                    first_transport = (first_comm.get("transport_results") or [{}])[-1]
                    doc["notification_state"] = first_transport.get("notification_state") or first_comm.get("status") or doc.get("notification_state")
                    doc["notification_delivery_mode"] = first_transport.get("delivery_mode") or doc.get("notification_delivery_mode")
                    doc["notification_provider_accepted"] = bool(first_transport.get("provider_accepted"))
                    doc["notification_provider_called"] = bool(first_transport.get("provider_called"))
                    doc["notification_failure_reason"] = first_transport.get("failure_reason")
                    doc["notification_capture_id"] = first_transport.get("capture_id") or doc.get("notification_capture_id")
                    doc["notification_last_updated_at"] = first_transport.get("ts") or doc.get("notification_last_updated_at")
                    report_dict.update({
                        "operations_control_plane": doc.get("operations_control_plane"),
                        "email_dispatch_suppressed": True,
                        "notification_state": doc.get("notification_state"),
                        "notification_delivery_mode": doc.get("notification_delivery_mode"),
                        "notification_provider_accepted": doc.get("notification_provider_accepted"),
                        "notification_provider_called": doc.get("notification_provider_called"),
                        "notification_failure_reason": doc.get("notification_failure_reason"),
                        "notification_capture_id": doc.get("notification_capture_id"),
                        "notification_last_updated_at": doc.get("notification_last_updated_at"),
                    })
                    await db.daily_reports.update_one(
                        {"id": doc.get("id")},
                        {"$set": {
                            "operations_control_plane": doc.get("operations_control_plane"),
                            "email_dispatch_suppressed": True,
                            "notification_state": doc.get("notification_state"),
                            "notification_delivery_mode": doc.get("notification_delivery_mode"),
                            "notification_provider_accepted": doc.get("notification_provider_accepted"),
                            "notification_provider_called": doc.get("notification_provider_called"),
                            "notification_failure_reason": doc.get("notification_failure_reason"),
                            "notification_capture_id": doc.get("notification_capture_id"),
                            "notification_last_updated_at": doc.get("notification_last_updated_at"),
                        }}
                    )
            except Exception as exc:  # noqa: BLE001
                failure_reason = f"operations_control_plane_exception:{type(exc).__name__}"
                logger.exception(
                    "[daily_reports] operations control plane failed for report id=%s doc_id=%s project_number=%s",
                    doc.get("id"),
                    doc.get("doc_id"),
                    doc.get("project_number"),
                )
                doc["operations_control_plane"] = {
                    "enabled": True,
                    "workflow_id": "oppc.daily_report_to_oppc",
                    "error_state": "failed_action_required",
                    "error_code": failure_reason,
                    "error_type": type(exc).__name__,
                    "error_message": str(exc)[:240],
                    "last_processed_at": datetime.now(timezone.utc).isoformat(),
                }
                doc["notification_state"] = "failed_action_required"
                doc["notification_failure_reason"] = failure_reason
                doc["notification_last_updated_at"] = datetime.now(timezone.utc).isoformat()
                report_dict.update({
                    "operations_control_plane": doc.get("operations_control_plane"),
                    "notification_state": doc.get("notification_state"),
                    "notification_failure_reason": doc.get("notification_failure_reason"),
                    "notification_last_updated_at": doc.get("notification_last_updated_at"),
                })
                await db.daily_reports.update_one(
                    {"id": doc.get("id")},
                    {"$set": {
                        "operations_control_plane": doc.get("operations_control_plane"),
                        "notification_state": doc.get("notification_state"),
                        "notification_failure_reason": doc.get("notification_failure_reason"),
                        "notification_last_updated_at": doc.get("notification_last_updated_at"),
                    }}
                )
            if _should_schedule_daily_report_email(doc):
                schedule_auto_email("daily-report", doc)

            # iter452.5 Tier 1 · Field Submitter Identity binding.
            # iter452.5.1 (P0) · FL token from header drives tier-1
            # resolution; orphan corner closed by tier-5 dead-letter.
            try:
                from lib.field_submitter_identity import resolve_identity  # noqa: PLC0415
                p = payload.model_dump()
                fl_token = (request.headers.get("X-FL-Token") or "").strip()
                await resolve_identity(
                    db,
                    workflow="daily_report",
                    record_id=doc.get("id") or "",
                    record_doc_id=doc.get("doc_id") or "",
                    project_number=doc.get("project_number") or "",
                    submitter_employee_id=str(p.get("submitter_employee_id") or "").strip(),
                    submitter_email_at_submit=str(p.get("submitter_email_at_submit") or "").strip(),
                    submitter_consent_at=p.get("submitter_consent_at"),
                    submitter_name_fallback=str(p.get("prepared_by") or "").strip(),
                    fl_token=fl_token,
                )
            except Exception:  # pragma: no cover — best-effort audit
                pass

            return DailyReport(**report_dict)

        return await with_idempotency(db, key, {"role": "public"}, _do_create, workflow="daily_report")

    @api_router.get("/daily-reports", response_model=List[DailyReportSummary])
    async def list_daily_reports(actor=Depends(require_admin)):
        scope_query = await governance_project_scope_filter(db, actor)
        if scope_query is None:
            return []
        # TRACK 24.9 · Exclude synthetic/test records from user-
        # facing operational listings. Preserves audit history —
        # marked records remain in the collection with
        # `synthetic_record=true` / `hidden_from_operations=true`
        # so admin audit surfaces can still see them.
        match_stage = apply_synthetic_dr_exclusion(scope_query)
        pipeline = [
            {"$match": match_stage},
            {"$sort": {"created_at": -1}},
            {"$limit": 1000},
            {"$project": {
                "_id": 0, "id": 1, "project_name": 1, "project_number": 1,
                "location": 1, "report_date": 1, "prepared_by": 1,
                "weather_summary": 1, "created_at": 1,
                "photo_count":   {"$size": {"$ifNull": ["$photos", []]}},
                "crew_count":    {"$size": {"$ifNull": ["$masci_crews", []]}},
                "sub_count":     {"$size": {"$ifNull": ["$subcontractors", []]}},
                "visitor_count": {"$size": {"$ifNull": ["$visitors", []]}},
            }},
        ]
        docs = await db.daily_reports.aggregate(pipeline).to_list(1000)
        return [
            DailyReportSummary(
                id=d.get("id", ""),
                project_name=d.get("project_name", ""),
                project_number=d.get("project_number", ""),
                location=d.get("location", ""),
                report_date=d.get("report_date", ""),
                prepared_by=d.get("prepared_by", ""),
                weather_summary=d.get("weather_summary", ""),
                photo_count=d.get("photo_count", 0) or 0,
                crew_count=d.get("crew_count", 0) or 0,
                sub_count=d.get("sub_count", 0) or 0,
                visitor_count=d.get("visitor_count", 0) or 0,
                created_at=d.get("created_at", ""),
            )
            for d in docs
        ]

    @api_router.get("/daily-reports/next-number")
    async def next_daily_report_number(date: Optional[str] = None):
        """Return a canonical DR-YYYY-NNNNN preview for the given year.

        TRACK 22.4b-followup-DR · B-03 FINAL ELIMINATION.
        This endpoint previously returned a `DR-YYYYMMDD-NNN` shape
        derived by counting rows for the day. That shape never matched
        the atomic canonical `doc_id` (`DR-YYYY-NNNNN` from
        doc_id_counters), and the frontend pre-fill populated
        `report_number` with it — producing 271 legacy skew rows
        (`report_number != doc_id`).

        The endpoint now:
          - Returns the **canonical** shape only.
          - Peeks the atomic counter WITHOUT incrementing it (so the
            actual doc_id assigned on submit may be higher if other
            reports land first — this is a preview, not a reservation).
          - Publishes an `is_preview_only: True` flag so any client
            treating it as authoritative can be found by grepping.

        The write path (create_daily_report) ALWAYS overwrites
        `report_number` with the freshly-minted `doc_id`, so client
        pre-fill drift can no longer poison the persisted record.
        """
        from doc_ids import _year_for  # noqa: PLC0415
        year = _year_for(date)
        counter = await db.doc_id_counters.find_one({"_id": f"DR-{year}"}, {"_id": 0, "seq": 1})
        next_seq = int((counter or {}).get("seq") or 0) + 1
        canonical = f"DR-{year}-{next_seq:05d}"
        return {
            "report_number": canonical,
            "doc_id_preview": canonical,
            "prefix": f"DR-{year}-",
            "is_preview_only": True,
            "note": (
                "This is a preview only. The authoritative doc_id / "
                "report_number is minted atomically at submit time."
            ),
        }

    @api_router.get("/daily-reports/duplicate-check")
    async def daily_report_duplicate_check(
        project_number: str,
        report_date: str,
        submitted_by: Optional[str] = None,
    ) -> Dict[str, Any]:
        """TRACK 26.11 · pre-submit duplicate guard.

        Returns any existing Daily Report matching
        ``(project_number, report_date [, submitted_by])`` so the
        client can surface a "You already submitted a report for this
        project on this date — continue anyway?" dialog before minting
        another doc_id. Non-blocking; the client decides whether to
        proceed. Admin-authorized override is always available by
        simply calling submit anyway.

        Zero data change. Read-only. Returns a shallow row shape so
        the operator can see what already exists (report_number,
        doc_id, submitted_at, submitted_by).
        """
        pn = (project_number or "").strip()
        rd = (report_date or "").strip()
        if not pn or not rd:
            raise HTTPException(status_code=400, detail="project_number and report_date required")
        query: Dict[str, Any] = {"project_number": pn, "report_date": rd}
        if submitted_by:
            query["prepared_by"] = submitted_by.strip()
        # TRACK 28.02B · exclude synthetic rows so the foreman-facing
        # duplicate dialog never surfaces a certification fixture as
        # a real prior submit.
        query = apply_synthetic_dr_exclusion(query)
        # Bound the scan defensively — a real match should be at most 1
        # or a small handful (rare same-day resubmit).
        cursor = db.daily_reports.find(
            query,
            {
                "_id": 0,
                "id": 1,
                "doc_id": 1,
                "report_number": 1,
                "project_number": 1,
                "report_date": 1,
                "prepared_by": 1,
                "submitted_at": 1,
                "created_at": 1,
                "lifecycle_state": 1,
            },
        ).limit(10)
        existing: List[Dict[str, Any]] = []
        async for row in cursor:
            existing.append(row)
        return {
            "project_number": pn,
            "report_date": rd,
            "submitted_by_filter": submitted_by or None,
            "count": len(existing),
            "exists": len(existing) > 0,
            "matches": existing,
        }

    @api_router.get("/admin/draft-health")
    async def admin_draft_health(
        actor=Depends(require_admin),
    ) -> Dict[str, Any]:
        """TRACK 26.11 · Draft Health card feed for OCC.

        Aggregates client-side draft-telemetry into distinct logical
        draft entities where possible. Historical rows lacking
        ``meta.actorIdentity`` fall back to ``deviceId + formKey`` and
        are disclosed with reduced confidence rather than fabricated as
        precise unique drafts.
        """
        now = datetime.now(timezone.utc)
        since_30d = now - timedelta(days=30)
        grouped_rows: List[Dict[str, Any]] = []
        try:
            async for row in db.draft_telemetry.aggregate(_draft_health_aggregation_pipeline(since_30d)):
                grouped_rows.append(row)
        except Exception:  # noqa: BLE001
            grouped_rows = []

        summary = _summarize_draft_entities(grouped_rows, now=now)

        return {
            "generated_at": now.isoformat(),
            **summary,
            "kpi_metadata": {
                "kpi_name": "Daily Report Draft Health",
                "business_definition": "Distinct logical draft slots derived from draft telemetry, not raw append-only event counts.",
                "source_of_truth": "draft_telemetry",
                "api_endpoint": "/api/admin/draft-health",
                "formula": {
                    "entity_key": ["formKey", "deviceId", "meta.actorIdentity"],
                    "time_window_days": 30,
                    "open_definition": "latest event is not commit/discard and a successful save exists",
                },
                "confidence": summary.get("entity_confidence"),
                "status_reason": "Legacy telemetry without actor identity is disclosed with reduced confidence instead of being fabricated as precise unique drafts.",
                "drilldown_source": "/api/draft-telemetry/recent",
                "owner": "daily-report-resiliency",
            },
            "sources": {
                "collection": "draft_telemetry",
                "populated_by": "frontend useFormDraft via POST /api/draft-telemetry",
                "aggregation_window_days": 30,
            },
        }



    @api_router.get("/daily-reports/exposure-signals")
    async def daily_report_exposure_signals(
        days: int = 14,
        actor=Depends(require_admin),
    ):
        """Phase V.2 · Wave-1B · Calm PM exposure tile aggregator.

        Reads structured constraint rows from recent Daily Reports and
        returns aggregate signal counts. Signal only · never an alert ·
        never triggers an RFI / schedule entry / notification.

        Doctrine: PM_EXPOSURE_TILE_CERTIFICATION.md
        Calmness: ADVISORY_FLAG_CERTIFICATION.md §5
        """
        from datetime import datetime as _dt, timedelta as _td
        from collections import Counter
        cutoff = (_dt.utcnow() - _td(days=max(1, min(days, 90)))).strftime("%Y-%m-%d")
        scope_query = await governance_project_scope_filter(db, actor, base_filter={"report_date": {"$gte": cutoff}})
        if scope_query is None:
            return {
                "window_days": days,
                "reports_with_constraints": 0,
                "rfi_signal_count": 0,
                "schedule_signal_count": 0,
                "top_constraint_types": [],
                "recent_trend": [],
                "top_projects": [],
                "doctrine": "PM_EXPOSURE_TILE_CERTIFICATION.md",
                "kind": "signal_only",
            }
        # TRACK 28.02B · exclude synthetic/certification DRs — an admin
        # exposure rollup is a user-facing surface even for admins.
        q = apply_synthetic_dr_exclusion(scope_query)
        cur = db.daily_reports.find(
            q,
            {"_id": 0, "constraints": 1, "report_date": 1, "project_number": 1},
        ).sort("report_date", -1).limit(2000)

        rfi_signal = 0
        sched_signal = 0
        types = Counter()
        per_day = Counter()
        per_project = Counter()
        reports_with_constraints = 0
        async for row in cur:
            rows = row.get("constraints") or []
            if rows:
                reports_with_constraints += 1
            for c in rows:
                if not isinstance(c, dict):
                    continue
                t = c.get("constraint_type") or "other"
                types[t] += 1
                per_day[row.get("report_date") or "?"] += 1
                pn = row.get("project_number") or "?"
                per_project[pn] += 1
                if c.get("may_require_rfi"):
                    rfi_signal += 1
                if c.get("may_affect_schedule"):
                    sched_signal += 1

        # Sort top lists for the calm tile UI
        top_types = [
            {"constraint_type": k, "count": n}
            for k, n in types.most_common(5)
        ]
        recent_trend = [
            {"date": d, "count": n}
            for d, n in sorted(per_day.items(), reverse=True)[:7]
        ]
        top_projects = [
            {"project_number": k, "count": n}
            for k, n in per_project.most_common(5)
        ]
        return {
            "window_days": days,
            "reports_with_constraints": reports_with_constraints,
            "rfi_signal_count": rfi_signal,
            "schedule_signal_count": sched_signal,
            "top_constraint_types": top_types,
            "recent_trend": recent_trend,
            "top_projects": top_projects,
            "doctrine": "PM_EXPOSURE_TILE_CERTIFICATION.md",
            "kind": "signal_only",
        }

    @api_router.post("/daily-reports/photo-intelligence/draft")
    async def daily_report_draft_photo_intelligence(body: DraftPhotoIntelligenceBody):
        from services.photo_intelligence import (  # noqa: PLC0415
            enqueue_v1_draft,
            process_v1_draft,
            list_v1_draft_intelligence,
        )

        payload = dict(body.payload or {})
        draft_identity = str(body.form_key or "").strip()
        await enqueue_v1_draft(db, draft_identity, payload)
        if payload.get("photos"):
            await process_v1_draft(
                db,
                draft_identity=draft_identity,
                draft=payload,
            )
        return await list_v1_draft_intelligence(
            db,
            draft_identity=draft_identity,
            draft=payload,
        )

    # ── TRACK 22.9B · Photo Intelligence read endpoint ─────────────
    # Returns aggregated grounded observations for a submitted Daily
    # Report. Consumers: `DailySummaryAssist` (for enriched context)
    # and PM screens. Safe to hit anonymously — no confidential data is
    # returned beyond what the field supervisor already entered/uploaded.
    @api_router.get("/daily-reports/{report_id}/photo-intelligence")
    async def daily_report_photo_intelligence(report_id: str):
        from services.photo_intelligence import (  # noqa: PLC0415
            list_v1_report_intelligence,
        )
        return await list_v1_report_intelligence(db, report_id)

    # ── TRACK 24.13 · Evidence Manifest read endpoint ──────────────
    # Builds an on-demand Evidence Manifest for a submitted Daily
    # Report. Combines:
    #   · typed supervisor fields from the DR record
    #   · aggregated photo intelligence
    #   · document extraction results for every attachment we can find
    #     (inline `attachments[]` on the DR + linked `db.docs` rows
    #      whose `project_id` matches)
    # Read-only. Never mutates the source DR. Extraction is cached
    # inside the extractor implementation.
    @api_router.get("/daily-reports/{report_id}/evidence-manifest")
    async def daily_report_evidence_manifest(report_id: str):
        from services.dr_evidence import (  # noqa: PLC0415
            build_manifest, manifest_hash,
        )
        from services.photo_intelligence import (  # noqa: PLC0415
            list_v1_report_intelligence,
        )
        row = await db.daily_reports.find_one({"id": report_id}, {"_id": 0})
        if not row:
            # Also accept doc_id lookup (DR-2026-NNNNN form).
            row = await db.daily_reports.find_one(
                {"doc_id": report_id}, {"_id": 0},
            )
        if not row:
            raise HTTPException(404, f"Daily report not found: {report_id}")

        photo_intel = await list_v1_report_intelligence(
            db, row.get("doc_id") or report_id,
        )
        # Attachment extractions — supervisors can drop attachments
        # directly on the DR (`attachments[]` inline metadata) but the
        # raw bytes may live on `db.docs`. For now we surface every
        # inline attachment; extracted bytes are optional and handled
        # by whichever tooling wrote the extraction result. If a caller
        # wants live extraction they can POST bytes to the extraction
        # endpoint below.
        att_ext = row.get("attachment_extractions") or []
        manifest = build_manifest(
            row,
            attachment_extractions=att_ext,
            photo_intel=photo_intel,
        )
        payload = manifest.to_dict()
        payload["manifest_hash"] = manifest_hash(manifest)
        return payload

    # ── TRACK 24.13 · One-shot attachment extraction probe ─────────
    # Accepts a base64-encoded file body and returns the extraction
    # envelope (status, text preview, row/page counts, warnings). Used
    # by the DR submit UI to show a live preview of "what the AI can
    # see" before the PM commits the report. NEVER stores the file.
    @api_router.post("/daily-reports/evidence/extract")
    async def daily_report_extract_attachment(payload: Dict[str, Any] = Body(...)):
        from services.dr_evidence import extract_attachment  # noqa: PLC0415
        import base64  # noqa: PLC0415
        filename = str(payload.get("filename") or "")
        mime = str(payload.get("mime") or "")
        b64 = payload.get("data_base64") or ""
        try:
            data = base64.b64decode(b64) if b64 else b""
        except Exception as e:  # noqa: BLE001
            raise HTTPException(
                400, f"invalid base64: {e.__class__.__name__}",
            ) from e
        result = extract_attachment(filename=filename, mime=mime, data=data)
        return result.to_dict()

    @api_router.get("/daily-reports/{report_id}/audit-footer")
    async def daily_report_audit_footer(
        report_id: str,
        actor=Depends(require_admin),  # noqa: ARG001
    ):
        """Phase V.2 · Wave-1A · DR audit footer.

        Returns SHA256 + continuity ID + rendered timestamp for the
        Daily Report. Footer payload is consumed by the PDF renderer
        and any external audit/claims surface.

        Doctrine: DAILY_REPORT_AUDIT_FOOTER_CERTIFICATION.md
        """
        row = await db.daily_reports.find_one({"id": report_id}, {"_id": 0})
        if not row:
            raise HTTPException(404, f"Daily report not found: {report_id}")
        # Always recompute from current envelope so the response reflects
        # the actual canonical content shape, not a stored cache.
        sha = _compute_audit_envelope_sha256(row)
        rendered_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")
        footer = (
            f"Official Record · {row.get('doc_id', '')} "
            f"· sha256={sha[:16]} · rendered {rendered_at}"
        )
        return {
            "report_id": report_id,
            "doc_id": row.get("doc_id", ""),
            "sha256": sha,
            "rendered_at_utc": rendered_at,
            "footer_text": footer,
        }

    @api_router.get("/daily-reports.csv", status_code=202)
    async def list_daily_reports_csv(
        actor=Depends(require_admin),
        background_tasks: BackgroundTasks = None,
    ):
        """Phase 5 · W8 · CSV export of daily reports.

        Same auth gate + same PM scope as the JSON list. No write peer.

        TRACK 28.02B (2026-02) — routes the aggregation through
        ``apply_synthetic_dr_exclusion`` so synthetic / certification /
        smoke-test rows (``TEST_``, ``SMOKE_``, ``synthetic_record``,
        ``hidden_from_operations``) are filtered out of the export.
        The JSON list already applies this filter; the CSV export was
        leaking the hidden lane. Locked by
        ``tests/test_track_28_02b_field_ops_e2e.py::test_daily_report_full_e2e``.
        """
        job = await create_async_job(
            "daily_reports_csv_export",
            result_type="binary",
            message="Preparing Daily Reports export…",
            details={"format": "csv"},
        )
        if background_tasks is not None:
            background_tasks.add_task(_run_daily_reports_csv_job, db, str(job.get("job_id")), actor)
        return {
            "ok": True,
            "job_id": job.get("job_id"),
            "kind": job.get("kind"),
            "status": "queued",
            "status_url": f"/api/jobs/{job.get('job_id')}/status",
            "poll_after_ms": 1400,
            "message": job.get("message"),
            "details": job.get("details") or {},
        }

    # TRACK 15.13E — fall back to `require_admin` when the new HR-read
    # gate isn't supplied (keeps existing test harness imports working).
    _read_dep = require_admin_pm_or_hr_read or require_admin

    @api_router.get("/daily-reports/{report_id}")
    async def get_daily_report(report_id: str, actor=Depends(_read_dep)):
        doc = await db.daily_reports.find_one({"id": report_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Daily report not found")
        if not await governance_project_scope_allows(db, actor, doc.get("project_number")):
            raise HTTPException(status_code=404, detail="Daily report not found")
        is_global_scope = (await governance_project_scope_filter(db, actor, base_filter={})) == {}
        if bool(doc.get("hidden_from_operations")) and not is_global_scope:
            raise HTTPException(status_code=404, detail="Daily report not found")
        try:
            from services.project_schedule_actuals_spine import list_schedule_actual_candidates_for_report  # noqa: PLC0415

            schedule_actual_candidates = await list_schedule_actual_candidates_for_report(db, report_id)
            doc["schedule_actual_candidates"] = schedule_actual_candidates
            doc["schedule_actual_candidate_summary"] = {
                "count": len(schedule_actual_candidates),
                "pending": sum(1 for row in schedule_actual_candidates if row.get("review_status") in {"pending_review", "review_required", "deferred"}),
                "approved": sum(1 for row in schedule_actual_candidates if row.get("review_status") == "approved"),
            }
        except Exception:  # noqa: BLE001
            doc.setdefault("schedule_actual_candidates", [])
            doc.setdefault("schedule_actual_candidate_summary", {"count": 0, "pending": 0, "approved": 0})
        return _sanitize_daily_report_for_actor(doc, actor)

    @api_router.delete("/daily-reports/{report_id}")
    async def delete_daily_report(report_id: str, _: bool = Depends(require_admin)):
        # ── Phase V.1 · M1 · Daily Report Delete Freeze ─────────────────
        # Per operator directive (2026-05-29 · Option C approval):
        #   "Historical reports remain accessible forever. No edits.
        #    No deletes. No conversion. No mutation."
        # The historical archive is canonical operational evidence.
        # Discovery against signed Daily Reports requires byte-identical
        # preservation. Hard delete is forbidden post-M1 cutover.
        raise HTTPException(
            status_code=410,
            detail={
                "error": "daily_report_delete_frozen",
                "message": (
                    "Daily Reports are preserved as the historical record. "
                    "Hard delete is no longer permitted. Records remain "
                    "accessible read-only."
                ),
                "doctrine": "LEGACY_RECORD_FREEZE_CERTIFICATION.md",
                "report_id": report_id,
            },
        )
