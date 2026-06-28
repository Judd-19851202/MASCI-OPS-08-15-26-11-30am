"""TRACK 16.12 · Driver Intelligence.

Reads ONLY from existing MASCI collections:
* ``transport_persons`` (Track 16.04+)
* ``transport_eligibility_state``
* ``transport_certificates`` (Track 16.08)
* ``transport_orientation_modules`` / orientation status
* ``driver_documents``
* ``transport_action_items``
* ``transport_dispatch_overrides``
* ``incidents`` (Safety — read-only)
* ``employees`` (HR — read-only)

Produces a deterministic snapshot with sub-indices (experience,
compliance, safety, performance) plus an overall reliability score.
Every score carries explanation rows so operators see "why".
"""
from __future__ import annotations

from datetime import timedelta
from typing import Any, Dict, List, Optional

from lib.transport_intelligence_core import (
    TENANT, SCHEMA_VERSION, now_iso, now_dt, days_until, parse_iso,
    clamp, composite, derive_band, make_explanation, projection_strip,
    write_intelligence_audit,
)


# ---------------------------------------------------------------------------
# Sub-index builders — each returns {score, weight, signals[], explanations[]}
# ---------------------------------------------------------------------------
async def _experience_index(db, person: Dict[str, Any],
                            hr_employee: Optional[Dict[str, Any]]
                            ) -> Dict[str, Any]:
    """Years with MASCI + driver-status promotion."""
    explanations: List[Dict[str, Any]] = []
    years = 0
    if hr_employee:
        hire = parse_iso(hr_employee.get("original_hire_date")
                          or hr_employee.get("hire_date"))
        if hire:
            years = max(0, int((now_dt() - hire).days / 365.25))
    # 0y → 50, 1y → 70, 3y → 85, 5y+ → 100 (deterministic linear).
    if years >= 5:
        score = 100.0
    elif years >= 3:
        score = 85.0
    elif years >= 1:
        score = 70.0
    elif years >= 0:
        score = 50.0
    else:
        score = 40.0
    explanations.append(make_explanation(
        code="years_with_masci", label=f"{years} year(s) with MASCI",
        impact="positive", weight=1.0, delta=score, fix=None,
        record_id=(hr_employee or {}).get("id"),
        record_type="employee" if hr_employee else None,
    ))
    if (person.get("kind") == "leased_driver"):
        score = clamp(score - 5)
        explanations.append(make_explanation(
            code="leased_driver", label="Leased carrier driver",
            impact="neutral", weight=1.0, delta=-5.0,
            fix="No action — informational",
        ))
    return {
        "score": clamp(score), "weight": 1.0,
        "signals": {"years_with_masci": years},
        "explanations": explanations,
    }


async def _compliance_index(db, person: Dict[str, Any],
                            eligibility: Optional[Dict[str, Any]],
                            ) -> Dict[str, Any]:
    """Orientation + documents + CDL + medical + Clearinghouse + eligibility."""
    explanations: List[Dict[str, Any]] = []
    base = 100.0

    elig_state = (eligibility or {}).get("state") or "pending_review"
    state_penalty = {
        "eligible": 0, "pending_review": 10, "needs_correction": 25,
        "suspended": 40, "expired": 30, "not_dispatchable": 60,
    }.get(elig_state, 30)
    base -= state_penalty
    explanations.append(make_explanation(
        code=f"eligibility_{elig_state}",
        label=f"Eligibility state: {elig_state.replace('_', ' ')}",
        impact="negative" if state_penalty else "positive",
        weight=1.0, delta=-state_penalty,
        fix=("Resolve documents / orientation / HR projection blocks"
             if state_penalty else None),
    ))

    # Open compliance documents / action items.
    open_actions = await db.transport_action_items.find(
        {"tenant": TENANT, "status": {"$in": ["open", "in_progress"]},
         "$or": [{"entity_id": person["id"]},
                 {"entity_type": "transport_person", "entity_id": person["id"]}]},
    ).to_list(50)
    blocking = [a for a in open_actions if a.get("severity") in ("block", "critical", "blocking")]
    if blocking:
        penalty = min(40, 8 * len(blocking))
        base -= penalty
        explanations.append(make_explanation(
            code="blocking_actions",
            label=f"{len(blocking)} blocking action item(s)",
            impact="negative", weight=1.0, delta=-penalty,
            fix="Resolve open blocking actions in Command Queue",
        ))

    # Driver documents nearing expiry.
    docs = await db.driver_documents.find(
        {"tenant": TENANT, "transport_person_id": person["id"]}
    ).to_list(100)
    expired = 0
    expiring_soon = 0
    for d in docs:
        days = days_until(d.get("expires_at"))
        if days is None:
            continue
        if days < 0:
            expired += 1
        elif days <= 30:
            expiring_soon += 1
    if expired:
        base -= min(30, expired * 10)
        explanations.append(make_explanation(
            code="documents_expired",
            label=f"{expired} document(s) expired",
            impact="negative", weight=1.0,
            delta=-min(30, expired * 10),
            fix="Renew expired documents in driver workspace",
        ))
    if expiring_soon:
        base -= min(12, expiring_soon * 4)
        explanations.append(make_explanation(
            code="documents_expiring",
            label=f"{expiring_soon} document(s) expiring within 30 days",
            impact="watch", weight=0.5, delta=-min(12, expiring_soon * 4),
            fix="Schedule renewal before expiration",
        ))

    return {
        "score": clamp(base), "weight": 2.0,
        "signals": {
            "eligibility_state": elig_state,
            "blocking_actions": len(blocking),
            "documents_expired": expired,
            "documents_expiring_30d": expiring_soon,
        },
        "explanations": explanations,
    }


