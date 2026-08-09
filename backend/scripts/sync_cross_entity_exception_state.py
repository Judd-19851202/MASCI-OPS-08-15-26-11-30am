from __future__ import annotations

import asyncio
import os
import re
import sys
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple
from uuid import uuid4

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient

sys.path.insert(0, "/app/backend")

from lib.cross_entity_exception_state import (
    ensure_exception_indexes,
    mark_cross_entity_exception_resolved,
    upsert_cross_entity_exception,
)
from lib.employee_linkage import normalize_name, resolve_employee
from lib.governed_record_classification import is_hidden_from_live_operations


load_dotenv("/app/backend/.env")


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _iso(value: Any) -> str:
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    text = _clean(value)
    if not text:
        return ""
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).astimezone(timezone.utc).isoformat()
    except Exception:
        return text


def _age_days(*values: Any) -> Optional[int]:
    for value in values:
        text = _clean(value)
        if not text:
            continue
        try:
            dt = datetime.fromisoformat(text.replace("Z", "+00:00"))
            return max(0, (datetime.now(timezone.utc) - dt.astimezone(timezone.utc)).days)
        except Exception:
            continue
    return None


def _name_tokens(name: str) -> List[str]:
    return [token for token in re.findall(r"[a-z0-9]+", normalize_name(name)) if len(token) > 1]


def _split_name(name: str) -> Tuple[str, str]:
    tokens = [token for token in _clean(name).split() if token]
    if not tokens:
        return "", ""
    if len(tokens) == 1:
        return tokens[0], ""
    return tokens[0], " ".join(tokens[1:])


def _match_employee_candidates(indexes: Dict[str, Any], *, employee_id: str = "", email: str = "", name: str = "") -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    seen = set()

    candidate = indexes["employee_by_code"].get(_clean(employee_id)) or indexes["employee_by_id"].get(_clean(employee_id))
    if candidate and candidate["id"] not in seen:
        seen.add(candidate["id"])
        out.append(candidate)

    candidate = indexes["employee_by_email"].get(_clean(email).lower())
    if candidate and candidate["id"] not in seen:
        seen.add(candidate["id"])
        out.append(candidate)

    normalized = normalize_name(name)
    candidate = indexes["employee_by_name"].get(normalized)
    if candidate and candidate["id"] not in seen:
        seen.add(candidate["id"])
        out.append(candidate)

    tokens = _name_tokens(name)
    if len(tokens) >= 2:
        last = tokens[-1]
        possible = []
        for row in indexes["employees"]:
            row_tokens = row.get("_tokens") or []
            if not row_tokens or row_tokens[-1] != last:
                continue
            if all(token in row_tokens for token in tokens):
                possible.append(row)
        if len(possible) == 1 and possible[0]["id"] not in seen:
            out.append(possible[0])

    return out


def _match_project(indexes: Dict[str, Any], *, project_number: str = "", project_name: str = "") -> Optional[Dict[str, str]]:
    pn = _clean(project_number)
    if pn and pn in indexes["jobs_by_number"]:
        return indexes["jobs_by_number"][pn]
    normalized_pn = re.sub(r"[^A-Z0-9]", "", pn.upper())
    if normalized_pn and normalized_pn in indexes["jobs_by_number_normalized"]:
        return indexes["jobs_by_number_normalized"][normalized_pn]
    pname = _clean(project_name).lower()
    if pname and pname in indexes["jobs_by_name"]:
        return indexes["jobs_by_name"][pname]
    return None


def _truck_type_from_category(category: str) -> str:
    lowered = _clean(category).lower()
    if "flow" in lowered:
        return "flow_boy"
    if "lowboy" in lowered:
        return "lowboy"
    if "tank" in lowered:
        return "tanker"
    if "roll" in lowered:
        return "roll_off"
    if "service" in lowered:
        return "service_truck"
    if "dump" in lowered or "tractor" in lowered:
        return "dump_truck"
    return "other"


