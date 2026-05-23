"""
routes/governance.py — Phase 2 P0+P1 · Compliance Gap Detector + Governance Health.

Cross-portal contradiction detection engine. Scans the existing source-of-truth
collections (employees · safety_training_records · safety_equipment_issuances ·
corrective_actions · incidents) and surfaces operational risk findings — WITHOUT
duplicating any source of truth.

Detector rules (this cut):
- DRV_MED_EXPIRED — active approved driver with expired medical card
- DRV_MED_EXPIRING — active approved driver with medical card expiring ≤30d
- DRV_CDL_EXPIRED — CDL holder with expired CDL
- DRV_CDL_EXPIRING — CDL holder with CDL expiring ≤30d
- TRN_EXPIRED — active employee with at least one expired training record
- PPE_MISSING — active field employee with no PPE issuance on file ever
- INC_CLOSED_CAPA_OPEN — incident marked closed but linked CAPA still open
- CAPA_OVERDUE — CAPA past its due_date and not in a closed status
- EMP_ARCHIVED_ACTIVE — employee soft-deleted but still flagged active
- EMP_DUP_NAMES — multiple active employee documents sharing the same name

Each finding is idempotent — id is a stable hash of (rule_id, entity_kind,
entity_id) so a re-scan upserts on top of the same finding and preserves
ack/resolve state. When a previously-flagged condition no longer matches,
the finding is auto-resolved with `resolved_by="system_auto"`.

Endpoints (admin-strict only — no PM/HR/Safety read-through):
- POST /api/admin/compliance/scan
- GET  /api/admin/compliance/findings
- GET  /api/admin/compliance/findings/{id}
- POST /api/admin/compliance/findings/{id}/acknowledge
- POST /api/admin/compliance/findings/{id}/resolve
- GET  /api/admin/governance/summary
"""
from __future__ import annotations

import hashlib
import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

COLLECTION = "compliance_findings"

SEVERITY_RANK = {
    "critical": 0,
    "high": 1,
    "medium": 2,
    "low": 3,
    "info": 4,
}

RULE_CATALOG: Dict[str, Dict[str, str]] = {
    "DRV_MED_EXPIRED":  {"category": "driver",   "severity": "critical", "title": "Driver medical card expired"},
    "DRV_MED_EXPIRING": {"category": "driver",   "severity": "high",     "title": "Driver medical card expiring ≤30d"},
    "DRV_CDL_EXPIRED":  {"category": "driver",   "severity": "critical", "title": "CDL expired"},
    "DRV_CDL_EXPIRING": {"category": "driver",   "severity": "high",     "title": "CDL expiring ≤30d"},
    "TRN_EXPIRED":      {"category": "training", "severity": "high",     "title": "Required training expired"},
    "PPE_MISSING":      {"category": "ppe",      "severity": "medium",   "title": "Active employee with no PPE issuance on file"},
    "INC_CLOSED_CAPA_OPEN": {"category": "incident", "severity": "high", "title": "Incident closed but CAPA still open"},
    "CAPA_OVERDUE":     {"category": "capa",     "severity": "high",     "title": "CAPA past due date"},
    "EMP_ARCHIVED_ACTIVE": {"category": "employee", "severity": "medium", "title": "Archived employee still flagged active"},
    "EMP_DUP_NAMES":    {"category": "employee", "severity": "low",      "title": "Duplicate active employee names"},
}


def _finding_id(rule_id: str, entity_kind: str, entity_id: str) -> str:
    raw = f"{rule_id}|{entity_kind}|{entity_id or ''}"
    return hashlib.sha1(raw.encode("utf-8")).hexdigest()[:24]


def _today_iso() -> str:
    return datetime.now(timezone.utc).isoformat()[:10]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _cutoff_iso(days: int) -> str:
    return (datetime.now(timezone.utc) + timedelta(days=days)).isoformat()[:10]


def _is_truthy(v: Any) -> bool:
    if isinstance(v, bool):
        return v
    if isinstance(v, str):
        return v.strip().lower() in {"true", "yes", "y", "1"}
    return bool(v)


