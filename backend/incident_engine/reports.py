"""Track 19.16 · Phase E · Report Intelligence Engine.

ONE report engine · MANY declarative report definitions.

Every report is a list of Sections. A Section names a source
(``case``, ``timeline``, ``evidence``, ``witnesses``, ``medical``,
``agency``, ``communications``, ``corrective_actions``, ``linked``,
``root_cause``, ``field_block_extras``) plus a role-visibility rule.

Reports NEVER own data. They project the case + its satellites into
audience-appropriate shapes. Zero-Drift preserved.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from . import case_service, corrective_actions as ca_engine, evidence as ev_engine
from . import workspace as ws
from .intelligence import _sla_status, compute_executive_brief


# Sections available to a report definition.
SECTION_HEADER          = "header"
SECTION_COVER           = "cover"
SECTION_SUMMARY         = "summary"
SECTION_TIMELINE        = "timeline"
SECTION_EVIDENCE        = "evidence"
SECTION_PHOTOGRAPHS     = "photographs"
SECTION_WITNESSES       = "witnesses"
SECTION_MEDICAL         = "medical"
SECTION_AGENCY          = "agency"
SECTION_COMMUNICATIONS  = "communications"
SECTION_CAPA            = "corrective_actions"
SECTION_ROOT_CAUSE      = "root_cause"
SECTION_VEHICLE         = "vehicle"
SECTION_UTILITY         = "utility"
SECTION_INJURY          = "injury"
SECTION_LINKED          = "linked"
SECTION_EXEC_SUMMARY    = "executive_summary"
SECTION_LESSONS_LEARNED = "lessons_learned"

# Nine declarative reports. Ordering IS the report layout.
# TRACK 19.17 · PDF Excellence — every report opens with a professional
# cover page, and photographs render inline with captions (not just as
# an evidence-index table). Empty sections are suppressed by the
# renderer so PDFs never carry blank blocks.
REPORT_DEFINITIONS: Dict[str, Dict[str, Any]] = {
    "executive_summary": {
        "title": "Executive Summary",
        "audience": "executive",
        "sections": [
            SECTION_COVER, SECTION_HEADER, SECTION_EXEC_SUMMARY, SECTION_SUMMARY,
            SECTION_PHOTOGRAPHS, SECTION_ROOT_CAUSE,
            SECTION_CAPA, SECTION_LESSONS_LEARNED,
        ],
        "medical_privacy": "aggregate_only",
        "internal_notes": False,
    },
    "insurance_package": {
        "title": "Insurance Package",
        "audience": "insurer",
        "sections": [
            SECTION_COVER, SECTION_HEADER, SECTION_SUMMARY, SECTION_VEHICLE,
            SECTION_INJURY, SECTION_TIMELINE, SECTION_WITNESSES,
            SECTION_PHOTOGRAPHS, SECTION_EVIDENCE, SECTION_AGENCY,
            SECTION_COMMUNICATIONS, SECTION_MEDICAL,
        ],
        "medical_privacy": "authorized_only",
        "internal_notes": False,
    },
    "witness_package": {
        "title": "Witness Package",
        "audience": "safety",
        "sections": [
            SECTION_COVER, SECTION_HEADER, SECTION_SUMMARY,
            SECTION_WITNESSES, SECTION_TIMELINE, SECTION_PHOTOGRAPHS,
        ],
        "medical_privacy": "hidden",
        "internal_notes": False,
    },
    "vehicle_package": {
        "title": "Vehicle Package",
        "audience": "fleet",
        "sections": [
            SECTION_COVER, SECTION_HEADER, SECTION_VEHICLE,
            SECTION_TIMELINE, SECTION_PHOTOGRAPHS, SECTION_EVIDENCE,
            SECTION_AGENCY, SECTION_LINKED,
        ],
        "medical_privacy": "hidden",
        "internal_notes": False,
    },
    "utility_strike_package": {
        "title": "Utility Strike Package",
        "audience": "utility_coordinator",
        "sections": [
            SECTION_COVER, SECTION_HEADER, SECTION_UTILITY,
            SECTION_TIMELINE, SECTION_PHOTOGRAPHS, SECTION_EVIDENCE,
            SECTION_COMMUNICATIONS, SECTION_AGENCY,
        ],
        "medical_privacy": "hidden",
        "internal_notes": False,
    },
    "employee_injury_package": {
        "title": "Employee Injury Package",
        "audience": "hr_safety",
        "sections": [
            SECTION_COVER, SECTION_HEADER, SECTION_INJURY, SECTION_MEDICAL,
            SECTION_TIMELINE, SECTION_WITNESSES, SECTION_PHOTOGRAPHS,
            SECTION_EVIDENCE, SECTION_ROOT_CAUSE, SECTION_CAPA,
        ],
        "medical_privacy": "full",
        "internal_notes": False,
    },
    "customer_incident_report": {
        "title": "Customer Incident Report",
        "audience": "customer",
        "sections": [
            SECTION_COVER, SECTION_HEADER, SECTION_SUMMARY,
            SECTION_TIMELINE, SECTION_CAPA,
        ],
        # No investigation notes, no credibility, no executive comments,
        # no photographs (customer-facing keeps things terse).
        "medical_privacy": "hidden",
        "internal_notes": False,
        "customer_facing": True,
    },
    "management_review": {
        "title": "Management Review",
        "audience": "management",
        "sections": [
            SECTION_COVER, SECTION_HEADER, SECTION_EXEC_SUMMARY,
            SECTION_SUMMARY, SECTION_TIMELINE, SECTION_PHOTOGRAPHS,
            SECTION_ROOT_CAUSE, SECTION_CAPA, SECTION_COMMUNICATIONS,
            SECTION_LINKED, SECTION_LESSONS_LEARNED,
        ],
        "medical_privacy": "aggregate_only",
        "internal_notes": True,
    },
    "osha_investigation_package": {
        "title": "OSHA Investigation Package",
        "audience": "compliance",
        "sections": [
            SECTION_COVER, SECTION_HEADER, SECTION_SUMMARY, SECTION_INJURY,
            SECTION_MEDICAL, SECTION_TIMELINE, SECTION_WITNESSES,
            SECTION_PHOTOGRAPHS, SECTION_EVIDENCE, SECTION_ROOT_CAUSE,
            SECTION_CAPA, SECTION_COMMUNICATIONS,
        ],
        "medical_privacy": "authorized_only",
        "internal_notes": False,
    },
}


def report_types() -> List[str]:
    return list(REPORT_DEFINITIONS.keys())


async def _render_section(db, *, case: Dict[str, Any], code: str,
                          privacy: str, allow_internal: bool,
                          customer_facing: bool) -> Dict[str, Any]:
    fb = case.get("field_block") or {}
    sb = case.get("safety_block") or {}
    case_id = case["id"]

    if code == SECTION_HEADER:
        return {
            "code": code,
            "title": "Header",
            "data": {
                "case_number":    case.get("case_number") or "",
                "state":          case.get("state"),
                "incident_type":  fb.get("incident_type") or "",
                "location_label": fb.get("location_label") or "",
                "job_number":     fb.get("job_number") or "",
                "occurred_at":    fb.get("occurred_at") or "",
                "reported_at":    fb.get("reported_at") or "",
                "submitted_at":   case.get("submitted_at") or "",
                "reporter_name":  fb.get("reporter_name") or "",
                "sla_status":     _sla_status(case),
            },
        }

    if code == SECTION_COVER:
        # TRACK 19.17 · Professional cover page. Loaded from field_block
        # + the __project_context__ sidecar (populated by the picker so
        # PDFs read like a professionally prepared investigation
        # package, not exported application data).
        ctx = fb.get("__project_context__") or {}
        return {"code": code, "title": "Cover", "data": {
            "case_number":     case.get("case_number") or "",
            "case_id":         case.get("id"),
            "incident_type":   fb.get("incident_type") or "",
            "occurred_at_date": fb.get("occurred_at_date") or "",
            "occurred_at_time": fb.get("occurred_at_time") or "",
            "location_label":  fb.get("location_label") or "",
            "job_number":      fb.get("job_number") or "",
            "project_name":    ctx.get("project_name") or "",
            "client":          ctx.get("client") or "",
            "project_manager": ctx.get("project_manager") or "",
            "superintendent":  ctx.get("superintendent") or "",
            "reporter_name":   fb.get("reporter_name") or "",
            "state":           case.get("state"),
        }}

    if code == SECTION_PHOTOGRAPHS:
        # Inline images with captions + timestamps. Field-block photos
        # carry data_url + captured_at + gps; evidence-attached photos
        # (via /evidence) do not carry bytes here (reference-only).
        photos = fb.get("photos") or []
        gallery = []
        for i, p in enumerate(photos):
            gallery.append({
                "index":       i + 1,
                "data_url":    p.get("data_url") or "",
                "name":        p.get("name") or "",
                "caption":     p.get("caption") or "",
                "captured_at": p.get("captured_at") or "",
                "gps":         p.get("gps") or None,
            })
        return {"code": code, "title": "Photographs", "data": gallery}

    if code == SECTION_SUMMARY:
        return {"code": code, "title": "Summary", "data": {
            "observed_conditions": fb.get("observed_conditions") or "",
            "immediate_actions":   fb.get("immediate_actions") or "",
        }}

    if code == SECTION_EXEC_SUMMARY:
        health = await ws.compute_case_health(db, case_id=case_id, case_doc=case)
        return {"code": code, "title": "Executive Summary", "data": {
            "state": case.get("state"),
            "readiness_pct": health.get("completeness_pct", 0),
            "blockers": health.get("blockers", []),
            "sla_status": _sla_status(case),
            "root_cause_present": bool((sb.get("root_cause_summary") or "").strip()),
            "osha_recordable": sb.get("osha_recordable"),
        }}

    if code == SECTION_TIMELINE:
        from .events import list_events
        events = await list_events(db, case_id=case_id)
        # For customer-facing reports strip internal event types.
        if customer_facing:
            allowed = {"case.created", "case.field_submitted", "case.state_changed",
                       "case.closed", "corrective_action.verified"}
            events = [e for e in events if e["event_type"] in allowed]
        return {"code": code, "title": "Timeline", "data": events}

    if code == SECTION_EVIDENCE:
        items = await ev_engine.list_evidence(db, case_id=case_id, include_withdrawn=False)
        # Reference-only; never embed the file itself.
        idx = [{
            "id": i["id"], "evidence_type": i["evidence_type"],
            "label": i.get("label") or "", "added_at": i.get("added_at") or "",
            "chain_of_custody_length": len(i.get("custody_chain") or []),
        } for i in items]
        return {"code": code, "title": "Evidence Index", "data": idx}

    if code == SECTION_WITNESSES:
        rows = await ws.list_witnesses(db, case_id=case_id)
        # Strip safety-only credibility notes for non-safety audiences.
        if not allow_internal:
            rows = [{**w, "credibility_notes": ""} for w in rows]
        return {"code": code, "title": "Witnesses", "data": rows}

    if code == SECTION_MEDICAL:
        if privacy == "hidden":
            return {"code": code, "title": "Medical", "data": {"redacted": True}}
        rows = await ws.list_medical(db, case_id=case_id)
        if privacy == "aggregate_only":
            total_lost = sum(int(m.get("lost_days") or 0) for m in rows)
            return {"code": code, "title": "Medical (aggregate)", "data": {
                "entries_count": len(rows), "total_lost_days": total_lost,
            }}
        # authorized_only / full — return full rows.
        return {"code": code, "title": "Medical", "data": rows}

    if code == SECTION_AGENCY:
        return {"code": code, "title": "Police / Agency",
                "data": await ws.list_agency(db, case_id=case_id)}

    if code == SECTION_COMMUNICATIONS:
        rows = await ws.list_communications(db, case_id=case_id)
        if customer_facing:
            # Only customer-directed communications appear on customer reports.
            rows = [r for r in rows if r.get("kind") == "customer"]
        return {"code": code, "title": "Communications", "data": rows}

    if code == SECTION_CAPA:
        rows = await ca_engine.list_actions(
            db, consumer_kind="incident_case", consumer_id=case_id,
        )
        if customer_facing:
            # Customers see title/state only.
            rows = [{"title": r["title"], "state": r["state"],
                     "action_class": r["action_class"]} for r in rows]
        return {"code": code, "title": "Corrective Actions", "data": rows}

    if code == SECTION_ROOT_CAUSE:
        return {"code": code, "title": "Root Cause", "data": {
            "summary": sb.get("root_cause_summary") or "",
            "categories": sb.get("root_cause_categories") or [],
            "contributing_factors": sb.get("contributing_factors") or [],
        }}

    if code == SECTION_VEHICLE:
        return {"code": code, "title": "Vehicle Details", "data": {
            "vehicle_ids": fb.get("vehicle_ids") or "",
            "drivers":     fb.get("drivers") or "",
            "passengers":  fb.get("passengers") or "",
            "police_response":     fb.get("police_response") or "",
            "police_case_number":  fb.get("police_case_number") or "",
            "tow_required":        fb.get("tow_required") or "",
            "traffic_control":     fb.get("traffic_control") or "",
            "third_party_involved": fb.get("third_party_involved") or "",
            "third_party_info":     fb.get("third_party_info") or "",
        }}

    if code == SECTION_UTILITY:
        return {"code": code, "title": "Utility Strike Details", "data": {
            "utility_type":         fb.get("utility_type") or "",
            "utility_owner":        fb.get("utility_owner") or "",
            "locate_ticket_number": fb.get("locate_ticket_number") or "",
            "locate_valid":         fb.get("locate_valid") or "",
            "service_interrupted":  fb.get("service_interrupted") or "",
            "emergency_response_called": fb.get("emergency_response_called") or "",
            "isp_information":      fb.get("isp_information") or "",
        }}

    if code == SECTION_INJURY:
        return {"code": code, "title": "Injury Details", "data": {
            "injured_employee":  fb.get("injured_employee") or "",
            "injury_body_part":  fb.get("injury_body_part") or "",
            "injury_severity":   fb.get("injury_severity") or "",
            "first_aid_given":   fb.get("first_aid_given") or "",
            "ems_transported":   fb.get("ems_transported") or "",
            "hospital_name":     fb.get("hospital_name") or "",
            "injury_description": fb.get("injury_description") or "",
            "osha_recordable":   sb.get("osha_recordable"),
        }}

    if code == SECTION_LINKED:
        return {"code": code, "title": "Linked Records",
                "data": case.get("cross_links") or []}

    if code == SECTION_LESSONS_LEARNED:
        return {"code": code, "title": "Lessons Learned", "data": {
            "root_cause_summary":   sb.get("root_cause_summary") or "",
            "contributing_factors": sb.get("contributing_factors") or [],
            "executive_review_notes": sb.get("executive_review_notes") if allow_internal else "",
        }}

    return {"code": code, "title": code, "data": None}


async def render_report(db, *, case_id: str, report_type: str) -> Dict[str, Any]:
    """Render a report by declarative type."""
    definition = REPORT_DEFINITIONS.get(report_type)
    if not definition:
        raise ValueError(f"unknown report type: {report_type!r}")
    case = await case_service.get_case(db, case_id)
    if not case:
        raise LookupError(f"case {case_id} not found")

    privacy = definition.get("medical_privacy", "hidden")
    allow_internal = bool(definition.get("internal_notes", False))
    customer_facing = bool(definition.get("customer_facing", False))

    sections: List[Dict[str, Any]] = []
    for code in definition["sections"]:
        try:
            sections.append(await _render_section(
                db, case=case, code=code, privacy=privacy,
                allow_internal=allow_internal, customer_facing=customer_facing,
            ))
        except Exception as e:
            sections.append({"code": code, "title": code, "data": None, "error": str(e)})

    return {
        "report_type": report_type,
        "title": definition["title"],
        "audience": definition["audience"],
        "case_id": case_id,
        "case_number": case.get("case_number") or "",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "medical_privacy": privacy,
        "customer_facing": customer_facing,
        "sections": sections,
    }


async def render_weekly_digest(db) -> Dict[str, Any]:
    """Weekly Executive Digest — reuses `/api/incident-intelligence/brief`.
    No new intelligence engine."""
    brief = await compute_executive_brief(db)
    return {
        "kind": "weekly_executive_digest",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "sections": [
            {"code": "organization_health", "title": "Organization Health", "data": brief["organization_health"]},
            {"code": "major_risks",         "title": "Major Risks",         "data": brief["highest_risks"]},
            {"code": "positive_trends",     "title": "Positive Trends",     "data": brief["positive_trends"]},
            {"code": "negative_trends",     "title": "Negative Trends",     "data": brief["negative_trends"]},
            {"code": "top_projects_by_risk", "title": "Top Projects by Risk", "data": brief["top_projects_by_risk"]},
            {"code": "fleet",               "title": "Fleet Snapshot",      "data": brief["fleet"]},
            {"code": "learning",            "title": "Learning",            "data": brief["learning"]},
        ],
    }


__all__ = [
    "REPORT_DEFINITIONS", "report_types",
    "render_report", "render_weekly_digest",
]
