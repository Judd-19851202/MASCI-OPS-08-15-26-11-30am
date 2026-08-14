"""Phase 9A — Trench Safety Reporting & Analytics Command Center.

Nine read-only operational reports plus a universal CSV exporter,
built on EXISTING certified collections:
  • trench_safety_assets · _holds · _repairs · _inspections
  • audit_events
  • trench_safety_pulses (Phase 8C)

No new analytics db. No BI engine. No new ETL. Every figure is a
deterministic query against the live registry.

Endpoints (all gated to safety/admin):
  GET /reports/executive             · Report 1
  GET /reports/road-plate            · Report 2
  GET /reports/inspection-compliance · Report 3
  GET /reports/repair-backlog        · Report 4
  GET /reports/holds                 · Report 5
  GET /reports/utilization           · Report 6
  GET /reports/missing-data          · Report 7
  GET /reports/project-assets        · Report 8
  GET /reports/activity              · Report 9
  GET /reports/{report_id}/export.csv

Common filters (any/all optional, ignored when blank):
  date_from · date_to (ISO 8601) · asset_type · project_id ·
  location · status · condition
"""
from __future__ import annotations

import csv
import io
import logging
from collections import Counter, defaultdict
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from ._helpers import now_iso
from ._models import ASSET_TYPES, OPERATIONAL_STATUSES
from lib.kpi_percent_complete import compliance_rate

logger = logging.getLogger(__name__)

PREFIX = "/trench-safety/reports"


# ────────────────────────────────────────────────────────────────────────
# Filter helpers
# ────────────────────────────────────────────────────────────────────────

class Filters:
    """Materialised set of filters parsed from query params."""

    def __init__(
        self,
        date_from: Optional[str],
        date_to: Optional[str],
        asset_type: Optional[str],
        project_id: Optional[str],
        location: Optional[str],
        status: Optional[str],
        condition: Optional[str],
    ):
        self.date_from = date_from or None
        self.date_to = date_to or None
        self.asset_type = asset_type or None
        self.project_id = project_id or None
        self.location = location or None
        self.status = status or None
        self.condition = condition or None

    def asset_query(self) -> Dict[str, Any]:
        q: Dict[str, Any] = {}
        if self.asset_type:
            q["asset_type"] = self.asset_type
        if self.project_id:
            q["current_project_id"] = self.project_id
        if self.location:
            q["current_location"] = {"$regex": self.location, "$options": "i"}
        if self.status:
            q["operational_status"] = self.status
        if self.condition:
            q["condition"] = self.condition
        return q

    def date_match(self, field: str = "ts") -> Dict[str, Any]:
        m: Dict[str, Any] = {}
        if self.date_from:
            m["$gte"] = self.date_from
        if self.date_to:
            m["$lte"] = self.date_to
        return {field: m} if m else {}

    def as_dict(self) -> Dict[str, Any]:
        return {
            "date_from": self.date_from, "date_to": self.date_to,
            "asset_type": self.asset_type, "project_id": self.project_id,
            "location": self.location, "status": self.status,
            "condition": self.condition,
        }


def _filter_dep(
    date_from: Optional[str] = Query(default=None),
    date_to: Optional[str] = Query(default=None),
    asset_type: Optional[str] = Query(default=None),
    project_id: Optional[str] = Query(default=None),
    location: Optional[str] = Query(default=None),
    status: Optional[str] = Query(default=None),
    condition: Optional[str] = Query(default=None),
) -> Filters:
    return Filters(date_from, date_to, asset_type, project_id, location, status, condition)


def _safe_pct(numer: int, denom: int) -> int:
    if denom <= 0:
        return 0
    return int(round(100 * numer / denom))


# ────────────────────────────────────────────────────────────────────────
# Report builders
# ────────────────────────────────────────────────────────────────────────

async def _load_assets(db, f: Filters) -> List[Dict[str, Any]]:
    return await db.trench_safety_assets.find(f.asset_query(), {"_id": 0}).to_list(5000)