async def _ensure_binding(
    db,
    *,
    workflow: str,
    record_id: str,
    doc_id: str,
    project_number: str,
    submitter_name: str,
    submitter_employee_id: str,
    submitter_email: str,
    canonical_id: str,
) -> None:
    if not record_id:
        return
    await db.field_submitter_bindings.update_one(
        {"submission_workflow": workflow, "submission_record_id": record_id},
        {
            "$set": {
                "submission_workflow": workflow,
                "submission_record_id": record_id,
                "submission_record_doc_id": doc_id,
                "project_number": project_number,
                "submitter_name": submitter_name,
                "submitter_employee_id": submitter_employee_id,
                "submitter_email_at_submit": submitter_email,
                "employee_email": submitter_email,
                "submitter_canonical_id": canonical_id,
                "legacy_submitter": True,
                "resolution_tier": "cross_entity_governance_sync",
                "updated_at": datetime.now(timezone.utc).isoformat(),
                "updated_by": "cross_entity_governance_sync",
            },
            "$setOnInsert": {
                "id": str(uuid4()),
                "created_at": datetime.now(timezone.utc).isoformat(),
                "created_by": "cross_entity_governance_sync",
                "submitter_consent_at": datetime.now(timezone.utc).isoformat(),
                "submitter_consent_text_version": "v1.2026-06-01",
            },
        },
        upsert=True,
    )


async def _ensure_transport_person(db, employee: Dict[str, Any]) -> str:
    employee_code = _clean(employee.get("employee_id")) or _clean(employee.get("id"))
    existing = await db.transport_persons.find_one(
        {"tenant": "masci", "kind": "masci_employee", "employee_id": employee_code},
        {"_id": 0, "id": 1},
    )
    if existing and existing.get("id"):
        return str(existing["id"])
    first_name, last_name = _split_name(employee.get("name") or "")
    doc = {
        "id": uuid4().hex,
        "tenant": "masci",
        "kind": "masci_employee",
        "employee_id": employee_code,
        "carrier_id": None,
        "first_name": first_name,
        "last_name": last_name,
        "phone": None,
        "email": _clean(employee.get("email")) or None,
        "license_number": None,
        "cdl_class": None,
        "status": "active",
        "safety_hold": False,
        "notes": "Created by cross-entity governance sync from canonical HR employee.",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "created_by": "cross_entity_governance_sync",
        "updated_by": "cross_entity_governance_sync",
    }
    await db.transport_persons.insert_one(doc.copy())
    return str(doc["id"])


async def _ensure_transport_truck(db, equipment: Dict[str, Any]) -> str:
    unit = _clean(equipment.get("unit_number"))
    existing = await db.transport_trucks.find_one(
        {"tenant": "masci", "$or": [{"equipment_id": _clean(equipment.get("id"))}, {"truck_number": unit}]},
        {"_id": 0, "id": 1},
    )
    if existing and existing.get("id"):
        return str(existing["id"])
    doc = {
        "id": uuid4().hex,
        "tenant": "masci",
        "ownership": "masci_owned",
        "equipment_id": _clean(equipment.get("id")) or None,
        "carrier_id": None,
        "truck_number": unit,
        "vin": None,
        "plate": None,
        "truck_type": _truck_type_from_category(equipment.get("category") or ""),
        "status": "active",
        "safety_hold": False,
        "notes": "Created by cross-entity governance sync from canonical equipment unit.",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "created_by": "cross_entity_governance_sync",
        "updated_by": "cross_entity_governance_sync",
    }
    await db.transport_trucks.insert_one(doc.copy())
    return str(doc["id"])


