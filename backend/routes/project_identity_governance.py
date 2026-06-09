"""
project_identity_governance.py — PROJECT-IDENTITY-005

Detect potential project identity drift across the platform. NEVER mutate.

Doctrine:
  • jobs_master is authoritative.
  • Historical records are immutable.
  • All identity decisions belong to the human operator.
  • This module is detection + queue only.

The endpoints expose:

  POST  /api/admin/project-identity/scan      → run detector, upsert items
  GET   /api/admin/project-identity/queue     → list governance items
  POST  /api/admin/project-identity/queue/{id}/resolve
                                              → operator resolution
  GET   /api/admin/project-identity/metrics   → dashboard metrics
"""
from __future__ import annotations

import logging
import re
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


# ─── Read-time PN normalization ──────────────────────────────────────
# Whitespace + dash + casing only. Nothing else. No guessing.
# Returns a normalized form ready for EXACT matching against canonical.
def normalize_pn(pn: str) -> str:
    if not pn:
        return ""
    s = str(pn).strip().upper()
    # collapse any run of whitespace to single space
    s = re.sub(r"\s+", " ", s)
    # normalize " - " / " -" / "- " variants to consistent " - "
    s = re.sub(r"\s*-\s*", " - ", s)
    # strip outer space again
    return s.strip()