async def report_executive(db, f: Filters) -> Dict[str, Any]:
    docs = await _load_assets(db, f)
    active = [d for d in docs if d.get("is_active")]
    status_counts = Counter(d.get("operational_status") or "Available" for d in active)
    available = status_counts.get("Available", 0)
    assigned = status_counts.get("Assigned", 0)
    in_transport = status_counts.get("In Transport", 0)
    on_hold = sum(status_counts.get(s, 0) for s in (
        "Safety Hold", "Inspection Hold", "Maintenance Hold", "Certification Hold",
    ))
    retired = sum(1 for d in docs if not d.get("is_active") or d.get("operational_status") == "Retired")

    # Inspection compliance
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    overdue = sum(1 for d in active if not d.get("last_inspection_at") or d["last_inspection_at"] < cutoff)
    inspection_compliance_pct, inspection_compliance_state = compliance_rate(len(active) - overdue, len(active))

    # Repair backlog
    open_repairs = await db.trench_safety_repairs.count_documents(
        {"status": {"$in": ["Open", "In Progress", "Waiting on Parts", "Vendor Repair"]}}
    )
    repair_backlog_pct = _safe_pct(open_repairs, max(len(active), 1))

    availability_pct = _safe_pct(available, max(len(active), 1))

    # Pull the latest stored pulse for the health score (deterministic Phase 8C value)
    latest_pulse = await db.trench_safety_pulses.find_one({}, sort=[("generated_at", -1)])
    health_score = None
    health_rating = None
    if latest_pulse and latest_pulse.get("snapshot", {}).get("health"):
        health_score = latest_pulse["snapshot"]["health"].get("score")
        health_rating = latest_pulse["snapshot"]["health"].get("rating")

    # Activity trends — counts of activity events across 7 / 30 / 90 days
    now = datetime.now(timezone.utc)
    windows = {
        "last_7d":  (now - timedelta(days=7)).isoformat(),
        "last_30d": (now - timedelta(days=30)).isoformat(),
        "last_90d": (now - timedelta(days=90)).isoformat(),
    }
    activity_trends: Dict[str, int] = {}
    for label, since in windows.items():
        activity_trends[label] = await db.audit_events.count_documents(
            {"kind": {"$regex": "^trench_"}, "ts": {"$gte": since}}
        )

    return {
        "totals": {
            "total_assets": len(docs),
            "active_assets": len(active),
            "available": available,
            "assigned": assigned,
            "in_transport": in_transport,
            "on_hold": on_hold,
            "retired": retired,
        },
        "ratios": {
            "asset_availability_pct": availability_pct,
            "inspection_compliance_pct": inspection_compliance_pct,
            "inspection_compliance_state": inspection_compliance_state,
            "repair_backlog_pct": repair_backlog_pct,
        },
        "health_score": health_score,
        "health_rating": health_rating,
        "activity_trends": activity_trends,
        "filters": f.as_dict(),
        "generated_at": now_iso(),
    }


