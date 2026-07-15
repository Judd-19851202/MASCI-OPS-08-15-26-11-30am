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
- Live AI synthesis is the primary path. If the provider fails, the
  endpoint degrades to the deterministic fallback — never a 5xx.
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

from services.dr_ai import build_evidence_bundle, get_ai_provider
from services.dr_ai.agents import AGENTS, AGENT_RESPONSE_SCHEMA


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
    form_key: Optional[str] = None
    tenant_id: Optional[str] = None
    language: Optional[str] = "en"
    evidence_refs: Optional[List[str]] = None
    force: Optional[bool] = False


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


def _num(v: Any) -> float:
    try:
        return float(v)
    except (TypeError, ValueError):
        return 0.0


def _uniq(seq: List[str]) -> List[str]:
    seen: List[str] = []
    for s in seq:
        s = _clean_str(s, 120)
        if s and s not in seen:
            seen.append(s)
    return seen


def _crew_hours(row: Dict[str, Any]) -> float:
    for key in ("hours", "hours_worked", "labor_hours"):
        if row.get(key) not in (None, ""):
            return round(_num(row.get(key)), 2)
    start = _clean_str(row.get("start_time"), 10)
    stop = _clean_str(row.get("stop_time"), 10)
    if not start or not stop or ":" not in start or ":" not in stop:
        return 0.0
    try:
        sh, sm = [int(x) for x in start.split(":", 1)]
        eh, em = [int(x) for x in stop.split(":", 1)]
        gross = (eh * 60 + em) - (sh * 60 + sm)
        if gross < 0:
            gross += 24 * 60
        lunch = max(0.0, _num(row.get("lunch_minutes")))
        return round(max(0.0, gross - lunch) / 60, 2)
    except Exception:  # noqa: BLE001
        return 0.0


def _build_summary_input(payload: Dict[str, Any]) -> Dict[str, Any]:
    p = payload or {}
    provided = p.get("summary_input") if isinstance(p.get("summary_input"), dict) else {}

    crews = []
    for row in _list_of_dicts(p.get("masci_crews")):
        crews.append({
            "employee_id": _clean_str(row.get("employee_id"), 80),
            "name": _clean_str(row.get("name") or row.get("employee_name_snapshot"), 120),
            "trade": _clean_str(row.get("trade") or row.get("trade_snapshot"), 80),
            "hours": _crew_hours(row),
        })

    subs = []
    for row in _list_of_dicts(p.get("subcontractors")):
        subs.append({
            "company": _clean_str(row.get("company") or row.get("vendor") or row.get("name"), 120),
            "headcount": int(_num(row.get("count") or row.get("headcount")) or 0),
            "hours": round(_num(row.get("hours")), 2),
            "work_description": _clean_str(row.get("work_performed") or row.get("notes"), 240),
        })

    equipment = []
    for row in _list_of_dicts(p.get("equipment")):
        run_hours = round(_num(row.get("hours_used") or row.get("run_time") or row.get("run_hours")), 2)
        idle_hours = round(_num(row.get("idle_hours") or row.get("idle_time") or row.get("idle")), 2)
        equipment.append({
            "description": _clean_str(row.get("description") or row.get("equipment") or row.get("label"), 120),
            "unit_number": _clean_str(row.get("unit_number") or row.get("unit"), 60),
            "operator": _clean_str(row.get("operator") or row.get("operator_name"), 120),
            "run_hours": run_hours,
            "idle_hours": idle_hours,
            "total_usage_hours": round(run_hours + idle_hours, 2),
        })

    production_rows = []
    for row in _list_of_dicts(p.get("production")):
        production_rows.append({
            "description": _clean_str(row.get("description") or row.get("activity") or row.get("name"), 160),
            "quantity": round(_num(row.get("quantity")), 2),
            "unit": _clean_str(row.get("unit"), 20),
            "percent_complete": int(_num(row.get("percent_complete")) or 0),
            "cost_code": _clean_str(row.get("cost_code"), 40),
            "work_area": _clean_str(row.get("station_from") or row.get("work_area"), 80),
        })

    photos = p.get("photos") or []
    photo_status = _clean_str(
        (provided.get("photos") or {}).get("status")
        or p.get("photo_intelligence_status")
        or ("not_requested" if photos else "no_photos"),
        60,
    ) or ("not_requested" if photos else "no_photos")

    return {
        "labor": {
            "employee_count": len(crews),
            "total_employee_hours": round(sum(r["hours"] for r in crews), 2),
            "rows": crews,
        },
        "subcontractors": {
            "subcontractor_count": len(subs),
            "total_headcount": sum(r["headcount"] for r in subs),
            "total_hours": round(sum(r["hours"] for r in subs), 2),
            "rows": subs,
        },
        "equipment": {
            "equipment_count": len(equipment),
            "total_run_hours": round(sum(r["run_hours"] for r in equipment), 2),
            "total_idle_hours": round(sum(r["idle_hours"] for r in equipment), 2),
            "total_usage_hours": round(sum(r["total_usage_hours"] for r in equipment), 2),
            "rows": equipment,
        },
        "production": {
            "rows": production_rows,
        },
        "photos": {
            "photo_count": len(photos),
            "status": photo_status,
            "lifecycle_status": _clean_str(
                (provided.get("photos") or {}).get("lifecycle_status")
                or photo_status,
                60,
            )
            or photo_status,
            "analyzed": int((provided.get("photos") or {}).get("analyzed") or 0),
            "pending": int((provided.get("photos") or {}).get("pending") or 0),
            "queued": int((provided.get("photos") or {}).get("queued") or 0),
            "processing": int((provided.get("photos") or {}).get("processing") or 0),
            "failed": int((provided.get("photos") or {}).get("failed") or 0),
            "observations": list((provided.get("photos") or {}).get("observations") or p.get("photo_observations") or [])[:30],
            "classification": _clean_str((provided.get("photos") or {}).get("classification"), 240),
        },
    }


