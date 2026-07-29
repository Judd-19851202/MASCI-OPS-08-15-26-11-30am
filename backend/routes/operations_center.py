"""
routes/operations_center.py — Iter C (Phase 2.5).

ONE shared, role-aware operational visibility endpoint. Aggregates
across the existing shared infrastructure streams:

  * Tasks               — open / overdue
  * Notifications       — recent + by severity
  * PO Requests         — pending approval / missing receipt / overdue
  * Document Expirations — expiring / expired
  * Incidents           — open
  * Corrective Actions  — open / overdue
  * Equipment           — out-of-service / maintenance holds / failed pre-ops
  * Audit Coverage      — append_audit usage per source module

NO new source-of-truth. NO duplicate Project Health logic. NO fake
metrics. Every card maps to a deep-link the user can click to open
the underlying list.

Per-role visibility (closed set, defined here so it's one audit point):

  admin / executive  → everything
  pm                 → scoped to PM projects + cross-cutting basics
  hr                 → employee accountability, expirations, offboarding
  shop / dispatch    → equipment readiness, holds, failed pre-ops, transfers

`asyncio.gather` runs all enabled probes in parallel — fast feel
without a job queue. Each probe is one Mongo `count_documents` or
small aggregation — lightweight, indexed-only queries.
"""
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Awaitable, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, Request

from lib.enterprise_governance import (
    build_governance_actor_context,
    require_governed_action,
    resolve_actor_from_request,
)

logger = logging.getLogger(__name__)


ROLE_VISIBILITY: Dict[str, tuple] = {
    "admin": (
        "tasks_overdue", "tasks_open",
        "po_pending_approval", "po_missing_receipt", "po_overdue_receipt",
        "po_approval_p90",
        "doc_exp_expiring", "doc_exp_expired",
        "incidents_open", "ca_overdue",
        "equipment_down", "equipment_holds",
        "preop_failed_recent", "repeat_equipment_failures",
        "integration_health", "audit_coverage",
    ),
    "executive": (
        "tasks_overdue", "po_pending_approval", "po_overdue_receipt",
        "incidents_open", "equipment_down", "ca_overdue",
        "integration_health",
    ),
    "pm": (
        "tasks_overdue", "po_pending_approval", "po_overdue_receipt",
        "po_approval_p90",
        "incidents_open", "ca_overdue", "doc_exp_expiring",
    ),
    "hr": (
        "tasks_overdue", "doc_exp_expiring", "doc_exp_expired",
        "lifecycle_pending_offboarding",
        "po_pending_approval", "po_missing_receipt",
    ),
    "shop": (
        "tasks_overdue", "equipment_down", "equipment_holds",
        "preop_failed_recent", "repeat_equipment_failures",
    ),
    "dispatch": (
        "tasks_overdue", "equipment_down", "equipment_holds",
        "preop_failed_recent", "repeat_equipment_failures",
    ),
    "safety": (
        "tasks_overdue", "incidents_open", "ca_overdue",
        "doc_exp_expiring",
    ),
}

