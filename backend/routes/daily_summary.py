"""DR-CUTOVER-002 · Daily Operational Summary endpoints.

Additive routes that let the existing Daily Job Report form draft,
accept, and update a Daily Operational Summary — without touching the
existing submit path, the HR/crew data flow, the email pipeline, the
PDF renderer, or ODS ingestion.

Doctrine
--------
- Never invent facts. The summary composer receives ONLY the current
  report payload and produces sentences composed of literal values from
  that payload (crew counts, equipment names, weather text, etc.). No
  live LLM call happens in this track; every sentence is deterministic.
  That satisfies the "must not fabricate" contract mechanically.
- AI is optional. Every call routes through
  ``resolve_ai_capabilities(db, tenant_id, "daily_report_summary")``.
  If disabled, the endpoint returns ``ok=True, enabled=False,
  reason_disabled=<code>`` — never a 5xx.
- The accepted summary lives on the existing ``daily_reports`` document
  under a small set of clearly-named optional fields. Legacy readers
  are unaffected by their absence.
- Field UI copy MUST NOT surface "AI", "model", "provider", "token",
  or "cost" language. That is a frontend concern; this route returns
  a machine-readable ``reason_disabled`` code only.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field

from services.ai_gateway.capabilities import resolve_ai_capabilities


# ─────────────────────── constants ────────────────────────────────

_MODULE = "daily_report_summary"
_DEFAULT_TENANT_ID = "masci"
_ACCEPTED_LANGUAGES = {"en", "es"}
_MAX_SUMMARY_CHARS = 4000


# ─────────────────────── payload models ───────────────────────────

class SummaryDraftBody(BaseModel):
    """Client sends the *current* (possibly unsaved) report payload
    so the composer can produce a preview before submit."""
    payload: Dict[str, Any] = Field(default_factory=dict)
    tenant_id: Optional[str] = None
    language: Optional[str] = "en"
    evidence_refs: Optional[List[str]] = None


class SummaryAcceptBody(BaseModel):
    summary_text: str = Field(min_length=1, max_length=_MAX_SUMMARY_CHARS)
    language: Optional[str] = "en"
    source: Optional[str] = "user_edited"    # "draft" | "user_edited"
    evidence_refs: Optional[List[str]] = None
    canonical_english: Optional[str] = None
    original_text: Optional[str] = None
    accepted_by: Optional[str] = None


# ─────────────────────── helpers ──────────────────────────────────

def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean_str(v: Any, limit: int = 240) -> str:
    if v is None:
        return ""
    return str(v).strip()[:limit]


def _list_of_dicts(v: Any) -> List[Dict[str, Any]]:
    return [x for x in (v or []) if isinstance(x, dict)]


def _sum_hours(rows: List[Dict[str, Any]], key_candidates=("hours", "labor_hours")) -> float:
    total = 0.0
    for r in rows:
        for k in key_candidates:
            v = r.get(k)
            try:
                if v is not None:
                    total += float(v)
                    break
            except (TypeError, ValueError):
                continue
    return round(total, 2)


def _uniq(seq: List[str]) -> List[str]:
    seen: List[str] = []
    for s in seq:
        s = _clean_str(s, 120)
        if s and s not in seen:
            seen.append(s)
    return seen


def _compose_deterministic_summary(
    payload: Dict[str, Any], *, language: str = "en",
) -> Dict[str, Any]:
    """Compose a professional multi-paragraph summary using ONLY values
    that appear literally in the payload. Never invents facts. Never
    calls an external LLM.

    Returns ``{summary_text, warnings, evidence_refs, sentence_count}``.
    Empty sections produce no sentence — an evidence-free field never
    appears in the output.
    """
    p = payload or {}
    project_name = _clean_str(p.get("project_name") or p.get("project"), 200)
    project_number = _clean_str(p.get("project_number"), 40)
    date = _clean_str(p.get("report_date"), 40)
    supervisor = _clean_str(p.get("prepared_by") or p.get("superintendent"), 120)
    shift = _clean_str(p.get("shift"), 40)
    weather = _clean_str(p.get("weather_summary"), 240)

    crews = _list_of_dicts(p.get("masci_crews"))
    subs = _list_of_dicts(p.get("subcontractors"))
    equipment = _list_of_dicts(p.get("equipment"))
    materials = _list_of_dicts(p.get("materials"))
    outbound = _list_of_dicts(p.get("outbound_materials"))
    activities = _list_of_dicts(p.get("activities"))
    production = _list_of_dicts(p.get("production"))
    constraints = _list_of_dicts(p.get("constraints"))
    photos = p.get("photos") or []
    photo_captions = [c for c in (p.get("photo_captions") or []) if _clean_str(c)]

    delays = _clean_str(p.get("schedule_delays_notes"), 500) \
        if _clean_str(p.get("schedule_delays")).lower() in ("yes", "y", "true") else ""
    weather_impact_notes = _clean_str(p.get("weather_impact_notes"), 500) \
        if _clean_str(p.get("weather_impact")).lower() in ("yes", "y", "true") else ""
    incidents = _clean_str(p.get("safety_incidents_today")).lower() in ("yes", "y", "true")
    injuries = _clean_str(p.get("injuries_reported")).lower() in ("yes", "y", "true")
    incident_notes = _clean_str(p.get("incident_notes"), 500)
    general_notes = _clean_str(p.get("general_notes"), 800)

    tomorrow = _clean_str((p.get("narrative_sections") or {}).get("tomorrow_plan"), 500)

    lines: List[str] = []
    warnings: List[str] = []

    # ── Opening line — project + date + supervisor.
    head_bits = []
    if project_name and project_number:
        head_bits.append(f"{project_name} ({project_number})")
    elif project_name:
        head_bits.append(project_name)
    elif project_number:
        head_bits.append(project_number)
    if date:
        head_bits.append(f"daily report for {date}")
    if supervisor:
        head_bits.append(f"prepared by {supervisor}")
    if shift:
        head_bits.append(f"{shift} shift")
    if head_bits:
        head = ", ".join(head_bits)
        lines.append((head[:1].upper() + head[1:]) + ".")
    else:
        warnings.append("no_project_or_date_in_payload")

    # ── Weather + weather impact.
    if weather:
        lines.append(f"Weather: {weather}.")
    if weather_impact_notes:
        lines.append(f"Weather impact: {weather_impact_notes}.")

    # ── Crew composition.
    if crews:
        crew_count = sum(int(c.get("count") or 0) for c in crews if str(c.get("count") or "").strip())
        crew_hours = _sum_hours(crews)
        trades = _uniq([_clean_str(c.get("trade") or c.get("role"), 60) for c in crews])
        parts = [f"MASCI crew of {crew_count}"] if crew_count else ["MASCI crew"]
        if trades:
            parts.append("across " + ", ".join(trades))
        if crew_hours:
            parts.append(f"logging {crew_hours} labor hours")
        lines.append(" ".join(parts).strip() + ".")

    # ── Subcontractors.
    if subs:
        sub_names = _uniq([_clean_str(s.get("company") or s.get("name"), 80) for s in subs])
        if sub_names:
            lines.append("Subcontractors on site: " + ", ".join(sub_names) + ".")

    # ── Equipment.
    if equipment:
        eq_names = _uniq([_clean_str(e.get("description") or e.get("equipment") or e.get("unit_number"), 60) for e in equipment])
        eq_hours = _sum_hours(equipment, key_candidates=("hours", "operating_hours"))
        if eq_names:
            head = "Equipment deployed: " + ", ".join(eq_names)
            if eq_hours:
                head += f" ({eq_hours} operating hours total)"
            lines.append(head + ".")

    # ── Production rows (structured quantities).
    if production:
        prod_bits = []
        for row in production[:8]:
            desc = _clean_str(row.get("description"), 120)
            qty = row.get("quantity")
            unit = _clean_str(row.get("unit"), 12) or ""
            if desc and qty is not None:
                try:
                    prod_bits.append(f"{float(qty):g} {unit} {desc}".strip())
                except (TypeError, ValueError):
                    continue
        if prod_bits:
            lines.append("Production installed: " + "; ".join(prod_bits) + ".")

    # ── Free-text activities (limit to keep it professional).
    if activities:
        act_texts = _uniq([_clean_str(a.get("description") or a.get("text"), 160) for a in activities])
        act_texts = [a for a in act_texts if a][:6]
        if act_texts:
            lines.append("Activities performed: " + "; ".join(act_texts) + ".")

    # ── Materials in / out.
    if materials:
        mat_names = _uniq([_clean_str(m.get("material") or m.get("description"), 80) for m in materials])
        if mat_names:
            lines.append("Materials received: " + ", ".join(mat_names) + ".")
    if outbound:
        out_names = _uniq([_clean_str(m.get("material") or m.get("description"), 80) for m in outbound])
        if out_names:
            lines.append("Material hauled offsite: " + ", ".join(out_names) + ".")

    # ── Constraints / delays.
    if constraints:
        con_types = _uniq([_clean_str(c.get("constraint_type"), 40) for c in constraints])
        if con_types:
            lines.append("Constraints logged: " + ", ".join(con_types) + ".")
    if delays:
        lines.append(f"Schedule delay noted: {delays}.")

    # ── Safety — strictly from evidence.
    if incidents or injuries:
        parts = []
        if incidents:
            parts.append("a safety incident was recorded")
        if injuries:
            parts.append("an injury was reported")
        if incident_notes:
            parts.append(f"notes: {incident_notes}")
        lines.append("Safety: " + "; ".join(parts) + ".")
    # ── Photos — count only. Never fabricate photo content.
    if photos:
        photo_line = f"{len(photos)} photo{'s' if len(photos) != 1 else ''} attached"
        if photo_captions:
            preview = "; ".join(photo_captions[:3])
            photo_line += f" — captions include: {preview}"
        lines.append(photo_line + ".")

    # ── General notes.
    if general_notes:
        lines.append(f"Notes: {general_notes}.")

    # ── Tomorrow plan.
    if tomorrow:
        lines.append(f"Plan for tomorrow: {tomorrow}.")

    if len(lines) <= 1:
        warnings.append("insufficient_evidence_for_meaningful_summary")

    summary_text = "\n\n".join(lines).strip()
    if len(summary_text) > _MAX_SUMMARY_CHARS:
        summary_text = summary_text[:_MAX_SUMMARY_CHARS].rstrip() + "…"

    evidence_refs = []
    for i, _ in enumerate(photos[:24]):
        evidence_refs.append(f"photo:{i}")

    return {
        "summary_text": summary_text,
        "warnings": warnings,
        "evidence_refs": evidence_refs,
        "sentence_count": len(lines),
    }


# ─────────────────────── registration ─────────────────────────────

def register_daily_summary_routes(
    api_router: APIRouter, *, db, rate_limit_public_post,
) -> None:
    """Mount DR-CUTOVER-002 routes onto ``api_router``."""

    # ─────── POST /api/daily-reports/summary/draft ─────────────────
    @api_router.post(
        "/daily-reports/summary/draft",
        dependencies=[Depends(rate_limit_public_post)],
    )
    async def draft_summary(body: SummaryDraftBody, request: Request):
        """Compose a preview summary from the current (unsaved)
        report payload. Never issues a live provider call.

        Response shape (both enabled + disabled paths):

            {
              "ok": true,
              "enabled": bool,
              "reason_disabled": str | null,
              "summary_text": str | null,
              "language": "en" | "es",
              "warnings": [str, ...],
              "evidence_refs": [str, ...],
              "request_id": "..."
            }
        """
        tenant_id = _clean_str(body.tenant_id, 60) or _DEFAULT_TENANT_ID
        language = (body.language or "en").lower()
        if language not in _ACCEPTED_LANGUAGES:
            language = "en"

        # Resolve AI capability. If off, return graceful disabled state.
        cap = await resolve_ai_capabilities(db, tenant_id, _MODULE)
        request_id = _clean_str(request.headers.get("X-Request-Id"), 120) or None

        if not cap.enabled:
            return {
                "ok": True,
                "enabled": False,
                "reason_disabled": cap.reason_disabled,
                "summary_text": None,
                "language": language,
                "warnings": [],
                "evidence_refs": [],
                "request_id": request_id,
            }

        composed = _compose_deterministic_summary(body.payload or {}, language=language)
        return {
            "ok": True,
            "enabled": True,
            "reason_disabled": None,
            "summary_text": composed["summary_text"],
            "language": language,
            "warnings": composed["warnings"],
            "evidence_refs": composed["evidence_refs"],
            "sentence_count": composed["sentence_count"],
            "request_id": request_id,
        }

    # ─────── POST /api/daily-reports/{report_id}/summary/accept ────
    @api_router.post(
        "/daily-reports/{report_id}/summary/accept",
        dependencies=[Depends(rate_limit_public_post)],
    )
    async def accept_summary(
        report_id: str, body: SummaryAcceptBody, request: Request,
    ):
        """Persist an accepted (possibly hand-edited) summary onto an
        already-submitted daily report.

        - Never modifies HR/crew data, equipment rows, safety fields,
          or ODS facts.
        - Returns 404 if the report does not exist.
        - Emits a best-effort ``intelligence_fact`` via ODS if enabled.
        """
        report_id = _clean_str(report_id, 120)
        if not report_id:
            raise HTTPException(status_code=400, detail="report_id required")

        try:
            existing = await db.daily_reports.find_one({"id": report_id}, {"_id": 0})
        except Exception:  # noqa: BLE001
            existing = None
        if not existing:
            raise HTTPException(status_code=404, detail="daily report not found")

        language = (body.language or "en").lower()
        if language not in _ACCEPTED_LANGUAGES:
            language = "en"
        source = body.source if body.source in {"draft", "user_edited"} else "user_edited"
        accepted_by = _clean_str(body.accepted_by, 120) or _clean_str(existing.get("prepared_by"), 120) or "supervisor"
        canonical_english = _clean_str(body.canonical_english, _MAX_SUMMARY_CHARS) or (
            body.summary_text if language == "en" else ""
        )
        original_text = _clean_str(body.original_text, _MAX_SUMMARY_CHARS) or None

        accepted_at = _now_iso()
        summary_text = body.summary_text.strip()[:_MAX_SUMMARY_CHARS]
        patch: Dict[str, Any] = {
            # Canonical Daily Report summary family for all new writes.
            "ai_accepted_summary": summary_text,
            "ai_accepted_summary_meta": {
                "source": "edited" if source == "user_edited" else "manual",
                "accepted_at": accepted_at,
                "accepted_by": accepted_by,
                "language": language,
                "canonical_english": canonical_english,
                "evidence_refs": list(body.evidence_refs or [])[:64],
                "original_text": original_text,
                "edited_by_user": source == "user_edited",
                "provider_masked": None,
                "model_masked": None,
            },
            # Legacy compatibility read fields retained temporarily.
            "daily_operational_summary": summary_text,
            "daily_operational_summary_status": "accepted",
            "daily_operational_summary_source": source,
            "daily_operational_summary_accepted_at": accepted_at,
            "daily_operational_summary_accepted_by": accepted_by,
            "daily_operational_summary_language": language,
            "daily_operational_summary_canonical_english": canonical_english,
            "daily_operational_summary_evidence_refs": list(body.evidence_refs or [])[:64],
        }
        if original_text:
            patch["daily_operational_summary_original_text"] = original_text

        try:
            await db.daily_reports.update_one(
                {"id": report_id}, {"$set": patch}
            )
        except Exception as exc:  # noqa: BLE001
            raise HTTPException(status_code=500, detail=f"summary persist failed: {exc}")

        # Best-effort intelligence_fact via ODS. Never blocks the accept.
        try:
            from services.ods_spine.ingest import _base, _v1_resolve_project_and_date, now_iso  # type: ignore  # noqa: PLC0415
            from services.ods_spine.flags import ods_enabled  # type: ignore  # noqa: PLC0415
            if ods_enabled():
                pid, date = _v1_resolve_project_and_date(existing)
                if pid and date:
                    fact = _base("daily_report", report_id, 0,
                                 "intel:operational_summary", pid, date,
                                 accepted_by, "intelligence_fact")
                    fact["payload"] = {
                        "audience": "supervisor",
                        "agent": "daily_operational_summary",
                        "language": language,
                        "source": source,
                        "chars": len(summary_text),
                    }
                    fact["accepted_at"] = _now_iso()
                    # Supersede previous is_current facts for same source_id+key.
                    await db.operational_facts.update_many(
                        {"source_type": "daily_report",
                         "source_id": report_id,
                         "fact_type": "intelligence_fact",
                         "source_item_id": "intel:operational_summary",
                         "is_current": True},
                        {"$set": {"is_current": False, "superseded_at": _now_iso()}},
                    )
                    await db.operational_facts.insert_one(fact)
        except Exception:  # noqa: BLE001
            pass  # never block acceptance on intelligence emission

        return {
            "ok": True,
            "report_id": report_id,
            "daily_operational_summary_status": "accepted",
            "daily_operational_summary_accepted_at": patch["daily_operational_summary_accepted_at"],
            "language": language,
        }


__all__ = ["register_daily_summary_routes", "_compose_deterministic_summary"]
