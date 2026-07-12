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
from typing import Any, Dict, List, Optional

from .classification import CLASSIFICATIONS
from .policy import (
    aggregate,
    evaluate_backup_footprint,
    evaluate_certified_waste,
    evaluate_evidence_freshness,
    evaluate_growth,
    evaluate_retention_compliance,
    evaluate_storage_cost,
    evaluate_technical_capacity,
    R2_USD_PER_GB_MONTH,
)


# Retained for backward compatibility of the response envelope so
# existing OCC/UI consumers do not break. Sub-scores are DERIVED from
# the composite policy verdict below — no independent scoring logic
# lives here anymore.
_WEIGHTS: Dict[str, float] = {
    "capacity_score":   0.20,
    "ownership_score":  0.20,
    "orphan_score":     0.15,
    "retention_score":  0.10,
    "backup_score":     0.15,
    "lifecycle_score":  0.10,
    "freshness_score":  0.10,
}


# ── Composite → legacy band mapping ────────────────────────────────
# Preserves backward compatibility of `band` / `overall_score` fields
# in the response envelope.  The composite policy verdict is the
# source of truth; band/score are cosmetic projections.
_STATUS_TO_BAND = {
    "HEALTHY": "GREEN",
    "ATTENTION": "AMBER",
    "CRITICAL": "RED",
    "UNKNOWN": "AMBER",
    "POLICY_REQUIRED": "AMBER",
}
_STATUS_TO_SCORE = {
    "HEALTHY": 95.0,
    "ATTENTION": 60.0,
    "CRITICAL": 20.0,
    "UNKNOWN": 55.0,
    "POLICY_REQUIRED": 55.0,
}


def _band(score: float) -> str:
    if score >= 85:
        return "GREEN"
    if score >= 65:
        return "AMBER"
    return "RED"


