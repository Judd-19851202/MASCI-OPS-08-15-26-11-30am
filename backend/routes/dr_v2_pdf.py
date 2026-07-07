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

from fastapi import APIRouter, Depends, HTTPException, Path, Response

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
        """DR-UNIFY-002 · union of legacy `daily_reports` + modern
        approved records into ONE list.

        Each row carries a `source` badge: `"legacy"` or `"modern"`.
        Scoping mirrors the PDF route (admin → all, PM → assigned
        projects, HR-read → all-read).
        """
        limit = max(1, min(int(limit or 50), 200))

        # ── Scope resolution ────────────────────────────────────────
        pm_project_filter: Optional[Dict[str, Any]] = None
        is_admin = actor is True
        is_hr = isinstance(actor, dict) and actor.get("_actor_kind") == "hr_user"
        if not is_admin and not is_hr and isinstance(actor, dict):
            scope = await compute_pm_scope(db, actor)
            if not scope.is_admin:
                nums = list(scope.project_numbers or [])
                if not nums:
                    return {"items": []}
                pm_project_filter = {"$in": nums}

        items: List[Dict[str, Any]] = []

        # ── Modern approvals (dr_v2_drafts + accept audit entry) ────
        recent_accepts_cursor = (
            db[APPROVAL_ENTRIES_COLL]
            .find({"action": "accept"}, {"_id": 0, "report_id": 1, "ts": 1})
            .sort("ts", -1)
            .limit(limit * 3)
        )
        seen_modern: set = set()
        modern_ids: List[str] = []
        modern_ts: Dict[str, str] = {}
        async for entry in recent_accepts_cursor:
            rid = entry.get("report_id")
            if not rid or rid in seen_modern:
                continue
            seen_modern.add(rid)
            modern_ts[rid] = entry.get("ts") or ""
            modern_ids.append(rid)
            if len(modern_ids) >= limit:
                break

        if modern_ids:
            draft_query: Dict[str, Any] = {"report_id": {"$in": modern_ids}}
            if pm_project_filter is not None:
                draft_query["$or"] = [
                    {"project_number": pm_project_filter},
                    {"day_setup.project_number": pm_project_filter},
                ]
            async for d in db[DRAFTS_COLL].find(
                draft_query,
                {
                    "_id": 0,
                    "report_id": 1,
                    "project_number": 1,
                    "report_date": 1,
                    "day_setup": 1,
                    "field_language": 1,
                },
            ):
                setup = d.get("day_setup") or {}
                # TRACK 24.9 · Post-filter modern rows using the same
                # synthetic classifier applied to legacy rows. The
                # `dr_v2_drafts` collection stores project info in a
                # nested `day_setup` dict which is why a mongo-level
                # $regex filter is awkward — a per-row classifier is
                # cheaper and cleaner given the small (limit*3) window.
                from lib.synthetic_dr_filter import is_synthetic_dr
                merged = {
                    "project_number": setup.get("project_number") or d.get("project_number") or "",
                    "project_name": setup.get("project_name") or "",
                }
                if is_synthetic_dr(merged):
                    continue
                items.append({
                    "id": d.get("report_id"),
                    "source": "modern",
                    "report_id": d.get("report_id"),
                    "project_number": merged["project_number"],
                    "project_name": merged["project_name"],
                    "report_date": d.get("report_date") or setup.get("report_date") or "",
                    "supervisor_name": setup.get("supervisor_name") or "",
                    "field_language": d.get("field_language") or "en",
                    "approved_at": modern_ts.get(d.get("report_id"), ""),
                })

        # ── Legacy approvals (daily_reports collection) ─────────────
        legacy_query: Dict[str, Any] = {}
        if pm_project_filter is not None:
            legacy_query["project_number"] = pm_project_filter
        # TRACK 24.9 · Exclude synthetic/test records from the
        # user-facing Approved Daily Reports export.
        from lib.synthetic_dr_filter import apply_synthetic_dr_exclusion
        legacy_query = apply_synthetic_dr_exclusion(legacy_query)
        # We include ALL legacy records; lifecycle state is optional
        # (pre-lifecycle records don't have `state` set). This matches
        # the existing /pm/daily and /admin/daily listing semantics.
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
            # Honor lifecycle gating when present; otherwise fall back
            # to "any submitted record is visible" so pre-lifecycle
            # documents keep flowing through the unified list.
            state = d.get("state") or (d.get("lifecycle") or {}).get("state")
            if state and state not in LEGACY_APPROVED_STATES:
                continue
            rid = d.get("id") or d.get("doc_id") or d.get("report_number")
            if not rid:
                continue
            items.append({
                "id": rid,
                "source": "legacy",
                "report_id": rid,
                "project_number": d.get("project_number") or "",
                "project_name": d.get("project_name") or "",
                "report_date": d.get("report_date") or "",
                "supervisor_name": d.get("prepared_by") or d.get("superintendent") or "",
                "field_language": "en",
                "approved_at": d.get("updated_at") or d.get("created_at") or d.get("report_date") or "",
            })

        # Newest first across both sources.
        items.sort(key=lambda it: it.get("approved_at") or "", reverse=True)
        return {"items": items[:limit]}

    @api_router.get("/dr-v2/reports/approved")
    async def dr_v2_list_approved(
        limit: int = 50,
        actor=Depends(require_admin_pm_or_hr_read),
    ):
        """Legacy path — retained for internal callers. Same contract
        as `/api/daily-reports/approved` (the canonical alias)."""
        return await _list_approved_impl(limit, actor)

    @api_router.get("/daily-reports/approved")
    async def daily_reports_list_approved(
        limit: int = 50,
        actor=Depends(require_admin_pm_or_hr_read),
    ):
        """DR-UNIFY-002 canonical alias · union of legacy + modern
        approved Daily Reports for management-side export."""
        return await _list_approved_impl(limit, actor)

    @api_router.get("/dr-v2/reports/{report_id}/pdf")
    async def dr_v2_report_pdf(
        report_id: str = Path(..., min_length=1),
        actor=Depends(require_admin_pm_or_hr_read),
    ):
        return await _render_pdf_impl(report_id, actor)

    @api_router.get("/daily-reports/{report_id}/pdf")
    async def daily_reports_pdf(
        report_id: str = Path(..., min_length=1),
        actor=Depends(require_admin_pm_or_hr_read),
    ):
        """DR-UNIFY-002 canonical alias · dispatches to modern or
        legacy renderer based on which collection owns the id."""
        return await _render_pdf_impl(report_id, actor)

    async def _render_pdf_impl(report_id: str, actor: Any):
        # 1. Look up the report in BOTH collections. Modern
        # `dr_v2_drafts` wins if both exist (should not happen in
        # practice — ids are namespaced).
        draft = await db[DRAFTS_COLL].find_one({"report_id": report_id}, {"_id": 0})
        legacy = None
        if not draft:
            legacy = await db[LEGACY_COLL].find_one(
                {"$or": [
                    {"id": report_id},
                    {"doc_id": report_id},
                    {"report_number": report_id},
                ]},
                {"_id": 0},
            )
        if not draft and not legacy:
            raise HTTPException(status_code=404, detail="report not found")

        record_project = (
            (draft or {}).get("day_setup", {}).get("project_number")
            or (draft or {}).get("project_number")
            or (legacy or {}).get("project_number")
            or ""
        )

        # 2. Enforce PM scope. Admin sentinel (True) and HR actor
        # (`_actor_kind == "hr_user"`) bypass this check.
        if isinstance(actor, dict) and actor.get("_actor_kind") != "hr_user":
            scope = await compute_pm_scope(db, actor)
            if not scope.allows(record_project):
                raise HTTPException(status_code=404, detail="report not found")

        # 3. Legacy path — render directly (no approval gate; the
        # legacy record IS the approved record by virtue of being
        # submitted, matching current V1 PDF email pipeline behavior).
        if legacy:
            try:
                pdf_bytes = render_record_pdf("daily-report", legacy)
            except Exception as ex:  # noqa: BLE001
                raise HTTPException(
                    status_code=500,
                    detail=f"PDF render failed: {type(ex).__name__}",
                ) from ex
            filename = f"MASCI_Daily_Report_{report_id}.pdf"
            rendered_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f'inline; filename="{filename}"',
                    "X-Content-Type-Options": "nosniff",
                    "X-Daily-Report-Id": report_id,
                    "X-Daily-Report-Source": "legacy",
                    "X-Daily-Report-Rendered-At": rendered_at,
                    "X-Daily-Report-Canonical-Language": "en",
                    "Cache-Control": "no-store",
                },
            )

        # 4. Modern path — require an accept entry.
        accept = await _latest_accept_entry(db, report_id)
        if not accept:
            raise HTTPException(
                status_code=409,
                detail="report is not yet approved; PDF export blocked",
            )

        # 5. Canonicalize ES → EN if needed.
        canonical = await _canonical_draft(db, report_id, draft)

        # 6. Pick up supervisor-edited summary.
        accepted_summary = ""
        edit_entry = await db[APPROVAL_ENTRIES_COLL].find_one(
            {"report_id": report_id, "edited_narrative": {"$exists": True, "$ne": None}},
            {"_id": 0, "edited_narrative": 1},
            sort=[("ts", -1)],
        )
        if edit_entry:
            accepted_summary = (edit_entry.get("edited_narrative") or "").strip()
        if not accepted_summary:
            accepted_summary = (canonical.get("accepted_summary") or "").strip() if isinstance(canonical.get("accepted_summary"), str) else ""

        # 7. Map to V1 record shape and render.
        record = _v2_to_v1_daily_record(canonical, accepted_summary=accepted_summary)
        try:
            pdf_bytes = render_record_pdf("daily-report", record)
        except Exception as ex:  # noqa: BLE001
            raise HTTPException(
                status_code=500,
                detail=f"PDF render failed: {type(ex).__name__}",
            ) from ex

        filename = f"MASCI_Daily_Report_{report_id}.pdf"
        rendered_at = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'inline; filename="{filename}"',
                "X-Content-Type-Options": "nosniff",
                "X-Daily-Report-Id": report_id,
                "X-Daily-Report-Source": "modern",
                "X-Daily-Report-Rendered-At": rendered_at,
                "X-Daily-Report-Canonical-Language": "en",
                # Retain legacy headers for backwards compatibility
                # with any existing internal caller reading them.
                "X-Dr-V2-Report-Id": report_id,
                "X-Dr-V2-Rendered-At": rendered_at,
                "X-Dr-V2-Canonical-Language": "en",
                "Cache-Control": "no-store",
            },
        )
