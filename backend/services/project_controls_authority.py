from __future__ import annotations

import hashlib
import re
from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from services.cost_codes.foundation import (
    build_planning_lifecycle_snapshot,
    build_planning_readiness,
    load_project_assignments,
)
from services.cost_codes.schedule_engine import build_schedule_snapshot


COLL_WORK_TYPES = "enterprise_work_type_registry"
COLL_PAY_ITEMS = "project_pay_item_registry"
COLL_MAPPINGS = "project_pay_item_work_type_mappings"
COLL_REVIEW = "project_controls_review_queue"
COLL_LOOKAHEAD = "project_controls_lookaheads"
COLL_LIFECYCLE = "project_controls_project_lifecycle"
COLL_CONFIRMED_CREWS = "project_controls_confirmed_crews"
COLL_CREW_OBSERVATIONS = "project_controls_crew_observations"
COLL_WORK_LEDGER = "project_controls_work_ledger"
COLL_AUDIT = "project_controls_authority_audit"
COLL_RUNS = "project_controls_authority_runs"

PROJECT_LIFECYCLE_STATES = [
    "Proposal",
    "Awarded",
    "Preconstruction",
    "Active",
    "Substantial Completion",
    "Final Completion",
    "Closed",
    "Archived",
]

DEFAULT_WORK_TYPES = [
    {"code": "CLEARING", "name": "Clearing", "category": "Site Preparation", "keywords": ["clear", "clearing", "grub", "demolition", "demo"]},
    {"code": "EARTHWORK", "name": "Earthwork", "category": "Grading", "keywords": ["earth", "grading", "grade", "embankment", "excavation", "fill"]},
    {"code": "DRAINAGE", "name": "Drainage", "category": "Utilities", "keywords": ["drain", "pipe", "storm", "culvert", "inlet", "manhole"]},
    {"code": "ASPHALT", "name": "Asphalt", "category": "Paving", "keywords": ["asphalt", "surface", "lift", "pave"]},
    {"code": "MILLING", "name": "Milling", "category": "Paving", "keywords": ["mill", "milling"]},
    {"code": "BASE", "name": "Base", "category": "Paving", "keywords": ["base", "limerock", "aggregate base"]},
    {"code": "CONCRETE_CURB", "name": "Concrete Curb", "category": "Concrete", "keywords": ["curb", "gutter"]},
    {"code": "SIDEWALK", "name": "Sidewalk", "category": "Concrete", "keywords": ["sidewalk", "pedestrian"]},
    {"code": "PIPE", "name": "Pipe", "category": "Utilities", "keywords": ["pipe", "storm pipe", "water main", "sanitary"]},
    {"code": "STRUCTURES", "name": "Structures", "category": "Structures", "keywords": ["structure", "retaining", "wall", "bridge"]},
    {"code": "STRIPING", "name": "Striping", "category": "Finishes", "keywords": ["striping", "thermo", "paint"]},
    {"code": "MOT", "name": "Maintenance of Traffic", "category": "Traffic Control", "keywords": ["mot", "traffic control", "maintenance of traffic"]},
    {"code": "ELECTRICAL", "name": "Electrical", "category": "Utilities", "keywords": ["electrical", "signal", "lighting", "conduit"]},
    {"code": "LANDSCAPING", "name": "Landscaping", "category": "Finishes", "keywords": ["landscaping", "sod", "irrigation", "planting"]},
    {"code": "CONCRETE_FLATWORK", "name": "Concrete Flatwork", "category": "Concrete", "keywords": ["concrete", "slab", "flatwork", "driveway"]},
]

EVENT_CONTRACTS = [
    {
        "event_key": "project_pay_item.created",
        "producer": "project_controls_authority",
        "authority_owner": "project_pay_item_registry",
        "consumers": ["pm_project_controls", "work_ledger", "operator_audit"],
        "idempotency_key": "project_number:pay_item_id:version",
        "operator_visible_consequence": "Pay item appears in PM project controls.",
    },
    {
        "event_key": "project_pay_item.mapping_review_required",
        "producer": "project_controls_authority",
        "authority_owner": "project_controls_review_queue",
        "consumers": ["admin_project_controls", "pm_project_controls"],
        "idempotency_key": "project_number:pay_item_id:review_type",
        "operator_visible_consequence": "Mapping needs review before it is treated as governed.",
    },
    {
        "event_key": "daily_report.work_blocks_derived",
        "producer": "daily_reports",
        "authority_owner": "daily_reports",
        "consumers": ["work_ledger", "pm_project_controls", "crew_intelligence"],
        "idempotency_key": "report_id:work_blocks_version",
        "operator_visible_consequence": "Work blocks become visible in the report and PM views.",
    },
    {
        "event_key": "crew_pattern.observed",
        "producer": "crew_intelligence",
        "authority_owner": "project_controls_crew_observations",
        "consumers": ["pm_project_controls", "admin_project_controls"],
        "idempotency_key": "project_number:source_record_id",
        "operator_visible_consequence": "Crew suggestion becomes explainable and reviewable.",
    },
    {
        "event_key": "crew.confirmed",
        "producer": "crew_intelligence",
        "authority_owner": "project_controls_confirmed_crews",
        "consumers": ["pm_project_controls", "daily_reports"],
        "idempotency_key": "project_number:crew_id:version",
        "operator_visible_consequence": "Confirmed crew becomes selectable and historically traceable.",
    },
    {
        "event_key": "lookahead.published",
        "producer": "project_controls_authority",
        "authority_owner": "project_controls_lookaheads",
        "consumers": ["pm_project_controls", "monday_review"],
        "idempotency_key": "project_number:lookahead_id:published_at",
        "operator_visible_consequence": "Two-week lookahead is visible as the PM working plan.",
    },
    {
        "event_key": "project.lifecycle_changed",
        "producer": "project_controls_authority",
        "authority_owner": "project_controls_project_lifecycle",
        "consumers": ["pm_project_controls", "admin_project_controls", "operator_audit"],
        "idempotency_key": "project_number:lifecycle_version",
        "operator_visible_consequence": "Project lifecycle and archive state change without deleting history.",
    },
]


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _norm(value: Any) -> str:
    return re.sub(r"[^a-z0-9]+", "-", _clean(value).lower()).strip("-")


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value in (None, ""):
            return default
        return float(value)
    except (TypeError, ValueError):
        return default


def _to_int(value: Any, default: int = 0) -> int:
    try:
        if value in (None, ""):
            return default
        return int(round(float(value)))
    except (TypeError, ValueError):
        return default


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _sanitize(val) for key, val in value.items() if key != "_id"}
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _fingerprint(parts: List[str]) -> str:
    payload = "::".join(_clean(part) for part in parts)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]


def _actor_label(actor: Optional[Dict[str, Any]]) -> str:
    row = actor or {}
    return _clean(row.get("email") or row.get("name") or row.get("id") or row.get("user_id") or "system") or "system"


def _status(value: Any, *, allowed: List[str], default: str) -> str:
    text = _clean(value)
    if not text:
        return default
    for item in allowed:
        if text.lower() == item.lower():
            return item
    raise ValueError(f"unsupported_status:{text}")


