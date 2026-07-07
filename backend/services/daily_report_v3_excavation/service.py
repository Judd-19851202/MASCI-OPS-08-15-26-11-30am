"""TRACK 23.10-E · Daily Report V3 Excavation submit-time service.

Called from `POST /api/daily-reports` after the DR document is minted.
Enforces the following invariants:

* Competent Person selection MUST come from the Track 23.10-B active
  Qualifications Engine registry. Free-text is rejected 400.
* Expired · suspended · revoked · pending qualifications are rejected.
* On accept:
  * Freezes a qualification snapshot (from 23.10-B).
  * Emits `competent_person_assignment_fact` (23.10-C).
  * Emits `excavation_day_fact` (23.10-C).
  * Computes and returns a Scheduling readiness snapshot.
* Non-excavation reports pass through unchanged.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional, Tuple

from fastapi import HTTPException

from services.certifications.qualification_registry import (
    get_qualification_snapshot, is_active,
)
from services.trench_safety.facts_emitter import (
    emit_competent_person_assignment_fact,
    emit_excavation_day_fact,
    recompute_project_excavation_summary,
)


READINESS_STATES = (
    "READY", "READY_WITH_ADVISORIES", "PENDING_REQUIREMENTS",
    "BLOCKED", "UNKNOWN",
)

# Cost/money guard — belt-and-suspenders on the DR write path.
BANNED_COST_KEYS = frozenset({
    "cost", "rate", "budget", "payroll", "wage", "wages",
    "dollars", "amount", "price", "spend", "spent", "revenue",
})


def _has_excavation(dr_doc: Dict[str, Any]) -> bool:
    """Any of the multiple gate fields signals excavation-today = YES."""
    v = str(dr_doc.get("excavation_activity_today") or "").strip().lower()
    if v in ("yes", "true", "y", "1"):
        return True
    exc = dr_doc.get("excavation") or {}
    if isinstance(exc, dict):
        gate = str(exc.get("excavation_today") or "").strip().lower()
        if gate in ("yes", "true", "y", "1"):
            return True
    return False


def _scrub_cost(obj: Any) -> Any:
    if isinstance(obj, dict):
        return {k: _scrub_cost(v) for k, v in obj.items()
                if k not in BANNED_COST_KEYS}
    if isinstance(obj, list):
        return [_scrub_cost(x) for x in obj]
    return obj


def _compute_readiness(exc: Dict[str, Any], cp_snapshot: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Deterministic readiness derivation. Never claims safe when any
    hard block is present. Safety remains authority — this only reads
    what the field crew declared."""
    def yn(v):
        s = str(v or "").strip().lower()
        return s in ("yes", "true", "y", "1")

    signals = {
        "excavation_work_today": True,
        "competent_person_assigned": bool(exc.get("competent_person_qualification_id")),
        "competent_person_qualification_active": bool(
            cp_snapshot and cp_snapshot.get("is_active_at_selection")
        ),
        "inspection_completed": yn(exc.get("inspection_completed")),
        "hold_issued": yn(exc.get("hold_issued")),
        "work_stopped": yn(exc.get("work_stopped")),
        "utility_conflict": yn(exc.get("utility_conflict")),
        "utility_damage_or_strike": yn(exc.get("utility_damage_or_strike")),
        "hazards_open": yn(exc.get("hazards_identified"))
            and not yn(exc.get("corrective_actions_complete")),
        "corrective_actions_open": yn(exc.get("corrective_actions_open")),
        "access_egress_ok": str(exc.get("access_egress_compliant") or "").lower() in ("yes", "true", "n/a", "na"),
        "atmosphere_ok_or_not_required":
            str(exc.get("atmospheric_testing_required") or "").lower() in ("no", "n/a", "na", "")
            or yn(exc.get("atmosphere_safe")),
        "water_mitigation_ok":
            not yn(exc.get("water_accumulation"))
            or bool((exc.get("water_mitigation") or "").strip()),
        "protective_system_selected": bool(
            [p for p in (exc.get("protective_systems") or []) if p]
            or (exc.get("protective_system") or "")
        ),
    }

    # Blocking rules.
    blockers = []
    if not signals["competent_person_assigned"]:
        blockers.append("no_active_competent_person")
    if not signals["competent_person_qualification_active"] and signals["competent_person_assigned"]:
        blockers.append("competent_person_qualification_inactive")
    if signals["hold_issued"]:
        blockers.append("hold_issued")
    if signals["work_stopped"] and not (exc.get("restart_time") or "").strip():
        blockers.append("work_stopped_no_restart")
    if signals["utility_damage_or_strike"]:
        blockers.append("utility_damage_or_strike")
    if str(exc.get("atmosphere_safe") or "").lower() == "no":
        blockers.append("unsafe_atmosphere")
    if not signals["protective_system_selected"]:
        blockers.append("no_protective_system_selected")
    if yn(exc.get("inspection_required")) and not signals["inspection_completed"]:
        blockers.append("inspection_required_but_not_completed")

    # Advisories (non-blocking).
    advisories = []
    if signals["utility_conflict"] and not signals["utility_damage_or_strike"]:
        advisories.append("utility_conflict_present")
    if signals["hazards_open"]:
        advisories.append("hazards_open")
    if signals["corrective_actions_open"]:
        advisories.append("corrective_actions_open")
    if not signals["access_egress_ok"]:
        advisories.append("access_egress_not_confirmed")
    if not signals["atmosphere_ok_or_not_required"]:
        advisories.append("atmosphere_unverified")
    if not signals["water_mitigation_ok"]:
        advisories.append("water_unmitigated")
    if not signals["inspection_completed"] and not yn(exc.get("inspection_required")):
        advisories.append("inspection_not_recorded")

    if blockers:
        state = "BLOCKED"
    elif not signals["excavation_work_today"]:
        state = "UNKNOWN"
    elif advisories:
        state = "READY_WITH_ADVISORIES"
    else:
        state = "READY"

    return {
        "state": state,
        "signals": signals,
        "blockers": blockers,
        "advisories": advisories,
        "safety_clear_to_schedule": (state in ("READY", "READY_WITH_ADVISORIES")),
        "computed_at": datetime.now(timezone.utc).isoformat(),
    }


