"""
Storage intelligence + cost estimator.

Executive analytics answered from the persisted `r2_inventory` +
`r2_classifications` collections. Everything is read-only.
Numbers rendered here MUST be evidence-backed — no fake projections.
"""
from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional


# Cloudflare R2 pricing (US spec, as of Feb 2026): $0.015 per GB-month
# for standard storage. Egress is free from R2 to any origin so we do
# not include it in the operator-facing cost estimate.
R2_USD_PER_GB_MONTH = 0.015


def _gb(bytes_val: int) -> float:
    return round(bytes_val / (1024 ** 3), 3)


async def top_prefixes(db, limit: int = 20) -> List[Dict[str, Any]]:
    """Aggregate inventory rows by top-level prefix — the executive
    "GB by folder" roll-up."""
    pipeline = [
        {"$group": {
            "_id": "$prefix",
            "bytes": {"$sum": "$size"},
            "count": {"$sum": 1},
        }},
        {"$sort": {"bytes": -1}},
        {"$limit": limit},
    ]
    out: List[Dict[str, Any]] = []
    async for row in db.r2_inventory.aggregate(pipeline):
        out.append({
            "prefix": row["_id"] or "<root>",
            "bytes": row["bytes"],
            "gb": _gb(row["bytes"]),
            "count": row["count"],
        })
    return out


async def top_projects(db, limit: int = 20) -> List[Dict[str, Any]]:
    """Aggregate by extracted project number.  `null` project rows are
    excluded (they roll up under `top_prefixes` instead)."""
    pipeline = [
        {"$match": {"project_number": {"$ne": None}}},
        {"$group": {
            "_id": "$project_number",
            "bytes": {"$sum": "$size"},
            "count": {"$sum": 1},
        }},
        {"$sort": {"bytes": -1}},
        {"$limit": limit},
    ]
    out: List[Dict[str, Any]] = []
    async for row in db.r2_inventory.aggregate(pipeline):
        out.append({
            "project_number": row["_id"],
            "bytes": row["bytes"],
            "gb": _gb(row["bytes"]),
            "count": row["count"],
        })
    return out


async def largest_objects(db, limit: int = 50) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    cursor = db.r2_inventory.find({}, {"_id": 0, "key": 1, "size": 1, "last_modified": 1, "prefix": 1, "project_number": 1}).sort("size", -1).limit(limit)
    async for row in cursor:
        out.append({
            "key": row.get("key"),
            "bytes": int(row.get("size") or 0),
            "gb": _gb(int(row.get("size") or 0)),
            "last_modified": row.get("last_modified"),
            "prefix": row.get("prefix"),
            "project_number": row.get("project_number"),
        })
    return out


async def growth_series(db, *, days: int = 90) -> List[Dict[str, Any]]:
    """Aggregate uploads by day from `first_seen_at`.  When the same
    key re-appears in later scans, it does NOT roll up again — the
    first-seen timestamp is stable."""
    cutoff = datetime.now(timezone.utc) - timedelta(days=days)
    pipeline = [
        {"$match": {"first_seen_at": {"$gte": cutoff.isoformat()}}},
        {"$project": {
            "day": {"$substr": ["$first_seen_at", 0, 10]},
            "size": 1,
        }},
        {"$group": {
            "_id": "$day",
            "bytes": {"$sum": "$size"},
            "count": {"$sum": 1},
        }},
        {"$sort": {"_id": 1}},
    ]
    out: List[Dict[str, Any]] = []
    async for row in db.r2_inventory.aggregate(pipeline):
        out.append({
            "day": row["_id"],
            "bytes": row["bytes"],
            "gb": _gb(row["bytes"]),
            "count": row["count"],
        })
    return out


def estimate_cost(
    total_bytes: int,
    orphan_bytes: int,
    *,
    price_gb_month_usd: float = R2_USD_PER_GB_MONTH,
) -> Dict[str, Any]:
    """Pure function — trivially unit-testable."""
    total_gb = total_bytes / (1024 ** 3)
    orphan_gb = orphan_bytes / (1024 ** 3)
    current_monthly = total_gb * price_gb_month_usd
    orphan_monthly = orphan_gb * price_gb_month_usd
    return {
        "unit_price_usd_per_gb_month": price_gb_month_usd,
        "current_monthly_usd": round(current_monthly, 4),
        "current_annual_usd": round(current_monthly * 12, 2),
        "orphan_reclaim_monthly_usd": round(orphan_monthly, 4),
        "orphan_reclaim_annual_usd": round(orphan_monthly * 12, 2),
        "projected_savings_pct": round(
            (orphan_monthly / current_monthly * 100.0) if current_monthly > 0 else 0.0, 2
        ),
    }
