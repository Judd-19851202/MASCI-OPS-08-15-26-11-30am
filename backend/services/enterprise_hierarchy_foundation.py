from __future__ import annotations

from collections import Counter, defaultdict
from copy import deepcopy
from datetime import datetime, timezone
import re
from typing import Any, Dict, Iterable, List, Optional, Tuple
from uuid import uuid4


COLLECTION_NODES = "enterprise_governance_organization"
COLLECTION_BINDINGS = "enterprise_governance_hierarchy_bindings"
COLLECTION_REVIEW = "enterprise_governance_hierarchy_review_queue"
COLLECTION_ASSIGNMENTS = "enterprise_governance_resource_assignments"
COLLECTION_AUDIT = "enterprise_governance_hierarchy_audit"
COLLECTION_RUNS = "enterprise_governance_hierarchy_runs"

NODE_TYPES = {
    "company",
    "division",
    "department",
    "region",
    "facility",
    "project",
    "contract",
    "phase",
    "work_package",
    "cost_code",
    "schedule_activity",
}

FACILITY_SUBTYPES = {"plant", "yard", "shop"}
RESOURCE_TYPES = {"employee", "crew", "equipment", "vendor_subcontractor", "material_line"}

VALID_PARENT_TYPES = {
    "company": set(),
    "division": {"company"},
    "department": {"company", "division"},
    "region": {"company", "division"},
    "facility": {"company", "division", "region"},
    "project": {"company", "division", "region", "facility"},
    "contract": {"project"},
    "phase": {"project", "contract"},
    "work_package": {"project", "phase"},
    "cost_code": {"project", "phase", "work_package"},
    "schedule_activity": {"project", "phase", "work_package", "cost_code"},
}

INHERITANCE_DEFAULTS = {
    "configuration": True,
    "permissions": True,
    "reporting_scope": True,
    "operating_standards": True,
    "localization_defaults": True,
    "notification_rules": True,
    "assignment_eligibility": True,
    "portfolio_visibility": True,
}

