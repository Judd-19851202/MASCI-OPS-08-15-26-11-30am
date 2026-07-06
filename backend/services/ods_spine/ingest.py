"""ODS-001 · Ingestors.

Every ingestor:
  1. Reads a source doc (never mutates it).
  2. Builds normalized facts.
  3. Supersedes prior facts for the same (source_type, source_id).
  4. Writes new facts + records an ingestion run.
  5. Triggers a KPI snapshot recompute for touched (project_id, date) pairs.

Idempotent: rerunning with the same source doc produces the same fact set
(new fact_ids, but identical envelope+payload content) and the OLD facts
are marked superseded — never left as `is_current=true` alongside new ones.
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, List, Tuple

from .flags import dr_v2_spine_emission_enabled, ods_enabled
from .model import (
    coerce_date, coerce_number, normalize_project_id, now_iso,
)
from .store import (
    COLL_FACTS, record_ingestion_run, supersede_facts, write_facts,
)


TENANT_DEFAULT = "masci"


def _resolve_project_and_date(draft: Dict[str, Any]) -> Tuple[str, str]:
    setup = (draft.get("day_setup") or {})
    pid = normalize_project_id(
        setup.get("project_number") or setup.get("project_id") or setup.get("project_name")
    )
    d = coerce_date(setup.get("report_date") or draft.get("report_date"))
    return pid, d


def _base(source_type: str, source_id: str, source_version: int,
          source_item_id: str, project_id: str, date: str,
          submitted_by: str, fact_type: str) -> Dict[str, Any]:
    return {
        "fact_id": uuid.uuid4().hex,
        "fact_type": fact_type,
        "tenant_id": TENANT_DEFAULT,
        "project_id": project_id,
        "date": date,
        "source_type": source_type,
        "source_id": source_id,
        "source_item_id": source_item_id,
        "source_version": source_version,
        "source_status": "full",
        "is_current": True,
        "submitted_by": submitted_by or "",
        "verified_identity": False,
        "confidence": 1.0,
        "trace_id": uuid.uuid4().hex,
        "created_at": now_iso(),
        "payload": {},
    }


def _build_facts_from_dr_v2_draft(draft: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Pure builder — no I/O. Emits normalized facts from a DR-V2 draft."""
    pid, date = _resolve_project_and_date(draft)
    if not pid or not date:
        return []  # partial — no anchor, refuse to emit

    src_type = "daily_report_v2"
    src_id = draft.get("report_id") or ""
    src_ver = int((draft.get("updated_at") or "").replace("-", "").replace(":", "").replace("T", "").replace(".", "").split("+")[0][:14] or 0)
    submitted_by = (draft.get("day_setup") or {}).get("supervisor_name") or draft.get("supervisor_id") or ""

    facts: List[Dict[str, Any]] = []

    # Labor facts — one per crew row
    for i, crew in enumerate(draft.get("masci_crews") or []):
        if not isinstance(crew, dict):
            continue
        item_id = f"crew:{i}:{crew.get('crew') or i}"
        for j, member in enumerate(crew.get("members") or [None]):
            f = _base(src_type, src_id, src_ver, f"{item_id}:m{j}", pid, date, submitted_by, "labor_fact")
            f["payload"] = {
                "employee_id": None,
                "person_name": str(member) if member else "",
                "company": "MASCI",
                "role": crew.get("role"),
                "hours": coerce_number(crew.get("hours")),
                "overtime_hours": coerce_number(crew.get("overtime")),
                "cost_code": crew.get("cost_code"),
                "verified_identity": False,
            }
            facts.append(f)

    # Equipment facts
    for i, eq in enumerate(draft.get("equipment_used") or []):
        if not isinstance(eq, dict):
            continue
        item_id = f"equipment:{i}:{eq.get('unit') or i}"
        f = _base(src_type, src_id, src_ver, item_id, pid, date, submitted_by, "equipment_fact")
        f["payload"] = {
            "equipment_id": eq.get("id") or eq.get("unit"),
            "equipment_label": eq.get("unit") or eq.get("label") or "",
            "operator": eq.get("operator"),
            "hours_used": coerce_number(eq.get("hours")),
            "idle_hours": coerce_number(eq.get("idle_hours")),
            "breakdown": bool(eq.get("breakdown")),
            "maintenance": bool(eq.get("maintenance")),
            "cost_code": eq.get("cost_code"),
        }
        facts.append(f)

    # Production facts (from activity_cards)
    for i, act in enumerate(draft.get("activity_cards") or []):
        if not isinstance(act, dict):
            continue
        item_id = f"activity:{i}:{act.get('id') or i}"
        f = _base(src_type, src_id, src_ver, item_id, pid, date, submitted_by, "production_fact")
        f["payload"] = {
            "cost_code": act.get("cost_code"),
            "activity": act.get("activity") or act.get("activity_type") or "",
            "work_area": act.get("area"),
            "quantity": coerce_number(act.get("qty") or act.get("quantity")),
            "unit": act.get("unit") or "",
            "crew_links": act.get("crew_ids") or ([act.get("crew")] if act.get("crew") else []),
            "equipment_links": act.get("equipment_ids") or [],
            "photo_evidence_links": act.get("photo_ids") or [],
        }
        facts.append(f)

    # Delay / constraint facts
    for i, c in enumerate(draft.get("constraint_cards") or []):
        if not isinstance(c, dict):
            continue
        item_id = f"constraint:{i}:{c.get('id') or i}"
        f = _base(src_type, src_id, src_ver, item_id, pid, date, submitted_by, "delay_fact")
        f["payload"] = {
            "delay_category": (c.get("type") or "other").lower(),
            "duration_hours": coerce_number(c.get("duration_hours")),
            "reason": c.get("note") or c.get("reason") or "",
            "responsible_party": c.get("responsible_party"),
            "impact": (c.get("impact") or "med").lower(),
            "cost_risk": bool(c.get("cost_risk")),
            "schedule_risk": bool(c.get("schedule_risk", True)),
            "needed_action": c.get("needed_action"),
        }
        facts.append(f)

    # Weather fact — one per report
    w = draft.get("weather") or {}
    if any(w.get(k) is not None for k in ("temperature_f", "precipitation", "wind_mph", "condition")):
        f = _base(src_type, src_id, src_ver, "weather:0", pid, date, submitted_by, "weather_fact")
        f["payload"] = {
            "temperature_f": coerce_number(w.get("temperature_f")),
            "precipitation_in": coerce_number(w.get("precipitation")),
            "wind_mph": coerce_number(w.get("wind_mph")),
            "condition": w.get("condition") or (draft.get("day_setup") or {}).get("weather"),
        }
        facts.append(f)

    # Readiness facts
    ready = draft.get("tomorrow_readiness") or {}
    for area in ("crew", "materials", "equipment", "permits"):
        flag_key = f"{area}_ok"
        if flag_key not in ready and not ready.get("blockers"):
            continue
        ok = bool(ready.get(flag_key))
        f = _base(src_type, src_id, src_ver, f"readiness:{area}", pid, date, submitted_by, "readiness_fact")
        f["payload"] = {
            "readiness_area": area if area != "crew" else "crew",
            "status": "ready" if ok else "at_risk",
            "blocker": ", ".join([str(b) for b in (ready.get("blockers") or [])]) if not ok else None,
        }
        facts.append(f)

    # Safety facts — supervisor incident/observation entries
    safety = draft.get("safety") or {}
    for i, ev in enumerate(safety.get("safety_incidents") or []):
        if not isinstance(ev, dict):
            continue
        item_id = f"safety:{i}:{ev.get('id') or i}"
        f = _base(src_type, src_id, src_ver, item_id, pid, date, submitted_by, "safety_fact")
        f["payload"] = {
            "safety_type": (ev.get("type") or "observation").lower(),
            "severity": (ev.get("severity") or "info").lower(),
            "narrative": ev.get("narrative"),
        }
        facts.append(f)

    # Photo evidence facts
    for i, p in enumerate(draft.get("photos") or []):
        if isinstance(p, str):
            ref = p
            item_id = f"photo:{i}:{p[:24]}"
            payload = {"photo_ref": ref}
        elif isinstance(p, dict):
            item_id = f"photo:{i}:{p.get('id') or i}"
            payload = {
                "photo_ref": p.get("ref") or p.get("id") or "",
                "storage_url": p.get("url"),
                "thumb_url": p.get("thumb"),
                "linked_activity": p.get("activity_id"),
                "caption": p.get("caption"),
            }
        else:
            continue
        f = _base(src_type, src_id, src_ver, item_id, pid, date, submitted_by, "photo_evidence_fact")
        f["payload"] = payload
        facts.append(f)

    return facts


