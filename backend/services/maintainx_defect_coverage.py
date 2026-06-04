"""
MaintainX Defect Source Coverage — read-only intelligence service.

Aggregates every equipment-defect source in ForgedOps into a single
operational view. Computes per-source totals plus a per-defect
readiness classification (READY / BLOCKED / DUPLICATE_RISK / EXCLUDED).

SAFETY: This module performs ZERO writes. It only runs `find()` reads
against existing operational collections. It never calls MaintainX.

Public entrypoint:
    `run_defect_coverage(db, *, sample_limit=200, since_days=30)`
        → CoverageReport
"""
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Optional, Tuple

# ─── Classification constants ────────────────────────────────────────
READY          = "READY"
BLOCKED        = "BLOCKED"
DUPLICATE_RISK = "DUPLICATE_RISK"
EXCLUDED       = "EXCLUDED"

# Source ids (mirror Phase 3 canonical_defect_payload spec)
SRC_FLEET_DVIR        = "fleet_dvir"
SRC_EQUIPMENT_PREOP   = "equipment_preop"
SRC_EQUIPMENT_INSP    = "equipment_inspection"
SRC_DISPATCH_BREAKDWN = "dispatch_breakdown"
SRC_SHOP_ISSUE        = "shop_issue"
SRC_MANUAL_OOS        = "manual_oos"

ALL_SOURCES = [
    SRC_FLEET_DVIR,
    SRC_EQUIPMENT_PREOP,
    SRC_EQUIPMENT_INSP,
    SRC_DISPATCH_BREAKDWN,
    SRC_SHOP_ISSUE,
    SRC_MANUAL_OOS,
]

# Pretty labels for the UI
SOURCE_LABEL = {
    SRC_FLEET_DVIR:        "Fleet DVIR",
    SRC_EQUIPMENT_PREOP:   "Equipment Pre-Op",
    SRC_EQUIPMENT_INSP:    "Equipment Inspection",
    SRC_DISPATCH_BREAKDWN: "Dispatch Breakdown",
    SRC_SHOP_ISSUE:        "Shop Issues",
    SRC_MANUAL_OOS:        "Manual OOS",
}


def _now() -> datetime:
    return datetime.now(timezone.utc)


def _iso(d: Optional[datetime]) -> Optional[str]:
    return d.isoformat() if d else None


def _norm_unit(value: Optional[str]) -> str:
    if not value:
        return ""
    return re.sub(r"[^A-Z0-9]+", "", str(value).upper())


# ═════════════════════════════════════════════════════════════════════
# Loaders — strictly read-only `find()` calls
# ═════════════════════════════════════════════════════════════════════
async def _load_fleet_defects(db) -> List[Dict[str, Any]]:
    """Open fleet defects (status != cleared, severity != null). Includes
    manual-OOS rows (inspection_kind == 'manual_oos') so we can split them
    out in classification."""
    cursor = db.fleet_defects.find(
        {"status": {"$ne": "cleared"}},
        {"_id": 0},
    ).sort("reported_at", -1)
    return await cursor.to_list(2000)


async def _load_equipment_inspections_with_fails(db, since_days: int) -> List[Dict[str, Any]]:
    """Equipment inspections (Pre-Op + scheduled) with at least one
    failure, within the lookback window. The collection is shared between
    fleet DVIR and heavy-equipment Pre-Op (see Phase 1 §3/§4); we discriminate
    by the `kind` field below."""
    since = _now() - timedelta(days=int(since_days))
    cursor = db.equipment_inspections.find(
        {
            "fail_count": {"$gt": 0},
            "created_at": {"$gte": since.isoformat()},
        },
        {"_id": 0},
    ).sort("created_at", -1)
    return await cursor.to_list(2000)


async def _load_active_holds(db) -> List[Dict[str, Any]]:
    """Active maintenance holds (`asset_holds.active == True`)."""
    cursor = db.asset_holds.find({"active": True}, {"_id": 0}).sort("created_at", -1)
    return await cursor.to_list(2000)


async def _load_asset_mappings(db) -> Dict[str, Dict[str, Any]]:
    """Index of `masci_equipment_id → mapping doc` for quick lookups."""
    rows = await db.asset_mappings.find({}, {"_id": 0}).to_list(20000)
    return {r.get("masci_equipment_id", ""): r for r in rows if r.get("masci_equipment_id")}