async def report_road_plate(db, f: Filters) -> Dict[str, Any]:
    # Force asset_type=Road Plate regardless of caller filter
    forced = Filters(
        f.date_from, f.date_to, "Road Plate",
        f.project_id, f.location, f.status, f.condition,
    )
    docs = await _load_assets(db, forced)
    active = [d for d in docs if d.get("is_active")]
    status_counts = Counter(d.get("operational_status") or "Available" for d in active)
    on_hold = sum(status_counts.get(s, 0) for s in (
        "Safety Hold", "Inspection Hold", "Maintenance Hold", "Certification Hold",
    ))

    open_repairs = await db.trench_safety_repairs.count_documents(
        {"asset_id": {"$in": [d["asset_id"] for d in active]},
         "status": {"$in": ["Open", "In Progress", "Waiting on Parts", "Vendor Repair"]}}
    )

    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    overdue = sum(1 for d in active if not d.get("last_inspection_at") or d["last_inspection_at"] < cutoff)
    inspection_compliance_pct, inspection_compliance_state = compliance_rate(len(active) - overdue, len(active))

    missing_capacity = sum(1 for d in active if not d.get("rated_capacity_lb"))
    missing_serial = sum(1 for d in active if d.get("missing_serial_number"))
    # Missing photos — assets with no rows in trench_safety_photos
    photo_rows = await db.trench_safety_photos.aggregate([
        {"$match": {"asset_id": {"$in": [d["asset_id"] for d in active]}}},
        {"$group": {"_id": "$asset_id", "n": {"$sum": 1}}},
    ]).to_list(2000)
    with_photos = {r["_id"] for r in photo_rows}
    missing_photos = sum(1 for d in active if d["asset_id"] not in with_photos)

    # Utilisation — Assigned + In Transport
    in_use = status_counts.get("Assigned", 0) + status_counts.get("In Transport", 0)
    utilization_pct = _safe_pct(in_use, max(len(active), 1))

    capacity_buckets: Dict[str, int] = defaultdict(int)
    for d in active:
        cap = d.get("rated_capacity_lb")
        if not cap:
            capacity_buckets["unknown"] += 1
        elif cap < 40000:
            capacity_buckets["lt_40k"] += 1
        elif cap < 80000:
            capacity_buckets["40k_80k"] += 1
        else:
            capacity_buckets["ge_80k"] += 1

    # Recent repair + deployment activity (last 30d)
    since_30d = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    rp_ids = [d["asset_id"] for d in active]
    repair_history = await db.trench_safety_repairs.count_documents(
        {"asset_id": {"$in": rp_ids}, "created_at": {"$gte": since_30d}}
    )
    deployment_history = await db.audit_events.count_documents(
        {"asset_id": {"$in": rp_ids},
         "kind": {"$in": [
             "trench_asset_status_changed",
             "trench_safety_transport_started",
             "trench_safety_transport_completed",
         ]},
         "ts": {"$gte": since_30d}}
    )

    return {
        "totals": {
            "total": len(active),
            "available": status_counts.get("Available", 0),
            "assigned": status_counts.get("Assigned", 0),
            "in_transport": status_counts.get("In Transport", 0),
            "on_hold": on_hold,
            "open_repairs": open_repairs,
            "missing_capacity_data": missing_capacity,
            "missing_serial_numbers": missing_serial,
            "missing_photos": missing_photos,
        },
        "ratios": {
            "utilization_pct": utilization_pct,
            "inspection_compliance_pct": inspection_compliance_pct,
            "inspection_compliance_state": inspection_compliance_state,
        },
        "capacity_inventory": dict(capacity_buckets),
        "trend_30d": {
            "repair_history": repair_history,
            "deployment_history": deployment_history,
        },
        "filters": forced.as_dict(),
        "generated_at": now_iso(),
    }


async def report_inspection_compliance(db, f: Filters) -> Dict[str, Any]:
    docs = await _load_assets(db, f)
    active = [d for d in docs if d.get("is_active")]
    cutoff_overdue = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    cutoff_due_soon = (datetime.now(timezone.utc) - timedelta(days=20)).isoformat()

    completed = 0   # has any last_inspection_at within 30 days
    due_soon = 0
    overdue = 0
    missing = 0
    for d in active:
        last = d.get("last_inspection_at")
        if not last:
            missing += 1
        elif last < cutoff_overdue:
            overdue += 1
        elif last < cutoff_due_soon:
            due_soon += 1
        else:
            completed += 1

    # Failed inspections (last 30d)
    since_30d = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    failed = await db.trench_safety_inspections.count_documents(
        {"submitted_at": {"$gte": since_30d}, "result": "Fail"}
    )

    # Breakdown by asset type
    by_type: Dict[str, Dict[str, int]] = {}
    for t in ASSET_TYPES:
        subset = [d for d in active if d.get("asset_type") == t]
        s_overdue = sum(1 for d in subset if not d.get("last_inspection_at") or d["last_inspection_at"] < cutoff_overdue)
        by_type[t] = {
            "total": len(subset),
            "overdue": s_overdue,
            "compliance_pct": _safe_pct(len(subset) - s_overdue, max(len(subset), 1)),
        }

    # Breakdown by yard / location
    by_yard: Dict[str, Dict[str, int]] = defaultdict(lambda: {"total": 0, "overdue": 0})
    for d in active:
        y = d.get("current_location") or d.get("yard_location") or "Unspecified"
        by_yard[y]["total"] += 1
        last = d.get("last_inspection_at")
        if not last or last < cutoff_overdue:
            by_yard[y]["overdue"] += 1

    # Top risk areas — yards with >= 1 overdue, sorted by count
    top_risk = sorted(
        [{"yard": k, **v, "compliance_pct": _safe_pct(v["total"] - v["overdue"], max(v["total"], 1))}
         for k, v in by_yard.items() if v["overdue"] > 0],
        key=lambda x: -x["overdue"],
    )[:8]

    compliance_score, compliance_score_state = compliance_rate(completed, len(active))

    # Trend — count of inspections submitted in last 7 / 30 / 90 days
    now = datetime.now(timezone.utc)
    trend = {
        "last_7d":  await db.trench_safety_inspections.count_documents({"submitted_at": {"$gte": (now - timedelta(days=7)).isoformat()}}),
        "last_30d": await db.trench_safety_inspections.count_documents({"submitted_at": {"$gte": (now - timedelta(days=30)).isoformat()}}),
        "last_90d": await db.trench_safety_inspections.count_documents({"submitted_at": {"$gte": (now - timedelta(days=90)).isoformat()}}),
    }

    return {
        "totals": {
            "completed": completed,
            "due_soon": due_soon,
            "overdue": overdue,
            "failed_30d": failed,
            "missing": missing,
        },
        "compliance_score": compliance_score,
        "compliance_score_state": compliance_score_state,
        "by_asset_type": by_type,
        "top_risk_areas": top_risk,
        "trend": trend,
        "filters": f.as_dict(),
        "generated_at": now_iso(),
    }


