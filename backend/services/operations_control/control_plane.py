from __future__ import annotations

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional

from lib.notification_delivery import deliver_notification
from lib.trust_spine import (
    STAGE_AUDIT_WRITTEN,
    STAGE_COMPLETED,
    STAGE_COMPLETED_FOR_ENVIRONMENT,
    STAGE_DELIVERY_CAPTURED_PREVIEW,
    STAGE_NOTIFICATION_QUEUED,
    STAGE_PROVIDER_ACCEPTED,
    STAGE_RECIPIENTS_BUILT,
    STAGE_ROUTING_RESOLVED,
    attach_correlation,
    emit_record_created,
    emit_workflow_stage,
)
from pm_routing import recipients_for_record_async
from routes.tasks_notifications import notification_service
from services.operations_control.registry import (
    build_operations_control_plane_registry,
    get_registered_communication_intent,
    get_registered_escalation_policy,
    get_registered_event,
    get_registered_template,
    get_registered_transport,
    get_registered_workflow,
)
from services.operations_control.case_management import (
    maybe_auto_create_case_from_control_plane_event,
)

COLLECTION_EVENTS = "operations_control_plane_events"
COLLECTION_COMMUNICATIONS = "operations_control_plane_communications"
COLLECTION_BASELINES = "operations_control_plane_baselines"
COLLECTION_EVIDENCE = "operations_control_plane_evidence"
COLLECTION_REGISTRY_SNAPSHOTS = "operations_control_plane_registry_snapshots"
COLLECTION_TRANSPORT_CAPTURES = "operations_control_plane_transport_captures"


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _now().isoformat()


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _severity_to_title(value: str) -> str:
    sev = _clean(value).lower()
    if sev == "critical":
        return "Critical"
    if sev == "warning":
        return "Warning"
    return "Info"


def _project_label(record: Dict[str, Any]) -> str:
    return _clean(record.get("project_name")) or _clean(record.get("project_number")) or "—"


def _template_fields(record: Dict[str, Any], communication: Dict[str, Any]) -> Dict[str, str]:
    return {
        "project_label": _project_label(record),
        "doc_id": _clean(record.get("doc_id")) or _clean(record.get("id")) or "record",
        "report_date": _clean(record.get("report_date")) or _clean(record.get("date")) or "—",
        "project_number": _clean(record.get("project_number")) or "—",
        "communication_id": _clean(communication.get("id")),
        "event_id": _clean(communication.get("source_event_id") or communication.get("source_event_type_id")),
    }


def _render_template(template_id: str, record: Dict[str, Any], communication: Dict[str, Any]) -> Dict[str, str]:
    template = get_registered_template(template_id)
    fields = _template_fields(record, communication)
    title = str(template.get("title_template") or "").format(**fields)[:200]
    message = str(template.get("message_template") or "").format(**fields)[:2000]
    note = str(template.get("email_note") or "").format(**fields)
    return {"title": title, "message": message, "email_note": note, "template_id": template_id}


