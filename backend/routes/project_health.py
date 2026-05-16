"""
routes/project_health.py — Phase H · Project / Job Health Dashboard.

Per-project operational friction summary. Aggregates the SAME shared
infrastructure streams Operations Center uses, but keyed on
`project_number` instead of role. NO new collection, NO duplicate
source-of-truth, NO scoring engine, NO AI.

Endpoint:
    GET /api/project-health

Response:
{
  "rows": [
    {
      "project_number": "...",
      "project_name": "...",
      "status": "green" | "amber" | "red",
      "indicators": {
        "tasks_overdue":         <count>,
        "pos_pending_approval":  <count>,
        "pos_missing_receipt":   <count>,
        "pos_overdue_receipt":   <count>,
        "docs_expiring":         <count>,
        "docs_expired":          <count>,
        "incidents_open":        <count>,
        "ca_overdue":            <count>
      },
      "updated_at": "<iso>"
    }
  ],
  "summary": {"green": N, "amber": N, "red": N, "total": N},
  "generated_at": "<iso>"
}

Status ladder (deterministic, simple, explainable, configurable):
  RED   = any of: ≥1 doc EXPIRED · ≥1 PO Overdue-Receipt
                · ≥1 incident open with severity High/Critical
                · ≥3 tasks overdue · ≥3 CAs overdue
  AMBER = any of: ≥1 task overdue · ≥1 PO missing receipt
                · ≥1 doc expiring (next 14d) · ≥1 CA overdue
  GREEN = no friction at all

Permissions:
  admin / executive / safety  → all active projects
  pm                          → only their scoped projects
  hr / shop / dispatch / FL   → 403 (not project-centric primary lens)
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException

logger = logging.getLogger(__name__)

# Roles that may view the project-health dashboard at all.
ALLOWED_ROLES = {"admin", "executive", "safety", "pm"}

# High-severity incident slugs (matches the closed enum used in
# safety incidents). Used by the red-status rule.
HIGH_SEV = {"High", "Critical", "Severe"}


def build_project_health_router(db, require_any_portal_token) -> APIRouter:
    router = APIRouter(tags=["project-health"])

    def _role(actor: Dict[str, Any]) -> str:
        return actor.get("_actor") or actor.get("role") or "admin"

    async def _project_numbers_for_actor(
        actor: Dict[str, Any], role: str,
    ) -> Optional[List[str]]:
        """Return the project_number whitelist for this actor, or None
        for unrestricted (admin/exec/safety)."""
        if role in ("admin", "executive", "safety"):
            return None
        if role == "pm":
            try:
                from pm_auth import compute_pm_scope  # noqa: PLC0415
                scope = await compute_pm_scope(db, actor)
                if getattr(scope, "is_admin", False):
                    return None
                return list(scope.project_numbers or [])
            except Exception as e:  # noqa: BLE001
                logger.warning("[project-health] PM scope failed: %s", e)
                return []
        return []

    @router.get("/api/project-health")
    async def project_health(
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        role = _role(actor)
        if role not in ALLOWED_ROLES:
            raise HTTPException(403,
                "Project Health is restricted to admin/PM/safety/exec.")

        now = datetime.now(timezone.utc)
        in_14d = now + timedelta(days=14)
        in_14d_iso = in_14d.isoformat()

        # ── Load active projects ──────────────────────────────────
        proj_filter: Dict[str, Any] = {"active": True}
        whitelist = await _project_numbers_for_actor(actor, role)
        if whitelist is not None:
            if not whitelist:
                return {
                    "rows": [],
                    "summary": {"green": 0, "amber": 0, "red": 0, "total": 0},
                    "generated_at": now.isoformat(),
                    "role": role,
                }
            proj_filter["project_number"] = {"$in": whitelist}

        projects: List[Dict[str, Any]] = []
        async for p in db.jobs_master.find(
            proj_filter,
            {"_id": 0, "project_number": 1, "project_name": 1, "name": 1,
             "active": 1, "updated_at": 1},
        ):
            if p.get("project_number"):
                projects.append(p)

        if not projects:
            return {
                "rows": [],
                "summary": {"green": 0, "amber": 0, "red": 0, "total": 0},
                "generated_at": now.isoformat(),
                "role": role,
            }

        pnums = [p["project_number"] for p in projects]

        # ── Bulk fetch indicators in parallel ────────────────────
        # We pull GROUP-BY project_number once per indicator (8 round-
        # trips, all parallel) instead of per-project counts (N×8).
        async def _agg_count_by(coll, match: Dict[str, Any],
                                 field: str = "project_number"):
            """Return {project_number: count} for a given match clause."""
            out: Dict[str, int] = {}
            pipeline = [
                {"$match": {**match, field: {"$in": pnums}}},
                {"$group": {"_id": f"${field}", "n": {"$sum": 1}}},
            ]
            async for row in coll.aggregate(pipeline):
                out[row["_id"]] = row["n"]
            return out

        async def _agg_tasks_overdue():
            return await _agg_count_by(
                db.tasks, {"status": "Overdue"}, "linked_project_number")

        async def _agg_pos_by_status(status: str):
            return await _agg_count_by(
                db.po_requests, {"status": status})

        async def _agg_pos_missing_receipt():
            return await _agg_count_by(
                db.po_requests,
                {"status": {"$in": ["Approved", "Pending Receipt",
                                    "Overdue Receipt"]},
                 "receipt_url": None})

        async def _agg_docs_expiring():
            return await _agg_count_by(
                db.document_expirations,
                {"status": "Expiring Soon",
                 "expires_at": {"$lte": in_14d_iso}},
                "linked_project_number")

        async def _agg_docs_expired():
            return await _agg_count_by(
                db.document_expirations,
                {"status": "Expired"},
                "linked_project_number")

        async def _agg_incidents_open():
            return await _agg_count_by(
                db.incidents,
                {"resolution_status": {"$ne": "Closed"}})

        async def _agg_incidents_open_high():
            return await _agg_count_by(
                db.incidents,
                {"resolution_status": {"$ne": "Closed"},
                 "severity": {"$in": list(HIGH_SEV)}})

        async def _agg_ca_overdue():
            return await _agg_count_by(
                db.corrective_actions,
                {"status": {"$nin": ["Completed", "Closed", "Cancelled"]},
                 "due_date": {"$lt": now.isoformat()}})

        (tasks_overdue, pos_pending, pos_missing, pos_overdue,
         docs_expiring, docs_expired, incidents_open,
         incidents_open_high, ca_overdue) = await asyncio.gather(
            _agg_tasks_overdue(),
            _agg_pos_by_status("Pending Approval"),
            _agg_pos_missing_receipt(),
            _agg_pos_by_status("Overdue Receipt"),
            _agg_docs_expiring(),
            _agg_docs_expired(),
            _agg_incidents_open(),
            _agg_incidents_open_high(),
            _agg_ca_overdue(),
        )

        # ── Assemble per-project rows + apply status ladder ──────
        rows: List[Dict[str, Any]] = []
        summary = {"green": 0, "amber": 0, "red": 0, "total": 0}
        for p in projects:
            pn = p["project_number"]
            ind = {
                "tasks_overdue":        tasks_overdue.get(pn, 0),
                "pos_pending_approval": pos_pending.get(pn, 0),
                "pos_missing_receipt":  pos_missing.get(pn, 0),
                "pos_overdue_receipt":  pos_overdue.get(pn, 0),
                "docs_expiring":        docs_expiring.get(pn, 0),
                "docs_expired":         docs_expired.get(pn, 0),
                "incidents_open":       incidents_open.get(pn, 0),
                "ca_overdue":           ca_overdue.get(pn, 0),
            }
            # Auxiliary signals for status determination only — NOT
            # surfaced as primary indicators.
            inc_high = incidents_open_high.get(pn, 0)

            # ── Status ladder (deterministic) ─────────────────────
            red = (
                ind["docs_expired"] >= 1
                or ind["pos_overdue_receipt"] >= 1
                or inc_high >= 1
                or ind["tasks_overdue"] >= 3
                or ind["ca_overdue"] >= 3
            )
            if red:
                status = "red"
            else:
                amber = (
                    ind["tasks_overdue"] >= 1
                    or ind["pos_missing_receipt"] >= 1
                    or ind["docs_expiring"] >= 1
                    or ind["ca_overdue"] >= 1
                )
                status = "amber" if amber else "green"

            summary[status] += 1
            summary["total"] += 1
            rows.append({
                "project_number": pn,
                "project_name": p.get("project_name") or p.get("name") or pn,
                "status": status,
                "indicators": ind,
                "updated_at": p.get("updated_at"),
            })

        # Default sort: worst first (red > amber > green); then by
        # total indicator sum desc; then alpha by project_number.
        rank = {"red": 0, "amber": 1, "green": 2}
        rows.sort(key=lambda r: (
            rank.get(r["status"], 99),
            -sum(r["indicators"].values()),
            r["project_number"],
        ))

        return {
            "rows": rows,
            "summary": summary,
            "generated_at": now.isoformat(),
            "role": role,
        }

    return router


__all__ = ["build_project_health_router", "ALLOWED_ROLES"]