async def report_repair_backlog(db, f: Filters) -> Dict[str, Any]:
    asset_ids: Optional[List[str]] = None
    if f.asset_query():
        docs = await _load_assets(db, f)
        asset_ids = [d["asset_id"] for d in docs]
    base_q: Dict[str, Any] = {}
    if asset_ids is not None:
        base_q["asset_id"] = {"$in": asset_ids}

    repairs = await db.trench_safety_repairs.find(base_q, {"_id": 0}).to_list(3000)
    now = datetime.now(timezone.utc)

    open_repairs = [r for r in repairs if r.get("status") in ("Open", "In Progress", "Waiting on Parts", "Vendor Repair")]
    completed = [r for r in repairs if r.get("status") in ("Completed", "Closed After Verification", "Closed")]

    def _days(r, since_field, until_field=None):
        try:
            t1 = datetime.fromisoformat((r.get(since_field) or "").replace("Z", "+00:00"))
            t2 = (datetime.fromisoformat((r.get(until_field) or "").replace("Z", "+00:00"))
                  if until_field and r.get(until_field) else now)
            return max(0, (t2 - t1).days)
        except Exception:  # noqa: BLE001
            return 0

    avg_days_open = (
        int(sum(_days(r, "created_at") for r in open_repairs) / len(open_repairs))
        if open_repairs else 0
    )
    avg_days_to_close = (
        int(sum(_days(r, "created_at", "closed_at") for r in completed) / len(completed))
        if completed else 0
    )

    by_kind = Counter(r.get("kind") or "unspecified" for r in repairs)
    # Map asset_id → asset_type for richer reporting
    docs_all = await _load_assets(db, Filters(None, None, None, None, None, None, None))
    type_map = {d["asset_id"]: d.get("asset_type") for d in docs_all}
    project_map = {d["asset_id"]: d.get("current_project_name") for d in docs_all}
    by_asset_type = Counter(type_map.get(r.get("asset_id"), "Unknown") for r in repairs)
    by_project = Counter(project_map.get(r.get("asset_id")) or "Unassigned" for r in repairs)

    # Top repeat — assets with > 1 repair
    per_asset = Counter(r.get("asset_id") for r in repairs)
    top_repeat = [{"asset_id": k, "asset_type": type_map.get(k), "repair_count": v}
                  for k, v in per_asset.most_common(10) if v > 1]

    # Trend
    trend = {}
    for label, days in (("last_7d", 7), ("last_30d", 30), ("last_90d", 90)):
        since = (now - timedelta(days=days)).isoformat()
        trend[label] = sum(1 for r in repairs if (r.get("created_at") or "") >= since)

    return {
        "totals": {
            "open_repairs": len(open_repairs),
            "completed_repairs": len(completed),
            "avg_days_open": avg_days_open,
            "avg_days_to_close": avg_days_to_close,
        },
        "by_kind": dict(by_kind),
        "by_asset_type": dict(by_asset_type),
        "by_project": dict(by_project),
        "top_repeat_assets": top_repeat,
        "trend": trend,
        "filters": f.as_dict(),
        "generated_at": now_iso(),
    }