# ---------------------------------------------------------------------------
# Detector rules — each returns a list of finding dicts (without id / status).
# ---------------------------------------------------------------------------

async def _detect_driver_expirations(db) -> List[Dict[str, Any]]:
    """DRV_MED_EXPIRED · DRV_MED_EXPIRING · DRV_CDL_EXPIRED · DRV_CDL_EXPIRING."""
    today = _today_iso()
    cutoff = _cutoff_iso(30)
    out: List[Dict[str, Any]] = []
    q = {
        "deleted_at": None,
        "is_active": {"$ne": False},
        "$or": [
            {"approved_company_driver": True},
            {"cdl_holder": True},
            {"driver_status": "active"},
        ],
    }
    cursor = db.employees.find(
        q,
        {"_id": 0, "id": 1, "name": 1, "driver_status": 1,
         "cdl_holder": 1, "approved_company_driver": 1,
         "cdl_expiration_date": 1, "medical_card_expiration_date": 1},
    )
    async for emp in cursor:
        emp_id = emp.get("id") or ""
        name = emp.get("name") or "(unnamed)"
        is_approved = _is_truthy(emp.get("approved_company_driver"))
        is_cdl = _is_truthy(emp.get("cdl_holder"))
        med = (emp.get("medical_card_expiration_date") or "").strip()
        cdl = (emp.get("cdl_expiration_date") or "").strip()

        if is_approved and med:
            if med < today:
                out.append({
                    "rule_id": "DRV_MED_EXPIRED",
                    "entity_kind": "employee",
                    "entity_id": emp_id,
                    "entity_name": name,
                    "description": f"{name} is an approved driver but their medical card expired on {med}.",
                    "source": {"medical_card_expiration_date": med, "today": today,
                               "approved_company_driver": True},
                })
            elif med <= cutoff:
                out.append({
                    "rule_id": "DRV_MED_EXPIRING",
                    "entity_kind": "employee",
                    "entity_id": emp_id,
                    "entity_name": name,
                    "description": f"{name}'s medical card expires on {med} (within 30 days).",
                    "source": {"medical_card_expiration_date": med, "today": today,
                               "cutoff_30d": cutoff},
                })

        if is_cdl and cdl:
            if cdl < today:
                out.append({
                    "rule_id": "DRV_CDL_EXPIRED",
                    "entity_kind": "employee",
                    "entity_id": emp_id,
                    "entity_name": name,
                    "description": f"{name} is a CDL holder but their CDL expired on {cdl}.",
                    "source": {"cdl_expiration_date": cdl, "today": today,
                               "cdl_holder": True},
                })
            elif cdl <= cutoff:
                out.append({
                    "rule_id": "DRV_CDL_EXPIRING",
                    "entity_kind": "employee",
                    "entity_id": emp_id,
                    "entity_name": name,
                    "description": f"{name}'s CDL expires on {cdl} (within 30 days).",
                    "source": {"cdl_expiration_date": cdl, "today": today,
                               "cutoff_30d": cutoff},
                })
    return out