CARD_META: Dict[str, Dict[str, str]] = {
    "tasks_overdue":              {"label": "Overdue tasks",        "url": "/tasks?status=Overdue",                "severity": "Critical"},
    "tasks_open":                 {"label": "Open tasks",           "url": "/tasks?status=Open",                   "severity": "Info"},
    "po_pending_approval":        {"label": "Pending PO approvals", "url": "/po-requests?status=Pending Approval", "severity": "Warning"},
    "po_missing_receipt":         {"label": "POs missing receipt",  "url": "/po-requests?quick=pending_receipt",   "severity": "Warning"},
    "po_overdue_receipt":         {"label": "Overdue PO receipts",  "url": "/po-requests?status=Overdue Receipt",  "severity": "Critical"},
    "po_approval_p90":            {"label": "PO Approval Time",     "url": "/po-requests?status=Pending Approval", "severity": "Info"},
    "doc_exp_expiring":           {"label": "Docs expiring soon",   "url": "/document-expirations?status=Expiring Soon", "severity": "Warning"},
    "doc_exp_expired":            {"label": "Docs expired",         "url": "/document-expirations?status=Expired", "severity": "Critical"},
    "incidents_open":             {"label": "Incidents open",       "url": "/incidents",                            "severity": "Critical"},
    "ca_overdue":                 {"label": "Corrective actions overdue", "url": "/safety-portal/corrective-actions", "severity": "Critical"},
    "equipment_down":             {"label": "Equipment out of service", "url": "/admin/assets?status=Out of Service", "severity": "Critical"},
    "equipment_holds":            {"label": "Active maintenance holds", "url": "/admin/operations-events?type=maintenance_hold", "severity": "Warning"},
    "preop_failed_recent":        {"label": "Failed pre-ops (7d)",  "url": "/admin/operations-events?type=preop_failed", "severity": "Warning"},
    "repeat_equipment_failures":  {"label": "Repeat Equipment Failures", "url": "/admin/assets", "severity": "Info"},
    "lifecycle_pending_offboarding": {"label": "Pending offboarding", "url": "/hr/employees?status=Pending Offboarding", "severity": "Warning"},
    "integration_health":         {"label": "Integration health",   "url": "/admin/system-health",                 "severity": "Info"},
    "audit_coverage":             {"label": "Audit-log coverage",   "url": "/admin/system-health#audit-coverage",  "severity": "Info"},
}