async def process_excavation_on_submit(
    db, dr_doc: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """Called after a DR is inserted. Returns the enriched
    `excavation` payload (with `qualification_snapshot` + `readiness`)
    or None if the report is non-excavation.

    Raises 400 when the CP selection is invalid — the DR submit route
    should surface this to the client.
    """
    if not _has_excavation(dr_doc):
        return None

    exc = dict(dr_doc.get("excavation") or {})
    exc = _scrub_cost(exc)

    # ── Competent Person gate ──────────────────────────────────────
    qid = exc.get("competent_person_qualification_id") or ""
    cp_snapshot: Optional[Dict[str, Any]] = None
    if qid:
        cp_snapshot = await get_qualification_snapshot(db, qid)
        if not cp_snapshot:
            raise HTTPException(
                400,
                {"error": "competent_person_invalid",
                 "message": "Competent Person qualification not found. "
                            "Selection must come from the active Qualifications Engine registry."},
            )
        if not cp_snapshot.get("is_active_at_selection"):
            raise HTTPException(
                400,
                {"error": "competent_person_not_active",
                 "message": "Selected Competent Person qualification is not "
                            "currently active (expired · suspended · revoked · pending)."},
            )
        if cp_snapshot.get("qualification_type") != "COMPETENT_PERSON":
            raise HTTPException(
                400,
                {"error": "wrong_qualification_type",
                 "message": "Selected qualification is not COMPETENT_PERSON."},
            )
        exc["qualification_snapshot"] = cp_snapshot
    # Free-text name is REJECTED — 23.10-E doctrine.
    elif (exc.get("competent_person_name_freetext") or "").strip():
        raise HTTPException(
            400,
            {"error": "free_text_competent_person_forbidden",
             "message": "Competent Person must be selected from the Qualifications Engine registry."},
        )

    # ── Readiness snapshot ─────────────────────────────────────────
    readiness = _compute_readiness(exc, cp_snapshot)
    exc["readiness"] = readiness
    exc["excavation_today"] = "yes"                 # canonical gate

    project_number = (dr_doc.get("project_number")
                      or (dr_doc.get("day_setup") or {}).get("project_number")
                      or "")

    # ── ODS fact emissions (idempotent) ────────────────────────────
    if cp_snapshot:
        try:
            await emit_competent_person_assignment_fact(
                db,
                project_number=project_number or None,
                consumer_collection="daily_reports",
                consumer_source_id="daily_reports",
                consumer_row_id=dr_doc.get("id"),
                qualification_snapshot=cp_snapshot,
                date_of_work=dr_doc.get("report_date"),
                actor=dr_doc.get("prepared_by") or "field",
                trigger="daily_reports.submit",
            )
        except Exception:                                          # noqa: BLE001
            pass                                                    # never fail the DR

    # `excavation_day_fact` — if the DR does not link a physical
    # trench_excavations record, we still emit an excavation-day fact
    # from the DR payload so downstream KPIs and the Safety Portal
    # register today's activity. The emitter is idempotent on the DR
    # id, so re-submit of the same DR collapses to 1 current fact.
    exc_shape = {
        "id": f"dr:{dr_doc.get('id')}",
        "report_id": dr_doc.get("id"),
        "daily_report_doc_id": dr_doc.get("id"),
        "project_number": project_number,
        "project_name": dr_doc.get("project_name"),
        "date_of_work": dr_doc.get("report_date"),
        "excavation_type": "trench",
        "max_depth_ft": exc.get("depth"),
        "protective_system": ", ".join(exc.get("protective_systems") or []),
        "inspection_completed": bool(exc.get("inspection_completed") in
                                     (True, "yes", "true", "1")),
        "hold_issued": bool(exc.get("hold_issued") in (True, "yes", "true", "1")),
        "utilities_status": ("damage_strike"
                             if str(exc.get("utility_damage_or_strike") or "").lower() in ("yes", "true")
                             else ("conflict"
                                   if str(exc.get("utility_conflict") or "").lower() in ("yes", "true")
                                   else "none")),
        "tomorrow_planned": False,
        "crew": dr_doc.get("masci_crews") or [],
        "competent_person_name": (cp_snapshot or {}).get("person_name_snapshot")
            or exc.get("competent_person_name_snapshot") or "",
        "competent_person_confirmed": bool(cp_snapshot),
    }
    try:
        await emit_excavation_day_fact(
            db, exc_shape,
            actor=dr_doc.get("prepared_by") or "field",
            trigger="daily_reports.excavation.submit",
        )
    except Exception:                                              # noqa: BLE001
        pass

    # ── Refresh per-project summary fact so Safety Portal / PM /
    # Scheduling read fresh counts immediately after submit.
    # Best-effort · never fail a DR submit on this hook.
    if project_number:
        try:
            await recompute_project_excavation_summary(
                db, project_number,
                actor=dr_doc.get("prepared_by") or "field",
                trigger="daily_reports.excavation.submit",
            )
        except Exception:                                          # noqa: BLE001
            pass

    # Store enriched excavation on the DR document.
    await db.daily_reports.update_one(
        {"id": dr_doc.get("id")},
        {"$set": {"excavation": exc}},
    )
    return exc


def excavation_evidence_for_ai(dr_doc: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Return the AI evidence sub-bundle for an excavation-enabled DR.

    Consumers (`services/ai/daily_summary_assist.py` / equivalent)
    should splice this dict under a top-level `excavation` key on the
    evidence they send to the model. Only excavation-enabled DRs
    return a non-None result — matches the mandate.
    """
    if not _has_excavation(dr_doc):
        return None
    exc = dr_doc.get("excavation") or {}
    if not isinstance(exc, dict):
        return None
    snap = exc.get("qualification_snapshot") or {}
    readiness = exc.get("readiness") or {}
    return _scrub_cost({
        "excavation_gate": "yes",
        "location": {
            "project_area": exc.get("project_area"),
            "station_from": exc.get("station_from"),
            "station_to": exc.get("station_to"),
            "location_notes": exc.get("location_notes"),
            "gps": exc.get("gps"),
        },
        "dimensions": {
            "length": exc.get("length"), "width": exc.get("width"),
            "depth": exc.get("depth"),
            "unit": exc.get("dimension_unit") or "ft",
        },
        "protective_system": {
            "systems": exc.get("protective_systems") or [],
            "notes": exc.get("protective_system_notes"),
        },
        "soil": {"type": exc.get("soil_type"), "notes": exc.get("soil_notes")},
        "utilities": {
            "exposed": exc.get("utilities_exposed") or [],
            "conflict": exc.get("utility_conflict"),
            "damage_or_strike": exc.get("utility_damage_or_strike"),
            "notes": exc.get("utilities_notes"),
        },
        "competent_person": {
            "employee_id": snap.get("employee_id"),
            "name": snap.get("person_name_snapshot"),
            "trade": snap.get("person_trade_snapshot"),
            "crew": snap.get("person_crew_snapshot"),
            "supervisor": snap.get("person_supervisor_snapshot"),
            "qualification_status": snap.get("verification_status_at_selection"),
            "expires_at": snap.get("expires_at_at_selection"),
            "cert_valid_at_report": snap.get("is_active_at_selection"),
        },
        "inspection": {
            "completed": exc.get("inspection_completed"),
            "time": exc.get("inspection_time"),
            "reinspection_required": exc.get("reinspection_required"),
            "weather_reinspection": exc.get("weather_reinspection"),
            "hazard_reinspection": exc.get("hazard_reinspection"),
        },
        "work_stoppage": {
            "stopped": exc.get("work_stopped"),
            "reason": exc.get("work_stop_reason"),
            "corrected": exc.get("work_stop_corrected"),
            "restart_time": exc.get("restart_time"),
            "hold_issued": exc.get("hold_issued"),
        },
        "access": {
            "compliant": exc.get("access_egress_compliant"),
            "notes": exc.get("access_notes"),
        },
        "atmosphere": {
            "required": exc.get("atmospheric_testing_required"),
            "safe": exc.get("atmosphere_safe"),
            "readings": exc.get("atmosphere_readings"),
            "notes": exc.get("atmosphere_notes"),
        },
        "water": {
            "accumulation": exc.get("water_accumulation"),
            "mitigation": exc.get("water_mitigation"),
        },
        "hazards": {
            "identified": exc.get("hazards_identified"),
            "corrective_actions": exc.get("corrective_actions"),
            "corrective_actions_open": exc.get("corrective_actions_open"),
        },
        "photos": {
            "count": len(exc.get("photo_refs") or []),
            "refs": exc.get("photo_refs") or [],
        },
        "readiness": {
            "state": readiness.get("state"),
            "blockers": readiness.get("blockers") or [],
            "advisories": readiness.get("advisories") or [],
        },
        # Deterministic fallback signals — the AI must not overclaim.
        "ai_guidance": {
            "must_not_claim_safe_to_use":
                "only when readiness.state == READY AND no blockers.",
            "must_not_hallucinate": True,
            "summary_scope": "excavation observations only when this block is present.",
        },
    })


def excavation_pdf_section(dr_doc: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Return the structured section injected into the Daily Report
    PDF renderer as 'Excavation / Trench Operations'.  Empty for
    non-excavation reports so the PDF stays clean."""
    if not _has_excavation(dr_doc):
        return None
    exc = dr_doc.get("excavation") or {}
    snap = exc.get("qualification_snapshot") or {}
    readiness = exc.get("readiness") or {}

    def _kv(label, value):
        if value in (None, "", []):
            return None
        if isinstance(value, list):
            value = ", ".join(str(x) for x in value)
        return {"label": label, "value": str(value)}

    rows = list(filter(None, [
        _kv("Project area", exc.get("project_area")),
        _kv("Station from", exc.get("station_from")),
        _kv("Station to", exc.get("station_to")),
        _kv("Location notes", exc.get("location_notes")),
        _kv("Length", exc.get("length")),
        _kv("Width", exc.get("width")),
        _kv("Depth", exc.get("depth")),
        _kv("Unit", exc.get("dimension_unit") or "ft"),
        _kv("Protective system", exc.get("protective_systems")),
        _kv("Protective system notes", exc.get("protective_system_notes")),
        _kv("Soil type", exc.get("soil_type")),
        _kv("Soil notes", exc.get("soil_notes")),
        _kv("Utilities exposed", exc.get("utilities_exposed")),
        _kv("Utility conflict", exc.get("utility_conflict")),
        _kv("Utility damage/strike", exc.get("utility_damage_or_strike")),
        _kv("Utility notes", exc.get("utilities_notes")),
        _kv("Access/egress compliant", exc.get("access_egress_compliant")),
        _kv("Atmospheric testing required", exc.get("atmospheric_testing_required")),
        _kv("Atmosphere safe", exc.get("atmosphere_safe")),
        _kv("Atmosphere readings", exc.get("atmosphere_readings")),
        _kv("Water accumulation", exc.get("water_accumulation")),
        _kv("Water mitigation", exc.get("water_mitigation")),
        _kv("Inspection completed", exc.get("inspection_completed")),
        _kv("Inspection time", exc.get("inspection_time")),
        _kv("Reinspection required", exc.get("reinspection_required")),
        _kv("Hazards identified", exc.get("hazards_identified")),
        _kv("Corrective actions", exc.get("corrective_actions")),
        _kv("Work stopped", exc.get("work_stopped")),
        _kv("Stop reason", exc.get("work_stop_reason")),
        _kv("Restart time", exc.get("restart_time")),
        _kv("Hold issued", exc.get("hold_issued")),
    ]))
    cp_rows = list(filter(None, [
        _kv("Competent Person", snap.get("person_name_snapshot")),
        _kv("Trade / role", snap.get("person_trade_snapshot")),
        _kv("Crew", snap.get("person_crew_snapshot")),
        _kv("Qualification status at submit",
            snap.get("verification_status_at_selection")),
        _kv("Qualification expiration at submit",
            snap.get("expires_at_at_selection")),
        _kv("Certificate valid at submit",
            "yes" if snap.get("is_active_at_selection") else "no"),
        _kv("Issuing organisation", snap.get("issuing_organization")),
        _kv("Certificate number", snap.get("certificate_number")),
    ]))
    return _scrub_cost({
        "title": "Excavation / Trench Operations",
        "rows": rows,
        "competent_person_snapshot": cp_rows,
        "readiness_state": readiness.get("state") or "UNKNOWN",
        "readiness_blockers": readiness.get("blockers") or [],
        "readiness_advisories": readiness.get("advisories") or [],
        "photo_refs": exc.get("photo_refs") or [],
        "ai_summary": (exc.get("ai_excavation_summary")
                       or dr_doc.get("ai_accepted_summary_excavation") or ""),
    })


def excavation_email_summary(dr_doc: Dict[str, Any]) -> str:
    """Compact text-only summary appended to the Daily Report email
    ONLY when excavation exists. Never claims safe-to-use unless
    readiness is READY."""
    if not _has_excavation(dr_doc):
        return ""
    exc = dr_doc.get("excavation") or {}
    snap = exc.get("qualification_snapshot") or {}
    readiness = exc.get("readiness") or {}
    lines = [
        "Excavation / trench operations were performed today.",
        f"  Location: {exc.get('project_area') or 'n/a'} · "
        f"{exc.get('station_from') or ''}–{exc.get('station_to') or ''}",
        f"  Dimensions: {exc.get('length') or '?'} × {exc.get('width') or '?'} × "
        f"{exc.get('depth') or '?'} {exc.get('dimension_unit') or 'ft'}",
        f"  Protective system: "
        f"{', '.join(exc.get('protective_systems') or []) or 'not recorded'}",
        f"  Soil type: {exc.get('soil_type') or 'not recorded'}",
        f"  Competent Person: {snap.get('person_name_snapshot') or 'MISSING'}"
        f" · cert {'VALID' if snap.get('is_active_at_selection') else 'REVIEW'}",
        f"  Inspection completed: {exc.get('inspection_completed') or 'no'}",
        f"  Readiness: {readiness.get('state') or 'UNKNOWN'}",
    ]
    if readiness.get("blockers"):
        lines.append(f"  Blockers: {', '.join(readiness['blockers'])}")
    if readiness.get("advisories"):
        lines.append(f"  Advisories: {', '.join(readiness['advisories'])}")
    return "\n".join(lines)


__all__ = [
    "process_excavation_on_submit",
    "excavation_evidence_for_ai",
    "excavation_pdf_section",
    "excavation_email_summary",
    "READINESS_STATES",
    "BANNED_COST_KEYS",
]