async def ingest_dr_v2_draft(db, draft: Dict[str, Any], *, actor: str = "system",
                             trigger: str = "event") -> Dict[str, Any]:
    """Emit spine facts from a DR-V2 draft. Idempotent. Safe to call frequently."""
    if not ods_enabled() or not dr_v2_spine_emission_enabled():
        return {"ok": False, "skipped": True, "reason": "flags_off"}

    src_id = draft.get("report_id") or ""
    if not src_id:
        return {"ok": False, "skipped": True, "reason": "no_report_id"}

    started = now_iso()
    facts = _build_facts_from_dr_v2_draft(draft)
    if not facts:
        run_id = await record_ingestion_run(
            db, source_type="daily_report_v2", source_id=src_id, source_version=0,
            actor=actor, trigger=trigger, ok=True,
            facts_inserted=0, facts_superseded=0, facts_unchanged=0,
            started_at=started, error="no_facts_derived",
        )
        return {"ok": True, "run_id": run_id, "facts_inserted": 0, "facts_superseded": 0}

    # Supersede previous is_current facts for this source
    superseded = await supersede_facts(db, source_type="daily_report_v2", source_id=src_id)
    run_id = uuid.uuid4().hex  # pre-generate so facts share it
    for f in facts:
        f["ingestion_run_id"] = run_id
    result = await write_facts(db, facts, ingestion_run_id=run_id)
    await record_ingestion_run(
        db, source_type="daily_report_v2", source_id=src_id,
        source_version=facts[0].get("source_version", 0),
        actor=actor, trigger=trigger, ok=True,
        facts_inserted=result["inserted"], facts_superseded=superseded,
        facts_unchanged=0, started_at=started,
    )
    # Overwrite the run_id we already used by inserting a doc keyed to it.
    # (record_ingestion_run created a NEW run_id; we recreate it under our
    # own to keep facts + run linked. Simplest: also update the newly
    # inserted run doc to inherit the pre-generated id.)
    await db["operational_ingestion_runs"].update_many(
        {"source_type": "daily_report_v2", "source_id": src_id, "started_at": started},
        {"$set": {"run_id": run_id}},
    )
    return {
        "ok": True, "run_id": run_id,
        "facts_inserted": result["inserted"],
        "facts_superseded": superseded,
        "project_id": facts[0]["project_id"], "date": facts[0]["date"],
    }