def build_operations_center_router(db, require_any_portal_token) -> APIRouter:
    router = APIRouter(tags=["operations-center"])

    # FORGEDOPS-P0.5 · Asset Spine Health Tile for the Operations Center.
    @router.get("/api/operations-center/asset-spine-tile")
    async def asset_spine_tile(
        request: Request,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
    ) -> Dict[str, Any]:
        """One canonical tile sourced from /api/asset-spine/health plus the
        latest persisted scan summary. Lean projection for the OC board."""
        await require_governed_action(
            db,
            actor=actor,
            action_key="operations_center.view",
            resource_type="operations_center_tile",
            resource={"id": "asset-spine-tile", "project_number": ""},
            requested_context={"tile": "asset_spine_health"},
            request=request,
        )
        from services.asset_spine import AssetSpine  # noqa: PLC0415
        spine = AssetSpine(db)
        h = await spine.health()
        return {
            "title": "Asset Spine Health",
            "url": "/admin/asset-spine",
            "metrics": {
                "total_assets": h.get("total_assets"),
                "active": h.get("active_assets"),
                "retired": h.get("retired_assets"),
                "coverage_pct": h.get("motive_coverage_pct"),
                "unmapped": h.get("unmapped_to_motive"),
                "queue": h.get("mapping_queue_depth"),
                "conflicts": h.get("conflicts"),
            },
            "last_scan": {
                "at": h.get("last_scan_at"),
                "findings": h.get("last_scan_findings"),
            },
            "severity": (
                "high" if (h.get("conflicts") or 0) > 100
                else "medium" if (h.get("motive_coverage_pct") or 0) < 75
                else "low"
            ),
        }

    def _role(a: Dict[str, Any]) -> str:
        return a.get("_actor") or a.get("role") or "admin"

    async def _governed_actor_context(request: Request, actor: Dict[str, Any]) -> Dict[str, Any]:
        resolved_actor = await resolve_actor_from_request(db, request, actor)
        return await build_governance_actor_context(db, resolved_actor)

    @router.get("/api/operations-center")
    async def operations_center(
        request: Request,
        actor: Dict[str, Any] = Depends(require_any_portal_token),
        role_override: Optional[str] = Query(default=None,
            description="Admin only — view another role's center."),
    ) -> Dict[str, Any]:
        await require_governed_action(
            db,
            actor=actor,
            action_key="operations_center.view",
            resource_type="operations_center",
            resource={"id": "operations-center", "project_number": ""},
            requested_context={"portal_role": _role(actor), "role_override": role_override or ""},
            request=request,
        )
        role = _role(actor)
        governed_context = await _governed_actor_context(request, actor)
        if role_override:
            override_decision = await require_governed_action(
                db,
                actor=actor,
                action_key="governance.admin",
                resource_type="operations_center_role_override",
                resource={"id": "operations-center-role-override", "project_number": ""},
                requested_context={"portal_role": role, "target_role": role_override},
                request=request,
            )
            if override_decision.get("allowed"):
                role = role_override
        visible = ROLE_VISIBILITY.get(role, ())
        if not visible:
            return {"role": role, "cards": [], "total": 0}

        scope_mode = str(governed_context.get("governance_scope_mode") or "")
        pm_proj: Optional[List[str]] = None if scope_mode == "global" else list(governed_context.get("project_numbers") or [])

        now = datetime.now(timezone.utc)
        seven_days_ago = now - timedelta(days=7)

        # ── Probes (each returns int count or {count, detail}) ──
        async def p_tasks_overdue() -> int:
            clauses: List[Dict[str, Any]] = [{"status": "Overdue"}]
            if role == "pm" and pm_proj is not None:
                clauses.append({"linked_project_number": {"$in": pm_proj}})
            elif role not in ("admin", "executive"):
                clauses.append({"$or": [
                    {"assignee_role": role}, {"assignee_role": None},
                ]})
            return await db.tasks.count_documents({"$and": clauses})

        async def p_tasks_open() -> int:
            clauses: List[Dict[str, Any]] = [{"status": {"$in": ["Open", "In Progress"]}}]
            if role == "pm" and pm_proj is not None:
                clauses.append({"linked_project_number": {"$in": pm_proj}})
            return await db.tasks.count_documents({"$and": clauses})

        async def p_po(status: str) -> int:
            clauses: List[Dict[str, Any]] = [{"status": status}]
            if role == "pm" and pm_proj is not None:
                clauses.append({"project_number": {"$in": pm_proj}})
            return await db.po_requests.count_documents({"$and": clauses})

        async def p_po_missing_receipt() -> int:
            clauses: List[Dict[str, Any]] = [{
                "status": {"$in": ["Approved", "Pending Receipt", "Overdue Receipt"]},
                "receipt_url": None,
            }]
            if role == "pm" and pm_proj is not None:
                clauses.append({"project_number": {"$in": pm_proj}})
            return await db.po_requests.count_documents({"$and": clauses})

        async def p_doc_exp(status: str) -> int:
            return await db.document_expirations.count_documents({"status": status})

        async def p_incidents_open() -> int:
            clauses: List[Dict[str, Any]] = [{"resolution_status": {"$ne": "Closed"}}]
            if role == "pm" and pm_proj is not None:
                clauses.append({"project_number": {"$in": pm_proj}})
            return await db.incidents.count_documents({"$and": clauses})

        async def p_ca_overdue() -> int:
            clauses: List[Dict[str, Any]] = [{
                "status": {"$nin": ["Completed", "Closed", "Cancelled"]},
                "due_date": {"$lt": now.isoformat()},
            }]
            if role == "pm" and pm_proj is not None:
                clauses.append({"project_number": {"$in": pm_proj}})
            return await db.corrective_actions.count_documents({"$and": clauses})

        async def p_equipment_down() -> int:
            return await db.equipment_master.count_documents({
                "status": {"$in": ["Out of Service", "Down", "Maintenance Hold"]},
            })

        async def p_equipment_holds() -> int:
            return await db.operations_events.count_documents({
                "event_type": {"$in": ["maintenance_hold_active",
                                        "maintenance_hold_requested"]},
                "status": "active",
            })

        async def p_preop_failed_recent() -> int:
            return await db.equipment_inspections.count_documents({
                "fail_count": {"$gt": 0},
                "created_at": {"$gte": seven_days_ago},
            })

        async def p_lifecycle_pending_offboarding() -> int:
            return await db.employees.count_documents({
                "lifecycle_status": "Pending Offboarding",
            })

        async def p_integration_health() -> Dict[str, Any]:
            """Light pulse — last health-check status. Mocked Motive/MaintainX
            are intentionally absent in preview; live env returns real status."""
            try:
                latest = await db.integration_health.find_one(
                    {}, {"_id": 0}, sort=[("checked_at", -1)],
                )
                if not latest:
                    return {"status": "unknown", "checked_at": None}
                return {"status": latest.get("status", "unknown"),
                        "checked_at": latest.get("checked_at")}
            except Exception:
                return {"status": "unknown", "checked_at": None}

        async def p_audit_coverage() -> Dict[str, Any]:
            """Count records per source-module that DO carry an `audit[]`
            array versus those that don't. Surfaces migration progress
            of the `append_audit` helper."""
            try:
                pipeline = [
                    {"$facet": {
                        "po_with":    [{"$match": {"audit": {"$exists": True, "$ne": []}}}, {"$count": "n"}],
                        "po_without": [{"$match": {"$or": [{"audit": {"$exists": False}}, {"audit": []}]}}, {"$count": "n"}],
                    }},
                ]
                po_agg = await db.po_requests.aggregate(pipeline).to_list(1)
                emp_agg = await db.employees.aggregate(pipeline).to_list(1)
                inc_agg = await db.incidents.aggregate(pipeline).to_list(1)
                def _pick(agg, key):
                    if not agg:
                        return 0
                    arr = agg[0].get(key) or []
                    return (arr[0]["n"] if arr else 0)
                modules = [
                    {"module": "po_requests",
                     "with": _pick(po_agg, "po_with"),
                     "without": _pick(po_agg, "po_without")},
                    {"module": "employees",
                     "with": _pick(emp_agg, "po_with"),
                     "without": _pick(emp_agg, "po_without")},
                    {"module": "incidents",
                     "with": _pick(inc_agg, "po_with"),
                     "without": _pick(inc_agg, "po_without")},
                ]
                covered = sum(m["with"] for m in modules)
                total = sum(m["with"] + m["without"] for m in modules)
                pct = round((covered / total) * 100) if total else 0
                return {"modules": modules, "covered": covered,
                        "total": total, "coverage_pct": pct}
            except Exception as e:  # noqa: BLE001
                logger.warning("[ops-center] audit_coverage failed: %s", e)
                return {"modules": [], "covered": 0, "total": 0, "coverage_pct": 0}

        # ── Iter161 · Signal-derived operational indicators ────────
        # Two restrained additions per user instruction (Iter160 +
        # Operations Center integration). Each card pulls its number
        # from the `operational_signal` rollup, applies a SIMPLE static
        # threshold, and returns an explicit severity. NO predictive
        # scoring. NO AI. NO charts. NO new collection.
        async def p_po_approval_p90() -> Dict[str, Any]:
            """30-day p90 of PO submit→approved cycle time. Threshold:
            ≤48h Info · ≤120h Warning · >120h Critical. Empty state =
            neutral 'No signal yet'."""
            try:
                since30 = now - timedelta(days=30)
                cur = db.usage_events.find(
                    {"kind": "operational_signal", "signal": "po.approve",
                     "at": {"$gte": since30},
                     "elapsed_ms": {"$exists": True, "$gte": 0}},
                    {"_id": 0, "elapsed_ms": 1},
                )
                values: List[int] = []
                async for row in cur:
                    v = row.get("elapsed_ms")
                    if isinstance(v, int):
                        values.append(v)
                if not values:
                    return {"display": "No signal yet", "p90_ms": 0,
                            "count": 0, "severity": "Info"}
                values.sort()
                n = len(values)
                # p90 — small n: last value; larger n: index ceil(.9*n)-1
                if n < 10:
                    p90 = values[-1]
                else:
                    p90 = values[min(n - 1, max(0, int(round(n * 0.9)) - 1))]
                s = p90 / 1000.0
                if s < 60:
                    display = f"{int(s)}s"
                elif s < 3600:
                    display = f"{int(s / 60)}m"
                elif s < 86400:
                    display = f"{s / 3600:.1f}h"
                else:
                    display = f"{s / 86400:.1f}d"
                h = s / 3600.0
                if h <= 48:
                    sev = "Info"
                elif h <= 120:
                    sev = "Warning"
                else:
                    sev = "Critical"
                return {"display": display, "p90_ms": int(p90),
                        "count": n, "severity": sev}
            except Exception as e:  # noqa: BLE001
                logger.warning("[ops-center] po_approval_p90 failed: %s", e)
                return {"display": "No signal yet", "p90_ms": 0,
                        "count": 0, "severity": "Info"}

        async def p_repeat_equipment_failures() -> Dict[str, Any]:
            """Equipment IDs with ≥3 fails in last 30 days. Threshold:
            0 = Info · ≥1 = Warning · ≥3 = Critical. Returns top 5
            offenders for deep-link convenience."""
            try:
                since30 = now - timedelta(days=30)
                cur = db.usage_events.aggregate([
                    {"$match": {
                        "kind": "operational_signal",
                        "signal": "equipment.fail",
                        "at": {"$gte": since30},
                        "dims.equipment_id": {"$exists": True, "$ne": ""},
                    }},
                    {"$group": {
                        "_id": "$dims.equipment_id",
                        "count": {"$sum": 1},
                    }},
                    {"$match": {"count": {"$gte": 3}}},
                    {"$sort": {"count": -1}},
                    {"$limit": 5},
                ])
                top: List[Dict[str, Any]] = []
                async for row in cur:
                    top.append({"equipment_id": row["_id"],
                                "count": row["count"]})
                n = len(top)
                if n == 0:
                    sev = "Info"
                    display = "No signal yet"
                elif n < 3:
                    sev = "Warning"
                    display = f"{n} repeat offender{'s' if n != 1 else ''}"
                else:
                    sev = "Critical"
                    display = f"{n} repeat offenders"
                return {"display": display, "count": n, "top": top,
                        "severity": sev}
            except Exception as e:  # noqa: BLE001
                logger.warning("[ops-center] repeat_equipment_failures failed: %s", e)
                return {"display": "No signal yet", "count": 0,
                        "top": [], "severity": "Info"}

        # ── Probe dispatch table ──────────────────────────────────
        PROBES: Dict[str, Callable[[], Awaitable[Any]]] = {
            "tasks_overdue": p_tasks_overdue,
            "tasks_open": p_tasks_open,
            "po_pending_approval": lambda: p_po("Pending Approval"),
            "po_missing_receipt": p_po_missing_receipt,
            "po_overdue_receipt": lambda: p_po("Overdue Receipt"),
            "po_approval_p90": p_po_approval_p90,
            "doc_exp_expiring": lambda: p_doc_exp("Expiring Soon"),
            "doc_exp_expired": lambda: p_doc_exp("Expired"),
            "incidents_open": p_incidents_open,
            "ca_overdue": p_ca_overdue,
            "equipment_down": p_equipment_down,
            "equipment_holds": p_equipment_holds,
            "preop_failed_recent": p_preop_failed_recent,
            "repeat_equipment_failures": p_repeat_equipment_failures,
            "lifecycle_pending_offboarding": p_lifecycle_pending_offboarding,
            "integration_health": p_integration_health,
            "audit_coverage": p_audit_coverage,
        }

        async def _safe(key: str):
            probe = PROBES.get(key)
            if not probe:
                return key, 0
            try:
                v = await probe()
                return key, v
            except Exception as e:  # noqa: BLE001
                logger.warning("[ops-center] probe %s failed: %s", key, e)
                return key, 0

        results = await asyncio.gather(*[_safe(k) for k in visible])
        cards = []
        for key, value in results:
            meta = CARD_META.get(key, {})
            if isinstance(value, dict):
                # Signal-derived cards may carry a dynamic `severity`
                # in the payload — honor it; otherwise fall back to the
                # static CARD_META severity. The severity field is
                # promoted to the card and stripped from the payload to
                # keep the contract clean (severity always lives on the
                # card, never inside `value`).
                dyn_sev = value.get("severity")
                clean_value = {k: v for k, v in value.items() if k != "severity"}
                cards.append({
                    "key": key,
                    "label": meta.get("label", key),
                    "severity": dyn_sev or meta.get("severity", "Info"),
                    "url": meta.get("url"),
                    "value": clean_value,
                })
            else:
                cards.append({
                    "key": key,
                    "label": meta.get("label", key),
                    "severity": meta.get("severity", "Info"),
                    "url": meta.get("url"),
                    "count": int(value or 0),
                })

        return {
            "role": role,
            "generated_at": now.isoformat(),
            "cards": cards,
            "total": sum(c.get("count", 0) for c in cards),
        }

    return router


__all__ = ["build_operations_center_router", "ROLE_VISIBILITY", "CARD_META"]