def _photo_observation_lines(items: List[Any]) -> List[str]:
    lines: List[str] = []
    for item in items[:8]:
        if not isinstance(item, dict):
            continue
        if item.get("eligibility_reason") and not item.get("is_jobsite_photo", True):
            continue
        if item.get("summary"):
            lines.append(_clean_str(item.get("summary"), 220))
        for obs in (item.get("observations") or [])[:3]:
            cleaned = _clean_str(obs, 180)
            if cleaned:
                lines.append(cleaned)
        desc = _clean_str(item.get("description"), 180)
        label = _clean_str(item.get("label"), 80)
        if desc:
            lines.append(f"{label}: {desc}" if label else desc)
        ticket = _clean_str(item.get("ticket_text"), 220)
        if ticket:
            lines.append(ticket)
    deduped: List[str] = []
    seen = set()
    for line in lines:
        key = line.lower()
        if not line or key in seen:
            continue
        seen.add(key)
        deduped.append(line)
    return deduped[:4]


def _is_low_value_photo_fact(text: str) -> bool:
    value = _clean_str(text, 240).lower()
    if not value:
        return True
    low_value_markers = [
        "logo",
        "branding",
        "color",
        "windows taskbar",
        "browser tab",
        "computer monitor is shown",
        "desktop monitor is shown",
        "web browser open",
        "computer monitor is photographed",
        "browser window",
        "admin or database management webpage",
        "screen",
    ]
    return any(marker in value for marker in low_value_markers)


def _rank_photo_observations(items: List[Any]) -> List[str]:
    ranked: List[str] = []
    seen = set()
    for item in items[:60]:
        if not isinstance(item, dict):
            continue
        desc = _clean_str(item.get("description"), 220)
        if not desc or _is_low_value_photo_fact(desc):
            continue
        key = desc.lower()
        if key in seen:
            continue
        seen.add(key)
        ranked.append(desc)
    return ranked[:5]


