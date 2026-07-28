from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

from lib.trust_spine import attach_correlation, emit_record_created, emit_workflow_stage
from pm_routing import recipients_for_record_async
from routes.tasks_notifications import task_service
from services.cost_codes.foundation import (
    load_project_confidence_history,
    load_project_forecast_history,
)
from services.cost_codes.oppc_briefings import load_monday_briefing_doc
from services.operations_control.registry import build_operations_control_plane_registry

COLLECTION_CASES = "operations_control_plane_cases"
COLLECTION_CASE_HISTORY = "operations_control_plane_case_history"
COLLECTION_CASE_EXPORTS = "operations_control_plane_case_exports"
COLLECTION_CASE_CERTIFICATIONS = "operations_control_plane_case_certifications"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _slug(value: Any) -> str:
    return _clean(value).lower().replace(" ", "_")


def _priority_for_severity(severity: str) -> str:
    sev = _slug(severity)
    return {
        "emergency": "P0",
        "critical": "P1",
        "high": "P1",
        "moderate": "P2",
        "low": "P3",
        "informational": "P4",
        "info": "P4",
    }.get(sev, "P2")


def _display_status(status: str) -> str:
    return _clean(status).upper() or "OPEN"


async def ensure_case_management_indexes(db) -> None:
    await db[COLLECTION_CASES].create_index("id", unique=True)
    await db[COLLECTION_CASES].create_index("case_number", unique=True)
    await db[COLLECTION_CASES].create_index("case_key", unique=True)
    await db[COLLECTION_CASES].create_index([("status", 1), ("priority", 1), ("updated_at", -1)])
    await db[COLLECTION_CASES].create_index([("project_number", 1), ("updated_at", -1)])
    await db[COLLECTION_CASES].create_index([("origin.originating_event_id", 1)], unique=True, sparse=True)
    await db[COLLECTION_CASE_HISTORY].create_index("id", unique=True)
    await db[COLLECTION_CASE_HISTORY].create_index([("case_id", 1), ("at", 1)])
    await db[COLLECTION_CASE_EXPORTS].create_index("id", unique=True)
    await db[COLLECTION_CASE_EXPORTS].create_index([("case_id", 1), ("created_at", -1)])
    await db[COLLECTION_CASE_CERTIFICATIONS].create_index("id", unique=True)
    await db[COLLECTION_CASE_CERTIFICATIONS].create_index([("daily_report_id", 1)], unique=True)


def _case_registry() -> Tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    registry = build_operations_control_plane_registry()
    return (
        registry,
        dict(registry.get("case_types") or {}),
        dict(registry.get("case_lifecycle") or {}),
    )


def _allowed_transition(from_status: str, to_status: str, lifecycle: Dict[str, Any]) -> bool:
    transitions = dict(lifecycle.get("transitions") or {})
    allowed = list(transitions.get(_display_status(from_status)) or [])
    return _display_status(to_status) in allowed