async def _load_equipment_master(db) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Dict[str, Any]]]:
    """Return (`by_id`, `by_unit_norm`) lookups."""
    rows = await db.equipment_master.find({}, {"_id": 0}).to_list(20000)
    by_id: Dict[str, Dict[str, Any]] = {r["id"]: r for r in rows if r.get("id")}
    by_unit: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        u = _norm_unit(r.get("unit_number"))
        if u:
            by_unit[u] = r
    return by_id, by_unit


# ═════════════════════════════════════════════════════════════════════
# Per-source normalisation → canonical "defect row" used by classifier
# ═════════════════════════════════════════════════════════════════════
def _norm_fleet_defect(row: Dict[str, Any], eq_by_unit: Dict) -> Dict[str, Any]:
    unit = row.get("trailer_unit_number") or row.get("truck_unit_number") or ""
    eq = eq_by_unit.get(_norm_unit(unit), {})
    is_manual = (row.get("inspection_kind") == "manual_oos")
    sev_raw = (row.get("severity") or "").lower()
    return {
        "source_type":      SRC_MANUAL_OOS if is_manual else SRC_FLEET_DVIR,
        "source_record_id": row.get("id") or "",
        "source_collection": "fleet_defects",
        "equipment_id":     eq.get("id") or "",
        "unit_number":      unit,
        "equipment_name":   eq.get("display_label") or eq.get("make_model") or "",
        "make":             eq.get("make") or "",
        "model":            eq.get("model") or "",
        "reported_by":      row.get("reported_by_name") or "",
        "reported_at":      row.get("reported_at") or row.get("created_at") or "",
        "severity":         "oos" if sev_raw == "oos" else ("monitor" if sev_raw == "monitor" else (sev_raw or "")),
        "status":           row.get("status") or "open",
        "out_of_service":   sev_raw == "oos",
        "safety_critical":  sev_raw == "oos",
        "photos_present":   bool(row.get("photos")),
        "defect_title":     (row.get("item_text") or "")[:200],
        "rts_required":     sev_raw == "oos",
    }


def _norm_inspection(row: Dict[str, Any], eq_by_unit: Dict) -> Dict[str, Any]:
    # The equipment_inspections collection serves BOTH heavy-equipment
    # Pre-Op (no `kind`, has `equipment_unit`) and Fleet DVIR (`kind` in
    # {pre_op, weekly_lead, weekly_emergency, dvir}). We discriminate here.
    is_fleet = bool(row.get("kind"))
    unit = row.get("truck_unit_number") or row.get("equipment_unit") or ""
    eq = eq_by_unit.get(_norm_unit(unit), {})
    oos = (row.get("out_of_service") == "Yes")
    fail_n = int(row.get("fail_count") or 0)

    if is_fleet:
        source_type = SRC_FLEET_DVIR
        title = f"DVIR — {fail_n} failed item(s)"
    else:
        # Heavy equipment pre-op shape (legacy + canonical)
        source_type = SRC_EQUIPMENT_PREOP
        title = f"Failed pre-op — {unit or '—'} ({fail_n} items)"

    severity = "oos" if oos else "monitor"
    return {
        "source_type":      source_type,
        "source_record_id": row.get("id") or "",
        "source_collection": "equipment_inspections",
        "equipment_id":     eq.get("id") or "",
        "unit_number":      unit,
        "equipment_name":   eq.get("display_label") or row.get("equipment_make") or "",
        "make":             eq.get("make") or row.get("equipment_make") or "",
        "model":            eq.get("model") or row.get("equipment_model") or "",
        "reported_by":      row.get("driver_name") or row.get("operator_name") or "",
        "reported_at":      row.get("created_at") or row.get("inspection_date") or "",
        "severity":         severity,
        "status":           "open",   # inspections don't carry a per-row close lifecycle
        "out_of_service":   oos,
        "safety_critical":  oos,
        "photos_present":   bool(row.get("photos")),
        "defect_title":     title[:200],
        "rts_required":     oos,
    }


