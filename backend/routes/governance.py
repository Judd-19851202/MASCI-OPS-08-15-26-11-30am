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
from fastapi.responses import Response as _FastAPIResponse
from pydantic import BaseModel, Field
from lib.synthetic_corrective_action_filter import apply_synthetic_corrective_action_exclusion
from lib.synthetic_hr_filter import apply_synthetic_hr_exclusion
from lib.synthetic_hr_filter import is_synthetic_hr
from lib.synthetic_safety_filter import apply_synthetic_incident_exclusion
from lib.synthetic_dr_filter import apply_synthetic_dr_exclusion

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
    # iter355 — Operator ↔ Employee Linkage Enforcement (Phase 2 P2).
    # Surfaces free-text employee references that cannot be linked to a
    # canonical employee, or that map ambiguously to multiple employees.
    "EMP_LINK_UNRESOLVABLE": {"category": "linkage", "severity": "high",   "title": "Employee name on records does not match any active employee"},
    "EMP_LINK_AMBIGUOUS":    {"category": "linkage", "severity": "high",   "title": "Employee name on records matches multiple active employees"},
    "EMP_LINK_MISSING_ID":   {"category": "linkage", "severity": "medium", "title": "Record stores employee_name but no employee_id (backfillable)"},
    # iter356 — Incident → CAPA → Closeout Lifecycle Enforcement (Phase 2 P0/P3).
    # Three rules tighten the corrective-action accountability chain.
    "INC_NEEDS_CAPA":           {"category": "lifecycle", "severity": "critical", "title": "Severe incident has no linked CAPA"},
    "CAPA_AWAITING_VERIFICATION": {"category": "lifecycle", "severity": "medium",   "title": "CAPA stuck in Pending Review beyond 7 days"},
    "CAPA_NO_OWNER":            {"category": "lifecycle", "severity": "medium",   "title": "Open CAPA has no assigned owner"},
}

_GOVERNANCE_FRESHNESS_SLA_MINUTES = 24 * 60