async def _detect_training_expired(db) -> List[Dict[str, Any]]:
    """TRN_EXPIRED — one finding per active employee who has ≥1 expired training record."""
    today = _today_iso()
    out: List[Dict[str, Any]] = []
    # Group expired training rows by employee.
    pipeline = [
        {"$match": {
            "expiration_date": {"$gt": "", "$lt": today},
        }},
        {"$group": {
            "_id": {"id": "$employee_id", "name": "$employee_name"},
            "expired_trainings": {"$addToSet": "$training_name"},
            "count": {"$sum": 1},
            "earliest": {"$min": "$expiration_date"},
        }},
        {"$limit": 1000},
    ]
    expired_by_emp: List[Dict[str, Any]] = []
    async for row in db.safety_training_records.aggregate(pipeline):
        expired_by_emp.append(row)

    # Resolve each grouped row against the employee master to filter out
    # archived / inactive employees (don't pollute the dashboard with
    # findings against people who left).
    for row in expired_by_emp:
        ident = row.get("_id") or {}
        emp_id = ident.get("id") or ""
        name = ident.get("name") or "(unnamed)"
        # Resolve employee record if we have an id; otherwise match by name.
        emp_doc = None
        if emp_id:
            emp_doc = await db.employees.find_one(
                {"id": emp_id}, {"_id": 0, "is_active": 1, "deleted_at": 1, "name": 1},
            )
        if not emp_doc and name and name != "(unnamed)":
            emp_doc = await db.employees.find_one(
                {"name": name}, {"_id": 0, "is_active": 1, "deleted_at": 1, "id": 1},
            )
            if emp_doc and not emp_id:
                emp_id = emp_doc.get("id") or ""
        if not emp_doc:
            # Loose evidence — employee not in master. Skip (handled by
            # EMP_ARCHIVED_ACTIVE / EMP_DUP_NAMES instead of polluting here).
            continue
        if emp_doc.get("deleted_at") is not None:
            continue
        if emp_doc.get("is_active") is False:
            continue
        trainings = sorted(t for t in (row.get("expired_trainings") or []) if t)
        earliest = row.get("earliest") or ""
        cnt = row.get("count") or 0
        # Use a stable per-employee id so the finding upserts across scans.
        out.append({
            "rule_id": "TRN_EXPIRED",
            "entity_kind": "employee",
            "entity_id": emp_id or name,
            "entity_name": name,
            "description": (
                f"{name} has {cnt} expired training record"
                f"{'s' if cnt != 1 else ''} on file. Earliest expiration: {earliest}."
            ),
            "source": {
                "expired_count": cnt,
                "earliest_expiration_date": earliest,
                "trainings": trainings[:15],  # cap evidence size
            },
        })
    return out


async def _detect_ppe_missing(db) -> List[Dict[str, Any]]:
    """PPE_MISSING — active employee with zero rows in safety_equipment_issuances."""
    out: List[Dict[str, Any]] = []
    # Gather all employee names that appear in any PPE issuance.
    names_with_ppe: Set[str] = set()
    async for row in db.safety_equipment_issuances.find(
        {}, {"_id": 0, "employee_name": 1},
    ):
        n = (row.get("employee_name") or "").strip()
        if n:
            names_with_ppe.add(n.lower())

    # Walk active employees and flag the ones missing entirely.
    q = {"deleted_at": None, "is_active": {"$ne": False}}
    cursor = db.employees.find(
        q, {"_id": 0, "id": 1, "name": 1, "position": 1, "is_field": 1},
    ).limit(2000)
    async for emp in cursor:
        name = (emp.get("name") or "").strip()
        if not name:
            continue
        # Skip purely office personnel where data exists; default to flag
        # if `is_field` is missing (better to over-flag than miss).
        is_field = emp.get("is_field")
        if is_field is False:
            continue
        if name.lower() in names_with_ppe:
            continue
        out.append({
            "rule_id": "PPE_MISSING",
            "entity_kind": "employee",
            "entity_id": emp.get("id") or name,
            "entity_name": name,
            "description": f"{name} is active but has zero PPE issuance records on file.",
            "source": {"position": emp.get("position") or "", "is_field": is_field},
        })
    return out


async def _detect_capa_overdue(db) -> List[Dict[str, Any]]:
    """CAPA_OVERDUE — open CAPA where due_date < today."""
    today = _today_iso()
    out: List[Dict[str, Any]] = []
    cursor = db.corrective_actions.find(
        {
            "due_date": {"$gt": "", "$lt": today},
            "status": {"$nin": ["closed", "completed", "verified", "resolved"]},
        },
        {"_id": 0, "id": 1, "title": 1, "description": 1, "status": 1,
         "due_date": 1, "linked_employee_name": 1, "employee_name": 1,
         "incident_id": 1, "owner": 1},
    ).limit(500)
    async for capa in cursor:
        capa_id = capa.get("id") or ""
        title = capa.get("title") or capa.get("description") or "(untitled CAPA)"
        person = capa.get("linked_employee_name") or capa.get("employee_name") or "(unassigned)"
        out.append({
            "rule_id": "CAPA_OVERDUE",
            "entity_kind": "capa",
            "entity_id": capa_id,
            "entity_name": title[:120],
            "description": (
                f"CAPA '{title[:80]}' is past due (due {capa.get('due_date')})"
                f" — status is '{capa.get('status') or 'open'}'. Linked: {person}."
            ),
            "source": {
                "status": capa.get("status") or "open",
                "due_date": capa.get("due_date"),
                "linked_employee": person,
                "incident_id": capa.get("incident_id"),
                "owner": capa.get("owner"),
            },
        })
    return out