def _norm_hold(row: Dict[str, Any], eq_by_id: Dict) -> Dict[str, Any]:
    eq = eq_by_id.get(row.get("asset_id"), {})
    severity_raw = (row.get("severity") or "").lower()
    oos = severity_raw in {"high", "critical", "oos"}
    return {
        "source_type":      SRC_MANUAL_OOS if row.get("source_module") in {"admin", "manual"}
                            else (SRC_SHOP_ISSUE if row.get("source_module") == "shop"
                            else (SRC_DISPATCH_BREAKDWN if row.get("source_module") == "dispatch"
                            else SRC_MANUAL_OOS)),
        "source_record_id": row.get("id") or "",
        "source_collection": "asset_holds",
        "equipment_id":     eq.get("id") or row.get("asset_id") or "",
        "unit_number":      eq.get("unit_number") or "",
        "equipment_name":   eq.get("display_label") or eq.get("make_model") or "",
        "make":             eq.get("make") or "",
        "model":            eq.get("model") or "",
        "reported_by":      row.get("created_by") or "",
        "reported_at":      row.get("created_at") or "",
        "severity":         severity_raw or "medium",
        "status":           "open" if row.get("active") else "cleared",
        "out_of_service":   bool(row.get("active")) and oos,
        "safety_critical":  oos,
        "photos_present":   False,
        "defect_title":     (row.get("reason") or "Maintenance hold")[:200],
        "rts_required":     bool(row.get("active")),
    }


# ═════════════════════════════════════════════════════════════════════
# Classifier
# ═════════════════════════════════════════════════════════════════════
def _classify(
    d: Dict[str, Any],
    *, asset_map: Dict[str, Dict[str, Any]],
    open_by_unit_title: Dict[Tuple[str, str], int],
) -> Dict[str, Any]:
    """Decide READY / BLOCKED / DUPLICATE_RISK / EXCLUDED. Returns a dict
    with `readiness`, `maintainx_status`, `reasons[]`."""
    reasons: List[str] = []

    # EXCLUDED — closed / cleared / no maintenance action
    if d.get("status") in {"cleared", "repaired", "closed"}:
        return {
            "readiness": EXCLUDED, "maintainx_status": "Excluded",
            "reasons": [f"status={d.get('status')}"],
        }

    # BLOCKED — missing critical identity fields
    if not d.get("equipment_id"):
        reasons.append("missing_equipment")
    if not d.get("unit_number"):
        reasons.append("missing_unit_number")
    if not d.get("source_record_id"):
        reasons.append("missing_source_reference")
    if reasons:
        return {"readiness": BLOCKED, "maintainx_status": "Blocked", "reasons": reasons}

    # DUPLICATE_RISK — another open defect on same unit + same title within set
    key = (_norm_unit(d.get("unit_number")), (d.get("defect_title") or "").strip().upper())
    if open_by_unit_title.get(key, 0) > 1:
        return {
            "readiness": DUPLICATE_RISK, "maintainx_status": "Duplicate Risk",
            "reasons": [f"multiple_open_defects_same_unit_same_title (n={open_by_unit_title[key]})"],
        }

    # READY — has an asset_mappings.maintainx.asset_id? If not, still
    # classify as READY but flag the MaintainX status as "Not Evaluated".
    mapping = asset_map.get(d.get("equipment_id")) or {}
    mx_asset_id = ((mapping.get("maintainx") or {}).get("asset_id") or "").strip()
    if mx_asset_id:
        return {
            "readiness": READY, "maintainx_status": "Mapped",
            "reasons": ["asset_mapped"], "maintainx_asset_id": mx_asset_id,
        }
    return {
        "readiness": READY, "maintainx_status": "Ready",
        "reasons": ["asset_unmapped_but_classifiable"],
    }