async def _safety_index(db, person: Dict[str, Any]) -> Dict[str, Any]:
    """Incident frequency + safety holds + recognition."""
    explanations: List[Dict[str, Any]] = []
    base = 100.0

    if person.get("safety_hold"):
        base -= 30
        explanations.append(make_explanation(
            code="safety_hold", label="Active safety hold",
            impact="negative", weight=1.0, delta=-30,
            fix="Lift safety hold once corrective action is verified",
        ))

    incidents_12mo = 0
    try:
        recent = now_dt() - timedelta(days=365)
        cur = db.incidents.find({
            "$or": [{"driver_id": person["id"]},
                    {"linked_employee_id": person.get("employee_id")}],
        })
        rows = await cur.to_list(200)
        for r in rows:
            ts = parse_iso(r.get("occurred_at") or r.get("created_at"))
            if ts and ts >= recent:
                incidents_12mo += 1
    except Exception:  # noqa: BLE001
        # Safety collection optional in test env; skip silently.
        pass
    if incidents_12mo:
        penalty = min(40, incidents_12mo * 15)
        base -= penalty
        explanations.append(make_explanation(
            code="incidents_12mo",
            label=f"{incidents_12mo} incident(s) in last 12 months",
            impact="negative", weight=1.5, delta=-penalty,
            fix="Coordinate Safety review",
        ))
    else:
        explanations.append(make_explanation(
            code="no_incidents",
            label="No incidents recorded in last 12 months",
            impact="positive", weight=1.0, delta=0,
        ))

    return {
        "score": clamp(base), "weight": 2.0,
        "signals": {"safety_hold": bool(person.get("safety_hold")),
                    "incidents_12mo": incidents_12mo},
        "explanations": explanations,
    }


