"""Track 19.37 · Passive Incident-Presence Scoring.

Deterministic, read-only, attention-only signal layer.

NOT auto-classification. NOT OSHA determination. NOT legal decisioning.
NOT root-cause automation. NOT fault or blame. This module surfaces
attention indicators that guide a Safety Manager toward cases needing
review. Every decision (OSHA recordability, root cause, discipline,
liability, closure) stays with humans.

Design rules
------------
- Pure function of inputs. No I/O. No mutation. No LLM. No inference.
- Every signal exposes its ``source_fields``, its ``rationale``, and its
  ``recommended_review_owner``.
- When a required input is missing, it is emitted into ``missing_inputs``
  and the signal's score contribution is 0.0 with a plain-language
  rationale.
- The output must be safe for the Executive Intelligence Model — it
  never introduces forbidden decision vocabulary
  (``osha_recordable`` · ``root_cause_conclusion`` · ``preventability`` ·
  ``liable`` · ``discipline`` · ``fault`` · ``blame``).

Signal set (v1 · 11 signals)
----------------------------
- possible_injury_presence
- possible_utility_involvement
- possible_vehicle_equipment_involvement
- possible_environmental_involvement
- possible_property_damage
- possible_public_exposure
- possible_police_agency_involvement
- possible_open_evidence_gap
- possible_delayed_closeout
- possible_overdue_capa
- possible_executive_review_needed
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


PRESENCE_SCORE_MODEL_VERSION = "1.0.0"

NO_AUTO_DECISION_NOTICE = (
    "This score is an attention signal only. "
    "Safety owns investigation and classification. "
    "The platform routes, records, reports, protects, and surfaces risk "
    "signals — it never decides OSHA recordability, root cause, liability, "
    "fault, or discipline."
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _now() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(v: Optional[str]) -> Optional[datetime]:
    if not v:
        return None
    try:
        return datetime.fromisoformat(v.replace("Z", "+00:00"))
    except Exception:
        return None


def _days_since(iso: Optional[str]) -> Optional[int]:
    d = _parse_iso(iso)
    if not d:
        return None
    return max(0, int((_now() - d).total_seconds() // 86400))


def _has(v: Any) -> bool:
    """A field is 'present' if it is a non-empty string, non-empty list, non-empty
    dict, a positive int/float, or the literal True. False/0/None/'' are absent."""
    if v is True:
        return True
    if isinstance(v, str):
        return v.strip() != ""
    if isinstance(v, (list, dict)):
        return len(v) > 0
    if isinstance(v, (int, float)):
        return v > 0
    return False


def _signal(
    key: str,
    label: str,
    score: float,
    confidence: str,
    rationale: str,
    source_fields: List[str],
    recommended_review_owner: str,
) -> Dict[str, Any]:
    return {
        "signal_key": key,
        "label": label,
        "score": round(max(0.0, min(1.0, float(score))), 3),
        "confidence": confidence,
        "rationale": rationale,
        "source_fields": list(source_fields),
        "recommended_review_owner": recommended_review_owner,
    }


# ---------------------------------------------------------------------------
# Individual signal rules (all deterministic)
# ---------------------------------------------------------------------------
def _signal_injury(fb: Dict[str, Any], medical: List[Dict[str, Any]]) -> Dict[str, Any]:
    keys = [
        "injured_person", "injured_person_name", "injury_description",
        "injury_body_part", "injury_type", "first_aid_given",
        "ambulance_called", "medical_treatment", "medical_needed",
    ]
    hit_keys = [k for k in keys if _has(fb.get(k))]
    has_medical = len(medical or []) > 0
    itype = (fb.get("incident_type") or "").lower()
    itype_hit = itype in {"employee_injury", "near_miss_injury", "workplace_violence"}

    present = bool(hit_keys or has_medical or itype_hit)
    score = 0.85 if present else 0.0
    conf = "high" if (hit_keys and has_medical) else "medium" if present else "high"
    parts: List[str] = []
    if hit_keys:
        parts.append(f"Field intake mentions {len(hit_keys)} injury-related field(s): "
                     + ", ".join(hit_keys) + ".")
    if has_medical:
        parts.append(f"{len(medical)} medical entry(ies) recorded on the case.")
    if itype_hit:
        parts.append(f"Incident type '{itype}' typically involves a person.")
    if not parts:
        parts.append("No injury-related field or medical entry detected.")

    return _signal(
        key="possible_injury_presence",
        label="Possible injury presence",
        score=score,
        confidence=conf,
        rationale=" ".join(parts),
        source_fields=[f"field_block.{k}" for k in hit_keys]
                      + (["case_medical[]"] if has_medical else [])
                      + (["field_block.incident_type"] if itype_hit else []),
        recommended_review_owner="safety",
    )


def _signal_utility(fb: Dict[str, Any]) -> Dict[str, Any]:
    keys = [
        "utility_type", "utility_owner", "utility_marked",
        "ticket_number", "one_call_ticket", "eight_one_one_ticket",
        "utility_damage_description",
    ]
    hit = [k for k in keys if _has(fb.get(k))]
    itype = (fb.get("incident_type") or "").lower()
    itype_hit = itype in {"utility_strike"}
    score = 0.9 if itype_hit else 0.7 if hit else 0.0
    return _signal(
        key="possible_utility_involvement",
        label="Possible utility involvement",
        score=score,
        confidence="high" if itype_hit else "medium" if hit else "high",
        rationale=(
            (f"Incident type '{itype}' involves utility infrastructure. "
             if itype_hit else "")
            + (f"Field intake mentions {len(hit)} utility field(s): "
               f"{', '.join(hit)}."
               if hit else
               ("No utility field or utility incident type detected."
                if not itype_hit else ""))
        ).strip(),
        source_fields=[f"field_block.{k}" for k in hit]
                      + (["field_block.incident_type"] if itype_hit else []),
        recommended_review_owner="safety",
    )


def _signal_vehicle_equipment(fb: Dict[str, Any]) -> Dict[str, Any]:
    veh_keys = ["vehicle_ids", "unit_numbers", "vehicle_description",
                "driver_name", "driver_role", "vehicle_operator"]
    equ_keys = ["equipment_ids", "equipment_description", "operator_name",
                "equipment_operator"]
    hit_v = [k for k in veh_keys if _has(fb.get(k))]
    hit_e = [k for k in equ_keys if _has(fb.get(k))]
    itype = (fb.get("incident_type") or "").lower()
    itype_hit = itype in {"vehicle_accident", "equipment_accident"}
    present = bool(hit_v or hit_e or itype_hit)
    score = 0.85 if itype_hit else (0.7 if (hit_v or hit_e) else 0.0)
    parts: List[str] = []
    if itype_hit:
        parts.append(f"Incident type '{itype}' involves motorized asset.")
    if hit_v:
        parts.append(f"Vehicle field(s) present: {', '.join(hit_v)}.")
    if hit_e:
        parts.append(f"Equipment field(s) present: {', '.join(hit_e)}.")
    if not parts:
        parts.append("No vehicle or equipment field detected.")
    return _signal(
        key="possible_vehicle_equipment_involvement",
        label="Possible vehicle or equipment involvement",
        score=score,
        confidence="high" if itype_hit else "medium" if present else "high",
        rationale=" ".join(parts),
        source_fields=[f"field_block.{k}" for k in hit_v + hit_e]
                      + (["field_block.incident_type"] if itype_hit else []),
        recommended_review_owner="safety",
    )


def _signal_environmental(fb: Dict[str, Any]) -> Dict[str, Any]:
    keys = ["environmental_impact", "spill_reported", "material_released",
            "material_type", "gallons_released"]
    hit = [k for k in keys if _has(fb.get(k))]
    itype = (fb.get("incident_type") or "").lower()
    itype_hit = itype in {"environmental", "spill", "release"}
    score = 0.85 if itype_hit else 0.65 if hit else 0.0
    return _signal(
        key="possible_environmental_involvement",
        label="Possible environmental involvement",
        score=score,
        confidence="high" if itype_hit else "medium" if hit else "high",
        rationale=(
            (f"Incident type '{itype}' is an environmental event. "
             if itype_hit else "")
            + (f"Field intake mentions environmental field(s): {', '.join(hit)}."
               if hit else "No environmental field or incident type detected.")
        ).strip(),
        source_fields=[f"field_block.{k}" for k in hit]
                      + (["field_block.incident_type"] if itype_hit else []),
        recommended_review_owner="safety",
    )


def _signal_property_damage(fb: Dict[str, Any]) -> Dict[str, Any]:
    keys = ["property_damage_description", "property_owner",
            "estimated_property_damage_usd"]
    hit = [k for k in keys if _has(fb.get(k))]
    itype = (fb.get("incident_type") or "").lower()
    itype_hit = itype in {"property_damage"}
    score = 0.75 if itype_hit else 0.6 if hit else 0.0
    return _signal(
        key="possible_property_damage",
        label="Possible property damage",
        score=score,
        confidence="high" if hit or itype_hit else "high",
        rationale=(
            (f"Incident type '{itype}' involves property. "
             if itype_hit else "")
            + (f"Field intake mentions property field(s): {', '.join(hit)}."
               if hit else "No property-damage field detected.")
        ).strip(),
        source_fields=[f"field_block.{k}" for k in hit]
                      + (["field_block.incident_type"] if itype_hit else []),
        recommended_review_owner="safety",
    )


def _signal_public_exposure(fb: Dict[str, Any]) -> Dict[str, Any]:
    keys = ["public_involved", "public_injuries", "public_witnesses",
            "third_party_present", "third_party_name"]
    hit = [k for k in keys if _has(fb.get(k))]
    present = bool(hit)
    score = 0.7 if present else 0.0
    return _signal(
        key="possible_public_exposure",
        label="Possible public exposure",
        score=score,
        confidence="medium" if present else "high",
        rationale=(
            f"Field intake mentions public/third-party field(s): {', '.join(hit)}."
            if hit else "No public or third-party involvement field detected."
        ),
        source_fields=[f"field_block.{k}" for k in hit],
        recommended_review_owner="safety",
    )


def _signal_police_agency(fb: Dict[str, Any], agency: List[Dict[str, Any]]) -> Dict[str, Any]:
    fb_keys = ["police_called", "police_department", "police_report_number",
               "agency_notified", "agency_name"]
    hit = [k for k in fb_keys if _has(fb.get(k))]
    ag_count = len(agency or [])
    score = 0.85 if ag_count else 0.6 if hit else 0.0
    return _signal(
        key="possible_police_agency_involvement",
        label="Possible police or agency involvement",
        score=score,
        confidence="high" if ag_count else "medium" if hit else "high",
        rationale=(
            (f"{ag_count} agency contact(s) recorded on the case. "
             if ag_count else "")
            + (f"Field intake mentions agency field(s): {', '.join(hit)}."
               if hit else
               ("No agency contact and no police/agency field detected."
                if not ag_count else ""))
        ).strip(),
        source_fields=[f"field_block.{k}" for k in hit]
                      + (["case_agency_contacts[]"] if ag_count else []),
        recommended_review_owner="safety",
    )


def _signal_evidence_gap(
    fb: Dict[str, Any], evidence: List[Dict[str, Any]],
    injury_present: bool, utility_present: bool,
    vehicle_equipment_present: bool, environmental_present: bool,
) -> Dict[str, Any]:
    active = [e for e in (evidence or []) if not e.get("withdrawn")]
    ev_count = len(active)
    warrants = injury_present or utility_present or vehicle_equipment_present or environmental_present
    is_gap = warrants and ev_count == 0
    return _signal(
        key="possible_open_evidence_gap",
        label="Possible open evidence gap",
        score=0.9 if is_gap else 0.0,
        confidence="high",
        rationale=(
            (f"{ev_count} active evidence item(s) captured. "
             if ev_count else "No active evidence captured. ")
            + ("Case has attention-worthy signals — evidence may be needed."
               if is_gap else
               "Signals present or evidence already captured; no gap detected.")
        ),
        source_fields=["incident_case_evidence[]",
                       "field_block.incident_type"],
        recommended_review_owner="safety",
    )


def _signal_delayed_closeout(case: Dict[str, Any]) -> Dict[str, Any]:
    state = (case.get("state") or "").upper()
    submitted = case.get("submitted_at") or case.get("created_at")
    days = _days_since(submitted)
    is_closed = state in {"CLOSED"}
    delayed = (not is_closed) and (days is not None) and days > 30
    if delayed:
        score = min(1.0, 0.5 + (days - 30) / 60.0)
    else:
        score = 0.0
    return _signal(
        key="possible_delayed_closeout",
        label="Possible delayed closeout",
        score=score,
        confidence="high",
        rationale=(
            (f"Case has been open {days} day(s) and is not CLOSED."
             if delayed else
             ("Case is CLOSED." if is_closed else
              (f"Case is {days} day(s) old; not yet at 30-day threshold."
               if days is not None else "Submission date is missing.")))
        ),
        source_fields=["incident_cases.state", "incident_cases.submitted_at",
                       "incident_cases.created_at"],
        recommended_review_owner="safety",
    )


def _signal_overdue_capa(capa: List[Dict[str, Any]]) -> Dict[str, Any]:
    now = _now()
    overdue = 0
    for a in capa or []:
        state = (a.get("state") or "").upper()
        due = _parse_iso(a.get("due_at"))
        if due and due < now and state in {"OPEN", "IN_PROGRESS", ""}:
            overdue += 1
    return _signal(
        key="possible_overdue_capa",
        label="Possible overdue corrective actions",
        score=min(1.0, 0.5 + 0.1 * overdue) if overdue else 0.0,
        confidence="high",
        rationale=(
            f"{overdue} corrective action(s) past their due date and not verified."
            if overdue else
            "No corrective action is past due, or none has been assigned."
        ),
        source_fields=["corrective_actions.due_at", "corrective_actions.state"],
        recommended_review_owner="safety",
    )


def _signal_executive_review_needed(case: Dict[str, Any]) -> Dict[str, Any]:
    state = (case.get("state") or "").upper()
    sb = case.get("safety_block") or {}
    ready_states = {"READY_FOR_REVIEW", "APPROVED", "PENDING_EXEC_REVIEW"}
    reviewer_present = bool((sb.get("executive_reviewer") or "").strip())
    needed = (state in ready_states) and (not reviewer_present)
    return _signal(
        key="possible_executive_review_needed",
        label="Possible executive review needed",
        score=0.8 if needed else 0.0,
        confidence="high",
        rationale=(
            (f"Case state '{state}' typically expects executive review, and "
             "no executive reviewer is recorded on the safety block."
             if needed else
             (f"Executive reviewer '{sb.get('executive_reviewer')}' recorded."
              if reviewer_present else
              f"Case state '{state}' does not require executive review yet."))
        ),
        source_fields=["incident_cases.state",
                       "incident_cases.safety_block.executive_reviewer"],
        recommended_review_owner="executive",
    )


def _detect_missing_inputs(
    case: Dict[str, Any], evidence: List[Dict[str, Any]],
    capa: List[Dict[str, Any]], medical: List[Dict[str, Any]],
    agency: List[Dict[str, Any]], tasks: List[Dict[str, Any]],
) -> List[str]:
    missing: List[str] = []
    if not case:
        missing.append("incident_cases_document")
        return missing
    if not (case.get("submitted_at") or case.get("created_at")):
        missing.append("incident_cases.submitted_at")
    if not (case.get("state") or "").strip():
        missing.append("incident_cases.state")
    fb = case.get("field_block") or {}
    if not (fb.get("incident_type") or "").strip():
        missing.append("field_block.incident_type")
    if evidence is None:
        missing.append("incident_case_evidence[]")
    if capa is None:
        missing.append("corrective_actions[]")
    if medical is None:
        missing.append("case_medical[]")
    if agency is None:
        missing.append("case_agency_contacts[]")
    if tasks is None:
        missing.append("case_tasks[]")
    return missing


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------
def compute_presence_score(
    case: Dict[str, Any],
    *,
    evidence: Optional[List[Dict[str, Any]]] = None,
    capa: Optional[List[Dict[str, Any]]] = None,
    medical: Optional[List[Dict[str, Any]]] = None,
    agency: Optional[List[Dict[str, Any]]] = None,
    tasks: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """Pure deterministic scorer. Zero I/O. Zero mutation."""
    fb = (case or {}).get("field_block") or {}
    evidence = list(evidence or [])
    capa = list(capa or [])
    medical = list(medical or [])
    agency = list(agency or [])
    tasks = list(tasks or [])

    injury = _signal_injury(fb, medical)
    utility = _signal_utility(fb)
    vehequ = _signal_vehicle_equipment(fb)
    envn = _signal_environmental(fb)
    prop = _signal_property_damage(fb)
    pub = _signal_public_exposure(fb)
    police = _signal_police_agency(fb, agency)
    evgap = _signal_evidence_gap(
        fb, evidence,
        injury_present=injury["score"] > 0,
        utility_present=utility["score"] > 0,
        vehicle_equipment_present=vehequ["score"] > 0,
        environmental_present=envn["score"] > 0,
    )
    delayed = _signal_delayed_closeout(case or {})
    capa_overdue = _signal_overdue_capa(capa)
    exec_review = _signal_executive_review_needed(case or {})

    signals = [injury, utility, vehequ, envn, prop, pub, police,
               evgap, delayed, capa_overdue, exec_review]

    # Overall attention score is the mean signal score, scaled 0-100.
    if signals:
        overall = round(100.0 * sum(s["score"] for s in signals) / len(signals))
    else:
        overall = 0
    level = "high" if overall >= 60 else "medium" if overall >= 30 else "low"

    return {
        "case_id": (case or {}).get("id") or "",
        "model_version": PRESENCE_SCORE_MODEL_VERSION,
        "generated_at": _now().isoformat(),
        "overall_attention_score": overall,
        "attention_level": level,
        "signals": signals,
        "missing_inputs": _detect_missing_inputs(case, evidence, capa,
                                                 medical, agency, tasks),
        "no_auto_decision_notice": NO_AUTO_DECISION_NOTICE,
    }


__all__ = [
    "PRESENCE_SCORE_MODEL_VERSION",
    "NO_AUTO_DECISION_NOTICE",
    "compute_presence_score",
]