async def report_holds(db, f: Filters) -> Dict[str, Any]:
    holds_q: Dict[str, Any] = {}
    if f.asset_query():
        docs = await _load_assets(db, f)
        ids = [d["asset_id"] for d in docs]
        holds_q["asset_id"] = {"$in": ids}
    holds = await db.trench_safety_holds.find(holds_q, {"_id": 0}).to_list(3000)
    now = datetime.now(timezone.utc)

    active_holds = [h for h in holds if h.get("is_active")]
    released = [h for h in holds if not h.get("is_active")]
    by_kind = Counter(h.get("kind") for h in active_holds)

    def _days(h):
        try:
            t = datetime.fromisoformat((h.get("opened_at") or "").replace("Z", "+00:00"))
            return max(0, (now - t).days)
        except Exception:  # noqa: BLE001
            return 0

    avg_days_open = (
        int(sum(_days(h) for h in active_holds) / len(active_holds)) if active_holds else 0
    )

    most_held = Counter(h.get("asset_id") for h in holds)
    docs_all = await _load_assets(db, Filters(None, None, None, None, None, None, None))
    type_map = {d["asset_id"]: d.get("asset_type") for d in docs_all}
    project_map = {d["asset_id"]: d.get("current_project_name") for d in docs_all}

    most_frequent = [
        {"asset_id": k, "asset_type": type_map.get(k), "hold_count": v}
        for k, v in most_held.most_common(10) if v > 0
    ]
    by_project = Counter(project_map.get(h.get("asset_id")) or "Unassigned"
                         for h in active_holds)

    # Trend — holds opened in last 7/30/90d
    trend: Dict[str, int] = {}
    for label, days in (("last_7d", 7), ("last_30d", 30), ("last_90d", 90)):
        since = (now - timedelta(days=days)).isoformat()
        trend[label] = sum(1 for h in holds if (h.get("opened_at") or "") >= since)

    return {
        "totals": {
            "active": len(active_holds),
            "released": len(released),
            "safety_holds": by_kind.get("Safety Hold", 0),
            "inspection_holds": by_kind.get("Inspection Hold", 0),
            "maintenance_holds": by_kind.get("Maintenance Hold", 0),
            "certification_holds": by_kind.get("Certification Hold", 0),
            "avg_days_open": avg_days_open,
        },
        "most_frequent_assets": most_frequent,
        "by_project": dict(by_project.most_common(15)),
        "trend": trend,
        "filters": f.as_dict(),
        "generated_at": now_iso(),
    }


async def report_utilization(db, f: Filters) -> Dict[str, Any]:
    docs = await _load_assets(db, f)
    active = [d for d in docs if d.get("is_active")]
    cs = Counter(d.get("operational_status") or "Available" for d in active)
    in_use = cs.get("Assigned", 0) + cs.get("In Transport", 0)
    idle = cs.get("Available", 0)
    retired = sum(1 for d in docs if not d.get("is_active") or d.get("operational_status") == "Retired")
    utilization_pct = _safe_pct(in_use, max(len(active), 1))

    by_type_util: Dict[str, Dict[str, int]] = {}
    for t in ASSET_TYPES:
        subset = [d for d in active if d.get("asset_type") == t]
        sub_cs = Counter(d.get("operational_status") or "Available" for d in subset)
        sub_used = sub_cs.get("Assigned", 0) + sub_cs.get("In Transport", 0)
        by_type_util[t] = {
            "total": len(subset),
            "in_use": sub_used,
            "idle": sub_cs.get("Available", 0),
            "utilization_pct": _safe_pct(sub_used, max(len(subset), 1)),
        }

    by_project: Dict[str, int] = Counter(
        (d.get("current_project_name") or "Unassigned") for d in active if d.get("operational_status") in ("Assigned", "In Transport")
    )

    return {
        "totals": {
            "available": cs.get("Available", 0),
            "assigned": cs.get("Assigned", 0),
            "in_transport": cs.get("In Transport", 0),
            "idle": idle,
            "retired": retired,
        },
        "utilization_pct": utilization_pct,
        "by_asset_type": by_type_util,
        "by_project": dict(by_project.most_common(15)),
        "filters": f.as_dict(),
        "generated_at": now_iso(),
    }


