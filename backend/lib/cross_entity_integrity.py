from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional, Set

from lib.governed_record_classification import is_hidden_from_live_operations


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _unique(values: Iterable[str]) -> Set[str]:
    return {v for v in values if v}


async def _binding_ids(db, workflow: str) -> Set[str]:
    if "field_submitter_bindings" not in await db.list_collection_names():
        return set()
    rows = [
        _clean(row.get("submission_record_id"))
        async for row in db.field_submitter_bindings.find(
            {
                "submission_workflow": workflow,
                "submitter_canonical_id": {"$nin": [None, ""]},
            },
            {"_id": 0, "submission_record_id": 1},
        )
    ]
    return _unique(rows)


async def _list_visible(db, collection: str, projection: Dict[str, int]) -> List[Dict[str, Any]]:
    if collection not in await db.list_collection_names():
        return []
    rows: List[Dict[str, Any]] = []
    async for row in db[collection].find({}, projection):
        row.pop("_id", None)
        if is_hidden_from_live_operations(row):
            continue
        rows.append(row)
    return rows


def _check(
    *,
    check_id: str,
    label: str,
    status: str,
    summary: str,
    canonical_entity: str,
    source_authority: str,
    downstream_consumers: List[str],
    counts: Dict[str, Any],
    sample_rows: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    return {
        "id": check_id,
        "label": label,
        "status": status,
        "summary": summary,
        "canonical_entity": canonical_entity,
        "source_authority": source_authority,
        "downstream_consumers": downstream_consumers,
        "counts": counts,
        "sample_rows": sample_rows or [],
    }


async def scan_cross_entity_integrity(db) -> Dict[str, Any]:
    jobs = [
        row async for row in db.jobs_master.find(
            {}, {"_id": 0, "project_number": 1, "project_name": 1}
        )
    ]
    project_numbers = _unique(_clean(row.get("project_number")) for row in jobs)

    employees = [
        row async for row in db.employees.find(
            {}, {"_id": 0, "id": 1, "employee_id": 1, "email": 1}
        )
    ]
    employee_ids = _unique(_clean(row.get("id")) for row in employees)
    employee_codes = _unique(_clean(row.get("employee_id")) for row in employees)
    employee_emails = _unique(_clean(row.get("email")).lower() for row in employees)
    user_directory_emails = set()
    if "user_directory" in await db.list_collection_names():
        user_directory_emails = _unique([
            _clean(row.get("email")).lower()
            async for row in db.user_directory.find({}, {"_id": 0, "email": 1})
        ])

    equipment = [
        row async for row in db.equipment_master.find(
            {}, {"_id": 0, "id": 1, "unit_number": 1}
        )
    ]
    equipment_ids = _unique(_clean(row.get("id")) for row in equipment)
    equipment_units = _unique(_clean(row.get("unit_number")).lower() for row in equipment)

    transport_people = [
        row async for row in db.transport_persons.find(
            {"status": {"$ne": "inactive"}}, {"_id": 0, "id": 1, "employee_id": 1, "kind": 1}
        )
    ]
    driver_ids = _unique(_clean(row.get("id")) for row in transport_people)
    person_employee_ids = [_clean(row.get("employee_id")) for row in transport_people if row.get("kind") == "masci_employee"]

    transport_trucks = [
        row async for row in db.transport_trucks.find(
            {"status": {"$ne": "inactive"}}, {"_id": 0, "id": 1, "equipment_id": 1}
        )
    ]
    truck_ids = _unique(_clean(row.get("id")) for row in transport_trucks)

    incident_binding_ids = await _binding_ids(db, "incident")
    daily_report_binding_ids = await _binding_ids(db, "daily_report")
    equipment_binding_ids = await _binding_ids(db, "equipment_inspection")

    checks: List[Dict[str, Any]] = []

    assignment_rows = [
        row async for row in db.project_team_assignments.find(
            {"active": True},
            {"_id": 0, "id": 1, "project_number": 1, "email": 1, "employee_id": 1},
        )
    ] if "project_team_assignments" in await db.list_collection_names() else []
    assignment_examples: List[Dict[str, Any]] = []
    orphan_project = orphan_email = orphan_employee = 0
    for row in assignment_rows:
        pn = _clean(row.get("project_number"))
        email = _clean(row.get("email")).lower()
        employee_id = _clean(row.get("employee_id"))
        if pn and pn not in project_numbers:
            orphan_project += 1
            if len(assignment_examples) < 5:
                assignment_examples.append({"id": row.get("id"), "project_number": pn})
        if email and email not in employee_emails and email not in user_directory_emails:
            orphan_email += 1
            if len(assignment_examples) < 5:
                assignment_examples.append({"id": row.get("id"), "email": email})
        if employee_id and employee_id not in employee_ids and employee_id not in employee_codes:
            orphan_employee += 1
            if len(assignment_examples) < 5:
                assignment_examples.append({"id": row.get("id"), "employee_id": employee_id})
    assignment_blockers = orphan_project + orphan_email + orphan_employee
    checks.append(
        _check(
            check_id="project_team_assignment_authority",
            label="Project assignment authority",
            status="green" if assignment_blockers == 0 else "red",
            summary=(
                "Active project-team assignments resolve to governed project and employee authorities."
                if assignment_blockers == 0
                else f"{assignment_blockers} active project-team assignment link(s) drift away from jobs_master or employees."
            ),
            canonical_entity="employees.id + jobs_master.project_number",
            source_authority="project_team_assignments.active roster rows",
            downstream_consumers=["team_snapshot", "ownership_lifecycle", "pm_routing"],
            counts={
                "active_rows": len(assignment_rows),
                "orphan_project": orphan_project,
                "orphan_email": orphan_email,
                "orphan_employee_id": orphan_employee,
            },
            sample_rows=assignment_examples,
        )
    )

    meeting_rows = await _list_visible(db, "meetings", {"_id": 0, "id": 1, "attendees": 1})
    meeting_examples: List[Dict[str, Any]] = []
    employee_attendees = employee_id_orphan = manual_review = masci_name_only = 0
    for row in meeting_rows:
        for attendee in row.get("attendees") or []:
            employee_id = _clean(attendee.get("employee_id"))
            if _clean(attendee.get("attendee_type")) == "employee":
                employee_attendees += 1
            if employee_id and employee_id not in employee_ids and employee_id not in employee_codes:
                employee_id_orphan += 1
                if len(meeting_examples) < 5:
                    meeting_examples.append({"meeting_id": row.get("id"), "employee_id": employee_id, "name": attendee.get("name")})
            if _clean(attendee.get("review_status")) == "needs_review":
                manual_review += 1
            if not employee_id and _clean(attendee.get("company")).lower() == "masci":
                masci_name_only += 1
                if len(meeting_examples) < 5:
                    meeting_examples.append({"meeting_id": row.get("id"), "name": attendee.get("name"), "issue": "masci_name_only"})
    meeting_blockers = employee_id_orphan + masci_name_only
    checks.append(
        _check(
            check_id="meeting_attendee_identity_normalization",
            label="Safety meeting attendee normalization",
            status="green" if meeting_blockers == 0 and manual_review == 0 else ("yellow" if meeting_blockers == 0 else "red"),
            summary=(
                "Safety meeting attendees are canonically bound to employees or explicitly dispositioned for review."
                if meeting_blockers == 0 and manual_review == 0
                else f"{meeting_blockers} attendee row(s) still rely on MASCI name-only linkage and {manual_review} attendee row(s) still need review."
            ),
            canonical_entity="employees.id",
            source_authority="meetings.attendees[] submit-time normalization",
            downstream_consumers=["meeting history", "safety attendance proof", "employee profile evidence"],
            counts={
                "visible_meetings": len(meeting_rows),
                "employee_attendees": employee_attendees,
                "employee_id_orphan": employee_id_orphan,
                "masci_name_only": masci_name_only,
                "needs_review": manual_review,
            },
            sample_rows=meeting_examples,
        )
    )

    incident_rows = await _list_visible(
        db,
        "incidents",
        {"_id": 0, "id": 1, "project_number": 1, "reported_by": 1, "reported_by_employee_id": 1, "employee_master_id": 1},
    )
    incident_examples: List[Dict[str, Any]] = []
    incident_orphan_project = incident_name_only = incident_unreachable = 0
    for row in incident_rows:
        pn = _clean(row.get("project_number"))
        if pn and pn not in project_numbers:
            incident_orphan_project += 1
            if len(incident_examples) < 5:
                incident_examples.append({"id": row.get("id"), "project_number": pn, "issue": "orphan_project"})
        has_employee = any(
            _clean(row.get(key)) in employee_ids or _clean(row.get(key)) in employee_codes
            for key in ("reported_by_employee_id", "employee_master_id")
        )
        if _clean(row.get("reported_by")) and not _clean(row.get("reported_by_employee_id")):
            incident_name_only += 1
        if not has_employee and _clean(row.get("id")) not in incident_binding_ids:
            incident_unreachable += 1
            if len(incident_examples) < 5:
                incident_examples.append({"id": row.get("id"), "reported_by": row.get("reported_by"), "issue": "history_unreachable"})
    incident_blockers = incident_orphan_project + incident_unreachable
    checks.append(
        _check(
            check_id="incident_project_and_submitter_lineage",
            label="Incident project + submitter lineage",
            status="green" if incident_blockers == 0 else "red",
            summary=(
                "Incident rows resolve to governed projects and at least one canonical employee/history path."
                if incident_blockers == 0
                else f"{incident_orphan_project} visible incident(s) point at non-canonical project numbers and {incident_unreachable} incident row(s) still miss canonical employee/history reachability."
            ),
            canonical_entity="jobs_master.project_number + employees.id",
            source_authority="incidents + field_submitter_bindings",
            downstream_consumers=["master_history employee profile", "incident lifecycle", "safety evidence exports"],
            counts={
                "visible_rows": len(incident_rows),
                "orphan_project": incident_orphan_project,
                "reported_by_name_only": incident_name_only,
                "history_reachable_via_binding": len(incident_binding_ids),
                "history_unreachable_rows": incident_unreachable,
            },
            sample_rows=incident_examples,
        )
    )

    daily_report_rows = await _list_visible(
        db,
        "daily_reports",
        {"_id": 0, "id": 1, "project_number": 1, "prepared_by": 1, "prepared_by_employee_id": 1, "masci_crews": 1},
    )
    daily_examples: List[Dict[str, Any]] = []
    daily_orphan_project = daily_name_only = daily_unreachable = crew_name_only = 0
    for row in daily_report_rows:
        pn = _clean(row.get("project_number"))
        if pn and pn not in project_numbers:
            daily_orphan_project += 1
            if len(daily_examples) < 5:
                daily_examples.append({"id": row.get("id"), "project_number": pn, "issue": "orphan_project"})
        if _clean(row.get("prepared_by")) and not _clean(row.get("prepared_by_employee_id")):
            daily_name_only += 1
        if not _clean(row.get("prepared_by_employee_id")) and _clean(row.get("id")) not in daily_report_binding_ids:
            daily_unreachable += 1
            if len(daily_examples) < 5:
                daily_examples.append({"id": row.get("id"), "prepared_by": row.get("prepared_by"), "issue": "history_unreachable"})
        for crew in row.get("masci_crews") or []:
            if isinstance(crew, dict) and _clean(crew.get("foreman")) and not _clean(crew.get("employee_id")):
                crew_name_only += 1
    daily_blockers = daily_orphan_project + daily_unreachable
    checks.append(
        _check(
            check_id="daily_report_project_and_submitter_lineage",
            label="Daily report project + submitter lineage",
            status="green" if daily_blockers == 0 else "red",
            summary=(
                "Daily reports resolve to governed projects and canonical submitter history."
                if daily_blockers == 0
                else f"{daily_orphan_project} visible daily report(s) point at non-canonical project numbers and {daily_unreachable} report row(s) still miss canonical submitter history linkage."
            ),
            canonical_entity="jobs_master.project_number + employees.id",
            source_authority="daily_reports + field_submitter_bindings",
            downstream_consumers=["master_history employee profile", "daily report evidence", "project rollups"],
            counts={
                "visible_rows": len(daily_report_rows),
                "orphan_project": daily_orphan_project,
                "prepared_by_name_only": daily_name_only,
                "crew_name_only_rows": crew_name_only,
                "history_reachable_via_binding": len(daily_report_binding_ids),
                "history_unreachable_rows": daily_unreachable,
            },
            sample_rows=daily_examples,
        )
    )

    equipment_rows = await _list_visible(
        db,
        "equipment_inspections",
        {"_id": 0, "id": 1, "project_number": 1, "equipment_master_id": 1, "equipment_unit": 1, "operator_name": 1, "operator_employee_id": 1},
    )
    equipment_examples: List[Dict[str, Any]] = []
    equipment_orphan_project = equipment_orphan_master = equipment_backfillable_master = operator_name_only = operator_unreachable = 0
    for row in equipment_rows:
        pn = _clean(row.get("project_number"))
        eq_id = _clean(row.get("equipment_master_id"))
        unit = _clean(row.get("equipment_unit")).lower()
        if pn and pn not in project_numbers:
            equipment_orphan_project += 1
            if len(equipment_examples) < 5:
                equipment_examples.append({"id": row.get("id"), "project_number": pn, "issue": "orphan_project"})
        if eq_id and eq_id not in equipment_ids:
            equipment_orphan_master += 1
            if len(equipment_examples) < 5:
                equipment_examples.append({"id": row.get("id"), "equipment_master_id": eq_id, "issue": "orphan_equipment"})
        if not eq_id and unit and unit in equipment_units:
            equipment_backfillable_master += 1
            if len(equipment_examples) < 5:
                equipment_examples.append({"id": row.get("id"), "equipment_unit": row.get("equipment_unit"), "issue": "missing_equipment_master_id"})
        if _clean(row.get("operator_name")) and not _clean(row.get("operator_employee_id")):
            operator_name_only += 1
        if not _clean(row.get("operator_employee_id")) and _clean(row.get("id")) not in equipment_binding_ids:
            operator_unreachable += 1
    equipment_blockers = equipment_orphan_project + equipment_orphan_master + equipment_backfillable_master + operator_unreachable
    checks.append(
        _check(
            check_id="equipment_preop_asset_and_operator_lineage",
            label="Equipment inspection asset + operator lineage",
            status="green" if equipment_blockers == 0 else "red",
            summary=(
                "Equipment inspections resolve to governed assets, projects, and operator history."
                if equipment_blockers == 0
                else f"{equipment_backfillable_master + equipment_orphan_master} equipment inspection row(s) still miss canonical asset linkage and {operator_unreachable} row(s) still miss operator history linkage."
            ),
            canonical_entity="equipment_master.id + jobs_master.project_number + employees.id",
            source_authority="equipment_inspections + field_submitter_bindings",
            downstream_consumers=["master_history equipment profile", "master_history employee profile", "shop + dispatch visibility"],
            counts={
                "visible_rows": len(equipment_rows),
                "orphan_project": equipment_orphan_project,
                "orphan_equipment_master_id": equipment_orphan_master,
                "missing_equipment_master_with_unit_match": equipment_backfillable_master,
                "operator_name_only": operator_name_only,
                "operator_history_unreachable_rows": operator_unreachable,
            },
            sample_rows=equipment_examples,
        )
    )

    dispatch_rows = await _list_visible(
        db,
        "dispatch_assignments",
        {"_id": 0, "id": 1, "project_number": 1, "truck_id": 1, "driver_id": 1, "equipment_id": 1, "current_state": 1},
    )
    dispatch_examples: List[Dict[str, Any]] = []
    dispatch_orphan_project = dispatch_orphan_driver = dispatch_orphan_truck = dispatch_orphan_equipment = dispatch_unscoped_active = 0
    for row in dispatch_rows:
        pn = _clean(row.get("project_number"))
        driver_id = _clean(row.get("driver_id"))
        truck_id = _clean(row.get("truck_id"))
        equipment_id = _clean(row.get("equipment_id"))
        current_state = _clean(row.get("current_state")).upper()
        if pn and pn not in project_numbers:
            dispatch_orphan_project += 1
            if len(dispatch_examples) < 5:
                dispatch_examples.append({"id": row.get("id"), "project_number": pn, "issue": "orphan_project"})
        if driver_id and driver_id not in driver_ids:
            dispatch_orphan_driver += 1
            if len(dispatch_examples) < 5:
                dispatch_examples.append({"id": row.get("id"), "driver_id": driver_id, "issue": "orphan_driver"})
        if truck_id and truck_id not in truck_ids:
            dispatch_orphan_truck += 1
            if len(dispatch_examples) < 5:
                dispatch_examples.append({"id": row.get("id"), "truck_id": truck_id, "issue": "orphan_truck"})
        if equipment_id and equipment_id not in equipment_ids:
            dispatch_orphan_equipment += 1
            if len(dispatch_examples) < 5:
                dispatch_examples.append({"id": row.get("id"), "equipment_id": equipment_id, "issue": "orphan_equipment"})
        if current_state in {"ASSIGNED", "EN_ROUTE", "IN_TRANSIT"} and not pn:
            dispatch_unscoped_active += 1
    dispatch_blockers = dispatch_orphan_project + dispatch_orphan_driver + dispatch_orphan_truck + dispatch_orphan_equipment + dispatch_unscoped_active
    checks.append(
        _check(
            check_id="dispatch_driver_truck_project_linkage",
            label="Dispatch driver/truck/project linkage",
            status="green" if dispatch_blockers == 0 else "red",
            summary=(
                "Dispatch assignments resolve to governed driver, truck, equipment, and project identifiers."
                if dispatch_blockers == 0
                else f"{dispatch_orphan_truck} dispatch row(s) still point at non-canonical truck IDs, {dispatch_orphan_driver} still point at non-canonical driver IDs, and {dispatch_unscoped_active} active assignment(s) still lack project scope."
            ),
            canonical_entity="transport_persons.id + transport_trucks.id + jobs_master.project_number + equipment_master.id",
            source_authority="dispatch_assignments",
            downstream_consumers=["pm_command_center", "dispatch command center", "driver profile", "equipment history"],
            counts={
                "visible_rows": len(dispatch_rows),
                "orphan_project": dispatch_orphan_project,
                "orphan_driver": dispatch_orphan_driver,
                "orphan_truck": dispatch_orphan_truck,
                "orphan_equipment": dispatch_orphan_equipment,
                "active_without_project": dispatch_unscoped_active,
            },
            sample_rows=dispatch_examples,
        )
    )

    duplicate_transport_employee = sum(1 for employee_id in person_employee_ids if person_employee_ids.count(employee_id) > 1)
    transport_orphan_employee = sum(1 for employee_id in person_employee_ids if employee_id not in employee_ids and employee_id not in employee_codes)
    checks.append(
        _check(
            check_id="transport_employee_projection_authority",
            label="Transportation employee projection authority",
            status="green" if duplicate_transport_employee == 0 and transport_orphan_employee == 0 else "red",
            summary=(
                "MASCI driver projections remain one-to-one with canonical employees."
                if duplicate_transport_employee == 0 and transport_orphan_employee == 0
                else f"Transportation has {duplicate_transport_employee} duplicate employee projection(s) and {transport_orphan_employee} orphan employee projection(s)."
            ),
            canonical_entity="employees.id / employees.employee_id",
            source_authority="transport_persons(kind=masci_employee)",
            downstream_consumers=["transportation dashboard", "driver profile", "dispatch gate"],
            counts={
                "active_transport_people": len(transport_people),
                "masci_employee_projections": len(person_employee_ids),
                "duplicate_employee_projection": duplicate_transport_employee,
                "orphan_employee_projection": transport_orphan_employee,
            },
        )
    )

    blocking = [row for row in checks if row.get("status") == "red"]
    return {
        "generated_at": _now_iso(),
        "overall_status": "green" if not blocking else "red",
        "release_gate_blocked": bool(blocking),
        "blocking_findings": [
            {"id": row.get("id"), "reason": row.get("summary")} for row in blocking
        ],
        "checks": checks,
    }


__all__ = ["scan_cross_entity_integrity"]