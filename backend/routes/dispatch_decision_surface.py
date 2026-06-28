"""TRACK 16.13 · Dispatch Decision Surface.

Surfaces the Track 16.12 Transportation Operations Intelligence engine
inside the dispatcher assignment flow. Read-only recommendation +
explainability audit. NEVER weakens the Track 16.09 dispatch hard-block
and NEVER duplicates intelligence calculations.

Endpoints
---------
* ``GET /api/dispatch/transportation/recommendation``
    Admin OR dispatch auth. Read-only.
* ``POST /api/dispatch/transportation/recommendation/audit``
    Admin OR dispatch auth. Records dispatcher interaction events:
    viewed / selected / non_recommended_selected / ignored. Never
    mutates assignments.
"""
from __future__ import annotations

import logging
import uuid
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

TENANT = "masci"
SCHEMA_VERSION = "16.13.0"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class RecommendationAuditEvent(BaseModel):
    event: str = Field(...,
                        pattern="^(viewed|selected|non_recommended_selected|ignored)$")
    recommendation_id: Optional[str] = None
    driver_id: Optional[str] = None
    carrier_id: Optional[str] = None
    truck_id: Optional[str] = None
    selected_driver_id: Optional[str] = None
    selected_carrier_id: Optional[str] = None
    selected_truck_id: Optional[str] = None
    note: Optional[str] = Field(None, max_length=500)
    score: Optional[float] = None
    grade: Optional[str] = None


