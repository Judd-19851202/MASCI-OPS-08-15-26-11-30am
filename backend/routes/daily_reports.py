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
    async def create_daily_report(payload: DailyReportCreate, request: Request):
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
            report = DailyReport(**payload.model_dump())
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
            # Stamp human-readable doc ID (DR-2026-00001) so the form, the PDF,
            # and the admin search bar can all reference the same number.
            from doc_ids import ensure_doc_id  # local import to keep startup fast
            await ensure_doc_id(db, doc, "DR", when=doc.get("report_date") or doc.get("created_at"))
            report.doc_id = doc["doc_id"]
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
        q = scope.filter({"report_date": {"$gte": cutoff}})
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