async def _detect_incident_closed_capa_open(db) -> List[Dict[str, Any]]:
    """INC_CLOSED_CAPA_OPEN — incident with status closed but at least one open CAPA linked."""
    out: List[Dict[str, Any]] = []
    cursor = db.incidents.find(
        {"status": {"$in": ["closed", "completed", "resolved"]}},
        {"_id": 0, "id": 1, "incident_id": 1, "description": 1,
         "person_involved": 1, "date_occurred": 1, "status": 1},
    ).limit(500)
    async for inc in cursor:
        inc_pk = inc.get("id") or inc.get("incident_id") or ""
        if not inc_pk:
            continue
        # Open CAPAs linked back to this incident by id.
        open_capa_count = await db.corrective_actions.count_documents({
            "incident_id": inc_pk,
            "status": {"$nin": ["closed", "completed", "verified", "resolved"]},
        })
        if open_capa_count <= 0:
            continue
        out.append({
            "rule_id": "INC_CLOSED_CAPA_OPEN",
            "entity_kind": "incident",
            "entity_id": inc_pk,
            "entity_name": (inc.get("description") or "(no description)")[:120],
            "description": (
                f"Incident {inc_pk} is marked '{inc.get('status')}' but has "
                f"{open_capa_count} open CAPA{'s' if open_capa_count != 1 else ''} still linked."
            ),
            "source": {
                "incident_status": inc.get("status"),
                "open_capa_count": open_capa_count,
                "person_involved": inc.get("person_involved"),
                "date_occurred": inc.get("date_occurred"),
            },
        })
    return out


async def _detect_employee_anomalies(db) -> List[Dict[str, Any]]:
    """EMP_ARCHIVED_ACTIVE + EMP_DUP_NAMES."""
    out: List[Dict[str, Any]] = []
    # Archived + still active flag.
    cursor = db.employees.find(
        {"deleted_at": {"$ne": None}, "is_active": True},
        {"_id": 0, "id": 1, "name": 1, "deleted_at": 1},
    ).limit(500)
    async for emp in cursor:
        out.append({
            "rule_id": "EMP_ARCHIVED_ACTIVE",
            "entity_kind": "employee",
            "entity_id": emp.get("id") or "",
            "entity_name": emp.get("name") or "(unnamed)",
            "description": (
                f"{emp.get('name') or '(unnamed)'} is archived (soft-deleted, deleted_at="
                f"{emp.get('deleted_at')}) but is_active=true. Restore or finalize archival."
            ),
            "source": {"deleted_at": emp.get("deleted_at"), "is_active": True},
        })

    # Duplicate active names — aggregate active employees by lowercased name.
    pipeline = [
        {"$match": {"deleted_at": None, "is_active": {"$ne": False}}},
        {"$project": {
            "_id": 0, "id": 1,
            "name_lc": {"$toLower": {"$trim": {"input": {"$ifNull": ["$name", ""]}}}},
        }},
        {"$match": {"name_lc": {"$ne": ""}}},
        {"$group": {
            "_id": "$name_lc",
            "ids": {"$push": "$id"},
            "count": {"$sum": 1},
        }},
        {"$match": {"count": {"$gt": 1}}},
        {"$limit": 200},
    ]
    async for row in db.employees.aggregate(pipeline):
        name = row.get("_id") or ""
        ids = row.get("ids") or []
        out.append({
            "rule_id": "EMP_DUP_NAMES",
            "entity_kind": "employee_group",
            "entity_id": f"dup:{name}",
            "entity_name": name,
            "description": (
                f"{row.get('count')} active employee records share the lowercased name "
                f"'{name}'. Likely duplicate identities — consolidate or distinguish."
            ),
            "source": {"name_lc": name, "ids": ids, "count": row.get("count")},
        })
    return out