async def report_missing_data(db, f: Filters) -> Dict[str, Any]:
    docs = await _load_assets(db, f)
    active = [d for d in docs if d.get("is_active")]

    def _flag(d):
        return {
            "missing_serial":        bool(d.get("missing_serial_number")),
            "missing_manufacturer":  bool(d.get("missing_manufacturer")),
            "missing_tabulated":     bool(d.get("tabulated_data_missing")),
            "missing_inspection":    not bool(d.get("last_inspection_at")),
            "missing_project":       not (d.get("current_project_id") or d.get("current_project_name")),
            "missing_location":      not (d.get("current_location") or d.get("yard_location")),
            "missing_capacity":      d.get("asset_type") == "Road Plate" and not d.get("rated_capacity_lb"),
        }

    affected: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    counts: Dict[str, int] = defaultdict(int)
    # Photo presence
    photo_rows = await db.trench_safety_photos.aggregate(
        [{"$group": {"_id": "$asset_id", "n": {"$sum": 1}}}]
    ).to_list(5000)
    with_photos = {r["_id"] for r in photo_rows}

    for d in active:
        f_ = _flag(d)
        f_["missing_photos"] = d["asset_id"] not in with_photos
        for k, v in f_.items():
            if v:
                counts[k] += 1
                affected[k].append({"asset_id": d["asset_id"], "asset_type": d.get("asset_type")})

    return {
        "counts": dict(counts),
        "affected": {k: v[:50] for k, v in affected.items()},
        "active_assets": len(active),
        "filters": f.as_dict(),
        "generated_at": now_iso(),
    }


async def report_project_assets(db, f: Filters) -> Dict[str, Any]:
    docs = await _load_assets(db, f)
    active = [d for d in docs if d.get("is_active")]

    by_project: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        "asset_ids": [], "asset_types": Counter(), "open_repairs": 0,
        "inspections_due": 0, "active_holds": 0,
    })
    cutoff = (datetime.now(timezone.utc) - timedelta(days=30)).isoformat()
    for d in active:
        pj = d.get("current_project_name") or d.get("current_project_id") or "Unassigned"
        slot = by_project[pj]
        slot["asset_ids"].append(d["asset_id"])
        slot["asset_types"][d.get("asset_type") or "Unknown"] += 1
        if not d.get("last_inspection_at") or d["last_inspection_at"] < cutoff:
            slot["inspections_due"] += 1
        if d.get("operational_status") in ("Safety Hold", "Inspection Hold", "Maintenance Hold", "Certification Hold"):
            slot["active_holds"] += 1

    # Pull repair counts for the assets we have in scope
    all_ids = [d["asset_id"] for d in active]
    if all_ids:
        rp_rows = await db.trench_safety_repairs.aggregate([
            {"$match": {"asset_id": {"$in": all_ids},
                        "status": {"$in": ["Open", "In Progress", "Waiting on Parts", "Vendor Repair"]}}},
            {"$group": {"_id": "$asset_id", "n": {"$sum": 1}}},
        ]).to_list(2000)
        by_asset_repairs = {r["_id"]: r["n"] for r in rp_rows}
        for pj, slot in by_project.items():
            slot["open_repairs"] = sum(by_asset_repairs.get(aid, 0) for aid in slot["asset_ids"])

    rows = []
    for pj, slot in by_project.items():
        total = len(slot["asset_ids"])
        # Asset health score per project — penalise holds, repairs, overdue
        health = max(0, 100 - (slot["active_holds"] * 8) - (slot["open_repairs"] * 5) - (slot["inspections_due"] * 3))
        # Risk score — inverse, simple
        risk = max(0, 100 - health)
        rows.append({
            "project": pj,
            "assigned_assets": total,
            "asset_types": dict(slot["asset_types"]),
            "road_plates": slot["asset_types"].get("Road Plate", 0),
            "trench_boxes": slot["asset_types"].get("Trench Box", 0),
            "open_repairs": slot["open_repairs"],
            "inspections_due": slot["inspections_due"],
            "active_holds": slot["active_holds"],
            "asset_health_score": health,
            "risk_score": risk,
        })
    rows.sort(key=lambda r: -r["risk_score"])

    return {
        "rows": rows,
        "total_projects": len(rows),
        "filters": f.as_dict(),
        "generated_at": now_iso(),
    }