def _clamp(v: float) -> float:
    return max(0.0, min(100.0, v))


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

    # 2) Classification snapshot.
    cls_row = await db.r2_lifecycle_runs.find_one(
        {"kind": "classification"}, {"_id": 0}, sort=[("completed_at", -1)],
    )
    counts = (cls_row or {}).get("counts") or {c: 0 for c in CLASSIFICATIONS}
    total = sum(counts.values())
    owned = counts.get("VERIFIED_OWNER", 0)
    orphans = counts.get("VERIFIED_ORPHAN", 0)
    orphan_bytes = int((cls_row or {}).get("verified_orphan_bytes") or 0)
    orphan_pct_value = 100.0 * (orphans / total) if total else 0.0
    classifier_completed_at = (cls_row or {}).get("completed_at")
    classifier_age_days = None
    if classifier_completed_at:
        m = _minutes_since(classifier_completed_at, now)
        classifier_age_days = m / (60.0 * 24.0) if m is not None else None

    # 3) Inventory freshness.
    inv_row = await db.r2_lifecycle_runs.find_one(
        {"kind": "inventory"}, {"_id": 0}, sort=[("completed_at", -1)],
    )
    inv_age_min = _minutes_since((inv_row or {}).get("completed_at"), now)
    inv_age_hours = inv_age_min / 60.0 if inv_age_min is not None else None
    lifecycle_pct = 100.0 * (total / (inv_row or {}).get("total_objects", 1)) if inv_row and inv_row.get("total_objects") else 0.0

    # 4) Backup freshness.
    bh_row = await db.backup_health.find_one(
        {"mode": {"$in": ["complete", "complete-r2", "complete-nightly"]}},
        {"_id": 0}, sort=[("ts", -1)],
    )
    backup_age_min = _minutes_since((bh_row or {}).get("ts"), now)

    # 5) R2 usage signal freshness (last passive probe row).
    usage_signal_age_hours: Optional[float] = None
    if usage_row and usage_row.get("ts"):
        m = _minutes_since(usage_row.get("ts"), now)
        usage_signal_age_hours = m / 60.0 if m is not None else None

    # 6) Growth series — derive daily deltas from consecutive
    #    `r2-usage-*` rows (chronological). No inference, no fabrication.
    usage_cursor = db.backup_health.find(
        {"mode": {"$in": ["r2-usage-alert", "r2-usage-warn"]}},
        {"_id": 0, "ts": 1, "size_bytes": 1},
    ).sort("ts", 1)
    usage_rows = await usage_cursor.to_list(length=500)
    daily_deltas_gb: List[float] = []
    for i in range(1, len(usage_rows)):
        prev = usage_rows[i - 1]
        curr = usage_rows[i]
        try:
            prev_ts = datetime.fromisoformat(str(prev.get("ts", "")).replace("Z", "+00:00"))
            curr_ts = datetime.fromisoformat(str(curr.get("ts", "")).replace("Z", "+00:00"))
        except Exception:  # noqa: BLE001
            continue
        days = max((curr_ts - prev_ts).total_seconds() / 86400.0, 0.001)
        delta_gb = (int(curr.get("size_bytes") or 0) - int(prev.get("size_bytes") or 0)) / (1024 ** 3)
        daily_deltas_gb.append(delta_gb / days)

    # 7) Retention encoded windows (source-of-truth). Today only the
    #    Track 15.28A tiered backup contract is encoded — legal
    #    retention items remain POLICY_REQUIRED.
    encoded_windows: Dict[str, Any] = {
        "backup_tier1_days": 14,
        "backup_tier2_days": 90,
        "backup_tier3_days": 365,
    }

    # ── Composite policy evaluation ─────────────────────────────────
    dim_capacity = evaluate_technical_capacity(gb if usage_row or total else None)
    dim_cost = evaluate_storage_cost(gb if usage_row or total else None)
    dim_growth = evaluate_growth(daily_deltas_gb)
    dim_waste = evaluate_certified_waste(orphan_pct_value if total else None, classifier_age_days)
    dim_backup = evaluate_backup_footprint(backup_age_min, lifecycle_rule_applied=None)
    dim_retention = evaluate_retention_compliance(encoded_windows)
    dim_freshness = evaluate_evidence_freshness(inv_age_hours, usage_signal_age_hours)

    verdict = aggregate([
        dim_capacity, dim_cost, dim_growth, dim_waste,
        dim_backup, dim_retention, dim_freshness,
    ])

    # ── Backward-compatible sub-scores derived from composite ───────
    def _score_from_status(s: str) -> float:
        return _STATUS_TO_SCORE.get(s, 55.0)

    subs = {
        "capacity_score":   round(_score_from_status(dim_capacity.status), 1),
        "ownership_score":  round(100.0 * (owned / total) if total else 0.0, 1),
        "orphan_score":     round(_score_from_status(dim_waste.status), 1),
        "retention_score":  round(_score_from_status(dim_retention.status), 1),
        "backup_score":     round(_score_from_status(dim_backup.status), 1),
        "lifecycle_score":  round(_clamp(lifecycle_pct), 1),
        "freshness_score":  round(_score_from_status(dim_freshness.status), 1),
    }
    overall = round(sum(subs[k] * w for k, w in _WEIGHTS.items()), 1)
    band = _STATUS_TO_BAND[verdict.status]

    # Cost evidence (single canonical estimator; used for the
    # `estimated_monthly_usd` UI hint).
    estimated_monthly = round(gb * R2_USD_PER_GB_MONTH, 4) if gb else 0.0

    return {
        "overall_score": overall,
        "band": band,
        "sub_scores": subs,
        "weights": _WEIGHTS,
        "capacity": {
            "gb": gb,
            # Retained keys so legacy UI / OCC selectors do not KeyError.
            # These are DEPRECATED — the truthful signal is `policy_verdict`.
            # `over_alert` is now sourced from the composite technical
            # capacity dimension against the *provider* ceiling only.
            "warn_gb": None,
            "alert_gb": None,
            "over_alert": dim_capacity.status == "CRITICAL",
            "estimated_monthly_usd": estimated_monthly,
        },
        "objects": {
            "total": total,
            "verified_owner": owned,
            "verified_orphan": orphans,
            "orphan_pct": round(orphan_pct_value, 2),
            "orphan_bytes": orphan_bytes,
        },
        "freshness": {
            "inventory_age_minutes": inv_age_min,
            "backup_age_minutes": backup_age_min,
            "usage_signal_age_hours": (
                round(usage_signal_age_hours, 2)
                if usage_signal_age_hours is not None else None
            ),
        },
        # NEW · Composite policy verdict — the truthful signal.
        "policy_verdict": verdict.to_dict(),
        "generated_at": now.isoformat(),
    }


async def health_summary(db, *, now: Optional[datetime] = None) -> Dict[str, Any]:
    """Alias — future room for cheap-path caching if OCC calls this
    multiple times per pod tick."""
    return await compute_storage_health(db, now=now)