# ═════════════════════════════════════════════════════════════════════
# Public pipeline
# ═════════════════════════════════════════════════════════════════════
async def run_defect_coverage(
    db, *, sample_limit: int = 200, since_days: int = 30,
) -> Dict[str, Any]:
    """Compute the full defect-source coverage view. Pure read pipeline."""
    started_at = _now().isoformat()

    # Loaders run concurrently is not needed at this scale — keep simple.
    fleet_defects = await _load_fleet_defects(db)
    inspections   = await _load_equipment_inspections_with_fails(db, since_days)
    holds         = await _load_active_holds(db)
    asset_map     = await _load_asset_mappings(db)
    eq_by_id, eq_by_unit = await _load_equipment_master(db)

    canonical: List[Dict[str, Any]] = []
    for r in fleet_defects:
        canonical.append(_norm_fleet_defect(r, eq_by_unit))
    for r in inspections:
        canonical.append(_norm_inspection(r, eq_by_unit))
    for r in holds:
        canonical.append(_norm_hold(r, eq_by_id))

    # Build the (unit_norm, title) frequency table for duplicate-risk detection
    open_by_unit_title: Dict[Tuple[str, str], int] = {}
    for d in canonical:
        if d.get("status") in {"cleared", "repaired", "closed"}:
            continue
        key = (_norm_unit(d.get("unit_number")), (d.get("defect_title") or "").strip().upper())
        open_by_unit_title[key] = open_by_unit_title.get(key, 0) + 1

    # Classify
    for d in canonical:
        d["classification"] = _classify(
            d, asset_map=asset_map, open_by_unit_title=open_by_unit_title,
        )

    # Source breakdown counts
    breakdown: Dict[str, Dict[str, int]] = {
        s: {"total": 0, "open": 0, "oos": 0, "safety_critical": 0,
            "ready": 0, "blocked": 0, "duplicate_risk": 0, "excluded": 0, "mapped": 0}
        for s in ALL_SOURCES
    }
    totals = {
        "open_defects": 0, "high_severity": 0, "safety_critical": 0,
        "out_of_service": 0, "ready_for_maintainx": 0, "blocked": 0,
        "duplicate_risk": 0, "mapped": 0, "excluded": 0,
    }

    for d in canonical:
        s = d.get("source_type") or SRC_MANUAL_OOS
        if s not in breakdown:
            breakdown[s] = {"total": 0, "open": 0, "oos": 0, "safety_critical": 0,
                            "ready": 0, "blocked": 0, "duplicate_risk": 0,
                            "excluded": 0, "mapped": 0}
        cls = d["classification"]["readiness"]
        mx_status = d["classification"]["maintainx_status"]

        breakdown[s]["total"] += 1
        if d.get("status") not in {"cleared", "repaired", "closed"}:
            breakdown[s]["open"] += 1
            totals["open_defects"] += 1
            if d.get("out_of_service"):
                breakdown[s]["oos"] += 1
                totals["out_of_service"] += 1
            if d.get("safety_critical"):
                breakdown[s]["safety_critical"] += 1
                totals["safety_critical"] += 1
            if d.get("severity") in {"oos", "high", "critical"}:
                totals["high_severity"] += 1
        if cls == READY:
            breakdown[s]["ready"] += 1
            totals["ready_for_maintainx"] += 1
        elif cls == BLOCKED:
            breakdown[s]["blocked"] += 1
            totals["blocked"] += 1
        elif cls == DUPLICATE_RISK:
            breakdown[s]["duplicate_risk"] += 1
            totals["duplicate_risk"] += 1
        elif cls == EXCLUDED:
            breakdown[s]["excluded"] += 1
            totals["excluded"] += 1
        if mx_status == "Mapped":
            breakdown[s]["mapped"] += 1
            totals["mapped"] += 1

    # Sort sample: OOS first, then duplicate-risk, then by reported_at desc
    canonical.sort(
        key=lambda d: (
            0 if d.get("out_of_service") else (1 if d["classification"]["readiness"] == DUPLICATE_RISK else 2),
            -1 * (len(d.get("reported_at") or "")),  # cheap "newer first"
            d.get("reported_at") or "",
        ),
    )

    sample = canonical[: max(1, min(int(sample_limit or 200), 1000))]

    return {
        "started_at": started_at,
        "since_days": since_days,
        "totals": totals,
        "breakdown": [
            {"source_type": s, "label": SOURCE_LABEL.get(s, s), **breakdown.get(s, {})}
            for s in ALL_SOURCES
        ],
        "defects": sample,
        "writes_performed": {
            "maintainx": 0, "equipment_master": 0, "fleet_defects": 0,
            "equipment_inspections": 0, "asset_holds": 0, "asset_mappings": 0,
        },
    }


__all__ = [
    "run_defect_coverage",
    "READY", "BLOCKED", "DUPLICATE_RISK", "EXCLUDED",
    "ALL_SOURCES", "SOURCE_LABEL",
]