DEPARTMENT_SEED = [
    ("project_management", "Project Management"),
    ("field_operations", "Field Operations"),
    ("shop_operations", "Shop Operations"),
    ("safety", "Safety"),
    ("human_resources", "Human Resources"),
]


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_ts(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _slug(value: str) -> str:
    cleaned = re.sub(r"[^a-z0-9]+", "-", (value or "").strip().lower())
    cleaned = re.sub(r"-+", "-", cleaned).strip("-")
    return cleaned or "unlabeled"


def _compact(value: str) -> str:
    return re.sub(r"\s+", " ", (value or "").strip())


def _norm(value: str) -> str:
    return _slug(_compact(value))


def _code(value: str, fallback_prefix: str) -> str:
    token = re.sub(r"[^A-Z0-9]+", "-", (value or "").upper()).strip("-")
    return token[:80] or f"{fallback_prefix}-{uuid4().hex[:8].upper()}"


def _sanitize(value: Any) -> Any:
    if isinstance(value, dict):
        return {str(key): _sanitize(val) for key, val in value.items()}
    if isinstance(value, list):
        return [_sanitize(item) for item in value]
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    return str(value)


def _path_parts(parent: Optional[Dict[str, Any]], name: str) -> List[str]:
    base = list(parent.get("path") or []) if parent else []
    return [*base, name]


def _ancestor_ids(parent: Optional[Dict[str, Any]]) -> List[str]:
    base = list(parent.get("ancestor_ids") or []) if parent else []
    if parent:
        base.append(parent["id"])
    return base


def _node_doc(
    *,
    node_id: str,
    code: str,
    name: str,
    node_type: str,
    parent: Optional[Dict[str, Any]] = None,
    subtype: str = "",
    description: str = "",
    company_id: str = "masci",
    owner: str = "enterprise_governance",
    steward: str = "enterprise_governance",
    source: str = "wp18c1_seed",
    source_collection: str = "",
    source_record_id: str = "",
    external_source_identifier: str = "",
    confidence: str = "high",
    active: bool = True,
    archived: bool = False,
    effective_start: str = "",
    effective_end: str = "",
    display_order: int = 0,
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "id": node_id,
        "code": code,
        "name": name,
        "description": description,
        "type": node_type,
        "subtype": subtype or "",
        "parent_id": parent.get("id") if parent else None,
        "path": _path_parts(parent, name),
        "ancestor_ids": _ancestor_ids(parent),
        "ancestry_path": " / ".join(_path_parts(parent, name)),
        "company_scope": company_id,
        "effective_start": effective_start or _utcnow(),
        "effective_end": effective_end or None,
        "active_status": active,
        "archive_status": archived,
        "owner_steward": owner,
        "steward": steward,
        "source": source,
        "source_provenance": source,
        "source_collection": source_collection,
        "source_record_id": source_record_id,
        "external_source_identifier": external_source_identifier,
        "display_order": display_order,
        "version": 1,
        "metadata_extension": metadata or {},
        "inheritance": deepcopy(INHERITANCE_DEFAULTS),
        "created_at": _utcnow(),
        "updated_at": _utcnow(),
        "audit_metadata": {
            "created_by": owner,
            "updated_by": owner,
        },
        "confidence": confidence,
        "binding_counts": {},
    }


def _binding_doc(
    *,
    binding_id: str,
    record_type: str,
    source_collection: str,
    source_record_id: str,
    source_label: str,
    target_node_id: str,
    binding_kind: str,
    confidence: str = "high",
    status: str = "bound",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    now = _utcnow()
    return {
        "binding_id": binding_id,
        "record_type": record_type,
        "source_collection": source_collection,
        "source_record_id": source_record_id,
        "source_label": source_label,
        "target_node_id": target_node_id,
        "binding_kind": binding_kind,
        "status": status,
        "confidence": confidence,
        "metadata": metadata or {},
        "created_at": now,
        "updated_at": now,
        "audit_metadata": {"created_by": "wp18c1_backfill", "updated_by": "wp18c1_backfill"},
    }


async def _write_audit(db, action: str, actor: Dict[str, Any], before: Any, after: Any, reason: str, request_context: Optional[Dict[str, Any]] = None) -> None:
    row = {
        "audit_id": f"eh_audit_{uuid4().hex}",
        "action": action,
        "actor": actor,
        "before": before,
        "after": after,
        "reason": reason,
        "source": "wp18c1",
        "request_context": request_context or {},
        "timestamp": _utcnow(),
    }
    await db[COLLECTION_AUDIT].insert_one(row)


async def ensure_hierarchy_indexes(db) -> None:
    await db[COLLECTION_NODES].create_index("id", unique=True)
    await db[COLLECTION_NODES].create_index([("type", 1), ("archive_status", 1), ("display_order", 1), ("name", 1)])
    await db[COLLECTION_NODES].create_index([("parent_id", 1), ("archive_status", 1), ("display_order", 1)])
    await db[COLLECTION_BINDINGS].create_index("binding_id", unique=True)
    await db[COLLECTION_BINDINGS].create_index([("target_node_id", 1), ("status", 1), ("record_type", 1)])
    await db[COLLECTION_REVIEW].create_index("review_id", unique=True)
    await db[COLLECTION_REVIEW].create_index([("status", 1), ("priority", 1), ("created_at", -1)])
    await db[COLLECTION_ASSIGNMENTS].create_index("assignment_id", unique=True)
    await db[COLLECTION_ASSIGNMENTS].create_index([("assigned_node_id", 1), ("active_status", 1), ("resource_type", 1)])
    await db[COLLECTION_AUDIT].create_index([("timestamp", -1)])
    await db[COLLECTION_RUNS].create_index([("run_at", -1)])


async def _get_node(db, node_id: str) -> Optional[Dict[str, Any]]:
    return await db[COLLECTION_NODES].find_one({"id": node_id}, {"_id": 0})


async def _upsert_node(db, doc: Dict[str, Any]) -> Dict[str, Any]:
    doc = deepcopy(doc)
    created_at = doc.pop("created_at", None) or _utcnow()
    doc["updated_at"] = _utcnow()
    await db[COLLECTION_NODES].update_one({"id": doc["id"]}, {"$set": doc, "$setOnInsert": {"created_at": created_at}}, upsert=True)
    return await _get_node(db, doc["id"])


async def _ensure_seed_node(
    db,
    *,
    node_id: str,
    code: str,
    name: str,
    node_type: str,
    parent: Optional[Dict[str, Any]],
    description: str,
    source: str,
    display_order: int,
    metadata: Optional[Dict[str, Any]] = None,
    subtype: str = "",
) -> Dict[str, Any]:
    existing = await _get_node(db, node_id)
    if existing:
        updated = {**existing}
        updated.update({
            "name": name,
            "description": description,
            "type": node_type,
            "subtype": subtype or existing.get("subtype") or "",
            "parent_id": parent.get("id") if parent else None,
            "path": _path_parts(parent, name),
            "ancestor_ids": _ancestor_ids(parent),
            "ancestry_path": " / ".join(_path_parts(parent, name)),
            "display_order": display_order,
            "source": source,
            "source_provenance": source,
            "metadata_extension": {**(existing.get("metadata_extension") or {}), **(metadata or {})},
            "active_status": True,
            "archive_status": False,
        })
        return await _upsert_node(db, updated)
    doc = _node_doc(
        node_id=node_id,
        code=code,
        name=name,
        node_type=node_type,
        parent=parent,
        description=description,
        source=source,
        source_collection="enterprise_governance_registry",
        source_record_id=node_id,
        display_order=display_order,
        metadata=metadata,
        subtype=subtype,
    )
    return await _upsert_node(db, doc)


async def _record_review_item(
    db,
    *,
    source_collection: str,
    source_record_id: str,
    source_label: str,
    suggested_type: str,
    reason: str,
    confidence: str,
    candidate_parent_id: str = "",
    suggested_subtype: str = "",
    evidence: Optional[Dict[str, Any]] = None,
) -> None:
    review_id = f"review::{source_collection}::{source_record_id}::{suggested_type}::{suggested_subtype or 'none'}"
    now = _utcnow()
    row = {
        "review_id": review_id,
        "source_collection": source_collection,
        "source_record_id": source_record_id,
        "source_label": source_label,
        "suggested_type": suggested_type,
        "suggested_subtype": suggested_subtype,
        "candidate_parent_id": candidate_parent_id or None,
        "reason": reason,
        "confidence": confidence,
        "status": "review_required",
        "priority": "medium" if confidence == "medium" else "high",
        "evidence": _sanitize(evidence or {}),
        "created_at": now,
        "updated_at": now,
    }
    set_row = deepcopy(row)
    set_row.pop("created_at", None)
    await db[COLLECTION_REVIEW].update_one({"review_id": review_id}, {"$set": set_row, "$setOnInsert": {"created_at": now}}, upsert=True)


async def _upsert_binding(db, doc: Dict[str, Any]) -> None:
    row = deepcopy(doc)
    created_at = row.pop("created_at", None) or _utcnow()
    row["updated_at"] = _utcnow()
    await db[COLLECTION_BINDINGS].update_one({"binding_id": row["binding_id"]}, {"$set": row, "$setOnInsert": {"created_at": created_at}}, upsert=True)


async def _upsert_assignment(db, doc: Dict[str, Any]) -> None:
    row = deepcopy(doc)
    created_at = row.pop("created_at", None) or _utcnow()
    row["updated_at"] = _utcnow()
    await db[COLLECTION_ASSIGNMENTS].update_one({"assignment_id": row["assignment_id"]}, {"$set": row, "$setOnInsert": {"created_at": created_at}}, upsert=True)


async def _seed_core_hierarchy(db) -> Dict[str, Dict[str, Any]]:
    company = await _ensure_seed_node(
        db,
        node_id="company:masci",
        code="MASCI",
        name="MASCI",
        node_type="company",
        parent=None,
        description="Operating company root for the current MASCI hierarchy.",
        source="enterprise_governance_registry_seed",
        display_order=0,
        metadata={"root_scope": True},
    )
    division = await _ensure_seed_node(
        db,
        node_id="division:operations",
        code="OPERATIONS",
        name="Operations",
        node_type="division",
        parent=company,
        description="Primary operating division evidenced by the active operational portals and governance defaults.",
        source="enterprise_governance_registry_seed",
        display_order=10,
    )
    departments = {}
    for idx, (slug, label) in enumerate(DEPARTMENT_SEED, start=20):
        departments[slug] = await _ensure_seed_node(
            db,
            node_id=f"department:{slug}",
            code=_code(label, "DEPT"),
            name=label,
            node_type="department",
            parent=division,
            description=f"{label} operating department available in the current MASCI platform.",
            source="enterprise_governance_registry_seed",
            display_order=idx,
        )
    return {"company": company, "division": division, **departments}


async def _normalize_legacy_organization_rows(db) -> int:
    updated = 0
    async for row in db[COLLECTION_NODES].find({"type": {"$exists": False}, "kind": {"$exists": True}}, {"_id": 0}):
        updated += 1
        patch = {
            "type": row.get("kind"),
            "archive_status": True,
            "active_status": False,
            "code": row.get("code") or _code(row.get("name") or row.get("id") or "LEGACY", "LEGACY"),
            "description": row.get("description") or "Legacy governance seed preserved for audit history; superseded by the governed organization structure.",
            "ancestry_path": " / ".join(row.get("path") or [row.get("name") or row.get("id") or "Legacy"]),
            "ancestor_ids": row.get("ancestor_ids") or [],
            "company_scope": row.get("company_scope") or "masci",
            "effective_start": row.get("effective_start") or _utcnow(),
            "effective_end": row.get("effective_end") or None,
            "owner_steward": row.get("owner_steward") or "enterprise_governance",
            "steward": row.get("steward") or "enterprise_governance",
            "source": row.get("source") or "legacy_governance_seed",
            "source_provenance": row.get("source_provenance") or "legacy_governance_seed",
            "source_collection": row.get("source_collection") or "enterprise_governance_organization",
            "source_record_id": row.get("source_record_id") or row.get("id"),
            "external_source_identifier": row.get("external_source_identifier") or "",
            "display_order": row.get("display_order") or 9999,
            "version": row.get("version") or 1,
            "metadata_extension": {**(row.get("metadata_extension") or {}), "legacy_shadow": True},
            "inheritance": row.get("inheritance") or deepcopy(INHERITANCE_DEFAULTS),
            "updated_at": _utcnow(),
        }
        await db[COLLECTION_NODES].update_one({"id": row["id"]}, {"$set": patch})
    return updated


def _looks_like_ambiguous_facility(name: str) -> bool:
    label = (name or "").upper()
    return any(token in label for token in ["THEFT", "PREVIEW", "CERT", " AREA ", "SITE ", "JOB", "RT "])


async def _backfill_projects(db, division: Dict[str, Any]) -> Dict[str, int]:
    created = 0
    bound = 0
    async for row in db.jobs_master.find({}, {"_id": 0, "project_number": 1, "project_name": 1, "location": 1, "status": 1, "pm_email": 1}):
        project_number = _compact(row.get("project_number") or "")
        if not project_number:
            continue
        node_id = f"project:{project_number}"
        name = _compact(row.get("project_name") or project_number)
        existing = await _get_node(db, node_id)
        if not existing:
            created += 1
            doc = _node_doc(
                node_id=node_id,
                code=project_number,
                name=name,
                node_type="project",
                parent=division,
                description=_compact(row.get("location") or "Project location not yet governed."),
                source="jobs_master_backfill",
                source_collection="jobs_master",
                source_record_id=project_number,
                external_source_identifier=project_number,
                metadata={
                    "project_number": project_number,
                    "pm_email": row.get("pm_email") or "",
                    "status": row.get("status") or "",
                    "location": row.get("location") or "",
                },
                display_order=100,
            )
            await _upsert_node(db, doc)
        binding = _binding_doc(
            binding_id=f"binding::jobs_master::{project_number}",
            record_type="project",
            source_collection="jobs_master",
            source_record_id=project_number,
            source_label=name,
            target_node_id=node_id,
            binding_kind="project_identity",
            metadata={"project_number": project_number},
        )
        await _upsert_binding(db, binding)
        bound += 1
    return {"created": created, "bound": bound}


async def _backfill_facilities(db, company: Dict[str, Any]) -> Dict[str, int]:
    created = 0
    bound = 0
    reviewed = 0
    exact_nodes: Dict[Tuple[str, str], str] = {}

    async for loc in db.operational_locations.find({}, {"_id": 0, "name": 1, "location_type": 1, "project_number": 1, "status": 1, "geocode_status": 1}):
        name = _compact(loc.get("name") or "")
        loc_type = _compact(loc.get("location_type") or "")
        if not name or loc_type not in {"SHOP", "YARD", "PLANT"}:
            if name and loc_type == "JOB" and any(token in name.upper() for token in ["YARD", "SHOP", "PLANT"]):
                reviewed += 1
                await _record_review_item(
                    db,
                    source_collection="operational_locations",
                    source_record_id=f"{loc_type}:{name}",
                    source_label=name,
                    suggested_type="facility",
                    suggested_subtype="yard" if "YARD" in name.upper() else "shop" if "SHOP" in name.upper() else "plant",
                    reason="Current location record uses JOB type but reads like a facility reference.",
                    confidence="medium",
                    candidate_parent_id=company["id"],
                    evidence=loc,
                )
            continue
        subtype = loc_type.lower()
        if _looks_like_ambiguous_facility(name):
            reviewed += 1
            await _record_review_item(
                db,
                source_collection="operational_locations",
                source_record_id=f"{loc_type}:{name}",
                source_label=name,
                suggested_type="facility",
                suggested_subtype=subtype,
                reason="Facility-like reference requires manual confirmation before canonical binding.",
                confidence="medium",
                candidate_parent_id=company["id"],
                evidence=loc,
            )
            continue
        node_id = f"facility:{subtype}:{_norm(name)}"
        exact_nodes[(subtype, _norm(name))] = node_id
        if not await _get_node(db, node_id):
            created += 1
            await _upsert_node(
                db,
                _node_doc(
                    node_id=node_id,
                    code=_code(name, subtype.upper()),
                    name=name,
                    node_type="facility",
                    parent=company,
                    subtype=subtype,
                    description=f"Governed {subtype} reference preserved from current operational location records.",
                    source="operational_locations_backfill",
                    source_collection="operational_locations",
                    source_record_id=f"{loc_type}:{name}",
                    external_source_identifier=name,
                    metadata={"location_type": loc_type, "status": loc.get("status") or "", "geocode_status": loc.get("geocode_status") or ""},
                    display_order=200,
                ),
            )
        await _upsert_binding(
            db,
            _binding_doc(
                binding_id=f"binding::operational_locations::{loc_type}::{_norm(name)}",
                record_type="facility_reference",
                source_collection="operational_locations",
                source_record_id=f"{loc_type}:{name}",
                source_label=name,
                target_node_id=node_id,
                binding_kind="facility_reference",
                metadata={"location_type": loc_type},
            ),
        )
        bound += 1

    async for eq in db.equipment_master.find({}, {"_id": 1, "asset_number": 1, "equipment_id": 1, "unit_number": 1, "external_id": 1, "current_location": 1, "location": 1}):
        current_location = _compact(eq.get("current_location") or eq.get("location") or "")
        if not current_location:
            continue
        subtype = "yard" if "YARD" in current_location.upper() else "shop" if "SHOP" in current_location.upper() else "plant" if "PLANT" in current_location.upper() else ""
        asset_key = _compact(eq.get("asset_number") or eq.get("equipment_id") or eq.get("unit_number") or eq.get("external_id") or str(eq.get("_id") or ""))
        if not subtype:
            reviewed += 1
            await _record_review_item(
                db,
                source_collection="equipment_master",
                source_record_id=f"location::{_norm(current_location)}",
                source_label=current_location,
                suggested_type="facility",
                reason="Equipment location does not clearly resolve to a governed facility subtype.",
                confidence="medium",
                candidate_parent_id=company["id"],
                evidence=eq,
            )
            continue
        key = (subtype, _norm(current_location))
        node_id = exact_nodes.get(key)
        if not node_id and not _looks_like_ambiguous_facility(current_location):
            node_id = f"facility:{subtype}:{_norm(current_location)}"
            exact_nodes[key] = node_id
            if not await _get_node(db, node_id):
                created += 1
                await _upsert_node(
                    db,
                    _node_doc(
                        node_id=node_id,
                        code=_code(current_location, subtype.upper()),
                        name=current_location,
                        node_type="facility",
                        parent=company,
                        subtype=subtype,
                        description=f"Governed {subtype} created from current equipment location evidence.",
                        source="equipment_master_backfill",
                        source_collection="equipment_master",
                        source_record_id=asset_key,
                        external_source_identifier=current_location,
                        metadata={"derived_from": "current_location"},
                        display_order=210,
                    ),
                )
        if not node_id:
            reviewed += 1
            await _record_review_item(
                db,
                source_collection="equipment_master",
                source_record_id=f"location::{_norm(current_location)}",
                source_label=current_location,
                suggested_type="facility",
                suggested_subtype=subtype,
                reason="Equipment location looked facility-like but matched an ambiguous value that requires review.",
                confidence="medium",
                candidate_parent_id=company["id"],
                evidence=eq,
            )
            continue
        await _upsert_binding(
            db,
            _binding_doc(
                binding_id=f"binding::equipment_master::{asset_key}",
                record_type="equipment_location",
                source_collection="equipment_master",
                source_record_id=asset_key,
                source_label=current_location,
                target_node_id=node_id,
                binding_kind="equipment_facility_binding",
                confidence="medium",
                metadata={"current_location": current_location},
            ),
        )
        bound += 1
    return {"created": created, "bound": bound, "reviewed": reviewed}


async def _reset_generated_facility_artifacts(db) -> None:
    await db[COLLECTION_BINDINGS].delete_many({"binding_kind": "equipment_facility_binding"})
    await db[COLLECTION_REVIEW].delete_many({"source_collection": "equipment_master"})


async def _backfill_resource_assignments(db) -> Dict[str, int]:
    created = 0
    async for row in db.project_team_assignments.find({}, {"_id": 0, "project_number": 1, "assignment_role": 1, "email": 1, "employee_id": 1, "active": 1, "start_date": 1, "end_date": 1, "source": 1}):
        project_number = _compact(row.get("project_number") or "")
        if not project_number:
            continue
        assignment_role = _compact(row.get("assignment_role") or "team_member")
        email = _compact(row.get("email") or "")
        resource_id = _compact(row.get("employee_id") or email)
        if not resource_id:
            continue
        assignment_id = f"resource_assignment::project_team_assignments::{project_number}::{assignment_role}::{_norm(resource_id)}"
        existing = await db[COLLECTION_ASSIGNMENTS].find_one({"assignment_id": assignment_id}, {"_id": 0})
        if not existing:
            created += 1
        await _upsert_assignment(
            db,
            {
                "assignment_id": assignment_id,
                "resource_type": "employee",
                "resource_id": resource_id,
                "assigned_node_id": f"project:{project_number}",
                "assignment_role": assignment_role,
                "effective_start": row.get("start_date") or _utcnow(),
                "effective_end": row.get("end_date") or None,
                "active_status": bool(row.get("active", True)),
                "source": row.get("source") or "project_team_assignments",
                "authority": "project_team_assignments",
                "project_scope": project_number,
                "facility_scope": None,
                "history": [],
                "created_at": existing.get("created_at") if existing else _utcnow(),
                "audit_metadata": {"created_by": "wp18c1_backfill", "updated_by": "wp18c1_backfill"},
                "metadata": {"email": email},
            },
        )
    return {"created": created}


async def _refresh_node_binding_counts(db) -> None:
    counts = defaultdict(Counter)
    async for row in db[COLLECTION_BINDINGS].find({"status": "bound"}, {"_id": 0, "target_node_id": 1, "record_type": 1}):
        counts[row.get("target_node_id")][row.get("record_type") or "binding"] += 1
    for node_id, counter in counts.items():
        await db[COLLECTION_NODES].update_one({"id": node_id}, {"$set": {"binding_counts": dict(counter), "updated_at": _utcnow()}})


async def ensure_enterprise_hierarchy_foundation(db, *, force: bool = False) -> Dict[str, Any]:
    await ensure_hierarchy_indexes(db)
    seeded = await _seed_core_hierarchy(db)
    legacy_rows = await _normalize_legacy_organization_rows(db)
    latest = await db[COLLECTION_RUNS].find_one({}, {"_id": 0}, sort=[("run_at", -1)])
    latest_ts = _parse_ts((latest or {}).get("run_at"))
    if not force and latest_ts and (datetime.now(timezone.utc) - latest_ts).total_seconds() < 900:
        return latest
    project_stats = await _backfill_projects(db, seeded["division"])
    await _reset_generated_facility_artifacts(db)
    facility_stats = await _backfill_facilities(db, seeded["company"])
    assignment_stats = await _backfill_resource_assignments(db)
    await _refresh_node_binding_counts(db)
    report = {
        "run_id": f"hierarchy_run_{uuid4().hex[:10]}",
        "run_at": _utcnow(),
        "company_id": seeded["company"]["id"],
        "division_id": seeded["division"]["id"],
        "project_stats": project_stats,
        "facility_stats": facility_stats,
        "assignment_stats": assignment_stats,
        "legacy_rows_archived": legacy_rows,
    }
    await db[COLLECTION_RUNS].insert_one(deepcopy(report))
    return report


async def get_hierarchy_overview(db) -> Dict[str, Any]:
    await ensure_enterprise_hierarchy_foundation(db)
    nodes = [row async for row in db[COLLECTION_NODES].find({}, {"_id": 0})]
    review_rows = [_sanitize(row) async for row in db[COLLECTION_REVIEW].find({"status": "review_required"}, {"_id": 0}).sort("created_at", -1).limit(50)]
    assignments = [_sanitize(row) async for row in db[COLLECTION_ASSIGNMENTS].find({}, {"_id": 0}).limit(50)]
    counts_by_type = Counter(row.get("type") for row in nodes if not row.get("archive_status"))
    latest = await db[COLLECTION_RUNS].find_one({}, {"_id": 0}, sort=[("run_at", -1)])
    live_nodes = [row for row in nodes if not row.get("archive_status")]
    company = next((row for row in live_nodes if row.get("type") == "company"), None)
    division = next((row for row in live_nodes if row.get("type") == "division"), None)
    departments = [row for row in live_nodes if row.get("type") == "department"]
    facilities = [row for row in live_nodes if row.get("type") == "facility"]
    projects = [row for row in live_nodes if row.get("type") == "project"]
    return {
        "summary": {
            "total_nodes": len(nodes),
            "active_nodes": sum(1 for row in nodes if row.get("active_status")),
            "archived_nodes": sum(1 for row in nodes if row.get("archive_status")),
            "counts_by_type": dict(counts_by_type),
            "bindings_total": await db[COLLECTION_BINDINGS].count_documents({}),
            "review_queue_total": await db[COLLECTION_REVIEW].count_documents({"status": "review_required"}),
            "resource_assignments_total": await db[COLLECTION_ASSIGNMENTS].count_documents({}),
            "projects_bound": await db[COLLECTION_BINDINGS].count_documents({"record_type": "project", "status": "bound"}),
        },
        "current_masci_hierarchy": {
            "company": company,
            "division": division,
            "departments": departments,
            "regions": [row for row in nodes if row.get("type") == "region"],
            "facilities": facilities,
            "projects": projects,
        },
        "review_queue": review_rows,
        "resource_assignment_sample": assignments,
        "latest_run": latest,
    }


async def list_hierarchy_nodes(
    db,
    *,
    node_type: str = "",
    parent_id: str = "",
    search: str = "",
    include_archived: bool = False,
) -> List[Dict[str, Any]]:
    await ensure_enterprise_hierarchy_foundation(db)
    query: Dict[str, Any] = {}
    if node_type:
        query["type"] = node_type
    if parent_id:
        query["parent_id"] = parent_id
    if not include_archived:
        query["archive_status"] = {"$ne": True}
    if search:
        pattern = {"$regex": re.escape(search), "$options": "i"}
        query["$or"] = [{"name": pattern}, {"code": pattern}, {"ancestry_path": pattern}]
    rows = [
        row async for row in db[COLLECTION_NODES].find(query, {"_id": 0}).sort(
            [("type", 1), ("display_order", 1), ("name", 1)]
        )
    ]
    return rows


async def get_hierarchy_node_detail(db, node_id: str) -> Dict[str, Any]:
    await ensure_enterprise_hierarchy_foundation(db)
    node = await _get_node(db, node_id)
    if not node:
        raise LookupError("hierarchy_node_not_found")
    children = [row async for row in db[COLLECTION_NODES].find({"parent_id": node_id}, {"_id": 0}).sort("name", 1)]
    ancestry = []
    for ancestor_id in node.get("ancestor_ids") or []:
        ancestor = await _get_node(db, ancestor_id)
        if ancestor:
            ancestry.append(ancestor)
    bindings = [row async for row in db[COLLECTION_BINDINGS].find({"target_node_id": node_id}, {"_id": 0}).sort("updated_at", -1).limit(100)]
    assignments = [row async for row in db[COLLECTION_ASSIGNMENTS].find({"assigned_node_id": node_id}, {"_id": 0}).sort("updated_at", -1).limit(100)]
    return {"node": node, "children": children, "ancestry": ancestry, "bindings": bindings, "resource_assignments": assignments}


def _validate_parent_type(node_type: str, parent: Optional[Dict[str, Any]]) -> None:
    allowed = VALID_PARENT_TYPES.get(node_type)
    if allowed is None:
        raise ValueError("unsupported_node_type")
    if not allowed and parent is not None:
        raise ValueError("parent_not_allowed")
    if allowed and parent is None:
        raise ValueError("parent_required")
    if parent is not None and parent.get("type") not in allowed:
        raise ValueError("invalid_parent_type")


async def create_hierarchy_node(db, *, body: Dict[str, Any], actor: Dict[str, Any]) -> Dict[str, Any]:
    await ensure_enterprise_hierarchy_foundation(db)
    node_type = _norm(body.get("type") or "")
    if node_type not in NODE_TYPES:
        raise ValueError("unsupported_node_type")
    subtype = _norm(body.get("subtype") or "")
    if node_type == "facility" and subtype not in FACILITY_SUBTYPES:
        raise ValueError("facility_subtype_required")
    parent_id = body.get("parent_id") or None
    parent = await _get_node(db, parent_id) if parent_id else None
    _validate_parent_type(node_type, parent)
    code = _compact(body.get("code") or "")
    name = _compact(body.get("name") or "")
    if not code or not name:
        raise ValueError("code_and_name_required")
    if await db[COLLECTION_NODES].find_one({"code": code, "type": node_type, "company_scope": body.get("company_scope") or "masci", "archive_status": {"$ne": True}}, {"_id": 0, "id": 1}):
        raise ValueError("duplicate_code")
    node_id = f"{node_type}:{subtype + ':' if subtype else ''}{_norm(code)}"
    doc = _node_doc(
        node_id=node_id,
        code=code,
        name=name,
        node_type=node_type,
        parent=parent,
        subtype=subtype,
        description=_compact(body.get("description") or ""),
        company_id=_compact(body.get("company_scope") or (parent.get("company_scope") if parent else "masci")) or "masci",
        owner=_compact(body.get("owner_steward") or actor.get("email") or actor.get("id") or "admin"),
        steward=_compact(body.get("steward") or actor.get("email") or actor.get("id") or "admin"),
        source="manual_governed_creation",
        source_collection="enterprise_governance_hierarchy_api",
        source_record_id=node_id,
        external_source_identifier=_compact(body.get("external_source_identifier") or ""),
        confidence="high",
        active=bool(body.get("active_status", True)),
        archived=bool(body.get("archive_status", False)),
        effective_start=body.get("effective_start") or _utcnow(),
        effective_end=body.get("effective_end") or None,
        display_order=int(body.get("display_order") or 0),
        metadata=body.get("metadata_extension") or {},
    )
    created = await _upsert_node(db, doc)
    await _write_audit(db, "create_node", actor, before=None, after=created, reason="manual hierarchy node creation")
    return created


async def update_hierarchy_node(db, *, node_id: str, body: Dict[str, Any], actor: Dict[str, Any]) -> Dict[str, Any]:
    await ensure_enterprise_hierarchy_foundation(db)
    node = await _get_node(db, node_id)
    if not node:
        raise LookupError("hierarchy_node_not_found")
    if body.get("code") and body.get("code") != node.get("code"):
        raise ValueError("code_is_immutable")
    if body.get("type") and _norm(body.get("type")) != node.get("type"):
        raise ValueError("type_is_immutable")
    updated = deepcopy(node)
    parent_id = body.get("parent_id") if "parent_id" in body else node.get("parent_id")
    parent = await _get_node(db, parent_id) if parent_id else None
    if parent and parent.get("id") == node_id:
        raise ValueError("circular_parent")
    if parent and node_id in (parent.get("ancestor_ids") or []):
        raise ValueError("circular_parent")
    _validate_parent_type(node.get("type"), parent)
    updated["name"] = _compact(body.get("name") or updated.get("name") or "")
    updated["description"] = _compact(body.get("description") or updated.get("description") or "")
    updated["parent_id"] = parent_id
    updated["path"] = _path_parts(parent, updated["name"])
    updated["ancestor_ids"] = _ancestor_ids(parent)
    updated["ancestry_path"] = " / ".join(updated["path"])
    updated["active_status"] = bool(body.get("active_status", updated.get("active_status", True)))
    updated["archive_status"] = bool(body.get("archive_status", updated.get("archive_status", False)))
    updated["display_order"] = int(body.get("display_order") or updated.get("display_order") or 0)
    updated["effective_start"] = body.get("effective_start") or updated.get("effective_start")
    updated["effective_end"] = body.get("effective_end") if "effective_end" in body else updated.get("effective_end")
    updated["owner_steward"] = _compact(body.get("owner_steward") or updated.get("owner_steward") or "")
    updated["steward"] = _compact(body.get("steward") or updated.get("steward") or "")
    updated["metadata_extension"] = {**(updated.get("metadata_extension") or {}), **(body.get("metadata_extension") or {})}
    updated["audit_metadata"] = {**(updated.get("audit_metadata") or {}), "updated_by": actor.get("email") or actor.get("id") or "admin"}
    saved = await _upsert_node(db, updated)
    await _write_audit(db, "update_node", actor, before=node, after=saved, reason="manual hierarchy node update")
    return saved


async def set_hierarchy_node_state(db, *, node_id: str, actor: Dict[str, Any], action: str, reason: str = "") -> Dict[str, Any]:
    node = await _get_node(db, node_id)
    if not node:
        raise LookupError("hierarchy_node_not_found")
    updated = deepcopy(node)
    if action == "activate":
        updated["active_status"] = True
        updated["archive_status"] = False
    elif action == "deactivate":
        updated["active_status"] = False
    elif action == "archive":
        updated["active_status"] = False
        updated["archive_status"] = True
    else:
        raise ValueError("unsupported_state_action")
    saved = await _upsert_node(db, updated)
    await _write_audit(db, action, actor, before=node, after=saved, reason=reason or action)
    return saved


async def bind_existing_record(
    db,
    *,
    actor: Dict[str, Any],
    record_type: str,
    source_collection: str,
    source_record_id: str,
    source_label: str,
    target_node_id: str,
    binding_kind: str,
    confidence: str = "high",
    metadata: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    if not await _get_node(db, target_node_id):
        raise LookupError("hierarchy_node_not_found")
    doc = _binding_doc(
        binding_id=f"binding::{source_collection}::{record_type}::{_norm(source_record_id)}::{_norm(target_node_id)}",
        record_type=record_type,
        source_collection=source_collection,
        source_record_id=source_record_id,
        source_label=source_label,
        target_node_id=target_node_id,
        binding_kind=binding_kind,
        confidence=confidence,
        metadata=metadata,
    )
    await _upsert_binding(db, doc)
    await _write_audit(db, "bind_record", actor, before=None, after=doc, reason="manual binding")
    await _refresh_node_binding_counts(db)
    return doc


async def list_hierarchy_bindings(db, *, status: str = "", record_type: str = "") -> List[Dict[str, Any]]:
    await ensure_enterprise_hierarchy_foundation(db)
    query: Dict[str, Any] = {}
    if status:
        query["status"] = status
    if record_type:
        query["record_type"] = record_type
    return [row async for row in db[COLLECTION_BINDINGS].find(query, {"_id": 0}).sort("updated_at", -1).limit(500)]


async def list_review_queue(db) -> List[Dict[str, Any]]:
    await ensure_enterprise_hierarchy_foundation(db)
    return [_sanitize(row) async for row in db[COLLECTION_REVIEW].find({}, {"_id": 0}).sort([("priority", -1), ("updated_at", -1)]).limit(500)]


async def list_resource_assignments(db, *, resource_type: str = "") -> List[Dict[str, Any]]:
    await ensure_enterprise_hierarchy_foundation(db)
    query: Dict[str, Any] = {}
    if resource_type:
        query["resource_type"] = resource_type
    return [row async for row in db[COLLECTION_ASSIGNMENTS].find(query, {"_id": 0}).sort("updated_at", -1).limit(500)]


async def get_scope_preview(db, *, email: str = "") -> Dict[str, Any]:
    await ensure_enterprise_hierarchy_foundation(db)
    query = {}
    if email:
        query["email"] = email.lower()
    identities = [row async for row in db.enterprise_governance_identity_projections.find(query, {"_id": 0}).limit(100)]
    results = []
    for row in identities:
        project_numbers = list(row.get("project_numbers") or [])
        project_node_ids = [f"project:{num}" for num in project_numbers if num]
        results.append({
            "identity": {
                "email": row.get("email") or "",
                "display_name": row.get("display_name") or row.get("name") or row.get("email") or "",
                "company_id": row.get("company_id") or "masci",
                "department_id": row.get("department_id") or None,
                "region_id": row.get("region_id") or None,
            },
            "scope_preview": {
                "company_scope": [row.get("company_id") or "masci"],
                "project_scope": project_node_ids,
                "division_scope": ["division:operations"],
                "department_scope": [row.get("department_id")] if row.get("department_id") else [],
                "region_scope": [row.get("region_id")] if row.get("region_id") else [],
            },
        })
    return {"count": len(results), "items": results}


async def get_latest_backfill_report(db) -> Dict[str, Any]:
    await ensure_enterprise_hierarchy_foundation(db)
    report = await db[COLLECTION_RUNS].find_one({}, {"_id": 0}, sort=[("run_at", -1)])
    return report or {}
