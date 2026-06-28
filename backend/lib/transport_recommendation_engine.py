"""TRACK 16.12 · Recommendation Engine.

Deterministic ranking of drivers / carriers / trucks for dispatch.
NEVER fabricates. Reasons are derived from the intelligence snapshots
(driver/carrier/truck) — same engine, no duplicate logic.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from lib.transport_intelligence_core import (
    TENANT, SCHEMA_VERSION, now_iso, write_intelligence_audit,
)


def _eligibility_filter(snap: Dict[str, Any]) -> bool:
    """Hard filter: only surface entities that are currently eligible
    OR pending review with a fair-or-better score."""
    state = snap.get("eligibility_state")
    if state == "eligible":
        return True
    if state == "pending_review":
        score = snap.get("overall", {}).get("score", 0)
        return score >= 60
    return False


def _why(snap: Dict[str, Any]) -> List[str]:
    """Collect positive explanation labels — operator-facing 'why'."""
    out = []
    for e in snap.get("explanations", []) or []:
        if e.get("impact") == "positive" and (e.get("delta") or 0) >= 0:
            out.append(e["label"])
    if not out:
        out.append("Highest composite score among eligible candidates")
    return out[:6]


def _watch(snap: Dict[str, Any]) -> List[str]:
    out = []
    for e in snap.get("explanations", []) or []:
        if e.get("impact") in ("watch", "negative"):
            out.append(e["label"])
    return out[:6]


async def recommend_drivers(
    db, *, limit: int = 10, carrier_id: Optional[str] = None,
) -> Dict[str, Any]:
    from lib.transport_driver_intelligence import list_driver_intelligence
    snaps = await list_driver_intelligence(db, limit=500)
    if carrier_id:
        snaps = [s for s in snaps if (s.get("carrier_id") == carrier_id
                                       or _matches_carrier(s, carrier_id))]
    eligible = [s for s in snaps if _eligibility_filter(s)]
    eligible.sort(key=lambda s: (
        s.get("overall", {}).get("score", 0),
        s.get("indices", {}).get("safety", {}).get("score", 0),
    ), reverse=True)
    out = []
    for snap in eligible[:limit]:
        out.append({
            "driver_id": snap["driver_id"],
            "display_name": snap["display_name"],
            "overall": snap["overall"],
            "operational_readiness": snap["operational_readiness"],
            "kind": snap["kind"],
            "why": _why(snap),
            "watch": _watch(snap),
        })
    await write_intelligence_audit(
        db, kind="driver_recommendations_generated",
        subject_type="recommendation", subject_id=None,
        snapshot={"limit": limit, "count": len(out),
                  "carrier_id": carrier_id,
                  "candidates_considered": len(snaps)})
    return {"ok": True, "count": len(out), "candidates_considered": len(snaps),
            "items": out, "schema_version": SCHEMA_VERSION,
            "generated_at": now_iso()}


def _matches_carrier(snap: Dict[str, Any], carrier_id: str) -> bool:
    """Defensive fallback in case carrier_id wasn't denormalised onto
    the snapshot. Match via signals.carrier_id when present."""
    return snap.get("signals", {}).get("carrier_id") == carrier_id


async def recommend_carriers(db, *, limit: int = 10) -> Dict[str, Any]:
    from lib.transport_carrier_intelligence import list_carrier_intelligence
    snaps = await list_carrier_intelligence(db, limit=500)
    snaps.sort(key=lambda s: (
        s.get("overall", {}).get("score", 0),
        s.get("indices", {}).get("reliability", {}).get("score", 0),
    ), reverse=True)
    out = []
    for s in snaps[:limit]:
        out.append({
            "carrier_id": s["carrier_id"],
            "legal_name": s["legal_name"],
            "overall": s["overall"],
            "preferred_status": s.get("preferred_status"),
            "why": _why(s),
            "watch": _watch(s),
        })
    await write_intelligence_audit(
        db, kind="carrier_recommendations_generated",
        subject_type="recommendation", subject_id=None,
        snapshot={"limit": limit, "count": len(out),
                  "candidates_considered": len(snaps)})
    return {"ok": True, "count": len(out),
            "candidates_considered": len(snaps),
            "items": out, "schema_version": SCHEMA_VERSION,
            "generated_at": now_iso()}


async def recommend_trucks(
    db, *, limit: int = 10, carrier_id: Optional[str] = None,
    truck_type: Optional[str] = None,
) -> Dict[str, Any]:
    from lib.transport_truck_intelligence import list_truck_intelligence
    snaps = await list_truck_intelligence(db, limit=500)
    if carrier_id:
        snaps = [s for s in snaps if s.get("carrier_id") == carrier_id]
    if truck_type:
        snaps = [s for s in snaps if s.get("truck_type") == truck_type]
    eligible = [s for s in snaps if _eligibility_filter(s)]
    eligible.sort(key=lambda s: s.get("overall", {}).get("score", 0),
                   reverse=True)
    out = []
    for s in eligible[:limit]:
        out.append({
            "truck_id": s["truck_id"],
            "truck_number": s["truck_number"],
            "truck_type": s["truck_type"],
            "carrier_id": s.get("carrier_id"),
            "overall": s["overall"],
            "why": _why(s),
            "watch": _watch(s),
        })
    await write_intelligence_audit(
        db, kind="truck_recommendations_generated",
        subject_type="recommendation", subject_id=None,
        snapshot={"limit": limit, "count": len(out),
                  "carrier_id": carrier_id, "truck_type": truck_type,
                  "candidates_considered": len(snaps)})
    return {"ok": True, "count": len(out),
            "candidates_considered": len(snaps),
            "items": out, "schema_version": SCHEMA_VERSION,
            "generated_at": now_iso()}


async def recommend_dispatch_triple(
    db, *, carrier_id: Optional[str] = None,
    truck_type: Optional[str] = None,
) -> Dict[str, Any]:
    """Return the top driver + truck + carrier triple — operator-facing
    composite recommendation."""
    drivers = await recommend_drivers(db, limit=1, carrier_id=carrier_id)
    trucks = await recommend_trucks(
        db, limit=1, carrier_id=carrier_id, truck_type=truck_type)
    carriers = await recommend_carriers(db, limit=1)
    return {
        "ok": True,
        "driver": (drivers["items"] or [None])[0],
        "truck": (trucks["items"] or [None])[0],
        "carrier": (carriers["items"] or [None])[0],
        "schema_version": SCHEMA_VERSION,
        "generated_at": now_iso(),
    }
