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

from fastapi import APIRouter, Depends, HTTPException, Request

from lib.corrective_action_truth import open_corrective_action_query, overdue_corrective_action_query
from lib.enterprise_governance import (
    governance_project_scope_numbers,
    require_governed_action,
)
from lib.synthetic_corrective_action_filter import apply_synthetic_corrective_action_exclusion

from services.cost_codes.foundation import (
    build_confidence_governance_summary,
    load_project_confidence_history,
    persist_project_confidence_snapshot,
)
from services.cost_codes.oppc_confidence import build_confidence_snapshot_record
from services.cost_codes.oppc_confidence_data import build_project_confidence_payload

logger = logging.getLogger(__name__)

# Roles that may view the project-health dashboard at all.
ALLOWED_ROLES = {"admin", "executive", "safety", "pm"}

# High-severity incident slugs (matches the closed enum used in
# safety incidents). Used by the red-status rule.
HIGH_SEV = {"High", "Critical", "Severe"}
_CLOSED_INCIDENT_RESOLUTION = "Closed"
def _open_incident_match(extra: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    match: Dict[str, Any] = {"resolution_status": {"$ne": _CLOSED_INCIDENT_RESOLUTION}}
    if extra:
        match.update(extra)
    return match


def _build_project_health_kpi_metadata(now_iso: str) -> Dict[str, Any]:
    return {
        "page": {
            "kpi_name": "Project Health",
            "business_definition": "Per-project operational friction summary with deterministic status ladders and canonical indicator formulas.",
            "source_of_truth": [
                "jobs_master",
                "tasks",
                "po_requests",
                "document_expirations",
                "incidents",
                "corrective_actions",
            ],
            "api_endpoint": "/api/project-health",
            "formula": {
                "row_entity": "project_number",
                "default_sort": "red > amber > green, then highest indicator total",
                "generated_at": now_iso,
            },
            "confidence": "HIGH",
            "status_reason": "Open incidents and corrective actions use the same canonical formulas consumed by Operations Center and PM command surfaces.",
            "drilldown_source": "/project-health",
            "owner": "project-health",
            "freshness": "Generated on request.",
        },
        "summary": {
            "red": {
                "kpi_name": "Red Projects",
                "business_definition": "Projects with at least one red-threshold breach.",
                "formula": [
                    "docs_expired >= 1",
                    "pos_overdue_receipt >= 1",
                    "open incidents with severity in High/Critical/Severe >= 1",
                    "tasks_overdue >= 3",
                    "ca_overdue >= 3",
                ],
            },
            "amber": {
                "kpi_name": "Amber Projects",
                "business_definition": "Projects with attention items but no red-threshold breach.",
                "formula": [
                    "tasks_overdue >= 1",
                    "pos_missing_receipt >= 1",
                    "docs_expiring within 14 days >= 1",
                    "ca_overdue >= 1",
                ],
            },
            "green": {
                "kpi_name": "Green Projects",
                "business_definition": "Projects with zero tracked friction indicators.",
                "formula": "No red or amber rule matched.",
            },
            "total": {
                "kpi_name": "Total Active Projects",
                "business_definition": "Active projects visible to the current actor scope.",
                "formula": "Count of active jobs_master rows after governance scoping.",
            },
            "avg_confidence": {
                "kpi_name": "Average Production Confidence",
                "business_definition": "Mean of the per-project production confidence scores already emitted on each row.",
                "formula": "sum(row.production_confidence.score) / row_count",
            },
        },
        "indicators": {
            "tasks_overdue": {
                "kpi_name": "Overdue Tasks",
                "business_definition": "Tasks whose canonical status is Overdue for a project.",
                "formula": {"match": {"status": "Overdue"}, "group_by": "linked_project_number"},
            },
            "pos_pending_approval": {
                "kpi_name": "POs Pending Approval",
                "business_definition": "PO requests still awaiting approval.",
                "formula": {"match": {"status": "Pending Approval"}, "group_by": "project_number"},
            },
            "pos_missing_receipt": {
                "kpi_name": "POs Missing Receipt",
                "business_definition": "Approved or receipt-phase POs without a receipt attachment.",
                "formula": {
                    "match": {
                        "status": {"$in": ["Approved", "Pending Receipt", "Overdue Receipt"]},
                        "receipt_url": None,
                    },
                    "group_by": "project_number",
                },
            },
            "pos_overdue_receipt": {
                "kpi_name": "POs Overdue Receipt",
                "business_definition": "PO requests explicitly marked Overdue Receipt.",
                "formula": {"match": {"status": "Overdue Receipt"}, "group_by": "project_number"},
            },
            "docs_expiring": {
                "kpi_name": "Docs Expiring 14 Days",
                "business_definition": "Document expirations expiring soon within the next 14 days.",
                "formula": {"match": {"status": "Expiring Soon", "expires_at": {"$lte": "now+14d"}}, "group_by": "linked_project_number"},
            },
            "docs_expired": {
                "kpi_name": "Docs Expired",
                "business_definition": "Document expirations already past due.",
                "formula": {"match": {"status": "Expired"}, "group_by": "linked_project_number"},
            },
            "incidents_open": {
                "kpi_name": "Open Incidents",
                "business_definition": "Canonical open incidents where resolution_status is not Closed.",
                "formula": {"match": _open_incident_match(), "group_by": "project_number"},
            },
            "ca_overdue": {
                "kpi_name": "Corrective Actions Overdue",
                "business_definition": "Open corrective actions with a due date in the past.",
                "formula": {"match": apply_synthetic_corrective_action_exclusion(overdue_corrective_action_query(today_iso=now_iso[:10])), "group_by": "project_number"},
            },
        },
    }


def build_project_health_router(db, require_any_portal_token) -> APIRouter:
    router = APIRouter(tags=["project-health"])

    def _role(actor: Dict[str, Any]) -> str:
        return actor.get("_actor") or actor.get("role") or "admin"

    @router.get("/api/project-health")
    async def project_health(
        request: Request,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        await require_governed_action(
            db,
            actor=actor,
            action_key="operations_center.view",
            resource_type="project_health_dashboard",
            resource={"id": "project-health-dashboard", "project_number": ""},
            requested_context={"workspace": "project_health"},
            request=request,
        )
        role = _role(actor)
        if role not in ALLOWED_ROLES:
            raise HTTPException(403,
                "Project Health is restricted to admin/PM/safety/exec.")

        now = datetime.now(timezone.utc)
        in_14d = now + timedelta(days=14)
        in_14d_iso = in_14d.isoformat()

        # ── Load active projects ──────────────────────────────────
        proj_filter: Dict[str, Any] = {"active": True}
        whitelist = await governance_project_scope_numbers(db, actor)
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
                _open_incident_match())

        async def _agg_incidents_open_high():
            return await _agg_count_by(
                db.incidents,
                _open_incident_match({"severity": {"$in": list(HIGH_SEV)}}))

        async def _agg_ca_overdue():
            return await _agg_count_by(
                db.corrective_actions,
                apply_synthetic_corrective_action_exclusion(overdue_corrective_action_query(today_iso=now.date().isoformat())))

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
        confidence_payloads = await asyncio.gather(*(build_project_confidence_payload(db, p) for p in projects)) if projects else []
        confidence_histories = await asyncio.gather(*(load_project_confidence_history(db, p["project_number"]) for p in projects)) if projects else []
        confidence_by_project = {p["project_number"]: payload for p, payload in zip(projects, confidence_payloads)}
        confidence_history_by_project = {p["project_number"]: history for p, history in zip(projects, confidence_histories)}

        # ── Assemble per-project rows + apply status ladder ──────
        rows: List[Dict[str, Any]] = []
        summary = {"green": 0, "amber": 0, "red": 0, "total": 0}
        for p in projects:
            pn = p["project_number"]
            confidence = confidence_by_project.get(pn) or {}
            confidence_history = confidence_history_by_project.get(pn) or {}
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
                "production_confidence": confidence,
                "production_confidence_governance": build_confidence_governance_summary(confidence_history),
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
            "kpi_metadata": _build_project_health_kpi_metadata(now.isoformat()),
        }

    @router.get("/api/project-health/{project_number}/confidence")
    async def project_confidence_detail(
        project_number: str,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        role = _role(actor)
        if role not in ALLOWED_ROLES:
            raise HTTPException(403, "Project confidence is restricted to admin/PM/safety/exec.")
        whitelist = await governance_project_scope_numbers(db, actor)
        if whitelist is not None and project_number not in whitelist:
            raise HTTPException(403, "Project not in actor scope.")
        job = await db.jobs_master.find_one({"project_number": project_number}, {"_id": 0})
        if not job:
            raise HTTPException(404, "Project not found.")
        confidence = await build_project_confidence_payload(db, job)
        history = await load_project_confidence_history(db, project_number)
        return {
            "project_number": project_number,
            "project_name": job.get("project_name") or job.get("name") or project_number,
            "production_confidence": confidence,
            "governance": build_confidence_governance_summary(history),
        }

    @router.post("/api/project-health/{project_number}/confidence/snapshots")
    async def snapshot_project_confidence(
        project_number: str,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        role = _role(actor)
        if role not in ALLOWED_ROLES:
            raise HTTPException(403, "Project confidence is restricted to admin/PM/safety/exec.")
        whitelist = await governance_project_scope_numbers(db, actor)
        if whitelist is not None and project_number not in whitelist:
            raise HTTPException(403, "Project not in actor scope.")
        job = await db.jobs_master.find_one({"project_number": project_number}, {"_id": 0})
        if not job:
            raise HTTPException(404, "Project not found.")
        confidence = await build_project_confidence_payload(db, job)
        snapshot = build_confidence_snapshot_record(
            project_number=project_number,
            confidence=confidence,
            actor_label=actor.get("email") or actor.get("full_name") or actor.get("id") or role,
            note="Confidence snapshot from project-health",
        )
        record = {"id": snapshot["snapshot_id"], "doc_id": snapshot["snapshot_id"], "project_number": project_number}
        try:
            from lib.trust_spine import emit_record_created, emit_workflow_stage  # noqa: PLC0415

            await emit_record_created(
                db,
                workflow="oppc-production-confidence",
                record=record,
                module="routes/project_health.py:snapshot_project_confidence",
                event_name="confidence_snapshot_created",
            )
            await emit_workflow_stage(
                db,
                workflow="oppc-production-confidence",
                stage="validation_complete",
                record=record,
                module="routes/project_health.py:snapshot_project_confidence",
                event_name="confidence_explainability_verified",
            )
        except Exception:
            pass
        try:
            await persist_project_confidence_snapshot(db, project_number=project_number, snapshot=snapshot)
        except LookupError as exc:
            raise HTTPException(404, str(exc)) from exc
        try:
            from lib.trust_spine import emit_workflow_stage  # noqa: PLC0415

            await emit_workflow_stage(
                db,
                workflow="oppc-production-confidence",
                stage="audit_written",
                record=record,
                module="jobs_master.oppc_confidence_history",
                event_name="confidence_snapshot_persisted",
            )
            await emit_workflow_stage(
                db,
                workflow="oppc-production-confidence",
                stage="dashboard_updated",
                record=record,
                module="routes/project_health.py:snapshot_project_confidence",
                event_name="confidence_dashboard_updated",
            )
            await emit_workflow_stage(
                db,
                workflow="oppc-production-confidence",
                stage="completed",
                record=record,
                module="routes/project_health.py:snapshot_project_confidence",
                event_name="confidence_snapshot_completed",
            )
        except Exception:
            pass
        return {"ok": True, "snapshot": snapshot, "production_confidence": confidence}

    return router


__all__ = ["build_project_health_router", "ALLOWED_ROLES"]