def _dedupe_emails(values: Iterable[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for raw in values:
        email = _clean(raw).lower()
        if not email or "@" not in email or email in seen:
            continue
        seen.add(email)
        out.append(email)
    return out


async def ensure_control_plane_indexes(db) -> None:
    await db[COLLECTION_EVENTS].create_index("id", unique=True)
    await db[COLLECTION_EVENTS].create_index([("event_type_id", 1), ("created_at", -1)])
    await db[COLLECTION_EVENTS].create_index([("workflow_id", 1), ("created_at", -1)])
    await db[COLLECTION_EVENTS].create_index([("record_id", 1), ("created_at", -1)])
    await db[COLLECTION_COMMUNICATIONS].create_index("id", unique=True)
    await db[COLLECTION_COMMUNICATIONS].create_index([("source_event_id", 1), ("created_at", -1)])
    await db[COLLECTION_COMMUNICATIONS].create_index([("workflow_id", 1), ("status", 1), ("created_at", -1)])
    await db[COLLECTION_COMMUNICATIONS].create_index([("ack_status", 1), ("ack_due_at", 1)])
    await db[COLLECTION_COMMUNICATIONS].create_index([("record_id", 1), ("created_at", -1)])
    await db[COLLECTION_BASELINES].create_index("id", unique=True)
    await db[COLLECTION_BASELINES].create_index([("baseline_name", 1), ("created_at", -1)])
    await db[COLLECTION_EVIDENCE].create_index("id", unique=True)
    await db[COLLECTION_EVIDENCE].create_index([("workflow_id", 1), ("created_at", -1)])
    await db[COLLECTION_REGISTRY_SNAPSHOTS].create_index([("registry_hash", 1)], unique=True)
    await db[COLLECTION_TRANSPORT_CAPTURES].create_index([("communication_id", 1), ("transport_id", 1)])


async def ensure_registry_snapshot(db) -> Dict[str, Any]:
    snapshot = build_operations_control_plane_registry()
    row = {
        "registry_hash": snapshot.get("registry_hash"),
        "version": snapshot.get("version"),
        "baseline_name": snapshot.get("baseline_name"),
        "snapshot": snapshot,
        "captured_at": _now_iso(),
    }
    await db[COLLECTION_REGISTRY_SNAPSHOTS].update_one(
        {"registry_hash": row["registry_hash"]},
        {"$setOnInsert": row},
        upsert=True,
    )
    return row


async def get_latest_registry_snapshot(db) -> Optional[Dict[str, Any]]:
    return await db[COLLECTION_REGISTRY_SNAPSHOTS].find_one({}, {"_id": 0}, sort=[("captured_at", -1)])


async def build_baseline_snapshot(db, *, baseline_name: str, actor_label: str) -> Dict[str, Any]:
    registry = build_operations_control_plane_registry()
    counts = {
        "events": await db[COLLECTION_EVENTS].count_documents({}),
        "communications": await db[COLLECTION_COMMUNICATIONS].count_documents({}),
        "captured_transports": await db[COLLECTION_TRANSPORT_CAPTURES].count_documents({}),
    }
    baseline = {
        "id": str(uuid.uuid4()),
        "baseline_name": baseline_name,
        "created_at": _now_iso(),
        "created_by": actor_label,
        "registry_hash": registry.get("registry_hash"),
        "registry_version": registry.get("version"),
        "counts": counts,
        "principles": list(registry.get("principles") or []),
        "workflow_ids": sorted((registry.get("workflows") or {}).keys()),
        "event_ids": sorted((registry.get("event_catalog") or {}).keys()),
        "communication_intent_ids": sorted((registry.get("communication_intents") or {}).keys()),
        "transport_ids": sorted((registry.get("transport_providers") or {}).keys()),
        "status": "captured",
    }
    await db[COLLECTION_BASELINES].insert_one(dict(baseline))
    return baseline


async def list_recent_baselines(db, limit: int = 10) -> List[Dict[str, Any]]:
    cur = db[COLLECTION_BASELINES].find({}, {"_id": 0}).sort("created_at", -1).limit(limit)
    return [row async for row in cur]


async def build_readiness_evidence_package(
    db,
    *,
    workflow_id: str,
    actor_label: str,
    record_id: Optional[str] = None,
) -> Dict[str, Any]:
    query: Dict[str, Any] = {"workflow_id": workflow_id}
    if record_id:
        query["record_id"] = record_id
    event_rows = await list_recent_control_plane_events(db, workflow_id=workflow_id, limit=10)
    communication_rows = await list_recent_communications(db, workflow_id=workflow_id, limit=10)
    baseline_rows = await list_recent_baselines(db, limit=3)
    capture_query: Dict[str, Any] = {}
    if record_id:
        capture_query["record_id"] = record_id
    capture_rows = [
        row async for row in db[COLLECTION_TRANSPORT_CAPTURES].find(capture_query, {"_id": 0}).sort("created_at", -1).limit(10)
    ]
    trust_query: Dict[str, Any] = {"workflow": "oppc-daily-report-proof-chain"}
    if record_id:
        trust_query["record_id"] = record_id
    trust_rows = [
        row async for row in db.trust_spine_events.find(trust_query, {"_id": 0}).sort("ts", -1).limit(20)
    ]
    evidence = {
        "id": str(uuid.uuid4()),
        "workflow_id": workflow_id,
        "record_id": record_id,
        "created_at": _now_iso(),
        "created_by": actor_label,
        "registry_hash": build_operations_control_plane_registry().get("registry_hash"),
        "event_count": len(event_rows),
        "communication_count": len(communication_rows),
        "capture_count": len(capture_rows),
        "baseline_ids": [row.get("id") for row in baseline_rows if row.get("id")],
        "events": event_rows,
        "communications": communication_rows,
        "transport_captures": capture_rows,
        "trust_spine_tail": trust_rows,
        "status": "captured",
    }
    await db[COLLECTION_EVIDENCE].insert_one(dict(evidence))
    return evidence


async def list_recent_evidence_packages(db, workflow_id: Optional[str] = None, limit: int = 10) -> List[Dict[str, Any]]:
    query: Dict[str, Any] = {}
    if workflow_id:
        query["workflow_id"] = workflow_id
    cur = db[COLLECTION_EVIDENCE].find(query, {"_id": 0}).sort("created_at", -1).limit(limit)
    return [row async for row in cur]


async def list_recent_control_plane_events(db, workflow_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    query: Dict[str, Any] = {}
    if workflow_id:
        query["workflow_id"] = workflow_id
    cur = db[COLLECTION_EVENTS].find(query, {"_id": 0}).sort("created_at", -1).limit(limit)
    return [row async for row in cur]


async def list_recent_communications(db, workflow_id: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    query: Dict[str, Any] = {}
    if workflow_id:
        query["workflow_id"] = workflow_id
    cur = db[COLLECTION_COMMUNICATIONS].find(query, {"_id": 0}).sort("created_at", -1).limit(limit)
    return [row async for row in cur]


async def get_communication_by_id(db, communication_id: str) -> Optional[Dict[str, Any]]:
    return await db[COLLECTION_COMMUNICATIONS].find_one({"id": communication_id}, {"_id": 0})


async def acknowledge_communication(
    db,
    *,
    communication_id: str,
    actor: Dict[str, Any],
    note: str = "",
) -> Optional[Dict[str, Any]]:
    now_iso = _now_iso()
    ack_by = {
        "role": _clean(actor.get("role")) or "unknown",
        "user_id": _clean(actor.get("id") or actor.get("user_id")),
        "name": _clean(actor.get("name") or actor.get("email")) or "system",
    }
    result = await db[COLLECTION_COMMUNICATIONS].update_one(
        {"id": communication_id},
        {
            "$set": {
                "ack_status": "acknowledged",
                "status": "acknowledged",
                "acknowledged_at": now_iso,
                "acknowledged_by": ack_by,
                "closed_at": now_iso,
                "closure_reason": _clean(note) or "acknowledged",
            },
            "$push": {
                "audit_log": {
                    "at": now_iso,
                    "action": "acknowledged",
                    "actor": ack_by,
                    "note": _clean(note) or None,
                }
            },
        },
    )
    if result.matched_count == 0:
        return None
    return await get_communication_by_id(db, communication_id)


async def run_due_escalations(db) -> Dict[str, Any]:
    now_iso = _now_iso()
    query = {
        "ack_required": True,
        "ack_status": "pending",
        "ack_due_at": {"$lte": now_iso},
        "escalated_at": None,
        "escalation_policy_id": {"$exists": True, "$ne": None},
    }
    escalated_ids: List[str] = []
    cur = db[COLLECTION_COMMUNICATIONS].find(query, {"_id": 0}).limit(50)
    async for communication in cur:
        policy_id = _clean(communication.get("escalation_policy_id"))
        if not policy_id:
            continue
        try:
            policy = get_registered_escalation_policy(policy_id)
            overdue_event_id = _clean(policy.get("overdue_event_id"))
            if not overdue_event_id:
                continue
            await emit_operational_event(
                db,
                event_id=overdue_event_id,
                record={
                    **(communication.get("record_snapshot") or {}),
                    "id": communication.get("record_id") or (communication.get("record_snapshot") or {}).get("id"),
                    "doc_id": communication.get("record_doc_id") or (communication.get("record_snapshot") or {}).get("doc_id"),
                    "project_number": communication.get("project_number") or (communication.get("record_snapshot") or {}).get("project_number"),
                    "project_name": communication.get("project_name") or (communication.get("record_snapshot") or {}).get("project_name"),
                },
                actor_label="system-escalation",
                context={
                    "communication_id": communication.get("id"),
                    "source_event_id": communication.get("source_event_id"),
                    "communication": communication,
                },
            )
            await db[COLLECTION_COMMUNICATIONS].update_one(
                {"id": communication.get("id")},
                {
                    "$set": {
                        "status": "escalated",
                        "ack_status": "overdue",
                        "escalated_at": now_iso,
                    },
                    "$push": {
                        "audit_log": {
                            "at": now_iso,
                            "action": "escalated",
                            "actor": {"role": "system", "name": "system-escalation"},
                            "policy_id": policy_id,
                        }
                    },
                },
            )
            escalated_ids.append(str(communication.get("id") or ""))
        except Exception:
            continue
    return {"ok": True, "checked_at": now_iso, "escalated_count": len(escalated_ids), "escalated_ids": escalated_ids}


async def _resolve_recipients(
    db,
    *,
    strategy_id: str,
    record: Dict[str, Any],
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    ctx = context or {}
    if strategy_id == "project_pm_distribution":
        dist = await recipients_for_record_async(db, record, "daily-report")
        return {
            "strategy_id": strategy_id,
            "recipient_roles": ["pm"],
            "to": _dedupe_emails(dist.get("to") or []),
            "cc": _dedupe_emails(dist.get("cc") or []),
            "all": _dedupe_emails(dist.get("all") or []),
            "resolution": {"pm_name": dist.get("pm_name"), "pm_email": dist.get("pm_email")},
        }
    if strategy_id == "daily_report_review_board":
        dist = await recipients_for_record_async(db, record, "daily-report")
        review_board = _dedupe_emails(list(dist.get("all") or []))
        return {
            "strategy_id": strategy_id,
            "recipient_roles": ["admin", "pm", "safety"],
            "to": review_board,
            "cc": [],
            "all": review_board,
            "resolution": {"review_board": review_board},
        }
    if strategy_id == "ops_admin_escalation":
        prior = ctx.get("communication") or {}
        original = list(prior.get("email_recipients") or [])
        escalation_to = _dedupe_emails(original)
        if not escalation_to:
            dist = await recipients_for_record_async(db, record, "daily-report")
            escalation_to = _dedupe_emails(list(dist.get("all") or []))
        return {
            "strategy_id": strategy_id,
            "recipient_roles": ["admin"],
            "to": escalation_to,
            "cc": [],
            "all": escalation_to,
            "resolution": {"escalated_from": _clean(prior.get("id")) or None},
        }
    if strategy_id == "case_primary_owner_and_admin":
        owner_email = _clean(record.get("case_owner_email") or record.get("owner_email")).lower()
        emails = _dedupe_emails([owner_email]) if owner_email else []
        return {
            "strategy_id": strategy_id,
            "recipient_roles": [record.get("assigned_role") or "pm", "admin"],
            "to": emails,
            "cc": [],
            "all": emails,
            "resolution": {
                "case_owner_name": _clean(record.get("case_owner_name")),
                "case_owner_email": owner_email,
            },
        }
    if strategy_id == "case_escalation_path":
        owner_email = _clean(record.get("case_owner_email") or record.get("owner_email")).lower()
        emails = _dedupe_emails([owner_email]) if owner_email else []
        return {
            "strategy_id": strategy_id,
            "recipient_roles": ["admin", record.get("assigned_role") or "pm"],
            "to": emails,
            "cc": [],
            "all": emails,
            "resolution": {
                "escalation_count": int((record.get("escalation_state") or {}).get("escalation_count") or 0),
                "case_owner_email": owner_email,
            },
        }
    return {
        "strategy_id": strategy_id,
        "recipient_roles": [],
        "to": [],
        "cc": [],
        "all": [],
        "resolution": {"reason": "unknown_strategy"},
    }


async def _materialize_in_app_notification(
    db,
    *,
    event_doc: Dict[str, Any],
    communication: Dict[str, Any],
    rendered: Dict[str, str],
    recipient_roles: List[str],
) -> List[str]:
    created_ids: List[str] = []
    severity = _severity_to_title(event_doc.get("severity") or "info")
    for role in recipient_roles:
        notif_id = await notification_service.fanout(
            db,
            {
                "event_id": event_doc.get("id"),
                "type": event_doc.get("event_type_id"),
                "title": rendered.get("title"),
                "message": rendered.get("message"),
                "severity": severity,
                "recipient_role": role,
                "linked_source_module": "operations_control.control_plane",
                "linked_source_record_id": communication.get("record_id"),
                "linked_project_number": communication.get("project_number") or None,
                "linked_request_id": communication.get("id"),
                "email_enabled": False,
                "pm_broadcast": role == "pm" and not bool(communication.get("project_number")),
            },
        )
        if notif_id:
            created_ids.append(str(notif_id))
    return created_ids


async def _deliver_email_transport(
    db,
    *,
    workflow: Dict[str, Any],
    event_doc: Dict[str, Any],
    communication: Dict[str, Any],
    rendered: Dict[str, str],
    recipients: List[str],
) -> Dict[str, Any]:
    html = (
        "<div style='font-family:Arial,sans-serif;line-height:1.5;color:#0f172a;'>"
        f"<h2 style='margin:0 0 12px 0;font-size:18px;'>{rendered.get('title')}</h2>"
        f"<p style='margin:0 0 12px 0;font-size:14px;'>{rendered.get('message')}</p>"
        f"<p style='margin:0;font-size:12px;color:#475569;'>{rendered.get('email_note')}</p>"
        "</div>"
    )
    return await deliver_notification(
        db=db,
        workflow=workflow.get("trust_workflow") or workflow.get("id") or "operations-control-plane",
        correlation_id=communication.get("correlation_id") or attach_correlation(communication),
        record_id=communication.get("record_id") or communication.get("id") or "",
        recipients=recipients,
        subject=rendered.get("title") or "Operational communication",
        html=html,
        metadata={
            "event_id": event_doc.get("id"),
            "event_type_id": event_doc.get("event_type_id"),
            "communication_id": communication.get("id"),
            "workflow_id": communication.get("workflow_id"),
        },
    )


async def emit_operational_event(
    db,
    *,
    event_id: str,
    record: Dict[str, Any],
    actor_label: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    registry = build_operations_control_plane_registry()
    event_def = get_registered_event(event_id)
    workflow = get_registered_workflow(event_def["workflow_id"])
    record_ref = {
        "id": _clean(record.get("id")) or str(uuid.uuid4()),
        "doc_id": _clean(record.get("doc_id")) or _clean(record.get("id")) or "",
        "project_number": _clean(record.get("project_number")),
    }
    cid = attach_correlation(record_ref)
    await emit_record_created(
        db,
        workflow=workflow.get("trust_workflow") or workflow.get("id") or event_def["workflow_id"],
        record=record_ref,
        module="services/operations_control/control_plane.py:emit_operational_event",
        event_name=event_id,
    )

    event_doc = {
        "id": str(uuid.uuid4()),
        "event_type_id": event_id,
        "workflow_id": event_def["workflow_id"],
        "workflow_title": workflow.get("title"),
        "record_id": record_ref["id"],
        "record_doc_id": record_ref["doc_id"],
        "project_number": record_ref["project_number"],
        "severity": event_def.get("severity") or "info",
        "operational_intent": event_def.get("operational_intent") or "communication_required",
        "communication_required": bool(event_def.get("communication_intent_ids")),
        "communication_intent_ids": list(event_def.get("communication_intent_ids") or []),
        "actor_label": actor_label,
        "context": dict(context or {}),
        "record_snapshot": {
            "id": _clean(record.get("id")),
            "doc_id": _clean(record.get("doc_id")),
            "project_number": _clean(record.get("project_number")),
            "project_name": _clean(record.get("project_name")),
            "report_date": _clean(record.get("report_date")),
            "lifecycle_state": _clean(record.get("lifecycle_state")),
        },
        "registry_hash": registry.get("registry_hash"),
        "correlation_id": cid,
        "created_at": _now_iso(),
        "status": "registered",
    }
    await db[COLLECTION_EVENTS].insert_one(dict(event_doc))

    await emit_workflow_stage(
        db,
        workflow=workflow.get("trust_workflow") or workflow.get("id") or event_def["workflow_id"],
        stage=STAGE_ROUTING_RESOLVED,
        record=record_ref,
        module="services/operations_control/control_plane.py:event_registered",
        status="ok",
        event_name=event_doc.get("event_type_id"),
    )

    communication_rows: List[Dict[str, Any]] = []
    for intent_id in event_doc["communication_intent_ids"]:
        communication_rows.append(
            await create_communication_from_event(
                db,
                event_doc=event_doc,
                communication_intent_id=intent_id,
                record=record,
            )
        )

    await db[COLLECTION_EVENTS].update_one(
        {"id": event_doc["id"]},
        {
            "$set": {
                "status": "processed",
                "communication_ids": [row.get("id") for row in communication_rows],
                "processed_at": _now_iso(),
            }
        },
    )

    await emit_workflow_stage(
        db,
        workflow=workflow.get("trust_workflow") or workflow.get("id") or event_def["workflow_id"],
        stage=STAGE_COMPLETED,
        record=record_ref,
        module="services/operations_control/control_plane.py:event_processed",
        status="ok",
        event_name=event_doc.get("event_type_id"),
    )
    case_result = None
    if _clean(event_id) == "oppc.daily_report.submitted":
        try:
            case_result = await maybe_auto_create_case_from_control_plane_event(
                db,
                event_doc=event_doc,
                record=record,
                actor_label=actor_label,
            )
        except Exception:
            case_result = {
                "created": False,
                "decision": {"outcome": "failed", "reason": "case_auto_create_failed"},
            }
    return {
        "event": event_doc,
        "communications": communication_rows,
        "case_result": case_result,
    }


async def create_communication_from_event(
    db,
    *,
    event_doc: Dict[str, Any],
    communication_intent_id: str,
    record: Dict[str, Any],
) -> Dict[str, Any]:
    workflow = get_registered_workflow(event_doc["workflow_id"])
    intent = get_registered_communication_intent(communication_intent_id)
    rendered = _render_template(
        intent["template_id"],
        record,
        {
            "id": "preview",
            "source_event_id": event_doc["id"],
            "source_event_type_id": event_doc["event_type_id"],
        },
    )
    recipients = await _resolve_recipients(
        db,
        strategy_id=intent.get("recipient_strategy") or "",
        record=record,
        context=event_doc.get("context") or {},
    )
    transport_ids = [str(x) for x in (intent.get("transport_ids") or [])]
    ack_required = bool(intent.get("ack_required"))
    ack_sla_minutes = int(intent.get("ack_sla_minutes") or 0)
    if ack_required and record.get("preview_ack_sla_minutes"):
        try:
            ack_sla_minutes = max(1, int(record.get("preview_ack_sla_minutes")))
        except Exception:
            ack_sla_minutes = int(intent.get("ack_sla_minutes") or 0)
    created_at = _now()
    communication = {
        "id": str(uuid.uuid4()),
        "workflow_id": event_doc["workflow_id"],
        "workflow_title": workflow.get("title"),
        "source_event_id": event_doc.get("id"),
        "source_event_type_id": event_doc.get("event_type_id"),
        "event_row_id": event_doc.get("id"),
        "record_id": _clean(record.get("id")),
        "record_doc_id": _clean(record.get("doc_id")) or _clean(record.get("id")),
        "project_number": _clean(record.get("project_number")),
        "project_name": _clean(record.get("project_name")),
        "communication_intent_id": communication_intent_id,
        "policy_evaluator": intent.get("policy_evaluator"),
        "template_id": intent.get("template_id"),
        "transport_ids": transport_ids,
        "recipient_strategy": intent.get("recipient_strategy"),
        "recipient_roles": list(recipients.get("recipient_roles") or []),
        "email_recipients": list(recipients.get("all") or []),
        "resolution": recipients.get("resolution") or {},
        "ack_required": ack_required,
        "ack_sla_minutes": ack_sla_minutes,
        "ack_status": "pending" if ack_required else "not_required",
        "ack_due_at": (created_at + timedelta(minutes=ack_sla_minutes)).isoformat() if ack_required and ack_sla_minutes > 0 else None,
        "acknowledged_at": None,
        "acknowledged_by": None,
        "escalation_policy_id": intent.get("escalation_policy_id"),
        "escalated_at": None,
        "closure_mode": intent.get("closure_mode") or "ack_or_escalate",
        "status": "routing_resolved",
        "message": rendered.get("message"),
        "title": rendered.get("title"),
        "registry_hash": build_operations_control_plane_registry().get("registry_hash"),
        "correlation_id": event_doc.get("correlation_id"),
        "created_at": created_at.isoformat(),
        "record_snapshot": {
            "id": _clean(record.get("id")),
            "doc_id": _clean(record.get("doc_id")),
            "project_number": _clean(record.get("project_number")),
            "project_name": _clean(record.get("project_name")),
            "report_date": _clean(record.get("report_date")),
            "lifecycle_state": _clean(record.get("lifecycle_state")),
        },
        "transport_results": [],
        "audit_log": [
            {
                "at": created_at.isoformat(),
                "action": "created",
                "actor": {"role": "system", "name": "operations-control-plane"},
                "communication_intent_id": communication_intent_id,
            }
        ],
        "closed_at": None,
        "closure_reason": None,
    }
    await db[COLLECTION_COMMUNICATIONS].insert_one(dict(communication))

    record_ref = {
        "id": communication["record_id"] or communication["id"],
        "doc_id": communication["record_doc_id"] or communication["record_id"] or communication["id"],
        "project_number": communication["project_number"],
        "_trust_cid": communication["correlation_id"],
    }

    await emit_workflow_stage(
        db,
        workflow=workflow.get("trust_workflow") or workflow.get("id") or event_doc["workflow_id"],
        stage=STAGE_RECIPIENTS_BUILT,
        record=record_ref,
        module="services/operations_control/control_plane.py:recipients",
        status="ok" if recipients.get("all") else "failed",
        failure_reason=None if recipients.get("all") else "no recipients resolved",
        event_name=event_doc.get("event_type_id"),
    )

    results: List[Dict[str, Any]] = []
    notification_ids: List[str] = []
    for transport_id in transport_ids:
        transport = get_registered_transport(transport_id)
        transport_result: Dict[str, Any] = {
            "transport_id": transport_id,
            "channel": transport.get("channel"),
            "provider": transport.get("provider"),
            "attempted_at": _now_iso(),
        }
        if transport.get("channel") == "in_app":
            notification_ids = await _materialize_in_app_notification(
                db,
                event_doc=event_doc,
                communication=communication,
                rendered=rendered,
                recipient_roles=list(recipients.get("recipient_roles") or []),
            )
            transport_result.update(
                {
                    "status": "materialized",
                    "notification_ids": notification_ids,
                    "provider_called": False,
                    "provider_accepted": False,
                }
            )
        elif transport.get("channel") == "email":
            await emit_workflow_stage(
                db,
                workflow=workflow.get("trust_workflow") or workflow.get("id") or event_doc["workflow_id"],
                stage=STAGE_NOTIFICATION_QUEUED,
                record=record_ref,
                module="services/operations_control/control_plane.py:email_transport",
                status="ok",
                event_name=event_doc.get("event_type_id"),
            )
            delivery = await _deliver_email_transport(
                db,
                workflow=workflow,
                event_doc=event_doc,
                communication=communication,
                rendered=rendered,
                recipients=list(recipients.get("all") or []),
            )
            transport_result.update(delivery)
            capture_row = {
                "id": str(uuid.uuid4()),
                "communication_id": communication["id"],
                "source_event_id": event_doc.get("id"),
                "source_event_type_id": event_doc.get("event_type_id"),
                "transport_id": transport_id,
                "record_id": communication["record_id"],
                "created_at": _now_iso(),
                "delivery": delivery,
            }
            await db[COLLECTION_TRANSPORT_CAPTURES].insert_one(capture_row)
            if delivery.get("notification_state") == "captured_preview":
                await emit_workflow_stage(
                    db,
                    workflow=workflow.get("trust_workflow") or workflow.get("id") or event_doc["workflow_id"],
                    stage=STAGE_DELIVERY_CAPTURED_PREVIEW,
                    record=record_ref,
                    module="services/operations_control/control_plane.py:email_capture",
                    status="ok",
                    event_name=event_doc.get("event_type_id"),
                )
                await emit_workflow_stage(
                    db,
                    workflow=workflow.get("trust_workflow") or workflow.get("id") or event_doc["workflow_id"],
                    stage=STAGE_COMPLETED_FOR_ENVIRONMENT,
                    record=record_ref,
                    module="services/operations_control/control_plane.py:email_capture",
                    status="ok",
                    event_name=event_doc.get("event_type_id"),
                )
            else:
                await emit_workflow_stage(
                    db,
                    workflow=workflow.get("trust_workflow") or workflow.get("id") or event_doc["workflow_id"],
                    stage=STAGE_PROVIDER_ACCEPTED,
                    record=record_ref,
                    module="services/operations_control/control_plane.py:email_provider",
                    status="ok" if delivery.get("provider_accepted") else "failed",
                    failure_reason=None if delivery.get("provider_accepted") else _clean(delivery.get("failure_reason")) or "provider_not_accepted",
                    event_name=event_doc.get("event_type_id"),
                )
        results.append(transport_result)

    overall_status = "awaiting_ack" if ack_required else "delivered"
    if any(r.get("notification_state") == "captured_preview" for r in results):
        overall_status = "captured_preview"
    if any(r.get("provider_accepted") for r in results):
        overall_status = "delivered"
    if any(r.get("status") == "materialized" for r in results) and overall_status == "awaiting_ack":
        overall_status = "awaiting_ack"

    await db[COLLECTION_COMMUNICATIONS].update_one(
        {"id": communication["id"]},
        {
            "$set": {
                "status": overall_status,
                "transport_results": results,
                "notification_ids": notification_ids,
                "last_updated_at": _now_iso(),
            },
            "$push": {
                "audit_log": {
                    "at": _now_iso(),
                    "action": "transport_executed",
                    "actor": {"role": "system", "name": "operations-control-plane"},
                    "transports": [row.get("transport_id") for row in results],
                }
            },
        },
    )

    await emit_workflow_stage(
        db,
        workflow=workflow.get("trust_workflow") or workflow.get("id") or event_doc["workflow_id"],
        stage=STAGE_AUDIT_WRITTEN,
        record=record_ref,
        module="services/operations_control/control_plane.py:audit",
        status="ok",
        event_name=event_doc.get("event_type_id"),
    )

    return {
        **communication,
        "status": overall_status,
        "transport_results": results,
        "notification_ids": notification_ids,
        "rendered": rendered,
    }


async def ingest_daily_report_submission(
    db,
    *,
    report: Dict[str, Any],
    actor_label: str,
) -> Dict[str, Any]:
    return await emit_operational_event(
        db,
        event_id="oppc.daily_report.submitted",
        record=report,
        actor_label=actor_label,
    )


async def ingest_daily_report_pending_review(
    db,
    *,
    report: Dict[str, Any],
    actor_label: str,
) -> Dict[str, Any]:
    return await emit_operational_event(
        db,
        event_id="oppc.daily_report.pending_review",
        record=report,
        actor_label=actor_label,
    )