# Build the canonical lookup by normalized PN
def _build_canonical_index(jobs_master_rows: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for j in jobs_master_rows or []:
        pn = (j.get("project_number") or "").strip()
        if not pn:
            continue
        out[normalize_pn(pn)] = j
    return out


# Source collections to scan (every collection that carries project refs)
SCAN_COLLECTIONS: List[Dict[str, str]] = [
    {"name": "daily_reports",            "num": "project_number", "nm": "project_name", "label": "Daily Reports"},
    {"name": "job_photos",               "num": "project_number", "nm": "project_name", "label": "Job Photos"},
    {"name": "incidents",                "num": "project_number", "nm": "project_name", "label": "Incidents"},
    {"name": "inspections",              "num": "project_number", "nm": "project_name", "label": "Site Inspections"},
    {"name": "meetings",                 "num": "project_number", "nm": "project_name", "label": "Meetings"},
    {"name": "equipment_inspections",    "num": "project_number", "nm": "project_name", "label": "Equipment Pre-Op"},
    {"name": "qaqc_inspections",         "num": "project_number", "nm": "project_name", "label": "QA/QC"},
    {"name": "safety_equipment_issuances","num": "project_number","nm": "project_name", "label": "Safety Equipment Issuances"},
    {"name": "safety_equipment_trainings","num": "project_number","nm": "project_name", "label": "Safety Equipment Trainings"},
    {"name": "trench_excavations",       "num": "project_number", "nm": "project_name", "label": "Trench Excavations"},
    {"name": "trench_safety_deployments","num": "project_number","nm": "project_name", "label": "Trench Deployments"},
    {"name": "po_requests",              "num": "project_number", "nm": "project_name", "label": "PO Requests"},
    {"name": "operations_actions",       "num": "job_number",     "nm": "job_name",     "label": "Operations Actions"},
    {"name": "asset_assignments",        "num": "project_number", "nm": "project_name", "label": "Asset Assignments"},
    {"name": "corrective_actions",       "num": "project_number", "nm": "project_name", "label": "Corrective Actions"},
    {"name": "field_leadership_records", "num": "project_number", "nm": "project_name", "label": "Field Leadership"},
    {"name": "haul_cycles",              "num": "project_number", "nm": "project_name", "label": "Haul Cycles"},
    {"name": "jhas",                     "num": "project_number", "nm": "project_name", "label": "JHAs"},
    {"name": "jha_acknowledgements",     "num": "project_number", "nm": "project_name", "label": "JHA Acknowledgements"},
    {"name": "fire_extinguishers",       "num": "project_number", "nm": "project_name", "label": "Fire Extinguishers"},
    {"name": "job_hazard_files",         "num": "project_number", "nm": "project_name", "label": "JHA Files"},
    {"name": "operational_events",       "num": "project_number", "nm": "project_name", "label": "Operational Events"},
    {"name": "operational_locations",    "num": "project_number", "nm": "project_name", "label": "Operational Locations"},
    {"name": "field_submitter_bindings", "num": "project_number", "nm": "project_name", "label": "Field Submitter Bindings"},
    {"name": "dispatch_assignments",     "num": "project_number", "nm": "project_name", "label": "Dispatch Assignments"},
]


# ─── Conflict types ───────────────────────────────────────────────────
# A: PN matches a canonical row, name differs from canonical
# B: Name matches a canonical row exactly, PN differs from canonical
# C: PN does not exact-match canonical but normalizes to a canonical PN
# D: PN populated, not found in jobs_master (and no normalization match)
# E: Blank PN, non-blank name
# F: Blank name, non-blank PN (operational but anonymous)
def _key(conflict_type: str, submitted_pn: str, submitted_nm: str) -> str:
    return f"{conflict_type}|{(submitted_pn or '').strip().upper()}|{(submitted_nm or '').strip().lower()}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


async def _list_jobs_master(db) -> List[Dict[str, Any]]:
    cursor = db.jobs_master.find({"deleted_at": {"$in": [None, ""]}}, {"_id": 0})
    return await cursor.to_list(2000)


async def run_detection(db) -> Dict[str, Any]:
    """Scan every project-bearing collection. Detect and UPSERT
    governance items. NEVER mutates source records.

    Returns a summary dict with per-type counts.
    """
    jobs_master = await _list_jobs_master(db)
    # Canonical exact PN map (kept as supplied so we can compare *exactly*)
    canonical_by_pn = {(j.get("project_number") or "").strip(): j for j in jobs_master if (j.get("project_number") or "").strip()}
    # Canonical name map (case-insensitive) for Type B
    canonical_by_name = {}
    for j in jobs_master:
        nm = (j.get("project_name") or "").strip()
        if nm:
            canonical_by_name.setdefault(nm.upper(), j)
    # Canonical normalized index for Type C
    canonical_by_norm = _build_canonical_index(jobs_master)

    # Aggregate observations: (conflict_type, submitted_pn, submitted_nm) → {modules, count, last_seen}
    obs: Dict[str, Dict[str, Any]] = {}

    def _accumulate(conflict_type: str, sub_pn: str, sub_nm: str,
                    canonical_pn: Optional[str], canonical_nm: Optional[str],
                    module_label: str, ts: Optional[str] = None) -> None:
        k = _key(conflict_type, sub_pn, sub_nm)
        if k not in obs:
            obs[k] = {
                "key": k,
                "conflict_type": conflict_type,
                "submitted_project_number": sub_pn,
                "submitted_project_name": sub_nm,
                "suggested_canonical_number": canonical_pn,
                "suggested_canonical_name": canonical_nm,
                "source_modules": [],
                "record_count": 0,
                "last_seen": ts or _now_iso(),
            }
        item = obs[k]
        item["record_count"] += 1
        if module_label not in item["source_modules"]:
            item["source_modules"].append(module_label)
        if ts and ts > (item["last_seen"] or ""):
            item["last_seen"] = ts

    for cfg in SCAN_COLLECTIONS:
        col = cfg["name"]
        num_field, nm_field = cfg["num"], cfg["nm"]
        try:
            cursor = db[col].find(
                {},
                {num_field: 1, nm_field: 1, "created_at": 1, "updated_at": 1,
                 "report_date": 1, "incident_date": 1, "meeting_date": 1,
                 "inspection_date": 1, "_id": 0},
            )
        except Exception as e:  # noqa: BLE001
            logger.warning(f"project-identity scan: skipping {col}: {e}")
            continue

        async for r in cursor:
            sub_pn_raw = r.get(num_field) or ""
            sub_nm_raw = r.get(nm_field) or ""
            sub_pn = str(sub_pn_raw).strip()
            sub_nm = str(sub_nm_raw).strip()
            ts = (
                r.get("updated_at")
                or r.get("created_at")
                or r.get("report_date")
                or r.get("incident_date")
                or r.get("meeting_date")
                or r.get("inspection_date")
                or _now_iso()
            )
            if isinstance(ts, datetime):
                ts = ts.replace(microsecond=0).isoformat()
            ts = str(ts)[:32]

            # E · blank PN, non-blank name
            if not sub_pn and sub_nm:
                _accumulate("E", "", sub_nm, None, None, cfg["label"], ts)
                continue
            # F · blank name, non-blank PN
            if sub_pn and not sub_nm:
                canon = canonical_by_pn.get(sub_pn)
                _accumulate(
                    "F",
                    sub_pn,
                    "",
                    canon.get("project_number") if canon else None,
                    canon.get("project_name") if canon else None,
                    cfg["label"],
                    ts,
                )
                continue
            # Both blank → operational anonymous; skip (no actionable governance)
            if not sub_pn and not sub_nm:
                continue

            # PN present + name present
            canon_exact = canonical_by_pn.get(sub_pn)
            if canon_exact:
                # A · same PN, different name
                if (canon_exact.get("project_name") or "").strip().upper() != sub_nm.upper():
                    _accumulate(
                        "A",
                        sub_pn,
                        sub_nm,
                        canon_exact.get("project_number"),
                        canon_exact.get("project_name"),
                        cfg["label"],
                        ts,
                    )
                # else exact canonical · no conflict
                continue

            # C · PN does not exact-match but normalizes to a canonical PN
            norm = normalize_pn(sub_pn)
            canon_norm = canonical_by_norm.get(norm)
            if canon_norm:
                _accumulate(
                    "C",
                    sub_pn,
                    sub_nm,
                    canon_norm.get("project_number"),
                    canon_norm.get("project_name"),
                    cfg["label"],
                    ts,
                )
                continue

            # B · name matches a canonical row exactly (case-insensitive),
            # PN differs
            canon_by_nm = canonical_by_name.get(sub_nm.upper())
            if canon_by_nm:
                _accumulate(
                    "B",
                    sub_pn,
                    sub_nm,
                    canon_by_nm.get("project_number"),
                    canon_by_nm.get("project_name"),
                    cfg["label"],
                    ts,
                )
                continue

            # D · PN present, no canonical match (and no normalization match)
            _accumulate("D", sub_pn, sub_nm, None, None, cfg["label"], ts)

    # Upsert into governance queue. Preserve operator resolutions.
    upserts = 0
    for item in obs.values():
        existing = await db.project_identity_conflicts.find_one(
            {"key": item["key"]}, {"_id": 0}
        )
        doc = {
            **item,
            "first_detected": (existing or {}).get("first_detected") or _now_iso(),
            "status": (existing or {}).get("status") or "open",
            "resolved_by": (existing or {}).get("resolved_by"),
            "resolved_at": (existing or {}).get("resolved_at"),
            "resolution_note": (existing or {}).get("resolution_note"),
            "matched_jobs_master_id": (existing or {}).get("matched_jobs_master_id"),
        }
        await db.project_identity_conflicts.update_one(
            {"key": item["key"]},
            {"$set": doc},
            upsert=True,
        )
        upserts += 1

    # Summary counts by type
    by_type: Dict[str, int] = defaultdict(int)
    for it in obs.values():
        by_type[it["conflict_type"]] += 1

    return {
        "scanned_at": _now_iso(),
        "items_total": upserts,
        "by_type": dict(by_type),
        "canonical_projects": len(canonical_by_pn),
        "scanned_collections": [c["name"] for c in SCAN_COLLECTIONS],
    }


class ResolutionBody(BaseModel):
    action: str = Field(..., description="match | leave_unmatched | intentional | dismiss")
    matched_jobs_master_id: Optional[str] = None
    note: Optional[str] = None


def build_project_identity_router(db, require_admin) -> APIRouter:
    router = APIRouter(prefix="/api/admin/project-identity", tags=["project-identity"])

    @router.post("/scan", dependencies=[Depends(require_admin)])
    async def scan():
        try:
            await db.project_identity_conflicts.create_index("key", unique=True)
            await db.project_identity_conflicts.create_index("status")
            await db.project_identity_conflicts.create_index("conflict_type")
        except Exception as e:  # noqa: BLE001
            logger.warning(f"project_identity_conflicts indexes: {e}")
        return await run_detection(db)

    @router.get("/queue", dependencies=[Depends(require_admin)])
    async def queue(
        status: Optional[str] = Query(None),
        conflict_type: Optional[str] = Query(None),
        limit: int = Query(500, ge=1, le=2000),
    ):
        q: Dict[str, Any] = {}
        if status:
            q["status"] = status
        if conflict_type:
            q["conflict_type"] = conflict_type
        cursor = (
            db.project_identity_conflicts.find(q, {"_id": 0})
            .sort([("status", 1), ("conflict_type", 1), ("record_count", -1)])
        )
        return await cursor.to_list(limit)

    @router.post("/queue/{key}/resolve", dependencies=[Depends(require_admin)])
    async def resolve(key: str, body: ResolutionBody):
        if body.action not in {"match", "leave_unmatched", "intentional", "dismiss"}:
            raise HTTPException(400, detail="Invalid action")
        status_map = {
            "match": "matched",
            "leave_unmatched": "left_unmatched",
            "intentional": "intentional",
            "dismiss": "dismissed",
        }
        update = {
            "status": status_map[body.action],
            "resolved_at": _now_iso(),
            "resolution_note": (body.note or "")[:500],
        }
        if body.action == "match":
            if not body.matched_jobs_master_id:
                raise HTTPException(400, detail="matched_jobs_master_id required for match")
            jm = await db.jobs_master.find_one(
                {"id": body.matched_jobs_master_id}, {"_id": 0}
            )
            if not jm:
                raise HTTPException(404, detail="jobs_master row not found")
            update["matched_jobs_master_id"] = jm["id"]
        res = await db.project_identity_conflicts.update_one(
            {"key": key}, {"$set": update}
        )
        if res.matched_count == 0:
            raise HTTPException(404, detail="Governance item not found")
        return {"ok": True, "key": key, "status": update["status"]}

    @router.get("/metrics", dependencies=[Depends(require_admin)])
    async def metrics():
        canonical_count = await db.jobs_master.count_documents(
            {"deleted_at": {"$in": [None, ""]}}
        )
        open_count = await db.project_identity_conflicts.count_documents({"status": "open"})
        matched_count = await db.project_identity_conflicts.count_documents({"status": "matched"})
        intentional_count = await db.project_identity_conflicts.count_documents({"status": "intentional"})
        left_count = await db.project_identity_conflicts.count_documents({"status": "left_unmatched"})
        dismissed_count = await db.project_identity_conflicts.count_documents({"status": "dismissed"})

        # Unmatched records = type D items still open (PN not in jobs_master,
        # no normalization match)
        unmatched_records_pipeline = [
            {"$match": {"status": "open", "conflict_type": "D"}},
            {"$group": {"_id": None, "total": {"$sum": "$record_count"}}},
        ]
        unmatched_records = 0
        async for r in db.project_identity_conflicts.aggregate(unmatched_records_pipeline):
            unmatched_records = r.get("total", 0)

        # Normalized matches = type C items
        normalized_pipeline = [
            {"$match": {"conflict_type": "C"}},
            {"$group": {"_id": None, "total": {"$sum": "$record_count"}}},
        ]
        normalized_matches = 0
        async for r in db.project_identity_conflicts.aggregate(normalized_pipeline):
            normalized_matches = r.get("total", 0)

        # Last governance action
        last_action_doc = await db.project_identity_conflicts.find_one(
            {"resolved_at": {"$ne": None}},
            {"_id": 0, "resolved_at": 1, "resolved_by": 1, "status": 1, "key": 1},
            sort=[("resolved_at", -1)],
        )

        # Identity health score: 100 minus penalties.
        # Each open Type A/B/D conflict = up to 2 pts; cap at 100.
        total_open_a = await db.project_identity_conflicts.count_documents(
            {"status": "open", "conflict_type": "A"}
        )
        total_open_b = await db.project_identity_conflicts.count_documents(
            {"status": "open", "conflict_type": "B"}
        )
        total_open_d = await db.project_identity_conflicts.count_documents(
            {"status": "open", "conflict_type": "D"}
        )
        penalty = min(100, 2 * (total_open_a + total_open_b) + total_open_d)
        health = max(0, 100 - penalty)

        return {
            "canonical_projects": canonical_count,
            "governance_queue": open_count,
            "unmatched_records": unmatched_records,
            "normalized_matches": normalized_matches,
            "intentional_variants": intentional_count,
            "projects_requiring_review": total_open_a + total_open_b + total_open_d,
            "matched_total": matched_count,
            "left_unmatched_total": left_count,
            "dismissed_total": dismissed_count,
            "last_governance_action": last_action_doc,
            "identity_health_score": health,
        }

    return router
