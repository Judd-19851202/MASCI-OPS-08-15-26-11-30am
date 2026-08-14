from __future__ import annotations

import asyncio
from collections import defaultdict
from copy import deepcopy
from datetime import date, datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

from services.project_controls_authority import (
    _actor_label,
    _clean,
    _sanitize,
    _status,
    _to_float,
    _write_audit,
)
from services.project_schedule_authority import (
    COLL_SCHEDULE_ACTIVITIES,
    COLL_SCHEDULE_REVIEW,
    COLL_SCHEDULE_VERSIONS,
    COLL_WORK_PACKAGES,
    ensure_project_schedule_foundation,
    get_reconciled_schedule_lookahead,
    list_schedule_activities,
    list_schedule_versions,
)
from lib.kpi_percent_complete import schedule_rollup_percent, SCHEDULE_MODE_MEAN


COLL_SCHEDULE_ACTUAL_CANDIDATES = "project_schedule_actual_candidates"
COLL_DAILY_WORK_PLANS = "project_daily_work_plans"
COLL_SCHEDULE_ACTUAL_RUNS = "project_schedule_actual_runs"

REVIEW_STATUSES = ["pending_review", "review_required", "approved", "rejected", "deferred"]
PLAN_STATUSES = ["draft", "published", "archived"]
SCHEDULE_PROGRESS_STATUSES = ["not_started", "in_progress", "completed"]


_ACTUALS_FOUNDATION_READY_DBS: set[str] = set()
_ACTUALS_FOUNDATION_READY_LOCK = asyncio.Lock()


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _as_date(value: Any) -> Optional[date]:
    text = _clean(value)[:10]
    if not text:
        return None
    try:
        return date.fromisoformat(text)
    except ValueError:
        return None


def _date_text(value: Any) -> str:
    parsed = _as_date(value)
    return parsed.isoformat() if parsed else ""


def _hours_from_row(row: Dict[str, Any]) -> float:
    return round(
        _to_float(row.get("hours"), 0.0)
        or _to_float(row.get("reported_hours"), 0.0)
        or _to_float(row.get("hours_used"), 0.0)
        or _to_float(row.get("regular_hours"), 0.0),
        4,
    )


async def _ensure_indexes(db) -> None:
    await db[COLL_SCHEDULE_ACTUAL_CANDIDATES].create_index([("project_number", 1), ("candidate_id", 1)], unique=True)
    await db[COLL_SCHEDULE_ACTUAL_CANDIDATES].create_index([("project_number", 1), ("review_status", 1), ("report_date", -1)])
    await db[COLL_SCHEDULE_ACTUAL_CANDIDATES].create_index([("project_number", 1), ("report_date", -1), ("source_report_id", -1)])
    await db[COLL_SCHEDULE_ACTUAL_CANDIDATES].create_index([("source_report_id", 1), ("work_block_id", 1), ("version_id", 1)], unique=True)
    await db[COLL_SCHEDULE_ACTUAL_CANDIDATES].create_index([("project_number", 1), ("activity_resolution.resolved_activity_id", 1), ("review_status", 1)])
    await db[COLL_DAILY_WORK_PLANS].create_index([("project_number", 1), ("work_date", 1)], unique=True)
    await db[COLL_SCHEDULE_ACTUAL_RUNS].create_index([("run_type", 1)], unique=True)


async def ensure_schedule_actuals_foundation(db) -> Dict[str, Any]:
    await ensure_project_schedule_foundation(db)
    db_key = str(getattr(db, "name", "")) or COLL_SCHEDULE_ACTUAL_CANDIDATES
    if db_key not in _ACTUALS_FOUNDATION_READY_DBS:
        async with _ACTUALS_FOUNDATION_READY_LOCK:
            if db_key not in _ACTUALS_FOUNDATION_READY_DBS:
                await _ensure_indexes(db)
                _ACTUALS_FOUNDATION_READY_DBS.add(db_key)
    latest = await db[COLL_SCHEDULE_ACTUAL_RUNS].find_one({"run_type": "wp18c5_actuals_backfill"}, {"_id": 0})
    return {
        "ok": True,
        "candidate_collection": COLL_SCHEDULE_ACTUAL_CANDIDATES,
        "daily_work_plan_collection": COLL_DAILY_WORK_PLANS,
        "backfill": _sanitize(latest or {"run_type": "wp18c5_actuals_backfill", "status": "pending_manual_run"}),
    }


async def _upsert_review_item(db, review: Dict[str, Any]) -> Dict[str, Any]:
    now = _utcnow()
    existing = await db[COLL_SCHEDULE_REVIEW].find_one({"review_id": review["review_id"]}, {"_id": 0})
    doc = {**(existing or {}), **_sanitize(review), "created_at": (existing or {}).get("created_at") or now, "updated_at": now}
    await db[COLL_SCHEDULE_REVIEW].replace_one({"review_id": doc["review_id"]}, doc, upsert=True)
    return _sanitize(doc)


async def _resolve_review_item(db, review_id: str, *, actor: Optional[Dict[str, Any]] = None, note: str = "") -> None:
    existing = await db[COLL_SCHEDULE_REVIEW].find_one({"review_id": review_id}, {"_id": 0})
    if not existing:
        return
    existing["status"] = "resolved"
    existing["resolution_note"] = _clean(note) or "Resolved by governed C5 actuals action."
    existing["resolved_at"] = _utcnow()
    existing["resolved_by"] = _actor_label(actor)
    existing["updated_at"] = _utcnow()
    await db[COLL_SCHEDULE_REVIEW].replace_one({"review_id": review_id}, existing, upsert=True)


def _candidate_id(project_number: str, version_id: str, report_id: str, work_block_id: str) -> str:
    return f"schedule-actual:{project_number}:{version_id}:{report_id}:{work_block_id}"


def _plan_id(project_number: str, work_date: str) -> str:
    return f"daily-work-plan:{project_number}:{work_date}"


def _norm_key(value: Any) -> str:
    return _clean(value).strip().lower()


def _dedupe_rows(rows: List[Dict[str, Any]], *, id_key: str = "id", label_key: str = "label") -> List[Dict[str, Any]]:
    seen = set()
    out: List[Dict[str, Any]] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        key = (_clean(row.get(id_key)) or _clean(row.get(label_key))).lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(_sanitize(row))
    return out


