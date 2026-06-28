"""TRACK 16.16 · Operations × Transportation Integration Layer.

THIN read-only consumer endpoint that lets Operations surfaces (Project
workspaces, Operations Center Command, PM Command Center) display
Transportation awareness without leaving their workspace.

Doctrine
========
* Operations CONSUMES Transportation. Transportation never consumes Operations.
* This route introduces NO new scoring, NO new collections, NO new
  audit kinds, NO new emails, NO new schedulers.
* Every value returned is composed from existing engines:
    - ``transportation_dashboard_hr_health()`` (Track 16.11A)
    - Phase-2 dashboard counters via the existing collections
      (``transport_eligibility_state`` · ``carrier_documents`` ·
      ``driver_documents`` · ``transport_truck_inspections`` ·
      ``transport_action_items``).
* The heavyweight per-entity engines (Track 16.12 driver/carrier/
  truck intelligence, Track 16.15 cleanup signal computation) are
  intentionally NOT invoked from this hot endpoint — they continue
  to serve the Intelligence Center + Cleanup Companion surfaces.
  Operations consumers see materialized action counts instead.
* Cross-portal RBAC mirrors `/api/operations/events`: any signed-in
  portal token (admin / safety / hr / shop / pm / dispatch) may READ.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends

logger = logging.getLogger(__name__)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _count_blocked_dispatches(db) -> int:
    """Eligibility states that prevent dispatch RIGHT NOW.

    Reads the existing ``transport_eligibility_state`` collection — no
    new compute. Mirrors the Track 16.09 dispatch gate truth table.
    """
    from lib.transport_phase2 import TENANT  # noqa: PLC0415
    blocking = ("not_dispatchable", "suspended", "expired", "needs_correction")
    rows = await db.transport_eligibility_state.find({
        "tenant": TENANT,
        "state": {"$in": list(blocking)},
    }).to_list(5000)
    return len(rows)


async def _count_open_action_items(db) -> int:
    """Open Transportation action items from the Track 16.10 queue."""
    from lib.transport_phase2 import TENANT  # noqa: PLC0415
    return await db.transport_action_items.count_documents({
        "tenant": TENANT,
        "status": {"$in": ["open", "in_progress"]},
    })


async def _build_dashboard_tiles(db) -> Dict[str, Any]:
    """Reuse the Track 16.06 dashboard tile counters verbatim.

    Inline-importing the helper functions from the Phase-2 module so
    we do not duplicate any of that logic. Returns the subset that
    Operations consumers care about.
    """
    from lib.transport_phase2 import TENANT  # noqa: PLC0415
    now_iso = datetime.now(timezone.utc).isoformat()
    soon_iso = (datetime.now(timezone.utc) + timedelta(days=30)).isoformat()

    # Per-target eligibility buckets — same shape as
    # ``routes.transportation_experience._count_states``.
    async def _buckets(target_type: str) -> Dict[str, int]:
        out: Dict[str, int] = {}
        cur = db.transport_eligibility_state.find({
            "tenant": TENANT, "target_type": target_type,
        })
        for r in await cur.to_list(10000):
            s = r.get("state") or "unknown"
            out[s] = out.get(s, 0) + 1
        return out

    carrier_b = await _buckets("carrier")
    person_b = await _buckets("person")
    truck_b = await _buckets("truck")

    pending_review = (
        await db.transport_persons.count_documents({
            "tenant": TENANT, "status": "pending_review"})
        + await db.carriers.count_documents({
            "tenant": TENANT, "status": "pending_review"})
    )
    documents_awaiting = (
        await db.carrier_documents.count_documents({
            "tenant": TENANT, "status": "pending_review"})
        + await db.driver_documents.count_documents({
            "tenant": TENANT, "status": "pending_review"})
    )
    upcoming_expirations = (
        await db.carrier_documents.count_documents({
            "tenant": TENANT, "expires_at": {"$gte": now_iso, "$lt": soon_iso},
            "status": {"$in": ["accepted", "pending_review"]},
        })
        + await db.driver_documents.count_documents({
            "tenant": TENANT, "expires_at": {"$gte": now_iso, "$lt": soon_iso},
            "status": {"$in": ["accepted", "pending_review"]},
        })
    )

    return {
        "available_drivers": person_b.get("eligible", 0),
        "available_trucks": truck_b.get("eligible", 0),
        "available_carriers": carrier_b.get("eligible", 0),
        "pending_reviews": pending_review,
        "documents_awaiting_review": documents_awaiting,
        "upcoming_expirations_30d": upcoming_expirations,
    }


def _build_risks(
    *,
    blocked_dispatches: int,
    top_cleanup: Optional[Dict[str, Any]],
    hr_health: Dict[str, Any],
    upcoming_expirations: int,
) -> List[Dict[str, Any]]:
    """Distill the readiness envelope into a calm operator-facing risk
    list. Returns at most 5 risks. Empty when fleet is healthy — no
    warning fatigue.
    """
    risks: List[Dict[str, Any]] = []
    if blocked_dispatches > 0:
        risks.append({
            "code": "blocked_dispatches",
            "severity": "action_required",
            "label": f"{blocked_dispatches} dispatch(es) currently blocked",
            "source": "transport_eligibility_state",
        })
    if top_cleanup and top_cleanup.get("severity") == "action_required":
        risks.append({
            "code": f"cleanup_{top_cleanup.get('signal_key', 'unknown')}",
            "severity": "action_required",
            "label": top_cleanup.get("title") or "Cleanup action required",
            "source": "cleanup_companion",
        })
    counts = (hr_health or {}).get("counts") or {}
    mismatches = counts.get("sync_mismatches") or 0
    if mismatches > 0:
        risks.append({
            "code": "hr_mismatch",
            "severity": "watch",
            "label": f"{mismatches} HR ↔ Transportation mismatch(es)",
            "source": "transport_sync_monitor",
        })
    if upcoming_expirations > 0:
        risks.append({
            "code": "upcoming_expirations",
            "severity": "watch",
            "label": (
                f"{upcoming_expirations} document(s) expiring within 30 days"),
            "source": "carrier_documents+driver_documents",
        })
    return risks[:5]


def _band_from_score(score: float) -> Dict[str, Any]:
    """Tiny calm projection — green / yellow / red — derived from
    existing Track 16.12 band score thresholds. NO new scoring; we
    simply map an existing score onto a 3-light visual."""
    score = float(score or 0)
    if score >= 80:
        return {"label": "green", "score": round(score, 1)}
    if score >= 50:
        return {"label": "yellow", "score": round(score, 1)}
    return {"label": "red", "score": round(score, 1)}


def register_track_16_16_routes(
    app, db,
    require_any_portal_dep: Callable,
) -> APIRouter:
    """Mount the Operations × Transportation integration endpoint."""
    router = APIRouter(
        prefix="/api/operations",
        tags=["operations-transportation-integration"],
    )

    @router.get("/transportation/readiness")
    async def transportation_readiness(
        _: Any = Depends(require_any_portal_dep),
    ) -> Dict[str, Any]:
        """One-shot read-only envelope for Operations consumers.

        Composed from EXISTING engines — no new scoring is performed.
        Performance discipline: only LIGHTWEIGHT engines run here
        (count-based eligibility + cleanup signals + HR sync KPIs).
        The heavyweight Track 16.12 per-entity intelligence engine
        is intentionally NOT invoked — its output is already served
        on the Intelligence Center for users who need it.
        """
        from lib.transport_phase2 import TENANT  # noqa: PLC0415

        # 1) Phase-2 dashboard counters (reused inline — same queries
        #    the existing Track 16.06 dashboard runs).
        tiles = await _build_dashboard_tiles(db)
        blocked_dispatches = await _count_blocked_dispatches(db)
        open_action_items = await _count_open_action_items(db)

        # 2) Count-based band projections (mirrors Track 16.06
        #    _compute_compliance_score). No new scoring — just a
        #    pct-eligible projection per target type.
        async def _bucket_score(target_type: str) -> float:
            cur = db.transport_eligibility_state.find(
                {"tenant": TENANT, "target_type": target_type})
            total = eligible = 0
            for r in await cur.to_list(10000):
                total += 1
                if r.get("state") == "eligible":
                    eligible += 1
            return (eligible / total * 100.0) if total else 0.0

        driver_score = await _bucket_score("person")
        truck_score = await _bucket_score("truck")
        carrier_score = await _bucket_score("carrier")
        # Overall = simple unweighted average across the three
        # populations (mirrors Track 16.06 compliance score
        # philosophy: eligible / total).
        present = [s for s in (driver_score, truck_score, carrier_score)
                   if s is not None]
        overall_score = sum(present) / len(present) if present else 0.0
        # Dispatch readiness = pct eligible across drivers + trucks
        # (the two entities that actually appear on dispatch rows).
        dispatch_score = ((driver_score + truck_score) / 2.0
                          if (driver_score is not None
                              and truck_score is not None) else 0.0)

        # 3) Cleanup awareness — read the count of materialized
        # cleanup action items (Track 16.15 materializes these on
        # operator demand). Fast: a single count query. We do NOT
        # invoke the cleanup-signals builder here — the heavy 12-signal
        # scan already runs on the Transportation Dashboard
        # (Track 16.15A) and the Intelligence Center; Operations
        # consumers see the same materialized queue.
        from lib.transport_phase2 import TENANT as _T  # noqa: PLC0415,F811
        cleanup_count = await db.transport_action_items.count_documents({
            "tenant": _T,
            "event_key": {"$regex": "^cleanup::"},
            "status": {"$in": ["open", "in_progress"]},
        })
        top_cleanup = None  # surfaced via Track 16.15A dashboard card.

        # 4) HR ↔ Transportation sync health — Track 16.11A (fast).
        try:
            from lib.transport_sync_monitor import (
                transportation_dashboard_hr_health,
            )
            hr_health = await transportation_dashboard_hr_health(db)
        except Exception as exc:  # noqa: BLE001
            logger.warning(
                f"[track-16-16] hr_health unavailable: {exc}")
            hr_health = {}

        # 5) Distill risks for the calm "only show if needed" banner.
        risks = _build_risks(
            blocked_dispatches=blocked_dispatches,
            top_cleanup=top_cleanup,
            hr_health=hr_health,
            upcoming_expirations=tiles["upcoming_expirations_30d"],
        )

        return {
            "ok": True,
            "schema_version": "16.16.0",
            "generated_at": _now_iso(),
            "overall_readiness": _band_from_score(overall_score),
            "driver_band": _band_from_score(driver_score),
            "truck_band": _band_from_score(truck_score),
            "carrier_band": _band_from_score(carrier_score),
            "dispatch_readiness": {
                "score": round(dispatch_score, 1),
                "label": _band_from_score(dispatch_score)["label"],
            },
            "capacity": {
                "drivers": {"pct_eligible": round(driver_score, 1)},
                "trucks":  {"pct_eligible": round(truck_score, 1)},
                "carriers": {"pct_eligible": round(carrier_score, 1)},
            },
            "snapshot": {
                **tiles,
                "blocked_dispatches": blocked_dispatches,
                "open_action_items": open_action_items,
            },
            "cleanup": {
                "total_signals": cleanup_count,
                "top": top_cleanup,
            },
            "hr_sync": {
                "health": (hr_health or {}).get("health") or "unknown",
                "mismatches": ((hr_health or {}).get("counts") or {}).get(
                    "sync_mismatches", 0),
            },
            "risks": risks,
            "links": {
                "transportation_dashboard": "/admin/transportation",
                "cleanup_companion": "/admin/transportation/intelligence/cleanup",
                "intelligence": "/admin/transportation/intelligence",
            },
            "note": (
                "Read-only mirror of Transportation engines. No business "
                "logic is computed here — every value is composed from "
                "Tracks 16.06 / 16.10 / 16.11A / 16.15. Heavyweight "
                "per-entity intelligence (Track 16.12) lives in the "
                "Intelligence Center."),
        }

    app.include_router(router)
    return router


__all__ = ["register_track_16_16_routes"]