async def report_activity(db, f: Filters) -> Dict[str, Any]:
    activity_kinds = [
        "trench_asset_created", "trench_asset_status_changed",
        "trench_asset_retired",
        "trench_asset_inspection_submitted", "trench_asset_inspection_passed",
        "trench_asset_inspection_failed",
        "trench_asset_repair_updated", "trench_asset_repair_verified",
        "trench_asset_hold_opened", "trench_asset_hold_cleared",
        "trench_safety_transport_started", "trench_safety_transport_completed",
    ]
    now = datetime.now(timezone.utc)
    out: Dict[str, Dict[str, int]] = {}
    for label, days in (("last_7d", 7), ("last_30d", 30), ("last_90d", 90)):
        since = (now - timedelta(days=days)).isoformat()
        rows = await db.audit_events.aggregate([
            {"$match": {"kind": {"$in": activity_kinds}, "ts": {"$gte": since}}},
            {"$group": {"_id": "$kind", "n": {"$sum": 1}}},
        ]).to_list(50)
        out[label] = {r["_id"]: r["n"] for r in rows}

    return {
        "by_window": out,
        "filters": f.as_dict(),
        "generated_at": now_iso(),
    }


# ────────────────────────────────────────────────────────────────────────
# Report registry · used by both JSON + CSV export endpoints
# ────────────────────────────────────────────────────────────────────────

_REPORT_REGISTRY = {
    "executive":             report_executive,
    "road-plate":            report_road_plate,
    "inspection-compliance": report_inspection_compliance,
    "repair-backlog":        report_repair_backlog,
    "holds":                 report_holds,
    "utilization":           report_utilization,
    "missing-data":          report_missing_data,
    "project-assets":        report_project_assets,
    "activity":              report_activity,
}


# ────────────────────────────────────────────────────────────────────────
# CSV exporter — flattens any report payload into row/col form
# ────────────────────────────────────────────────────────────────────────

def _flatten_for_csv(report_id: str, payload: Dict[str, Any]) -> List[List[str]]:
    """Produce a 2-D table for the CSV exporter — best-effort flattening.

    Top-level KV pairs go into a "Summary" section; nested arrays/dicts
    go into their own section with explicit headers. Identical layout
    across every report type so leadership recognises the format.
    """
    rows: List[List[str]] = []
    rows.append([f"MASCI Trench Safety Report · {report_id}"])
    rows.append([f"Generated at {payload.get('generated_at','')}"])
    rows.append([])

    def _emit_dict_section(title: str, d: Dict[str, Any]):
        rows.append([title])
        for k, v in d.items():
            if isinstance(v, (str, int, float, bool)) or v is None:
                rows.append([str(k), "" if v is None else str(v)])
        rows.append([])

    def _emit_list_section(title: str, items: List[Dict[str, Any]]):
        if not items:
            rows.append([title, "(empty)"])
            rows.append([])
            return
        keys = list(items[0].keys())
        rows.append([title])
        rows.append(keys)
        for it in items:
            rows.append([str(it.get(k, "")) for k in keys])
        rows.append([])

    for key, val in payload.items():
        if key in ("filters", "generated_at"):
            continue
        if isinstance(val, dict):
            # If dict-of-dicts, treat as table; otherwise summary
            if val and all(isinstance(v, dict) for v in val.values()):
                items = []
                for k2, v2 in val.items():
                    items.append({"key": k2, **{kk: vv for kk, vv in v2.items() if not isinstance(vv, (list, dict))}})
                _emit_list_section(key, items)
            else:
                _emit_dict_section(key, val)
        elif isinstance(val, list):
            list_items = [x for x in val if isinstance(x, dict)]
            _emit_list_section(key, list_items)
        else:
            rows.append([str(key), str(val) if val is not None else ""])

    rows.append([])
    rows.append(["Filters"])
    for k, v in (payload.get("filters") or {}).items():
        rows.append([str(k), "" if v is None else str(v)])
    return rows


