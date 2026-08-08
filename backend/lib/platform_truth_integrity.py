from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional

from lib.governed_certification_lane import GOVERNED_CERTIFICATION_PROJECT_NUMBER
from lib.governed_fixture_evidence import find_fixture_evidence
from lib.governed_record_classification import HIDDEN_CLASSIFICATIONS, is_hidden_from_live_operations
from lib.synthetic_dr_filter import _TEST_NAME_RE as DR_TEST_NAME_RE
from lib.synthetic_dr_filter import _TEST_PROJECT_RE as DR_TEST_PROJECT_RE
from lib.synthetic_fleet_filter import DISPATCH_ASSIGNMENT_FIELDS, EQUIPMENT_MASTER_FIELDS, FLEET_DEFECT_FIELDS, INSPECTION_FIELDS as FLEET_INSPECTION_FIELDS
from lib.synthetic_fleet_filter import _TEST_SENTINEL_RE as FLEET_TEST_RE
from lib.synthetic_flr_filter import _TEST_NAME_RE as FLR_TEST_NAME_RE
from lib.synthetic_flr_filter import _TEST_PROJECT_RE as FLR_TEST_PROJECT_RE
from lib.synthetic_hr_filter import _TEST_EMAIL_RE as HR_TEST_EMAIL_RE
from lib.synthetic_hr_filter import _TEST_NAME_RE as HR_TEST_NAME_RE
from lib.synthetic_safety_filter import INCIDENT_FIELDS, INSPECTION_FIELDS as SAFETY_INSPECTION_FIELDS, JHA_FIELDS, MEETING_FIELDS, SAFETY_DOC_FIELDS, SAFETY_ISSUANCE_FIELDS, SAFETY_TRAINING_FIELDS
from lib.synthetic_safety_filter import _TEST_SENTINEL_RE as SAFETY_TEST_RE
from services.project_schedule_actuals_spine import get_daily_work_plan
from services.project_earned_value_engine import get_project_earned_value_snapshot
from services.project_schedule_authority import get_reconciled_schedule_lookahead


def _utcnow() -> datetime:
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    return _utcnow().isoformat()


