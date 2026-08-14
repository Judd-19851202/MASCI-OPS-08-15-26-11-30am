from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Set, Tuple

from lib.cross_entity_exception_state import CROSS_ENTITY_EXCEPTION_COLLECTION
from lib.governed_fixture_evidence import find_fixture_evidence, governed_fixture_markers
from lib.governed_record_classification import is_hidden_from_live_operations


ACTIVE_DISPATCH_STATES = {"ASSIGNED", "EN_ROUTE", "IN_TRANSIT"}
CURRENT_DAYS_WINDOW = 30

FAMILY_TO_COLLECTION = {
    "meeting_attendee_identity_normalization": "meetings",
    "incident_project_and_submitter_lineage": "incidents",
    "daily_report_project_and_submitter_lineage": "daily_reports",
    "equipment_preop_asset_and_operator_lineage": "equipment_inspections",
    "dispatch_driver_truck_project_linkage": "dispatch_assignments",
}

COLLECTION_TO_FIXTURE_FAMILY = {
    "meetings": "meetings",
    "incidents": "incidents",
    "daily_reports": "daily_reports",
    "equipment_inspections": "equipment_inspections",
    "dispatch_assignments": "dispatch_assignments",
}

MATERIAL_CURRENT_TRUTH_RELATIONSHIPS = {
    ("dispatch_assignments", "project_lineage"),
    ("dispatch_assignments", "driver_lineage"),
    ("dispatch_assignments", "truck_lineage"),
    ("dispatch_assignments", "equipment_lineage"),
    ("dispatch_assignments", "active_scope"),
}