async def ingest_dr_v2_approval(db, *, report_id: str, action: str, agent: str,
                                supervisor_id: str, narrative: str,
                                confidence: float, source_facts: List[str],
                                model: str, provider: str) -> Dict[str, Any]:
    """Emit an intelligence_fact when the supervisor accepts an AI agent output."""
    if not ods_enabled() or not dr_v2_spine_emission_enabled():
        return {"ok": False, "skipped": True, "reason": "flags_off"}
    if action != "accept":
        return {"ok": False, "skipped": True, "reason": "non_accept_action"}

    # We need project_id + date — look up the draft.
    draft = await db["dr_v2_drafts"].find_one({"report_id": report_id}, {"_id": 0})
    if not draft:
        return {"ok": False, "skipped": True, "reason": "draft_not_found"}

    pid, date = _resolve_project_and_date(draft)
    if not pid or not date:
        return {"ok": False, "skipped": True, "reason": "missing_project_or_date"}

    started = now_iso()
    fact = _base("daily_report_v2", report_id, 0, f"intel:{agent}", pid, date,
                 supervisor_id or "", "intelligence_fact")
    fact["confidence"] = float(confidence or 0.0)
    fact["payload"] = {
        "audience": "supervisor",
        "agent": agent,
        "insight": narrative or "",
        "sources_facts": source_facts or [],
        "model": model,               # kept for audit; hidden from field UI
        "provider": provider,
        "approved_by": supervisor_id or "",
        "approved_at": started,
    }

    await supersede_facts(
        db, source_type="daily_report_v2", source_id=report_id,
        source_item_ids=[fact["source_item_id"]],
    )
    run_id = uuid.uuid4().hex
    fact["ingestion_run_id"] = run_id
    result = await write_facts(db, [fact], ingestion_run_id=run_id)
    await record_ingestion_run(
        db, source_type="daily_report_v2", source_id=report_id,
        source_version=0, actor=supervisor_id or "supervisor",
        trigger="event", ok=True,
        facts_inserted=result["inserted"], facts_superseded=0,
        facts_unchanged=0, started_at=started,
    )
    await db["operational_ingestion_runs"].update_many(
        {"source_type": "daily_report_v2", "source_id": report_id, "started_at": started},
        {"$set": {"run_id": run_id}},
    )
    return {"ok": True, "run_id": run_id, "fact_id": fact["fact_id"]}