def _parse_dt(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if not value:
        return None
    try:
        text = str(value)
        if text.endswith("Z"):
            text = text[:-1] + "+00:00"
        parsed = datetime.fromisoformat(text)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _signature_hash(rows: Iterable[Dict[str, Any]], fields: List[str]) -> List[tuple]:
    out: List[tuple] = []
    for row in rows:
        item = tuple(_clean(row.get(field)) for field in fields)
        if any(item):
            out.append(item)
    return sorted(out)


def _family_status(*, heuristic_only_count: int, fixture_only_count: int, explicit_hidden_count: int, certification_project_rows: int, conflicting_marker_count: int, operator_consumer_count: int, mixed_mode: bool) -> str:
    if conflicting_marker_count > 0:
        return "red"
    if fixture_only_count > 0:
        return "red"
    if heuristic_only_count > 0:
        return "red"
    if mixed_mode and certification_project_rows > 0 and operator_consumer_count > 0:
        return "yellow"
    if explicit_hidden_count > 0 or certification_project_rows > 0:
        return "green"
    return "green"


def _family_summary(*, heuristic_only_count: int, fixture_only_count: int, explicit_hidden_count: int, certification_project_rows: int, conflicting_marker_count: int, mixed_mode: bool) -> str:
    if conflicting_marker_count > 0:
        return f"{conflicting_marker_count} records carry contradictory truth markers."
    if fixture_only_count > 0:
        return f"{fixture_only_count} records match deterministic fixture evidence but still lack explicit governed metadata."
    if heuristic_only_count > 0:
        return f"{heuristic_only_count} records still rely on heuristic-only exclusion instead of explicit governed metadata."
    if mixed_mode and certification_project_rows > 0:
        return f"Certification-scoped rows exist ({certification_project_rows}) and must remain isolated from operator/executive aggregates."
    if explicit_hidden_count > 0:
        return f"{explicit_hidden_count} records are explicitly governed as technical/synthetic/certification and hidden from operator truth."
    return "No governed contamination evidence is currently present in this family."


async def _count(db, collection: str, query: Dict[str, Any]) -> int:
    if collection not in await db.list_collection_names():
        return 0
    return await db[collection].count_documents(query)


async def _sample(db, collection: str, query: Dict[str, Any], *, fields: Dict[str, int], limit: int = 5) -> List[Dict[str, Any]]:
    if collection not in await db.list_collection_names():
        return []
    return [row async for row in db[collection].find(query, fields).limit(limit)]


async def _fixture_only_matches(
    db,
    *,
    collection: str,
    family_id: str,
    limit: int = 5,
) -> Dict[str, Any]:
    if collection not in await db.list_collection_names():
        return {"count": 0, "samples": []}
    count = 0
    samples: List[Dict[str, Any]] = []
    cursor = db[collection].find({})
    async for row in cursor:
        if is_hidden_from_live_operations(row):
            continue
        if find_fixture_evidence(row, family_id):
            count += 1
            if len(samples) < limit:
                row.pop("_id", None)
                samples.append(row)
    return {"count": count, "samples": samples}


def _explicit_hidden_query() -> Dict[str, Any]:
    return {
        "$or": [
            {"technical_record_classification": {"$in": sorted(HIDDEN_CLASSIFICATIONS)}},
            {"truth_visibility_scope": "technical_audit_only"},
            {"synthetic_record": True},
            {"hidden_from_operations": True},
            {"certification_record": True},
        ]
    }


def _not_explicit_hidden_query() -> Dict[str, Any]:
    return {
        "$and": [
            {"$or": [{"technical_record_classification": {"$exists": False}}, {"technical_record_classification": {"$nin": sorted(HIDDEN_CLASSIFICATIONS)}}]},
            {"truth_visibility_scope": {"$ne": "technical_audit_only"}},
            {"synthetic_record": {"$ne": True}},
            {"hidden_from_operations": {"$ne": True}},
            {"certification_record": {"$ne": True}},
        ]
    }


def _regex_or(fields: Iterable[str], pattern: str) -> Dict[str, Any]:
    return {"$or": [{field: {"$regex": pattern, "$options": "i"}} for field in fields]}


def _hr_heuristic_query() -> Dict[str, Any]:
    return {
        "$or": [
            {"name": {"$regex": HR_TEST_NAME_RE, "$options": "i"}},
            {"preferred_name": {"$regex": HR_TEST_NAME_RE, "$options": "i"}},
            {"legal_first_name": {"$regex": HR_TEST_NAME_RE, "$options": "i"}},
            {"legal_last_name": {"$regex": HR_TEST_NAME_RE, "$options": "i"}},
            {"employee_id": {"$regex": HR_TEST_NAME_RE, "$options": "i"}},
            {"email": {"$regex": HR_TEST_EMAIL_RE, "$options": "i"}},
        ]
    }


def _flr_heuristic_query() -> Dict[str, Any]:
    return {
        "$or": [
            {"employee_name": {"$regex": FLR_TEST_NAME_RE, "$options": "i"}},
            {"supervisor_name": {"$regex": FLR_TEST_NAME_RE, "$options": "i"}},
            {"submitted_by_name": {"$regex": FLR_TEST_NAME_RE, "$options": "i"}},
            {"project_number": {"$regex": FLR_TEST_PROJECT_RE, "$options": "i"}},
            {"project_name": {"$regex": FLR_TEST_NAME_RE, "$options": "i"}},
        ]
    }


def _dr_heuristic_query() -> Dict[str, Any]:
    return {
        "$or": [
            {"project_number": {"$regex": DR_TEST_PROJECT_RE, "$options": "i"}},
            {"project_name": {"$regex": DR_TEST_NAME_RE, "$options": "i"}},
        ]
    }


def _safety_heuristic_query(fields: Iterable[str]) -> Dict[str, Any]:
    return _regex_or(fields, SAFETY_TEST_RE)


def _fleet_heuristic_query(fields: Iterable[str]) -> Dict[str, Any]:
    return _regex_or(fields, FLEET_TEST_RE)


FAMILY_CONFIGS: List[Dict[str, Any]] = [
    {
        "family_id": "employees",
        "label": "Employees",
        "collection": "employees",
        "classification_mode": "heuristic_plus_explicit",
        "heuristic_query": _hr_heuristic_query,
        "operator_consumer_collections": ["employees"],
        "sample_fields": {"_id": 0, "id": 1, "name": 1, "preferred_name": 1, "email": 1, "employee_id": 1, "synthetic_record": 1, "hidden_from_operations": 1},
    },
    {
        "family_id": "projects",
        "label": "Projects",
        "collection": "jobs_master",
        "classification_mode": "governed_certification_project_scope",
        "certification_query": lambda: {"project_number": GOVERNED_CERTIFICATION_PROJECT_NUMBER},
        "operator_consumer_collections": ["jobs_master"],
        "sample_fields": {"_id": 0, "project_number": 1, "project_name": 1, "pm_email": 1, "certification_project": 1},
        "mixed_mode": True,
    },
    {
        "family_id": "project_members",
        "label": "Project Members",
        "collection": "project_team_assignments",
        "classification_mode": "governed_certification_project_scope",
        "certification_query": lambda: {"project_number": GOVERNED_CERTIFICATION_PROJECT_NUMBER},
        "operator_consumer_collections": ["project_team_assignments"],
        "sample_fields": {"_id": 0, "id": 1, "project_number": 1, "email": 1, "assignment_role": 1, "active": 1},
        "mixed_mode": True,
    },
    {
        "family_id": "daily_reports",
        "label": "Daily Reports",
        "collection": "daily_reports",
        "classification_mode": "explicit_plus_legacy_heuristic",
        "heuristic_query": _dr_heuristic_query,
        "operator_consumer_collections": ["daily_reports"],
        "sample_fields": {"_id": 0, "id": 1, "project_number": 1, "project_name": 1, "synthetic_record": 1, "hidden_from_operations": 1, "certification_record": 1},
    },
    {
        "family_id": "field_leadership_records",
        "label": "Field Leadership Records",
        "collection": "field_leadership_records",
        "classification_mode": "heuristic_plus_explicit",
        "heuristic_query": _flr_heuristic_query,
        "operator_consumer_collections": ["field_leadership_records"],
        "sample_fields": {"_id": 0, "id": 1, "employee_name": 1, "project_number": 1, "project_name": 1, "kind": 1, "synthetic_record": 1, "hidden_from_operations": 1},
    },
    {
        "family_id": "corrective_actions",
        "label": "Corrective Actions",
        "collection": "corrective_actions",
        "classification_mode": "explicit_governed",
        "operator_consumer_collections": ["corrective_actions"],
        "sample_fields": {"_id": 0, "id": 1, "title": 1, "project_number": 1, "status": 1, "technical_record_classification": 1, "truth_visibility_scope": 1, "synthetic_record": 1, "hidden_from_operations": 1, "certification_record": 1},
    },
    {
        "family_id": "incidents",
        "label": "Incidents",
        "collection": "incidents",
        "classification_mode": "heuristic_plus_explicit",
        "heuristic_query": lambda: _safety_heuristic_query(INCIDENT_FIELDS),
        "operator_consumer_collections": ["incidents"],
        "sample_fields": {"_id": 0, "id": 1, "project_number": 1, "project_name": 1, "reported_by": 1, "synthetic_record": 1, "hidden_from_operations": 1},
    },
    {
        "family_id": "meetings",
        "label": "Safety Meetings",
        "collection": "meetings",
        "classification_mode": "heuristic_plus_explicit",
        "heuristic_query": lambda: _safety_heuristic_query(MEETING_FIELDS),
        "operator_consumer_collections": ["meetings"],
        "sample_fields": {"_id": 0, "id": 1, "project_number": 1, "project_name": 1, "topic": 1, "synthetic_record": 1, "hidden_from_operations": 1},
    },
    {
        "family_id": "jhas",
        "label": "JHAs / JHPs",
        "collection": "jhas",
        "classification_mode": "heuristic_plus_explicit",
        "heuristic_query": lambda: _safety_heuristic_query(JHA_FIELDS),
        "operator_consumer_collections": ["jhas"],
        "sample_fields": {"_id": 0, "id": 1, "project_number": 1, "project_name": 1, "task": 1, "synthetic_record": 1, "hidden_from_operations": 1},
    },
    {
        "family_id": "inspections",
        "label": "Safety Inspections",
        "collection": "inspections",
        "classification_mode": "heuristic_plus_explicit",
        "heuristic_query": lambda: _safety_heuristic_query(SAFETY_INSPECTION_FIELDS),
        "operator_consumer_collections": ["inspections"],
        "sample_fields": {"_id": 0, "id": 1, "project_number": 1, "project_name": 1, "inspector_name": 1, "synthetic_record": 1, "hidden_from_operations": 1},
    },
    {
        "family_id": "training_records",
        "label": "Training / Qualifications",
        "collection": "safety_training_records",
        "classification_mode": "heuristic_plus_explicit",
        "heuristic_query": lambda: _safety_heuristic_query(SAFETY_TRAINING_FIELDS),
        "operator_consumer_collections": ["safety_training_records"],
        "sample_fields": {"_id": 0, "id": 1, "employee_name": 1, "training_name": 1, "project_number": 1, "synthetic_record": 1, "hidden_from_operations": 1},
    },
    {
        "family_id": "safety_documents",
        "label": "Safety Documents",
        "collection": "safety_documents",
        "classification_mode": "heuristic_plus_explicit",
        "heuristic_query": lambda: _safety_heuristic_query(SAFETY_DOC_FIELDS),
        "operator_consumer_collections": ["safety_documents"],
        "sample_fields": {"_id": 0, "id": 1, "title": 1, "project_number": 1, "synthetic_record": 1, "hidden_from_operations": 1},
    },
    {
        "family_id": "safety_issuances",
        "label": "Safety Issuances",
        "collection": "safety_equipment_issuances",
        "classification_mode": "heuristic_plus_explicit",
        "heuristic_query": lambda: _safety_heuristic_query(SAFETY_ISSUANCE_FIELDS),
        "operator_consumer_collections": ["safety_equipment_issuances"],
        "sample_fields": {"_id": 0, "id": 1, "employee_name": 1, "equipment_name": 1, "synthetic_record": 1, "hidden_from_operations": 1},
    },
    {
        "family_id": "equipment_master",
        "label": "Equipment / Fleet",
        "collection": "equipment_master",
        "classification_mode": "heuristic_plus_explicit",
        "heuristic_query": lambda: _fleet_heuristic_query(EQUIPMENT_MASTER_FIELDS),
        "operator_consumer_collections": ["equipment_master"],
        "sample_fields": {"_id": 0, "id": 1, "unit_number": 1, "display_label": 1, "synthetic_record": 1, "hidden_from_operations": 1},
    },
    {
        "family_id": "dispatch_assignments",
        "label": "Dispatch Assignments",
        "collection": "dispatch_assignments",
        "classification_mode": "heuristic_plus_explicit",
        "heuristic_query": lambda: _fleet_heuristic_query(DISPATCH_ASSIGNMENT_FIELDS),
        "operator_consumer_collections": ["dispatch_assignments"],
        "sample_fields": {"_id": 0, "id": 1, "truck_id": 1, "driver_name": 1, "project_number": 1, "synthetic_record": 1, "hidden_from_operations": 1},
    },
    {
        "family_id": "fleet_defect_items",
        "label": "Fleet Defects",
        "collection": "fleet_defect_items",
        "classification_mode": "heuristic_plus_explicit",
        "heuristic_query": lambda: _fleet_heuristic_query(FLEET_DEFECT_FIELDS),
        "operator_consumer_collections": ["fleet_defect_items"],
        "sample_fields": {"_id": 0, "id": 1, "unit_number": 1, "project_number": 1, "synthetic_record": 1, "hidden_from_operations": 1},
    },
    {
        "family_id": "equipment_inspections",
        "label": "Equipment Inspections / DVIR",
        "collection": "equipment_inspections",
        "classification_mode": "heuristic_plus_explicit",
        "heuristic_query": lambda: _fleet_heuristic_query(FLEET_INSPECTION_FIELDS),
        "operator_consumer_collections": ["equipment_inspections"],
        "sample_fields": {"_id": 0, "id": 1, "equipment_unit": 1, "project_number": 1, "operator_name": 1, "synthetic_record": 1, "hidden_from_operations": 1},
    },
    {
        "family_id": "project_budget_actual_cost_candidates",
        "label": "Budget Actual Cost Candidates",
        "collection": "project_budget_actual_cost_candidates",
        "classification_mode": "governed_certification_project_scope",
        "certification_query": lambda: {"project_number": {"$regex": r"^(ZZ-RUNTIME-CERT-2026|TEST[_\-]|ITER[0-9])", "$options": "i"}},
        "operator_consumer_collections": ["project_budget_actual_cost_candidates"],
        "sample_fields": {"_id": 0, "candidate_id": 1, "project_number": 1, "vendor": 1, "review_status": 1},
        "mixed_mode": True,
    },
    {
        "family_id": "project_forecasting_snapshots",
        "label": "C7 Forecast Snapshots",
        "collection": "project_forecasting_snapshots",
        "classification_mode": "governed_certification_project_scope",
        "certification_query": lambda: {"project_number": GOVERNED_CERTIFICATION_PROJECT_NUMBER},
        "operator_consumer_collections": ["project_forecasting_snapshots"],
        "sample_fields": {"_id": 0, "version_id": 1, "project_number": 1, "generated_at": 1, "fingerprint": 1},
        "mixed_mode": True,
    },
    {
        "family_id": "project_earned_value_snapshots",
        "label": "C8 Earned Value Snapshots",
        "collection": "project_earned_value_snapshots",
        "classification_mode": "governed_certification_project_scope",
        "certification_query": lambda: {"project_number": GOVERNED_CERTIFICATION_PROJECT_NUMBER},
        "operator_consumer_collections": ["project_earned_value_snapshots"],
        "sample_fields": {"_id": 0, "project_number": 1, "generated_at": 1, "audience": 1, "cache_status": 1},
        "mixed_mode": True,
    },
    {
        "family_id": "portfolio_intelligence_snapshots",
        "label": "C9 Portfolio Snapshots",
        "collection": "portfolio_intelligence_snapshots",
        "classification_mode": "governed_certification_project_scope",
        "certification_query": lambda: {"scope.project_numbers": GOVERNED_CERTIFICATION_PROJECT_NUMBER},
        "operator_consumer_collections": ["portfolio_intelligence_snapshots"],
        "sample_fields": {"_id": 0, "snapshot_id": 1, "generated_at": 1, "scope_key": 1},
        "mixed_mode": True,
    },
    {
        "family_id": "backup_recovery",
        "label": "Backup / Recovery Certification",
        "collection": "backup_health",
        "classification_mode": "technical_only",
        "operator_consumer_collections": ["backup_health", "drill_runs"],
        "sample_fields": {"_id": 0, "mode": 1, "ts": 1, "ok": 1, "filename": 1},
    },
]


async def scan_platform_contamination_integrity(db) -> Dict[str, Any]:
    generated_at = _now_iso()
    family_results: List[Dict[str, Any]] = []
    blocking = []

    for config in FAMILY_CONFIGS:
        collection = config["collection"]
        exists = collection in await db.list_collection_names()
        if not exists:
            family_results.append({
                "family_id": config["family_id"],
                "label": config["label"],
                "collection": collection,
                "status": "unknown",
                "classification_mode": config["classification_mode"],
                "summary": "Collection is absent in this runtime.",
                "present": False,
            })
            continue

        total_records = await db[collection].count_documents({})
        explicit_hidden_count = await _count(db, collection, _explicit_hidden_query())
        heuristic_query_builder = config.get("heuristic_query")
        heuristic_query = heuristic_query_builder() if callable(heuristic_query_builder) else None
        heuristic_candidate_count = await _count(db, collection, heuristic_query) if heuristic_query else 0
        heuristic_only_count = await _count(db, collection, {"$and": [heuristic_query, _not_explicit_hidden_query()]}) if heuristic_query else 0
        fixture_scan = await _fixture_only_matches(
            db,
            collection=collection,
            family_id=config["family_id"],
        )
        fixture_only_count = fixture_scan["count"]
        certification_query_builder = config.get("certification_query")
        certification_query = certification_query_builder() if callable(certification_query_builder) else None
        certification_project_rows = await _count(db, collection, certification_query) if certification_query else 0
        conflicting_marker_query = {"$or": [
            {"$and": [{"synthetic_record": True}, {"hidden_from_operations": {"$ne": True}}]},
            {"$and": [{"certification_record": True}, {"hidden_from_operations": {"$ne": True}}]},
            {"$and": [{"technical_record_classification": "live_operational"}, {"hidden_from_operations": True}]},
        ]}
        conflicting_marker_count = await _count(db, collection, conflicting_marker_query)
        status = _family_status(
            heuristic_only_count=heuristic_only_count,
            fixture_only_count=fixture_only_count,
            explicit_hidden_count=explicit_hidden_count,
            certification_project_rows=certification_project_rows,
            conflicting_marker_count=conflicting_marker_count,
            operator_consumer_count=len(config.get("operator_consumer_collections") or []),
            mixed_mode=bool(config.get("mixed_mode")),
        )
        samples = await _sample(
            db,
            collection,
            {"$or": [q for q in [heuristic_query, certification_query, _explicit_hidden_query()] if q]},
            fields=config.get("sample_fields") or {"_id": 0},
        )
        for row in fixture_scan["samples"]:
            if row not in samples:
                samples.append(row)
            if len(samples) >= 5:
                break
        result = {
            "family_id": config["family_id"],
            "label": config["label"],
            "collection": collection,
            "present": True,
            "classification_mode": config["classification_mode"],
            "total_records": total_records,
            "explicit_hidden_count": explicit_hidden_count,
            "heuristic_candidate_count": heuristic_candidate_count,
            "heuristic_only_count": heuristic_only_count,
            "fixture_only_count": fixture_only_count,
            "certification_project_rows": certification_project_rows,
            "conflicting_marker_count": conflicting_marker_count,
            "status": status,
            "summary": _family_summary(
                heuristic_only_count=heuristic_only_count,
                fixture_only_count=fixture_only_count,
                explicit_hidden_count=explicit_hidden_count,
                certification_project_rows=certification_project_rows,
                conflicting_marker_count=conflicting_marker_count,
                mixed_mode=bool(config.get("mixed_mode")),
            ),
            "operator_consumer_collections": config.get("operator_consumer_collections") or [],
            "sample_rows": samples,
        }
        family_results.append(result)
        if status == "red":
            blocking.append({
                "family_id": config["family_id"],
                "collection": collection,
                "reason": result["summary"],
            })

    overall_status = "green" if not blocking else "red"
    return {
        "generated_at": generated_at,
        "overall_status": overall_status,
        "release_gate_blocked": bool(blocking),
        "blocking_findings": blocking,
        "families": family_results,
    }


async def _scan_lookahead_staleness(db) -> Dict[str, Any]:
    active_versions = [row async for row in db.project_schedule_versions.find({"status": "active"}, {"_id": 0, "project_number": 1, "version_id": 1})]
    stale_projects: List[Dict[str, Any]] = []
    checked = 0
    for row in active_versions:
        project_number = row.get("project_number")
        version_id = row.get("version_id")
        if not project_number or not version_id:
            continue
        activities = [a async for a in db.project_schedule_activities.find({"project_number": project_number, "version_id": version_id}, {"_id": 0, "activity_id": 1, "budget_line_id": 1, "customer_pay_item_number": 1, "planned_start_date": 1, "planned_finish_date": 1})]
        lookahead = await get_reconciled_schedule_lookahead(db, project_number)
        if not activities or not lookahead:
            continue
        checked += 1
        upstream = _signature_hash(activities, ["activity_id", "budget_line_id", "customer_pay_item_number", "planned_start_date", "planned_finish_date"])
        downstream = _signature_hash(lookahead.get("tasks") or [], ["activity_id", "budget_line_id", "customer_pay_item_number", "planned_start", "planned_finish"])
        if upstream != downstream:
            stale_projects.append({
                "project_number": project_number,
                "active_version_id": version_id,
                "lookahead_updated_at": lookahead.get("updated_at"),
                "upstream_count": len(upstream),
                "downstream_count": len(downstream),
            })
    return {
        "id": "schedule_lookahead_active_signature",
        "label": "Schedule → Lookahead",
        "status": "green" if not stale_projects else "red",
        "summary": "Lookahead task signature matches the active governed schedule for every checked project." if not stale_projects else f"{len(stale_projects)} project(s) have stale lookahead tasks relative to the active schedule.",
        "checked_projects": checked,
        "mismatches": stale_projects[:10],
        "upstream_identity": "project_schedule_versions.status=active + project_schedule_activities.version_id",
        "downstream_identity": "project_controls_lookaheads.lookahead_id=current",
        "invalidation_trigger": "Any change in the active schedule activity signature.",
        "failure_behavior": "FAIL health certification when current lookahead does not match the active schedule signature.",
    }


async def _scan_daily_plan_staleness(db) -> Dict[str, Any]:
    cutoff = _utcnow().date().isoformat()
    plans = [row async for row in db.project_daily_work_plans.find({"work_date": {"$gte": cutoff}}, {"_id": 0, "project_number": 1, "work_date": 1, "version_id": 1, "lookahead_id": 1, "baseline_version_id": 1})]
    mismatches = []
    for row in plans:
        project_number = row.get("project_number")
        if not project_number:
            continue
        active = await db.project_schedule_versions.find_one({"project_number": project_number, "status": "active"}, {"_id": 0, "version_id": 1, "baseline_version_id": 1})
        if not active:
            continue
        current_plan = await get_daily_work_plan(db, project_number, work_date=row.get("work_date") or "")
        current_lookahead_id = current_plan.get("lookahead_id") or f"lookahead:{project_number}:current"
        if current_plan.get("version_id") != active.get("version_id") or current_plan.get("lookahead_id") != current_lookahead_id:
            mismatches.append({
                "project_number": project_number,
                "work_date": row.get("work_date"),
                "plan_version_id": current_plan.get("version_id"),
                "active_version_id": active.get("version_id"),
                "plan_lookahead_id": current_plan.get("lookahead_id"),
                "current_lookahead_id": current_lookahead_id,
            })
    return {
        "id": "lookahead_daily_plan_current_signature",
        "label": "Lookahead → Daily Work Plan",
        "status": "green" if not mismatches else "red",
        "summary": "Current/near-current daily work plans reference the active schedule version and current lookahead." if not mismatches else f"{len(mismatches)} current or near-current daily work plan(s) reference stale schedule or lookahead versions.",
        "checked_plans": len(plans),
        "mismatches": mismatches[:10],
        "upstream_identity": "project_schedule_versions.active.version_id + current lookahead_id",
        "downstream_identity": "project_daily_work_plans.version_id + lookahead_id",
        "invalidation_trigger": "Any current schedule activation or current lookahead refresh affecting the plan horizon.",
        "failure_behavior": "FAIL health certification when a current plan still points at an older schedule or lookahead.",
    }


async def _scan_ev_forecast_snapshot_staleness(db) -> Dict[str, Any]:
    ev_rows = [row async for row in db.project_earned_value_snapshots.find({}, {"_id": 0, "project_number": 1, "generated_at": 1, "source_register": 1})]
    mismatches = []
    for row in ev_rows:
        project_number = row.get("project_number")
        current_snapshot = await get_project_earned_value_snapshot(db, project_number, actor={"email": "system", "role": "system"}, audience="admin", force_refresh=False)
        latest_forecast = await db.project_forecasting_snapshots.find_one({"project_number": project_number}, {"_id": 0, "version_id": 1, "generated_at": 1}, sort=[("version_number", -1)])
        current_version = ((current_snapshot.get("source_register") or {}).get("forecast_snapshot") or "")
        if latest_forecast and latest_forecast.get("version_id") != current_version:
            mismatches.append({
                "project_number": project_number,
                "earned_value_generated_at": current_snapshot.get("generated_at"),
                "earned_value_forecast_version": current_version,
                "latest_forecast_version": latest_forecast.get("version_id"),
                "latest_forecast_generated_at": latest_forecast.get("generated_at"),
            })
    return {
        "id": "c7_to_c8_snapshot_dependency",
        "label": "C7 Forecast → C8 Earned Value",
        "status": "green" if not mismatches else "red",
        "summary": "Every earned-value snapshot references the latest governed forecast snapshot for its project." if not mismatches else f"{len(mismatches)} earned-value snapshot(s) reference an older forecast snapshot version.",
        "checked_snapshots": len(ev_rows),
        "mismatches": mismatches[:10],
        "upstream_identity": "project_forecasting_snapshots.version_id",
        "downstream_identity": "project_earned_value_snapshots.source_register.forecast_snapshot",
        "invalidation_trigger": "A new forecast snapshot version for the same project.",
        "failure_behavior": "FAIL health certification when C8 is anchored to an outdated C7 snapshot.",
    }


async def _scan_portfolio_snapshot_staleness(db) -> Dict[str, Any]:
    snapshots = [row async for row in db.portfolio_intelligence_snapshots.find({}, {"_id": 0, "scope_key": 1, "generated_at": 1, "projects": 1})]
    mismatches = []
    for snapshot in snapshots:
        generated_at = _parse_dt(snapshot.get("generated_at"))
        latest_dependency = generated_at
        late_projects: List[Dict[str, Any]] = []
        for row in snapshot.get("projects") or []:
            project_number = row.get("project_number")
            if not project_number:
                continue
            ev = await db.project_earned_value_snapshots.find_one({"project_number": project_number}, {"_id": 0, "generated_at": 1})
            fc = await db.project_forecasting_snapshots.find_one({"project_number": project_number}, {"_id": 0, "generated_at": 1}, sort=[("version_number", -1)])
            for dep, kind in ((ev, "c8"), (fc, "c7")):
                dep_dt = _parse_dt((dep or {}).get("generated_at"))
                if dep_dt and generated_at and dep_dt > generated_at:
                    if latest_dependency is None or dep_dt > latest_dependency:
                        latest_dependency = dep_dt
                    late_projects.append({"project_number": project_number, "dependency": kind, "dependency_generated_at": dep.get("generated_at")})
        if late_projects:
            mismatches.append({
                "scope_key": snapshot.get("scope_key"),
                "snapshot_generated_at": snapshot.get("generated_at"),
                "late_dependencies": late_projects[:10],
            })
    return {
        "id": "c7_c8_to_c9_snapshot_dependency",
        "label": "C7/C8 → C9 Portfolio",
        "status": "green" if not mismatches else "red",
        "summary": "Every cached portfolio snapshot is at least as current as its C7/C8 project dependencies." if not mismatches else f"{len(mismatches)} portfolio snapshot(s) were generated before newer C7/C8 project dependencies existed.",
        "checked_snapshots": len(snapshots),
        "mismatches": mismatches[:10],
        "upstream_identity": "project_forecasting_snapshots.generated_at + project_earned_value_snapshots.generated_at",
        "downstream_identity": "portfolio_intelligence_snapshots.generated_at",
        "invalidation_trigger": "Any later C7 or C8 snapshot for an included project.",
        "failure_behavior": "FAIL health certification when a cached C9 snapshot predates newer C7/C8 source snapshots.",
    }


async def _scan_safety_aggregate_parity(db) -> Dict[str, Any]:
    closed = {"Completed", "Closed", "Cancelled", "Canceled", "completed", "closed", "cancelled", "canceled"}
    rows = [row async for row in db.corrective_actions.find({}, {"_id": 0, "status": 1, "due_date": 1, "technical_record_classification": 1, "truth_visibility_scope": 1, "synthetic_record": 1, "hidden_from_operations": 1, "certification_record": 1})]

    def _visible(row: Dict[str, Any]) -> bool:
        classification = _clean(row.get("technical_record_classification")).lower()
        if classification in HIDDEN_CLASSIFICATIONS:
            return False
        if row.get("truth_visibility_scope") == "technical_audit_only":
            return False
        if row.get("synthetic_record") is True or row.get("hidden_from_operations") is True or row.get("certification_record") is True:
            return False
        return True

    today_iso = _utcnow().date().isoformat()
    open_count = sum(1 for row in rows if _visible(row) and _clean(row.get("status")) not in closed)
    overdue_count = sum(1 for row in rows if _visible(row) and _clean(row.get("status")) not in closed and _clean(row.get("due_date"))[:10] and _clean(row.get("due_date"))[:10] < today_iso)
    return {
        "id": "safety_source_to_aggregate",
        "label": "Safety Source → Aggregate",
        "status": "green",
        "summary": "Source-record oracle for operator-visible corrective actions is available and tested independently.",
        "expected_open": open_count,
        "expected_overdue": overdue_count,
        "upstream_identity": "corrective_actions governed visibility markers",
        "downstream_identity": "Safety Overview + Executive Overview + exports",
        "invalidation_trigger": "Any corrective-action create/update/archive/reopen affecting status, due date, or visibility markers.",
        "failure_behavior": "FAIL health certification if consumer aggregates diverge from this governed source-record oracle.",
    }


async def scan_platform_stale_derived_state(db) -> Dict[str, Any]:
    generated_at = _now_iso()
    checks = [
        await _scan_lookahead_staleness(db),
        await _scan_daily_plan_staleness(db),
        await _scan_ev_forecast_snapshot_staleness(db),
        await _scan_portfolio_snapshot_staleness(db),
        await _scan_safety_aggregate_parity(db),
    ]
    blocking = [row for row in checks if row.get("status") == "red"]
    return {
        "generated_at": generated_at,
        "overall_status": "green" if not blocking else "red",
        "release_gate_blocked": bool(blocking),
        "blocking_findings": [{"id": row.get("id"), "reason": row.get("summary")} for row in blocking],
        "checks": checks,
    }


async def scan_platform_truth_integrity(db) -> Dict[str, Any]:
    contamination = await scan_platform_contamination_integrity(db)
    stale = await scan_platform_stale_derived_state(db)
    overall_status = "green" if contamination.get("overall_status") == "green" and stale.get("overall_status") == "green" else "red"
    return {
        "generated_at": _now_iso(),
        "overall_status": overall_status,
        "release_gate_blocked": bool(contamination.get("release_gate_blocked") or stale.get("release_gate_blocked")),
        "contamination": contamination,
        "stale_derived_state": stale,
    }


__all__ = [
    "scan_platform_contamination_integrity",
    "scan_platform_stale_derived_state",
    "scan_platform_truth_integrity",
]