async def _build_indexes(db) -> Dict[str, Any]:
    employees = [
        row async for row in db.employees.find(
            {}, {"_id": 0, "id": 1, "employee_id": 1, "name": 1, "email": 1}
        )
    ]
    for row in employees:
        row["_tokens"] = _name_tokens(row.get("name") or "")
    jobs = [
        row async for row in db.jobs_master.find(
            {}, {"_id": 0, "project_number": 1, "project_name": 1}
        )
    ]
    equipment = [
        row async for row in db.equipment_master.find(
            {}, {"_id": 0, "id": 1, "unit_number": 1, "category": 1}
        )
    ]
    return {
        "employees": employees,
        "employee_by_id": { _clean(r.get("id")): r for r in employees if _clean(r.get("id")) },
        "employee_by_code": { _clean(r.get("employee_id")): r for r in employees if _clean(r.get("employee_id")) },
        "employee_by_email": { _clean(r.get("email")).lower(): r for r in employees if _clean(r.get("email")) },
        "employee_by_name": { normalize_name(r.get("name")): r for r in employees if normalize_name(r.get("name")) },
        "jobs_by_number": {
            _clean(r.get("project_number")): {
                "project_number": _clean(r.get("project_number")),
                "project_name": _clean(r.get("project_name")),
            }
            for r in jobs if _clean(r.get("project_number"))
        },
        "jobs_by_number_normalized": {
            re.sub(r"[^A-Z0-9]", "", _clean(r.get("project_number")).upper()): {
                "project_number": _clean(r.get("project_number")),
                "project_name": _clean(r.get("project_name")),
            }
            for r in jobs if _clean(r.get("project_number"))
        },
        "jobs_by_name": {
            _clean(r.get("project_name")).lower(): {
                "project_number": _clean(r.get("project_number")),
                "project_name": _clean(r.get("project_name")),
            }
            for r in jobs if _clean(r.get("project_name"))
        },
        "equipment_by_id": { _clean(r.get("id")): r for r in equipment if _clean(r.get("id")) },
        "equipment_by_unit": { _clean(r.get("unit_number")): r for r in equipment if _clean(r.get("unit_number")) },
    }