def register_track_16_13_routes(
    app, db, *,
    require_dispatch_or_admin_dep: Callable[..., Any],
) -> APIRouter:
    router = APIRouter(prefix="/api/dispatch/transportation",
                       tags=["dispatch-decision-surface"])

    async def _audit(kind: str, actor: Dict[str, Any],
                     payload: Dict[str, Any]) -> str:
        """Best-effort audit writer. Returns audit id."""
        aid = uuid.uuid4().hex
        try:
            await db.transport_dispatch_recommendation_audit.insert_one({
                "id": aid, "tenant": TENANT, "kind": kind,
                "actor_role": (actor or {}).get("role") or "dispatch",
                "actor_email": (actor or {}).get("email"),
                "actor_id": (actor or {}).get("id"),
                "payload": payload,
                "schema_version": SCHEMA_VERSION,
                "ts": _now_iso(),
            })
        except Exception as exc:  # noqa: BLE001
            logger.warning("dispatch_decision audit failed: %s", exc)
        return aid

    @router.get("/recommendation")
    async def recommendation(
        carrier_id: Optional[str] = Query(None),
        truck_type: Optional[str] = Query(None),
        transport_person_id: Optional[str] = Query(None),
        transport_truck_id: Optional[str] = Query(None),
        job_id: Optional[str] = Query(None),
        project_id: Optional[str] = Query(None),
        requested_date: Optional[str] = Query(None),
        limit: int = Query(5, ge=1, le=20),
        actor: Dict[str, Any] = Depends(require_dispatch_or_admin_dep),
    ) -> Dict[str, Any]:
        """Read-only dispatch recommendation. Delegates to Track 16.12
        recommendation engine; never re-implements scoring."""
        try:
            from lib.transport_recommendation_engine import (
                recommend_drivers, recommend_carriers, recommend_trucks,
                recommend_dispatch_triple,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("intelligence engine unavailable: %s", exc)
            await _audit("transport_dispatch_recommendation_failed", actor,
                          {"reason": "engine_unavailable",
                           "error": str(exc)[:240]})
            return {
                "ok": False,
                "schema_version": SCHEMA_VERSION,
                "generated_at": _now_iso(),
                "message": (
                    "Recommendation unavailable. Assignment can continue "
                    "through standard eligibility gate."),
            }

        try:
            triple = await recommend_dispatch_triple(
                db, carrier_id=carrier_id, truck_type=truck_type)
            driver_list = await recommend_drivers(
                db, limit=limit, carrier_id=carrier_id)
            carrier_list = await recommend_carriers(db, limit=limit)
            truck_list = await recommend_trucks(
                db, limit=limit, carrier_id=carrier_id,
                truck_type=truck_type)

            # Excluded options: enumerate non-dispatchable drivers/trucks/
            # carriers via existing eligibility state so dispatchers see why.
            excluded = await _excluded_options(db, limit=limit)

            # Composite score / why / watch from the best driver candidate
            # (the dispatch triple's driver pick).
            best_driver = triple.get("driver") or {}
            score = float(((best_driver.get("overall") or {}).get("score")) or 0)
            grade = (best_driver.get("overall") or {}).get("grade") or "fair"
            why = best_driver.get("why") or []
            watch = best_driver.get("watch") or []

            rec_id = uuid.uuid4().hex
            payload = {
                "ok": True,
                "recommendation_id": rec_id,
                "recommended": {
                    "carrier": triple.get("carrier"),
                    "driver": triple.get("driver"),
                    "truck": triple.get("truck"),
                    "triple": triple,
                    "score": round(score, 2),
                    "grade": grade,
                    "why": why,
                    "watch": watch,
                },
                "alternatives": {
                    "drivers": driver_list.get("items", []),
                    "carriers": carrier_list.get("items", []),
                    "trucks": truck_list.get("items", []),
                },
                "excluded": excluded,
                "context": {
                    "job_id": job_id, "project_id": project_id,
                    "requested_date": requested_date,
                    "carrier_id": carrier_id, "truck_type": truck_type,
                    "transport_person_id": transport_person_id,
                    "transport_truck_id": transport_truck_id,
                },
                "schema_version": SCHEMA_VERSION,
                "generated_at": _now_iso(),
            }
            await _audit("transport_dispatch_recommendation_generated",
                          actor,
                          {"recommendation_id": rec_id,
                           "score": payload["recommended"]["score"],
                           "grade": grade,
                           "candidates_considered": {
                               "drivers": driver_list.get(
                                   "candidates_considered", 0),
                               "carriers": carrier_list.get(
                                   "candidates_considered", 0),
                               "trucks": truck_list.get(
                                   "candidates_considered", 0),
                           },
                           "context": payload["context"]})
            return payload
        except Exception as exc:  # noqa: BLE001
            logger.warning("dispatch_decision recommendation failed: %s", exc)
            await _audit("transport_dispatch_recommendation_failed", actor,
                          {"reason": "compute_error",
                           "error": str(exc)[:240]})
            return {
                "ok": False,
                "schema_version": SCHEMA_VERSION,
                "generated_at": _now_iso(),
                "message": (
                    "Recommendation unavailable. Assignment can continue "
                    "through standard eligibility gate."),
            }

    @router.post("/recommendation/audit")
    async def recommendation_audit(
        body: RecommendationAuditEvent,
        actor: Dict[str, Any] = Depends(require_dispatch_or_admin_dep),
    ) -> Dict[str, Any]:
        """Capture dispatcher interaction with the recommendation surface.
        Operational learning only — never punitive, never blocking."""
        kind_map = {
            "viewed": "transport_dispatch_recommendation_viewed",
            "selected": "transport_dispatch_recommendation_selected",
            "non_recommended_selected":
                "transport_dispatch_non_recommended_selected",
            "ignored": "transport_dispatch_recommendation_ignored",
        }
        kind = kind_map.get(body.event)
        if not kind:
            raise HTTPException(400, "invalid event")
        aid = await _audit(kind, actor, body.model_dump(exclude_none=True))
        return {"ok": True, "audit_id": aid,
                "schema_version": SCHEMA_VERSION}

    app.include_router(router)
    return router


# ---------------------------------------------------------------------------
# Helper: enumerate non-dispatchable rows for the "excluded" surface.
# Uses the canonical eligibility table — no duplicated logic.
# ---------------------------------------------------------------------------
async def _excluded_options(db, *, limit: int) -> Dict[str, List[Dict[str, Any]]]:
    excluded: Dict[str, List[Dict[str, Any]]] = {
        "drivers": [], "trucks": [], "carriers": [],
    }
    blocking_states = {"not_dispatchable", "suspended", "expired",
                        "needs_correction"}
    cur = db.transport_eligibility_state.find({"tenant": TENANT})
    rows = await cur.to_list(2000)
    rows = [r for r in rows if r.get("state") in blocking_states]

    # Group + cap per type.
    by_target: Dict[str, List[Dict[str, Any]]] = {"person": [],
                                                   "truck": [],
                                                   "carrier": []}
    for r in rows:
        tt = r.get("target_type")
        if tt in by_target:
            by_target[tt].append(r)

    for tt, items in by_target.items():
        coll = {"person": "transport_persons",
                "truck": "transport_trucks",
                "carrier": "carriers"}[tt]
        bucket_key = {"person": "drivers", "truck": "trucks",
                       "carrier": "carriers"}[tt]
        for r in items[:limit]:
            row = await db[coll].find_one(
                {"id": r.get("target_id"), "tenant": TENANT})
            if not row:
                continue
            row.pop("_id", None)
            reasons = [{"label": x.get("label") or x.get("code"),
                         "code": x.get("code")}
                        for x in (r.get("reasons") or [])]
            excluded[bucket_key].append({
                "id": r.get("target_id"),
                "name": (row.get("legal_name")
                          or row.get("truck_number")
                          or f"{row.get('first_name','')} "
                             f"{row.get('last_name','')}".strip()
                          or r.get("target_id")),
                "state": r.get("state"),
                "reasons": reasons,
            })
    return excluded
