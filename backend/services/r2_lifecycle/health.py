"""
Phase 10 · Storage Health score.

Reads from the persisted lifecycle collections (`r2_inventory`,
`r2_classifications`, `r2_lifecycle_runs`) plus the existing
`backup_health` collection and computes a composite health score.

The score is deliberately transparent: every sub-score is exposed on
the response so operators (and the OCC card) can see why the number is
what it is. NO black-box weighting.

Sub-scores (0–100 each)
-----------------------
- capacity_score        — 100 when usage < warn, degrades to 0 at 3× alert.
- ownership_score       — % of objects with a VERIFIED_OWNER classification.
- orphan_score          — 100 when 0 orphans, degrades linearly to 0 at
                          20 % orphan share.
- retention_score       — 100 when SYSTEM/BACKUP/HISTORICAL objects are
                          intact (no accidental deletion signal).
- backup_score          — from `backup_health` — last backup ≤ 60 min → 100.
- lifecycle_score       — % of inventory rows classified in the latest
                          run (should be 100 after every full pass).
- freshness_score       — how recently the inventory scan ran.

Overall = weighted average.  Weights chosen to punish orphan growth
and stale scans while rewarding backup freshness.
"""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

from .classification import CLASSIFICATIONS


_WEIGHTS: Dict[str, float] = {
    "capacity_score":   0.20,
    "ownership_score":  0.20,
    "orphan_score":     0.15,
    "retention_score":  0.10,
    "backup_score":     0.15,
    "lifecycle_score":  0.10,
    "freshness_score":  0.10,
}


def _band(score: float) -> str:
    if score >= 85:
        return "GREEN"
    if score >= 65:
        return "AMBER"
    return "RED"


def _clamp(v: float) -> float:
    return max(0.0, min(100.0, v))


def _capacity_score(gb: float, warn_gb: float, alert_gb: float) -> float:
    if warn_gb <= 0 or alert_gb <= warn_gb:
        return 100.0
    if gb <= warn_gb:
        return 100.0
    # Linear taper from warn → alert → 3×alert → 0.
    if gb <= alert_gb:
        return _clamp(75.0 - 50.0 * ((gb - warn_gb) / max(alert_gb - warn_gb, 1e-6)))
    # Over alert.
    upper = alert_gb * 3.0
    return _clamp(25.0 - 25.0 * min((gb - alert_gb) / max(upper - alert_gb, 1e-6), 1.0))


def _minutes_since(ts_iso: Optional[str], now: datetime) -> Optional[float]:
    if not ts_iso:
        return None
    try:
        ts = datetime.fromisoformat(ts_iso.replace("Z", "+00:00"))
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=timezone.utc)
    except Exception:  # noqa: BLE001
        return None
    return (now - ts).total_seconds() / 60.0


async def compute_storage_health(
    db,
    *,
    now: Optional[datetime] = None,
) -> Dict[str, Any]:
    """Return the composite storage health payload used by OCC + the
    Admin OS · Storage & Recovery domain page."""
    now = now or datetime.now(timezone.utc)

    # 1) Bucket capacity (from `backup_health.r2-usage-*` most recent row).
    usage_row = await db.backup_health.find_one(
        {"mode": {"$in": ["r2-usage-alert", "r2-usage-warn"]}},
        {"_id": 0}, sort=[("ts", -1)],
    )
    if usage_row:
        usage_bytes = int(usage_row.get("size_bytes") or 0)
        gb = round(usage_bytes / (1024 ** 3), 2)
    else:
        # Fall back to inventory total when the observability row is missing.
        stat = await db.r2_inventory.aggregate([
            {"$group": {"_id": None, "b": {"$sum": "$size"}}}
        ]).to_list(1)
        gb = round((stat[0]["b"] if stat else 0) / (1024 ** 3), 2)
    warn_gb, alert_gb = 45.0, 50.0

    # 2) Classification snapshot.
    cls_row = await db.r2_lifecycle_runs.find_one(
        {"kind": "classification"}, {"_id": 0}, sort=[("completed_at", -1)],
    )
    counts = (cls_row or {}).get("counts") or {c: 0 for c in CLASSIFICATIONS}
    total = sum(counts.values())
    owned = counts.get("VERIFIED_OWNER", 0)
    orphans = counts.get("VERIFIED_ORPHAN", 0)
    orphan_bytes = int((cls_row or {}).get("verified_orphan_bytes") or 0)

    # 3) Inventory freshness.
    inv_row = await db.r2_lifecycle_runs.find_one(
        {"kind": "inventory"}, {"_id": 0}, sort=[("completed_at", -1)],
    )
    inv_age_min = _minutes_since((inv_row or {}).get("completed_at"), now)
    lifecycle_pct = 100.0 * (total / (inv_row or {}).get("total_objects", 1)) if inv_row and inv_row.get("total_objects") else 0.0

    # 4) Backup freshness.
    bh_row = await db.backup_health.find_one(
        {"mode": {"$in": ["complete", "complete-r2", "complete-nightly"]}},
        {"_id": 0}, sort=[("ts", -1)],
    )
    backup_age_min = _minutes_since((bh_row or {}).get("ts"), now)

    # ── Sub-scores ─────────────────────────────────────────────────────
    capacity_score = _capacity_score(gb, warn_gb, alert_gb)
    ownership_score = 100.0 * (owned / total) if total else 0.0
    orphan_pct = 100.0 * (orphans / total) if total else 0.0
    orphan_score = _clamp(100.0 - orphan_pct * 5.0)  # 20 % → 0
    retention_score = 100.0  # No accidental-delete signal wired yet.
    backup_score = (
        100.0 if (backup_age_min is not None and backup_age_min <= 60)
        else (75.0 if (backup_age_min is not None and backup_age_min <= 1440) else 0.0)
    )
    lifecycle_score = _clamp(lifecycle_pct)
    freshness_score = (
        100.0 if (inv_age_min is not None and inv_age_min <= 60 * 24)
        else (60.0 if (inv_age_min is not None and inv_age_min <= 60 * 24 * 7) else 0.0)
    )

    subs = {
        "capacity_score":   round(capacity_score, 1),
        "ownership_score":  round(ownership_score, 1),
        "orphan_score":     round(orphan_score, 1),
        "retention_score":  round(retention_score, 1),
        "backup_score":     round(backup_score, 1),
        "lifecycle_score":  round(lifecycle_score, 1),
        "freshness_score":  round(freshness_score, 1),
    }
    overall = round(sum(subs[k] * w for k, w in _WEIGHTS.items()), 1)

    return {
        "overall_score": overall,
        "band": _band(overall),
        "sub_scores": subs,
        "weights": _WEIGHTS,
        "capacity": {
            "gb": gb,
            "warn_gb": warn_gb,
            "alert_gb": alert_gb,
            "over_alert": gb > alert_gb,
        },
        "objects": {
            "total": total,
            "verified_owner": owned,
            "verified_orphan": orphans,
            "orphan_pct": round(orphan_pct, 2),
            "orphan_bytes": orphan_bytes,
        },
        "freshness": {
            "inventory_age_minutes": inv_age_min,
            "backup_age_minutes": backup_age_min,
        },
        "generated_at": now.isoformat(),
    }


async def health_summary(db, *, now: Optional[datetime] = None) -> Dict[str, Any]:
    """Alias — future room for cheap-path caching if OCC calls this
    multiple times per pod tick."""
    return await compute_storage_health(db, now=now)