async def _registry_maps(db) -> Dict[str, Dict[str, Dict[str, Any]]]:
    suppliers = [row async for row in db.suppliers.find({"is_active": {"$ne": False}}, {"_id": 0})]
    equipment = [row async for row in db.equipment_master.find({"$or": [{"is_active": {"$ne": False}}, {"active": {"$ne": False}}]}, {"_id": 0})]
    return {
        "supplier_by_id": {str(row.get("id") or "").lower(): row for row in suppliers if _clean(row.get("id"))},
        "supplier_by_name": {str(row.get("name") or "").lower(): row for row in suppliers if _clean(row.get("name"))},
        "equipment_by_id": {str(row.get("id") or row.get("equipment_master_id") or "").lower(): row for row in equipment if _clean(row.get("id") or row.get("equipment_master_id"))},
        "equipment_by_unit": {str(row.get("unit_number") or row.get("asset_number") or "").lower(): row for row in equipment if _clean(row.get("unit_number") or row.get("asset_number"))},
        "equipment_by_label": {str(row.get("display_label") or row.get("make_model") or "").lower(): row for row in equipment if _clean(row.get("display_label") or row.get("make_model"))},
    }


def _resolve_supplier_row(row: Dict[str, Any], registry: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    supplier_id = _clean(row.get("vendor_id") or row.get("supplier_id") or row.get("id"))
    supplier_name = _clean(row.get("vendor_name") or row.get("supplier") or row.get("company") or row.get("subcontractor_name") or row.get("name") or row.get("description"))
    doc = None
    confidence = "review_required"
    if supplier_id:
        doc = (registry.get("supplier_by_id") or {}).get(supplier_id.lower())
        if doc:
            confidence = "high"
    if not doc and supplier_name:
        doc = (registry.get("supplier_by_name") or {}).get(supplier_name.lower())
        if doc:
            confidence = "medium"
    return {
        "source_supplier_id": supplier_id,
        "source_supplier_name": supplier_name,
        "resolved_supplier_id": _clean((doc or {}).get("id")),
        "resolved_supplier_name": _clean((doc or {}).get("name") or supplier_name),
        "confidence": confidence,
        "registry_status": "resolved" if doc else "review_required",
    }


def _resolve_equipment_row(row: Dict[str, Any], registry: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
    equipment_id = _clean(row.get("equipment_id") or row.get("asset_id") or row.get("equipment_master_id") or row.get("id"))
    unit_number = _clean(row.get("unit_number") or row.get("description") or row.get("label"))
    doc = None
    confidence = "review_required"
    if equipment_id:
        doc = (registry.get("equipment_by_id") or {}).get(equipment_id.lower())
        if doc:
            confidence = "high"
    if not doc and unit_number:
        unit_key = unit_number.lower()
        doc = (registry.get("equipment_by_unit") or {}).get(unit_key) or (registry.get("equipment_by_label") or {}).get(unit_key)
        if doc:
            confidence = "medium"
    return {
        "source_equipment_id": equipment_id,
        "source_equipment_label": unit_number,
        "resolved_equipment_id": _clean((doc or {}).get("id") or (doc or {}).get("equipment_master_id")),
        "resolved_unit_number": _clean((doc or {}).get("unit_number") or (doc or {}).get("asset_number") or unit_number),
        "confidence": confidence,
        "registry_status": "resolved" if doc else "review_required",
        "hours": _hours_from_row(row),
    }


def _activity_match_score(block: Dict[str, Any], activity: Dict[str, Any], report_date: str) -> Tuple[int, List[str]]:
    score = 0
    reasons: List[str] = []
    if _clean(block.get("schedule_activity_id")) and _clean(block.get("schedule_activity_id")) == _clean(activity.get("activity_id")):
        return 120, ["Exact schedule activity ID preserved from the Daily Report work block."]
    if _clean(block.get("customer_pay_item_number")) and _clean(block.get("customer_pay_item_number")) == _clean(activity.get("customer_pay_item_number")):
        score += 42
        reasons.append("Exact customer pay-item link matched the active governed schedule.")
    if _clean(block.get("cost_code")) and _clean(block.get("cost_code")) == _clean(activity.get("project_cost_code")):
        score += 36
        reasons.append("Exact project cost-code link matched the active governed schedule.")
    if _clean(block.get("work_package_id")) and _clean(block.get("work_package_id")) == _clean(activity.get("work_package_id")):
        score += 22
        reasons.append("Work package alignment matched the active governed schedule.")
    block_work_types = {_norm_key(item) for item in (block.get("work_type_ids") or []) if _clean(item)}
    activity_work_types = {_norm_key(activity.get("enterprise_work_type_id"))}
    if block_work_types & activity_work_types:
        score += 12
        reasons.append("Work-type evidence overlapped with the active governed schedule.")
    report_dt = _as_date(report_date)
    start_dt = _as_date(activity.get("planned_start_date"))
    finish_dt = _as_date(activity.get("planned_finish_date"))
    if report_dt and start_dt and finish_dt and start_dt <= report_dt <= finish_dt:
        score += 8
        reasons.append("Report date fell within the current schedule activity window.")
    if _clean(block.get("title")) and _clean(block.get("title")).lower() in _clean(activity.get("activity_name")).lower():
        score += 6
        reasons.append("Work-block title overlapped the activity name.")
    return score, reasons


def _resolve_activity(block: Dict[str, Any], activities: List[Dict[str, Any]], report_date: str) -> Dict[str, Any]:
    explicit_id = _clean(block.get("schedule_activity_id"))
    if explicit_id:
        exact = next((row for row in activities if _clean(row.get("activity_id")) == explicit_id), None)
        if exact:
            return {
                "resolved_activity_id": exact.get("activity_id") or "",
                "resolved_activity_name": exact.get("activity_name") or "",
                "confidence": "high",
                "match_basis": "explicit_schedule_activity_id",
                "score": 120,
                "reasons": ["Exact schedule activity ID preserved from the work block."],
                "alternative_activity_ids": [],
            }
        return {
            "resolved_activity_id": "",
            "resolved_activity_name": "",
            "confidence": "review_required",
            "match_basis": "explicit_schedule_activity_id_missing_from_active_version",
            "score": 0,
            "reasons": ["The Daily Report preserved a schedule activity ID, but it does not exist on the active schedule version."],
            "alternative_activity_ids": [],
        }
    scored: List[Tuple[int, Dict[str, Any], List[str]]] = []
    for activity in activities:
        score, reasons = _activity_match_score(block, activity, report_date)
        if score > 0:
            scored.append((score, activity, reasons))
    if not scored:
        return {
            "resolved_activity_id": "",
            "resolved_activity_name": "",
            "confidence": "review_required",
            "match_basis": "no_reusable_activity_match",
            "score": 0,
            "reasons": ["No active schedule activity could be matched safely from the preserved work-block evidence."],
            "alternative_activity_ids": [],
        }
    scored.sort(key=lambda item: (-item[0], item[1].get("activity_id") or ""))
    best_score, best_activity, best_reasons = scored[0]
    alternatives = [row.get("activity_id") for _, row, _ in scored[1:4] if _clean(row.get("activity_id"))]
    ambiguous = len(scored) > 1 and scored[1][0] == best_score and best_score < 100
    if best_score < 35 or ambiguous:
        reason = "Multiple active schedule activities remained plausible; PM review is required." if ambiguous else "The available evidence is too weak to create a schedule authority link automatically."
        return {
            "resolved_activity_id": "",
            "resolved_activity_name": "",
            "confidence": "review_required",
            "match_basis": "review_required",
            "score": best_score,
            "reasons": best_reasons + [reason],
            "alternative_activity_ids": alternatives[:3],
        }
    return {
        "resolved_activity_id": best_activity.get("activity_id") or "",
        "resolved_activity_name": best_activity.get("activity_name") or "",
        "confidence": "high" if best_score >= 80 else "medium",
        "match_basis": "scored_governed_match",
        "score": best_score,
        "reasons": best_reasons,
        "alternative_activity_ids": alternatives[:3],
    }


def _material_flow(block: Dict[str, Any], report: Dict[str, Any], *, block_count: int) -> Dict[str, Any]:
    delivered = []
    installed = []
    returned = []
    waste = []
    outbound_unclassified = []
    for row in block.get("material_entries") or []:
        if not isinstance(row, dict):
            continue
        quantity = round(_to_float(row.get("quantity") or row.get("installed_quantity"), 0.0), 4)
        common = {
            "material_id": _clean(row.get("material_id") or row.get("id")),
            "description": _clean(row.get("description") or row.get("material") or row.get("name")),
            "quantity": quantity,
            "unit": _clean(row.get("unit") or row.get("unit_of_measure")),
            "source_kind": "daily_reports.materials",
            "confidence": "preserved_source",
        }
        flow_kind = _clean(row.get("material_flow_kind") or row.get("entry_kind") or row.get("flow_kind")).lower()
        if flow_kind in {"installed", "consumed"}:
            installed.append(common)
        elif flow_kind == "returned":
            returned.append(common)
        elif flow_kind == "waste":
            waste.append(common)
        else:
            delivered.append(common)

    outbound_rows = [row for row in (report.get("outbound_materials") or []) if isinstance(row, dict)]
    if outbound_rows:
        if block_count == 1:
            for row in outbound_rows:
                outbound_unclassified.append(
                    {
                        "material_id": _clean(row.get("material_id") or row.get("id")),
                        "description": _clean(row.get("material") or row.get("description") or row.get("name")),
                        "quantity": round(_to_float(row.get("quantity"), 0.0), 4),
                        "unit": _clean(row.get("unit")),
                        "hauler": _clean(row.get("hauler")),
                        "destination": _clean(row.get("destination")),
                        "ticket_or_manifest": _clean(row.get("ticket_or_manifest")),
                        "notes": _clean(row.get("notes")),
                        "source_kind": "daily_reports.outbound_materials",
                        "confidence": "review_required",
                    }
                )
    review_required = bool(outbound_rows) or not installed
    return {
        "delivered": delivered,
        "installed": installed,
        "returned": returned,
        "waste": waste,
        "outbound_unclassified": outbound_unclassified,
        "review_required": review_required,
        "notes": [
            "Material deliveries remain distinct from installation or consumption.",
            "Outbound material rows are preserved separately until a PM classifies return versus waste when the source record is ambiguous.",
        ],
    }


def _candidate_review_reason(candidate: Dict[str, Any]) -> str:
    reasons = []
    resolution = candidate.get("activity_resolution") or {}
    if resolution.get("confidence") == "review_required":
        reasons.append("Schedule activity mapping still needs PM review.")
    unresolved_equipment = sum(1 for row in candidate.get("equipment_registry_links") or [] if row.get("registry_status") != "resolved")
    unresolved_suppliers = sum(1 for row in candidate.get("supplier_registry_links") or [] if row.get("registry_status") != "resolved")
    if unresolved_equipment:
        reasons.append(f"{unresolved_equipment} equipment linkage(s) still need governed registry confirmation.")
    if unresolved_suppliers:
        reasons.append(f"{unresolved_suppliers} supplier or subcontractor linkage(s) still need governed registry confirmation.")
    material_flow = candidate.get("material_flow") or {}
    if material_flow.get("review_required"):
        reasons.append("Material delivery / installation / outbound classification still needs PM review.")
    return " ".join(reasons) or "Daily Report facts are preserved as a candidate until PM approves the schedule actual."


async def _build_candidate(db, report: Dict[str, Any], block: Dict[str, Any], version: Dict[str, Any], activities: List[Dict[str, Any]], registry: Dict[str, Dict[str, Dict[str, Any]]]) -> Dict[str, Any]:
    report_id = _clean(report.get("id") or report.get("doc_id"))
    work_block_id = _clean(block.get("work_block_id")) or f"{report_id}:work-block"
    existing = await db[COLL_SCHEDULE_ACTUAL_CANDIDATES].find_one(
        {"source_report_id": report_id, "work_block_id": work_block_id, "version_id": version.get("version_id")},
        {"_id": 0},
    )
    activity_resolution = _resolve_activity(block, activities, _clean(report.get("report_date")))
    material_flow = _material_flow(block, report, block_count=len(report.get("work_blocks") or []))
    equipment_links = [_resolve_equipment_row(row, registry) for row in (block.get("equipment_entries") or []) if isinstance(row, dict)]
    supplier_links = [_resolve_supplier_row(row, registry) for row in (block.get("subcontractor_entries") or []) if isinstance(row, dict)]
    for row in block.get("material_entries") or []:
        if isinstance(row, dict) and (_clean(row.get("supplier")) or _clean(row.get("vendor_name"))):
            supplier_links.append(_resolve_supplier_row(row, registry))
    unique_supplier_links = _dedupe_rows(
        [
            {
                "id": row.get("resolved_supplier_id") or row.get("source_supplier_id") or row.get("source_supplier_name"),
                "label": row.get("resolved_supplier_name") or row.get("source_supplier_name"),
                **row,
            }
            for row in supplier_links
        ]
    )
    unique_equipment_links = _dedupe_rows(
        [
            {
                "id": row.get("resolved_equipment_id") or row.get("source_equipment_id") or row.get("resolved_unit_number"),
                "label": row.get("resolved_unit_number") or row.get("source_equipment_label"),
                **row,
            }
            for row in equipment_links
        ]
    )
    review_status = (existing or {}).get("review_status") or (
        "review_required"
        if activity_resolution.get("confidence") == "review_required"
        or any(row.get("registry_status") != "resolved" for row in unique_equipment_links)
        or any(row.get("registry_status") != "resolved" for row in unique_supplier_links)
        or material_flow.get("review_required")
        else "pending_review"
    )
    approved_actual = deepcopy((existing or {}).get("approved_actual") or {})
    candidate = {
        "candidate_id": _clean((existing or {}).get("candidate_id")) or _candidate_id(_clean(report.get("project_number")), version.get("version_id") or "", report_id, work_block_id),
        "project_number": _clean(report.get("project_number")),
        "project_name": _clean(report.get("project_name")),
        "version_id": version.get("version_id") or "",
        "baseline_version_id": version.get("baseline_version_id") or version.get("version_id") or "",
        "source_report_id": report_id,
        "source_report_number": _clean(report.get("doc_id") or report.get("report_number")),
        "report_date": _clean(report.get("report_date")),
        "work_block_id": work_block_id,
        "work_block_title": _clean(block.get("title") or "Work Block"),
        "review_status": _status(review_status or "pending_review", allowed=REVIEW_STATUSES, default="pending_review"),
        "activity_resolution": _sanitize(activity_resolution),
        "planned_links": {
            "work_package_id": _clean(block.get("work_package_id")),
            "phase_id": _clean(block.get("phase_id")),
            "customer_pay_item_number": _clean(block.get("customer_pay_item_number")),
            "pay_item_id": _clean(block.get("pay_item_id")),
            "cost_code": _clean(block.get("cost_code")),
        },
        "actual_facts": {
            "installed_quantity": round(_to_float(block.get("installed_quantity"), 0.0), 4),
            "unit": _clean(block.get("unit")),
            "location": _clean(block.get("location") or report.get("location")),
            "field_notes": _clean(block.get("field_notes")),
            "labor_entries": _sanitize(block.get("labor_entries") or []),
            "equipment_entries": _sanitize(block.get("equipment_entries") or []),
            "material_entries": _sanitize(block.get("material_entries") or []),
            "subcontractor_entries": _sanitize(block.get("subcontractor_entries") or []),
            "constraint_entries": _sanitize(block.get("constraint_entries") or []),
        },
        "equipment_registry_links": unique_equipment_links,
        "supplier_registry_links": unique_supplier_links,
        "material_flow": _sanitize(material_flow),
        "approved_actual": _sanitize(approved_actual),
        "review_note": _clean((existing or {}).get("review_note")),
        "review_history": list((existing or {}).get("review_history") or []),
        "provenance": {
            "candidate_contract_version": "wp18c5.v1",
            "source_daily_report_contract": _clean(report.get("work_blocks_version") or "wp18c2.v1"),
            "source_collection": "daily_reports",
            "source_report_sha256": _clean(report.get("audit_envelope_sha256")),
            "generated_at": _utcnow(),
            "generated_by": "project_schedule_actuals_spine",
        },
        "preserved_report_context": {
            "doc_id": _clean(report.get("doc_id") or report.get("report_number")),
            "prepared_by": _clean(report.get("prepared_by")),
            "report_date": _clean(report.get("report_date")),
            "project_number": _clean(report.get("project_number")),
            "project_name": _clean(report.get("project_name")),
        },
        "preserved_work_block_snapshot": _sanitize(block),
        "created_at": (existing or {}).get("created_at") or _utcnow(),
        "created_by": (existing or {}).get("created_by") or "project_schedule_actuals_spine",
        "updated_at": _utcnow(),
        "updated_by": "project_schedule_actuals_spine",
    }
    return candidate


async def _sync_candidate_review_item(db, candidate: Dict[str, Any], *, actor: Optional[Dict[str, Any]] = None) -> None:
    review_id = f"schedule-review:actual:{candidate['candidate_id']}"
    if candidate.get("review_status") in {"approved", "rejected"}:
        await _resolve_review_item(db, review_id, actor=actor, note="Schedule actual candidate resolved by PM action.")
        return
    await _upsert_review_item(
        db,
        {
            "review_id": review_id,
            "project_number": candidate.get("project_number"),
            "status": "review_required",
            "priority": 88,
            "source_kind": "schedule_actual_candidate",
            "source_record_id": candidate.get("candidate_id"),
            "title": f"Schedule actual candidate review required for {candidate.get('source_report_number') or candidate.get('source_report_id')}",
            "reason": _candidate_review_reason(candidate),
            "confidence": "human_required",
            "provenance": {
                "candidate_id": candidate.get("candidate_id"),
                "activity_resolution": candidate.get("activity_resolution"),
                "material_flow": candidate.get("material_flow"),
            },
        },
    )


async def _active_version(db, project_number: str) -> Optional[Dict[str, Any]]:
    versions = await list_schedule_versions(db, project_number)
    return next((row for row in versions if row.get("status") == "active"), None)


async def sync_schedule_actual_candidates_for_report(db, report: Dict[str, Any], *, actor: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    await ensure_schedule_actuals_foundation(db)
    project_number = _clean(report.get("project_number"))
    if not project_number:
        return {"count": 0, "items": []}
    active_version = await _active_version(db, project_number)
    if not active_version:
        return {"count": 0, "items": [], "status": "no_active_schedule_version"}
    activities = await list_schedule_activities(db, project_number, version_id=active_version.get("version_id") or "")
    registry = await _registry_maps(db)
    work_blocks = [row for row in (report.get("work_blocks") or []) if isinstance(row, dict)]
    items: List[Dict[str, Any]] = []
    for block in work_blocks:
        candidate = await _build_candidate(db, report, block, active_version, activities, registry)
        await db[COLL_SCHEDULE_ACTUAL_CANDIDATES].replace_one({"candidate_id": candidate["candidate_id"]}, candidate, upsert=True)
        await _sync_candidate_review_item(db, candidate, actor=actor)
        items.append(_sanitize(candidate))
    return {
        "count": len(items),
        "items": items,
        "approved": sum(1 for item in items if item.get("review_status") == "approved"),
        "pending": sum(1 for item in items if item.get("review_status") in {"pending_review", "review_required", "deferred"}),
        "version_id": active_version.get("version_id"),
    }


async def list_schedule_actual_candidates(db, project_number: str, *, status: str = "", report_id: str = "") -> List[Dict[str, Any]]:
    await ensure_schedule_actuals_foundation(db)
    query: Dict[str, Any] = {"project_number": project_number}
    if _clean(status):
        query["review_status"] = _status(status, allowed=REVIEW_STATUSES, default="pending_review")
    if _clean(report_id):
        query["source_report_id"] = _clean(report_id)
    return [_sanitize(row) async for row in db[COLL_SCHEDULE_ACTUAL_CANDIDATES].find(query, {"_id": 0}).sort([("report_date", -1), ("source_report_id", -1)])]


async def list_schedule_actual_candidates_for_report(db, report_id: str) -> List[Dict[str, Any]]:
    return [_sanitize(row) async for row in db[COLL_SCHEDULE_ACTUAL_CANDIDATES].find({"source_report_id": _clean(report_id)}, {"_id": 0}).sort([("updated_at", -1)])]


async def _sync_work_package_actual_state(db, project_number: str, version_id: str, work_package_id: str) -> None:
    if not _clean(work_package_id):
        return
    activities = [
        row
        async for row in db[COLL_SCHEDULE_ACTIVITIES].find(
            {"project_number": project_number, "version_id": version_id, "work_package_id": work_package_id},
            {"_id": 0},
        )
    ]
    if not activities:
        return
    actual_links = {
        "daily_report_ids": sorted({report_id for row in activities for report_id in ((row.get("actual_links") or {}).get("daily_report_ids") or []) if _clean(report_id)}),
        "work_block_ids": sorted({block_id for row in activities for block_id in ((row.get("actual_links") or {}).get("work_block_ids") or []) if _clean(block_id)}),
    }
    actual_totals = {
        "approved_activity_count": sum(1 for row in activities if ((row.get("actual_state") or {}).get("status") not in {None, "", "not_started"})),
        # PC-SCHEDULE / SCHEDULE_MODE_MEAN (Wave 5): unweighted average of activity
        # approved progress across this work package. Explicit governed mode.
        "approved_percent_complete_average": schedule_rollup_percent(
            [(row.get("actual_state") or {}).get("approved_percent_complete") for row in activities],
            agg=SCHEDULE_MODE_MEAN,
        ),
        "installed_quantity_total": round(sum(_to_float((row.get("actual_state") or {}).get("installed_quantity_total"), 0.0) for row in activities), 4),
        "labor_hours_total": round(sum(_to_float((row.get("actual_state") or {}).get("labor_hours_total"), 0.0) for row in activities), 4),
    }
    await db[COLL_WORK_PACKAGES].update_one(
        {"project_number": project_number, "version_id": version_id, "work_package_id": work_package_id},
        {"$set": {"actual_links": actual_links, "actual_totals": actual_totals, "updated_at": _utcnow()}},
    )


async def _sync_activity_actual_state(db, project_number: str, version_id: str, activity_id: str) -> Dict[str, Any]:
    activity = await db[COLL_SCHEDULE_ACTIVITIES].find_one({"project_number": project_number, "version_id": version_id, "activity_id": activity_id}, {"_id": 0})
    if not activity:
        raise LookupError("schedule_activity_not_found")
    candidates = [
        row
        async for row in db[COLL_SCHEDULE_ACTUAL_CANDIDATES].find(
            {
                "project_number": project_number,
                "version_id": version_id,
                "review_status": "approved",
                "approved_actual.activity_id": activity_id,
            },
            {"_id": 0},
        ).sort([("report_date", 1), ("updated_at", 1)])
    ]
    if not candidates:
        actual_state = {
            "status": "not_started",
            "approved_candidate_count": 0,
            "actual_start_date": "",
            "actual_finish_date": "",
            "last_progress_date": "",
            "approved_percent_complete": 0.0,
            "installed_quantity_total": 0.0,
            "labor_hours_total": 0.0,
            "equipment_hours_total": 0.0,
            "delivered_material_quantity_total": 0.0,
            "installed_material_quantity_total": 0.0,
            "returned_material_quantity_total": 0.0,
            "waste_material_quantity_total": 0.0,
        }
        await db[COLL_SCHEDULE_ACTIVITIES].update_one(
            {"project_number": project_number, "version_id": version_id, "activity_id": activity_id},
            {"$set": {"actual_state": actual_state, "actual_links": {"work_block_ids": [], "daily_report_ids": [], "production_rows": 0}, "updated_at": _utcnow()}},
        )
        return actual_state
    start_dates = [_date_text((row.get("approved_actual") or {}).get("actual_start_date") or row.get("report_date")) for row in candidates]
    finish_dates = [_date_text((row.get("approved_actual") or {}).get("actual_finish_date")) for row in candidates if _date_text((row.get("approved_actual") or {}).get("actual_finish_date"))]
    percent_complete = max(_to_float((row.get("approved_actual") or {}).get("approved_percent_complete"), 0.0) for row in candidates)
    installed_total = round(sum(_to_float((row.get("approved_actual") or {}).get("approved_installed_quantity"), 0.0) for row in candidates), 4)
    labor_total = round(sum(sum(_hours_from_row(item) for item in ((row.get("actual_facts") or {}).get("labor_entries") or [])) for row in candidates), 4)
    equipment_total = round(sum(sum(_hours_from_row(item) for item in ((row.get("actual_facts") or {}).get("equipment_entries") or [])) for row in candidates), 4)
    material_delivered = round(sum(sum(_to_float(item.get("quantity"), 0.0) for item in ((row.get("material_flow") or {}).get("delivered") or [])) for row in candidates), 4)
    material_installed = round(sum(sum(_to_float(item.get("quantity"), 0.0) for item in ((row.get("material_flow") or {}).get("installed") or [])) for row in candidates), 4)
    material_returned = round(sum(sum(_to_float(item.get("quantity"), 0.0) for item in ((row.get("material_flow") or {}).get("returned") or [])) for row in candidates), 4)
    material_waste = round(sum(sum(_to_float(item.get("quantity"), 0.0) for item in ((row.get("material_flow") or {}).get("waste") or [])) for row in candidates), 4)
    actual_status = "completed" if finish_dates or percent_complete >= 100.0 else "in_progress"
    actual_state = {
        "status": actual_status,
        "approved_candidate_count": len(candidates),
        "actual_start_date": min([value for value in start_dates if value] or [""]),
        "actual_finish_date": max(finish_dates or [""]),
        "last_progress_date": max([_clean(row.get("report_date")) for row in candidates if _clean(row.get("report_date"))] or [""]),
        "approved_percent_complete": round(percent_complete, 2),
        "installed_quantity_total": installed_total,
        "labor_hours_total": labor_total,
        "equipment_hours_total": equipment_total,
        "delivered_material_quantity_total": material_delivered,
        "installed_material_quantity_total": material_installed,
        "returned_material_quantity_total": material_returned,
        "waste_material_quantity_total": material_waste,
        "notes": "PM-approved actuals are additive and never rewrite the preserved Daily Report or the baseline schedule.",
    }
    actual_links = {
        "work_block_ids": sorted({row.get("work_block_id") for row in candidates if _clean(row.get("work_block_id"))}),
        "daily_report_ids": sorted({row.get("source_report_id") for row in candidates if _clean(row.get("source_report_id"))}),
        "production_rows": len(candidates),
    }
    future_rollups = deepcopy(activity.get("future_rollups") or {})
    future_rollups.update(
        {
            "equipment_hours": equipment_total,
            "material_delivered": material_delivered,
            "material_installed": material_installed,
            "material_returned": material_returned,
            "material_waste": material_waste,
        }
    )
    await db[COLL_SCHEDULE_ACTIVITIES].update_one(
        {"project_number": project_number, "version_id": version_id, "activity_id": activity_id},
        {"$set": {"actual_state": actual_state, "actual_links": actual_links, "future_rollups": future_rollups, "updated_at": _utcnow()}},
    )
    await _sync_work_package_actual_state(db, project_number, version_id, _clean(activity.get("work_package_id")))
    return actual_state


async def review_schedule_actual_candidate(db, project_number: str, candidate_id: str, payload: Dict[str, Any], *, actor: Dict[str, Any]) -> Dict[str, Any]:
    await ensure_schedule_actuals_foundation(db)
    candidate = await db[COLL_SCHEDULE_ACTUAL_CANDIDATES].find_one({"project_number": project_number, "candidate_id": candidate_id}, {"_id": 0})
    if not candidate:
        raise LookupError("schedule_actual_candidate_not_found")
    action = _clean(payload.get("action") or "approve").lower()
    if action not in {"approve", "reject", "defer", "needs_review"}:
        raise ValueError("schedule_actual_action_invalid")
    updated = deepcopy(candidate)
    previous_activity_id = _clean((candidate.get("approved_actual") or {}).get("activity_id"))
    approved_activity_id = _clean(payload.get("activity_id") or (candidate.get("activity_resolution") or {}).get("resolved_activity_id"))
    approved_activity_name = _clean(payload.get("activity_name") or (candidate.get("activity_resolution") or {}).get("resolved_activity_name"))
    if action == "approve" and not approved_activity_id:
        raise ValueError("schedule_actual_activity_required")
    approved_percent = max(0.0, min(100.0, _to_float(payload.get("approved_percent_complete"), _to_float((candidate.get("approved_actual") or {}).get("approved_percent_complete"), 0.0))))
    approved_quantity = round(_to_float(payload.get("approved_installed_quantity"), _to_float((candidate.get("actual_facts") or {}).get("installed_quantity"), 0.0)), 4)
    approved_status = _status(payload.get("schedule_progress_status") or ("completed" if approved_percent >= 100 else "in_progress" if approved_percent > 0 or approved_quantity > 0 else "not_started"), allowed=SCHEDULE_PROGRESS_STATUSES, default="not_started")
    updated["review_status"] = {
        "approve": "approved",
        "reject": "rejected",
        "defer": "deferred",
        "needs_review": "review_required",
    }[action]
    updated["review_note"] = _clean(payload.get("review_note") or "")
    updated["updated_at"] = _utcnow()
    updated["updated_by"] = _actor_label(actor)
    updated.setdefault("review_history", []).append(
        {
            "action": action,
            "at": updated["updated_at"],
            "by": _actor_label(actor),
            "note": updated["review_note"],
        }
    )
    if action == "approve":
        updated["approved_actual"] = {
            "activity_id": approved_activity_id,
            "activity_name": approved_activity_name or approved_activity_id,
            "actual_start_date": _date_text(payload.get("actual_start_date") or (candidate.get("approved_actual") or {}).get("actual_start_date") or candidate.get("report_date")),
            "actual_finish_date": _date_text(payload.get("actual_finish_date") or (candidate.get("approved_actual") or {}).get("actual_finish_date") or (candidate.get("report_date") if approved_status == "completed" else "")),
            "approved_percent_complete": approved_percent,
            "approved_installed_quantity": approved_quantity,
            "schedule_progress_status": approved_status,
            "approved_at": updated["updated_at"],
            "approved_by": _actor_label(actor),
            "governance_note": updated["review_note"] or "PM approved the Daily Report candidate as governed schedule actual evidence.",
        }
        updated["activity_resolution"] = {
            **(updated.get("activity_resolution") or {}),
            "resolved_activity_id": approved_activity_id,
            "resolved_activity_name": approved_activity_name or approved_activity_id,
            "confidence": "human_confirmed",
            "match_basis": "pm_approved_actual",
        }
        await _resolve_review_item(db, f"schedule-review:actual:{candidate_id}", actor=actor, note="PM approved schedule actual candidate.")
    else:
        updated["approved_actual"] = {}
        if action in {"reject", "needs_review", "defer"}:
            await _upsert_review_item(
                db,
                {
                    "review_id": f"schedule-review:actual:{candidate_id}",
                    "project_number": project_number,
                    "status": "review_required" if action != "reject" else "rejected",
                    "priority": 88,
                    "source_kind": "schedule_actual_candidate",
                    "source_record_id": candidate_id,
                    "title": f"Schedule actual candidate {action}",
                    "reason": updated["review_note"] or _candidate_review_reason(updated),
                    "confidence": "human_required",
                    "provenance": {"candidate_id": candidate_id, "action": action},
                },
            )
    await db[COLL_SCHEDULE_ACTUAL_CANDIDATES].replace_one({"candidate_id": candidate_id}, updated, upsert=True)
    if action == "approve":
        actual_state = await _sync_activity_actual_state(db, project_number, candidate.get("version_id") or "", approved_activity_id)
        updated["activity_actual_state_after_review"] = actual_state
        if previous_activity_id and previous_activity_id != approved_activity_id:
            await _sync_activity_actual_state(db, project_number, candidate.get("version_id") or "", previous_activity_id)
        await db[COLL_SCHEDULE_ACTUAL_CANDIDATES].update_one(
            {"candidate_id": candidate_id},
            {"$set": {"activity_actual_state_after_review": actual_state, "updated_at": _utcnow(), "updated_by": _actor_label(actor)}},
        )
    elif previous_activity_id:
        await _sync_activity_actual_state(db, project_number, candidate.get("version_id") or "", previous_activity_id)
    await _write_audit(db, f"schedule_actual_candidate_{action}", actor, "schedule_actual_candidate", candidate_id, updated, before=candidate)
    return _sanitize(updated)


def _forecast_row(current_activity: Dict[str, Any], baseline_activity: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    actual_state = current_activity.get("actual_state") or {}
    current_start = _date_text(current_activity.get("planned_start_date"))
    current_finish = _date_text(current_activity.get("planned_finish_date"))
    actual_start = _date_text(actual_state.get("actual_start_date")) or current_start
    approved_percent = _to_float(actual_state.get("approved_percent_complete"), 0.0)
    if _date_text(actual_state.get("actual_finish_date")):
        forecast_start = actual_start
        forecast_finish = _date_text(actual_state.get("actual_finish_date"))
        forecast_status = "completed"
    elif (actual_state.get("status") or "") == "in_progress":
        anchor = _as_date(actual_state.get("last_progress_date")) or _as_date(current_start) or datetime.now(timezone.utc).date()
        duration_days = max(int(current_activity.get("duration_days") or 1), 1)
        completed_days = int(round(duration_days * (approved_percent / 100.0))) if approved_percent > 0 else 0
        remaining_days = max(1, duration_days - completed_days)
        forecast_start = actual_start or current_start
        forecast_finish = (anchor + timedelta(days=max(remaining_days, 1) - 1)).isoformat()
        forecast_status = "in_progress"
    else:
        forecast_start = current_start
        forecast_finish = current_finish
        forecast_status = current_activity.get("status") or "not_started"
    baseline_start = _date_text((baseline_activity or {}).get("planned_start_date"))
    baseline_finish = _date_text((baseline_activity or {}).get("planned_finish_date"))
    slip_days = 0
    finish_dt = _as_date(forecast_finish)
    compare_dt = _as_date(current_finish) or _as_date(baseline_finish)
    if finish_dt and compare_dt:
        slip_days = max(0, (finish_dt - compare_dt).days)
    return {
        "activity_id": current_activity.get("activity_id") or "",
        "activity_name": current_activity.get("activity_name") or "",
        "work_package_id": current_activity.get("work_package_id") or "",
        "project_cost_code": current_activity.get("project_cost_code") or "",
        "baseline_start_date": baseline_start,
        "baseline_finish_date": baseline_finish,
        "current_start_date": current_start,
        "current_finish_date": current_finish,
        "forecast_start_date": forecast_start,
        "forecast_finish_date": forecast_finish,
        "forecast_status": forecast_status,
        "approved_percent_complete": round(approved_percent, 2),
        "slip_days": slip_days,
    }


async def build_schedule_forecast_view(db, project_number: str, *, version_id: str = "") -> Dict[str, Any]:
    await ensure_schedule_actuals_foundation(db)
    version = None
    if _clean(version_id):
        version = await db[COLL_SCHEDULE_VERSIONS].find_one({"project_number": project_number, "version_id": _clean(version_id)}, {"_id": 0})
    if not version:
        version = await _active_version(db, project_number)
    if not version:
        return {"version": None, "rows": [], "summary": {"rows": 0, "slipped": 0, "completed": 0}}
    current_rows = await list_schedule_activities(db, project_number, version_id=version.get("version_id") or "")
    baseline_rows = await list_schedule_activities(db, project_number, version_id=version.get("baseline_version_id") or version.get("version_id") or "")
    baseline_map = {row.get("activity_id"): row for row in baseline_rows if _clean(row.get("activity_id"))}
    rows = [_forecast_row(row, baseline_map.get(row.get("activity_id"))) for row in current_rows]
    return {
        "version": _sanitize(version),
        "rows": rows,
        "summary": {
            "rows": len(rows),
            "slipped": sum(1 for row in rows if int(row.get("slip_days") or 0) > 0),
            "completed": sum(1 for row in rows if row.get("forecast_status") == "completed"),
        },
    }


def _plan_item_from_activity(activity: Dict[str, Any]) -> Dict[str, Any]:
    planned = activity.get("planned_assignments") or {}
    actual_state = activity.get("actual_state") or {}
    return {
        "plan_item_id": f"plan-item:{activity.get('activity_id') or activity.get('work_package_id') or 'activity'}",
        "activity_id": activity.get("activity_id") or "",
        "activity_name": activity.get("activity_name") or "",
        "work_package_id": activity.get("work_package_id") or "",
        "budget_line_id": activity.get("budget_line_id") or "",
        "customer_pay_item_number": activity.get("customer_pay_item_number") or "",
        "project_cost_code": activity.get("project_cost_code") or "",
        "planned_quantity": round(_to_float(planned.get("planned_production_quantity"), 0.0), 4),
        "planned_hours": round(_to_float(planned.get("planned_hours"), 0.0), 4),
        "planned_crews": _sanitize(planned.get("planned_crew_ids") or []),
        "planned_equipment": _sanitize(planned.get("planned_equipment_ids") or []),
        "planned_materials": _sanitize(planned.get("planned_materials") or []),
        "planned_vendors": _sanitize(planned.get("planned_vendor_refs") or []),
        "planned_subcontractors": _sanitize(planned.get("planned_subcontractor_refs") or []),
        "planned_constraints": _sanitize(planned.get("planned_constraints") or []),
        "actual_status": actual_state.get("status") or "not_started",
        "approved_percent_complete": round(_to_float(actual_state.get("approved_percent_complete"), 0.0), 2),
        "daily_goal_note": "",
    }


async def get_daily_work_plan(db, project_number: str, *, work_date: str = "") -> Dict[str, Any]:
    await ensure_schedule_actuals_foundation(db)
    work_date = _date_text(work_date) or datetime.now(timezone.utc).date().isoformat()
    existing = await db[COLL_DAILY_WORK_PLANS].find_one({"project_number": project_number, "work_date": work_date}, {"_id": 0})
    active_version = await _active_version(db, project_number)
    lookahead = await get_reconciled_schedule_lookahead(db, project_number)
    current_version_id = (active_version or {}).get("version_id") or ""
    current_lookahead_id = lookahead.get("lookahead_id") or ""
    current_lookahead_version = int(lookahead.get("version") or 0)
    if existing:
        is_current_horizon = work_date >= datetime.now(timezone.utc).date().isoformat()
        if is_current_horizon and (
            _clean(existing.get("version_id")) != _clean(current_version_id)
            or _clean(existing.get("lookahead_id")) != _clean(current_lookahead_id)
            or int(existing.get("lookahead_version") or 0) != current_lookahead_version
        ):
            await db[COLL_DAILY_WORK_PLANS].delete_one({"project_number": project_number, "work_date": work_date})
        else:
            return _sanitize(existing)
    if not active_version:
        return {
            "plan_id": _plan_id(project_number, work_date),
            "project_number": project_number,
            "work_date": work_date,
            "status": "draft",
            "version_id": "",
            "items": [],
            "notes": "No active governed schedule version exists yet.",
        }
    activities = await list_schedule_activities(db, project_number, version_id=active_version.get("version_id") or "")
    focus_activity_ids = {row.get("activity_id") for row in activities if _clean(row.get("activity_id")) and ((_as_date(row.get("planned_start_date")) or date.min) <= _as_date(work_date) <= (_as_date(row.get("planned_finish_date")) or date.max))}
    for task in lookahead.get("tasks") or []:
        if _clean(task.get("activity_id")):
            focus_activity_ids.add(_clean(task.get("activity_id")))
    selected = [row for row in activities if row.get("activity_id") in focus_activity_ids][:12]
    plan = {
        "plan_id": _plan_id(project_number, work_date),
        "project_number": project_number,
        "work_date": work_date,
        "status": "draft",
        "version_id": active_version.get("version_id") or "",
        "baseline_version_id": active_version.get("baseline_version_id") or active_version.get("version_id") or "",
        "lookahead_id": lookahead.get("lookahead_id") or "",
        "lookahead_version": current_lookahead_version,
        "items": [_plan_item_from_activity(row) for row in selected],
        "notes": "Daily work plans are governed overlays derived from the active current schedule and the rolling lookahead. They never overwrite baseline history.",
        "created_at": _utcnow(),
        "created_by": "project_schedule_actuals_spine",
        "updated_at": _utcnow(),
        "updated_by": "project_schedule_actuals_spine",
    }
    await db[COLL_DAILY_WORK_PLANS].replace_one(
        {"project_number": project_number, "work_date": work_date},
        plan,
        upsert=True,
    )
    return _sanitize(plan)


async def save_daily_work_plan(db, project_number: str, payload: Dict[str, Any], *, actor: Dict[str, Any]) -> Dict[str, Any]:
    work_date = _date_text(payload.get("work_date")) or datetime.now(timezone.utc).date().isoformat()
    existing = await get_daily_work_plan(db, project_number, work_date=work_date)
    updated = deepcopy(existing)
    updated["status"] = _status(payload.get("status") or updated.get("status") or "draft", allowed=PLAN_STATUSES, default="draft")
    updated["notes"] = _clean(payload.get("notes") or updated.get("notes") or "")
    updated["items"] = _sanitize(payload.get("items") or updated.get("items") or [])
    updated["updated_at"] = _utcnow()
    updated["updated_by"] = _actor_label(actor)
    if updated["status"] == "published":
        updated["published_at"] = updated.get("published_at") or updated["updated_at"]
        updated["published_by"] = updated.get("published_by") or _actor_label(actor)
    await db[COLL_DAILY_WORK_PLANS].replace_one({"project_number": project_number, "work_date": work_date}, updated, upsert=True)
    await _write_audit(db, "daily_work_plan_saved", actor, "daily_work_plan", updated.get("plan_id") or _plan_id(project_number, work_date), updated, before=existing)
    return _sanitize(updated)


async def get_schedule_actuals_overview(db, project_number: str, *, work_date: str = "") -> Dict[str, Any]:
    await ensure_schedule_actuals_foundation(db)
    candidates = await list_schedule_actual_candidates(db, project_number)
    forecast = await build_schedule_forecast_view(db, project_number)
    daily_work_plan = await get_daily_work_plan(db, project_number, work_date=work_date)
    return {
        "counts": {
            "candidates": len(candidates),
            "pending_review": sum(1 for row in candidates if row.get("review_status") in {"pending_review", "review_required"}),
            "approved": sum(1 for row in candidates if row.get("review_status") == "approved"),
            "deferred": sum(1 for row in candidates if row.get("review_status") == "deferred"),
            "rejected": sum(1 for row in candidates if row.get("review_status") == "rejected"),
            "forecast_rows": len(forecast.get("rows") or []),
        },
        "baseline_current_forecast_contract": {
            "baseline": "Approved original commitment preserved by baseline_version_id. Never overwritten by C5 actuals.",
            "current": "Active working schedule version with revision history. PM lookahead and daily work plan remain overlays on this current plan.",
            "forecast": "Deterministic expected outcome derived from PM-approved actuals and remaining duration. It never masquerades as baseline or current commitment.",
        },
        "forecast": forecast,
        "daily_work_plan": daily_work_plan,
        "candidates": candidates[:150],
        "report_links": sorted({row.get("source_report_id") for row in candidates if _clean(row.get("source_report_id"))})[:50],
    }


async def get_admin_schedule_actuals_overview(db, project_number: str = "") -> Dict[str, Any]:
    await ensure_schedule_actuals_foundation(db)
    query: Dict[str, Any] = {"project_number": project_number} if _clean(project_number) else {}
    items = [_sanitize(row) async for row in db[COLL_SCHEDULE_ACTUAL_CANDIDATES].find(query, {"_id": 0}).sort([("updated_at", -1)]).limit(200)]
    plans = [_sanitize(row) async for row in db[COLL_DAILY_WORK_PLANS].find(query, {"_id": 0}).sort([("work_date", -1)]).limit(50)]
    return {
        "summary": {
            "candidates": await db[COLL_SCHEDULE_ACTUAL_CANDIDATES].count_documents(query),
            "approved": await db[COLL_SCHEDULE_ACTUAL_CANDIDATES].count_documents({**query, "review_status": "approved"}),
            "review_required": await db[COLL_SCHEDULE_ACTUAL_CANDIDATES].count_documents({**query, "review_status": {"$in": ["pending_review", "review_required", "deferred"]}}),
            "daily_work_plans": await db[COLL_DAILY_WORK_PLANS].count_documents(query),
        },
        "candidates": items,
        "daily_work_plans": plans,
    }


async def run_schedule_actuals_backfill(db, *, force: bool = False) -> Dict[str, Any]:
    await ensure_schedule_actuals_foundation(db)
    last_run = await db[COLL_SCHEDULE_ACTUAL_RUNS].find_one({"run_type": "wp18c5_actuals_backfill"}, {"_id": 0})
    if last_run and not force:
        return _sanitize(last_run)
    candidates_synced = 0
    projects_processed = 0
    reports_processed = 0
    project_numbers = {_clean(row.get("project_number")) async for row in db.jobs_master.find({"project_number": {"$ne": ""}}, {"_id": 0, "project_number": 1})}
    for project_number in sorted(project_numbers):
        if not project_number or not await _active_version(db, project_number):
            continue
        projects_processed += 1
        async for report in db.daily_reports.find({"project_number": project_number, "work_blocks_version": {"$ne": ""}}, {"_id": 0, "id": 1, "doc_id": 1, "project_number": 1, "project_name": 1, "report_date": 1, "prepared_by": 1, "audit_envelope_sha256": 1, "work_blocks_version": 1, "work_blocks": 1, "outbound_materials": 1, "location": 1}):
            reports_processed += 1
            result = await sync_schedule_actual_candidates_for_report(db, report, actor={"email": "system", "role": "system"})
            candidates_synced += int(result.get("count") or 0)
    report = {
        "run_type": "wp18c5_actuals_backfill",
        "run_id": f"wp18c5-backfill:{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S')}",
        "ran_at": _utcnow(),
        "force": force,
        "projects_processed": projects_processed,
        "reports_processed": reports_processed,
        "candidates_synced": candidates_synced,
        "status": "completed",
        "mode": "additive_only",
    }
    await db[COLL_SCHEDULE_ACTUAL_RUNS].replace_one({"run_type": "wp18c5_actuals_backfill"}, report, upsert=True)
    return _sanitize(report)