DETECTORS = [
    _detect_driver_expirations,
    _detect_training_expired,
    _detect_ppe_missing,
    _detect_capa_overdue,
    _detect_incident_closed_capa_open,
    _detect_employee_anomalies,
]


# ---------------------------------------------------------------------------
# Scan + persistence helpers
# ---------------------------------------------------------------------------

async def _run_scan(db) -> Dict[str, Any]:
    """Run every detector, upsert findings, auto-resolve disappeared ones.
    Returns a summary dict { rule_counts, severity_counts, total_open, resolved_auto }.
    """
    started_at = _now_iso()
    detected: List[Dict[str, Any]] = []
    detector_errors: Dict[str, str] = {}
    for detector in DETECTORS:
        try:
            rows = await detector(db)
            detected.extend(rows)
        except Exception as e:  # noqa: BLE001
            logger.exception("Detector %s failed: %s", detector.__name__, e)
            detector_errors[detector.__name__] = str(e)

    # Stamp each row.
    detected_ids: Set[str] = set()
    for row in detected:
        rule_id = row["rule_id"]
        meta = RULE_CATALOG.get(rule_id, {})
        row["id"] = _finding_id(rule_id, row["entity_kind"], row["entity_id"])
        row["severity"] = meta.get("severity") or "info"
        row["category"] = meta.get("category") or "other"
        row["title"] = meta.get("title") or rule_id
        detected_ids.add(row["id"])

    # Upsert. Preserve user state (status/ack/resolve) when re-detecting the
    # same finding. Always refresh source + last_detected_at.
    now_iso = _now_iso()
    upserts = 0
    for row in detected:
        existing = await db[COLLECTION].find_one({"id": row["id"]}, {"_id": 0})
        if existing:
            # Re-open if previously auto-resolved (system inferred the
            # condition cleared, but it has come back).
            new_status = existing.get("status") or "open"
            if existing.get("status") == "resolved" and existing.get("resolved_by") == "system_auto":
                new_status = "open"
            await db[COLLECTION].update_one(
                {"id": row["id"]},
                {"$set": {
                    "title": row["title"],
                    "description": row["description"],
                    "source": row["source"],
                    "severity": row["severity"],
                    "category": row["category"],
                    "entity_name": row["entity_name"],
                    "last_detected_at": now_iso,
                    "status": new_status,
                }},
            )
        else:
            await db[COLLECTION].insert_one({
                **row,
                "status": "open",
                "first_detected_at": now_iso,
                "last_detected_at": now_iso,
                "acknowledged_by": None,
                "acknowledged_at": None,
                "acknowledged_note": None,
                "resolved_by": None,
                "resolved_at": None,
                "resolved_note": None,
            })
        upserts += 1

    # Auto-resolve any open finding whose id was not seen this scan and is
    # not already user-resolved.
    auto_resolved = 0
    cursor = db[COLLECTION].find(
        {"status": {"$in": ["open", "acknowledged"]}},
        {"_id": 0, "id": 1},
    )
    stale_ids: List[str] = []
    async for row in cursor:
        if row["id"] not in detected_ids:
            stale_ids.append(row["id"])
    if stale_ids:
        res = await db[COLLECTION].update_many(
            {"id": {"$in": stale_ids}, "status": {"$in": ["open", "acknowledged"]}},
            {"$set": {
                "status": "resolved",
                "resolved_by": "system_auto",
                "resolved_at": now_iso,
                "resolved_note": "Condition no longer detected.",
            }},
        )
        auto_resolved = res.modified_count

    rule_counts: Dict[str, int] = {}
    severity_counts: Dict[str, int] = {}
    for row in detected:
        rule_counts[row["rule_id"]] = rule_counts.get(row["rule_id"], 0) + 1
        severity_counts[row["severity"]] = severity_counts.get(row["severity"], 0) + 1

    summary = {
        "started_at": started_at,
        "finished_at": _now_iso(),
        "detected_total": len(detected),
        "upserts": upserts,
        "auto_resolved": auto_resolved,
        "rule_counts": rule_counts,
        "severity_counts": severity_counts,
        "detector_errors": detector_errors,
    }

    # Persist scan log (last 50 retained).
    await db["compliance_scans"].insert_one({**summary})
    # Trim oldest beyond 50.
    total_logs = await db["compliance_scans"].count_documents({})
    if total_logs > 50:
        cutoff_doc = await db["compliance_scans"].find_one(
            {}, {"_id": 0, "started_at": 1},
            sort=[("started_at", -1)], skip=49,
        )
        if cutoff_doc:
            await db["compliance_scans"].delete_many(
                {"started_at": {"$lt": cutoff_doc["started_at"]}}
            )
    return summary