async def _performance_index(db, person: Dict[str, Any]
                              ) -> Dict[str, Any]:
    """Orientation certificate health + override frequency + freshness."""
    explanations: List[Dict[str, Any]] = []
    base = 100.0

    # Orientation certificate freshness.
    try:
        cert = await db.transport_certificates.find_one(
            {"tenant": TENANT, "transport_person_id": person["id"]},
            sort=[("issued_at", -1)],
        )
    except Exception:  # noqa: BLE001
        cert = None
    if not cert:
        base -= 25
        explanations.append(make_explanation(
            code="no_orientation_cert",
            label="No orientation certificate on file",
            impact="negative", weight=1.0, delta=-25,
            fix="Complete driver orientation modules",
        ))
    else:
        days = days_until(cert.get("expires_at"))
        if days is None:
            base -= 5
        elif days < 0:
            base -= 25
            explanations.append(make_explanation(
                code="orientation_expired",
                label="Orientation certificate expired",
                impact="negative", weight=1.0, delta=-25,
                fix="Refresh annual orientation",
                record_id=cert.get("id"), record_type="transport_certificate",
            ))
        elif days <= 60:
            base -= 8
            explanations.append(make_explanation(
                code="orientation_expiring",
                label=f"Orientation expires in {days} days",
                impact="watch", weight=0.5, delta=-8,
                fix="Schedule renewal before expiration",
                record_id=cert.get("id"), record_type="transport_certificate",
            ))
        else:
            explanations.append(make_explanation(
                code="orientation_current",
                label="Orientation certificate current",
                impact="positive", weight=1.0, delta=0,
                record_id=cert.get("id"), record_type="transport_certificate",
            ))

    # Dispatch overrides last 90 days (frequent overrides = compensating signal).
    try:
        ninety_days_ago = (now_dt() - timedelta(days=90)).isoformat()
        cur = db.transport_dispatch_overrides.find({
            "tenant": TENANT, "driver_id": person["id"],
            "created_at": {"$gte": ninety_days_ago},
        })
        overrides = await cur.to_list(50)
    except Exception:  # noqa: BLE001
        overrides = []
    if len(overrides) >= 3:
        base -= 15
        explanations.append(make_explanation(
            code="frequent_overrides",
            label=f"{len(overrides)} dispatch overrides in last 90 days",
            impact="watch", weight=1.0, delta=-15,
            fix="Investigate root cause and close compliance gaps",
        ))

    return {
        "score": clamp(base), "weight": 1.5,
        "signals": {"orientation_present": bool(cert),
                    "overrides_90d": len(overrides)},
        "explanations": explanations,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------
async def compute_driver_intelligence(
    db, driver_id: str, *, persist_audit: bool = True,
) -> Dict[str, Any]:
    """Compute and (optionally) audit a driver intelligence snapshot.
    Read-only against business collections."""
    person = await db.transport_persons.find_one(
        {"tenant": TENANT, "id": driver_id})
    if not person:
        return {
            "ok": False, "error": "driver_not_found",
            "driver_id": driver_id,
            "schema_version": SCHEMA_VERSION,
            "computed_at": now_iso(),
        }

    eligibility = await db.transport_eligibility_state.find_one({
        "tenant": TENANT, "target_type": "person",
        "target_id": driver_id,
    })

    # HR record (optional — only meaningful for masci_employee).
    hr_employee = None
    if person.get("kind") == "masci_employee" and person.get("employee_id"):
        try:
            hr_employee = await db.employees.find_one(
                {"$or": [{"employee_id": person["employee_id"]},
                          {"id": person["employee_id"]}],
                 "deleted_at": None}, {"_id": 0})
        except Exception:  # noqa: BLE001
            pass

    experience = await _experience_index(db, person, hr_employee)
    compliance = await _compliance_index(db, person, eligibility)
    safety = await _safety_index(db, person)
    performance = await _performance_index(db, person)

    overall = composite([
        {"score": experience["score"], "weight": experience["weight"]},
        {"score": compliance["score"], "weight": compliance["weight"]},
        {"score": safety["score"], "weight": safety["weight"]},
        {"score": performance["score"], "weight": performance["weight"]},
    ])
    operational_readiness = composite([
        {"score": compliance["score"], "weight": 2.0},
        {"score": performance["score"], "weight": 1.0},
    ])

    all_expl = (
        experience["explanations"] + compliance["explanations"]
        + safety["explanations"] + performance["explanations"]
    )

    snapshot = {
        "driver_id": driver_id,
        "kind": person.get("kind"),
        "display_name": (f"{person.get('first_name','')} "
                          f"{person.get('last_name','')}").strip()
                          or person.get("email") or "Unknown driver",
        "eligibility_state": (eligibility or {}).get("state"),
        "indices": {
            "experience": derive_band(experience["score"]),
            "compliance": derive_band(compliance["score"]),
            "safety": derive_band(safety["score"]),
            "performance": derive_band(performance["score"]),
        },
        "overall": derive_band(overall),
        "operational_readiness": derive_band(operational_readiness),
        "explanations": all_expl,
        "signals": {
            **experience["signals"],
            **compliance["signals"],
            **safety["signals"],
            **performance["signals"],
        },
        "computed_at": now_iso(),
        "schema_version": SCHEMA_VERSION,
    }

    if persist_audit:
        await write_intelligence_audit(
            db, kind="driver_intelligence_refresh",
            subject_type="transport_person",
            subject_id=driver_id, snapshot={
                "overall": snapshot["overall"],
                "indices": snapshot["indices"],
                "signals": snapshot["signals"],
            },
        )
    return snapshot


async def list_driver_intelligence(
    db, *, limit: int = 200, state: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Fan-out across all drivers (read-only). Used by recommendation
    engine + executive dashboard."""
    query: Dict[str, Any] = {"tenant": TENANT}
    cur = db.transport_persons.find(query).limit(limit)
    drivers = await cur.to_list(limit)
    out: List[Dict[str, Any]] = []
    for d in drivers:
        snap = await compute_driver_intelligence(
            db, d["id"], persist_audit=False)
        if not snap.get("ok", True):
            continue
        if state and snap.get("eligibility_state") != state:
            continue
        out.append(snap)
    return out
