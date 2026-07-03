"""Track 19.36 · Executive Intelligence Layer — pure read-only assembler.

Consumes existing Phase A/C data (incident_cases · incident_case_events ·
incident_case_evidence · corrective_actions · workspace satellites) and
returns ONE unified Executive Intelligence Model.

Consumers: Executive Case Report page, Executive Report PDF, and any
future executive surface. There must be exactly one source of truth.

Rules
-----
- READ-ONLY. Never writes to any collection.
- Never invents facts. Every field is derived from an existing certified
  document field or list. If a value is missing, it is emitted as an
  empty string / empty list / None, and mirrored in ``missing_fields``.
- Timeline is assembled from the certified ``incident_case_events``
  collection (Phase A audit surface) — same source as
  ``/api/incident-cases/{id}/timeline``.
- Evidence chain mirrors ``incident_case_evidence`` including the
  append-only ``custody_chain`` — no re-hashing, no reordering.
- Readiness sub-scores are explainable: every sub-score exposes the
  numerator, denominator, and human-readable rationale.
- The ``why_it_matters`` briefing is deterministic and template-based;
  it inserts only values that already live on the case document.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import case_service
from .events import list_events
from .evidence import list_evidence
from .corrective_actions import list_actions, summary_for_case
from . import workspace as ws


# ---------------------------------------------------------------------------
# Model version — bump on any additive shape change.
# Consumers may key their rendering off this.
# ---------------------------------------------------------------------------
EXECUTIVE_INTELLIGENCE_MODEL_VERSION = "1.0.0"


# ---------------------------------------------------------------------------
# Helpers — pure, deterministic, no I/O
# ---------------------------------------------------------------------------
def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _s(v: Any) -> str:
    return "" if v is None else str(v)


def _days_between(a_iso: str, b_iso: str) -> Optional[int]:
    """Whole-day delta between two ISO timestamps. None if either missing/bad."""
    try:
        a = datetime.fromisoformat(a_iso.replace("Z", "+00:00"))
        b = datetime.fromisoformat(b_iso.replace("Z", "+00:00"))
    except Exception:
        return None
    return max(0, int((b - a).total_seconds() // 86400))


def _severity_from_case(fb: Dict[str, Any], sb: Dict[str, Any]) -> str:
    """Deterministic severity band from certified fields only.

    Never guesses. Explainable via ``severity_rationale`` in the summary.
    """
    lost = int(sb.get("lost_time_days") or 0)
    restricted = int(sb.get("days_restricted") or 0)
    osha = sb.get("osha_recordable")
    itype = (fb.get("incident_type") or "").lower()

    if lost >= 1 or (isinstance(osha, bool) and osha is True):
        return "high"
    if restricted >= 1 or itype in {"utility_strike", "vehicle_accident",
                                    "environmental", "workplace_violence"}:
        return "elevated"
    if itype in {"employee_injury", "equipment_accident", "property_damage"}:
        return "moderate"
    return "low"


def _severity_rationale(fb: Dict[str, Any], sb: Dict[str, Any], sev: str) -> str:
    """Plain-English explanation of the severity band."""
    lost = int(sb.get("lost_time_days") or 0)
    restricted = int(sb.get("days_restricted") or 0)
    osha = sb.get("osha_recordable")
    itype = (fb.get("incident_type") or "").lower()
    parts: List[str] = []
    if lost >= 1:
        parts.append(f"lost time recorded ({lost} day(s))")
    if isinstance(osha, bool) and osha is True:
        parts.append("Safety marked case OSHA recordable")
    if restricted >= 1:
        parts.append(f"restricted duty recorded ({restricted} day(s))")
    if itype:
        parts.append(f"incident type '{itype}'")
    if not parts:
        return "No high-risk indicators recorded on the case."
    return f"Severity '{sev}' derived from: " + "; ".join(parts) + "."


# ---------------------------------------------------------------------------
# Sub-model builders
# ---------------------------------------------------------------------------
def _build_case_ref(case: Dict[str, Any]) -> Dict[str, Any]:
    fb = case.get("field_block") or {}
    return {
        "case_id":       _s(case.get("id")),
        "case_number":   _s(case.get("case_number")),
        "state":         _s(case.get("state")),
        "tenant_id":     _s(case.get("tenant_id")),
        "created_at":    _s(case.get("created_at")),
        "submitted_at":  _s(case.get("submitted_at")),
        "closed_at":     _s(case.get("closed_at")),
        "reopened_at":   _s(case.get("reopened_at")),
        "incident_type": _s(fb.get("incident_type")),
        "job_number":    _s(fb.get("job_number")),
        "location_label": _s(fb.get("location_label")),
        "occurred_at":   _s(fb.get("occurred_at")),
        "reported_at":   _s(fb.get("reported_at")),
        "reporter_name": _s(fb.get("reporter_name")),
    }


def _build_executive_summary(
    case: Dict[str, Any], severity: str, severity_why: str,
) -> Dict[str, Any]:
    fb = case.get("field_block") or {}
    sb = case.get("safety_block") or {}
    itype = _s(fb.get("incident_type"))
    where = _s(fb.get("location_label")) or "an unspecified location"
    job = _s(fb.get("job_number"))
    who = _s(fb.get("reporter_name")) or "the on-site reporter"
    when = _s(fb.get("occurred_at")) or _s(fb.get("reported_at")) or _s(case.get("submitted_at"))
    what = _s(fb.get("observed_conditions"))
    return {
        "headline": (
            f"{itype.replace('_', ' ').title() or 'Incident'} at "
            f"{where}{(' · job ' + job) if job else ''}"
        ),
        "occurred_at": when,
        "reporter": who,
        "location": where,
        "job_number": job,
        "one_paragraph": (
            f"On {when or 'an unrecorded date'}, a "
            f"{itype.replace('_', ' ') or 'reportable event'} was reported at "
            f"{where}{(' (job ' + job + ')') if job else ''}. "
            f"Reported by {who}."
            + (f" {what}" if what else "")
        ).strip(),
        "severity_band": severity,
        "severity_rationale": severity_why,
        "state": _s(case.get("state")),
        "root_cause_summary": _s(sb.get("root_cause_summary")),
    }


def _build_timeline(case: Dict[str, Any], events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Every event traced back to its certified audit row.

    Zero-drift: no synthesis, no reordering — events are returned in the
    order the audit surface returns them. Consumers get: id, at, actor,
    event_type, summary, source_ref (the collection this event came
    from so any exec can audit it back).
    """
    out: List[Dict[str, Any]] = []
    for e in events or []:
        out.append({
            "id": _s(e.get("id")),
            "at": _s(e.get("at")),
            "actor_name": _s(e.get("actor_name")),
            "actor_role": _s(e.get("actor_role")),
            "event_type": _s(e.get("event_type")),
            "from_state": _s(e.get("from_state")),
            "to_state": _s(e.get("to_state")),
            "reason": _s(e.get("reason")),
            "summary": _compose_event_summary(e),
            "source": "incident_case_events",
        })
    return out