def _constraint_types(report: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    for row in report.get("constraints") or []:
        if not isinstance(row, dict):
            continue
        ctype = _slug(row.get("constraint_type"))
        if ctype:
            out.append(ctype)
    return out


def _case_type_from_report(report: Dict[str, Any], case_types: Dict[str, Any]) -> str:
    constraints = set(_constraint_types(report))
    if _clean(report.get("injuries_reported")).lower() == "yes" or _clean(report.get("safety_incidents_today")).lower() == "yes":
        return "safety_event"
    if "utility" in constraints:
        return "utility_conflict"
    if "material" in constraints:
        return "material_delay"
    if _clean(report.get("schedule_delays")).lower() == "yes":
        return "schedule_variance"
    if "weather" in constraints:
        return "production_shortfall"
    if "equipment" in constraints:
        return "equipment_failure"
    fallback = "daily_report_exception"
    return fallback if fallback in case_types else next(iter(case_types.keys()), "general_operational_exception")


def _case_score(report: Dict[str, Any]) -> Dict[str, Any]:
    reasons: List[str] = []
    score = 0
    constraints = list(report.get("constraints") or [])
    if _clean(report.get("schedule_delays")).lower() == "yes":
        score += 1
        reasons.append("schedule_delay")
    if len(constraints) >= 2:
        score += 1
        reasons.append("multiple_constraints")
    if _clean(report.get("weather_impact")).lower() == "yes":
        score += 1
        reasons.append("weather_impact")
    if _clean(report.get("safety_incidents_today")).lower() == "yes":
        score += 2
        reasons.append("safety_incident")
    if _clean(report.get("injuries_reported")).lower() == "yes":
        score += 2
        reasons.append("injury_reported")
    if bool(report.get("certification_record")):
        score += 3
        reasons.append("preview_certification_scope")
    if len(_clean(report.get("general_notes"))) >= 60 or len(_clean(report.get("schedule_delays_notes"))) >= 30:
        score += 1
        reasons.append("narrative_operational_impact")
    severity = "moderate"
    if "injury_reported" in reasons:
        severity = "critical"
    elif "safety_incident" in reasons or score >= 5:
        severity = "high"
    elif score <= 1:
        severity = "low"
    return {
        "score": score,
        "reasons": reasons,
        "severity": severity,
        "priority": _priority_for_severity(severity),
    }


async def _ownership_for_project(db, report: Dict[str, Any]) -> Dict[str, Any]:
    owner = {
        "assigned_role": "admin",
        "case_owner_role": "admin",
        "case_owner_name": "Operations Admin",
        "case_owner_email": "",
        "ownership_source": "fallback_admin",
    }
    explicit_email = _clean(report.get("case_owner_email") or report.get("project_pm_email")).lower()
    explicit_name = _clean(report.get("case_owner_name") or report.get("project_pm_name"))
    if explicit_email:
        owner.update(
            {
                "assigned_role": "pm",
                "case_owner_role": "pm",
                "case_owner_name": explicit_name or explicit_email,
                "case_owner_email": explicit_email,
                "ownership_source": "explicit_preview_owner",
            }
        )
        return owner
    try:
        dist = await recipients_for_record_async(db, report, "daily-report")
        if dist.get("pm_email"):
            owner.update(
                {
                    "assigned_role": "pm",
                    "case_owner_role": "pm",
                    "case_owner_name": _clean(dist.get("pm_name")) or _clean(dist.get("pm_email")),
                    "case_owner_email": _clean(dist.get("pm_email")).lower(),
                    "ownership_source": "project_pm_distribution",
                }
            )
    except Exception:
        pass
    return owner


def _case_key_from_record(record: Dict[str, Any], policy_id: str) -> str:
    return f"{_clean(record.get('id'))}:{_clean(policy_id)}"


async def _append_case_history(
    db,
    *,
    case_id: str,
    event_type: str,
    actor: Dict[str, Any],
    note: str = "",
    from_status: Optional[str] = None,
    to_status: Optional[str] = None,
    details: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    row = {
        "id": str(uuid.uuid4()),
        "case_id": case_id,
        "event_type": _clean(event_type),
        "actor": {
            "id": _clean(actor.get("id") or actor.get("user_id")),
            "role": _clean(actor.get("role")) or "system",
            "name": _clean(actor.get("name") or actor.get("email")) or "system",
            "email": _clean(actor.get("email")),
        },
        "note": _clean(note),
        "from_status": _display_status(from_status or "") if from_status else None,
        "to_status": _display_status(to_status or "") if to_status else None,
        "details": dict(details or {}),
        "at": _now_iso(),
    }
    await db[COLLECTION_CASE_HISTORY].insert_one(dict(row))
    await db[COLLECTION_CASES].update_one(
        {"id": case_id},
        {
            "$set": {
                "updated_at": row["at"],
                "last_history_at": row["at"],
                "last_history_event": row["event_type"],
            },
            "$push": {
                "audit_history": {
                    "id": row["id"],
                    "at": row["at"],
                    "event_type": row["event_type"],
                    "actor": row["actor"],
                    "note": row["note"],
                    "from_status": row.get("from_status"),
                    "to_status": row.get("to_status"),
                }
            },
        },
    )
    return row


async def get_case_by_id(db, case_id: str) -> Optional[Dict[str, Any]]:
    return await db[COLLECTION_CASES].find_one({"id": case_id}, {"_id": 0})


async def get_case_by_event_id(db, event_id: str) -> Optional[Dict[str, Any]]:
    return await db[COLLECTION_CASES].find_one({"origin.originating_event_id": event_id}, {"_id": 0})


async def list_case_history(db, case_id: str, limit: int = 500) -> List[Dict[str, Any]]:
    cur = db[COLLECTION_CASE_HISTORY].find({"case_id": case_id}, {"_id": 0}).sort("at", 1).limit(limit)
    return [row async for row in cur]


async def list_cases(
    db,
    *,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    project_number: Optional[str] = None,
    limit: int = 200,
) -> Dict[str, Any]:
    query: Dict[str, Any] = {}
    if status:
        query["status"] = _display_status(status)
    if severity:
        query["severity"] = _slug(severity)
    if project_number:
        query["project_number"] = _clean(project_number)
    rows = [
        row
        async for row in db[COLLECTION_CASES].find(query, {"_id": 0}).sort(
            [("priority_rank", 1), ("updated_at", -1)]
        ).limit(limit)
    ]
    summary = {
        "total": len(rows),
        "open": sum(1 for row in rows if row.get("status") not in {"CLOSED", "ARCHIVED", "CANCELLED"}),
        "escalated": sum(1 for row in rows if row.get("status") == "ESCALATED"),
        "pending_verification": sum(1 for row in rows if row.get("status") == "PENDING_VERIFICATION"),
        "critical": sum(1 for row in rows if row.get("severity") in {"critical", "emergency"}),
    }
    return {"count": len(rows), "summary": summary, "cases": rows}


def _priority_rank(priority: str) -> int:
    return {"P0": 0, "P1": 1, "P2": 2, "P3": 3, "P4": 4}.get(_clean(priority).upper(), 9)


async def maybe_auto_create_case_from_control_plane_event(
    db,
    *,
    event_doc: Dict[str, Any],
    record: Dict[str, Any],
    actor_label: str,
) -> Dict[str, Any]:
    await ensure_case_management_indexes(db)
    registry, case_types, lifecycle = _case_registry()
    policies = dict(registry.get("case_creation_policies") or {})
    policy = dict(policies.get(_clean(event_doc.get("event_type_id"))) or {})
    if not policy:
        return {"created": False, "decision": {"outcome": "suppress", "reason": "no_policy"}}
    case_key = _case_key_from_record(record, _clean(policy.get("id")) or "case_policy")
    existing = await db[COLLECTION_CASES].find_one(
        {
            "$or": [
                {"origin.originating_event_id": _clean(event_doc.get("id"))},
                {"case_key": case_key},
                {
                    "origin.source_record_id": _clean(record.get("id")),
                    "origin.policy_id": _clean(policy.get("id")) or "case_policy",
                },
            ]
        },
        {"_id": 0},
    )
    if existing:
        return {"created": False, "case": existing, "decision": {"outcome": "link", "reason": "existing_case_for_event"}}
    score = _case_score(record)
    threshold = int(policy.get("create_threshold") or 999)
    if score["score"] < threshold:
        return {"created": False, "decision": {"outcome": "suppress", "reason": "below_threshold", "score": score}}
    case_type_id = _case_type_from_report(record, case_types)
    case_type = dict(case_types.get(case_type_id) or {})
    ownership = await _ownership_for_project(db, record)
    case_id = str(uuid.uuid4())
    correlation_id = _clean(event_doc.get("correlation_id")) or attach_correlation(
        {"id": case_id, "doc_id": case_id, "project_number": _clean(record.get("project_number"))}
    )
    preview_ack_sla = None
    if bool(record.get("certification_record")):
        preview_ack_sla = int(policy.get("proof_scope_accelerated_ack_sla_minutes") or 1)
    case_doc = {
        "id": case_id,
        "case_number": f"OPC-{_now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
        "doc_id": f"OPC-{_now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
        "case_key": case_key,
        "case_type_id": case_type_id,
        "case_type_label": case_type.get("display_name") or case_type_id,
        "status": _display_status((lifecycle.get("default_status") or "OPEN")),
        "severity": _slug(score.get("severity")),
        "priority": score.get("priority") or _priority_for_severity(score.get("severity") or "moderate"),
        "priority_rank": _priority_rank(score.get("priority") or "P2"),
        "project_number": _clean(record.get("project_number")),
        "project_name": _clean(record.get("project_name")),
        "location": _clean(record.get("location")),
        "report_date": _clean(record.get("report_date")),
        "case_owner_role": ownership.get("case_owner_role"),
        "case_owner_name": ownership.get("case_owner_name"),
        "case_owner_email": ownership.get("case_owner_email"),
        "assigned_role": ownership.get("assigned_role"),
        "ownership_source": ownership.get("ownership_source"),
        "preview_ack_sla_minutes": preview_ack_sla,
        "origin": {
            "originating_event_id": _clean(event_doc.get("id")),
            "originating_event_type_id": _clean(event_doc.get("event_type_id")),
            "source_collection": _clean(event_doc.get("record_snapshot", {}).get("source_collection") or event_doc.get("source_collection") or "daily_reports"),
            "source_record_id": _clean(record.get("id")),
            "source_doc_id": _clean(record.get("doc_id")),
            "source_record_type": "daily_report",
            "policy_id": _clean(policy.get("id")),
            "policy_version": _clean(policy.get("version")),
            "decision_mode": _clean(policy.get("decision_mode")) or "auto",
            "decision_score": score,
            "created_from_preview_certification": bool(record.get("certification_record")),
        },
        "correlation_id": correlation_id,
        "causation_ids": [_clean(event_doc.get("id"))],
        "linked_record_ids": {
            "daily_report_id": _clean(record.get("id")),
            "daily_report_doc_id": _clean(record.get("doc_id")),
            "event_ids": [_clean(event_doc.get("id"))],
            "communication_ids": [],
            "task_ids": [],
            "evidence_package_ids": [],
            "baseline_ids": [],
            "variance_keys": [],
            "corrective_action_ids": [],
            "related_case_ids": [],
        },
        "resolution": {
            "root_cause": "",
            "reason": "",
            "summary": "",
            "verified_by": "",
            "verified_at": "",
            "verification_notes": "",
            "closed_at": "",
            "reopened_at": "",
            "duplicate_of_case_id": "",
        },
        "escalation_state": {
            "is_escalated": False,
            "last_escalated_at": "",
            "escalation_count": 0,
        },
        "policy_flags": {
            "closure_requirements": list(case_type.get("closure_requirements") or []),
            "evidence_requirements": list(case_type.get("evidence_requirements") or []),
            "required_roles": list(case_type.get("required_roles") or []),
            "one_event_one_outcome": bool(policy.get("one_event_one_outcome")),
        },
        "audit_history": [],
        "created_at": _now_iso(),
        "updated_at": _now_iso(),
    }
    case_doc["doc_id"] = case_doc["case_number"]
    await db[COLLECTION_CASES].insert_one(dict(case_doc))
    await _append_case_history(
        db,
        case_id=case_id,
        event_type="case_created",
        actor={"role": "system", "name": actor_label or "operations-control-plane"},
        note="Case created from registered event policy.",
        to_status=case_doc["status"],
        details={"originating_event_id": _clean(event_doc.get("id")), "policy_id": case_doc["origin"]["policy_id"]},
    )
    case_ref = {
        "id": case_doc["id"],
        "doc_id": case_doc["case_number"],
        "project_number": case_doc["project_number"],
        "_trust_cid": case_doc["correlation_id"],
    }
    await emit_record_created(
        db,
        workflow="oppc-operational-case-management",
        record=case_ref,
        module="services/operations_control/case_management.py:maybe_auto_create_case_from_control_plane_event",
        event_name="operational_case.created",
    )
    await emit_workflow_stage(
        db,
        workflow="oppc-operational-case-management",
        stage="record_created",
        record=case_ref,
        module="services/operations_control/case_management.py:case_record_created",
        status="ok",
        event_name="operational_case.created",
    )
    from services.operations_control.control_plane import emit_operational_event

    event_result = await emit_operational_event(
        db,
        event_id="operational_case.created",
        record=case_doc,
        actor_label=actor_label or "operations-control-plane",
        context={
            "case_id": case_doc["id"],
            "case_number": case_doc["case_number"],
            "originating_event_id": _clean(event_doc.get("id")),
        },
    )
    communication_ids = [row.get("id") for row in (event_result.get("communications") or []) if row.get("id")]
    event_ids = [event_result.get("event", {}).get("id")] if event_result.get("event", {}).get("id") else []
    linked = dict(case_doc.get("linked_record_ids") or {})
    linked["communication_ids"] = communication_ids
    linked["event_ids"] = [*linked.get("event_ids", []), *event_ids]
    await db[COLLECTION_CASES].update_one(
        {"id": case_id},
        {
            "$set": {
                "linked_record_ids": linked,
                "latest_case_event_id": event_result.get("event", {}).get("id"),
                "latest_communication_id": communication_ids[0] if communication_ids else "",
            }
        },
    )
    case_doc = await get_case_by_id(db, case_id) or case_doc
    return {
        "created": True,
        "case": case_doc,
        "decision": {"outcome": "create", "score": score, "policy_id": case_doc["origin"]["policy_id"]},
        "case_event": event_result.get("event"),
        "case_communications": event_result.get("communications") or [],
    }


async def _resolve_case_links(db, case_doc: Dict[str, Any]) -> Dict[str, Any]:
    project_number = _clean(case_doc.get("project_number"))
    variance_rows: List[Dict[str, Any]] = []
    if project_number:
        cur = db.operational_variance_reviews.find({"project_number": project_number}, {"_id": 0}).sort("updated_at", -1).limit(10)
        variance_rows = [row async for row in cur]
    forecast_history = await load_project_forecast_history(db, project_number)
    confidence_history = await load_project_confidence_history(db, project_number)
    monday_briefing = None
    if project_number:
        try:
            monday_briefing = await load_monday_briefing_doc(
                db,
                scope_type="project",
                scope_key=project_number,
                week_ending=_clean(case_doc.get("report_date")) or _now().date().isoformat(),
            )
        except Exception:
            monday_briefing = None
    tasks = [
        row
        async for row in db.tasks.find(
            {
                "$or": [
                    {"source_record_id": case_doc.get("id")},
                    {"linked_project_number": project_number, "source_module": "operations_control.case_management"},
                ]
            },
            {"_id": 0},
        ).sort("created_at", -1).limit(50)
    ]
    corrective_actions = [
        row
        async for row in db.corrective_actions.find(
            {"project_number": project_number} if project_number else {"id": {"$in": []}},
            {"_id": 0},
        ).sort("created_at", -1).limit(20)
    ]
    return {
        "variance_reviews": variance_rows,
        "forecast_history": forecast_history,
        "confidence_history": confidence_history,
        "monday_briefing": monday_briefing or {},
        "tasks": tasks,
        "corrective_actions": corrective_actions,
    }


async def build_case_assembly(db, case_id: str) -> Dict[str, Any]:
    case_doc = await get_case_by_id(db, case_id)
    if not case_doc:
        raise LookupError(f"Unknown case: {case_id}")
    linked = dict(case_doc.get("linked_record_ids") or {})
    daily_report = None
    if linked.get("daily_report_id"):
        daily_report = await db.daily_reports.find_one({"id": linked.get("daily_report_id")}, {"_id": 0})
    event_ids = [str(x) for x in (linked.get("event_ids") or []) if str(x).strip()]
    communication_ids = [str(x) for x in (linked.get("communication_ids") or []) if str(x).strip()]
    events = [
        row
        async for row in db.operations_control_plane_events.find(
            {"id": {"$in": event_ids}} if event_ids else {"id": {"$in": []}},
            {"_id": 0},
        ).sort("created_at", 1)
    ]
    communications = [
        row
        async for row in db.operations_control_plane_communications.find(
            {"id": {"$in": communication_ids}} if communication_ids else {"id": {"$in": []}},
            {"_id": 0},
        ).sort("created_at", 1)
    ]
    history = await list_case_history(db, case_id)
    trust_rows = [
        row
        async for row in db.trust_spine_events.find(
            {
                "$or": [
                    {"record_id": case_id},
                    {"record_id": linked.get("daily_report_id")},
                    {"correlation_id": case_doc.get("correlation_id")},
                ]
            },
            {"_id": 0},
        ).sort("ts", 1).limit(200)
    ]
    evidence_rows = [
        row
        async for row in db.operations_control_plane_evidence.find(
            {
                "$or": [
                    {"record_id": case_id},
                    {"record_id": linked.get("daily_report_id")},
                    {"id": {"$in": list(linked.get("evidence_package_ids") or [])}},
                ]
            },
            {"_id": 0},
        ).sort("created_at", -1).limit(20)
    ]
    baseline_rows = [
        row
        async for row in db.operations_control_plane_baselines.find(
            {"id": {"$in": list(linked.get("baseline_ids") or [])}} if linked.get("baseline_ids") else {"id": {"$in": []}},
            {"_id": 0},
        ).sort("created_at", -1)
    ]
    satellites = await _resolve_case_links(db, case_doc)
    summary = {
        "case_id": case_doc.get("id"),
        "case_number": case_doc.get("case_number"),
        "status": case_doc.get("status"),
        "severity": case_doc.get("severity"),
        "priority": case_doc.get("priority"),
        "communication_count": len(communications),
        "trust_event_count": len(trust_rows),
        "evidence_count": len(evidence_rows),
        "task_count": len(satellites.get("tasks") or []),
        "variance_review_count": len(satellites.get("variance_reviews") or []),
        "forecast_snapshot_count": len((satellites.get("forecast_history") or {}).get("snapshots") or []),
        "confidence_snapshot_count": len((satellites.get("confidence_history") or {}).get("snapshots") or []),
    }
    return {
        "case": case_doc,
        "summary": summary,
        "authoritative_records": {
            "daily_report": daily_report or {},
            "events": events,
            "communications": communications,
            "history": history,
            "trust_spine": trust_rows,
            "evidence_packages": evidence_rows,
            "baselines": baseline_rows,
            **satellites,
        },
    }


async def build_case_timeline(db, case_id: str) -> List[Dict[str, Any]]:
    assembly = await build_case_assembly(db, case_id)
    case_doc = assembly.get("case") or {}
    rows: List[Dict[str, Any]] = []
    daily_report = (assembly.get("authoritative_records") or {}).get("daily_report") or {}
    if daily_report:
        rows.append(
            {
                "id": f"dr:{daily_report.get('id')}",
                "kind": "daily_report",
                "at": daily_report.get("created_at") or case_doc.get("created_at"),
                "title": f"Daily Report {daily_report.get('doc_id') or daily_report.get('id')}",
                "status": daily_report.get("lifecycle_state") or "submitted",
                "source_id": daily_report.get("id"),
                "details": {
                    "project_number": daily_report.get("project_number"),
                    "project_name": daily_report.get("project_name"),
                },
            }
        )
    for row in (assembly.get("authoritative_records") or {}).get("events") or []:
        rows.append(
            {
                "id": f"event:{row.get('id')}",
                "kind": "event",
                "at": row.get("created_at"),
                "title": row.get("title") or row.get("event_type_id"),
                "status": row.get("status") or "processed",
                "source_id": row.get("id"),
                "details": {"event_type_id": row.get("event_type_id"), "workflow_id": row.get("workflow_id")},
            }
        )
    for row in (assembly.get("authoritative_records") or {}).get("communications") or []:
        rows.append(
            {
                "id": f"comm:{row.get('id')}",
                "kind": "communication",
                "at": row.get("created_at"),
                "title": row.get("title") or row.get("communication_intent_id"),
                "status": row.get("status") or row.get("ack_status"),
                "source_id": row.get("id"),
                "details": {
                    "ack_status": row.get("ack_status"),
                    "ack_due_at": row.get("ack_due_at"),
                    "email_recipients": row.get("email_recipients") or [],
                },
            }
        )
    for row in (assembly.get("authoritative_records") or {}).get("history") or []:
        rows.append(
            {
                "id": f"history:{row.get('id')}",
                "kind": "case_history",
                "at": row.get("at"),
                "title": row.get("event_type"),
                "status": row.get("to_status") or row.get("from_status") or case_doc.get("status"),
                "source_id": row.get("id"),
                "details": row.get("details") or {},
            }
        )
    for row in (assembly.get("authoritative_records") or {}).get("tasks") or []:
        created_at = row.get("created_at")
        if isinstance(created_at, datetime):
            created_at = created_at.astimezone(timezone.utc).isoformat()
        rows.append(
            {
                "id": f"task:{row.get('id')}",
                "kind": "task",
                "at": created_at,
                "title": row.get("title"),
                "status": row.get("status"),
                "source_id": row.get("id"),
                "details": {"priority": row.get("priority"), "due_at": row.get("due_at")},
            }
        )
    for row in (assembly.get("authoritative_records") or {}).get("trust_spine") or []:
        rows.append(
            {
                "id": f"trust:{row.get('id') or row.get('ts')}",
                "kind": "trust_spine",
                "at": row.get("ts"),
                "title": row.get("event_name") or row.get("stage") or "trust_spine",
                "status": row.get("status") or row.get("stage"),
                "source_id": row.get("id") or row.get("record_id"),
                "details": {"workflow": row.get("workflow"), "stage": row.get("stage")},
            }
        )
    rows.sort(key=lambda row: _clean(row.get("at")) or "")
    return rows


async def build_case_relationship_graph(db, case_id: str) -> Dict[str, Any]:
    assembly = await build_case_assembly(db, case_id)
    case_doc = assembly.get("case") or {}
    linked = dict(case_doc.get("linked_record_ids") or {})
    nodes = [
        {
            "id": case_doc.get("id"),
            "type": "case",
            "label": case_doc.get("case_number") or case_doc.get("id"),
            "status": case_doc.get("status"),
            "metadata": {"severity": case_doc.get("severity"), "priority": case_doc.get("priority")},
        }
    ]
    edges: List[Dict[str, Any]] = []
    daily_report_id = linked.get("daily_report_id")
    if daily_report_id:
        nodes.append(
            {
                "id": daily_report_id,
                "type": "daily_report",
                "label": linked.get("daily_report_doc_id") or daily_report_id,
                "status": "authoritative",
                "metadata": {"project_number": case_doc.get("project_number")},
            }
        )
        edges.append({"from": daily_report_id, "to": case_doc.get("id"), "relationship": "originates_case"})
    for event_id in linked.get("event_ids") or []:
        nodes.append({"id": event_id, "type": "event", "label": event_id, "status": "registered", "metadata": {}})
        edges.append({"from": event_id, "to": case_doc.get("id"), "relationship": "governed_outcome"})
    for comm_id in linked.get("communication_ids") or []:
        nodes.append({"id": comm_id, "type": "communication", "label": comm_id, "status": "persisted", "metadata": {}})
        edges.append({"from": case_doc.get("id"), "to": comm_id, "relationship": "communicated_via"})
    for task_id in linked.get("task_ids") or []:
        nodes.append({"id": task_id, "type": "task", "label": task_id, "status": "linked", "metadata": {}})
        edges.append({"from": case_doc.get("id"), "to": task_id, "relationship": "corrective_action"})
    for related_id in linked.get("related_case_ids") or []:
        nodes.append({"id": related_id, "type": "case", "label": related_id, "status": "related", "metadata": {}})
        edges.append({"from": case_doc.get("id"), "to": related_id, "relationship": "related_case"})
    for baseline_id in linked.get("baseline_ids") or []:
        nodes.append({"id": baseline_id, "type": "baseline", "label": baseline_id, "status": "captured", "metadata": {}})
        edges.append({"from": case_doc.get("id"), "to": baseline_id, "relationship": "included_in_baseline"})
    for evidence_id in linked.get("evidence_package_ids") or []:
        nodes.append({"id": evidence_id, "type": "evidence", "label": evidence_id, "status": "captured", "metadata": {}})
        edges.append({"from": case_doc.get("id"), "to": evidence_id, "relationship": "evidence_package"})
    return {"nodes": nodes, "edges": edges}


async def transition_case(
    db,
    *,
    case_id: str,
    to_status: str,
    actor: Dict[str, Any],
    reason: str = "",
    resolution_summary: str = "",
    root_cause: str = "",
    verification_notes: str = "",
    duplicate_of_case_id: str = "",
) -> Dict[str, Any]:
    registry, _, lifecycle = _case_registry()
    case_doc = await get_case_by_id(db, case_id)
    if not case_doc:
        raise LookupError(f"Unknown case: {case_id}")
    from_status = _display_status(case_doc.get("status"))
    to_status = _display_status(to_status)
    if not _allowed_transition(from_status, to_status, lifecycle):
        raise ValueError(f"Transition {from_status} -> {to_status} is not allowed")
    linked = dict(case_doc.get("linked_record_ids") or {})
    evidence_ids = list(linked.get("evidence_package_ids") or [])
    if to_status == "DUPLICATE" and not _clean(duplicate_of_case_id):
        raise ValueError("duplicate_of_case_id is required when marking a case duplicate")
    if to_status == "CLOSED":
        if not (_clean(reason) or _clean(case_doc.get("resolution", {}).get("reason"))):
            raise ValueError("Case closure requires a recorded closure reason")
        if not (_clean(root_cause) or _clean(case_doc.get("resolution", {}).get("root_cause"))):
            raise ValueError("Case closure requires a root cause or governed reason")
        if not evidence_ids:
            raise ValueError("Case closure requires at least one captured evidence package")
    now_iso = _now_iso()
    update_set: Dict[str, Any] = {
        "status": to_status,
        "updated_at": now_iso,
    }
    resolution = dict(case_doc.get("resolution") or {})
    if resolution_summary:
        resolution["summary"] = _clean(resolution_summary)
    if reason:
        resolution["reason"] = _clean(reason)
    if root_cause:
        resolution["root_cause"] = _clean(root_cause)
    if verification_notes:
        resolution["verification_notes"] = _clean(verification_notes)
    if to_status == "PENDING_VERIFICATION":
        resolution["verified_at"] = now_iso
        resolution["verified_by"] = _clean(actor.get("name") or actor.get("email") or actor.get("role"))
    if to_status == "CLOSED":
        resolution["closed_at"] = now_iso
        resolution["verified_at"] = resolution.get("verified_at") or now_iso
        resolution["verified_by"] = resolution.get("verified_by") or _clean(actor.get("name") or actor.get("email") or actor.get("role"))
    if to_status == "REOPENED":
        resolution["reopened_at"] = now_iso
    if to_status == "DUPLICATE":
        resolution["duplicate_of_case_id"] = _clean(duplicate_of_case_id)
        linked["related_case_ids"] = sorted({*list(linked.get("related_case_ids") or []), _clean(duplicate_of_case_id)})
        update_set["linked_record_ids"] = linked
    update_set["resolution"] = resolution
    escalation = dict(case_doc.get("escalation_state") or {})
    if to_status == "ESCALATED":
        escalation["is_escalated"] = True
        escalation["last_escalated_at"] = now_iso
        escalation["escalation_count"] = int(escalation.get("escalation_count") or 0) + 1
    elif to_status in {"RESOLVED", "CLOSED", "UNDER_REVIEW", "INVESTIGATING", "ACTION_REQUIRED", "RECOVERY_ACTIVE", "PENDING_VERIFICATION"}:
        escalation["is_escalated"] = False
    update_set["escalation_state"] = escalation
    await db[COLLECTION_CASES].update_one({"id": case_id}, {"$set": update_set})
    await _append_case_history(
        db,
        case_id=case_id,
        event_type="case_transition",
        actor=actor,
        note=reason or f"Transitioned to {to_status}",
        from_status=from_status,
        to_status=to_status,
        details={"resolution_summary": _clean(resolution_summary), "duplicate_of_case_id": _clean(duplicate_of_case_id)},
    )
    event_name = {
        "ESCALATED": "operational_case.escalated",
        "PENDING_VERIFICATION": "operational_case.pending_verification",
        "RESOLVED": "operational_case.resolved",
        "CLOSED": "operational_case.closed",
        "REOPENED": "operational_case.reopened",
    }.get(to_status)
    if event_name:
        from services.operations_control.control_plane import emit_operational_event

        fresh = await get_case_by_id(db, case_id)
        if fresh:
            result = await emit_operational_event(
                db,
                event_id=event_name,
                record=fresh,
                actor_label=_clean(actor.get("name") or actor.get("email") or actor.get("role")) or "system",
                context={"case_id": case_id, "from_status": from_status, "to_status": to_status},
            )
            comm_ids = [row.get("id") for row in (result.get("communications") or []) if row.get("id")]
            if comm_ids:
                await db[COLLECTION_CASES].update_one(
                    {"id": case_id},
                    {
                        "$addToSet": {"linked_record_ids.communication_ids": {"$each": comm_ids}},
                        "$set": {"latest_communication_id": comm_ids[-1]},
                    },
                )
    fresh = await get_case_by_id(db, case_id)
    if not fresh:
        raise LookupError(f"Unknown case after transition: {case_id}")
    return fresh


async def acknowledge_case_communication(
    db,
    *,
    case_id: str,
    communication_id: str,
    actor: Dict[str, Any],
    note: str = "",
) -> Dict[str, Any]:
    from services.operations_control.control_plane import acknowledge_communication

    row = await acknowledge_communication(db, communication_id=communication_id, actor=actor, note=note)
    if not row:
        raise LookupError(f"Unknown communication: {communication_id}")
    await _append_case_history(
        db,
        case_id=case_id,
        event_type="communication_acknowledged",
        actor=actor,
        note=note or "Communication acknowledged",
        details={"communication_id": communication_id},
    )
    fresh = await get_case_by_id(db, case_id)
    if not fresh:
        raise LookupError(f"Unknown case: {case_id}")
    return fresh


async def create_case_task(
    db,
    *,
    case_id: str,
    actor: Dict[str, Any],
    title: str,
    description: str = "",
    assignee_role: str = "pm",
    priority: str = "High",
    due_minutes: int = 1440,
) -> Dict[str, Any]:
    case_doc = await get_case_by_id(db, case_id)
    if not case_doc:
        raise LookupError(f"Unknown case: {case_id}")
    task_id = await task_service.create(
        db,
        {
            "title": _clean(title) or f"Operational Case {case_doc.get('case_number')} follow-up",
            "description": _clean(description) or f"Corrective action linked to case {case_doc.get('case_number')}",
            "source_module": "operations_control.case_management",
            "source_record_id": case_id,
            "linked_project_number": case_doc.get("project_number"),
            "assignee_role": _clean(assignee_role) or case_doc.get("assigned_role") or "pm",
            "priority": _clean(priority).title(),
            "due_at": _now() + timedelta(minutes=max(1, int(due_minutes or 1))),
            "created_by": {
                "role": _clean(actor.get("role")) or "admin",
                "name": _clean(actor.get("name") or actor.get("email")) or "system",
                "email": _clean(actor.get("email")),
            },
        },
    )
    await db[COLLECTION_CASES].update_one(
        {"id": case_id},
        {"$addToSet": {"linked_record_ids.task_ids": task_id}, "$set": {"updated_at": _now_iso()}},
    )
    await _append_case_history(
        db,
        case_id=case_id,
        event_type="task_linked",
        actor=actor,
        note=_clean(title) or "Case task created",
        details={"task_id": task_id},
    )
    fresh = await get_case_by_id(db, case_id)
    if not fresh:
        raise LookupError(f"Unknown case: {case_id}")
    return {"case": fresh, "task_id": task_id}


async def link_related_case(
    db,
    *,
    case_id: str,
    related_case_id: str,
    actor: Dict[str, Any],
    note: str = "",
) -> Dict[str, Any]:
    if case_id == related_case_id:
        raise ValueError("A case cannot link to itself")
    primary = await get_case_by_id(db, case_id)
    related = await get_case_by_id(db, related_case_id)
    if not primary or not related:
        raise LookupError("Both case records must exist before linking them")
    await db[COLLECTION_CASES].update_one(
        {"id": case_id},
        {"$addToSet": {"linked_record_ids.related_case_ids": related_case_id}, "$set": {"updated_at": _now_iso()}},
    )
    await db[COLLECTION_CASES].update_one(
        {"id": related_case_id},
        {"$addToSet": {"linked_record_ids.related_case_ids": case_id}, "$set": {"updated_at": _now_iso()}},
    )
    await _append_case_history(
        db,
        case_id=case_id,
        event_type="related_case_linked",
        actor=actor,
        note=note or f"Linked related case {related_case_id}",
        details={"related_case_id": related_case_id},
    )
    fresh = await get_case_by_id(db, case_id)
    if not fresh:
        raise LookupError(f"Unknown case: {case_id}")
    return fresh


async def capture_case_evidence_package(db, *, case_id: str, actor: Dict[str, Any]) -> Dict[str, Any]:
    case_doc = await get_case_by_id(db, case_id)
    if not case_doc:
        raise LookupError(f"Unknown case: {case_id}")
    from services.operations_control.control_plane import build_readiness_evidence_package

    evidence = await build_readiness_evidence_package(
        db,
        workflow_id="oppc.operational_case_management",
        actor_label=_clean(actor.get("name") or actor.get("email") or actor.get("role")) or "system",
        record_id=case_id,
    )
    await db[COLLECTION_CASES].update_one(
        {"id": case_id},
        {"$addToSet": {"linked_record_ids.evidence_package_ids": evidence.get("id")}, "$set": {"updated_at": _now_iso()}},
    )
    await _append_case_history(
        db,
        case_id=case_id,
        event_type="evidence_package_captured",
        actor=actor,
        note="Case evidence package captured",
        details={"evidence_package_id": evidence.get("id")},
    )
    return evidence


async def include_case_in_baseline(
    db,
    *,
    case_id: str,
    actor: Dict[str, Any],
    baseline_name: str,
) -> Dict[str, Any]:
    case_doc = await get_case_by_id(db, case_id)
    if not case_doc:
        raise LookupError(f"Unknown case: {case_id}")
    from services.operations_control.control_plane import build_baseline_snapshot

    baseline = await build_baseline_snapshot(
        db,
        baseline_name=_clean(baseline_name) or "Operations Control Plane v1",
        actor_label=_clean(actor.get("name") or actor.get("email") or actor.get("role")) or "system",
    )
    await db[COLLECTION_CASES].update_one(
        {"id": case_id},
        {"$addToSet": {"linked_record_ids.baseline_ids": baseline.get("id")}, "$set": {"updated_at": _now_iso()}},
    )
    await _append_case_history(
        db,
        case_id=case_id,
        event_type="baseline_included",
        actor=actor,
        note="Case included in baseline snapshot",
        details={"baseline_id": baseline.get("id")},
    )
    return baseline


async def export_case_evidence_package(db, *, case_id: str, actor: Dict[str, Any]) -> Dict[str, Any]:
    case_doc = await get_case_by_id(db, case_id)
    if not case_doc:
        raise LookupError(f"Unknown case: {case_id}")
    assembly = await build_case_assembly(db, case_id)
    timeline = await build_case_timeline(db, case_id)
    graph = await build_case_relationship_graph(db, case_id)
    payload = {
        "case": assembly.get("case") or {},
        "summary": assembly.get("summary") or {},
        "authoritative_records": assembly.get("authoritative_records") or {},
        "timeline": timeline,
        "relationship_graph": graph,
        "exported_at": _now_iso(),
        "exported_by": {
            "role": _clean(actor.get("role")),
            "name": _clean(actor.get("name") or actor.get("email")),
            "email": _clean(actor.get("email")),
        },
        "proof_chain": {
            "daily_report_id": (assembly.get("authoritative_records") or {}).get("daily_report", {}).get("id"),
            "originating_event_id": (assembly.get("case") or {}).get("origin", {}).get("originating_event_id"),
            "communication_ids": ((assembly.get("case") or {}).get("linked_record_ids") or {}).get("communication_ids") or [],
            "task_ids": ((assembly.get("case") or {}).get("linked_record_ids") or {}).get("task_ids") or [],
            "evidence_package_ids": ((assembly.get("case") or {}).get("linked_record_ids") or {}).get("evidence_package_ids") or [],
            "baseline_ids": ((assembly.get("case") or {}).get("linked_record_ids") or {}).get("baseline_ids") or [],
        },
    }
    export_row = {
        "id": str(uuid.uuid4()),
        "case_id": case_id,
        "case_number": case_doc.get("case_number"),
        "created_at": _now_iso(),
        "created_by": {
            "role": _clean(actor.get("role")),
            "name": _clean(actor.get("name") or actor.get("email")),
            "email": _clean(actor.get("email")),
        },
        "payload": payload,
        "status": "captured",
    }
    await db[COLLECTION_CASE_EXPORTS].insert_one(dict(export_row))
    await _append_case_history(
        db,
        case_id=case_id,
        event_type="evidence_exported",
        actor=actor,
        note="Case evidence package exported",
        details={"export_id": export_row.get("id")},
    )
    return export_row


async def create_preview_case_certification_record(db, *, actor: Dict[str, Any]) -> Dict[str, Any]:
    await ensure_case_management_indexes(db)
    from doc_ids import ensure_doc_id
    from services.operations_control.control_plane import ingest_daily_report_submission

    cert_id = str(uuid.uuid4())
    today = _now().date().isoformat()
    report = {
        "id": cert_id,
        "project_name": "PREVIEW OPPC CASE CERTIFICATION",
        "project_number": f"PREVIEW-OPPC-{_now().strftime('%m%d')}",
        "location": "Preview certification lane",
        "report_date": today,
        "prepared_by": _clean(actor.get("name") or actor.get("email")) or "Preview Operator",
        "project_pm_name": "Certification PM",
        "project_pm_email": "cert.pm@example.com",
        "case_owner_name": "Certification PM",
        "case_owner_email": "cert.pm@example.com",
        "weather_summary": "Controlled preview certification run",
        "schedule_delays": "Yes",
        "schedule_delays_notes": "Preview-only SLA and escalation certification path for OPPC case management.",
        "weather_impact": "Yes",
        "general_notes": "Fresh preview certification Daily Report for Operational Case proof-chain verification.",
        "constraints": [
            {"constraint_type": "utility", "hours_impact": 1.0, "notes": "Preview certification utility constraint"},
            {"constraint_type": "weather", "hours_impact": 1.0, "notes": "Preview certification weather impact"},
            {"constraint_type": "other", "hours_impact": 0.5, "notes": "Preview certification task linkage expected"},
        ],
        "production": [
            {"description": "Preview certification operational chain", "quantity": 1, "unit": "EA"},
        ],
        "photos": [],
        "activities": [],
        "materials": [],
        "equipment": [],
        "masci_crews": [],
        "subcontractors": [],
        "visitors": [],
        "certification_record": True,
        "synthetic_record": True,
        "hidden_from_operations": True,
        "email_dispatch_suppressed": True,
        "certification_track_id": "WP-OPPC-14F",
        "certification_run_id": cert_id,
        "certification_release_reason": "Preview-safe Operational Case certification",
        "certification_required_workflows": ["oppc.daily_report_to_oppc", "oppc.operational_case_management"],
        "created_at": _now_iso(),
        "prepared_by_bound": False,
        "prepared_by_identity": None,
    }
    await ensure_doc_id(db, report, "DR", when=report.get("report_date") or report.get("created_at"))
    report["audit_envelope_sha256"] = ""
    await db.daily_reports.insert_one(dict(report))
    control_plane_result = await ingest_daily_report_submission(
        db,
        report=report,
        actor_label=_clean(actor.get("name") or actor.get("email") or actor.get("role")) or "Preview Operator",
    )
    case_result = dict(control_plane_result.get("case_result") or {})
    case_doc = dict(case_result.get("case") or {})
    if not case_doc:
        raise LookupError("Preview certification Daily Report did not produce an Operational Case")
    certification = {
        "id": str(uuid.uuid4()),
        "daily_report_id": report.get("id"),
        "daily_report_doc_id": report.get("doc_id"),
        "case_id": case_doc.get("id"),
        "case_number": case_doc.get("case_number"),
        "created_at": _now_iso(),
        "created_by": {
            "role": _clean(actor.get("role")),
            "name": _clean(actor.get("name") or actor.get("email")),
            "email": _clean(actor.get("email")),
        },
        "status": "daily_report_registered",
    }
    await db[COLLECTION_CASE_CERTIFICATIONS].insert_one(dict(certification))
    await _append_case_history(
        db,
        case_id=case_doc.get("id"),
        event_type="preview_certification_record_created",
        actor=actor,
        note="Fresh preview Daily Report certification record created.",
        details={"daily_report_id": report.get("id"), "daily_report_doc_id": report.get("doc_id")},
    )
    return {
        "certification": certification,
        "daily_report": report,
        "control_plane_result": control_plane_result,
        "case": case_doc,
    }


async def run_case_certification_chain(db, *, actor: Dict[str, Any]) -> Dict[str, Any]:
    created = await create_preview_case_certification_record(db, actor=actor)
    case_doc = dict(created.get("case") or {})
    case_id = _clean(case_doc.get("id"))
    if not case_id:
        raise LookupError("Preview certification case id missing")
    linked = dict(case_doc.get("linked_record_ids") or {})
    initial_comm_ids = list(linked.get("communication_ids") or [])
    if initial_comm_ids:
        await acknowledge_case_communication(
            db,
            case_id=case_id,
            communication_id=initial_comm_ids[0],
            actor=actor,
            note="Preview acknowledgement captured",
        )
    await transition_case(
        db,
        case_id=case_id,
        to_status="UNDER_REVIEW",
        actor=actor,
        reason="Preview certification review started",
    )
    await transition_case(
        db,
        case_id=case_id,
        to_status="INVESTIGATING",
        actor=actor,
        reason="Preview certification investigation started",
    )
    task_result = await create_case_task(
        db,
        case_id=case_id,
        actor=actor,
        title="Preview corrective action",
        description="Validate recovery path, task linkage, and persistence for preview certification.",
        assignee_role="pm",
        priority="High",
        due_minutes=60,
    )
    fresh = await get_case_by_id(db, case_id)
    linked = dict((fresh or {}).get("linked_record_ids") or {})
    task_ids = list(linked.get("task_ids") or [])
    if task_ids:
        task_doc = await db.tasks.find_one({"id": task_ids[-1]}, {"_id": 0})
        if task_doc:
            await task_service.update(
                db,
                task_ids[-1],
                {"status": "Completed", "completion_notes": "Preview corrective action completed"},
                {
                    "role": _clean(actor.get("role")) or "admin",
                    "name": _clean(actor.get("name") or actor.get("email")) or "system",
                    "email": _clean(actor.get("email")),
                },
            )
    await transition_case(
        db,
        case_id=case_id,
        to_status="ACTION_REQUIRED",
        actor=actor,
        reason="Corrective action created",
        resolution_summary="Task-linked corrective path initiated.",
    )
    await transition_case(
        db,
        case_id=case_id,
        to_status="RECOVERY_ACTIVE",
        actor=actor,
        reason="Preview recovery linkage active",
        root_cause="Preview operational variance chain validation",
    )
    await transition_case(
        db,
        case_id=case_id,
        to_status="MONITORING",
        actor=actor,
        reason="Recovery action completed and under monitoring",
    )
    await transition_case(
        db,
        case_id=case_id,
        to_status="PENDING_VERIFICATION",
        actor=actor,
        reason="Awaiting final verification",
        verification_notes="Preview verification step recorded",
    )
    evidence = await capture_case_evidence_package(db, case_id=case_id, actor=actor)
    baseline = await include_case_in_baseline(
        db,
        case_id=case_id,
        actor=actor,
        baseline_name="Operations Control Plane v1",
    )
    await transition_case(
        db,
        case_id=case_id,
        to_status="RESOLVED",
        actor=actor,
        reason="Preview chain resolved",
        resolution_summary="Operational chain reconstructed end-to-end.",
        root_cause="Preview certification operational issue",
    )
    await transition_case(
        db,
        case_id=case_id,
        to_status="CLOSED",
        actor=actor,
        reason="Closure requirements satisfied in preview certification",
        resolution_summary="Evidence captured and baseline inclusion recorded.",
        root_cause="Preview certification operational issue",
    )
    await transition_case(
        db,
        case_id=case_id,
        to_status="REOPENED",
        actor=actor,
        reason="Preview reopening path verified",
    )
    await transition_case(
        db,
        case_id=case_id,
        to_status="UNDER_REVIEW",
        actor=actor,
        reason="Reopened case returned to governed review",
    )
    await transition_case(
        db,
        case_id=case_id,
        to_status="INVESTIGATING",
        actor=actor,
        reason="Reopened case investigating again",
    )
    await transition_case(
        db,
        case_id=case_id,
        to_status="ACTION_REQUIRED",
        actor=actor,
        reason="Reopened case action path revalidated",
    )
    await transition_case(
        db,
        case_id=case_id,
        to_status="RECOVERY_ACTIVE",
        actor=actor,
        reason="Reopened recovery path reactivated",
    )
    await transition_case(
        db,
        case_id=case_id,
        to_status="MONITORING",
        actor=actor,
        reason="Reopened monitoring step completed",
    )
    await transition_case(
        db,
        case_id=case_id,
        to_status="PENDING_VERIFICATION",
        actor=actor,
        reason="Reopened case pending verification",
        verification_notes="Reopen and verify path captured",
    )
    await transition_case(
        db,
        case_id=case_id,
        to_status="RESOLVED",
        actor=actor,
        reason="Reopened case resolved",
        resolution_summary="Reopened case completed for certification chain.",
        root_cause="Preview certification operational issue",
    )
    await transition_case(
        db,
        case_id=case_id,
        to_status="CLOSED",
        actor=actor,
        reason="Reopened closure verified",
        resolution_summary="Case closed after reopening verification.",
        root_cause="Preview certification operational issue",
    )
    duplicate_case = await create_preview_case_certification_record(db, actor=actor)
    duplicate_case_id = _clean((duplicate_case.get("case") or {}).get("id"))
    if duplicate_case_id:
        await transition_case(
            db,
            case_id=duplicate_case_id,
            to_status="DUPLICATE",
            actor=actor,
            reason="Preview duplicate handling verified",
            duplicate_of_case_id=case_id,
        )
        await link_related_case(
            db,
            case_id=case_id,
            related_case_id=duplicate_case_id,
            actor=actor,
            note="Preview related-case linkage created",
        )
    export_row = await export_case_evidence_package(db, case_id=case_id, actor=actor)
    final_case = await get_case_by_id(db, case_id)
    certification_state = "verified_complete" if final_case and _display_status(final_case.get("status")) == "CLOSED" else "not_ready"
    await db[COLLECTION_CASE_CERTIFICATIONS].update_one(
        {"daily_report_id": created.get("daily_report", {}).get("id")},
        {
            "$set": {
                "status": certification_state,
                "final_case_status": (final_case or {}).get("status"),
                "evidence_export_id": export_row.get("id"),
                "baseline_id": baseline.get("id"),
                "completed_at": _now_iso(),
                "duplicate_case_id": duplicate_case_id,
            }
        },
    )
    return {
        "release_determination": "OPERATIONS CONTROL PLANE v1 — VERIFIED COMPLETE" if certification_state == "verified_complete" else "OPERATIONS CONTROL PLANE v1 — NOT READY",
        "preview_daily_report": created.get("daily_report"),
        "primary_case": final_case,
        "duplicate_case_id": duplicate_case_id,
        "task_id": task_result.get("task_id"),
        "evidence_export_id": export_row.get("id"),
        "baseline_id": baseline.get("id"),
        "certification_id": created.get("certification", {}).get("id"),
    }
