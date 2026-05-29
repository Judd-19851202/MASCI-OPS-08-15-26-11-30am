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
from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, ConfigDict, Field

from pm_auth import compute_pm_scope


# ── Phase V.2 · Wave-1A · Structured production + constraints ────────


_PRODUCTION_UNITS = {"LF", "SY", "CY", "TON", "EA", "ACRE", "OTHER"}
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
    """
    model_config = ConfigDict(extra="forbid")

    row_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    description: str = ""                       # what was placed/installed/poured
    quantity: float = 0.0                       # > 0 when row has substance
    unit: Literal["LF", "SY", "CY", "TON", "EA", "ACRE", "OTHER"] = "OTHER"
    custom_unit_label: Optional[str] = None     # only when unit == "OTHER"
    station_from: Optional[str] = None          # e.g. "12+50"
    station_to: Optional[str] = None            # e.g. "13+00"
    location: Optional[str] = None              # free-text fallback for non-station jobs
    notes: Optional[str] = None                 # ≤ 280 chars · voice or text


class ConstraintRow(BaseModel):
    """One structured constraint/delay entry on a Daily Report."""
    model_config = ConfigDict(extra="forbid")

    row_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    constraint_type: Literal[
        "weather", "utility", "survey", "material", "equipment",
        "trucking", "mot", "cei_inspection", "owner_engineer",
        "safety", "other",
    ] = "other"
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

    # Phase V.2 · Wave-1A · structured production + constraints.
    production: List[ProductionRow] = Field(default_factory=list)
    constraints: List[ConstraintRow] = Field(default_factory=list)

    photos: List[str] = Field(default_factory=list)

    prepared_by_signature: Optional[str] = ""
    superintendent_signature: Optional[str] = ""
    distribution_list: Optional[List[str]] = Field(default=None, max_length=20)


class DailyReport(DailyReportCreate):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    doc_id: Optional[str] = ""  # human-readable: DR-YYYY-NNNNN, stamped on insert
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    # Wave-1A · audit envelope. Computed at insert; never client-supplied.
    audit_envelope_sha256: Optional[str] = ""


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


def register_daily_reports_routes(api_router: APIRouter, db, require_admin, rate_limit_public_post, schedule_auto_email):
    """Attach Daily Report endpoints to the shared router."""

    @api_router.post("/daily-reports", response_model=DailyReport, dependencies=[Depends(rate_limit_public_post)])
    async def create_daily_report(payload: DailyReportCreate, request: Request):
        # ── Phase V.2 · Wave-1A · POST RESTORED (M1 freeze partial revert) ──
        # Per operator directive (2026-05-29 · Wave-1A authorization):
        #   "Restore POST /api/daily-reports. Keep DELETE = 410."
        # Doctrine: /app/memory/WAVE_1A_IMPLEMENTATION_REPORT.md
        # Idempotent submit (Phase J · Field Resiliency) preserved.
        from lib.idempotency import with_idempotency, idem_key_from_request  # noqa: PLC0415
        key = idem_key_from_request(request)

        async def _do_create():
            report = DailyReport(**payload.model_dump())
            # Wave-1A · advisory flag derivation (deterministic · operator-defined).
            _derive_advisory_flags(report)
            doc = report.model_dump()
            # Stamp human-readable doc ID (DR-2026-00001) so the form, the PDF,
            # and the admin search bar can all reference the same number.
            from doc_ids import ensure_doc_id  # local import to keep startup fast
            await ensure_doc_id(db, doc, "DR", when=doc.get("report_date") or doc.get("created_at"))
            report.doc_id = doc["doc_id"]
            # Wave-1A · audit envelope hash (continuity + tamper detection).
            doc["audit_envelope_sha256"] = _compute_audit_envelope_sha256(doc)
            report_dict = report.model_dump()
            report_dict["audit_envelope_sha256"] = doc["audit_envelope_sha256"]
            await db.daily_reports.insert_one(doc)
            doc.pop("_id", None)
            # Mirror photos into the Job Photos library (Phase 1 read-only).
            try:
                from routes.job_photos import index_record_photos
                await index_record_photos(db, "daily_report", doc)
            except Exception:
                pass  # never block a submit on indexing
            schedule_auto_email("daily-report", doc)
            return DailyReport(**report_dict)

        return await with_idempotency(db, key, {"role": "public"}, _do_create)

    @api_router.get("/daily-reports", response_model=List[DailyReportSummary])
    async def list_daily_reports(actor=Depends(require_admin)):
        scope = await compute_pm_scope(db, actor)
        pipeline = [
            {"$match": scope.filter({})},
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
        """Return the next available DR-YYYYMMDD-NNN for the given (or today's) date."""
        d = (date or datetime.now(timezone.utc).strftime("%Y-%m-%d")).replace("-", "")
        prefix = f"DR-{d}-"
        n = await db.daily_reports.count_documents({"report_number": {"$regex": f"^{prefix}"}})
        return {"report_number": f"{prefix}{n + 1:03d}", "prefix": prefix}

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

        Same auth gate + same PM scope as the JSON list. No write peer."""
        import csv as _csv  # noqa: PLC0415
        import io as _io    # noqa: PLC0415
        from fastapi.responses import Response as _Resp  # noqa: PLC0415
        scope = await compute_pm_scope(db, actor)
        pipeline = [
            {"$match": scope.filter({})},
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

    @api_router.get("/daily-reports/{report_id}")
    async def get_daily_report(report_id: str, actor=Depends(require_admin)):
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