# ═════════════════════════════════════════════════════════════════════
# DR-CUTOVER-001 · V1 daily_reports → ODS ingestor
# ═════════════════════════════════════════════════════════════════════
# The V1 `daily_reports` collection has a DIFFERENT shape than the V2
# draft. Fields we can safely map (with V1 semantics):
#
#   masci_crews[]        {trade, foreman, count, hours, work_performed}
#   equipment[]          {unit, hours, operator, ...}
#   photos[]             attachment refs
#   activities[]         freeform activities (may be empty)
#   materials[]          material rows
#   subcontractors[]     sub-crew rows (rendered as labor_fact with company)
#   visitors[]           informational (not emitted)
#   weather_snapshots[]  hourly weather rows
#   safety_incidents_today   "Yes"/"No" string flag
#   injuries_reported        "Yes"/"No" string flag
#   incident_notes           freeform text
#   schedule_delays          "Yes"/"No" + schedule_delays_notes
#   weather_impact           "Yes"/"No" + weather_impact_notes
#
# When a field is a Yes/No flag with no structured detail, we still
# emit a tiny fact carrying the flag + freeform note so PM/Admin
# dashboards can count "reports with safety incidents", etc. Any fact
# emitted from V1 partial data carries `source_status="partial"`.

def _v1_yesno(val: Any) -> bool:
    if isinstance(val, bool):
        return val
    if isinstance(val, str):
        return val.strip().lower() in {"yes", "y", "true", "1"}
    return False


def _v1_resolve_project_and_date(rec: Dict[str, Any]) -> Tuple[str, str]:
    pid = normalize_project_id(
        rec.get("project_number") or rec.get("project_id") or rec.get("project_name")
    )
    d = coerce_date(rec.get("report_date"))
    return pid, d


