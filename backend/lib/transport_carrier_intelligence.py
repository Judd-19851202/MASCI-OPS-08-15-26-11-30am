"""TRACK 16.12 · Carrier Intelligence.

Aggregates carrier health from existing MASCI sources only. Pure
async functions — no mutation of carrier records.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict, List, Optional

from lib.transport_intelligence_core import (
    TENANT, SCHEMA_VERSION, now_iso, now_dt, days_until, parse_iso,
    clamp, composite, derive_band, make_explanation,
    write_intelligence_audit,
)


async def _fleet_signals(db, carrier_id: str) -> Dict[str, Any]:
    trucks = await db.transport_trucks.find(
        {"tenant": TENANT, "carrier_id": carrier_id}).to_list(500)
    drivers = await db.transport_persons.find(
        {"tenant": TENANT, "carrier_id": carrier_id}).to_list(500)
    active_trucks = sum(1 for t in trucks if t.get("status") == "active")
    active_drivers = sum(1 for d in drivers if d.get("status") == "active")
    return {
        "fleet_size": len(trucks),
        "active_trucks": active_trucks,
        "active_drivers": active_drivers,
        "total_drivers": len(drivers),
        "drivers": drivers,
        "trucks": trucks,
    }


async def _average_eligibility(db, items: List[Dict[str, Any]],
                               target_type: str) -> Dict[str, Any]:
    eligible = 0
    blocked = 0
    states: Dict[str, int] = {}
    for it in items:
        row = await db.transport_eligibility_state.find_one({
            "tenant": TENANT, "target_type": target_type,
            "target_id": it["id"]})
        st = (row or {}).get("state") or "pending_review"
        states[st] = states.get(st, 0) + 1
        if st == "eligible":
            eligible += 1
        elif st in ("not_dispatchable", "suspended", "expired",
                     "needs_correction"):
            blocked += 1
    total = len(items)
    pct = (eligible / total * 100.0) if total else 0.0
    return {"eligible": eligible, "blocked": blocked,
            "states": states, "total": total, "pct_eligible": pct}


async def _packet_signal(db, carrier_id: str) -> Dict[str, Any]:
    try:
        pkt = await db.transport_carrier_packets.find_one(
            {"tenant": TENANT, "carrier_id": carrier_id})
    except Exception:  # noqa: BLE001
        pkt = None
    status = (pkt or {}).get("status")
    return {"packet_status": status, "rate_acknowledged":
            bool((pkt or {}).get("rate_acknowledged"))}


async def compute_carrier_intelligence(
    db, carrier_id: str, *, persist_audit: bool = True,
) -> Dict[str, Any]:
    carrier = await db.carriers.find_one(
        {"tenant": TENANT, "id": carrier_id})
    if not carrier:
        return {"ok": False, "error": "carrier_not_found",
                "carrier_id": carrier_id,
                "schema_version": SCHEMA_VERSION,
                "computed_at": now_iso()}

    fleet = await _fleet_signals(db, carrier_id)
    drivers_avg = await _average_eligibility(db, fleet["drivers"], "person")
    trucks_avg = await _average_eligibility(db, fleet["trucks"], "truck")
    packet = await _packet_signal(db, carrier_id)

    explanations: List[Dict[str, Any]] = []

    # Compliance — packet + rate + average eligibility.
    compliance = 100.0
    pkt = packet.get("packet_status")
    if pkt != "approved":
        delta = 25 if pkt in ("draft", "sent", "submitted", "pending_review",
                                 None) else 35
        compliance -= delta
        explanations.append(make_explanation(
            code=f"packet_{pkt or 'missing'}",
            label=f"Carrier packet status: {pkt or 'missing'}",
            impact="negative", weight=1.0, delta=-delta,
            fix="Approve carrier packet via Transportation admin",
        ))
    if not packet.get("rate_acknowledged"):
        compliance -= 10
        explanations.append(make_explanation(
            code="rate_not_acknowledged",
            label="Active rate schedule not acknowledged",
            impact="negative", weight=1.0, delta=-10,
            fix="Acknowledge current rate schedule",
        ))

    # Safety — carrier-level safety hold.
    safety = 100.0
    if carrier.get("safety_hold"):
        safety -= 35
        explanations.append(make_explanation(
            code="carrier_safety_hold",
            label="Carrier safety hold engaged",
            impact="negative", weight=1.0, delta=-35,
            fix="Resolve safety hold conditions",
        ))

    # Reliability — average driver/truck eligibility.
    reliability = clamp((drivers_avg["pct_eligible"] +
                          trucks_avg["pct_eligible"]) / 2 if (
                          drivers_avg["total"] or trucks_avg["total"]) else 50)
    explanations.append(make_explanation(
        code="fleet_eligibility",
        label=(f"{drivers_avg['eligible']}/{drivers_avg['total']} drivers "
                f"and {trucks_avg['eligible']}/{trucks_avg['total']} trucks "
                f"eligible"),
        impact="positive" if reliability >= 75 else "watch",
        weight=2.0, delta=reliability - 50,
    ))

    # Experience proxy — years partnered.
    created = parse_iso(carrier.get("created_at"))
    years = int((now_dt() - created).days / 365.25) if created else 0
    experience = clamp(50 + min(50, years * 10))
    explanations.append(make_explanation(
        code="years_partnered",
        label=f"{years} year(s) partnered with MASCI",
        impact="positive", weight=1.0, delta=experience - 50,
    ))

    overall = composite([
        {"score": compliance, "weight": 2.0},
        {"score": safety, "weight": 2.0},
        {"score": reliability, "weight": 2.0},
        {"score": experience, "weight": 1.0},
    ])
    preferred = bool(overall >= 85 and safety >= 80 and compliance >= 80)

    snapshot = {
        "carrier_id": carrier_id,
        "legal_name": carrier.get("legal_name"),
        "dba_name": carrier.get("dba_name"),
        "carrier_type": carrier.get("carrier_type"),
        "fleet": {
            "fleet_size": fleet["fleet_size"],
            "active_trucks": fleet["active_trucks"],
            "active_drivers": fleet["active_drivers"],
            "total_drivers": fleet["total_drivers"],
            "drivers_eligible_pct": round(drivers_avg["pct_eligible"], 2),
            "trucks_eligible_pct": round(trucks_avg["pct_eligible"], 2),
        },
        "indices": {
            "compliance": derive_band(compliance),
            "safety": derive_band(safety),
            "reliability": derive_band(reliability),
            "experience": derive_band(experience),
        },
        "packet": packet,
        "overall": derive_band(overall),
        "preferred_status": preferred,
        "explanations": explanations,
        "signals": {
            "fleet_size": fleet["fleet_size"],
            "drivers_eligible": drivers_avg["eligible"],
            "trucks_eligible": trucks_avg["eligible"],
            "years_partnered": years,
            "carrier_safety_hold": bool(carrier.get("safety_hold")),
        },
        "computed_at": now_iso(),
        "schema_version": SCHEMA_VERSION,
    }

    if persist_audit:
        await write_intelligence_audit(
            db, kind="carrier_intelligence_refresh",
            subject_type="carrier", subject_id=carrier_id,
            snapshot={"overall": snapshot["overall"],
                      "indices": snapshot["indices"],
                      "signals": snapshot["signals"]})
    return snapshot


async def list_carrier_intelligence(db, *, limit: int = 200
                                     ) -> List[Dict[str, Any]]:
    carriers = await db.carriers.find(
        {"tenant": TENANT}).limit(limit).to_list(limit)
    out: List[Dict[str, Any]] = []
    for c in carriers:
        snap = await compute_carrier_intelligence(
            db, c["id"], persist_audit=False)
        if snap.get("ok", True):
            out.append(snap)
    return out