# ---------------------------------------------------------------------------
# Pydantic models
# ---------------------------------------------------------------------------

class AcknowledgePayload(BaseModel):
    note: Optional[str] = Field(default=None, max_length=1000)


class ResolvePayload(BaseModel):
    note: Optional[str] = Field(default=None, max_length=1000)


# ---------------------------------------------------------------------------
# Router factory
# ---------------------------------------------------------------------------

def build_governance_router(db, require_admin_strict):
    router = APIRouter(tags=["governance"])

    @router.post("/api/admin/compliance/scan",
                 dependencies=[Depends(require_admin_strict)])
    async def run_scan_endpoint():
        summary = await _run_scan(db)
        return {"ok": True, **summary}

    @router.get("/api/admin/compliance/findings",
                dependencies=[Depends(require_admin_strict)])
    async def list_findings(
        status: Optional[str] = Query(default=None),
        severity: Optional[str] = Query(default=None),
        rule_id: Optional[str] = Query(default=None),
        category: Optional[str] = Query(default=None),
        entity_kind: Optional[str] = Query(default=None),
        q: Optional[str] = Query(default=None),
        limit: int = Query(default=200, ge=1, le=1000),
    ):
        flt: Dict[str, Any] = {}
        if status:
            flt["status"] = status
        else:
            # Default: hide resolved unless explicitly requested.
            flt["status"] = {"$in": ["open", "acknowledged"]}
        if severity:
            flt["severity"] = severity
        if rule_id:
            flt["rule_id"] = rule_id
        if category:
            flt["category"] = category
        if entity_kind:
            flt["entity_kind"] = entity_kind
        if q:
            safe = re.escape(q.strip())
            if safe:
                flt["$or"] = [
                    {"entity_name": {"$regex": safe, "$options": "i"}},
                    {"description": {"$regex": safe, "$options": "i"}},
                ]
        items: List[Dict[str, Any]] = []
        cursor = db[COLLECTION].find(flt, {"_id": 0}).sort(
            [("severity", 1), ("last_detected_at", -1)]
        ).limit(limit)
        async for row in cursor:
            items.append(row)
        # Sort severity correctly (lexical mongo sort doesn't respect our rank).
        items.sort(key=lambda r: (SEVERITY_RANK.get(r.get("severity", "info"), 99),
                                  -1 * (1 if (r.get("last_detected_at") or "") else 0),
                                  r.get("last_detected_at") or ""))
        items.reverse()  # most recent within rank first
        items.sort(key=lambda r: SEVERITY_RANK.get(r.get("severity", "info"), 99))
        return {"ok": True, "items": items, "count": len(items)}

    @router.get("/api/admin/compliance/findings/{finding_id}",
                dependencies=[Depends(require_admin_strict)])
    async def get_finding(finding_id: str):
        doc = await db[COLLECTION].find_one({"id": finding_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Finding not found")
        return {"ok": True, "finding": doc}

    @router.post("/api/admin/compliance/findings/{finding_id}/acknowledge",
                 dependencies=[Depends(require_admin_strict)])
    async def acknowledge_finding(finding_id: str, body: AcknowledgePayload):
        doc = await db[COLLECTION].find_one({"id": finding_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Finding not found")
        if doc.get("status") == "resolved":
            raise HTTPException(status_code=400,
                                detail="Cannot acknowledge a resolved finding")
        now = _now_iso()
        await db[COLLECTION].update_one(
            {"id": finding_id},
            {"$set": {
                "status": "acknowledged",
                "acknowledged_by": "admin",
                "acknowledged_at": now,
                "acknowledged_note": (body.note or "").strip() or None,
            }},
        )
        updated = await db[COLLECTION].find_one({"id": finding_id}, {"_id": 0})
        return {"ok": True, "finding": updated}

    @router.post("/api/admin/compliance/findings/{finding_id}/resolve",
                 dependencies=[Depends(require_admin_strict)])
    async def resolve_finding(finding_id: str, body: ResolvePayload):
        doc = await db[COLLECTION].find_one({"id": finding_id}, {"_id": 0})
        if not doc:
            raise HTTPException(status_code=404, detail="Finding not found")
        now = _now_iso()
        await db[COLLECTION].update_one(
            {"id": finding_id},
            {"$set": {
                "status": "resolved",
                "resolved_by": "admin",
                "resolved_at": now,
                "resolved_note": (body.note or "").strip() or None,
            }},
        )
        updated = await db[COLLECTION].find_one({"id": finding_id}, {"_id": 0})
        return {"ok": True, "finding": updated}

    @router.get("/api/admin/governance/summary",
                dependencies=[Depends(require_admin_strict)])
    async def governance_summary():
        # Open by severity
        sev_counts: Dict[str, int] = {k: 0 for k in SEVERITY_RANK.keys()}
        async for row in db[COLLECTION].aggregate([
            {"$match": {"status": {"$in": ["open", "acknowledged"]}}},
            {"$group": {"_id": "$severity", "n": {"$sum": 1}}},
        ]):
            sev_counts[row["_id"] or "info"] = row["n"]

        # Status breakdown
        status_counts: Dict[str, int] = {"open": 0, "acknowledged": 0, "resolved": 0}
        async for row in db[COLLECTION].aggregate([
            {"$group": {"_id": "$status", "n": {"$sum": 1}}},
        ]):
            status_counts[row["_id"] or "open"] = row["n"]

        # Category breakdown (open only)
        cat_counts: Dict[str, int] = {}
        async for row in db[COLLECTION].aggregate([
            {"$match": {"status": {"$in": ["open", "acknowledged"]}}},
            {"$group": {"_id": "$category", "n": {"$sum": 1}}},
        ]):
            cat_counts[row["_id"] or "other"] = row["n"]

        # Per-rule open counts
        rule_counts: Dict[str, int] = {}
        async for row in db[COLLECTION].aggregate([
            {"$match": {"status": {"$in": ["open", "acknowledged"]}}},
            {"$group": {"_id": "$rule_id", "n": {"$sum": 1}}},
            {"$sort": {"n": -1}},
        ]):
            rule_counts[row["_id"]] = row["n"]

        # Last scan
        last_scan = await db["compliance_scans"].find_one(
            {}, {"_id": 0}, sort=[("started_at", -1)],
        )

        # Convergence score — simple weighted formula:
        # 100 if no open critical/high; otherwise penalize critical=20, high=8, medium=3, low=1
        score = 100
        score -= 20 * sev_counts.get("critical", 0)
        score -= 8 * sev_counts.get("high", 0)
        score -= 3 * sev_counts.get("medium", 0)
        score -= 1 * sev_counts.get("low", 0)
        score = max(0, min(100, score))

        # Health label
        if score >= 90:
            health_label = "healthy"
        elif score >= 70:
            health_label = "fair"
        elif score >= 40:
            health_label = "degraded"
        else:
            health_label = "critical"

        return {
            "ok": True,
            "severity_counts": sev_counts,
            "status_counts": status_counts,
            "category_counts": cat_counts,
            "rule_counts": rule_counts,
            "convergence_score": score,
            "health_label": health_label,
            "last_scan": last_scan,
            "rule_catalog": RULE_CATALOG,
        }

    return router


__all__ = ["build_governance_router", "RULE_CATALOG", "_run_scan", "COLLECTION"]