MATERIAL_DOWNSTREAM_CATEGORIES = {
    "meeting_attendee_identity_normalization": ["operator_history", "safety_decision", "downstream_engine"],
    "incident_project_and_submitter_lineage": ["operator_history", "safety_decision", "kpi", "downstream_engine"],
    "daily_report_project_and_submitter_lineage": ["operator_history", "kpi", "workflow", "downstream_engine"],
    "equipment_preop_asset_and_operator_lineage": ["operator_history", "workflow", "safety_decision", "downstream_engine"],
    "dispatch_driver_truck_project_linkage": ["operator_history", "workflow", "assignment", "downstream_engine"],
}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _parse_dt(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    text = _clean(value)
    if not text:
        return None
    try:
        text = text.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(text)
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except Exception:
        return None


def _age_days_bucket(value: Optional[int]) -> str:
    if value is None:
        return "unknown"
    if value <= 30:
        return "0-30"
    if value <= 90:
        return "31-90"
    if value <= 180:
        return "91-180"
    if value <= 365:
        return "181-365"
    return "366+"


def _count_map(values: Iterable[str]) -> Dict[str, int]:
    out: Dict[str, int] = {}
    for value in values:
        out[value] = out.get(value, 0) + 1
    return dict(sorted(out.items(), key=lambda item: (-item[1], item[0])))


def _active_employee(row: Optional[Dict[str, Any]]) -> bool:
    if not row:
        return False
    if row.get("is_active") is True:
        return True
    for key in ("status", "employment_status"):
        if _clean(row.get(key)).lower() == "active":
            return True
    return False


def _active_project(row: Optional[Dict[str, Any]]) -> bool:
    if not row:
        return False
    if row.get("active") is True or row.get("is_active") is True:
        return True
    status = _clean(row.get("status")).lower()
    if status in {"active", "in_progress", "open"}:
        return True
    if row.get("completed") is True:
        return False
    return False


def _active_equipment(row: Optional[Dict[str, Any]]) -> bool:
    if not row:
        return False
    if row.get("is_active") is True or row.get("active") is True:
        return _clean(row.get("status")).lower() != "retired"
    status = _clean(row.get("status")).lower()
    return status in {"available", "inspection hold", "safety hold", "maintenance hold", "active"}


def _active_vehicle(row: Optional[Dict[str, Any]]) -> bool:
    if not row:
        return False
    status = _clean(row.get("status")).lower()
    return status in {"active", "pending_review"}


def _source_age_days(source_row: Optional[Dict[str, Any]]) -> Optional[int]:
    if not source_row:
        return None
    for key in (
        "report_date",
        "incident_date",
        "meeting_date",
        "inspection_date",
        "occurred_at",
        "assigned_at",
        "created_at",
    ):
        parsed = _parse_dt(source_row.get(key))
        if parsed:
            return max(0, (datetime.now(timezone.utc) - parsed.astimezone(timezone.utc)).days)
    return None


def _current_live_source(*, source_collection: str, source_row: Optional[Dict[str, Any]], source_age_days: Optional[int]) -> bool:
    if not source_row:
        return False
    if source_collection == "dispatch_assignments":
        return _clean(source_row.get("current_state")).upper() in ACTIVE_DISPATCH_STATES and not is_hidden_from_live_operations(source_row)
    if source_collection in {"daily_reports", "incidents", "meetings", "equipment_inspections"}:
        return source_age_days is not None and source_age_days <= CURRENT_DAYS_WINDOW and not is_hidden_from_live_operations(source_row)
    return False


def _cause_flags(exception_row: Dict[str, Any]) -> Dict[str, bool]:
    reason_code = _clean(exception_row.get("reason_code"))
    candidate_count = len(exception_row.get("candidate_matches") or [])
    missing_source_evidence = not bool(exception_row.get("evidence_available"))
    missing_canonical_id = reason_code in {
        "legacy_project_without_canonical_jobs_master_match",
        "dispatch_project_without_canonical_jobs_master_match",
        "dispatch_equipment_reference_without_canonical_match",
        "legacy_submitter_without_deterministic_employee_match",
        "legacy_operator_without_deterministic_employee_match",
        "legacy_dispatch_driver_without_deterministic_transport_match",
        "legacy_dispatch_truck_without_deterministic_transport_match",
        "meeting_attendee_requires_documented_review",
        "active_dispatch_without_project_scope",
    }
    ambiguous_identity = candidate_count > 1 or reason_code == "meeting_attendee_requires_documented_review"
    requires_guessing = (
        exception_row.get("status") == "accepted_historical_gap"
        and reason_code != "non_masci_tenant_fixture"
        and (candidate_count != 1 or missing_canonical_id)
    )
    return {
        "missing_canonical_id": missing_canonical_id,
        "ambiguous_identity": ambiguous_identity,
        "missing_source_evidence": missing_source_evidence,
        "requires_guessing": requires_guessing,
    }


def _downstream_flags(exception_row: Dict[str, Any]) -> Dict[str, bool]:
    categories = MATERIAL_DOWNSTREAM_CATEGORIES.get(_clean(exception_row.get("family")), [])
    return {
        "operator_history": "operator_history" in categories,
        "kpi": "kpi" in categories,
        "workflow": "workflow" in categories,
        "qualification": "qualification" in categories,
        "safety_decision": "safety_decision" in categories,
        "assignment": "assignment" in categories,
        "downstream_engine": "downstream_engine" in categories,
    }


async def _load_map(db, collection: str, projection: Dict[str, int], *, key: str = "id") -> Dict[str, Dict[str, Any]]:
    if collection not in await db.list_collection_names():
        return {}
    rows = [row async for row in db[collection].find({}, projection)]
    return {
        _clean(row.get(key)): {k: v for k, v in row.items() if k != "_id"}
        for row in rows
        if _clean(row.get(key))
    }


async def _load_lookup_context(db) -> Dict[str, Any]:
    employees = [
        row async for row in db.employees.find(
            {}, {"_id": 0, "id": 1, "employee_id": 1, "is_active": 1, "status": 1, "employment_status": 1}
        )
    ]
    jobs = [
        row async for row in db.jobs_master.find(
            {}, {"_id": 0, "project_number": 1, "project_name": 1, "active": 1, "is_active": 1, "status": 1, "completed": 1}
        )
    ]
    equipment = [
        row async for row in db.equipment_master.find(
            {}, {"_id": 0, "id": 1, "unit_number": 1, "is_active": 1, "active": 1, "status": 1}
        )
    ]
    vehicles = [
        row async for row in db.transport_trucks.find(
            {}, {"_id": 0, "id": 1, "truck_number": 1, "status": 1, "equipment_id": 1}
        )
    ]
    return {
        "employees_by_id": {_clean(row.get("id")): row for row in employees if _clean(row.get("id"))},
        "employees_by_code": {_clean(row.get("employee_id")): row for row in employees if _clean(row.get("employee_id"))},
        "jobs_by_number": {_clean(row.get("project_number")): row for row in jobs if _clean(row.get("project_number"))},
        "jobs_by_name": {_clean(row.get("project_name")).lower(): row for row in jobs if _clean(row.get("project_name"))},
        "equipment_by_id": {_clean(row.get("id")): row for row in equipment if _clean(row.get("id"))},
        "equipment_by_unit": {_clean(row.get("unit_number")): row for row in equipment if _clean(row.get("unit_number"))},
        "vehicles_by_id": {_clean(row.get("id")): row for row in vehicles if _clean(row.get("id"))},
        "vehicles_by_number": {_clean(row.get("truck_number")): row for row in vehicles if _clean(row.get("truck_number"))},
    }


async def normalize_cross_entity_exception_state(db) -> Dict[str, Any]:
    if CROSS_ENTITY_EXCEPTION_COLLECTION not in await db.list_collection_names():
        return {"updated_source_rows": 0, "updated_exception_rows": 0, "fixture_rows_hidden": 0}

    source_maps = {
        coll: await _load_map(db, coll, {"_id": 0}, key="id")
        for coll in COLLECTION_TO_FIXTURE_FAMILY
    }

    updated_source_rows = 0
    fixture_rows_hidden = 0
    for coll, family in COLLECTION_TO_FIXTURE_FAMILY.items():
        collection = db[coll]
        for row in source_maps[coll].values():
            if is_hidden_from_live_operations(row):
                continue
            markers = governed_fixture_markers(row, family)
            if not markers:
                continue
            await collection.update_one({"id": row.get("id")}, {"$set": markers})
            row.update(markers)
            updated_source_rows += 1
            fixture_rows_hidden += 1

    updated_exception_rows = 0
    cursor = db[CROSS_ENTITY_EXCEPTION_COLLECTION].find({"active": True}, {"_id": 0})
    async for exception_row in cursor:
        coll = _clean(exception_row.get("source_collection"))
        source_row = source_maps.get(coll, {}).get(_clean(exception_row.get("source_record_id")))
        if not source_row:
            continue
        fixture_family = COLLECTION_TO_FIXTURE_FAMILY.get(coll)
        fixture = bool(find_fixture_evidence(source_row, fixture_family)) if fixture_family else False
        hidden = is_hidden_from_live_operations(source_row)
        if not (fixture or hidden):
            continue
        if exception_row.get("status") == "excluded_non_operational" and exception_row.get("review_status") == "documented_excluded":
            continue
        updates = {
            "status": "excluded_non_operational",
            "review_status": "documented_excluded",
            "blocks_gate": False,
            "active": True,
            "updated_at": _now_iso(),
            "reason_code": "fixture_record_with_verified_test_provenance",
            "reason_detail": "Source record is explicitly governed as non-operational by deterministic fixture evidence or existing governed hidden markers.",
            "evidence_available": True,
        }
        if fixture and fixture_family:
            rule = find_fixture_evidence(source_row, fixture_family) or {}
            evidence_summary = dict(exception_row.get("evidence_summary") or {})
            evidence_summary.setdefault("fixture_evidence_source", _clean(rule.get("evidence_source")))
            updates["evidence_summary"] = evidence_summary
        await db[CROSS_ENTITY_EXCEPTION_COLLECTION].update_one(
            {"key": exception_row.get("key")},
            {"$set": updates},
        )
        updated_exception_rows += 1

    return {
        "updated_source_rows": updated_source_rows,
        "updated_exception_rows": updated_exception_rows,
        "fixture_rows_hidden": fixture_rows_hidden,
    }


async def scan_cross_entity_exception_reconciliation(db) -> Dict[str, Any]:
    # Stream the full active population so the reconciliation total and all
    # breakdowns never truncate at a fixed cap (future-scale correctness).
    rows = [r async for r in db[CROSS_ENTITY_EXCEPTION_COLLECTION].find({"active": True}, {"_id": 0})]
    context = await _load_lookup_context(db)
    source_maps = {
        coll: await _load_map(db, coll, {"_id": 0}, key="id")
        for coll in COLLECTION_TO_FIXTURE_FAMILY
    }

    total = len(rows)
    by_family = _count_map(_clean(row.get("family")) for row in rows)
    by_relationship_type = _count_map(_clean(row.get("relationship_type")) for row in rows)
    by_reason_code = _count_map(_clean(row.get("reason_code")) for row in rows)
    by_status = _count_map(_clean(row.get("status")) for row in rows)
    age_bands = _count_map(_age_days_bucket(row.get("age_days")) for row in rows)

    active_employee = active_project = active_equipment = active_vehicle = 0
    current_live = historical_legacy = 0
    missing_canonical_id = ambiguous_identity = missing_source_evidence = requires_guessing = 0
    operator_history = kpi = workflow = qualification = safety_decision = assignment = downstream_engine = 0
    any_material_downstream = 0
    materially_misclassified = 0
    hidden_or_fixture = 0
    current_live_nonblocking = 0
    current_live_by_family: Dict[str, int] = {}
    current_live_by_reason: Dict[str, int] = {}
    current_live_by_relationship: Dict[str, int] = {}

    samples: List[Dict[str, Any]] = []

    for row in rows:
        coll = _clean(row.get("source_collection"))
        source_row = source_maps.get(coll, {}).get(_clean(row.get("source_record_id")))
        fixture = False
        if source_row and COLLECTION_TO_FIXTURE_FAMILY.get(coll):
            fixture = bool(find_fixture_evidence(source_row, COLLECTION_TO_FIXTURE_FAMILY[coll]))
        hidden = is_hidden_from_live_operations(source_row)
        if fixture or hidden:
            hidden_or_fixture += 1

        source_age_days = row.get("age_days") if row.get("age_days") is not None else _source_age_days(source_row)
        raw_current_live = _current_live_source(
            source_collection=coll,
            source_row=source_row,
            source_age_days=source_age_days,
        )
        current_live_flag = raw_current_live and not hidden and not fixture and _clean(row.get("status")) != "excluded_non_operational"
        if current_live_flag:
            current_live += 1
            current_live_by_family[_clean(row.get("family"))] = current_live_by_family.get(_clean(row.get("family")), 0) + 1
            current_live_by_reason[_clean(row.get("reason_code"))] = current_live_by_reason.get(_clean(row.get("reason_code")), 0) + 1
            current_live_by_relationship[_clean(row.get("relationship_type"))] = current_live_by_relationship.get(_clean(row.get("relationship_type")), 0) + 1
        else:
            historical_legacy += 1

        employee_hits: Set[str] = set()
        project_hits: Set[str] = set()
        equipment_hits: Set[str] = set()
        vehicle_hits: Set[str] = set()

        for candidate in row.get("candidate_matches") or []:
            emp = context["employees_by_id"].get(_clean(candidate.get("id"))) or context["employees_by_code"].get(_clean(candidate.get("employee_id")))
            if _active_employee(emp):
                employee_hits.add(_clean(candidate.get("id")) or _clean(candidate.get("employee_id")))

        project_number = _clean(row.get("source_project_number"))
        project_name = _clean(row.get("source_project_name")).lower()
        project_row = context["jobs_by_number"].get(project_number) or context["jobs_by_name"].get(project_name)
        if _active_project(project_row):
            project_hits.add(_clean(project_row.get("project_number")))

        if source_row:
            for key in ("employee_master_id", "reported_by_employee_id", "prepared_by_employee_id", "operator_employee_id"):
                employee_row = context["employees_by_id"].get(_clean(source_row.get(key))) or context["employees_by_code"].get(_clean(source_row.get(key)))
                if _active_employee(employee_row):
                    employee_hits.add(_clean(source_row.get(key)))
            for key in ("equipment_master_id", "equipment_id"):
                equipment_row = context["equipment_by_id"].get(_clean(source_row.get(key)))
                if _active_equipment(equipment_row):
                    equipment_hits.add(_clean(source_row.get(key)))
            vehicle_row = context["vehicles_by_id"].get(_clean(source_row.get("truck_id"))) or context["vehicles_by_number"].get(_clean(source_row.get("truck_id")))
            if _active_vehicle(vehicle_row):
                vehicle_hits.add(_clean(source_row.get("truck_id")))

        if employee_hits:
            active_employee += 1
        if project_hits:
            active_project += 1
        if equipment_hits:
            active_equipment += 1
        if vehicle_hits:
            active_vehicle += 1

        cause_flags = _cause_flags(row)
        missing_canonical_id += 1 if cause_flags["missing_canonical_id"] else 0
        ambiguous_identity += 1 if cause_flags["ambiguous_identity"] else 0
        missing_source_evidence += 1 if cause_flags["missing_source_evidence"] else 0
        requires_guessing += 1 if cause_flags["requires_guessing"] else 0

        downstream_flags = _downstream_flags(row)
        operator_history += 1 if downstream_flags["operator_history"] else 0
        kpi += 1 if downstream_flags["kpi"] else 0
        workflow += 1 if downstream_flags["workflow"] else 0
        qualification += 1 if downstream_flags["qualification"] else 0
        safety_decision += 1 if downstream_flags["safety_decision"] else 0
        assignment += 1 if downstream_flags["assignment"] else 0
        downstream_engine += 1 if downstream_flags["downstream_engine"] else 0
        if any(downstream_flags.values()):
            any_material_downstream += 1

        nonblocking = not bool(row.get("blocks_gate"))
        material_current_truth = (coll, _clean(row.get("relationship_type"))) in MATERIAL_CURRENT_TRUTH_RELATIONSHIPS
        if current_live_flag and nonblocking:
            current_live_nonblocking += 1
        if current_live_flag and nonblocking and material_current_truth and not (hidden or fixture):
            materially_misclassified += 1
            if len(samples) < 15:
                samples.append(
                    {
                        "key": row.get("key"),
                        "family": row.get("family"),
                        "relationship_type": row.get("relationship_type"),
                        "reason_code": row.get("reason_code"),
                        "source_collection": coll,
                        "source_record_id": row.get("source_record_id"),
                    }
                )

    return {
        "generated_at": _now_iso(),
        "total_exceptions": total,
        "count_by_source_family": by_family,
        "count_by_relationship_type": by_relationship_type,
        "count_by_reason_code": by_reason_code,
        "count_by_status": by_status,
        "count_by_age_time_period": age_bands,
        "active_entity_involvement": {
            "active_employees": active_employee,
            "active_projects": active_project,
            "active_equipment": active_equipment,
            "active_vehicles": active_vehicle,
        },
        "record_temporality": {
            "current_live_operational_records": current_live,
            "historical_or_legacy_records": historical_legacy,
            "hidden_or_fixture_records": hidden_or_fixture,
        },
        "cause_summary": {
            "missing_canonical_ids": missing_canonical_id,
            "ambiguous_identity": ambiguous_identity,
            "missing_source_evidence": missing_source_evidence,
            "deterministic_backfill_would_require_guessing": requires_guessing,
        },
        "downstream_relevance": {
            "operator_facing_history_or_profile": operator_history,
            "kpi_or_derived_state": kpi,
            "workflow": workflow,
            "qualification": qualification,
            "safety_decision": safety_decision,
            "assignment": assignment,
            "downstream_engine_or_export": downstream_engine,
            "any_material_downstream_relevance": any_material_downstream,
        },
        "classification_integrity": {
            "materially_misclassified_exceptions": materially_misclassified,
            "non_blocking_current_live_exceptions": current_live_nonblocking,
            "fixture_or_hidden_source_exceptions": hidden_or_fixture,
        },
        "non_blocking_current_live_breakdown": {
            "by_source_family": dict(sorted(current_live_by_family.items(), key=lambda item: (-item[1], item[0]))),
            "by_reason_code": dict(sorted(current_live_by_reason.items(), key=lambda item: (-item[1], item[0]))),
            "by_relationship_type": dict(sorted(current_live_by_relationship.items(), key=lambda item: (-item[1], item[0]))),
        },
        "methodology": {
            "current_live_operational_definition": "Dispatch rows are current/live when current_state is ASSIGNED, EN_ROUTE, or IN_TRANSIT. Meetings, incidents, daily reports, and equipment inspections are current/live when the source event date is within the last 30 days and the source row is not hidden from live operations.",
            "active_entity_definition": "Employees use is_active/status, projects use jobs_master.active/status, equipment uses is_active/status != Retired, and vehicles use transport_trucks.status in {active,pending_review}.",
            "non_blocking_rule": "Exceptions remain non-blocking only when source evidence is preserved and leaving the row unresolved cannot create materially false current operational truth. Deterministic fixture evidence and governed hidden markers are excluded from current-live truth counts.",
        },
        "material_misclassification_samples": samples,
    }


async def cross_entity_exception_reconciliation_csv(db) -> str:
    reconciliation = await scan_cross_entity_exception_reconciliation(db)
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["section", "metric", "count"])
    writer.writerow(["summary", "total_exceptions", reconciliation["total_exceptions"]])
    for section in (
        "count_by_source_family",
        "count_by_relationship_type",
        "count_by_reason_code",
        "count_by_status",
        "count_by_age_time_period",
    ):
        for metric, count in reconciliation.get(section, {}).items():
            writer.writerow([section, metric, count])
    for section in ("active_entity_involvement", "record_temporality", "cause_summary", "downstream_relevance", "classification_integrity"):
        for metric, count in reconciliation.get(section, {}).items():
            writer.writerow([section, metric, count])
    return buf.getvalue()


__all__ = [
    "normalize_cross_entity_exception_state",
    "scan_cross_entity_exception_reconciliation",
    "cross_entity_exception_reconciliation_csv",
]