def _photo_observations_for_ai(photo_intel: Optional[Dict[str, Any]]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for index, row in enumerate(list((photo_intel or {}).get("photos") or [])[:24], start=1):
        if not isinstance(row, dict):
            continue
        if _clean_str(row.get("analysis_status"), 40) != "complete":
            continue
        observations: List[str] = []
        for entry in row.get("observations") or []:
            if isinstance(entry, dict):
                text = _clean_str(entry.get("description") or entry.get("label"), 240)
            else:
                text = _clean_str(entry, 240)
            if text:
                observations.append(text)
        summary = _clean_str(row.get("narrative"), 600)
        if not summary and not observations:
            continue
        items.append(
            {
                "photo_number": index,
                "photo_id": _clean_str(row.get("photo_id"), 80),
                "summary": summary,
                "observations": observations[:6],
                "citation_hint": (
                    f"Photo {index}"
                    + (f" ({_clean_str(row.get('photo_id'), 24)})" if _clean_str(row.get("photo_id"), 24) else "")
                ),
            }
        )
    return items


def _build_photo_evidence_manifest(photo_items: List[Dict[str, Any]]) -> List[str]:
    manifest: List[str] = []
    for item in photo_items[:24]:
        if not isinstance(item, dict):
            continue
        photo_number = int(item.get("photo_number") or 0)
        citation = _clean_str(item.get("citation_hint"), 80) or (f"Photo {photo_number}" if photo_number else "Photo")
        summary = _clean_str(item.get("summary"), 420)
        observations = [
            _clean_str(obs, 260)
            for obs in list(item.get("observations") or [])[:6]
            if _clean_str(obs, 260)
        ]
        if summary:
            manifest.append(f"{citation}: summary evidence — {summary}")
        for obs_index, obs in enumerate(observations, start=1):
            manifest.append(f"{citation}: technical observation {obs_index} — {obs}")
    return manifest[:120]


def _day_narrative_system_prompt_with_photo_citations() -> str:
    base = AGENTS["day_narrative"]["system"]
    return (
        base
        + "\n\nPHOTO CITATION REQUIREMENT:\n"
        + "When `photo_observations[]` is present, you MUST explicitly cite grounded photo evidence in the prose. "
        + "Use direct photo references such as 'Photo 3 shows …', 'Photo 5 confirms …', or 'Photo 2 documents …'. "
        + "Every photo citation MUST be tied to the exact `photo_observations[]` entry provided in the evidence bundle. "
        + "Do NOT generalize as 'site photos show' when a numbered photo citation is available. "
        + "If multiple photos contain technical evidence, weave the strongest numbered citations into the narrative. "
        + "If no grounded numbered photo evidence exists, say nothing about photo content beyond acknowledging attached photos."
    )


def _compose_pm_grade_fallback(payload: Dict[str, Any], summary_input: Dict[str, Any]) -> str:
    paragraphs: List[str] = []
    production_rows = list((summary_input.get("production") or {}).get("rows") or [])
    labor = summary_input.get("labor") or {}
    subcontractors = summary_input.get("subcontractors") or {}
    equipment = summary_input.get("equipment") or {}
    photos = summary_input.get("photos") or {}

    work_bits = []
    for row in production_rows[:4]:
        desc = _clean_str(row.get("description"), 120)
        qty = row.get("quantity")
        unit = _clean_str(row.get("unit"), 20)
        pct = int(_num(row.get("percent_complete")) or 0)
        if desc and qty:
            phrase = f"{float(qty):g} {unit} {desc}".strip()
            if pct > 0:
                phrase += f" ({pct}% complete)"
            work_bits.append(phrase)
    if work_bits:
        paragraphs.append("Work completed: " + "; ".join(work_bits) + ".")

    workforce_bits = []
    employee_count = int(labor.get("employee_count") or 0)
    employee_hours = round(_num(labor.get("total_employee_hours")), 2)
    if employee_count or employee_hours:
        workforce_bits.append(
            f"MASCI recorded {employee_count} employee{'s' if employee_count != 1 else ''} and {employee_hours:.2f} labor hours"
        )
    sub_count = int(subcontractors.get("subcontractor_count") or 0)
    sub_hours = round(_num(subcontractors.get("total_hours")), 2)
    if sub_count or sub_hours:
        workforce_bits.append(
            f"{sub_count} subcontractor/vendor entr{'ies' if sub_count != 1 else 'y'} contributing {sub_hours:.2f} hours"
        )
    equip_count = int(equipment.get("equipment_count") or 0)
    run_hours = round(_num(equipment.get("total_run_hours")), 2)
    idle_hours = round(_num(equipment.get("total_idle_hours")), 2)
    if equip_count or run_hours or idle_hours:
        workforce_bits.append(
            f"{equip_count} equipment unit{'s' if equip_count != 1 else ''} logged {run_hours:.2f} run hours and {idle_hours:.2f} idle hours"
        )
    if workforce_bits:
        paragraphs.append("Workforce and equipment: " + "; ".join(workforce_bits) + ".")

    materials_rows = _list_of_dicts(payload.get("materials"))
    outbound_rows = _list_of_dicts(payload.get("outbound_materials"))
    material_bits = []
    for row in materials_rows[:4]:
        desc = _clean_str(row.get("material") or row.get("description"), 120)
        qty = _clean_str(row.get("quantity"), 40)
        unit = _clean_str(row.get("unit"), 20)
        supplier = _clean_str(row.get("supplier"), 80)
        if desc:
            part = f"{qty} {unit} {desc}".strip() if qty else desc
            if supplier:
                part += f" from {supplier}"
            material_bits.append(part)
    for row in outbound_rows[:3]:
        desc = _clean_str(row.get("material") or row.get("description"), 120)
        qty = _clean_str(row.get("quantity"), 40)
        unit = _clean_str(row.get("unit"), 20)
        if desc:
            material_bits.append((f"hauled {qty} {unit} {desc}".strip()))
    if material_bits:
        paragraphs.append("Materials and logistics: " + "; ".join(material_bits) + ".")

    photo_facts = _rank_photo_observations(list(photos.get("observations") or []))
    photo_observation_count = len(list(photos.get("observations") or []))
    if photo_facts:
        paragraphs.append("Photo-supported evidence: " + "; ".join(photo_facts[:2]) + ".")
    elif int(photos.get("photo_count") or 0) > 0:
        failed_count = max(0, int(photos.get("photo_count") or 0) - photo_observation_count)
        if failed_count > 0:
            paragraphs.append(f"Photo-supported evidence: Photo analysis failed for {failed_count} photos.")
        else:
            paragraphs.append(
                f"Photo-supported evidence: {int(photos.get('photo_count') or 0)} submitted photos were reviewed."
            )

    issue_bits = []
    if _clean_str(payload.get("schedule_delays"), 20).lower() in {"yes", "y", "true"}:
        notes = _clean_str(payload.get("schedule_delays_notes"), 240)
        issue_bits.append(notes or "Schedule delay reported")
    if _clean_str(payload.get("weather_impact"), 20).lower() in {"yes", "y", "true"}:
        notes = _clean_str(payload.get("weather_impact_notes"), 240)
        issue_bits.append(notes or "Weather impact reported")
    general_notes = _clean_str(payload.get("general_notes"), 300)
    if general_notes:
        issue_bits.append(general_notes)
    if issue_bits:
        paragraphs.append("Issues and attention: " + "; ".join(issue_bits[:3]) + ".")

    tomorrow = _clean_str((payload.get("narrative_sections") or {}).get("tomorrow_plan"), 320)
    if tomorrow:
        paragraphs.append(f"Next work: {tomorrow}.")

    return "\n\n".join([p for p in paragraphs if p]).strip()


def _build_live_ai_bundle(payload: Dict[str, Any], photo_intel: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    summary_input = _build_summary_input(payload)
    normalized = dict(payload or {})
    supervisor = _clean_str(
        normalized.get("supervisor_name")
        or normalized.get("prepared_by")
        or normalized.get("superintendent"),
        120,
    )
    if supervisor and not normalized.get("supervisor_name"):
        normalized["supervisor_name"] = supervisor
    if normalized.get("equipment") and not normalized.get("equipment_used"):
        normalized["equipment_used"] = normalized.get("equipment")
    if normalized.get("activities") and not normalized.get("activity_cards"):
        normalized["activity_cards"] = normalized.get("activities")
    if normalized.get("constraints") and not normalized.get("constraint_cards"):
        normalized["constraint_cards"] = normalized.get("constraints")
    day_impacts = dict(normalized.get("day_impacts") or {})
    if _clean_str(normalized.get("schedule_delays"), 20):
        day_impacts["schedule_delays"] = _clean_str(normalized.get("schedule_delays"), 20)
    if _clean_str(normalized.get("schedule_delays_notes"), 320):
        day_impacts["schedule_delays_notes"] = _clean_str(normalized.get("schedule_delays_notes"), 320)
    if _clean_str(normalized.get("weather_impact"), 20):
        day_impacts["weather_impact"] = _clean_str(normalized.get("weather_impact"), 20)
    if _clean_str(normalized.get("weather_impact_notes"), 320):
        day_impacts["weather_impact_notes"] = _clean_str(normalized.get("weather_impact_notes"), 320)
    if day_impacts:
        normalized["day_impacts"] = day_impacts
    normalized["crew_hours_total"] = round(_num((summary_input.get("labor") or {}).get("total_employee_hours")), 2)
    normalized["equipment_hours"] = round(_num((summary_input.get("equipment") or {}).get("total_usage_hours")), 2)
    ai_photo_obs = _photo_observations_for_ai(photo_intel)
    if ai_photo_obs:
        normalized["photo_observations"] = ai_photo_obs
        normalized["photo_evidence_manifest"] = _build_photo_evidence_manifest(ai_photo_obs)
    return build_evidence_bundle(normalized)


async def _compose_live_summary(
    payload: Dict[str, Any],
    *,
    photo_intel: Optional[Dict[str, Any]],
    language: str,
    request_id: Optional[str],
    session_key: str,
) -> Dict[str, Any]:
    composed = _compose_deterministic_summary(payload, language=language)
    evidence_bundle = _build_live_ai_bundle(payload, photo_intel)
    provider = get_ai_provider()
    result = await provider.synthesize(
        agent="day_narrative",
        system_message=_day_narrative_system_prompt_with_photo_citations(),
        user_payload=evidence_bundle,
        response_schema=AGENT_RESPONSE_SCHEMA,
        session_id=f"daily-summary-{session_key[:80]}",
    )

    narrative = _clean_str(getattr(result, "narrative", ""), _MAX_SUMMARY_CHARS)
    if getattr(result, "ai_available", False) and narrative:
        return {
            "ok": True,
            "enabled": True,
            "reason_disabled": None,
            "mode": "live_ai",
            "summary_text": narrative,
            "language": language,
            "warnings": list(getattr(result, "uncertainties", []) or [])[:12],
            "evidence_refs": list(getattr(result, "evidence_refs", []) or [])[:64],
            "sentence_count": max(1, narrative.count(".") + narrative.count("\n\n")),
            "summary_input": composed["summary_input"],
            "photo_intelligence": photo_intel,
            "confidence": float(getattr(result, "confidence", 0.0) or 0.0),
            "request_id": request_id,
        }

    fallback_warnings = list(composed["warnings"])
    fallback_warnings.extend(list(getattr(result, "uncertainties", []) or [])[:6])
    return {
        "ok": True,
        "enabled": False,
        "reason_disabled": getattr(result, "fallback_reason", None) or "live_ai_unavailable",
        "mode": "deterministic_fallback",
        "summary_text": composed["summary_text"],
        "language": language,
        "warnings": fallback_warnings,
        "evidence_refs": composed["evidence_refs"],
        "sentence_count": composed["sentence_count"],
        "summary_input": composed["summary_input"],
        "photo_intelligence": photo_intel,
        "confidence": 0.0,
        "request_id": request_id,
    }


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
    summary_input = _build_summary_input(p)

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
    labor = summary_input.get("labor") or {}
    if crews or labor.get("employee_count") or labor.get("total_employee_hours"):
        crew_count = int(labor.get("employee_count") or 0)
        crew_hours = round(_num(labor.get("total_employee_hours")), 2)
        trades = _uniq([_clean_str(c.get("trade") or c.get("role"), 60) for c in crews])
        parts = [f"MASCI crew of {crew_count} employee{'s' if crew_count != 1 else ''}"] if crew_count else ["MASCI crew"]
        if trades:
            parts.append("across " + ", ".join(trades))
        if crew_hours:
            parts.append(f"logging {crew_hours} labor hours")
        lines.append(" ".join(parts).strip() + ".")

    # ── Subcontractors.
    sub_input = summary_input.get("subcontractors") or {}
    if subs:
        sub_names = _uniq([_clean_str(s.get("company") or s.get("name"), 80) for s in subs])
        if sub_names:
            sentence = "Subcontractors on site: " + ", ".join(sub_names)
            if sub_input.get("total_hours"):
                sentence += f" · {sub_input.get('total_hours')} labor hours"
            lines.append(sentence + ".")

    # ── Equipment.
    equip_input = summary_input.get("equipment") or {}
    if equipment:
        eq_names = _uniq([_clean_str(e.get("description") or e.get("equipment") or e.get("unit_number"), 60) for e in equipment])
        if eq_names:
            head = "Equipment deployed: " + ", ".join(eq_names)
            if equip_input.get("total_run_hours") or equip_input.get("total_idle_hours"):
                head += (
                    f" ({equip_input.get('total_run_hours', 0)} run hours"
                    f", {equip_input.get('total_idle_hours', 0)} idle hours)"
                )
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
                    pct = int(_num(row.get("percent_complete")) or 0)
                    chunk = f"{float(qty):g} {unit} {desc}".strip()
                    if pct > 0:
                        chunk += f" ({pct}% complete)"
                    prod_bits.append(chunk)
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
    photo_input = summary_input.get("photos") or {}
    if photos:
        photo_line = f"{len(photos)} photo{'s' if len(photos) != 1 else ''} attached"
        if photo_captions:
            preview = "; ".join(photo_captions[:3])
            photo_line += f" — captions include: {preview}"
        photo_status = photo_input.get("lifecycle_status") or photo_input.get("status")
        if photo_status and photo_status not in {"complete_with_observations", "complete_zero_observations"}:
            photo_line += f" · photo intelligence {str(photo_status).replace('_', ' ')}"
        lines.append(photo_line + ".")
    photo_obs_lines = _photo_observation_lines(photo_input.get("observations") or [])
    if photo_obs_lines:
        lines.append("Grounded photo observations: " + "; ".join(photo_obs_lines) + ".")

    # ── General notes.
    if general_notes:
        lines.append(f"Notes: {general_notes}.")

    # ── Tomorrow plan.
    if tomorrow:
        lines.append(f"Plan for tomorrow: {tomorrow}.")

    if len(lines) <= 1:
        warnings.append("insufficient_evidence_for_meaningful_summary")

    summary_text = _compose_pm_grade_fallback(p, summary_input) or "\n\n".join(lines).strip()
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
        "summary_input": summary_input,
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
        report payload. Uses live AI synthesis with deterministic
        fallback only on provider failure.

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
        language = (body.language or "en").lower()
        if language not in _ACCEPTED_LANGUAGES:
            language = "en"

        request_id = _clean_str(request.headers.get("X-Request-Id"), 120) or None
        payload = dict(body.payload or {})
        photo_intel = None
        form_key = _clean_str(body.form_key, 180) or _clean_str(payload.get("form_key"), 180)
        try:
            from services.photo_intelligence import (  # noqa: PLC0415
                process_v1_draft,
                list_v1_draft_intelligence,
            )
            if form_key and (payload.get("photos") or []):
                await process_v1_draft(
                    db,
                    draft_identity=form_key,
                    draft=payload,
                )
                photo_intel = await list_v1_draft_intelligence(
                    db,
                    draft_identity=form_key,
                    draft=payload,
                )
                payload["photo_observations"] = _photo_observations_for_ai(photo_intel)
                payload["photo_intelligence_status"] = photo_intel.get("status") or payload.get("photo_intelligence_status")
                payload["summary_input"] = {
                    **(payload.get("summary_input") or {}),
                    "photos": {
                        **((payload.get("summary_input") or {}).get("photos") or {}),
                        "photo_count": int(photo_intel.get("photo_count") or len(payload.get("photos") or [])),
                        "status": photo_intel.get("status") or "no_photos",
                        "lifecycle_status": photo_intel.get("lifecycle_status") or photo_intel.get("status") or "no_photos",
                        "analyzed": int(photo_intel.get("analyzed") or 0),
                        "pending": int(photo_intel.get("pending") or 0),
                        "queued": int(photo_intel.get("queued") or 0),
                        "processing": int(photo_intel.get("processing") or 0),
                        "failed": int(photo_intel.get("failed") or 0),
                        "observations": list(photo_intel.get("observations") or [])[:60],
                        "classification": photo_intel.get("classification") or "",
                    },
                }
        except Exception:  # noqa: BLE001
            photo_intel = None
        session_key = form_key or _clean_str(payload.get("project_number"), 40) or "draft"
        return await _compose_live_summary(
            payload,
            photo_intel=photo_intel,
            language=language,
            request_id=request_id,
            session_key=session_key,
        )

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
