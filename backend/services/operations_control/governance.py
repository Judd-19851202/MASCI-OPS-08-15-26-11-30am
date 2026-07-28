"""Governance repair operations for the Operations Control Center."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List

from routes.governance import _backfill_employee_links, _issue_missing_ppe_records

from .registry import Operation, OperationCategory, RiskLevel


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _compact_per_collection(per_collection: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for name, metrics in (per_collection or {}).items():
        rows.append({
            "collection": name,
            "scanned": int(metrics.get("scanned") or 0),
            "backfilled": int(metrics.get("backfilled") or 0),
            "skipped_no_match": int(metrics.get("skipped_no_match") or 0),
            "skipped_ambiguous": int(metrics.get("skipped_ambiguous") or 0),
        })
    rows.sort(key=lambda row: (row["backfilled"], row["collection"]), reverse=True)
    return rows


async def _employee_link_backfill_status(payload: Dict[str, Any]) -> Dict[str, Any]:
    db = payload["_db"]
    result = await _backfill_employee_links(db, dry_run=True)
    total = int(result.get("total_backfilled") or 0)
    status = "warning" if total > 0 else "healthy"
    summary = (
        f"{total} operational record(s) can be backfilled with authoritative employee_id values."
        if total > 0
        else "No uniquely linkable records are missing employee_id values."
    )
    return {
        "status": status,
        "summary": summary,
        "dry_run_ready": True,
        "candidate_count": total,
        "ambiguous_names_skipped": int(result.get("ambiguous_names_skipped") or 0),
        "per_collection": _compact_per_collection(result.get("per_collection") or {}),
        "generated_at": _now_iso(),
    }


async def _employee_link_backfill_dry_run(payload: Dict[str, Any]) -> Dict[str, Any]:
    db = payload["_db"]
    result = await _backfill_employee_links(db, dry_run=True)
    total = int(result.get("total_backfilled") or 0)
    return {
        "status": "dry_run_ready",
        "summary": (
            f"Would backfill {total} missing employee link(s) across operational records."
            if total > 0
            else "No backfillable employee links found."
        ),
        "candidate_count": total,
        "ambiguous_names_skipped": int(result.get("ambiguous_names_skipped") or 0),
        "per_collection": _compact_per_collection(result.get("per_collection") or {}),
        "generated_at": _now_iso(),
    }


async def _employee_link_backfill_apply(payload: Dict[str, Any]) -> Dict[str, Any]:
    db = payload["_db"]
    result = await _backfill_employee_links(db, dry_run=False)
    total = int(result.get("total_backfilled") or 0)
    return {
        "status": "completed",
        "summary": (
            f"Backfilled {total} employee link(s) with canonical employee_id values."
            if total > 0
            else "No employee link changes were needed."
        ),
        "candidate_count": total,
        "ambiguous_names_skipped": int(result.get("ambiguous_names_skipped") or 0),
        "per_collection": _compact_per_collection(result.get("per_collection") or {}),
        "generated_at": _now_iso(),
    }


async def _ppe_issue_status(payload: Dict[str, Any]) -> Dict[str, Any]:
    db = payload["_db"]
    result = await _issue_missing_ppe_records(
        db,
        dry_run=True,
        issued_by="Operations Control Center",
        default_items=["Hard Hat", "Safety Vest", "Safety Glasses", "Gloves"],
    )
    count = int(result.get("missing_employee_count") or 0)
    status = "warning" if count > 0 else "healthy"
    summary = (
        f"{count} active field employee(s) are missing PPE issuance records."
        if count > 0
        else "All active field employees have at least one PPE issuance record."
    )
    return {
        "status": status,
        "summary": summary,
        "dry_run_ready": True,
        "candidate_count": count,
        "preview": list(result.get("preview") or [])[:10],
        "generated_at": _now_iso(),
    }


async def _ppe_issue_dry_run(payload: Dict[str, Any]) -> Dict[str, Any]:
    db = payload["_db"]
    default_items = [
        str(item).strip()
        for item in (payload.get("default_items") or ["Hard Hat", "Safety Vest", "Safety Glasses", "Gloves"])
        if str(item).strip()
    ]
    result = await _issue_missing_ppe_records(
        db,
        dry_run=True,
        issued_by=(payload.get("actor_email") or "Operations Control Center").strip() or "Operations Control Center",
        default_items=default_items,
    )
    count = int(result.get("missing_employee_count") or 0)
    return {
        "status": "dry_run_ready",
        "summary": (
            f"Would create default PPE issuance records for {count} employee(s)."
            if count > 0
            else "No missing PPE issuance records found."
        ),
        "candidate_count": count,
        "default_items": default_items,
        "preview": list(result.get("preview") or [])[:25],
        "generated_at": _now_iso(),
    }


async def _ppe_issue_apply(payload: Dict[str, Any]) -> Dict[str, Any]:
    db = payload["_db"]
    default_items = [
        str(item).strip()
        for item in (payload.get("default_items") or ["Hard Hat", "Safety Vest", "Safety Glasses", "Gloves"])
        if str(item).strip()
    ]
    result = await _issue_missing_ppe_records(
        db,
        dry_run=False,
        issued_by=(payload.get("actor_email") or "Operations Control Center").strip() or "Operations Control Center",
        default_items=default_items,
    )
    created = int(result.get("created_count") or 0)
    return {
        "status": "completed",
        "summary": (
            f"Created {created} PPE issuance record(s) for active field employees missing them."
            if created > 0
            else "No PPE issuance changes were required."
        ),
        "candidate_count": int(result.get("missing_employee_count") or 0),
        "created_count": created,
        "default_items": default_items,
        "preview": list(result.get("preview") or [])[:25],
        "generated_at": _now_iso(),
    }


def operations(_db) -> List[Operation]:
    return [
        Operation(
            id="governance.employee_link_backfill",
            title="Employee Link Backfill",
            description=(
                "Dry-run and apply canonical employee_id backfills for operational records that are "
                "uniquely linkable by employee_name."
            ),
            category=OperationCategory.GOVERNANCE,
            risk=RiskLevel.DATA_MIGRATION,
            status_fn=_employee_link_backfill_status,
            dry_run_fn=_employee_link_backfill_dry_run,
            apply_fn=_employee_link_backfill_apply,
            reads=["employees", "linked operational record collections"],
            writes=["employee_id on uniquely linkable operational records"],
            never_touches=["ambiguous employee names", "PPE issuance data", "R2 objects"],
            requires_dry_run=True,
        ),
        Operation(
            id="governance.issue_missing_ppe",
            title="Issue Missing PPE Records",
            description=(
                "Dry-run and apply default PPE issuance records for active field employees with no issuance on file."
            ),
            category=OperationCategory.GOVERNANCE,
            risk=RiskLevel.DATA_MIGRATION,
            status_fn=_ppe_issue_status,
            dry_run_fn=_ppe_issue_dry_run,
            apply_fn=_ppe_issue_apply,
            reads=["employees", "safety_equipment_issuances"],
            writes=["safety_equipment_issuances upserts"],
            never_touches=["existing PPE issuance rows", "employee master identity", "R2 objects"],
            requires_dry_run=True,
        ),
    ]