def _governance_freshness(last_scan: Optional[Dict[str, Any]], *, now: Optional[datetime] = None) -> Dict[str, Any]:
    now = now or datetime.now(timezone.utc)
    if not last_scan:
        return {
            "state": "UNKNOWN",
            "confidence": "UNKNOWN",
            "scan_execution_health": "UNKNOWN",
            "last_scan_at": None,
            "data_age_minutes": None,
            "freshness_sla_minutes": _GOVERNANCE_FRESHNESS_SLA_MINUTES,
            "status_reason": "No governance scan has been recorded yet.",
            "detector_error_count": 0,
        }

    finished_at = last_scan.get("finished_at") or last_scan.get("started_at")
    scan_ts: Optional[datetime] = None
    if finished_at:
        try:
            scan_ts = datetime.fromisoformat(str(finished_at).replace("Z", "+00:00"))
            if scan_ts.tzinfo is None:
                scan_ts = scan_ts.replace(tzinfo=timezone.utc)
        except Exception:  # noqa: BLE001
            scan_ts = None
    age_minutes = ((now - scan_ts).total_seconds() / 60.0) if scan_ts else None
    detector_errors = list(last_scan.get("detector_errors") or [])
    if detector_errors:
        return {
            "state": "SCAN_FAILED",
            "confidence": "LOW",
            "scan_execution_health": "FAILED",
            "last_scan_at": scan_ts.isoformat() if scan_ts else None,
            "data_age_minutes": round(age_minutes, 1) if age_minutes is not None else None,
            "freshness_sla_minutes": _GOVERNANCE_FRESHNESS_SLA_MINUTES,
            "status_reason": f"{len(detector_errors)} detector(s) errored during the last scan.",
            "detector_error_count": len(detector_errors),
        }
    if age_minutes is None:
        return {
            "state": "UNKNOWN",
            "confidence": "UNKNOWN",
            "scan_execution_health": "UNKNOWN",
            "last_scan_at": None,
            "data_age_minutes": None,
            "freshness_sla_minutes": _GOVERNANCE_FRESHNESS_SLA_MINUTES,
            "status_reason": "Last scan timestamp is unavailable or unreadable.",
            "detector_error_count": 0,
        }
    if age_minutes <= _GOVERNANCE_FRESHNESS_SLA_MINUTES:
        state = "CURRENT"
        confidence = "HIGH"
        reason = "Governance scan freshness is within the current SLA."
    elif age_minutes <= _GOVERNANCE_FRESHNESS_SLA_MINUTES * 3:
        state = "AGING"
        confidence = "MEDIUM"
        reason = "Governance scan is older than SLA but still within the aging buffer."
    else:
        state = "STALE"
        confidence = "STALE"
        reason = "Governance findings are older than the current freshness SLA."
    return {
        "state": state,
        "confidence": confidence,
        "scan_execution_health": "OK",
        "last_scan_at": scan_ts.isoformat(),
        "data_age_minutes": round(age_minutes, 1),
        "freshness_sla_minutes": _GOVERNANCE_FRESHNESS_SLA_MINUTES,
        "status_reason": reason,
        "detector_error_count": 0,
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
    q = apply_synthetic_hr_exclusion({"deleted_at": None, "is_active": {"$ne": False}})
    cursor = db.employees.find(
        q, {"_id": 0, "id": 1, "name": 1, "position": 1, "is_field": 1, "trade": 1, "crew": 1, "role": 1},
    ).limit(2000)
    async for emp in cursor:
        name = (emp.get("name") or "").strip()
        if not name:
            continue
        if is_synthetic_hr(emp):
            continue
        applicability = _employee_ppe_applicability(emp)
        if not applicability["requires_ppe"]:
            continue
        if name.lower() in names_with_ppe:
            continue
        out.append({
            "rule_id": "PPE_MISSING",
            "entity_kind": "employee",
            "entity_id": emp.get("id") or name,
            "entity_name": name,
            "description": f"{name} is active but has zero PPE issuance records on file.",
            "source": {
                "position": emp.get("position") or "",
                "trade": emp.get("trade") or "",
                "crew": emp.get("crew") or "",
                "role": emp.get("role") or "",
                "is_field": emp.get("is_field"),
                "applicability_reason": applicability["reason"],
            },
        })
    return out


_OFFICE_PPE_EXEMPT_RE = re.compile(r"\b(accounting|payroll|hr|human resources|office|admin|clerk|reception)\b", re.I)


def _employee_ppe_applicability(emp: Dict[str, Any]) -> Dict[str, Any]:
    if emp.get("is_field") is True:
        return {"requires_ppe": True, "reason": "explicit_is_field"}

    signals = {
        "trade": str(emp.get("trade") or "").strip(),
        "crew": str(emp.get("crew") or "").strip(),
        "role": str(emp.get("role") or "").strip(),
        "position": str(emp.get("position") or "").strip(),
    }
    values = [v for v in signals.values() if v]
    if not values:
        return {"requires_ppe": False, "reason": "missing_field_applicability_evidence"}
    if any(_OFFICE_PPE_EXEMPT_RE.search(v) for v in values):
        return {"requires_ppe": False, "reason": "office_or_admin_role"}
    if signals["trade"]:
        return {"requires_ppe": True, "reason": "trade_signal"}
    if signals["crew"]:
        return {"requires_ppe": True, "reason": "crew_signal"}
    if signals["role"]:
        return {"requires_ppe": True, "reason": "role_signal"}
    if signals["position"]:
        return {"requires_ppe": True, "reason": "position_signal"}
    return {"requires_ppe": False, "reason": "missing_field_applicability_evidence"}


async def _detect_capa_overdue(db) -> List[Dict[str, Any]]:
    """CAPA_OVERDUE — open CAPA where due_date < today."""
    today = _today_iso()
    out: List[Dict[str, Any]] = []
    cursor = db.corrective_actions.find(
        apply_synthetic_corrective_action_exclusion({
            "due_date": {"$gt": "", "$lt": today},
            "status": {"$nin": ["closed", "completed", "verified", "resolved"]},
        }),
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
        open_capa_count = await db.corrective_actions.count_documents(
            apply_synthetic_corrective_action_exclusion({
                "incident_id": inc_pk,
                "status": {"$nin": ["closed", "completed", "verified", "resolved"]},
            })
        )
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


# ---------------------------------------------------------------------------
# iter360 — Daily Report crew linkage scan (nested array variant).
# Extends the iter355 linkage detector to scan daily_reports.masci_crews[].
# Reuses the EMP_LINK_* rule ids so findings flow into the same
# acknowledge/resolve/backfill UX without a new finding category.
# ---------------------------------------------------------------------------

async def _detect_daily_report_crew_linkage(db) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []

    # Active employee name index (same shape as _detect_employee_linkage).
    name_index: Dict[str, List[Dict[str, Any]]] = {}
    async for emp in db.employees.find(
        apply_synthetic_hr_exclusion({"deleted_at": None, "is_active": {"$ne": False}}),
        {"_id": 0, "id": 1, "name": 1},
    ).limit(5000):
        n = _norm_name(emp.get("name"))
        if n:
            name_index.setdefault(n, []).append(emp)

    # Aggregate per-name evidence across daily_reports.masci_crews[].
    # masci_crews stores {name, trade, hours, ..., employee_id (iter360)}.
    name_evidence: Dict[str, Dict[str, Any]] = {}
    async for dr in db.daily_reports.find(
        apply_synthetic_dr_exclusion({"masci_crews": {"$exists": True, "$ne": []}}),
        {"_id": 0, "id": 1, "masci_crews": 1, "report_date": 1},
    ).limit(2000):
        for row in (dr.get("masci_crews") or []):
            raw = (row.get("name") or "").strip()
            if not raw or _is_placeholder_identity(raw):
                continue
            n = _norm_name(raw)
            if not n:
                continue
            slot = name_evidence.setdefault(n, {
                "raw": raw, "count": 0, "missing_id_count": 0,
                "sample_reports": [],
            })
            slot["count"] += 1
            if not row.get("employee_id"):
                slot["missing_id_count"] += 1
            if len(slot["sample_reports"]) < 3:
                slot["sample_reports"].append({
                    "report_id": dr.get("id"),
                    "report_date": dr.get("report_date") or "",
                })

    # Classify exactly like _detect_employee_linkage so findings land
    # under the existing EMP_LINK_* rule ids.
    for n, ev in name_evidence.items():
        matches = name_index.get(n, [])
        raw = ev["raw"]
        total = ev["count"]

        if len(matches) == 0:
            out.append({
                "rule_id": "EMP_LINK_UNRESOLVABLE",
                "entity_kind": "linkage",
                "entity_id": f"unresolvable:dr:{n}",
                "entity_name": raw,
                "description": (
                    f"'{raw}' appears on {total} daily report crew row"
                    f"{'s' if total != 1 else ''} but does not match any "
                    f"active employee. Likely typo, archived person, or "
                    f"subcontractor not in the employee master."
                ),
                "source": {
                    "name_norm": n, "raw": raw, "record_count": total,
                    "collections": {"daily_reports": total},
                    "sample_reports": ev["sample_reports"],
                },
            })
        elif len(matches) > 1:
            ids = [m.get("id", "") for m in matches if m.get("id")]
            out.append({
                "rule_id": "EMP_LINK_AMBIGUOUS",
                "entity_kind": "linkage",
                "entity_id": f"ambiguous:dr:{n}",
                "entity_name": raw,
                "description": (
                    f"'{raw}' appears on {total} daily report crew row"
                    f"{'s' if total != 1 else ''} but matches "
                    f"{len(matches)} active employees. Operator must disambiguate."
                ),
                "source": {
                    "name_norm": n, "raw": raw,
                    "matched_employee_ids": ids,
                    "match_count": len(matches),
                    "collections": {"daily_reports": total},
                    "sample_reports": ev["sample_reports"],
                },
            })
        elif ev["missing_id_count"] > 0:
            emp = matches[0]
            out.append({
                "rule_id": "EMP_LINK_MISSING_ID",
                "entity_kind": "linkage",
                "entity_id": f"missing_id:dr:{n}",
                "entity_name": raw,
                "description": (
                    f"'{raw}' is uniquely linkable to {emp.get('name') or raw} "
                    f"(employee_id={emp.get('id')}) but {ev['missing_id_count']} "
                    f"daily report crew row{'s' if ev['missing_id_count'] != 1 else ''} "
                    f"still store the name without the id. The frontend now "
                    f"captures employee_id at entry — only historic rows should appear here."
                ),
                "source": {
                    "name_norm": n, "raw": raw,
                    "target_employee_id": emp.get("id"),
                    "missing_id_count": ev["missing_id_count"],
                    "collections": {"daily_reports": ev["missing_id_count"]},
                    "sample_reports": ev["sample_reports"],
                },
            })
    return out
#
# Free-text employee references across operational records (training,
# PPE issuance, CAPAs, incident person-involved, daily-report crew rosters)
# are the highest-risk identity-drift surface on the platform. This
# detector resolves every distinct employee name found across those
# collections against the active employee master, then classifies each
# distinct name as:
#   - linked         : matches exactly one active employee → optional backfill candidate
#   - ambiguous      : matches >1 active employees → operator must disambiguate
#   - unresolvable   : matches 0 active employees → likely typo / archived / stale
#
# One finding per problematic name (NOT per record) — keeps the dashboard
# focused on the identity gap, with the source dict enumerating affected
# collections + record counts so admins know what to clean up.
# ---------------------------------------------------------------------------

# Each entry: (collection, name_fields[], id_field, kind_label)
# id_field is the column we'd backfill when name → unique active employee.
LINKAGE_SOURCES = [
    ("safety_training_records", ["employee_name"],                                  "employee_id",  "training"),
    ("safety_equipment_issuances", ["employee_name"],                               "employee_id",  "ppe"),
    ("corrective_actions",      ["linked_employee_name", "employee_name"],          "employee_id",  "capa"),
    ("incidents",               ["person_name", "person_involved"],                 "employee_id",  "incident"),
]


def _norm_name(s: Any) -> str:
    if not isinstance(s, str):
        return ""
    return " ".join(s.strip().lower().split())


def _is_placeholder_identity(v: Any) -> bool:
    norm = _norm_name(v)
    if not norm:
        return True
    compact = norm.replace(" ", "")
    if len(compact) < 2:
        return True
    return norm in {"n/a", "na", "unknown", "none", "employee", "tbd"}


async def _detect_employee_linkage(db) -> List[Dict[str, Any]]:
    """EMP_LINK_UNRESOLVABLE · EMP_LINK_AMBIGUOUS · EMP_LINK_MISSING_ID.

    Walks the linkage sources above, builds an in-memory name → {collection: count}
    map, then classifies each name against the active-employee master.
    """
    out: List[Dict[str, Any]] = []

    # Step 1 — build the active employee master index. We map normalized
    # name → list of employee documents (need the list so we can detect
    # ambiguous matches).
    name_index: Dict[str, List[Dict[str, Any]]] = {}
    async for emp in db.employees.find(
        apply_synthetic_hr_exclusion({"deleted_at": None, "is_active": {"$ne": False}}),
        {"_id": 0, "id": 1, "name": 1},
    ).limit(5000):
        n = _norm_name(emp.get("name"))
        if not n:
            continue
        name_index.setdefault(n, []).append(emp)

    # Step 2 — walk every linkage source and tally records per normalized name.
    # name_evidence: {norm_name: {"raw": "best raw spelling",
    #                              "collections": {"training": N, ...},
    #                              "missing_id_count": N}}
    name_evidence: Dict[str, Dict[str, Any]] = {}

    for coll_name, name_fields, id_field, kind in LINKAGE_SOURCES:
        # Project the fields we need + the id field for the missing-id signal.
        proj = {"_id": 0, id_field: 1}
        for f in name_fields:
            proj[f] = 1
        source_query: Dict[str, Any] = {}
        if coll_name == "incidents":
            source_query = apply_synthetic_incident_exclusion({})
        elif coll_name == "corrective_actions":
            source_query = apply_synthetic_corrective_action_exclusion({})
        async for doc in db[coll_name].find(source_query, proj).limit(20000):
            # Collect any name candidate from this doc (a record might have
            # multiple name fields like linked_employee_name + employee_name).
            raw_candidates: List[str] = []
            for f in name_fields:
                v = doc.get(f)
                if isinstance(v, str) and v.strip():
                    raw_candidates.append(v.strip())
            if not raw_candidates:
                continue
            id_present = bool(doc.get(id_field))
            # Use the first non-empty candidate as the canonical raw.
            raw = raw_candidates[0]
            if _is_placeholder_identity(raw):
                continue
            n = _norm_name(raw)
            if not n:
                continue
            slot = name_evidence.setdefault(n, {
                "raw": raw, "collections": {}, "missing_id_count": 0,
            })
            slot["collections"][kind] = slot["collections"].get(kind, 0) + 1
            if not id_present:
                slot["missing_id_count"] += 1

    # Step 3 — classify each distinct name found across operational records.
    for n, ev in name_evidence.items():
        matches = name_index.get(n, [])
        raw = ev["raw"]
        total_records = sum(ev["collections"].values())
        coll_summary = ", ".join(
            f"{k}={v}" for k, v in sorted(ev["collections"].items())
        )

        if len(matches) == 0:
            out.append({
                "rule_id": "EMP_LINK_UNRESOLVABLE",
                "entity_kind": "linkage",
                "entity_id": f"unresolvable:{n}",
                "entity_name": raw,
                "description": (
                    f"'{raw}' appears on {total_records} operational record"
                    f"{'s' if total_records != 1 else ''} ({coll_summary}) but does "
                    f"not match any active employee. Likely typo, archived person, "
                    f"or subcontractor not in the employee master."
                ),
                "source": {
                    "name_norm": n, "raw": raw,
                    "collections": ev["collections"],
                    "record_count": total_records,
                },
            })
        elif len(matches) > 1:
            ids = [m.get("id", "") for m in matches if m.get("id")]
            out.append({
                "rule_id": "EMP_LINK_AMBIGUOUS",
                "entity_kind": "linkage",
                "entity_id": f"ambiguous:{n}",
                "entity_name": raw,
                "description": (
                    f"'{raw}' appears on {total_records} record"
                    f"{'s' if total_records != 1 else ''} ({coll_summary}) but "
                    f"matches {len(matches)} active employees. Cannot safely "
                    f"backfill — operator must disambiguate."
                ),
                "source": {
                    "name_norm": n, "raw": raw,
                    "matched_employee_ids": ids,
                    "match_count": len(matches),
                    "collections": ev["collections"],
                    "record_count": total_records,
                },
            })
        else:
            # Unique linkable name. Only flag if at least one record is
            # missing its employee_id — those are the backfill candidates.
            if ev["missing_id_count"] > 0:
                emp = matches[0]
                out.append({
                    "rule_id": "EMP_LINK_MISSING_ID",
                    "entity_kind": "linkage",
                    "entity_id": f"missing_id:{n}",
                    "entity_name": raw,
                    "description": (
                        f"'{raw}' is uniquely linkable to {emp.get('name') or raw} "
                        f"(employee_id={emp.get('id')}) but {ev['missing_id_count']} "
                        f"record{'s' if ev['missing_id_count'] != 1 else ''} "
                        f"({coll_summary}) still store the name without the id. "
                        f"Backfillable via POST /api/admin/compliance/backfill-employee-links."
                    ),
                    "source": {
                        "name_norm": n, "raw": raw,
                        "target_employee_id": emp.get("id"),
                        "missing_id_count": ev["missing_id_count"],
                        "collections": ev["collections"],
                    },
                })
    return out


async def _backfill_employee_links(db, dry_run: bool = True) -> Dict[str, Any]:
    """Resolve every uniquely-linkable employee name on operational records
    and set the employee_id column where it is missing/empty. Returns
    per-collection update counts.

    Safe by default — dry_run=True returns the would-be counts without
    mutating. Setting dry_run=False mutates the records.
    """
    # Re-resolve the active employee master inline (we cannot trust the
    # detector having run recently — backfill must be a stand-alone call).
    name_index: Dict[str, str] = {}
    dup_names: set = set()
    async for emp in db.employees.find(
        apply_synthetic_hr_exclusion({"deleted_at": None, "is_active": {"$ne": False}}),
        {"_id": 0, "id": 1, "name": 1},
    ).limit(5000):
        n = _norm_name(emp.get("name"))
        emp_id = emp.get("id")
        if not (n and emp_id):
            continue
        if n in name_index and name_index[n] != emp_id:
            dup_names.add(n)
        name_index[n] = emp_id
    # Drop ambiguous names so we never mis-link them.
    for n in dup_names:
        name_index.pop(n, None)

    per_collection: Dict[str, Dict[str, int]] = {}

    dr_scanned = 0
    dr_backfilled = 0
    dr_skipped_no_match = 0
    dr_skipped_ambiguous = 0
    dr_cursor = db.daily_reports.find(
        apply_synthetic_dr_exclusion({"masci_crews": {"$exists": True, "$ne": []}}),
        {"_id": 0, "id": 1, "masci_crews": 1},
    ).limit(20000)
    async for dr in dr_cursor:
        dr_scanned += 1
        rows = list(dr.get("masci_crews") or [])
        if not rows:
            continue
        changed = False
        for row in rows:
            if not isinstance(row, dict) or row.get("employee_id"):
                continue
            raw = (row.get("name") or "").strip()
            if not raw or _is_placeholder_identity(raw):
                continue
            n = _norm_name(raw)
            target = name_index.get(n)
            if not target:
                if n in dup_names:
                    dr_skipped_ambiguous += 1
                else:
                    dr_skipped_no_match += 1
                continue
            dr_backfilled += 1
            if not dry_run:
                row["employee_id"] = target
                row["linkage_backfilled_at"] = _now_iso()
                changed = True
        if changed and not dry_run and dr.get("id"):
            await db.daily_reports.update_one(
                {"id": dr.get("id")},
                {"$set": {"masci_crews": rows, "linkage_backfilled_at": _now_iso()}},
            )
    per_collection["daily_reports"] = {
        "scanned": dr_scanned,
        "backfilled": dr_backfilled,
        "skipped_no_match": dr_skipped_no_match,
        "skipped_ambiguous": dr_skipped_ambiguous,
    }

    for coll_name, name_fields, id_field, _kind in LINKAGE_SOURCES:
        scanned = 0
        backfilled = 0
        skipped_no_match = 0
        skipped_ambiguous = 0
        proj = {"_id": 0, "id": 1, id_field: 1}
        for f in name_fields:
            proj[f] = 1
        source_query: Dict[str, Any] = {}
        if coll_name == "incidents":
            source_query = apply_synthetic_incident_exclusion({})
        elif coll_name == "corrective_actions":
            source_query = apply_synthetic_corrective_action_exclusion({})
        cursor = db[coll_name].find(source_query, proj).limit(20000)
        async for doc in cursor:
            scanned += 1
            if doc.get(id_field):
                continue  # already linked
            # Pick the first non-empty name we find.
            name_raw = ""
            for f in name_fields:
                v = doc.get(f)
                if isinstance(v, str) and v.strip():
                    name_raw = v.strip()
                    break
            if not name_raw or _is_placeholder_identity(name_raw):
                continue
            n = _norm_name(name_raw)
            target = name_index.get(n)
            if not target:
                # Could be unresolvable or ambiguous.
                if n in dup_names:
                    skipped_ambiguous += 1
                else:
                    skipped_no_match += 1
                continue
            doc_pk = doc.get("id")
            if not doc_pk:
                continue
            if not dry_run:
                await db[coll_name].update_one(
                    {"id": doc_pk},
                    {"$set": {id_field: target,
                              "linkage_backfilled_at": _now_iso()}},
                )
            backfilled += 1
        per_collection[coll_name] = {
            "scanned": scanned, "backfilled": backfilled,
            "skipped_no_match": skipped_no_match,
            "skipped_ambiguous": skipped_ambiguous,
        }

    total_backfilled = sum(
        v["backfilled"] for v in per_collection.values()
    )
    return {
        "ok": True,
        "dry_run": dry_run,
        "total_backfilled": total_backfilled,
        "active_unique_names": len(name_index),
        "ambiguous_names_skipped": len(dup_names),
        "per_collection": per_collection,
    }


async def _build_employee_link_review_queue(db, materialize: bool = False) -> Dict[str, Any]:
    findings = await _detect_employee_linkage(db)
    candidates: List[Dict[str, Any]] = []
    stored = 0
    for finding in findings:
        if finding.get("rule_id") != "EMP_LINK_UNRESOLVABLE":
            continue
        source = finding.get("source") or {}
        item = {
            "queue_type": "employee_link_ambiguity",
            "queue_key": str(finding.get("entity_id") or ""),
            "entity_name": finding.get("entity_name"),
            "name_norm": source.get("name_norm"),
            "matched_employee_ids": list(source.get("matched_employee_ids") or []),
            "match_count": int(source.get("match_count") or 0),
            "collections": source.get("collections") or {},
            "record_count": int(source.get("record_count") or 0),
            "status": "PENDING_REVIEW",
            "generated_at": _now_iso(),
            "resolution_policy": "operator_must_disambiguate",
        }
        candidates.append(item)
        if materialize:
            await db["employee_link_review_queue"].update_one(
                {"queue_key": item["queue_key"]},
                {"$set": item},
                upsert=True,
            )
            stored += 1
    return {
        "ok": True,
        "materialized": materialize,
        "candidate_count": len(candidates),
        "stored_count": stored,
        "candidates": candidates[:100],
        "queue_collection": "employee_link_review_queue",
    }


# ---------------------------------------------------------------------------
# iter356 — Incident → CAPA → Closeout Lifecycle Enforcement (Phase 2 P0).
#
# Three rules that surface lifecycle continuity breaks:
#  - INC_NEEDS_CAPA           severe incident (High / Critical / OSHA Recordable)
#                             with zero CAPAs linked back.
#  - CAPA_AWAITING_VERIFICATION CAPA sitting in 'Pending Review' for >7 days
#                             (operator forgot to verify + close).
#  - CAPA_NO_OWNER            open/in-progress CAPA with no assigned_to_name.
#
# Together with the existing INC_CLOSED_CAPA_OPEN + CAPA_OVERDUE rules, these
# close the silent-failure loops on the incident → corrective-action chain.
# ---------------------------------------------------------------------------

SEVERE_INCIDENT_SEVERITIES = {"high", "critical", "severe"}


def _incident_severity_is_severe(inc: Dict[str, Any]) -> bool:
    sev = str(inc.get("severity") or "").strip().lower()
    if sev in SEVERE_INCIDENT_SEVERITIES:
        return True
    rec = inc.get("osha_recordable")
    if isinstance(rec, bool):
        return rec
    if isinstance(rec, str) and rec.strip().lower() in {"yes", "true", "1"}:
        return True
    return False


async def _detect_incident_lifecycle(db) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    today = _today_iso()

    # Rule 1: INC_NEEDS_CAPA — severe incidents w/ zero linked CAPAs.
    cursor = db.incidents.find(
        apply_synthetic_incident_exclusion({}),
        {"_id": 0, "id": 1, "description": 1, "severity": 1,
         "osha_recordable": 1, "incident_date": 1, "date_occurred": 1,
         "person_name": 1, "person_involved": 1, "project_name": 1,
         "status": 1},
    ).limit(2000)
    async for inc in cursor:
        if not _incident_severity_is_severe(inc):
            continue
        inc_pk = inc.get("id")
        if not inc_pk:
            continue
        linked = await db.corrective_actions.count_documents(apply_synthetic_corrective_action_exclusion({
            "$or": [
                {"incident_id": inc_pk},
                {"source_kind": "incident", "source_id": inc_pk},
                {"related_entities": {"$elemMatch": {"kind": "incident", "id": inc_pk}}},
            ],
        }))
        if linked > 0:
            continue
        person = inc.get("person_name") or inc.get("person_involved") or "(unknown)"
        when = inc.get("incident_date") or inc.get("date_occurred") or ""
        out.append({
            "rule_id": "INC_NEEDS_CAPA",
            "entity_kind": "incident",
            "entity_id": inc_pk,
            "entity_name": (inc.get("description") or f"Incident {inc_pk[:8]}")[:120],
            "description": (
                f"Severe incident on {when or 'unknown date'} (severity="
                f"{inc.get('severity') or 'n/a'}, recordable="
                f"{inc.get('osha_recordable') or 'n/a'}, person={person}) "
                f"has no linked corrective action. Lifecycle rule: every "
                f"High / Critical / OSHA-recordable incident must spawn a "
                f"CAPA before closeout."
            ),
            "source": {
                "severity": inc.get("severity"),
                "osha_recordable": inc.get("osha_recordable"),
                "incident_date": when,
                "person": person,
                "project_name": inc.get("project_name"),
                "incident_status": inc.get("status"),
            },
        })

    # Rule 2: CAPA_AWAITING_VERIFICATION — Pending Review > 7 days.
    cutoff_7d = (datetime.now(timezone.utc) - timedelta(days=7)).isoformat()
    cursor = db.corrective_actions.find(
        apply_synthetic_corrective_action_exclusion({
            "status": {"$in": ["Pending Review", "pending_review", "pending review"]},
            "updated_at": {"$lt": cutoff_7d},
        }),
        {"_id": 0},
    ).limit(500)
    async for capa in cursor:
        capa_id = capa.get("id") or ""
        title = capa.get("title") or capa.get("description") or "(untitled CAPA)"
        owner = capa.get("assigned_to_name") or capa.get("owner") or "(unassigned)"
        stuck_days = "—"
        try:
            ts = capa.get("updated_at") or capa.get("created_at")
            if ts:
                stuck = datetime.now(timezone.utc) - datetime.fromisoformat(
                    str(ts).replace("Z", "+00:00")
                )
                stuck_days = str(int(stuck.total_seconds() / 86400))
        except Exception:
            pass
        out.append({
            "rule_id": "CAPA_AWAITING_VERIFICATION",
            "entity_kind": "capa",
            "entity_id": capa_id,
            "entity_name": title[:120],
            "description": (
                f"CAPA '{title[:80]}' has been in 'Pending Review' for "
                f"{stuck_days} day(s). Owner: {owner}. Lifecycle rule: a "
                f"second reviewer must Verify the work before status moves "
                f"to Closed."
            ),
            "source": {
                "status": capa.get("status"),
                "updated_at": capa.get("updated_at"),
                "owner": owner,
                "project_number": capa.get("project_number"),
            },
        })

    # Rule 3: CAPA_NO_OWNER — open/in-progress with no assigned_to_name.
    cursor = db.corrective_actions.find(
        apply_synthetic_corrective_action_exclusion({
            "status": {"$nin": ["Closed", "closed", "Verified", "verified", "completed", "resolved"]},
            "$or": [{"assigned_to_name": {"$in": [None, ""]}},
                    {"assigned_to_name": {"$exists": False}}],
        }),
        {"_id": 0},
    ).limit(500)
    async for capa in cursor:
        capa_id = capa.get("id") or ""
        title = capa.get("title") or capa.get("description") or "(untitled CAPA)"
        out.append({
            "rule_id": "CAPA_NO_OWNER",
            "entity_kind": "capa",
            "entity_id": capa_id,
            "entity_name": title[:120],
            "description": (
                f"CAPA '{title[:80]}' is {capa.get('status') or 'open'} but "
                f"has no assigned owner. Lifecycle rule: every active CAPA "
                f"must have a responsible person before Pending Review."
            ),
            "source": {
                "status": capa.get("status"),
                "due_date": capa.get("due_date"),
                "priority": capa.get("priority"),
                "project_number": capa.get("project_number"),
            },
        })
    _ = today  # unused but reserved
    return out


DETECTORS = [
    _detect_driver_expirations,
    _detect_training_expired,
    _detect_ppe_missing,
    _detect_capa_overdue,
    _detect_incident_closed_capa_open,
    _detect_employee_anomalies,
    _detect_employee_linkage,
    _detect_daily_report_crew_linkage,
    _detect_incident_lifecycle,
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


class BackfillPayload(BaseModel):
    dry_run: bool = Field(default=True)


class PpeIssuePayload(BaseModel):
    dry_run: bool = Field(default=True)
    issued_by: str = Field(default="System Governance Repair", max_length=200)
    default_items: List[str] = Field(default_factory=lambda: ["Hard Hat", "Safety Vest", "Safety Glasses", "Gloves"])


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

    @router.post("/api/admin/compliance/backfill-employee-links",
                 dependencies=[Depends(require_admin_strict)])
    async def backfill_employee_links(body: BackfillPayload):
        """iter355 · Operator ↔ Employee Linkage Enforcement.

        Sets employee_id on every operational record whose employee_name
        uniquely resolves to one active employee. Idempotent — records
        already carrying employee_id are skipped. Ambiguous names are
        never touched. dry_run=True (default) returns the would-be counts
        without mutating.
        """
        return await _backfill_employee_links(db, dry_run=bool(body.dry_run))

    @router.post("/api/admin/compliance/employee-link-review-queue",
                 dependencies=[Depends(require_admin_strict)])
    async def employee_link_review_queue(body: BackfillPayload):
        return await _build_employee_link_review_queue(db, materialize=not bool(body.dry_run))

    @router.post("/api/admin/compliance/issue-missing-ppe",
                 dependencies=[Depends(require_admin_strict)])
    async def issue_missing_ppe(body: PpeIssuePayload):
        return await _issue_missing_ppe_records(
            db,
            dry_run=bool(body.dry_run),
            issued_by=(body.issued_by or "System Governance Repair").strip() or "System Governance Repair",
            default_items=[str(x).strip() for x in (body.default_items or []) if str(x).strip()],
        )

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

    @router.get("/api/admin/compliance/findings.csv",
                dependencies=[Depends(require_admin_strict)])
    async def list_findings_csv(
        status: Optional[str] = Query(default=None),
        severity: Optional[str] = Query(default=None),
        rule_id: Optional[str] = Query(default=None),
        category: Optional[str] = Query(default=None),
        entity_kind: Optional[str] = Query(default=None),
        q: Optional[str] = Query(default=None),
        limit: int = Query(default=2000, ge=1, le=10000),
    ):
        """Phase 5 · W8 · CSV export of compliance findings. Same
        filter semantics as the JSON list; defaults to open + acknowledged."""
        import csv as _csv  # noqa: PLC0415
        import io as _io    # noqa: PLC0415
        flt: Dict[str, Any] = {}
        if status:
            flt["status"] = status
        else:
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
        rows: List[Dict[str, Any]] = []
        async for row in db[COLLECTION].find(flt, {"_id": 0}).limit(limit):
            rows.append(row)
        rows.sort(key=lambda r: SEVERITY_RANK.get(r.get("severity", "info"), 99))

        buf = _io.StringIO()
        fields = [
            "rule_id", "severity", "category", "status",
            "entity_kind", "entity_id", "entity_name",
            "description", "first_detected_at", "last_detected_at",
            "acknowledged_at", "acknowledged_by",
            "resolved_at", "resolved_by",
        ]
        writer = _csv.DictWriter(buf, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        for r in rows:
            writer.writerow({f: (r.get(f) or "") for f in fields})
        return _FastAPIResponse(
            content=buf.getvalue(),
            media_type="text/csv; charset=utf-8",
            headers={
                "Content-Disposition": 'attachment; filename="compliance_findings.csv"',
                "Cache-Control": "private, no-store",
            },
        )

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
        now = datetime.now(timezone.utc)
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
        freshness = _governance_freshness(last_scan, now=now)

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
            "freshness": freshness,
            "kpi_metadata": {
                "kpi_name": "Governance Summary",
                "business_definition": "Persisted governance findings inventory plus explicit scan freshness and execution confidence.",
                "source_of_truth": ["compliance_findings", "compliance_scans"],
                "api_endpoint": "/api/admin/governance/summary",
                "formula": {
                    "finding_inventory": "open + acknowledged findings grouped by severity and rule",
                    "freshness_sla_minutes": _GOVERNANCE_FRESHNESS_SLA_MINUTES,
                },
                "confidence": freshness.get("confidence"),
                "status_reason": freshness.get("status_reason"),
                "drilldown_source": "/admin/governance/legacy-health",
                "owner": "governance-trust",
            },
            "rule_catalog": RULE_CATALOG,
            "recommended_repairs": {
                "employee_link_backfill_endpoint": "/api/admin/compliance/backfill-employee-links",
                "employee_link_review_queue_endpoint": "/api/admin/compliance/employee-link-review-queue",
                "ppe_issue_endpoint": "/api/admin/compliance/issue-missing-ppe",
            },
        }

    # ════════════════════════════════════════════════════════════════
    # iter379 · Operational Inventory & Guidance Telemetry
    # ──────────────────────────────────────────────────────────────
    # Extracted from server.py L652-L721 (operational inventory routes +
    # guidance search-misses). All admin-strict. Pure registry inspection
    # for the inventory routes; DB read + aggregation for search-misses.
    # ════════════════════════════════════════════════════════════════

    @router.get("/api/admin/operational-inventory",
                dependencies=[Depends(require_admin_strict)])
    async def admin_operational_inventory():
        """Full operational inventory snapshot: portals × user types ×
        public routes × workflows × translation readiness × drift.

        Read-only; pure registry inspection; never touches DB."""
        from governance.inventory import compute_full_inventory  # noqa: PLC0415
        return compute_full_inventory()

    @router.get("/api/admin/operational-inventory/portals",
                dependencies=[Depends(require_admin_strict)])
    async def admin_operational_inventory_portals():
        """Portal-only matrix (10-field coverage per portal). Lightweight
        endpoint for the 'Portals' tab on the dashboard."""
        from governance.inventory import compute_portal_matrix  # noqa: PLC0415
        return {"portals": compute_portal_matrix()}

    @router.get("/api/admin/operational-inventory/translation",
                dependencies=[Depends(require_admin_strict)])
    async def admin_operational_inventory_translation():
        """Translation-readiness snapshot (system-wide aggregates + per
        section + per scope). Tracks Pass 3 progress as body_es lands."""
        from governance.inventory import compute_translation_readiness  # noqa: PLC0415
        return compute_translation_readiness()

    @router.get("/api/admin/operational-inventory/drift",
                dependencies=[Depends(require_admin_strict)])
    async def admin_operational_inventory_drift():
        """Drift signal: portals/articles/routes/workflows missing required
        coverage fields. Severity-tagged for triage."""
        from governance.inventory import compute_drift  # noqa: PLC0415
        return compute_drift()

    @router.get("/api/admin/guidance/search-misses",
                dependencies=[Depends(require_admin_strict)])
    async def admin_guidance_search_misses(limit: int = 100):
        """List recent zero-result guidance searches. Operational gap-intel.

        Returns the most-recent {limit} miss rows, plus an aggregated count
        of distinct queries (case-folded) so the highest-demand gaps surface
        first.
        """
        safe_limit = max(1, min(int(limit or 100), 500))
        cursor = db.guidance_search_misses.find(
            {}, {"_id": 0}
        ).sort("ts", -1).limit(safe_limit)
        rows = await cursor.to_list(safe_limit)
        # Aggregate by normalized query
        agg: dict = {}
        for r in rows:
            key = (r.get("query") or "").strip().lower()
            if not key:
                continue
            agg[key] = agg.get(key, 0) + 1
        top = sorted(
            ({"query": k, "count": v} for k, v in agg.items()),
            key=lambda x: -x["count"],
        )
        return {"recent": rows, "top": top[:50], "count": len(rows)}

    return router


async def _issue_missing_ppe_records(
    db,
    *,
    dry_run: bool = True,
    issued_by: str,
    default_items: Optional[List[str]] = None,
) -> Dict[str, Any]:
    defaults = [item for item in (default_items or []) if item]
    names_with_ppe: Set[str] = set()
    async for row in db.safety_equipment_issuances.find({}, {"_id": 0, "employee_name": 1}):
        n = (row.get("employee_name") or "").strip()
        if n:
            names_with_ppe.add(n.lower())

    missing: List[Dict[str, Any]] = []
    async for emp in db.employees.find(
        apply_synthetic_hr_exclusion({"deleted_at": None, "is_active": {"$ne": False}}),
        {"_id": 0, "id": 1, "name": 1, "employee_id": 1, "position": 1, "is_field": 1, "trade": 1, "crew": 1, "role": 1},
    ).limit(5000):
        name = (emp.get("name") or "").strip()
        if not name:
            continue
        if is_synthetic_hr(emp):
            continue
        if not _employee_ppe_applicability(emp)["requires_ppe"]:
            continue
        if name.lower() in names_with_ppe:
            continue
        missing.append(emp)

    preview = []
    created = 0
    for idx, emp in enumerate(missing, start=1):
        record = {
            "id": f"gov-ppe-{(emp.get('id') or str(idx)).replace(' ', '-').lower()}",
            "employee_id": emp.get("id"),
            "employee_name": emp.get("name"),
            "issued_date": _today_iso(),
            "issued_at": _now_iso(),
            "created_at": _now_iso(),
            "updated_at": _now_iso(),
            "issued_by": issued_by,
            "status": "issued",
            "project_name": "Governance PPE Catch-up",
            "project_number": "GOV-PPE-CATCHUP",
            "items": [
                {"name": item, "qty": 1, "condition": "new", "unit_cost": 0.0, "total_cost": 0.0}
                for item in defaults
            ],
            "total_value": 0.0,
            "acknowledgment": True,
            "governance_repair": True,
        }
        preview.append({
            "employee_id": emp.get("id"),
            "employee_name": emp.get("name"),
            "issuance_id": record["id"],
            "items": defaults,
        })
        if not dry_run:
            await db.safety_equipment_issuances.update_one(
                {"id": record["id"]},
                {"$setOnInsert": record},
                upsert=True,
            )
            created += 1

    return {
        "ok": True,
        "dry_run": dry_run,
        "missing_employee_count": len(missing),
        "created_count": 0 if dry_run else created,
        "preview": preview[:100],
        "default_items": defaults,
    }


__all__ = ["build_governance_router", "RULE_CATALOG", "_run_scan", "COLLECTION"]