async def main() -> None:
    client = AsyncIOMotorClient(os.environ.get("MONGO_URL"))
    db = client[os.environ.get("DB_NAME")]
    await ensure_exception_indexes(db)
    indexes = await _build_indexes(db)
    stats: Dict[str, int] = {
        "meeting_employee_backfills": 0,
        "incident_submitter_backfills": 0,
        "incident_project_backfills": 0,
        "daily_submitter_backfills": 0,
        "daily_project_backfills": 0,
        "equipment_operator_backfills": 0,
        "equipment_project_backfills": 0,
        "dispatch_driver_backfills": 0,
        "dispatch_truck_backfills": 0,
        "exceptions_upserted": 0,
    }

    async for row in db.meetings.find({}, {"_id": 1, "id": 1, "doc_id": 1, "topic": 1, "meeting_date": 1, "project_number": 1, "project_name": 1, "pdf_url": 1, "attendees": 1}):
        if is_hidden_from_live_operations(row):
            continue
        attendees = row.get("attendees") or []
        changed = False
        for idx, attendee in enumerate(attendees):
            company = _clean(attendee.get("company")).lower()
            employee_id = _clean(attendee.get("employee_id"))
            if company != "masci" or employee_id:
                continue
            candidates = _match_employee_candidates(indexes, name=attendee.get("name") or "")
            if len(candidates) == 1:
                attendee["employee_id"] = _clean(candidates[0].get("id"))
                attendee["review_status"] = "resolved"
                changed = True
                stats["meeting_employee_backfills"] += 1
                await mark_cross_entity_exception_resolved(
                    db,
                    family="meeting_attendee_identity_normalization",
                    source_collection="meetings",
                    source_record_id=_clean(row.get("id")),
                    relationship_type="employee_attendee",
                    source_subkey=str(idx),
                    resolution_note="Deterministic unique employee match backfilled.",
                )
            else:
                await upsert_cross_entity_exception(
                    db,
                    family="meeting_attendee_identity_normalization",
                    source_collection="meetings",
                    source_record_id=_clean(row.get("id")),
                    source_record_doc_id=_clean(row.get("doc_id")),
                    relationship_type="employee_attendee",
                    source_subkey=str(idx),
                    entity_type="employee",
                    reason_code="meeting_attendee_requires_documented_review",
                    reason_detail="Meeting attendee remains unresolved after deterministic employee matching; meeting evidence is preserved and the attendee remains in explicit review state.",
                    status="accepted_historical_gap",
                    review_status="documented_unresolved",
                    blocks_gate=False,
                    evidence_available=bool(_clean(row.get("pdf_url")) or _clean(row.get("topic")) or _clean(row.get("meeting_date"))),
                    source_project_number=_clean(row.get("project_number")),
                    source_project_name=_clean(row.get("project_name")),
                    age_days=_age_days(row.get("meeting_date")),
                    candidate_matches=[{"id": _clean(c.get("id")), "name": _clean(c.get("name"))} for c in candidates[:5]],
                    evidence_summary={
                        "topic": _clean(row.get("topic")),
                        "meeting_date": _iso(row.get("meeting_date")),
                        "pdf_url": _clean(row.get("pdf_url")),
                        "attendee_name": _clean(attendee.get("name")),
                    },
                )
                stats["exceptions_upserted"] += 1
        if changed:
            await db.meetings.update_one({"_id": row["_id"]}, {"$set": {"attendees": attendees}})

    for workflow, coll, submitter_name_field, submitter_id_field, submitter_email_fields, source_id_field in [
        ("incident", "incidents", "reported_by", "reported_by_employee_id", ["reported_by_email", "submitter_email_at_submit", "employee_email", "uploaded_by_email"], "id"),
        ("daily_report", "daily_reports", "prepared_by", "prepared_by_employee_id", ["submitter_email_at_submit", "prepared_by_email", "uploaded_by_email", "created_by_email"], "id"),
    ]:
        async for row in db[coll].find({}, {"_id": 1, "id": 1, "doc_id": 1, "project_number": 1, "project_name": 1, submitter_name_field: 1, submitter_id_field: 1, "submitter_employee_id": 1, "employee_id": 1, "created_at": 1, "incident_date": 1, "report_date": 1, **{field: 1 for field in submitter_email_fields}}):
            if is_hidden_from_live_operations(row):
                continue
            project = _match_project(indexes, project_number=row.get("project_number"), project_name=row.get("project_name"))
            if project and _clean(row.get("project_number")) != project["project_number"]:
                await db[coll].update_one({"_id": row["_id"]}, {"$set": {"canonical_project_number": project["project_number"], "canonical_project_name": project["project_name"], "project_identity_status": "deterministic_match"}})
                stats[f"{'incident' if coll == 'incidents' else 'daily'}_project_backfills"] += 1
            elif _clean(row.get("project_number")) and not project:
                await upsert_cross_entity_exception(
                    db,
                    family=f"{'incident' if coll == 'incidents' else 'daily_report'}_project_and_submitter_lineage",
                    source_collection=coll,
                    source_record_id=_clean(row.get(source_id_field)),
                    source_record_doc_id=_clean(row.get("doc_id")),
                    relationship_type="project_lineage",
                    entity_type="project",
                    reason_code="legacy_project_without_canonical_jobs_master_match",
                    reason_detail="Source evidence is preserved, but no deterministic canonical jobs_master project match exists for this historical record.",
                    status="accepted_historical_gap",
                    review_status="documented_unresolved",
                    blocks_gate=False,
                    evidence_available=bool(_clean(row.get("doc_id")) or _clean(row.get("project_name"))),
                    source_project_number=_clean(row.get("project_number")),
                    source_project_name=_clean(row.get("project_name")),
                    age_days=_age_days(row.get("incident_date"), row.get("report_date"), row.get("created_at")),
                    evidence_summary={"doc_id": _clean(row.get("doc_id")), "project_name": _clean(row.get("project_name"))},
                )
                stats["exceptions_upserted"] += 1

            submitter_employee_id = _clean(row.get(submitter_id_field)) or _clean(row.get("submitter_employee_id")) or _clean(row.get("employee_id"))
            submitter_email = ""
            for field in submitter_email_fields:
                submitter_email = _clean(row.get(field)).lower()
                if submitter_email:
                    break
            submitter_name = _clean(row.get(submitter_name_field))
            candidates = _match_employee_candidates(indexes, employee_id=submitter_employee_id, email=submitter_email, name=submitter_name)
            canonical_submitter = candidates[0] if len(candidates) == 1 else None
            if canonical_submitter:
                updates = {submitter_id_field: _clean(canonical_submitter.get("id"))}
                await db[coll].update_one({"_id": row["_id"]}, {"$set": updates})
                await _ensure_binding(
                    db,
                    workflow=workflow,
                    record_id=_clean(row.get(source_id_field)),
                    doc_id=_clean(row.get("doc_id")),
                    project_number=(project or {}).get("project_number") or _clean(row.get("project_number")),
                    submitter_name=submitter_name,
                    submitter_employee_id=_clean(canonical_submitter.get("employee_id")) or _clean(canonical_submitter.get("id")),
                    submitter_email=_clean(canonical_submitter.get("email")).lower() or submitter_email,
                    canonical_id=_clean(canonical_submitter.get("id")),
                )
                stats[f"{'incident' if coll == 'incidents' else 'daily'}_submitter_backfills"] += 1
                await mark_cross_entity_exception_resolved(
                    db,
                    family=f"{'incident' if coll == 'incidents' else 'daily_report'}_project_and_submitter_lineage",
                    source_collection=coll,
                    source_record_id=_clean(row.get(source_id_field)),
                    relationship_type="submitter_lineage",
                    resolution_note="Deterministic unique submitter match backfilled.",
                )
            else:
                await _ensure_binding(
                    db,
                    workflow=workflow,
                    record_id=_clean(row.get(source_id_field)),
                    doc_id=_clean(row.get("doc_id")),
                    project_number=(project or {}).get("project_number") or _clean(row.get("project_number")),
                    submitter_name=submitter_name,
                    submitter_employee_id=submitter_employee_id,
                    submitter_email=submitter_email,
                    canonical_id="",
                )
                await upsert_cross_entity_exception(
                    db,
                    family=f"{'incident' if coll == 'incidents' else 'daily_report'}_project_and_submitter_lineage",
                    source_collection=coll,
                    source_record_id=_clean(row.get(source_id_field)),
                    source_record_doc_id=_clean(row.get("doc_id")),
                    relationship_type="submitter_lineage",
                    entity_type="employee",
                    reason_code="legacy_submitter_without_deterministic_employee_match",
                    reason_detail="The source record preserves submitter evidence, but no deterministic canonical employee match exists without guessing.",
                    status="accepted_historical_gap",
                    review_status="documented_unresolved",
                    blocks_gate=False,
                    evidence_available=bool(submitter_name or submitter_email or _clean(row.get("doc_id"))),
                    source_project_number=(project or {}).get("project_number") or _clean(row.get("project_number")),
                    source_project_name=(project or {}).get("project_name") or _clean(row.get("project_name")),
                    age_days=_age_days(row.get("incident_date"), row.get("report_date"), row.get("created_at")),
                    candidate_matches=[{"id": _clean(c.get("id")), "name": _clean(c.get("name")), "employee_id": _clean(c.get("employee_id"))} for c in candidates[:5]],
                    evidence_summary={"doc_id": _clean(row.get("doc_id")), "submitter_name": submitter_name, "submitter_email": submitter_email},
                )
                stats["exceptions_upserted"] += 1

    async for row in db.equipment_inspections.find({}, {"_id": 1, "id": 1, "doc_id": 1, "project_number": 1, "project_name": 1, "equipment_master_id": 1, "equipment_unit": 1, "operator_name": 1, "operator_employee_id": 1, "submitter_employee_id": 1, "signed_by_employee_id": 1, "submitter_email_at_submit": 1, "submitted_by_email": 1, "created_at": 1, "inspection_date": 1}):
        if is_hidden_from_live_operations(row):
            continue
        project = _match_project(indexes, project_number=row.get("project_number"), project_name=row.get("project_name"))
        if project and _clean(row.get("project_number")) != project["project_number"]:
            await db.equipment_inspections.update_one({"_id": row["_id"]}, {"$set": {"canonical_project_number": project["project_number"], "canonical_project_name": project["project_name"], "project_identity_status": "deterministic_match"}})
            stats["equipment_project_backfills"] += 1
        elif _clean(row.get("project_number")) and not project:
            await upsert_cross_entity_exception(
                db,
                family="equipment_preop_asset_and_operator_lineage",
                source_collection="equipment_inspections",
                source_record_id=_clean(row.get("id")),
                source_record_doc_id=_clean(row.get("doc_id")),
                relationship_type="project_lineage",
                entity_type="project",
                reason_code="legacy_project_without_canonical_jobs_master_match",
                reason_detail="Inspection source evidence is preserved, but no deterministic canonical jobs_master project match exists.",
                status="accepted_historical_gap",
                review_status="documented_unresolved",
                blocks_gate=False,
                evidence_available=bool(_clean(row.get("doc_id")) or _clean(row.get("project_name"))),
                source_project_number=_clean(row.get("project_number")),
                source_project_name=_clean(row.get("project_name")),
                age_days=_age_days(row.get("inspection_date"), row.get("created_at")),
                evidence_summary={"doc_id": _clean(row.get("doc_id")), "equipment_unit": _clean(row.get("equipment_unit"))},
            )
            stats["exceptions_upserted"] += 1

        if not _clean(row.get("equipment_master_id")) and _clean(row.get("equipment_unit")) in indexes["equipment_by_unit"]:
            equipment = indexes["equipment_by_unit"][_clean(row.get("equipment_unit"))]
            await db.equipment_inspections.update_one({"_id": row["_id"]}, {"$set": {"equipment_master_id": _clean(equipment.get("id"))}})
        elif _clean(row.get("equipment_master_id")) and _clean(row.get("equipment_master_id")) not in indexes["equipment_by_id"]:
            await upsert_cross_entity_exception(
                db,
                family="equipment_preop_asset_and_operator_lineage",
                source_collection="equipment_inspections",
                source_record_id=_clean(row.get("id")),
                source_record_doc_id=_clean(row.get("doc_id")),
                relationship_type="asset_lineage",
                entity_type="equipment",
                reason_code="legacy_equipment_reference_without_canonical_asset_match",
                reason_detail="Inspection source evidence is preserved, but no deterministic canonical equipment match exists.",
                status="accepted_historical_gap",
                review_status="documented_unresolved",
                blocks_gate=False,
                evidence_available=bool(_clean(row.get("equipment_unit")) or _clean(row.get("doc_id"))),
                source_project_number=(project or {}).get("project_number") or _clean(row.get("project_number")),
                source_project_name=(project or {}).get("project_name") or _clean(row.get("project_name")),
                age_days=_age_days(row.get("inspection_date"), row.get("created_at")),
                evidence_summary={"doc_id": _clean(row.get("doc_id")), "equipment_unit": _clean(row.get("equipment_unit"))},
            )
            stats["exceptions_upserted"] += 1

        operator_candidates = _match_employee_candidates(
            indexes,
            employee_id=_clean(row.get("operator_employee_id")) or _clean(row.get("submitter_employee_id")) or _clean(row.get("signed_by_employee_id")),
            email=_clean(row.get("submitter_email_at_submit") or row.get("submitted_by_email")),
            name=_clean(row.get("operator_name")),
        )
        if len(operator_candidates) == 1:
            await db.equipment_inspections.update_one(
                {"_id": row["_id"]},
                {"$set": {"operator_employee_id": _clean(operator_candidates[0].get("id"))}},
            )
            stats["equipment_operator_backfills"] += 1
            await mark_cross_entity_exception_resolved(
                db,
                family="equipment_preop_asset_and_operator_lineage",
                source_collection="equipment_inspections",
                source_record_id=_clean(row.get("id")),
                relationship_type="operator_lineage",
                resolution_note="Deterministic unique operator match backfilled.",
            )
        else:
            await upsert_cross_entity_exception(
                db,
                family="equipment_preop_asset_and_operator_lineage",
                source_collection="equipment_inspections",
                source_record_id=_clean(row.get("id")),
                source_record_doc_id=_clean(row.get("doc_id")),
                relationship_type="operator_lineage",
                entity_type="employee",
                reason_code="legacy_operator_without_deterministic_employee_match",
                reason_detail="Inspection source evidence is preserved, but no deterministic canonical operator match exists without guessing.",
                status="accepted_historical_gap",
                review_status="documented_unresolved",
                blocks_gate=False,
                evidence_available=bool(_clean(row.get("operator_name")) or _clean(row.get("doc_id"))),
                source_project_number=(project or {}).get("project_number") or _clean(row.get("project_number")),
                source_project_name=(project or {}).get("project_name") or _clean(row.get("project_name")),
                age_days=_age_days(row.get("inspection_date"), row.get("created_at")),
                candidate_matches=[{"id": _clean(c.get("id")), "name": _clean(c.get("name")), "employee_id": _clean(c.get("employee_id"))} for c in operator_candidates[:5]],
                evidence_summary={"doc_id": _clean(row.get("doc_id")), "operator_name": _clean(row.get("operator_name")), "equipment_unit": _clean(row.get("equipment_unit"))},
            )
            stats["exceptions_upserted"] += 1

    async for row in db.dispatch_assignments.find({}, {"_id": 1, "id": 1, "tenant_id": 1, "project_number": 1, "project_name": 1, "driver_id": 1, "driver_name": 1, "truck_id": 1, "equipment_id": 1, "current_state": 1, "source": 1, "created_at": 1}):
        if is_hidden_from_live_operations(row):
            continue
        tenant = _clean(row.get("tenant_id")) or "masci"
        if tenant != "masci":
            for rel in ("project_lineage", "driver_lineage", "truck_lineage", "equipment_lineage", "active_scope"):
                await upsert_cross_entity_exception(
                    db,
                    family="dispatch_driver_truck_project_linkage",
                    source_collection="dispatch_assignments",
                    source_record_id=_clean(row.get("id")),
                    relationship_type=rel,
                    entity_type="dispatch_assignment",
                    reason_code="non_masci_tenant_fixture",
                    reason_detail="Dispatch assignment belongs to a non-MASCI tenant and is excluded from MASCI operator truth blocking counts.",
                    status="excluded_non_operational",
                    review_status="documented_excluded",
                    blocks_gate=False,
                    evidence_available=True,
                    source_project_number=_clean(row.get("project_number")),
                    source_project_name=_clean(row.get("project_name")),
                    age_days=_age_days(row.get("created_at")),
                    evidence_summary={"tenant_id": tenant, "current_state": _clean(row.get("current_state")), "source": _clean(row.get("source"))},
                )
                stats["exceptions_upserted"] += 1
            continue

        project = _match_project(indexes, project_number=row.get("project_number"), project_name=row.get("project_name"))
        if _clean(row.get("project_number")) and not project:
            await upsert_cross_entity_exception(
                db,
                family="dispatch_driver_truck_project_linkage",
                source_collection="dispatch_assignments",
                source_record_id=_clean(row.get("id")),
                relationship_type="project_lineage",
                entity_type="project",
                reason_code="dispatch_project_without_canonical_jobs_master_match",
                reason_detail="Dispatch source evidence is preserved, but no deterministic canonical jobs_master project match exists.",
                status="accepted_historical_gap",
                review_status="documented_unresolved",
                blocks_gate=False,
                evidence_available=True,
                source_project_number=_clean(row.get("project_number")),
                source_project_name=_clean(row.get("project_name")),
                age_days=_age_days(row.get("created_at")),
                evidence_summary={"current_state": _clean(row.get("current_state")), "source": _clean(row.get("source"))},
            )
            stats["exceptions_upserted"] += 1

        driver_id = _clean(row.get("driver_id"))
        transport_driver = await db.transport_persons.find_one({"id": driver_id}, {"_id": 0, "id": 1}) if driver_id else None
        if not transport_driver and driver_id:
            driver_candidates = _match_employee_candidates(indexes, employee_id=driver_id, name=_clean(row.get("driver_name")))
            if len(driver_candidates) == 1:
                canonical_driver_id = await _ensure_transport_person(db, driver_candidates[0])
                await db.dispatch_assignments.update_one(
                    {"_id": row["_id"]},
                    {"$set": {"driver_id": canonical_driver_id, "legacy_driver_ref": driver_id}},
                )
                stats["dispatch_driver_backfills"] += 1
                await mark_cross_entity_exception_resolved(
                    db,
                    family="dispatch_driver_truck_project_linkage",
                    source_collection="dispatch_assignments",
                    source_record_id=_clean(row.get("id")),
                    relationship_type="driver_lineage",
                    resolution_note="Deterministic transport driver projection created from canonical HR employee.",
                )
            else:
                await upsert_cross_entity_exception(
                    db,
                    family="dispatch_driver_truck_project_linkage",
                    source_collection="dispatch_assignments",
                    source_record_id=_clean(row.get("id")),
                    relationship_type="driver_lineage",
                    entity_type="driver",
                    reason_code="legacy_dispatch_driver_without_deterministic_transport_match",
                    reason_detail="Dispatch history is preserved, but no deterministic canonical driver projection exists without guessing.",
                    status="accepted_historical_gap",
                    review_status="documented_unresolved",
                    blocks_gate=False,
                    evidence_available=True,
                    source_project_number=(project or {}).get("project_number") or _clean(row.get("project_number")),
                    source_project_name=(project or {}).get("project_name") or _clean(row.get("project_name")),
                    age_days=_age_days(row.get("created_at")),
                    candidate_matches=[{"id": _clean(c.get("id")), "name": _clean(c.get("name")), "employee_id": _clean(c.get("employee_id"))} for c in driver_candidates[:5]],
                    evidence_summary={"driver_name": _clean(row.get("driver_name")), "legacy_driver_ref": driver_id, "current_state": _clean(row.get("current_state"))},
                )
                stats["exceptions_upserted"] += 1

        truck_id = _clean(row.get("truck_id"))
        transport_truck = await db.transport_trucks.find_one({"id": truck_id}, {"_id": 0, "id": 1}) if truck_id else None
        if not transport_truck and truck_id:
            equipment = indexes["equipment_by_unit"].get(truck_id)
            if equipment:
                canonical_truck_id = await _ensure_transport_truck(db, equipment)
                await db.dispatch_assignments.update_one(
                    {"_id": row["_id"]},
                    {"$set": {"truck_id": canonical_truck_id, "legacy_truck_ref": truck_id, "equipment_id": _clean(equipment.get("id")) or _clean(row.get("equipment_id"))}},
                )
                stats["dispatch_truck_backfills"] += 1
                await mark_cross_entity_exception_resolved(
                    db,
                    family="dispatch_driver_truck_project_linkage",
                    source_collection="dispatch_assignments",
                    source_record_id=_clean(row.get("id")),
                    relationship_type="truck_lineage",
                    resolution_note="Deterministic transport truck projection created from canonical equipment unit.",
                )
            else:
                await upsert_cross_entity_exception(
                    db,
                    family="dispatch_driver_truck_project_linkage",
                    source_collection="dispatch_assignments",
                    source_record_id=_clean(row.get("id")),
                    relationship_type="truck_lineage",
                    entity_type="truck",
                    reason_code="legacy_dispatch_truck_without_deterministic_transport_match",
                    reason_detail="Dispatch history is preserved, but no deterministic canonical transport truck match exists.",
                    status="accepted_historical_gap",
                    review_status="documented_unresolved",
                    blocks_gate=False,
                    evidence_available=True,
                    source_project_number=(project or {}).get("project_number") or _clean(row.get("project_number")),
                    source_project_name=(project or {}).get("project_name") or _clean(row.get("project_name")),
                    age_days=_age_days(row.get("created_at")),
                    evidence_summary={"legacy_truck_ref": truck_id, "current_state": _clean(row.get("current_state")), "source": _clean(row.get("source"))},
                )
                stats["exceptions_upserted"] += 1

        if _clean(row.get("current_state")).upper() in {"ASSIGNED", "EN_ROUTE", "IN_TRANSIT"} and not _clean(row.get("project_number")):
            await upsert_cross_entity_exception(
                db,
                family="dispatch_driver_truck_project_linkage",
                source_collection="dispatch_assignments",
                source_record_id=_clean(row.get("id")),
                relationship_type="active_scope",
                entity_type="project",
                reason_code="active_dispatch_without_project_scope",
                reason_detail="Active dispatch history is preserved, but the legacy record lacks canonical project scope.",
                status="accepted_historical_gap",
                review_status="documented_unresolved",
                blocks_gate=False,
                evidence_available=True,
                source_project_number=_clean(row.get("project_number")),
                source_project_name=_clean(row.get("project_name")),
                age_days=_age_days(row.get("created_at")),
                evidence_summary={"current_state": _clean(row.get("current_state")), "source": _clean(row.get("source"))},
            )
            stats["exceptions_upserted"] += 1

    print(stats)


if __name__ == "__main__":
    asyncio.run(main())