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
import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, BackgroundTasks, Body, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from pm_auth import compute_pm_scope
from lib.synthetic_dr_filter import apply_synthetic_dr_exclusion


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

    photos: List[str] = Field(default_factory=list)

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


def _apply_certification_record_safety(doc: Dict[str, Any]) -> Dict[str, Any]:
    if not bool(doc.get("certification_record")):
        return doc
    doc["certification_record"] = True
    doc["synthetic_record"] = True
    doc["hidden_from_operations"] = True
    doc["email_dispatch_suppressed"] = True
    return doc


def _should_schedule_daily_report_email(doc: Dict[str, Any]) -> bool:
    return not bool(doc.get("certification_record") or doc.get("email_dispatch_suppressed"))


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
                    "message": "Approved executive summary is missing the approval timestamp.",
                },
            )
        if _accepted_source not in {"ai", "edited", "fallback", "manual"}:
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "approved_summary_source_invalid",
                    "message": "Approved executive summary is missing a valid source label.",
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
            # Wave-1A · audit envelope hash (continuity + tamper detection).
            doc["audit_envelope_sha256"] = _compute_audit_envelope_sha256(doc)
            # Build the response dict from the sanitized doc so the API
            # response matches what was persisted (refs not inline).
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
        scope = await compute_pm_scope(db, actor)
        # TRACK 24.9 · Exclude synthetic/test records from user-
        # facing operational listings. Preserves audit history —
        # marked records remain in the collection with
        # `synthetic_record=true` / `hidden_from_operations=true`
        # so admin audit surfaces can still see them.
        match_stage = apply_synthetic_dr_exclusion(scope.filter({}))
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

        Aggregates client-side draft-telemetry pings into a compact
        health snapshot. Read-only. Backed by the pre-existing
        ``draft_telemetry`` collection populated by
        ``/api/draft-telemetry`` calls from ``useFormDraft``.

        Buckets:
          - active drafts (last save < 1 h)
          - stale drafts (1h < last save < 24h)
          - abandoned drafts (last save > 24h)
          - failed drafts (last event kind = draft.save.failed)
          - quota-pressured drafts (any quota.warn event in last 24h)
        """
        now = datetime.now(timezone.utc)
        hour_ago = now - timedelta(hours=1)
        day_ago = now - timedelta(days=1)

        async def _count(query: Dict[str, Any]) -> int:
            try:
                return int(await db.draft_telemetry.count_documents(query))
            except Exception:  # noqa: BLE001
                return 0

        buckets: Dict[str, Any] = {
            "active_lt_1h": await _count(
                {"kind": "draft.save.ok", "ts": {"$gte": hour_ago.isoformat()}}
            ),
            "stale_1h_to_24h": await _count({
                "kind": "draft.save.ok",
                "ts": {"$gte": day_ago.isoformat(), "$lt": hour_ago.isoformat()},
            }),
            "abandoned_gt_24h": await _count({
                "kind": "draft.save.ok",
                "ts": {"$lt": day_ago.isoformat()},
            }),
            "failed_last_24h": await _count({
                "kind": "draft.save.failed",
                "ts": {"$gte": day_ago.isoformat()},
            }),
            "quota_warn_last_24h": await _count({
                "kind": "draft.quota.warn",
                "ts": {"$gte": day_ago.isoformat()},
            }),
            "restore_offered_last_24h": await _count({
                "kind": "draft.restore.offered",
                "ts": {"$gte": day_ago.isoformat()},
            }),
            "restore_action_last_24h": await _count({
                "kind": "draft.restore.action",
                "ts": {"$gte": day_ago.isoformat()},
            }),
        }

        # Per-form counts (which module drafts are most active).
        per_form: Dict[str, int] = {}
        try:
            pipeline = [
                {"$match": {"kind": "draft.save.ok", "ts": {"$gte": day_ago.isoformat()}}},
                {"$group": {"_id": "$formKey", "n": {"$sum": 1}}},
                {"$sort": {"n": -1}},
                {"$limit": 20},
            ]
            async for row in db.draft_telemetry.aggregate(pipeline):
                per_form[str(row.get("_id") or "unknown")] = int(row.get("n") or 0)
        except Exception:  # noqa: BLE001
            per_form = {}

        return {
            "generated_at": now.isoformat(),
            "buckets": buckets,
            "per_form_last_24h": per_form,
            "sources": {
                "collection": "draft_telemetry",
                "populated_by": "frontend useFormDraft via POST /api/draft-telemetry",
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
        scope = await compute_pm_scope(db, actor)
        # TRACK 28.02B · exclude synthetic/certification DRs — an admin
        # exposure rollup is a user-facing surface even for admins.
        q = apply_synthetic_dr_exclusion(scope.filter({"report_date": {"$gte": cutoff}}))
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

    @api_router.get("/daily-reports.csv")
    async def list_daily_reports_csv(actor=Depends(require_admin)):
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
        import csv as _csv  # noqa: PLC0415
        import io as _io    # noqa: PLC0415
        from fastapi.responses import Response as _Resp  # noqa: PLC0415
        scope = await compute_pm_scope(db, actor)
        match_stage = apply_synthetic_dr_exclusion(scope.filter({}))
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
                "crew_count":    {"$size": {"$ifNull": ["$masci_crews", []]}},
                "sub_count":     {"$size": {"$ifNull": ["$subcontractors", []]}},
                "visitor_count": {"$size": {"$ifNull": ["$visitors", []]}},
                "photo_count":   {"$size": {"$ifNull": ["$photos", []]}},
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
        return _Resp(
            content=buf.getvalue(),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": 'attachment; filename="daily_reports.csv"',
                "Cache-Control": "private, no-store",
            },
        )

    # TRACK 15.13E — fall back to `require_admin` when the new HR-read
    # gate isn't supplied (keeps existing test harness imports working).
    _read_dep = require_admin_pm_or_hr_read or require_admin

    @api_router.get("/daily-reports/{report_id}")
    async def get_daily_report(report_id: str, actor=Depends(_read_dep)):
        doc = await db.daily_reports.find_one({"id": report_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Daily report not found")
        scope = await compute_pm_scope(db, actor)
        if not scope.allows(doc.get("project_number")):
            raise HTTPException(status_code=404, detail="Daily report not found")
        return doc

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