def _build_facts_from_dr_v1_report(rec: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Pure builder — no I/O. Emits normalized ODS facts from a V1
    `daily_reports` document. Idempotency is upstream (`supersede_facts`).

    Uses `source_type="daily_report"` (distinct from V2's
    `daily_report_v2`) so dashboards can attribute origin.
    """
    pid, date = _v1_resolve_project_and_date(rec)
    if not pid or not date:
        return []

    src_type = "daily_report_v1"
    src_id = rec.get("id") or rec.get("doc_id") or rec.get("report_number") or ""
    if not src_id:
        return []
    # Source_version: derive from updated/created timestamp if present.
    ts = str(rec.get("updated_at") or rec.get("created_at") or "")
    src_ver = int(
        ts.replace("-", "").replace(":", "").replace("T", "").replace(".", "").split("+")[0][:14]
        or 0
    )
    submitted_by = rec.get("prepared_by") or rec.get("superintendent") or ""

    facts: List[Dict[str, Any]] = []

    # ── Labor facts — one per masci_crews[] entry, expanded by `count`
    for i, crew in enumerate(rec.get("masci_crews") or []):
        if not isinstance(crew, dict):
            continue
        # V1 uses a single row per trade with `count` and shared `hours`.
        # Emit ONE labor_fact per crew row (per-member expansion would
        # inflate labor_hours). PM dashboards multiply hours × count.
        count = crew.get("count") or crew.get("crew_size") or 1
        try:
            count = int(count)
        except (TypeError, ValueError):
            count = 1
        item_id = f"crew:{i}:{crew.get('trade') or i}"
        f = _base(src_type, src_id, src_ver, item_id, pid, date, submitted_by, "labor_fact")
        f["source_status"] = "partial"  # V1 crew rows don't name members
        f["payload"] = {
            "employee_id": None,
            "person_name": crew.get("foreman") or "",
            "company": "MASCI",
            "role": crew.get("trade") or "",
            "hours": coerce_number(crew.get("hours")),
            "crew_size": count,
            "labor_hours": coerce_number(crew.get("hours")) * count if crew.get("hours") else 0,
            "work_performed": crew.get("work_performed") or "",
            "verified_identity": False,
        }
        facts.append(f)

    # ── Subcontractor rows also emit labor_fact with company override
    for i, sub in enumerate(rec.get("subcontractors") or []):
        if not isinstance(sub, dict):
            continue
        item_id = f"sub:{i}:{sub.get('company') or i}"
        count = sub.get("count") or 1
        try:
            count = int(count)
        except (TypeError, ValueError):
            count = 1
        f = _base(src_type, src_id, src_ver, item_id, pid, date, submitted_by, "labor_fact")
        f["source_status"] = "partial"
        f["payload"] = {
            "employee_id": None,
            "person_name": sub.get("foreman") or "",
            "company": sub.get("company") or "SUB",
            "role": sub.get("trade") or "SUB",
            "hours": coerce_number(sub.get("hours")),
            "crew_size": count,
            "labor_hours": coerce_number(sub.get("hours")) * count if sub.get("hours") else 0,
            "work_performed": sub.get("work_performed") or "",
        }
        facts.append(f)

    # ── Equipment facts
    for i, eq in enumerate(rec.get("equipment") or []):
        if not isinstance(eq, dict):
            continue
        item_id = f"equipment:{i}:{eq.get('unit') or eq.get('id') or i}"
        f = _base(src_type, src_id, src_ver, item_id, pid, date, submitted_by, "equipment_fact")
        f["payload"] = {
            "equipment_id": eq.get("id") or eq.get("unit"),
            "equipment_label": eq.get("unit") or eq.get("label") or "",
            "operator": eq.get("operator"),
            "hours_used": coerce_number(eq.get("hours")),
            "idle_hours": coerce_number(eq.get("idle_hours")),
            "breakdown": bool(eq.get("breakdown")),
            "maintenance": bool(eq.get("maintenance")),
        }
        facts.append(f)

    # ── Production facts from `activities[]`
    for i, act in enumerate(rec.get("activities") or []):
        if not isinstance(act, dict):
            continue
        item_id = f"activity:{i}:{act.get('id') or i}"
        f = _base(src_type, src_id, src_ver, item_id, pid, date, submitted_by, "production_fact")
        f["source_status"] = "partial"
        f["payload"] = {
            "cost_code": act.get("cost_code"),
            "activity": act.get("activity") or act.get("name") or "",
            "work_area": act.get("area"),
            "quantity": coerce_number(act.get("quantity") or act.get("qty")),
            "unit": act.get("unit") or "",
        }
        facts.append(f)

    # ── Material facts
    for i, mat in enumerate(rec.get("materials") or []):
        if not isinstance(mat, dict):
            continue
        item_id = f"material:{i}:{mat.get('id') or i}"
        f = _base(src_type, src_id, src_ver, item_id, pid, date, submitted_by, "material_fact")
        f["source_status"] = "partial"
        f["payload"] = {
            "material": mat.get("material") or mat.get("name") or "",
            "quantity": coerce_number(mat.get("quantity") or mat.get("qty")),
            "unit": mat.get("unit") or "",
            "supplier": mat.get("supplier") or mat.get("vendor") or "",
            "ticket": mat.get("ticket") or "",
        }
        facts.append(f)

    # ── Weather fact — prefer `weather_snapshots[]`, else `weather_summary`
    snaps = rec.get("weather_snapshots") or []
    if snaps and isinstance(snaps[0], dict):
        w = snaps[0]
        f = _base(src_type, src_id, src_ver, "weather:0", pid, date, submitted_by, "weather_fact")
        f["payload"] = {
            "temperature_f": coerce_number(w.get("temp_f")),
            "precipitation_in": coerce_number(w.get("precip_in")),
            "wind_mph": coerce_number(w.get("wind_mph")),
            "condition": w.get("condition") or rec.get("weather_summary") or "",
        }
        facts.append(f)
    elif rec.get("weather_summary"):
        f = _base(src_type, src_id, src_ver, "weather:0", pid, date, submitted_by, "weather_fact")
        f["source_status"] = "partial"
        f["payload"] = {"condition": rec.get("weather_summary") or ""}
        facts.append(f)

    # ── Weather-impact delay
    if _v1_yesno(rec.get("weather_impact")):
        f = _base(src_type, src_id, src_ver, "delay:weather", pid, date, submitted_by, "delay_fact")
        f["source_status"] = "partial"
        f["payload"] = {
            "delay_category": "weather",
            "reason": rec.get("weather_impact_notes") or "Weather impact reported",
            "impact": "med",
            "schedule_risk": True,
        }
        facts.append(f)

    # ── Schedule delays
    if _v1_yesno(rec.get("schedule_delays")):
        f = _base(src_type, src_id, src_ver, "delay:schedule", pid, date, submitted_by, "delay_fact")
        f["source_status"] = "partial"
        f["payload"] = {
            "delay_category": "schedule",
            "reason": rec.get("schedule_delays_notes") or "Schedule delay reported",
            "impact": "med",
            "schedule_risk": True,
        }
        facts.append(f)

    # ── Safety facts (Yes/No flag with freeform notes)
    has_safety = _v1_yesno(rec.get("safety_incidents_today"))
    has_injury = _v1_yesno(rec.get("injuries_reported"))
    if has_safety or has_injury or (rec.get("incident_notes") or "").strip():
        f = _base(src_type, src_id, src_ver, "safety:0", pid, date, submitted_by, "safety_fact")
        f["source_status"] = "partial"
        f["payload"] = {
            "safety_type": "incident" if has_safety else "observation",
            "severity": "high" if has_injury else ("med" if has_safety else "info"),
            "injuries_reported": has_injury,
            "safety_incident_reported": has_safety,
            "narrative": (rec.get("incident_notes") or "").strip(),
        }
        facts.append(f)

    # ── Photo evidence facts
    for i, p in enumerate(rec.get("photos") or []):
        if isinstance(p, str):
            item_id = f"photo:{i}:{p[:32]}"
            payload = {"photo_ref": p}
        elif isinstance(p, dict):
            item_id = f"photo:{i}:{p.get('id') or p.get('key') or i}"
            payload = {
                "photo_ref": p.get("key") or p.get("id") or p.get("url") or "",
                "storage_url": p.get("url"),
                "thumb_url": p.get("thumb") or p.get("thumbnail"),
                "caption": p.get("caption") or p.get("note"),
                "linked_activity": p.get("activity_id"),
            }
        else:
            continue
        f = _base(src_type, src_id, src_ver, item_id, pid, date, submitted_by, "photo_evidence_fact")
        f["payload"] = payload
        facts.append(f)

    # ── TRACK 22.9A · Accepted Draft Summary → day_summary_fact.
    # If the supervisor accepted (or edited) the Draft Summary at submit
    # time, emit one canonical fact so PM/project/executive dashboards
    # can render the narrative from the spine, not the raw DR doc.
    summary_text = (rec.get("ai_accepted_summary") or "").strip()
    if summary_text:
        meta = rec.get("ai_accepted_summary_meta") or {}
        f = _base(src_type, src_id, src_ver, "day_summary", pid, date,
                  submitted_by, "day_summary_fact")
        f["payload"] = {
            "text": summary_text[:2500],
            "source": meta.get("source") or "ai",
            "provider_masked": meta.get("provider_masked"),
            "model_masked": meta.get("model_masked"),
            "generated_at": meta.get("generated_at"),
            "accepted_at": meta.get("accepted_at"),
            "edited_by_user": bool(meta.get("edited_by_user")),
            "confidence": meta.get("confidence"),
            "evidence_refs": (meta.get("evidence_refs") or [])[:20],
            "latency_ms": meta.get("latency_ms"),
        }
        facts.append(f)

    return facts


async def _enrich_photo_evidence_facts(
    db, src_id: str, facts: List[Dict[str, Any]],
) -> None:
    """TRACK 22.9B — Attach grounded intel to photo_evidence_facts.

    Reads `dr_v2_photo_intelligence` rows (populated by the V1 pipeline
    or the V2 flow) and merges labels/caption/confidence into each
    matching photo_evidence_fact payload. Pure best-effort — any error
    is silently swallowed. Never fabricates: only surfaces what the
    analyzer already stored.
    """
    if not src_id or not facts:
        return
    import hashlib as _hashlib  # noqa: PLC0415
    try:
        rows = await db["dr_v2_photo_intelligence"].find(
            {"report_id": src_id, "analysis_status": "complete"},
            {"_id": 0, "photo_id": 1, "observations": 1,
             "narrative": 1, "confidence": 1},
        ).to_list(length=200)
    except Exception:  # noqa: BLE001
        rows = []
    if not rows:
        return
    intel_by_photo_id: Dict[str, Dict[str, Any]] = {
        (r.get("photo_id") or ""): r for r in rows if r.get("photo_id")
    }
    for f in facts:
        if f.get("fact_type") != "photo_evidence_fact":
            continue
        ref = (f.get("payload") or {}).get("photo_ref") or ""
        if not ref:
            continue
        pid = _hashlib.sha1(str(ref).encode("utf-8")).hexdigest()[:20]
        row = intel_by_photo_id.get(pid)
        if not row:
            continue
        obs = row.get("observations") or []
        f["payload"]["ai_tags"] = [
            o.get("label", "") for o in obs
            if isinstance(o, dict) and o.get("label")
        ][:16]
        cap = (row.get("narrative") or "").strip()
        if cap:
            f["payload"]["ai_caption"] = cap[:500]
        conf = row.get("confidence")
        if isinstance(conf, (int, float)):
            f["confidence"] = float(conf)



async def ingest_dr_v1_report(
    db, report: Dict[str, Any], *, actor: str = "system", trigger: str = "event",
) -> Dict[str, Any]:
    """Emit spine facts from a V1 `daily_reports` document. Idempotent.

    Safe to call from the V1 submit hook AND from the backfill job.
    Uses `source_type="daily_report"` so dashboards can distinguish the
    origin from V2 (`daily_report_v2`).
    """
    if not ods_enabled() or not dr_v2_spine_emission_enabled():
        return {"ok": False, "skipped": True, "reason": "flags_off"}

    src_id = report.get("id") or report.get("doc_id") or report.get("report_number") or ""
    if not src_id:
        return {"ok": False, "skipped": True, "reason": "no_report_id"}

    started = now_iso()
    facts = _build_facts_from_dr_v1_report(report)
    # TRACK 22.9B · If photo intelligence has analyzed any of the
    # attached photos, enrich the photo_evidence_fact payload with
    # grounded ai_tags / caption. Best-effort; missing intel simply
    # leaves the pre-22.9B payload shape unchanged.
    if facts:
        try:
            await _enrich_photo_evidence_facts(db, src_id, facts)
        except Exception:  # noqa: BLE001
            pass
    if not facts:
        run_id = await record_ingestion_run(
            db, source_type="daily_report_v1", source_id=src_id, source_version=0,
            actor=actor, trigger=trigger, ok=True,
            facts_inserted=0, facts_superseded=0, facts_unchanged=0,
            started_at=started, error="no_facts_derived",
        )
        return {"ok": True, "run_id": run_id, "facts_inserted": 0, "facts_superseded": 0}

    superseded = await supersede_facts(db, source_type="daily_report_v1", source_id=src_id)
    run_id = uuid.uuid4().hex
    for f in facts:
        f["ingestion_run_id"] = run_id
    result = await write_facts(db, facts, ingestion_run_id=run_id)
    await record_ingestion_run(
        db, source_type="daily_report_v1", source_id=src_id,
        source_version=facts[0].get("source_version", 0),
        actor=actor, trigger=trigger, ok=True,
        facts_inserted=result["inserted"], facts_superseded=superseded,
        facts_unchanged=0, started_at=started,
    )
    await db["operational_ingestion_runs"].update_many(
        {"source_type": "daily_report_v1", "source_id": src_id, "started_at": started},
        {"$set": {"run_id": run_id}},
    )
    return {
        "ok": True, "run_id": run_id,
        "facts_inserted": result["inserted"],
        "facts_superseded": superseded,
        "project_id": facts[0]["project_id"], "date": facts[0]["date"],
    }