# ────────────────────────────────────────────────────────────────────────
# Route registration
# ────────────────────────────────────────────────────────────────────────

def register_report_routes(
    api_router: APIRouter,
    db,
    *,
    require_safety_or_admin,
) -> None:
    @api_router.get(PREFIX + "/list")
    async def list_reports(_actor: dict = Depends(require_safety_or_admin)):
        return {"reports": [
            {"id": "executive",             "name": "Executive Asset Health"},
            {"id": "road-plate",            "name": "Road Plate Command"},
            {"id": "inspection-compliance", "name": "Inspection Compliance"},
            {"id": "repair-backlog",        "name": "Repair Backlog"},
            {"id": "holds",                 "name": "Hold Management"},
            {"id": "utilization",           "name": "Asset Utilization"},
            {"id": "missing-data",          "name": "Missing Data"},
            {"id": "project-assets",        "name": "Project Asset"},
            {"id": "activity",              "name": "Activity & Audit"},
        ]}

    def _make_route(report_id: str, fn):
        @api_router.get(PREFIX + f"/{report_id}", name=f"trench_safety_report_{report_id}")
        async def _h(
            f: Filters = Depends(_filter_dep),
            _actor: dict = Depends(require_safety_or_admin),
        ):
            return await fn(db, f)
        _h.__name__ = f"report_{report_id}"
        return _h

    for rid, fn in _REPORT_REGISTRY.items():
        _make_route(rid, fn)

    @api_router.get(PREFIX + "/{report_id}/export.csv")
    async def export_csv(
        report_id: str,
        f: Filters = Depends(_filter_dep),
        _actor: dict = Depends(require_safety_or_admin),
    ):
        fn = _REPORT_REGISTRY.get(report_id)
        if not fn:
            raise HTTPException(404, f"Unknown report {report_id!r}")
        payload = await fn(db, f)
        rows = _flatten_for_csv(report_id, payload)
        buf = io.StringIO()
        writer = csv.writer(buf)
        for r in rows:
            writer.writerow(r)
        buf.seek(0)
        filename = f"trench_safety_{report_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.csv"
        return StreamingResponse(
            iter([buf.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    # ──────────────────────────────────────────────────────────────────
    # Phase 9B — XLSX export (openpyxl, native Excel) and PDF export
    # (reportlab, simple table layout). Both reuse the SAME flattened
    # report payload as CSV so the contract is uniform.
    # ──────────────────────────────────────────────────────────────────
    @api_router.get(PREFIX + "/{report_id}/export.xlsx")
    async def export_xlsx(
        report_id: str,
        f: Filters = Depends(_filter_dep),
        actor: dict = Depends(require_safety_or_admin),
    ):
        from .report_export import render_xlsx  # noqa: PLC0415
        fn = _REPORT_REGISTRY.get(report_id)
        if not fn:
            raise HTTPException(404, f"Unknown report {report_id!r}")
        payload = await fn(db, f)
        rows = _flatten_for_csv(report_id, payload)
        actor_email = (actor or {}).get("email") or "system"
        buf = render_xlsx(report_id, rows, actor_email)
        filename = f"trench_safety_{report_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.xlsx"
        return StreamingResponse(
            iter([buf.getvalue()]),
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )

    @api_router.get(PREFIX + "/{report_id}/export.pdf")
    async def export_pdf(
        report_id: str,
        f: Filters = Depends(_filter_dep),
        actor: dict = Depends(require_safety_or_admin),
    ):
        from .report_export import render_pdf  # noqa: PLC0415
        fn = _REPORT_REGISTRY.get(report_id)
        if not fn:
            raise HTTPException(404, f"Unknown report {report_id!r}")
        payload = await fn(db, f)
        rows = _flatten_for_csv(report_id, payload)
        actor_email = (actor or {}).get("email") or "system"
        buf = render_pdf(report_id, rows, actor_email, payload.get("filters") or {})
        filename = f"trench_safety_{report_id}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M')}.pdf"
        return StreamingResponse(
            iter([buf.getvalue()]),
            media_type="application/pdf",
            headers={"Content-Disposition": f'attachment; filename="{filename}"'},
        )
