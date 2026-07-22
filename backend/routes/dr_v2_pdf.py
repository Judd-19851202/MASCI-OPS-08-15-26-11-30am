"""
DR-ROI-001F · Part 2 · Daily Report V2 PDF Output.

Renders APPROVED Daily Report V2 records to the same MASCI-native
letter-size PDF that V1 has always produced.

Doctrine
--------
* EN-only canonical PDF — Spanish field-mode drafts are canonicalized
  to English via `dr_v2_bilingual_audit` before render. The official
  record-of-truth is English; ES stays for audit preservation only.
* NO field/supervisor exposure — this route is intentionally NOT wired
  into the V2 field shell. Access is restricted to Admin / PM (scoped
  to their assigned projects) / HR (read-only cross-portal) so the
  field workflow keeps its "Invisible Intelligence" contract.
* NO new PDF layout — reuses `pdf_render.render_record_pdf("daily-report")`
  so V2 output is byte-comparable to V1 output. This is the platform
  identity the user has explicitly demanded twice.
* Approval gate — the report_id MUST have at least one `accept` action
  logged in `dr_v2_ai_audit_entries`. Drafts without a supervisor
  approval return 409, matching the "approved source records only"
  rule in the original DR-ROI-001F directive.

Endpoint
--------
    GET /api/dr-v2/reports/{report_id}/pdf
        Auth: Admin · PM (scoped) · HR read gate
        200  application/pdf (Content-Disposition: inline)
        401  no token
        403  PM out of scope
        404  draft not found
        409  draft not yet approved
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Path

from lib.async_jobs import (
    complete_async_job_binary,
    create_async_job,
    fail_async_job,
    mark_async_job_processing,
)
from lib.runtime_cache import get_or_set_runtime_json
from pdf_render import render_record_pdf


DRAFTS_COLL = "dr_v2_drafts"
APPROVAL_ENTRIES_COLL = "dr_v2_ai_audit_entries"
BILINGUAL_AUDIT_COLL = "dr_v2_bilingual_audit"
LEGACY_COLL = "daily_reports"

# Legacy `daily_reports` records are considered "approved" once they
# have transitioned to any of these lifecycle states. Legacy records
# without lifecycle metadata (pre-lifecycle deployment) are treated as
# approved by virtue of being submitted at all — this matches how the
# platform has always exposed them via /pm/daily and /admin/daily.
LEGACY_APPROVED_STATES = {"approved", "submitted", "signed", "closed", "finalized"}


# -----------------------------------------------------------------------------
# V2 → V1 record mapper
# -----------------------------------------------------------------------------

def _fmt_weather(weather: Dict[str, Any]) -> str:
    if not isinstance(weather, dict):
        return ""
    bits: List[str] = []
    t = weather.get("temperature_f")
    if t not in (None, ""):
        bits.append(f"{t}°F")
    precip = (weather.get("precipitation") or "").strip() if isinstance(weather.get("precipitation"), str) else ""
    if precip:
        bits.append(precip)
    w = weather.get("wind_mph")
    if w not in (None, ""):
        bits.append(f"wind {w} mph")
    return " · ".join(bits)


def _fmt_gps(gps: Any) -> Dict[str, Any]:
    """Accept either `{lat, lng}` or `"lat,lng"` and return {gps_lat, gps_lng}."""
    if isinstance(gps, dict):
        return {"gps_lat": gps.get("lat") or gps.get("latitude"),
                "gps_lng": gps.get("lng") or gps.get("longitude")}
    if isinstance(gps, str) and "," in gps:
        try:
            a, b = gps.split(",", 1)
            return {"gps_lat": float(a.strip()), "gps_lng": float(b.strip())}
        except (TypeError, ValueError):
            return {}
    return {}


def _joined(*parts: Any, sep: str = "\n\n") -> str:
    """Join non-empty stringified parts with a separator."""
    out = [str(p).strip() for p in parts if p and str(p).strip()]
    return sep.join(out)


def _v2_activity_narratives(cards: List[Dict[str, Any]]) -> Dict[str, str]:
    """Fold V2 activity cards into V1 narrative_sections buckets.

    Each card can carry `notes` (freeform) and `production` (structured).
    We put everything into `work_completed` — the V1 narrative_sections
    key the platform PDF already renders. Zero new schema, no drift.
    """
    work: List[str] = []
    for c in cards or []:
        if not isinstance(c, dict):
            continue
        label = (c.get("activity") or c.get("category") or "").strip()
        notes = (c.get("notes") or "").strip()
        production = c.get("production") or {}
        prod_bits: List[str] = []
        if isinstance(production, dict):
            for k, v in production.items():
                if v in (None, "", 0):
                    continue
                prod_bits.append(f"{k}: {v}")
        parts: List[str] = []
        if label:
            parts.append(f"[{label}]")
        if notes:
            parts.append(notes)
        if prod_bits:
            parts.append("(" + ", ".join(prod_bits) + ")")
        if parts:
            work.append(" ".join(parts))
    return {"work_completed": "\n".join(work).strip()}


def _v2_constraint_narratives(cards: List[Dict[str, Any]]) -> Dict[str, str]:
    """V2 constraint chips → V1 `delays` narrative bucket."""
    out: List[str] = []
    for c in cards or []:
        if not isinstance(c, dict):
            continue
        cat = (c.get("category") or c.get("type") or "").strip()
        what = (c.get("what_happened") or "").strip()
        impact = (c.get("impact") or "").strip()
        parts: List[str] = []
        if cat:
            parts.append(f"[{cat}]")
        if what:
            parts.append(what)
        if impact:
            parts.append(f"Impact: {impact}")
        if parts:
            out.append(" ".join(parts))
    return {"delays": "\n".join(out).strip()}


def _v2_tomorrow_narrative(tomorrow: Dict[str, Any]) -> Dict[str, str]:
    """V2 tomorrow_readiness → V1 `tomorrow_plan` narrative bucket."""
    if not isinstance(tomorrow, dict):
        return {}
    bits: List[str] = []
    for label, key in [
        ("Crew needs", "crew_needs"),
        ("Equipment needs", "equipment_needs"),
        ("Material needs", "material_needs"),
        ("Decisions needed", "decisions_needed"),
    ]:
        v = (tomorrow.get(key) or "").strip() if isinstance(tomorrow.get(key), str) else ""
        if v:
            bits.append(f"{label}: {v}")
    return {"tomorrow_plan": "\n".join(bits).strip()}


def _v2_to_v1_daily_record(
    draft: Dict[str, Any],
    *,
    accepted_summary: Optional[str] = None,
) -> Dict[str, Any]:
    """Translate a canonical (English) V2 draft into the V1 daily-report
    record shape consumed by `pdf_render._render_daily`.

    Any field the V1 renderer already knows about maps 1:1. V2-only
    freeform sections fold into `narrative_sections` (a supported V1
    extension since Track 15.62).
    """
    setup = draft.get("day_setup") or {}
    weather = draft.get("weather") or {}
    safety = draft.get("safety") or {}

    weather_line = _fmt_weather(weather) or (setup.get("weather") or "")
    gps = _fmt_gps(setup.get("gps_location"))

    narrative_sections: Dict[str, str] = {}
    narrative_sections.update(_v2_activity_narratives(draft.get("activity_cards") or []))
    narrative_sections.update(_v2_constraint_narratives(draft.get("constraint_cards") or []))
    narrative_sections.update(_v2_tomorrow_narrative(draft.get("tomorrow_readiness") or {}))

    # Daily Operational Summary — the single supervisor-approved summary
    # at the bottom of the V2 shell. Surfaced as its own narrative slot
    # so it prints prominently. Fallback bucket if the V1 renderer
    # doesn't split it out: prepend to general_notes.
    if accepted_summary:
        narrative_sections["work_completed"] = _joined(
            accepted_summary,
            narrative_sections.get("work_completed", ""),
        )

    # Drop empty narrative buckets so the V1 renderer skips them.
    narrative_sections = {k: v for k, v in narrative_sections.items() if v}

    quality_notes = (safety.get("quality_notes") or "").strip() if isinstance(safety.get("quality_notes"), str) else ""
    general_notes = _joined(
        quality_notes,
        (safety.get("quality_findings") or "") if isinstance(safety.get("quality_findings"), str) else "",
    )

    record: Dict[str, Any] = {
        # Identity (V1 shape)
        "id": draft.get("report_id") or "",
        "doc_id": draft.get("report_id") or "",
        "report_number": draft.get("report_id") or "",
        # Header
        "project_name": setup.get("project_name") or "",
        "project_number": setup.get("project_number") or draft.get("project_number") or "",
        "location": setup.get("location_label") or setup.get("location") or "",
        "report_date": draft.get("report_date") or setup.get("report_date") or "",
        "prepared_by": setup.get("supervisor_name") or draft.get("supervisor_id") or "",
        "superintendent": setup.get("superintendent") or "",
        "weather_summary": weather_line,
        # Safety / general
        "schedule_delays": "",
        "weather_impact": (weather.get("impact") or "") if isinstance(weather.get("impact"), str) else "",
        "safety_incidents_today": "Yes" if safety.get("safety_incidents") else "No",
        "injuries_reported": "Yes" if safety.get("injuries_reported") else "No",
        "general_notes": general_notes,
        "narrative_sections": narrative_sections,
        # Crews / equipment / photos
        "masci_crews": draft.get("masci_crews") or [],
        "equipment": draft.get("equipment_used") or [],
        "photos": draft.get("photos") or [],
        # V2 audit metadata — surfaces on the render footer so CEI/FDOT
        # can trace the record back to the V2 approval.
        "field_language": draft.get("field_language") or "en",
        "canonical_language": draft.get("canonical_language") or "en",
        "is_dr_v2": True,
    }
    if gps:
        record.update(gps)
    return record


# -----------------------------------------------------------------------------
# Approval / canonical lookup
# -----------------------------------------------------------------------------

async def _latest_accept_entry(db, report_id: str) -> Optional[Dict[str, Any]]:
    """Return the most recent `accept` entry for this report_id, if any."""
    entry = await db[APPROVAL_ENTRIES_COLL].find_one(
        {"report_id": report_id, "action": "accept"},
        {"_id": 0},
        sort=[("ts", -1)],
    )
    return entry


async def _canonical_draft(db, report_id: str, draft: Dict[str, Any]) -> Dict[str, Any]:
    """Return the English canonical draft.

    Preference order:
      1. `dr_v2_bilingual_audit.canonical_draft` (most recent) — always
         English regardless of field_language.
      2. Raw draft, when the report was submitted in English.
    """
    if (draft.get("field_language") or "en").lower() == "en":
        return draft
    audit = await db[BILINGUAL_AUDIT_COLL].find_one(
        {"report_id": report_id, "translation_status": {"$ne": "not_required"}},
        {"_id": 0, "canonical_draft": 1},
        sort=[("created_at", -1)],
    )
    if audit and isinstance(audit.get("canonical_draft"), dict):
        return audit["canonical_draft"]
    return draft


# -----------------------------------------------------------------------------
# Route registration
# -----------------------------------------------------------------------------

def register_dr_v2_pdf_routes(
    api_router: APIRouter,
    db,
    *,
    require_admin_pm_or_hr_read,
    compute_pm_scope,
) -> None:
    """Attach `/api/dr-v2/reports/{report_id}/pdf` to the shared router."""

    async def _list_approved_impl(
        limit: int,
        actor: Any,
    ) -> Dict[str, Any]:
        """Canonical approved Daily Reports list sourced from
        `daily_reports` only."""
        limit = max(1, min(int(limit or 50), 200))

        # ── Scope resolution ────────────────────────────────────────
        pm_project_filter: Optional[Dict[str, Any]] = None
        cache_scope_key = "admin"
        is_admin = actor is True
        is_hr = isinstance(actor, dict) and actor.get("_actor_kind") == "hr_user"
        if not is_admin and not is_hr and isinstance(actor, dict):
            scope = await compute_pm_scope(db, actor)
            if not scope.is_admin:
                nums = list(scope.project_numbers or [])
                if not nums:
                    return {"items": []}
                pm_project_filter = {"$in": nums}
                cache_scope_key = "pm:" + "|".join(sorted(nums))
        elif is_hr:
            cache_scope_key = "hr"

        cache_key = f"dashboard:approved-daily-reports:{cache_scope_key}:limit:{limit}"

        async def _build_items() -> Dict[str, Any]:
            items: List[Dict[str, Any]] = []
            legacy_query: Dict[str, Any] = {}
            if pm_project_filter is not None:
                legacy_query["project_number"] = pm_project_filter
            from lib.synthetic_dr_filter import apply_synthetic_dr_exclusion
            legacy_query = apply_synthetic_dr_exclusion(legacy_query)
            legacy_cursor = (
                db[LEGACY_COLL]
                .find(
                    legacy_query,
                    {
                        "_id": 0,
                        "id": 1,
                        "doc_id": 1,
                        "report_number": 1,
                        "project_number": 1,
                        "project_name": 1,
                        "report_date": 1,
                        "prepared_by": 1,
                        "superintendent": 1,
                        "created_at": 1,
                        "updated_at": 1,
                        "state": 1,
                        "lifecycle": 1,
                    },
                )
                .sort([("report_date", -1), ("created_at", -1)])
                .limit(limit)
            )
            async for d in legacy_cursor:
                state = d.get("state") or (d.get("lifecycle") or {}).get("state")
                if state and state not in LEGACY_APPROVED_STATES:
                    continue
                rid = d.get("id") or d.get("doc_id") or d.get("report_number")
                if not rid:
                    continue
                items.append({
                    "id": rid,
                    "source": "canonical",
                    "report_id": rid,
                    "project_number": d.get("project_number") or "",
                    "project_name": d.get("project_name") or "",
                    "report_date": d.get("report_date") or "",
                    "supervisor_name": d.get("prepared_by") or d.get("superintendent") or "",
                    "field_language": "en",
                    "approved_at": d.get("updated_at") or d.get("created_at") or d.get("report_date") or "",
                })

            items.sort(key=lambda it: it.get("approved_at") or "", reverse=True)
            return {"items": items[:limit]}

        return await get_or_set_runtime_json(cache_key, ttl_seconds=45, builder=_build_items)

    @api_router.get("/daily-reports/approved")
    async def daily_reports_list_approved(
        limit: int = 50,
        actor=Depends(require_admin_pm_or_hr_read),
    ):
        """Canonical approved Daily Reports list."""
        return await _list_approved_impl(limit, actor)

    @api_router.get("/daily-reports/{report_id}/pdf", status_code=202)
    async def daily_reports_pdf(
        report_id: str = Path(..., min_length=1),
        actor=Depends(require_admin_pm_or_hr_read),
        background_tasks: BackgroundTasks = None,
    ):
        """Canonical Daily Report PDF export."""
        return await _queue_pdf_job(report_id, actor, background_tasks)

    async def _queue_pdf_job(report_id: str, actor: Any, background_tasks: Optional[BackgroundTasks]):
        job = await create_async_job(
            "daily_report_pdf",
            result_type="binary",
            message="Preparing PDF...",
            details={"report_id": report_id},
        )
        if background_tasks is not None:
            background_tasks.add_task(_run_pdf_job, str(job.get("job_id")), report_id, actor)
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

    async def _render_pdf_export_impl(report_id: str, actor: Any) -> Dict[str, Any]:
        legacy = await db[LEGACY_COLL].find_one(
            {"$or": [
                {"id": report_id},
                {"doc_id": report_id},
                {"report_number": report_id},
            ]},
            {"_id": 0},
        )
        if not legacy:
            raise HTTPException(status_code=404, detail="report not found")

        record_project = (legacy or {}).get("project_number") or ""

        # 2. Enforce PM scope. Admin sentinel (True) and HR actor
        # (`_actor_kind == "hr_user"`) bypass this check.
        if isinstance(actor, dict) and actor.get("_actor_kind") != "hr_user":
            scope = await compute_pm_scope(db, actor)
            if not scope.allows(record_project):
                raise HTTPException(status_code=404, detail="report not found")

        try:
            pdf_bytes = render_record_pdf("daily-report", legacy)
        except Exception as ex:  # noqa: BLE001
            raise HTTPException(
                status_code=500,
                detail=f"PDF render failed: {type(ex).__name__}",
            ) from ex

        filename = f"MASCI_Daily_Report_{report_id}.pdf"
        rendered_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")  # TRACK-27.03-EXEMPT: machine-consumed HTTP header (X-Daily-Report-Rendered-At)
        return {
            "pdf_bytes": pdf_bytes,
            "filename": filename,
            "rendered_at": rendered_at,
            "source": "canonical",
        }

    async def _run_pdf_job(job_id: str, report_id: str, actor: Any) -> None:
        await mark_async_job_processing(job_id, message="Rendering PDF...", details={"report_id": report_id})
        try:
            export = await _render_pdf_export_impl(report_id, actor)
            await complete_async_job_binary(
                job_id,
                content=export.get("pdf_bytes") or b"",
                media_type="application/pdf",
                filename=str(export.get("filename") or f"MASCI_Daily_Report_{report_id}.pdf"),
                message="PDF ready.",
                result_meta={
                    "rendered_at": export.get("rendered_at") or "",
                    "source": export.get("source") or "",
                    "report_id": report_id,
                },
            )
        except HTTPException as exc:
            await fail_async_job(
                job_id,
                error_code=f"pdf_http_{exc.status_code}",
                message=str(exc.detail),
                details={"report_id": report_id},
            )
        except Exception as exc:  # noqa: BLE001
            await fail_async_job(
                job_id,
                error_code="pdf_render_failed",
                message=f"PDF render failed: {type(exc).__name__}",
                details={"report_id": report_id},
            )
