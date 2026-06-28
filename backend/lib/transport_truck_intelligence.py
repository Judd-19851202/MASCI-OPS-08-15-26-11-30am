"""TRACK 16.12 · Truck Intelligence."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from lib.transport_intelligence_core import (
    TENANT, SCHEMA_VERSION, now_iso, days_until, parse_iso, now_dt,
    clamp, composite, derive_band, make_explanation,
    write_intelligence_audit,
)


async def _inspection_signal(db, truck_id: str) -> Dict[str, Any]:
    try:
        latest = await db.transport_truck_inspections.find_one(
            {"tenant": TENANT, "transport_truck_id": truck_id},
            sort=[("inspected_at", -1)])
    except Exception:  # noqa: BLE001
        latest = None
    if not latest:
        return {"result": None, "inspected_at": None,
                "days_since_inspection": None, "id": None}
    inspected = parse_iso(latest.get("inspected_at"))
    return {
        "result": latest.get("result"),
        "inspected_at": latest.get("inspected_at"),
        "days_since_inspection": (
            int((now_dt() - inspected).days) if inspected else None),
        "id": latest.get("id"),
    }


async def compute_truck_intelligence(
    db, truck_id: str, *, persist_audit: bool = True,
) -> Dict[str, Any]:
    truck = await db.transport_trucks.find_one(
        {"tenant": TENANT, "id": truck_id})
    if not truck:
        return {"ok": False, "error": "truck_not_found",
                "truck_id": truck_id,
                "schema_version": SCHEMA_VERSION,
                "computed_at": now_iso()}

    elig = await db.transport_eligibility_state.find_one({
        "tenant": TENANT, "target_type": "truck", "target_id": truck_id})

    inspection = await _inspection_signal(db, truck_id)
    explanations: List[Dict[str, Any]] = []
    base = 100.0

    elig_state = (elig or {}).get("state") or "pending_review"
    elig_penalty = {
        "eligible": 0, "pending_review": 10, "needs_correction": 25,
        "suspended": 40, "expired": 30, "not_dispatchable": 60,
    }.get(elig_state, 30)
    base -= elig_penalty
    explanations.append(make_explanation(
        code=f"eligibility_{elig_state}",
        label=f"Eligibility state: {elig_state.replace('_', ' ')}",
        impact="negative" if elig_penalty else "positive",
        weight=1.0, delta=-elig_penalty,
        fix="Resolve inspection / documentation / DOT compliance"
            if elig_penalty else None,
    ))

    if truck.get("safety_hold"):
        base -= 30
        explanations.append(make_explanation(
            code="truck_safety_hold", label="Truck safety hold engaged",
            impact="negative", weight=1.0, delta=-30,
            fix="Resolve safety hold conditions",
        ))

    if inspection["result"] == "ready":
        explanations.append(make_explanation(
            code="inspection_ready", label="Truck inspection: ready",
            impact="positive", weight=1.0, delta=0,
            record_id=inspection.get("id"),
            record_type="transport_truck_inspection",
        ))
    elif inspection["result"] == "not_ready":
        base -= 35
        explanations.append(make_explanation(
            code="inspection_not_ready", label="Truck inspection: not ready",
            impact="negative", weight=1.0, delta=-35,
            record_id=inspection.get("id"),
            record_type="transport_truck_inspection",
            fix="Resolve inspection findings",
        ))
    elif inspection["result"] is None:
        base -= 20
        explanations.append(make_explanation(
            code="inspection_missing",
            label="No truck inspection on file",
            impact="negative", weight=1.0, delta=-20,
            fix="Complete the MASCI Hauler Readiness Inspection",
        ))

    # Days since inspection — staleness signal.
    dsi = inspection.get("days_since_inspection")
    if isinstance(dsi, int) and dsi >= 180:
        base -= 15
        explanations.append(make_explanation(
            code="inspection_stale",
            label=f"Last inspection {dsi} days ago",
            impact="watch", weight=0.5, delta=-15,
            fix="Schedule a fresh inspection",
        ))

    # Mechanical readiness derived from status + safety_hold + inspection.
    mechanical = clamp(base)
    overall = composite([
        {"score": mechanical, "weight": 2.0},
        {"score": 100 if not truck.get("safety_hold") else 60, "weight": 1.0},
        {"score": 100 if elig_state == "eligible" else 60, "weight": 1.0},
    ])

    snapshot = {
        "truck_id": truck_id,
        "truck_number": truck.get("truck_number"),
        "ownership": truck.get("ownership"),
        "truck_type": truck.get("truck_type"),
        "carrier_id": truck.get("carrier_id"),
        "indices": {
            "mechanical_readiness": derive_band(mechanical),
            "dot_compliance": derive_band(
                100 if elig_state == "eligible" else 60),
        },
        "overall": derive_band(overall),
        "inspection": inspection,
        "eligibility_state": elig_state,
        "explanations": explanations,
        "signals": {
            "inspection_result": inspection.get("result"),
            "safety_hold": bool(truck.get("safety_hold")),
            "days_since_inspection": dsi,
        },
        "computed_at": now_iso(),
        "schema_version": SCHEMA_VERSION,
    }

    if persist_audit:
        await write_intelligence_audit(
            db, kind="truck_intelligence_refresh",
            subject_type="transport_truck",
            subject_id=truck_id,
            snapshot={"overall": snapshot["overall"],
                      "indices": snapshot["indices"],
                      "signals": snapshot["signals"]})
    return snapshot


async def list_truck_intelligence(db, *, limit: int = 200
                                   ) -> List[Dict[str, Any]]:
    trucks = await db.transport_trucks.find(
        {"tenant": TENANT}).limit(limit).to_list(limit)
    out: List[Dict[str, Any]] = []
    for t in trucks:
        snap = await compute_truck_intelligence(
            db, t["id"], persist_audit=False)
        if snap.get("ok", True):
            out.append(snap)
    return out
