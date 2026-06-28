"""TRACK 16.12 · Transportation Operations Intelligence — orchestrator.

Single composer that turns the per-entity intelligence libraries into
an executive dashboard. The dashboard NEVER recomputes business logic
locally — it delegates to the canonical compute_* functions.
"""
from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict, List

from lib.transport_intelligence_core import (
    TENANT, SCHEMA_VERSION, now_iso, now_dt, parse_iso,
    write_intelligence_audit, derive_band, composite, clamp,
)


def _avg_score(snaps: List[Dict[str, Any]], path: str) -> float:
    if not snaps:
        return 0.0
    total = 0.0
    n = 0
    keys = path.split(".")
    for s in snaps:
        v: Any = s
        for k in keys:
            if not isinstance(v, dict):
                v = None
                break
            v = v.get(k)
        if isinstance(v, (int, float)):
            total += float(v)
            n += 1
    return total / n if n else 0.0


def _top(snaps: List[Dict[str, Any]], n: int = 5) -> List[Dict[str, Any]]:
    return sorted(
        snaps, key=lambda s: s.get("overall", {}).get("score", 0),
        reverse=True)[:n]


def _attention(snaps: List[Dict[str, Any]], n: int = 5) -> List[Dict[str, Any]]:
    return sorted(
        snaps, key=lambda s: s.get("overall", {}).get("score", 0))[:n]


async def _trends(db) -> Dict[str, Any]:
    """Pull intelligence audit history and bucket overall scores by
    30 / 90 / 365 day windows. Deterministic averages — no forecasting."""
    now = now_dt()
    horizons = {"30d": 30, "90d": 90, "365d": 365}
    out: Dict[str, Any] = {}
    for label, days in horizons.items():
        since = (now - timedelta(days=days)).isoformat()
        rows = await db.transport_intelligence_audit.find({
            "tenant": TENANT,
            "kind": {"$in": ["driver_intelligence_refresh",
                              "carrier_intelligence_refresh",
                              "truck_intelligence_refresh"]},
            "ts": {"$gte": since},
        }).to_list(5000)
        totals = {"driver_intelligence_refresh": [],
                  "carrier_intelligence_refresh": [],
                  "truck_intelligence_refresh": []}
        for r in rows:
            try:
                sc = r["snapshot"]["overall"]["score"]
                totals[r["kind"]].append(float(sc))
            except Exception:  # noqa: BLE001
                continue
        out[label] = {
            kind: {"avg_score": round(sum(v) / len(v), 2) if v else None,
                    "samples": len(v)}
            for kind, v in totals.items()
        }
    return out


async def build_executive_dashboard(db) -> Dict[str, Any]:
    from lib.transport_driver_intelligence import list_driver_intelligence
    from lib.transport_carrier_intelligence import list_carrier_intelligence
    from lib.transport_truck_intelligence import list_truck_intelligence

    drivers = await list_driver_intelligence(db, limit=500)
    carriers = await list_carrier_intelligence(db, limit=500)
    trucks = await list_truck_intelligence(db, limit=500)

    driver_avg = _avg_score(drivers, "overall.score")
    carrier_avg = _avg_score(carriers, "overall.score")
    truck_avg = _avg_score(trucks, "overall.score")

    # Operational health rolls everything up — drivers + carriers + trucks
    # weighted equally so no surface drowns out the others.
    operational_health = composite([
        {"score": driver_avg, "weight": 2.0},
        {"score": carrier_avg, "weight": 1.5},
        {"score": truck_avg, "weight": 1.5},
    ])

    # Dispatch readiness — share of eligible drivers + trucks.
    eligible_drivers = sum(1 for d in drivers
                            if d.get("eligibility_state") == "eligible")
    eligible_trucks = sum(1 for t in trucks
                           if t.get("eligibility_state") == "eligible")
    dispatch_readiness = clamp(
        ((eligible_drivers + eligible_trucks)
         / max(1, len(drivers) + len(trucks))) * 100.0)

    # Capacity proxy — eligible counts.
    capacity = {
        "drivers": {"total": len(drivers), "eligible": eligible_drivers,
                     "pct_eligible": round(
                         (eligible_drivers / len(drivers) * 100) if drivers else 0, 2)},
        "trucks": {"total": len(trucks), "eligible": eligible_trucks,
                    "pct_eligible": round(
                        (eligible_trucks / len(trucks) * 100) if trucks else 0, 2)},
        "carriers": {"total": len(carriers)},
    }

    trends = await _trends(db)

    dashboard = {
        "ok": True,
        "schema_version": SCHEMA_VERSION,
        "generated_at": now_iso(),
        "transportation_health": derive_band(operational_health),
        "driver_health": derive_band(driver_avg),
        "carrier_health": derive_band(carrier_avg),
        "truck_health": derive_band(truck_avg),
        "dispatch_readiness": derive_band(dispatch_readiness),
        "operational_readiness": derive_band(operational_health),
        "capacity": capacity,
        "top_performers": {
            "drivers": [{"id": s["driver_id"],
                         "name": s.get("display_name"),
                         "score": s["overall"]["score"]}
                        for s in _top(drivers)],
            "carriers": [{"id": s["carrier_id"],
                           "name": s.get("legal_name"),
                           "score": s["overall"]["score"]}
                         for s in _top(carriers)],
            "trucks": [{"id": s["truck_id"],
                         "name": s.get("truck_number"),
                         "score": s["overall"]["score"]}
                       for s in _top(trucks)],
        },
        "attention_required": {
            "drivers": [{"id": s["driver_id"],
                         "name": s.get("display_name"),
                         "score": s["overall"]["score"],
                         "watch": [e["label"] for e in s.get("explanations", [])
                                    if e.get("impact") in ("watch", "negative")][:3]}
                        for s in _attention(drivers)],
            "carriers": [{"id": s["carrier_id"],
                           "name": s.get("legal_name"),
                           "score": s["overall"]["score"]}
                         for s in _attention(carriers)],
            "trucks": [{"id": s["truck_id"],
                         "name": s.get("truck_number"),
                         "score": s["overall"]["score"]}
                       for s in _attention(trucks)],
        },
        "trends": trends,
    }

    await write_intelligence_audit(
        db, kind="executive_dashboard_generated",
        subject_type="executive_dashboard", subject_id=None,
        snapshot={
            "transportation_health": dashboard["transportation_health"],
            "driver_health": dashboard["driver_health"],
            "carrier_health": dashboard["carrier_health"],
            "truck_health": dashboard["truck_health"],
            "dispatch_readiness": dashboard["dispatch_readiness"],
            "capacity": dashboard["capacity"],
        },
    )
    return dashboard


async def build_operational_health(db) -> Dict[str, Any]:
    """Thin shim used by API for the consolidated KPIs widget."""
    dash = await build_executive_dashboard(db)
    return {
        "transportation_health": dash["transportation_health"],
        "driver_health": dash["driver_health"],
        "carrier_health": dash["carrier_health"],
        "truck_health": dash["truck_health"],
        "dispatch_readiness": dash["dispatch_readiness"],
        "operational_readiness": dash["operational_readiness"],
        "capacity": dash["capacity"],
        "schema_version": SCHEMA_VERSION,
        "generated_at": dash["generated_at"],
    }