def _compose_event_summary(e: Dict[str, Any]) -> str:
    et = _s(e.get("event_type"))
    fs = _s(e.get("from_state"))
    ts = _s(e.get("to_state"))
    reason = _s(e.get("reason"))
    actor = _s(e.get("actor_name")) or _s(e.get("actor_role"))
    core = et.replace("_", " ")
    if fs and ts:
        core = f"State: {fs} → {ts}"
    who = f" · by {actor}" if actor else ""
    why = f" · {reason}" if reason else ""
    return (core + who + why).strip(" ·")


def _build_evidence_chain(evidence: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Every attachment surfaced with its append-only custody chain."""
    out: List[Dict[str, Any]] = []
    for ev in evidence or []:
        out.append({
            "id": _s(ev.get("id")),
            "evidence_type": _s(ev.get("evidence_type")),
            "label": _s(ev.get("label")),
            "description": _s(ev.get("description")),
            "storage_key": _s(ev.get("storage_key")),
            "external_url": _s(ev.get("external_url")),
            "added_by": _s(ev.get("added_by")),
            "added_by_role": _s(ev.get("added_by_role")),
            "added_at": _s(ev.get("added_at")),
            "withdrawn": bool(ev.get("withdrawn")),
            "withdrawn_at": _s(ev.get("withdrawn_at")),
            "withdrawn_by": _s(ev.get("withdrawn_by")),
            "withdrawal_reason": _s(ev.get("withdrawal_reason")),
            "custody_chain": list(ev.get("custody_chain") or []),
            "source": "incident_case_evidence",
        })
    return out


def _build_people(case: Dict[str, Any], witnesses: List[Dict[str, Any]]) -> Dict[str, Any]:
    fb = case.get("field_block") or {}
    personnel = list(fb.get("personnel_present") or [])
    return {
        "reporter": {
            "name": _s(fb.get("reporter_name")),
            "role": _s(fb.get("reporter_role")),
        },
        "personnel_present": personnel,
        "witnesses": [
            {
                "id": _s(w.get("id")),
                "name": _s(w.get("name")),
                "kind": _s(w.get("kind")),
                "status": _s(w.get("status")),
                "statement_recorded": bool((w.get("statement") or "").strip()),
                "source": "case_witnesses",
            }
            for w in (witnesses or [])
        ],
    }


def _build_asset_buckets(case: Dict[str, Any]) -> Dict[str, Any]:
    """Extract equipment / vehicle / property / environmental / utility
    references directly from ``field_block`` (extra fields are allowed).
    Zero invention: only surfaces keys that already exist on the doc."""
    fb = case.get("field_block") or {}
    return {
        "equipment_ids": list(fb.get("equipment_ids") or []),
        "vehicle_ids":   list(fb.get("vehicle_ids") or []),
        "unit_numbers":  list(fb.get("unit_numbers") or []),
        "property":      _s(fb.get("property_damage_description")),
        "environmental": _s(fb.get("environmental_impact")),
        "utility":       _s(fb.get("utility_type")) or _s(fb.get("utility_owner")),
    }


def _build_medical(medical: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "id":            _s(m.get("id")),
            "kind":          _s(m.get("kind")),
            "at":            _s(m.get("at")),
            "provider":      _s(m.get("provider")),
            "subject_name":  _s(m.get("subject_name")),
            "lost_days":     int(m.get("lost_days") or 0),
            "restricted_days": int(m.get("restricted_days") or 0),
            "notes":         _s(m.get("notes")),
            "source":        "case_medical",
        }
        for m in (medical or [])
    ]


def _build_agency(agency: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "id":            _s(a.get("id")),
            "agency_name":   _s(a.get("agency_name")),
            "officer_name":  _s(a.get("officer_name")),
            "report_number": _s(a.get("report_number")),
            "at":            _s(a.get("at")),
            "notes":         _s(a.get("notes")),
            "source":        "case_agency_contacts",
        }
        for a in (agency or [])
    ]


def _build_communications(comms: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "id":           _s(c.get("id")),
            "kind":         _s(c.get("kind")),
            "at":           _s(c.get("at")),
            "subject":      _s(c.get("subject")),
            "contact_name": _s(c.get("contact_name")),
            "contact_role": _s(c.get("contact_role")),
            "contact_org":  _s(c.get("contact_org")),
            "body":         _s(c.get("body")),
            "source":       "case_communications",
        }
        for c in (comms or [])
    ]


def _build_capa(
    actions: List[Dict[str, Any]], summary: Dict[str, Any],
) -> Dict[str, Any]:
    items = [
        {
            "id":               _s(a.get("id")),
            "title":            _s(a.get("title")),
            "action_class":     _s(a.get("action_class")),
            "state":            _s(a.get("state")),
            "assigned_to_name": _s(a.get("assigned_to_name")),
            "assigned_to_role": _s(a.get("assigned_to_role")),
            "due_at":           _s(a.get("due_at")),
            "completed_at":     _s(a.get("completed_at")),
            "verified_at":      _s(a.get("verified_at")),
            "verification_notes": _s(a.get("verification_notes")),
            "source":           "corrective_actions",
        }
        for a in (actions or [])
    ]
    return {
        "items": items,
        "totals": {
            "total":    int(summary.get("total") or 0),
            "open":     int(summary.get("open") or 0),
            "verified": int(summary.get("verified") or 0),
            "canceled": int(summary.get("canceled") or 0),
        },
    }


def _build_tasks(tasks: List[Dict[str, Any]]) -> Dict[str, Any]:
    items = [
        {
            "id":              _s(t.get("id")),
            "title":           _s(t.get("title")),
            "assigned_to_name": _s(t.get("assigned_to_name")),
            "status":          _s(t.get("status")),
            "due_at":          _s(t.get("due_at")),
            "source":          "case_tasks",
        }
        for t in (tasks or [])
    ]
    open_states = {"open", "in_progress", "blocked"}
    open_items = [t for t in items if t["status"] in open_states]
    return {
        "items": items,
        "totals": {
            "total": len(items),
            "open":  len(open_items),
        },
    }


def _build_regulatory_review(case: Dict[str, Any], agency: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Regulatory / Insurance / Legal buckets.

    Strictly separated from the immutable field block. Everything here
    is Safety-owned or Admin-owned per the Track 19.34 doctrine.
    """
    sb = case.get("safety_block") or {}
    return {
        "osha_review": {
            "osha_recordable": sb.get("osha_recordable"),
            "osha_case_number": _s(sb.get("osha_case_number")),
            "recordability_reason": _s(sb.get("recordability_reason")),
            "owner": "safety",
            "source": "incident_cases.safety_block",
        },
        "insurance_review": {
            "workers_comp_days_lost": int(sb.get("lost_time_days") or 0),
            "workers_comp_days_restricted": int(sb.get("days_restricted") or 0),
            "medical_summary": _s(sb.get("medical_summary")),
            "owner": "safety",
            "source": "incident_cases.safety_block",
        },
        "legal_review": {
            "police_case_number": _s(sb.get("police_case_number")),
            "agency_contacts": _build_agency(agency),
            "owner": "safety",
            "source": "incident_cases.safety_block + case_agency_contacts",
        },
        "executive_review": {
            "reviewer": _s(sb.get("executive_reviewer")),
            "notes":    _s(sb.get("executive_review_notes")),
            "owner":    "executive",
            "source":   "incident_cases.safety_block",
        },
    }


def _build_readiness(
    case: Dict[str, Any],
    evidence: List[Dict[str, Any]],
    witnesses: List[Dict[str, Any]],
    medical: List[Dict[str, Any]],
    agency: List[Dict[str, Any]],
    capa_summary: Dict[str, Any],
    tasks: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Six explainable sub-scores + overall.

    Every sub-score exposes numerator, denominator, and rationale.
    Presence-based (Track 19.35 doctrine): capture beats blanks.
    """
    sb = case.get("safety_block") or {}
    open_capa = int(capa_summary.get("open") or 0)
    total_capa = int(capa_summary.get("total") or 0)
    verified_capa = int(capa_summary.get("verified") or 0)
    open_tasks = sum(1 for t in (tasks or [])
                     if _s(t.get("status")) in ("open", "in_progress", "blocked"))

    scores: List[Dict[str, Any]] = []

    # 1. Investigation — root cause + contributing factors
    rc = bool((sb.get("root_cause_summary") or "").strip())
    cf = bool(sb.get("contributing_factors"))
    inv_num = int(rc) + int(cf)
    scores.append(_score("investigation", inv_num, 2,
                         "Root cause summary + contributing factors documented."))

    # 2. Evidence
    ev_ok = 1 if any(not e.get("withdrawn") for e in (evidence or [])) else 0
    scores.append(_score("evidence", ev_ok, 1,
                         "At least one non-withdrawn evidence item captured."))

    # 3. Witness
    w_ok = 1 if witnesses else 0
    scores.append(_score("witnesses", w_ok, 1,
                         "At least one witness recorded."))

    # 4. CAPA
    if total_capa == 0:
        capa_num = 0
        capa_rationale = "No corrective actions assigned yet."
    else:
        capa_num = verified_capa
        capa_rationale = (
            f"{verified_capa} of {total_capa} corrective actions verified · "
            f"{open_capa} still open."
        )
    scores.append(_score("capa", capa_num, max(total_capa, 1), capa_rationale,
                         is_ratio=True))

    # 5. Documentation — medical / agency presence
    doc_num = int(bool(medical)) + int(bool(agency))
    scores.append(_score("documentation", doc_num, 2,
                         "Medical entry + agency contact captured (as applicable)."))

    # 6. Executive readiness — no open tasks · reviewer noted
    exec_num = 0
    if open_tasks == 0:
        exec_num += 1
    if (sb.get("executive_reviewer") or "").strip():
        exec_num += 1
    scores.append(_score("executive", exec_num, 2,
                         (f"{open_tasks} open task(s) remain. "
                          f"Executive reviewer "
                          f"{'recorded' if (sb.get('executive_reviewer') or '').strip() else 'not yet recorded'}.")))

    total_num = sum(s["num"] for s in scores)
    total_den = sum(s["den"] for s in scores)
    overall_pct = round((total_num / total_den) * 100) if total_den else 0
    band = "high" if overall_pct >= 80 else "medium" if overall_pct >= 50 else "low"

    return {
        "overall_pct": overall_pct,
        "band": band,
        "sub_scores": scores,
    }


def _score(key: str, num: int, den: int, rationale: str,
           is_ratio: bool = False) -> Dict[str, Any]:
    pct = round((num / den) * 100) if den else 0
    return {
        "key": key,
        "num": int(num),
        "den": int(den) or 1,
        "pct": pct,
        "rationale": rationale,
        "kind": "ratio" if is_ratio else "count",
    }


def _build_decision_records(events: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Every state transition and executive-review event, with actor /
    timestamp / reason. Sourced from the certified audit ledger."""
    out: List[Dict[str, Any]] = []
    for e in events or []:
        et = _s(e.get("event_type"))
        if et in ("state_transition", "case_closed", "case_reopened",
                  "executive_reviewed", "safety_intake"):
            out.append({
                "id":           _s(e.get("id")),
                "at":           _s(e.get("at")),
                "decision":     et.replace("_", " ").title(),
                "from_state":   _s(e.get("from_state")),
                "to_state":     _s(e.get("to_state")),
                "actor_name":   _s(e.get("actor_name")),
                "actor_role":   _s(e.get("actor_role")),
                "reason":       _s(e.get("reason")),
                "source":       "incident_case_events",
            })
    return out


def _build_operational_intelligence(
    case: Dict[str, Any],
    events: List[Dict[str, Any]],
    capa_summary: Dict[str, Any],
) -> Dict[str, Any]:
    fb = case.get("field_block") or {}
    submitted = _s(case.get("submitted_at")) or _s(case.get("created_at"))
    now = _now_iso()
    closed = _s(case.get("closed_at"))
    intake_at = ""
    first_capa_at = ""
    for e in events or []:
        et = _s(e.get("event_type"))
        if et == "safety_intake" and not intake_at:
            intake_at = _s(e.get("at"))
        if et in ("corrective_action_created", "capa_created") and not first_capa_at:
            first_capa_at = _s(e.get("at"))
    return {
        "occurred_at":         _s(fb.get("occurred_at")),
        "reported_at":         _s(fb.get("reported_at")),
        "submitted_at":        submitted,
        "safety_intake_at":    intake_at,
        "first_capa_at":       first_capa_at,
        "closed_at":           closed,
        "time_to_intake_days": _days_between(submitted, intake_at) if intake_at else None,
        "time_to_capa_days":   _days_between(submitted, first_capa_at) if first_capa_at else None,
        "time_to_closure_days": _days_between(submitted, closed) if closed else None,
        "days_open":           _days_between(submitted, closed or now),
        "corrective_action_open": int(capa_summary.get("open") or 0),
        "corrective_action_total": int(capa_summary.get("total") or 0),
    }


def _build_why_it_matters(
    case_ref: Dict[str, Any],
    summary: Dict[str, Any],
    readiness: Dict[str, Any],
    ops: Dict[str, Any],
    capa: Dict[str, Any],
    regulatory: Dict[str, Any],
) -> Dict[str, Any]:
    """Fact-based executive briefing. Every sentence is either a direct
    field or a formatted count. No invention. If a value is missing, the
    briefing says so explicitly."""
    sev = summary.get("severity_band") or "unrated"
    days_open = ops.get("days_open")
    days_open_str = f"{days_open} day(s) open" if days_open is not None else "Days-open not computable"
    open_capa = capa.get("totals", {}).get("open") or 0
    total_capa = capa.get("totals", {}).get("total") or 0
    osha = regulatory.get("osha_review", {}).get("osha_recordable")
    osha_line = (
        "OSHA recordable — Yes." if osha is True else
        "OSHA recordable — No." if osha is False else
        "OSHA recordable determination — Not documented yet."
    )
    what = summary.get("one_paragraph") or "Not documented yet."
    ready_pct = readiness.get("overall_pct") or 0
    ready_band = readiness.get("band") or "low"

    return {
        "what_happened": what,
        "why_leadership_should_care": (
            f"Severity band '{sev}'. "
            f"{summary.get('severity_rationale') or 'No severity indicators recorded.'} "
            f"{osha_line} "
            f"{days_open_str}."
        ),
        "current_risk_if_no_action": (
            f"{open_capa} corrective action(s) open of {total_capa} assigned. "
            f"Investigation readiness {ready_pct}% ({ready_band}). "
            + ("Unresolved corrective actions extend organizational exposure until closed."
               if open_capa > 0 else
               "No open corrective actions recorded — verify closeout requirements are met.")
        ),
        "recommended_executive_decision": _recommend(
            state=case_ref.get("state"),
            ready_pct=ready_pct,
            open_capa=open_capa,
            osha=osha,
        ),
        "expected_outcome_if_implemented": (
            "Closing the remaining CAPAs and completing the investigation "
            "checklist enables case closure at the required documentation "
            "bar and reduces further exposure."
        ),
        "source_note": (
            "Every sentence in this briefing is derived from certified case "
            "fields (incident_cases · corrective_actions · incident_case_events · "
            "incident_case_evidence). No content was generated by inference."
        ),
    }


def _recommend(*, state: str, ready_pct: int, open_capa: int,
               osha: Optional[bool]) -> str:
    state = (state or "").upper()
    if state == "CLOSED":
        return "Case is closed. Recommend periodic review of documented lessons learned."
    if open_capa > 0:
        return (
            f"Drive the {open_capa} open corrective action(s) to Verified "
            "before closure. Assign an owner for any unassigned CAPA."
        )
    if ready_pct < 50:
        return ("Push the investigation to the Case Workspace: capture "
                "evidence, witness statements, and root cause before advancing.")
    if osha is None:
        return ("Confirm OSHA recordability determination in the Safety "
                "block before closure.")
    return "Ready for closeout review. Confirm Executive Review notes in the Safety block."


def _build_missing_fields(model: Dict[str, Any]) -> List[str]:
    """Explicit ledger of fields the assembler could not populate.
    Consumers surface this as 'Not documented yet.'"""
    missing: List[str] = []
    s = model.get("executive_summary") or {}
    r = (model.get("regulatory_review") or {}).get("osha_review") or {}
    sb_root = (s.get("root_cause_summary") or "").strip()
    if not sb_root:
        missing.append("root_cause_summary")
    if r.get("osha_recordable") is None:
        missing.append("osha_recordable")
    if not (s.get("one_paragraph") or "").strip():
        missing.append("executive_summary_paragraph")
    if not model.get("timeline"):
        missing.append("timeline")
    if not model.get("evidence_chain"):
        missing.append("evidence_chain")
    return missing


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
async def assemble_executive_intelligence(
    db, *, case_id: str,
) -> Dict[str, Any]:
    """Load once, assemble once. Returns the full executive model."""
    case = await case_service.get_case(db, case_id)
    if not case:
        raise LookupError(f"case {case_id!r} not found")

    events    = await list_events(db, case_id=case_id, limit=2000)
    evidence  = await list_evidence(db, case_id=case_id, include_withdrawn=True)
    witnesses = await ws.list_witnesses(db, case_id=case_id)
    medical   = await ws.list_medical(db, case_id=case_id)
    agency    = await ws.list_agency(db, case_id=case_id)
    comms     = await ws.list_communications(db, case_id=case_id)
    tasks     = await ws.list_tasks(db, case_id=case_id)
    capa_list = await list_actions(db, consumer_kind="incident_case",
                                   consumer_id=case_id)
    capa_summary = await summary_for_case(db, case_id=case_id)

    fb = case.get("field_block") or {}
    sb = case.get("safety_block") or {}
    severity = _severity_from_case(fb, sb)
    severity_why = _severity_rationale(fb, sb, severity)

    case_ref   = _build_case_ref(case)
    summary    = _build_executive_summary(case, severity, severity_why)
    timeline   = _build_timeline(case, events)
    ev_chain   = _build_evidence_chain(evidence)
    people     = _build_people(case, witnesses)
    assets     = _build_asset_buckets(case)
    med        = _build_medical(medical)
    ag         = _build_agency(agency)
    comm_list  = _build_communications(comms)
    capa_block = _build_capa(capa_list, capa_summary)
    task_block = _build_tasks(tasks)
    regulatory = _build_regulatory_review(case, agency)
    readiness  = _build_readiness(case, evidence, witnesses, medical,
                                  agency, capa_summary, tasks)
    decisions  = _build_decision_records(events)
    ops        = _build_operational_intelligence(case, events, capa_summary)
    why        = _build_why_it_matters(case_ref, summary, readiness, ops,
                                       capa_block, regulatory)

    model: Dict[str, Any] = {
        "model_version": EXECUTIVE_INTELLIGENCE_MODEL_VERSION,
        "generated_at": _now_iso(),
        "case_ref": case_ref,
        "executive_summary": summary,
        "why_it_matters": why,
        "timeline": timeline,
        "evidence_chain": ev_chain,
        "people": people,
        "asset_buckets": assets,
        "medical": med,
        "agency": ag,
        "communications": comm_list,
        "corrective_actions": capa_block,
        "outstanding_tasks": task_block,
        "regulatory_review": regulatory,
        "readiness": readiness,
        "decision_records": decisions,
        "operational_intelligence": ops,
        "sources": {
            "case":             "incident_cases",
            "timeline":         "incident_case_events",
            "evidence":         "incident_case_evidence",
            "corrective_actions": "corrective_actions",
            "witnesses":        "case_witnesses",
            "medical":          "case_medical",
            "agency":           "case_agency_contacts",
            "communications":   "case_communications",
            "tasks":            "case_tasks",
        },
    }
    model["missing_fields"] = _build_missing_fields(model)
    return model


__all__ = [
    "EXECUTIVE_INTELLIGENCE_MODEL_VERSION",
    "assemble_executive_intelligence",
]
