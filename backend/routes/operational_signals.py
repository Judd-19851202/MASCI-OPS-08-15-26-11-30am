"""
routes/operational_signals.py — Iter160 (Phase 2.5 · Operational Signal Density).

Admin-only aggregation endpoint over operational signals stored in
db.usage_events with kind='operational_signal'.

Surfaces REAL operational metrics with NO predictive analytics, NO AI
scoring, NO fake KPIs. Each metric is a direct rollup of recorded events
written at the fan-out tap points.

Endpoint:
    GET /api/admin/operational-signals?window_days=30

Response shape (deliberately compact — UI overlays are sparse):
{
  "window_days": 30,
  "since": "2026-04-16T...",
  "throughput": {                # daily counts by signal
    "incident.created":  {"total": N, "by_day": [{"d": "YYYY-MM-DD", "n": N}, ...]},
    "ca.created":        {...},
    "po.submit":         {...},
    "equipment.fail":    {...},
    "fire_ext.fail":     {...},
    "training.deficiency": {...},
    "doc.threshold_fired": {...},
    "hr.offboarding_started": {...}
  },
  "cycle_time_ms": {             # avg + p50 + p90 in milliseconds
    "ca.closed":   {"count": N, "avg_ms": M, "p50_ms": M, "p90_ms": M},
    "po.approve":  {...},
    "po.receipt":  {...},
    "po.close":    {...}
  },
  "equipment_top_failing": [     # top 10 failing equipment ids
    {"equipment_id": "...", "count": N}, ...
  ],
  "doc_threshold_breakdown": [   # category × threshold counts
    {"category": "...", "threshold": N, "count": N}, ...
  ],
  "deltas": {                    # 30-day delta vs previous 30 days
    "incident.created": {"current": N, "previous": N, "direction": "up|down|flat"},
    ...
  }
}
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends

logger = logging.getLogger(__name__)


# Signals exposed as throughput tiles (daily counts) on the admin surface.
THROUGHPUT_SIGNALS = [
    "incident.created",
    "ca.created",
    "po.submit",
    "equipment.fail",
    "fire_ext.fail",
    "training.deficiency",
    "doc.threshold_fired",
    "hr.offboarding_started",
]

# Signals exposed as cycle-time rollups (use elapsed_ms).
CYCLE_TIME_SIGNALS = ["ca.closed", "po.approve", "po.receipt", "po.close"]


async def _throughput_for_signal(
    db, signal: str, since: datetime,
) -> Dict[str, Any]:
    """Return {total, by_day[]} for a single signal in the window."""
    cur = db.usage_events.aggregate([
        {"$match": {
            "kind": "operational_signal",
            "signal": signal,
            "at": {"$gte": since},
        }},
        {"$group": {
            "_id": {
                "y": {"$year": "$at"},
                "m": {"$month": "$at"},
                "d": {"$dayOfMonth": "$at"},
            },
            "n": {"$sum": 1},
        }},
        {"$sort": {"_id.y": 1, "_id.m": 1, "_id.d": 1}},
    ])
    by_day: List[Dict[str, Any]] = []
    total = 0
    async for row in cur:
        _id = row["_id"]
        d = f"{_id['y']:04d}-{_id['m']:02d}-{_id['d']:02d}"
        by_day.append({"d": d, "n": row["n"]})
        total += row["n"]
    return {"total": total, "by_day": by_day}


async def _cycle_time_for_signal(
    db, signal: str, since: datetime,
) -> Dict[str, Any]:
    """Return {count, avg_ms, p50_ms, p90_ms} for a single signal.

    Pulls elapsed_ms values, computes avg + quantiles in Python (Mongo <7
    lacks $percentile in stable). Bounded result set: we sort + slice
    in-memory — at the volumes this platform generates (≤a few thousand
    events / month per signal) this is far cheaper than a Mongo
    aggregation pipeline.
    """
    cur = db.usage_events.find(
        {
            "kind": "operational_signal",
            "signal": signal,
            "at": {"$gte": since},
            "elapsed_ms": {"$exists": True, "$gte": 0},
        },
        {"_id": 0, "elapsed_ms": 1},
    )
    values: List[int] = []
    async for row in cur:
        v = row.get("elapsed_ms")
        if isinstance(v, int):
            values.append(v)
    if not values:
        return {"count": 0, "avg_ms": 0, "p50_ms": 0, "p90_ms": 0}
    values.sort()
    n = len(values)
    avg = int(sum(values) / n)
    p50 = values[int(n * 0.50)]
    # p90 — use ceil-style index so p90 of 10 values = values[9]
    p90 = values[min(n - 1, int(round(n * 0.90)) - 1) if n >= 10 else n - 1]
    return {"count": n, "avg_ms": avg, "p50_ms": p50, "p90_ms": p90}


async def _equipment_top_failing(db, since: datetime, limit: int = 10):
    """Top failing equipment_id from dims (recorded at equipment.fail
    signal). Returns rows ordered by count desc."""
    cur = db.usage_events.aggregate([
        {"$match": {
            "kind": "operational_signal",
            "signal": "equipment.fail",
            "at": {"$gte": since},
            "dims.equipment_id": {"$exists": True, "$ne": ""},
        }},
        {"$group": {
            "_id": "$dims.equipment_id",
            "count": {"$sum": 1},
        }},
        {"$sort": {"count": -1}},
        {"$limit": limit},
    ])
    out: List[Dict[str, Any]] = []
    async for row in cur:
        out.append({"equipment_id": row["_id"], "count": row["count"]})
    return out


async def _doc_threshold_breakdown(db, since: datetime):
    """Category × threshold counts for doc.threshold_fired signal."""
    cur = db.usage_events.aggregate([
        {"$match": {
            "kind": "operational_signal",
            "signal": "doc.threshold_fired",
            "at": {"$gte": since},
        }},
        {"$group": {
            "_id": {
                "category": {"$ifNull": ["$dims.category", "unknown"]},
                "threshold": {"$ifNull": ["$dims.threshold", -999]},
            },
            "count": {"$sum": 1},
        }},
        {"$sort": {"count": -1}},
    ])
    out: List[Dict[str, Any]] = []
    async for row in cur:
        _id = row["_id"]
        out.append({
            "category": _id.get("category"),
            "threshold": _id.get("threshold"),
            "count": row["count"],
        })
    return out


async def _delta_for_signal(
    db, signal: str, current_since: datetime, window_days: int,
) -> Dict[str, Any]:
    """Compare current-window count vs previous-window count for one signal."""
    previous_since = current_since - timedelta(days=window_days)
    cur_n = await db.usage_events.count_documents({
        "kind": "operational_signal",
        "signal": signal,
        "at": {"$gte": current_since},
    })
    prev_n = await db.usage_events.count_documents({
        "kind": "operational_signal",
        "signal": signal,
        "at": {"$gte": previous_since, "$lt": current_since},
    })
    if cur_n > prev_n:
        direction = "up"
    elif cur_n < prev_n:
        direction = "down"
    else:
        direction = "flat"
    return {"current": cur_n, "previous": prev_n, "direction": direction}


def build_operational_signals_router(db, require_admin):
    router = APIRouter(tags=["operational-signals"])

    @router.get("/api/admin/operational-signals",
                dependencies=[Depends(require_admin)])
    async def get_operational_signals(window_days: int = 30) -> Dict[str, Any]:
        # Clamp window — protect against runaway scans.
        try:
            wd_raw = int(window_days)
        except (TypeError, ValueError):
            wd_raw = 30
        wd = max(1, min(wd_raw, 180))
        since = datetime.now(timezone.utc) - timedelta(days=wd)

        # Throughput tiles
        throughput: Dict[str, Any] = {}
        for s in THROUGHPUT_SIGNALS:
            try:
                throughput[s] = await _throughput_for_signal(db, s, since)
            except Exception as e:  # noqa: BLE001
                logger.warning("throughput(%s) failed: %s", s, e)
                throughput[s] = {"total": 0, "by_day": []}

        # Cycle time rollups
        cycle: Dict[str, Any] = {}
        for s in CYCLE_TIME_SIGNALS:
            try:
                cycle[s] = await _cycle_time_for_signal(db, s, since)
            except Exception as e:  # noqa: BLE001
                logger.warning("cycle_time(%s) failed: %s", s, e)
                cycle[s] = {"count": 0, "avg_ms": 0, "p50_ms": 0, "p90_ms": 0}

        # Top failing equipment
        try:
            equipment_top = await _equipment_top_failing(db, since)
        except Exception as e:  # noqa: BLE001
            logger.warning("equipment_top failed: %s", e)
            equipment_top = []

        # Doc threshold breakdown
        try:
            doc_breakdown = await _doc_threshold_breakdown(db, since)
        except Exception as e:  # noqa: BLE001
            logger.warning("doc_breakdown failed: %s", e)
            doc_breakdown = []

        # Window-over-window deltas
        deltas: Dict[str, Any] = {}
        for s in THROUGHPUT_SIGNALS:
            try:
                deltas[s] = await _delta_for_signal(db, s, since, wd)
            except Exception as e:  # noqa: BLE001
                logger.warning("delta(%s) failed: %s", s, e)
                deltas[s] = {"current": 0, "previous": 0, "direction": "flat"}

        return {
            "window_days": wd,
            "since": since.isoformat(),
            "throughput": throughput,
            "cycle_time_ms": cycle,
            "equipment_top_failing": equipment_top,
            "doc_threshold_breakdown": doc_breakdown,
            "deltas": deltas,
        }

    return router


__all__ = ["build_operational_signals_router"]