def _work_type_doc(seed: Dict[str, Any], existing: Optional[Dict[str, Any]] = None, actor: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    now = _utcnow()
    row = dict(existing or {})
    code = _clean(seed.get("code") or row.get("code"))
    if not code:
        raise ValueError("work_type_code_required")
    work_type_id = row.get("work_type_id") or f"work-type:{_norm(code)}"
    return {
        "work_type_id": work_type_id,
        "code": code,
        "name": _clean(seed.get("name") or row.get("name") or code.title()),
        "description": _clean(seed.get("description") or row.get("description") or seed.get("name") or row.get("name") or ""),
        "category": _clean(seed.get("category") or row.get("category") or "General"),
        "keywords": sorted({item for item in [_norm(x) for x in (seed.get("keywords") or row.get("keywords") or [])] if item}),
        "status": _status(seed.get("status") or row.get("status") or "active", allowed=["active", "inactive", "archived"], default="active"),
        "governance_owner": "enterprise_work_type_registry",
        "created_at": row.get("created_at") or now,
        "created_by": row.get("created_by") or _actor_label(actor),
        "updated_at": now,
        "updated_by": _actor_label(actor),
        "effective_start": _clean(seed.get("effective_start") or row.get("effective_start") or now),
        "effective_end": _clean(seed.get("effective_end") or row.get("effective_end") or ""),
        "source": _clean(seed.get("source") or row.get("source") or "wp18c2_seed"),
        "audit_history": list(row.get("audit_history") or []),
    }


async def _write_audit(db, action: str, actor: Optional[Dict[str, Any]], resource_type: str, resource_id: str, after: Dict[str, Any], before: Optional[Dict[str, Any]] = None, metadata: Optional[Dict[str, Any]] = None) -> None:
    audit_id = f"audit:{resource_type}:{resource_id}:{_fingerprint([action, _utcnow(), _actor_label(actor)])}"
    await db[COLL_AUDIT].insert_one(
        {
            "audit_id": audit_id,
            "action": action,
            "resource_type": resource_type,
            "resource_id": resource_id,
            "actor": _sanitize(actor or {}),
            "before": _sanitize(before or {}),
            "after": _sanitize(after or {}),
            "metadata": _sanitize(metadata or {}),
            "created_at": _utcnow(),
        }
    )


async def _ensure_indexes(db) -> None:
    await db[COLL_WORK_TYPES].create_index("work_type_id", unique=True)
    await db[COLL_WORK_TYPES].create_index("code", unique=True)
    await db[COLL_PAY_ITEMS].create_index([("project_number", 1), ("pay_item_id", 1)], unique=True)
    await db[COLL_PAY_ITEMS].create_index([("project_number", 1), ("customer_pay_item_number", 1)])
    await db[COLL_MAPPINGS].create_index([("project_number", 1), ("mapping_id", 1)], unique=True)
    await db[COLL_MAPPINGS].create_index([("project_number", 1), ("pay_item_id", 1)])
    await db[COLL_REVIEW].create_index("review_id", unique=True)
    await db[COLL_REVIEW].create_index([("project_number", 1), ("status", 1), ("priority", -1)])
    await db[COLL_LOOKAHEAD].create_index([("project_number", 1), ("lookahead_id", 1)], unique=True)
    await db[COLL_LIFECYCLE].create_index("project_number", unique=True)
    await db[COLL_CONFIRMED_CREWS].create_index([("project_number", 1), ("crew_id", 1)], unique=True)
    await db[COLL_CREW_OBSERVATIONS].create_index([("project_number", 1), ("source_record_id", 1)], unique=True)
    await db[COLL_WORK_LEDGER].create_index([("project_number", 1), ("report_date", -1)])
    await db[COLL_WORK_LEDGER].create_index([("source_report_id", 1), ("work_block_id", 1)], unique=True)
    await db[COLL_AUDIT].create_index([("resource_type", 1), ("resource_id", 1), ("created_at", -1)])
    await db[COLL_RUNS].create_index("run_id", unique=True)


async def _seed_work_types(db) -> Dict[str, int]:
    created = 0
    updated = 0
    for seed in DEFAULT_WORK_TYPES:
        existing = await db[COLL_WORK_TYPES].find_one({"code": seed["code"]}, {"_id": 0})
        doc = _work_type_doc(seed, existing=existing, actor={"id": "wp18c2-seed", "email": "wp18c2@system"})
        await db[COLL_WORK_TYPES].update_one(
            {"work_type_id": doc["work_type_id"]},
            {"$set": doc},
            upsert=True,
        )
        if existing:
            updated += 1
        else:
            created += 1
    return {"created": created, "updated": updated, "total": created + updated}


def _jobs_status_text(job: Dict[str, Any]) -> str:
    return _clean(job.get("status") or job.get("project_status") or job.get("lifecycle_state") or job.get("stage") or "")


def _derive_lifecycle_from_job(job: Optional[Dict[str, Any]]) -> Tuple[str, List[str]]:
    row = job or {}
    notes: List[str] = []
    status_text = _jobs_status_text(row).lower()
    archived_flag = bool(row.get("archived") or row.get("archive_status") or row.get("is_archived"))
    active_flag = row.get("active")
    if archived_flag:
        notes.append("Derived archived state from existing project archive flag.")
        return "Archived", notes
    if any(token in status_text for token in ["proposal", "pursuit", "bid"]):
        notes.append("Derived lifecycle from project status text.")
        return "Proposal", notes
    if any(token in status_text for token in ["award", "won"]):
        notes.append("Derived lifecycle from project status text.")
        return "Awarded", notes
    if "preconstruction" in status_text or "pre-construction" in status_text:
        notes.append("Derived lifecycle from project status text.")
        return "Preconstruction", notes
    if any(token in status_text for token in ["substantial completion", "substantial_complete"]):
        notes.append("Derived lifecycle from project status text.")
        return "Substantial Completion", notes
    if any(token in status_text for token in ["final completion", "final_complete"]):
        notes.append("Derived lifecycle from project status text.")
        return "Final Completion", notes
    if any(token in status_text for token in ["closed", "complete", "completed"]):
        notes.append("Derived lifecycle from project status text.")
        return "Closed", notes
    if active_flag is True:
        notes.append("Derived lifecycle from active project flag.")
        return "Active", notes
    if active_flag is False:
        notes.append("Project is inactive in jobs_master; human review still required for closure/archive distinction.")
        return "Closed", notes
    notes.append("Lifecycle evidence is incomplete; defaulted to Active while preserving original project record for review.")
    return "Active", notes


async def _load_job(db, project_number: str) -> Dict[str, Any]:
    if not project_number:
        raise LookupError("project_number_required")
    row = await db.jobs_master.find_one({"project_number": project_number}, {"_id": 0})
    if not row:
        raise LookupError("project_not_found")
    return row


async def _maybe_get_project_node(db, project_number: str) -> Optional[Dict[str, Any]]:
    return await db.enterprise_governance_organization.find_one(
        {
            "type": "project",
            "$or": [
                {"code": project_number},
                {"source_record_id": project_number},
                {"metadata_extension.project_number": project_number},
            ],
        },
        {"_id": 0},
    )


async def get_project_lifecycle(db, project_number: str) -> Dict[str, Any]:
    await ensure_project_controls_foundation(db)
    job = await _load_job(db, project_number)
    row = await db[COLL_LIFECYCLE].find_one({"project_number": project_number}, {"_id": 0})
    derived_state, derived_notes = _derive_lifecycle_from_job(job)
    if row:
        out = dict(row)
        out["source_job_snapshot"] = {
            "project_number": job.get("project_number"),
            "project_name": job.get("project_name") or job.get("name") or project_number,
            "status_fields": {
                "status": job.get("status"),
                "project_status": job.get("project_status"),
                "active": job.get("active"),
                "archived": job.get("archived"),
            },
        }
        out["derived_state_from_source"] = derived_state
        out["derived_notes"] = derived_notes
        return _sanitize(out)
    project_node = await _maybe_get_project_node(db, project_number)
    now = _utcnow()
    doc = {
        "project_number": project_number,
        "project_name": job.get("project_name") or job.get("name") or project_number,
        "current_state": derived_state,
        "archive_status": bool(project_node.get("archive_status") if project_node else False),
        "previous_state": "",
        "allowed_states": list(PROJECT_LIFECYCLE_STATES),
        "state_history": [
            {
                "at": now,
                "actor": "wp18c2_backfill",
                "from_state": "",
                "to_state": derived_state,
                "reason": "Derived from current protected project identity evidence.",
            }
        ],
        "archive_history": [],
        "permissions_boundary": {
            "pm_scope_required": True,
            "archive_never_deletes": True,
            "historical_records_retained": True,
        },
        "updated_at": now,
        "updated_by": "wp18c2_backfill",
        "source_job_snapshot": {
            "project_number": job.get("project_number"),
            "project_name": job.get("project_name") or job.get("name") or project_number,
            "status_fields": {
                "status": job.get("status"),
                "project_status": job.get("project_status"),
                "active": job.get("active"),
                "archived": job.get("archived"),
            },
        },
        "derived_state_from_source": derived_state,
        "derived_notes": derived_notes,
    }
    await db[COLL_LIFECYCLE].insert_one(doc)
    return _sanitize(doc)


async def set_project_lifecycle_state(db, project_number: str, *, actor: Dict[str, Any], next_state: str, reason: str = "") -> Dict[str, Any]:
    row = await get_project_lifecycle(db, project_number)
    if next_state not in PROJECT_LIFECYCLE_STATES:
        raise ValueError("unsupported_lifecycle_state")
    current = row.get("current_state") or ""
    updated = deepcopy(row)
    updated["previous_state"] = current
    updated["current_state"] = next_state
    updated["updated_at"] = _utcnow()
    updated["updated_by"] = _actor_label(actor)
    updated.setdefault("state_history", []).append(
        {
            "at": updated["updated_at"],
            "actor": _actor_label(actor),
            "from_state": current,
            "to_state": next_state,
            "reason": _clean(reason) or "Manual governed lifecycle update.",
        }
    )
    await db[COLL_LIFECYCLE].replace_one({"project_number": project_number}, updated, upsert=True)
    await _write_audit(db, "project_lifecycle_updated", actor, "project_lifecycle", project_number, updated, before=row)
    return _sanitize(updated)


async def archive_project(db, project_number: str, *, actor: Dict[str, Any], reason: str = "") -> Dict[str, Any]:
    lifecycle = await set_project_lifecycle_state(db, project_number, actor=actor, next_state="Archived", reason=reason or "Governed project archive action.")
    lifecycle["archive_status"] = True
    lifecycle.setdefault("archive_history", []).append(
        {
            "at": _utcnow(),
            "actor": _actor_label(actor),
            "action": "archive",
            "reason": _clean(reason) or "Governed archive action",
        }
    )
    await db[COLL_LIFECYCLE].replace_one({"project_number": project_number}, lifecycle, upsert=True)
    project_node = await _maybe_get_project_node(db, project_number)
    if project_node:
        await db.enterprise_governance_organization.update_one(
            {"id": project_node.get("id")},
            {"$set": {"archive_status": True, "active_status": False, "updated_at": _utcnow()}},
        )
    return _sanitize(lifecycle)


async def restore_project(db, project_number: str, *, actor: Dict[str, Any], reason: str = "") -> Dict[str, Any]:
    row = await get_project_lifecycle(db, project_number)
    restore_state = row.get("previous_state") or "Active"
    restored = await set_project_lifecycle_state(db, project_number, actor=actor, next_state=restore_state, reason=reason or "Governed archive restore action.")
    restored["archive_status"] = False
    restored.setdefault("archive_history", []).append(
        {
            "at": _utcnow(),
            "actor": _actor_label(actor),
            "action": "restore",
            "reason": _clean(reason) or "Governed restore action",
        }
    )
    await db[COLL_LIFECYCLE].replace_one({"project_number": project_number}, restored, upsert=True)
    project_node = await _maybe_get_project_node(db, project_number)
    if project_node:
        await db.enterprise_governance_organization.update_one(
            {"id": project_node.get("id")},
            {"$set": {"archive_status": False, "active_status": True, "updated_at": _utcnow()}},
        )
    return _sanitize(restored)


async def list_enterprise_work_types(db, *, include_archived: bool = False) -> List[Dict[str, Any]]:
    await ensure_project_controls_foundation(db)
    query: Dict[str, Any] = {}
    if not include_archived:
        query["status"] = {"$ne": "archived"}
    return [_sanitize(row) async for row in db[COLL_WORK_TYPES].find(query, {"_id": 0}).sort([("status", 1), ("name", 1)])]


async def upsert_enterprise_work_type(db, payload: Dict[str, Any], *, actor: Dict[str, Any], work_type_id: Optional[str] = None) -> Dict[str, Any]:
    await ensure_project_controls_foundation(db)
    lookup: Dict[str, Any]
    if work_type_id:
        lookup = {"work_type_id": work_type_id}
    else:
        code = _clean(payload.get("code"))
        if not code:
            raise ValueError("work_type_code_required")
        lookup = {"code": code}
    existing = await db[COLL_WORK_TYPES].find_one(lookup, {"_id": 0})
    doc = _work_type_doc(payload, existing=existing, actor=actor)
    await db[COLL_WORK_TYPES].replace_one({"work_type_id": doc["work_type_id"]}, doc, upsert=True)
    await _write_audit(db, "work_type_upserted", actor, "work_type", doc["work_type_id"], doc, before=existing)
    return _sanitize(doc)


def _pay_item_doc(project_number: str, payload: Dict[str, Any], existing: Optional[Dict[str, Any]], actor: Dict[str, Any]) -> Dict[str, Any]:
    now = _utcnow()
    row = dict(existing or {})
    customer_no = _clean(payload.get("customer_pay_item_number") or row.get("customer_pay_item_number"))
    description = _clean(payload.get("description") or row.get("description"))
    if not customer_no:
        raise ValueError("customer_pay_item_number_required")
    if not description:
        raise ValueError("pay_item_description_required")
    contract_quantity = round(_to_float(payload.get("contract_quantity"), _to_float(row.get("contract_quantity"), 0.0)), 4)
    contract_unit_price = round(_to_float(payload.get("contract_unit_price"), _to_float(row.get("contract_unit_price"), 0.0)), 4)
    contract_value = round(_to_float(payload.get("contract_value"), contract_quantity * contract_unit_price), 4)
    pay_item_id = row.get("pay_item_id") or payload.get("pay_item_id") or f"pay-item:{project_number}:{_norm(customer_no)}"
    return {
        "pay_item_id": pay_item_id,
        "project_number": project_number,
        "project_name": _clean(payload.get("project_name") or row.get("project_name")),
        "customer_pay_item_number": customer_no,
        "description": description,
        "unit": _clean(payload.get("unit") or row.get("unit") or ""),
        "contract_quantity": contract_quantity,
        "contract_unit_price": contract_unit_price,
        "contract_value": contract_value,
        "contract_id": _clean(payload.get("contract_id") or row.get("contract_id")),
        "phase_id": _clean(payload.get("phase_id") or row.get("phase_id")),
        "work_package_id": _clean(payload.get("work_package_id") or row.get("work_package_id")),
        "schedule_activity_id": _clean(payload.get("schedule_activity_id") or row.get("schedule_activity_id")),
        "schedule_activity_name": _clean(payload.get("schedule_activity_name") or row.get("schedule_activity_name")),
        "status": _status(payload.get("status") or row.get("status") or "active", allowed=["draft", "active", "inactive", "archived"], default="active"),
        "effective_start": _clean(payload.get("effective_start") or row.get("effective_start") or now),
        "effective_end": _clean(payload.get("effective_end") or row.get("effective_end")),
        "billing_relevance": bool(payload.get("billing_relevance", row.get("billing_relevance", True))),
        "production_relevance": bool(payload.get("production_relevance", row.get("production_relevance", True))),
        "schedule_relevance": bool(payload.get("schedule_relevance", row.get("schedule_relevance", True))),
        "source": _clean(payload.get("source") or row.get("source") or "manual_governed_entry"),
        "source_record": _sanitize(payload.get("source_record") or row.get("source_record") or {}),
        "provenance": _sanitize(payload.get("provenance") or row.get("provenance") or {"entered_once": True, "owner": "project_pay_item_registry"}),
        "confidence": _clean(payload.get("confidence") or row.get("confidence") or "human_confirmed"),
        "created_at": row.get("created_at") or now,
        "created_by": row.get("created_by") or _actor_label(actor),
        "updated_at": now,
        "updated_by": _actor_label(actor),
    }


async def list_project_pay_items(db, project_number: str) -> List[Dict[str, Any]]:
    await ensure_project_controls_foundation(db)
    return [_sanitize(row) async for row in db[COLL_PAY_ITEMS].find({"project_number": project_number}, {"_id": 0}).sort([("status", 1), ("customer_pay_item_number", 1)])]


async def _upsert_review_item(db, review: Dict[str, Any]) -> Dict[str, Any]:
    existing = await db[COLL_REVIEW].find_one({"review_id": review["review_id"]}, {"_id": 0})
    now = _utcnow()
    doc = {
        **(existing or {}),
        **review,
        "created_at": (existing or {}).get("created_at") or now,
        "updated_at": now,
    }
    await db[COLL_REVIEW].replace_one({"review_id": doc["review_id"]}, doc, upsert=True)
    return _sanitize(doc)


async def _mark_review_resolved(db, review_id: str, *, actor: Optional[Dict[str, Any]] = None, resolution_note: str = "") -> None:
    row = await db[COLL_REVIEW].find_one({"review_id": review_id}, {"_id": 0})
    if not row:
        return
    row["status"] = "resolved"
    row["resolution_note"] = _clean(resolution_note) or "Resolved by subsequent governed action."
    row["resolved_at"] = _utcnow()
    row["resolved_by"] = _actor_label(actor)
    await db[COLL_REVIEW].replace_one({"review_id": review_id}, row, upsert=True)


async def _ensure_pay_item_mapping_review(db, pay_item: Dict[str, Any], *, note: str = "") -> Dict[str, Any]:
    review_id = f"review:mapping:{pay_item['project_number']}:{pay_item['pay_item_id']}"
    return await _upsert_review_item(
        db,
        {
            "review_id": review_id,
            "project_number": pay_item["project_number"],
            "review_type": "pay_item_mapping_required",
            "status": "review_required",
            "priority": 90,
            "source_collection": COLL_PAY_ITEMS,
            "source_record_id": pay_item["pay_item_id"],
            "title": f"Mapping required for pay item {pay_item.get('customer_pay_item_number') or pay_item.get('pay_item_id')}",
            "reason": note or "Project pay item is preserved, but governed work-type mapping still needs human review.",
            "provenance": {
                "customer_pay_item_number": pay_item.get("customer_pay_item_number"),
                "description": pay_item.get("description"),
                "source": pay_item.get("source"),
            },
            "confidence": "human_required",
        },
    )


async def upsert_project_pay_item(db, project_number: str, payload: Dict[str, Any], *, actor: Dict[str, Any]) -> Dict[str, Any]:
    await ensure_project_controls_foundation(db)
    pay_item_id = _clean(payload.get("pay_item_id"))
    existing = await db[COLL_PAY_ITEMS].find_one({"project_number": project_number, "pay_item_id": pay_item_id}, {"_id": 0}) if pay_item_id else None
    if not existing and payload.get("customer_pay_item_number"):
        existing = await db[COLL_PAY_ITEMS].find_one(
            {"project_number": project_number, "customer_pay_item_number": _clean(payload.get("customer_pay_item_number"))},
            {"_id": 0},
        )
    doc = _pay_item_doc(project_number, payload, existing, actor)
    await db[COLL_PAY_ITEMS].replace_one({"project_number": project_number, "pay_item_id": doc["pay_item_id"]}, doc, upsert=True)
    await _write_audit(db, "project_pay_item_upserted", actor, "project_pay_item", doc["pay_item_id"], doc, before=existing)
    mapping = await db[COLL_MAPPINGS].find_one({"project_number": project_number, "pay_item_id": doc["pay_item_id"], "status": {"$in": ["approved", "active"]}}, {"_id": 0})
    if not mapping:
        await _ensure_pay_item_mapping_review(db, doc)
    return _sanitize(doc)


def _tokenize(text: str) -> List[str]:
    return [tok for tok in re.split(r"[^a-z0-9]+", (text or "").lower()) if tok]


def _suggest_work_type(pay_item: Dict[str, Any], work_types: List[Dict[str, Any]]) -> Dict[str, Any]:
    haystack = set(_tokenize(f"{pay_item.get('customer_pay_item_number')} {pay_item.get('description') or ''}"))
    best: Optional[Dict[str, Any]] = None
    best_score = 0
    for work_type in work_types:
        terms = set(_tokenize(work_type.get("name") or "")) | set(work_type.get("keywords") or []) | {_norm(work_type.get("code") or "")}
        score = len(haystack & terms)
        if score > best_score:
            best = work_type
            best_score = score
    if not best:
        return {"primary_work_type_id": "", "confidence": "review_required", "matched_terms": []}
    confidence = "high" if best_score >= 2 else "medium"
    return {
        "primary_work_type_id": best.get("work_type_id") or "",
        "confidence": confidence,
        "matched_terms": sorted(list(haystack & (set(best.get("keywords") or []) | set(_tokenize(best.get("name") or ""))))),
    }


def _mapping_doc(project_number: str, payload: Dict[str, Any], pay_item: Dict[str, Any], work_types: List[Dict[str, Any]], existing: Optional[Dict[str, Any]], actor: Dict[str, Any]) -> Dict[str, Any]:
    now = _utcnow()
    row = dict(existing or {})
    suggestion = _suggest_work_type(pay_item, work_types)
    primary_work_type_id = _clean(payload.get("primary_work_type_id") or row.get("primary_work_type_id") or suggestion.get("primary_work_type_id"))
    secondary_work_type_ids = [
        _clean(item)
        for item in (payload.get("secondary_work_type_ids") or row.get("secondary_work_type_ids") or [])
        if _clean(item)
    ]
    mapping_id = row.get("mapping_id") or payload.get("mapping_id") or f"mapping:{project_number}:{pay_item['pay_item_id']}"
    requested_status = payload.get("status") or row.get("status") or ("approved" if payload.get("primary_work_type_id") else "pending_review")
    status = _status(requested_status, allowed=["suggested", "pending_review", "approved", "rejected", "deferred", "active"], default="pending_review")
    if status == "active":
        status = "approved"
    return {
        "mapping_id": mapping_id,
        "project_number": project_number,
        "pay_item_id": pay_item["pay_item_id"],
        "customer_pay_item_number": pay_item.get("customer_pay_item_number"),
        "primary_work_type_id": primary_work_type_id,
        "secondary_work_type_ids": secondary_work_type_ids,
        "confidence": _clean(payload.get("confidence") or row.get("confidence") or suggestion.get("confidence") or "review_required"),
        "source": _clean(payload.get("source") or row.get("source") or ("human_governed" if payload.get("primary_work_type_id") else "deterministic_suggestion")),
        "effective_start": _clean(payload.get("effective_start") or row.get("effective_start") or now),
        "effective_end": _clean(payload.get("effective_end") or row.get("effective_end")),
        "status": status,
        "mapper": _clean(payload.get("mapper") or row.get("mapper") or _actor_label(actor)),
        "approver": _clean(payload.get("approver") or row.get("approver") or (_actor_label(actor) if status == "approved" else "")),
        "matched_terms": suggestion.get("matched_terms") or row.get("matched_terms") or [],
        "audit_history": list(row.get("audit_history") or []),
        "created_at": row.get("created_at") or now,
        "created_by": row.get("created_by") or _actor_label(actor),
        "updated_at": now,
        "updated_by": _actor_label(actor),
        "explanation": _clean(payload.get("explanation") or row.get("explanation") or "Governed mapping between project pay item and enterprise work type."),
    }


async def list_project_mappings(db, project_number: str) -> List[Dict[str, Any]]:
    await ensure_project_controls_foundation(db)
    return [_sanitize(row) async for row in db[COLL_MAPPINGS].find({"project_number": project_number}, {"_id": 0}).sort([("updated_at", -1), ("mapping_id", 1)])]


async def upsert_project_mapping(db, project_number: str, payload: Dict[str, Any], *, actor: Dict[str, Any]) -> Dict[str, Any]:
    await ensure_project_controls_foundation(db)
    pay_item_id = _clean(payload.get("pay_item_id"))
    if not pay_item_id:
        raise ValueError("pay_item_id_required")
    pay_item = await db[COLL_PAY_ITEMS].find_one({"project_number": project_number, "pay_item_id": pay_item_id}, {"_id": 0})
    if not pay_item:
        raise LookupError("project_pay_item_not_found")
    existing = await db[COLL_MAPPINGS].find_one({"project_number": project_number, "pay_item_id": pay_item_id}, {"_id": 0})
    work_types = await list_enterprise_work_types(db, include_archived=False)
    doc = _mapping_doc(project_number, payload, pay_item, work_types, existing, actor)
    await db[COLL_MAPPINGS].replace_one({"project_number": project_number, "mapping_id": doc["mapping_id"]}, doc, upsert=True)
    await _write_audit(db, "project_mapping_upserted", actor, "project_mapping", doc["mapping_id"], doc, before=existing)
    review_id = f"review:mapping:{project_number}:{pay_item_id}"
    if doc["status"] == "approved" and doc.get("primary_work_type_id"):
        await _mark_review_resolved(db, review_id, actor=actor, resolution_note="Mapping approved by human operator.")
    else:
        await _ensure_pay_item_mapping_review(db, pay_item, note="Mapping still requires governed human review.")
    return _sanitize(doc)


async def list_review_queue(db, *, project_number: str = "", status: str = "") -> List[Dict[str, Any]]:
    await ensure_project_controls_foundation(db)
    query: Dict[str, Any] = {}
    if project_number:
        query["project_number"] = project_number
    if status:
        query["status"] = status
    return [_sanitize(row) async for row in db[COLL_REVIEW].find(query, {"_id": 0}).sort([("priority", -1), ("updated_at", -1)]).limit(500)]


def _resource_match_value(row: Dict[str, Any]) -> str:
    return _clean(row.get("cost_code") or row.get("code") or row.get("activity_code") or row.get("schedule_activity_id") or "")


def _build_labor_entries(report: Dict[str, Any], block_key: str, *, include_shared: bool) -> List[Dict[str, Any]]:
    rows = []
    for crew in report.get("masci_crews") or []:
        key = _resource_match_value(crew)
        if block_key and key and key != block_key:
            continue
        if block_key and not include_shared and not key:
            continue
        rows.append(
            {
                "employee_id": _clean(crew.get("employee_id")),
                "employee_name": _clean(crew.get("name") or crew.get("employee_name_snapshot")),
                "role": _clean(crew.get("trade") or crew.get("trade_role_display")),
                "hours_regular": round(_to_float(crew.get("hours"), 0.0), 4),
                "hours_overtime": round(_to_float(crew.get("overtime_hours"), 0.0), 4),
                "crew_id": _clean(crew.get("confirmed_crew_id") or crew.get("crew_id")),
                "source": "daily_reports.masci_crews",
            }
        )
    return rows


def _build_equipment_entries(report: Dict[str, Any], block_key: str, *, include_shared: bool) -> List[Dict[str, Any]]:
    rows = []
    for item in report.get("equipment") or []:
        key = _resource_match_value(item)
        if block_key and key and key != block_key:
            continue
        if block_key and not include_shared and not key:
            continue
        rows.append(
            {
                "asset_id": _clean(item.get("equipment_id") or item.get("asset_id") or item.get("unit_number")),
                "asset_label": _clean(item.get("description") or item.get("equipment_name")),
                "operating_hours": round(_to_float(item.get("hours_used") or item.get("run_time"), 0.0), 4),
                "idle_hours": round(_to_float(item.get("idle_hours") or item.get("idle_time"), 0.0), 4),
                "standby_hours": round(_to_float(item.get("standby_hours"), 0.0), 4),
                "operator_name": _clean(item.get("operator_name")),
                "source": "daily_reports.equipment",
            }
        )
    return rows


def _build_material_entries(report: Dict[str, Any], block_key: str, *, include_shared: bool) -> List[Dict[str, Any]]:
    rows = []
    for item in report.get("materials") or []:
        key = _resource_match_value(item)
        if block_key and key and key != block_key:
            continue
        if block_key and not include_shared and not key:
            continue
        rows.append(
            {
                "description": _clean(item.get("description")),
                "supplier": _clean(item.get("supplier") or item.get("carrier")),
                "delivered_quantity": round(_to_float(item.get("quantity"), 0.0), 4),
                "installed_quantity": round(_to_float(item.get("installed_quantity"), _to_float(item.get("quantity"), 0.0)), 4),
                "waste_quantity": round(_to_float(item.get("waste_quantity"), 0.0), 4),
                "unit": _clean(item.get("unit") or item.get("unit_snapshot")),
                "ticket_number": _clean(item.get("ticket_number")),
                "source": "daily_reports.materials",
            }
        )
    return rows


def _build_subcontractor_entries(report: Dict[str, Any], block_key: str, *, include_shared: bool) -> List[Dict[str, Any]]:
    rows = []
    for item in report.get("subcontractors") or []:
        key = _resource_match_value(item)
        if block_key and key and key != block_key:
            continue
        if block_key and not include_shared and not key:
            continue
        rows.append(
            {
                "vendor_name": _clean(item.get("company")),
                "foreman": _clean(item.get("foreman")),
                "work_performed": _clean(item.get("work_performed")),
                "quantity": round(_to_float(item.get("quantity"), 0.0), 4),
                "hours": round(_to_float(item.get("hours"), 0.0), 4),
                "headcount": _to_int(item.get("count"), 0),
                "commitment_ref": _clean(item.get("commitment_ref")),
                "source": "daily_reports.subcontractors",
            }
        )
    return rows


def _build_constraint_entries(report: Dict[str, Any], block_key: str, *, include_shared: bool) -> List[Dict[str, Any]]:
    rows = []
    for item in report.get("constraints") or []:
        key = _resource_match_value(item)
        if block_key and key and key != block_key:
            continue
        if block_key and not include_shared and not key:
            continue
        rows.append(
            {
                "constraint_id": _clean(item.get("constraint_id") or item.get("row_id")),
                "constraint_type": _clean(item.get("constraint_type")),
                "hours_impact": round(_to_float(item.get("hours_impact"), 0.0), 4),
                "notes": _clean(item.get("notes")),
                "source": "daily_reports.constraints",
            }
        )
    return rows


def _default_work_block_from_cost_row(report: Dict[str, Any], row: Dict[str, Any], index: int, total_blocks: int) -> Dict[str, Any]:
    key = _clean(row.get("cost_code") or row.get("cpm_activity_id") or row.get("code"))
    include_shared = total_blocks == 1
    return {
        "work_block_id": _clean(row.get("work_block_id") or f"{report.get('id') or report.get('doc_id') or 'dr'}:block:{index + 1}"),
        "title": _clean(row.get("item_name") or row.get("description") or row.get("cost_code") or f"Work Block {index + 1}"),
        "source_mode": "derived_from_cost_code_quantities",
        "project_number": _clean(report.get("project_number")),
        "contract_id": _clean(row.get("contract_id")),
        "phase_id": _clean(row.get("phase_id")),
        "work_package_id": _clean(row.get("work_package_id")),
        "pay_item_id": _clean(row.get("pay_item_id")),
        "customer_pay_item_number": _clean(row.get("customer_pay_item_number")),
        "cost_code": _clean(row.get("cost_code")),
        "work_type_ids": [item for item in row.get("work_type_ids") or [] if _clean(item)],
        "primary_work_type_id": _clean(row.get("primary_work_type_id")),
        "schedule_activity_id": _clean(row.get("schedule_activity_id") or row.get("cpm_activity_id")),
        "schedule_activity_name": _clean(row.get("schedule_activity_name") or row.get("cpm_activity_name")),
        "installed_quantity": round(_to_float(row.get("installed_quantity"), 0.0), 4),
        "unit": _clean(row.get("unit_of_measure") or row.get("unit") or ""),
        "location": _clean(row.get("location") or report.get("location")),
        "work_area": _clean(row.get("work_area")),
        "field_notes": _clean(row.get("notes")),
        "schedule_actual_proposal_status": "proposed_only",
        "labor_entries": _build_labor_entries(report, key, include_shared=include_shared),
        "equipment_entries": _build_equipment_entries(report, key, include_shared=include_shared),
        "material_entries": _build_material_entries(report, key, include_shared=include_shared),
        "subcontractor_entries": _build_subcontractor_entries(report, key, include_shared=include_shared),
        "constraint_entries": _build_constraint_entries(report, key, include_shared=include_shared),
        "photo_refs": list(report.get("photos") or []) if include_shared else [],
        "attachment_refs": list(report.get("attachments") or []) if include_shared else [],
        "qaqc_refs": list(row.get("qaqc_refs") or []),
        "safety_refs": list(row.get("safety_refs") or []),
        "shared_report_resource_counts": {
            "crew_rows": len(report.get("masci_crews") or []),
            "equipment_rows": len(report.get("equipment") or []),
            "material_rows": len(report.get("materials") or []),
            "subcontractor_rows": len(report.get("subcontractors") or []),
        },
    }


def _default_work_block_from_production_row(report: Dict[str, Any], row: Dict[str, Any], index: int, total_blocks: int) -> Dict[str, Any]:
    key = _clean(row.get("cost_code") or row.get("activity_code") or row.get("schedule_activity_id"))
    include_shared = total_blocks == 1
    return {
        "work_block_id": _clean(row.get("work_block_id") or f"{report.get('id') or report.get('doc_id') or 'dr'}:prod-block:{index + 1}"),
        "title": _clean(row.get("description") or f"Production Block {index + 1}"),
        "source_mode": "derived_from_production",
        "project_number": _clean(report.get("project_number")),
        "contract_id": _clean(row.get("contract_id")),
        "phase_id": _clean(row.get("phase_id")),
        "work_package_id": _clean(row.get("work_package_id")),
        "pay_item_id": _clean(row.get("pay_item_id")),
        "customer_pay_item_number": _clean(row.get("customer_pay_item_number")),
        "cost_code": _clean(row.get("cost_code")),
        "work_type_ids": [item for item in row.get("work_type_ids") or [] if _clean(item)],
        "primary_work_type_id": _clean(row.get("primary_work_type_id")),
        "schedule_activity_id": _clean(row.get("schedule_activity_id") or row.get("activity_code")),
        "schedule_activity_name": _clean(row.get("schedule_activity_name")),
        "installed_quantity": round(_to_float(row.get("quantity"), 0.0), 4),
        "unit": _clean(row.get("unit") or row.get("unit_snapshot") or ""),
        "location": _clean(row.get("location") or report.get("location")),
        "work_area": _clean(row.get("station_from") or row.get("station_to") or ""),
        "field_notes": _clean(row.get("notes")),
        "schedule_actual_proposal_status": "proposed_only",
        "labor_entries": _build_labor_entries(report, key, include_shared=include_shared),
        "equipment_entries": _build_equipment_entries(report, key, include_shared=include_shared),
        "material_entries": _build_material_entries(report, key, include_shared=include_shared),
        "subcontractor_entries": _build_subcontractor_entries(report, key, include_shared=include_shared),
        "constraint_entries": _build_constraint_entries(report, key, include_shared=include_shared),
        "photo_refs": list(report.get("photos") or []) if include_shared else [],
        "attachment_refs": list(report.get("attachments") or []) if include_shared else [],
        "qaqc_refs": list(row.get("qaqc_refs") or []),
        "safety_refs": list(row.get("safety_refs") or []),
        "shared_report_resource_counts": {
            "crew_rows": len(report.get("masci_crews") or []),
            "equipment_rows": len(report.get("equipment") or []),
            "material_rows": len(report.get("materials") or []),
            "subcontractor_rows": len(report.get("subcontractors") or []),
        },
    }


def _normalize_explicit_work_block(report: Dict[str, Any], row: Dict[str, Any], index: int) -> Dict[str, Any]:
    out = deepcopy(row)
    out["work_block_id"] = _clean(out.get("work_block_id") or f"{report.get('id') or report.get('doc_id') or 'dr'}:manual:{index + 1}")
    out["title"] = _clean(out.get("title") or out.get("description") or f"Work Block {index + 1}")
    out["project_number"] = _clean(out.get("project_number") or report.get("project_number"))
    out["installed_quantity"] = round(_to_float(out.get("installed_quantity"), 0.0), 4)
    out["schedule_actual_proposal_status"] = _clean(out.get("schedule_actual_proposal_status") or "proposed_only")
    out["labor_entries"] = _sanitize(out.get("labor_entries") or [])
    out["equipment_entries"] = _sanitize(out.get("equipment_entries") or [])
    out["material_entries"] = _sanitize(out.get("material_entries") or [])
    out["subcontractor_entries"] = _sanitize(out.get("subcontractor_entries") or [])
    out["constraint_entries"] = _sanitize(out.get("constraint_entries") or [])
    out["photo_refs"] = list(out.get("photo_refs") or [])
    out["attachment_refs"] = list(out.get("attachment_refs") or [])
    return out


def derive_work_blocks_from_report(report: Dict[str, Any]) -> List[Dict[str, Any]]:
    explicit = [row for row in (report.get("work_blocks") or []) if isinstance(row, dict)]
    if explicit:
        return [_normalize_explicit_work_block(report, row, idx) for idx, row in enumerate(explicit)]

    cost_rows = [
        row for row in (report.get("cost_code_quantities") or [])
        if _to_float(row.get("installed_quantity"), 0.0) > 0 or _clean(row.get("notes")) or _clean(row.get("cost_code"))
    ]
    if cost_rows:
        return [_default_work_block_from_cost_row(report, row, idx, len(cost_rows)) for idx, row in enumerate(cost_rows)]

    prod_rows = [
        row for row in (report.get("production") or [])
        if _to_float(row.get("quantity"), 0.0) > 0 or _clean(row.get("description"))
    ]
    if prod_rows:
        return [_default_work_block_from_production_row(report, row, idx, len(prod_rows)) for idx, row in enumerate(prod_rows)]

    has_any_resource = any(
        bool(report.get(field))
        for field in ["masci_crews", "equipment", "materials", "subcontractors", "constraints", "activities"]
    )
    if not has_any_resource:
        return []
    return [
        {
            "work_block_id": f"{report.get('id') or report.get('doc_id') or 'dr'}:general:1",
            "title": "General Field Work",
            "source_mode": "derived_from_report_level_resources",
            "project_number": _clean(report.get("project_number")),
            "contract_id": "",
            "phase_id": "",
            "work_package_id": "",
            "pay_item_id": "",
            "customer_pay_item_number": "",
            "cost_code": "",
            "work_type_ids": [],
            "primary_work_type_id": "",
            "schedule_activity_id": "",
            "schedule_activity_name": "",
            "installed_quantity": 0.0,
            "unit": "",
            "location": _clean(report.get("location")),
            "work_area": "",
            "field_notes": _clean(report.get("general_notes")),
            "schedule_actual_proposal_status": "proposed_only",
            "labor_entries": _build_labor_entries(report, "", include_shared=True),
            "equipment_entries": _build_equipment_entries(report, "", include_shared=True),
            "material_entries": _build_material_entries(report, "", include_shared=True),
            "subcontractor_entries": _build_subcontractor_entries(report, "", include_shared=True),
            "constraint_entries": _build_constraint_entries(report, "", include_shared=True),
            "photo_refs": list(report.get("photos") or []),
            "attachment_refs": list(report.get("attachments") or []),
            "qaqc_refs": [],
            "safety_refs": [],
            "shared_report_resource_counts": {
                "crew_rows": len(report.get("masci_crews") or []),
                "equipment_rows": len(report.get("equipment") or []),
                "material_rows": len(report.get("materials") or []),
                "subcontractor_rows": len(report.get("subcontractors") or []),
            },
        }
    ]


def _work_block_summary(blocks: List[Dict[str, Any]]) -> Dict[str, Any]:
    return {
        "work_block_count": len(blocks),
        "blocks_with_pay_item": sum(1 for block in blocks if _clean(block.get("pay_item_id") or block.get("customer_pay_item_number"))),
        "blocks_with_schedule_activity": sum(1 for block in blocks if _clean(block.get("schedule_activity_id"))),
        "labor_rows": sum(len(block.get("labor_entries") or []) for block in blocks),
        "equipment_rows": sum(len(block.get("equipment_entries") or []) for block in blocks),
        "material_rows": sum(len(block.get("material_entries") or []) for block in blocks),
        "subcontractor_rows": sum(len(block.get("subcontractor_entries") or []) for block in blocks),
        "constraint_rows": sum(len(block.get("constraint_entries") or []) for block in blocks),
    }


async def sync_work_blocks_for_report(db, report: Dict[str, Any], *, foundation_ready: bool = False) -> Dict[str, Any]:
    if not foundation_ready:
        await ensure_project_controls_foundation(db)
    blocks = derive_work_blocks_from_report(report)
    summary = _work_block_summary(blocks)
    report_id = _clean(report.get("id") or report.get("doc_id"))
    if report_id:
        await db[COLL_WORK_LEDGER].delete_many({"source_report_id": report_id})
    for block in blocks:
        ledger_row = {
            "ledger_id": f"ledger:{report_id}:{block['work_block_id']}",
            "source_report_id": report_id,
            "source_report_number": _clean(report.get("doc_id") or report.get("report_number")),
            "project_number": _clean(report.get("project_number")),
            "project_name": _clean(report.get("project_name")),
            "report_date": _clean(report.get("report_date")),
            "work_block_id": block["work_block_id"],
            "title": block.get("title"),
            "authority_owner": "daily_reports",
            "ledger_contract_version": "wp18c2.v1",
            "cost_code": block.get("cost_code"),
            "pay_item_id": block.get("pay_item_id"),
            "customer_pay_item_number": block.get("customer_pay_item_number"),
            "primary_work_type_id": block.get("primary_work_type_id"),
            "work_type_ids": block.get("work_type_ids") or [],
            "schedule_activity_id": block.get("schedule_activity_id"),
            "schedule_actual_proposal_status": block.get("schedule_actual_proposal_status") or "proposed_only",
            "installed_quantity": round(_to_float(block.get("installed_quantity"), 0.0), 4),
            "unit": _clean(block.get("unit")),
            "resource_counts": {
                "labor": len(block.get("labor_entries") or []),
                "equipment": len(block.get("equipment_entries") or []),
                "materials": len(block.get("material_entries") or []),
                "subcontractors": len(block.get("subcontractor_entries") or []),
                "constraints": len(block.get("constraint_entries") or []),
            },
            "block": _sanitize(block),
            "created_at": _utcnow(),
        }
        await db[COLL_WORK_LEDGER].replace_one(
            {"source_report_id": report_id, "work_block_id": block["work_block_id"]},
            ledger_row,
            upsert=True,
        )
    return {"work_blocks": blocks, "work_block_summary": summary}


def _derive_crew_observation(report: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    project_number = _clean(report.get("project_number"))
    members = []
    for row in report.get("masci_crews") or []:
        name = _clean(row.get("employee_id") or row.get("name") or row.get("employee_name_snapshot"))
        if name:
            members.append(name)
    members = sorted(dict.fromkeys(members))
    if not project_number or len(members) < 2:
        return None
    leader = _clean(report.get("superintendent") or report.get("prepared_by") or members[0])
    signature = _fingerprint([project_number, leader, *members])
    source_record_id = _clean(report.get("id") or report.get("doc_id") or signature)
    confidence_score = min(0.95, 0.45 + (0.08 * len(members)))
    return {
        "observation_id": f"crew-observation:{project_number}:{source_record_id}",
        "project_number": project_number,
        "project_name": _clean(report.get("project_name")),
        "source_record_id": source_record_id,
        "source_report_number": _clean(report.get("doc_id") or report.get("report_number")),
        "observed_on": _clean(report.get("report_date") or report.get("created_at")),
        "leader": leader,
        "members": members,
        "member_count": len(members),
        "equipment_units": sorted(
            {
                _clean(row.get("equipment_id") or row.get("asset_id") or row.get("description") or row.get("unit_number"))
                for row in (report.get("equipment") or [])
                if _clean(row.get("equipment_id") or row.get("asset_id") or row.get("description") or row.get("unit_number"))
            }
        ),
        "signature": signature,
        "confidence_score": round(confidence_score, 3),
        "confidence": "high" if confidence_score >= 0.75 else "medium",
        "explainability": {
            "leader_source": "daily_reports.superintendent_or_prepared_by",
            "member_source": "daily_reports.masci_crews",
            "equipment_source": "daily_reports.equipment",
        },
        "created_at": _utcnow(),
        "updated_at": _utcnow(),
    }


async def sync_crew_observation_for_report(db, report: Dict[str, Any], *, foundation_ready: bool = False) -> Optional[Dict[str, Any]]:
    if not foundation_ready:
        await ensure_project_controls_foundation(db)
    observation = _derive_crew_observation(report)
    if not observation:
        return None
    await db[COLL_CREW_OBSERVATIONS].replace_one(
        {"project_number": observation["project_number"], "source_record_id": observation["source_record_id"]},
        observation,
        upsert=True,
    )
    return _sanitize(observation)


async def list_project_crew_intelligence(db, project_number: str) -> Dict[str, Any]:
    await ensure_project_controls_foundation(db)
    observations = [
        _sanitize(row)
        async for row in db[COLL_CREW_OBSERVATIONS].find({"project_number": project_number}, {"_id": 0}).sort("observed_on", -1).limit(250)
    ]
    confirmed = [
        _sanitize(row)
        async for row in db[COLL_CONFIRMED_CREWS].find({"project_number": project_number}, {"_id": 0}).sort("updated_at", -1).limit(100)
    ]
    review_index = {
        row.get("review_id"): row
        for row in await list_review_queue(db, project_number=project_number)
        if row.get("review_type") == "crew_pattern_review"
    }
    grouped: Dict[str, Dict[str, Any]] = {}
    for row in observations:
        sig = _clean(row.get("signature"))
        if not sig:
            continue
        bucket = grouped.setdefault(
            sig,
            {
                "suggestion_id": f"crew-suggestion:{project_number}:{sig}",
                "project_number": project_number,
                "leader": row.get("leader") or "",
                "members": list(row.get("members") or []),
                "member_count": int(row.get("member_count") or 0),
                "equipment_units": Counter(),
                "first_seen": row.get("observed_on") or row.get("created_at") or "",
                "last_seen": row.get("observed_on") or row.get("created_at") or "",
                "observation_count": 0,
                "source_record_ids": [],
                "confidence_score": 0.0,
            },
        )
        bucket["observation_count"] += 1
        bucket["source_record_ids"].append(row.get("source_record_id"))
        bucket["confidence_score"] = max(float(bucket["confidence_score"]), float(row.get("confidence_score") or 0.0))
        obs_date = _clean(row.get("observed_on") or row.get("created_at"))
        if obs_date and (not bucket["first_seen"] or obs_date < bucket["first_seen"]):
            bucket["first_seen"] = obs_date
        if obs_date and (not bucket["last_seen"] or obs_date > bucket["last_seen"]):
            bucket["last_seen"] = obs_date
        bucket["equipment_units"].update(row.get("equipment_units") or [])

    confirmed_signatures = {row.get("signature") for row in confirmed if row.get("signature")}
    suggestions: List[Dict[str, Any]] = []
    for sig, bucket in grouped.items():
        if sig in confirmed_signatures:
            continue
        suggestion_id = bucket["suggestion_id"]
        review = review_index.get(f"review:crew:{project_number}:{sig}") or {}
        confidence = min(0.98, float(bucket["confidence_score"]) + (0.06 * max(bucket["observation_count"] - 1, 0)))
        suggestions.append(
            {
                "suggestion_id": suggestion_id,
                "project_number": project_number,
                "leader": bucket["leader"],
                "members": bucket["members"],
                "member_count": bucket["member_count"],
                "equipment_units": sorted(bucket["equipment_units"].keys()),
                "first_seen": bucket["first_seen"],
                "last_seen": bucket["last_seen"],
                "observation_count": bucket["observation_count"],
                "source_record_ids": bucket["source_record_ids"],
                "confidence_score": round(confidence, 3),
                "confidence": "high" if confidence >= 0.8 else ("medium" if confidence >= 0.6 else "review_required"),
                "status": review.get("status") or "pending_review",
                "review_note": review.get("reason") or "Observed recurring crew pattern requires human confirmation.",
            }
        )
    suggestions.sort(key=lambda row: (-row["observation_count"], -row["confidence_score"], row["leader"]))
    return {"confirmed_crews": confirmed, "suggestions": suggestions[:50], "observations": observations[:50]}


async def confirm_project_crew(db, project_number: str, payload: Dict[str, Any], *, actor: Dict[str, Any]) -> Dict[str, Any]:
    await ensure_project_controls_foundation(db)
    suggestion_id = _clean(payload.get("suggestion_id"))
    members = sorted(dict.fromkeys([_clean(item) for item in (payload.get("members") or []) if _clean(item)]))
    leader = _clean(payload.get("leader"))
    signature = _clean(payload.get("signature"))
    if suggestion_id:
        crew_data = await list_project_crew_intelligence(db, project_number)
        match = next((row for row in crew_data.get("suggestions") or [] if row.get("suggestion_id") == suggestion_id), None)
        if not match:
            raise LookupError("crew_suggestion_not_found")
        members = members or list(match.get("members") or [])
        leader = leader or _clean(match.get("leader"))
        signature = signature or _clean(match.get("suggestion_id").split(":")[-1])
    if len(members) < 2:
        raise ValueError("confirmed_crew_requires_two_members")
    crew_name = _clean(payload.get("crew_name") or f"{leader or members[0]} Crew")
    now = _utcnow()
    crew_id = _clean(payload.get("crew_id") or f"crew:{project_number}:{_norm(crew_name)}:{uuid4().hex[:6]}")
    existing = await db[COLL_CONFIRMED_CREWS].find_one({"project_number": project_number, "crew_id": crew_id}, {"_id": 0})
    doc = {
        "crew_id": crew_id,
        "project_number": project_number,
        "crew_name": crew_name,
        "leader": leader,
        "members": members,
        "member_count": len(members),
        "effective_start": _clean(payload.get("effective_start") or now),
        "effective_end": _clean(payload.get("effective_end")),
        "facility_scope": _clean(payload.get("facility_scope")),
        "project_scope": project_number,
        "lifecycle_status": _status(payload.get("lifecycle_status") or "active", allowed=["draft", "active", "inactive", "archived"], default="active"),
        "source": _clean(payload.get("source") or ("crew_pattern_confirmation" if suggestion_id else "manual_confirmed_crew")),
        "confirmation_authority": _actor_label(actor),
        "confidence": _clean(payload.get("confidence") or "human_confirmed"),
        "signature": signature or _fingerprint([project_number, leader, *members]),
        "history": list((existing or {}).get("history") or []),
        "created_at": (existing or {}).get("created_at") or now,
        "created_by": (existing or {}).get("created_by") or _actor_label(actor),
        "updated_at": now,
        "updated_by": _actor_label(actor),
    }
    doc["history"].append({"at": now, "actor": _actor_label(actor), "event": "confirmed", "member_count": len(members)})
    await db[COLL_CONFIRMED_CREWS].replace_one({"project_number": project_number, "crew_id": crew_id}, doc, upsert=True)
    if suggestion_id or signature:
        review_sig = signature or suggestion_id.split(":")[-1]
        await _mark_review_resolved(db, f"review:crew:{project_number}:{review_sig}", actor=actor, resolution_note="Crew suggestion confirmed by human operator.")
    await _write_audit(db, "crew_confirmed", actor, "confirmed_crew", crew_id, doc, before=existing)
    return _sanitize(doc)


async def set_crew_suggestion_review_state(db, project_number: str, suggestion_id: str, *, actor: Dict[str, Any], action: str, note: str = "") -> Dict[str, Any]:
    await ensure_project_controls_foundation(db)
    signature = suggestion_id.split(":")[-1]
    status_map = {"accept": "resolved", "reject": "rejected", "defer": "deferred"}
    if action not in status_map:
        raise ValueError("unsupported_crew_review_action")
    review = await _upsert_review_item(
        db,
        {
            "review_id": f"review:crew:{project_number}:{signature}",
            "project_number": project_number,
            "review_type": "crew_pattern_review",
            "status": status_map[action],
            "priority": 70,
            "source_collection": COLL_CREW_OBSERVATIONS,
            "source_record_id": suggestion_id,
            "title": f"Crew suggestion {action}",
            "reason": _clean(note) or f"Crew suggestion marked {action} by human operator.",
            "provenance": {"suggestion_id": suggestion_id, "action": action},
            "confidence": "human_required",
        },
    )
    await _write_audit(db, f"crew_suggestion_{action}", actor, "crew_suggestion", suggestion_id, review)
    return review


async def list_project_work_ledger(db, project_number: str, *, limit: int = 100) -> List[Dict[str, Any]]:
    await ensure_project_controls_foundation(db)
    return [_sanitize(row) async for row in db[COLL_WORK_LEDGER].find({"project_number": project_number}, {"_id": 0}).sort([("report_date", -1), ("source_report_id", -1)]).limit(min(max(limit, 1), 500))]


def _build_default_lookahead_from_schedule(project_number: str, schedule_payload: Dict[str, Any]) -> Dict[str, Any]:
    schedule = dict(schedule_payload.get("schedule") or {})
    tasks = list(schedule.get("tasks") or [])
    window = schedule.get("window") or {}
    anchor = _clean(window.get("anchor_date")) or datetime.now(timezone.utc).date().isoformat()
    window_start = _clean(window.get("start_date"))
    window_end = _clean(window.get("end_date"))
    focus_tasks = []
    for task in tasks[:20]:
        focus_tasks.append(
            {
                "code": _clean(task.get("code")),
                "title": _clean(task.get("item_name") or task.get("cpm_activity_name") or task.get("code")),
                "schedule_activity_id": _clean(task.get("cpm_activity_id")),
                "planned_start": _clean(task.get("current_committed_start_date") or task.get("baseline_start") or task.get("requested_start")),
                "planned_finish": _clean(task.get("current_committed_finish_date") or task.get("baseline_finish")),
                "responsible_party": _clean(task.get("planned_performer") or "PM / Field"),
                "constraint_refs": [],
                "notes": _clean(task.get("notes")),
            }
        )
    return {
        "lookahead_id": f"lookahead:{project_number}:current",
        "project_number": project_number,
        "window_days": 14,
        "anchor_date": anchor,
        "window_start_date": window_start,
        "window_end_date": window_end,
        "status": "draft",
        "published_at": "",
        "published_by": "",
        "version": 1,
        "tasks": focus_tasks,
        "constraints": [],
        "comparison_note": "Planned vs actual remains reviewed by PM; field actuals never overwrite schedule truth.",
        "created_at": _utcnow(),
        "updated_at": _utcnow(),
    }


async def get_project_lookahead(db, project_number: str) -> Dict[str, Any]:
    await ensure_project_controls_foundation(db)
    existing = await db[COLL_LOOKAHEAD].find_one({"project_number": project_number, "lookahead_id": f"lookahead:{project_number}:current"}, {"_id": 0})
    if existing:
        return _sanitize(existing)
    assignments = await load_project_assignments(db, project_number)
    schedule = build_schedule_snapshot(assignments, None)
    payload = _build_default_lookahead_from_schedule(project_number, {"schedule": schedule})
    await db[COLL_LOOKAHEAD].insert_one(payload)
    return _sanitize(payload)


async def save_project_lookahead(db, project_number: str, payload: Dict[str, Any], *, actor: Dict[str, Any]) -> Dict[str, Any]:
    await ensure_project_controls_foundation(db)
    existing = await get_project_lookahead(db, project_number)
    updated = deepcopy(existing)
    updated["status"] = _status(payload.get("status") or updated.get("status") or "draft", allowed=["draft", "published", "archived"], default="draft")
    updated["tasks"] = _sanitize(payload.get("tasks") or updated.get("tasks") or [])
    updated["constraints"] = _sanitize(payload.get("constraints") or updated.get("constraints") or [])
    updated["comparison_note"] = _clean(payload.get("comparison_note") or updated.get("comparison_note") or "")
    updated["version"] = int(updated.get("version") or 1) + 1
    updated["updated_at"] = _utcnow()
    updated["updated_by"] = _actor_label(actor)
    if updated["status"] == "published":
        updated["published_at"] = updated.get("published_at") or updated["updated_at"]
        updated["published_by"] = updated.get("published_by") or _actor_label(actor)
    await db[COLL_LOOKAHEAD].replace_one({"project_number": project_number, "lookahead_id": updated["lookahead_id"]}, updated, upsert=True)
    await _write_audit(db, "project_lookahead_saved", actor, "project_lookahead", updated["lookahead_id"], updated, before=existing)
    return _sanitize(updated)


async def get_project_controls_overview(db, project_number: str) -> Dict[str, Any]:
    await ensure_project_controls_foundation(db)
    job = await _load_job(db, project_number)
    pay_items = await list_project_pay_items(db, project_number)
    mappings = await list_project_mappings(db, project_number)
    review_items = await list_review_queue(db, project_number=project_number)
    lookahead = await get_project_lookahead(db, project_number)
    lifecycle = await get_project_lifecycle(db, project_number)
    crew = await list_project_crew_intelligence(db, project_number)
    assignments = await load_project_assignments(db, project_number)
    planning_readiness = build_planning_readiness(assignments)
    schedule = build_schedule_snapshot(assignments, None)
    planning_lifecycle = build_planning_lifecycle_snapshot(
        planning_readiness=planning_readiness,
        stored={},
        schedule_window=schedule.get("window") or {},
    )
    work_ledger = await list_project_work_ledger(db, project_number, limit=25)
    latest_reports = [
        _sanitize(row)
        async for row in db.daily_reports.find({"project_number": project_number}, {"_id": 0, "id": 1, "doc_id": 1, "report_date": 1, "work_block_summary": 1, "work_blocks": 1}).sort("report_date", -1).limit(10)
    ]
    return {
        "project": {
            "project_number": project_number,
            "project_name": job.get("project_name") or job.get("name") or project_number,
            "pm_email": job.get("pm_email") or "",
            "co_pm_emails": job.get("co_pm_emails") or [],
        },
        "authority_boundaries": {
            "project_identity": "jobs_master",
            "enterprise_work_types": COLL_WORK_TYPES,
            "project_pay_items": COLL_PAY_ITEMS,
            "governed_mappings": COLL_MAPPINGS,
            "project_schedule_truth": "cost_codes.schedule_engine",
            "lookahead_truth": COLL_LOOKAHEAD,
            "daily_field_actuals": "daily_reports",
            "constraints_truth": "operational_constraints",
            "crew_confirmation_truth": COLL_CONFIRMED_CREWS,
            "archive_truth": COLL_LIFECYCLE,
            "ai_role": "advisory_only",
        },
        "counts": {
            "pay_items": len(pay_items),
            "approved_mappings": sum(1 for row in mappings if row.get("status") == "approved"),
            "mapping_reviews": sum(1 for row in review_items if row.get("review_type") == "pay_item_mapping_required" and row.get("status") != "resolved"),
            "crew_suggestions": len(crew.get("suggestions") or []),
            "confirmed_crews": len(crew.get("confirmed_crews") or []),
            "work_ledger_rows": len(work_ledger),
        },
        "lifecycle": lifecycle,
        "lookahead": lookahead,
        "schedule_authority": {
            "planning_readiness": planning_readiness,
            "planning_lifecycle": planning_lifecycle,
            "schedule_window": schedule.get("window") or {},
            "task_count": len(schedule.get("tasks") or []),
        },
        "crew_intelligence": crew,
        "latest_work_ledger": work_ledger,
        "latest_reports": latest_reports,
        "event_contracts": EVENT_CONTRACTS,
    }


async def get_admin_project_controls_overview(db) -> Dict[str, Any]:
    await ensure_project_controls_foundation(db)
    work_types = await list_enterprise_work_types(db, include_archived=True)
    review_items = await list_review_queue(db)
    pay_item_count = await db[COLL_PAY_ITEMS].count_documents({})
    mapping_count = await db[COLL_MAPPINGS].count_documents({})
    lookahead_count = await db[COLL_LOOKAHEAD].count_documents({})
    confirmed_crews = await db[COLL_CONFIRMED_CREWS].count_documents({})
    ledger_rows = await db[COLL_WORK_LEDGER].count_documents({})
    projects_with_pay_items = await db[COLL_PAY_ITEMS].distinct("project_number")
    return {
        "summary": {
            "enterprise_work_types": len(work_types),
            "project_pay_items": pay_item_count,
            "governed_mappings": mapping_count,
            "review_queue_open": sum(1 for row in review_items if row.get("status") not in {"resolved", "rejected"}),
            "lookaheads": lookahead_count,
            "confirmed_crews": confirmed_crews,
            "work_ledger_rows": ledger_rows,
            "projects_with_pay_items": len(projects_with_pay_items),
        },
        "work_types": work_types,
        "review_queue": review_items[:100],
        "event_contracts": EVENT_CONTRACTS,
    }


async def run_project_controls_backfill(db, *, force: bool = False) -> Dict[str, Any]:
    await _ensure_indexes(db)
    await _seed_work_types(db)
    run_id = f"wp18c2-backfill:{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}"
    ledger_reports = 0
    crew_observations = 0
    pay_item_reviews = 0
    lifecycle_seeded = 0
    last_run = await db[COLL_RUNS].find_one({"run_type": "wp18c2_backfill"}, {"_id": 0})
    if last_run and not force:
        return _sanitize(last_run)

    async for report in db.daily_reports.find({}, {"_id": 0}).sort("report_date", -1):
        sync_result = await sync_work_blocks_for_report(db, report, foundation_ready=True)
        report_patch = {
            "work_blocks": sync_result["work_blocks"],
            "work_block_summary": sync_result["work_block_summary"],
            "work_blocks_version": "wp18c2.v1",
            "work_blocks_governed_at": _utcnow(),
        }
        await db.daily_reports.update_one({"id": report.get("id")}, {"$set": report_patch})
        ledger_reports += 1
        obs = await sync_crew_observation_for_report(db, {**report, **report_patch}, foundation_ready=True)
        if obs:
            crew_observations += 1

    async for job in db.jobs_master.find({"project_number": {"$ne": ""}}, {"_id": 0, "project_number": 1, "project_name": 1, "name": 1, "assigned_cost_codes": 1, "status": 1, "project_status": 1, "active": 1, "archived": 1}):
        project_number = _clean(job.get("project_number"))
        if not project_number:
            continue
        lifecycle = await get_project_lifecycle(db, project_number)
        if lifecycle:
            lifecycle_seeded += 1
        pay_item_total = await db[COLL_PAY_ITEMS].count_documents({"project_number": project_number})
        if pay_item_total == 0 and (job.get("assigned_cost_codes") or []):
            await _upsert_review_item(
                db,
                {
                    "review_id": f"review:pay-item-foundation:{project_number}",
                    "project_number": project_number,
                    "review_type": "project_pay_item_authority_missing",
                    "status": "review_required",
                    "priority": 80,
                    "source_collection": "jobs_master",
                    "source_record_id": project_number,
                    "title": f"Project pay items not yet entered for {project_number}",
                    "reason": "Project has governed planning/cost-code setup but no customer pay-item authority entered yet. Original project identity is preserved; no pay items were fabricated.",
                    "provenance": {
                        "project_name": job.get("project_name") or job.get("name") or project_number,
                        "assigned_cost_codes_count": len(job.get("assigned_cost_codes") or []),
                    },
                    "confidence": "human_required",
                },
            )
            pay_item_reviews += 1

    report = {
        "run_id": run_id,
        "run_type": "wp18c2_backfill",
        "ran_at": _utcnow(),
        "force": force,
        "ledger_reports_processed": ledger_reports,
        "crew_observations_written": crew_observations,
        "project_pay_item_reviews_opened": pay_item_reviews,
        "project_lifecycle_records_seeded": lifecycle_seeded,
    }
    await db[COLL_RUNS].replace_one({"run_type": "wp18c2_backfill"}, report, upsert=True)
    return _sanitize(report)


async def ensure_project_controls_foundation(db, *, force_backfill: bool = False) -> Dict[str, Any]:
    await _ensure_indexes(db)
    seed = await _seed_work_types(db)
    if force_backfill:
        backfill = await run_project_controls_backfill(db, force=True)
    else:
        last_run = await db[COLL_RUNS].find_one({"run_type": "wp18c2_backfill"}, {"_id": 0})
        backfill = _sanitize(last_run or {"run_type": "wp18c2_backfill", "status": "pending_manual_run"})
    return {"ok": True, "seed": seed, "backfill": backfill}
